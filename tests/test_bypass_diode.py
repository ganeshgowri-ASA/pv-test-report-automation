"""
Unit tests for Bypass Diode Test Block
"""

import unittest
from datetime import datetime
from test_blocks.bypass_diode import BypassDiodeTest, BypassDiodeResult, DiodeCharacteristics
from test_blocks.base import TestStatus, Standard


class TestBypassDiodeTest(unittest.TestCase):
    """Test cases for BypassDiodeTest class"""

    def setUp(self):
        """Set up test fixtures"""
        self.test = BypassDiodeTest(
            module="TEST-MODULE-001",
            test_id=9999,
            diode_count=3,
            operator="Test Operator"
        )

    def test_initialization(self):
        """Test proper initialization"""
        self.assertEqual(self.test.module_id, "TEST-MODULE-001")
        self.assertEqual(self.test.test_id, 9999)
        self.assertEqual(self.test.diode_count, 3)
        self.assertIn(Standard.IEC_61215, self.test.metadata.standards)
        self.assertIn(Standard.ISO_17025, self.test.metadata.standards)

    def test_forward_vi_curve(self):
        """Test forward V-I curve measurement"""
        vi_data = self.test.measure_forward_vi_curve(diode_index=0)

        # Check that all test currents have voltage measurements
        self.assertEqual(len(vi_data), len(self.test.forward_test_currents))

        # Check voltage values are reasonable
        for current, voltage in vi_data.items():
            self.assertGreater(voltage, 0)
            self.assertLess(voltage, 2.0)  # Should be < 2V for good diode
            # Voltage should increase with current
            if current > 1.0:
                self.assertGreater(voltage, 0.4)

    def test_reverse_leakage(self):
        """Test reverse leakage current measurement"""
        leakage = self.test.measure_reverse_leakage(diode_index=0)

        # Check leakage is positive and reasonable
        self.assertGreater(leakage, 0)
        self.assertLess(leakage, 1000.0)  # Should be < 1000µA for any functional diode

    def test_thermal_performance(self):
        """Test thermal performance measurement"""
        temperature = self.test.measure_thermal_performance(diode_index=0)

        # Check temperature is reasonable
        self.assertGreater(temperature, 20.0)  # Above room temp under load
        self.assertLess(temperature, 150.0)  # Below damage threshold

    def test_shading_activation(self):
        """Test shading activation"""
        activated, voltage, response_time = self.test.test_shading_activation(diode_index=0)

        # Check activation parameters
        self.assertIsInstance(activated, bool)
        self.assertGreater(voltage, 0)
        self.assertLess(voltage, 1.5)
        self.assertGreater(response_time, 0)
        self.assertLess(response_time, 1000.0)  # Should be < 1 second

    def test_single_diode(self):
        """Test complete single diode test"""
        result = self.test.test_single_diode(diode_index=0)

        # Check DiodeCharacteristics object
        self.assertIsInstance(result, DiodeCharacteristics)
        self.assertEqual(result.diode_index, 0)
        self.assertGreater(len(result.forward_voltage_at_currents), 0)
        self.assertGreater(result.reverse_leakage_current_ua, 0)
        self.assertGreater(result.thermal_temperature_c, 0)
        self.assertIsInstance(result.activation_verified, bool)

    def test_all_diodes(self):
        """Test complete test sequence for all diodes"""
        result = self.test.test_all_diodes()

        # Check BypassDiodeResult object
        self.assertIsInstance(result, BypassDiodeResult)
        self.assertEqual(result.module_id, "TEST-MODULE-001")
        self.assertEqual(result.test_id, 9999)
        self.assertEqual(result.diode_count, 3)

        # Check that we have results for all diodes
        self.assertEqual(len(result.forward_voltage), 3)
        self.assertEqual(len(result.reverse_leakage_ua), 3)
        self.assertEqual(len(result.diode_characteristics), 3)

        # Check pass status
        self.assertIsInstance(result.pass_status, bool)
        self.assertIsInstance(result.activation_verified, bool)

        # Check test duration
        self.assertGreater(result.test_duration_seconds, 0)

    def test_environmental_conditions(self):
        """Test setting environmental conditions"""
        self.test.set_environmental_conditions(
            temperature=25.0,
            humidity=50.0,
            pressure=1013.25
        )

        env = self.test.metadata.environmental_conditions
        self.assertEqual(env['temperature_c'], 25.0)
        self.assertEqual(env['humidity_percent'], 50.0)
        self.assertEqual(env['pressure_hpa'], 1013.25)

    def test_equipment_info(self):
        """Test setting equipment information"""
        cal_date = datetime(2025, 1, 1)
        self.test.set_equipment(
            equipment_id="TEST-EQUIP-001",
            calibration_date=cal_date
        )

        self.assertEqual(self.test.metadata.equipment_id, "TEST-EQUIP-001")
        self.assertEqual(self.test.metadata.calibration_date, cal_date)

    def test_json_export(self):
        """Test JSON export functionality"""
        result = self.test.test_all_diodes()
        json_output = self.test.export_results(result, format='json')

        # Check that JSON is valid
        import json
        data = json.loads(json_output)

        self.assertEqual(data['module_id'], "TEST-MODULE-001")
        self.assertEqual(data['diode_count'], 3)
        self.assertIn('forward_voltage', data)
        self.assertIn('reverse_leakage_ua', data)

    def test_csv_export(self):
        """Test CSV export functionality"""
        result = self.test.test_all_diodes()
        csv_output = self.test.export_results(result, format='csv')

        # Check CSV has header and data rows
        lines = csv_output.strip().split('\n')
        self.assertGreater(len(lines), 1)  # Header + at least 1 data row
        self.assertIn('Diode', lines[0])  # Check header
        self.assertEqual(len(lines), 4)  # Header + 3 diodes

    def test_result_to_dict(self):
        """Test result serialization to dictionary"""
        result = self.test.test_all_diodes()
        data = result.to_dict()

        # Check dictionary structure
        self.assertIsInstance(data, dict)
        self.assertIn('test_id', data)
        self.assertIn('module_id', data)
        self.assertIn('diode_count', data)
        self.assertIn('pass_status', data)
        self.assertIn('diode_summary', data)

        # Check diode summary
        self.assertEqual(len(data['diode_summary']), 3)


class TestDiodeCharacteristics(unittest.TestCase):
    """Test cases for DiodeCharacteristics dataclass"""

    def test_overall_pass(self):
        """Test overall pass logic"""
        # All pass
        char_pass = DiodeCharacteristics(
            diode_index=0,
            forward_voltage_at_currents={8.0: 0.8},
            reverse_leakage_current_ua=10.0,
            thermal_temperature_c=60.0,
            activation_voltage=0.65,
            activation_verified=True,
            pass_forward_vf=True,
            pass_reverse_leakage=True,
            pass_thermal=True,
            pass_activation=True
        )
        self.assertTrue(char_pass.overall_pass)

        # One failure
        char_fail = DiodeCharacteristics(
            diode_index=0,
            forward_voltage_at_currents={8.0: 1.5},
            reverse_leakage_current_ua=10.0,
            thermal_temperature_c=60.0,
            activation_voltage=0.65,
            activation_verified=True,
            pass_forward_vf=False,  # Failed
            pass_reverse_leakage=True,
            pass_thermal=True,
            pass_activation=True
        )
        self.assertFalse(char_fail.overall_pass)


if __name__ == '__main__':
    unittest.main()
