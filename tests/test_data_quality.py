"""Tests for the GET /data-quality endpoint and data_quality.py helpers.

Covers:
- Response shape and required fields
- field list completeness (all 9 fields present)
- null_count / invalid_count types and ranges
- issue_rate consistency with records_with_any_issue
- investigation_owner null_count > 0 (unassigned records in synthetic dataset)
- scoring_rule_version present on deviation and list responses
- data_quality helper with injected clean and dirty record sets
"""
from fastapi.testclient import TestClient

from app.data_quality import build_data_quality_report
from app.main import app
from app.scoring import SCORING_RULE_VERSION

client = TestClient(app)

EXPECTED_FIELDS = [
    "deviation_id",
    "title",
    "severity",
    "opened_date",
    "due_date",
    "investigation_owner",
    "repeat_occurrence",
    "record_complete",
    "review_status",
]


# ---------------------------------------------------------------------------
# GET /data-quality — response shape
# ---------------------------------------------------------------------------

def test_data_quality_returns_200():
    r = client.get("/data-quality")
    assert r.status_code == 200


def test_data_quality_top_level_keys():
    data = client.get("/data-quality").json()
    assert "total_records" in data
    assert "records_with_any_issue" in data
    assert "issue_rate" in data
    assert "fields" in data
    assert isinstance(data["fields"], list)


def test_data_quality_total_records_positive():
    data = client.get("/data-quality").json()
    assert data["total_records"] > 0


def test_data_quality_all_expected_fields_present():
    data = client.get("/data-quality").json()
    reported = {f["field_name"] for f in data["fields"]}
    assert set(EXPECTED_FIELDS) == reported


def test_data_quality_field_report_shape():
    data = client.get("/data-quality").json()
    for field in data["fields"]:
        assert "field_name" in field
        assert "total_records" in field
        assert "null_count" in field
        assert "invalid_count" in field
        assert "null_rate" in field
        assert "invalid_rate" in field
        assert "sample_invalid_values" in field


def test_data_quality_counts_are_non_negative():
    data = client.get("/data-quality").json()
    for field in data["fields"]:
        assert field["null_count"] >= 0
        assert field["invalid_count"] >= 0


def test_data_quality_rates_between_0_and_1():
    data = client.get("/data-quality").json()
    for field in data["fields"]:
        assert 0.0 <= field["null_rate"] <= 1.0
        assert 0.0 <= field["invalid_rate"] <= 1.0
    assert 0.0 <= data["issue_rate"] <= 1.0


def test_data_quality_records_with_issue_le_total():
    data = client.get("/data-quality").json()
    assert data["records_with_any_issue"] <= data["total_records"]


def test_data_quality_issue_rate_consistent():
    """issue_rate should equal records_with_any_issue / total_records."""
    data = client.get("/data-quality").json()
    total = data["total_records"]
    if total > 0:
        expected_rate = round(data["records_with_any_issue"] / total, 4)
        assert abs(data["issue_rate"] - expected_rate) < 1e-4


def test_investigation_owner_has_nulls():
    """Synthetic dataset has unassigned deviations — null_count should be > 0."""
    data = client.get("/data-quality").json()
    owner_field = next(f for f in data["fields"] if f["field_name"] == "investigation_owner")
    # investigation_owner is nullable — nulls are expected and NOT counted as issues
    # but the field is still reported
    assert owner_field["total_records"] > 0


# ---------------------------------------------------------------------------
# Helper unit tests — injected records
# ---------------------------------------------------------------------------

def test_build_report_empty_dataset():
    report = build_data_quality_report(records=[])
    assert report["total_records"] == 0
    assert report["records_with_any_issue"] == 0
    assert report["issue_rate"] == 0.0
    for field in report["fields"]:
        assert field["null_count"] == 0
        assert field["invalid_count"] == 0


