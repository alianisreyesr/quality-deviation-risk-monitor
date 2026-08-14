"""Unit tests for Pydantic models: app.models and app.audit_models."""
import pytest
from datetime import date, datetime, timezone
from app.models import DeviationResponse
from app.audit_models import AuditEventResponse, ReviewActionRequest, AuditTrailResponse


# ---------------------------------------------------------------------------
# DeviationResponse
# ---------------------------------------------------------------------------

MIN_DEVIATION = {
    "deviation_id": "DEV-001",
    "title": "Temperature excursion in cold storage",
    "severity": "High",
    "opened_date": date(2026, 7, 1),
    "due_date": date(2026, 8, 1),
    "investigation_owner": None,
    "repeat_occurrence": False,
    "record_complete": True,
    "review_status": "pending",
    "risk_score": 6,
    "risk_level": "High",
    "risk_reasons": ["Severity is High", "Past due date"],
    "scoring_rule_version": "1.0.0",
}


def test_deviation_response_accepts_minimum_fields():
    record = DeviationResponse(**MIN_DEVIATION)
    assert record.deviation_id == "DEV-001"
    assert record.risk_level == "High"


def test_deviation_response_risk_reasons_is_list():
    record = DeviationResponse(**MIN_DEVIATION)
    assert isinstance(record.risk_reasons, list)
    assert len(record.risk_reasons) == 2


def test_deviation_response_optional_investigation_owner_none():
    record = DeviationResponse(**MIN_DEVIATION)
    assert record.investigation_owner is None


def test_deviation_response_serialises_to_dict():
    record = DeviationResponse(**MIN_DEVIATION)
    d = record.model_dump()
    assert d["deviation_id"] == "DEV-001"
    assert "risk_reasons" in d
    assert "scoring_rule_version" in d


def test_deviation_response_rejects_missing_required_field():
    bad = {k: v for k, v in MIN_DEVIATION.items() if k != "deviation_id"}
    with pytest.raises(Exception):  # pydantic ValidationError
        DeviationResponse(**bad)


def test_deviation_response_rejects_invalid_risk_level():
    bad = {**MIN_DEVIATION, "risk_level": "Critical"}
    with pytest.raises(Exception):
        DeviationResponse(**bad)


# ---------------------------------------------------------------------------
# ReviewActionRequest
# ---------------------------------------------------------------------------

def test_review_action_request_valid_actions():
    for action in ("acknowledge", "investigate", "close"):
        ra = ReviewActionRequest(action=action, actor="test-user")
        assert ra.action == action


def test_review_action_request_rejects_invalid_action():
    with pytest.raises(Exception):
        ReviewActionRequest(action="delete", actor="test-user")


def test_review_action_request_comment_is_optional():
    ra = ReviewActionRequest(action="acknowledge", actor="analyst-1")
    assert ra.comment is None


def test_review_action_request_comment_stored_when_provided():
    ra = ReviewActionRequest(action="close", actor="qa-lead", comment="Root cause confirmed.")
    assert ra.comment == "Root cause confirmed."


def test_review_action_request_rejects_empty_actor():
    with pytest.raises(Exception):
        ReviewActionRequest(action="acknowledge", actor="")


# ---------------------------------------------------------------------------
# AuditEventResponse
# ---------------------------------------------------------------------------

AUDIT_EVENT = {
    "event_id": 1,
    "deviation_id": "DEV-001",
    "action": "acknowledge",
    "actor": "analyst-1",
    "comment": None,
    "previous_status": "pending",
    "new_status": "under_review",
    "created_at": datetime(2026, 8, 12, 22, 0, 0, tzinfo=timezone.utc),
}


def test_audit_event_response_required_fields():
    event = AuditEventResponse(**AUDIT_EVENT)
    assert event.deviation_id == "DEV-001"
    assert event.actor == "analyst-1"
    assert event.event_id == 1


def test_audit_event_response_status_transition_captured():
    event = AuditEventResponse(**AUDIT_EVENT)
    assert event.previous_status == "pending"
    assert event.new_status == "under_review"


def test_audit_event_response_comment_optional():
    event = AuditEventResponse(**AUDIT_EVENT)
    assert event.comment is None


def test_audit_event_response_with_comment():
    event = AuditEventResponse(**{**AUDIT_EVENT, "comment": "Acknowledged by QA."})
    assert event.comment == "Acknowledged by QA."


# ---------------------------------------------------------------------------
# AuditTrailResponse (replaces AuditMiddlewareEvent — serialization round-trip)
# ---------------------------------------------------------------------------

def test_audit_trail_response_round_trip():
    """Model serialises and deserialises without data loss."""
    payload = {
        "deviation_id": "DEV-001",
        "current_review_status": "closed",
        "event_count": 3,
        "events": [
            {"event_id": 1, "action": "acknowledge"},
            {"event_id": 2, "action": "investigate"},
            {"event_id": 3, "action": "close"},
        ],
    }
    trail = AuditTrailResponse(**payload)
    dumped = trail.model_dump()
    assert dumped["deviation_id"] == "DEV-001"
    assert dumped["event_count"] == 3
    assert len(dumped["events"]) == 3


def test_audit_trail_response_event_count_matches_events_list():
    payload = {
        "deviation_id": "DEV-002",
        "current_review_status": "under_review",
        "event_count": 1,
        "events": [{"event_id": 1, "action": "acknowledge"}],
    }
    trail = AuditTrailResponse(**payload)
    assert trail.event_count == len(trail.events)
