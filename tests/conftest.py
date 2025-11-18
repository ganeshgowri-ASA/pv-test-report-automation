"""
Pytest configuration and fixtures for PV test automation.

Provides common test fixtures for:
- Equipment configuration
- Test data
- Mock equipment instances
"""

import pytest
from typing import Dict, Any
from datetime import datetime


@pytest.fixture
def equipment_config() -> Dict[str, Any]:
    """
    Provide standard equipment configuration for tests.

    Returns:
        Equipment configuration dictionary
    """
    return {
        "thermal_camera": {
            "type": "FLIR-T1020",
            "resolution": "1024x768",
            "framerate": 30,
            "temperature_range": [-40, 1200]
        },
        "solar_simulator": {
            "type": "Xenon-Arc",
            "max_irradiance": 1200,
            "uniformity": 0.02,
            "stability": 0.01
        },
        "temp_logger": {
            "type": "Agilent-34970A",
            "channels": 8,
            "sample_rate": 10.0,
            "accuracy": 0.1
        }
    }


@pytest.fixture
def test_parameters() -> Dict[str, Any]:
    """
    Provide standard test parameters.

    Returns:
        Test parameters dictionary
    """
    return {
        "irradiance_w_m2": 1000.0,
        "temperature_threshold_c": 85.0,
        "duration_hours": 1.0,
        "thermal_interval_seconds": 300,
        "shading_pattern": "single_cell"
    }


@pytest.fixture
def module_id() -> str:
    """Provide test module identifier."""
    return "PV-TEST-001"


@pytest.fixture
def operator_id() -> str:
    """Provide test operator identifier."""
    return "OP-12345"
