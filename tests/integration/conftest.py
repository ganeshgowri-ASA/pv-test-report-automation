"""
Integration Test Configuration and Shared Fixtures
PV Test Report Automation System
"""
import pytest
import os
from typing import Generator, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timezone

# Import when available
# from src.database.base import Base
# from src.database.models import *
# from src.config.core import ConfigManager
# from src.security.core import SecurityManager


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Provide test configuration."""
    return {
        "database_url": os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:"),
        "api_base_url": os.getenv("TEST_API_BASE_URL", "http://localhost:8000"),
        "test_data_dir": os.path.join(os.path.dirname(__file__), "test_data"),
        "mock_llm_api": True,
        "log_level": "DEBUG",
        "iso_17025_mode": True,
    }


@pytest.fixture(scope="session")
def db_engine(test_config):
    """Create test database engine."""
    engine = create_engine(
        test_config["database_url"],
        echo=False,
        pool_pre_ping=True,
    )

    # When models are implemented:
    # Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    # Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Provide a transactional database session for each test."""
    connection = db_engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_pv_module_data() -> Dict[str, Any]:
    """Provide sample PV module test data."""
    return {
        "manufacturer": "Test Solar Inc.",
        "model": "TS-400W-PERC",
        "serial_number": "TS2025-001-12345",
        "rated_power": 400.0,
        "technology": "Monocrystalline PERC",
        "dimensions": {"length": 1960, "width": 992, "height": 40},
        "weight": 22.5,
        "cells": 120,
        "cell_type": "M10 PERC",
        "frame": "Anodized Aluminum",
        "glass": "3.2mm Tempered",
        "backsheet": "White TPE",
        "junction_box": "IP68 Rated",
        "connectors": "MC4 Compatible",
        "test_date": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def sample_test_configuration() -> Dict[str, Any]:
    """Provide sample test configuration per IEC 61215."""
    return {
        "standard": "IEC 61215-1:2021",
        "tests_to_perform": [
            "visual_inspection",
            "electrical_performance",
            "insulation_test",
            "wet_leakage_current",
            "thermal_cycling",
            "humidity_freeze",
            "uv_preconditioning",
            "hot_spot_endurance",
            "mechanical_load",
            "hail_impact",
        ],
        "test_conditions": {
            "irradiance": 1000.0,  # W/m²
            "module_temperature": 25.0,  # °C
            "am": 1.5,  # Air mass
            "wind_speed": None,  # Indoor testing
        },
        "equipment": {
            "iv_tracer": "Pasan SunSim 3c",
            "climate_chamber": "Weiss WK 180",
            "el_imaging": "BT Imaging LIS-R3",
            "insulation_tester": "Fluke 1555",
        },
    }


@pytest.fixture
def sample_calibration_data() -> Dict[str, Any]:
    """Provide sample equipment calibration data for ISO 17025."""
    return {
        "equipment_id": "CAL-2025-001",
        "equipment_name": "Fluke 1555 Insulation Tester",
        "calibration_date": "2025-01-15",
        "next_calibration_date": "2026-01-15",
        "calibration_lab": "NABL Accredited Lab XYZ",
        "certificate_number": "NABL-CAL-2025-12345",
        "traceability": "NIST traceable standards",
        "uncertainty": {
            "range_100V": {"value": 0.5, "unit": "%", "k": 2},
            "range_500V": {"value": 0.8, "unit": "%", "k": 2},
            "range_1000V": {"value": 1.0, "unit": "%", "k": 2},
        },
        "status": "valid",
    }


@pytest.fixture
def mock_llm_response() -> Dict[str, Any]:
    """Provide mock LLM API response."""
    return {
        "model": "claude-3-5-sonnet-20241022",
        "usage": {
            "input_tokens": 1250,
            "output_tokens": 450,
        },
        "content": "Based on the test results, the PV module meets all IEC 61215 requirements...",
        "stop_reason": "end_turn",
    }


@pytest.fixture
def sample_iv_curve_data() -> Dict[str, Any]:
    """Provide sample I-V curve measurement data."""
    import numpy as np

    # Simulated I-V curve for 400W module
    voltage = np.linspace(0, 48.5, 100)
    current = 10.5 * (1 - np.exp((voltage - 48.5) / 5.2))
    current = np.maximum(current, 0)

    return {
        "voltage": voltage.tolist(),
        "current": current.tolist(),
        "irradiance": 1000.0,
        "temperature": 25.0,
        "parameters": {
            "voc": 48.5,  # Open circuit voltage (V)
            "isc": 10.5,  # Short circuit current (A)
            "vmp": 40.2,  # Max power voltage (V)
            "imp": 9.95,  # Max power current (A)
            "pmax": 400.0,  # Max power (W)
            "ff": 78.5,  # Fill factor (%)
        },
    }


@pytest.fixture
def sample_el_image_defects() -> Dict[str, Any]:
    """Provide sample EL image defect detection data."""
    return {
        "image_path": "/data/el_images/TS2025-001-12345_el.tif",
        "resolution": {"width": 4096, "height": 2160},
        "defects_detected": [
            {
                "type": "crack",
                "severity": "high",
                "location": {"x": 1250, "y": 850, "width": 45, "height": 120},
                "confidence": 0.92,
            },
            {
                "type": "hotspot",
                "severity": "medium",
                "location": {"x": 2100, "y": 1100, "width": 60, "height": 60},
                "confidence": 0.87,
            },
            {
                "type": "finger_interruption",
                "severity": "low",
                "location": {"x": 3200, "y": 450, "width": 25, "height": 80},
                "confidence": 0.75,
            },
        ],
        "overall_grade": "B",
        "passed": True,
    }


@pytest.fixture
def sample_audit_trail() -> Dict[str, Any]:
    """Provide sample audit trail entry for compliance."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": "user-12345",
        "user_name": "John Smith",
        "action": "test_result_approved",
        "resource_type": "test_report",
        "resource_id": "report-67890",
        "changes": {
            "status": {"old": "pending_approval", "new": "approved"},
            "approved_by": "John Smith",
            "approval_timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0...",
        "compliance": {
            "iso_17025": True,
            "cfr_part_11": True,
            "signature": "e-signature-hash-abc123",
        },
    }


# Markers for different test categories
def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: Integration tests requiring multiple modules"
    )
    config.addinivalue_line(
        "markers", "database: Tests requiring database connection"
    )
    config.addinivalue_line(
        "markers", "api: Tests requiring API endpoints"
    )
    config.addinivalue_line(
        "markers", "llm: Tests requiring LLM API integration"
    )
    config.addinivalue_line(
        "markers", "compliance: Tests verifying ISO 17025/NABL compliance"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take significant time (>5s)"
    )
    config.addinivalue_line(
        "markers", "security: Security-related tests"
    )
