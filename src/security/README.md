# Security Module Documentation

## Overview

The security module provides comprehensive security infrastructure for the PV Test Report Automation system, ensuring compliance with **ISO 17025** and **21 CFR Part 11** standards.

## Features

### 1. Cryptography (`crypto.py`)
- **AES-256-CBC Encryption**: NIST FIPS 197 compliant symmetric encryption
- **Bcrypt Password Hashing**: OWASP-compliant password storage with configurable work factor
- **Fernet Vault**: Authenticated encryption with timestamp verification
- **PBKDF2-HMAC Key Derivation**: NIST SP 800-132 compliant key generation from passwords
- **Secure Random Generation**: Cryptographically secure tokens, PINs, and random data
- **Audit Logging**: Comprehensive logging of all cryptographic operations

### 2. Authentication (`auth.py`)
- **JWT Token Management**: Access tokens, refresh tokens, and API keys
- **OAuth2 Password Bearer**: FastAPI-compatible OAuth2 implementation
- **Token Refresh Logic**: Secure token rotation and renewal
- **User Management**: Registration, authentication, password changes
- **FastAPI Dependencies**: Ready-to-use route protection decorators

### 3. Role-Based Access Control (`rbac.py`)
- **7 Predefined Roles**:
  - **Admin**: Full system access
  - **Lab Manager**: Laboratory operations and personnel management
  - **Technician**: Test execution and report creation
  - **Reviewer**: Technical review and validation
  - **Approver**: Final approval authority
  - **Auditor**: Quality auditing and compliance
  - **Viewer**: Read-only access

- **Granular Permissions**:
  - Test management (create, execute, view, edit, delete)
  - Report management (create, review, approve, publish, sign)
  - Audit operations (view, export, manage)
  - User management (create, edit, delete, assign roles)
  - Equipment management (create, edit, delete, calibrate)
  - System configuration
  - Data management
  - Quality control

### 4. API Key Vault (`api_vault.py`)
- **Encrypted Storage**: Fernet/AES-256 encryption at rest
- **LLM Provider Support**:
  - Anthropic (Claude)
  - OpenAI (GPT)
  - Google (Gemini)
  - Cohere
  - HuggingFace
  - Azure OpenAI
  - Custom providers

- **Key Management**:
  - Key rotation policies
  - Expiration tracking
  - Usage statistics
  - Environment isolation
  - Tag-based organization

### 5. Configuration (`config.py`)
- **Environment-based Configuration**: Separate settings for dev/staging/prod
- **Validation**: Pydantic-based configuration validation
- **Security Best Practices**: Enforced strong keys and secure defaults

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Generate secure keys
python -c "import secrets; print(f'JWT_SECRET_KEY={secrets.token_urlsafe(32)}')"
python -c "from cryptography.fernet import Fernet; print(f'API_VAULT_MASTER_KEY={Fernet.generate_key().decode()}')"
```

## Quick Start

### 1. Basic Encryption

```python
from src.security import AESCipher, PasswordHasher

# AES encryption
cipher = AESCipher()
encrypted = cipher.encrypt("sensitive data")
decrypted = cipher.decrypt(encrypted)

# Password hashing
hasher = PasswordHasher()
password_hash = hasher.hash_password("user_password")
is_valid = hasher.verify_password("user_password", password_hash)
```

### 2. JWT Authentication

```python
from src.security import JWTManager, JWTConfig, User
from datetime import timedelta

# Configure JWT
config = JWTConfig(
    secret_key="your-secret-key-at-least-32-characters",
    access_token_expire_minutes=30
)
jwt_manager = JWTManager(config)

# Create user
user = User(
    user_id="user123",
    username="johndoe",
    email="john@example.com",
    roles=["technician"],
    scopes=["create_test", "execute_test"]
)

# Generate tokens
access_token = jwt_manager.create_access_token(user, fresh=True)
refresh_token = jwt_manager.create_refresh_token(user)

# Verify token
payload = jwt_manager.verify_token(access_token)
```

### 3. Role-Based Access Control

```python
from src.security import get_rbac_manager, Role, Permission, User

rbac = get_rbac_manager()

# Create user with role
user = User(
    user_id="tech001",
    username="technician1",
    email="tech@lab.com",
    roles=[Role.TECHNICIAN.value]
)

# Check permissions
can_create = rbac.has_permission(user, Permission.CREATE_TEST)
can_approve = rbac.has_permission(user, Permission.APPROVE_REPORT)

# Use decorators in FastAPI
from fastapi import Depends
from src.security import require_permission

@app.post("/tests")
@require_permission(Permission.CREATE_TEST)
async def create_test(user: User = Depends(get_current_user)):
    # Only users with CREATE_TEST permission can access
    pass
```

### 4. API Key Vault

```python
from src.security import APIKeyVault, LLMProvider
from pathlib import Path

# Create vault
vault = APIKeyVault(storage_path=Path("vault.json"))

