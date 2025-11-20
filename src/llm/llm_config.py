"""
LLM Configuration and Management Module

Handles API keys, model selection, cost tracking, and rate limiting
for various LLM providers.
"""

import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Any
from pathlib import Path
import json
import logging
from datetime import datetime, timedelta
from threading import Lock

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"


class ModelType(Enum):
    """Available model types."""
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_4 = "gpt-4"
    GPT_35_TURBO = "gpt-3.5-turbo"
    GEMINI_PRO = "gemini-pro"
    GEMINI_PRO_VISION = "gemini-pro-vision"
    GEMINI_15_PRO = "gemini-1.5-pro"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    name: str
    provider: LLMProvider
    max_tokens: int
    cost_per_1k_input: float  # USD
    cost_per_1k_output: float  # USD
    supports_vision: bool = False
    supports_function_calling: bool = False
    context_window: int = 4096
    temperature_default: float = 0.7


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    requests_per_minute: int = 60
    tokens_per_minute: int = 90000
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    exponential_backoff: bool = True


@dataclass
class UsageStats:
    """Track LLM usage statistics."""
    total_requests: int = 0
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    total_cost: float = 0.0
    errors: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    last_reset: datetime = field(default_factory=datetime.now)

    def reset(self):
        """Reset usage statistics."""
        self.total_requests = 0
        self.total_tokens_input = 0
        self.total_tokens_output = 0
        self.total_cost = 0.0
        self.errors = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.last_reset = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_requests': self.total_requests,
            'total_tokens_input': self.total_tokens_input,
            'total_tokens_output': self.total_tokens_output,
            'total_cost': self.total_cost,
            'errors': self.errors,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'last_reset': self.last_reset.isoformat()
        }


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.request_timestamps: list[float] = []
        self.token_usage: list[tuple[float, int]] = []
        self.lock = Lock()

    def check_rate_limit(self, tokens: int = 0) -> tuple[bool, Optional[float]]:
        """
        Check if request is within rate limits.

        Returns:
            (allowed, wait_time) - wait_time is None if allowed immediately
        """
        with self.lock:
            current_time = time.time()
            minute_ago = current_time - 60

            # Clean old timestamps
            self.request_timestamps = [
                ts for ts in self.request_timestamps if ts > minute_ago
            ]
            self.token_usage = [
                (ts, tok) for ts, tok in self.token_usage if ts > minute_ago
            ]

            # Check request rate
            if len(self.request_timestamps) >= self.config.requests_per_minute:
                wait_time = 60 - (current_time - self.request_timestamps[0])
                return False, wait_time

            # Check token rate
            total_tokens = sum(tok for _, tok in self.token_usage) + tokens
            if total_tokens > self.config.tokens_per_minute:
                wait_time = 60 - (current_time - self.token_usage[0][0])
                return False, wait_time

            return True, None

    def record_request(self, tokens: int = 0):
        """Record a successful request."""
        with self.lock:
            current_time = time.time()
            self.request_timestamps.append(current_time)
            if tokens > 0:
                self.token_usage.append((current_time, tokens))


