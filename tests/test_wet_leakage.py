"""
Unit tests for Wet Leakage Current Test Block.
"""

import unittest
from datetime import datetime, timedelta

from test_blocks.wet_leakage import WetLeakageTest, WetLeakageTestResult
from models.base import TestStatus


class TestWetLeakageTestResult(unittest.TestCase):
    """Test WetLeakageTestResult data model."""

    def test_basic_result_creation(self):
        """Test creating a basic test result."""
        result = WetLeakageTestResult(
            test_id=1,
            module_id=101,
            applied_voltage=1200.0,
            leakage_current_ua=25.5,
            duration_sec=120
        )

        self.assertEqual(result.test_id, 1)
        self.assertEqual(result.module_id, 101)
        self.assertEqual(result.applied_voltage, 1200.0)
        self.assertEqual(result.leakage_current_ua, 25.5)
        self.assertEqual(result.duration_sec, 120)

    def test_pass_fail_determination(self):
        """Test pass/fail logic."""
        # Test passing result
        result_pass = WetLeakageTestResult(
            test_id=1,
            module_id=101,
            applied_voltage=1200.0,
            leakage_current_ua=25.5,  # Below 50μA limit
            duration_sec=120  # Meets minimum 120s
        )
        self.assertTrue(result_pass.determine_pass_fail())
        self.assertTrue(result_pass.pass_status)

        # Test failing result (excessive current)
        result_fail_current = WetLeakageTestResult(
            test_id=2,
            module_id=102,
            applied_voltage=1200.0,
            leakage_current_ua=75.0,  # Exceeds 50μA limit
            duration_sec=120
        )
        self.assertFalse(result_fail_current.determine_pass_fail())
        self.assertFalse(result_fail_current.pass_status)

        # Test failing result (insufficient duration)
        result_fail_duration = WetLeakageTestResult(
            test_id=3,
            module_id=103,
            applied_voltage=1200.0,
            leakage_current_ua=25.5,
            duration_sec=60  # Below minimum 120s
        )
        self.assertFalse(result_fail_duration.determine_pass_fail())
        self.assertFalse(result_fail_duration.pass_status)

    def test_voltage_validation(self):
        """Test voltage validation."""
        # Valid voltage
        result = WetLeakageTestResult(
            test_id=1,
            module_id=101,
            applied_voltage=1200.0,
            leakage_current_ua=25.5,
            duration_sec=120
        )
        self.assertEqual(result.applied_voltage, 1200.0)

        # Test minimum voltage requirement
        with self.assertRaises(ValueError):
            WetLeakageTestResult(
                test_id=2,
                module_id=102,
                applied_voltage=500.0,  # Below 1000V minimum
                leakage_current_ua=25.5,
                duration_sec=120
            )

    def test_custom_limits(self):
        """Test custom pass/fail limits."""
        result = WetLeakageTestResult(
            test_id=1,
            module_id=101,
            applied_voltage=1200.0,
            leakage_current_ua=60.0,
            duration_sec=180,
            max_leakage_ua=100.0,  # Custom higher limit
            min_duration_sec=150  # Custom longer duration
        )

        self.assertTrue(result.determine_pass_fail())
        self.assertTrue(result.pass_status)


class TestWetLeakageTest(unittest.TestCase):
    """Test WetLeakageTest execution class."""

    def test_initialization(self):
        """Test test initialization."""
        test = WetLeakageTest(module="PV-001", module_voc=45.6)

        self.assertEqual(test.module, "PV-001")
        self.assertEqual(test.module_voc, 45.6)
        self.assertIsNotNone(test.safety)

    def test_voltage_calculation(self):
        """Test automatic voltage calculation."""
        test = WetLeakageTest(module="PV-001", module_voc=45.6)

        # Test auto-calculation: 1000V + 1.2×Voc
        expected = 1000.0 + 1.2 * 45.6
        calculated = test.calculate_test_voltage()

        self.assertAlmostEqual(calculated, expected, places=1)

    def test_voltage_override(self):
        """Test manual voltage override."""
        test = WetLeakageTest(module="PV-001", module_voc=45.6)

        # Override with custom voltage
        override_voltage = 1500.0
        calculated = test.calculate_test_voltage(voltage=override_voltage)

        self.assertEqual(calculated, override_voltage)

    def test_measurement_execution(self):
        """Test measurement execution."""
        test = WetLeakageTest(
            module="PV-001",
            module_voc=45.6,
            test_id=1001,
            module_id=1001
        )

        result = test.measure(
            voltage=1200.0,
            operator_id="TEST-OPERATOR",
            equipment_id="TEST-EQUIPMENT"
        )

        # Verify result structure
        self.assertIsInstance(result, WetLeakageTestResult)
        self.assertEqual(result.test_id, 1001)
        self.assertEqual(result.module_id, 1001)
        self.assertEqual(result.applied_voltage, 1200.0)
        self.assertGreaterEqual(result.leakage_current_ua, 0)
        self.assertEqual(result.duration_sec, 120)  # Default duration
        self.assertEqual(result.operator_id, "TEST-OPERATOR")
        self.assertEqual(result.equipment_id, "TEST-EQUIPMENT")

        # Verify status is set
        self.assertIn(result.status, [TestStatus.PASSED, TestStatus.FAILED])

    def test_safety_checks(self):
        """Test safety interlock verification."""
        test = WetLeakageTest(module="PV-001")

        # Safety checks should pass (simulated)
        self.assertTrue(test.safety.verify_all_checks())

    def test_calibration_validation(self):
        """Test calibration validation."""
        test = WetLeakageTest(module="PV-001")

        # Recent calibration
        recent_cal = datetime.now() - timedelta(days=30)
        result = test.measure(
            voltage=1200.0,
            calibration_date=recent_cal
        )
        self.assertIsNotNone(result)

        # Expired calibration (should still run but log warning)
        expired_cal = datetime.now() - timedelta(days=400)
        result = test.measure(
            voltage=1200.0,
            calibration_date=expired_cal
        )
        self.assertIsNotNone(result)


class TestIntegration(unittest.TestCase):
    """Integration tests."""

    def test_complete_workflow(self):
        """Test complete test workflow."""
        # Initialize
        test = WetLeakageTest(
            module="PV-TEST",
            module_voc=45.6,
            test_id=9999,
            module_id=9999
        )

        # Execute with full parameters
        result = test.measure(
            duration_sec=150,
            operator_id="TECH-001",
            equipment_id="HV-001",
            calibration_date=datetime.now() - timedelta(days=100),
            ambient_temp_c=25.0,
            humidity_percent=50.0,
            water_temp_c=20.0,
            notes="Integration test"
        )

        # Verify complete result
        self.assertIsNotNone(result)
        self.assertEqual(result.test_id, 9999)
        self.assertEqual(result.operator_id, "TECH-001")
        self.assertEqual(result.equipment_id, "HV-001")
        self.assertEqual(result.ambient_temp_c, 25.0)
        self.assertEqual(result.humidity_percent, 50.0)
        self.assertEqual(result.notes, "Integration test")

        # Verify JSON export
        data = result.model_dump()
        self.assertIsInstance(data, dict)
        self.assertIn('test_id', data)
        self.assertIn('leakage_current_ua', data)
        self.assertIn('pass_status', data)


if __name__ == '__main__':
    unittest.main()
