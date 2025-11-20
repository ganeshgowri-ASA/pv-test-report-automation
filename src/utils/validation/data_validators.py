"""
Core Data Validation Functions

Provides comprehensive validation for PV test data including IEC/ISO compliance
validators, data type validators, and range validators per international standards.

Standards covered:
- IEC 61853: Performance testing and energy rating
- IEC 62804: Test methods for detection of potential-induced degradation
- IEC 60904: Photovoltaic devices measurement procedures
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
import numpy as np

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationError(Exception):
    """Base exception for validation errors."""
    pass


class IECComplianceError(ValidationError):
    """Exception raised when IEC standard compliance fails."""
    pass


class RangeValidationError(ValidationError):
    """Exception raised when value is outside acceptable range."""
    pass


class DataTypeValidationError(ValidationError):
    """Exception raised when data type validation fails."""
    pass


@dataclass
class ValidationIssue:
    """Represents a single validation issue."""
    severity: ValidationSeverity
    message: str
    field: Optional[str] = None
    value: Optional[Any] = None
    expected: Optional[str] = None
    standard: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "severity": self.severity.value,
            "message": self.message,
            "field": self.field,
            "value": self.value,
            "expected": self.expected,
            "standard": self.standard,
        }


@dataclass
class ValidationReport:
    """Comprehensive validation report."""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    warnings: int = 0
    errors: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_issue(self, issue: ValidationIssue) -> None:
        """Add a validation issue to the report."""
        self.issues.append(issue)
        if issue.severity == ValidationSeverity.WARNING:
            self.warnings += 1
        elif issue.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL):
            self.errors += 1
            self.is_valid = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "is_valid": self.is_valid,
            "issues": [issue.to_dict() for issue in self.issues],
            "warnings": self.warnings,
            "errors": self.errors,
            "metadata": self.metadata,
        }

    def get_summary(self) -> str:
        """Get a human-readable summary."""
        status = "PASSED" if self.is_valid else "FAILED"
        return f"Validation {status}: {self.errors} errors, {self.warnings} warnings"


class DataValidator:
    """
    Core data validator for PV test measurements.

    Provides comprehensive validation capabilities with configurable standards
    compliance and detailed reporting.
    """

    # IEC 61853 standard ranges
    IEC_61853_RANGES = {
        "irradiance": (0, 1500),  # W/m²
        "module_temperature": (-40, 85),  # °C
        "ambient_temperature": (-40, 60),  # °C
        "wind_speed": (0, 25),  # m/s
        "angle_of_incidence": (0, 90),  # degrees
    }

    # IEC 60904 measurement ranges
    IEC_60904_RANGES = {
        "voltage": (0, 1500),  # V (typical max for PV modules)
        "current": (0, 50),  # A (typical max for PV modules)
        "power": (0, 750),  # W (typical max for PV modules)
    }

    # IEC 62804 test conditions
    IEC_62804_CONDITIONS = {
        "test_voltage": (-1500, 1500),  # V
        "test_duration": (0, 192),  # hours
        "temperature": (60, 85),  # °C
        "relative_humidity": (0, 100),  # %
    }

    def __init__(self, strict_mode: bool = True):
        """
        Initialize data validator.

        Args:
            strict_mode: If True, raises exceptions on errors. If False, collects issues.
        """
        self.strict_mode = strict_mode
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def validate_batch(
        self,
        data_list: List[Dict[str, Any]],
        validation_func: callable
    ) -> List[ValidationReport]:
        """
        Validate a batch of data items.

        Args:
            data_list: List of data dictionaries to validate
            validation_func: Validation function to apply to each item

        Returns:
            List of validation reports, one per item
        """
        reports = []
        for idx, data in enumerate(data_list):
            try:
                report = validation_func(data)
                report.metadata["batch_index"] = idx
                reports.append(report)
            except Exception as e:
                self.logger.error(f"Validation failed for batch item {idx}: {e}")
                report = ValidationReport(is_valid=False)
                report.add_issue(ValidationIssue(
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Validation exception: {str(e)}",
                    field=f"batch_item_{idx}"
                ))
                reports.append(report)

        return reports


def validate_voltage(
    voltage: Union[float, np.ndarray],
    min_voltage: Optional[float] = None,
    max_voltage: Optional[float] = None,
    standard: str = "IEC 60904"
) -> ValidationReport:
    """
    Validate voltage measurements per IEC 60904 standards.

    Args:
        voltage: Voltage value(s) in Volts
        min_voltage: Minimum acceptable voltage (optional)
        max_voltage: Maximum acceptable voltage (optional)
        standard: Standard to validate against

    Returns:
        ValidationReport with validation results
    """
    report = ValidationReport(is_valid=True)

    # Use default ranges if not specified
    if min_voltage is None:
        min_voltage = DataValidator.IEC_60904_RANGES["voltage"][0]
    if max_voltage is None:
        max_voltage = DataValidator.IEC_60904_RANGES["voltage"][1]

    # Convert to array for uniform handling
    voltage_array = np.atleast_1d(voltage)

    # Check for NaN or infinite values
    if np.any(np.isnan(voltage_array)):
        report.add_issue(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message="Voltage contains NaN values",
            field="voltage",
            standard=standard
        ))

    if np.any(np.isinf(voltage_array)):
        report.add_issue(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message="Voltage contains infinite values",
            field="voltage",
            standard=standard
        ))

    # Check range
    valid_voltages = voltage_array[~np.isnan(voltage_array) & ~np.isinf(voltage_array)]
    if len(valid_voltages) > 0:
        if np.any(valid_voltages < min_voltage):
            count = np.sum(valid_voltages < min_voltage)
            report.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"{count} voltage value(s) below minimum",
                field="voltage",
                value=float(np.min(valid_voltages)),
                expected=f">= {min_voltage} V",
                standard=standard
            ))

        if np.any(valid_voltages > max_voltage):
            count = np.sum(valid_voltages > max_voltage)
            report.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"{count} voltage value(s) above maximum",
                field="voltage",
                value=float(np.max(valid_voltages)),
                expected=f"<= {max_voltage} V",
                standard=standard
            ))

    # Check for negative voltages (warning, may be valid in some contexts)
    if np.any(valid_voltages < 0):
        report.add_issue(ValidationIssue(
            severity=ValidationSeverity.WARNING,
            message="Negative voltage values detected",
            field="voltage",
            value=float(np.min(valid_voltages)),
            standard=standard
        ))

    return report


def validate_current(
    current: Union[float, np.ndarray],
    min_current: Optional[float] = None,
    max_current: Optional[float] = None,
    standard: str = "IEC 60904"
) -> ValidationReport:
    """
    Validate current measurements per IEC 60904 standards.

    Args:
        current: Current value(s) in Amperes
        min_current: Minimum acceptable current (optional)
        max_current: Maximum acceptable current (optional)
        standard: Standard to validate against

    Returns:
        ValidationReport with validation results
    """
    report = ValidationReport(is_valid=True)

    # Use default ranges if not specified
    if min_current is None:
        min_current = DataValidator.IEC_60904_RANGES["current"][0]
    if max_current is None:
        max_current = DataValidator.IEC_60904_RANGES["current"][1]

    # Convert to array for uniform handling
    current_array = np.atleast_1d(current)

    # Check for NaN or infinite values
    if np.any(np.isnan(current_array)):
        report.add_issue(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message="Current contains NaN values",
            field="current",
            standard=standard
        ))

    if np.any(np.isinf(current_array)):
        report.add_issue(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message="Current contains infinite values",
            field="current",
            standard=standard
        ))

    # Check range
    valid_currents = current_array[~np.isnan(current_array) & ~np.isinf(current_array)]
    if len(valid_currents) > 0:
        if np.any(valid_currents < min_current):
            count = np.sum(valid_currents < min_current)
            report.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"{count} current value(s) below minimum",
                field="current",
                value=float(np.min(valid_currents)),
                expected=f">= {min_current} A",
                standard=standard
            ))

        if np.any(valid_currents > max_current):
            count = np.sum(valid_currents > max_current)
            report.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"{count} current value(s) above maximum",
                field="current",
                value=float(np.max(valid_currents)),
                expected=f"<= {max_current} A",
                standard=standard
            ))

    return report


def validate_power(
    power: Union[float, np.ndarray],
    voltage: Optional[Union[float, np.ndarray]] = None,
    current: Optional[Union[float, np.ndarray]] = None,
    tolerance: float = 0.01,
    standard: str = "IEC 60904"
) -> ValidationReport:
    """
    Validate power measurements and check consistency with V and I.

    Args:
        power: Power value(s) in Watts
        voltage: Optional voltage values for cross-validation
        current: Optional current values for cross-validation
        tolerance: Relative tolerance for P = V * I check (default 1%)
        standard: Standard to validate against

    Returns:
        ValidationReport with validation results
    """
    report = ValidationReport(is_valid=True)

    # Convert to array for uniform handling
    power_array = np.atleast_1d(power)

    # Check for NaN or infinite values
    if np.any(np.isnan(power_array)):
        report.add_issue(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message="Power contains NaN values",
            field="power",
            standard=standard
        ))

    if np.any(np.isinf(power_array)):
        report.add_issue(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message="Power contains infinite values",
            field="power",
            standard=standard
        ))

    # Check for negative power (warning)
    valid_power = power_array[~np.isnan(power_array) & ~np.isinf(power_array)]
    if len(valid_power) > 0 and np.any(valid_power < 0):
        report.add_issue(ValidationIssue(
            severity=ValidationSeverity.WARNING,
            message="Negative power values detected",
            field="power",
            value=float(np.min(valid_power)),
            standard=standard
        ))

    # Cross-validate with voltage and current if provided
    if voltage is not None and current is not None:
        voltage_array = np.atleast_1d(voltage)
        current_array = np.atleast_1d(current)

        if len(voltage_array) == len(current_array) == len(power_array):
            calculated_power = voltage_array * current_array
            valid_indices = (
                ~np.isnan(voltage_array) &
                ~np.isnan(current_array) &
                ~np.isnan(power_array)
            )

            if np.any(valid_indices):
                differences = np.abs(
                    power_array[valid_indices] - calculated_power[valid_indices]
                )
                relative_errors = differences / (calculated_power[valid_indices] + 1e-10)

                if np.any(relative_errors > tolerance):
                    max_error = float(np.max(relative_errors) * 100)
                    report.add_issue(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Power inconsistent with V*I (max error: {max_error:.2f}%)",
                        field="power",
                        expected=f"P = V * I ± {tolerance*100}%",
                        standard=standard
                    ))

    return report


def validate_irradiance(
    irradiance: Union[float, np.ndarray],
    standard: str = "IEC 61853"
) -> ValidationReport:
    """
    Validate irradiance measurements per IEC 61853 standards.

    Args:
        irradiance: Irradiance value(s) in W/m²
        standard: Standard to validate against

    Returns:
        ValidationReport with validation results
    """
    report = ValidationReport(is_valid=True)

    min_irr, max_irr = DataValidator.IEC_61853_RANGES["irradiance"]
    irradiance_array = np.atleast_1d(irradiance)

    # Check for NaN or infinite values
    if np.any(np.isnan(irradiance_array)):
        report.add_issue(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message="Irradiance contains NaN values",
            field="irradiance",
            standard=standard
        ))

    if np.any(np.isinf(irradiance_array)):
        report.add_issue(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message="Irradiance contains infinite values",
            field="irradiance",
            standard=standard
        ))

    # Check range
    valid_irr = irradiance_array[~np.isnan(irradiance_array) & ~np.isinf(irradiance_array)]
    if len(valid_irr) > 0:
        if np.any(valid_irr < min_irr):
            count = np.sum(valid_irr < min_irr)
            report.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"{count} irradiance value(s) below minimum",
                field="irradiance",
                value=float(np.min(valid_irr)),
                expected=f">= {min_irr} W/m²",
                standard=standard
            ))

        if np.any(valid_irr > max_irr):
            count = np.sum(valid_irr > max_irr)
            report.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message=f"{count} irradiance value(s) above typical maximum",
                field="irradiance",
                value=float(np.max(valid_irr)),
                expected=f"typically <= {max_irr} W/m²",
                standard=standard
            ))

    # Check for STC conditions (1000 W/m² ± 10%)
    stc_irradiance = 1000.0
    stc_tolerance = 100.0
    if len(valid_irr) > 0:
        near_stc = np.abs(valid_irr - stc_irradiance) < stc_tolerance
        if np.any(near_stc):
            report.metadata["stc_measurements"] = int(np.sum(near_stc))

    return report


def validate_temperature(
    temperature: Union[float, np.ndarray],
    temp_type: str = "module",
    standard: str = "IEC 61853"
) -> ValidationReport:
    """
    Validate temperature measurements per IEC 61853 standards.

    Args:
        temperature: Temperature value(s) in °C
        temp_type: Type of temperature ("module" or "ambient")
        standard: Standard to validate against

    Returns:
        ValidationReport with validation results
    """
    report = ValidationReport(is_valid=True)

    # Select appropriate range
    if temp_type == "module":
        min_temp, max_temp = DataValidator.IEC_61853_RANGES["module_temperature"]
    elif temp_type == "ambient":
        min_temp, max_temp = DataValidator.IEC_61853_RANGES["ambient_temperature"]
    else:
        report.add_issue(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message=f"Invalid temperature type: {temp_type}",
            field="temp_type",
            expected="'module' or 'ambient'",
            standard=standard
        ))
        return report

    temperature_array = np.atleast_1d(temperature)

    # Check for NaN or infinite values
    if np.any(np.isnan(temperature_array)):
        report.add_issue(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message=f"{temp_type.capitalize()} temperature contains NaN values",
            field=f"{temp_type}_temperature",
            standard=standard
        ))

    if np.any(np.isinf(temperature_array)):
        report.add_issue(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message=f"{temp_type.capitalize()} temperature contains infinite values",
            field=f"{temp_type}_temperature",
            standard=standard
        ))

    # Check range
    valid_temp = temperature_array[~np.isnan(temperature_array) & ~np.isinf(temperature_array)]
    if len(valid_temp) > 0:
        if np.any(valid_temp < min_temp):
            count = np.sum(valid_temp < min_temp)
            report.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"{count} {temp_type} temperature value(s) below minimum",
                field=f"{temp_type}_temperature",
                value=float(np.min(valid_temp)),
                expected=f">= {min_temp} °C",
                standard=standard
            ))

        if np.any(valid_temp > max_temp):
            count = np.sum(valid_temp > max_temp)
            report.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"{count} {temp_type} temperature value(s) above maximum",
                field=f"{temp_type}_temperature",
                value=float(np.max(valid_temp)),
                expected=f"<= {max_temp} °C",
                standard=standard
            ))

    # Check for STC conditions (25°C ± 2°C for module temperature)
    if temp_type == "module":
        stc_temp = 25.0
        stc_tolerance = 2.0
        if len(valid_temp) > 0:
            near_stc = np.abs(valid_temp - stc_temp) < stc_tolerance
            if np.any(near_stc):
                report.metadata["stc_measurements"] = int(np.sum(near_stc))

    return report


def validate_module_parameters(
    parameters: Dict[str, Any],
    required_fields: Optional[List[str]] = None
) -> ValidationReport:
    """
    Validate module specification parameters.

    Args:
        parameters: Dictionary of module parameters
        required_fields: List of required parameter names

    Returns:
        ValidationReport with validation results
    """
    report = ValidationReport(is_valid=True)

    # Default required fields for PV modules
    if required_fields is None:
        required_fields = [
            "manufacturer",
            "model",
            "p_max",
            "v_oc",
            "i_sc",
            "v_mp",
            "i_mp",
            "efficiency",
            "technology",
        ]

    # Check for required fields
    missing_fields = [field for field in required_fields if field not in parameters]
    if missing_fields:
        report.add_issue(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message=f"Missing required module parameters: {', '.join(missing_fields)}",
            field="module_parameters",
            expected=f"Required fields: {', '.join(required_fields)}"
        ))

    # Validate numeric parameters if present
    numeric_params = {
        "p_max": (0, 1000),  # W
        "v_oc": (0, 100),  # V
        "i_sc": (0, 20),  # A
        "v_mp": (0, 100),  # V
        "i_mp": (0, 20),  # A
        "efficiency": (0, 30),  # %
    }

    for param, (min_val, max_val) in numeric_params.items():
        if param in parameters:
            value = parameters[param]
            try:
                value = float(value)
                if value < min_val or value > max_val:
                    report.add_issue(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Parameter {param} outside typical range",
                        field=param,
                        value=value,
                        expected=f"{min_val} to {max_val}"
                    ))
            except (ValueError, TypeError):
                report.add_issue(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Parameter {param} is not numeric",
                    field=param,
                    value=value,
                    expected="numeric value"
                ))

    # Validate string parameters
    string_params = ["manufacturer", "model", "technology"]
    for param in string_params:
        if param in parameters:
            value = parameters[param]
            if not isinstance(value, str) or not value.strip():
                report.add_issue(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Parameter {param} is not a valid string",
                    field=param,
                    value=value,
                    expected="non-empty string"
                ))

    # Cross-validate electrical parameters
    if all(p in parameters for p in ["v_mp", "i_mp", "p_max"]):
        try:
            v_mp = float(parameters["v_mp"])
            i_mp = float(parameters["i_mp"])
            p_max = float(parameters["p_max"])
            calculated_p = v_mp * i_mp

            if abs(calculated_p - p_max) / p_max > 0.05:  # 5% tolerance
                report.add_issue(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Inconsistent power parameters: Vmp*Imp={calculated_p:.2f}W, Pmax={p_max:.2f}W",
                    field="p_max",
                    expected="Pmax ≈ Vmp * Imp"
                ))
        except (ValueError, TypeError, ZeroDivisionError):
            pass

    return report


def validate_test_conditions(
    conditions: Dict[str, Any],
    test_type: str = "standard"
) -> ValidationReport:
    """
    Validate test conditions per IEC standards.

    Args:
        conditions: Dictionary of test conditions
        test_type: Type of test ("standard", "degradation", "performance")

    Returns:
        ValidationReport with validation results
    """
    report = ValidationReport(is_valid=True)

    # Standard test conditions (STC) per IEC 61215
    stc_conditions = {
        "irradiance": 1000.0,  # W/m²
        "module_temperature": 25.0,  # °C
        "air_mass": 1.5,
    }

    # Check for required condition fields
    required_conditions = ["irradiance", "module_temperature"]
    if test_type == "degradation":
        required_conditions.extend(["test_duration", "stress_type"])

    missing = [cond for cond in required_conditions if cond not in conditions]
    if missing:
        report.add_issue(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message=f"Missing required test conditions: {', '.join(missing)}",
            field="test_conditions",
            expected=f"Required: {', '.join(required_conditions)}"
        ))

    # Validate individual conditions
    if "irradiance" in conditions:
        irr_report = validate_irradiance(conditions["irradiance"])
        for issue in irr_report.issues:
            report.add_issue(issue)

    if "module_temperature" in conditions:
        temp_report = validate_temperature(conditions["module_temperature"], "module")
        for issue in temp_report.issues:
            report.add_issue(issue)

    if "ambient_temperature" in conditions:
        temp_report = validate_temperature(conditions["ambient_temperature"], "ambient")
        for issue in temp_report.issues:
            report.add_issue(issue)

    # Check if conditions match STC
    if all(cond in conditions for cond in ["irradiance", "module_temperature"]):
        try:
            irr = float(conditions["irradiance"])
            temp = float(conditions["module_temperature"])

            is_stc = (
                abs(irr - stc_conditions["irradiance"]) < 50 and
                abs(temp - stc_conditions["module_temperature"]) < 2
            )

            if is_stc:
                report.metadata["test_condition_type"] = "STC"
            else:
                report.metadata["test_condition_type"] = "non-STC"
        except (ValueError, TypeError):
            pass

    return report


def validate_metadata(
    metadata: Dict[str, Any],
    required_fields: Optional[List[str]] = None
) -> ValidationReport:
    """
    Validate test metadata for completeness and format.

    Args:
        metadata: Dictionary of metadata fields
        required_fields: List of required metadata fields

    Returns:
        ValidationReport with validation results
    """
    report = ValidationReport(is_valid=True)

    # Default required metadata fields
    if required_fields is None:
        required_fields = [
            "test_date",
            "test_facility",
            "operator",
            "equipment_id",
            "standard_reference",
        ]

    # Check for required fields
    missing = [field for field in required_fields if field not in metadata]
    if missing:
        report.add_issue(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message=f"Missing required metadata: {', '.join(missing)}",
            field="metadata",
            expected=f"Required fields: {', '.join(required_fields)}"
        ))

    # Validate date format if present
    if "test_date" in metadata:
        from datetime import datetime
        try:
            # Try common date formats
            date_str = str(metadata["test_date"])
            date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]
            parsed = False
            for fmt in date_formats:
                try:
                    datetime.strptime(date_str, fmt)
                    parsed = True
                    break
                except ValueError:
                    continue

            if not parsed:
                report.add_issue(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message="Test date format not recognized",
                    field="test_date",
                    value=date_str,
                    expected="ISO format (YYYY-MM-DD) recommended"
                ))
        except Exception:
            report.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Invalid test date",
                field="test_date",
                value=metadata.get("test_date")
            ))

    # Validate string fields
    string_fields = ["test_facility", "operator", "equipment_id", "standard_reference"]
    for field in string_fields:
        if field in metadata:
            value = metadata[field]
            if not isinstance(value, str) or not value.strip():
                report.add_issue(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Metadata field '{field}' is not a valid string",
                    field=field,
                    value=value,
                    expected="non-empty string"
                ))

    return report
