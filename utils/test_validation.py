"""
Unit tests for PV test lab validation utilities.

This module contains pytest test cases and fixtures for all validation
modules: validation, numeric_validators, file_validators, protocol_validators,
and iso17025_validators.
"""

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import pytest

# Import all validators
from .validation import (
    ValidationResult,
    ValidationError,
    validate_module_serial,
    validate_datetime_format,
    validate_standard_reference,
    validate_equipment_id,
    validate_email,
    validate_username,
    validate_date_range,
    validate_reviewer_hierarchy,
    batch_validate,
)

from .numeric_validators import (
    validate_numeric_range,
    validate_percentage,
    detect_outliers_zscore,
    detect_outliers_iqr,
    calculate_combined_uncertainty,
    propagate_uncertainty,
    count_significant_figures,
    round_to_sig_figs,
    validate_significant_figures,
    convert_units,
    validate_unit_consistency,
    MeasurementUncertainty,
)

from .file_validators import (
    validate_file_size,
    validate_mime_type,
    validate_file_extension,
    validate_csv_structure,
    validate_file,
)

from .protocol_validators import (
    validate_mst_sequence,
    validate_thermal_cycle,
    validate_safety_test_voltage,
    validate_dielectric_strength,
    validate_ammonia_concentration,
    validate_salt_mist_severity,
    validate_stc_conditions,
    validate_module_power_rating,
    validate_test_sequence_dependency,
)

from .iso17025_validators import (
    validate_calibration_certificate,
    validate_calibration_interval,
    validate_traceability_chain,
    validate_uncertainty_budget,
    validate_accreditation_scope,
    validate_equipment_qualification,
    validate_measurement_result_reporting,
    UncertaintyBudget,
    CalibrationCertificate,
)


# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest.fixture
def valid_module_serials() -> List[str]:
    """Fixture providing valid module serial numbers."""
    return [
        "PV-2025-001234",
        "PV-2024-999999",
        "PV-2023-000001",
    ]


@pytest.fixture
def invalid_module_serials() -> List[str]:
    """Fixture providing invalid module serial numbers."""
    return [
        "PV-25-1234",      # Wrong year format
        "ABC-2025-001",     # Wrong prefix
        "PV-2025",          # Incomplete
        "",                 # Empty
        "pv-2025-001234",   # Lowercase (should be normalized)
    ]


@pytest.fixture
def sample_datetime_strings() -> dict:
    """Fixture providing datetime test strings."""
    return {
        "valid": [
            "2025-01-15T10:30:00Z",
            "2025-01-15T10:30:00.123456Z",
            "2025-01-15 10:30:00",
            "2025-01-15",
        ],
        "invalid": [
            "2025/01/15",
            "15-01-2025",
            "not-a-date",
            "",
        ]
    }


@pytest.fixture
def test_file_path(tmp_path: Path) -> Path:
    """Fixture creating a temporary test file."""
    test_file = tmp_path / "test_data.csv"
    test_file.write_text("Module_ID,Power_W,Voltage_V\nPV-001,320,40\nPV-002,315,39")
    return test_file


@pytest.fixture
def sample_calibration_cert() -> CalibrationCertificate:
    """Fixture providing a sample calibration certificate."""
    return CalibrationCertificate(
        certificate_number="CAL-2024-001",
        equipment_id="SIM-001",
        calibration_date=datetime.now() - timedelta(days=100),
        due_date=datetime.now() + timedelta(days=265),
        lab_name="National Calibration Lab",
        accreditation_body="NABL",
        uncertainty=0.5,
        traceability="national"
    )


@pytest.fixture
def sample_uncertainty_budget() -> UncertaintyBudget:
    """Fixture providing a sample uncertainty budget."""
    return UncertaintyBudget(
        components={
            "type_a": 0.05,
            "type_b_calibration": 0.10,
            "type_b_environmental": 0.03,
            "type_b_resolution": 0.02,
        },
        combined_uncertainty=0.12,
        expanded_uncertainty=0.24,
        coverage_factor=2.0,
        confidence_level=95.0
    )


@pytest.fixture
def nabl_accredited_scopes() -> List[dict]:
    """Fixture providing NABL accreditation scopes."""
    return [
        {"method": "PV Module Testing", "standard": "IEC 61215"},
        {"method": "IV Curve Measurement", "standard": "IEC 60904"},
        {"method": "Safety Testing", "standard": "IEC 61730"},
        {"method": "Thermal Cycling", "standard": "IEC 61215"},
    ]


# ============================================================================
# Tests: validation.py
# ============================================================================

