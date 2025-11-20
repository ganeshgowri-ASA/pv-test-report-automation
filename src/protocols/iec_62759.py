"""
IEC 62759 - Transportation Testing of Photovoltaic Modules

This module implements IEC 62759-1 (Transportation testing) for PV modules,
including mechanical load testing, environmental exposure, and durability assessment.

Test Procedures:
- Mechanical load simulation (vibration, shock)
- Edge load testing
- Environmental cycling
- Visual inspection
- Electrical performance verification

Pass/Fail Criteria:
- No visible damage (cracks, delamination)
- Power degradation < 5%
- Insulation resistance maintained
- No safety hazards
"""

import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from .base_protocol import (
    BaseProtocol, ProtocolResult, Uncertainty, TestStatus, DataQuality
)


class DefectSeverity(Enum):
    """Visual defect severity classification"""
    NONE = "NONE"
    MINOR = "MINOR"          # Cosmetic only, no performance impact
    MODERATE = "MODERATE"    # May affect performance
    MAJOR = "MAJOR"          # Significant performance impact
    CRITICAL = "CRITICAL"    # Safety hazard or complete failure


class TransportationMode(Enum):
    """Transportation mode classification"""
    ROAD = "ROAD"
    RAIL = "RAIL"
    SEA = "SEA"
    AIR = "AIR"
    COMBINED = "COMBINED"


@dataclass
class MechanicalLoadProfile:
    """Container for mechanical load test profile"""
    load_type: str  # 'static', 'cyclic', 'vibration', 'shock'
    magnitude: float  # N or Pa
    duration: float  # seconds or cycles
    frequency: Optional[float] = None  # Hz for vibration
    direction: Optional[str] = None  # 'front', 'back', 'edge'


@dataclass
class VisualInspection:
    """Container for visual inspection results"""
    inspection_time: str  # 'before', 'after', 'during'
    defects: List[Dict[str, Any]]
    overall_condition: str
    images: Optional[List[str]] = None


