"""Simple in-memory caching with TTL for scored deviations."""
from datetime import datetime, timezone
from typing import Any

from app.logger import setup_logger

logger = setup_logger(__name__)


class CachedScoredDeviations:
    """Thread-safe cache for scored deviations with time-to-live."""
    
    def __init__(self, ttl_seconds: int = 300):
        """Initialize cache with TTL.
        
        Args:
            ttl_seconds: Time-to-live in seconds (default: 5 minutes)
        """
        self.ttl_seconds = ttl_seconds
        self._data: list[dict[str, Any]] | None = None
        self._timestamp: datetime | None = None
    
    def is_valid(self) -> bool:
        """Check if cache is still valid.
        
        Returns:
            True if cache exists and hasn't expired, False otherwise
        """
        if self._data is None or self._timestamp is None:
            return False
        
        elapsed = (datetime.now(timezone.utc) - self._timestamp).total_seconds()
        is_fresh = elapsed < self.ttl_seconds
        
        if not is_fresh:
            logger.debug(f"Cache expired after {elapsed:.1f}s (TTL: {self.ttl_seconds}s)")
        
        return is_fresh
    
    def get(self) -> list[dict[str, Any]] | None:
        """Retrieve cached data if valid.
        
        Returns:
            Cached data if valid, None otherwise
        """
        if self.is_valid():
            logger.debug("Returning cached scored deviations")
            return self._data
        
        logger.debug("Cache miss or expired")
        return None
    
    def set(self, data: list[dict[str, Any]]) -> None:
        """Store data in cache.
        
        Args:
            data: List of scored deviation records
        """
        self._data = data
        self._timestamp = datetime.now(timezone.utc)
        logger.debug(f"Cached {len(data)} scored deviations (TTL: {self.ttl_seconds}s)")
    
    def invalidate(self) -> None:
        """Clear cache."""
        self._data = None
        self._timestamp = None
        logger.debug("Cache invalidated")


# Global cache instances — deviations and CAPA are cached independently so
# invalidating/refreshing one never discards the other.
_cache = CachedScoredDeviations(ttl_seconds=300)
_capa_cache = CachedScoredDeviations(ttl_seconds=300)


def get_cached_scored(loader_func) -> list[dict[str, Any]]:
    """Get cached scored deviations, calling loader if cache miss.

    Args:
        loader_func: Function that loads and scores deviations

    Returns:
        List of scored deviations
    """
    cached = _cache.get()
    if cached is not None:
        return cached

    # Cache miss: load and cache
    data = loader_func()
    _cache.set(data)
    return data


def get_cached_scored_capas(loader_func) -> list[dict[str, Any]]:
    """Get cached scored CAPA records, calling loader if cache miss."""
    cached = _capa_cache.get()
    if cached is not None:
        return cached

    data = loader_func()
    _capa_cache.set(data)
    return data


def invalidate_cache() -> None:
    """Manually invalidate both caches (useful for testing or refresh endpoints)."""
    _cache.invalidate()
    _capa_cache.invalidate()
