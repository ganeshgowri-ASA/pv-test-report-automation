"""
Numeric validation utilities for PV test measurements.

This module provides validators for numeric data including range checks,
statistical outlier detection, measurement uncertainty propagation, and
significant figures handling per IEC 60904 standards.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import List, Optional, Tuple, Union
import math
import statistics

from .validation import ValidationResult, ValidationError


class UnitType(Enum):
    """Supported unit types for conversion validation."""
    POWER = "power"          # W, kW, mW
    VOLTAGE = "voltage"      # V, mV
    CURRENT = "current"      # A, mA
    TEMPERATURE = "temperature"  # °C, K
    PERCENTAGE = "percentage"    # %
    RESISTANCE = "resistance"    # Ω, kΩ, mΩ


# Unit conversion factors to base units
UNIT_CONVERSIONS = {
    # Power (base: W)
    "W": 1.0,
    "kW": 1000.0,
    "mW": 0.001,
    "MW": 1_000_000.0,

    # Voltage (base: V)
    "V": 1.0,
    "mV": 0.001,
    "kV": 1000.0,

    # Current (base: A)
    "A": 1.0,
    "mA": 0.001,
    "kA": 1000.0,

    # Temperature (special handling)
    "°C": 1.0,
    "C": 1.0,
    "K": 1.0,  # Requires offset

    # Resistance (base: Ω)
    "Ω": 1.0,
    "ohm": 1.0,
    "kΩ": 1000.0,
    "kohm": 1000.0,
    "mΩ": 0.001,
    "mohm": 0.001,
}


@dataclass
class MeasurementUncertainty:
    """
    Measurement uncertainty per ISO/IEC Guide 98-3 (GUM).

    Attributes:
        value: Measured value
        uncertainty: Combined standard uncertainty
        k_factor: Coverage factor (typically 2 for 95% confidence)
        expanded_uncertainty: k * uncertainty
        relative_uncertainty: uncertainty / value (%)
    """
    value: float
    uncertainty: float
    k_factor: float = 2.0

    @property
    def expanded_uncertainty(self) -> float:
        """Calculate expanded uncertainty."""
        return self.k_factor * self.uncertainty

    @property
    def relative_uncertainty(self) -> float:
        """Calculate relative uncertainty as percentage."""
        if self.value == 0:
            return float('inf')
        return abs(self.uncertainty / self.value) * 100

    def __str__(self) -> str:
        """Format as: value ± expanded_uncertainty."""
        return f"{self.value} ± {self.expanded_uncertainty}"


# ============================================================================
# Range Validators
# ============================================================================

def validate_numeric_range(
    value: Union[int, float],
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    tolerance: float = 0.0,
    inclusive: bool = True,
    field_name: Optional[str] = None
) -> ValidationResult:
    """
    Validate numeric value is within specified range with tolerance.

    Args:
        value: Numeric value to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        tolerance: Acceptable tolerance (±)
        inclusive: Include boundary values (default True)
        field_name: Name of field for error messages

    Returns:
        ValidationResult with range check details

    Example:
        >>> result = validate_numeric_range(85.2, min_value=83.0, max_value=87.0, tolerance=2.0)
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value=value)
    field = field_name or "Value"

    # Type check
    if not isinstance(value, (int, float)):
        result.add_error(f"{field} must be numeric")
        return result

    if math.isnan(value) or math.isinf(value):
        result.add_error(f"{field} must be a finite number")
        return result

    # Range checks with tolerance
    if min_value is not None:
        lower_bound = min_value - tolerance
        if inclusive:
            if value < lower_bound:
                result.add_error(
                    f"{field} ({value}) is below minimum ({min_value} - {tolerance} = {lower_bound})"
                )
        else:
            if value <= lower_bound:
                result.add_error(
                    f"{field} ({value}) must be greater than {lower_bound}"
                )

    if max_value is not None:
        upper_bound = max_value + tolerance
        if inclusive:
            if value > upper_bound:
                result.add_error(
                    f"{field} ({value}) exceeds maximum ({max_value} + {tolerance} = {upper_bound})"
                )
        else:
            if value >= upper_bound:
                result.add_error(
                    f"{field} ({value}) must be less than {upper_bound}"
                )

    # Metadata
    result.metadata["range"] = {
        "min": min_value,
        "max": max_value,
        "tolerance": tolerance,
        "within_range": result.is_valid
    }

    return result


