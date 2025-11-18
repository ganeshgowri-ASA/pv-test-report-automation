"""
IEC 62804 PID Testing Protocol - Unit Tests

Comprehensive unit tests for all IEC 62804 modules.
"""

import unittest
from datetime import datetime, timedelta
import time

from .models import (
    TestMethod, TestStatus, TestResult, ModuleType,
    IEC62804TestCreate
)
from .chamber_control import (
    SimulatedChamberController, ChamberSetpoint, ChamberMonitor
)
from .voltage_control import (
    SimulatedVoltageSupply, VoltageSupplyConfig, VoltageMonitor,
    InterlockType
)
from .flash_tester import (
    SimulatedFlashTester, FlashTestScheduler, correct_to_stc
)
from .leakage_monitor import LeakageCurrentMonitor
from .degradation_analyzer import (
    DegradationAnalyzer, DegradationLevel, DegradationComparator
)
from .recovery_test import (
    PIDRecoveryTest, RecoveryMethod, RecoveryClassification
)
from .report_generator import IEC62804ReportGenerator


class TestChamberControl(unittest.TestCase):
    """Test chamber control functionality"""

    def setUp(self):
        """Set up test chamber"""
        self.chamber = SimulatedChamberController("TEST-CHAMBER-01")

    def test_connection(self):
        """Test chamber connection"""
        self.assertTrue(self.chamber.connect())
        self.assertTrue(self.chamber.is_connected())
        self.assertTrue(self.chamber.disconnect())
        self.assertFalse(self.chamber.is_connected())

    def test_temperature_setpoint(self):
        """Test temperature setpoint"""
        self.chamber.connect()
        self.assertTrue(self.chamber.set_temperature(60.0))

        # Test invalid temperature
        self.assertFalse(self.chamber.set_temperature(200.0))

    def test_humidity_setpoint(self):
        """Test humidity setpoint"""
        self.chamber.connect()
        self.assertTrue(self.chamber.set_humidity(85.0))

        # Test invalid humidity
        self.assertFalse(self.chamber.set_humidity(150.0))

    def test_chamber_operation(self):
        """Test chamber start/stop"""
        self.chamber.connect()
        self.assertTrue(self.chamber.start())
        self.assertTrue(self.chamber.stop())

    def test_reading(self):
        """Test chamber reading"""
        self.chamber.connect()
        reading = self.chamber.get_reading()

        self.assertIsNotNone(reading.timestamp)
        self.assertGreater(reading.temperature, 0)
        self.assertGreater(reading.humidity, 0)

    def test_setpoint_reach(self):
        """Test reaching setpoint"""
        self.chamber.connect()

        setpoint = ChamberSetpoint(temperature=60.0, humidity=85.0)
        self.chamber.set_setpoint(setpoint)
        self.chamber.start()

        # Simulate reaching setpoint
        for _ in range(20):
            reading = self.chamber.get_reading()
            if self.chamber.is_at_setpoint(reading):
                break
            time.sleep(0.1)

        self.assertTrue(self.chamber.is_at_setpoint())


