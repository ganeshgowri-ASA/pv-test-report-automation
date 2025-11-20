"""
Unit tests for IEC protocol implementations.

Tests all protocol modules for correctness and compliance.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from src.models.base_models import TestSample, CalibrationRecord
from src.protocols.iec_61215_mst import (
    IEC61215MST,
    DampHeatTestConfig,
    ThermalCyclingConfig,
)
from src.protocols.iec_61730_safety import (
    IEC61730Safety,
    DielectricTestConfig,
    SafetyClass,
    ApplicationClass,
)
from src.protocols.iec_61853_performance import (
    IEC61853Performance,
    IrradianceTemperatureConfig,
)
from src.protocols.iec_61701_salt_mist import (
    IEC61701SaltMist,
    SaltMistConfig,
    SaltMistSeverityLevel,
)


@pytest.fixture
def sample_module() -> TestSample:
    """Create sample test module."""
    return TestSample(
        sample_id="TEST-001",
        module_type="TEST-MODULE-400W",
        manufacturer="Test Manufacturer",
        serial_number="SN123456",
        rated_power=400.0,
        voltage_oc=48.0,
        current_sc=11.0,
        voltage_mpp=40.0,
        current_mpp=10.0,
        dimensions={"length": 1980, "width": 990, "area_m2": 1.96},
    )


@pytest.fixture
def calibration_records() -> list[CalibrationRecord]:
    """Create calibration records."""
    return [
        CalibrationRecord(
            equipment_id="DH-CHAMBER-001",
            equipment_name="Damp Heat Chamber",
            calibration_date=datetime(2024, 1, 1),
            due_date=datetime(2025, 1, 1),
            calibration_certificate="CAL-2024-001",
            calibrated_by="Cal Lab Inc",
            calibration_lab="NABL Accredited Lab",
            traceability="NIST traceable",
            uncertainty={"temperature": 0.5, "humidity": 2.0},
        )
    ]


class TestIEC61215MST:
    """Test IEC 61215 Module Stress Testing."""

    def test_damp_heat_test(self, sample_module: TestSample, calibration_records: list[CalibrationRecord]) -> None:
        """Test damp heat test execution."""
        tester = IEC61215MST(sample_module, uuid4())
        config = DampHeatTestConfig(cycles=200)

        result = tester.run_damp_heat_test(config, calibration_records)

        assert result.test_name == "Damp Heat (DH) Test"
        assert result.initial_power == 400.0
        assert result.power_degradation_percent < 5.0  # Should pass
        assert result.pass_fail is True

    def test_thermal_cycling_test(self, sample_module: TestSample, calibration_records: list[CalibrationRecord]) -> None:
        """Test thermal cycling test execution."""
        tester = IEC61215MST(sample_module, uuid4())
        config = ThermalCyclingConfig(cycles=200)

        result = tester.run_thermal_cycling_test(config, calibration_records)

        assert result.test_name == "Thermal Cycling (TC) Test"
        assert result.power_degradation_percent < 5.0
        assert result.pass_fail is True

    def test_generate_report(self, sample_module: TestSample, calibration_records: list[CalibrationRecord]) -> None:
        """Test report generation."""
        tester = IEC61215MST(sample_module, uuid4())
        config = DampHeatTestConfig(cycles=200)

        tester.run_damp_heat_test(config, calibration_records)
        report = tester.generate_report()

        assert report.report_number.startswith("IEC61215")
        assert report.test_type == "IEC 61215 Module Stress Testing"
        assert "IEC 61215:2021" in report.compliance_standards


class TestIEC61730Safety:
    """Test IEC 61730 Safety Qualification."""

    def test_dielectric_test(self, sample_module: TestSample, calibration_records: list[CalibrationRecord]) -> None:
        """Test dielectric withstand test."""
        tester = IEC61730Safety(sample_module, uuid4(), SafetyClass.CLASS_II, ApplicationClass.CLASS_A)
        config = DielectricTestConfig(test_voltage_vac=1000.0)

        result = tester.run_dielectric_withstand_test(config, calibration_records)

        assert result.test_name == "Dielectric Withstand Voltage Test"
        assert result.pass_fail is True


class TestIEC61853Performance:
    """Test IEC 61853 Performance Testing."""

    def test_irradiance_temperature_matrix(self, sample_module: TestSample, calibration_records: list[CalibrationRecord]) -> None:
        """Test irradiance-temperature matrix."""
        tester = IEC61853Performance(sample_module, uuid4())
        config = IrradianceTemperatureConfig()

        result = tester.run_irradiance_temperature_matrix(config, calibration_records)

        assert result.test_name == "Irradiance-Temperature Performance Matrix"
        assert result.performance_matrix is not None
        assert result.temperature_coefficients is not None


class TestIEC61701SaltMist:
    """Test IEC 61701 Salt Mist Corrosion."""

    def test_salt_mist_test(self, sample_module: TestSample, calibration_records: list[CalibrationRecord]) -> None:
        """Test salt mist corrosion test."""
        tester = IEC61701SaltMist(sample_module, uuid4())
        config = SaltMistConfig.from_severity_level(SaltMistSeverityLevel.LEVEL_3)

        result = tester.run_salt_mist_test(config, calibration_records)

        assert result.test_name == "Salt Mist Corrosion Test"
        assert result.severity_level == "3"
        assert len(result.visual_inspections) > 0