def validate_percentage(
    value: Union[int, float],
    min_percent: float = 0.0,
    max_percent: float = 100.0,
    allow_negative: bool = False
) -> ValidationResult:
    """
    Validate percentage value.

    Args:
        value: Percentage value to validate
        min_percent: Minimum percentage (default 0)
        max_percent: Maximum percentage (default 100)
        allow_negative: Allow negative percentages

    Returns:
        ValidationResult

    Example:
        >>> result = validate_percentage(95.5)
        >>> assert result.is_valid
    """
    min_val = -100.0 if allow_negative else min_percent
    return validate_numeric_range(
        value,
        min_value=min_val,
        max_value=max_percent,
        field_name="Percentage"
    )


# ============================================================================
# Statistical Validators
# ============================================================================

def detect_outliers_zscore(
    data: List[float],
    threshold: float = 3.0,
    return_indices: bool = False
) -> ValidationResult:
    """
    Detect outliers using Z-score method.

    Outliers are values with |z-score| > threshold (typically 3.0).

    Args:
        data: List of numeric measurements
        threshold: Z-score threshold for outliers
        return_indices: Return indices of outliers

    Returns:
        ValidationResult with outlier information

    Example:
        >>> data = [10.1, 10.2, 10.0, 10.3, 50.0]  # 50.0 is outlier
        >>> result = detect_outliers_zscore(data)
        >>> len(result.value["outliers"])
        1
    """
    result = ValidationResult(is_valid=True, value={"outliers": [], "clean_data": []})

    if len(data) < 3:
        result.add_warning("Need at least 3 data points for outlier detection")
        result.value["clean_data"] = data
        return result

    try:
        mean = statistics.mean(data)
        stdev = statistics.stdev(data)

        if stdev == 0:
            result.add_warning("Standard deviation is zero, no outliers detected")
            result.value["clean_data"] = data
            return result

        outliers = []
        outlier_indices = []
        clean_data = []

        for i, value in enumerate(data):
            z_score = abs((value - mean) / stdev)

            if z_score > threshold:
                outliers.append({
                    "value": value,
                    "z_score": z_score,
                    "index": i
                })
                outlier_indices.append(i)
            else:
                clean_data.append(value)

        result.value["outliers"] = outliers
        result.value["clean_data"] = clean_data
        result.metadata["mean"] = mean
        result.metadata["stdev"] = stdev
        result.metadata["threshold"] = threshold
        result.metadata["outlier_count"] = len(outliers)

        if return_indices:
            result.value["outlier_indices"] = outlier_indices

        # Warning if outliers found
        if outliers:
            result.add_warning(
                f"Found {len(outliers)} outlier(s) with Z-score > {threshold}"
            )

    except Exception as e:
        result.add_error(f"Outlier detection failed: {str(e)}")

    return result


