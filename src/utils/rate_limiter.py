"""Rate limiting for GPT API calls."""

import time
from typing import Optional
from threading import Lock
from collections import deque
from datetime import datetime, timedelta


class RateLimiter:
    """Rate limiter to prevent exceeding API limits."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        tokens_per_minute: int = 90000
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute
            tokens_per_minute: Maximum tokens per minute
        """
        self.requests_per_minute = requests_per_minute
        self.tokens_per_minute = tokens_per_minute

        self._request_times: deque = deque()
        self._token_usage: deque = deque()
        self._lock = Lock()

    def _clean_old_entries(self, queue: deque, window_seconds: int = 60) -> None:
        """Remove entries older than the time window."""
        cutoff_time = time.time() - window_seconds
        while queue and queue[0]["timestamp"] < cutoff_time:
            queue.popleft()

    def can_proceed(self, estimated_tokens: int = 0) -> bool:
        """
        Check if request can proceed without exceeding limits.

        Args:
            estimated_tokens: Estimated tokens for the request

        Returns:
            True if request can proceed, False otherwise
        """
        with self._lock:
            self._clean_old_entries(self._request_times)
            self._clean_old_entries(self._token_usage)

            # Check request limit
            if len(self._request_times) >= self.requests_per_minute:
                return False

            # Check token limit
            if estimated_tokens > 0:
                current_tokens = sum(
                    entry["tokens"] for entry in self._token_usage
                )
                if current_tokens + estimated_tokens > self.tokens_per_minute:
                    return False

            return True

    def wait_if_needed(self, estimated_tokens: int = 0) -> float:
        """
        Wait if necessary to comply with rate limits.

        Args:
            estimated_tokens: Estimated tokens for the request

        Returns:
            Time waited in seconds
        """
        wait_time = 0.0

        while not self.can_proceed(estimated_tokens):
            time.sleep(0.1)
            wait_time += 0.1

        return wait_time

    def record_request(self, tokens_used: int = 0) -> None:
        """
        Record a request and token usage.

        Args:
            tokens_used: Actual tokens used in the request
        """
        current_time = time.time()

        with self._lock:
            self._request_times.append({"timestamp": current_time})

            if tokens_used > 0:
                self._token_usage.append({
                    "timestamp": current_time,
                    "tokens": tokens_used
                })

    def get_stats(self) -> dict:
        """Get current rate limiter statistics."""
        with self._lock:
            self._clean_old_entries(self._request_times)
            self._clean_old_entries(self._token_usage)

            current_requests = len(self._request_times)
            current_tokens = sum(
                entry["tokens"] for entry in self._token_usage
            )

            return {
                "requests_this_minute": current_requests,
                "requests_limit": self.requests_per_minute,
                "requests_remaining": max(
                    0,
                    self.requests_per_minute - current_requests
                ),
                "tokens_this_minute": current_tokens,
                "tokens_limit": self.tokens_per_minute,
                "tokens_remaining": max(
                    0,
                    self.tokens_per_minute - current_tokens
                ),
            }

    def reset(self) -> None:
        """Reset rate limiter."""
        with self._lock:
            self._request_times.clear()
            self._token_usage.clear()