# Add API key
key_id = vault.add_key(
    provider=LLMProvider.ANTHROPIC,
    api_key="sk-ant-your-api-key",
    name="Production Claude Key",
    created_by="admin",
    environment="production",
    rotation_policy_days=90
)

# Retrieve API key
api_key = vault.get_key(key_id, user_id="system")

# Get key by provider
claude_key = vault.get_key_by_provider(
    LLMProvider.ANTHROPIC,
    environment="production"
)

# List all keys
keys = vault.list_keys(provider=LLMProvider.ANTHROPIC)

# Rotate key
vault.rotate_key(key_id, "new-api-key-value", rotated_by="admin")
```

### 5. FastAPI Integration

```python
from fastapi import FastAPI, Depends
from src.security import (
    get_current_user,
    get_current_active_user,
    require_permission,
    require_role,
    User,
    Permission,
    Role
)

app = FastAPI()

# Protected endpoint - any authenticated user
@app.get("/profile")
async def get_profile(user: User = Depends(get_current_user)):
    return {"user_id": user.user_id, "username": user.username}

# Protected endpoint - specific permission
@app.post("/tests")
@require_permission(Permission.CREATE_TEST)
async def create_test(user: User = Depends(get_current_active_user)):
    return {"message": "Test created"}

# Protected endpoint - specific role
@app.post("/users")
@require_role(Role.ADMIN)
async def create_user(user: User = Depends(get_current_active_user)):
    return {"message": "User created"}

# Multiple permissions (any)
from src.security import require_any_permission

@app.put("/reports/{report_id}")
@require_any_permission([Permission.EDIT_REPORT, Permission.REVIEW_REPORT])
async def update_report(report_id: str, user: User = Depends(get_current_active_user)):
    return {"message": "Report updated"}
```

## Compliance Features

### ISO 17025 Compliance
- **Access Control**: Hierarchical role-based permissions
- **Audit Trail**: Comprehensive logging of all operations
- **Data Integrity**: Encryption and checksums
- **User Management**: Authentication and authorization

### 21 CFR Part 11 Compliance
- **Electronic Signatures**: Support for e-signatures with reasons
- **Audit Trails**: Secure, time-stamped audit logs
- **System Access**: Limited to authorized users
- **Authority Checks**: Role and permission verification
- **Operational Checks**: User identity verification

## Security Best Practices

### Production Deployment
1. **Generate Strong Keys**:
   ```bash
   # JWT secret (minimum 32 characters)
   python -c "import secrets; print(secrets.token_urlsafe(64))"

   # Fernet key for API vault
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

2. **Environment Variables**: Never commit `.env` files
3. **HTTPS Only**: Always use HTTPS in production
4. **Secure Cookies**: Enable `secure` and `httponly` flags
5. **Rate Limiting**: Enable rate limiting to prevent abuse
6. **Audit Logs**: Regularly review audit logs
7. **Key Rotation**: Implement regular key rotation policies

### Password Requirements
- Minimum length: 8 characters (recommend 12+)
- Complexity: Mix of uppercase, lowercase, numbers, symbols
- Bcrypt rounds: 12 (configurable via `CRYPTO__BCRYPT_ROUNDS`)

### Token Security
- Access tokens: Short-lived (default 30 minutes)
- Refresh tokens: Longer-lived (default 7 days)
- API keys: Long-lived with rotation policy
- Store tokens securely (httponly cookies or secure storage)

## Testing

```python
# Run security validation
from src.security import validate_security_setup

results = validate_security_setup()
print(f"All tests passed: {results['all_passed']}")

# Get security info
from src.security import get_security_info

info = get_security_info()
print(f"Security version: {info['version']}")
print(f"Supported roles: {info['roles']}")
```

## API Reference

### Crypto Module
- `AESCipher`: AES-256-CBC encryption
- `PasswordHasher`: Bcrypt password hashing
- `FernetVault`: Fernet symmetric encryption
- `KeyDerivation`: PBKDF2-HMAC key derivation
- `SecureRandom`: Cryptographically secure random generation

### Auth Module
- `JWTManager`: JWT token management
- `AuthenticationService`: Complete authentication service
- `User`, `UserInDB`: User models
- `TokenPayload`, `TokenResponse`: Token models

### RBAC Module
- `RBACManager`: Role and permission management
- `Role`: Predefined roles enum
- `Permission`: System permissions enum
- `require_permission`, `require_role`: FastAPI decorators

### API Vault Module
- `APIKeyVault`: Encrypted API key storage
- `LLMProvider`: Supported LLM providers
- `APIKeyMetadata`: Key metadata and tracking

## Troubleshooting

### Common Issues

1. **"Invalid key size" error**
   - Ensure JWT secret is at least 32 characters
   - Verify API vault master key is valid Fernet key

2. **"Token expired" error**
   - Check system clock synchronization
   - Adjust token expiration settings if needed

3. **"Permission denied" error**
   - Verify user has correct roles/permissions
   - Check RBAC configuration

4. **"API key not found" error**
   - Ensure key exists in vault
   - Check environment filter (dev/staging/prod)

## License

Copyright (c) 2025 PV Test Report Automation Team
