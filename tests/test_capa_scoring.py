"""Unit tests for the explainable CAPA risk-scoring and aging rules."""
from datetime import date

import pytest

from app.capa_scoring import (
    AGING_TIER_CRITICAL_DAYS,
    AGING_TIER_ELEVATED_DAYS,
    compute_aging_days,
    score_capa,
)

TODAY = date(2026, 8, 31)


def _base_record(**overrides) -> dict:
    record = {
        "capa_id": "CAPA-TEST",
        "deviation_id": None,
        "title": "Synthetic test CAPA",
        "capa_type": "Corrective",
        "severity": "Low",
        "root_cause": "Human Error",
        "opened_date": "2026-08-25",   # 6 days old relative to TODAY
        "due_date": "2099-12-31",      # far future -> not overdue
        "closure_date": None,
        "owner": "Test Owner",
        "recurrence_flag": False,
        "effectiveness_check_complete": False,
        "status": "Open",
    }
    record.update(overrides)
    return record


def test_low_risk_clean_open_record():
    result = score_capa(_base_record(), today=TODAY)
    assert result["risk_level"] == "Low"
    assert result["risk_score"] == 0
    assert result["risk_reasons"] == []
    assert result["aging_days"] == 6


def test_high_severity_adds_three_points():
    result = score_capa(_base_record(severity="High"), today=TODAY)
    assert result["risk_score"] == 3
    assert "High severity" in result["risk_reasons"]


def test_medium_severity_adds_one_point():
    result = score_capa(_base_record(severity="Medium"), today=TODAY)
    assert result["risk_score"] == 1
    assert "Medium severity" in result["risk_reasons"]


def test_overdue_open_capa_adds_three_points():
    result = score_capa(_base_record(due_date="2020-01-01"), today=TODAY)
    assert result["risk_score"] >= 3
    assert "Past due date" in result["risk_reasons"]


def test_closed_capa_is_never_overdue():
    """Past due_date must not penalize a CAPA that has already closed."""
    result = score_capa(
        _base_record(
            due_date="2020-01-01",
            status="Closed",
            closure_date="2026-08-01",
            effectiveness_check_complete=True,
        ),
        today=TODAY,
    )
    assert "Past due date" not in result["risk_reasons"]


def test_no_owner_on_open_capa_adds_two_points():
    result = score_capa(_base_record(owner=""), today=TODAY)
    assert result["risk_score"] == 2
    assert "No CAPA owner assigned" in result["risk_reasons"]


def test_missing_owner_on_closed_capa_not_penalized():
    """Ownership only matters while the CAPA is actively open."""
    result = score_capa(
        _base_record(
            owner=None,
            status="Closed",
            closure_date="2026-08-30",
            effectiveness_check_complete=True,
        ),
        today=TODAY,
    )
    assert "No CAPA owner assigned" not in result["risk_reasons"]


def test_recurring_root_cause_adds_two_points():
    result = score_capa(_base_record(recurrence_flag=True), today=TODAY)
    assert result["risk_score"] == 2
    assert "Recurring root cause" in result["risk_reasons"]


def test_missing_root_cause_adds_one_point():
    result = score_capa(_base_record(root_cause=""), today=TODAY)
    assert result["risk_score"] == 1
    assert "Missing root cause" in result["risk_reasons"]


def test_closed_without_effectiveness_check_adds_two_points():
    result = score_capa(
        _base_record(status="Closed", closure_date="2026-08-30", effectiveness_check_complete=False),
        today=TODAY,
    )
    assert result["risk_score"] == 2
    assert "Closed without a completed effectiveness check" in result["risk_reasons"]


def test_closed_with_effectiveness_check_no_penalty():
    result = score_capa(
        _base_record(status="Closed", closure_date="2026-08-30", effectiveness_check_complete=True),
        today=TODAY,
    )
    assert result["risk_score"] == 0
    assert result["risk_reasons"] == []


@pytest.mark.parametrize(
    "opened_date,expected_reason",
    [
        ("2026-07-01", f"Open more than {AGING_TIER_CRITICAL_DAYS} days"),  # 61 days old
        ("2026-07-25", f"Open more than {AGING_TIER_ELEVATED_DAYS} days"),  # 37 days old
    ],
)
def test_aging_tiers_add_points(opened_date, expected_reason):
    result = score_capa(_base_record(opened_date=opened_date), today=TODAY)
    assert expected_reason in result["risk_reasons"]
    assert result["risk_score"] > 0


def test_aging_freezes_at_closure():
    """aging_days for a closed CAPA reflects time-to-close, not time since closure."""
    result = score_capa(
        _base_record(
            opened_date="2026-07-01",
            closure_date="2026-07-15",
            status="Closed",
            effectiveness_check_complete=True,
        ),
        today=TODAY,
    )
    assert result["aging_days"] == 14


def test_compute_aging_days_matches_score_capa():
    record = _base_record(opened_date="2026-08-01")
    assert compute_aging_days(record, today=TODAY) == 30


def test_all_risk_factors_yields_high_level():
    result = score_capa(
        _base_record(
            severity="High",
            due_date="2020-01-01",
            owner="",
            recurrence_flag=True,
            root_cause="",
            opened_date="2026-06-01",
        ),
        today=TODAY,
    )
    assert result["risk_level"] == "High"
    assert result["risk_score"] >= 5


def test_string_boolean_values_are_handled():
    """CSV values arrive as strings; scoring must handle both forms."""
    result = score_capa(
        _base_record(recurrence_flag="True", effectiveness_check_complete="False"),
        today=TODAY,
    )
    assert "Recurring root cause" in result["risk_reasons"]
