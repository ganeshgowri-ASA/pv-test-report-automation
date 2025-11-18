"""Tests for utility modules."""

import unittest
import time
import tempfile
import os

from src.utils.cache import CacheManager
from src.utils.rate_limiter import RateLimiter
from src.utils.cost_tracker import CostTracker


class TestCacheManager(unittest.TestCase):
    """Test cases for cache manager."""

    def setUp(self):
        """Set up test fixtures."""
        self.cache = CacheManager(max_size=10, ttl_seconds=2)

    def test_cache_set_and_get(self):
        """Test setting and getting cache entries."""
        self.cache.set("prompt1", "model1", "response1")

        result = self.cache.get("prompt1", "model1")
        self.assertEqual(result, "response1")

    def test_cache_miss(self):
        """Test cache miss."""
        result = self.cache.get("nonexistent", "model")
        self.assertIsNone(result)

    def test_cache_expiration(self):
        """Test cache entry expiration."""
        self.cache.set("prompt", "model", "response")

        # Should be available immediately
        result = self.cache.get("prompt", "model")
        self.assertEqual(result, "response")

        # Wait for expiration
        time.sleep(3)

        # Should be expired
        result = self.cache.get("prompt", "model")
        self.assertIsNone(result)

    def test_cache_max_size(self):
        """Test cache max size enforcement."""
        cache = CacheManager(max_size=3, ttl_seconds=60)

        # Add 4 items
        for i in range(4):
            cache.set(f"prompt{i}", "model", f"response{i}")

        # Cache should only have 3 items
        stats = cache.get_stats()
        self.assertEqual(stats["size"], 3)

        # Oldest item should be evicted
        self.assertIsNone(cache.get("prompt0", "model"))

    def test_cache_stats(self):
        """Test cache statistics."""
        self.cache.set("p1", "m1", "r1")

        # Hit
        self.cache.get("p1", "m1")

        # Miss
        self.cache.get("p2", "m1")

        stats = self.cache.get_stats()

        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["hit_rate"], 0.5)

    def test_cache_clear(self):
        """Test cache clearing."""
        self.cache.set("p1", "m1", "r1")
        self.cache.set("p2", "m1", "r2")

        self.cache.clear()

        stats = self.cache.get_stats()
        self.assertEqual(stats["size"], 0)


class TestRateLimiter(unittest.TestCase):
    """Test cases for rate limiter."""

    def setUp(self):
        """Set up test fixtures."""
        self.limiter = RateLimiter(
            requests_per_minute=5,
            tokens_per_minute=1000
        )

    def test_can_proceed_initially(self):
        """Test that requests can proceed initially."""
        self.assertTrue(self.limiter.can_proceed(100))

    def test_request_limit(self):
        """Test request rate limiting."""
        # Record max requests
        for _ in range(5):
            self.limiter.record_request(100)

        # Should be at limit
        self.assertFalse(self.limiter.can_proceed(100))

    def test_token_limit(self):
        """Test token rate limiting."""
        # Use up most tokens
        self.limiter.record_request(900)

        # Should not allow request that would exceed limit
        self.assertFalse(self.limiter.can_proceed(200))

        # Should allow smaller request
        self.assertTrue(self.limiter.can_proceed(50))

    def test_stats(self):
        """Test rate limiter statistics."""
        self.limiter.record_request(100)
        self.limiter.record_request(200)

        stats = self.limiter.get_stats()

        self.assertEqual(stats["requests_this_minute"], 2)
        self.assertEqual(stats["tokens_this_minute"], 300)
        self.assertGreater(stats["requests_remaining"], 0)

    def test_reset(self):
        """Test rate limiter reset."""
        self.limiter.record_request(500)
        self.limiter.reset()

        stats = self.limiter.get_stats()
        self.assertEqual(stats["requests_this_minute"], 0)
        self.assertEqual(stats["tokens_this_minute"], 0)


class TestCostTracker(unittest.TestCase):
    """Test cases for cost tracker."""

    def setUp(self):
        """Set up test fixtures."""
        # Use temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        self.tracker = CostTracker(
            storage_path=self.temp_file.name,
            alert_threshold_usd=10.0
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_record_cost(self):
        """Test cost recording."""
        self.tracker.record_cost(
            model="gpt-4-turbo",
            prompt_tokens=1000,
            completion_tokens=500,
            cost_usd=0.025
        )

        total = self.tracker.get_total_cost()
        self.assertAlmostEqual(total, 0.025, places=4)

    def test_multiple_costs(self):
        """Test recording multiple costs."""
        costs = [0.01, 0.02, 0.03, 0.04]

        for cost in costs:
            self.tracker.record_cost(
                model="gpt-4-turbo",
                prompt_tokens=100,
                completion_tokens=50,
                cost_usd=cost
            )

        total = self.tracker.get_total_cost()
        self.assertAlmostEqual(total, sum(costs), places=4)

    def test_cost_by_model(self):
        """Test cost breakdown by model."""
        self.tracker.record_cost("gpt-4-turbo", 100, 50, 0.01)
        self.tracker.record_cost("gpt-4-turbo", 100, 50, 0.02)
        self.tracker.record_cost("gpt-3.5-turbo", 100, 50, 0.005)

        by_model = self.tracker.get_cost_by_model()

        self.assertAlmostEqual(by_model["gpt-4-turbo"], 0.03, places=4)
        self.assertAlmostEqual(by_model["gpt-3.5-turbo"], 0.005, places=4)

    def test_stats(self):
        """Test cost statistics."""
        for i in range(5):
            self.tracker.record_cost("gpt-4-turbo", 100, 50, 0.01)

        stats = self.tracker.get_stats(days=30)

        self.assertEqual(stats["total_requests"], 5)
        self.assertAlmostEqual(stats["total_cost_usd"], 0.05, places=4)
        self.assertAlmostEqual(stats["average_cost_per_request"], 0.01, places=4)

    def test_persistence(self):
        """Test cost data persistence."""
        self.tracker.record_cost("gpt-4-turbo", 100, 50, 0.01)

        # Create new tracker with same file
        new_tracker = CostTracker(storage_path=self.temp_file.name)

        total = new_tracker.get_total_cost()
        self.assertAlmostEqual(total, 0.01, places=4)


if __name__ == '__main__':
    unittest.main()
