"""Response caching mechanism for GPT integration."""

import hashlib
import json
import time
from typing import Optional, Any, Dict
from collections import OrderedDict
from threading import Lock


class CacheManager:
    """Manages caching of GPT responses to reduce API calls and costs."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """
        Initialize cache manager.

        Args:
            max_size: Maximum number of cached items
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def _generate_key(self, prompt: str, model: str, **kwargs) -> str:
        """Generate cache key from request parameters."""
        cache_data = {
            "prompt": prompt,
            "model": model,
            **kwargs
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()

    def get(self, prompt: str, model: str, **kwargs) -> Optional[Any]:
        """
        Retrieve cached response.

        Args:
            prompt: The prompt string
            model: The model name
            **kwargs: Additional parameters that affect the response

        Returns:
            Cached response if found and not expired, None otherwise
        """
        key = self._generate_key(prompt, model, **kwargs)

        with self._lock:
            if key in self._cache:
                entry = self._cache[key]

                # Check if entry has expired
                if time.time() - entry["timestamp"] > self.ttl_seconds:
                    del self._cache[key]
                    self._misses += 1
                    return None

                # Move to end (most recently used)
                self._cache.move_to_end(key)
                self._hits += 1
                return entry["response"]

            self._misses += 1
            return None

    def set(self, prompt: str, model: str, response: Any, **kwargs) -> None:
        """
        Store response in cache.

        Args:
            prompt: The prompt string
            model: The model name
            response: The response to cache
            **kwargs: Additional parameters that affect the response
        """
        key = self._generate_key(prompt, model, **kwargs)

        with self._lock:
            # Remove oldest entry if at max size
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._cache.popitem(last=False)

            self._cache[key] = {
                "response": response,
                "timestamp": time.time()
            }
            self._cache.move_to_end(key)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "ttl_seconds": self.ttl_seconds
        }

    def invalidate_expired(self) -> int:
        """Remove all expired entries. Returns number of entries removed."""
        current_time = time.time()
        expired_keys = []

        with self._lock:
            for key, entry in self._cache.items():
                if current_time - entry["timestamp"] > self.ttl_seconds:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]

        return len(expired_keys)