class TestCoreValidation:
    """Test cases for core validation utilities."""

    def test_validate_module_serial_valid(self, valid_module_serials):
        """Test validation of valid module serial numbers."""
        for serial in valid_module_serials:
            result = validate_module_serial(serial)
            assert result.is_valid, f"Failed for {serial}: {result.errors}"
            assert result.value == serial.upper()

    def test_validate_module_serial_invalid(self, invalid_module_serials):
        """Test validation rejects invalid serial numbers."""
        for serial in invalid_module_serials:
            result = validate_module_serial(serial)
            if serial.lower() == "pv-2025-001234":
                # Should normalize to uppercase
                assert result.is_valid
            else:
                assert not result.is_valid or serial == ""

    def test_validate_datetime_format_valid(self, sample_datetime_strings):
        """Test datetime format validation with valid strings."""
        for dt_str in sample_datetime_strings["valid"]:
            result = validate_datetime_format(dt_str)
            assert result.is_valid, f"Failed for {dt_str}: {result.errors}"
            assert isinstance(result.value, datetime)

    def test_validate_datetime_format_invalid(self, sample_datetime_strings):
        """Test datetime format validation rejects invalid strings."""
        for dt_str in sample_datetime_strings["invalid"]:
            result = validate_datetime_format(dt_str)
            assert not result.is_valid

    def test_validate_standard_reference(self):
        """Test IEC/ISO standard reference validation."""
        valid_refs = [
            "IEC 61215",
            "IEC 61215-1:2021",
            "ISO/IEC 17025:2017",
            "IEC 62716 Ed. 2.0",
        ]
        for ref in valid_refs:
            result = validate_standard_reference(ref)
            assert result.is_valid, f"Failed for {ref}: {result.errors}"

    def test_validate_equipment_id(self):
        """Test equipment ID validation."""
        result = validate_equipment_id("SIM-001", prefix="SIM-")
        assert result.is_valid
        assert result.value == "SIM-001"

    def test_validate_email(self):
        """Test email validation."""
        valid_emails = ["tech@lab.com", "reviewer@testlab.org"]
        for email in valid_emails:
            result = validate_email(email)
            assert result.is_valid

    def test_validate_date_range(self):
        """Test date range validation."""
        result = validate_date_range("2025-01-01", "2025-01-15")
        assert result.is_valid
        assert result.metadata["duration_days"] == 14

    def test_validate_reviewer_hierarchy(self):
        """Test reviewer hierarchy validation."""
        result = validate_reviewer_hierarchy(
            technician="tech01",
            reviewer="reviewer01",
            approver="manager01"
        )
        assert result.is_valid

        # Test self-review prevention
        result = validate_reviewer_hierarchy(
            technician="tech01",
            reviewer="tech01",
            approver="manager01"
        )
        assert not result.is_valid


# ============================================================================
# Tests: numeric_validators.py
# ============================================================================

class TestNumericValidators:
    """Test cases for numeric validation utilities."""

    def test_validate_numeric_range(self):
        """Test numeric range validation."""
        result = validate_numeric_range(85.2, min_value=83.0, max_value=87.0)
        assert result.is_valid

        result = validate_numeric_range(90.0, min_value=83.0, max_value=87.0)
        assert not result.is_valid

    def test_validate_percentage(self):
        """Test percentage validation."""
        result = validate_percentage(95.5)
        assert result.is_valid

        result = validate_percentage(150.0)
        assert not result.is_valid

    def test_detect_outliers_zscore(self):
        """Test Z-score outlier detection."""
        data = [10.1, 10.2, 10.0, 10.3, 10.1, 50.0]  # 50.0 is outlier
        result = detect_outliers_zscore(data, threshold=3.0)
        assert result.is_valid
        assert len(result.value["outliers"]) >= 1

    def test_detect_outliers_iqr(self):
        """Test IQR outlier detection."""
        data = [10.1, 10.2, 10.0, 10.3, 10.1, 50.0]
        result = detect_outliers_iqr(data, multiplier=1.5)
        assert result.is_valid
        assert len(result.value["outliers"]) >= 1

    def test_calculate_combined_uncertainty(self):
        """Test combined uncertainty calculation."""
        uncertainties = [0.1, 0.05, 0.08]
        result = calculate_combined_uncertainty(uncertainties)
        assert result.is_valid
        assert result.value > 0

    def test_propagate_uncertainty(self):
        """Test uncertainty propagation."""
        result = propagate_uncertainty(10.0, 0.1, "*", 5.0, 0.05)
        assert result.is_valid
        assert result.value["result"] == 50.0

    def test_count_significant_figures(self):
        """Test significant figures counting."""
        assert count_significant_figures(0.00123) == 3
        assert count_significant_figures(1.230) == 4
        assert count_significant_figures(100) == 3

    def test_round_to_sig_figs(self):
        """Test rounding to significant figures."""
        result = round_to_sig_figs(123.456, 4)
        assert result.is_valid
        assert result.value == 123.5

    def test_convert_units(self):
        """Test unit conversion."""
        result = convert_units(1500, "mW", "W")
        assert result.is_valid
        assert result.value == 1.5

    def test_measurement_uncertainty(self):
        """Test MeasurementUncertainty dataclass."""
        mu = MeasurementUncertainty(value=100.0, uncertainty=2.0, k_factor=2.0)
        assert mu.expanded_uncertainty == 4.0
        assert mu.relative_uncertainty == 2.0


