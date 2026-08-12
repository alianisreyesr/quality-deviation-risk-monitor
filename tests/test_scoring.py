"""Unit tests for the explainable risk-scoring rules."""
import pytest
from app.scoring import score_deviation


def _base_record(**overrides) -> dict:
    record = {
        "deviation_id": "DEV-TEST",
        "title": "Synthetic test record",
        "severity": "Low",
        "opened_date": "2026-01-01",
        "due_date": "2099-12-31",  # far future -> not overdue
        "investigation_owner": "Test Owner",
        "repeat_occurrence": False,
        "record_complete": True,
        "review_status": "Pending Review",
    }
    record.update(overrides)
    return record


def test_low_risk_clean_record():
    result = score_deviation(_base_record())
    assert result["risk_level"] == "Low"
    assert result["risk_score"] == 0
    assert result["risk_reasons"] == []


def test_high_severity_adds_three_points():
    result = score_deviation(_base_record(severity="High"))
    assert result["risk_score"] == 3
    assert "High severity" in result["risk_reasons"]


def test_medium_severity_adds_one_point():
    result = score_deviation(_base_record(severity="Medium"))
    assert result["risk_score"] == 1
    assert "Medium severity" in result["risk_reasons"]


def test_overdue_record_adds_three_points():
    result = score_deviation(_base_record(due_date="2020-01-01"))
    assert result["risk_score"] >= 3
    assert "Past due date" in result["risk_reasons"]


def test_no_owner_adds_two_points():
    result = score_deviation(_base_record(investigation_owner=""))
    assert result["risk_score"] == 2
    assert "No investigation owner assigned" in result["risk_reasons"]


def test_repeat_occurrence_adds_two_points():
    result = score_deviation(_base_record(repeat_occurrence=True))
    assert result["risk_score"] == 2
    assert "Repeat occurrence" in result["risk_reasons"]


def test_incomplete_record_adds_two_points():
    result = score_deviation(_base_record(record_complete=False))
    assert result["risk_score"] == 2
    assert "Required data is incomplete" in result["risk_reasons"]


def test_all_risk_factors_yields_high_level():
    result = score_deviation(
        _base_record(
            severity="High",
            due_date="2020-01-01",
            investigation_owner="",
            repeat_occurrence=True,
            record_complete=False,
        )
    )
    assert result["risk_level"] == "High"
    assert result["risk_score"] >= 5
    assert len(result["risk_reasons"]) == 5


def test_none_owner_treated_as_unassigned():
    result = score_deviation(_base_record(investigation_owner=None))
    assert "No investigation owner assigned" in result["risk_reasons"]


def test_string_boolean_values_are_handled():
    """CSV values arrive as strings; scoring must handle both forms."""
    result = score_deviation(
        _base_record(repeat_occurrence="True", record_complete="False")
    )
    assert "Repeat occurrence" in result["risk_reasons"]
    assert "Required data is incomplete" in result["risk_reasons"]
