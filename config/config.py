"""
Configuration Management for PV Test Automation System
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "PV Test Automation System"
    APP_ENV: str = "production"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"

    # Database
    DATABASE_URL: str = "postgresql://pv_admin:changeme@postgres:5432/pv_test_automation"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://redis:6379"

    # MinIO / S3
    MINIO_URL: str = "minio:9000"
    MINIO_ROOT_USER: str = "admin"
    MINIO_ROOT_PASSWORD: str = "changeme123"
    MINIO_BUCKET: str = "pv-test-data"
    MINIO_SECURE: bool = False

    # RabbitMQ / Celery
    CELERY_BROKER_URL: str = "amqp://admin:changeme@rabbitmq:5672"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    # API Keys
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None

    # Security
    JWT_SECRET_KEY: str = "CHANGE_ME_JWT_SECRET"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Accreditation
    ACCREDITATION_NUMBER: str = "TC-XXXX"
    LAB_NAME: str = "PV Testing Laboratory"
    LAB_ADDRESS: str = ""
    NABL_LOGO_PATH: str = "/app/assets/nabl_logo.png"
    ILAC_LOGO_PATH: str = "/app/assets/ilac_logo.png"
    COMPANY_LOGO_PATH: str = "/app/assets/company_logo.png"

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 100
    ALLOWED_EXTENSIONS: str = "xlsx,xls,docx,pdf,jpg,png,json,csv,xml,vsdx"

    # Report Generation
    DEFAULT_REPORT_TEMPLATE: str = "iso_17025_standard"
    ENABLE_LLM_NARRATIVES: bool = True
    DEFAULT_LLM_PROVIDER: str = "claude"

    # Email (Optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@pvtesting.com"

    # Monitoring
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_ENABLED: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings
