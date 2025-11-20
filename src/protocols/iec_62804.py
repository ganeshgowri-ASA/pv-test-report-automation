"""
IEC 62804 - Potential Induced Degradation (PID) Testing

This module implements IEC 62804-1 (Test methods for the detection of potential-induced
degradation) for PV modules.

Test Procedures:
- PID stress testing (±1000V, 96 hours, 85°C, 85% RH)
- Power degradation measurement
- Recovery testing
- Leakage current monitoring

Pass/Fail Criteria:
- Power degradation < 5% (Class A)
- Power degradation < 20% (Class B)
- Full recovery within 96 hours
"""

import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from .base_protocol import (
    BaseProtocol, ProtocolResult, Uncertainty, TestStatus, DataQuality
)


@dataclass
class PIDTestSequence:
    """Container for PID test sequence data"""
    timestamps: List[datetime]
    power_measurements: List[float]
    voltage_stress: float  # Applied voltage (V)
    temperature: List[float]  # °C
    humidity: List[float]  # %RH
    leakage_current: List[float]  # mA


class PIDClass(str):
    """PID classification based on degradation"""
    CLASS_A = "A"  # < 5% degradation
    CLASS_B = "B"  # < 20% degradation
    FAIL = "FAIL"  # ≥ 20% degradation


