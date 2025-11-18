"""
Outdoor Exposure Test Block (Session 24)

Implements field testing protocols, weather data integration, performance ratio
calculation, and degradation tracking for long-term PV module performance evaluation.
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
class WeatherData:
    """Weather measurement data"""
    timestamp: datetime
    irradiance_poa: float  # W/m² (Plane of Array)
    irradiance_ghi: float  # W/m² (Global Horizontal Irradiance)
    ambient_temperature: float  # °C
    module_temperature: float  # °C
    wind_speed: float  # m/s
    wind_direction: float  # degrees
    humidity: float  # %RH
    pressure: float  # hPa
    precipitation: float  # mm


@dataclass
class PerformanceData:
    """Module performance measurement"""
    timestamp: datetime
    power: float  # W
    voltage: float  # V
    current: float  # A
    energy: float  # Wh (integrated)
    irradiance: float  # W/m²
    module_temp: float  # °C


class WeatherStation(EquipmentInterface):
    """Weather station equipment interface"""

    def connect(self) -> bool:
        """Connect to weather station"""
        self.logger.info(f"Connecting to weather station {self.equipment_id}")
        self.connected = True
        return True

    def disconnect(self) -> bool:
        """Disconnect from weather station"""
        self.logger.info(f"Disconnecting weather station {self.equipment_id}")
        self.connected = False
        return True

    def initialize(self) -> bool:
        """Initialize weather station"""
        self.logger.info("Initializing weather station")
        return self.configure({
            'sampling_rate': 60,  # seconds
            'sensors': ['pyranometer', 'thermometer', 'anemometer', 'hygrometer']
        })

    def configure(self, settings: Dict[str, Any]) -> bool:
        """Configure weather station"""
        self.config.update(settings)
        return True

    def measure(self, parameter: str) -> MeasurementData:
        """Measure weather parameter"""
        # Stub: Simulate realistic outdoor weather
        value_map = {
            'irradiance_poa': max(0, 600 + np.random.normal(0, 100)),  # W/m²
            'irradiance_ghi': max(0, 550 + np.random.normal(0, 90)),  # W/m²
            'ambient_temperature': 25 + np.random.normal(0, 5),  # °C
            'wind_speed': max(0, 3 + np.random.exponential(2)),  # m/s
            'humidity': np.clip(50 + np.random.normal(0, 15), 10, 100),  # %RH
            'pressure': 1013 + np.random.normal(0, 5)  # hPa
        }

        value = value_map.get(parameter, 0.0)
        unit_map = {
            'irradiance_poa': 'W/m²',
            'irradiance_ghi': 'W/m²',
            'ambient_temperature': '°C',
            'wind_speed': 'm/s',
            'humidity': '%RH',
            'pressure': 'hPa'
        }

        return MeasurementData(
            timestamp=datetime.now(),
            value=value,
            unit=unit_map.get(parameter, ''),
            parameter_name=parameter,
            equipment_id=self.equipment_id,
            uncertainty=self.get_uncertainty(parameter, value)
        )

    def get_weather_data(self) -> WeatherData:
        """Get complete weather data snapshot"""
        poa = self.measure('irradiance_poa')
        ghi = self.measure('irradiance_ghi')
        ambient = self.measure('ambient_temperature')
        wind = self.measure('wind_speed')
        humid = self.measure('humidity')
        press = self.measure('pressure')

        # Calculate module temperature from ambient and irradiance
        module_temp = ambient.value + (poa.value / 1000) * 25  # NOCT approximation

        return WeatherData(
            timestamp=datetime.now(),
            irradiance_poa=poa.value,
            irradiance_ghi=ghi.value,
            ambient_temperature=ambient.value,
            module_temperature=module_temp,
            wind_speed=wind.value,
            wind_direction=np.random.uniform(0, 360),
            humidity=humid.value,
            pressure=press.value,
            precipitation=0.0
        )


class PowerMeter(EquipmentInterface):
    """Power meter for module performance monitoring"""

    def connect(self) -> bool:
        """Connect to power meter"""
        self.logger.info(f"Connecting to power meter {self.equipment_id}")
        self.connected = True
        return True

    def disconnect(self) -> bool:
        """Disconnect from power meter"""
        self.logger.info(f"Disconnecting power meter {self.equipment_id}")
        self.connected = False
        return True

    def initialize(self) -> bool:
        """Initialize power meter"""
        self.logger.info("Initializing power meter")
        return self.configure({
            'sampling_rate': 1,  # Hz
            'integration': True
        })

    def configure(self, settings: Dict[str, Any]) -> bool:
        """Configure power meter"""
        self.config.update(settings)
        return True

    def measure(self, parameter: str) -> MeasurementData:
        """Measure electrical parameter"""
        # Stub: Simulate module output
        value_map = {
            'power': max(0, 250 + np.random.normal(0, 20)),  # W
            'voltage': 35 + np.random.normal(0, 2),  # V
            'current': 7 + np.random.normal(0, 0.5),  # A
            'energy': 0.25  # Wh per second at 1 Hz
        }

        value = value_map.get(parameter, 0.0)
        unit_map = {
            'power': 'W',
            'voltage': 'V',
            'current': 'A',
            'energy': 'Wh'
        }

        return MeasurementData(
            timestamp=datetime.now(),
            value=value,
            unit=unit_map.get(parameter, ''),
            parameter_name=parameter,
            equipment_id=self.equipment_id
        )


class OutdoorExposureTest(BaseTestBlock):
    """
    Outdoor Exposure Test Block

    Monitors long-term outdoor performance of PV modules including
    performance ratio, degradation rate, and environmental correlation.
    """

    def __init__(
        self,
        test_id: str,
        operator: str,
        config: Dict[str, Any],
        weather_station: WeatherStation,
        power_meter: PowerMeter
    ):
        super().__init__(
            test_id=test_id,
            operator=operator,
            config=config,
            equipment=[weather_station, power_meter]
        )

        self.weather_station = weather_station
        self.power_meter = power_meter
        self.weather_data: List[WeatherData] = []
        self.performance_data: List[PerformanceData] = []

    def _initialize_parameters(self) -> None:
        """Initialize test parameters"""
        self.parameters = {
            'test_duration_days': TestParameter(
                name='test_duration_days',
                value=365,  # 1 year typical
                unit='days',
                description='Total outdoor exposure duration'
            ),
            'sampling_interval': TestParameter(
                name='sampling_interval',
                value=300,  # 5 minutes
                unit='s',
                description='Data sampling interval'
            ),
            'rated_power': TestParameter(
                name='rated_power',
                value=300,  # W
                unit='W',
                description='Module rated power at STC'
            ),
            'module_area': TestParameter(
                name='module_area',
                value=1.94,  # m²
                unit='m²',
                description='Module active area'
            ),
            'min_irradiance': TestParameter(
                name='min_irradiance',
                value=200,  # W/m²
                unit='W/m²',
                description='Minimum irradiance for PR calculation'
            ),
            'min_performance_ratio': TestParameter(
                name='min_performance_ratio',
                value=75.0,  # %
                unit='%',
                description='Minimum acceptable performance ratio'
            ),
            'max_degradation_rate': TestParameter(
                name='max_degradation_rate',
                value=0.5,  # % per year
                unit='%/year',
                description='Maximum acceptable degradation rate'
            )
        }

    def execute(self) -> TestBlockResult:
        """Execute outdoor exposure test"""
        self.start_time = datetime.now()
        self.logger.info(f"Starting outdoor exposure test {self.test_id}")

        try:
            # Validate equipment
            issues = self.validate_equipment()
            if issues:
                raise RuntimeError(f"Equipment validation failed: {', '.join(issues)}")

            # Initialize equipment
            self.weather_station.initialize()
            self.power_meter.initialize()

            # Collect data
            self.measurements = self._collect_data()

            # Analyze data
            self.analysis_results = self._analyze_data()

            # Check for anomalies
            self._detect_anomalies()

        except Exception as e:
            self.logger.error(f"Error during outdoor exposure test: {e}")
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
        """Collect outdoor performance and weather data"""
        self.logger.info("Collecting outdoor exposure data...")

        measurements = []
        sampling_interval = self.parameters['sampling_interval'].value

        # Simulate data collection over test period
        # For demo: collect 100 data points instead of full duration
        num_samples = 100
        test_duration_days = self.parameters['test_duration_days'].value

        self.logger.info(f"Simulating {test_duration_days} days with {num_samples} samples")

        for i in range(num_samples):
            # Simulate time progression
            elapsed_days = (i / num_samples) * test_duration_days
            timestamp = self.start_time + timedelta(days=elapsed_days)

            # Get weather data
            weather = self.weather_station.get_weather_data()
            weather.timestamp = timestamp
            self.weather_data.append(weather)

            # Record weather measurements
            measurements.append(MeasurementData(
                timestamp=timestamp,
                value=weather.irradiance_poa,
                unit='W/m²',
                parameter_name='irradiance_poa',
                equipment_id=self.weather_station.equipment_id
            ))

            measurements.append(MeasurementData(
                timestamp=timestamp,
                value=weather.module_temperature,
                unit='°C',
                parameter_name='module_temperature',
                equipment_id=self.weather_station.equipment_id
            ))

            # Get performance data (only when sufficient irradiance)
            if weather.irradiance_poa >= self.parameters['min_irradiance'].value:
                power_meas = self.power_meter.measure('power')
                voltage_meas = self.power_meter.measure('voltage')
                current_meas = self.power_meter.measure('current')

                # Apply degradation over time (simulate realistic degradation)
                degradation_factor = 1.0 - (elapsed_days / 365) * 0.005  # 0.5% per year

                performance = PerformanceData(
                    timestamp=timestamp,
                    power=power_meas.value * degradation_factor,
                    voltage=voltage_meas.value,
                    current=current_meas.value,
                    energy=power_meas.value * degradation_factor * (sampling_interval / 3600),  # Wh
                    irradiance=weather.irradiance_poa,
                    module_temp=weather.module_temperature
                )
                self.performance_data.append(performance)

                measurements.append(MeasurementData(
                    timestamp=timestamp,
                    value=performance.power,
                    unit='W',
                    parameter_name='power',
                    equipment_id=self.power_meter.equipment_id,
                    metadata={'irradiance': weather.irradiance_poa}
                ))

        self.logger.info(
            f"Collected {len(self.weather_data)} weather records and "
            f"{len(self.performance_data)} performance records"
        )

        return measurements

    def _analyze_data(self) -> Dict[str, Any]:
        """Analyze outdoor exposure data"""
        self.logger.info("Analyzing outdoor exposure data...")

        if not self.performance_data or not self.weather_data:
            return {'error': 'Insufficient data'}

        # Calculate performance ratio
        pr_analysis = self._calculate_performance_ratio()

        # Calculate degradation rate
        degradation_analysis = self._calculate_degradation_rate()

        # Calculate energy yield
        energy_yield = self._calculate_energy_yield()

        # Analyze environmental correlations
        environmental_analysis = self._analyze_environmental_factors()

        # Calculate availability
        availability = self._calculate_availability()

        # Temperature coefficient analysis
        temp_coeff = self._analyze_temperature_coefficient()

        return {
            'performance_ratio': pr_analysis,
            'degradation': degradation_analysis,
            'energy_yield': energy_yield,
            'environmental_factors': environmental_analysis,
            'availability': availability,
            'temperature_coefficient': temp_coeff,
            'test_duration_days': (self.weather_data[-1].timestamp - self.weather_data[0].timestamp).days,
            'total_samples': len(self.performance_data)
        }

    def _calculate_performance_ratio(self) -> Dict[str, float]:
        """
        Calculate Performance Ratio (PR)

        PR = (Actual Energy / Expected Energy) * 100%
        Expected Energy = Rated Power * Irradiance / 1000
        """
        if not self.performance_data:
            return {}

        pr_values = []
        rated_power = self.parameters['rated_power'].value

        for perf in self.performance_data:
            # Expected power at current irradiance
            expected_power = rated_power * (perf.irradiance / 1000.0)

            if expected_power > 0:
                pr = (perf.power / expected_power) * 100
                pr_values.append(pr)

        if not pr_values:
            return {}

        pr_array = np.array(pr_values)

        return {
            'mean_pr': float(np.mean(pr_array)),
            'median_pr': float(np.median(pr_array)),
            'std_pr': float(np.std(pr_array, ddof=1)) if len(pr_array) > 1 else 0.0,
            'min_pr': float(np.min(pr_array)),
            'max_pr': float(np.max(pr_array)),
            'pr_values_count': len(pr_values)
        }

    def _calculate_degradation_rate(self) -> Dict[str, Any]:
        """
        Calculate power degradation rate over time

        Uses linear regression of normalized power over time
        """
        if len(self.performance_data) < 10:
            return {'status': 'insufficient_data'}

        # Normalize power to irradiance (W/m²)
        times = np.array([(p.timestamp - self.performance_data[0].timestamp).days
                         for p in self.performance_data])
        normalized_powers = np.array([p.power / (p.irradiance / 1000.0)
                                     for p in self.performance_data])

        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(times, normalized_powers)

        # Calculate degradation rate (% per year)
        initial_power = intercept
        degradation_rate_per_day = slope / initial_power * 100 if initial_power > 0 else 0
        degradation_rate_per_year = degradation_rate_per_day * 365

        return {
            'degradation_rate_per_year': float(degradation_rate_per_year),
            'degradation_rate_per_day': float(degradation_rate_per_day),
            'r_squared': float(r_value ** 2),
            'p_value': float(p_value),
            'confidence_interval_95': float(1.96 * std_err * 365),  # Annual CI
            'statistically_significant': p_value < 0.05,
            'initial_power': float(initial_power),
            'final_power': float(slope * times[-1] + intercept)
        }

    def _calculate_energy_yield(self) -> Dict[str, float]:
        """Calculate total and specific energy yield"""
        if not self.performance_data:
            return {}

        # Total energy (Wh)
        total_energy = sum(p.energy for p in self.performance_data)

        # Duration in years
        duration_days = (self.performance_data[-1].timestamp -
                        self.performance_data[0].timestamp).days
        duration_years = duration_days / 365.0

        # Specific yield (kWh/kWp/year)
        rated_power_kw = self.parameters['rated_power'].value / 1000.0
        specific_yield = (total_energy / 1000.0) / (rated_power_kw * duration_years) if duration_years > 0 else 0

        # Total irradiation (kWh/m²)
        total_irradiation = sum(w.irradiance_poa for w in self.weather_data) * \
                          (self.parameters['sampling_interval'].value / 3600.0) / 1000.0

        return {
            'total_energy_kwh': total_energy / 1000.0,
            'specific_yield_kwh_per_kwp_year': float(specific_yield),
            'total_irradiation_kwh_per_m2': float(total_irradiation),
            'duration_days': duration_days
        }

    def _analyze_environmental_factors(self) -> Dict[str, Any]:
        """Analyze correlation between performance and environmental factors"""
        if not self.performance_data or not self.weather_data:
            return {}

        # Match performance and weather data by timestamp
        powers = np.array([p.power for p in self.performance_data])
        temps = np.array([p.module_temp for p in self.performance_data])
        irradiances = np.array([p.irradiance for p in self.performance_data])

        # Correlation analysis
        temp_corr = np.corrcoef(temps, powers)[0, 1] if len(temps) > 1 else 0.0
        irr_corr = np.corrcoef(irradiances, powers)[0, 1] if len(irradiances) > 1 else 0.0

        return {
            'temperature_correlation': float(temp_corr),
            'irradiance_correlation': float(irr_corr),
            'mean_irradiance': float(np.mean(irradiances)),
            'mean_module_temperature': float(np.mean(temps)),
            'max_module_temperature': float(np.max(temps))
        }

    def _calculate_availability(self) -> Dict[str, float]:
        """Calculate system availability"""
        # Total possible measurement periods
        total_duration = (self.weather_data[-1].timestamp -
                         self.weather_data[0].timestamp).total_seconds()
        expected_samples = total_duration / self.parameters['sampling_interval'].value

        actual_samples = len(self.weather_data)

        availability = (actual_samples / expected_samples * 100) if expected_samples > 0 else 0

        return {
            'availability_percent': float(availability),
            'actual_samples': actual_samples,
            'expected_samples': int(expected_samples)
        }

    def _analyze_temperature_coefficient(self) -> Dict[str, float]:
        """Analyze temperature coefficient of power"""
        if len(self.performance_data) < 10:
            return {}

        # Normalize power to 1000 W/m²
        normalized_powers = []
        module_temps = []

        for perf in self.performance_data:
            if perf.irradiance > 700:  # Only use high irradiance data
                normalized_power = perf.power * (1000.0 / perf.irradiance)
                normalized_powers.append(normalized_power)
                module_temps.append(perf.module_temp)

        if len(normalized_powers) < 10:
            return {}

        # Linear regression: Power vs Temperature
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            module_temps, normalized_powers
        )

        # Temperature coefficient (%/°C)
        power_at_25c = slope * 25 + intercept
        temp_coeff = (slope / power_at_25c * 100) if power_at_25c > 0 else 0

        return {
            'temperature_coefficient_pct_per_c': float(temp_coeff),
            'r_squared': float(r_value ** 2),
            'power_at_25c': float(power_at_25c)
        }

    def _detect_anomalies(self) -> None:
        """Detect anomalies in outdoor exposure data"""
        # Check performance ratio
        pr_analysis = self.analysis_results.get('performance_ratio', {})
        mean_pr = pr_analysis.get('mean_pr', 0)
        min_pr = self.parameters['min_performance_ratio'].value

        if mean_pr < min_pr:
            self.log_anomaly(
                f"Low performance ratio: {mean_pr:.2f}% (min: {min_pr}%)"
            )

        # Check degradation rate
        degradation = self.analysis_results.get('degradation', {})
        deg_rate = degradation.get('degradation_rate_per_year', 0)
        max_deg_rate = self.parameters['max_degradation_rate'].value

        if abs(deg_rate) > max_deg_rate:
            self.log_anomaly(
                f"High degradation rate: {deg_rate:.3f}%/year (max: {max_deg_rate}%/year)"
            )

        # Check for availability issues
        availability_data = self.analysis_results.get('availability', {})
        availability = availability_data.get('availability_percent', 0)

        if availability < 95:
            self.log_anomaly(
                f"Low data availability: {availability:.1f}%"
            )

        # Check for extreme temperatures
        env_factors = self.analysis_results.get('environmental_factors', {})
        max_temp = env_factors.get('max_module_temperature', 0)

        if max_temp > 85:
            self.log_anomaly(
                f"Extreme module temperature recorded: {max_temp:.1f}°C"
            )

    def _determine_pass_fail(self) -> Tuple[TestResult, Dict[str, bool]]:
        """Determine pass/fail status"""
        criteria = {}

        # Performance ratio criterion
        pr_analysis = self.analysis_results.get('performance_ratio', {})
        mean_pr = pr_analysis.get('mean_pr', 0)
        criteria['performance_ratio'] = mean_pr >= self.parameters['min_performance_ratio'].value

        # Degradation rate criterion
        degradation = self.analysis_results.get('degradation', {})
        deg_rate = abs(degradation.get('degradation_rate_per_year', 999))
        criteria['degradation_rate'] = deg_rate <= self.parameters['max_degradation_rate'].value

        # Data quality criterion
        availability_data = self.analysis_results.get('availability', {})
        availability = availability_data.get('availability_percent', 0)
        criteria['data_availability'] = availability >= 95.0

        # Statistical significance criterion (for degradation)
        criteria['degradation_significant'] = degradation.get('statistically_significant', False)

        # Overall result
        all_pass = all(criteria.values())
        critical_pass = criteria.get('performance_ratio', False) and criteria.get('data_availability', False)

        if all_pass:
            return TestResult.PASS, criteria
        elif critical_pass:
            return TestResult.CONDITIONAL_PASS, criteria
        else:
            return TestResult.FAIL, criteria
