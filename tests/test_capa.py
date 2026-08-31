"""Integration tests for the GET /capas and GET /capas/{capa_id} endpoints."""
from fastapi.testclient import TestClient

from app.capa_scoring import CAPA_SCORING_RULE_VERSION
from app.main import app

client = TestClient(app)


def test_capas_returns_records():
    response = client.get("/capas")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "records" in data
    assert data["count"] > 0
    assert len(data["records"]) == data["count"]


def test_capas_each_record_has_required_fields():
    response = client.get("/capas")
    records = response.json()["records"]
    required_fields = {
        "capa_id", "title", "capa_type", "severity", "status",
        "aging_days", "risk_score", "risk_level", "risk_reasons",
        "scoring_rule_version",
    }
    for record in records:
        assert required_fields.issubset(record.keys()), f"Missing fields in {record['capa_id']}"


def test_capas_include_scoring_rule_version():
    records = client.get("/capas").json()["records"]
    for record in records:
        assert record["scoring_rule_version"] == CAPA_SCORING_RULE_VERSION


def test_filter_capas_by_high_risk_returns_only_high():
    response = client.get("/capas?risk_level=High")
    assert response.status_code == 200
    records = response.json()["records"]
    assert all(r["risk_level"] == "High" for r in records)


def test_filter_capas_invalid_risk_level_returns_422():
    response = client.get("/capas?risk_level=Critical")
    assert response.status_code == 422


def test_filter_capas_by_status():
    response = client.get("/capas?status=Closed")
    assert response.status_code == 200
    records = response.json()["records"]
    assert records, "Expected at least one closed CAPA in the synthetic dataset"
    assert all(r["status"] == "Closed" for r in records)


def test_filter_capas_invalid_status_returns_422():
    response = client.get("/capas?status=Cancelled")
    assert response.status_code == 422


def test_get_single_capa_by_id():
    first_id = client.get("/capas").json()["records"][0]["capa_id"]
    response = client.get(f"/capas/{first_id}")
    assert response.status_code == 200
    assert response.json()["capa_id"] == first_id


def test_get_missing_capa_returns_404():
    response = client.get("/capas/CAPA-DOES-NOT-EXIST")
    assert response.status_code == 404


def test_closed_capas_have_zero_aging_growth_reasons():
    """A closed CAPA's risk_reasons must never include an open-only signal."""
    records = client.get("/capas?status=Closed").json()["records"]
    open_only_reasons = {
        "Past due date",
        "No CAPA owner assigned",
        "Open more than 30 days",
        "Open more than 60 days",
    }
    for record in records:
        assert not open_only_reasons.intersection(record["risk_reasons"])
