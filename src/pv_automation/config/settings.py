"""Application settings and configuration management"""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseSettings):
    """LLM provider configuration"""

    provider: str = Field(default="gemini", description="LLM provider to use")
    api_key: Optional[str] = Field(default=None, description="API key for the LLM provider")
    model: str = Field(
        default="gemini-2.0-flash-exp", description="Model name for text generation"
    )
    vision_model: str = Field(
        default="gemini-2.0-flash-exp", description="Model name for vision tasks"
    )
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Generation temperature")
    max_tokens: int = Field(default=2048, ge=1, le=32768, description="Maximum output tokens")
    top_p: float = Field(default=0.95, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    top_k: int = Field(default=40, ge=1, le=100, description="Top-k sampling parameter")
    enable_safety_filters: bool = Field(
        default=True, description="Enable content safety filters"
    )

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate LLM provider"""
        allowed = ["gemini", "claude", "openai"]
        if v.lower() not in allowed:
            raise ValueError(f"Provider must be one of {allowed}")
        return v.lower()

    model_config = SettingsConfigDict(env_prefix="GEMINI_", case_sensitive=False)


class FileUploadConfig(BaseSettings):
    """File upload configuration"""

    max_image_size_mb: int = Field(default=10, ge=1, le=50, description="Max image size in MB")
    allowed_image_formats: List[str] = Field(
        default=["png", "jpg", "jpeg", "tiff", "bmp"],
        description="Allowed image file formats",
    )
    upload_dir: Path = Field(
        default=Path("./uploads"), description="Directory for uploaded files"
    )

    @field_validator("upload_dir")
    @classmethod
    def validate_upload_dir(cls, v: Path) -> Path:
        """Ensure upload directory exists"""
        v.mkdir(parents=True, exist_ok=True)
        return v

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)


class PVStandardsConfig(BaseSettings):
    """PV standards configuration"""

    default_standard: str = Field(
        default="IEC 61215", description="Default PV testing standard"
    )
    enable_compliance_checking: bool = Field(
        default=True, description="Enable automatic compliance checking"
    )

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)


class FeatureFlags(BaseSettings):
    """Feature flags for enabling/disabling functionality"""

    enable_vision_analysis: bool = Field(
        default=True, description="Enable vision-based defect analysis"
    )
    enable_predictive_analysis: bool = Field(
        default=True, description="Enable predictive failure analysis"
    )
    enable_batch_processing: bool = Field(
        default=True, description="Enable batch processing of reports"
    )

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)


class Settings(BaseSettings):
    """Main application settings"""

    # Application metadata
    app_name: str = Field(default="PV Test Report Automation", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    log_level: str = Field(default="INFO", description="Logging level")

    # Sub-configurations
    llm: LLMConfig = Field(default_factory=LLMConfig)
    file_upload: FileUploadConfig = Field(default_factory=FileUploadConfig)
    pv_standards: PVStandardsConfig = Field(default_factory=PVStandardsConfig)
    features: FeatureFlags = Field(default_factory=FeatureFlags)

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v_upper

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    Returns:
        Settings: Application configuration instance
    """
    return Settings()


# Convenience function to reload settings (useful for testing)
def reload_settings() -> Settings:
    """
    Reload settings by clearing cache.

    Returns:
        Settings: Fresh application configuration instance
    """
    get_settings.cache_clear()
    return get_settings()
