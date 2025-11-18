"""Configuration management for GPT integration."""

import os
from typing import Optional, Dict
from pydantic_settings import BaseSettings
from pydantic import Field


class Config(BaseSettings):
    """Configuration settings for GPT integration."""

    # OpenAI Settings
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_organization: Optional[str] = Field(None, env="OPENAI_ORGANIZATION")
    default_model: str = Field(default="gpt-4-turbo", env="GPT_DEFAULT_MODEL")
    default_temperature: float = Field(default=0.7, env="GPT_DEFAULT_TEMPERATURE")
    default_max_tokens: int = Field(default=2000, env="GPT_DEFAULT_MAX_TOKENS")

    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(
        default=60,
        env="RATE_LIMIT_RPM"
    )
    rate_limit_tokens_per_minute: int = Field(
        default=90000,
        env="RATE_LIMIT_TPM"
    )

    # Caching
    enable_cache: bool = Field(default=True, env="ENABLE_CACHE")
    cache_ttl_seconds: int = Field(default=3600, env="CACHE_TTL")
    cache_max_size: int = Field(default=1000, env="CACHE_MAX_SIZE")

    # Cost Tracking
    enable_cost_tracking: bool = Field(default=True, env="ENABLE_COST_TRACKING")
    cost_alert_threshold_usd: float = Field(
        default=100.0,
        env="COST_ALERT_THRESHOLD"
    )

    # Retry Logic
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    retry_delay_seconds: float = Field(default=1.0, env="RETRY_DELAY")
    exponential_backoff: bool = Field(default=True, env="EXPONENTIAL_BACKOFF")

    # Compliance Standards
    default_compliance_standard: str = Field(
        default="IEC 61215",
        env="DEFAULT_COMPLIANCE_STANDARD"
    )

    # Multi-language Support
    default_language: str = Field(default="en", env="DEFAULT_LANGUAGE")
    supported_languages: list = Field(
        default=["en", "es", "de", "fr", "zh", "ja"],
        env="SUPPORTED_LANGUAGES"
    )

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(None, env="LOG_FILE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls()

    def get_model_pricing(self, model: str) -> Dict[str, float]:
        """Get pricing information for a model (per 1K tokens)."""
        pricing = {
            "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
            "gpt-4o": {"prompt": 0.005, "completion": 0.015},
            "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
        }
        return pricing.get(model, {"prompt": 0.01, "completion": 0.03})