class IEC62804(BaseProtocol):
    """
    IEC 62804-1 PID Testing Protocol

    Implements potential-induced degradation testing for PV modules
    according to IEC 62804-1 standard.
    """

    # Standard test conditions
    STRESS_VOLTAGE = 1000  # V (can be positive or negative)
    STRESS_TEMPERATURE = 85  # °C
    STRESS_HUMIDITY = 85  # %RH
    STRESS_DURATION = 96  # hours

    # Recovery test conditions
    RECOVERY_DURATION = 96  # hours
    RECOVERY_TEMPERATURE = 85  # °C
    RECOVERY_HUMIDITY = 0  # %RH (dry)

    # Pass/fail thresholds
    CLASS_A_THRESHOLD = 5.0  # % power degradation
    CLASS_B_THRESHOLD = 20.0  # % power degradation

    def __init__(self):
        """Initialize IEC 62804 protocol handler"""
        super().__init__("IEC 62804-1", "2015")

        self.uncertainty_sources = {
            'power_measurement': 0.03,  # 3%
            'temperature_control': 2.0,  # ±2°C
            'humidity_control': 5.0,     # ±5%RH
            'voltage_stress': 0.02,      # 2% of applied voltage
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate PID test data

        Args:
            data: Dictionary containing PID test data

        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            'initial_power', 'post_stress_power',
            'stress_duration_hours', 'stress_temperature',
            'stress_humidity', 'stress_voltage'
        ]

        for field in required_fields:
            if field not in data:
                print(f"Error: Missing required field '{field}'")
                return False

        # Validate stress conditions
        temp = data['stress_temperature']
        if not self.check_data_range(temp, 80, 90, "Stress temperature (°C)"):
            print("Warning: Temperature should be 85±5°C")

        humidity = data['stress_humidity']
        if not self.check_data_range(humidity, 80, 90, "Stress humidity (%RH)"):
            print("Warning: Humidity should be 85±5%RH")

        voltage = abs(data['stress_voltage'])
        if not self.check_data_range(voltage, 500, 1500, "Stress voltage (V)"):
            print("Warning: Typical stress voltage is ±1000V")

        duration = data['stress_duration_hours']
        if duration < 24:
            print("Warning: Minimum stress duration should be 24 hours (96h recommended)")

        # Check power values are positive
        if data['initial_power'] <= 0 or data['post_stress_power'] <= 0:
            print("Error: Power values must be positive")
            return False

        return True

    def calculate(self, data: Dict[str, Any]) -> ProtocolResult:
        """
        Analyze PID test results and determine classification

        Args:
            data: Dictionary with PID test data

        Returns:
            ProtocolResult with PID analysis
        """
        if not self.validate_data(data):
            result = self.create_result(status=TestStatus.FAIL)
            result.notes = "Data validation failed"
            return result

        result = self.create_result(status=TestStatus.PASS)

        # Extract data
        p_initial = data['initial_power']
        p_post_stress = data['post_stress_power']
        stress_voltage = data['stress_voltage']
        stress_duration = data['stress_duration_hours']
        stress_temp = data['stress_temperature']
        stress_humidity = data['stress_humidity']

        # Store metadata
        result.metadata.update({
            'stress_voltage_V': stress_voltage,
            'stress_duration_hours': stress_duration,
            'stress_temperature_C': stress_temp,
            'stress_humidity_RH': stress_humidity,
            'test_standard': 'IEC 62804-1:2015'
        })

        # Calculate degradation
        degradation = self._calculate_degradation(p_initial, p_post_stress)
        result.add_measurement('power_degradation', degradation)

        # Determine PID classification
        pid_class = self._classify_pid_result(degradation.value)
        result.add_measurement('PID_classification', pid_class)

        # Calculate degradation rate
        deg_rate = self._calculate_degradation_rate(degradation.value, stress_duration)
        result.add_measurement('degradation_rate_per_hour', deg_rate)

        # Analyze time-series data if available
        if 'time_series' in data:
            time_analysis = self._analyze_time_series(data['time_series'])
            result.add_measurement('time_series_analysis', time_analysis)

        # Analyze leakage current if available
        if 'leakage_current' in data:
            leakage_analysis = self._analyze_leakage_current(data['leakage_current'])
            result.add_measurement('leakage_current_analysis', leakage_analysis)

        # Analyze recovery data if available
        if 'recovery_data' in data:
            recovery = self._analyze_recovery(
                p_initial, p_post_stress, data['recovery_data']
            )
            result.add_measurement('recovery_analysis', recovery)

        # Compare with reference module if available
        if 'reference_module_power' in data:
            ref_comparison = self._compare_with_reference(
                degradation.value, data['reference_module_power']
            )
            result.add_measurement('reference_comparison', ref_comparison)

        # Assess data quality
        result.data_quality = self.assess_data_quality(degradation)

        # Apply pass/fail criteria
        self._apply_pass_fail_criteria(result, pid_class)

        return result

    def _calculate_degradation(self, p_initial: float, p_final: float) -> Uncertainty:
        """
        Calculate power degradation percentage

        Degradation (%) = (P_initial - P_final) / P_initial × 100

        Args:
            p_initial: Initial power before stress (W)
            p_final: Power after stress (W)

        Returns:
            Uncertainty object with degradation percentage
        """
        if p_initial <= 0:
            raise ValueError("Initial power must be positive")

        degradation_value = ((p_initial - p_final) / p_initial) * 100

        # Calculate uncertainty
        # Assuming two independent measurements with same uncertainty
        rel_unc_power = self.uncertainty_sources['power_measurement']

        # Propagate uncertainty for ratio
        # u(deg)/deg ≈ sqrt(2) × u(P)/P for (P1-P2)/P1 when P1≈P2
        rel_unc_degradation = np.sqrt(2) * rel_unc_power

        std_uncertainty = abs(degradation_value) * rel_unc_degradation

        # For small degradation, absolute uncertainty dominates
        if abs(degradation_value) < 1.0:
            std_uncertainty = max(std_uncertainty, 0.5)  # Minimum 0.5% absolute

        return Uncertainty(
            value=degradation_value,
            standard_uncertainty=std_uncertainty,
            sources={'power_measurements': std_uncertainty}
        )

    def _classify_pid_result(self, degradation: float) -> str:
        """
        Classify PID test result based on degradation

        Args:
            degradation: Power degradation percentage

        Returns:
            PID classification string
        """
        if degradation < self.CLASS_A_THRESHOLD:
            return PIDClass.CLASS_A
        elif degradation < self.CLASS_B_THRESHOLD:
            return PIDClass.CLASS_B
        else:
            return PIDClass.FAIL

    def _calculate_degradation_rate(self, degradation: float,
                                    duration_hours: float) -> Uncertainty:
        """
        Calculate degradation rate

        Args:
            degradation: Total degradation (%)
            duration_hours: Test duration (hours)

        Returns:
            Uncertainty object with degradation rate (%/hour)
        """
        if duration_hours <= 0:
            raise ValueError("Duration must be positive")

        rate_value = degradation / duration_hours

        # Uncertainty scales with rate
        rate_uncertainty = rate_value * self.uncertainty_sources['power_measurement']

        return Uncertainty(
            value=rate_value,
            standard_uncertainty=rate_uncertainty,
            sources={'calculation': rate_uncertainty}
        )

    def _analyze_time_series(self, time_series: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze time-series degradation data

        Args:
            time_series: Dictionary with time-series measurements

        Returns:
            Dictionary with time-series analysis results
        """
        times = np.array(time_series.get('hours', []))
        powers = np.array(time_series.get('powers', []))

        if len(times) < 3 or len(powers) < 3:
            return {'error': 'Insufficient time-series data'}

        # Normalize to initial power
        p_initial = powers[0]
        normalized_power = (powers / p_initial) * 100  # Percentage of initial

        # Fit degradation model: P(t) = P0 × exp(-k×t) or linear
        # Try linear fit first
        regression = self.calculate_linear_regression(times, normalized_power)

        # Calculate when degradation reaches thresholds
        time_to_5pct = self._calculate_time_to_threshold(
            times, normalized_power, 95.0  # 5% degradation
        )

        time_to_20pct = self._calculate_time_to_threshold(
            times, normalized_power, 80.0  # 20% degradation
        )

        return {
            'linear_degradation_rate_pct_per_hour': regression['slope'],
            'r_squared': regression['r_squared'],
            'time_to_5pct_degradation_hours': time_to_5pct,
            'time_to_20pct_degradation_hours': time_to_20pct,
            'initial_power_pct': normalized_power[0],
            'final_power_pct': normalized_power[-1],
            'degradation_profile': 'linear' if regression['r_squared'] > 0.95 else 'non-linear'
        }

    def _calculate_time_to_threshold(self, times: np.ndarray, powers: np.ndarray,
                                     threshold: float) -> Optional[float]:
        """
        Calculate time to reach degradation threshold

        Args:
            times: Time array (hours)
            powers: Power array (% of initial)
            threshold: Power threshold (% of initial)

        Returns:
            Time to reach threshold (hours) or None if not reached
        """
        # Check if threshold is crossed
        if powers[-1] > threshold:
            # Threshold not reached
            return None

        # Find interpolation points
        idx = np.where(powers <= threshold)[0]
        if len(idx) == 0:
            return None

        first_below = idx[0]

        if first_below == 0:
            return times[0]

        # Linear interpolation
        t1, t2 = times[first_below - 1], times[first_below]
        p1, p2 = powers[first_below - 1], powers[first_below]

        time_at_threshold = t1 + (threshold - p1) * (t2 - t1) / (p2 - p1)

        return float(time_at_threshold)

    def _analyze_leakage_current(self, leakage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze leakage current during PID test

        Args:
            leakage_data: Dictionary with leakage current measurements

        Returns:
            Dictionary with leakage current analysis
        """
        times = np.array(leakage_data.get('hours', []))
        currents = np.array(leakage_data.get('current_mA', []))

        if len(currents) == 0:
            return {'error': 'No leakage current data'}

        return {
            'initial_leakage_mA': float(currents[0]),
            'final_leakage_mA': float(currents[-1]),
            'max_leakage_mA': float(np.max(currents)),
            'mean_leakage_mA': float(np.mean(currents)),
            'leakage_stable': np.std(currents) < 0.1 * np.mean(currents)  # CV < 10%
        }

    def _analyze_recovery(self, p_initial: float, p_post_stress: float,
                         recovery_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze PID recovery after stress removal

        Args:
            p_initial: Initial power before stress (W)
            p_post_stress: Power immediately after stress (W)
            recovery_data: Dictionary with recovery test data

        Returns:
            Dictionary with recovery analysis
        """
        p_recovered = recovery_data.get('final_power', p_post_stress)
        recovery_duration = recovery_data.get('duration_hours', 0)

        # Calculate recovery percentage
        degradation = ((p_initial - p_post_stress) / p_initial) * 100
        recovery_amount = ((p_recovered - p_post_stress) / p_initial) * 100
        recovery_percentage = (recovery_amount / degradation * 100) if degradation > 0 else 0

        residual_degradation = ((p_initial - p_recovered) / p_initial) * 100

        # Classify recovery
        if residual_degradation < 1.0:
            recovery_class = "Full recovery"
        elif residual_degradation < 5.0:
            recovery_class = "Partial recovery (>95%)"
        elif residual_degradation < 10.0:
            recovery_class = "Partial recovery (>90%)"
        else:
            recovery_class = "Poor recovery"

        return {
            'recovered_power_W': p_recovered,
            'recovery_percentage': recovery_percentage,
            'residual_degradation_pct': residual_degradation,
            'recovery_duration_hours': recovery_duration,
            'recovery_classification': recovery_class,
            'full_recovery': residual_degradation < 1.0
        }

    def _compare_with_reference(self, test_degradation: float,
                               ref_power: Dict[str, float]) -> Dict[str, Any]:
        """
        Compare test module with reference module

        Args:
            test_degradation: Test module degradation (%)
            ref_power: Reference module power data

        Returns:
            Dictionary with comparison results
        """
        ref_initial = ref_power.get('initial', 0)
        ref_final = ref_power.get('final', 0)

        if ref_initial <= 0:
            return {'error': 'Invalid reference data'}

        ref_degradation = ((ref_initial - ref_final) / ref_initial) * 100

        # Calculate relative degradation
        relative_degradation = test_degradation - ref_degradation

        # Determine if test module performed better or worse
        comparison = {
            'reference_degradation_pct': ref_degradation,
            'test_degradation_pct': test_degradation,
            'relative_degradation_pct': relative_degradation,
            'better_than_reference': relative_degradation < 0,
            'degradation_difference_pct': abs(relative_degradation)
        }

        if abs(relative_degradation) < 2.0:
            comparison['assessment'] = "Similar to reference"
        elif relative_degradation < 0:
            comparison['assessment'] = "Better than reference"
        else:
            comparison['assessment'] = "Worse than reference"

        return comparison

    def _apply_pass_fail_criteria(self, result: ProtocolResult, pid_class: str):
        """
        Apply pass/fail criteria based on IEC 62804

        Args:
            result: ProtocolResult to update
            pid_class: PID classification
        """
        # Check if passes Class A
        result.add_criterion('passes_class_A', pid_class == PIDClass.CLASS_A)

        # Check if passes Class B
        result.add_criterion('passes_class_B',
                           pid_class in [PIDClass.CLASS_A, PIDClass.CLASS_B])

        # Update overall status based on classification
        if pid_class == PIDClass.FAIL:
            result.status = TestStatus.FAIL
            result.notes += "Module failed PID test (≥20% degradation). "

        # Check recovery if available
        recovery = result.measurements.get('recovery_analysis')
        if isinstance(recovery, dict):
            full_recovery = recovery.get('full_recovery', False)
            result.add_criterion('full_recovery_achieved', full_recovery)

            if full_recovery:
                result.notes += "Full recovery achieved after stress removal. "

        # Check leakage current stability
        leakage = result.measurements.get('leakage_current_analysis')
        if isinstance(leakage, dict):
            stable = leakage.get('leakage_stable', True)
            result.add_criterion('leakage_current_stable', stable)

        # Check test duration compliance
        duration = result.metadata.get('stress_duration_hours', 0)
        result.add_criterion('test_duration_compliant', duration >= 96)
