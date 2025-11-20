"""
Unit tests for LLM Configuration Module
"""

import pytest
import tempfile
from pathlib import Path
import json
import time
from datetime import datetime, timedelta

from ..llm_config import (
    LLMConfig,
    LLMProvider,
    ModelType,
    ModelConfig,
    RateLimitConfig,
    RateLimiter,
    UsageStats,
    get_config,
    set_config
)


class TestModelConfig:
    """Test ModelConfig dataclass."""

    def test_model_config_creation(self):
        """Test creating a model configuration."""
        config = ModelConfig(
            name="test-model",
            provider=LLMProvider.OPENAI,
            max_tokens=4096,
            cost_per_1k_input=0.01,
            cost_per_1k_output=0.03
        )

        assert config.name == "test-model"
        assert config.provider == LLMProvider.OPENAI
        assert config.max_tokens == 4096
        assert config.cost_per_1k_input == 0.01
        assert config.cost_per_1k_output == 0.03


class TestRateLimiter:
    """Test RateLimiter functionality."""

    def test_rate_limiter_allows_initial_request(self):
        """Test that initial request is allowed."""
        config = RateLimitConfig(requests_per_minute=10, tokens_per_minute=1000)
        limiter = RateLimiter(config)

        allowed, wait_time = limiter.check_rate_limit(100)
        assert allowed is True
        assert wait_time is None

    def test_rate_limiter_records_request(self):
        """Test recording requests."""
        config = RateLimitConfig(requests_per_minute=10, tokens_per_minute=1000)
        limiter = RateLimiter(config)

        limiter.record_request(100)
        assert len(limiter.request_timestamps) == 1
        assert len(limiter.token_usage) == 1

    def test_rate_limiter_blocks_excessive_requests(self):
        """Test that excessive requests are blocked."""
        config = RateLimitConfig(requests_per_minute=2, tokens_per_minute=1000)
        limiter = RateLimiter(config)

        # Record maximum allowed requests
        limiter.record_request(100)
        limiter.record_request(100)

        # Next request should be blocked
        allowed, wait_time = limiter.check_rate_limit(100)
        assert allowed is False
        assert wait_time is not None
        assert wait_time > 0

    def test_rate_limiter_blocks_excessive_tokens(self):
        """Test that excessive tokens are blocked."""
        config = RateLimitConfig(requests_per_minute=100, tokens_per_minute=500)
        limiter = RateLimiter(config)

        limiter.record_request(400)

        # Next request with 200 tokens should be blocked
        allowed, wait_time = limiter.check_rate_limit(200)
        assert allowed is False
        assert wait_time is not None


class TestUsageStats:
    """Test UsageStats functionality."""

    def test_usage_stats_initialization(self):
        """Test usage stats initialization."""
        stats = UsageStats()

        assert stats.total_requests == 0
        assert stats.total_tokens_input == 0
        assert stats.total_tokens_output == 0
        assert stats.total_cost == 0.0
        assert stats.errors == 0
        assert stats.cache_hits == 0
        assert stats.cache_misses == 0

    def test_usage_stats_reset(self):
        """Test resetting usage stats."""
        stats = UsageStats()
        stats.total_requests = 10
        stats.total_cost = 5.0

        stats.reset()

        assert stats.total_requests == 0
        assert stats.total_cost == 0.0

    def test_usage_stats_to_dict(self):
        """Test converting usage stats to dictionary."""
        stats = UsageStats()
        stats.total_requests = 5
        stats.total_cost = 2.5

        data = stats.to_dict()

        assert data['total_requests'] == 5
        assert data['total_cost'] == 2.5
        assert 'last_reset' in data


