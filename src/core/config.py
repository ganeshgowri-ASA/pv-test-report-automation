"""Core configuration for PV Test Report Automation.

ISO 17025 Compliant Configuration Management
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with ISO 17025 compliance."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Application
    APP_NAME: str = "PV Test Report Automation"
    APP_ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Security
    SECRET_KEY: str = Field(..., min_length=32)
    ENCRYPTION_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/pv_test_reports"
    REDIS_URL: str = "redis://localhost:6379/0"

    # HashiCorp Vault (Session 37)
    VAULT_ADDR: Optional[str] = None
    VAULT_TOKEN: Optional[str] = None
    VAULT_NAMESPACE: str = "pv-automation"

    # AWS Secrets Manager
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    SECRETS_MANAGER_PREFIX: str = "pv-automation/"

    # LLM API Keys
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None

    # LLM Orchestrator Settings (Session 38)
    LLM_DEFAULT_MODEL: str = "claude-3-5-sonnet-20241022"
    LLM_FALLBACK_ENABLED: bool = True
    LLM_MAX_RETRIES: int = 3
    LLM_TIMEOUT_SECONDS: int = 30

    # Export Settings (Sessions 40-44, 48)
    EXPORT_TEMP_DIR: str = "/tmp/pv-exports"
    EXPORT_ARCHIVE_DIR: str = "/var/pv-exports/archive"
    MAX_EXPORT_SIZE_MB: int = 100

    # Celery/Redis
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Email Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@pvautomation.com"

    # ISO 17025 Compliance Settings
    ENABLE_AUDIT_LOGGING: bool = True
    REQUIRE_DIGITAL_SIGNATURES: bool = True
    RETENTION_PERIOD_DAYS: int = 2555  # 7 years

    # WebSocket Settings (Sessions 45-47)
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS: int = 100

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.APP_ENV == "development"


# Global settings instance
settings = Settings()
