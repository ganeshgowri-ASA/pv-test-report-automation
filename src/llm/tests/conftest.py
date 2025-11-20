"""
Shared test fixtures and configuration for LLM tests
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock

from ..llm_config import LLMConfig, LLMProvider


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_config(temp_dir):
    """Create a test LLM configuration."""
    config = LLMConfig(
        config_file=temp_dir / "config.json",
        cache_dir=temp_dir / "cache"
    )
    # Set test API keys
    config.set_api_key(LLMProvider.OPENAI, "test-openai-key")
    config.set_api_key(LLMProvider.GEMINI, "test-gemini-key")
    return config


@pytest.fixture
def sample_report_data():
    """Provide sample PV test report data."""
    return {
        'report_id': 'TEST-2024-001',
        'module_id': 'PV-MODULE-001',
        'manufacturer': 'Test Solar Inc.',
        'model': 'TestPanel-300',
        'report_type': 'IEC 61215 Qualification Test',
        'test_date': '2024-01-15',
        'test_results': {
            'visual_inspection': {
                'status': 'pass',
                'notes': 'No visible defects'
            },
            'power_measurement': {
                'pmax': 305.2,
                'pmax_spec': 300.0,
                'deviation': 1.7,
                'status': 'pass'
            },
            'thermal_cycling': {
                'cycles_completed': 200,
                'power_degradation': 3.2,
                'degradation_limit': 5.0,
                'status': 'pass'
            },
            'damp_heat': {
                'duration_hours': 1000,
                'power_degradation': 4.1,
                'insulation_resistance': 45.2,
                'status': 'pass'
            }
        },
        'overall_result': 'pass',
        'compliance_standards': ['IEC 61215', 'IEC 61730']
    }


@pytest.fixture
def sample_test_results():
    """Provide sample test results data."""
    return {
        'test_count': 15,
        'passed': 14,
        'failed': 1,
        'pass_rate': 93.3,
        'critical_failures': 0,
        'warnings': 2
    }


@pytest.fixture
def mock_gpt_response():
    """Create a mock GPT response."""
    from ..gpt_integration import GPTResponse

    return GPTResponse(
        content="This is a mock response from GPT.",
        model="gpt-4-turbo-preview",
        tokens_input=100,
        tokens_output=50,
        cost=0.5,
        finish_reason="stop",
        metadata={'id': 'mock-id-123'}
    )


@pytest.fixture
def mock_gemini_response():
    """Create a mock Gemini response."""
    from ..gemini_integration import GeminiResponse

    return GeminiResponse(
        content="This is a mock response from Gemini.",
        model="gemini-1.5-pro",
        tokens_input=100,
        tokens_output=50,
        cost=0.3,
        safety_ratings=[]
    )


@pytest.fixture
def sample_compliance_requirements():
    """Provide sample compliance requirements."""
    from ..compliance_checker import StandardRequirement

    return [
        StandardRequirement(
            id="IEC61215-10.1",
            standard="IEC 61215",
            section="10.1",
            description="Visual Inspection",
            category="Initial Tests",
            mandatory=True,
            test_methods=["Visual inspection"],
            acceptance_criteria="No visual defects"
        ),
        StandardRequirement(
            id="IEC61215-10.2",
            standard="IEC 61215",
            section="10.2",
            description="Maximum Power Determination",
            category="Initial Tests",
            mandatory=True,
            test_methods=["STC measurement"],
            acceptance_criteria="Pmax within ±3% of rated power"
        ),
        StandardRequirement(
            id="IEC61215-10.8",
            standard="IEC 61215",
            section="10.8",
            description="Thermal Cycling",
            category="Environmental Tests",
            mandatory=True,
            test_methods=["200 cycles: -40°C to +85°C"],
            acceptance_criteria="Pmax degradation ≤5%"
        )
    ]


@pytest.fixture
def sample_key_findings():
    """Provide sample key findings."""
    from ..report_summarizer import KeyFinding

    return [
        KeyFinding(
            category="Performance",
            finding="Module power output exceeds specification by 1.7%",
            severity="notable",
            impact="Positive performance indication",
            recommendation="Continue monitoring in production"
        ),
        KeyFinding(
            category="Reliability",
            finding="Thermal cycling test shows 3.2% degradation",
            severity="informational",
            impact="Within acceptable limits",
            recommendation="No action required"
        ),
        KeyFinding(
            category="Compliance",
            finding="All IEC 61215 tests passed",
            severity="informational",
            impact="Module qualifies for certification",
            recommendation="Proceed with certification process"
        )
    ]


# Markers for different test categories
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_api_key: mark test as requiring actual API key"
    )


# Skip integration tests by default
def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip certain tests by default."""
    skip_integration = pytest.mark.skip(reason="Integration test - run with --integration flag")
    skip_api = pytest.mark.skip(reason="Requires API key - run with --api-tests flag")

    for item in items:
        if "integration" in item.keywords and not config.getoption("--integration", default=False):
            item.add_marker(skip_integration)
        if "requires_api_key" in item.keywords and not config.getoption("--api-tests", default=False):
            item.add_marker(skip_api)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests"
    )
    parser.addoption(
        "--api-tests",
        action="store_true",
        default=False,
        help="Run tests that require real API keys"
    )
