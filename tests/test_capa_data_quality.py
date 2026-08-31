"""Tests for GET /capas/data-quality and the CAPA data_quality helpers.

Mirrors tests/test_data_quality.py — covers unique IDs, required fields,
valid dates, and allowed severity/type/status values for the CAPA dataset.
"""
from fastapi.testclient import TestClient

from app.data_quality import build_capa_data_quality_report
from app.main import app

client = TestClient(app)

EXPECTED_FIELDS = [
    "capa_id",
    "title",
    "capa_type",
    "severity",
    "opened_date",
    "due_date",
    "closure_date",
    "owner",
    "root_cause",
    "recurrence_flag",
    "effectiveness_check_complete",
    "status",
]


def test_capa_data_quality_returns_200():
    r = client.get("/capas/data-quality")
    assert r.status_code == 200


def test_capa_data_quality_all_expected_fields_present():
    data = client.get("/capas/data-quality").json()
    reported = {f["field_name"] for f in data["fields"]}
    assert set(EXPECTED_FIELDS) == reported


def test_capa_data_quality_rates_between_0_and_1():
    data = client.get("/capas/data-quality").json()
    for field in data["fields"]:
        assert 0.0 <= field["null_rate"] <= 1.0
        assert 0.0 <= field["invalid_rate"] <= 1.0
    assert 0.0 <= data["issue_rate"] <= 1.0


def test_capa_data_quality_issue_rate_consistent():
    data = client.get("/capas/data-quality").json()
    total = data["total_records"]
    if total > 0:
        expected_rate = round(data["records_with_any_issue"] / total, 4)
        assert abs(data["issue_rate"] - expected_rate) < 1e-4


# ---------------------------------------------------------------------------
# Unique-ID detection (duplicate capa_id)
# ---------------------------------------------------------------------------

def _clean_capa(**overrides) -> dict:
    record = {
        "capa_id": "CAPA-TEST-01",
        "title": "Test CAPA",
        "capa_type": "Corrective",
        "severity": "Low",
        "opened_date": "2026-01-01",
        "due_date": "2026-06-01",
        "closure_date": None,
        "owner": "tester",
        "root_cause": "Human Error",
        "recurrence_flag": "false",
        "effectiveness_check_complete": "true",
        "status": "Open",
    }
    record.update(overrides)
    return record


def test_duplicate_capa_id_flags_both_records():
    dup_a = _clean_capa()
    dup_b = _clean_capa(title="A different title, same ID")
    report = build_capa_data_quality_report(records=[dup_a, dup_b])
    id_field = next(f for f in report["fields"] if f["field_name"] == "capa_id")
    assert id_field["invalid_count"] == 2
    assert "CAPA-TEST-01" in id_field["sample_invalid_values"]
    assert report["records_with_any_issue"] == 2


def test_unique_capa_ids_no_issue():
    a = _clean_capa(capa_id="CAPA-TEST-01")
    b = _clean_capa(capa_id="CAPA-TEST-02")
    report = build_capa_data_quality_report(records=[a, b])
    id_field = next(f for f in report["fields"] if f["field_name"] == "capa_id")
    assert id_field["invalid_count"] == 0
    assert report["records_with_any_issue"] == 0


def test_invalid_capa_type_detected():
    bad = _clean_capa(capa_type="Remedial")
    report = build_capa_data_quality_report(records=[bad])
    field = next(f for f in report["fields"] if f["field_name"] == "capa_type")
    assert field["invalid_count"] == 1
    assert "Remedial" in field["sample_invalid_values"]


def test_invalid_status_detected():
    bad = _clean_capa(status="Cancelled")
    report = build_capa_data_quality_report(records=[bad])
    field = next(f for f in report["fields"] if f["field_name"] == "status")
    assert field["invalid_count"] == 1


def test_missing_required_title_detected():
    bad = _clean_capa(title="")
    report = build_capa_data_quality_report(records=[bad])
    field = next(f for f in report["fields"] if f["field_name"] == "title")
    assert field["null_count"] == 1


def test_clean_record_no_issues():
    report = build_capa_data_quality_report(records=[_clean_capa()])
    assert report["records_with_any_issue"] == 0
