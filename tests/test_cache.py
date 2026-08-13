"""Unit tests for the in-memory CachedScoredDeviations class and helpers.

Covers:
- CachedScoredDeviations.is_valid()  (empty / fresh / expired)
- CachedScoredDeviations.get() / set() / invalidate()
- get_cached_scored()  (cache-hit and cache-miss paths)
- POST /cache/invalidate  endpoint
"""
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.cache import CachedScoredDeviations, get_cached_scored, invalidate_cache
from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# CachedScoredDeviations — unit-level
# ---------------------------------------------------------------------------

def test_empty_cache_is_not_valid():
    cache = CachedScoredDeviations(ttl_seconds=300)
    assert cache.is_valid() is False


def test_cache_get_returns_none_when_empty():
    cache = CachedScoredDeviations(ttl_seconds=300)
    assert cache.get() is None


def test_cache_set_then_get_returns_data():
    cache = CachedScoredDeviations(ttl_seconds=300)
    sample = [{"deviation_id": "DEV-001", "risk_level": "High"}]
    cache.set(sample)
    assert cache.is_valid() is True
    assert cache.get() == sample


def test_cache_invalidate_clears_data():
    cache = CachedScoredDeviations(ttl_seconds=300)
    cache.set([{"deviation_id": "DEV-002"}])
    cache.invalidate()
    assert cache.is_valid() is False
    assert cache.get() is None


def test_expired_cache_returns_none():
    cache = CachedScoredDeviations(ttl_seconds=1)
    cache.set([{"deviation_id": "DEV-003"}])
    # Simulate expiry by backdating the timestamp
    cache._timestamp = datetime.now() - timedelta(seconds=10)
    assert cache.is_valid() is False
    assert cache.get() is None


def test_cache_returns_same_reference_on_hit():
    cache = CachedScoredDeviations(ttl_seconds=300)
    data = [{"deviation_id": "DEV-004"}]
    cache.set(data)
    result = cache.get()
    assert result is data


# ---------------------------------------------------------------------------
# get_cached_scored — loader function integration
# ---------------------------------------------------------------------------

def test_get_cached_scored_calls_loader_on_miss():
    invalidate_cache()  # ensure clean state
    loader = MagicMock(return_value=[{"deviation_id": "DEV-005"}])
    result = get_cached_scored(loader)
    loader.assert_called_once()
    assert result == [{"deviation_id": "DEV-005"}]


def test_get_cached_scored_does_not_call_loader_on_hit():
    invalidate_cache()
    loader = MagicMock(return_value=[{"deviation_id": "DEV-006"}])
    get_cached_scored(loader)  # first call — miss
    loader.reset_mock()
    get_cached_scored(loader)  # second call — hit
    loader.assert_not_called()


# ---------------------------------------------------------------------------
# POST /cache/invalidate — endpoint
# ---------------------------------------------------------------------------

def test_cache_invalidate_endpoint_returns_200():
    response = client.post("/cache/invalidate")
    assert response.status_code == 200


def test_cache_invalidate_endpoint_response_shape():
    response = client.post("/cache/invalidate")
    data = response.json()
    assert "message" in data or "status" in data or "detail" in data
