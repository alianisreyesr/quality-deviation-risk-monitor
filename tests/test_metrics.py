"""Tests for GET /metrics and app/metrics.py helpers."""
from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.metrics import (
    build_capa_aging_metric,
    build_capa_closure_metric,
    build_deviation_aging_metric,
    build_quality_metrics,
    build_recurrence_metric,
    build_root_cause_breakdown,
    build_severity_distribution,
)

client = TestClient(app)


def test_metrics_returns_200():
    r = client.get("/metrics")
    assert r.status_code == 200


def test_metrics_top_level_keys():
    data = client.get("/metrics").json()
    for key in (
        "generated_at", "deviation_aging", "capa_aging", "recurrence",
        "severity_distribution", "capa_closure", "root_causes",
    ):
        assert key in data


def test_metrics_severity_distribution_shape():
    data = client.get("/metrics").json()
    for bucket in ("deviations", "capas"):
        dist = data["severity_distribution"][bucket]
        assert set(dist.keys()) == {"Low", "Medium", "High"}
        assert sum(dist.values()) > 0


def test_metrics_recurrence_rates_between_0_and_1():
    data = client.get("/metrics").json()
    assert 0.0 <= data["recurrence"]["deviation_recurrence_rate"] <= 1.0
    assert 0.0 <= data["recurrence"]["capa_recurrence_rate"] <= 1.0


def test_metrics_capa_closure_rate_consistent():
    data = client.get("/metrics").json()
    closure = data["capa_closure"]
    assert closure["closed_count"] <= closure["total_capas"]
    if closure["total_capas"]:
        expected = round(closure["closed_count"] / closure["total_capas"], 4)
        assert abs(closure["closure_rate"] - expected) < 1e-4


# ---------------------------------------------------------------------------
# Unit tests — injected records with a fixed "today"
# ---------------------------------------------------------------------------

TODAY = date(2026, 8, 31)


def test_deviation_aging_excludes_closed_records():
    records = [
        {"opened_date": "2026-08-01", "review_status": "Open"},
        {"opened_date": "2026-01-01", "review_status": "Closed"},
    ]
    result = build_deviation_aging_metric(records, today=TODAY)
    assert result["open_count"] == 1
    assert result["avg_days_open"] == 30.0


def test_deviation_aging_empty_dataset():
    result = build_deviation_aging_metric([], today=TODAY)
    assert result["open_count"] == 0
    assert result["avg_days_open"] == 0.0


def test_capa_aging_matches_capa_scoring():
    records = [
        {"opened_date": "2026-07-01", "status": "Open"},
        {"opened_date": "2026-08-01", "status": "Closed", "closure_date": "2026-08-10"},
    ]
    result = build_capa_aging_metric(records, today=TODAY)
    # Only the open record contributes — the closed one is excluded, matching
    # deviation aging's open-only scope.
    assert result["open_count"] == 1
    assert result["max_days_open"] == 61


def test_recurrence_metric_rates():
    deviations = [{"repeat_occurrence": True}, {"repeat_occurrence": False}]
    capas = [{"recurrence_flag": "true"}, {"recurrence_flag": "false"}, {"recurrence_flag": "false"}]
    result = build_recurrence_metric(deviations, capas)
    assert result["deviation_recurrence_rate"] == 0.5
    assert round(result["capa_recurrence_rate"], 4) == round(1 / 3, 4)


def test_severity_distribution_ignores_unknown_values():
    records = [{"severity": "High"}, {"severity": "High"}, {"severity": "Unknown"}]
    result = build_severity_distribution(records)
    assert result == {"Low": 0, "Medium": 0, "High": 2}


def test_capa_closure_metric_effectiveness_rate():
    capas = [
        {"status": "Closed", "effectiveness_check_complete": True, "opened_date": "2026-01-01", "closure_date": "2026-01-11"},
        {"status": "Closed", "effectiveness_check_complete": False, "opened_date": "2026-01-01", "closure_date": "2026-01-21"},
        {"status": "Open", "effectiveness_check_complete": False, "opened_date": "2026-01-01"},
    ]
    result = build_capa_closure_metric(capas)
    assert result["total_capas"] == 3
    assert result["closed_count"] == 2
    assert result["closure_rate"] == round(2 / 3, 4)
    assert result["effectiveness_check_rate_at_closure"] == 0.5
    assert result["avg_days_to_close"] == 15.0


def test_root_cause_breakdown_buckets_missing_as_unspecified():
    capas = [{"root_cause": "Training Gap"}, {"root_cause": ""}, {"root_cause": None}]
    result = build_root_cause_breakdown(capas)
    assert result["Training Gap"] == 1
    assert result["Unspecified"] == 2


def test_build_quality_metrics_end_to_end_runs():
    """Smoke test against the live seeded database (no injected records)."""
    payload = build_quality_metrics()
    assert payload["deviation_aging"]["open_count"] >= 0
    assert payload["capa_closure"]["total_capas"] > 0