def detect_outliers_iqr(
    data: List[float],
    multiplier: float = 1.5,
    return_indices: bool = False
) -> ValidationResult:
    """
    Detect outliers using Interquartile Range (IQR) method.

    Outliers are values outside [Q1 - k*IQR, Q3 + k*IQR] where k=multiplier.

    Args:
        data: List of numeric measurements
        multiplier: IQR multiplier (typically 1.5)
        return_indices: Return indices of outliers

    Returns:
        ValidationResult with outlier information

    Example:
        >>> data = [10.1, 10.2, 10.0, 10.3, 50.0]
        >>> result = detect_outliers_iqr(data)
        >>> len(result.value["outliers"])
        1
    """
    result = ValidationResult(is_valid=True, value={"outliers": [], "clean_data": []})

    if len(data) < 4:
        result.add_warning("Need at least 4 data points for IQR outlier detection")
        result.value["clean_data"] = data
        return result

    try:
        sorted_data = sorted(data)
        q1 = statistics.quantiles(sorted_data, n=4)[0]  # 25th percentile
        q3 = statistics.quantiles(sorted_data, n=4)[2]  # 75th percentile
        iqr = q3 - q1

        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr

        outliers = []
        outlier_indices = []
        clean_data = []

        for i, value in enumerate(data):
            if value < lower_bound or value > upper_bound:
                outliers.append({
                    "value": value,
                    "deviation": min(abs(value - lower_bound), abs(value - upper_bound)),
                    "index": i
                })
                outlier_indices.append(i)
            else:
                clean_data.append(value)

        result.value["outliers"] = outliers
        result.value["clean_data"] = clean_data
        result.metadata["q1"] = q1
        result.metadata["q3"] = q3
        result.metadata["iqr"] = iqr
        result.metadata["lower_bound"] = lower_bound
        result.metadata["upper_bound"] = upper_bound
        result.metadata["outlier_count"] = len(outliers)

        if return_indices:
            result.value["outlier_indices"] = outlier_indices

        if outliers:
            result.add_warning(
                f"Found {len(outliers)} outlier(s) outside IQR bounds "
                f"[{lower_bound:.2f}, {upper_bound:.2f}]"
            )

    except Exception as e:
        result.add_error(f"IQR outlier detection failed: {str(e)}")

    return result


# ============================================================================
# Measurement Uncertainty
# ============================================================================

def calculate_combined_uncertainty(
    uncertainties: List[float],
    correlation: Optional[List[List[float]]] = None
) -> ValidationResult:
    """
    Calculate combined standard uncertainty from multiple sources.

    Per ISO/IEC Guide 98-3 (GUM): u_c = sqrt(sum(u_i^2)) for uncorrelated sources.

    Args:
        uncertainties: List of standard uncertainties
        correlation: Correlation matrix for correlated sources (optional)

    Returns:
        ValidationResult with combined uncertainty

    Example:
        >>> result = calculate_combined_uncertainty([0.1, 0.05, 0.08])
        >>> result.value  # Combined uncertainty
        0.14177...
    """
    result = ValidationResult(is_valid=True, value=0.0)

    if not uncertainties:
        result.add_error("No uncertainties provided")
        return result

    try:
        if correlation is None:
            # Uncorrelated: RSS (Root Sum of Squares)
            combined = math.sqrt(sum(u**2 for u in uncertainties))
        else:
            # Correlated: matrix multiplication
            n = len(uncertainties)
            if len(correlation) != n or any(len(row) != n for row in correlation):
                result.add_error("Correlation matrix dimensions must match uncertainties")
                return result

            # u_c^2 = sum_i sum_j (u_i * u_j * r_ij)
            variance = 0.0
            for i in range(n):
                for j in range(n):
                    variance += uncertainties[i] * uncertainties[j] * correlation[i][j]

            combined = math.sqrt(variance)

        result.value = combined
        result.metadata["method"] = "correlated" if correlation else "uncorrelated"
        result.metadata["sources"] = len(uncertainties)
        result.metadata["individual_uncertainties"] = uncertainties

    except Exception as e:
        result.add_error(f"Uncertainty calculation failed: {str(e)}")

    return result


