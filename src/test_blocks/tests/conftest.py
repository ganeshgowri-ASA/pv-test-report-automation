"""
Pytest configuration and shared fixtures for test blocks
"""

import pytest
import logging


@pytest.fixture(scope='session', autouse=True)
def configure_logging():
    """Configure logging for tests"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


@pytest.fixture
def test_config():
    """Standard test configuration"""
    return {
        'module_area': 2.0,
        'rated_power': 300,
        'test_duration': 60
    }
