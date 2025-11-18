"""
Core validation utilities for PV test lab automation.

This module provides base validation classes and common validators for
string formats, dates, and equipment identifiers used in photovoltaic
testing according to IEC/ISO standards.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional, Union
import re


class ValidationSeverity(Enum):
    """Validation result severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """
    Standardized validation result container.

    Attributes:
        is_valid: Whether the validation passed
        value: The validated value (may be normalized/converted)
        errors: List of error messages
        warnings: List of warning messages
        metadata: Additional validation context

    Example:
        >>> result = ValidationResult(is_valid=True, value="PV-2025-001234")
        >>> if result.is_valid:
        ...     print(f"Valid: {result.value}")
    """
    is_valid: bool
    value: Any = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def add_error(self, message: str, severity: ValidationSeverity = ValidationSeverity.ERROR) -> None:
        """Add an error message and mark as invalid."""
        self.is_valid = False
        self.errors.append(f"[{severity.value.upper()}] {message}")

    def add_warning(self, message: str) -> None:
        """Add a warning message without invalidating."""
        self.warnings.append(message)


class ValidationError(Exception):
    """Custom exception for validation failures."""

    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.format_message())

    def format_message(self) -> str:
        """Format error message with field and value context."""
        parts = [self.message]
        if self.field:
            parts.append(f"Field: {self.field}")
        if self.value is not None:
            parts.append(f"Value: {self.value}")
        return " | ".join(parts)


# ============================================================================
# String Validators
# ============================================================================

def validate_module_serial(
    serial: str,
    pattern: Optional[str] = None,
    required_length: Optional[int] = None
) -> ValidationResult:
    """
    Validate module serial number format.

    Default pattern matches: PV-YYYY-NNNNNN (e.g., PV-2025-001234)
    Custom patterns can be provided for different manufacturers.

    Args:
        serial: Serial number to validate
        pattern: Regex pattern (default: PV-YYYY-NNNNNN format)
        required_length: Exact length requirement (optional)

    Returns:
        ValidationResult with normalized serial number

    Example:
        >>> result = validate_module_serial("PV-2025-001234")
        >>> assert result.is_valid
        >>> result = validate_module_serial("ABC-XYZ-123", pattern=r"^[A-Z]{3}-[A-Z]{3}-\d{3}$")
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value=serial)

    # Basic checks
    if not serial or not isinstance(serial, str):
        result.add_error("Serial number must be a non-empty string")
        return result

    serial = serial.strip().upper()

    # Length validation
    if required_length and len(serial) != required_length:
        result.add_error(f"Serial number must be exactly {required_length} characters")
        return result

    # Pattern validation
    if pattern is None:
        # Default pattern: PV-YYYY-NNNNNN
        pattern = r'^PV-\d{4}-\d{6}$'

    if not re.match(pattern, serial):
        result.add_error(
            f"Serial number '{serial}' does not match required format. "
            f"Expected pattern: {pattern}"
        )
        return result

    result.value = serial
    result.metadata["normalized"] = True
    return result


def validate_datetime_format(
    dt_string: str,
    formats: Optional[List[str]] = None,
    require_iso8601: bool = True
) -> ValidationResult:
    """
    Validate and parse datetime strings.

    Supports ISO 8601 format by default, with optional custom formats.

    Args:
        dt_string: DateTime string to validate
        formats: List of allowed datetime formats (uses ISO 8601 if None)
        require_iso8601: Enforce ISO 8601 compliance

    Returns:
        ValidationResult with parsed datetime object

    Example:
        >>> result = validate_datetime_format("2025-01-15T10:30:00Z")
        >>> assert result.is_valid
        >>> isinstance(result.value, datetime)
        True
    """
    result = ValidationResult(is_valid=True, value=None)

    if not dt_string or not isinstance(dt_string, str):
        result.add_error("DateTime must be a non-empty string")
        return result

    # Default ISO 8601 formats
    if formats is None:
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",           # 2025-01-15T10:30:00Z
            "%Y-%m-%dT%H:%M:%S.%fZ",        # 2025-01-15T10:30:00.123456Z
            "%Y-%m-%dT%H:%M:%S%z",          # 2025-01-15T10:30:00+0530
            "%Y-%m-%d %H:%M:%S",            # 2025-01-15 10:30:00
            "%Y-%m-%d",                     # 2025-01-15
        ]

    # Try parsing with each format
    parsed_dt = None
    for fmt in formats:
        try:
            parsed_dt = datetime.strptime(dt_string, fmt)
            result.metadata["format_used"] = fmt
            break
        except ValueError:
            continue

    if parsed_dt is None:
        result.add_error(
            f"DateTime '{dt_string}' does not match any allowed format. "
            f"Expected formats: {formats}"
        )
        return result

    # ISO 8601 compliance check
    if require_iso8601 and 'T' not in dt_string and len(dt_string) > 10:
        result.add_warning(
            "DateTime format is not ISO 8601 compliant. "
            "Consider using format: YYYY-MM-DDTHH:MM:SSZ"
        )

    result.value = parsed_dt
    result.metadata["original"] = dt_string
    return result


def validate_standard_reference(reference: str) -> ValidationResult:
    """
    Validate IEC/ISO standard reference format.

    Supports formats like:
    - IEC 61215
    - IEC 61215-1:2021
    - ISO/IEC 17025:2017
    - IEC 62716 Ed. 2.0

    Args:
        reference: Standard reference string

    Returns:
        ValidationResult with normalized reference

    Example:
        >>> result = validate_standard_reference("IEC 61215-1:2021")
        >>> assert result.is_valid
        >>> result.value
        'IEC 61215-1:2021'
    """
    result = ValidationResult(is_valid=True, value=reference)

    if not reference or not isinstance(reference, str):
        result.add_error("Standard reference must be a non-empty string")
        return result

    reference = reference.strip()

    # Pattern: IEC/ISO number with optional part and year
    pattern = r'^(IEC|ISO|ISO/IEC)\s*\d{4,5}(-\d+)?(\s+Ed\.\s*\d+\.\d+)?(:\d{4})?$'

    if not re.match(pattern, reference, re.IGNORECASE):
        result.add_error(
            f"Standard reference '{reference}' is not in valid format. "
            f"Examples: 'IEC 61215', 'IEC 61215-1:2021', 'ISO/IEC 17025:2017'"
        )
        return result

    result.value = reference
    return result


def validate_equipment_id(
    equipment_id: str,
    prefix: Optional[str] = None,
    allow_alphanumeric: bool = True
) -> ValidationResult:
    """
    Validate equipment/instrument ID format.

    Args:
        equipment_id: Equipment identifier
        prefix: Required prefix (e.g., "SIM-" for simulators)
        allow_alphanumeric: Allow letters and numbers (default True)

    Returns:
        ValidationResult with normalized equipment ID

    Example:
        >>> result = validate_equipment_id("SIM-001", prefix="SIM-")
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value=equipment_id)

    if not equipment_id or not isinstance(equipment_id, str):
        result.add_error("Equipment ID must be a non-empty string")
        return result

    equipment_id = equipment_id.strip().upper()

    # Prefix check
    if prefix and not equipment_id.startswith(prefix.upper()):
        result.add_error(f"Equipment ID must start with '{prefix}'")
        return result

    # Character validation
    if allow_alphanumeric:
        pattern = r'^[A-Z0-9\-_]+$'
    else:
        pattern = r'^[A-Z\-_]+\d+$'

    if not re.match(pattern, equipment_id):
        result.add_error(
            f"Equipment ID '{equipment_id}' contains invalid characters. "
            f"Allowed: {'alphanumeric' if allow_alphanumeric else 'prefix + numbers'}, hyphens, underscores"
        )
        return result

    result.value = equipment_id
    result.metadata["normalized"] = True
    return result


