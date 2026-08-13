"""Unit tests for Pydantic models: app.models and app.audit_models."""
import pytest
from datetime import datetime, timezone
from app.models import DeviationRecord, ReviewAction
from app.audit_models import AuditEventResponse, AuditMiddlewareEvent


# ---------------------------------------------------------------------------
# DeviationRecord
# ---------------------------------------------------------------------------

MIN_DEVIATION = {
    "deviation_id": "DEV-001",
    "title": "Temperature excursion in cold storage",
    "severity": "Major",
    "status": "Open",
    "review_status": "pending",
    "risk_score": 6,
    "risk_level": "High",
    "risk_reasons": ["Severity is Major", "Past due date"],
}


def test_deviation_record_accepts_minimum_fields():
    record = DeviationRecord(**MIN_DEVIATION)
    assert record.deviation_id == "DEV-001"
    assert record.risk_level == "High"


def test_deviation_record_risk_reasons_is_list():
    record = DeviationRecord(**MIN_DEVIATION)
    assert isinstance(record.risk_reasons, list)
    assert len(record.risk_reasons) == 2


def test_deviation_record_optional_fields_default_none():
    record = DeviationRecord(**MIN_DEVIATION)
    # Optional fields like assigned_to, due_date should be absent or None
    assert getattr(record, "assigned_to", None) is None
    assert getattr(record, "due_date", None) is None


def test_deviation_record_serialises_to_dict():
    record = DeviationRecord(**MIN_DEVIATION)
    d = record.model_dump()
    assert d["deviation_id"] == "DEV-001"
    assert "risk_reasons" in d


def test_deviation_record_rejects_missing_required_field():
    bad = {k: v for k, v in MIN_DEVIATION.items() if k != "deviation_id"}
    with pytest.raises(Exception):  # pydantic ValidationError
        DeviationRecord(**bad)


# ---------------------------------------------------------------------------
# ReviewAction
# ---------------------------------------------------------------------------

def test_review_action_valid_actions():
    for action in ("acknowledge", "investigate", "close"):
        ra = ReviewAction(action=action, actor="test-user")
        assert ra.action == action


def test_review_action_rejects_invalid_action():
    with pytest.raises(Exception):
        ReviewAction(action="delete", actor="test-user")


def test_review_action_comment_is_optional():
    ra = ReviewAction(action="acknowledge", actor="analyst-1")
    assert ra.comment is None


def test_review_action_comment_stored_when_provided():
    ra = ReviewAction(action="close", actor="qa-lead", comment="Root cause confirmed.")
    assert ra.comment == "Root cause confirmed."


# ---------------------------------------------------------------------------
# AuditEventResponse
# ---------------------------------------------------------------------------

AUDIT_EVENT = {
    "id": 1,
    "deviation_id": "DEV-001",
    "action": "acknowledge",
    "actor": "analyst-1",
    "created_at": datetime(2026, 8, 12, 22, 0, 0, tzinfo=timezone.utc).isoformat(),
}


def test_audit_event_response_required_fields():
    event = AuditEventResponse(**AUDIT_EVENT)
    assert event.deviation_id == "DEV-001"
    assert event.actor == "analyst-1"


def test_audit_event_response_optional_fields_absent():
    event = AuditEventResponse(**AUDIT_EVENT)
    assert getattr(event, "comment", None) is None
    assert getattr(event, "previous_status", None) is None
    assert getattr(event, "new_status", None) is None


# ---------------------------------------------------------------------------
# AuditMiddlewareEvent (serialization round-trip)
# ---------------------------------------------------------------------------

def test_audit_middleware_event_round_trip():
    """Model serialises and deserialises without data loss."""
    payload = {
        "id": 99,
        "action": "POST /deviations/DEV-001/review",
        "actor": "system",
        "status_code": 200,
        "latency_ms": 45,
        "created_at": datetime(2026, 8, 12, 22, 0, 0, tzinfo=timezone.utc).isoformat(),
    }
    event = AuditMiddlewareEvent(**payload)
    dumped = event.model_dump()
    assert dumped["status_code"] == 200
    assert dumped["latency_ms"] == 45
