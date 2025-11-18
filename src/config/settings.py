"""Configuration Settings Loader
Loads YAML configs and environment variables for the system.

This module provides centralized configuration management for the PV Test Report
Automation system, including database settings, API keys, file storage, and
integration with IEC/ISO standards configuration.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseSettings, Field, validator, SecretStr
from functools import lru_cache


class Settings(BaseSettings):
    """Application Settings

    Loads configuration from environment variables and .env file.
    Provides type-safe access to all system configuration parameters.
    """

    # ==========================================================================
    # Application Information
    # ==========================================================================
    app_name: str = Field(default="PV Test Report Automation", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")

    # ==========================================================================
    # Database Configuration
    # ==========================================================================
    database_url: str = Field(
        default="sqlite:///./pv_test.db",
        env="DATABASE_URL",
        description="Database connection URL (SQLite, PostgreSQL, MySQL supported)"
    )
    db_echo: bool = Field(
        default=False,
        env="DB_ECHO",
        description="Echo SQL statements to console (for debugging)"
    )
    db_pool_size: int = Field(
        default=5,
        env="DB_POOL_SIZE",
        description="Database connection pool size"
    )
    db_max_overflow: int = Field(
        default=10,
        env="DB_MAX_OVERFLOW",
        description="Maximum overflow connections beyond pool_size"
    )
    db_pool_timeout: int = Field(
        default=30,
        env="DB_POOL_TIMEOUT",
        description="Connection pool timeout in seconds"
    )

    # ==========================================================================
    # Security Configuration
    # ==========================================================================
    secret_key: str = Field(
        default="change-this-secret-key-in-production",
        env="SECRET_KEY",
        description="Secret key for JWT token generation and encryption"
    )
    algorithm: str = Field(
        default="HS256",
        env="ALGORITHM",
        description="JWT encryption algorithm"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        env="ACCESS_TOKEN_EXPIRE_MINUTES",
        description="JWT access token expiration time in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        env="REFRESH_TOKEN_EXPIRE_DAYS",
        description="JWT refresh token expiration time in days"
    )

    # Password Requirements
    password_min_length: int = Field(default=8, env="PASSWORD_MIN_LENGTH")
    password_require_uppercase: bool = Field(default=True, env="PASSWORD_REQUIRE_UPPERCASE")
    password_require_lowercase: bool = Field(default=True, env="PASSWORD_REQUIRE_LOWERCASE")
    password_require_digits: bool = Field(default=True, env="PASSWORD_REQUIRE_DIGITS")
    password_require_special: bool = Field(default=True, env="PASSWORD_REQUIRE_SPECIAL")

    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="CORS_ORIGINS",
        description="Allowed CORS origins (comma-separated in env)"
    )
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(default=["*"], env="CORS_ALLOW_METHODS")
    cors_allow_headers: List[str] = Field(default=["*"], env="CORS_ALLOW_HEADERS")

    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # ==========================================================================
    # LLM API Configuration (stored in vault/secrets management in production)
    # ==========================================================================
    claude_api_key: SecretStr = Field(
        default="",
        env="CLAUDE_API_KEY",
        description="Anthropic Claude API key"
    )
    claude_model: str = Field(
        default="claude-3-opus-20240229",
        env="CLAUDE_MODEL",
        description="Claude model version"
    )
    claude_max_tokens: int = Field(
        default=4096,
        env="CLAUDE_MAX_TOKENS",
        description="Maximum tokens for Claude responses"
    )

    openai_api_key: SecretStr = Field(
        default="",
        env="OPENAI_API_KEY",
        description="OpenAI API key"
    )
    openai_model: str = Field(
        default="gpt-4-turbo-preview",
        env="OPENAI_MODEL",
        description="OpenAI model version"
    )
    openai_max_tokens: int = Field(
        default=4096,
        env="OPENAI_MAX_TOKENS",
        description="Maximum tokens for OpenAI responses"
    )

    gemini_api_key: SecretStr = Field(
        default="",
        env="GEMINI_API_KEY",
        description="Google Gemini API key"
    )
    gemini_model: str = Field(
        default="gemini-pro",
        env="GEMINI_MODEL",
        description="Gemini model version"
    )

    # Default LLM provider
    default_llm_provider: str = Field(
        default="claude",
        env="DEFAULT_LLM_PROVIDER",
        description="Default LLM provider (claude, openai, gemini)"
    )

    # LLM Request Configuration
    llm_timeout_seconds: int = Field(
        default=60,
        env="LLM_TIMEOUT_SECONDS",
        description="LLM API request timeout"
    )
    llm_retry_attempts: int = Field(
        default=3,
        env="LLM_RETRY_ATTEMPTS",
        description="Number of retry attempts for failed LLM requests"
    )
    llm_retry_delay_seconds: int = Field(
        default=2,
        env="LLM_RETRY_DELAY_SECONDS",
        description="Delay between retry attempts"
    )

    # ==========================================================================
    # File Storage Configuration
    # ==========================================================================
    upload_dir: Path = Field(
        default=Path("./uploads"),
        env="UPLOAD_DIR",
        description="Directory for uploaded files"
    )
    max_upload_size_mb: int = Field(
        default=100,
        env="MAX_UPLOAD_SIZE_MB",
        description="Maximum file upload size in megabytes"
    )
    allowed_upload_extensions: List[str] = Field(
        default=[".pdf", ".xlsx", ".xls", ".csv", ".jpg", ".jpeg", ".png", ".txt", ".docx"],
        env="ALLOWED_UPLOAD_EXTENSIONS",
        description="Allowed file extensions for uploads"
    )

    # Storage paths
    reports_dir: Path = Field(
        default=Path("./reports"),
        env="REPORTS_DIR",
        description="Directory for generated reports"
    )
    temp_dir: Path = Field(
        default=Path("./temp"),
        env="TEMP_DIR",
        description="Directory for temporary files"
    )
    archive_dir: Path = Field(
        default=Path("./archive"),
        env="ARCHIVE_DIR",
        description="Directory for archived files"
    )

    @validator("allowed_upload_extensions", pre=True)
    def parse_allowed_extensions(cls, v):
        """Parse allowed extensions from comma-separated string"""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v

    # ==========================================================================
    # Report Generation Configuration
    # ==========================================================================
    latex_compiler: str = Field(
        default="pdflatex",
        env="LATEX_COMPILER",
        description="LaTeX compiler (pdflatex, xelatex, lualatex)"
    )
    latex_compile_passes: int = Field(
        default=2,
        env="LATEX_COMPILE_PASSES",
        description="Number of LaTeX compilation passes"
    )
    report_template_dir: Path = Field(
        default=Path("./templates"),
        env="REPORT_TEMPLATE_DIR",
        description="Directory for report templates"
    )
    report_logo_path: Optional[Path] = Field(
        default=None,
        env="REPORT_LOGO_PATH",
        description="Path to company logo for reports"
    )

    # Report metadata
    company_name: str = Field(
        default="PV Testing Laboratory",
        env="COMPANY_NAME",
        description="Company/Laboratory name"
    )
    company_address: str = Field(
        default="",
        env="COMPANY_ADDRESS",
        description="Company address"
    )
    company_contact: str = Field(
        default="",
        env="COMPANY_CONTACT",
        description="Company contact information"
    )
    nabl_cert_number: Optional[str] = Field(
        default=None,
        env="NABL_CERT_NUMBER",
        description="NABL certification number"
    )
    nabl_validity: Optional[str] = Field(
        default=None,
        env="NABL_VALIDITY",
        description="NABL certification validity date"
    )

    # ==========================================================================
    # Email Configuration
    # ==========================================================================
    smtp_host: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: str = Field(default="", env="SMTP_USERNAME")
    smtp_password: SecretStr = Field(default="", env="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, env="SMTP_USE_TLS")
    smtp_use_ssl: bool = Field(default=False, env="SMTP_USE_SSL")

    email_from: str = Field(
        default="noreply@pvtesting.com",
        env="EMAIL_FROM",
        description="Default sender email address"
    )
    email_from_name: str = Field(
        default="PV Test Report System",
        env="EMAIL_FROM_NAME",
        description="Default sender name"
    )

    # ==========================================================================
    # Logging Configuration
    # ==========================================================================
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_file: Optional[Path] = Field(
        default=Path("./logs/app.log"),
        env="LOG_FILE",
        description="Log file path"
    )
    log_rotation: str = Field(
        default="1 day",
        env="LOG_ROTATION",
        description="Log rotation interval"
    )
    log_retention: str = Field(
        default="30 days",
        env="LOG_RETENTION",
        description="Log retention period"
    )
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT",
        description="Log message format"
    )

    # ==========================================================================
    # API Rate Limiting
    # ==========================================================================
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_per_minute: int = Field(
        default=60,
        env="RATE_LIMIT_PER_MINUTE",
        description="API requests per minute per IP"
    )
    rate_limit_per_hour: int = Field(
        default=1000,
        env="RATE_LIMIT_PER_HOUR",
        description="API requests per hour per IP"
    )

    # ==========================================================================
    # Testing Configuration
    # ==========================================================================
    test_database_url: str = Field(
        default="sqlite:///./test_pv.db",
        env="TEST_DATABASE_URL",
        description="Test database URL"
    )
    test_mode: bool = Field(
        default=False,
        env="TEST_MODE",
        description="Enable test mode"
    )

    # ==========================================================================
    # Cache Configuration
    # ==========================================================================
    cache_enabled: bool = Field(default=True, env="CACHE_ENABLED")
    cache_backend: str = Field(
        default="redis",
        env="CACHE_BACKEND",
        description="Cache backend (redis, memcached, inmemory)"
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL",
        description="Redis connection URL"
    )
    cache_default_timeout: int = Field(
        default=300,
        env="CACHE_DEFAULT_TIMEOUT",
        description="Default cache timeout in seconds"
    )

    # ==========================================================================
    # Celery/Background Task Configuration
    # ==========================================================================
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        env="CELERY_BROKER_URL",
        description="Celery broker URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        env="CELERY_RESULT_BACKEND",
        description="Celery result backend URL"
    )
    celery_task_always_eager: bool = Field(
        default=False,
        env="CELERY_TASK_ALWAYS_EAGER",
        description="Execute tasks synchronously (for testing)"
    )

    # ==========================================================================
    # Monitoring and Metrics
    # ==========================================================================
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    sentry_dsn: Optional[str] = Field(
        default=None,
        env="SENTRY_DSN",
        description="Sentry DSN for error tracking"
    )

    # ==========================================================================
    # Feature Flags
    # ==========================================================================
    enable_ai_extraction: bool = Field(
        default=True,
        env="ENABLE_AI_EXTRACTION",
        description="Enable AI-powered data extraction"
    )
    enable_auto_qa: bool = Field(
        default=True,
        env="ENABLE_AUTO_QA",
        description="Enable automated quality assurance"
    )
    enable_batch_processing: bool = Field(
        default=True,
        env="ENABLE_BATCH_PROCESSING",
        description="Enable batch processing of reports"
    )

    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            """Custom environment variable parser"""
            if field_name.endswith("_dir") or field_name.endswith("_path"):
                return Path(raw_val)
            return raw_val


def load_standards_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load IEC/ISO standards configuration from YAML file

    Args:
        config_path: Optional custom path to standards config file.
                    Defaults to standards_config.yaml in the same directory.

    Returns:
        Dictionary containing all standards configuration

    Raises:
        FileNotFoundError: If configuration file is not found
        yaml.YAMLError: If YAML parsing fails
    """
    if config_path is None:
        config_path = Path(__file__).parent / "standards_config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Standards configuration file not found: {config_path}"
        )

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        if not config or 'standards' not in config:
            raise ValueError(
                "Invalid standards configuration: 'standards' section not found"
            )

        return config

    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Failed to parse standards configuration: {e}")


