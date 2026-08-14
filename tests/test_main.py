"""
Unit tests for Quality Deviation Risk Monitor.
Grounded in ICH Q10 §3.2 and ICH Q9(R1) §4.
"""
from fastapi.testclient import TestClient
from app.main import app, score_deviation
from app import config

client = TestClient(app)


def base_record(**overrides):
    record = {
        "deviation_id":        "DEV-TEST-0",
        "title":               "Synthetic test record",
        "severity":            "Low",
        "opened_date":         "2026-08-13",
        "due_date":            "2099-12-31",
        "investigation_owner": "QA Owner",
        "repeat_occurrence":   "False",
        "record_complete":     "True",
        "review_status":       "Open",
    }
    record.update(overrides)
    return record


# Severity
def test_high_severity_adds_three_points():
    result = score_deviation(base_record(severity="High"))
    assert result["risk_score"] >= config.SEVERITY_SCORES["High"]
    assert "High severity" in result["risk_reasons"]

def test_medium_severity_adds_one_point():
    result = score_deviation(base_record(severity="Medium"))
    assert result["risk_score"] >= config.SEVERITY_SCORES["Medium"]
    assert "Medium severity" in result["risk_reasons"]

def test_low_severity_adds_no_points():
    result = score_deviation(base_record(severity="Low"))
    assert config.SEVERITY_SCORES["Low"] == 0
    assert "Low severity" not in result["risk_reasons"]


# Aging (ICH Q10 §3.2)
def test_aging_no_penalty_under_30_days():
    result = score_deviation(base_record(opened_date="2026-08-01", review_status="Open"))
    assert not any("days" in r.lower() for r in result["risk_reasons"])

def test_aging_tier1_over_30_days():
    result = score_deviation(base_record(opened_date="2026-07-01", review_status="Open"))
    assert any(f"{config.AGING_THRESHOLD_DAYS_TIER1} days" in r for r in result["risk_reasons"])
    assert result["risk_score"] >= config.AGING_SCORE_TIER1

def test_aging_tier2_over_60_days():
    result = score_deviation(base_record(opened_date="2026-06-01", review_status="Open"))
    assert any(f"{config.AGING_THRESHOLD_DAYS_TIER2} days" in r for r in result["risk_reasons"])
    assert result["risk_score"] >= config.AGING_SCORE_TIER1 + config.AGING_SCORE_TIER2

def test_aging_no_penalty_when_closed():
    result = score_deviation(base_record(opened_date="2025-01-01", review_status="Closed"))
    assert not any("days" in r.lower() for r in result["risk_reasons"]), \
        "Closed deviations must not receive aging penalty"


# Other factors
def test_past_due_date_adds_points():
    result = score_deviation(base_record(due_date="2020-01-01"))
    assert result["risk_score"] >= config.SCORE_PAST_DUE_DATE
    assert "Past due date" in result["risk_reasons"]

def test_no_owner_adds_points():
    result = score_deviation(base_record(investigation_owner=""))
    assert result["risk_score"] >= config.SCORE_NO_OWNER
    assert "No investigation owner assigned" in result["risk_reasons"]

def test_repeat_occurrence_adds_points():
    result = score_deviation(base_record(repeat_occurrence="True"))
    assert result["risk_score"] >= config.SCORE_REPEAT_OCCURRENCE
    assert "Repeat occurrence" in result["risk_reasons"]

def test_incomplete_record_adds_points():
    result = score_deviation(base_record(record_complete="False"))
    assert result["risk_score"] >= config.SCORE_INCOMPLETE_RECORD
    assert "Required data is incomplete" in result["risk_reasons"]


# Classification
def test_clean_record_is_low_risk():
    result = score_deviation(base_record())
    assert result["risk_level"] == "Low"
    assert result["risk_score"] == 0

def test_high_risk_record_has_explainable_reasons():
    record = base_record(
        severity="High", opened_date="2026-01-01", due_date="2026-01-02",
        investigation_owner="", repeat_occurrence="True",
        record_complete="False", review_status="Open",
    )
    result = score_deviation(record)
    assert result["risk_level"] == "High"
    assert result["risk_score"] >= config.RISK_THRESHOLD_HIGH
    assert "High severity" in result["risk_reasons"]
    assert "Past due date" in result["risk_reasons"]
    assert "No investigation owner assigned" in result["risk_reasons"]
    assert "Repeat occurrence" in result["risk_reasons"]
    assert "Required data is incomplete" in result["risk_reasons"]
    assert any(str(config.AGING_THRESHOLD_DAYS_TIER2) in r for r in result["risk_reasons"])


# API
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
    assert all(r["risk_level"] == "High" for r in payload["records"])

def test_summary_endpoint_returns_risk_counts():
    response = client.get("/summary")
    assert response.status_code == 200
    payload = response.json()
    assert "total_records" in payload
    assert set(payload["risk_counts"]).issubset({"Low", "Medium", "High"})