class TestVoltageControl(unittest.TestCase):
    """Test voltage supply control"""

    def setUp(self):
        """Set up test voltage supply"""
        config = VoltageSupplyConfig(max_voltage=1500.0, max_current=0.1)
        self.supply = SimulatedVoltageSupply("TEST-SUPPLY-01", config=config)

    def test_connection(self):
        """Test supply connection"""
        self.assertTrue(self.supply.connect())
        self.assertTrue(self.supply.is_connected())

    def test_voltage_setpoint(self):
        """Test voltage setpoint"""
        self.supply.connect()
        self.assertTrue(self.supply.set_voltage(-1000.0))

        # Test voltage exceeding limits
        self.assertFalse(self.supply.set_voltage(-2000.0))

    def test_current_limit(self):
        """Test current limit"""
        self.supply.connect()
        self.assertTrue(self.supply.set_current_limit(0.05))

        # Test current exceeding limits
        self.assertFalse(self.supply.set_current_limit(0.5))

    def test_output_enable(self):
        """Test output enable/disable"""
        self.supply.connect()
        self.assertTrue(self.supply.enable_output())

        reading = self.supply.get_reading()
        self.assertTrue(reading.output_enabled)

        self.assertTrue(self.supply.disable_output())
        reading = self.supply.get_reading()
        self.assertFalse(reading.output_enabled)

    def test_interlock(self):
        """Test safety interlock"""
        self.supply.connect()

        # Set interlock open
        self.supply.set_interlock(InterlockType.DOOR, False)

        # Should not be able to enable output
        self.assertFalse(self.supply.enable_output())

        # Close interlock
        self.supply.set_interlock(InterlockType.DOOR, True)
        self.assertTrue(self.supply.enable_output())

    def test_emergency_stop(self):
        """Test emergency stop"""
        self.supply.connect()
        self.supply.enable_output()

        # Trigger emergency stop
        self.supply.emergency_stop()

        reading = self.supply.get_reading()
        self.assertFalse(reading.output_enabled)

    def test_voltage_ramp(self):
        """Test voltage ramping"""
        self.supply.connect()

        # Ramp to -1000V
        self.supply.set_voltage(-1000.0)
        self.supply.enable_output()

        # Simulate ramping
        for _ in range(15):
            reading = self.supply.get_reading()
            if abs(reading.voltage - (-1000.0)) < 5.0:
                break
            time.sleep(0.1)

        reading = self.supply.get_reading()
        self.assertAlmostEqual(reading.voltage, -1000.0, delta=10.0)


class TestFlashTester(unittest.TestCase):
    """Test flash tester / I-V tracer"""

    def setUp(self):
        """Set up test flash tester"""
        self.tester = SimulatedFlashTester(
            "TEST-TESTER-01",
            nominal_pmax=300.0,
            nominal_voc=40.0,
            nominal_isc=9.0
        )

    def test_connection(self):
        """Test tester connection"""
        self.assertTrue(self.tester.connect())
        self.assertTrue(self.tester.is_connected())

    def test_iv_curve_measurement(self):
        """Test I-V curve measurement"""
        self.tester.connect()

        iv_data = self.tester.measure_iv_curve()

        self.assertIsNotNone(iv_data)
        self.assertGreater(iv_data.pmax, 0)
        self.assertGreater(iv_data.voc, 0)
        self.assertGreater(iv_data.isc, 0)
        self.assertGreater(iv_data.ff, 0)
        self.assertGreater(len(iv_data.points), 0)

    def test_degradation_simulation(self):
        """Test degradation simulation"""
        self.tester.connect()

        # Measure initial
        iv_initial = self.tester.measure_iv_curve()
        initial_pmax = iv_initial.pmax

        # Set degradation
        self.tester.set_degradation(10.0)  # 10% degradation

        # Measure degraded
        iv_degraded = self.tester.measure_iv_curve()
        degraded_pmax = iv_degraded.pmax

        # Check degradation
        actual_deg = ((initial_pmax - degraded_pmax) / initial_pmax) * 100
        self.assertAlmostEqual(actual_deg, 10.0, delta=1.0)

    def test_stc_correction(self):
        """Test STC correction"""
        measured_pmax = 285.0  # W
        measured_irradiance = 950.0  # W/m²
        measured_temp = 30.0  # °C

        corrected = correct_to_stc(measured_pmax, measured_irradiance, measured_temp)

        # Should be higher than measured (correcting from 950 to 1000 W/m²)
        self.assertGreater(corrected, measured_pmax)


class TestLeakageMonitor(unittest.TestCase):
    """Test leakage current monitoring"""

    def setUp(self):
        """Set up test components"""
        self.supply = SimulatedVoltageSupply("TEST-SUPPLY-01")
        self.supply.connect()

        self.monitor = LeakageCurrentMonitor(
            voltage_supply=self.supply,
            threshold_ma=50.0,
            critical_threshold_ma=100.0,
            sample_interval=0.1  # Fast for testing
        )

    def test_monitoring_start_stop(self):
        """Test monitoring start/stop"""
        self.monitor.start_monitoring()
        self.assertTrue(self.monitor.is_monitoring())

        time.sleep(0.5)  # Let it collect some samples

        self.monitor.stop_monitoring()
        self.assertFalse(self.monitor.is_monitoring())

    def test_current_reading(self):
        """Test current reading"""
        self.monitor.start_monitoring()
        time.sleep(0.3)  # Let it collect samples

        reading = self.monitor.get_current_reading()
        self.assertIsNotNone(reading)
        self.assertGreaterEqual(reading.current_ma, 0)

        self.monitor.stop_monitoring()

    def test_statistics(self):
        """Test statistics calculation"""
        self.monitor.start_monitoring()
        time.sleep(0.5)  # Collect samples

        stats = self.monitor.get_statistics()
        self.assertIsNotNone(stats)
        self.assertGreater(stats.num_readings, 0)
        self.assertGreaterEqual(stats.mean_current_ma, 0)

        self.monitor.stop_monitoring()