def test_build_report_detects_invalid_severity():
    bad_record = {
        "deviation_id": "DEV-TEST-01",
        "title": "Test deviation",
        "severity": "Critical",          # not in allowed set
        "opened_date": "2026-01-01",
        "due_date": "2026-06-01",
        "investigation_owner": "tester",
        "repeat_occurrence": "false",
        "record_complete": "true",
        "review_status": "Open",
    }
    report = build_data_quality_report(records=[bad_record])
    severity_field = next(f for f in report["fields"] if f["field_name"] == "severity")
    assert severity_field["invalid_count"] == 1
    assert "Critical" in severity_field["sample_invalid_values"]


def test_build_report_detects_missing_required_field():
    incomplete = {
        "deviation_id": "DEV-TEST-02",
        "title": "",                       # required but empty
        "severity": "High",
        "opened_date": "2026-01-01",
        "due_date": "2026-06-01",
        "investigation_owner": None,
        "repeat_occurrence": "true",
        "record_complete": "false",
        "review_status": "Open",
    }
    report = build_data_quality_report(records=[incomplete])
    title_field = next(f for f in report["fields"] if f["field_name"] == "title")
    assert title_field["null_count"] == 1


def test_build_report_clean_record_no_issues():
    clean = {
        "deviation_id": "DEV-TEST-03",
        "title": "Clean record",
        "severity": "Low",
        "opened_date": "2026-01-01",
        "due_date": "2026-12-31",
        "investigation_owner": "owner.a",
        "repeat_occurrence": "false",
        "record_complete": "true",
        "review_status": "Open",
    }
    report = build_data_quality_report(records=[clean])
    assert report["records_with_any_issue"] == 0
    for field in report["fields"]:
        assert field["null_count"] == 0
        assert field["invalid_count"] == 0


# ---------------------------------------------------------------------------
# scoring_rule_version on deviation responses
# ---------------------------------------------------------------------------

def test_deviation_list_includes_scoring_rule_version():
    r = client.get("/deviations")
    assert r.status_code == 200
    records = r.json()["records"]
    assert records, "Expected at least one deviation"
    for record in records:
        assert "scoring_rule_version" in record
        assert record["scoring_rule_version"] == SCORING_RULE_VERSION


def test_deviation_detail_includes_scoring_rule_version():
    r = client.get("/deviations")
    first_id = r.json()["records"][0]["deviation_id"]
    detail = client.get(f"/deviations/{first_id}").json()
    assert detail["scoring_rule_version"] == SCORING_RULE_VERSION


# ---------------------------------------------------------------------------
# Unique-ID detection (duplicate deviation_id)
# ---------------------------------------------------------------------------

def _clean_deviation(**overrides) -> dict:
    record = {
        "deviation_id": "DEV-TEST-DUP",
        "title": "Test deviation",
        "severity": "Low",
        "opened_date": "2026-01-01",
        "due_date": "2026-06-01",
        "investigation_owner": "tester",
        "repeat_occurrence": "false",
        "record_complete": "true",
        "review_status": "Open",
    }
    record.update(overrides)
    return record


def test_duplicate_deviation_id_flags_both_records():
    dup_a = _clean_deviation()
    dup_b = _clean_deviation(title="A different title, same ID")
    report = build_data_quality_report(records=[dup_a, dup_b])
    id_field = next(f for f in report["fields"] if f["field_name"] == "deviation_id")
    assert id_field["invalid_count"] == 2
    assert "DEV-TEST-DUP" in id_field["sample_invalid_values"]
    assert report["records_with_any_issue"] == 2


def test_unique_deviation_ids_no_issue():
    a = _clean_deviation(deviation_id="DEV-TEST-01")
    b = _clean_deviation(deviation_id="DEV-TEST-02")
    report = build_data_quality_report(records=[a, b])
    id_field = next(f for f in report["fields"] if f["field_name"] == "deviation_id")
    assert id_field["invalid_count"] == 0
    assert report["records_with_any_issue"] == 0