class LLMConfig:
    """Main LLM configuration manager."""

    # Model configurations
    MODELS = {
        ModelType.GPT_4_TURBO: ModelConfig(
            name="gpt-4-turbo-preview",
            provider=LLMProvider.OPENAI,
            max_tokens=4096,
            cost_per_1k_input=0.01,
            cost_per_1k_output=0.03,
            supports_vision=True,
            supports_function_calling=True,
            context_window=128000,
            temperature_default=0.7
        ),
        ModelType.GPT_4: ModelConfig(
            name="gpt-4",
            provider=LLMProvider.OPENAI,
            max_tokens=8192,
            cost_per_1k_input=0.03,
            cost_per_1k_output=0.06,
            supports_function_calling=True,
            context_window=8192
        ),
        ModelType.GPT_35_TURBO: ModelConfig(
            name="gpt-3.5-turbo",
            provider=LLMProvider.OPENAI,
            max_tokens=4096,
            cost_per_1k_input=0.0005,
            cost_per_1k_output=0.0015,
            supports_function_calling=True,
            context_window=16385
        ),
        ModelType.GEMINI_PRO: ModelConfig(
            name="gemini-pro",
            provider=LLMProvider.GEMINI,
            max_tokens=2048,
            cost_per_1k_input=0.00025,
            cost_per_1k_output=0.0005,
            context_window=32760
        ),
        ModelType.GEMINI_PRO_VISION: ModelConfig(
            name="gemini-pro-vision",
            provider=LLMProvider.GEMINI,
            max_tokens=2048,
            cost_per_1k_input=0.00025,
            cost_per_1k_output=0.0005,
            supports_vision=True,
            context_window=32760
        ),
        ModelType.GEMINI_15_PRO: ModelConfig(
            name="gemini-1.5-pro",
            provider=LLMProvider.GEMINI,
            max_tokens=8192,
            cost_per_1k_input=0.00125,
            cost_per_1k_output=0.00375,
            supports_vision=True,
            context_window=1000000
        ),
    }

    def __init__(
        self,
        config_file: Optional[Path] = None,
        cache_dir: Optional[Path] = None
    ):
        """
        Initialize LLM configuration.

        Args:
            config_file: Path to configuration file
            cache_dir: Directory for caching responses
        """
        self.config_file = config_file or Path.home() / ".pv_automation" / "llm_config.json"
        self.cache_dir = cache_dir or Path.home() / ".pv_automation" / "llm_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # API keys
        self._api_keys: Dict[LLMProvider, str] = {}
        self._load_api_keys()

        # Rate limiters per provider
        self.rate_limiters: Dict[LLMProvider, RateLimiter] = {
            LLMProvider.OPENAI: RateLimiter(RateLimitConfig(
                requests_per_minute=60,
                tokens_per_minute=90000
            )),
            LLMProvider.GEMINI: RateLimiter(RateLimitConfig(
                requests_per_minute=60,
                tokens_per_minute=120000
            )),
        }

        # Usage statistics per model
        self.usage_stats: Dict[str, UsageStats] = {}
        self._load_usage_stats()

        # Default model
        self.default_model = ModelType.GPT_4_TURBO

        # Cache settings
        self.enable_cache = True
        self.cache_ttl = timedelta(days=7)

    def _load_api_keys(self):
        """Load API keys from environment and config file."""
        # Load from environment
        if openai_key := os.getenv("OPENAI_API_KEY"):
            self._api_keys[LLMProvider.OPENAI] = openai_key

        if gemini_key := os.getenv("GOOGLE_API_KEY"):
            self._api_keys[LLMProvider.GEMINI] = gemini_key

        if anthropic_key := os.getenv("ANTHROPIC_API_KEY"):
            self._api_keys[LLMProvider.ANTHROPIC] = anthropic_key

        # Load from config file if exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    api_keys = config_data.get('api_keys', {})
                    for provider_str, key in api_keys.items():
                        provider = LLMProvider(provider_str)
                        if provider not in self._api_keys:  # Don't override env vars
                            self._api_keys[provider] = key
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")

    def get_api_key(self, provider: LLMProvider) -> Optional[str]:
        """Get API key for a provider."""
        return self._api_keys.get(provider)

    def set_api_key(self, provider: LLMProvider, key: str):
        """Set API key for a provider."""
        self._api_keys[provider] = key
        self._save_config()

    def _save_config(self):
        """Save configuration to file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        config_data = {
            'api_keys': {
                provider.value: key
                for provider, key in self._api_keys.items()
            }
        }
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

    def _load_usage_stats(self):
        """Load usage statistics from file."""
        stats_file = self.cache_dir / "usage_stats.json"
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    stats_data = json.load(f)
                    for model_name, stats in stats_data.items():
                        usage = UsageStats()
                        usage.total_requests = stats.get('total_requests', 0)
                        usage.total_tokens_input = stats.get('total_tokens_input', 0)
                        usage.total_tokens_output = stats.get('total_tokens_output', 0)
                        usage.total_cost = stats.get('total_cost', 0.0)
                        usage.errors = stats.get('errors', 0)
                        usage.cache_hits = stats.get('cache_hits', 0)
                        usage.cache_misses = stats.get('cache_misses', 0)
                        if last_reset := stats.get('last_reset'):
                            usage.last_reset = datetime.fromisoformat(last_reset)
                        self.usage_stats[model_name] = usage
            except Exception as e:
                logger.warning(f"Failed to load usage stats: {e}")

    def save_usage_stats(self):
        """Save usage statistics to file."""
        stats_file = self.cache_dir / "usage_stats.json"
        stats_data = {
            model_name: stats.to_dict()
            for model_name, stats in self.usage_stats.items()
        }
        with open(stats_file, 'w') as f:
            json.dump(stats_data, f, indent=2)

    def get_model_config(self, model_type: ModelType) -> ModelConfig:
        """Get configuration for a specific model."""
        return self.MODELS[model_type]

    def track_usage(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        error: bool = False,
        cache_hit: bool = False
    ):
        """Track usage for a model."""
        if model_name not in self.usage_stats:
            self.usage_stats[model_name] = UsageStats()

        stats = self.usage_stats[model_name]
        stats.total_requests += 1
        stats.total_tokens_input += input_tokens
        stats.total_tokens_output += output_tokens
        stats.total_cost += cost

        if error:
            stats.errors += 1

        if cache_hit:
            stats.cache_hits += 1
        else:
            stats.cache_misses += 1

        # Save every 10 requests
        if stats.total_requests % 10 == 0:
            self.save_usage_stats()

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get summary of all usage statistics."""
        total_cost = sum(stats.total_cost for stats in self.usage_stats.values())
        total_requests = sum(stats.total_requests for stats in self.usage_stats.values())
        total_tokens = sum(
            stats.total_tokens_input + stats.total_tokens_output
            for stats in self.usage_stats.values()
        )

        return {
            'total_cost': total_cost,
            'total_requests': total_requests,
            'total_tokens': total_tokens,
            'by_model': {
                model_name: stats.to_dict()
                for model_name, stats in self.usage_stats.items()
            }
        }

    def reset_usage_stats(self, model_name: Optional[str] = None):
        """Reset usage statistics for a model or all models."""
        if model_name:
            if model_name in self.usage_stats:
                self.usage_stats[model_name].reset()
        else:
            for stats in self.usage_stats.values():
                stats.reset()
        self.save_usage_stats()


# Global configuration instance
_global_config: Optional[LLMConfig] = None


def get_config() -> LLMConfig:
    """Get or create global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = LLMConfig()
    return _global_config


def set_config(config: LLMConfig):
    """Set global configuration instance."""
    global _global_config
    _global_config = config
