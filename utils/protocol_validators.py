"""
Protocol-specific validators for IEC/ISO PV testing standards.

This module provides validators for test parameters according to:
- IEC 61215: Terrestrial PV modules - Design qualification
- IEC 61730: PV module safety qualification
- IEC 62716: Ammonia corrosion testing
- IEC 61701: Salt mist corrosion testing
- IEC 60904: PV device measurement standards
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

from .validation import ValidationResult, ValidationError
from .numeric_validators import validate_numeric_range


# ============================================================================
# IEC Standard Enums
# ============================================================================

class IEC61215TestType(Enum):
    """IEC 61215 test types."""
    MST_200 = "Damp Heat 200 cycles"           # Module Stability Test
    MST_50 = "Damp Heat 50 cycles"
    THERMAL_CYCLING = "Thermal Cycling"
    HUMIDITY_FREEZE = "Humidity Freeze"
    UV_PRECONDITIONING = "UV Preconditioning"
    OUTDOOR_EXPOSURE = "Outdoor Exposure"
    HOT_SPOT_ENDURANCE = "Hot-spot Endurance"
    REVERSE_CURRENT = "Reverse Current"
    MECHANICAL_LOAD = "Mechanical Load"
    HAIL_IMPACT = "Hail Impact"


class IEC61701SeverityLevel(Enum):
    """IEC 61701 salt mist severity levels."""
    LEVEL_1 = 1  # Low severity
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4
    LEVEL_5 = 5
    LEVEL_6 = 6  # High severity


class IEC61730SafetyClass(Enum):
    """IEC 61730 safety classes."""
    CLASS_A = "A"  # Hazardous voltage ≤ 120V DC or 75V AC
    CLASS_B = "B"  # Hazardous voltage > 120V DC or 75V AC
    CLASS_C = "C"  # Special applications


@dataclass
class TestStandard:
    """Test standard reference."""
    standard: str
    version: Optional[str] = None
    clause: Optional[str] = None

    def __str__(self) -> str:
        parts = [self.standard]
        if self.version:
            parts.append(f"v{self.version}")
        if self.clause:
            parts.append(f"Clause {self.clause}")
        return " ".join(parts)


# ============================================================================
# IEC 61215 Validators (Terrestrial PV Modules)
# ============================================================================

def validate_mst_sequence(
    cycles: int,
    temperature_celsius: float,
    humidity_percent: float,
    duration_hours: float,
    test_type: str = "MST-200"
) -> ValidationResult:
    """
    Validate IEC 61215 Module Stability Test (MST) sequence parameters.

    Standard requirements:
    - MST-200: 200 cycles at 85°C/85%RH, 1000 hours total
    - MST-50: 50 cycles at 85°C/85%RH, 250 hours total
    - Each cycle: typically 5 hours

    Args:
        cycles: Number of damp heat cycles
        temperature_celsius: Test temperature (typically 85°C)
        humidity_percent: Relative humidity (typically 85%)
        duration_hours: Total test duration
        test_type: MST type (MST-200 or MST-50)

    Returns:
        ValidationResult with MST compliance check

    Example:
        >>> result = validate_mst_sequence(
        ...     cycles=200,
        ...     temperature_celsius=85.0,
        ...     humidity_percent=85.0,
        ...     duration_hours=1000
        ... )
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value={
        "cycles": cycles,
        "temperature": temperature_celsius,
        "humidity": humidity_percent,
        "duration_hours": duration_hours
    })

    # Define requirements based on test type
    requirements = {
        "MST-200": {"cycles": 200, "temp": 85.0, "humidity": 85.0, "hours": 1000},
        "MST-50": {"cycles": 50, "temp": 85.0, "humidity": 85.0, "hours": 250},
    }

    if test_type not in requirements:
        result.add_error(f"Unknown MST test type: {test_type}. Expected: MST-200 or MST-50")
        return result

    req = requirements[test_type]

    # Validate cycles
    if cycles != req["cycles"]:
        result.add_error(
            f"{test_type} requires {req['cycles']} cycles, got {cycles}"
        )

    # Validate temperature (±2°C tolerance per IEC 61215)
    temp_result = validate_numeric_range(
        temperature_celsius,
        min_value=req["temp"],
        max_value=req["temp"],
        tolerance=2.0,
        field_name="Temperature"
    )
    if not temp_result.is_valid:
        result.is_valid = False
        result.errors.extend(temp_result.errors)

    # Validate humidity (±5% tolerance)
    humidity_result = validate_numeric_range(
        humidity_percent,
        min_value=req["humidity"],
        max_value=req["humidity"],
        tolerance=5.0,
        field_name="Relative Humidity"
    )
    if not humidity_result.is_valid:
        result.is_valid = False
        result.errors.extend(humidity_result.errors)

    # Validate duration
    expected_hours = req["hours"]
    if abs(duration_hours - expected_hours) > expected_hours * 0.05:  # 5% tolerance
        result.add_warning(
            f"Duration {duration_hours}h differs from typical {expected_hours}h "
            f"by more than 5%"
        )

    result.metadata["test_type"] = test_type
    result.metadata["requirements"] = req
    result.metadata["standard"] = "IEC 61215"

    return result


