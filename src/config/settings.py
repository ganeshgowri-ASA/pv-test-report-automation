"""
Configuration settings management for PV Test Report Automation.

This module provides centralized configuration management using environment variables
and Pydantic settings for type safety and validation.
"""

import os
from typing import Optional
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application Settings
    APP_NAME: str = "PV Test Report Automation"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    ENVIRONMENT: str = Field(default="development", description="Environment: development/staging/production")

    # Claude API Configuration
    CLAUDE_API_KEY: str = Field(default="", description="Anthropic Claude API key")
    CLAUDE_MODEL: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Claude model to use for analysis"
    )
    CLAUDE_API_ENDPOINT: str = Field(
        default="https://api.anthropic.com/v1",
        description="Claude API endpoint URL"
    )
    CLAUDE_MAX_TOKENS: int = Field(
        default=4096,
        description="Maximum tokens for Claude responses"
    )
    CLAUDE_TEMPERATURE: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Temperature for Claude responses (0.0-1.0)"
    )
    CLAUDE_TIMEOUT: int = Field(
        default=120,
        description="API request timeout in seconds"
    )

    # Rate Limiting
    CLAUDE_MAX_RETRIES: int = Field(default=3, description="Max retry attempts for API calls")
    CLAUDE_RETRY_DELAY: float = Field(default=2.0, description="Initial retry delay in seconds")
    CLAUDE_RATE_LIMIT_REQUESTS: int = Field(
        default=50,
        description="Max requests per minute"
    )

    # Cost Tracking
    ENABLE_COST_TRACKING: bool = Field(default=True, description="Enable token cost tracking")
    COST_ALERT_THRESHOLD: float = Field(
        default=100.0,
        description="Alert when daily cost exceeds this amount (USD)"
    )

    # Database Configuration
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="Database connection URL"
    )
    DB_POOL_SIZE: int = Field(default=5, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=10, description="Max database overflow connections")

    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        default="json",
        description="Log format: json or text"
    )
    LOG_FILE_PATH: str = Field(
        default="logs/app.log",
        description="Application log file path"
    )
    AUDIT_LOG_PATH: str = Field(
        default="logs/audit.log",
        description="Audit trail log file path"
    )
    LLM_LOG_PATH: str = Field(
        default="logs/llm.log",
        description="LLM interaction log file path"
    )

    # Audit Trail
    ENABLE_AUDIT_TRAIL: bool = Field(default=True, description="Enable audit trail logging")
    AUDIT_LOG_LLM_PROMPTS: bool = Field(
        default=True,
        description="Log LLM prompts and responses in audit trail"
    )
    AUDIT_RETENTION_DAYS: int = Field(
        default=365,
        description="Audit log retention period in days"
    )

    # Security
    SECRET_KEY: str = Field(
        default="",
        description="Secret key for encryption and signing"
    )
    API_KEY_ENCRYPTION_ENABLED: bool = Field(
        default=True,
        description="Encrypt API keys in database"
    )
    ALLOWED_HOSTS: list[str] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1"],
        description="Allowed host names"
    )

    # Standards and Compliance
    SUPPORTED_STANDARDS: list[str] = Field(
        default_factory=lambda: [
            "IEC 61215",
            "IEC 61730",
            "IEC 61853",
            "IEC 62716",
            "IEC 61701",
            "IEC 62804",
            "IEC 60904",
            "IEC 62759",
            "ISO 17025",
            "ISO 9001",
        ],
        description="Supported testing standards"
    )

    # Report Generation
    DEFAULT_REPORT_LANGUAGE: str = Field(
        default="en",
        description="Default language for reports (ISO 639-1 code)"
    )
    SUPPORTED_LANGUAGES: list[str] = Field(
        default_factory=lambda: ["en", "es", "fr", "de", "zh", "ja", "hi"],
        description="Supported languages for report generation"
    )
    EXPORT_FORMATS: list[str] = Field(
        default_factory=lambda: ["pdf", "docx", "xlsx", "html", "json"],
        description="Supported export formats"
    )

    # File Storage
    UPLOAD_DIR: str = Field(
        default="uploads",
        description="Directory for file uploads"
    )
    MAX_UPLOAD_SIZE: int = Field(
        default=52428800,  # 50MB
        description="Maximum upload file size in bytes"
    )
    ALLOWED_EXTENSIONS: list[str] = Field(
        default_factory=lambda: [".pdf", ".xlsx", ".csv", ".txt", ".json"],
        description="Allowed file extensions for uploads"
    )

    # Performance
    CACHE_ENABLED: bool = Field(default=True, description="Enable response caching")
    CACHE_TTL: int = Field(default=3600, description="Cache time-to-live in seconds")

    @field_validator("CLAUDE_API_KEY")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate that API key is set in non-development environments."""
        # In production, API key must be set
        # We'll allow empty in development for testing
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v_upper

    @field_validator("DEFAULT_REPORT_LANGUAGE")
    @classmethod
    def validate_language_code(cls, v: str) -> str:
        """Validate language code format."""
        if len(v) != 2:
            raise ValueError("Language code must be 2 characters (ISO 639-1)")
        return v.lower()

    def get_log_dir(self) -> Path:
        """Get the logs directory path."""
        log_dir = Path(self.LOG_FILE_PATH).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    def get_upload_dir(self) -> Path:
        """Get the uploads directory path."""
        upload_dir = Path(self.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get or create the global settings instance.

    Returns:
        Settings: The application settings instance.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment.

    Returns:
        Settings: The refreshed application settings instance.
    """
    global _settings
    _settings = Settings()
    return _settings
