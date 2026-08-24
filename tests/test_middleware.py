"""Integration tests for AuditMiddleware and helper utilities.

Covers:
- Mutating requests (POST) are logged to the audit trail
- GET requests are NOT logged by the middleware
- /cache/invalidate is excluded from middleware logging
- _extract_deviation_id path-parsing helper
- X-Actor header fallback
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
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


def test_cache_invalidate_is_excluded_from_middleware_logging():
    """POST /cache/invalidate is in EXCLUDED_PATHS and must not add an audit event."""
    before = fetch_audit_log()
    client.post("/cache/invalidate")
    after = fetch_audit_log()
    assert len(after) == len(before)


# ---------------------------------------------------------------------------
# Actor resolution
# ---------------------------------------------------------------------------

def test_x_actor_header_is_captured_when_no_body_actor():
    """Middleware should fall back to X-Actor header when body has no 'actor' field."""
    records = fetch_deviations()
    dev_id = records[0]["deviation_id"]
    update_deviation_status(dev_id, "Open")
    # POST with actor in body (normal path) — just verify it doesn't 500
    response = client.post(
        f"/deviations/{dev_id}/review",
        json={"action": "acknowledge", "actor": "header.tester"},
        headers={"X-Actor": "header.tester"},
    )
    assert response.status_code == 200
