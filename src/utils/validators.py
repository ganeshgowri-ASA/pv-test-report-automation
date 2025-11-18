"""
Validation utilities for PV test parameters and results.

Provides validation functions for:
- Parameter tolerance checking
- Measurement uncertainty validation
- Equipment calibration verification
- Environmental condition validation
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import math


class ParameterValidator:
    """Validates test parameters against standard specifications."""

    @staticmethod
    def check_tolerance(
        value: float,
        min_val: float,
        max_val: float,
        parameter_name: str = "Parameter"
    ) -> Tuple[bool, str]:
        """
        Check if value is within tolerance range.

        Args:
            value: Value to check
            min_val: Minimum acceptable value
            max_val: Maximum acceptable value
            parameter_name: Name of parameter for error message

        Returns:
            Tuple of (is_valid, error_message)
        """
        if min_val <= value <= max_val:
            return True, ""
        else:
            error_msg = (
                f"{parameter_name} value {value} is outside tolerance range "
                f"[{min_val}, {max_val}]"
            )
            return False, error_msg

    @staticmethod
    def check_measurement_uncertainty(
        measurement: float,
        uncertainty: float,
        specification_limit: float,
        guard_band_factor: float = 1.0
    ) -> Tuple[bool, str]:
        """
        Validate measurement considering uncertainty and guard bands.

        Args:
            measurement: Measured value
            uncertainty: Measurement uncertainty
            specification_limit: Specification limit
            guard_band_factor: Guard band factor (default 1.0 = no guard band)

        Returns:
            Tuple of (is_valid, error_message)
        """
        effective_limit = specification_limit - (guard_band_factor * uncertainty)
        if measurement <= effective_limit:
            return True, ""
        else:
            error_msg = (
                f"Measurement {measurement} exceeds effective limit {effective_limit:.2f} "
                f"(spec: {specification_limit}, uncertainty: {uncertainty})"
            )
            return False, error_msg

    @staticmethod
    def validate_percentage_range(
        value: float,
        min_pct: float = 0.0,
        max_pct: float = 100.0
    ) -> Tuple[bool, str]:
        """
        Validate a percentage value is within range.

        Args:
            value: Percentage value to validate
            min_pct: Minimum percentage
            max_pct: Maximum percentage

        Returns:
            Tuple of (is_valid, error_message)
        """
        if min_pct <= value <= max_pct:
            return True, ""
        else:
            error_msg = f"Percentage {value}% is outside range [{min_pct}%, {max_pct}%]"
            return False, error_msg

    @staticmethod
    def validate_velocity(
        velocity_ms: float,
        target_velocity_ms: float,
        tolerance_pct: float = 2.5
    ) -> Tuple[bool, str]:
        """
        Validate impact velocity is within tolerance of target.

        Args:
            velocity_ms: Measured velocity (m/s)
            target_velocity_ms: Target velocity (m/s)
            tolerance_pct: Tolerance percentage

        Returns:
            Tuple of (is_valid, error_message)
        """
        delta = abs(velocity_ms - target_velocity_ms)
        max_delta = target_velocity_ms * (tolerance_pct / 100.0)

        if delta <= max_delta:
            return True, ""
        else:
            actual_pct = (delta / target_velocity_ms) * 100
            error_msg = (
                f"Velocity {velocity_ms} m/s deviates {actual_pct:.2f}% from target "
                f"{target_velocity_ms} m/s (tolerance: {tolerance_pct}%)"
            )
            return False, error_msg


class EquipmentValidator:
    """Validates equipment calibration and suitability."""

    @staticmethod
    def check_calibration_status(
        calibration_date: datetime,
        calibration_due_date: datetime,
        current_date: Optional[datetime] = None
    ) -> Tuple[bool, str]:
        """
        Check if equipment calibration is valid.

        Args:
            calibration_date: Date of last calibration
            calibration_due_date: Date calibration expires
            current_date: Current date (defaults to now)

        Returns:
            Tuple of (is_valid, error_message)
        """
        if current_date is None:
            current_date = datetime.now()

        if current_date > calibration_due_date:
            days_overdue = (current_date - calibration_due_date).days
            error_msg = f"Calibration expired {days_overdue} days ago"
            return False, error_msg
        elif current_date < calibration_date:
            error_msg = "Calibration date is in the future"
            return False, error_msg
        else:
            return True, ""

    @staticmethod
    def validate_equipment_range(
        measurement_value: float,
        equipment_min: float,
        equipment_max: float,
        parameter_name: str = "Measurement"
    ) -> Tuple[bool, str]:
        """
        Validate measurement is within equipment's operating range.

        Args:
            measurement_value: Value being measured
            equipment_min: Equipment minimum range
            equipment_max: Equipment maximum range
            parameter_name: Name of parameter

        Returns:
            Tuple of (is_valid, error_message)
        """
        if equipment_min <= measurement_value <= equipment_max:
            return True, ""
        else:
            error_msg = (
                f"{parameter_name} {measurement_value} is outside equipment range "
                f"[{equipment_min}, {equipment_max}]"
            )
            return False, error_msg


class EnvironmentalValidator:
    """Validates environmental test conditions."""

    @staticmethod
    def validate_conditions(
        temperature_celsius: Optional[float] = None,
        humidity_pct: Optional[float] = None,
        pressure_kpa: Optional[float] = None,
        limits: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, list]:
        """
        Validate environmental conditions are within acceptable ranges.

        Args:
            temperature_celsius: Ambient temperature
            humidity_pct: Relative humidity
            pressure_kpa: Atmospheric pressure
            limits: Dictionary of environmental limits

        Returns:
            Tuple of (all_valid, list_of_errors)
        """
        errors = []

        if limits is None:
            from src.utils.constants import ENVIRONMENTAL_LIMITS
            limits = ENVIRONMENTAL_LIMITS

        if temperature_celsius is not None:
            temp_limits = limits.get("temperature_celsius", {})
            if not (temp_limits.get("min", -999) <= temperature_celsius <= temp_limits.get("max", 999)):
                errors.append(
                    f"Temperature {temperature_celsius}°C outside range "
                    f"[{temp_limits.get('min')}°C, {temp_limits.get('max')}°C]"
                )

        if humidity_pct is not None:
            humidity_limits = limits.get("relative_humidity_pct", {})
            if not (humidity_limits.get("min", 0) <= humidity_pct <= humidity_limits.get("max", 100)):
                errors.append(
                    f"Humidity {humidity_pct}% outside range "
                    f"[{humidity_limits.get('min')}%, {humidity_limits.get('max')}%]"
                )

        if pressure_kpa is not None:
            pressure_limits = limits.get("atmospheric_pressure_kpa", {})
            if not (pressure_limits.get("min", 0) <= pressure_kpa <= pressure_limits.get("max", 200)):
                errors.append(
                    f"Pressure {pressure_kpa} kPa outside range "
                    f"[{pressure_limits.get('min')} kPa, {pressure_limits.get('max')} kPa]"
                )

        return len(errors) == 0, errors


class ResultValidator:
    """Validates test results and compliance."""

    @staticmethod
    def validate_power_degradation(
        power_before_w: float,
        power_after_w: float,
        max_degradation_pct: float = 5.0
    ) -> Tuple[bool, float, str]:
        """
        Validate power degradation is within acceptable limits.

        Args:
            power_before_w: Power before test (W)
            power_after_w: Power after test (W)
            max_degradation_pct: Maximum allowable degradation (%)

        Returns:
            Tuple of (is_valid, degradation_pct, message)
        """
        if power_before_w <= 0:
            return False, 0.0, "Invalid power_before value (must be > 0)"

        degradation_pct = ((power_before_w - power_after_w) / power_before_w) * 100

        if degradation_pct <= max_degradation_pct:
            message = f"Power degradation {degradation_pct:.2f}% is acceptable"
            return True, degradation_pct, message
        else:
            message = (
                f"Power degradation {degradation_pct:.2f}% exceeds limit "
                f"{max_degradation_pct}%"
            )
            return False, degradation_pct, message

    @staticmethod
    def calculate_combined_uncertainty(
        uncertainty_components: Dict[str, float]
    ) -> float:
        """
        Calculate combined standard uncertainty using RSS method.

        Args:
            uncertainty_components: Dictionary of uncertainty components

        Returns:
            Combined uncertainty (root sum square)
        """
        sum_squares = sum(u**2 for u in uncertainty_components.values())
        return math.sqrt(sum_squares)

    @staticmethod
    def validate_repeatability(
        measurements: list,
        max_rsd_pct: float = 5.0
    ) -> Tuple[bool, float, str]:
        """
        Validate measurement repeatability using RSD.

        Args:
            measurements: List of repeated measurements
            max_rsd_pct: Maximum allowable relative standard deviation (%)

        Returns:
            Tuple of (is_valid, rsd_pct, message)
        """
        if len(measurements) < 2:
            return False, 0.0, "At least 2 measurements required for repeatability check"

        mean_val = sum(measurements) / len(measurements)
        if mean_val == 0:
            return False, 0.0, "Mean value is zero, cannot calculate RSD"

        variance = sum((x - mean_val)**2 for x in measurements) / (len(measurements) - 1)
        std_dev = math.sqrt(variance)
        rsd_pct = (std_dev / mean_val) * 100

        if rsd_pct <= max_rsd_pct:
            message = f"Repeatability RSD {rsd_pct:.2f}% is acceptable"
            return True, rsd_pct, message
        else:
            message = f"Repeatability RSD {rsd_pct:.2f}% exceeds limit {max_rsd_pct}%"
            return False, rsd_pct, message
