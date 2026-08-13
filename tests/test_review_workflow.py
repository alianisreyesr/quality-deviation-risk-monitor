"""Tests for reviewer workflow state-transition validation (Issue #4).

Covers:
- Valid transitions: Open→acknowledge, Open→investigate, UnderReview→investigate,
  UnderReview→close, InvestigationInProgress→close
- Blocked transitions: 409 Conflict responses with detail payload
- Terminal state: Closed deviations reject all actions
- GET /deviations/{id}/audit-trail — happy path and 404
- Input validation: missing actor (422), invalid action (422)
- Comment stored and returned
- Audit event created on every successful transition
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.audit_db import fetch_audit_log, update_deviation_status
from app.database import fetch_deviations

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deviation_id_by_status(status: str) -> str | None:
    """Find a deviation currently in the given review_status, or None."""
    for r in fetch_deviations():
        if r["review_status"] == status:
            return r["deviation_id"]
    return None


def _force_status(deviation_id: str, status: str) -> None:
    """Directly set a deviation to a specific status for test setup."""
    update_deviation_status(deviation_id, status)


def _review(deviation_id: str, action: str, actor: str = "test.user", comment: str | None = None) -> dict:
    payload: dict = {"action": action, "actor": actor}
    if comment:
        payload["comment"] = comment
    return client.post(f"/deviations/{deviation_id}/review", json=payload)


def _first_id() -> str:
    records = fetch_deviations()
    assert records, "Database is empty"
    return records[0]["deviation_id"]


def _id_at(index: int) -> str:
    records = fetch_deviations()
    assert len(records) > index
    return records[index]["deviation_id"]


# ---------------------------------------------------------------------------
# Valid transitions
# ---------------------------------------------------------------------------

def test_open_to_acknowledge_succeeds():
    dev_id = _id_at(0)
    _force_status(dev_id, "Open")
    r = _review(dev_id, "acknowledge", actor="qa.analyst")
    assert r.status_code == 200
    assert r.json()["new_status"] == "Under Review"


def test_open_to_investigate_succeeds():
    dev_id = _id_at(1)
    _force_status(dev_id, "Open")
    r = _review(dev_id, "investigate", actor="qa.lead")
    assert r.status_code == 200
    assert r.json()["new_status"] == "Investigation In Progress"


def test_under_review_to_investigate_succeeds():
    dev_id = _id_at(2)
    _force_status(dev_id, "Under Review")
    r = _review(dev_id, "investigate", actor="qa.lead")
    assert r.status_code == 200
    assert r.json()["new_status"] == "Investigation In Progress"


def test_under_review_to_close_succeeds():
    dev_id = _id_at(3)
    _force_status(dev_id, "Under Review")
    r = _review(dev_id, "close", actor="qa.manager")
    assert r.status_code == 200
    assert r.json()["new_status"] == "Closed"


def test_investigation_in_progress_to_close_succeeds():
    dev_id = _id_at(4)
    _force_status(dev_id, "Investigation In Progress")
    r = _review(dev_id, "close", actor="qa.director")
    assert r.status_code == 200
    assert r.json()["new_status"] == "Closed"


# ---------------------------------------------------------------------------
# Blocked transitions — expect 409 Conflict
# ---------------------------------------------------------------------------

def test_closed_acknowledge_returns_409():
    dev_id = _id_at(5)
    _force_status(dev_id, "Closed")
    r = _review(dev_id, "acknowledge", actor="tester")
    assert r.status_code == 409


def test_closed_investigate_returns_409():
    dev_id = _id_at(6)
    _force_status(dev_id, "Closed")
    r = _review(dev_id, "investigate", actor="tester")
    assert r.status_code == 409


def test_closed_close_returns_409():
    dev_id = _id_at(7)
    _force_status(dev_id, "Closed")
    r = _review(dev_id, "close", actor="tester")
    assert r.status_code == 409


def test_under_review_acknowledge_returns_409():
    """Re-acknowledging an already-Under-Review deviation is not permitted."""
    dev_id = _id_at(8)
    _force_status(dev_id, "Under Review")
    r = _review(dev_id, "acknowledge", actor="tester")
    assert r.status_code == 409


def test_investigation_in_progress_acknowledge_returns_409():
    dev_id = _id_at(9)
    _force_status(dev_id, "Investigation In Progress")
    r = _review(dev_id, "acknowledge", actor="tester")
    assert r.status_code == 409


def test_investigation_in_progress_investigate_returns_409():
    """Cannot re-investigate a deviation already in investigation."""
    dev_id = _id_at(10)
    _force_status(dev_id, "Investigation In Progress")
    r = _review(dev_id, "investigate", actor="tester")
    assert r.status_code == 409


# ---------------------------------------------------------------------------
# 409 response body validation
# ---------------------------------------------------------------------------

def test_409_response_contains_transition_detail():
    dev_id = _id_at(11)
    _force_status(dev_id, "Closed")
    r = _review(dev_id, "acknowledge", actor="tester")
    assert r.status_code == 409
    body = r.json()["detail"]
    assert body["deviation_id"] == dev_id
    assert body["current_status"] == "Closed"
    assert body["requested_action"] == "acknowledge"
    assert body["allowed_actions"] == []  # Closed is terminal


def test_409_allowed_actions_for_under_review():
    dev_id = _id_at(12)
    _force_status(dev_id, "Under Review")
    r = _review(dev_id, "acknowledge", actor="tester")
    assert r.status_code == 409
    body = r.json()["detail"]
    assert set(body["allowed_actions"]) == {"investigate", "close"}


# ---------------------------------------------------------------------------
# GET /deviations/{id}/audit-trail
# ---------------------------------------------------------------------------

def test_audit_trail_endpoint_returns_200():
    dev_id = _first_id()
    r = client.get(f"/deviations/{dev_id}/audit-trail")
    assert r.status_code == 200
    data = r.json()
    assert data["deviation_id"] == dev_id
    assert "current_review_status" in data
    assert "event_count" in data
    assert isinstance(data["events"], list)
    assert data["event_count"] == len(data["events"])


def test_audit_trail_not_found_returns_404():
    r = client.get("/deviations/DEV-DOES-NOT-EXIST/audit-trail")
    assert r.status_code == 404


def test_audit_trail_reflects_new_event():
    dev_id = _id_at(0)
    _force_status(dev_id, "Open")
    before = client.get(f"/deviations/{dev_id}/audit-trail").json()["event_count"]
    _review(dev_id, "acknowledge", actor="trail.tester")
    after = client.get(f"/deviations/{dev_id}/audit-trail").json()["event_count"]
    assert after == before + 1


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def test_missing_actor_returns_422():
    dev_id = _first_id()
    r = client.post(f"/deviations/{dev_id}/review", json={"action": "acknowledge"})
    assert r.status_code == 422


def test_invalid_action_returns_422():
    dev_id = _first_id()
    r = client.post(f"/deviations/{dev_id}/review", json={"action": "approve", "actor": "x"})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Comment handling
# ---------------------------------------------------------------------------

def test_comment_stored_and_returned():
    dev_id = _id_at(0)
    _force_status(dev_id, "Open")
    r = _review(dev_id, "acknowledge", actor="reviewer", comment="Priority escalation")
    assert r.status_code == 200
    assert r.json()["comment"] == "Priority escalation"


# ---------------------------------------------------------------------------
# Audit event created on success
# ---------------------------------------------------------------------------

def test_successful_transition_creates_audit_event():
    dev_id = _id_at(1)
    _force_status(dev_id, "Open")
    before = len(fetch_audit_log(deviation_id=dev_id))
    _review(dev_id, "acknowledge", actor="event.checker")
    after = len(fetch_audit_log(deviation_id=dev_id))
    assert after == before + 1


def test_blocked_transition_does_not_create_audit_event():
    """A 409 rejection must not write to the audit log."""
    dev_id = _id_at(2)
    _force_status(dev_id, "Closed")
    before = len(fetch_audit_log(deviation_id=dev_id))
    _review(dev_id, "acknowledge", actor="blocked.tester")
    after = len(fetch_audit_log(deviation_id=dev_id))
    assert after == before  # no new event for a blocked transition