def propagate_uncertainty(
    value: float,
    uncertainty: float,
    operation: str,
    operand_value: float,
    operand_uncertainty: float
) -> ValidationResult:
    """
    Propagate uncertainty through mathematical operations.

    Supports: addition, subtraction, multiplication, division.

    Args:
        value: First operand value
        uncertainty: First operand uncertainty
        operation: Mathematical operation (+, -, *, /)
        operand_value: Second operand value
        operand_uncertainty: Second operand uncertainty

    Returns:
        ValidationResult with propagated uncertainty

    Example:
        >>> result = propagate_uncertainty(10.0, 0.1, "*", 5.0, 0.05)
        >>> result.value["result"]
        50.0
    """
    result = ValidationResult(is_valid=True, value={})

    try:
        # Calculate result
        if operation == "+":
            result_value = value + operand_value
            # u_sum = sqrt(u1^2 + u2^2)
            result_uncertainty = math.sqrt(uncertainty**2 + operand_uncertainty**2)

        elif operation == "-":
            result_value = value - operand_value
            # Same as addition
            result_uncertainty = math.sqrt(uncertainty**2 + operand_uncertainty**2)

        elif operation == "*":
            result_value = value * operand_value
            # u_prod/prod = sqrt((u1/v1)^2 + (u2/v2)^2)
            rel_unc = math.sqrt(
                (uncertainty/value)**2 + (operand_uncertainty/operand_value)**2
            )
            result_uncertainty = abs(result_value) * rel_unc

        elif operation == "/":
            if operand_value == 0:
                result.add_error("Division by zero")
                return result
            result_value = value / operand_value
            # Same as multiplication
            rel_unc = math.sqrt(
                (uncertainty/value)**2 + (operand_uncertainty/operand_value)**2
            )
            result_uncertainty = abs(result_value) * rel_unc

        else:
            result.add_error(f"Unsupported operation: {operation}")
            return result

        result.value = {
            "result": result_value,
            "uncertainty": result_uncertainty,
            "relative_uncertainty_percent": (result_uncertainty/abs(result_value))*100 if result_value != 0 else 0
        }

        result.metadata["operation"] = operation
        result.metadata["operands"] = {
            "v1": value, "u1": uncertainty,
            "v2": operand_value, "u2": operand_uncertainty
        }

    except Exception as e:
        result.add_error(f"Uncertainty propagation failed: {str(e)}")

    return result


# ============================================================================
# Significant Figures (IEC 60904)
# ============================================================================

def count_significant_figures(value: Union[int, float, str]) -> int:
    """
    Count significant figures in a number.

    Args:
        value: Numeric value or string representation

    Returns:
        Number of significant figures

    Example:
        >>> count_significant_figures(0.00123)
        3
        >>> count_significant_figures(1.230)
        4
    """
    # Convert to string
    value_str = str(value)

    # Remove sign
    value_str = value_str.lstrip('-+')

    # Handle scientific notation
    if 'e' in value_str.lower():
        value_str = value_str.split('e')[0]

    # Remove decimal point
    value_str = value_str.replace('.', '')

    # Remove leading zeros
    value_str = value_str.lstrip('0')

    # Count remaining digits
    return len(value_str) if value_str else 1


def round_to_sig_figs(
    value: float,
    sig_figs: int,
    standard: str = "IEC 60904"
) -> ValidationResult:
    """
    Round value to specified significant figures per IEC 60904.

    Args:
        value: Value to round
        sig_figs: Number of significant figures
        standard: Rounding standard (IEC 60904, IEEE 754)

    Returns:
        ValidationResult with rounded value

    Example:
        >>> result = round_to_sig_figs(123.456, 4)
        >>> result.value
        123.5
    """
    result = ValidationResult(is_valid=True, value=value)

    if sig_figs < 1:
        result.add_error("Significant figures must be at least 1")
        return result

    try:
        if value == 0:
            result.value = 0.0
            return result

        # Determine the order of magnitude
        magnitude = math.floor(math.log10(abs(value)))

        # Calculate decimal places needed
        decimal_places = sig_figs - magnitude - 1

        # Round using Decimal for precision
        decimal_value = Decimal(str(value))
        rounded = float(decimal_value.quantize(
            Decimal(10) ** -decimal_places,
            rounding=ROUND_HALF_UP
        ))

        result.value = rounded
        result.metadata["original_value"] = value
        result.metadata["sig_figs"] = sig_figs
        result.metadata["standard"] = standard

    except Exception as e:
        result.add_error(f"Rounding failed: {str(e)}")

    return result


