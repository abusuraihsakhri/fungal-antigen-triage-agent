"""Tests for Fungal Antigen Triage Agent."""
import json
import pytest
from myco_sentinel import (
    interpret_bdg,
    interpret_gm,
    interpret_crag,
    interpret_mannan,
    assess_pretest_probability,
    combined_interpretation,
    BDG_FALSE_POSITIVE_FACTORS,
    GM_FALSE_POSITIVE_FACTORS,
    main,
)


# ─── BDG Interpretation Tests ────────────────────────────────────────────────

def test_bdg_negative():
    result = interpret_bdg(30.0)
    assert result["category"] == "NEGATIVE"
    assert result["clinical_significance"] == "LOW"


def test_bdg_indeterminate():
    result = interpret_bdg(70.0)
    assert result["category"] == "INDETERMINATE"
    assert result["clinical_significance"] == "MODERATE"


def test_bdg_positive():
    result = interpret_bdg(150.0)
    assert result["category"] == "POSITIVE"
    assert result["clinical_significance"] == "HIGH"


def test_bdg_boundary_60():
    result = interpret_bdg(60.0)
    assert result["category"] == "INDETERMINATE"


def test_bdg_boundary_80():
    result = interpret_bdg(80.0)
    assert result["category"] == "POSITIVE"


def test_bdg_boundary_59():
    result = interpret_bdg(59.9)
    assert result["category"] == "NEGATIVE"


def test_bdg_false_positive_hemodialysis():
    result = interpret_bdg(150.0, false_positive_factors=["hemodialysis"])
    assert result["false_positive_risk"] == "HIGH"
    assert result["clinical_significance"] == "MODERATE"  # Adjusted down


def test_bdg_false_positive_antibiotics():
    result = interpret_bdg(150.0, false_positive_factors=["piperacillin_tazobactam"])
    assert len(result["false_positive_factors"]) > 0


def test_bdg_negative_value():
    result = interpret_bdg(-10.0)
    assert "error" in result


def test_bdg_has_alerts_positive():
    result = interpret_bdg(200.0)
    assert len(result["alerts"]) > 0
    assert result["alerts"][0]["type"] == "BDG_POSITIVE"


def test_bdg_has_alerts_indeterminate():
    result = interpret_bdg(65.0)
    assert len(result["alerts"]) > 0
    assert result["alerts"][0]["type"] == "BDG_INDETERMINATE"


# ─── GM Interpretation Tests ─────────────────────────────────────────────────

def test_gm_serum_negative():
    result = interpret_gm(0.3, "serum")
    assert result["category"] == "NEGATIVE"


def test_gm_serum_indeterminate():
    result = interpret_gm(0.7, "serum")
    assert result["category"] == "INDETERMINATE"


def test_gm_serum_positive():
    result = interpret_gm(1.5, "serum")
    assert result["category"] == "POSITIVE"
    assert result["clinical_significance"] == "HIGH"


def test_gm_bal_negative():
    result = interpret_gm(0.5, "bal")
    assert result["category"] == "NEGATIVE"


def test_gm_bal_positive():
    result = interpret_gm(0.8, "bal")
    assert result["category"] == "POSITIVE"


def test_gm_bal_threshold():
    result = interpret_gm(0.7, "bal")
    assert result["category"] == "POSITIVE"


def test_gm_false_positive_piptazo():
    result = interpret_gm(1.5, "serum", false_positive_factors=["piperacillin_tazobactam"])
    assert result["false_positive_risk"] == "HIGH"
    assert result["clinical_significance"] == "MODERATE"


def test_gm_negative_value():
    result = interpret_gm(-0.5, "serum")
    assert "error" in result


def test_gm_has_alerts():
    result = interpret_gm(1.5, "serum")
    assert len(result["alerts"]) > 0


# ─── CrAg Interpretation Tests ───────────────────────────────────────────────

def test_crag_negative():
    result = interpret_crag(False)
    assert result["category"] == "NEGATIVE"
    assert result["clinical_significance"] == "LOW"


def test_crag_positive_serum():
    result = interpret_crag(True, titer="1:128", specimen_type="serum")
    assert result["category"] == "POSITIVE"
    assert result["clinical_significance"] == "HIGH"
    assert result["disease_burden"] == "MODERATE"


def test_crag_positive_csf():
    result = interpret_crag(True, specimen_type="csf")
    assert result["category"] == "POSITIVE"
    assert result["clinical_significance"] == "CRITICAL"


def test_crag_high_titer():
    result = interpret_crag(True, titer="1:1024")
    assert result["disease_burden"] == "HIGH"