def validate_thermal_cycle(
    min_temp_celsius: float,
    max_temp_celsius: float,
    num_cycles: int,
    ramp_rate_celsius_per_min: Optional[float] = None
) -> ValidationResult:
    """
    Validate IEC 61215 thermal cycling parameters.

    Standard requirements:
    - Temperature range: -40°C to +85°C (or -40°C to +110°C for extended)
    - Number of cycles: typically 200 or 50
    - Ramp rate: not exceeding 100°C/hour

    Args:
        min_temp_celsius: Minimum cycle temperature
        max_temp_celsius: Maximum cycle temperature
        num_cycles: Number of thermal cycles
        ramp_rate_celsius_per_min: Temperature ramp rate (optional)

    Returns:
        ValidationResult with thermal cycle compliance

    Example:
        >>> result = validate_thermal_cycle(-40, 85, 200)
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value={
        "min_temp": min_temp_celsius,
        "max_temp": max_temp_celsius,
        "cycles": num_cycles
    })

    # Validate temperature range
    if min_temp_celsius > -40.0:
        result.add_error(
            f"Minimum temperature ({min_temp_celsius}°C) must be ≤ -40°C per IEC 61215"
        )

    if max_temp_celsius not in [85.0, 110.0]:
        if max_temp_celsius < 85.0:
            result.add_error(
                f"Maximum temperature ({max_temp_celsius}°C) must be ≥ 85°C"
            )
        elif 85.0 < max_temp_celsius < 110.0:
            result.add_warning(
                f"Non-standard max temperature {max_temp_celsius}°C. "
                f"Standard values: 85°C or 110°C"
            )
        elif max_temp_celsius > 110.0:
            result.add_error(
                f"Maximum temperature ({max_temp_celsius}°C) exceeds 110°C"
            )

    # Validate temperature delta
    temp_delta = max_temp_celsius - min_temp_celsius
    if temp_delta < 125.0:
        result.add_warning(
            f"Temperature delta ({temp_delta}°C) is less than typical 125°C or 150°C"
        )

    # Validate number of cycles
    if num_cycles not in [50, 200, 500]:
        result.add_warning(
            f"Number of cycles ({num_cycles}) is non-standard. "
            f"Typical values: 50, 200, or 500"
        )

    # Validate ramp rate
    if ramp_rate_celsius_per_min is not None:
        max_ramp_rate = 100.0 / 60.0  # 100°C/hour = 1.67°C/min
        if ramp_rate_celsius_per_min > max_ramp_rate:
            result.add_error(
                f"Ramp rate ({ramp_rate_celsius_per_min:.2f}°C/min) exceeds "
                f"maximum {max_ramp_rate:.2f}°C/min (100°C/hour)"
            )
        result.metadata["ramp_rate_celsius_per_min"] = ramp_rate_celsius_per_min

    result.metadata["temperature_delta"] = temp_delta
    result.metadata["standard"] = "IEC 61215"

    return result


# ============================================================================
# IEC 61730 Validators (PV Module Safety)
# ============================================================================

def validate_safety_test_voltage(
    test_voltage_v: float,
    system_voltage_v: float,
    safety_class: str = "B"
) -> ValidationResult:
    """
    Validate IEC 61730 safety test voltage parameters.

    Args:
        test_voltage_v: Applied test voltage
        system_voltage_v: Module system voltage
        safety_class: Safety class (A, B, or C)

    Returns:
        ValidationResult with safety compliance

    Example:
        >>> result = validate_safety_test_voltage(1000, 600, "B")
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value={
        "test_voltage": test_voltage_v,
        "system_voltage": system_voltage_v,
        "safety_class": safety_class
    })

    # Validate safety class
    try:
        safety_class_enum = IEC61730SafetyClass(safety_class)
    except ValueError:
        result.add_error(
            f"Invalid safety class '{safety_class}'. Must be A, B, or C"
        )
        return result

    # Test voltage requirements
    if safety_class == "A":
        if system_voltage_v > 120.0:
            result.add_error(
                f"Class A requires system voltage ≤ 120V DC, got {system_voltage_v}V"
            )
        min_test_voltage = system_voltage_v + 500
    elif safety_class == "B":
        if system_voltage_v <= 120.0:
            result.add_warning(
                f"Class B typically for voltage > 120V DC, got {system_voltage_v}V"
            )
        min_test_voltage = system_voltage_v + 1000
    else:  # Class C
        min_test_voltage = system_voltage_v + 1000

    # Validate test voltage
    if test_voltage_v < min_test_voltage:
        result.add_error(
            f"Test voltage ({test_voltage_v}V) must be ≥ {min_test_voltage}V "
            f"for Class {safety_class}"
        )

    result.metadata["min_test_voltage"] = min_test_voltage
    result.metadata["standard"] = "IEC 61730"

    return result