def validate_email(email: str, domain_whitelist: Optional[List[str]] = None) -> ValidationResult:
    """
    Validate email address format for reviewer fields.

    Args:
        email: Email address to validate
        domain_whitelist: List of allowed domains (optional)

    Returns:
        ValidationResult with normalized email

    Example:
        >>> result = validate_email("reviewer@testlab.com")
        >>> assert result.is_valid
        >>> result = validate_email("reviewer@testlab.com", domain_whitelist=["testlab.com"])
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value=email)

    if not email or not isinstance(email, str):
        result.add_error("Email must be a non-empty string")
        return result

    email = email.strip().lower()

    # Basic email pattern
    pattern = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'

    if not re.match(pattern, email):
        result.add_error(f"Email '{email}' is not in valid format")
        return result

    # Domain whitelist check
    if domain_whitelist:
        domain = email.split('@')[1]
        if domain not in domain_whitelist:
            result.add_error(
                f"Email domain '{domain}' is not in whitelist: {domain_whitelist}"
            )
            return result

    result.value = email
    result.metadata["normalized"] = True
    return result


def validate_username(
    username: str,
    min_length: int = 3,
    max_length: int = 50,
    allow_special: bool = False
) -> ValidationResult:
    """
    Validate username format.

    Args:
        username: Username to validate
        min_length: Minimum length (default 3)
        max_length: Maximum length (default 50)
        allow_special: Allow special characters beyond underscore/hyphen

    Returns:
        ValidationResult with normalized username

    Example:
        >>> result = validate_username("tech_reviewer_01")
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value=username)

    if not username or not isinstance(username, str):
        result.add_error("Username must be a non-empty string")
        return result

    username = username.strip().lower()

    # Length check
    if len(username) < min_length:
        result.add_error(f"Username must be at least {min_length} characters")
        return result

    if len(username) > max_length:
        result.add_error(f"Username must not exceed {max_length} characters")
        return result

    # Character validation
    if allow_special:
        pattern = r'^[a-z0-9._\-@]+$'
    else:
        pattern = r'^[a-z0-9._\-]+$'

    if not re.match(pattern, username):
        result.add_error(
            f"Username '{username}' contains invalid characters. "
            f"Allowed: letters, numbers, dots, hyphens, underscores"
        )
        return result

    result.value = username
    result.metadata["normalized"] = True
    return result


