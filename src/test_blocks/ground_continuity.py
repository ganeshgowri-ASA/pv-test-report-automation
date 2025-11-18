"""
Ground Continuity Test Block (Session 27)

Implements ground continuity test (GCT), resistance measurement, and grounding
verification for PV module safety according to IEC 61730-2.
"""

from dataclasses import dataclass
from datetime import datetime
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
class GCTMeasurement:
    """Ground continuity test measurement"""
    timestamp: datetime
    resistance: float  # Ohm
    test_current: float  # A
    voltage_drop: float  # V
    test_points: Tuple[str, str]  # (point1, point2)
    contact_resistance: float  # Ohm (estimated)


class GroundContinuityTester(EquipmentInterface):
    """Ground continuity/bond tester equipment interface"""

    def connect(self) -> bool:
        """Connect to ground continuity tester"""
        self.logger.info(f"Connecting to ground continuity tester {self.equipment_id}")
        self.connected = True
        return True

    def disconnect(self) -> bool:
        """Disconnect from ground continuity tester"""
        self.logger.info(f"Disconnecting ground continuity tester {self.equipment_id}")
        self.connected = False
        return True

    def initialize(self) -> bool:
        """Initialize ground continuity tester"""
        self.logger.info("Initializing ground continuity tester")
        return self.configure({
            'test_current': 25,  # A (typical: 25A for 1 minute per IEC 61730-2)
            'measurement_method': '4-wire',  # Kelvin measurement
            'resolution': 0.001,  # 1 mΩ
            'auto_zero': True
        })

    def configure(self, settings: Dict[str, Any]) -> bool:
        """Configure tester settings"""
        self.config.update(settings)
        return True

    def measure(self, parameter: str) -> MeasurementData:
        """Measure parameter"""
        # Stub: Simulate measurement
        value_map = {
            'resistance': max(0.001, np.random.normal(0.05, 0.01)),  # ~50 mΩ typical
            'current': self.config.get('test_current', 25.0),
            'voltage': 0.0
        }

        value = value_map.get(parameter, 0.0)
        unit_map = {
            'resistance': 'Ohm',
            'current': 'A',
            'voltage': 'V'
        }

        return MeasurementData(
            timestamp=datetime.now(),
            value=value,
            unit=unit_map.get(parameter, ''),
            parameter_name=parameter,
            equipment_id=self.equipment_id,
            uncertainty=self.get_uncertainty(parameter, value)
        )

    def measure_resistance(
        self,
        test_current: float,
        duration: float = 60.0
    ) -> Tuple[float, float, List[float]]:
        """
        Measure ground continuity resistance

        Args:
            test_current: Test current in A
            duration: Test duration in seconds

        Returns:
            Tuple of (resistance, voltage_drop, resistance_samples)
        """
        self.logger.info(f"Measuring ground resistance at {test_current}A for {duration}s")

        # Stub: Simulate 4-wire resistance measurement
        # Typical good ground path: 30-100 mΩ
        base_resistance = 0.05 + np.random.normal(0, 0.01)  # 50 mΩ ± 10 mΩ

        # Simulate multiple measurements during test
        num_samples = 10
        resistance_samples = []

        for _ in range(num_samples):
            # Add slight variation and heating effect
            sample = base_resistance + np.random.normal(0, 0.002)  # ±2 mΩ noise
            resistance_samples.append(max(0.001, sample))

        # Calculate average resistance
        resistance = float(np.mean(resistance_samples))

        # Calculate voltage drop (V = I × R)
        voltage_drop = test_current * resistance

        return resistance, voltage_drop, resistance_samples

    def perform_contact_check(self) -> Tuple[bool, float]:
        """
        Check test probe contact quality

        Returns:
            Tuple of (good_contact, contact_resistance)
        """
        # Measure with low current to check contact
        contact_resistance = max(0, np.random.normal(0.010, 0.005))  # ~10 mΩ typical

        # Good contact: < 50 mΩ
        good_contact = contact_resistance < 0.050

        return good_contact, contact_resistance