# ============================================================================
# Tests: file_validators.py
# ============================================================================

class TestFileValidators:
    """Test cases for file validation utilities."""

    def test_validate_file_size(self, test_file_path):
        """Test file size validation."""
        result = validate_file_size(str(test_file_path), file_category="csv")
        assert result.is_valid
        assert result.value > 0

    def test_validate_file_extension(self, test_file_path):
        """Test file extension validation."""
        result = validate_file_extension(str(test_file_path), [".csv", ".txt"])
        assert result.is_valid
        assert result.value == ".csv"

    def test_validate_csv_structure(self, test_file_path):
        """Test CSV structure validation."""
        result = validate_csv_structure(
            str(test_file_path),
            required_columns=["Module_ID", "Power_W", "Voltage_V"]
        )
        assert result.is_valid
        assert result.value["row_count"] == 2

    def test_validate_file(self, test_file_path):
        """Test complete file validation."""
        result = validate_file(
            str(test_file_path),
            max_size_mb=1.0,
            allowed_extensions=[".csv"],
            validate_mime=False  # Skip MIME for simple test
        )
        assert result.is_valid


# ============================================================================
# Tests: protocol_validators.py
# ============================================================================

class TestProtocolValidators:
    """Test cases for IEC/ISO protocol validators."""

    def test_validate_mst_sequence(self):
        """Test IEC 61215 MST sequence validation."""
        result = validate_mst_sequence(
            cycles=200,
            temperature_celsius=85.0,
            humidity_percent=85.0,
            duration_hours=1000,
            test_type="MST-200"
        )
        assert result.is_valid

    def test_validate_thermal_cycle(self):
        """Test IEC 61215 thermal cycling validation."""
        result = validate_thermal_cycle(-40, 85, 200)
        assert result.is_valid

    def test_validate_safety_test_voltage(self):
        """Test IEC 61730 safety voltage validation."""
        result = validate_safety_test_voltage(1000, 600, "B")
        assert result.is_valid

    def test_validate_dielectric_strength(self):
        """Test dielectric strength validation."""
        result = validate_dielectric_strength(2000, 60, 5.0)
        assert result.is_valid

    def test_validate_ammonia_concentration(self):
        """Test IEC 62716 ammonia test validation."""
        result = validate_ammonia_concentration(30, 168, 50, 90)
        assert result.is_valid

    def test_validate_salt_mist_severity(self):
        """Test IEC 61701 salt mist validation."""
        result = validate_salt_mist_severity(3, 30, 2.0)
        assert result.is_valid

    def test_validate_stc_conditions(self):
        """Test STC conditions validation."""
        result = validate_stc_conditions(1000, 25, "AM1.5G")
        assert result.is_valid

    def test_validate_module_power_rating(self):
        """Test module power rating validation."""
        result = validate_module_power_rating(320, 315, tolerance_percent=3.0)
        assert result.is_valid

    def test_validate_test_sequence_dependency(self):
        """Test test sequence dependency validation."""
        completed = ["Visual Inspection", "Electrical Testing"]
        prerequisites = {
            "Electrical Testing": ["Visual Inspection"],
            "MST": ["Electrical Testing", "Visual Inspection"]
        }
        result = validate_test_sequence_dependency(completed, prerequisites)
        assert result.is_valid


# ============================================================================
# Tests: iso17025_validators.py
# ============================================================================

