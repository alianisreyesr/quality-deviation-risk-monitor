"""Shared pytest fixtures for the test suite."""
import pytest

from app.database import initialize_database


@pytest.fixture(scope="session", autouse=True)
def _initialize_test_database():
    """Ensure the SQLite database is initialized before any test runs.

    This is required in CI environments where the database file does not
    already exist, since some tests instantiate the FastAPI TestClient
    without triggering the app's lifespan startup event.
    """
    initialize_database()
