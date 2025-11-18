# Configuration Management System

This directory contains the configuration management system for the PV Test Report Automation project.

## Overview

The configuration system provides:
- **Application Settings**: Environment-based configuration using Pydantic
- **Standards Configuration**: IEC/ISO standards definitions in YAML format
- **Type Safety**: Full type hints and validation
- **Environment Variables**: Support for `.env` files and environment-specific configs
- **Production Ready**: Caching, validation, and best practices built-in

## Files

### `standards_config.yaml`
Comprehensive YAML configuration containing:
- **IEC 61215 Series**: Design qualification and type approval standards
- **IEC 61730**: Module safety qualification
- **IEC 61853**: Performance testing and energy rating
- **IEC 62804**: Potential-induced degradation (PID) testing
- **IEC 60904**: Photovoltaic device measurements
- **ISO/IEC 17025**: Laboratory accreditation requirements
- **Test Parameters**: Environmental conditions, acceptance criteria
- **Reporting Standards**: Required sections, data formatting

### `settings.py`
Python settings module featuring:
- **Pydantic BaseSettings**: Type-safe configuration with validation
- **Environment Variables**: Automatic loading from `.env` files
- **LLM Configuration**: Claude, OpenAI, Gemini API settings
- **Database Settings**: SQLAlchemy connection configuration
- **Security Settings**: JWT, passwords, CORS
- **File Storage**: Upload, reports, templates directories
- **Email/SMTP**: Email notification configuration
- **Caching**: Redis configuration
- **Background Tasks**: Celery configuration
- **Feature Flags**: Enable/disable system features

### `__init__.py`
Module initialization providing:
- Clean imports for the entire config module
- Exported functions and settings instances
- Version information

## Usage

### Basic Usage

```python
from src.config import settings, standards_config

# Access application settings
print(settings.database_url)
print(settings.upload_dir)
print(settings.company_name)

# Access standards configuration
iec_61215 = standards_config['standards']['iec_61215']
print(iec_61215['title'])
print(iec_61215['test_sequence']['mst_tests'])
```

### Helper Functions

```python
from src.config import (
    get_standard_info,
    get_test_info,
    get_upload_path,
    get_report_path,
    ensure_directories,
    validate_environment
)

# Get information about a standard
standard = get_standard_info('iec_61215', standards_config)
print(standard['version'])

# Get information about a specific test
test = get_test_info('iec_61215', 'MST 10', standards_config)
print(f"{test['name']}: {test['duration_days']} days, {test['cycles']} cycles")

# Get file paths
upload_path = get_upload_path('test_data.xlsx')
report_path = get_report_path('report_2024_001.pdf')

# Ensure all directories exist
ensure_directories()

# Validate environment configuration
warnings = validate_environment()
for warning in warnings:
    print(warning)
```

### Environment-Specific Configuration

```python
# In development
# .env contains: ENVIRONMENT=development
# settings.debug will be True, uses SQLite, etc.

# In production
# .env contains: ENVIRONMENT=production
# settings.debug will be False, uses PostgreSQL, etc.
```

### Accessing LLM APIs

```python
from src.config import settings

# Check which LLM is configured
if settings.claude_api_key.get_secret_value():
    # Use Claude API
    api_key = settings.claude_api_key.get_secret_value()
    model = settings.claude_model
```

### Standards Configuration Examples

```python
from src.config import standards_config

# Get all test codes for IEC 61215
iec_61215 = standards_config['standards']['iec_61215']
for group_name, tests in iec_61215['test_groups'].items():
    print(f"\n{group_name}:")
    for test in tests:
        print(f"  {test['code']}: {test['name']}")

# Get acceptance criteria
criteria = iec_61215['acceptance_criteria']
print(f"Max power degradation: {criteria['power_degradation_max_percent']}%")

# Get climate zones for IEC 61853
iec_61853 = standards_config['standards']['iec_61853']
for zone in iec_61853['climate_zones']:
    print(f"{zone['code']}: {zone['name']} - {zone['characteristics']}")
```

## Environment Setup

### 1. Copy Example Environment File

```bash
cp .env.example .env
```

### 2. Configure Required Variables

Edit `.env` and set at minimum:

```bash
# Generate a strong secret key
SECRET_KEY="your-secret-key-here"

# Set your database (for production)
DATABASE_URL="postgresql://user:pass@localhost/pv_test"

# Add your LLM API key(s)
CLAUDE_API_KEY="your-claude-api-key"

# Set company information
COMPANY_NAME="Your Lab Name"
NABL_CERT_NUMBER="TC-1234"
```

### 3. Create Required Directories

```bash
mkdir -p uploads reports templates temp archive logs
```

Or use Python:

```python
from src.config import ensure_directories
ensure_directories()
```

## Configuration Validation

The system includes built-in validation to check for common issues:

```python
from src.config import validate_environment

warnings = validate_environment()
if warnings:
    for warning in warnings:
        print(f"⚠️  {warning}")
else:
    print("✅ Configuration is valid")
```

Common validation checks:
- Production environment with default secret key
- Debug mode enabled in production
- Missing LLM API keys when AI features enabled
- SQLite database in production
- Missing NABL certification details

## Testing Configuration

Run the settings module directly to test configuration:

```bash
python src/config/settings.py
```

