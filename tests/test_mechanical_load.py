"""Unit tests for Mechanical Load Test Block.

Tests cover:
- Test initialization and validation
- Static and dynamic load test modes
- Deflection monitoring
- Power degradation calculation
- Pass/fail criteria
- ISO 17025 traceability
- Report generation
"""

import pytest
from datetime import datetime
from uuid import UUID

from pv_automation.test_blocks.mechanical import (
    DeflectionMeasurement,
    LoadType,
    LoadSurface,
    MechanicalLoadTest,
    PowerMeasurement,
)
from pv_automation.test_blocks.base_test_block import TestStatus, TestStandard


class TestPowerMeasurement:
    """Test cases for PowerMeasurement model."""

    def test_power_measurement_creation(self):
        """Test creating a valid power measurement."""
        pm = PowerMeasurement(
            pmax_w=450.0,
            voc_v=48.5,
            isc_a=11.2,
            vmp_v=40.2,
            imp_a=11.19,
            fill_factor=0.827
        )
        assert pm.pmax_w == 450.0
        assert pm.fill_factor == 0.827
        assert pm.irradiance_wm2 == 1000.0  # default
        assert pm.temperature_c == 25.0  # default

    def test_power_measurement_validation(self):
        """Test power measurement validation."""
        # Negative power should fail
        with pytest.raises(ValueError):
            PowerMeasurement(
                pmax_w=-450.0,
                voc_v=48.5,
                isc_a=11.2,
                vmp_v=40.2,
                imp_a=11.19,
                fill_factor=0.827
            )

        # Fill factor > 1 should fail
        with pytest.raises(ValueError):
            PowerMeasurement(
                pmax_w=450.0,
                voc_v=48.5,
                isc_a=11.2,
                vmp_v=40.2,
                imp_a=11.19,
                fill_factor=1.1
            )


class TestDeflectionMeasurement:
    """Test cases for DeflectionMeasurement model."""

    def test_deflection_measurement_creation(self):
        """Test creating a deflection measurement."""
        dm = DeflectionMeasurement(
            load_pa=2400.0,
            deflection_mm=22.3,
            position="center"
        )
        assert dm.load_pa == 2400.0
        assert dm.deflection_mm == 22.3
        assert dm.position == "center"
        assert dm.cycle_number is None

    def test_deflection_with_cycle_number(self):
        """Test deflection measurement with cycle number."""
        dm = DeflectionMeasurement(
            load_pa=1000.0,
            deflection_mm=12.5,
            position="center",
            cycle_number=500
        )
        assert dm.cycle_number == 500


class TestMechanicalLoadTestInitialization:
    """Test cases for MechanicalLoadTest initialization."""

    def test_static_load_test_creation(self):
        """Test creating a static load test."""
        test = MechanicalLoadTest(
            module_id="PV-001",
            load_type=LoadType.STATIC_FRONT,
            load_pa=2400.0,
            operator_name="Test Operator"
        )
        assert test.module_id == "PV-001"
        assert test.load_type == LoadType.STATIC_FRONT
        assert test.load_pa == 2400.0
        assert test.status == TestStatus.PENDING
        assert test.test_standard == TestStandard.IEC_61215

    def test_dynamic_load_test_creation(self):
        """Test creating a dynamic load test."""
        test = MechanicalLoadTest(
            module_id="PV-002",
            load_type=LoadType.DYNAMIC,
            load_pa=1000.0,
            cycles=1000,
            operator_name="Test Operator"
        )
        assert test.load_type == LoadType.DYNAMIC
        assert test.cycles == 1000
        assert isinstance(test.id, UUID)

    def test_invalid_load_value(self):
        """Test validation of load values."""
        with pytest.raises(ValueError):
            MechanicalLoadTest(
                module_id="PV-001",
                load_type=LoadType.STATIC_FRONT,
                load_pa=-2400.0,  # Negative load
                operator_name="Test Operator"
            )

    def test_empty_module_id(self):
        """Test validation of module ID."""
        with pytest.raises(ValueError):
            MechanicalLoadTest(
                module_id="",
                load_type=LoadType.STATIC_FRONT,
                load_pa=2400.0,
                operator_name="Test Operator"
            )


