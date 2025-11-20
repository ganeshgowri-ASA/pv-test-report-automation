# Testing Infrastructure

Comprehensive testing suite for PV Test Report Automation System.

## Overview

This directory contains the complete testing infrastructure including:
- **Unit Tests** - Component-level testing
- **Integration Tests** - Multi-component interaction testing
- **QA Tests** - Quality assurance scenarios
- **E2E Tests** - End-to-end browser automation tests

## Test Structure

```
tests/
├── integration/          # Integration tests
│   ├── test_workflow_integration.py
│   ├── test_database_integration.py
│   ├── test_api_integration.py
│   └── test_file_processing.py
├── unit/                 # Unit tests
│   ├── test_data_validators.py
│   ├── test_parsers.py
│   ├── test_exporters.py
│   └── fixtures.py
├── qa/                   # QA tests
│   ├── test_qa_scenarios.py
│   ├── test_regression.py
│   └── test_performance.py
└── e2e/                  # End-to-end tests
    ├── test_user_journeys.py
    ├── test_browser_compatibility.py
    └── conftest.py
```

## Running Tests

### All Tests

```bash
pytest
```

### Unit Tests Only

```bash
pytest tests/unit/ -m unit
```

### Integration Tests

```bash
pytest tests/integration/ -m integration
```

### QA Tests

```bash
pytest tests/qa/ -m qa
```

### E2E Tests

```bash
pytest tests/e2e/ -m e2e
```

### Exclude Slow Tests

```bash
pytest -m "not slow"
```

### Run Specific Test File

```bash
pytest tests/unit/test_data_validators.py -v
```

### Run with Coverage

```bash
pytest --cov=src --cov-report=html
```

### Parallel Execution

```bash
pytest -n auto
```

## Test Markers

Use markers to selectively run tests:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.qa` - QA tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.browser` - Browser-based tests
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.regression` - Regression tests

Example:
```python
@pytest.mark.unit
def test_validation():
    assert True
```

## Coverage Goals

- **Overall Coverage**: >80%
- **Critical Modules**: >90%
- **New Features**: 100%

View coverage report:
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## Writing Tests

### Unit Test Example

```python
import pytest

@pytest.mark.unit
class TestDataValidator:
    def test_validate_voltage(self):
        validator = DataValidator()
        assert validator.validate_voltage(35.2) == True
```

### Integration Test Example

```python
import pytest

@pytest.mark.integration
@pytest.mark.asyncio
async def test_workflow(db_session):
    workflow = WorkflowEngine(db_session)
    result = await workflow.process_report(test_data)
    assert result.status == "SUCCESS"
```

### Using Fixtures

```python
def test_with_fixture(sample_test_report):
    # sample_test_report is provided by conftest.py
    assert sample_test_report["test_id"] == "TEST-001"
```

## Fixtures

Common fixtures are available in:
- `/conftest.py` - Root level shared fixtures
- `tests/unit/fixtures.py` - Unit test fixtures
- `tests/e2e/conftest.py` - E2E test fixtures

Available fixtures:
- `sample_test_report` - Sample test report data
- `sample_equipment` - Sample equipment data
- `mock_database` - Mock database connection
- `mock_llm_service` - Mock LLM service
- `temp_directory` - Temporary directory for file operations

## Continuous Integration

Tests are automatically run on:
- Pull requests to main/develop
- Push to main/develop
- Daily scheduled runs

See `.github/workflows/ci.yml` for configuration.

## Performance Testing

Run performance benchmarks:
```bash
pytest tests/qa/test_performance.py -m performance
```

Generate performance report:
```bash
pytest --benchmark-only --benchmark-json=performance.json
```

## Test Data

Test data files are stored in:
- `tests/test_data/` - Static test files
- Temporary data generated in `temp_directory` fixture

## Debugging Tests

### Run with verbose output

```bash
pytest -vv
```

### Show local variables on failure

```bash
pytest -l
```

### Drop into debugger on failure

```bash
pytest --pdb
```

### Run last failed tests

```bash
pytest --lf
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Cleanup**: Use fixtures for setup/teardown
3. **Descriptive Names**: Test names should describe what they test
4. **AAA Pattern**: Arrange, Act, Assert
5. **One Assertion**: Prefer one logical assertion per test
6. **Mock External**: Mock external services and APIs
7. **Fast Execution**: Keep unit tests fast (<1s)
8. **Coverage**: Aim for high coverage, but quality over quantity

## Troubleshooting

### Tests Hanging

```bash
pytest --timeout=300  # 5 minute timeout
```

### Import Errors

Ensure you're in the project root:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Database Issues

Reset test database:
```bash
pytest --create-db
```

### Cache Issues

Clear pytest cache:
```bash
pytest --cache-clear
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Playwright](https://playwright.dev/python/)
- [Project Documentation](../README.md)