class IEC62759(BaseProtocol):
    """
    IEC 62759-1 Transportation Testing Protocol

    Implements transportation testing procedures for PV modules
    according to IEC 62759-1 standard.
    """

    # Standard mechanical load limits
    STATIC_LOAD_FRONT = 2400  # Pa (positive pressure)
    STATIC_LOAD_BACK = 2400   # Pa (negative pressure)
    EDGE_LOAD = 100           # N per meter of edge

    # Performance degradation limits
    MAX_POWER_DEGRADATION = 5.0  # %
    MIN_INSULATION_RESISTANCE = 40  # MΩ for safety class II

    # Vibration test parameters (based on ASTM D4169)
    VIBRATION_FREQUENCY_RANGE = (1, 200)  # Hz
    VIBRATION_DURATION = 3600  # seconds (1 hour per axis)

    def __init__(self):
        """Initialize IEC 62759 protocol handler"""
        super().__init__("IEC 62759-1", "2015")

        self.uncertainty_sources = {
            'power_measurement': 0.03,     # 3%
            'load_measurement': 0.05,      # 5%
            'dimension_measurement': 0.001,  # 0.1%
            'insulation_resistance': 0.10,  # 10%
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate transportation test data

        Args:
            data: Dictionary containing test data

        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            'initial_power',
            'final_power',
            'mechanical_tests',
            'visual_inspections'
        ]

        for field in required_fields:
            if field not in data:
                print(f"Error: Missing required field '{field}'")
                return False

        # Validate power values
        if data['initial_power'] <= 0 or data['final_power'] <= 0:
            print("Error: Power values must be positive")
            return False

        # Validate mechanical test data
        if not isinstance(data['mechanical_tests'], list):
            print("Error: mechanical_tests must be a list")
            return False

        if len(data['mechanical_tests']) == 0:
            print("Warning: No mechanical tests specified")

        # Validate visual inspections
        if not isinstance(data['visual_inspections'], list):
            print("Error: visual_inspections must be a list")
            return False

        if len(data['visual_inspections']) < 2:
            print("Warning: Should have at least before and after inspections")

        return True

    def calculate(self, data: Dict[str, Any]) -> ProtocolResult:
        """
        Analyze transportation test results

        Args:
            data: Dictionary with transportation test data

        Returns:
            ProtocolResult with complete analysis
        """
        if not self.validate_data(data):
            result = self.create_result(status=TestStatus.FAIL)
            result.notes = "Data validation failed"
            return result

        result = self.create_result(status=TestStatus.PASS)

        # Extract data
        p_initial = data['initial_power']
        p_final = data['final_power']

        # Store metadata
        result.metadata.update({
            'transportation_mode': data.get('transportation_mode', 'Unknown'),
            'test_sequence': data.get('test_sequence', 'Standard'),
            'module_type': data.get('module_type', 'Unknown'),
            'mounting_configuration': data.get('mounting', 'Free-standing')
        })

        # Calculate power degradation
        degradation = self._calculate_power_degradation(p_initial, p_final)
        result.add_measurement('power_degradation', degradation)

        # Analyze mechanical load tests
        mech_analysis = self._analyze_mechanical_tests(data['mechanical_tests'])
        result.add_measurement('mechanical_test_results', mech_analysis)

        # Analyze visual inspections
        visual_analysis = self._analyze_visual_inspections(data['visual_inspections'])
        result.add_measurement('visual_inspection_results', visual_analysis)

        # Check insulation resistance if available
        if 'insulation_resistance' in data:
            insulation = self._analyze_insulation_resistance(data['insulation_resistance'])
            result.add_measurement('insulation_resistance', insulation)

        # Analyze environmental exposure if available
        if 'environmental_tests' in data:
            env_analysis = self._analyze_environmental_tests(data['environmental_tests'])
            result.add_measurement('environmental_test_results', env_analysis)

        # Analyze vibration profile if available
        if 'vibration_data' in data:
            vib_analysis = self._analyze_vibration_response(data['vibration_data'])
            result.add_measurement('vibration_analysis', vib_analysis)

        # Assess overall durability
        durability_score = self._calculate_durability_score(result.measurements)
        result.add_measurement('durability_score', durability_score)

        # Assess data quality
        result.data_quality = self.assess_data_quality(degradation)

        # Apply pass/fail criteria
        self._apply_pass_fail_criteria(result)

        return result

    def _calculate_power_degradation(self, p_initial: float, p_final: float) -> Uncertainty:
        """
        Calculate power degradation after transportation testing

        Args:
            p_initial: Initial power (W)
            p_final: Final power (W)

        Returns:
            Uncertainty object with degradation percentage
        """
        if p_initial <= 0:
            raise ValueError("Initial power must be positive")

        degradation_value = ((p_initial - p_final) / p_initial) * 100

        # Calculate uncertainty
        rel_unc_power = self.uncertainty_sources['power_measurement']
        rel_unc_degradation = np.sqrt(2) * rel_unc_power

        std_uncertainty = abs(degradation_value) * rel_unc_degradation

        # Minimum absolute uncertainty
        if abs(degradation_value) < 1.0:
            std_uncertainty = max(std_uncertainty, 0.3)

        return Uncertainty(
            value=degradation_value,
            standard_uncertainty=std_uncertainty,
            sources={'power_measurements': std_uncertainty}
        )

    def _analyze_mechanical_tests(self, mechanical_tests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze mechanical load test results

        Args:
            mechanical_tests: List of mechanical test configurations and results

        Returns:
            Dictionary with mechanical test analysis
        """
        analysis = {
            'total_tests': len(mechanical_tests),
            'tests_passed': 0,
            'tests_failed': 0,
            'max_load_applied': 0.0,
            'test_summary': []
        }

        for test in mechanical_tests:
            test_type = test.get('type', 'unknown')
            load = test.get('load', 0)
            passed = test.get('passed', True)
            defects_found = test.get('defects_found', [])

            # Update counters
            if passed:
                analysis['tests_passed'] += 1
            else:
                analysis['tests_failed'] += 1

            analysis['max_load_applied'] = max(analysis['max_load_applied'], load)

            # Summarize test
            test_summary = {
                'type': test_type,
                'load': load,
                'passed': passed,
                'defects_count': len(defects_found),
                'duration': test.get('duration', 'N/A')
            }

            # Check against standard limits
            if test_type == 'static_front':
                test_summary['exceeds_standard'] = load >= self.STATIC_LOAD_FRONT
            elif test_type == 'static_back':
                test_summary['exceeds_standard'] = load >= self.STATIC_LOAD_BACK
            elif test_type == 'edge_load':
                test_summary['exceeds_standard'] = load >= self.EDGE_LOAD

            analysis['test_summary'].append(test_summary)

        # Calculate pass rate
        if analysis['total_tests'] > 0:
            analysis['pass_rate_percent'] = (analysis['tests_passed'] / analysis['total_tests']) * 100
        else:
            analysis['pass_rate_percent'] = 0.0

        # Overall assessment
        if analysis['tests_failed'] == 0:
            analysis['overall_assessment'] = "All mechanical tests passed"
        elif analysis['tests_failed'] <= 1:
            analysis['overall_assessment'] = "Minor mechanical test failures"
        else:
            analysis['overall_assessment'] = "Multiple mechanical test failures"

        return analysis

    def _analyze_visual_inspections(self, inspections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze visual inspection results

        Args:
            inspections: List of visual inspection records

        Returns:
            Dictionary with visual inspection analysis
        """
        analysis = {
            'total_inspections': len(inspections),
            'defects_summary': {
                'NONE': 0,
                'MINOR': 0,
                'MODERATE': 0,
                'MAJOR': 0,
                'CRITICAL': 0
            },
            'defect_types': {},
            'inspection_timeline': []
        }

        all_defects = []

        for inspection in inspections:
            inspection_time = inspection.get('time', 'unknown')
            defects = inspection.get('defects', [])

            # Count defects by severity
            for defect in defects:
                severity = defect.get('severity', 'MINOR')
                defect_type = defect.get('type', 'unknown')

                # Update severity counts
                if severity in analysis['defects_summary']:
                    analysis['defects_summary'][severity] += 1

                # Update defect type counts
                if defect_type not in analysis['defect_types']:
                    analysis['defect_types'][defect_type] = 0
                analysis['defect_types'][defect_type] += 1

                all_defects.append(defect)

            # Record timeline
            analysis['inspection_timeline'].append({
                'time': inspection_time,
                'defects_count': len(defects),
                'condition': inspection.get('overall_condition', 'unknown')
            })

        # Determine worst defect severity
        if analysis['defects_summary']['CRITICAL'] > 0:
            analysis['worst_severity'] = 'CRITICAL'
        elif analysis['defects_summary']['MAJOR'] > 0:
            analysis['worst_severity'] = 'MAJOR'
        elif analysis['defects_summary']['MODERATE'] > 0:
            analysis['worst_severity'] = 'MODERATE'
        elif analysis['defects_summary']['MINOR'] > 0:
            analysis['worst_severity'] = 'MINOR'
        else:
            analysis['worst_severity'] = 'NONE'

        # Count total defects
        analysis['total_defects'] = len(all_defects)

        # Assessment
        if analysis['worst_severity'] == 'NONE':
            analysis['overall_assessment'] = "No defects detected"
        elif analysis['worst_severity'] == 'MINOR':
            analysis['overall_assessment'] = "Minor cosmetic defects only"
        elif analysis['worst_severity'] == 'MODERATE':
            analysis['overall_assessment'] = "Moderate defects detected"
        elif analysis['worst_severity'] == 'MAJOR':
            analysis['overall_assessment'] = "Major defects detected - performance impact likely"
        else:
            analysis['overall_assessment'] = "Critical defects detected - safety hazard"

        return analysis

    def _analyze_insulation_resistance(self, insulation_data: Dict[str, Any]) -> Uncertainty:
        """
        Analyze insulation resistance measurements

        Args:
            insulation_data: Dictionary with insulation resistance data

        Returns:
            Uncertainty object with insulation resistance (MΩ)
        """
        resistance_value = insulation_data.get('value', 0)  # MΩ

        if resistance_value <= 0:
            raise ValueError("Insulation resistance must be positive")

        # Calculate uncertainty
        std_uncertainty = resistance_value * self.uncertainty_sources['insulation_resistance']

        return Uncertainty(
            value=resistance_value,
            standard_uncertainty=std_uncertainty,
            sources={'measurement': std_uncertainty}
        )

    def _analyze_environmental_tests(self, env_tests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze environmental exposure tests

        Args:
            env_tests: List of environmental test configurations

        Returns:
            Dictionary with environmental test analysis
        """
        analysis = {
            'total_tests': len(env_tests),
            'test_types': [],
            'extreme_conditions': []
        }

        for test in env_tests:
            test_type = test.get('type', 'unknown')
            temperature = test.get('temperature', None)
            humidity = test.get('humidity', None)
            duration = test.get('duration_hours', 0)

            analysis['test_types'].append(test_type)

            # Check for extreme conditions
            if temperature is not None:
                if temperature < -40 or temperature > 85:
                    analysis['extreme_conditions'].append({
                        'parameter': 'temperature',
                        'value': temperature,
                        'unit': '°C'
                    })

            if humidity is not None:
                if humidity > 85:
                    analysis['extreme_conditions'].append({
                        'parameter': 'humidity',
                        'value': humidity,
                        'unit': '%RH'
                    })

        analysis['extreme_conditions_count'] = len(analysis['extreme_conditions'])

        return analysis

    def _analyze_vibration_response(self, vibration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze vibration test response

        Args:
            vibration_data: Dictionary with vibration test data

        Returns:
            Dictionary with vibration analysis
        """
        frequencies = np.array(vibration_data.get('frequencies', []))
        accelerations = np.array(vibration_data.get('accelerations', []))  # g's
        axes_tested = vibration_data.get('axes', ['x', 'y', 'z'])

        if len(frequencies) == 0 or len(accelerations) == 0:
            return {'error': 'Insufficient vibration data'}

        analysis = {
            'frequency_range_Hz': [float(np.min(frequencies)), float(np.max(frequencies))],
            'max_acceleration_g': float(np.max(accelerations)),
            'mean_acceleration_g': float(np.mean(accelerations)),
            'axes_tested': axes_tested,
            'test_duration_per_axis_hours': vibration_data.get('duration', 1.0)
        }

        # Find resonance frequencies (local maxima in acceleration)
        if len(accelerations) > 10:
            # Simple peak detection
            peaks = []
            for i in range(1, len(accelerations) - 1):
                if accelerations[i] > accelerations[i-1] and accelerations[i] > accelerations[i+1]:
                    if accelerations[i] > np.mean(accelerations) * 1.5:  # Significant peaks only
                        peaks.append({
                            'frequency_Hz': float(frequencies[i]),
                            'acceleration_g': float(accelerations[i])
                        })

            analysis['resonance_peaks'] = peaks
            analysis['resonance_peaks_count'] = len(peaks)

        # Check if meets standard duration
        total_duration = analysis['test_duration_per_axis_hours'] * len(axes_tested)
        analysis['meets_standard_duration'] = total_duration >= 3.0  # 1 hour per axis minimum

        return analysis

    def _calculate_durability_score(self, measurements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate overall durability score

        Args:
            measurements: Dictionary of all measurements

        Returns:
            Dictionary with durability score and rating
        """
        score = 100.0  # Start with perfect score

        # Deduct points for power degradation
        degradation = measurements.get('power_degradation')
        if isinstance(degradation, Uncertainty):
            score -= min(degradation.value, 20.0)  # Max 20 points deduction

        # Deduct points for visual defects
        visual = measurements.get('visual_inspection_results')
        if isinstance(visual, dict):
            worst_severity = visual.get('worst_severity', 'NONE')
            severity_penalties = {
                'NONE': 0,
                'MINOR': 5,
                'MODERATE': 15,
                'MAJOR': 30,
                'CRITICAL': 50
            }
            score -= severity_penalties.get(worst_severity, 0)

        # Deduct points for mechanical test failures
        mechanical = measurements.get('mechanical_test_results')
        if isinstance(mechanical, dict):
            failures = mechanical.get('tests_failed', 0)
            score -= min(failures * 10, 30)  # Max 30 points deduction

        # Bonus for passing all tests
        if score >= 95:
            score = min(score + 5, 100)

        # Ensure score is in valid range
        score = max(0, min(100, score))

        # Determine rating
        if score >= 90:
            rating = "Excellent"
        elif score >= 75:
            rating = "Good"
        elif score >= 60:
            rating = "Acceptable"
        elif score >= 40:
            rating = "Poor"
        else:
            rating = "Failed"

        return {
            'score': score,
            'rating': rating,
            'max_score': 100
        }

    def _apply_pass_fail_criteria(self, result: ProtocolResult):
        """
        Apply pass/fail criteria based on IEC 62759

        Args:
            result: ProtocolResult to update
        """
        # Check power degradation
        degradation = result.measurements.get('power_degradation')
        if isinstance(degradation, Uncertainty):
            result.add_criterion('power_degradation_acceptable',
                               degradation.value < self.MAX_POWER_DEGRADATION)

            if degradation.value >= self.MAX_POWER_DEGRADATION:
                result.status = TestStatus.FAIL
                result.notes += f"Power degradation ({degradation.value:.1f}%) exceeds limit ({self.MAX_POWER_DEGRADATION}%). "

        # Check visual inspection
        visual = result.measurements.get('visual_inspection_results')
        if isinstance(visual, dict):
            worst_severity = visual.get('worst_severity', 'NONE')

            result.add_criterion('no_critical_defects',
                               worst_severity != 'CRITICAL')

            result.add_criterion('no_major_defects',
                               worst_severity not in ['CRITICAL', 'MAJOR'])

            if worst_severity == 'CRITICAL':
                result.status = TestStatus.FAIL
                result.notes += "Critical visual defects detected - safety hazard. "
            elif worst_severity == 'MAJOR':
                result.status = TestStatus.WARNING
                result.notes += "Major visual defects detected. "

        # Check insulation resistance
        insulation = result.measurements.get('insulation_resistance')
        if isinstance(insulation, Uncertainty):
            result.add_criterion('insulation_resistance_adequate',
                               insulation.value >= self.MIN_INSULATION_RESISTANCE)

            if insulation.value < self.MIN_INSULATION_RESISTANCE:
                result.status = TestStatus.FAIL
                result.notes += f"Insulation resistance ({insulation.value:.1f} MΩ) below minimum ({self.MIN_INSULATION_RESISTANCE} MΩ). "

        # Check mechanical tests
        mechanical = result.measurements.get('mechanical_test_results')
        if isinstance(mechanical, dict):
            tests_failed = mechanical.get('tests_failed', 0)
            result.add_criterion('all_mechanical_tests_passed',
                               tests_failed == 0)

        # Check durability score
        durability = result.measurements.get('durability_score')
        if isinstance(durability, dict):
            score = durability.get('score', 0)
            result.add_criterion('durability_score_acceptable',
                               score >= 60)

            if score < 60:
                result.status = TestStatus.FAIL
                result.notes += f"Durability score ({score:.0f}/100) below acceptable threshold. "