def get_standard_info(standard_id: str, standards_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get information about a specific standard

    Args:
        standard_id: Standard identifier (e.g., 'iec_61215', 'iso_17025')
        standards_config: Standards configuration dictionary

    Returns:
        Dictionary containing standard information, or None if not found
    """
    return standards_config.get('standards', {}).get(standard_id)


def get_test_info(standard_id: str, test_code: str, standards_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get information about a specific test within a standard

    Args:
        standard_id: Standard identifier (e.g., 'iec_61215')
        test_code: Test code (e.g., 'MST 01', 'MST 10')
        standards_config: Standards configuration dictionary

    Returns:
        Dictionary containing test information, or None if not found
    """
    standard = get_standard_info(standard_id, standards_config)
    if not standard:
        return None

    test_groups = standard.get('test_groups', {})
    for group_name, tests in test_groups.items():
        for test in tests:
            if test.get('code') == test_code:
                test['group'] = group_name
                return test

    return None


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance

    This function uses lru_cache to ensure settings are loaded only once.

    Returns:
        Settings instance
    """
    return Settings()


@lru_cache()
def get_standards_config() -> Dict[str, Any]:
    """Get cached standards configuration

    This function uses lru_cache to ensure config is loaded only once.

    Returns:
        Standards configuration dictionary
    """
    return load_standards_config()


# Global instances (can be imported directly)
settings = get_settings()
standards_config = get_standards_config()


# Convenience functions for common operations
def get_upload_path(filename: str) -> Path:
    """Get full path for uploaded file

    Args:
        filename: Name of the file

    Returns:
        Full path to the file in upload directory
    """
    return settings.upload_dir / filename


def get_report_path(filename: str) -> Path:
    """Get full path for generated report

    Args:
        filename: Name of the report file

    Returns:
        Full path to the report file
    """
    return settings.reports_dir / filename


def get_template_path(template_name: str) -> Path:
    """Get full path for report template

    Args:
        template_name: Name of the template file

    Returns:
        Full path to the template file
    """
    return settings.report_template_dir / template_name


def ensure_directories() -> None:
    """Ensure all required directories exist

    Creates directories for uploads, reports, templates, temp, archive, and logs
    if they don't already exist.
    """
    directories = [
        settings.upload_dir,
        settings.reports_dir,
        settings.report_template_dir,
        settings.temp_dir,
        settings.archive_dir,
    ]

    if settings.log_file:
        directories.append(settings.log_file.parent)

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def validate_environment() -> List[str]:
    """Validate environment configuration

    Checks for common configuration issues and missing required settings.

    Returns:
        List of validation warnings (empty if all OK)
    """
    warnings = []

    # Check for production environment with default secret key
    if settings.environment == "production":
        if settings.secret_key == "change-this-secret-key-in-production":
            warnings.append(
                "CRITICAL: Using default secret key in production environment! "
                "Set SECRET_KEY environment variable."
            )

        if settings.debug:
            warnings.append(
                "WARNING: Debug mode enabled in production environment"
            )

        if not settings.sentry_dsn:
            warnings.append(
                "WARNING: No Sentry DSN configured for production error tracking"
            )

    # Check for missing API keys if features are enabled
    if settings.enable_ai_extraction:
        if (not settings.claude_api_key.get_secret_value() and
            not settings.openai_api_key.get_secret_value() and
            not settings.gemini_api_key.get_secret_value()):
            warnings.append(
                "WARNING: AI extraction enabled but no LLM API keys configured"
            )

    # Check NABL configuration
    if not settings.nabl_cert_number:
        warnings.append(
            "INFO: NABL certification number not configured"
        )

    # Check database configuration
    if settings.database_url.startswith("sqlite") and settings.environment == "production":
        warnings.append(
            "WARNING: Using SQLite in production. Consider PostgreSQL or MySQL for production."
        )

    return warnings


if __name__ == "__main__":
    """Module test - validate configuration and display settings"""
    print("=" * 80)
    print("PV Test Report Automation - Configuration Validation")
    print("=" * 80)
    print()

    # Load settings
    print(f"Environment: {settings.environment}")
    print(f"Debug: {settings.debug}")
    print(f"Database: {settings.database_url}")
    print(f"Upload Directory: {settings.upload_dir}")
    print(f"Reports Directory: {settings.reports_dir}")
    print()

    # Validate environment
    warnings = validate_environment()
    if warnings:
        print("Configuration Warnings:")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")
    else:
        print("✓ No configuration warnings")
    print()

    # Test standards config loading
    print("Standards Configuration:")
    standards = list(standards_config.get('standards', {}).keys())
    print(f"  Loaded {len(standards)} standards")
    print(f"  Standards: {', '.join(standards[:5])}...")
    print()

    # Test specific standard lookup
    iec_61215 = get_standard_info('iec_61215', standards_config)
    if iec_61215:
        print(f"IEC 61215 Information:")
        print(f"  Title: {iec_61215.get('title')}")
        print(f"  Version: {iec_61215.get('version')}")
        print(f"  MST Tests: {iec_61215.get('test_sequence', {}).get('mst_tests')}")
    print()

    # Ensure directories
    ensure_directories()
    print("✓ All required directories created/verified")
    print()

    print("=" * 80)
