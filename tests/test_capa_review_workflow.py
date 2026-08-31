"""Tests for CAPA reviewer workflow state-transition validation (Issue #40).

Mirrors tests/test_review_workflow.py for deviations. Covers:
- Valid transitions: Open→start, In Progress→submit_for_effectiveness_check,
  In Progress→close, Pending Effectiveness Check→close
- Blocked transitions: 409 Conflict responses with detail payload
- Terminal state: Closed CAPAs reject all actions
- Effectiveness-check hard gate: closing without
  effectiveness_check_complete=true returns 409, even when the transition
  itself is otherwise allowed
- GET /capas/{id}/audit-trail — happy path and 404
- Input validation: missing actor (422), invalid action (422)
- Comment stored and returned
- Audit event created on every successful transition, not on blocked ones
"""
from fastapi.testclient import TestClient

from app.audit_db import fetch_audit_log, update_capa_status
from app.config import DATABASE_FILE
from app.database import connection, fetch_capas
from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _force_capa(capa_id: str, status: str, effectiveness_check_complete: bool | None = None) -> None:
    """Directly set a CAPA's status (and optionally its effectiveness-check
    flag) for test setup."""
    update_capa_status(capa_id, status)
    if effectiveness_check_complete is not None:
        with connection(DATABASE_FILE) as conn:
            conn.execute(
                "UPDATE capas SET effectiveness_check_complete = ? WHERE capa_id = ?",
                (1 if effectiveness_check_complete else 0, capa_id),
            )
            conn.commit()


def _review(capa_id: str, action: str, actor: str = "test.user", comment: str | None = None) -> dict:
    payload: dict = {"action": action, "actor": actor}
    if comment:
        payload["comment"] = comment
    return client.post(f"/capas/{capa_id}/review", json=payload)


def _id_at(index: int) -> str:
    records = fetch_capas()
    assert len(records) > index, "Not enough CAPA records seeded for this test"
    return records[index]["capa_id"]


# ---------------------------------------------------------------------------
# Valid transitions
# ---------------------------------------------------------------------------

def test_open_to_start_succeeds():
    capa_id = _id_at(0)
    _force_capa(capa_id, "Open")
    r = _review(capa_id, "start", actor="qa.analyst")
    assert r.status_code == 200
    assert r.json()["new_status"] == "In Progress"


def test_in_progress_to_submit_for_effectiveness_check_succeeds():
    capa_id = _id_at(1)
    _force_capa(capa_id, "In Progress")
    r = _review(capa_id, "submit_for_effectiveness_check", actor="qa.lead")
    assert r.status_code == 200
    assert r.json()["new_status"] == "Pending Effectiveness Check"


def test_in_progress_to_close_succeeds_when_effectiveness_check_complete():
    capa_id = _id_at(2)
    _force_capa(capa_id, "In Progress", effectiveness_check_complete=True)
    r = _review(capa_id, "close", actor="qa.manager")
    assert r.status_code == 200
    assert r.json()["new_status"] == "Closed"


def test_pending_effectiveness_check_to_close_succeeds_when_complete():
    capa_id = _id_at(3)
    _force_capa(capa_id, "Pending Effectiveness Check", effectiveness_check_complete=True)
    r = _review(capa_id, "close", actor="qa.director")
    assert r.status_code == 200
    assert r.json()["new_status"] == "Closed"


# ---------------------------------------------------------------------------
# Blocked transitions — expect 409 Conflict
# ---------------------------------------------------------------------------

def test_closed_start_returns_409():
    capa_id = _id_at(4)
    _force_capa(capa_id, "Closed", effectiveness_check_complete=True)
    r = _review(capa_id, "start", actor="tester")
    assert r.status_code == 409


def test_closed_close_returns_409():
    capa_id = _id_at(5)
    _force_capa(capa_id, "Closed", effectiveness_check_complete=True)
    r = _review(capa_id, "close", actor="tester")
    assert r.status_code == 409


def test_open_close_returns_409():
    """Cannot skip straight from Open to Closed."""
    capa_id = _id_at(6)
    _force_capa(capa_id, "Open", effectiveness_check_complete=True)
    r = _review(capa_id, "close", actor="tester")
    assert r.status_code == 409


def test_open_submit_for_effectiveness_check_returns_409():
    capa_id = _id_at(7)
    _force_capa(capa_id, "Open")
    r = _review(capa_id, "submit_for_effectiveness_check", actor="tester")
    assert r.status_code == 409


def test_pending_effectiveness_check_start_returns_409():
    capa_id = _id_at(8)
    _force_capa(capa_id, "Pending Effectiveness Check")
    r = _review(capa_id, "start", actor="tester")
    assert r.status_code == 409


# ---------------------------------------------------------------------------
# Effectiveness-check hard gate
# ---------------------------------------------------------------------------

def test_close_blocked_when_effectiveness_check_incomplete_from_in_progress():
    capa_id = _id_at(9)
    _force_capa(capa_id, "In Progress", effectiveness_check_complete=False)
    r = _review(capa_id, "close", actor="tester")
    assert r.status_code == 409
    body = r.json()["detail"]
    assert body["capa_id"] == capa_id
    assert body["requested_action"] == "close"


