"""
Security Configuration Management
ISO 17025 and 21 CFR Part 11 compliant configuration system
"""

import os
from typing import Optional, List
from pathlib import Path

from pydantic import BaseModel, Field, validator, SecretStr
from pydantic_settings import BaseSettings


class CryptoConfig(BaseModel):
    """Cryptography configuration"""
    # AES Configuration
    aes_key_size: int = Field(default=32, description="AES key size in bytes (32 = 256-bit)")

    # Password Hashing Configuration
    bcrypt_rounds: int = Field(default=12, ge=10, le=16, description="Bcrypt work factor")

    # Key Derivation Configuration
    pbkdf2_iterations: int = Field(default=600000, description="PBKDF2 iterations")
    pbkdf2_salt_size: int = Field(default=32, description="PBKDF2 salt size in bytes")

    # Random Token Configuration
    default_token_bytes: int = Field(default=32, description="Default random token size")


class JWTSecurityConfig(BaseModel):
    """JWT security configuration"""
    secret_key: SecretStr = Field(..., description="JWT signing secret key")
    algorithm: str = Field(default="HS256", description="JWT signing algorithm")

    # Token Expiration
    access_token_expire_minutes: int = Field(default=30, description="Access token TTL in minutes")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token TTL in days")
    api_key_token_expire_days: int = Field(default=365, description="API key token TTL in days")
    password_reset_expire_hours: int = Field(default=24, description="Password reset token TTL")
    email_verification_expire_hours: int = Field(default=48, description="Email verification token TTL")

    # JWT Claims
    issuer: str = Field(default="pv-test-report-system", description="Token issuer")
    audience: str = Field(default="pv-test-api", description="Token audience")

    # Token Refresh
    allow_refresh: bool = Field(default=True, description="Allow token refresh")
    refresh_token_rotation: bool = Field(default=True, description="Rotate refresh tokens on use")

    @validator('secret_key')
    def validate_secret_key(cls, v):
        """Ensure secret key is sufficiently strong"""
        secret = v.get_secret_value() if hasattr(v, 'get_secret_value') else v
        if len(secret) < 32:
            raise ValueError("JWT secret key must be at least 32 characters")
        return v


class APIVaultConfig(BaseModel):
    """API key vault configuration"""
    vault_master_key: SecretStr = Field(..., description="Vault master encryption key")
    storage_path: Optional[Path] = Field(default=None, description="Path to persist vault data")
    use_aes: bool = Field(default=False, description="Use AES-256 instead of Fernet")

    # Key Management
    enable_key_rotation: bool = Field(default=True, description="Enable automatic key rotation")
    default_key_ttl_days: int = Field(default=365, description="Default API key TTL")
    rotation_warning_days: int = Field(default=30, description="Days before expiration to warn")

    # Supported Providers
    enabled_providers: List[str] = Field(
        default=[
            "anthropic",
            "openai",
            "google",
            "cohere",
            "huggingface",
            "azure_openai"
        ],
        description="Enabled LLM providers"
    )


class RBACConfig(BaseModel):
    """RBAC configuration"""
    # Role Management
    allow_custom_roles: bool = Field(default=True, description="Allow custom role creation")
    default_role: str = Field(default="viewer", description="Default role for new users")

    # Permission Caching
    cache_permissions: bool = Field(default=True, description="Cache user permissions")
    permission_cache_ttl_seconds: int = Field(default=300, description="Permission cache TTL")

    # Audit
    log_permission_checks: bool = Field(default=True, description="Log all permission checks")
    log_role_changes: bool = Field(default=True, description="Log all role changes")


class SessionConfig(BaseModel):
    """Session management configuration"""
    # Session Timeout
    session_timeout_minutes: int = Field(default=60, description="Session timeout in minutes")
    absolute_session_timeout_hours: int = Field(default=12, description="Absolute session timeout")

    # Session Security
    secure_cookies: bool = Field(default=True, description="Use secure cookies (HTTPS only)")
    httponly_cookies: bool = Field(default=True, description="Use httponly cookies")
    samesite_cookies: str = Field(default="lax", description="SameSite cookie attribute")

    # Session Storage
    session_storage: str = Field(default="memory", description="Session storage backend")


