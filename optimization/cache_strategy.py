"""
Caching strategy implementation and utilities.
"""
from functools import wraps
from typing import Any, Callable, Optional
import time
import hashlib
import json
from datetime import datetime, timedelta


class CacheManager:
    """Simple in-memory cache manager."""

    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache manager.

        Args:
            default_ttl: Default time-to-live in seconds
        """
        self._cache = {}
        self._timestamps = {}
        self.default_ttl = default_ttl
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }

    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            self.stats["misses"] += 1
            return None

        # Check if expired
        if key in self._timestamps:
            timestamp, ttl = self._timestamps[key]
            if time.time() - timestamp > ttl:
                # Expired
                del self._cache[key]
                del self._timestamps[key]
                self.stats["misses"] += 1
                self.stats["evictions"] += 1
                return None

        self.stats["hits"] += 1
        return self._cache[key]

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
        """
        self._cache[key] = value
        self._timestamps[key] = (time.time(), ttl or self.default_ttl)

    def delete(self, key: str):
        """Delete key from cache."""
        if key in self._cache:
            del self._cache[key]
            if key in self._timestamps:
                del self._timestamps[key]

    def clear(self):
        """Clear all cache."""
        self._cache.clear()
        self._timestamps.clear()
        self.stats["evictions"] += len(self._cache)

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total * 100) if total > 0 else 0

        return {
            **self.stats,
            "hit_rate": hit_rate,
            "size": len(self._cache)
        }


# Global cache instance
_cache = CacheManager()


def cached(ttl: int = 300):
    """
    Decorator for caching function results.

    Args:
        ttl: Time-to-live in seconds

    Example:
        @cached(ttl=600)
        def expensive_function(param1, param2):
            # ... expensive computation
            return result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__module__}.{func.__name__}:" + \
                       _cache._generate_key(*args, **kwargs)

            # Try to get from cache
            result = _cache.get(cache_key)
            if result is not None:
                return result

            # Execute function
            result = func(*args, **kwargs)

            # Store in cache
            _cache.set(cache_key, result, ttl)

            return result

        # Add cache management methods to function
        wrapper.cache_clear = lambda: _cache.clear()
        wrapper.cache_stats = lambda: _cache.get_stats()

        return wrapper

    return decorator


class QueryCache:
    """Database query result cache."""

    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl
        self.cache = CacheManager(default_ttl=ttl)

    def get_query_result(self, query: str, params: tuple = ()) -> Optional[Any]:
        """Get cached query result."""
        key = self._make_query_key(query, params)
        return self.cache.get(key)

    def set_query_result(self, query: str, params: tuple, result: Any):
        """Cache query result."""
        key = self._make_query_key(query, params)

        # Implement LRU eviction if cache is full
        if len(self.cache._cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache._timestamps.keys(),
                           key=lambda k: self.cache._timestamps[k][0])
            self.cache.delete(oldest_key)

        self.cache.set(key, result)

    def _make_query_key(self, query: str, params: tuple) -> str:
        """Generate cache key for query."""
        return hashlib.md5(f"{query}:{params}".encode()).hexdigest()

    def invalidate_table(self, table_name: str):
        """Invalidate all queries involving a table."""
        # Simple implementation: clear all
        # More sophisticated version would track which queries use which tables
        self.cache.clear()


class ReportCache:
    """Cache for generated reports."""

    def __init__(self, cache_dir: str = "/tmp/report_cache"):
        self.cache_dir = cache_dir
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        from pathlib import Path
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)

    def get_cached_report(self, report_id: str, format: str) -> Optional[bytes]:
        """Get cached report file."""
        from pathlib import Path

        cache_file = Path(self.cache_dir) / f"{report_id}_{format}.cache"

        if not cache_file.exists():
            return None

        # Check if cache is stale (older than 1 hour)
        mtime = cache_file.stat().st_mtime
        if time.time() - mtime > 3600:
            cache_file.unlink()
            return None

        return cache_file.read_bytes()

    def cache_report(self, report_id: str, format: str, content: bytes):
        """Cache report file."""
        from pathlib import Path

        cache_file = Path(self.cache_dir) / f"{report_id}_{format}.cache"
        cache_file.write_bytes(content)

    def clear_report_cache(self, report_id: str):
        """Clear cached reports for a specific report ID."""
        from pathlib import Path

        cache_dir = Path(self.cache_dir)
        for cache_file in cache_dir.glob(f"{report_id}_*.cache"):
            cache_file.unlink()


# Example usage functions
def example_cached_function():
    """Example of using the cached decorator."""

    @cached(ttl=600)
    def get_equipment_list(status: str = "CALIBRATED"):
        """Expensive database query."""
        print("Executing expensive query...")
        time.sleep(1)  # Simulate slow query
        return [
            {"id": 1, "name": "Equipment 1", "status": status},
            {"id": 2, "name": "Equipment 2", "status": status}
        ]

    # First call - cache miss
    print("First call:")
    result1 = get_equipment_list("CALIBRATED")
    print(f"Result: {result1}")

    # Second call - cache hit
    print("\nSecond call:")
    result2 = get_equipment_list("CALIBRATED")
    print(f"Result: {result2}")

    # Check cache stats
    print(f"\nCache stats: {get_equipment_list.cache_stats()}")


def print_cache_statistics():
    """Print cache statistics."""
    stats = _cache.get_stats()

    print("\nCACHE STATISTICS")
    print("=" * 50)
    print(f"Cache Hits:      {stats['hits']}")
    print(f"Cache Misses:    {stats['misses']}")
    print(f"Hit Rate:        {stats['hit_rate']:.2f}%")
    print(f"Cache Size:      {stats['size']} entries")
    print(f"Evictions:       {stats['evictions']}")


if __name__ == "__main__":
    print("Running cache strategy examples...\n")
    example_cached_function()
    print_cache_statistics()