class TestDegradationAnalyzer(unittest.TestCase):
    """Test degradation analysis"""

    def setUp(self):
        """Set up analyzer"""
        self.initial_pmax = 300.0  # W
        self.analyzer = DegradationAnalyzer(self.initial_pmax)

    def test_degradation_calculation(self):
        """Test degradation calculation"""
        degraded_pmax = 270.0  # 10% degradation

        degradation = self.analyzer.calculate_degradation(degraded_pmax)
        self.assertAlmostEqual(degradation, 10.0, delta=0.1)

    def test_add_measurement(self):
        """Test adding measurements"""
        self.analyzer.add_measurement(
            timestamp=datetime.utcnow(),
            elapsed_hours=0.0,
            pmax=300.0,
            voc=40.0,
            isc=9.0,
            ff=0.83
        )

        self.analyzer.add_measurement(
            timestamp=datetime.utcnow(),
            elapsed_hours=24.0,
            pmax=285.0,
            voc=39.5,
            isc=8.9,
            ff=0.82
        )

        degradation = self.analyzer.get_current_degradation()
        self.assertGreater(degradation, 0)

    def test_degradation_rate(self):
        """Test degradation rate calculation"""
        # Add measurements
        start_time = datetime.utcnow()

        for hours in [0, 24, 48]:
            pmax = 300.0 - (hours * 0.5)  # 0.5W/hour degradation
            self.analyzer.add_measurement(
                timestamp=start_time + timedelta(hours=hours),
                elapsed_hours=float(hours),
                pmax=pmax,
                voc=40.0,
                isc=9.0,
                ff=0.83
            )

        rate = self.analyzer.calculate_degradation_rate()
        # Rate should be approximately 0.167 %/hour (0.5W / 300W * 100)
        self.assertGreater(rate, 0)

    def test_classification(self):
        """Test degradation classification"""
        self.assertEqual(
            self.analyzer.classify_degradation(0.5),
            DegradationLevel.NONE
        )
        self.assertEqual(
            self.analyzer.classify_degradation(2.0),
            DegradationLevel.MINIMAL
        )
        self.assertEqual(
            self.analyzer.classify_degradation(4.0),
            DegradationLevel.MODERATE
        )
        self.assertEqual(
            self.analyzer.classify_degradation(7.0),
            DegradationLevel.SIGNIFICANT
        )
        self.assertEqual(
            self.analyzer.classify_degradation(15.0),
            DegradationLevel.SEVERE
        )

    def test_test_result_determination(self):
        """Test pass/fail determination"""
        # Test must run 96 hours
        self.assertEqual(
            self.analyzer.determine_test_result(3.0, 50.0),
            TestResult.PENDING
        )

        # Pass result
        self.assertEqual(
            self.analyzer.determine_test_result(3.0, 96.0),
            TestResult.PASS
        )

        # Marginal result
        self.assertEqual(
            self.analyzer.determine_test_result(7.0, 96.0),
            TestResult.MARGINAL
        )

        # Fail result
        self.assertEqual(
            self.analyzer.determine_test_result(15.0, 96.0),
            TestResult.FAIL
        )