def validate_dielectric_strength(
    test_voltage_v: float,
    duration_seconds: float,
    leakage_current_ma: float,
    max_leakage_ma: float = 50.0
) -> ValidationResult:
    """
    Validate IEC 61730 dielectric strength test parameters.

    Args:
        test_voltage_v: Applied test voltage
        duration_seconds: Test duration (typically 60s)
        leakage_current_ma: Measured leakage current
        max_leakage_ma: Maximum allowed leakage current

    Returns:
        ValidationResult with dielectric test compliance

    Example:
        >>> result = validate_dielectric_strength(2000, 60, 5.0)
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value={
        "test_voltage": test_voltage_v,
        "duration": duration_seconds,
        "leakage_current": leakage_current_ma
    })

    # Validate duration (typically 60 seconds)
    if duration_seconds < 60.0:
        result.add_warning(
            f"Test duration ({duration_seconds}s) is less than typical 60s"
        )

    # Validate leakage current
    if leakage_current_ma > max_leakage_ma:
        result.add_error(
            f"Leakage current ({leakage_current_ma}mA) exceeds maximum "
            f"allowed ({max_leakage_ma}mA)"
        )

    result.metadata["max_leakage_current"] = max_leakage_ma
    result.metadata["standard"] = "IEC 61730"
    result.metadata["pass"] = leakage_current_ma <= max_leakage_ma

    return result


# ============================================================================
# IEC 62716 Validators (Ammonia Corrosion)
# ============================================================================

def validate_ammonia_concentration(
    concentration_ppm: float,
    test_duration_hours: float,
    temperature_celsius: float = 50.0,
    humidity_percent: float = 90.0
) -> ValidationResult:
    """
    Validate IEC 62716 ammonia corrosion test parameters.

    Standard requirements:
    - Ammonia concentration: 10-50 ppm (typically 30 ppm)
    - Test duration: typically 168 hours (7 days)
    - Temperature: 50°C ± 2°C
    - Humidity: 90% ± 5%

    Args:
        concentration_ppm: NH3 concentration in ppm
        test_duration_hours: Total test duration
        temperature_celsius: Test chamber temperature
        humidity_percent: Relative humidity

    Returns:
        ValidationResult with ammonia test compliance

    Example:
        >>> result = validate_ammonia_concentration(30, 168, 50, 90)
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value={
        "concentration_ppm": concentration_ppm,
        "duration_hours": test_duration_hours,
        "temperature": temperature_celsius,
        "humidity": humidity_percent
    })

    # Validate ammonia concentration (10-50 ppm)
    conc_result = validate_numeric_range(
        concentration_ppm,
        min_value=10.0,
        max_value=50.0,
        tolerance=2.0,  # ±2 ppm tolerance
        field_name="Ammonia concentration"
    )
    if not conc_result.is_valid:
        result.is_valid = False
        result.errors.extend(conc_result.errors)

    # Typical concentration is 30 ppm
    if abs(concentration_ppm - 30.0) > 5.0:
        result.add_warning(
            f"Concentration {concentration_ppm} ppm differs from typical 30 ppm"
        )

    # Validate temperature (50°C ± 2°C)
    temp_result = validate_numeric_range(
        temperature_celsius,
        min_value=50.0,
        max_value=50.0,
        tolerance=2.0,
        field_name="Temperature"
    )
    if not temp_result.is_valid:
        result.is_valid = False
        result.errors.extend(temp_result.errors)

    # Validate humidity (90% ± 5%)
    humidity_result = validate_numeric_range(
        humidity_percent,
        min_value=90.0,
        max_value=90.0,
        tolerance=5.0,
        field_name="Relative Humidity"
    )
    if not humidity_result.is_valid:
        result.is_valid = False
        result.errors.extend(humidity_result.errors)

    # Validate duration (typically 168 hours = 7 days)
    if test_duration_hours < 168.0:
        result.add_warning(
            f"Test duration ({test_duration_hours}h) is less than typical 168h (7 days)"
        )

    result.metadata["standard"] = "IEC 62716"
    result.metadata["typical_duration_hours"] = 168

    return result


