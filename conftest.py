"""
Shared pytest configuration and fixtures for PV Test Report Automation.

This file is automatically loaded by pytest and provides fixtures
that are available to all test modules.
"""
import pytest
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil
from typing import Generator, Dict, Any
from unittest.mock import Mock, MagicMock


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests"
    )
    config.addinivalue_line(
        "markers", "qa: QA tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )
    config.addinivalue_line(
        "markers", "browser: Browser-based tests"
    )
    config.addinivalue_line(
        "markers", "visual: Visual regression tests"
    )
    config.addinivalue_line(
        "markers", "regression: Regression tests"
    )
    config.addinivalue_line(
        "markers", "performance: Performance tests"
    )


# ============================================================================
# Async Support
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Directory and File Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Provide path to test data directory."""
    data_dir = Path(__file__).parent / "tests" / "test_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture
def temp_directory() -> Generator[Path, None, None]:
    """Provide a temporary directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def sample_excel_file(temp_directory: Path) -> Path:
    """Create a sample Excel file for testing."""
    excel_file = temp_directory / "test_data.xlsx"
    excel_file.touch()
    return excel_file


@pytest.fixture
def sample_pdf_file(temp_directory: Path) -> Path:
    """Create a sample PDF file for testing."""
    pdf_file = temp_directory / "test_report.pdf"
    pdf_file.touch()
    return pdf_file


@pytest.fixture
def sample_image_file(temp_directory: Path) -> Path:
    """Create a sample image file for testing."""
    image_file = temp_directory / "test_image.jpg"
    image_file.touch()
    return image_file


# ============================================================================
# Data Fixtures
# ============================================================================

@pytest.fixture
def sample_test_report() -> Dict[str, Any]:
    """Provide a sample test report."""
    return {
        "test_id": "TEST-001",
        "standard": "IEC 61853-1",
        "status": "DRAFT",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "measurements": [
            {"voltage": 35.2, "current": 8.5, "power": 299.2},
            {"voltage": 36.1, "current": 8.3, "power": 299.6},
            {"voltage": 37.0, "current": 8.1, "power": 299.7}
        ],
        "metadata": {
            "temperature": 25.0,
            "irradiance": 1000.0,
            "test_date": "2024-01-15"
        }
    }


@pytest.fixture
def sample_equipment() -> Dict[str, Any]:
    """Provide sample equipment data."""
    return {
        "equipment_id": "EQ-001",
        "name": "Solar Simulator",
        "model": "SS-1000X",
        "manufacturer": "Test Equipment Inc.",
        "serial_number": "SN123456",
        "calibration_date": datetime.now().isoformat(),
        "next_calibration": (datetime.now() + timedelta(days=365)).isoformat(),
        "status": "CALIBRATED"
    }


@pytest.fixture
def sample_user() -> Dict[str, Any]:
    """Provide sample user data."""
    return {
        "user_id": "USER-001",
        "username": "test_user",
        "email": "test@example.com",
        "role": "TECHNICIAN",
        "permissions": ["read", "write", "execute"]
    }


@pytest.fixture
def sample_measurements() -> list:
    """Provide sample measurement data."""
    return [
        {
            "timestamp": datetime.now().isoformat(),
            "voltage": 35.2,
            "current": 8.5,
            "power": 299.2,
            "temperature": 25.0,
            "irradiance": 1000.0
        },
        {
            "timestamp": (datetime.now() + timedelta(seconds=1)).isoformat(),
            "voltage": 36.1,
            "current": 8.3,
            "power": 299.6,
            "temperature": 25.1,
            "irradiance": 1000.0
        },
        {
            "timestamp": (datetime.now() + timedelta(seconds=2)).isoformat(),
            "voltage": 37.0,
            "current": 8.1,
            "power": 299.7,
            "temperature": 25.0,
            "irradiance": 1000.0
        }
    ]


@pytest.fixture
def standard_test_data() -> Dict[str, Any]:
    """Provide test data for various standards."""
    return {
        "IEC 61853-1": {
            "irradiance_levels": [100, 200, 400, 600, 800, 1000, 1100],
            "temperature_levels": [15, 25, 50, 75],
            "required_measurements": ["voltage", "current", "power"]
        },
        "IEC 60904-1": {
            "reference_conditions": {
                "irradiance": 1000,
                "temperature": 25,
                "spectrum": "AM1.5G"
            }
        },
        "IEC 62804-1": {
            "test_duration": 96,  # hours
            "voltage_levels": [600, 1000],
            "temperature": 60
        }
    }


# ============================================================================
# Mock Service Fixtures
# ============================================================================

@pytest.fixture
def mock_database():
    """Provide a mock database connection."""
    db = Mock()
    db.connected = True
    db.execute = Mock(return_value=True)
    db.commit = Mock()
    db.rollback = Mock()
    db.close = Mock()
    return db


@pytest.fixture
def mock_file_storage():
    """Provide a mock file storage service."""
    storage = Mock()
    storage.upload = Mock(return_value={"file_id": "FILE123", "status": "success"})
    storage.download = Mock(return_value=b"file content")
    storage.delete = Mock(return_value=True)
    storage.exists = Mock(return_value=True)
    return storage


@pytest.fixture
def mock_llm_service():
    """Provide a mock LLM service."""
    llm = Mock()
    llm.analyze = Mock(return_value={"summary": "Test report analysis"})
    llm.extract = Mock(return_value={"data": "extracted data"})
    llm.validate = Mock(return_value={"valid": True})
    return llm


@pytest.fixture
def mock_api_client():
    """Provide a mock API client."""
    client = Mock()
    client.get = Mock(return_value={"status": 200, "data": {}})
    client.post = Mock(return_value={"status": 201, "data": {"id": "123"}})
    client.put = Mock(return_value={"status": 200, "data": {}})
    client.delete = Mock(return_value={"status": 204})
    return client


@pytest.fixture
def mock_email_service():
    """Provide a mock email service."""
    email = Mock()
    email.send = Mock(return_value=True)
    email.send_batch = Mock(return_value={"sent": 5, "failed": 0})
    return email


@pytest.fixture
def mock_notification_service():
    """Provide a mock notification service."""
    notifications = Mock()
    notifications.send = Mock(return_value=True)
    notifications.subscribe = Mock(return_value=True)
    notifications.unsubscribe = Mock(return_value=True)
    return notifications


@pytest.fixture
def mock_cache():
    """Provide a mock cache service."""
    cache = Mock()
    cache.get = Mock(return_value=None)
    cache.set = Mock(return_value=True)
    cache.delete = Mock(return_value=True)
    cache.clear = Mock(return_value=True)
    return cache


@pytest.fixture
def mock_logger():
    """Provide a mock logger."""
    logger = Mock()
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.critical = Mock()
    return logger


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Provide sample configuration."""
    return {
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "test_db",
            "user": "test_user"
        },
        "storage": {
            "type": "local",
            "path": "/tmp/storage"
        },
        "llm": {
            "provider": "openai",
            "model": "gpt-4",
            "api_key": "test_key"
        },
        "logging": {
            "level": "INFO",
            "file": "test.log"
        }
    }


@pytest.fixture
def test_user_credentials() -> Dict[str, Dict[str, str]]:
    """Provide test user credentials."""
    return {
        "technician": {
            "username": "test_technician",
            "password": "test_password_123"
        },
        "manager": {
            "username": "test_manager",
            "password": "test_password_456"
        },
        "admin": {
            "username": "test_admin",
            "password": "test_password_789"
        }
    }


# ============================================================================
# Database Fixtures (for integration tests)
# ============================================================================

@pytest.fixture(scope="session")
async def test_database():
    """Provide a test database connection (for integration tests)."""
    # This would set up a test database
    # For now, return a mock
    db = {"connection": "test_connection"}
    yield db
    # Cleanup


@pytest.fixture
async def db_session(test_database):
    """Provide a database session with automatic rollback."""
    # Start transaction
    # yield session
    # Rollback transaction
    yield test_database


# ============================================================================
# Time Fixtures
# ============================================================================

@pytest.fixture
def freeze_time():
    """Freeze time for testing."""
    frozen_time = datetime(2024, 1, 15, 12, 0, 0)
    return frozen_time


# ============================================================================
# Cleanup Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test."""
    yield
    # Cleanup code here if needed


# ============================================================================
# Performance Fixtures
# ============================================================================

@pytest.fixture
def benchmark_timer():
    """Provide a timer for benchmarking."""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

    return Timer()
