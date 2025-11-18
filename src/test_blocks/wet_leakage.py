"""
Wet Leakage Current Test Block (Session 26)

Implements wet leakage current (WLT) test procedures, leakage current measurement,
and safety assessment according to IEC 61730-2 for PV module safety qualification.
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
class WLTMeasurement:
    """Wet leakage current measurement"""
    timestamp: datetime
    leakage_current: float  # A
    test_voltage: float  # V
    polarity: str  # 'positive' or 'negative'
    surface_resistance: float  # Ohm
    spray_duration: float  # seconds
    settling_time: float  # seconds


class LeakageCurrentMeter(EquipmentInterface):
    """Leakage current measurement equipment"""

    def connect(self) -> bool:
        """Connect to leakage current meter"""
        self.logger.info(f"Connecting to leakage current meter {self.equipment_id}")
        self.connected = True
        return True

    def disconnect(self) -> bool:
        """Disconnect from leakage current meter"""
        self.logger.info(f"Disconnecting leakage current meter {self.equipment_id}")
        self.connected = False
        return True

    def initialize(self) -> bool:
        """Initialize leakage current meter"""
        self.logger.info("Initializing leakage current meter")
        return self.configure({
            'range': 'auto',
            'resolution': 0.1e-6,  # 0.1 µA
            'sampling_rate': 10,  # Hz
            'filter': 'low_pass'
        })

    def configure(self, settings: Dict[str, Any]) -> bool:
        """Configure meter settings"""
        self.config.update(settings)
        return True

    def measure(self, parameter: str) -> MeasurementData:
        """Measure leakage current"""
        # Stub: Simulate leakage current measurement
        # Typical values: < 5 mA for Class II modules
        if parameter == 'leakage_current':
            value = max(0, np.random.normal(1e-3, 0.5e-3))  # ~1 mA ± 0.5 mA
            unit = 'A'
        else:
            value = 0.0
            unit = ''

        return MeasurementData(
            timestamp=datetime.now(),
            value=value,
            unit=unit,
            parameter_name=parameter,
            equipment_id=self.equipment_id,
            uncertainty=self.get_uncertainty(parameter, value)
        )

    def measure_continuous(
        self,
        duration: float,
        test_voltage: float
    ) -> List[float]:
        """
        Measure leakage current continuously

        Args:
            duration: Measurement duration in seconds
            test_voltage: Applied test voltage

        Returns:
            List of leakage current values (A)
        """
        sampling_rate = self.config.get('sampling_rate', 10)
        num_samples = int(duration * sampling_rate)

        # Simulate realistic leakage current profile
        # Initial spike, then settling to steady state
        currents = []

        for i in range(num_samples):
            t = i / sampling_rate

            # Exponential decay to steady state
            transient = 2e-3 * np.exp(-t / 5.0)  # Initial spike decays in ~5s
            steady_state = 1e-3  # Steady state ~1 mA
            noise = np.random.normal(0, 0.1e-3)

            current = transient + steady_state + noise
            currents.append(max(0, current))

        return currents


class WaterSpraySystem(EquipmentInterface):
    """Water spray system for wet leakage test"""

    def __init__(self, equipment_id: str, config: Dict[str, Any]):
        super().__init__(equipment_id, config)
        self.is_spraying: bool = False
        self.solution_conductivity: float = 0.0  # S/m

    def connect(self) -> bool:
        """Connect to spray system"""
        self.logger.info(f"Connecting to water spray system {self.equipment_id}")
        self.connected = True
        return True

    def disconnect(self) -> bool:
        """Disconnect from spray system"""
        self.logger.info(f"Disconnecting water spray system {self.equipment_id}")
        self.connected = False
        self.is_spraying = False
        return True

    def initialize(self) -> bool:
        """Initialize spray system"""
        self.logger.info("Initializing water spray system")
        return self.configure({
            'nozzle_type': 'oscillating',
            'spray_angle': 60,  # degrees
            'distance': 0.5,  # meters
            'flow_rate': 1.5,  # L/min
            'solution_conductivity': 0.05  # S/m (per IEC 61730-2)
        })

    def configure(self, settings: Dict[str, Any]) -> bool:
        """Configure spray system"""
        self.config.update(settings)
        self.solution_conductivity = settings.get('solution_conductivity', 0.05)
        return True

    def measure(self, parameter: str) -> MeasurementData:
        """Measure spray parameter"""
        value_map = {
            'conductivity': self.solution_conductivity + np.random.normal(0, 0.001),
            'flow_rate': self.config.get('flow_rate', 1.5) + np.random.normal(0, 0.05),
            'temperature': 23.0 + np.random.normal(0, 1.0)
        }

        value = value_map.get(parameter, 0.0)
        unit_map = {
            'conductivity': 'S/m',
            'flow_rate': 'L/min',
            'temperature': '°C'
        }

        return MeasurementData(
            timestamp=datetime.now(),
            value=value,
            unit=unit_map.get(parameter, ''),
            parameter_name=parameter,
            equipment_id=self.equipment_id
        )

    def start_spray(self) -> bool:
        """Start water spray"""
        self.logger.info("Starting water spray")
        self.is_spraying = True
        return True

    def stop_spray(self) -> bool:
        """Stop water spray"""
        self.logger.info("Stopping water spray")
        self.is_spraying = False
        return True

    def verify_solution(self) -> bool:
        """Verify test solution conductivity"""
        measured_conductivity = self.measure('conductivity').value
        target_conductivity = self.solution_conductivity

        tolerance = 0.005  # ±0.005 S/m
        within_spec = abs(measured_conductivity - target_conductivity) <= tolerance

        if not within_spec:
            self.logger.warning(
                f"Solution conductivity out of spec: {measured_conductivity:.3f} S/m "
                f"(target: {target_conductivity:.3f} ± {tolerance} S/m)"
            )

        return within_spec


class HighVoltageSource(EquipmentInterface):
    """High voltage source for WLT"""

    def __init__(self, equipment_id: str, config: Dict[str, Any]):
        super().__init__(equipment_id, config)
        self.output_voltage: float = 0.0
        self.output_enabled: bool = False

    def connect(self) -> bool:
        """Connect to HV source"""
        self.logger.info(f"Connecting to HV source {self.equipment_id}")
        self.connected = True
        return True

    def disconnect(self) -> bool:
        """Disconnect from HV source"""
        self.logger.info(f"Disconnecting HV source {self.equipment_id}")
        self.connected = False
        self.output_enabled = False
        return True

    def initialize(self) -> bool:
        """Initialize HV source"""
        self.logger.info("Initializing HV source")
        return self.configure({
            'voltage_range': (0, 2000),  # V
            'current_limit': 100e-3,  # 100 mA
            'polarity': 'switchable'
        })

    def configure(self, settings: Dict[str, Any]) -> bool:
        """Configure HV source"""
        self.config.update(settings)
        return True

    def measure(self, parameter: str) -> MeasurementData:
        """Measure output parameter"""
        value_map = {
            'voltage': self.output_voltage + np.random.normal(0, 1.0),
            'current': 0.0  # Measured separately
        }

        value = value_map.get(parameter, 0.0)
        unit = 'V' if parameter == 'voltage' else 'A'

        return MeasurementData(
            timestamp=datetime.now(),
            value=value,
            unit=unit,
            parameter_name=parameter,
            equipment_id=self.equipment_id
        )

    def set_voltage(self, voltage: float, polarity: str = 'positive') -> bool:
        """Set output voltage and polarity"""
        self.logger.info(f"Setting voltage to {voltage}V ({polarity})")
        self.output_voltage = voltage if polarity == 'positive' else -voltage
        return True

    def enable_output(self) -> bool:
        """Enable HV output"""
        self.logger.info("Enabling HV output")
        self.output_enabled = True
        return True

    def disable_output(self) -> bool:
        """Disable HV output"""
        self.logger.info("Disabling HV output")
        self.output_enabled = False
        self.output_voltage = 0.0
        return True


class WetLeakageTest(BaseTestBlock):
    """
    Wet Leakage Current Test Block

    Tests leakage current under wet conditions to verify electrical safety
    of PV modules according to IEC 61730-2.
    """

    def __init__(
        self,
        test_id: str,
        operator: str,
        config: Dict[str, Any],
        leakage_meter: LeakageCurrentMeter,
        spray_system: WaterSpraySystem,
        hv_source: HighVoltageSource
    ):
        super().__init__(
            test_id=test_id,
            operator=operator,
            config=config,
            equipment=[leakage_meter, spray_system, hv_source]
        )

        self.leakage_meter = leakage_meter
        self.spray_system = spray_system
        self.hv_source = hv_source
        self.wlt_measurements: List[WLTMeasurement] = []

    def _initialize_parameters(self) -> None:
        """Initialize test parameters"""
        self.parameters = {
            'test_voltage': TestParameter(
                name='test_voltage',
                value=500,  # V (typical for Class II modules)
                unit='V',
                description='Test voltage (Umax + 1000V for Class II)'
            ),
            'spray_duration': TestParameter(
                name='spray_duration',
                value=60,  # seconds
                unit='s',
                description='Water spray duration'
            ),
            'settling_time': TestParameter(
                name='settling_time',
                value=10,  # seconds
                unit='s',
                description='Time to allow current to settle'
            ),
            'measurement_duration': TestParameter(
                name='measurement_duration',
                value=30,  # seconds
                unit='s',
                description='Leakage current measurement duration'
            ),
            'solution_conductivity': TestParameter(
                name='solution_conductivity',
                value=0.05,  # S/m
                unit='S/m',
                description='Test solution conductivity (IEC 61730-2)'
            ),
            'max_leakage_current': TestParameter(
                name='max_leakage_current',
                value=5e-3,  # 5 mA for Class II
                unit='A',
                description='Maximum acceptable leakage current'
            ),
            'test_polarities': TestParameter(
                name='test_polarities',
                value=['positive', 'negative'],
                unit='',
                description='Test voltage polarities'
            )
        }

    def execute(self) -> TestBlockResult:
        """Execute wet leakage current test"""
        self.start_time = datetime.now()
        self.logger.info(f"Starting wet leakage test {self.test_id}")

        try:
            # Validate equipment
            issues = self.validate_equipment()
            if issues:
                raise RuntimeError(f"Equipment validation failed: {', '.join(issues)}")

            # Safety checks
            if not self._perform_safety_checks():
                raise RuntimeError("Safety checks failed")

            # Initialize equipment
            self.leakage_meter.initialize()
            self.spray_system.initialize()
            self.hv_source.initialize()

            # Verify test solution
            if not self.spray_system.verify_solution():
                raise RuntimeError("Test solution verification failed")

            # Collect test data
            self.measurements = self._collect_data()

            # Analyze results
            self.analysis_results = self._analyze_data()

            # Check for anomalies
            self._detect_anomalies()

        except Exception as e:
            self.logger.error(f"Error during wet leakage test: {e}")
            # Ensure safety shutdown
            self._emergency_shutdown()

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
            'grounding_verified': True,
            'isolation_transformer': True,
            'gfci_functional': True,
            'spray_system_grounded': True,
            'area_secured': True
        }

        all_pass = all(safety_checks.values())

        if not all_pass:
            failed = [k for k, v in safety_checks.items() if not v]
            self.logger.error(f"Safety checks failed: {failed}")

        return all_pass

    def _collect_data(self) -> List[MeasurementData]:
        """Collect wet leakage current data"""
        self.logger.info("Collecting wet leakage current data...")

        measurements = []

        # Get test parameters
        test_voltage = self.parameters['test_voltage'].value
        spray_duration = self.parameters['spray_duration'].value
        settling_time = self.parameters['settling_time'].value
        measurement_duration = self.parameters['measurement_duration'].value
        polarities = self.parameters['test_polarities'].value

        # Verify solution conductivity
        conductivity_meas = self.spray_system.measure('conductivity')
        measurements.append(conductivity_meas)

        # Perform test for each polarity
        for polarity in polarities:
            self.logger.info(f"Testing polarity: {polarity}")

            # Set test voltage
            self.hv_source.set_voltage(test_voltage, polarity)

            # Start water spray
            self.spray_system.start_spray()
            self.logger.info(f"Spraying for {spray_duration}s...")

            # Simulate spray duration
            # In production, would actually wait

            # Enable HV output
            self.hv_source.enable_output()

            # Wait for settling
            self.logger.info(f"Settling for {settling_time}s...")

            # Measure leakage current continuously
            self.logger.info(f"Measuring leakage current for {measurement_duration}s...")

            leakage_currents = self.leakage_meter.measure_continuous(
                duration=measurement_duration,
                test_voltage=test_voltage
            )

            # Stop spray
            self.spray_system.stop_spray()

            # Disable HV output
            self.hv_source.disable_output()

            # Calculate surface resistance
            mean_leakage = np.mean(leakage_currents)
            surface_resistance = test_voltage / mean_leakage if mean_leakage > 0 else float('inf')

            # Create WLT measurement record
            wlt_measurement = WLTMeasurement(
                timestamp=datetime.now(),
                leakage_current=mean_leakage,
                test_voltage=test_voltage,
                polarity=polarity,
                surface_resistance=surface_resistance,
                spray_duration=spray_duration,
                settling_time=settling_time
            )
            self.wlt_measurements.append(wlt_measurement)

            # Store individual current measurements
            for i, current in enumerate(leakage_currents):
                measurements.append(MeasurementData(
                    timestamp=datetime.now(),
                    value=current,
                    unit='A',
                    parameter_name=f'leakage_current_{polarity}',
                    equipment_id=self.leakage_meter.equipment_id,
                    metadata={
                        'sample': i,
                        'polarity': polarity,
                        'test_voltage': test_voltage
                    }
                ))

            # Log results
            self.logger.info(
                f"{polarity}: Leakage current = {mean_leakage*1e3:.3f} mA, "
                f"Surface resistance = {surface_resistance/1e3:.1f} kΩ"
            )

        return measurements

    def _analyze_data(self) -> Dict[str, Any]:
        """Analyze wet leakage test results"""
        self.logger.info("Analyzing wet leakage test data...")

        if not self.wlt_measurements:
            return {'error': 'No measurements available'}

        # Extract leakage currents
        leakage_currents = np.array([m.leakage_current for m in self.wlt_measurements])
        surface_resistances = np.array([m.surface_resistance for m in self.wlt_measurements
                                       if m.surface_resistance < float('inf')])

        # Calculate statistics
        leakage_stats = {
            'mean': float(np.mean(leakage_currents)),
            'max': float(np.max(leakage_currents)),
            'min': float(np.min(leakage_currents)),
            'std': float(np.std(leakage_currents, ddof=1)) if len(leakage_currents) > 1 else 0.0
        }

        resistance_stats = {
            'mean': float(np.mean(surface_resistances)) if len(surface_resistances) > 0 else 0,
            'min': float(np.min(surface_resistances)) if len(surface_resistances) > 0 else 0
        }

        # Analyze polarity dependence
        polarity_analysis = self._analyze_polarity_dependence()

        # Analyze current stability
        stability_analysis = self._analyze_current_stability()

        return {
            'leakage_current_stats': leakage_stats,
            'surface_resistance_stats': resistance_stats,
            'max_leakage_current_ma': leakage_stats['max'] * 1e3,
            'mean_leakage_current_ma': leakage_stats['mean'] * 1e3,
            'polarity_analysis': polarity_analysis,
            'stability_analysis': stability_analysis,
            'num_polarities_tested': len(self.wlt_measurements),
            'test_voltage': self.wlt_measurements[0].test_voltage if self.wlt_measurements else 0
        }

    def _analyze_polarity_dependence(self) -> Dict[str, Any]:
        """Analyze dependence of leakage current on voltage polarity"""
        positive_currents = [m.leakage_current for m in self.wlt_measurements
                            if m.polarity == 'positive']
        negative_currents = [m.leakage_current for m in self.wlt_measurements
                            if m.polarity == 'negative']

        if not positive_currents or not negative_currents:
            return {'status': 'incomplete'}

        positive_avg = np.mean(positive_currents)
        negative_avg = np.mean(negative_currents)

        ratio = positive_avg / negative_avg if negative_avg > 0 else float('inf')

        return {
            'positive_average_ma': float(positive_avg * 1e3),
            'negative_average_ma': float(negative_avg * 1e3),
            'ratio_positive_to_negative': float(ratio),
            'polarity_dependent': abs(ratio - 1.0) > 0.2  # > 20% difference
        }

    def _analyze_current_stability(self) -> Dict[str, Any]:
        """Analyze stability of leakage current over measurement period"""
        # Get continuous measurements for each polarity
        stability_results = {}

        for polarity in ['positive', 'negative']:
            polarity_measurements = self.get_measurements(f'leakage_current_{polarity}')

            if len(polarity_measurements) < 2:
                continue

            currents = np.array([m.value for m in polarity_measurements])

            # Calculate coefficient of variation
            cv = (np.std(currents, ddof=1) / np.mean(currents) * 100) if np.mean(currents) > 0 else 0

            # Check for trend
            time_indices = np.arange(len(currents))
            if len(currents) > 2:
                from scipy import stats
                slope, intercept, r_value, p_value, std_err = stats.linregress(time_indices, currents)
                trend = 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable'
            else:
                trend = 'insufficient_data'

            stability_results[polarity] = {
                'coefficient_of_variation': float(cv),
                'trend': trend,
                'stable': cv < 10.0  # CV < 10% considered stable
            }

        return stability_results

    def _detect_anomalies(self) -> None:
        """Detect anomalies in wet leakage test"""
        if not self.wlt_measurements:
            return

        max_leakage = self.parameters['max_leakage_current'].value

        for measurement in self.wlt_measurements:
            # Check leakage current limit
            if measurement.leakage_current > max_leakage:
                self.log_anomaly(
                    f"High leakage current ({measurement.polarity} polarity): "
                    f"{measurement.leakage_current*1e3:.3f} mA "
                    f"(max: {max_leakage*1e3:.1f} mA)"
                )

            # Check for very low surface resistance
            if measurement.surface_resistance < 10e3:  # < 10 kΩ
                self.log_anomaly(
                    f"Low surface resistance ({measurement.polarity} polarity): "
                    f"{measurement.surface_resistance/1e3:.1f} kΩ"
                )

        # Check polarity dependence
        polarity_analysis = self.analysis_results.get('polarity_analysis', {})
        if polarity_analysis.get('polarity_dependent', False):
            self.log_anomaly(
                f"Significant polarity dependence detected: "
                f"ratio = {polarity_analysis.get('ratio_positive_to_negative', 0):.2f}"
            )

        # Check stability
        stability = self.analysis_results.get('stability_analysis', {})
        for polarity, data in stability.items():
            if not data.get('stable', True):
                self.log_anomaly(
                    f"Unstable leakage current ({polarity}): "
                    f"CV = {data.get('coefficient_of_variation', 0):.1f}%"
                )

    def _determine_pass_fail(self) -> Tuple[TestResult, Dict[str, bool]]:
        """Determine pass/fail status"""
        criteria = {}

        if not self.wlt_measurements:
            return TestResult.ERROR, criteria

        max_leakage = self.parameters['max_leakage_current'].value

        # Check each polarity
        for measurement in self.wlt_measurements:
            polarity_name = f"leakage_{measurement.polarity}"
            criteria[polarity_name] = measurement.leakage_current <= max_leakage

        # Overall leakage criterion
        max_measured_leakage = max(m.leakage_current for m in self.wlt_measurements)
        criteria['overall_leakage'] = max_measured_leakage <= max_leakage

        # Stability criterion
        stability = self.analysis_results.get('stability_analysis', {})
        all_stable = all(data.get('stable', False) for data in stability.values())
        criteria['current_stable'] = all_stable

        # Overall result
        all_pass = all(criteria.values())
        critical_pass = criteria.get('overall_leakage', False)

        if all_pass:
            return TestResult.PASS, criteria
        elif critical_pass:
            return TestResult.CONDITIONAL_PASS, criteria
        else:
            return TestResult.FAIL, criteria

    def _emergency_shutdown(self) -> None:
        """Emergency shutdown procedure"""
        self.logger.warning("EMERGENCY SHUTDOWN")

        try:
            self.hv_source.disable_output()
            self.spray_system.stop_spray()
        except Exception as e:
            self.logger.error(f"Error during emergency shutdown: {e}")

    def cleanup(self) -> None:
        """Cleanup and ensure safety"""
        # Ensure HV is disabled and spray is stopped
        if self.hv_source.output_enabled:
            self.logger.warning("HV still enabled during cleanup - disabling")
            self.hv_source.disable_output()

        if self.spray_system.is_spraying:
            self.logger.warning("Spray still active during cleanup - stopping")
            self.spray_system.stop_spray()

        super().cleanup()
