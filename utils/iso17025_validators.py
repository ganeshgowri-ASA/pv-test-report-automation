"""
ISO/IEC 17025 compliance validators for laboratory accreditation.

This module provides validators for:
- Calibration certificate validation and expiry checks
- Measurement traceability to SI units
- Uncertainty budget completeness
- NABL/ILAC accreditation scope validation
- Equipment qualification status
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Union

from .validation import ValidationResult, ValidationError, validate_datetime_format


# ============================================================================
# Enums and Constants
# ============================================================================

class AccreditationBody(Enum):
    """Recognized accreditation bodies."""
    NABL = "NABL"          # National Accreditation Board for Testing and Calibration Laboratories (India)
    ILAC = "ILAC"          # International Laboratory Accreditation Cooperation
    A2LA = "A2LA"          # American Association for Laboratory Accreditation
    ISO17025 = "ISO17025"  # Generic ISO/IEC 17025
    UKAS = "UKAS"          # United Kingdom Accreditation Service
    DAkkS = "DAkkS"        # Deutsche Akkreditierungsstelle (Germany)


class CalibrationStatus(Enum):
    """Equipment calibration status."""
    VALID = "valid"
    EXPIRING_SOON = "expiring_soon"
    EXPIRED = "expired"
    OVERDUE = "overdue"
    NOT_CALIBRATED = "not_calibrated"


class TraceabilityLevel(Enum):
    """Measurement traceability levels."""
    SI_DIRECT = "SI_direct"              # Direct traceability to SI units
    NATIONAL_STANDARD = "national"       # National metrology institute
    ACCREDITED_LAB = "accredited_lab"    # Accredited calibration lab
    MANUFACTURER = "manufacturer"         # Manufacturer calibration
    UNTRACED = "untraced"                # No traceability


@dataclass
class CalibrationCertificate:
    """Calibration certificate information."""
    certificate_number: str
    equipment_id: str
    calibration_date: datetime
    due_date: datetime
    lab_name: str
    accreditation_body: str
    certificate_path: Optional[str] = None
    uncertainty: Optional[float] = None
    traceability: str = "accredited_lab"

    @property
    def is_valid(self) -> bool:
        """Check if certificate is currently valid."""
        return datetime.now() < self.due_date

    @property
    def days_until_expiry(self) -> int:
        """Calculate days until certificate expires."""
        delta = self.due_date - datetime.now()
        return delta.days


@dataclass
class UncertaintyBudget:
    """Measurement uncertainty budget components."""
    components: Dict[str, float] = field(default_factory=dict)
    combined_uncertainty: Optional[float] = None
    expanded_uncertainty: Optional[float] = None
    coverage_factor: float = 2.0
    confidence_level: float = 95.0

    def is_complete(self) -> bool:
        """Check if all required components are present."""
        required = ["type_a", "type_b_calibration", "type_b_environmental"]
        return all(comp in self.components for comp in required)


# ============================================================================
# Calibration Certificate Validators
# ============================================================================

def validate_calibration_certificate(
    certificate_number: str,
    calibration_date: Union[str, datetime],
    due_date: Union[str, datetime],
    warning_days: int = 30
) -> ValidationResult:
    """
    Validate calibration certificate dates and expiry status.

    Args:
        certificate_number: Certificate identification number
        calibration_date: Date of calibration
        due_date: Calibration due date
        warning_days: Days before expiry to issue warning (default 30)

    Returns:
        ValidationResult with calibration status

    Example:
        >>> from datetime import datetime, timedelta
        >>> cal_date = datetime.now() - timedelta(days=300)
        >>> due_date = datetime.now() + timedelta(days=65)
        >>> result = validate_calibration_certificate("CAL-2024-001", cal_date, due_date)
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value={})

    # Parse dates if strings
    if isinstance(calibration_date, str):
        cal_result = validate_datetime_format(calibration_date)
        if not cal_result.is_valid:
            result.add_error(f"Invalid calibration date: {cal_result.errors}")
            return result
        calibration_date = cal_result.value

    if isinstance(due_date, str):
        due_result = validate_datetime_format(due_date)
        if not due_result.is_valid:
            result.add_error(f"Invalid due date: {due_result.errors}")
            return result
        due_date = due_result.value

    # Validate date logic
    if calibration_date > due_date:
        result.add_error(
            f"Calibration date ({calibration_date}) cannot be after due date ({due_date})"
        )
        return result

    # Check current status
    now = datetime.now()
    days_until_expiry = (due_date - now).days

    if due_date < now:
        # Expired
        days_overdue = (now - due_date).days
        result.add_error(
            f"Calibration certificate {certificate_number} expired {days_overdue} days ago"
        )
        status = CalibrationStatus.EXPIRED

    elif days_until_expiry <= warning_days:
        # Expiring soon
        result.add_warning(
            f"Calibration certificate {certificate_number} expires in {days_until_expiry} days"
        )
        status = CalibrationStatus.EXPIRING_SOON

    else:
        # Valid
        status = CalibrationStatus.VALID

    # Calculate calibration interval
    interval_days = (due_date - calibration_date).days

    result.value = {
        "certificate_number": certificate_number,
        "status": status.value,
        "calibration_date": calibration_date,
        "due_date": due_date,
        "days_until_expiry": days_until_expiry,
        "calibration_interval_days": interval_days
    }

    result.metadata["status"] = status.value
    result.metadata["days_until_expiry"] = days_until_expiry
    result.metadata["is_valid"] = status == CalibrationStatus.VALID

    return result


