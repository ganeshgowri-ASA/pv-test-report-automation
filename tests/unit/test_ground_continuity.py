"""Unit tests for Ground Continuity Test module."""

import pytest
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from test_blocks.ground_continuity import (
    GroundContinuityTest,
    GroundContinuityMeasurement,
    MeasurementPoint,
    WireConfiguration,
)
from test_blocks.base import EnvironmentalConditions, TestStatus


class TestGroundContinuityTest:
    """Test cases for GroundContinuityTest class."""

    def test_initialization_default_parameters(self):
        """Test initialization with default parameters."""
        test = GroundContinuityTest(
            test_id="GC-001",
            module_id="PV-001",
            operator="Test Operator"
        )

        assert test.test_id == "GC-001"
        assert test.module_id == "PV-001"
        assert test.operator == "Test Operator"
        assert test.test_current == 25.0
        assert test.test_duration == 60.0
        assert test.max_resistance_ohm == 0.1
        assert test.wire_configuration == WireConfiguration.FOUR_WIRE_KELVIN

    def test_initialization_custom_parameters(self):
        """Test initialization with custom parameters."""
        test = GroundContinuityTest(
            test_id="GC-002",
            module_id="PV-002",
            operator="Test Operator",
            test_current=30.0,
            test_duration=90.0,
            max_resistance_ohm=0.08
        )

        assert test.test_current == 30.0
        assert test.test_duration == 90.0
        assert test.max_resistance_ohm == 0.08

    def test_validation_test_current_too_low(self):
        """Test validation rejects current below minimum."""
        with pytest.raises(ValueError, match="below minimum requirement"):
            GroundContinuityTest(
                test_id="GC-003",
                module_id="PV-003",
                operator="Test Operator",
                test_current=5.0  # Too low
            )

    def test_validation_test_current_too_high(self):
        """Test validation rejects current above maximum."""
        with pytest.raises(ValueError, match="exceeds maximum safe limit"):
            GroundContinuityTest(
                test_id="GC-004",
                module_id="PV-004",
                operator="Test Operator",
                test_current=60.0  # Too high
            )

    def test_validation_test_duration_too_short(self):
        """Test validation rejects duration below minimum."""
        with pytest.raises(ValueError, match="at least 30 seconds"):
            GroundContinuityTest(
                test_id="GC-005",
                module_id="PV-005",
                operator="Test Operator",
                test_duration=20.0  # Too short
            )

    def test_validation_max_resistance_invalid(self):
        """Test validation rejects invalid resistance threshold."""
        with pytest.raises(ValueError, match="threshold too high"):
            GroundContinuityTest(
                test_id="GC-006",
                module_id="PV-006",
                operator="Test Operator",
                max_resistance_ohm=1.5  # Too high
            )

    def test_validate_test_conditions_valid(self):
        """Test condition validation with valid parameters."""
        env = EnvironmentalConditions(
            temperature_celsius=25.0,
            humidity_percent=50.0
        )

        test = GroundContinuityTest(
            test_id="GC-007",
            module_id="PV-007",
            operator="Test Operator",
            environmental_conditions=env
        )

        assert test.validate_test_conditions() is True

    def test_validate_test_conditions_temperature_out_of_range(self):
        """Test condition validation rejects temperature out of range."""
        env = EnvironmentalConditions(
            temperature_celsius=40.0,  # Too high
            humidity_percent=50.0
        )

        test = GroundContinuityTest(
            test_id="GC-008",
            module_id="PV-008",
            operator="Test Operator",
            environmental_conditions=env
        )

        with pytest.raises(ValueError, match="temperature.*outside acceptable range"):
            test.validate_test_conditions()

    def test_validate_test_conditions_humidity_out_of_range(self):
        """Test condition validation rejects humidity out of range."""
        env = EnvironmentalConditions(
            temperature_celsius=25.0,
            humidity_percent=90.0  # Too high
        )

        test = GroundContinuityTest(
            test_id="GC-009",
            module_id="PV-009",
            operator="Test Operator",
            environmental_conditions=env
        )

        with pytest.raises(ValueError, match="humidity.*outside acceptable range"):
            test.validate_test_conditions()

    def test_pre_test_safety_check_pass(self):
        """Test pre-test safety check with valid parameters."""
        test = GroundContinuityTest(
            test_id="GC-010",
            module_id="PV-010",
            operator="Test Operator"
        )

        assert test.pre_test_safety_check() is True

    def test_pre_test_safety_check_fail(self):
        """Test pre-test safety check with invalid parameters."""
        test = GroundContinuityTest(
            test_id="GC-011",
            module_id="PV-011",
            operator="Test Operator",
            test_current=25.0,
            emergency_current_limit=20.0  # Current exceeds emergency limit
        )

        assert test.pre_test_safety_check() is False

    def test_perform_measurement_simulated(self):
        """Test simulated measurement."""
        test = GroundContinuityTest(
            test_id="GC-012",
            module_id="PV-012",
            operator="Test Operator"
        )

        result = test.perform_measurement(simulated=True)

        assert "measurements" in result
        assert "total_points" in result
        assert result["total_points"] > 0
        assert len(test.measurements) == result["total_points"]

    def test_perform_measurement_specific_point(self):
        """Test measurement of specific point."""
        test = GroundContinuityTest(
            test_id="GC-013",
            module_id="PV-013",
            operator="Test Operator"
        )

        result = test.perform_measurement(
            measurement_point=MeasurementPoint.FRAME_TO_GROUND.value,
            simulated=True
        )

        assert result["total_points"] == 1
        assert result["measurements"][0].measurement_point == MeasurementPoint.FRAME_TO_GROUND.value

    def test_simulate_measurement_fixed_resistance(self):
        """Test simulation with fixed resistance value."""
        test = GroundContinuityTest(
            test_id="GC-014",
            module_id="PV-014",
            operator="Test Operator"
        )

        result = test.perform_measurement(
            measurement_point=MeasurementPoint.FRAME_TO_GROUND.value,
            simulated=True,
            simulated_resistance=0.05
        )

        measurement = result["measurements"][0]
        assert abs(measurement.measured_resistance.value - 0.05) < 0.001

    def test_evaluate_pass_fail_passing(self):
        """Test pass/fail evaluation with passing measurements."""
        test = GroundContinuityTest(
            test_id="GC-015",
            module_id="PV-015",
            operator="Test Operator"
        )

        # Perform measurement with low resistance
        result = test.perform_measurement(simulated=True, simulated_resistance=0.05)

        # Evaluate
        pass_status = test.evaluate_pass_fail(result)

        assert pass_status is True
        assert test.overall_pass_status is True

    def test_evaluate_pass_fail_failing(self):
        """Test pass/fail evaluation with failing measurements."""
        test = GroundContinuityTest(
            test_id="GC-016",
            module_id="PV-016",
            operator="Test Operator",
            max_resistance_ohm=0.1
        )

        # Perform measurement with high resistance
        result = test.perform_measurement(simulated=True, simulated_resistance=0.25)

        # Evaluate
        pass_status = test.evaluate_pass_fail(result)

        assert pass_status is False
        assert test.overall_pass_status is False

    def test_generate_report(self):
        """Test report generation."""
        test = GroundContinuityTest(
            test_id="GC-017",
            module_id="PV-017",
            operator="Test Operator"
        )

        # Perform measurements
        test.perform_measurement(simulated=True)

        # Generate report
        report = test.generate_report()

        # Verify report structure
        assert "test_information" in report
        assert "test_parameters" in report
        assert "measurements" in report
        assert "statistics" in report
        assert "result" in report
        assert "iso_17025_compliance" in report

        # Verify test information
        assert report["test_information"]["test_id"] == "GC-017"
        assert report["test_information"]["module_id"] == "PV-017"
        assert report["test_information"]["standard"] == "IEC 61730"

        # Verify statistics
        assert report["statistics"]["total_points_measured"] > 0

    def test_run_test_complete_sequence(self):
        """Test complete test sequence."""
        test = GroundContinuityTest(
            test_id="GC-018",
            module_id="PV-018",
            operator="Test Operator"
        )

        # Run complete test
        report = test.run_test(simulated=True)

        # Verify report generated
        assert report is not None
        assert "result" in report
        assert "overall_status" in report["result"]

    def test_measurement_points_enumeration(self):
        """Test all measurement point enumerations."""
        expected_points = [
            "frame_to_ground",
            "frame_to_terminal",
            "mounting_hole_1",
            "mounting_hole_2",
            "mounting_hole_3",
            "mounting_hole_4",
            "junction_box_to_frame",
        ]

        for point in expected_points:
            # Verify enumeration exists
            assert hasattr(MeasurementPoint, point.upper())

    def test_wire_configuration_types(self):
        """Test wire configuration types."""
        assert WireConfiguration.TWO_WIRE.value == "2-wire"
        assert WireConfiguration.FOUR_WIRE_KELVIN.value == "4-wire-kelvin"

    def test_post_test_safety_check(self):
        """Test post-test safety check."""
        test = GroundContinuityTest(
            test_id="GC-019",
            module_id="PV-019",
            operator="Test Operator"
        )

        # Perform measurements
        test.perform_measurement(simulated=True)

        # Post-test check
        assert test.post_test_safety_check() is True

    def test_measurement_with_environmental_conditions(self):
        """Test measurement recording environmental conditions."""
        env = EnvironmentalConditions(
            temperature_celsius=23.5,
            humidity_percent=45.0,
            pressure_kpa=101.3
        )

        test = GroundContinuityTest(
            test_id="GC-020",
            module_id="PV-020",
            operator="Test Operator",
            environmental_conditions=env
        )

        report = test.run_test(simulated=True)

        assert report["environmental_conditions"] is not None
        assert report["environmental_conditions"]["temperature_celsius"] == 23.5
        assert report["environmental_conditions"]["humidity_percent"] == 45.0


