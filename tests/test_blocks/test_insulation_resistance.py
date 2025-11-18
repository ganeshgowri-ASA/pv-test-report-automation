"""Unit tests for Insulation Resistance Test"""

import pytest
from datetime import datetime, timedelta

from src.test_blocks.insulation import InsulationResistanceTest, InsulationTest
from src.equipment.megohmmeter import MegohmeterSimulator
from src.models.measurement import EnvironmentalConditions


class TestInsulationTest:
    """Test InsulationTest model"""

    def test_insulation_test_creation(self):
        """Test creating InsulationTest instance"""
        test = InsulationTest(
            test_id=1,
            module_id=12345,
            test_voltage=1000,
            condition="wet",
            resistance_mohm=85.5,
            polarity="positive",
            pass_status=True
        )

        assert test.test_id == 1
        assert test.module_id == 12345
        assert test.test_voltage == 1000
        assert test.condition == "wet"
        assert test.resistance_mohm == 85.5
        assert test.polarity == "positive"
        assert test.pass_status is True
        assert isinstance(test.timestamp, datetime)

    def test_insulation_test_serialization(self):
        """Test JSON serialization"""
        test = InsulationTest(
            test_id=1,
            module_id=12345,
            test_voltage=1000,
            condition="wet",
            resistance_mohm=85.5,
            polarity="positive",
            pass_status=True
        )

        data = test.model_dump()
        assert data["test_id"] == 1
        assert data["resistance_mohm"] == 85.5


