"""Regression coverage for interpretation, parsing, and audit integrity."""
import math
import pytest
from pydantic import ValidationError

from agents.base import AuditTrail, SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from fungal_antigen_triage_agent.cli import parse_csv_boolean
from myco_sentinel import (
    interpret_bdg, interpret_gm, interpret_crag, interpret_mannan,
    combined_interpretation,
)


def test_audit_hmac_detects_modified_signed_content():
    trail = AuditTrail("test-only-signing-key")
    trail.log("supervisor", "service", "EVALUATED", {"count": 1})
    assert trail.verify_integrity()
    trail.logs[0]["event_type"] = "FORGED"
    assert not trail.verify_integrity()


def test_audit_hash_chain_detects_modified_signature():
    trail = AuditTrail("test-only-signing-key")
    trail.log("supervisor", "service", "START", {"count": 1})
    trail.log("supervisor", "service", "END", {"count": 2})
    trail.logs[0]["current_hash"] = "0" * 64
    assert not trail.verify_integrity()


def test_audit_trail_exposes_defensive_copy():
    trail = AuditTrail("test-only-signing-key")
    trail.log("supervisor", "service", "TEST", {"value": 1})
    returned = trail.get_trail()
    returned[0]["actor"] = "attacker"
    assert trail.verify_integrity()
    assert trail.logs[0]["actor"] == "supervisor"


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), True])
def test_bdg_rejects_non_numeric_or_nonfinite(value):
    assert "error" in interpret_bdg(value)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_gm_rejects_nonfinite(value):
    assert "error" in interpret_gm(value)


def test_gm_rejects_invalid_specimen():
    assert "error" in interpret_gm(0.7, specimen_type="plasma")


def test_crag_rejects_bad_titer_and_pressure():
    assert "error" in interpret_crag(True, titer="unexpected")
    assert "error" in interpret_crag(True, csf_opening_pressure=float("nan"))


def test_mannan_rejects_nonfinite_measurement():
    assert "error" in interpret_mannan(mannan_value=float("nan"))
    assert "error" in interpret_mannan(anti_mannan_value=float("inf"))


def test_invalid_combined_result_is_not_classified_low():
    value = combined_interpretation(bdg_value=float("nan"), gm_index=0.2)
    assert value["combined_severity"] == "INVALID_INPUT"
    assert "error" in value


def test_empty_combined_result_does_not_claim_all_negative():
    value = combined_interpretation()
    assert value["tests_performed"] == []
    assert "No assays supplied" in value["combined_interpretation"]


@pytest.mark.parametrize("value,expected", [
    ("false", False), ("False", False), ("0", False),
    ("true", True), ("TRUE", True), ("1", True), ("", False)
])
def test_explicit_csv_boolean(value, expected):
    assert parse_csv_boolean(value) is expected


def test_csv_boolean_invalid_value_rejected():
    with pytest.raises(ValueError):
        parse_csv_boolean("sometimes")


@pytest.mark.parametrize("field", ["primary_metric", "secondary_metric"])
def test_agent_metric_rejects_nonfinite(field):
    payload = {"task_id": "T-1", "target_identifier": "KEY-1", "primary_metric": 1.0}
    payload[field] = float("nan")
    with pytest.raises(ValidationError):
        SystemTaskPayload(**payload)


def test_phi_guard_scans_metadata():
    case = SystemTaskPayload(
        task_id="T1", target_identifier="K1", primary_metric=1.0,
        attributes={"note": "MRN: 123456"},
    )
    with pytest.raises(SecurityException):
        SystemSupervisor().process_task(case)
