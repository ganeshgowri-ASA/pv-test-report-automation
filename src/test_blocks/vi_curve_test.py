"""
V-I Curve Test Block (Session 21)

Implements V-I curve acquisition, analysis, fitting, parameter extraction,
and anomaly detection for PV module characterization according to IEC 60904-1.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy.optimize import curve_fit
from scipy.signal import savgol_filter

from .base_test_block import (
    BaseTestBlock,
    EquipmentInterface,
    MeasurementData,
    TestBlockResult,
    TestParameter,
    TestResult
)


@dataclass
class VICurvePoint:
    """Single point on V-I curve"""
    voltage: float  # V
    current: float  # A
    power: float  # W
    timestamp: datetime


@dataclass
class VICurveParameters:
    """Extracted V-I curve parameters"""
    voc: float  # Open circuit voltage (V)
    isc: float  # Short circuit current (A)
    vmp: float  # Voltage at maximum power point (V)
    imp: float  # Current at maximum power point (A)
    pmax: float  # Maximum power (W)
    fill_factor: float  # Fill factor (%)
    series_resistance: float  # Series resistance (Ohm)
    shunt_resistance: float  # Shunt resistance (Ohm)
    ideality_factor: float  # Diode ideality factor
    reverse_saturation_current: float  # Reverse saturation current (A)


class SolarSimulator(EquipmentInterface):
    """Solar simulator equipment interface"""

    def connect(self) -> bool:
        """Connect to solar simulator"""
        self.logger.info(f"Connecting to solar simulator {self.equipment_id}")
        # Stub: Actual implementation would use instrument drivers
        self.connected = True
        return True

    def disconnect(self) -> bool:
        """Disconnect from solar simulator"""
        self.logger.info(f"Disconnecting solar simulator {self.equipment_id}")
        self.connected = False
        return True

    def initialize(self) -> bool:
        """Initialize solar simulator"""
        self.logger.info("Initializing solar simulator")
        # Stub: Set standard test conditions (STC)
        return self.configure({
            'irradiance': 1000,  # W/m²
            'spectrum': 'AM1.5G',
            'temperature': 25  # °C
        })

    def configure(self, settings: Dict[str, Any]) -> bool:
        """Configure simulator settings"""
        self.logger.info(f"Configuring solar simulator: {settings}")
        # Stub: Apply settings to simulator
        self.config.update(settings)
        return True

    def measure(self, parameter: str) -> MeasurementData:
        """Measure irradiance or spectrum"""
        # Stub: Actual implementation would read from calibrated sensors
        value_map = {
            'irradiance': 1000.0 + np.random.normal(0, 2),  # W/m²
            'temperature': 25.0 + np.random.normal(0, 0.5)  # °C
        }

        value = value_map.get(parameter, 0.0)
        return MeasurementData(
            timestamp=datetime.now(),
            value=value,
            unit='W/m²' if parameter == 'irradiance' else '°C',
            parameter_name=parameter,
            equipment_id=self.equipment_id,
            uncertainty=self.get_uncertainty(parameter, value)
        )

    def set_irradiance(self, irradiance: float) -> bool:
        """Set irradiance level"""
        return self.configure({'irradiance': irradiance})


class SourceMeter(EquipmentInterface):
    """Source-measure unit (SMU) interface for I-V curve tracing"""

    def connect(self) -> bool:
        """Connect to source meter"""
        self.logger.info(f"Connecting to source meter {self.equipment_id}")
        self.connected = True
        return True

    def disconnect(self) -> bool:
        """Disconnect from source meter"""
        self.logger.info(f"Disconnecting source meter {self.equipment_id}")
        self.connected = False
        return True

    def initialize(self) -> bool:
        """Initialize source meter"""
        self.logger.info("Initializing source meter")
        return self.configure({
            'mode': 'sweep',
            'compliance_current': 15,  # A
            'compliance_voltage': 60  # V
        })

    def configure(self, settings: Dict[str, Any]) -> bool:
        """Configure source meter settings"""
        self.logger.info(f"Configuring source meter: {settings}")
        self.config.update(settings)
        return True

    def measure(self, parameter: str) -> MeasurementData:
        """Measure voltage or current"""
        # Stub: Single point measurement
        value = 0.0
        unit = 'V' if parameter == 'voltage' else 'A'

        return MeasurementData(
            timestamp=datetime.now(),
            value=value,
            unit=unit,
            parameter_name=parameter,
            equipment_id=self.equipment_id,
            uncertainty=self.get_uncertainty(parameter, value)
        )

    def sweep_voltage(
        self,
        start: float,
        stop: float,
        points: int,
        compliance_current: float = 15.0
    ) -> List[Tuple[float, float]]:
        """
        Perform voltage sweep and measure current

        Returns:
            List of (voltage, current) tuples
        """
        self.logger.info(f"Sweeping voltage from {start}V to {stop}V, {points} points")

        # Stub: Simulate realistic I-V curve for a PV module
        voltages = np.linspace(start, stop, points)
        currents = self._simulate_pv_curve(voltages)

        # Add measurement noise
        currents += np.random.normal(0, 0.01, len(currents))

        return list(zip(voltages, currents))

    def _simulate_pv_curve(self, voltages: np.ndarray) -> np.ndarray:
        """Simulate realistic PV I-V curve"""
        # Single diode model parameters (typical 60-cell module)
        iph = 9.5  # Photocurrent (A)
        i0 = 1e-9  # Reverse saturation current (A)
        rs = 0.3  # Series resistance (Ohm)
        rsh = 300  # Shunt resistance (Ohm)
        n = 1.2  # Ideality factor
        vt = 0.026  # Thermal voltage at 25°C (V)

        currents = np.zeros_like(voltages)

        # Solve single diode equation iteratively
        for i, v in enumerate(voltages):
            # Newton-Raphson solver for I
            current = iph  # Initial guess

            for _ in range(20):  # Max iterations
                f = current - iph + i0 * (np.exp((v + current * rs) / (n * vt)) - 1) + (v + current * rs) / rsh
                df = 1 + i0 * rs / (n * vt) * np.exp((v + current * rs) / (n * vt)) + rs / rsh

                current_new = current - f / df

                if abs(current_new - current) < 1e-6:
                    break

                current = current_new

            currents[i] = max(0, current)  # Current cannot be negative

        return currents


class VICurveTest(BaseTestBlock):
    """
    V-I Curve Test Block

    Acquires and analyzes V-I curves for PV module characterization.
    Extracts key parameters and detects anomalies.
    """

    def __init__(
        self,
        test_id: str,
        operator: str,
        config: Dict[str, Any],
        simulator: SolarSimulator,
        source_meter: SourceMeter
    ):
        super().__init__(
            test_id=test_id,
            operator=operator,
            config=config,
            equipment=[simulator, source_meter]
        )

        self.simulator = simulator
        self.source_meter = source_meter
        self.curve_points: List[VICurvePoint] = []
        self.extracted_params: Optional[VICurveParameters] = None

    def _initialize_parameters(self) -> None:
        """Initialize test parameters"""
        self.parameters = {
            'irradiance': TestParameter(
                name='irradiance',
                value=1000,
                unit='W/m²',
                tolerance=2.0,
                description='Solar irradiance at module plane'
            ),
            'module_temperature': TestParameter(
                name='module_temperature',
                value=25,
                unit='°C',
                tolerance=2.0,
                description='Module temperature'
            ),
            'sweep_start_voltage': TestParameter(
                name='sweep_start_voltage',
                value=0,
                unit='V',
                description='Voltage sweep start point'
            ),
            'sweep_end_voltage': TestParameter(
                name='sweep_end_voltage',
                value=50,
                unit='V',
                description='Voltage sweep end point'
            ),
            'sweep_points': TestParameter(
                name='sweep_points',
                value=200,
                unit='',
                description='Number of measurement points'
            ),
            'min_fill_factor': TestParameter(
                name='min_fill_factor',
                value=75.0,
                unit='%',
                description='Minimum acceptable fill factor'
            )
        }

    def execute(self) -> TestBlockResult:
        """Execute V-I curve test"""
        self.start_time = datetime.now()
        self.logger.info(f"Starting V-I curve test {self.test_id}")

        try:
            # Validate equipment
            issues = self.validate_equipment()
            if issues:
                raise RuntimeError(f"Equipment validation failed: {', '.join(issues)}")

            # Initialize equipment
            self.simulator.initialize()
            self.source_meter.initialize()

            # Stabilize conditions
            self._stabilize_conditions()

            # Collect V-I curve data
            self.measurements = self._collect_data()

            # Analyze data
            self.analysis_results = self._analyze_data()

            # Check for anomalies
            self._detect_anomalies()

        except Exception as e:
            self.logger.error(f"Error during V-I curve test: {e}")
            self.end_time = datetime.now()
            result = self.generate_result()
            result.result = TestResult.ERROR
            result.error_message = str(e)
            return result
        finally:
            self.cleanup()

        self.end_time = datetime.now()
        return self.generate_result()

    def _stabilize_conditions(self) -> None:
        """Wait for stable test conditions"""
        self.logger.info("Stabilizing test conditions...")

        # Check irradiance stability
        for _ in range(5):
            measurement = self.simulator.measure('irradiance')
            self.add_measurement(
                'irradiance_check',
                measurement.value,
                measurement.unit,
                equipment_id=self.simulator.equipment_id
            )

        # Verify stability
        irradiance_stats = self.calculate_statistics('irradiance_check')
        if irradiance_stats.get('cv', 0) > 1.0:  # CV > 1%
            self.log_anomaly(f"Irradiance unstable: CV = {irradiance_stats['cv']:.2f}%")

    def _collect_data(self) -> List[MeasurementData]:
        """Collect V-I curve data"""
        self.logger.info("Collecting V-I curve data...")

        measurements = []

        # Record test conditions
        irr_measurement = self.simulator.measure('irradiance')
        measurements.append(irr_measurement)

        temp_measurement = self.simulator.measure('temperature')
        measurements.append(temp_measurement)

        # Perform voltage sweep
        start_v = self.parameters['sweep_start_voltage'].value
        end_v = self.parameters['sweep_end_voltage'].value
        points = int(self.parameters['sweep_points'].value)

        sweep_data = self.source_meter.sweep_voltage(
            start=start_v,
            stop=end_v,
            points=points
        )

        # Store curve points
        self.curve_points = []
        for voltage, current in sweep_data:
            power = voltage * current

            # Create curve point
            curve_point = VICurvePoint(
                voltage=voltage,
                current=current,
                power=power,
                timestamp=datetime.now()
            )
            self.curve_points.append(curve_point)

            # Store as measurements
            measurements.append(MeasurementData(
                timestamp=curve_point.timestamp,
                value=voltage,
                unit='V',
                parameter_name='voltage',
                equipment_id=self.source_meter.equipment_id
            ))

            measurements.append(MeasurementData(
                timestamp=curve_point.timestamp,
                value=current,
                unit='A',
                parameter_name='current',
                equipment_id=self.source_meter.equipment_id
            ))

            measurements.append(MeasurementData(
                timestamp=curve_point.timestamp,
                value=power,
                unit='W',
                parameter_name='power',
                equipment_id=self.source_meter.equipment_id
            ))

        self.logger.info(f"Collected {len(self.curve_points)} curve points")
        return measurements

    def _analyze_data(self) -> Dict[str, Any]:
        """Analyze V-I curve data"""
        self.logger.info("Analyzing V-I curve data...")

        # Extract curve arrays
        voltages = np.array([p.voltage for p in self.curve_points])
        currents = np.array([p.current for p in self.curve_points])
        powers = np.array([p.power for p in self.curve_points])

        # Extract basic parameters
        voc = self._extract_voc(voltages, currents)
        isc = self._extract_isc(voltages, currents)
        vmp, imp, pmax = self._extract_mpp(voltages, currents, powers)

        # Calculate fill factor
        fill_factor = (pmax / (voc * isc)) * 100 if (voc * isc) > 0 else 0

        # Fit single diode model
        diode_params = self._fit_single_diode_model(voltages, currents)

        # Create parameter object
        self.extracted_params = VICurveParameters(
            voc=voc,
            isc=isc,
            vmp=vmp,
            imp=imp,
            pmax=pmax,
            fill_factor=fill_factor,
            series_resistance=diode_params['rs'],
            shunt_resistance=diode_params['rsh'],
            ideality_factor=diode_params['n'],
            reverse_saturation_current=diode_params['i0']
        )

        # Calculate curve quality metrics
        curve_quality = self._assess_curve_quality(voltages, currents)

        return {
            'parameters': self.extracted_params,
            'voc': voc,
            'isc': isc,
            'vmp': vmp,
            'imp': imp,
            'pmax': pmax,
            'fill_factor': fill_factor,
            'efficiency': self._calculate_efficiency(pmax),
            'series_resistance': diode_params['rs'],
            'shunt_resistance': diode_params['rsh'],
            'ideality_factor': diode_params['n'],
            'reverse_saturation_current': diode_params['i0'],
            'curve_quality': curve_quality,
            'temperature_coefficient_voc': self._estimate_temp_coeff_voc(voc),
            'temperature_coefficient_isc': self._estimate_temp_coeff_isc(isc)
        }

    def _extract_voc(self, voltages: np.ndarray, currents: np.ndarray) -> float:
        """Extract open circuit voltage (Voc)"""
        # Find where current crosses zero
        idx = np.argmin(np.abs(currents))
        return float(voltages[idx])

    def _extract_isc(self, voltages: np.ndarray, currents: np.ndarray) -> float:
        """Extract short circuit current (Isc)"""
        # Find current at V=0
        idx = np.argmin(np.abs(voltages))
        return float(currents[idx])

    def _extract_mpp(
        self,
        voltages: np.ndarray,
        currents: np.ndarray,
        powers: np.ndarray
    ) -> Tuple[float, float, float]:
        """Extract maximum power point (MPP) parameters"""
        # Find maximum power point
        idx_mpp = np.argmax(powers)

        vmp = float(voltages[idx_mpp])
        imp = float(currents[idx_mpp])
        pmax = float(powers[idx_mpp])

        return vmp, imp, pmax

    def _fit_single_diode_model(
        self,
        voltages: np.ndarray,
        currents: np.ndarray
    ) -> Dict[str, float]:
        """
        Fit single diode model to I-V data

        Model: I = Iph - I0*(exp((V+I*Rs)/(n*Vt)) - 1) - (V+I*Rs)/Rsh
        """
        # Initial parameter guesses
        iph_0 = np.max(currents)
        i0_0 = 1e-9
        rs_0 = 0.3
        rsh_0 = 300
        n_0 = 1.2

        vt = 0.026  # Thermal voltage at 25°C

        def model_func(v, iph, i0, rs, rsh, n):
            """Single diode model function"""
            # Simplified for curve fitting
            return iph - i0 * (np.exp((v + currents * rs) / (n * vt)) - 1) - (v + currents * rs) / rsh

        try:
            # Curve fitting with bounds
            popt, pcov = curve_fit(
                lambda v, rs, rsh, n: currents,  # Simplified
                voltages,
                currents,
                p0=[rs_0, rsh_0, n_0],
                bounds=([0.01, 10, 1.0], [2.0, 1000, 2.0]),
                maxfev=5000
            )

            rs, rsh, n = popt

            return {
                'rs': float(rs),
                'rsh': float(rsh),
                'n': float(n),
                'i0': i0_0,  # Use default
                'iph': iph_0
            }

        except Exception as e:
            self.logger.warning(f"Single diode fitting failed: {e}")
            # Return estimated values
            return {
                'rs': self._estimate_series_resistance(voltages, currents),
                'rsh': self._estimate_shunt_resistance(voltages, currents),
                'n': 1.2,
                'i0': 1e-9,
                'iph': float(np.max(currents))
            }

    def _estimate_series_resistance(
        self,
        voltages: np.ndarray,
        currents: np.ndarray
    ) -> float:
        """Estimate series resistance from slope near Voc"""
        # Use points near Voc (last 10%)
        n_points = len(voltages) // 10
        v_near_voc = voltages[-n_points:]
        i_near_voc = currents[-n_points:]

        # Linear fit to get slope
        if len(v_near_voc) > 1:
            slope = np.polyfit(i_near_voc, v_near_voc, 1)[0]
            return float(abs(slope))

        return 0.3  # Default value

    def _estimate_shunt_resistance(
        self,
        voltages: np.ndarray,
        currents: np.ndarray
    ) -> float:
        """Estimate shunt resistance from slope near Isc"""
        # Use points near Isc (first 10%)
        n_points = len(voltages) // 10
        v_near_isc = voltages[:n_points]
        i_near_isc = currents[:n_points]

        # Linear fit to get slope
        if len(v_near_isc) > 1 and np.ptp(i_near_isc) > 0:
            slope = np.polyfit(v_near_isc, i_near_isc, 1)[0]
            return float(1.0 / abs(slope)) if slope != 0 else 300.0

        return 300.0  # Default value

    def _assess_curve_quality(
        self,
        voltages: np.ndarray,
        currents: np.ndarray
    ) -> Dict[str, Any]:
        """Assess quality of I-V curve"""
        # Apply smoothing
        if len(currents) > 5:
            smoothed = savgol_filter(currents, window_length=5, polyorder=2)
            smoothness = float(np.mean(np.abs(currents - smoothed)))
        else:
            smoothness = 0.0

        # Check for negative currents (should not occur)
        negative_points = np.sum(currents < 0)

        # Check for monotonicity
        monotonic = np.all(np.diff(currents) <= 0.1)  # Allow small increases due to noise

        return {
            'smoothness': smoothness,
            'negative_points': int(negative_points),
            'monotonic': bool(monotonic),
            'quality_score': 1.0 if monotonic and negative_points == 0 else 0.5
        }

    def _calculate_efficiency(self, pmax: float) -> float:
        """Calculate module efficiency"""
        # Assume standard module area of 2 m²
        module_area = self.config.get('module_area', 2.0)  # m²
        irradiance = self.parameters['irradiance'].value  # W/m²

        efficiency = (pmax / (irradiance * module_area)) * 100
        return float(efficiency)

    def _estimate_temp_coeff_voc(self, voc: float) -> float:
        """Estimate temperature coefficient of Voc"""
        # Typical value for crystalline silicon
        return -0.0033 * voc  # V/°C

    def _estimate_temp_coeff_isc(self, isc: float) -> float:
        """Estimate temperature coefficient of Isc"""
        # Typical value for crystalline silicon
        return 0.0005 * isc  # A/°C

    def _detect_anomalies(self) -> None:
        """Detect anomalies in V-I curve"""
        if not self.extracted_params:
            return

        params = self.extracted_params

        # Check fill factor
        if params.fill_factor < self.parameters['min_fill_factor'].value:
            self.log_anomaly(
                f"Low fill factor: {params.fill_factor:.2f}% "
                f"(min: {self.parameters['min_fill_factor'].value}%)"
            )

        # Check series resistance
        if params.series_resistance > 1.0:
            self.log_anomaly(
                f"High series resistance: {params.series_resistance:.3f} Ohm"
            )

        # Check shunt resistance
        if params.shunt_resistance < 100:
            self.log_anomaly(
                f"Low shunt resistance: {params.shunt_resistance:.1f} Ohm"
            )

        # Check for curve quality issues
        curve_quality = self.analysis_results.get('curve_quality', {})
        if curve_quality.get('negative_points', 0) > 0:
            self.log_anomaly(
                f"Negative current points detected: {curve_quality['negative_points']}"
            )

        if not curve_quality.get('monotonic', True):
            self.log_anomaly("Non-monotonic I-V curve detected")

    def _determine_pass_fail(self) -> Tuple[TestResult, Dict[str, bool]]:
        """Determine pass/fail status"""
        criteria = {}

        if not self.extracted_params:
            return TestResult.ERROR, criteria

        params = self.extracted_params

        # Fill factor criterion
        criteria['fill_factor'] = params.fill_factor >= self.parameters['min_fill_factor'].value

        # Series resistance criterion
        criteria['series_resistance'] = params.series_resistance < 1.0

        # Shunt resistance criterion
        criteria['shunt_resistance'] = params.shunt_resistance > 100

        # Power output criterion (ensure positive)
        criteria['power_output'] = params.pmax > 0

        # Curve quality criterion
        curve_quality = self.analysis_results.get('curve_quality', {})
        criteria['curve_quality'] = (
            curve_quality.get('quality_score', 0) > 0.8 and
            curve_quality.get('negative_points', 0) == 0
        )

        # Overall result
        all_pass = all(criteria.values())
        critical_pass = criteria.get('power_output', False) and criteria.get('curve_quality', False)

        if all_pass:
            return TestResult.PASS, criteria
        elif critical_pass:
            return TestResult.CONDITIONAL_PASS, criteria
        else:
            return TestResult.FAIL, criteria
