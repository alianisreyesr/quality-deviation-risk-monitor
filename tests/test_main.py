from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.scoring import score_deviation


def test_high_risk_record_has_explainable_reasons():
    result = score_deviation({"deviation_id": "DEV-TEST-1", "title": "Synthetic test record", "severity": "High", "opened_date": "2026-01-01", "due_date": "2026-01-02", "investigation_owner": "", "repeat_occurrence": "True", "record_complete": "False", "review_status": "Pending Review"}, today=date(2026, 2, 1))
    assert result["risk_level"] == "High"
    assert result["risk_score"] == 12
    assert result["risk_reasons"] == ["High severity", "Past due date", "No investigation owner assigned", "Repeat occurrence", "Required data is incomplete"]


def test_low_risk_record_has_no_reasons():
    result = score_deviation({"deviation_id": "DEV-TEST-2", "title": "Synthetic test record", "severity": "Low", "opened_date": "2026-01-01", "due_date": "2026-12-31", "investigation_owner": "Alex", "repeat_occurrence": False, "record_complete": True, "review_status": "In Review"}, today=date(2026, 2, 1))
    assert result["risk_level"] == "Low"
    assert result["risk_score"] == 0


def test_api_endpoints_return_typed_synthetic_records():
    with TestClient(app) as client:
        health = client.get("/health")
        deviations = client.get("/deviations?risk_level=High")
        summary = client.get("/summary")
    assert health.status_code == 200
    assert health.json()["decision_support"] == "human review required"
    assert deviations.status_code == 200
    assert all(record["risk_level"] == "High" for record in deviations.json()["records"])
    assert summary.json()["total_records"] >= deviations.json()["count"]


def test_unknown_deviation_returns_404():
    with TestClient(app) as client:
        response = client.get("/deviations/DEV-DOES-NOT-EXIST")
    assert response.status_code == 404