class TestRecoveryTest(unittest.TestCase):
    """Test PID recovery testing"""

    def setUp(self):
        """Set up recovery test"""
        self.tester = SimulatedFlashTester("TEST-TESTER-01", nominal_pmax=300.0)
        self.tester.connect()

        self.recovery = PIDRecoveryTest(
            flash_tester=self.tester,
            initial_pmax=300.0,
            degraded_pmax=270.0,
            recovery_method=RecoveryMethod.PASSIVE
        )

    def test_recovery_start(self):
        """Test recovery start"""
        self.recovery.start_recovery()
        self.assertIsNotNone(self.recovery._start_time)

    def test_add_measurement(self):
        """Test adding recovery measurements"""
        self.recovery.start_recovery()

        # Add measurements
        self.recovery.add_measurement(270.0)  # 0% recovery
        self.recovery.add_measurement(285.0)  # 50% recovery
        self.recovery.add_measurement(295.0)  # ~83% recovery

        current_recovery = self.recovery.get_current_recovery()
        self.assertGreater(current_recovery, 0)

    def test_recovery_classification(self):
        """Test recovery classification"""
        self.assertEqual(
            self.recovery.classify_recovery(85.0),
            RecoveryClassification.REVERSIBLE
        )
        self.assertEqual(
            self.recovery.classify_recovery(50.0),
            RecoveryClassification.PARTIALLY_REVERSIBLE
        )
        self.assertEqual(
            self.recovery.classify_recovery(10.0),
            RecoveryClassification.IRREVERSIBLE
        )


class TestReportGenerator(unittest.TestCase):
    """Test report generation"""

    def setUp(self):
        """Set up test data"""
        self.test_data = {
            "test_id": 1,
            "test_date": datetime.utcnow(),
            "test_method": "B",
            "operator": "Test Operator",
            "status": "completed",
            "module_serial": "TEST-MODULE-001",
            "manufacturer": "Test Manufacturer",
            "model": "Test Model",
            "module_type": "monofacial",
            "voltage": -1000.0,
            "duration_hours": 96,
            "temperature": 60.0,
            "humidity": 85.0,
            "start_time": datetime.utcnow(),
            "end_time": datetime.utcnow() + timedelta(hours=96),
            "initial_pmax": 300.0,
            "final_pmax": 285.0,
            "degradation_pct": 5.0,
            "degradation_rate": 0.052,
            "result": "pass",
            "flash_results": [
                {
                    "elapsed_hours": 0.0,
                    "pmax": 300.0,
                    "voc": 40.0,
                    "isc": 9.0,
                    "ff": 0.83,
                    "degradation_pct": 0.0
                },
                {
                    "elapsed_hours": 96.0,
                    "pmax": 285.0,
                    "voc": 39.5,
                    "isc": 8.9,
                    "ff": 0.82,
                    "degradation_pct": 5.0
                }
            ]
        }

    def test_text_report_generation(self):
        """Test text report generation"""
        generator = IEC62804ReportGenerator(self.test_data)
        report = generator.generate_text_report()

        self.assertIsInstance(report, str)
        self.assertIn("IEC 62804", report)
        self.assertIn("TEST-MODULE-001", report)
        self.assertIn("PASS", report)

    def test_html_report_generation(self):
        """Test HTML report generation"""
        generator = IEC62804ReportGenerator(self.test_data)
        report = generator.generate_html_report()

        self.assertIsInstance(report, str)
        self.assertIn("<html>", report)
        self.assertIn("IEC 62804", report)
        self.assertIn("TEST-MODULE-001", report)

    def test_json_report_generation(self):
        """Test JSON report generation"""
        generator = IEC62804ReportGenerator(self.test_data)
        report = generator.generate_json_report()

        self.assertIsInstance(report, str)
        self.assertIn("TEST-MODULE-001", report)


class TestModels(unittest.TestCase):
    """Test Pydantic models"""

    def test_test_create_validation(self):
        """Test IEC62804TestCreate validation"""
        # Valid test
        test = IEC62804TestCreate(
            module_serial="TEST-001",
            test_method=TestMethod.METHOD_B,
            temperature=60.0,
            humidity=85.0,
            voltage=-1000.0
        )

        self.assertEqual(test.module_serial, "TEST-001")
        self.assertEqual(test.test_method, TestMethod.METHOD_B)

    def test_humidity_validation(self):
        """Test humidity validation for Method B"""
        # Method B requires humidity
        with self.assertRaises(ValueError):
            IEC62804TestCreate(
                module_serial="TEST-001",
                test_method=TestMethod.METHOD_B,
                temperature=60.0,
                humidity=None  # Should fail
            )

    def test_temperature_validation(self):
        """Test temperature validation"""
        # Method B temperature should be 60°C ± 5°C
        with self.assertRaises(ValueError):
            IEC62804TestCreate(
                module_serial="TEST-001",
                test_method=TestMethod.METHOD_B,
                temperature=85.0,  # Too high for Method B
                humidity=85.0
            )


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests()