class ComplianceConfig(BaseModel):
    """ISO 17025 and 21 CFR Part 11 compliance configuration"""
    # 21 CFR Part 11
    enable_electronic_signatures: bool = Field(default=True, description="Enable e-signatures")
    require_signature_reason: bool = Field(default=True, description="Require signature reason")
    dual_signature_required: bool = Field(default=False, description="Require two signatures")

    # ISO 17025
    enable_audit_trail: bool = Field(default=True, description="Enable audit trail")
    audit_retention_days: int = Field(default=2555, description="Audit log retention (7 years)")
    require_change_justification: bool = Field(default=True, description="Require change justification")

    # Data Integrity
    enable_data_checksums: bool = Field(default=True, description="Enable data integrity checks")
    enable_encryption_at_rest: bool = Field(default=True, description="Encrypt data at rest")


class SecurityConfig(BaseSettings):
    """
    Master security configuration
    Loads from environment variables with fallback to defaults
    """
    # Environment
    environment: str = Field(default="development", description="Environment: development/staging/production")
    debug: bool = Field(default=False, description="Debug mode (disable in production)")

    # Crypto Configuration
    crypto: CryptoConfig = Field(default_factory=CryptoConfig)

    # JWT Configuration
    jwt_secret_key: SecretStr = Field(..., env="JWT_SECRET_KEY")
    jwt: Optional[JWTSecurityConfig] = None

    # API Vault Configuration
    api_vault_master_key: SecretStr = Field(..., env="API_VAULT_MASTER_KEY")
    api_vault: Optional[APIVaultConfig] = None

    # RBAC Configuration
    rbac: RBACConfig = Field(default_factory=RBACConfig)

    # Session Configuration
    session: SessionConfig = Field(default_factory=SessionConfig)

    # Compliance Configuration
    compliance: ComplianceConfig = Field(default_factory=ComplianceConfig)

    # CORS Configuration
    cors_enabled: bool = Field(default=True, description="Enable CORS")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins"
    )

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_per_minute: int = Field(default=60, description="Requests per minute per IP")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format: json/text")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        env_nested_delimiter = "__"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize JWT config from secret key if not provided
        if self.jwt is None:
            self.jwt = JWTSecurityConfig(secret_key=self.jwt_secret_key)

        # Initialize API vault config from master key if not provided
        if self.api_vault is None:
            vault_path = None
            if self.environment == "production":
                vault_path = Path("/var/lib/pv-test-report/api_vault.json")

            self.api_vault = APIVaultConfig(
                vault_master_key=self.api_vault_master_key,
                storage_path=vault_path
            )

    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment value"""
        allowed = ['development', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v

    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level"""
        allowed = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v.upper()

    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "development"

    def get_jwt_config(self) -> JWTSecurityConfig:
        """Get JWT configuration"""
        if self.jwt is None:
            raise ValueError("JWT configuration not initialized")
        return self.jwt

    def get_api_vault_config(self) -> APIVaultConfig:
        """Get API vault configuration"""
        if self.api_vault is None:
            raise ValueError("API vault configuration not initialized")
        return self.api_vault


# Singleton configuration instance
_config: Optional[SecurityConfig] = None


def get_security_config() -> SecurityConfig:
    """
    Get global security configuration instance

    Returns:
        SecurityConfig instance
    """
    global _config
    if _config is None:
        _config = load_security_config()
    return _config


def load_security_config(env_file: Optional[str] = None) -> SecurityConfig:
    """
    Load security configuration from environment

    Args:
        env_file: Optional path to .env file

    Returns:
        SecurityConfig instance
    """
    if env_file:
        return SecurityConfig(_env_file=env_file)
    return SecurityConfig()


def reset_security_config() -> None:
    """Reset global configuration (mainly for testing)"""
    global _config
    _config = None


# Development/Testing Helper
def get_test_security_config() -> SecurityConfig:
    """
    Get test security configuration with safe defaults

    Returns:
        SecurityConfig for testing
    """
    return SecurityConfig(
        environment="development",
        debug=True,
        jwt_secret_key=SecretStr("test_jwt_secret_key_minimum_32_characters_long_for_testing"),
        api_vault_master_key=SecretStr("test_vault_key_minimum_32_chars_long"),
        cors_origins=["*"],
        rate_limit_enabled=False
    )
