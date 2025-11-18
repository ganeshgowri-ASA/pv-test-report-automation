"""
PV Test Lab Data Validation Utilities

This package provides comprehensive validation utilities for photovoltaic
test laboratory automation according to IEC/ISO standards and ISO 17025
compliance requirements.

Modules:
    validation: Core validators for strings, dates, and cross-field validation
    numeric_validators: Numeric range, statistical, and uncertainty validators
    file_validators: File upload, MIME type, and structure validators
    protocol_validators: IEC/ISO protocol-specific validators
    iso17025_validators: Accreditation compliance validators

Usage:
    from utils.validation import validate_module_serial, validate_email
    from utils.numeric_validators import validate_numeric_range
    from utils.protocol_validators import validate_mst_sequence
    from utils.iso17025_validators import validate_calibration_certificate
"""

__version__ = "1.0.0"
__author__ = "PV Test Lab Automation Team"

# Import commonly used classes and functions
from .validation import (
    ValidationResult,
    ValidationError,
    ValidationSeverity,
    validate_module_serial,
    validate_datetime_format,
    validate_standard_reference,
    validate_equipment_id,
    validate_email,
    validate_username,
    validate_date_range,
    validate_reviewer_hierarchy,
    batch_validate,
)

from .numeric_validators import (
    validate_numeric_range,
    validate_percentage,
    detect_outliers_zscore,
    detect_outliers_iqr,
    calculate_combined_uncertainty,
    propagate_uncertainty,
    round_to_sig_figs,
    convert_units,
    MeasurementUncertainty,
    UnitType,
)

from .file_validators import (
    validate_file_size,
    validate_mime_type,
    validate_file_extension,
    validate_csv_structure,
    validate_excel_structure,
    validate_pdf_metadata,
    validate_file,
    FileInfo,
)

from .protocol_validators import (
    validate_mst_sequence,
    validate_thermal_cycle,
    validate_safety_test_voltage,
    validate_ammonia_concentration,
    validate_salt_mist_severity,
    validate_stc_conditions,
    validate_module_power_rating,
    validate_test_sequence_dependency,
    IEC61215TestType,
    IEC61701SeverityLevel,
    IEC61730SafetyClass,
)

from .iso17025_validators import (
    validate_calibration_certificate,
    validate_traceability_chain,
    validate_uncertainty_budget,
    validate_accreditation_scope,
    validate_equipment_qualification,
    validate_measurement_result_reporting,
    CalibrationCertificate,
    UncertaintyBudget,
    AccreditationBody,
    CalibrationStatus,
)

__all__ = [
    # Core
    "ValidationResult",
    "ValidationError",
    "ValidationSeverity",

    # String validators
    "validate_module_serial",
    "validate_datetime_format",
    "validate_standard_reference",
    "validate_equipment_id",
    "validate_email",
    "validate_username",

    # Cross-field validators
    "validate_date_range",
    "validate_reviewer_hierarchy",
    "batch_validate",

    # Numeric validators
    "validate_numeric_range",
    "validate_percentage",
    "detect_outliers_zscore",
    "detect_outliers_iqr",
    "calculate_combined_uncertainty",
    "propagate_uncertainty",
    "round_to_sig_figs",
    "convert_units",
    "MeasurementUncertainty",
    "UnitType",

    # File validators
    "validate_file_size",
    "validate_mime_type",
    "validate_file_extension",
    "validate_csv_structure",
    "validate_excel_structure",
    "validate_pdf_metadata",
    "validate_file",
    "FileInfo",

    # Protocol validators
    "validate_mst_sequence",
    "validate_thermal_cycle",
    "validate_safety_test_voltage",
    "validate_ammonia_concentration",
    "validate_salt_mist_severity",
    "validate_stc_conditions",
    "validate_module_power_rating",
    "validate_test_sequence_dependency",
    "IEC61215TestType",
    "IEC61701SeverityLevel",
    "IEC61730SafetyClass",

    # ISO 17025 validators
    "validate_calibration_certificate",
    "validate_traceability_chain",
    "validate_uncertainty_budget",
    "validate_accreditation_scope",
    "validate_equipment_qualification",
    "validate_measurement_result_reporting",
    "CalibrationCertificate",
    "UncertaintyBudget",
    "AccreditationBody",
    "CalibrationStatus",
]