def validate_calibration_interval(
    calibration_date: datetime,
    due_date: datetime,
    recommended_interval_months: int = 12,
    tolerance_months: int = 1
) -> ValidationResult:
    """
    Validate calibration interval against recommended frequency.

    Args:
        calibration_date: Date of calibration
        due_date: Next calibration due date
        recommended_interval_months: Recommended interval (default 12 months)
        tolerance_months: Acceptable deviation (default ±1 month)

    Returns:
        ValidationResult with interval compliance

    Example:
        >>> from datetime import datetime, timedelta
        >>> cal_date = datetime(2024, 1, 1)
        >>> due_date = datetime(2025, 1, 1)
        >>> result = validate_calibration_interval(cal_date, due_date, 12)
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value={})

    # Calculate actual interval
    interval_days = (due_date - calibration_date).days
    interval_months = interval_days / 30.44  # Average days per month

    # Calculate recommended interval in days
    recommended_days = recommended_interval_months * 30.44
    tolerance_days = tolerance_months * 30.44

    # Check compliance
    deviation_days = abs(interval_days - recommended_days)

    if deviation_days > tolerance_days:
        result.add_warning(
            f"Calibration interval ({interval_months:.1f} months) deviates from "
            f"recommended {recommended_interval_months} months by {deviation_days/30.44:.1f} months"
        )

    result.value = {
        "interval_days": interval_days,
        "interval_months": interval_months,
        "recommended_months": recommended_interval_months,
        "deviation_months": (interval_days - recommended_days) / 30.44
    }

    result.metadata["compliant"] = deviation_days <= tolerance_days

    return result


# ============================================================================
# Measurement Traceability Validators
# ============================================================================

def validate_traceability_chain(
    equipment_id: str,
    traceability_level: str,
    reference_standard: Optional[str] = None,
    national_lab: Optional[str] = None
) -> ValidationResult:
    """
    Validate measurement traceability chain to SI units.

    Args:
        equipment_id: Equipment identifier
        traceability_level: Level of traceability (SI_direct, national, accredited_lab, etc.)
        reference_standard: Reference standard used
        national_lab: National metrology institute (for national traceability)

    Returns:
        ValidationResult with traceability compliance

    Example:
        >>> result = validate_traceability_chain(
        ...     "SIM-001",
        ...     "accredited_lab",
        ...     reference_standard="NIST Reference Cell"
        ... )
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value={
        "equipment_id": equipment_id,
        "traceability_level": traceability_level
    })

    # Validate traceability level
    try:
        trace_level = TraceabilityLevel(traceability_level.lower())
    except ValueError:
        result.add_error(
            f"Invalid traceability level '{traceability_level}'. "
            f"Valid levels: {', '.join([t.value for t in TraceabilityLevel])}"
        )
        return result

    # Check requirements for each level
    if trace_level == TraceabilityLevel.SI_DIRECT:
        if not reference_standard:
            result.add_warning(
                "Direct SI traceability should specify reference standard"
            )

    elif trace_level == TraceabilityLevel.NATIONAL_STANDARD:
        if not national_lab:
            result.add_warning(
                "National traceability should specify national metrology institute"
            )
        result.metadata["national_lab"] = national_lab

    elif trace_level == TraceabilityLevel.ACCREDITED_LAB:
        if not reference_standard:
            result.add_warning(
                "Accredited lab traceability should specify reference standard used"
            )

    elif trace_level == TraceabilityLevel.UNTRACED:
        result.add_error(
            f"Equipment {equipment_id} has no traceability - not ISO 17025 compliant"
        )

    result.value["reference_standard"] = reference_standard
    result.metadata["traceability_level"] = trace_level.value
    result.metadata["compliant"] = trace_level != TraceabilityLevel.UNTRACED

    return result


# ============================================================================
# Uncertainty Budget Validators
# ============================================================================

