# PV Test Report Automation System

World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## Features

### Security Core (Phase 1 - Session 03) ✅
Complete security infrastructure with:
- **Encryption**: AES-256-CBC, Fernet vault, bcrypt password hashing
- **Authentication**: JWT tokens, OAuth2, token refresh, API keys
- **Authorization**: Role-Based Access Control (RBAC) with 7 predefined roles
- **API Key Vault**: Secure encrypted storage for LLM API keys (Claude, OpenAI, Gemini)
- **Compliance**: ISO 17025 and 21 CFR Part 11 compliant
- **Audit Logging**: Comprehensive audit trail for all security operations

### Roles & Permissions
- **Admin**: Full system access
- **Lab Manager**: Laboratory operations and personnel management
- **Technician**: Test execution and report creation
- **Reviewer**: Technical review and validation
- **Approver**: Final approval authority (21 CFR Part 11)
- **Auditor**: Quality auditing and compliance monitoring
- **Viewer**: Read-only access

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration
```

### Generate Security Keys

```bash
# Generate JWT secret key
python -c "import secrets; print(f'JWT_SECRET_KEY={secrets.token_urlsafe(64)}')"

# Generate API vault master key
python -c "from cryptography.fernet import Fernet; print(f'API_VAULT_MASTER_KEY={Fernet.generate_key().decode()}')"
```

### Basic Usage

```python
from src.security import (
    AESCipher,
    PasswordHasher,
    JWTManager,
    JWTConfig,
    get_rbac_manager,
    APIKeyVault,
    LLMProvider
)

# Encrypt sensitive data
cipher = AESCipher()
encrypted = cipher.encrypt("sensitive data")
decrypted = cipher.decrypt(encrypted)

# Hash passwords
hasher = PasswordHasher()
password_hash = hasher.hash_password("user_password")

# Create JWT tokens
config = JWTConfig(secret_key="your-secret-key-minimum-32-chars")
jwt_manager = JWTManager(config)
token = jwt_manager.create_access_token(user)

# Manage API keys
vault = APIKeyVault()
key_id = vault.add_key(
    provider=LLMProvider.ANTHROPIC,
    api_key="sk-ant-...",
    name="Production Claude",
    created_by="admin"
)
```

## Project Structure

```
pv-test-report-automation/
├── src/
│   ├── security/              # Security core module
│   │   ├── __init__.py       # Module exports
│   │   ├── crypto.py         # Encryption and hashing
│   │   ├── auth.py           # JWT authentication
│   │   ├── rbac.py           # Role-based access control
│   │   ├── api_vault.py      # API key vault
│   │   ├── config.py         # Security configuration
│   │   └── README.md         # Security documentation
│   └── __init__.py
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
├── .gitignore
├── LICENSE
└── README.md
```

## Security & Compliance

### ISO 17025 Compliance
- **Access Control**: Hierarchical role-based permissions
- **Audit Trail**: Comprehensive logging of all operations
- **Data Integrity**: Encryption at rest and in transit
- **User Management**: Secure authentication and authorization

### 21 CFR Part 11 Compliance
- **Electronic Signatures**: Support for digital signatures with reasons
- **Audit Trails**: Secure, time-stamped, computer-generated audit logs
- **System Access**: Limited to authorized individuals
- **Authority Checks**: Verification of user permissions
- **Operational Checks**: User identity verification

## Documentation

- [Security Module Documentation](src/security/README.md)
- [Configuration Guide](.env.example)

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
black src/

# Lint code
flake8 src/
pylint src/

# Type checking
mypy src/
```

## Roadmap

- [x] Phase 1 Session 03: Security Core Implementation
- [ ] Phase 1 Session 04: Database models and migrations
- [ ] Phase 1 Session 05: Test execution engine
- [ ] Phase 2: LLM integration for report generation
- [ ] Phase 3: Multi-format export (PDF, Excel, Word)
- [ ] Phase 4: Web interface and API

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

## License

See [LICENSE](LICENSE) file for details.

## Support

For issues and questions, please use the GitHub issue tracker.
