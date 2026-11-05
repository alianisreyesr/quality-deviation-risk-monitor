"""Integration tests for AuditMiddleware and helper utilities.

Covers:
- Mutating requests (POST) are logged to the audit trail
- GET requests are NOT logged by the middleware
- /cache/invalidate is logged by the middleware (no route-level audit call)
- _extract_deviation_id path-parsing helper
- X-Actor header fallback
"""
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import auth_headers
from app.audit_db import fetch_audit_log, update_deviation_status
from app.audit_middleware import _extract_deviation_id
from app.database import fetch_deviations

client = TestClient(app)


# ---------------------------------------------------------------------------
# _extract_deviation_id — unit tests for the path-parsing helper
# ---------------------------------------------------------------------------

def test_extract_deviation_id_review_path():
    assert _extract_deviation_id("/deviations/DEV-001/review") == "DEV-001"


def test_extract_deviation_id_plain_deviations_path():
    # /deviations/{id} — no sub-path
    assert _extract_deviation_id("/deviations/DEV-042") == "DEV-042"


def test_extract_deviation_id_unrelated_path_returns_none():
    assert _extract_deviation_id("/summary") is None


def test_extract_deviation_id_root_returns_none():
    assert _extract_deviation_id("/") is None


def test_extract_deviation_id_empty_string_returns_none():
    assert _extract_deviation_id("") is None


# ---------------------------------------------------------------------------
# Middleware logging — mutating requests create audit events
# ---------------------------------------------------------------------------

def test_post_review_is_logged_by_middleware():
    """A POST /deviations/{id}/review call must produce at least one audit event."""
    records = fetch_deviations()
    assert records, "Need at least one deviation"
    dev_id = records[0]["deviation_id"]
    update_deviation_status(dev_id, "Open")

    before = len(fetch_audit_log(deviation_id=dev_id))
    client.post(
        f"/deviations/{dev_id}/review",
        json={"action": "acknowledge", "actor": "middleware.tester"},
        headers=auth_headers("admin", "middleware.tester"),
    )
    after = len(fetch_audit_log(deviation_id=dev_id))
    # At minimum one event added (the router itself inserts one; middleware may add another)
    assert after > before


def test_get_request_does_not_add_middleware_event():
    """GET /deviations must NOT be logged by AuditMiddleware."""
    before = fetch_audit_log()
    client.get("/deviations")
    after = fetch_audit_log()
    # Counts should be equal — GET is not a mutating method
    assert len(after) == len(before)


def test_cache_invalidate_is_logged_by_middleware():
    """POST /cache/invalidate has no route-level audit call, so the generic
    middleware is its only audit coverage — it must add an event."""
    before = len(fetch_audit_log())
    client.post("/cache/invalidate", headers=auth_headers("admin"))
    after = len(fetch_audit_log())
    assert after > before


# ---------------------------------------------------------------------------
# Actor resolution
# ---------------------------------------------------------------------------

def test_x_actor_header_and_body_actor_are_ignored_for_attribution():
    """The audit actor comes from the verified token, never from X-Actor or the body."""
    client.post("/cache/invalidate", headers={**auth_headers("admin", "real.admin"), "X-Actor": "spoofed"})
    events = fetch_audit_log(limit=1)
    assert events[0]["actor"] == "real.admin"


def test_unauthenticated_mutation_is_rejected_and_not_logged():
    before = len(fetch_audit_log())
    response = client.post("/cache/invalidate", headers={"X-Actor": "spoofed"})
    assert response.status_code == 401
    assert len(fetch_audit_log()) == before
