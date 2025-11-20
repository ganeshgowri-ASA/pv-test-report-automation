"""
Dielectric Test Block (Session 25)

Implements high voltage dielectric withstand testing, insulation integrity verification,
and safety compliance according to IEC 61215-2 and IEC 61730.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from .base_test_block import (
    BaseTestBlock,
    EquipmentInterface,
    MeasurementData,
    TestBlockResult,
    TestParameter,
    TestResult
)


@dataclass
class DielectricMeasurement:
    """Single dielectric test measurement"""
    timestamp: datetime
    test_voltage: float  # V
    leakage_current: float  # A
    duration: float  # seconds
    location: str  # Test configuration
    breakdown_occurred: bool
    partial_discharge: float  # pC (pico-Coulombs)


class HipotTester(EquipmentInterface):
    """High potential (Hipot) tester equipment interface"""

    def __init__(self, equipment_id: str, config: Dict[str, Any]):
        super().__init__(equipment_id, config)
        self.test_voltage: float = 0.0
        self.is_testing: bool = False
        self.emergency_stop: bool = False

    def connect(self) -> bool:
        """Connect to Hipot tester"""
        self.logger.info(f"Connecting to Hipot tester {self.equipment_id}")
        self.connected = True
        return True

    def disconnect(self) -> bool:
        """Disconnect from Hipot tester"""
        self.logger.info(f"Disconnecting Hipot tester {self.equipment_id}")
        self.connected = False
        self.is_testing = False
        return True

    def initialize(self) -> bool:
        """Initialize Hipot tester"""
        self.logger.info("Initializing Hipot tester")
        return self.configure({
            'voltage_range': (0, 5000),  # V
            'current_limit': 50e-3,  # 50 mA trip current
            'ramp_rate': 500,  # V/s
            'frequency': 60,  # Hz (AC) or 0 for DC
            'safety_interlock': True
        })

    def configure(self, settings: Dict[str, Any]) -> bool:
        """Configure Hipot tester settings"""
        self.logger.info(f"Configuring Hipot tester: {settings}")
        self.config.update(settings)
        return True

    def measure(self, parameter: str) -> MeasurementData:
        """Measure parameter during test"""
        # Stub: Simulate measurement during test
        value_map = {
            'voltage': self.test_voltage,
            'leakage_current': max(0, np.random.normal(5e-6, 1e-6)),  # ~5 µA typical
            'partial_discharge': max(0, np.random.normal(10, 5))  # pC
        }

        value = value_map.get(parameter, 0.0)
        unit_map = {
            'voltage': 'V',
            'leakage_current': 'A',
            'partial_discharge': 'pC'
        }

        return MeasurementData(
            timestamp=datetime.now(),
            value=value,
            unit=unit_map.get(parameter, ''),
            parameter_name=parameter,
            equipment_id=self.equipment_id
        )

    def apply_voltage(
        self,
        voltage: float,
        duration: float,
        ramp_rate: Optional[float] = None
    ) -> Tuple[bool, float, bool]:
        """
        Apply test voltage and monitor for breakdown

        Args:
            voltage: Test voltage in V
            duration: Test duration in seconds
            ramp_rate: Voltage ramp rate in V/s (optional)

        Returns:
            Tuple of (success, leakage_current, breakdown_occurred)
        """
        self.logger.info(f"Applying {voltage}V for {duration}s")

        if self.emergency_stop:
            self.logger.error("Emergency stop activated!")
            return False, 0.0, False

        ramp_rate = ramp_rate or self.config.get('ramp_rate', 500)
        current_limit = self.config.get('current_limit', 50e-3)

        # Simulate voltage ramp
        ramp_time = voltage / ramp_rate
        self.logger.info(f"Ramping to {voltage}V at {ramp_rate}V/s ({ramp_time:.1f}s)")

        self.test_voltage = voltage
        self.is_testing = True

        # Simulate leakage current (good insulation: < 10 µA)
        base_leakage = voltage / 500e6  # 500 MOhm insulation
        leakage_current = base_leakage + np.random.normal(0, 1e-6)

        # Check for breakdown (very rare in good modules)
        breakdown_probability = min(0.001, max(0, (voltage - 2000) / 10000))  # Higher voltage = higher risk
        breakdown_occurred = np.random.random() < breakdown_probability

        if breakdown_occurred:
            self.logger.warning("BREAKDOWN DETECTED!")
            self.is_testing = False
            return False, leakage_current, True

        # Check current limit
        if leakage_current > current_limit:
            self.logger.warning(f"Current limit exceeded: {leakage_current*1e3:.3f} mA")
            self.is_testing = False
            return False, leakage_current, False

        # Hold voltage for duration
        # In real implementation, would continuously monitor
        # Stub: Just simulate successful hold

        self.is_testing = False
        return True, leakage_current, False

    def emergency_shutdown(self) -> bool:
        """Emergency shutdown of high voltage"""
        self.logger.warning("EMERGENCY SHUTDOWN ACTIVATED")
        self.emergency_stop = True
        self.test_voltage = 0.0
        self.is_testing = False
        return True


class DielectricTest(BaseTestBlock):
    """
    Dielectric Withstand Test Block

    Performs high voltage dielectric testing to verify insulation integrity
    and safety compliance of PV modules.
    """

    def __init__(
        self,
        test_id: str,
        operator: str,
        config: Dict[str, Any],
        hipot_tester: HipotTester
    ):
        super().__init__(
            test_id=test_id,
            operator=operator,
            config=config,
            equipment=[hipot_tester]
        )

        self.hipot_tester = hipot_tester
        self.dielectric_measurements: List[DielectricMeasurement] = []

    def _initialize_parameters(self) -> None:
        """Initialize test parameters"""
        self.parameters = {
            'test_voltage_ac': TestParameter(
                name='test_voltage_ac',
                value=1000 + 2 * 50,  # Umax + 2*Voc (for 50V module)
                unit='V',
                description='AC test voltage (IEC 61215-2 formula)'
            ),
            'test_voltage_dc': TestParameter(
                name='test_voltage_dc',
                value=1.5 * (1000 + 2 * 50),  # 1.5 * AC voltage
                unit='V',
                description='DC test voltage'
            ),
            'test_duration': TestParameter(
                name='test_duration',
                value=60,  # 1 minute
                unit='s',
                description='Voltage application duration'
            ),
            'ramp_rate': TestParameter(
                name='ramp_rate',
                value=500,
                unit='V/s',
                description='Voltage ramp rate'
            ),
            'max_leakage_current': TestParameter(
                name='max_leakage_current',
                value=50e-3,  # 50 mA
                unit='A',
                description='Maximum allowable leakage current'
            ),
            'test_configurations': TestParameter(
                name='test_configurations',
                value=['frame_to_circuits', 'frame_to_terminals'],
                unit='',
                description='Dielectric test configurations'
            ),
            'test_type': TestParameter(
                name='test_type',
                value='DC',  # 'AC' or 'DC'
                unit='',
                description='Type of dielectric test'
            )
        }

    def execute(self) -> TestBlockResult:
        """Execute dielectric withstand test"""
        self.start_time = datetime.now()
        self.logger.info(f"Starting dielectric test {self.test_id}")

        try:
            # Validate equipment
            issues = self.validate_equipment()
            if issues:
                raise RuntimeError(f"Equipment validation failed: {', '.join(issues)}")

            # Safety checks
            if not self._perform_safety_checks():
                raise RuntimeError("Safety checks failed")

            # Initialize equipment
            self.hipot_tester.initialize()

            # Collect test data
            self.measurements = self._collect_data()

            # Analyze results
            self.analysis_results = self._analyze_data()

            # Check for anomalies
            self._detect_anomalies()

        except Exception as e:
            self.logger.error(f"Error during dielectric test: {e}")
            # Ensure voltage is removed
            self.hipot_tester.emergency_shutdown()

            self.end_time = datetime.now()
            result = self.generate_result()
            result.result = TestResult.ERROR
            result.error_message = str(e)
            return result
        finally:
            self.cleanup()

        self.end_time = datetime.now()
        return self.generate_result()

    def _perform_safety_checks(self) -> bool:
        """Perform pre-test safety checks"""
        self.logger.info("Performing safety checks...")

        safety_checks = {
            'operator_trained': True,  # Verify operator certification
            'safety_equipment': True,  # Verify safety equipment present
            'grounding_verified': True,  # Verify proper grounding
            'area_secured': True,  # Verify test area secured
            'emergency_stop_functional': True  # Test emergency stop
        }

        all_pass = all(safety_checks.values())

        if not all_pass:
            failed = [k for k, v in safety_checks.items() if not v]
            self.logger.error(f"Safety checks failed: {failed}")

        return all_pass

    def _collect_data(self) -> List[MeasurementData]:
        """Collect dielectric test data"""
        self.logger.info("Collecting dielectric test data...")

        measurements = []

        # Get test parameters
        test_type = self.parameters['test_type'].value
        test_voltage = (self.parameters['test_voltage_dc'].value if test_type == 'DC'
                       else self.parameters['test_voltage_ac'].value)
        test_duration = self.parameters['test_duration'].value
        ramp_rate = self.parameters['ramp_rate'].value
        configurations = self.parameters['test_configurations'].value

        self.logger.info(f"Test type: {test_type}, Voltage: {test_voltage}V, Duration: {test_duration}s")

        # Perform test for each configuration
        for config in configurations:
            self.logger.info(f"Testing configuration: {config}")

            # Apply test voltage
            success, leakage_current, breakdown = self.hipot_tester.apply_voltage(
                voltage=test_voltage,
                duration=test_duration,
                ramp_rate=ramp_rate
            )

            # Measure partial discharge
            pd_measurement = self.hipot_tester.measure('partial_discharge')
            partial_discharge = pd_measurement.value

            # Create measurement record
            dielectric_meas = DielectricMeasurement(
                timestamp=datetime.now(),
                test_voltage=test_voltage,
                leakage_current=leakage_current,
                duration=test_duration,
                location=config,
                breakdown_occurred=breakdown,
                partial_discharge=partial_discharge
            )
            self.dielectric_measurements.append(dielectric_meas)

            # Store as measurements
            measurements.append(MeasurementData(
                timestamp=dielectric_meas.timestamp,
                value=test_voltage,
                unit='V',
                parameter_name=f'voltage_{config}',
                equipment_id=self.hipot_tester.equipment_id
            ))

            measurements.append(MeasurementData(
                timestamp=dielectric_meas.timestamp,
                value=leakage_current,
                unit='A',
                parameter_name=f'leakage_current_{config}',
                equipment_id=self.hipot_tester.equipment_id,
                metadata={
                    'test_voltage': test_voltage,
                    'breakdown': breakdown,
                    'partial_discharge_pc': partial_discharge
                }
            ))

            # Log results
            if breakdown:
                self.logger.error(
                    f"{config}: BREAKDOWN at {test_voltage}V, "
                    f"Leakage: {leakage_current*1e3:.3f} mA"
                )
            elif not success:
                self.logger.warning(
                    f"{config}: Test failed (no breakdown), "
                    f"Leakage: {leakage_current*1e3:.3f} mA"
                )
            else:
                self.logger.info(
                    f"{config}: PASS, "
                    f"Leakage: {leakage_current*1e6:.3f} µA, "
                    f"PD: {partial_discharge:.1f} pC"
                )

            # Safety: Ramp down voltage
            self.logger.info("Ramping down voltage...")

        return measurements

    def _analyze_data(self) -> Dict[str, Any]:
        """Analyze dielectric test results"""
        self.logger.info("Analyzing dielectric test data...")

        if not self.dielectric_measurements:
            return {'error': 'No measurements available'}

        # Extract leakage currents
        leakage_currents = np.array([m.leakage_current for m in self.dielectric_measurements])
        partial_discharges = np.array([m.partial_discharge for m in self.dielectric_measurements])

        # Check for breakdowns
        breakdowns = [m for m in self.dielectric_measurements if m.breakdown_occurred]
        num_breakdowns = len(breakdowns)

        # Calculate statistics
        leakage_stats = {
            'mean': float(np.mean(leakage_currents)),
            'max': float(np.max(leakage_currents)),
            'min': float(np.min(leakage_currents))
        }

        pd_stats = {
            'mean': float(np.mean(partial_discharges)),
            'max': float(np.max(partial_discharges)),
            'min': float(np.min(partial_discharges))
        }

        # Calculate insulation resistance estimate
        test_voltage = self.dielectric_measurements[0].test_voltage
        estimated_resistance = []
        for current in leakage_currents:
            if current > 0:
                resistance = test_voltage / current
                estimated_resistance.append(resistance)

        resistance_stats = {
            'mean': float(np.mean(estimated_resistance)) if estimated_resistance else 0,
            'min': float(np.min(estimated_resistance)) if estimated_resistance else 0
        }

        return {
            'test_voltage': test_voltage,
            'test_type': self.parameters['test_type'].value,
            'num_configurations': len(self.dielectric_measurements),
            'num_breakdowns': num_breakdowns,
            'breakdown_locations': [m.location for m in breakdowns],
            'leakage_current_stats': leakage_stats,
            'partial_discharge_stats': pd_stats,
            'estimated_resistance_stats': resistance_stats,
            'all_tests_passed': num_breakdowns == 0,
            'max_leakage_current_ma': leakage_stats['max'] * 1e3,
            'max_partial_discharge_pc': pd_stats['max']
        }

    def _detect_anomalies(self) -> None:
        """Detect anomalies in dielectric test"""
        if not self.dielectric_measurements:
            return

        max_leakage = self.parameters['max_leakage_current'].value

        for measurement in self.dielectric_measurements:
            # Check for breakdown
            if measurement.breakdown_occurred:
                self.log_anomaly(
                    f"CRITICAL: Dielectric breakdown at {measurement.location} "
                    f"at {measurement.test_voltage}V"
                )

            # Check leakage current
            if measurement.leakage_current > max_leakage:
                self.log_anomaly(
                    f"High leakage current at {measurement.location}: "
                    f"{measurement.leakage_current*1e3:.3f} mA "
                    f"(max: {max_leakage*1e3:.1f} mA)"
                )

            # Check partial discharge
            if measurement.partial_discharge > 100:  # > 100 pC is concerning
                self.log_anomaly(
                    f"High partial discharge at {measurement.location}: "
                    f"{measurement.partial_discharge:.1f} pC"
                )

        # Check for consistency between configurations
        leakage_currents = [m.leakage_current for m in self.dielectric_measurements]
        if len(leakage_currents) > 1:
            max_current = max(leakage_currents)
            min_current = min(leakage_currents)

            if max_current > 0 and (max_current / min_current) > 10:  # 10x difference
                self.log_anomaly(
                    f"Large variation in leakage current between configurations: "
                    f"{min_current*1e6:.1f} to {max_current*1e6:.1f} µA"
                )

    def _determine_pass_fail(self) -> Tuple[TestResult, Dict[str, bool]]:
        """Determine pass/fail status"""
        criteria = {}

        if not self.dielectric_measurements:
            return TestResult.ERROR, criteria

        max_leakage = self.parameters['max_leakage_current'].value

        # Check each configuration
        for measurement in self.dielectric_measurements:
            config_name = f"breakdown_{measurement.location}"
            criteria[config_name] = not measurement.breakdown_occurred

            leakage_name = f"leakage_{measurement.location}"
            criteria[leakage_name] = measurement.leakage_current <= max_leakage

        # Overall criteria
        criteria['no_breakdowns'] = self.analysis_results.get('num_breakdowns', 1) == 0
        criteria['leakage_acceptable'] = self.analysis_results.get('max_leakage_current_ma', 999) <= max_leakage * 1e3

        # Partial discharge criterion (informational)
        criteria['partial_discharge_low'] = self.analysis_results.get('max_partial_discharge_pc', 999) < 100

        # Overall result
        all_pass = all(criteria.values())
        critical_pass = criteria.get('no_breakdowns', False) and criteria.get('leakage_acceptable', False)

        if all_pass:
            return TestResult.PASS, criteria
        elif critical_pass:
            return TestResult.CONDITIONAL_PASS, criteria
        else:
            return TestResult.FAIL, criteria

    def cleanup(self) -> None:
        """Cleanup and ensure safety"""
        # Ensure voltage is removed
        if self.hipot_tester.is_testing:
            self.logger.warning("Test still active during cleanup - emergency shutdown")
            self.hipot_tester.emergency_shutdown()

        super().cleanup()
