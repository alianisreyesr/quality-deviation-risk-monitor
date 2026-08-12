"""Integration tests for the FastAPI endpoints."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["data_classification"] == "synthetic portfolio data"


def test_deviations_returns_records():
    response = client.get("/deviations")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "records" in data
    assert data["count"] > 0
    assert len(data["records"]) == data["count"]


def test_deviations_each_record_has_required_fields():
    response = client.get("/deviations")
    records = response.json()["records"]
    required_fields = {"deviation_id", "title", "severity", "risk_level", "risk_score", "risk_reasons"}
    for record in records:
        assert required_fields.issubset(record.keys()), f"Missing fields in {record['deviation_id']}"


def test_filter_by_high_risk_returns_only_high():
    response = client.get("/deviations?risk_level=High")
    assert response.status_code == 200
    records = response.json()["records"]
    assert all(r["risk_level"] == "High" for r in records)


def test_filter_by_low_risk_returns_only_low():
    response = client.get("/deviations?risk_level=Low")
    assert response.status_code == 200
    records = response.json()["records"]
    assert all(r["risk_level"] == "Low" for r in records)


def test_filter_invalid_risk_level_returns_422():
    response = client.get("/deviations?risk_level=Critical")
    assert response.status_code == 422


def test_summary_has_all_risk_levels():
    response = client.get("/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_records" in data
    assert set(data["risk_counts"].keys()) == {"Low", "Medium", "High"}


def test_summary_counts_match_total():
    response = client.get("/summary")
    data = response.json()
    risk_total = sum(data["risk_counts"].values())
    assert risk_total == data["total_records"]


def test_summary_review_status_counts_are_positive():
    response = client.get("/summary")
    review_counts = response.json()["review_status_counts"]
    assert all(v > 0 for v in review_counts.values())