def test_crag_low_titer():
    result = interpret_crag(True, titer="1:4")
    assert result["disease_burden"] == "LOW"


def test_crag_elevated_pressure():
    result = interpret_crag(True, specimen_type="csf", csf_opening_pressure=35.0)
    assert any(a["type"] == "ELEVATED_OPENING_PRESSURE" for a in result["alerts"])


def test_crag_has_alerts_positive():
    result = interpret_crag(True)
    assert len(result["alerts"]) > 0


# ─── Mannan/Anti-mannan Tests ────────────────────────────────────────────────

def test_mannan_both_negative():
    result = interpret_mannan(mannan_value=50.0, anti_mannan_value=5.0)
    assert result["category"] == "BOTH_NEGATIVE"


def test_mannan_both_positive():
    result = interpret_mannan(mannan_value=200.0, anti_mannan_value=20.0)
    assert result["category"] == "BOTH_POSITIVE"
    assert result["clinical_significance"] == "HIGH"


def test_mannan_antigen_only():
    result = interpret_mannan(mannan_value=200.0, anti_mannan_value=5.0)
    assert result["category"] == "MANNAN_POSITIVE"


def test_mannan_antibody_only():
    result = interpret_mannan(mannan_value=50.0, anti_mannan_value=20.0)
    assert result["category"] == "ANTI_MANNAN_POSITIVE"


def test_mannan_threshold():
    result = interpret_mannan(mannan_value=125.0)
    assert result["mannan_positive"] is True


# ─── Pre-test Probability Tests ──────────────────────────────────────────────

def test_pretest_low_risk():
    result = assess_pretest_probability({})
    assert result["risk_category"] == "LOW"
    assert result["risk_score"] == 0


def test_pretest_high_risk():
    factors = {
        "neutropenic": True,
        "hematologic_malignancy": True,
        "central_venous_catheter": True,
        "broad_spectrum_antibiotics": True,
    }
    result = assess_pretest_probability(factors)
    assert result["risk_category"] == "HIGH"
    assert result["risk_score"] >= 8


def test_pretest_moderate_risk():
    factors = {"prolonged_icu": True, "corticosteroids": True}
    result = assess_pretest_probability(factors)
    assert result["risk_category"] == "MODERATE"


def test_pretest_hiv():
    factors = {"hiv_aids": True}
    result = assess_pretest_probability(factors)
    assert result["risk_score"] >= 3


def test_pretest_risk_factors_counted():
    factors = {"neutropenic": True, "liver_failure": True}
    result = assess_pretest_probability(factors)
    assert result["total_risk_factors"] == 2


# ─── Combined Interpretation Tests ───────────────────────────────────────────

def test_combined_all_negative():
    result = combined_interpretation(bdg_value=30.0, gm_index=0.2)
    assert result["combined_severity"] == "LOW"


def test_combined_bdg_positive_gm_positive():
    result = combined_interpretation(bdg_value=150.0, gm_index=1.5)
    assert result["combined_severity"] == "HIGH"
    assert len(result["tests_performed"]) == 2


def test_combined_single_positive():
    result = combined_interpretation(bdg_value=150.0, gm_index=0.2)
    assert result["combined_severity"] == "MODERATE"


def test_combined_with_host_factors():
    result = combined_interpretation(
        bdg_value=150.0,
        host_factors={"neutropenic": True, "hematologic_malignancy": True,
                      "central_venous_catheter": True, "broad_spectrum_antibiotics": True},
    )
    assert "pretest_probability" in result
    assert result["pretest_probability"]["risk_category"] == "HIGH"


def test_combined_with_crag():
    result = combined_interpretation(crag_positive=True)
    assert "CrAg" in result["tests_performed"]


def test_combined_with_mannan():
    result = combined_interpretation(mannan_value=200.0, anti_mannan_value=20.0)
    assert "Mannan/Anti-mannan" in result["tests_performed"]


# ─── CLI Tests ───────────────────────────────────────────────────────────────

def test_cli_bdg():
    assert main(["bdg", "--value", "150.0"]) == 0


def test_cli_gm():
    assert main(["gm", "--index", "1.5"]) == 0


def test_cli_crag():
    assert main(["crag", "--positive"]) == 0


def test_cli_combined():
    assert main(["combined", "--bdg", "150.0", "--gm", "1.5"]) == 0


def test_cli_help():
    with pytest.raises(SystemExit) as exc:
        main(["bdg", "--help"])
    assert exc.value.code == 0