# ============================================================================
# IEC 61701 Validators (Salt Mist Corrosion)
# ============================================================================

def validate_salt_mist_severity(
    severity_level: int,
    num_cycles: int,
    cycle_duration_hours: float = 2.0
) -> ValidationResult:
    """
    Validate IEC 61701 salt mist corrosion test severity level.

    Severity levels 1-6 with corresponding number of cycles:
    - Level 1: 10 cycles (marine, low)
    - Level 2: 20 cycles
    - Level 3: 30 cycles
    - Level 4: 40 cycles
    - Level 5: 50 cycles
    - Level 6: 60 cycles (marine, high)

    Args:
        severity_level: Severity level (1-6)
        num_cycles: Number of exposure cycles
        cycle_duration_hours: Duration per cycle (typically 2h)

    Returns:
        ValidationResult with salt mist compliance

    Example:
        >>> result = validate_salt_mist_severity(3, 30, 2.0)
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value={
        "severity_level": severity_level,
        "num_cycles": num_cycles,
        "cycle_duration": cycle_duration_hours
    })

    # Validate severity level
    if severity_level not in range(1, 7):
        result.add_error(
            f"Severity level must be 1-6, got {severity_level}"
        )
        return result

    # Expected number of cycles for each level
    expected_cycles = {
        1: 10, 2: 20, 3: 30, 4: 40, 5: 50, 6: 60
    }

    expected = expected_cycles[severity_level]
    if num_cycles != expected:
        result.add_error(
            f"Severity level {severity_level} requires {expected} cycles, "
            f"got {num_cycles}"
        )

    # Validate cycle duration (typically 2 hours)
    if abs(cycle_duration_hours - 2.0) > 0.5:
        result.add_warning(
            f"Cycle duration ({cycle_duration_hours}h) differs from typical 2h"
        )

    # Calculate total test duration
    total_hours = num_cycles * cycle_duration_hours
    result.metadata["total_duration_hours"] = total_hours
    result.metadata["expected_cycles"] = expected
    result.metadata["standard"] = "IEC 61701"

    return result


# ============================================================================
# IEC 60904 Validators (Measurement Standards)
# ============================================================================

def validate_stc_conditions(
    irradiance_w_m2: float,
    temperature_celsius: float,
    spectrum: str = "AM1.5G"
) -> ValidationResult:
    """
    Validate Standard Test Conditions (STC) per IEC 60904-3.

    STC requirements:
    - Irradiance: 1000 W/m² ± 2%
    - Module temperature: 25°C ± 2°C
    - Spectral distribution: AM1.5G

    Args:
        irradiance_w_m2: Irradiance in W/m²
        temperature_celsius: Module temperature
        spectrum: Spectral distribution reference

    Returns:
        ValidationResult with STC compliance

    Example:
        >>> result = validate_stc_conditions(1000, 25, "AM1.5G")
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value={
        "irradiance": irradiance_w_m2,
        "temperature": temperature_celsius,
        "spectrum": spectrum
    })

    # Validate irradiance (1000 W/m² ± 2%)
    irr_result = validate_numeric_range(
        irradiance_w_m2,
        min_value=1000.0,
        max_value=1000.0,
        tolerance=20.0,  # 2% of 1000
        field_name="Irradiance"
    )
    if not irr_result.is_valid:
        result.is_valid = False
        result.errors.extend(irr_result.errors)

    # Validate temperature (25°C ± 2°C)
    temp_result = validate_numeric_range(
        temperature_celsius,
        min_value=25.0,
        max_value=25.0,
        tolerance=2.0,
        field_name="Module Temperature"
    )
    if not temp_result.is_valid:
        result.is_valid = False
        result.errors.extend(temp_result.errors)

    # Validate spectrum
    allowed_spectra = ["AM1.5G", "AM1.5", "AM1.5D", "AM0"]
    if spectrum not in allowed_spectra:
        result.add_warning(
            f"Spectrum '{spectrum}' is non-standard. "
            f"Standard spectra: {', '.join(allowed_spectra)}"
        )

    result.metadata["standard"] = "IEC 60904-3"
    result.metadata["stc_compliant"] = result.is_valid

    return result