class TestDeflectionMonitoring:
    """Test cases for deflection monitoring."""

    def test_add_deflection_measurement(self):
        """Test adding deflection measurements."""
        test = MechanicalLoadTest(
            module_id="PV-001",
            load_type=LoadType.STATIC_FRONT,
            load_pa=2400.0,
            operator_name="Test Operator"
        )

        test.add_deflection_measurement(load_pa=0, deflection_mm=0)
        test.add_deflection_measurement(load_pa=1200, deflection_mm=10.8)
        test.add_deflection_measurement(load_pa=2400, deflection_mm=22.3)

        assert len(test.deflection_measurements) == 3
        assert test.max_deflection_mm == 22.3

    def test_max_deflection_tracking(self):
        """Test that max deflection is tracked correctly."""
        test = MechanicalLoadTest(
            module_id="PV-001",
            load_type=LoadType.DYNAMIC,
            load_pa=1000.0,
            cycles=10,
            operator_name="Test Operator"
        )

        test.add_deflection_measurement(load_pa=1000, deflection_mm=12.5)
        test.add_deflection_measurement(load_pa=-1000, deflection_mm=-15.3)
        test.add_deflection_measurement(load_pa=1000, deflection_mm=12.8)

        # Should track absolute maximum
        assert test.max_deflection_mm == 15.3

    def test_deflection_statistics(self):
        """Test deflection statistics calculation."""
        test = MechanicalLoadTest(
            module_id="PV-001",
            load_type=LoadType.STATIC_FRONT,
            load_pa=2400.0,
            operator_name="Test Operator"
        )

        test.add_deflection_measurement(load_pa=600, deflection_mm=5.0)
        test.add_deflection_measurement(load_pa=1200, deflection_mm=10.0)
        test.add_deflection_measurement(load_pa=1800, deflection_mm=15.0)
        test.add_deflection_measurement(load_pa=2400, deflection_mm=20.0)

        stats = test.calculate_statistics()
        assert stats["mean_deflection_mm"] == 12.5
        assert stats["max_deflection_mm"] == 20.0
        assert stats["min_deflection_mm"] == 5.0
        assert stats["measurement_count"] == 4


class TestPowerDegradation:
    """Test cases for power degradation analysis."""

    def test_power_degradation_calculation(self):
        """Test power degradation calculation."""
        test = MechanicalLoadTest(
            module_id="PV-001",
            load_type=LoadType.STATIC_FRONT,
            load_pa=2400.0,
            operator_name="Test Operator"
        )

        # Pre-test: 450W
        pre_power = PowerMeasurement(
            pmax_w=450.0,
            voc_v=48.5,
            isc_a=11.2,
            vmp_v=40.2,
            imp_a=11.19,
            fill_factor=0.827
        )
        test.set_pre_test_power(pre_power)

        # Post-test: 445.5W (1% degradation)
        post_power = PowerMeasurement(
            pmax_w=445.5,
            voc_v=48.4,
            isc_a=11.18,
            vmp_v=40.1,
            imp_a=11.11,
            fill_factor=0.825
        )
        test.set_post_test_power(post_power)

        assert test.power_degradation_pct == pytest.approx(1.0, rel=1e-2)

    def test_no_degradation(self):
        """Test case with no power degradation."""
        test = MechanicalLoadTest(
            module_id="PV-001",
            load_type=LoadType.STATIC_FRONT,
            load_pa=2400.0,
            operator_name="Test Operator"
        )

        power = PowerMeasurement(
            pmax_w=450.0,
            voc_v=48.5,
            isc_a=11.2,
            vmp_v=40.2,
            imp_a=11.19,
            fill_factor=0.827
        )
        test.set_pre_test_power(power)
        test.set_post_test_power(power)

        assert test.power_degradation_pct == 0.0


