"""Shared pytest fixtures for the test suite."""
import pytest

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
