"""
Insulation Resistance Test Block (Session 22)

Implements IR testing procedures, resistance calculations, pass/fail criteria,
and trend analysis for PV module safety compliance according to IEC 61215-2.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy import stats

from .base_test_block import (
    BaseTestBlock,
    EquipmentInterface,
    MeasurementData,
    TestBlockResult,
    TestParameter,
    TestResult
)


@dataclass
class IRMeasurement:
    """Single insulation resistance measurement"""
    timestamp: datetime
    resistance: float  # Ohms
    test_voltage: float  # V
    temperature: float  # °C
    humidity: float  # %RH
    leakage_current: float  # A
    location: str  # Test location/configuration


class Megohmmeter(EquipmentInterface):
    """Megohmmeter/insulation tester equipment interface"""

    def connect(self) -> bool:
        """Connect to megohmmeter"""
        self.logger.info(f"Connecting to megohmmeter {self.equipment_id}")
        self.connected = True
        return True

    def disconnect(self) -> bool:
        """Disconnect from megohmmeter"""
        self.logger.info(f"Disconnecting megohmmeter {self.equipment_id}")
        self.connected = False
        return True

    def initialize(self) -> bool:
        """Initialize megohmmeter"""
        self.logger.info("Initializing megohmmeter")
        return self.configure({
            'test_voltage': 1000,  # V DC
            'measurement_time': 60,  # seconds
            'ranging': 'auto'
        })

    def configure(self, settings: Dict[str, Any]) -> bool:
        """Configure megohmmeter settings"""
        self.logger.info(f"Configuring megohmmeter: {settings}")
        self.config.update(settings)
        return True

    def measure(self, parameter: str) -> MeasurementData:
        """Measure insulation resistance"""
        # Stub: Simulate realistic IR measurement
        if parameter == 'resistance':
            # Typical good module: > 400 MOhm
            base_resistance = 500e6 + np.random.normal(0, 50e6)
            value = max(1e6, base_resistance)  # Minimum 1 MOhm
            unit = 'Ohm'
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

    def measure_resistance(
        self,
        test_voltage: float,
        duration: float = 60.0
    ) -> Tuple[float, float]:
        """
        Measure insulation resistance at specified voltage

        Args:
            test_voltage: Test voltage in V DC
            duration: Measurement duration in seconds

        Returns:
            Tuple of (resistance in Ohms, leakage current in A)
        """
        self.logger.info(f"Measuring IR at {test_voltage}V for {duration}s")

        # Stub: Simulate time-dependent resistance measurement
        # Real measurements show initial charging followed by stable value
        base_resistance = 500e6 + np.random.normal(0, 50e6)

        # Simulate stabilization
        resistance = max(1e6, base_resistance)
        leakage_current = test_voltage / resistance if resistance > 0 else 0

        return resistance, leakage_current


class EnvironmentMonitor(EquipmentInterface):
    """Environmental conditions monitoring equipment"""

    def connect(self) -> bool:
        """Connect to environment monitor"""
        self.logger.info(f"Connecting to environment monitor {self.equipment_id}")
        self.connected = True
        return True

    def disconnect(self) -> bool:
        """Disconnect from environment monitor"""
        self.logger.info(f"Disconnecting environment monitor {self.equipment_id}")
        self.connected = False
        return True

    def initialize(self) -> bool:
        """Initialize environment monitor"""
        self.logger.info("Initializing environment monitor")
        return True

    def configure(self, settings: Dict[str, Any]) -> bool:
        """Configure environment monitor"""
        self.config.update(settings)
        return True

    def measure(self, parameter: str) -> MeasurementData:
        """Measure environmental parameter"""
        # Stub: Simulate environmental conditions
        value_map = {
            'temperature': 23.0 + np.random.normal(0, 1.0),  # °C
            'humidity': 45.0 + np.random.normal(0, 5.0)  # %RH
        }

        value = value_map.get(parameter, 0.0)
        unit = '°C' if parameter == 'temperature' else '%RH'

        return MeasurementData(
            timestamp=datetime.now(),
            value=value,
            unit=unit,
            parameter_name=parameter,
            equipment_id=self.equipment_id,
            uncertainty=self.get_uncertainty(parameter, value)
        )


class InsulationResistanceTest(BaseTestBlock):
    """
    Insulation Resistance Test Block

    Tests electrical insulation integrity of PV modules to ensure safety
    and compliance with IEC 61215-2 requirements.
    """

    def __init__(
        self,
        test_id: str,
        operator: str,
        config: Dict[str, Any],
        megohmmeter: Megohmmeter,
        env_monitor: Optional[EnvironmentMonitor] = None
    ):
        super().__init__(
            test_id=test_id,
            operator=operator,
            config=config,
            equipment=[megohmmeter] + ([env_monitor] if env_monitor else [])
        )

        self.megohmmeter = megohmmeter
        self.env_monitor = env_monitor
        self.ir_measurements: List[IRMeasurement] = []

    def _initialize_parameters(self) -> None:
        """Initialize test parameters"""
        self.parameters = {
            'test_voltage': TestParameter(
                name='test_voltage',
                value=1000,
                unit='V',
                tolerance=50,
                description='DC test voltage for IR measurement'
            ),
            'measurement_duration': TestParameter(
                name='measurement_duration',
                value=60,
                unit='s',
                description='Duration of each IR measurement'
            ),
            'min_resistance': TestParameter(
                name='min_resistance',
                value=40e6,  # 40 MOhm minimum per IEC 61215-2
                unit='Ohm',
                description='Minimum acceptable insulation resistance'
            ),
            'test_configurations': TestParameter(
                name='test_configurations',
                value=['terminals_to_frame', 'positive_to_frame', 'negative_to_frame'],
                unit='',
                description='IR test configurations to perform'
            ),
            'stabilization_time': TestParameter(
                name='stabilization_time',
                value=300,  # 5 minutes
                unit='s',
                description='Time to allow module to stabilize before testing'
            )
        }

    def execute(self) -> TestBlockResult:
        """Execute insulation resistance test"""
        self.start_time = datetime.now()
        self.logger.info(f"Starting insulation resistance test {self.test_id}")

        try:
            # Validate equipment
            issues = self.validate_equipment()
            if issues:
                raise RuntimeError(f"Equipment validation failed: {', '.join(issues)}")

            # Initialize equipment
            self.megohmmeter.initialize()
            if self.env_monitor:
                self.env_monitor.initialize()

            # Collect data
            self.measurements = self._collect_data()

            # Analyze data
            self.analysis_results = self._analyze_data()

            # Check for anomalies
            self._detect_anomalies()

        except Exception as e:
            self.logger.error(f"Error during IR test: {e}")
            self.end_time = datetime.now()
            result = self.generate_result()
            result.result = TestResult.ERROR
            result.error_message = str(e)
            return result
        finally:
            self.cleanup()

        self.end_time = datetime.now()
        return self.generate_result()

    def _collect_data(self) -> List[MeasurementData]:
        """Collect insulation resistance measurements"""
        self.logger.info("Collecting insulation resistance data...")

        measurements = []

        # Allow module to stabilize
        stabilization_time = self.parameters['stabilization_time'].value
        self.logger.info(f"Waiting {stabilization_time}s for module stabilization...")
        # In production, would wait actual time

        # Get test voltage
        test_voltage = self.parameters['test_voltage'].value

        # Get test configurations
        configurations = self.parameters['test_configurations'].value

        # Perform IR test for each configuration
        for config in configurations:
            self.logger.info(f"Testing configuration: {config}")

            # Record environmental conditions
            if self.env_monitor:
                temp_measurement = self.env_monitor.measure('temperature')
                measurements.append(temp_measurement)
                temperature = temp_measurement.value

                humidity_measurement = self.env_monitor.measure('humidity')
                measurements.append(humidity_measurement)
                humidity = humidity_measurement.value
            else:
                temperature = 23.0  # Default
                humidity = 45.0  # Default

            # Perform IR measurement
            resistance, leakage_current = self.megohmmeter.measure_resistance(
                test_voltage=test_voltage,
                duration=self.parameters['measurement_duration'].value
            )

            # Create IR measurement record
            ir_measurement = IRMeasurement(
                timestamp=datetime.now(),
                resistance=resistance,
                test_voltage=test_voltage,
                temperature=temperature,
                humidity=humidity,
                leakage_current=leakage_current,
                location=config
            )
            self.ir_measurements.append(ir_measurement)

            # Store as measurements
            measurements.append(MeasurementData(
                timestamp=ir_measurement.timestamp,
                value=resistance,
                unit='Ohm',
                parameter_name=f'resistance_{config}',
                equipment_id=self.megohmmeter.equipment_id,
                metadata={
                    'test_voltage': test_voltage,
                    'temperature': temperature,
                    'humidity': humidity,
                    'leakage_current': leakage_current
                }
            ))

            self.logger.info(
                f"{config}: {resistance/1e6:.1f} MOhm "
                f"(leakage: {leakage_current*1e9:.3f} nA)"
            )

        return measurements

    def _analyze_data(self) -> Dict[str, Any]:
        """Analyze insulation resistance data"""
        self.logger.info("Analyzing insulation resistance data...")

        if not self.ir_measurements:
            return {'error': 'No measurements available'}

        # Extract resistance values
        resistances = np.array([m.resistance for m in self.ir_measurements])
        leakage_currents = np.array([m.leakage_current for m in self.ir_measurements])

        # Calculate statistics
        resistance_stats = {
            'mean': float(np.mean(resistances)),
            'min': float(np.min(resistances)),
            'max': float(np.max(resistances)),
            'std': float(np.std(resistances, ddof=1)) if len(resistances) > 1 else 0.0
        }

        leakage_stats = {
            'mean': float(np.mean(leakage_currents)),
            'max': float(np.max(leakage_currents))
        }

        # Normalize to standard conditions (if environmental data available)
        normalized_resistances = self._normalize_to_standard_conditions()

        # Trend analysis (if historical data available)
        trend_analysis = self._analyze_trends()

        # Calculate polarization index (if multiple time measurements available)
        polarization_index = self._calculate_polarization_index()

        return {
            'resistance_stats': resistance_stats,
            'leakage_stats': leakage_stats,
            'min_resistance': resistance_stats['min'],
            'max_resistance': resistance_stats['max'],
            'mean_resistance': resistance_stats['mean'],
            'min_leakage_current': float(np.min(leakage_currents)),
            'max_leakage_current': float(np.max(leakage_currents)),
            'normalized_resistances': normalized_resistances,
            'trend_analysis': trend_analysis,
            'polarization_index': polarization_index,
            'configurations_tested': len(self.ir_measurements)
        }

    def _normalize_to_standard_conditions(self) -> Dict[str, float]:
        """
        Normalize resistance measurements to standard conditions (20°C, 50% RH)

        Temperature coefficient: approximately 5-10% per °C
        Humidity effect: varies with material
        """
        normalized = {}

        for measurement in self.ir_measurements:
            # Temperature correction factor (simplified)
            temp_coefficient = 0.05  # 5% per °C
            temp_correction = 1.0 + temp_coefficient * (20.0 - measurement.temperature)

            # Humidity correction (simplified)
            humidity_coefficient = 0.02  # 2% per %RH
            humidity_correction = 1.0 + humidity_coefficient * (50.0 - measurement.humidity)

            # Apply corrections
            normalized_r = measurement.resistance * temp_correction * humidity_correction

            normalized[measurement.location] = float(normalized_r)

        return normalized

    def _analyze_trends(self) -> Dict[str, Any]:
        """Analyze trends in IR measurements over time"""
        # In production, would compare with historical database
        # For now, analyze current session only

        if len(self.ir_measurements) < 2:
            return {'status': 'insufficient_data'}

        resistances = np.array([m.resistance for m in self.ir_measurements])

        # Check for decreasing trend (potential degradation)
        if len(resistances) > 2:
            slope = np.polyfit(range(len(resistances)), resistances, 1)[0]

            trend = {
                'slope': float(slope),
                'direction': 'decreasing' if slope < 0 else 'increasing' if slope > 0 else 'stable',
                'degradation_rate': float(abs(slope) / np.mean(resistances) * 100)  # % per measurement
            }

            if slope < -1e6:  # Decreasing by > 1 MOhm per measurement
                trend['warning'] = 'Significant decreasing trend detected'

            return trend

        return {'status': 'stable'}

    def _calculate_polarization_index(self) -> Optional[float]:
        """
        Calculate polarization index (PI)

        PI = R(10min) / R(1min)
        PI > 2.0 indicates good insulation
        PI < 1.0 indicates deteriorated insulation
        """
        # In production, would measure at 1 min and 10 min intervals
        # For now, return None as stub

        # Stub calculation assuming we have time-series data
        if len(self.ir_measurements) >= 2:
            # Simplified: use first and last measurements
            r_initial = self.ir_measurements[0].resistance
            r_final = self.ir_measurements[-1].resistance

            pi = r_final / r_initial if r_initial > 0 else None

            return float(pi) if pi else None

        return None

    def _detect_anomalies(self) -> None:
        """Detect anomalies in IR measurements"""
        if not self.ir_measurements:
            return

        min_resistance = self.parameters['min_resistance'].value

        for measurement in self.ir_measurements:
            # Check minimum resistance requirement
            if measurement.resistance < min_resistance:
                self.log_anomaly(
                    f"Low insulation resistance at {measurement.location}: "
                    f"{measurement.resistance/1e6:.1f} MOhm "
                    f"(min: {min_resistance/1e6:.1f} MOhm)"
                )

            # Check for very high leakage current
            if measurement.leakage_current > 1e-6:  # > 1 µA
                self.log_anomaly(
                    f"High leakage current at {measurement.location}: "
                    f"{measurement.leakage_current*1e6:.3f} µA"
                )

        # Check variation between configurations
        resistances = np.array([m.resistance for m in self.ir_measurements])
        if len(resistances) > 1:
            cv = np.std(resistances, ddof=1) / np.mean(resistances) * 100

            if cv > 50:  # More than 50% variation
                self.log_anomaly(
                    f"High variation between test configurations: CV = {cv:.1f}%"
                )

        # Check polarization index
        pi = self.analysis_results.get('polarization_index')
        if pi is not None and pi < 1.0:
            self.log_anomaly(
                f"Low polarization index: {pi:.2f} (indicates deteriorated insulation)"
            )

        # Check environmental conditions
        if self.env_monitor:
            for measurement in self.ir_measurements:
                if measurement.humidity > 85:
                    self.log_anomaly(
                        f"High humidity during test: {measurement.humidity:.1f}% RH"
                    )

                if measurement.temperature < 10 or measurement.temperature > 35:
                    self.log_anomaly(
                        f"Temperature outside recommended range: {measurement.temperature:.1f}°C"
                    )

    def _determine_pass_fail(self) -> Tuple[TestResult, Dict[str, bool]]:
        """Determine pass/fail status"""
        criteria = {}

        if not self.ir_measurements:
            return TestResult.ERROR, criteria

        min_resistance = self.parameters['min_resistance'].value

        # Check each configuration
        for measurement in self.ir_measurements:
            config_name = f"resistance_{measurement.location}"
            criteria[config_name] = measurement.resistance >= min_resistance

        # Check overall minimum
        min_measured = min(m.resistance for m in self.ir_measurements)
        criteria['overall_minimum'] = min_measured >= min_resistance

        # Check leakage current
        max_leakage = max(m.leakage_current for m in self.ir_measurements)
        criteria['leakage_current'] = max_leakage < 1e-6  # < 1 µA

        # Check polarization index if available
        pi = self.analysis_results.get('polarization_index')
        if pi is not None:
            criteria['polarization_index'] = pi >= 1.0

        # Overall result
        all_pass = all(criteria.values())

        if all_pass:
            return TestResult.PASS, criteria
        elif criteria.get('overall_minimum', False):
            return TestResult.CONDITIONAL_PASS, criteria
        else:
            return TestResult.FAIL, criteria
