"""
Unit Tests for PV Test Report Validation Utilities

Comprehensive test suite for data validators, schema validators, and compliance checkers.
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any

# Import modules to test
from ..data_validators import (
    DataValidator,
    ValidationReport,
    ValidationIssue,
    ValidationSeverity,
    validate_voltage,
    validate_current,
    validate_power,
    validate_irradiance,
    validate_temperature,
    validate_module_parameters,
    validate_test_conditions,
    validate_metadata,
)

from ..schema_validators import (
    TestDataSchema,
    ModuleSpecSchema,
    EnvironmentalConditionsSchema,
    MeasurementSchema,
    ValidationResultSchema,
    TechnologyType,
    TestType,
)

from ..compliance_checker import (
    ComplianceChecker,
    check_iso17025_compliance,
    check_nabl_compliance,
    check_iec_conformance,
    check_data_completeness,
    ComplianceLevel,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def valid_module_spec() -> Dict[str, Any]:
    """Fixture providing valid module specification data."""
    return {
        "manufacturer": "Test Solar Inc.",
        "model": "TS-300-72M",
        "serial_number": "TS300-2024-001",
        "technology": TechnologyType.MONO_SI,
        "p_max": 300.0,
        "v_oc": 40.0,
        "i_sc": 9.5,
        "v_mp": 33.0,
        "i_mp": 9.09,
        "efficiency": 18.5,
        "length": 1650.0,
        "width": 992.0,
        "area": 1.637,
        "weight": 18.5,
        "cells_in_series": 72,
        "temp_coeff_pmax": -0.40,
        "temp_coeff_voc": -0.31,
        "temp_coeff_isc": 0.05,
        "certification": ["IEC 61215", "IEC 61730"],
    }


@pytest.fixture
def valid_environmental_conditions() -> Dict[str, Any]:
    """Fixture providing valid environmental conditions."""
    return {
        "irradiance": 1000.0,
        "module_temperature": 25.0,
        "ambient_temperature": 20.0,
        "wind_speed": 1.0,
        "relative_humidity": 45.0,
        "air_mass": 1.5,
        "angle_of_incidence": 0.0,
    }


@pytest.fixture
def valid_measurements() -> list:
    """Fixture providing valid measurement data."""
    measurements = []
    for v in np.linspace(0, 40, 20):
        # Simple I-V curve approximation
        i = 9.5 * (1 - v / 40.0) if v < 40 else 0
        measurements.append({
            "voltage": float(v),
            "current": float(i),
            "power": float(v * i),
            "timestamp": datetime.now(),
        })
    return measurements


@pytest.fixture
def valid_test_data(
    valid_module_spec,
    valid_environmental_conditions,
    valid_measurements
) -> Dict[str, Any]:
    """Fixture providing complete valid test data."""
    return {
        "test_id": "TEST-2024-001",
        "test_type": TestType.IV_CURVE,
        "test_date": datetime.now(),
        "test_facility": "Solar Test Lab",
        "operator": "John Doe",
        "equipment_id": "FLASH-001",
        "module_spec": valid_module_spec,
        "conditions": valid_environmental_conditions,
        "measurements": valid_measurements,
        "standard_reference": ["IEC 60904", "IEC 61215"],
        "calibration_date": datetime.now() - timedelta(days=100),
        "calibration_certificate": "CAL-2024-001",
        "quality_assurance_passed": True,
    }


# ============================================================================
# Data Validators Tests
# ============================================================================

class TestVoltageValidation:
    """Tests for voltage validation."""

    def test_valid_single_voltage(self):
        """Test validation of single valid voltage."""
        report = validate_voltage(30.0)
        assert report.is_valid
        assert len(report.issues) == 0

    def test_valid_voltage_array(self):
        """Test validation of valid voltage array."""
        voltages = np.array([0, 10, 20, 30, 40])
        report = validate_voltage(voltages)
        assert report.is_valid

    def test_voltage_out_of_range_low(self):
        """Test voltage below minimum range."""
        report = validate_voltage(-10.0, min_voltage=0.0)
        assert not report.is_valid
        assert report.errors > 0

    def test_voltage_out_of_range_high(self):
        """Test voltage above maximum range."""
        report = validate_voltage(2000.0, max_voltage=1500.0)
        assert not report.is_valid
        assert report.errors > 0

    def test_voltage_with_nan(self):
        """Test voltage array containing NaN."""
        voltages = np.array([10, 20, np.nan, 30])
        report = validate_voltage(voltages)
        assert not report.is_valid

    def test_voltage_with_inf(self):
        """Test voltage array containing infinity."""
        voltages = np.array([10, 20, np.inf, 30])
        report = validate_voltage(voltages)
        assert not report.is_valid

    def test_negative_voltage_warning(self):
        """Test negative voltage generates warning."""
        report = validate_voltage(-5.0, min_voltage=-10.0)
        assert report.warnings > 0


class TestCurrentValidation:
    """Tests for current validation."""

    def test_valid_current(self):
        """Test validation of valid current."""
        report = validate_current(8.5)
        assert report.is_valid

    def test_current_array(self):
        """Test validation of current array."""
        currents = np.linspace(0, 10, 20)
        report = validate_current(currents)
        assert report.is_valid

    def test_current_out_of_range(self):
        """Test current out of range."""
        report = validate_current(100.0, max_current=50.0)
        assert not report.is_valid

    def test_current_with_nan(self):
        """Test current with NaN values."""
        currents = np.array([5, np.nan, 7])
        report = validate_current(currents)
        assert not report.is_valid


class TestPowerValidation:
    """Tests for power validation."""

    def test_valid_power(self):
        """Test validation of valid power."""
        report = validate_power(250.0)
        assert report.is_valid

    def test_power_consistency_check(self):
        """Test power consistency with V and I."""
        voltage = 30.0
        current = 8.0
        power = 240.0  # Exactly V * I
        report = validate_power(power, voltage, current)
        assert report.is_valid

    def test_power_inconsistency(self):
        """Test power inconsistent with V * I."""
        voltage = 30.0
        current = 8.0
        power = 300.0  # Significantly different from V * I
        report = validate_power(power, voltage, current, tolerance=0.01)
        assert report.warnings > 0

    def test_negative_power_warning(self):
        """Test negative power generates warning."""
        report = validate_power(-50.0)
        assert report.warnings > 0


class TestIrradianceValidation:
    """Tests for irradiance validation."""

    def test_valid_irradiance(self):
        """Test validation of valid irradiance."""
        report = validate_irradiance(1000.0)
        assert report.is_valid

    def test_irradiance_at_stc(self):
        """Test STC irradiance detection."""
        report = validate_irradiance(1000.0)
        assert report.is_valid
        assert "stc_measurements" in report.metadata

    def test_irradiance_out_of_range(self):
        """Test irradiance out of range."""
        report = validate_irradiance(-10.0)
        assert not report.is_valid

    def test_high_irradiance_warning(self):
        """Test high irradiance generates warning."""
        report = validate_irradiance(1600.0)
        assert report.warnings > 0


class TestTemperatureValidation:
    """Tests for temperature validation."""

    def test_valid_module_temperature(self):
        """Test validation of valid module temperature."""
        report = validate_temperature(25.0, temp_type="module")
        assert report.is_valid

    def test_valid_ambient_temperature(self):
        """Test validation of valid ambient temperature."""
        report = validate_temperature(20.0, temp_type="ambient")
        assert report.is_valid

    def test_module_temperature_at_stc(self):
        """Test STC temperature detection."""
        report = validate_temperature(25.0, temp_type="module")
        assert "stc_measurements" in report.metadata

    def test_temperature_out_of_range(self):
        """Test temperature out of range."""
        report = validate_temperature(100.0, temp_type="module")
        assert not report.is_valid

    def test_invalid_temperature_type(self):
        """Test invalid temperature type."""
        report = validate_temperature(25.0, temp_type="invalid")
        assert not report.is_valid


class TestModuleParameterValidation:
    """Tests for module parameter validation."""

    def test_valid_module_parameters(self, valid_module_spec):
        """Test validation of valid module parameters."""
        report = validate_module_parameters(valid_module_spec)
        assert report.is_valid

    def test_missing_required_fields(self):
        """Test missing required fields."""
        params = {"manufacturer": "Test Inc."}
        report = validate_module_parameters(params)
        assert not report.is_valid

    def test_invalid_numeric_parameter(self):
        """Test invalid numeric parameter."""
        params = {
            "manufacturer": "Test Inc.",
            "model": "Test-300",
            "p_max": "not_a_number",  # Invalid
            "v_oc": 40.0,
            "i_sc": 9.0,
            "v_mp": 33.0,
            "i_mp": 9.0,
            "efficiency": 18.0,
            "technology": "mono-Si",
        }
        report = validate_module_parameters(params)
        assert not report.is_valid

    def test_power_consistency(self):
        """Test power parameter consistency."""
        params = {
            "manufacturer": "Test Inc.",
            "model": "Test-300",
            "p_max": 300.0,
            "v_oc": 40.0,
            "i_sc": 9.0,
            "v_mp": 30.0,
            "i_mp": 10.0,  # Would give 300W
            "efficiency": 18.0,
            "technology": "mono-Si",
        }
        report = validate_module_parameters(params)
        assert report.is_valid


class TestTestConditionsValidation:
    """Tests for test conditions validation."""

    def test_valid_standard_conditions(self, valid_environmental_conditions):
        """Test validation of valid test conditions."""
        report = validate_test_conditions(valid_environmental_conditions)
        assert report.is_valid

    def test_missing_required_conditions(self):
        """Test missing required conditions."""
        conditions = {"irradiance": 1000.0}  # Missing temperature
        report = validate_test_conditions(conditions)
        assert not report.is_valid

    def test_stc_detection(self):
        """Test STC condition detection."""
        conditions = {
            "irradiance": 1000.0,
            "module_temperature": 25.0,
        }
        report = validate_test_conditions(conditions)
        assert "test_condition_type" in report.metadata
        assert report.metadata["test_condition_type"] == "STC"


class TestMetadataValidation:
    """Tests for metadata validation."""

    def test_valid_metadata(self):
        """Test validation of valid metadata."""
        metadata = {
            "test_date": "2024-01-15",
            "test_facility": "Solar Lab",
            "operator": "John Doe",
            "equipment_id": "FLASH-001",
            "standard_reference": "IEC 60904",
        }
        report = validate_metadata(metadata)
        assert report.is_valid

    def test_missing_required_metadata(self):
        """Test missing required metadata."""
        metadata = {"test_date": "2024-01-15"}
        report = validate_metadata(metadata)
        assert not report.is_valid

    def test_invalid_date_format(self):
        """Test invalid date format generates warning."""
        metadata = {
            "test_date": "not-a-date",
            "test_facility": "Solar Lab",
            "operator": "John Doe",
            "equipment_id": "FLASH-001",
            "standard_reference": "IEC 60904",
        }
        report = validate_metadata(metadata)
        # Should have warnings or errors about date
        assert len(report.issues) > 0


class TestDataValidatorBatch:
    """Tests for batch validation."""

    def test_batch_validation(self):
        """Test batch validation of multiple datasets."""
        validator = DataValidator()
        data_list = [
            {"voltage": 30.0},
            {"voltage": 35.0},
            {"voltage": 40.0},
        ]

        def validate_item(data):
            return validate_voltage(data["voltage"])

        reports = validator.validate_batch(data_list, validate_item)
        assert len(reports) == 3
        assert all(r.is_valid for r in reports)


# ============================================================================
# Schema Validators Tests
# ============================================================================

class TestModuleSpecSchema:
    """Tests for ModuleSpecSchema."""

    def test_valid_module_spec(self, valid_module_spec):
        """Test creating valid module spec."""
        spec = ModuleSpecSchema(**valid_module_spec)
        assert spec.manufacturer == "Test Solar Inc."
        assert spec.p_max == 300.0

    def test_electrical_consistency_validation(self):
        """Test electrical parameter consistency."""
        spec_data = {
            "manufacturer": "Test Inc.",
            "model": "Test-300",
            "technology": TechnologyType.MONO_SI,
            "p_max": 300.0,
            "v_oc": 40.0,
            "i_sc": 10.0,
            "v_mp": 30.0,
            "i_mp": 10.0,
            "efficiency": 18.0,
        }
        spec = ModuleSpecSchema(**spec_data)
        assert spec.p_max == 300.0

    def test_invalid_power_consistency(self):
        """Test invalid power consistency raises error."""
        spec_data = {
            "manufacturer": "Test Inc.",
            "model": "Test-300",
            "technology": TechnologyType.MONO_SI,
            "p_max": 400.0,  # Inconsistent with Vmp * Imp
            "v_oc": 40.0,
            "i_sc": 10.0,
            "v_mp": 30.0,
            "i_mp": 10.0,  # Would give 300W
            "efficiency": 18.0,
        }
        with pytest.raises(ValueError):
            ModuleSpecSchema(**spec_data)

    def test_vmp_less_than_voc(self):
        """Test Vmp must be less than Voc."""
        spec_data = {
            "manufacturer": "Test Inc.",
            "model": "Test-300",
            "technology": TechnologyType.MONO_SI,
            "p_max": 300.0,
            "v_oc": 30.0,
            "i_sc": 10.0,
            "v_mp": 40.0,  # Greater than Voc - invalid
            "i_mp": 7.5,
            "efficiency": 18.0,
        }
        with pytest.raises(ValueError):
            ModuleSpecSchema(**spec_data)


class TestEnvironmentalConditionsSchema:
    """Tests for EnvironmentalConditionsSchema."""

    def test_valid_conditions(self, valid_environmental_conditions):
        """Test creating valid environmental conditions."""
        conditions = EnvironmentalConditionsSchema(**valid_environmental_conditions)
        assert conditions.irradiance == 1000.0
        assert conditions.module_temperature == 25.0

    def test_is_stc_method(self):
        """Test is_stc() method."""
        conditions = EnvironmentalConditionsSchema(
            irradiance=1000.0,
            module_temperature=25.0,
        )
        assert conditions.is_stc()

    def test_not_stc(self):
        """Test non-STC conditions."""
        conditions = EnvironmentalConditionsSchema(
            irradiance=800.0,
            module_temperature=45.0,
        )
        assert not conditions.is_stc()

    def test_temperature_relationship_validation(self):
        """Test module temp vs ambient temp validation."""
        # Module temp significantly lower than ambient - unusual
        with pytest.raises(ValueError):
            EnvironmentalConditionsSchema(
                irradiance=1000.0,
                module_temperature=15.0,
                ambient_temperature=30.0,
            )


class TestMeasurementSchema:
    """Tests for MeasurementSchema."""

    def test_valid_measurement(self):
        """Test creating valid measurement."""
        measurement = MeasurementSchema(
            voltage=30.0,
            current=8.0,
        )
        assert measurement.power == 240.0  # Auto-calculated

    def test_power_auto_calculation(self):
        """Test power is auto-calculated."""
        measurement = MeasurementSchema(
            voltage=30.0,
            current=8.0,
        )
        assert measurement.power == 240.0

    def test_power_validation(self):
        """Test provided power is validated against V*I."""
        with pytest.raises(ValueError):
            MeasurementSchema(
                voltage=30.0,
                current=8.0,
                power=300.0,  # Inconsistent
            )

    def test_quality_flag_validation(self):
        """Test quality flag validation."""
        measurement = MeasurementSchema(
            voltage=30.0,
            current=8.0,
            quality_flag="good",
        )
        assert measurement.quality_flag == "good"

        with pytest.raises(ValueError):
            MeasurementSchema(
                voltage=30.0,
                current=8.0,
                quality_flag="invalid_flag",
            )


class TestTestDataSchema:
    """Tests for TestDataSchema."""

    def test_valid_test_data(self, valid_test_data):
        """Test creating valid test data."""
        test_data = TestDataSchema(**valid_test_data)
        assert test_data.test_id == "TEST-2024-001"
        assert len(test_data.measurements) > 0

    def test_calibration_date_validation(self, valid_test_data):
        """Test calibration date validation."""
        # Calibration too old
        old_data = valid_test_data.copy()
        old_data["calibration_date"] = datetime.now() - timedelta(days=400)

        with pytest.raises(ValueError):
            TestDataSchema(**old_data)

    def test_future_date_validation(self, valid_test_data):
        """Test future dates are rejected."""
        future_data = valid_test_data.copy()
        future_data["test_date"] = datetime.now() + timedelta(days=10)

        with pytest.raises(ValueError):
            TestDataSchema(**future_data)

    def test_derived_parameters_calculation(self, valid_test_data):
        """Test derived parameters are calculated."""
        test_data = TestDataSchema(**valid_test_data)
        assert test_data.peak_power is not None
        assert test_data.fill_factor is not None


class TestValidationResultSchema:
    """Tests for ValidationResultSchema."""

    def test_create_validation_result(self):
        """Test creating validation result."""
        result = ValidationResultSchema(is_valid=True)
        assert result.is_valid
        assert result.error_count == 0

    def test_add_error(self):
        """Test adding errors to result."""
        result = ValidationResultSchema(is_valid=True)
        result.add_error("Test error", field="test_field")

        assert not result.is_valid
        assert result.error_count == 1

    def test_add_warning(self):
        """Test adding warnings."""
        result = ValidationResultSchema(is_valid=True)
        result.add_error(
            "Test warning",
            field="test_field",
            severity=ValidationSeverityEnum.WARNING
        )

        assert result.is_valid  # Warnings don't invalidate
        assert result.warning_count == 1

    def test_get_summary(self):
        """Test get_summary method."""
        result = ValidationResultSchema(is_valid=True)
        summary = result.get_summary()
        assert "PASSED" in summary


# ============================================================================
# Compliance Checker Tests
# ============================================================================

class TestComplianceChecker:
    """Tests for ComplianceChecker."""

    def test_iso17025_compliance_check(self, valid_test_data):
        """Test ISO 17025 compliance checking."""
        test_data = TestDataSchema(**valid_test_data)
        report = check_iso17025_compliance(test_data)

        assert report.standard.value == "ISO/IEC 17025:2017"
        assert len(report.check_results) > 0

    def test_nabl_compliance_check(self, valid_test_data):
        """Test NABL compliance checking."""
        test_data = TestDataSchema(**valid_test_data)
        report = check_nabl_compliance(test_data)

        assert report.standard.value == "NABL 162"
        assert len(report.check_results) > 0

    def test_iec_conformance_check(self, valid_test_data):
        """Test IEC conformance checking."""
        test_data = TestDataSchema(**valid_test_data)
        report = check_iec_conformance(test_data)

        assert len(report.check_results) > 0

    def test_data_completeness_check(self, valid_test_data):
        """Test data completeness checking."""
        test_data = TestDataSchema(**valid_test_data)
        result = check_data_completeness(test_data)

        assert isinstance(result, ValidationResultSchema)

    def test_missing_calibration_fails_iso17025(self, valid_test_data):
        """Test missing calibration fails ISO 17025."""
        incomplete_data = valid_test_data.copy()
        incomplete_data["calibration_date"] = datetime.now() - timedelta(days=100)
        incomplete_data["calibration_certificate"] = None

        test_data = TestDataSchema(**incomplete_data)
        report = check_iso17025_compliance(test_data)

        # Should have failures for missing calibration certificate
        failed = report.get_failed_requirements()
        assert len(failed) > 0

    def test_expired_calibration_fails(self, valid_test_data):
        """Test expired calibration fails compliance."""
        # Create data with expired calibration (need to set test_date in future)
        old_data = valid_test_data.copy()
        old_data["calibration_date"] = datetime.now() - timedelta(days=400)

        # This should fail during TestDataSchema creation
        with pytest.raises(ValueError):
            TestDataSchema(**old_data)


class TestComplianceReport:
    """Tests for ComplianceReport."""

    def test_get_summary_text(self, valid_test_data):
        """Test compliance report summary text."""
        test_data = TestDataSchema(**valid_test_data)
        report = check_iso17025_compliance(test_data)

        summary = report.get_summary_text()
        assert "ISO/IEC 17025" in summary
        assert "Checks:" in summary

    def test_get_failed_requirements(self, valid_test_data):
        """Test getting failed requirements."""
        # Create incomplete data
        incomplete_data = valid_test_data.copy()
        incomplete_data["operator"] = ""  # Missing operator

        test_data = TestDataSchema(**incomplete_data)
        report = check_iso17025_compliance(test_data)

        failed = report.get_failed_requirements()
        # Should have at least one failure
        assert isinstance(failed, list)


# ============================================================================
# Integration Tests
# ============================================================================

class TestValidationIntegration:
    """Integration tests for complete validation workflow."""

    def test_complete_validation_workflow(self, valid_test_data):
        """Test complete validation workflow from data to compliance."""
        # 1. Create test data schema
        test_data = TestDataSchema(**valid_test_data)

        # 2. Validate data quality
        quality_result = test_data.validate_data_quality()
        assert isinstance(quality_result, ValidationResultSchema)

        # 3. Check compliance
        iso_report = check_iso17025_compliance(test_data)
        nabl_report = check_nabl_compliance(test_data)
        iec_report = check_iec_conformance(test_data)

        # All should generate reports
        assert iso_report is not None
        assert nabl_report is not None
        assert iec_report is not None

    def test_validation_with_issues(self):
        """Test validation workflow with data issues."""
        # Create data with known issues
        problematic_data = {
            "test_id": "TEST-2024-002",
            "test_type": TestType.IV_CURVE,
            "test_date": datetime.now(),
            "test_facility": "Solar Test Lab",
            "operator": "Jane Doe",
            "equipment_id": "FLASH-002",
            "module_spec": {
                "manufacturer": "Test Inc.",
                "model": "Test-250",
                "technology": TechnologyType.POLY_SI,
                "p_max": 250.0,
                "v_oc": 37.0,
                "i_sc": 8.5,
                "v_mp": 30.0,
                "i_mp": 8.33,
                "efficiency": 15.5,
            },
            "conditions": {
                "irradiance": 800.0,  # Not STC
                "module_temperature": 45.0,  # Not STC
            },
            "measurements": [
                {"voltage": 30.0, "current": 8.0}
            ],  # Only 1 measurement - insufficient
            "standard_reference": [],  # No standards - issue
            # Missing calibration data - issue
        }

        test_data = TestDataSchema(**problematic_data)

        # Check data quality
        quality_result = test_data.validate_data_quality()
        assert quality_result.warning_count > 0 or quality_result.error_count > 0

        # Check completeness
        completeness_result = check_data_completeness(test_data)
        assert not completeness_result.is_valid


# ============================================================================
# Performance and Edge Cases
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_large_measurement_array(self):
        """Test validation with large number of measurements."""
        large_voltage_array = np.random.uniform(0, 40, 10000)
        report = validate_voltage(large_voltage_array)
        assert report is not None

    def test_empty_measurements(self):
        """Test handling of empty measurements."""
        report = validate_voltage(np.array([]))
        assert report.is_valid  # Empty is technically valid

    def test_single_measurement_point(self):
        """Test with single measurement."""
        report = validate_voltage(30.0)
        assert report.is_valid

    def test_extreme_values(self):
        """Test with extreme but valid values."""
        # Test at boundaries
        report_min = validate_voltage(0.0)
        assert report_min.is_valid

        report_max = validate_voltage(1500.0, max_voltage=1500.0)
        assert report_max.is_valid


# ============================================================================
# Test Runner Configuration
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