Output example:
```
================================================================================
PV Test Report Automation - Configuration Validation
================================================================================

Environment: development
Debug: False
Database: sqlite:///./pv_test.db
Upload Directory: uploads
Reports Directory: reports

✓ No configuration warnings

Standards Configuration:
  Loaded 13 standards
  Standards: iec_61215, iec_61215_1, iec_61215_1_1, iec_61215_1_2, iec_61215_1_3...

IEC 61215 Information:
  Title: Terrestrial photovoltaic (PV) modules - Design qualification and type approval
  Version: 2021
  MST Tests: 19

✓ All required directories created/verified

================================================================================
```

## Production Deployment

### 1. Security Checklist

- [ ] Generate strong `SECRET_KEY` (32+ characters)
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=False`
- [ ] Use PostgreSQL or MySQL (not SQLite)
- [ ] Configure proper SMTP settings
- [ ] Set up Redis for caching
- [ ] Configure Sentry for error tracking
- [ ] Update `CORS_ORIGINS` with actual frontend URLs
- [ ] Store API keys in secrets manager (AWS Secrets Manager, Vault, etc.)
- [ ] Enable rate limiting
- [ ] Configure SSL/TLS certificates

### 2. Environment Variables

Production `.env` example:

```bash
ENVIRONMENT=production
DEBUG=False
SECRET_KEY="generate-with-python-secrets-module"
DATABASE_URL="postgresql://user:pass@db.example.com/pv_test"
REDIS_URL="redis://cache.example.com:6379/0"
SENTRY_DSN="https://your-sentry-dsn"
CORS_ORIGINS="https://app.example.com,https://www.example.com"
```

### 3. Secrets Management

For production, use a secrets management system:

```python
# Example: AWS Secrets Manager
import boto3
import json

def load_secrets():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='pv-test-automation')
    secrets = json.loads(response['SecretString'])

    os.environ['SECRET_KEY'] = secrets['secret_key']
    os.environ['DATABASE_URL'] = secrets['database_url']
    os.environ['CLAUDE_API_KEY'] = secrets['claude_api_key']
```

## Standards Configuration

### Adding a New Standard

To add a new IEC/ISO standard:

1. Edit `standards_config.yaml`
2. Add the standard under the `standards:` section
3. Follow the existing structure:

```yaml
standards:
  iec_xxxxx:
    version: "2024"
    full_name: "IEC XXXXX:2024"
    title: "Standard title here"
    scope: "What this standard covers"

    parts:
      - number: 1
        title: "Part 1 title"
        description: "Description"

    tests:
      - code: "TEST 01"
        name: "Test name"
        duration_hours: 24
```

### Updating Test Parameters

To modify test parameters or acceptance criteria:

```yaml
test_parameters:
  environmental_conditions:
    standard_test_conditions:
      irradiance_wm2: 1000
      module_temperature_c: 25
      air_mass: 1.5
```

## Type Safety

All settings are fully typed using Pydantic:

```python
from src.config import settings

# These are type-checked and validated
database_url: str = settings.database_url
upload_dir: Path = settings.upload_dir
max_upload_size: int = settings.max_upload_size_mb
debug: bool = settings.debug

# Secret strings are protected
api_key = settings.claude_api_key.get_secret_value()  # str
```

## Caching

Settings and standards configuration are cached using `@lru_cache()`:

```python
from src.config import get_settings, get_standards_config

# These calls return the same cached instances
settings1 = get_settings()
settings2 = get_settings()
assert settings1 is settings2  # True

config1 = get_standards_config()
config2 = get_standards_config()
assert config1 is config2  # True
```

## Best Practices

1. **Never commit `.env` files** - Add to `.gitignore`
2. **Use environment-specific configs** - `.env.dev`, `.env.prod`
3. **Rotate secrets regularly** - Update API keys, tokens
4. **Validate on startup** - Call `validate_environment()` during app init
5. **Use Path objects** - For all file/directory settings
6. **Type hints everywhere** - Leverage Pydantic's validation
7. **Document changes** - Update this README when adding settings
8. **Test configuration** - Run validation before deploying

## Troubleshooting

### Issue: Settings not loading from .env

**Solution**: Ensure `.env` file exists in project root and contains valid key=value pairs

```bash
# Check if .env exists
ls -la .env

# Validate .env syntax
cat .env
```

### Issue: YAML parsing errors

**Solution**: Validate YAML syntax

```bash
# Install yamllint
pip install yamllint

# Check YAML file
yamllint src/config/standards_config.yaml
```

### Issue: Missing directories

**Solution**: Run ensure_directories()

```python
from src.config import ensure_directories
ensure_directories()
```

### Issue: Secret key warnings in production

**Solution**: Generate a proper secret key

```python
import secrets
print(secrets.token_urlsafe(32))
```

Then set in `.env`:
```bash
SECRET_KEY="generated-key-here"
```

## Contributing

When adding new configuration options:

1. Add to `Settings` class in `settings.py`
2. Add to `.env.example` with description
3. Update this README
4. Add validation if needed
5. Update tests

## Related Documentation

- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/usage/settings/)
- [IEC 61215:2021 Standard](https://webstore.iec.ch/publication/61347)
- [IEC 61730:2023 Standard](https://webstore.iec.ch/publication/68549)
- [ISO/IEC 17025:2017](https://www.iso.org/standard/66912.html)

## Version History

- **v1.0.0** (2025-11-18): Initial configuration management system
  - Comprehensive IEC/ISO standards coverage
  - Pydantic-based settings
  - Environment variable support
  - Production-ready validation