class TestPassFailCriteria:
    """Test cases for pass/fail criteria evaluation."""

    def test_passing_test(self):
        """Test that passes all criteria."""
        test = MechanicalLoadTest(
            module_id="PV-001",
            load_type=LoadType.STATIC_FRONT,
            load_pa=2400.0,
            operator_name="Test Operator"
        )

        # Pre-test power
        pre_power = PowerMeasurement(
            pmax_w=450.0,
            voc_v=48.5,
            isc_a=11.2,
            vmp_v=40.2,
            imp_a=11.19,
            fill_factor=0.827
        )
        test.set_pre_test_power(pre_power)

        # Acceptable deflection
        test.add_deflection_measurement(load_pa=2400, deflection_mm=22.3)

        # Post-test: 3% degradation (within limit)
        post_power = PowerMeasurement(
            pmax_w=436.5,
            voc_v=48.3,
            isc_a=11.1,
            vmp_v=40.0,
            imp_a=10.91,
            fill_factor=0.820
        )
        test.set_post_test_power(post_power)

        result = test.execute()
        assert result is True
        assert test.pass_status is True
        assert test.status == TestStatus.PASSED

    def test_failing_test_power_degradation(self):
        """Test that fails due to excessive power degradation."""
        test = MechanicalLoadTest(
            module_id="PV-001",
            load_type=LoadType.STATIC_FRONT,
            load_pa=2400.0,
            operator_name="Test Operator"
        )

        # Pre-test power
        pre_power = PowerMeasurement(
            pmax_w=450.0,
            voc_v=48.5,
            isc_a=11.2,
            vmp_v=40.2,
            imp_a=11.19,
            fill_factor=0.827
        )
        test.set_pre_test_power(pre_power)

        # Acceptable deflection
        test.add_deflection_measurement(load_pa=2400, deflection_mm=22.3)

        # Post-test: 8% degradation (exceeds limit)
        post_power = PowerMeasurement(
            pmax_w=414.0,
            voc_v=47.8,
            isc_a=10.9,
            vmp_v=39.5,
            imp_a=10.48,
            fill_factor=0.795
        )
        test.set_post_test_power(post_power)

        result = test.execute()
        assert result is False
        assert test.pass_status is False
        assert test.status == TestStatus.FAILED
        assert len(test.error_messages) > 0

    def test_failing_test_excessive_deflection(self):
        """Test that fails due to excessive deflection."""
        test = MechanicalLoadTest(
            module_id="PV-001",
            load_type=LoadType.STATIC_FRONT,
            load_pa=2400.0,
            operator_name="Test Operator"
        )

        # Pre-test power
        pre_power = PowerMeasurement(
            pmax_w=450.0,
            voc_v=48.5,
            isc_a=11.2,
            vmp_v=40.2,
            imp_a=11.19,
            fill_factor=0.827
        )
        test.set_pre_test_power(pre_power)

        # Excessive deflection (exceeds 40mm limit)
        test.add_deflection_measurement(load_pa=2400, deflection_mm=45.0)

        # Post-test: acceptable degradation
        post_power = PowerMeasurement(
            pmax_w=445.5,
            voc_v=48.4,
            isc_a=11.18,
            vmp_v=40.1,
            imp_a=11.11,
            fill_factor=0.825
        )
        test.set_post_test_power(post_power)

        result = test.execute()
        assert result is False
        assert test.pass_status is False


class TestValidation:
    """Test cases for input validation."""

    def test_validate_dynamic_test_requires_cycles(self):
        """Test that dynamic tests require cycles."""
        test = MechanicalLoadTest(
            module_id="PV-001",
            load_type=LoadType.DYNAMIC,
            load_pa=1000.0,
            # Missing cycles
            operator_name="Test Operator"
        )

        assert test.validate_input_data() is False
        assert len(test.error_messages) > 0

    def test_iec_61215_compliance_warning(self):
        """Test IEC 61215 compliance warnings."""
        test = MechanicalLoadTest(
            module_id="PV-001",
            load_type=LoadType.STATIC_FRONT,
            load_pa=3000.0,  # Non-standard load
            operator_name="Test Operator"
        )

        test.validate_input_data()
        assert len(test.warnings) > 0