class TestInsulationResistanceTest:
    """Test InsulationResistanceTest class"""

    def test_initialization(self):
        """Test test initialization"""
        test = InsulationResistanceTest(module="PV-001", operator="Test Operator")
        assert test.module == "PV-001"
        assert test.operator == "Test Operator"
        assert isinstance(test.megohmmeter, MegohmeterSimulator)
        assert len(test.tests) == 0

    def test_initialize_success(self):
        """Test successful initialization"""
        test = InsulationResistanceTest(module="PV-001")
        result = test.initialize()

        assert result is True
        assert test.test_block is not None
        assert test.test_block.module_id == "PV-001"
        assert test.test_block.standard == "IEC 61215-2:2016 / IEC 61730-2:2016"
        assert test.megohmmeter.connected is True

    def test_measure_wet_condition_pass(self):
        """Test wet condition measurement that passes"""
        test = InsulationResistanceTest(module="PV-001")
        test.initialize()

        result = test.measure(voltage=1000, condition="wet", polarity="positive")

        assert result is not None
        assert result.test.test_voltage == 1000
        assert result.test.condition == "wet"
        assert result.test.polarity == "positive"
        assert result.test.resistance_mohm > 0
        # Pass status depends on simulated value, but should be consistent
        assert isinstance(result.test.pass_status, bool)

    def test_measure_dry_condition(self):
        """Test dry condition measurement"""
        test = InsulationResistanceTest(module="PV-002")
        test.initialize()

        result = test.measure(voltage=1000, condition="dry", polarity="positive")

        assert result.test.condition == "dry"
        assert result.test.resistance_mohm > 0

    def test_measure_different_voltages(self):
        """Test measurements at different voltages"""
        test = InsulationResistanceTest(module="PV-003")
        test.initialize()

        result_500v = test.measure(voltage=500, condition="wet")
        result_1000v = test.measure(voltage=1000, condition="wet")

        assert result_500v.test.test_voltage == 500
        assert result_1000v.test.test_voltage == 1000

    def test_pass_fail_logic_wet(self):
        """Test pass/fail logic for wet condition"""
        # Wet minimum: 40 MΩ
        test = InsulationResistanceTest(module="PV-004")

        # Create manual test to verify logic
        test_pass = InsulationTest(
            test_id=1,
            module_id=1,
            test_voltage=1000,
            condition="wet",
            resistance_mohm=50.0,  # Above 40 MΩ
            polarity="positive",
            pass_status=50.0 >= InsulationResistanceTest.WET_MINIMUM_RESISTANCE_MOHM
        )

        test_fail = InsulationTest(
            test_id=2,
            module_id=1,
            test_voltage=1000,
            condition="wet",
            resistance_mohm=30.0,  # Below 40 MΩ
            polarity="positive",
            pass_status=30.0 >= InsulationResistanceTest.WET_MINIMUM_RESISTANCE_MOHM
        )

        assert test_pass.pass_status is True
        assert test_fail.pass_status is False

    def test_pass_fail_logic_dry(self):
        """Test pass/fail logic for dry condition"""
        # Dry minimum: 400 MΩ
        test_pass = InsulationTest(
            test_id=1,
            module_id=1,
            test_voltage=1000,
            condition="dry",
            resistance_mohm=500.0,  # Above 400 MΩ
            polarity="positive",
            pass_status=500.0 >= InsulationResistanceTest.DRY_MINIMUM_RESISTANCE_MOHM
        )

        test_fail = InsulationTest(
            test_id=2,
            module_id=1,
            test_voltage=1000,
            condition="dry",
            resistance_mohm=300.0,  # Below 400 MΩ
            polarity="positive",
            pass_status=300.0 >= InsulationResistanceTest.DRY_MINIMUM_RESISTANCE_MOHM
        )

        assert test_pass.pass_status is True
        assert test_fail.pass_status is False

    def test_full_test_sequence(self):
        """Test full test sequence with both polarities"""
        test = InsulationResistanceTest(module="PV-005")
        test.initialize()

        results = test.run_full_test_sequence(
            voltage=1000,
            condition="wet",
            test_both_polarities=True
        )

        assert len(results) == 2
        assert results[0].test.polarity == "positive"
        assert results[1].test.polarity == "negative"

    def test_full_test_sequence_single_polarity(self):
        """Test full test sequence with single polarity"""
        test = InsulationResistanceTest(module="PV-006")
        test.initialize()

        results = test.run_full_test_sequence(
            voltage=1000,
            condition="wet",
            test_both_polarities=False
        )

        assert len(results) == 1
        assert results[0].test.polarity == "positive"

    def test_environmental_conditions(self):
        """Test with environmental conditions"""
        env = EnvironmentalConditions(
            temperature_c=25.0,
            humidity_percent=50.0,
            pressure_hpa=1013.25
        )

        test = InsulationResistanceTest(module="PV-007")
        test.initialize()

        result = test.measure(
            voltage=1000,
            condition="wet",
            environmental_conditions=env
        )

        assert result.environmental_conditions is not None
        assert result.environmental_conditions.temperature_c == 25.0
        assert result.environmental_conditions.humidity_percent == 50.0

    def test_finalize(self):
        """Test test finalization"""
        test = InsulationResistanceTest(module="PV-008")
        test.initialize()

        # Perform some measurements
        test.measure(voltage=1000, condition="wet")
        test.measure(voltage=1000, condition="wet", polarity="negative")

        summary = test.finalize()

        assert summary is not None
        assert summary["module"] == "PV-008"
        assert summary["total_tests"] == 2
        assert "overall_status" in summary
        assert summary["overall_status"] in ["PASS", "FAIL"]
        assert test.test_block.status.value in ["completed", "failed"]

    def test_context_manager(self):
        """Test context manager usage"""
        with InsulationResistanceTest(module="PV-009") as test:
            result = test.measure(voltage=1000, condition="wet")
            assert result is not None

        # Test should be finalized and equipment disconnected
        assert test.megohmmeter.connected is False

    def test_measure_without_initialization(self):
        """Test that measure fails without initialization"""
        test = InsulationResistanceTest(module="PV-010")

        with pytest.raises(RuntimeError, match="Test not initialized"):
            test.measure(voltage=1000, condition="wet")

    def test_invalid_voltage(self):
        """Test with invalid voltage"""
        test = InsulationResistanceTest(module="PV-011")
        test.initialize()

        # This should be caught by type checking, but test runtime behavior
        with pytest.raises((ValueError, Exception)):
            test.measure(voltage=750, condition="wet")  # Invalid voltage

    def test_test_counter_increments(self):
        """Test that test counter increments properly"""
        test = InsulationResistanceTest(module="PV-012")
        test.initialize()

        assert test.test_counter == 0

        test.measure(voltage=1000, condition="wet")
        assert test.test_counter == 1

        test.measure(voltage=1000, condition="wet")
        assert test.test_counter == 2

        test.measure(voltage=1000, condition="wet")
        assert test.test_counter == 3

    def test_audit_trail(self):
        """Test audit trail creation"""
        test = InsulationResistanceTest(module="PV-013", operator="Test User")
        test.initialize()

        test.measure(voltage=1000, condition="wet")

        assert test.test_block is not None
        assert len(test.test_block.audit_trail) > 0

        # Check for specific audit entries
        audit_actions = [entry.action for entry in test.test_block.audit_trail]
        assert "test_initialized" in audit_actions
        assert "measurement_started" in audit_actions
        assert "measurement_completed" in audit_actions

    def test_compliance_data(self):
        """Test compliance data is properly set"""
        test = InsulationResistanceTest(module="PV-014")
        test.initialize()

        assert test.test_block.compliance_data is not None
        assert test.test_block.compliance_data.standard == "IEC 61215-2:2016 / IEC 61730-2:2016"
        assert test.test_block.compliance_data.accreditation == "ISO/IEC 17025"

    def test_calibration_validation(self):
        """Test that calibration is validated"""
        # Simulator should have valid calibration
        test = InsulationResistanceTest(module="PV-015")
        result = test.initialize()

        assert result is True
        assert test.megohmmeter.is_calibration_valid() is True

    def test_data_logging_enabled(self):
        """Test with data logging enabled"""
        test = InsulationResistanceTest(
            module="PV-016",
            enable_logging=True,
            enable_iso17025=True
        )
        test.initialize()
        test.measure(voltage=1000, condition="wet")
        summary = test.finalize()

        assert summary is not None
        # Logging should create files (check in actual integration test)

    def test_data_logging_disabled(self):
        """Test with data logging disabled"""
        test = InsulationResistanceTest(
            module="PV-017",
            enable_logging=False,
            enable_iso17025=False
        )
        test.initialize()
        test.measure(voltage=1000, condition="wet")
        summary = test.finalize()

        assert summary is not None


class TestMegohmeterSimulator:
    """Test Megohmmeter simulator"""

    def test_simulator_creation(self):
        """Test creating simulator"""
        sim = MegohmeterSimulator()
        assert sim.info.instrument_id.startswith("SIM-MEG-")
        assert sim.info.manufacturer == "Simulated"

    def test_simulator_connection(self):
        """Test simulator connection"""
        sim = MegohmeterSimulator()
        assert sim.connect() is True
        assert sim.connected is True

        assert sim.disconnect() is True
        assert sim.connected is False

    def test_simulator_measurement(self):
        """Test simulator measurement"""
        sim = MegohmeterSimulator()
        sim.connect()

        resistance = sim.measure_resistance(test_voltage=1000, measurement_time=1)

        assert resistance is not None
        assert resistance > 0
        # Simulator should return realistic values (40-900 MΩ range)
        assert 30 < resistance < 1000

    def test_simulator_calibration_valid(self):
        """Test simulator calibration"""
        sim = MegohmeterSimulator()
        assert sim.is_calibration_valid() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