def test_close_blocked_when_effectiveness_check_incomplete_from_pending():
    capa_id = _id_at(10)
    _force_capa(capa_id, "Pending Effectiveness Check", effectiveness_check_complete=False)
    r = _review(capa_id, "close", actor="tester")
    assert r.status_code == 409


def test_close_blocked_does_not_change_status():
    capa_id = _id_at(11)
    _force_capa(capa_id, "Pending Effectiveness Check", effectiveness_check_complete=False)
    _review(capa_id, "close", actor="tester")
    record = next(r for r in fetch_capas() if r["capa_id"] == capa_id)
    assert record["status"] == "Pending Effectiveness Check"


def test_close_blocked_does_not_create_audit_event():
    capa_id = _id_at(12)
    _force_capa(capa_id, "In Progress", effectiveness_check_complete=False)
    before = len(fetch_audit_log(capa_id=capa_id))
    _review(capa_id, "close", actor="tester")
    after = len(fetch_audit_log(capa_id=capa_id))
    assert after == before


# ---------------------------------------------------------------------------
# 409 response body validation
# ---------------------------------------------------------------------------

def test_409_response_contains_transition_detail():
    capa_id = _id_at(13)
    _force_capa(capa_id, "Closed", effectiveness_check_complete=True)
    r = _review(capa_id, "start", actor="tester")
    assert r.status_code == 409
    body = r.json()["detail"]
    assert body["capa_id"] == capa_id
    assert body["current_status"] == "Closed"
    assert body["requested_action"] == "start"
    assert body["allowed_actions"] == []  # Closed is terminal


def test_409_allowed_actions_for_in_progress():
    capa_id = _id_at(14)
    _force_capa(capa_id, "In Progress", effectiveness_check_complete=True)
    r = _review(capa_id, "start", actor="tester")
    assert r.status_code == 409
    body = r.json()["detail"]
    assert set(body["allowed_actions"]) == {"submit_for_effectiveness_check", "close"}


# ---------------------------------------------------------------------------
# GET /capas/{id}/audit-trail
# ---------------------------------------------------------------------------

def test_capa_audit_trail_endpoint_returns_200():
    capa_id = _id_at(0)
    r = client.get(f"/capas/{capa_id}/audit-trail")
    assert r.status_code == 200
    data = r.json()
    assert data["capa_id"] == capa_id
    assert "current_status" in data
    assert "event_count" in data
    assert isinstance(data["events"], list)
    assert data["event_count"] == len(data["events"])


def test_capa_audit_trail_not_found_returns_404():
    r = client.get("/capas/CAPA-DOES-NOT-EXIST/audit-trail")
    assert r.status_code == 404


def test_capa_audit_trail_reflects_new_event():
    capa_id = _id_at(0)
    _force_capa(capa_id, "Open")
    before = client.get(f"/capas/{capa_id}/audit-trail").json()["event_count"]
    _review(capa_id, "start", actor="trail.tester")
    after = client.get(f"/capas/{capa_id}/audit-trail").json()["event_count"]
    assert after == before + 1


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def test_missing_actor_returns_422():
    capa_id = _id_at(0)
    r = client.post(f"/capas/{capa_id}/review", json={"action": "start"})
    assert r.status_code == 422


def test_invalid_action_returns_422():
    capa_id = _id_at(0)
    r = client.post(f"/capas/{capa_id}/review", json={"action": "approve", "actor": "x"})
    assert r.status_code == 422


def test_review_unknown_capa_returns_404():
    r = client.post(
        "/capas/CAPA-DOES-NOT-EXIST/review",
        json={"action": "start", "actor": "tester"},
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Comment handling
# ---------------------------------------------------------------------------

def test_comment_stored_and_returned():
    capa_id = _id_at(1)
    _force_capa(capa_id, "Open")
    r = _review(capa_id, "start", actor="reviewer", comment="Kicking off remediation")
    assert r.status_code == 200
    assert r.json()["comment"] == "Kicking off remediation"


# ---------------------------------------------------------------------------
# Audit event created on success
# ---------------------------------------------------------------------------

def test_successful_transition_creates_audit_event():
    capa_id = _id_at(2)
    _force_capa(capa_id, "Open")
    before = len(fetch_audit_log(capa_id=capa_id))
    _review(capa_id, "start", actor="event.checker")
    after = len(fetch_audit_log(capa_id=capa_id))
    assert after == before + 1


def test_blocked_transition_does_not_create_audit_event():
    """A 409 rejection must not write to the audit log."""
    capa_id = _id_at(3)
    _force_capa(capa_id, "Closed", effectiveness_check_complete=True)
    before = len(fetch_audit_log(capa_id=capa_id))
    _review(capa_id, "start", actor="blocked.tester")
    after = len(fetch_audit_log(capa_id=capa_id))
    assert after == before


def test_capa_audit_events_are_isolated_from_deviation_audit_events():
    """CAPA review events must not leak into deviation-scoped audit queries."""
    capa_id = _id_at(4)
    _force_capa(capa_id, "Open")
    _review(capa_id, "start", actor="isolation.tester")
    # No deviation shares an id with this CAPA, so filtering the general
    # audit log by this capa_id must return only capa-scoped rows.
    events = fetch_audit_log(capa_id=capa_id)
    assert all(e["capa_id"] == capa_id for e in events)
    assert all(e["deviation_id"] is None for e in events)