def validate_uncertainty_budget(
    budget: UncertaintyBudget,
    require_all_components: bool = True
) -> ValidationResult:
    """
    Validate completeness of measurement uncertainty budget.

    Args:
        budget: UncertaintyBudget object with components
        require_all_components: Require all standard components

    Returns:
        ValidationResult with budget completeness

    Example:
        >>> budget = UncertaintyBudget(
        ...     components={
        ...         "type_a": 0.05,
        ...         "type_b_calibration": 0.10,
        ...         "type_b_environmental": 0.03
        ...     },
        ...     combined_uncertainty=0.12,
        ...     expanded_uncertainty=0.24,
        ...     coverage_factor=2.0
        ... )
        >>> result = validate_uncertainty_budget(budget)
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value=budget)

    # Check component completeness
    required_components = [
        "type_a",                    # Statistical (Type A)
        "type_b_calibration",        # Calibration uncertainty (Type B)
        "type_b_environmental",      # Environmental conditions (Type B)
    ]

    optional_components = [
        "type_b_resolution",         # Instrument resolution
        "type_b_drift",              # Equipment drift
        "type_b_repeatability",      # Measurement repeatability
        "type_b_stability",          # Long-term stability
    ]

    missing_components = []
    for comp in required_components:
        if comp not in budget.components:
            missing_components.append(comp)
            if require_all_components:
                result.add_error(f"Missing required uncertainty component: {comp}")

    if missing_components and not require_all_components:
        result.add_warning(
            f"Missing recommended components: {', '.join(missing_components)}"
        )

    # Validate combined uncertainty calculation
    if budget.combined_uncertainty is not None:
        # Check RSS calculation
        calculated_combined = sum(u**2 for u in budget.components.values()) ** 0.5

        deviation = abs(calculated_combined - budget.combined_uncertainty)
        if deviation > 0.01:  # 1% tolerance
            result.add_warning(
                f"Combined uncertainty ({budget.combined_uncertainty}) differs from "
                f"calculated RSS ({calculated_combined:.4f})"
            )

    # Validate expanded uncertainty
    if budget.expanded_uncertainty is not None and budget.combined_uncertainty is not None:
        expected_expanded = budget.combined_uncertainty * budget.coverage_factor
        deviation = abs(expected_expanded - budget.expanded_uncertainty)

        if deviation > 0.01:
            result.add_warning(
                f"Expanded uncertainty ({budget.expanded_uncertainty}) should be "
                f"combined uncertainty × k = {expected_expanded:.4f}"
            )

    # Validate coverage factor
    if budget.coverage_factor not in [2.0, 2.58, 3.0]:
        result.add_warning(
            f"Non-standard coverage factor {budget.coverage_factor}. "
            f"Typical values: 2.0 (95%), 2.58 (99%), 3.0 (99.7%)"
        )

    result.metadata["component_count"] = len(budget.components)
    result.metadata["required_count"] = len(required_components)
    result.metadata["completeness"] = len(budget.components) / len(required_components)
    result.metadata["is_complete"] = budget.is_complete()

    return result


# ============================================================================
# Accreditation Scope Validators
# ============================================================================

def validate_accreditation_scope(
    test_method: str,
    test_standard: str,
    accredited_scopes: List[Dict[str, str]],
    accreditation_body: str = "NABL"
) -> ValidationResult:
    """
    Validate that test is within laboratory's accreditation scope.

    Args:
        test_method: Test method being performed
        test_standard: Standard reference (e.g., "IEC 61215")
        accredited_scopes: List of accredited test scopes
        accreditation_body: Accreditation body (NABL, ILAC, etc.)

    Returns:
        ValidationResult with scope compliance

    Example:
        >>> scopes = [
        ...     {"method": "PV Module Testing", "standard": "IEC 61215"},
        ...     {"method": "IV Curve Measurement", "standard": "IEC 60904"}
        ... ]
        >>> result = validate_accreditation_scope(
        ...     "PV Module Testing",
        ...     "IEC 61215",
        ...     scopes
        ... )
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value={})

    # Validate accreditation body
    try:
        accred_body = AccreditationBody(accreditation_body)
    except ValueError:
        result.add_warning(
            f"Unknown accreditation body '{accreditation_body}'. "
            f"Known bodies: {', '.join([a.value for a in AccreditationBody])}"
        )

    # Check if test is in scope
    in_scope = False
    matching_scope = None

    for scope in accredited_scopes:
        method_match = test_method.lower() in scope.get("method", "").lower()
        standard_match = test_standard.lower() in scope.get("standard", "").lower()

        if method_match and standard_match:
            in_scope = True
            matching_scope = scope
            break

    if not in_scope:
        result.add_error(
            f"Test '{test_method}' under '{test_standard}' is NOT in accredited scope"
        )
        result.metadata["accredited"] = False
    else:
        result.metadata["accredited"] = True
        result.metadata["matching_scope"] = matching_scope

    result.value = {
        "test_method": test_method,
        "test_standard": test_standard,
        "in_scope": in_scope,
        "accreditation_body": accreditation_body
    }

    return result


