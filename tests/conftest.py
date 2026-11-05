"""Shared pytest fixtures for the test suite."""
import os

import pytest

# Must be set before app.auth is imported (the secret is read at import time).
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-key-with-at-least-32-chars")
os.environ.setdefault("ENVIRONMENT", "test")

from app.database import initialize_database
from app.audit_db import initialize_audit_table


@pytest.fixture(scope="session", autouse=True)
def _initialize_test_database():
    """Ensure the SQLite database and audit_log table exist before any test runs.

    Required in CI environments where the database file does not already exist,
    since some tests instantiate the FastAPI TestClient without triggering the
    app's lifespan startup event.
    """
    initialize_database()
    initialize_audit_table()


@pytest.fixture(autouse=True)
def _rate_limiting_off_by_default():
    """All tests share one client IP, so limits are disabled unless a test opts in."""
    from app.rate_limit import limiter

    previous = limiter.enabled
    limiter.enabled = False
    limiter.reset()
    yield
    limiter.enabled = previous
    limiter.reset()


def auth_headers(role: str = "admin", username: str | None = None) -> dict[str, str]:
    """Bearer header for a token signed with the test secret."""
    from app.auth import Role, User, create_access_token

    name = username or f"{role}.test"
    return {"Authorization": f"Bearer {create_access_token(User(username=name, role=Role(role)))}"}
