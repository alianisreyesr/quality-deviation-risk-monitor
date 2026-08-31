"""Integration tests for the audit trail endpoints and middleware.

Covers:
- POST /deviations/{id}/review  (acknowledge / investigate / close)
- GET  /audit-log               (full log + deviation_id filter + limit)
- AuditMiddleware               (verifies mutating requests are logged)
- Input validation              (missing actor, invalid action, bad deviation_id)
"""
from fastapi.testclient import TestClient

from app.main import app
from app.audit_db import fetch_audit_log, update_deviation_status
from app.database import fetch_deviations

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _first_deviation_id() -> str:
    """Return the deviation_id of the first record in the DB."""
    records = fetch_deviations()
    assert records, "Database is empty — cannot run audit tests"
    return records[0]["deviation_id"]


def _post_review(deviation_id: str, action: str = "acknowledge", actor: str = "test.user", comment: str | None = None) -> dict:
    payload: dict = {"action": action, "actor": actor}
    if comment:
        payload["comment"] = comment
    return client.post(f"/deviations/{deviation_id}/review", json=payload)


def _open(deviation_id: str) -> None:
    update_deviation_status(deviation_id, "Open")


# ---------------------------------------------------------------------------
# GET /audit-log — baseline
# ---------------------------------------------------------------------------

def test_audit_log_returns_200():
    response = client.get("/audit-log")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "events" in data
    assert isinstance(data["events"], list)


# ---------------------------------------------------------------------------
# POST /deviations/{id}/review — happy paths
# ---------------------------------------------------------------------------

def test_review_acknowledge_returns_200_shape():
    dev_id = _first_deviation_id()
    _open(dev_id)
    response = _post_review(dev_id, action="acknowledge", actor="qa.analyst")
    assert response.status_code == 200
    data = response.json()
    assert data["deviation_id"] == dev_id
    assert data["action"] == "acknowledge"
    assert data["actor"] == "qa.analyst"
    assert data["new_status"] == "Under Review"
    assert "previous_status" in data
    assert "event_id" in data
    assert "created_at" in data


def test_review_updates_deviation_status():
    dev_id = _first_deviation_id()
    _open(dev_id)
    _post_review(dev_id, action="investigate", actor="qa.lead")
    # Confirm the deviation's review_status changed
    records = fetch_deviations()
    target = next(r for r in records if r["deviation_id"] == dev_id)
    assert target["review_status"] == "Investigation In Progress"


def test_review_creates_audit_event():
    dev_id = _first_deviation_id()
    _open(dev_id)
    before_count = len(fetch_audit_log(deviation_id=dev_id))
    _post_review(dev_id, action="acknowledge", actor="auditor.1", comment="Initial triage")
    after_count = len(fetch_audit_log(deviation_id=dev_id))
    assert after_count == before_count + 1


def test_review_all_three_actions():
    records = fetch_deviations()
    assert len(records) >= 3, "Need at least 3 deviations to test all actions"
    actions_statuses = [
        ("acknowledge", "Under Review"),
        ("investigate", "Investigation In Progress"),
        ("close", "Closed"),
    ]
    for i, (action, expected_status) in enumerate(actions_statuses):
        dev_id = records[i]["deviation_id"]
        start = "Open" if action != "close" else "Under Review"
        update_deviation_status(dev_id, start)
        response = _post_review(dev_id, action=action, actor=f"tester.{i}")
        assert response.status_code == 200
        assert response.json()["new_status"] == expected_status


def test_review_with_comment_stored():
    dev_id = _first_deviation_id()
    _open(dev_id)
    response = _post_review(dev_id, action="acknowledge", actor="reviewer", comment="Looks critical")
    assert response.status_code == 200
    assert response.json()["comment"] == "Looks critical"


# ---------------------------------------------------------------------------
# POST /deviations/{id}/review — error paths
# ---------------------------------------------------------------------------

def test_review_invalid_deviation_returns_404():
    response = _post_review("DEV-DOES-NOT-EXIST", action="acknowledge", actor="tester")
    assert response.status_code == 404


def test_review_missing_actor_returns_422():
    dev_id = _first_deviation_id()
    response = client.post(f"/deviations/{dev_id}/review", json={"action": "acknowledge"})
    assert response.status_code == 422


def test_review_invalid_action_returns_422():
    dev_id = _first_deviation_id()
    response = client.post(
        f"/deviations/{dev_id}/review",
        json={"action": "approve", "actor": "tester"},
    )
    assert response.status_code == 422


def test_actor_max_length_validation():
    dev_id = _first_deviation_id()
    response = client.post(
        f"/deviations/{dev_id}/review",
        json={"action": "acknowledge", "actor": "x" * 101},  # max_length=100
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /audit-log — filtering and pagination
# ---------------------------------------------------------------------------

def test_audit_log_filter_by_deviation_id():
    dev_id = _first_deviation_id()
    _open(dev_id)
    # Ensure at least one event exists for this deviation
    _post_review(dev_id, action="acknowledge", actor="filter.tester")
    response = client.get(f"/audit-log?deviation_id={dev_id}")
    assert response.status_code == 200
    data = response.json()
    # Every returned event must belong to the requested deviation
    for event in data["events"]:
        assert event["deviation_id"] == dev_id


def test_audit_log_limit_param():
    response = client.get("/audit-log?limit=2")
    assert response.status_code == 200
    assert len(response.json()["events"]) <= 2


def test_audit_log_limit_above_max_returns_422():
    response = client.get("/audit-log?limit=501")
    assert response.status_code == 422


def test_audit_log_newest_first():
    dev_id = _first_deviation_id()
    _open(dev_id)
    # Post two events in sequence
    _post_review(dev_id, action="acknowledge", actor="order.a")
    _post_review(dev_id, action="investigate", actor="order.b")
    events = client.get(f"/audit-log?deviation_id={dev_id}").json()["events"]
    if len(events) >= 2:
        assert events[0]["id"] > events[1]["id"], "Audit log should be newest-first"