class TestLLMConfig:
    """Test LLMConfig functionality."""

    def test_config_initialization(self):
        """Test config initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            cache_dir = Path(tmpdir) / "cache"

            config = LLMConfig(config_file=config_file, cache_dir=cache_dir)

            assert config.config_file == config_file
            assert config.cache_dir == cache_dir
            assert cache_dir.exists()

    def test_get_model_config(self):
        """Test getting model configuration."""
        config = LLMConfig()

        gpt4_config = config.get_model_config(ModelType.GPT_4_TURBO)

        assert gpt4_config.name == "gpt-4-turbo-preview"
        assert gpt4_config.provider == LLMProvider.OPENAI
        assert gpt4_config.supports_vision is True

    def test_set_and_get_api_key(self):
        """Test setting and getting API keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            config = LLMConfig(config_file=config_file)

            test_key = "test-api-key-123"
            config.set_api_key(LLMProvider.OPENAI, test_key)

            retrieved_key = config.get_api_key(LLMProvider.OPENAI)
            assert retrieved_key == test_key

            # Verify it was saved to file
            assert config_file.exists()
            with open(config_file, 'r') as f:
                saved_data = json.load(f)
                assert saved_data['api_keys']['openai'] == test_key

    def test_track_usage(self):
        """Test tracking usage."""
        config = LLMConfig()

        model_name = "test-model"
        config.track_usage(
            model_name=model_name,
            input_tokens=100,
            output_tokens=50,
            cost=0.5,
            cache_hit=False
        )

        assert model_name in config.usage_stats
        stats = config.usage_stats[model_name]
        assert stats.total_requests == 1
        assert stats.total_tokens_input == 100
        assert stats.total_tokens_output == 50
        assert stats.total_cost == 0.5
        assert stats.cache_misses == 1

    def test_get_usage_summary(self):
        """Test getting usage summary."""
        config = LLMConfig()

        # Track some usage
        config.track_usage("model1", 100, 50, 0.5)
        config.track_usage("model2", 200, 100, 1.0)

        summary = config.get_usage_summary()

        assert summary['total_cost'] == 1.5
        assert summary['total_requests'] == 2
        assert summary['total_tokens'] == 450
        assert 'model1' in summary['by_model']
        assert 'model2' in summary['by_model']

    def test_reset_usage_stats(self):
        """Test resetting usage statistics."""
        config = LLMConfig()

        # Track usage
        config.track_usage("test-model", 100, 50, 0.5)
        assert config.usage_stats["test-model"].total_requests == 1

        # Reset
        config.reset_usage_stats("test-model")
        assert config.usage_stats["test-model"].total_requests == 0

    def test_models_configuration(self):
        """Test that all models are properly configured."""
        config = LLMConfig()

        # Test GPT models
        assert ModelType.GPT_4_TURBO in config.MODELS
        assert ModelType.GPT_4 in config.MODELS
        assert ModelType.GPT_35_TURBO in config.MODELS

        # Test Gemini models
        assert ModelType.GEMINI_PRO in config.MODELS
        assert ModelType.GEMINI_PRO_VISION in config.MODELS
        assert ModelType.GEMINI_15_PRO in config.MODELS

        # Verify cost information is present
        for model_config in config.MODELS.values():
            assert model_config.cost_per_1k_input > 0
            assert model_config.cost_per_1k_output > 0


class TestGlobalConfig:
    """Test global config functions."""

    def test_get_config_creates_instance(self):
        """Test that get_config creates a global instance."""
        config1 = get_config()
        config2 = get_config()

        # Should return the same instance
        assert config1 is config2

    def test_set_config(self):
        """Test setting global config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_config = LLMConfig(config_file=Path(tmpdir) / "config.json")
            set_config(custom_config)

            retrieved_config = get_config()
            assert retrieved_config is custom_config


@pytest.fixture
def temp_config():
    """Fixture for temporary config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.json"
        cache_dir = Path(tmpdir) / "cache"
        yield LLMConfig(config_file=config_file, cache_dir=cache_dir)


class TestConfigPersistence:
    """Test configuration persistence."""

    def test_save_and_load_config(self, temp_config):
        """Test saving and loading configuration."""
        # Set API key
        temp_config.set_api_key(LLMProvider.OPENAI, "test-key")

        # Create new config with same file
        new_config = LLMConfig(
            config_file=temp_config.config_file,
            cache_dir=temp_config.cache_dir
        )

        # Should load the saved API key
        # Note: Environment variables take precedence
        if not new_config.get_api_key(LLMProvider.OPENAI):
            # If not from env, should be from file
            assert new_config.get_api_key(LLMProvider.OPENAI) == "test-key"

    def test_save_and_load_usage_stats(self, temp_config):
        """Test saving and loading usage stats."""
        # Track some usage
        temp_config.track_usage("test-model", 100, 50, 0.5)
        temp_config.save_usage_stats()

        # Create new config
        new_config = LLMConfig(
            config_file=temp_config.config_file,
            cache_dir=temp_config.cache_dir
        )

        # Should load the saved stats
        assert "test-model" in new_config.usage_stats
        assert new_config.usage_stats["test-model"].total_requests == 1
