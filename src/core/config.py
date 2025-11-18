"""
Configuration management for PV test report automation.

Handles environment variables and application settings using Pydantic Settings.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # Smartsheet Configuration
    smartsheet_api_key: str = Field(
        default="",
        description="Smartsheet API key for authentication"
    )
    smartsheet_workspace_id: Optional[str] = Field(
        default=None,
        description="Default Smartsheet workspace ID"
    )

    # Visio Configuration
    visio_enable: bool = Field(
        default=True,
        description="Enable Visio diagram processing"
    )
    visio_default_export_format: str = Field(
        default="svg",
        description="Default export format for Visio diagrams"
    )

    # Gantt/MS Project Configuration
    gantt_default_format: str = Field(
        default="json",
        description="Default output format for Gantt data"
    )
    gantt_enable_baseline_comparison: bool = Field(
        default=True,
        description="Enable baseline vs. actual comparison"
    )

    # Application Settings
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    environment: str = Field(
        default="development",
        description="Runtime environment (development, staging, production)"
    )

    # File Processing
    max_file_size_mb: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum file size in MB for processing"
    )
    temp_dir: str = Field(
        default="/tmp/pv-ingestion",
        description="Temporary directory for file processing"
    )

    # Output Configuration
    output_dir: str = Field(
        default="./output",
        description="Directory for output files"
    )

    # Database (future use)
    database_url: Optional[str] = Field(
        default=None,
        description="Database connection URL"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed_levels:
            raise ValueError(f"log_level must be one of {allowed_levels}")
        return v_upper

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment is one of the allowed values."""
        allowed_envs = ["development", "staging", "production"]
        v_lower = v.lower()
        if v_lower not in allowed_envs:
            raise ValueError(f"environment must be one of {allowed_envs}")
        return v_lower

    def ensure_temp_dir(self) -> Path:
        """Ensure temporary directory exists and return as Path object."""
        temp_path = Path(self.temp_dir)
        temp_path.mkdir(parents=True, exist_ok=True)
        return temp_path

    def ensure_output_dir(self) -> Path:
        """Ensure output directory exists and return as Path object."""
        output_path = Path(self.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path

    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment (useful for testing)."""
    global _settings
    _settings = Settings()
    return _settings
