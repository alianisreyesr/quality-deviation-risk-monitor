from fastapi.testclient import TestClient

from app.main import app, score_deviation

client = TestClient(app)


def test_high_risk_record_has_explainable_reasons():
    record = {
        "deviation_id": "DEV-TEST-1",
        "title": "Synthetic test record",
        "severity": "High",
        "opened_date": "2026-01-01",
        "due_date": "2026-01-02",
        "investigation_owner": "",
        "repeat_occurrence": "True",
        "record_complete": "False",
        "review_status": "Pending Review",
    }

    result = score_deviation(record)

    assert result["risk_level"] == "High"
    assert result["risk_score"] >= 5
    assert "High severity" in result["risk_reasons"]
    assert "No investigation owner assigned" in result["risk_reasons"]
    assert "Required data is incomplete" in result["risk_reasons"]


def test_health_endpoint_identifies_synthetic_data():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["data_classification"] == "synthetic portfolio data"


def test_deviations_endpoint_filters_by_risk_level():
    response = client.get("/deviations?risk_level=High")

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] > 0
    assert all(record["risk_level"] == "High" for record in payload["records"])


def test_summary_endpoint_returns_risk_counts():
    response = client.get("/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_records"] == 6
    assert set(payload["risk_counts"]) == {"Low", "Medium", "High"}
