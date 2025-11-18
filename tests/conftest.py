"""Pytest configuration."""
import pytest


@pytest.fixture
def test_config():
    """Test configuration."""
    return {
        "database_url": "postgresql://test:test@localhost:5432/test_db",
        "redis_url": "redis://localhost:6379/15"
    }