def validate_module_power_rating(
    measured_power_w: float,
    nameplate_power_w: float,
    tolerance_percent: float = 3.0
) -> ValidationResult:
    """
    Validate measured power against nameplate rating.

    Typical tolerance: -0% to +3% for positive tolerance modules,
    or ±3% for standard modules.

    Args:
        measured_power_w: Measured power at STC
        nameplate_power_w: Nameplate power rating
        tolerance_percent: Allowed tolerance (±%)

    Returns:
        ValidationResult with power rating validation

    Example:
        >>> result = validate_module_power_rating(320, 315, tolerance_percent=3.0)
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value={
        "measured_power": measured_power_w,
        "nameplate_power": nameplate_power_w
    })

    # Calculate deviation
    deviation_w = measured_power_w - nameplate_power_w
    deviation_percent = (deviation_w / nameplate_power_w) * 100

    # Check tolerance
    if abs(deviation_percent) > tolerance_percent:
        result.add_error(
            f"Measured power ({measured_power_w}W) deviates {deviation_percent:+.2f}% "
            f"from nameplate ({nameplate_power_w}W), exceeds ±{tolerance_percent}% tolerance"
        )

    # Check if below nameplate (always a concern)
    if measured_power_w < nameplate_power_w:
        result.add_warning(
            f"Measured power is {abs(deviation_percent):.2f}% below nameplate rating"
        )

    result.metadata["deviation_w"] = deviation_w
    result.metadata["deviation_percent"] = deviation_percent
    result.metadata["tolerance_percent"] = tolerance_percent

    return result


# ============================================================================
# Test Sequence Validators
# ============================================================================

def validate_test_sequence_dependency(
    completed_tests: List[str],
    required_prerequisites: Dict[str, List[str]]
) -> ValidationResult:
    """
    Validate test sequence dependencies.

    Args:
        completed_tests: List of completed test names
        required_prerequisites: Dict mapping test names to required prerequisite tests

    Returns:
        ValidationResult with sequence validation

    Example:
        >>> completed = ["Visual Inspection", "Electrical Testing"]
        >>> prerequisites = {
        ...     "Electrical Testing": ["Visual Inspection"],
        ...     "MST": ["Electrical Testing", "Visual Inspection"]
        ... }
        >>> result = validate_test_sequence_dependency(completed, prerequisites)
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value=completed_tests)

    missing_prerequisites = {}

    for test, prereqs in required_prerequisites.items():
        if test in completed_tests:
            # Check if all prerequisites are completed
            missing = [p for p in prereqs if p not in completed_tests]
            if missing:
                missing_prerequisites[test] = missing
                result.add_error(
                    f"Test '{test}' requires prerequisites: {', '.join(missing)}"
                )

    if missing_prerequisites:
        result.metadata["missing_prerequisites"] = missing_prerequisites

    result.metadata["completed_tests"] = completed_tests
    result.metadata["total_dependencies"] = len(required_prerequisites)

    return result