class TestGroundContinuityMeasurement:
    """Test cases for GroundContinuityMeasurement class."""

    def test_measurement_creation(self):
        """Test measurement object creation."""
        from test_blocks.base import MeasurementUncertainty

        measurement = GroundContinuityMeasurement(
            test_id="GC-M-001",
            test_name="Test Measurement",
            standard="IEC 61730",
            operator="Test Operator",
            measurement_point=MeasurementPoint.FRAME_TO_GROUND.value,
            test_current_amps=25.0,
            measured_resistance=MeasurementUncertainty(
                value=0.05,
                uncertainty=0.002,
                unit="Ohm"
            ),
            test_duration_seconds=60.0
        )

        assert measurement.measurement_point == MeasurementPoint.FRAME_TO_GROUND.value
        assert measurement.test_current_amps == 25.0
        assert measurement.measured_resistance.value == 0.05

    def test_measurement_current_validation(self):
        """Test measurement current validation."""
        from test_blocks.base import MeasurementUncertainty

        with pytest.raises(ValueError, match="Test current must be positive"):
            GroundContinuityMeasurement(
                test_id="GC-M-002",
                test_name="Test Measurement",
                standard="IEC 61730",
                operator="Test Operator",
                measurement_point=MeasurementPoint.FRAME_TO_GROUND.value,
                test_current_amps=-5.0,  # Negative current
                measured_resistance=MeasurementUncertainty(
                    value=0.05,
                    uncertainty=0.002,
                    unit="Ohm"
                ),
                test_duration_seconds=60.0
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