# ============================================================================
# Cross-Field Validators
# ============================================================================

def validate_date_range(
    start_date: Union[str, datetime],
    end_date: Union[str, datetime],
    allow_same_day: bool = True,
    max_duration_days: Optional[int] = None
) -> ValidationResult:
    """
    Validate that start date is before end date.

    Args:
        start_date: Start datetime (string or datetime object)
        end_date: End datetime (string or datetime object)
        allow_same_day: Allow start and end on same day
        max_duration_days: Maximum allowed duration in days

    Returns:
        ValidationResult with duration metadata

    Example:
        >>> result = validate_date_range("2025-01-01", "2025-01-15")
        >>> assert result.is_valid
        >>> result.metadata["duration_days"]
        14
    """
    result = ValidationResult(is_valid=True, value={"start": start_date, "end": end_date})

    # Parse strings to datetime if needed
    if isinstance(start_date, str):
        start_result = validate_datetime_format(start_date)
        if not start_result.is_valid:
            result.add_error(f"Invalid start date: {start_result.errors}")
            return result
        start_date = start_result.value

    if isinstance(end_date, str):
        end_result = validate_datetime_format(end_date)
        if not end_result.is_valid:
            result.add_error(f"Invalid end date: {end_result.errors}")
            return result
        end_date = end_result.value

    # Compare dates
    if start_date > end_date:
        result.add_error(
            f"Start date ({start_date}) must be before end date ({end_date})"
        )
        return result

    if start_date == end_date and not allow_same_day:
        result.add_error("Start and end dates cannot be the same")
        return result

    # Calculate duration
    duration = (end_date - start_date).days
    result.metadata["duration_days"] = duration
    result.metadata["duration_hours"] = duration * 24

    # Max duration check
    if max_duration_days and duration > max_duration_days:
        result.add_error(
            f"Duration ({duration} days) exceeds maximum allowed ({max_duration_days} days)"
        )
        return result

    result.value = {"start": start_date, "end": end_date, "duration_days": duration}
    return result


def validate_reviewer_hierarchy(
    technician: str,
    reviewer: str,
    approver: Optional[str] = None,
    prevent_self_review: bool = True
) -> ValidationResult:
    """
    Validate reviewer hierarchy (Technician → Reviewer → Approver).

    Args:
        technician: Technician username/email
        reviewer: Reviewer username/email
        approver: Approver username/email (optional)
        prevent_self_review: Prevent same person in multiple roles

    Returns:
        ValidationResult with hierarchy validation

    Example:
        >>> result = validate_reviewer_hierarchy(
        ...     technician="tech01",
        ...     reviewer="reviewer01",
        ...     approver="manager01"
        ... )
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value={
        "technician": technician,
        "reviewer": reviewer,
        "approver": approver
    })

    # Validate each field
    for role, person in [("technician", technician), ("reviewer", reviewer)]:
        if not person:
            result.add_error(f"{role.capitalize()} is required")
            return result

    # Self-review prevention
    if prevent_self_review:
        if technician == reviewer:
            result.add_error("Technician and Reviewer cannot be the same person")
            return result

        if approver:
            if technician == approver:
                result.add_error("Technician and Approver cannot be the same person")
                return result
            if reviewer == approver:
                result.add_error("Reviewer and Approver cannot be the same person")
                return result

    result.metadata["hierarchy_valid"] = True
    return result


# ============================================================================
# Helper Functions
# ============================================================================

def batch_validate(
    validators: List[tuple],
    stop_on_first_error: bool = False
) -> ValidationResult:
    """
    Run multiple validators and aggregate results.

    Args:
        validators: List of (validator_func, args, kwargs) tuples
        stop_on_first_error: Stop on first validation failure

    Returns:
        Aggregated ValidationResult

    Example:
        >>> validators = [
        ...     (validate_module_serial, ("PV-2025-001234",), {}),
        ...     (validate_email, ("tech@lab.com",), {})
        ... ]
        >>> result = batch_validate(validators)
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value=[])
    all_results = []

    for i, (validator_func, args, kwargs) in enumerate(validators):
        try:
            val_result = validator_func(*args, **kwargs)
            all_results.append(val_result)

            if not val_result.is_valid:
                result.is_valid = False
                result.errors.extend(val_result.errors)

                if stop_on_first_error:
                    break

            result.warnings.extend(val_result.warnings)
            result.value.append(val_result.value)

        except Exception as e:
            result.add_error(f"Validator {i} failed: {str(e)}")
            if stop_on_first_error:
                break

    result.metadata["results"] = all_results
    result.metadata["total_validators"] = len(validators)
    result.metadata["passed"] = sum(1 for r in all_results if r.is_valid)

    return result
