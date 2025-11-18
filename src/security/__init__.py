"""
PV Test Report Automation - Security Module
ISO 17025 and 21 CFR Part 11 Compliant Security Infrastructure

This module provides comprehensive security features including:
- Encryption (AES-256-CBC, Fernet)
- Password hashing (bcrypt)
- JWT authentication with OAuth2
- Role-Based Access Control (RBAC)
- Secure API key vault for LLM keys

Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "PV Test Report Automation Team"

# ==========================================
# Cryptography Module
# ==========================================
from .crypto import (
    # Core cipher classes
    AESCipher,
    PasswordHasher,
    FernetVault,
    KeyDerivation,
    SecureRandom,

    # Exceptions
    EncryptionError,
    DecryptionError,
    KeyDerivationError,

    # Enums
    CryptoAlgorithm,

    # Audit logging
    AuditLogger,
    get_audit_logger,
)

# ==========================================
# Authentication Module
# ==========================================
from .auth import (
    # Core classes
    JWTManager,
    JWTConfig,
    AuthenticationService,

    # Models
    User,
    UserInDB,
    TokenPayload,
    TokenResponse,

    # Enums
    TokenType,
    TokenStatus,

    # Exceptions
    AuthenticationError,
    TokenExpiredError,
    InvalidTokenError,
    InsufficientPermissionsError,

    # FastAPI dependencies
    oauth2_scheme,
    http_bearer,
    get_current_user,
    get_current_active_user,
    require_scopes,
    require_roles,
)

# ==========================================
# RBAC Module
# ==========================================
from .rbac import (
    # Core classes
    RBACManager,
    get_rbac_manager,

    # Models
    RoleDefinition,
    PermissionCheck,

    # Enums
    Role,
    Permission,

    # Role definitions
    ROLE_DEFINITIONS,

    # Decorators
    require_permission,
    require_any_permission,
    require_role,
)

# ==========================================
# API Vault Module
# ==========================================
from .api_vault import (
    # Core classes
    APIKeyVault,
    create_vault_from_env,

    # Models
    APIKeyMetadata,
    StoredAPIKey,

    # Enums
    LLMProvider,
    APIKeyStatus,

    # Exceptions
    APIKeyError,
    APIKeyNotFoundError,
    APIKeyExpiredError,
)


# ==========================================
# Public API
# ==========================================
__all__ = [
    # Version
    "__version__",
    "__author__",

    # Crypto
    "AESCipher",
    "PasswordHasher",
    "FernetVault",
    "KeyDerivation",
    "SecureRandom",
    "EncryptionError",
    "DecryptionError",
    "KeyDerivationError",
    "CryptoAlgorithm",
    "AuditLogger",
    "get_audit_logger",

    # Auth
    "JWTManager",
    "JWTConfig",
    "AuthenticationService",
    "User",
    "UserInDB",
    "TokenPayload",
    "TokenResponse",
    "TokenType",
    "TokenStatus",
    "AuthenticationError",
    "TokenExpiredError",
    "InvalidTokenError",
    "InsufficientPermissionsError",
    "oauth2_scheme",
    "http_bearer",
    "get_current_user",
    "get_current_active_user",
    "require_scopes",
    "require_roles",

    # RBAC
    "RBACManager",
    "get_rbac_manager",
    "RoleDefinition",
    "PermissionCheck",
    "Role",
    "Permission",
    "ROLE_DEFINITIONS",
    "require_permission",
    "require_any_permission",
    "require_role",

    # API Vault
    "APIKeyVault",
    "create_vault_from_env",
    "APIKeyMetadata",
    "StoredAPIKey",
    "LLMProvider",
    "APIKeyStatus",
    "APIKeyError",
    "APIKeyNotFoundError",
    "APIKeyExpiredError",
]


# ==========================================
# Module Initialization
# ==========================================
def get_security_info() -> dict:
    """
    Get information about the security module

    Returns:
        Dictionary with module information
    """
    return {
        "version": __version__,
        "modules": {
            "crypto": "AES-256-CBC, Fernet, bcrypt, PBKDF2-HMAC-SHA256",
            "auth": "JWT, OAuth2, Password Bearer",
            "rbac": "Role-Based Access Control with 7 predefined roles",
            "api_vault": "Encrypted storage for LLM API keys",
        },
        "compliance": ["ISO 17025", "21 CFR Part 11"],
        "supported_llm_providers": [
            "Anthropic (Claude)",
            "OpenAI (GPT)",
            "Google (Gemini)",
            "Cohere",
            "HuggingFace",
            "Azure OpenAI",
        ],
        "roles": [role.value for role in Role],
        "encryption_algorithms": [algo.value for algo in CryptoAlgorithm],
    }


def validate_security_setup() -> dict:
    """
    Validate security module setup and configuration

    Returns:
        Dictionary with validation results
    """
    results = {
        "crypto_module": False,
        "auth_module": False,
        "rbac_module": False,
        "api_vault_module": False,
        "errors": [],
    }

    try:
        # Test crypto module
        cipher = AESCipher()
        test_data = "test_encryption"
        encrypted = cipher.encrypt(test_data)
        decrypted = cipher.decrypt(encrypted)
        results["crypto_module"] = (test_data == decrypted)
    except Exception as e:
        results["errors"].append(f"Crypto module error: {str(e)}")

    try:
        # Test auth module
        from datetime import timedelta
        config = JWTConfig(
            secret_key="test_secret_key_minimum_32_characters_long",
            access_token_expire_minutes=30
        )
        jwt_manager = JWTManager(config)
        results["auth_module"] = True
    except Exception as e:
        results["errors"].append(f"Auth module error: {str(e)}")

    try:
        # Test RBAC module
        rbac = get_rbac_manager()
        test_user = User(
            user_id="test",
            username="test",
            email="test@example.com",
            roles=[Role.TECHNICIAN.value],
            scopes=[Permission.CREATE_TEST.value]
        )
        has_perm = rbac.has_permission(test_user, Permission.CREATE_TEST, log_check=False)
        results["rbac_module"] = has_perm
    except Exception as e:
        results["errors"].append(f"RBAC module error: {str(e)}")

    try:
        # Test API vault module
        vault = APIKeyVault()
        results["api_vault_module"] = True
    except Exception as e:
        results["errors"].append(f"API vault module error: {str(e)}")

    results["all_passed"] = all([
        results["crypto_module"],
        results["auth_module"],
        results["rbac_module"],
        results["api_vault_module"],
    ])

    return results


# ==========================================
# ISO 17025 and 21 CFR Part 11 Compliance
# ==========================================
COMPLIANCE_FEATURES = {
    "ISO_17025": {
        "access_control": "Role-based access control with hierarchical permissions",
        "audit_trail": "Comprehensive audit logging for all security operations",
        "data_integrity": "Encryption at rest and in transit",
        "user_management": "User authentication and authorization",
    },
    "CFR_PART_11": {
        "electronic_signatures": "Support for electronic signatures on reports",
        "audit_trails": "Secure, computer-generated, time-stamped audit trails",
        "system_access": "Limited system access to authorized individuals",
        "authority_checks": "Verification of authority to access and modify records",
        "operational_checks": "Determination that persons are who they claim to be",
        "device_checks": "Use of secure, time-stamped audit trails",
    }
}


def get_compliance_status() -> dict:
    """
    Get compliance status for ISO 17025 and 21 CFR Part 11

    Returns:
        Dictionary with compliance feature status
    """
    return {
        "compliant_standards": ["ISO 17025", "21 CFR Part 11"],
        "features": COMPLIANCE_FEATURES,
        "last_updated": "2025-11-18",
        "version": __version__,
    }
