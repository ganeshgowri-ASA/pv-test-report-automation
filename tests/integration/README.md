# Integration Test Suite
## PV Test Report Automation System

This integration test suite provides comprehensive testing coverage for the PV test lab report automation system, ensuring ISO 17025/NABL compliance and robust integration between modules.

## Directory Structure

```
tests/integration/
├── conftest.py                          # Shared fixtures and configuration
├── README.md                            # This file
├── foundation/
│   ├── test_database_integration.py     # Database models and relationships
│   ├── test_config_integration.py       # Configuration management
│   ├── test_security_integration.py     # Security and authentication
│   └── test_audit_trail_integration.py  # Audit trail and data lineage
├── data_ingestion/
│   ├── test_excel_ingestion.py          # Excel file ingestion
│   ├── test_document_ingestion.py       # Word/PDF ingestion
│   ├── test_image_ingestion.py          # Image processing and OCR
│   └── test_storage_integration.py      # Data storage and retrieval
├── protocols/
│   ├── test_iec_61215_integration.py    # IEC 61215 protocol
│   ├── test_iec_61730_integration.py    # IEC 61730 protocol
│   └── test_protocol_compliance.py      # Cross-protocol compliance
├── test_blocks/
│   ├── test_iv_curve_integration.py     # I-V curve analysis
│   ├── test_el_detection_integration.py # EL defect detection
│   └── test_equipment_integration.py    # Equipment interfaces
├── workflow/
│   ├── test_review_workflow.py          # Review and approval workflow
│   ├── test_notification_integration.py # Notification system
│   └── test_calibration_integration.py  # Calibration tracking
├── llm/
│   ├── test_llm_integration.py          # LLM API integrations
│   └── test_compliance_checker.py       # LLM compliance checking
├── export/
│   ├── test_pdf_export_integration.py   # PDF export
│   ├── test_excel_export_integration.py # Excel export
│   └── test_multi_format_export.py      # Multi-format export
└── ui/
    ├── test_streamlit_ui_integration.py # Streamlit UI
    └── test_api_endpoints.py            # API endpoint integration
```

## Running Tests

### Run All Integration Tests
```bash
pytest tests/integration/ -v
```

### Run Specific Test Category
```bash
# Database integration tests
pytest tests/integration/foundation/test_database_integration.py -v

# LLM integration tests
pytest tests/integration/llm/ -v -m llm

# Compliance tests only
pytest tests/integration/ -v -m compliance

# Skip slow tests
pytest tests/integration/ -v -m "not slow"
```

### Run by Marker
```bash
# Run only database tests
pytest tests/integration/ -v -m database

# Run only security tests
pytest tests/integration/ -v -m security

# Run API tests
pytest tests/integration/ -v -m api
```

### Generate Coverage Report
```bash
pytest tests/integration/ --cov=src --cov-report=html --cov-report=term
```

## Test Markers

Tests are categorized using pytest markers:

- `@pytest.mark.integration` - Integration tests requiring multiple modules
- `@pytest.mark.database` - Tests requiring database connection
- `@pytest.mark.api` - Tests requiring API endpoints
- `@pytest.mark.llm` - Tests requiring LLM API integration
- `@pytest.mark.compliance` - Tests verifying ISO 17025/NABL compliance
- `@pytest.mark.slow` - Tests that take significant time (>5s)
- `@pytest.mark.security` - Security-related tests

## Configuration

### Environment Variables

Create a `.env.test` file:

```bash
# Database
TEST_DATABASE_URL=postgresql://test_user:test_pass@localhost:5432/pv_test_db

# API
TEST_API_BASE_URL=http://localhost:8000

# LLM APIs (use test/mock keys)
ANTHROPIC_API_KEY=test-claude-key
OPENAI_API_KEY=test-gpt-key
GOOGLE_API_KEY=test-gemini-key

# Security
JWT_SECRET_KEY=test-jwt-secret-key
ENCRYPTION_KEY=test-encryption-key

# ISO 17025 Mode
ISO_17025_MODE=true
NABL_MODE=true

# Logging
LOG_LEVEL=DEBUG
```

### Test Data

Sample test data is provided in fixtures (`conftest.py`):

- `sample_pv_module_data` - PV module specifications
- `sample_test_configuration` - IEC test configuration
- `sample_calibration_data` - Equipment calibration data
- `sample_iv_curve_data` - I-V curve measurements
- `sample_el_image_defects` - EL defect detection results
- `sample_audit_trail` - Audit trail entries

## Current Implementation Status

### ✅ Ready to Run (Fixtures and Configuration)
- `conftest.py` - All fixtures and configuration ready
- Test data generators
- Database session management
- Mock LLM responses

### ⚠️ Skipped (Awaiting Implementation)
Most tests are currently skipped with informative messages indicating which branch needs to be implemented first. Example:

```python
pytest.skip("ClaudeAPIClient not yet implemented (Branch 34) - SECURITY CRITICAL")
```

### 🔴 Critical Priority Tests
1. **Security Tests** - `test_llm_integration.py:TestLLMSecurityIntegration`
   - API key management (Branches 34-36)
   - PII sanitization
   - Audit logging

2. **Compliance Tests** - `test_database_integration.py:TestComplianceIntegration`
   - ISO 17025 traceability (Branch 32)
   - Measurement uncertainty (Branch 33)
   - Electronic signatures (Branch 04)

3. **Integration Tests** - `test_database_integration.py:TestDatabaseIntegration`
   - Database models (Branch 01 - fix required)
   - Relationships and cascades
   - Data integrity

## Integration Test Coverage Goals

| Module | Target Coverage | Current | Status |
|--------|----------------|---------|--------|
| **Database Models** | 90% | 0% | ⚠️ Branch 01 has bug |
| **Config System** | 85% | 0% | 🔴 Not implemented |
| **Security Core** | 100% | 0% | 🔴 Not implemented |
| **Data Ingestion** | 80% | 0% | 🔴 Not implemented |
| **IEC Protocols** | 90% | 0% | 🔴 Not implemented |
| **Test Blocks** | 85% | 0% | 🔴 Not implemented |
| **LLM Integration** | 95% | 0% | 🔴 Not implemented |
| **Export Engines** | 80% | 0% | 🔴 Not implemented |
| **UI Components** | 75% | 0% | 🔴 Not implemented |

## Writing New Integration Tests

### Test Template

```python
@pytest.mark.integration
@pytest.mark.database  # Add relevant markers
class TestMyIntegration:
    """Test description."""

    def test_feature_integration(self, db_session, fixture_name):
        """Test specific integration scenario."""
        # Arrange
        # ... setup code

        # Act
        # ... execute integration

        # Assert
        # ... verify results

        # Optional: Clean up (usually handled by fixtures)
```

### Best Practices

1. **Use Fixtures** - Leverage existing fixtures from `conftest.py`
2. **Test Real Integration** - Don't mock core integration points
3. **ISO 17025 Compliance** - Verify traceability and uncertainty
4. **Security First** - Test authentication, authorization, encryption
5. **Performance** - Mark slow tests with `@pytest.mark.slow`
6. **Documentation** - Clear docstrings explaining what's tested

## Compliance Testing

### ISO 17025:2017 Requirements

Each integration test should verify:

1. **Equipment Calibration** (Section 6.5)
   - Valid calibration certificates
   - Traceability to national/international standards
   - Calibration intervals maintained

2. **Measurement Uncertainty** (Section 6.6)
   - GUM framework calculations
   - All uncertainty sources identified
   - Expanded uncertainty (k=2) reported

3. **Technical Records** (Section 7.5)
   - Complete test records
   - Audit trail maintained
   - Electronic signatures where required

4. **Traceability** (Section 6.2)
   - Sample tracking from receipt to disposal
   - Test procedure version control
   - Equipment usage tracking

### NABL Requirements

Tests should verify:
- Data integrity and immutability
- Personnel qualification tracking
- Inter-laboratory comparisons (when applicable)
- Proficiency testing results

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio

      - name: Run integration tests
        env:
          TEST_DATABASE_URL: postgresql://postgres:test_pass@localhost/postgres
        run: |
          pytest tests/integration/ -v --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure PostgreSQL is running
   - Check `TEST_DATABASE_URL` environment variable
   - Verify database user has CREATE DATABASE permissions

2. **Fixture Not Found**
   - Check that `conftest.py` is in the correct location
   - Ensure fixture is properly decorated with `@pytest.fixture`

3. **Import Errors**
   - Most imports are commented out until modules are implemented
   - Uncomment imports as modules become available

4. **Skipped Tests**
   - Expected behavior until branches are implemented
   - Check skip reason for which branch is needed

## Next Steps

1. **Fix Branch 01 Bug** - Add missing `Integer` import
2. **Implement Foundation Layer** (Branches 02-05)
3. **Uncomment Test Code** - As modules become available
4. **Run Tests** - Verify integration as code is implemented
5. **Measure Coverage** - Aim for >80% integration test coverage
6. **Security Audit** - Focus on security-critical tests
7. **Compliance Audit** - Verify ISO 17025/NABL requirements

## Contact

For questions about the integration test suite, refer to:
- QA Test Results Report: `/qa_test_results.md`
- Merge Readiness Assessment: `/merge_readiness.md`
- Branch-specific analysis: `/ANALYSIS_REPORTS/`

---

**Last Updated:** 2025-11-20
**Version:** 1.0
**Maintainer:** PV Automation QA Team