class TestISO17025Traceability:
    """Test cases for ISO 17025 traceability."""

    def test_equipment_tracking(self):
        """Test equipment ID tracking."""
        test = MechanicalLoadTest(
            module_id="PV-001",
            load_type=LoadType.STATIC_FRONT,
            load_pa=2400.0,
            operator_name="Test Operator",
            equipment_ids=["PRESS-001", "LVDT-001", "IV-TRACER-001"]
        )

        assert len(test.equipment_ids) == 3
        assert "PRESS-001" in test.equipment_ids

    def test_environmental_conditions(self):
        """Test environmental conditions tracking."""
        test = MechanicalLoadTest(
            module_id="PV-001",
            load_type=LoadType.STATIC_FRONT,
            load_pa=2400.0,
            operator_name="Test Operator",
            environmental_conditions={
                "temperature_c": 23.5,
                "humidity_pct": 45.0,
                "atmospheric_pressure_kpa": 101.3
            }
        )

        assert test.environmental_conditions["temperature_c"] == 23.5
        assert test.environmental_conditions["humidity_pct"] == 45.0

    def test_operator_tracking(self):
        """Test operator name tracking."""
        test = MechanicalLoadTest(
            module_id="PV-001",
            load_type=LoadType.STATIC_FRONT,
            load_pa=2400.0,
            operator_name="John Smith"
        )

        assert test.operator_name == "John Smith"


class TestReportGeneration:
    """Test cases for report generation."""

    def test_generate_report_structure(self):
        """Test report generation structure."""
        test = MechanicalLoadTest(
            module_id="PV-001",
            load_type=LoadType.STATIC_FRONT,
            load_pa=2400.0,
            operator_name="Test Operator"
        )

        report = test.generate_report()

        # Check required fields
        assert "test_id" in report
        assert "test_name" in report
        assert "test_standard" in report
        assert "module_id" in report
        assert "status" in report
        assert "load_type" in report
        assert "load_pa" in report
        assert "operator_name" in report

    def test_report_includes_measurements(self):
        """Test that report includes all measurements."""
        test = MechanicalLoadTest(
            module_id="PV-001",
            load_type=LoadType.STATIC_FRONT,
            load_pa=2400.0,
            operator_name="Test Operator"
        )

        pre_power = PowerMeasurement(
            pmax_w=450.0,
            voc_v=48.5,
            isc_a=11.2,
            vmp_v=40.2,
            imp_a=11.19,
            fill_factor=0.827
        )
        test.set_pre_test_power(pre_power)

        report = test.generate_report()
        assert report["pre_test_power"] is not None
        assert report["pre_test_power"]["pmax_w"] == 450.0


class TestTestExecution:
    """Test cases for test execution flow."""

    def test_test_lifecycle(self):
        """Test complete test lifecycle."""
        test = MechanicalLoadTest(
            module_id="PV-001",
            load_type=LoadType.STATIC_FRONT,
            load_pa=2400.0,
            operator_name="Test Operator"
        )

        assert test.status == TestStatus.PENDING
        assert test.start_time is None

        test.start_test()
        assert test.status == TestStatus.RUNNING
        assert test.start_time is not None

        test.complete_test(passed=True)
        assert test.status == TestStatus.PASSED
        assert test.end_time is not None
        assert test.duration_seconds is not None

    def test_test_abort(self):
        """Test aborting a test."""
        test = MechanicalLoadTest(
            module_id="PV-001",
            load_type=LoadType.STATIC_FRONT,
            load_pa=2400.0,
            operator_name="Test Operator"
        )

        test.start_test()
        test.abort_test("Equipment failure")

        assert test.status == TestStatus.ABORTED
        assert len(test.error_messages) > 0
        assert "Equipment failure" in test.error_messages[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
