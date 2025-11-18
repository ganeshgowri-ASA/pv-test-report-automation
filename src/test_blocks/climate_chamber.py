"""
Climate Chamber Test Block (Session 23)

Implements temperature cycling, humidity freeze, damp heat testing, and
environmental conditioning for PV module durability testing according to IEC 61215-2.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
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


class TestType(Enum):
    """Climate chamber test types"""
    TEMPERATURE_CYCLING = "TC"  # IEC 61215-2 MQT 11
    HUMIDITY_FREEZE = "HF"  # IEC 61215-2 MQT 12
    DAMP_HEAT = "DH"  # IEC 61215-2 MQT 13
    THERMAL_CYCLING = "TH"  # Advanced thermal cycling


@dataclass
class CycleProfile:
    """Environmental cycle profile definition"""
    name: str
    temperature_points: List[Tuple[float, float]]  # [(temp_C, duration_min), ...]
    humidity_points: Optional[List[Tuple[float, float]]]  # [(rh_%, duration_min), ...]
    ramp_rate: float  # °C/min
    cycles: int


@dataclass
class EnvironmentalCondition:
    """Environmental condition measurement"""
    timestamp: datetime
    temperature: float  # °C
    humidity: float  # %RH
    cycle_number: int
    phase: str  # 'heating', 'cooling', 'soaking', 'stabilizing'


class ClimateChamber(EquipmentInterface):
    """Climate/environmental chamber equipment interface"""

    def __init__(self, equipment_id: str, config: Dict[str, Any]):
        super().__init__(equipment_id, config)
        self.current_temperature: float = 25.0
        self.current_humidity: float = 50.0
        self.target_temperature: float = 25.0
        self.target_humidity: float = 50.0
        self.is_running: bool = False

    def connect(self) -> bool:
        """Connect to climate chamber"""
        self.logger.info(f"Connecting to climate chamber {self.equipment_id}")
        self.connected = True
        return True

    def disconnect(self) -> bool:
        """Disconnect from climate chamber"""
        self.logger.info(f"Disconnecting climate chamber {self.equipment_id}")
        self.connected = False
        self.is_running = False
        return True

    def initialize(self) -> bool:
        """Initialize climate chamber"""
        self.logger.info("Initializing climate chamber")
        return self.configure({
            'temperature_range': (-40, 85),  # °C
            'humidity_range': (10, 95),  # %RH
            'ramp_rate': 3.0,  # °C/min
            'safety_limits': True
        })

    def configure(self, settings: Dict[str, Any]) -> bool:
        """Configure chamber settings"""
        self.logger.info(f"Configuring climate chamber: {settings}")
        self.config.update(settings)
        return True

    def measure(self, parameter: str) -> MeasurementData:
        """Measure chamber condition"""
        # Stub: Simulate chamber conditions
        value_map = {
            'temperature': self.current_temperature + np.random.normal(0, 0.2),
            'humidity': self.current_humidity + np.random.normal(0, 1.0)
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

    def set_temperature(self, temperature: float, humidity: Optional[float] = None) -> bool:
        """Set target temperature and optional humidity"""
        self.logger.info(f"Setting chamber to {temperature}°C" +
                        (f", {humidity}% RH" if humidity else ""))

        self.target_temperature = temperature
        if humidity is not None:
            self.target_humidity = humidity

        return True

    def start_cycle(self) -> bool:
        """Start environmental cycling"""
        self.logger.info("Starting environmental cycle")
        self.is_running = True
        return True

    def stop_cycle(self) -> bool:
        """Stop environmental cycling"""
        self.logger.info("Stopping environmental cycle")
        self.is_running = False
        return True

    def get_status(self) -> Dict[str, Any]:
        """Get chamber status"""
        return {
            'running': self.is_running,
            'current_temperature': self.current_temperature,
            'current_humidity': self.current_humidity,
            'target_temperature': self.target_temperature,
            'target_humidity': self.target_humidity,
            'at_setpoint': abs(self.current_temperature - self.target_temperature) < 1.0
        }

    def simulate_ramp(self, target_temp: float, ramp_rate: float) -> None:
        """Simulate temperature ramping (for testing)"""
        # Stub: Instantly set to target (real implementation would ramp gradually)
        self.current_temperature = target_temp


class DataLogger(EquipmentInterface):
    """Data logger for continuous environmental monitoring"""

    def connect(self) -> bool:
        """Connect to data logger"""
        self.logger.info(f"Connecting to data logger {self.equipment_id}")
        self.connected = True
        return True

    def disconnect(self) -> bool:
        """Disconnect from data logger"""
        self.logger.info(f"Disconnecting data logger {self.equipment_id}")
        self.connected = False
        return True

    def initialize(self) -> bool:
        """Initialize data logger"""
        self.logger.info("Initializing data logger")
        return self.configure({
            'sampling_rate': 60,  # seconds
            'channels': ['temperature', 'humidity', 'voltage', 'current']
        })

    def configure(self, settings: Dict[str, Any]) -> bool:
        """Configure data logger"""
        self.config.update(settings)
        return True

    def measure(self, parameter: str) -> MeasurementData:
        """Read parameter from data logger"""
        # Stub implementation
        value = 0.0
        unit = ''

        return MeasurementData(
            timestamp=datetime.now(),
            value=value,
            unit=unit,
            parameter_name=parameter,
            equipment_id=self.equipment_id
        )


class ClimateChamberTest(BaseTestBlock):
    """
    Climate Chamber Test Block

    Performs environmental stress testing including temperature cycling,
    humidity freeze, and damp heat tests.
    """

    def __init__(
        self,
        test_id: str,
        operator: str,
        config: Dict[str, Any],
        chamber: ClimateChamber,
        data_logger: Optional[DataLogger] = None,
        test_type: TestType = TestType.TEMPERATURE_CYCLING
    ):
        super().__init__(
            test_id=test_id,
            operator=operator,
            config=config,
            equipment=[chamber] + ([data_logger] if data_logger else [])
        )

        self.chamber = chamber
        self.data_logger = data_logger
        self.test_type = test_type
        self.conditions: List[EnvironmentalCondition] = []
        self.cycle_profile: Optional[CycleProfile] = None

    def _initialize_parameters(self) -> None:
        """Initialize test parameters based on test type"""
        # Common parameters
        base_params = {
            'sampling_interval': TestParameter(
                name='sampling_interval',
                value=300,  # 5 minutes
                unit='s',
                description='Environmental data sampling interval'
            ),
            'stabilization_tolerance': TestParameter(
                name='stabilization_tolerance',
                value=2.0,
                unit='°C',
                description='Temperature stabilization tolerance'
            )
        }

        # Test-specific parameters
        if self.test_type == TestType.TEMPERATURE_CYCLING:
            specific_params = {
                'num_cycles': TestParameter(
                    name='num_cycles',
                    value=200,
                    unit='',
                    description='Number of temperature cycles (IEC 61215-2: 200)'
                ),
                'low_temperature': TestParameter(
                    name='low_temperature',
                    value=-40,
                    unit='°C',
                    description='Low temperature setpoint'
                ),
                'high_temperature': TestParameter(
                    name='high_temperature',
                    value=85,
                    unit='°C',
                    description='High temperature setpoint'
                ),
                'dwell_time': TestParameter(
                    name='dwell_time',
                    value=30,
                    unit='min',
                    description='Dwell time at each temperature'
                )
            }

        elif self.test_type == TestType.HUMIDITY_FREEZE:
            specific_params = {
                'num_cycles': TestParameter(
                    name='num_cycles',
                    value=10,
                    unit='',
                    description='Number of humidity-freeze cycles (IEC 61215-2: 10)'
                ),
                'humidity_temperature': TestParameter(
                    name='humidity_temperature',
                    value=85,
                    unit='°C',
                    description='Temperature during humidity phase'
                ),
                'humidity_level': TestParameter(
                    name='humidity_level',
                    value=85,
                    unit='%RH',
                    description='Humidity level'
                ),
                'freeze_temperature': TestParameter(
                    name='freeze_temperature',
                    value=-40,
                    unit='°C',
                    description='Freeze temperature'
                ),
                'humidity_duration': TestParameter(
                    name='humidity_duration',
                    value=20,
                    unit='hours',
                    description='Duration of humidity phase'
                )
            }

        elif self.test_type == TestType.DAMP_HEAT:
            specific_params = {
                'temperature': TestParameter(
                    name='temperature',
                    value=85,
                    unit='°C',
                    description='Damp heat temperature'
                ),
                'humidity': TestParameter(
                    name='humidity',
                    value=85,
                    unit='%RH',
                    description='Damp heat humidity'
                ),
                'duration': TestParameter(
                    name='duration',
                    value=1000,
                    unit='hours',
                    description='Test duration (IEC 61215-2: 1000 hours)'
                )
            }

        else:
            specific_params = {}

        self.parameters = {**base_params, **specific_params}

    def _create_cycle_profile(self) -> CycleProfile:
        """Create environmental cycle profile based on test type"""
        if self.test_type == TestType.TEMPERATURE_CYCLING:
            # IEC 61215-2 MQT 11: TC200
            return CycleProfile(
                name="TC200",
                temperature_points=[
                    (85, 30),   # High temp, 30 min dwell
                    (-40, 30),  # Low temp, 30 min dwell
                ],
                humidity_points=None,
                ramp_rate=3.0,  # °C/min (typical chamber capability)
                cycles=int(self.parameters['num_cycles'].value)
            )

        elif self.test_type == TestType.HUMIDITY_FREEZE:
            # IEC 61215-2 MQT 12: HF10
            return CycleProfile(
                name="HF10",
                temperature_points=[
                    (85, 1200),   # 20 hours at 85°C
                    (-40, 60),    # 1 hour at -40°C (min)
                ],
                humidity_points=[
                    (85, 1200),   # 85% RH during high temp
                    (None, 60),   # No humidity control during freeze
                ],
                ramp_rate=1.0,
                cycles=int(self.parameters['num_cycles'].value)
            )

        elif self.test_type == TestType.DAMP_HEAT:
            # IEC 61215-2 MQT 13: DH1000
            return CycleProfile(
                name="DH1000",
                temperature_points=[
                    (85, 60000),  # 1000 hours constant
                ],
                humidity_points=[
                    (85, 60000),  # 1000 hours constant
                ],
                ramp_rate=1.0,
                cycles=1  # Single long exposure
            )

        else:
            raise ValueError(f"Unknown test type: {self.test_type}")

    def execute(self) -> TestBlockResult:
        """Execute climate chamber test"""
        self.start_time = datetime.now()
        self.logger.info(f"Starting {self.test_type.value} test {self.test_id}")

        try:
            # Validate equipment
            issues = self.validate_equipment()
            if issues:
                raise RuntimeError(f"Equipment validation failed: {', '.join(issues)}")

            # Initialize equipment
            self.chamber.initialize()
            if self.data_logger:
                self.data_logger.initialize()

            # Create cycle profile
            self.cycle_profile = self._create_cycle_profile()

            # Run test cycles
            self.measurements = self._collect_data()

            # Analyze data
            self.analysis_results = self._analyze_data()

            # Check for anomalies
            self._detect_anomalies()

        except Exception as e:
            self.logger.error(f"Error during climate chamber test: {e}")
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
        """Collect environmental data during test cycles"""
        self.logger.info(f"Collecting data for {self.cycle_profile.name}...")

        measurements = []

        # Start chamber cycling
        self.chamber.start_cycle()

        # Execute cycles
        for cycle_num in range(1, self.cycle_profile.cycles + 1):
            self.logger.info(f"Starting cycle {cycle_num}/{self.cycle_profile.cycles}")

            # Execute each temperature point in the cycle
            for i, (temp, duration_min) in enumerate(self.cycle_profile.temperature_points):
                # Get corresponding humidity if specified
                humidity = None
                if self.cycle_profile.humidity_points:
                    humidity, _ = self.cycle_profile.humidity_points[i]

                # Set chamber conditions
                self.chamber.set_temperature(temp, humidity)

                # Simulate ramping
                phase = "heating" if temp > self.chamber.current_temperature else "cooling"
                self.chamber.simulate_ramp(temp, self.cycle_profile.ramp_rate)

                # Log condition change
                self.logger.info(
                    f"Cycle {cycle_num}: {phase} to {temp}°C" +
                    (f", {humidity}% RH" if humidity else "")
                )

                # Simulate dwell period with periodic measurements
                # In production, would actually wait and measure continuously
                num_samples = max(1, int(duration_min / 5))  # Sample every 5 minutes

                for sample in range(num_samples):
                    # Measure temperature
                    temp_measurement = self.chamber.measure('temperature')
                    measurements.append(temp_measurement)

                    # Measure humidity
                    humidity_measurement = self.chamber.measure('humidity')
                    measurements.append(humidity_measurement)

                    # Record condition
                    condition = EnvironmentalCondition(
                        timestamp=datetime.now(),
                        temperature=temp_measurement.value,
                        humidity=humidity_measurement.value,
                        cycle_number=cycle_num,
                        phase='soaking' if sample > 0 else phase
                    )
                    self.conditions.append(condition)

            # Log cycle completion
            self.logger.info(f"Completed cycle {cycle_num}/{self.cycle_profile.cycles}")

            # For demo purposes, limit to first 5 cycles
            if cycle_num >= 5 and self.cycle_profile.cycles > 10:
                self.logger.info(f"Demo mode: Simulating remaining {self.cycle_profile.cycles - 5} cycles")
                # Add summary measurements for remaining cycles
                for remaining_cycle in range(cycle_num + 1, self.cycle_profile.cycles + 1):
                    # Just add final measurements for each remaining cycle
                    for temp, _ in self.cycle_profile.temperature_points:
                        measurements.append(MeasurementData(
                            timestamp=datetime.now(),
                            value=temp + np.random.normal(0, 0.5),
                            unit='°C',
                            parameter_name='temperature',
                            equipment_id=self.chamber.equipment_id
                        ))
                break

        # Stop chamber
        self.chamber.stop_cycle()

        self.logger.info(f"Collected {len(measurements)} measurements over {len(self.conditions)} conditions")
        return measurements

    def _analyze_data(self) -> Dict[str, Any]:
        """Analyze environmental test data"""
        self.logger.info("Analyzing environmental test data...")

        if not self.conditions:
            return {'error': 'No condition data available'}

        # Extract temperature and humidity arrays
        temperatures = np.array([c.temperature for c in self.conditions])
        humidities = np.array([c.humidity for c in self.conditions])

        # Calculate statistics
        temp_stats = {
            'mean': float(np.mean(temperatures)),
            'min': float(np.min(temperatures)),
            'max': float(np.max(temperatures)),
            'std': float(np.std(temperatures, ddof=1)) if len(temperatures) > 1 else 0.0,
            'range': float(np.ptp(temperatures))
        }

        humidity_stats = {
            'mean': float(np.mean(humidities)),
            'min': float(np.min(humidities)),
            'max': float(np.max(humidities)),
            'std': float(np.std(humidities, ddof=1)) if len(humidities) > 1 else 0.0
        }

        # Analyze temperature uniformity
        uniformity = self._analyze_uniformity(temperatures)

        # Analyze cycle completion
        expected_cycles = self.cycle_profile.cycles
        completed_cycles = max([c.cycle_number for c in self.conditions]) if self.conditions else 0

        # Calculate exposure metrics
        exposure_metrics = self._calculate_exposure_metrics()

        # Analyze stabilization performance
        stabilization = self._analyze_stabilization()

        return {
            'test_type': self.test_type.value,
            'temperature_stats': temp_stats,
            'humidity_stats': humidity_stats,
            'uniformity': uniformity,
            'expected_cycles': expected_cycles,
            'completed_cycles': completed_cycles,
            'completion_rate': (completed_cycles / expected_cycles * 100) if expected_cycles > 0 else 0,
            'exposure_metrics': exposure_metrics,
            'stabilization_performance': stabilization,
            'total_test_time_hours': (self.end_time - self.start_time).total_seconds() / 3600 if self.end_time else 0
        }

    def _analyze_uniformity(self, values: np.ndarray) -> Dict[str, float]:
        """Analyze temperature/humidity uniformity"""
        # Group by cycle and analyze variance within cycles
        if len(values) < 2:
            return {'uniformity': 0.0}

        return {
            'coefficient_of_variation': float(np.std(values, ddof=1) / np.mean(values) * 100) if np.mean(values) != 0 else 0.0,
            'uniformity_index': float(1.0 - np.std(values, ddof=1) / np.ptp(values)) if np.ptp(values) > 0 else 1.0
        }

    def _calculate_exposure_metrics(self) -> Dict[str, Any]:
        """Calculate cumulative exposure metrics"""
        if not self.conditions:
            return {}

        # Calculate time at various temperature ranges
        high_temp_time = sum(1 for c in self.conditions if c.temperature > 70)
        low_temp_time = sum(1 for c in self.conditions if c.temperature < 0)
        high_humidity_time = sum(1 for c in self.conditions if c.humidity > 80)

        sampling_interval = self.parameters['sampling_interval'].value / 60  # Convert to minutes

        return {
            'high_temperature_exposure_hours': high_temp_time * sampling_interval / 60,
            'low_temperature_exposure_hours': low_temp_time * sampling_interval / 60,
            'high_humidity_exposure_hours': high_humidity_time * sampling_interval / 60,
            'total_exposure_hours': len(self.conditions) * sampling_interval / 60
        }

    def _analyze_stabilization(self) -> Dict[str, Any]:
        """Analyze temperature stabilization performance"""
        # Check how quickly chamber stabilizes at setpoints
        # Stub: Would analyze actual ramp and stabilization times

        return {
            'average_ramp_time_minutes': 15.0,  # Stub
            'stabilization_achieved': True,
            'overshoot_events': 0
        }

    def _detect_anomalies(self) -> None:
        """Detect anomalies in environmental testing"""
        if not self.conditions:
            return

        # Check for temperature excursions
        tolerance = self.parameters['stabilization_tolerance'].value

        for i, condition in enumerate(self.conditions):
            # Determine expected temperature for this phase
            if self.test_type == TestType.TEMPERATURE_CYCLING:
                expected_temps = [self.parameters['low_temperature'].value,
                                self.parameters['high_temperature'].value]
            elif self.test_type == TestType.DAMP_HEAT:
                expected_temps = [self.parameters['temperature'].value]
            else:
                expected_temps = []

            # Check if temperature is within tolerance of any setpoint
            if expected_temps and condition.phase == 'soaking':
                within_tolerance = any(
                    abs(condition.temperature - temp) <= tolerance
                    for temp in expected_temps
                )

                if not within_tolerance:
                    self.log_anomaly(
                        f"Temperature deviation at cycle {condition.cycle_number}: "
                        f"{condition.temperature:.1f}°C (tolerance: ±{tolerance}°C)"
                    )

        # Check cycle completion
        expected_cycles = self.cycle_profile.cycles
        completed_cycles = self.analysis_results.get('completed_cycles', 0)

        if completed_cycles < expected_cycles:
            self.log_anomaly(
                f"Incomplete test: {completed_cycles}/{expected_cycles} cycles completed"
            )

        # Check for humidity control issues (if applicable)
        if self.test_type in [TestType.HUMIDITY_FREEZE, TestType.DAMP_HEAT]:
            expected_humidity = self.parameters.get('humidity_level') or self.parameters.get('humidity')
            if expected_humidity:
                humidity_values = [c.humidity for c in self.conditions if c.phase == 'soaking']
                if humidity_values:
                    mean_humidity = np.mean(humidity_values)
                    if abs(mean_humidity - expected_humidity.value) > 5.0:  # ±5% RH tolerance
                        self.log_anomaly(
                            f"Humidity deviation: {mean_humidity:.1f}% RH "
                            f"(target: {expected_humidity.value}% RH)"
                        )

    def _determine_pass_fail(self) -> Tuple[TestResult, Dict[str, bool]]:
        """Determine pass/fail status"""
        criteria = {}

        # Check cycle completion
        completion_rate = self.analysis_results.get('completion_rate', 0)
        criteria['cycle_completion'] = completion_rate >= 100.0

        # Check temperature stability
        temp_stats = self.analysis_results.get('temperature_stats', {})
        criteria['temperature_stability'] = temp_stats.get('std', 999) < 5.0  # Within ±5°C

        # Check humidity control (if applicable)
        if self.test_type in [TestType.HUMIDITY_FREEZE, TestType.DAMP_HEAT]:
            humidity_stats = self.analysis_results.get('humidity_stats', {})
            criteria['humidity_control'] = humidity_stats.get('std', 999) < 10.0  # Within ±10% RH

        # Check for no critical anomalies
        critical_anomalies = [a for a in self.anomalies if 'deviation' in a.lower()]
        criteria['no_critical_anomalies'] = len(critical_anomalies) == 0

        # Overall result
        all_pass = all(criteria.values())
        essential_pass = criteria.get('cycle_completion', False)

        if all_pass:
            return TestResult.PASS, criteria
        elif essential_pass:
            return TestResult.CONDITIONAL_PASS, criteria
        else:
            return TestResult.FAIL, criteria