# ============================================================================
# Equipment Qualification Validators
# ============================================================================

def validate_equipment_qualification(
    equipment_id: str,
    last_calibration: datetime,
    last_verification: Optional[datetime] = None,
    last_maintenance: Optional[datetime] = None,
    calibration_interval_days: int = 365,
    verification_interval_days: int = 90
) -> ValidationResult:
    """
    Validate equipment qualification status (IQ/OQ/PQ compliance).

    Args:
        equipment_id: Equipment identifier
        last_calibration: Date of last calibration
        last_verification: Date of last intermediate verification
        last_maintenance: Date of last preventive maintenance
        calibration_interval_days: Calibration interval (default 365 days)
        verification_interval_days: Verification interval (default 90 days)

    Returns:
        ValidationResult with qualification status

    Example:
        >>> from datetime import datetime, timedelta
        >>> last_cal = datetime.now() - timedelta(days=200)
        >>> last_ver = datetime.now() - timedelta(days=30)
        >>> result = validate_equipment_qualification("SIM-001", last_cal, last_ver)
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value={})

    now = datetime.now()

    # Check calibration status
    days_since_calibration = (now - last_calibration).days
    cal_due_in_days = calibration_interval_days - days_since_calibration

    if cal_due_in_days < 0:
        result.add_error(
            f"Equipment {equipment_id} calibration is {abs(cal_due_in_days)} days overdue"
        )
        cal_status = CalibrationStatus.OVERDUE
    elif cal_due_in_days <= 30:
        result.add_warning(
            f"Equipment {equipment_id} calibration due in {cal_due_in_days} days"
        )
        cal_status = CalibrationStatus.EXPIRING_SOON
    else:
        cal_status = CalibrationStatus.VALID

    # Check intermediate verification
    if last_verification:
        days_since_verification = (now - last_verification).days
        ver_due_in_days = verification_interval_days - days_since_verification

        if ver_due_in_days < 0:
            result.add_warning(
                f"Intermediate verification is {abs(ver_due_in_days)} days overdue"
            )
    else:
        result.add_warning(
            f"No intermediate verification recorded for {equipment_id}"
        )
        ver_due_in_days = None

    # Check maintenance
    if last_maintenance:
        days_since_maintenance = (now - last_maintenance).days
        result.metadata["days_since_maintenance"] = days_since_maintenance
    else:
        result.add_warning(f"No maintenance records for {equipment_id}")

    result.value = {
        "equipment_id": equipment_id,
        "calibration_status": cal_status.value,
        "days_until_calibration_due": cal_due_in_days,
        "days_until_verification_due": ver_due_in_days
    }

    result.metadata["qualified"] = cal_status in [
        CalibrationStatus.VALID,
        CalibrationStatus.EXPIRING_SOON
    ]

    return result


# ============================================================================
# Measurement Result Validators
# ============================================================================

def validate_measurement_result_reporting(
    measured_value: float,
    uncertainty: float,
    unit: str,
    confidence_level: float = 95.0,
    significant_figures: int = 4
) -> ValidationResult:
    """
    Validate measurement result reporting per ISO 17025 requirements.

    Args:
        measured_value: Measured value
        uncertainty: Expanded uncertainty (k=2 typically)
        unit: Measurement unit
        confidence_level: Confidence level (default 95%)
        significant_figures: Required significant figures

    Returns:
        ValidationResult with reporting compliance

    Example:
        >>> result = validate_measurement_result_reporting(
        ...     measured_value=320.5,
        ...     uncertainty=3.2,
        ...     unit="W",
        ...     confidence_level=95.0
        ... )
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value={})

    # Validate uncertainty is reported
    if uncertainty <= 0:
        result.add_error(
            "Measurement uncertainty must be reported per ISO 17025"
        )
        return result

    # Check relative uncertainty
    relative_uncertainty = (uncertainty / abs(measured_value)) * 100

    if relative_uncertainty > 10.0:
        result.add_warning(
            f"Relative uncertainty ({relative_uncertainty:.2f}%) is high (>10%)"
        )

    # Validate confidence level
    if confidence_level not in [68.3, 95.0, 95.45, 99.0, 99.73]:
        result.add_warning(
            f"Non-standard confidence level {confidence_level}%. "
            f"Typical: 95% (k=2) or 99% (k=2.58)"
        )

    # Format result string
    result_string = f"{measured_value:.{significant_figures}g} ± {uncertainty:.2g} {unit} ({confidence_level}% confidence)"

    result.value = {
        "measured_value": measured_value,
        "uncertainty": uncertainty,
        "unit": unit,
        "relative_uncertainty_percent": relative_uncertainty,
        "confidence_level": confidence_level,
        "formatted_result": result_string
    }

    result.metadata["compliant_reporting"] = True

    return result