class TestISO17025Validators:
    """Test cases for ISO 17025 compliance validators."""

    def test_validate_calibration_certificate(self, sample_calibration_cert):
        """Test calibration certificate validation."""
        result = validate_calibration_certificate(
            sample_calibration_cert.certificate_number,
            sample_calibration_cert.calibration_date,
            sample_calibration_cert.due_date
        )
        assert result.is_valid
        assert result.metadata["is_valid"]

    def test_validate_calibration_interval(self):
        """Test calibration interval validation."""
        cal_date = datetime(2024, 1, 1)
        due_date = datetime(2025, 1, 1)
        result = validate_calibration_interval(cal_date, due_date, 12)
        assert result.is_valid

    def test_validate_traceability_chain(self):
        """Test measurement traceability validation."""
        result = validate_traceability_chain(
            "SIM-001",
            "accredited_lab",
            reference_standard="NIST Reference Cell"
        )
        assert result.is_valid

    def test_validate_uncertainty_budget(self, sample_uncertainty_budget):
        """Test uncertainty budget validation."""
        result = validate_uncertainty_budget(sample_uncertainty_budget)
        assert result.is_valid

    def test_validate_accreditation_scope(self, nabl_accredited_scopes):
        """Test accreditation scope validation."""
        result = validate_accreditation_scope(
            "PV Module Testing",
            "IEC 61215",
            nabl_accredited_scopes,
            "NABL"
        )
        assert result.is_valid
        assert result.metadata["accredited"]

    def test_validate_equipment_qualification(self):
        """Test equipment qualification validation."""
        last_cal = datetime.now() - timedelta(days=200)
        last_ver = datetime.now() - timedelta(days=30)
        result = validate_equipment_qualification("SIM-001", last_cal, last_ver)
        assert result.is_valid

    def test_validate_measurement_result_reporting(self):
        """Test measurement result reporting validation."""
        result = validate_measurement_result_reporting(
            measured_value=320.5,
            uncertainty=3.2,
            unit="W",
            confidence_level=95.0
        )
        assert result.is_valid


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple validators."""

    def test_complete_test_report_validation(self):
        """Test complete test report validation workflow."""
        # Validate module serial
        serial_result = validate_module_serial("PV-2025-001234")
        assert serial_result.is_valid

        # Validate test conditions
        stc_result = validate_stc_conditions(1000, 25, "AM1.5G")
        assert stc_result.is_valid

        # Validate power measurement
        power_result = validate_module_power_rating(320, 315, 3.0)
        assert power_result.is_valid

        # Validate reviewer hierarchy
        reviewer_result = validate_reviewer_hierarchy(
            "tech01", "reviewer01", "manager01"
        )
        assert reviewer_result.is_valid

    def test_batch_validation(self):
        """Test batch validation of multiple validators."""
        validators = [
            (validate_module_serial, ("PV-2025-001234",), {}),
            (validate_email, ("tech@lab.com",), {}),
            (validate_percentage, (95.5,), {}),
        ]
        result = batch_validate(validators)
        assert result.is_valid
        assert result.metadata["passed"] == 3


# ============================================================================
# Parameterized Tests
# ============================================================================

@pytest.mark.parametrize("value,min_val,max_val,expected", [
    (50, 0, 100, True),
    (150, 0, 100, False),
    (-10, 0, 100, False),
    (0, 0, 100, True),
    (100, 0, 100, True),
])
def test_numeric_range_parametrized(value, min_val, max_val, expected):
    """Parameterized test for numeric range validation."""
    result = validate_numeric_range(value, min_val, max_val)
    assert result.is_valid == expected


@pytest.mark.parametrize("from_unit,to_unit,value,expected", [
    ("W", "kW", 1000, 1.0),
    ("mW", "W", 500, 0.5),
    ("V", "mV", 5, 5000),
    ("A", "mA", 2, 2000),
])
def test_unit_conversion_parametrized(from_unit, to_unit, value, expected):
    """Parameterized test for unit conversion."""
    result = convert_units(value, from_unit, to_unit)
    assert result.is_valid
    assert abs(result.value - expected) < 0.01


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Performance tests for validators."""

    def test_outlier_detection_performance(self):
        """Test outlier detection with large dataset."""
        import random
        data = [random.gauss(100, 5) for _ in range(1000)]
        data.extend([200, 250, 300])  # Add outliers

        result = detect_outliers_zscore(data, threshold=3.0)
        assert result.is_valid
        assert len(result.value["outliers"]) > 0

    def test_batch_validation_performance(self):
        """Test batch validation with many validators."""
        validators = [
            (validate_module_serial, (f"PV-2025-{i:06d}",), {})
            for i in range(100)
        ]
        result = batch_validate(validators)
        assert result.is_valid
        assert result.metadata["passed"] == 100


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_empty_input_handling(self):
        """Test handling of empty inputs."""
        result = validate_module_serial("")
        assert not result.is_valid

    def test_none_input_handling(self):
        """Test handling of None inputs."""
        # Should handle gracefully without crashing
        with pytest.raises((TypeError, AttributeError)):
            validate_numeric_range(None, 0, 100)

    def test_invalid_types(self):
        """Test handling of invalid type inputs."""
        result = validate_numeric_range("not_a_number", 0, 100)
        assert not result.is_valid


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
