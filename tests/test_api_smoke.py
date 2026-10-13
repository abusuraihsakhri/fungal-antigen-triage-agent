"""HTTP smoke tests for both existing FastAPI application surfaces."""
from fastapi.testclient import TestClient

from fungal_antigen_triage_agent.server import create_app
from agents.api import app as audit_app


def test_clinical_server_routes():
    app = create_app()
    assert app is not None
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        result = client.post("/api/audit", json={
            "case_id": "SYNTH-001", "patient_synthetic_id": "SYNTH-P1",
            "primary_metric": 12.0, "secondary_metric": 5.0,
            "status_flag": "NORMAL", "is_stat": False,
        })
        assert result.status_code == 200
        assert result.json()["overall_status"] == "CONCORDANT_NORMAL"
        chat = client.post("/api/chat", json={"query": "status"})
        assert chat.status_code == 200


def test_generic_audit_server_routes_and_phi_rejection():
    with TestClient(audit_app) as client:
        assert client.get("/health").status_code == 200
        response = client.post("/api/audit", json={
            "task_id": "SYNTH-001", "target_identifier": "SPECIMEN-1",
            "primary_metric": 1.0,
        })
        assert response.status_code == 200
        assert response.json()["total_alerts"] == 0
        blocked = client.post("/api/audit", json={
            "task_id": "SYNTH-002", "target_identifier": "SPECIMEN-2",
            "primary_metric": 1.0, "attributes": {"note": "MRN: 123456"},
        })
        assert blocked.status_code == 422
        assert "MRN" not in str(blocked.json())