class GroundContinuityTest(BaseTestBlock):
    """
    Ground Continuity Test Block

    Verifies electrical continuity of grounding/bonding paths in PV modules
    to ensure safety in fault conditions.
    """

    def __init__(
        self,
        test_id: str,
        operator: str,
        config: Dict[str, Any],
        continuity_tester: GroundContinuityTester
    ):
        super().__init__(
            test_id=test_id,
            operator=operator,
            config=config,
            equipment=[continuity_tester]
        )

        self.continuity_tester = continuity_tester
        self.gct_measurements: List[GCTMeasurement] = []

    def _initialize_parameters(self) -> None:
        """Initialize test parameters"""
        self.parameters = {
            'test_current': TestParameter(
                name='test_current',
                value=25,  # A
                unit='A',
                description='Test current (IEC 61730-2: 25A for 1 min)'
            ),
            'test_duration': TestParameter(
                name='test_duration',
                value=60,  # seconds
                unit='s',
                description='Test current application duration'
            ),
            'max_resistance': TestParameter(
                name='max_resistance',
                value=0.1,  # Ohm (100 mΩ)
                unit='Ohm',
                description='Maximum acceptable ground resistance'
            ),
            'max_voltage_drop': TestParameter(
                name='max_voltage_drop',
                value=2.5,  # V (at 25A)
                unit='V',
                description='Maximum voltage drop during test'
            ),
            'test_paths': TestParameter(
                name='test_paths',
                value=[
                    ('frame_corner_1', 'frame_corner_2'),
                    ('frame_corner_1', 'frame_corner_3'),
                    ('frame_corner_1', 'frame_corner_4'),
                    ('mounting_hole_1', 'mounting_hole_2'),
                    ('frame_corner_1', 'ground_terminal')
                ],
                unit='',
                description='Ground continuity paths to test'
            ),
            'contact_resistance_limit': TestParameter(
                name='contact_resistance_limit',
                value=0.050,  # 50 mΩ
                unit='Ohm',
                description='Maximum acceptable contact resistance'
            )
        }

    def execute(self) -> TestBlockResult:
        """Execute ground continuity test"""
        self.start_time = datetime.now()
        self.logger.info(f"Starting ground continuity test {self.test_id}")

        try:
            # Validate equipment
            issues = self.validate_equipment()
            if issues:
                raise RuntimeError(f"Equipment validation failed: {', '.join(issues)}")

            # Initialize equipment
            self.continuity_tester.initialize()

            # Collect test data
            self.measurements = self._collect_data()

            # Analyze results
            self.analysis_results = self._analyze_data()

            # Check for anomalies
            self._detect_anomalies()

        except Exception as e:
            self.logger.error(f"Error during ground continuity test: {e}")
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
        """Collect ground continuity measurements"""
        self.logger.info("Collecting ground continuity data...")

        measurements = []

        # Get test parameters
        test_current = self.parameters['test_current'].value
        test_duration = self.parameters['test_duration'].value
        test_paths = self.parameters['test_paths'].value

        # Test each ground path
        for point1, point2 in test_paths:
            self.logger.info(f"Testing path: {point1} → {point2}")

            # Verify contact quality
            good_contact, contact_resistance = self.continuity_tester.perform_contact_check()

            if not good_contact:
                self.logger.warning(
                    f"Poor contact detected: {contact_resistance*1e3:.1f} mΩ - "
                    "cleaning contacts and retrying"
                )

                # Simulate contact cleaning and retry
                good_contact, contact_resistance = self.continuity_tester.perform_contact_check()

            # Measure ground resistance
            resistance, voltage_drop, resistance_samples = \
                self.continuity_tester.measure_resistance(
                    test_current=test_current,
                    duration=test_duration
                )

            # Create GCT measurement record
            gct_measurement = GCTMeasurement(
                timestamp=datetime.now(),
                resistance=resistance,
                test_current=test_current,
                voltage_drop=voltage_drop,
                test_points=(point1, point2),
                contact_resistance=contact_resistance
            )
            self.gct_measurements.append(gct_measurement)

            # Store measurements
            measurements.append(MeasurementData(
                timestamp=gct_measurement.timestamp,
                value=resistance,
                unit='Ohm',
                parameter_name=f'resistance_{point1}_to_{point2}',
                equipment_id=self.continuity_tester.equipment_id,
                metadata={
                    'test_current': test_current,
                    'voltage_drop': voltage_drop,
                    'contact_resistance': contact_resistance
                }
            ))

            # Store resistance samples for analysis
            for i, sample in enumerate(resistance_samples):
                measurements.append(MeasurementData(
                    timestamp=datetime.now(),
                    value=sample,
                    unit='Ohm',
                    parameter_name=f'resistance_sample_{point1}_to_{point2}',
                    equipment_id=self.continuity_tester.equipment_id,
                    metadata={
                        'sample': i,
                        'total_samples': len(resistance_samples)
                    }
                ))

            # Log results
            self.logger.info(
                f"{point1} → {point2}: R = {resistance*1e3:.1f} mΩ, "
                f"V_drop = {voltage_drop:.3f} V"
            )

        return measurements

    def _analyze_data(self) -> Dict[str, Any]:
        """Analyze ground continuity test results"""
        self.logger.info("Analyzing ground continuity data...")

        if not self.gct_measurements:
            return {'error': 'No measurements available'}

        # Extract resistances
        resistances = np.array([m.resistance for m in self.gct_measurements])
        voltage_drops = np.array([m.voltage_drop for m in self.gct_measurements])
        contact_resistances = np.array([m.contact_resistance for m in self.gct_measurements])

        # Calculate statistics
        resistance_stats = {
            'mean': float(np.mean(resistances)),
            'max': float(np.max(resistances)),
            'min': float(np.min(resistances)),
            'std': float(np.std(resistances, ddof=1)) if len(resistances) > 1 else 0.0,
            'median': float(np.median(resistances))
        }

        voltage_drop_stats = {
            'mean': float(np.mean(voltage_drops)),
            'max': float(np.max(voltage_drops)),
            'min': float(np.min(voltage_drops))
        }

        contact_resistance_stats = {
            'mean': float(np.mean(contact_resistances)),
            'max': float(np.max(contact_resistances))
        }

        # Analyze resistance uniformity
        uniformity = self._analyze_resistance_uniformity()

        # Check for temperature rise effects
        temp_rise_analysis = self._analyze_temperature_effects()

        # Identify highest resistance path
        max_resistance_measurement = max(self.gct_measurements, key=lambda m: m.resistance)
        worst_path = {
            'points': max_resistance_measurement.test_points,
            'resistance_mohm': max_resistance_measurement.resistance * 1e3,
            'voltage_drop': max_resistance_measurement.voltage_drop
        }

        return {
            'resistance_stats': resistance_stats,
            'voltage_drop_stats': voltage_drop_stats,
            'contact_resistance_stats': contact_resistance_stats,
            'max_resistance_mohm': resistance_stats['max'] * 1e3,
            'mean_resistance_mohm': resistance_stats['mean'] * 1e3,
            'max_voltage_drop': voltage_drop_stats['max'],
            'uniformity': uniformity,
            'temperature_effects': temp_rise_analysis,
            'worst_path': worst_path,
            'num_paths_tested': len(self.gct_measurements)
        }

    def _analyze_resistance_uniformity(self) -> Dict[str, Any]:
        """Analyze uniformity of resistance across test paths"""
        if len(self.gct_measurements) < 2:
            return {'status': 'insufficient_data'}

        resistances = np.array([m.resistance for m in self.gct_measurements])

        # Calculate coefficient of variation
        cv = (np.std(resistances, ddof=1) / np.mean(resistances) * 100) if np.mean(resistances) > 0 else 0

        # Check for outliers
        median = np.median(resistances)
        mad = np.median(np.abs(resistances - median))
        outlier_threshold = 3.5  # Modified Z-score threshold

        outliers = []
        for i, r in enumerate(resistances):
            if mad > 0:
                modified_z = 0.6745 * (r - median) / mad
                if abs(modified_z) > outlier_threshold:
                    outliers.append({
                        'path': self.gct_measurements[i].test_points,
                        'resistance_mohm': r * 1e3,
                        'deviation_from_median_mohm': (r - median) * 1e3
                    })

        return {
            'coefficient_of_variation': float(cv),
            'uniform': cv < 30.0,  # CV < 30% considered uniform
            'outliers': outliers,
            'num_outliers': len(outliers)
        }

    def _analyze_temperature_effects(self) -> Dict[str, Any]:
        """Analyze temperature rise effects during high current test"""
        # Analyze resistance samples over time to detect heating
        # Get sample measurements for first path
        first_path = self.gct_measurements[0].test_points
        sample_param = f'resistance_sample_{first_path[0]}_to_{first_path[1]}'

        samples = self.get_measurements(sample_param)

        if len(samples) < 3:
            return {'status': 'insufficient_data'}

        resistances = np.array([s.value for s in samples])

        # Check for increasing trend (indicates heating)
        initial_resistance = resistances[0]
        final_resistance = resistances[-1]
        resistance_change = final_resistance - initial_resistance
        percent_change = (resistance_change / initial_resistance * 100) if initial_resistance > 0 else 0

        # Temperature coefficient of copper: ~0.4%/°C
        # Estimated temperature rise
        estimated_temp_rise = percent_change / 0.4

        return {
            'initial_resistance_mohm': float(initial_resistance * 1e3),
            'final_resistance_mohm': float(final_resistance * 1e3),
            'resistance_change_mohm': float(resistance_change * 1e3),
            'percent_change': float(percent_change),
            'estimated_temp_rise_c': float(estimated_temp_rise),
            'heating_detected': abs(percent_change) > 2.0  # > 2% change
        }

    def _detect_anomalies(self) -> None:
        """Detect anomalies in ground continuity test"""
        if not self.gct_measurements:
            return

        max_resistance = self.parameters['max_resistance'].value
        max_voltage_drop = self.parameters['max_voltage_drop'].value
        contact_resistance_limit = self.parameters['contact_resistance_limit'].value

        for measurement in self.gct_measurements:
            # Check resistance limit
            if measurement.resistance > max_resistance:
                self.log_anomaly(
                    f"High ground resistance {measurement.test_points}: "
                    f"{measurement.resistance*1e3:.1f} mΩ "
                    f"(max: {max_resistance*1e3:.1f} mΩ)"
                )

            # Check voltage drop
            if measurement.voltage_drop > max_voltage_drop:
                self.log_anomaly(
                    f"High voltage drop {measurement.test_points}: "
                    f"{measurement.voltage_drop:.3f} V "
                    f"(max: {max_voltage_drop:.3f} V)"
                )

            # Check contact resistance
            if measurement.contact_resistance > contact_resistance_limit:
                self.log_anomaly(
                    f"High contact resistance {measurement.test_points}: "
                    f"{measurement.contact_resistance*1e3:.1f} mΩ"
                )

        # Check uniformity
        uniformity = self.analysis_results.get('uniformity', {})
        if uniformity.get('num_outliers', 0) > 0:
            self.log_anomaly(
                f"Non-uniform ground resistance detected: "
                f"{uniformity['num_outliers']} outlier paths"
            )

        # Check for heating
        temp_effects = self.analysis_results.get('temperature_effects', {})
        if temp_effects.get('heating_detected', False):
            self.log_anomaly(
                f"Significant heating detected: "
                f"ΔT ≈ {temp_effects.get('estimated_temp_rise_c', 0):.1f}°C"
            )

        # Check variation between paths
        resistances = [m.resistance for m in self.gct_measurements]
        if len(resistances) > 1:
            max_r = max(resistances)
            min_r = min(resistances)

            if max_r > 0 and (max_r / min_r) > 3:  # 3x difference
                self.log_anomaly(
                    f"Large variation in ground resistance: "
                    f"{min_r*1e3:.1f} to {max_r*1e3:.1f} mΩ"
                )

    def _determine_pass_fail(self) -> Tuple[TestResult, Dict[str, bool]]:
        """Determine pass/fail status"""
        criteria = {}

        if not self.gct_measurements:
            return TestResult.ERROR, criteria

        max_resistance = self.parameters['max_resistance'].value
        max_voltage_drop = self.parameters['max_voltage_drop'].value

        # Check each path
        for measurement in self.gct_measurements:
            point1, point2 = measurement.test_points
            path_name = f"resistance_{point1}_to_{point2}"
            criteria[path_name] = measurement.resistance <= max_resistance

            voltage_name = f"voltage_{point1}_to_{point2}"
            criteria[voltage_name] = measurement.voltage_drop <= max_voltage_drop

        # Overall criteria
        criteria['all_resistances_acceptable'] = all(
            m.resistance <= max_resistance for m in self.gct_measurements
        )

        criteria['all_voltage_drops_acceptable'] = all(
            m.voltage_drop <= max_voltage_drop for m in self.gct_measurements
        )

        # Uniformity criterion (informational)
        uniformity = self.analysis_results.get('uniformity', {})
        criteria['resistance_uniform'] = uniformity.get('uniform', False)

        # Overall result
        all_pass = all(criteria.values())
        critical_pass = (criteria.get('all_resistances_acceptable', False) and
                        criteria.get('all_voltage_drops_acceptable', False))

        if all_pass:
            return TestResult.PASS, criteria
        elif critical_pass:
            return TestResult.CONDITIONAL_PASS, criteria
        else:
            return TestResult.FAIL, criteria