def validate_significant_figures(
    value: float,
    uncertainty: float,
    min_sig_figs: int = 2
) -> ValidationResult:
    """
    Validate that value has appropriate significant figures based on uncertainty.

    Rule: Report value to same decimal place as first significant figure of uncertainty.

    Args:
        value: Measured value
        uncertainty: Measurement uncertainty
        min_sig_figs: Minimum required significant figures

    Returns:
        ValidationResult with sig figs compliance

    Example:
        >>> result = validate_significant_figures(123.456, 0.05, min_sig_figs=3)
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value=value)

    # Count sig figs
    value_sig_figs = count_significant_figures(value)
    unc_sig_figs = count_significant_figures(uncertainty)

    if value_sig_figs < min_sig_figs:
        result.add_warning(
            f"Value has {value_sig_figs} significant figures, "
            f"minimum recommended: {min_sig_figs}"
        )

    # Check if uncertainty is reported appropriately (1-2 sig figs)
    if unc_sig_figs > 2:
        result.add_warning(
            f"Uncertainty should typically have 1-2 significant figures, "
            f"found {unc_sig_figs}"
        )

    result.metadata["value_sig_figs"] = value_sig_figs
    result.metadata["uncertainty_sig_figs"] = unc_sig_figs
    result.metadata["min_required"] = min_sig_figs

    return result


# ============================================================================
# Unit Conversion Validators
# ============================================================================

def convert_units(
    value: float,
    from_unit: str,
    to_unit: str,
    value_type: Optional[UnitType] = None
) -> ValidationResult:
    """
    Convert value between units with validation.

    Args:
        value: Numeric value to convert
        from_unit: Source unit (e.g., "mW")
        to_unit: Target unit (e.g., "W")
        value_type: Type of measurement (optional validation)

    Returns:
        ValidationResult with converted value

    Example:
        >>> result = convert_units(1500, "mW", "W")
        >>> result.value
        1.5
    """
    result = ValidationResult(is_valid=True, value=value)

    # Check if units exist
    if from_unit not in UNIT_CONVERSIONS:
        result.add_error(f"Unknown source unit: {from_unit}")
        return result

    if to_unit not in UNIT_CONVERSIONS:
        result.add_error(f"Unknown target unit: {to_unit}")
        return result

    try:
        # Special handling for temperature
        if from_unit in ["°C", "C", "K"] or to_unit in ["°C", "C", "K"]:
            if from_unit == "K" and to_unit in ["°C", "C"]:
                converted = value - 273.15
            elif from_unit in ["°C", "C"] and to_unit == "K":
                converted = value + 273.15
            else:
                converted = value  # Same temperature scale
        else:
            # Standard conversion: to base unit, then to target
            base_value = value * UNIT_CONVERSIONS[from_unit]
            converted = base_value / UNIT_CONVERSIONS[to_unit]

        result.value = converted
        result.metadata["original_value"] = value
        result.metadata["from_unit"] = from_unit
        result.metadata["to_unit"] = to_unit
        result.metadata["conversion_factor"] = converted / value if value != 0 else 0

    except Exception as e:
        result.add_error(f"Unit conversion failed: {str(e)}")

    return result


def validate_unit_consistency(
    measurements: List[Tuple[float, str]],
    expected_unit: str
) -> ValidationResult:
    """
    Validate that all measurements use consistent units or can be converted.

    Args:
        measurements: List of (value, unit) tuples
        expected_unit: Expected unit for all measurements

    Returns:
        ValidationResult with normalized measurements

    Example:
        >>> measurements = [(100, "W"), (0.1, "kW"), (100000, "mW")]
        >>> result = validate_unit_consistency(measurements, "W")
        >>> all(val == 100.0 for val in result.value)
        True
    """
    result = ValidationResult(is_valid=True, value=[])

    normalized = []
    for value, unit in measurements:
        # Convert to expected unit
        conv_result = convert_units(value, unit, expected_unit)

        if not conv_result.is_valid:
            result.is_valid = False
            result.errors.extend(conv_result.errors)
            continue

        normalized.append(conv_result.value)

    result.value = normalized
    result.metadata["expected_unit"] = expected_unit
    result.metadata["measurement_count"] = len(measurements)

    return result
