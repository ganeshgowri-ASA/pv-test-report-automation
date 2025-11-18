"""
Data Validation Module

Provides comprehensive validation utilities for PV test data including:
- IEC/ISO compliance validation
- Data type and range validation
- Schema validation using Pydantic models
- Compliance checking for ISO 17025 and NABL standards
"""

from typing import List

from .data_validators import (
    DataValidator,
    validate_voltage,
    validate_current,
    validate_power,
    validate_irradiance,
    validate_temperature,
    validate_module_parameters,
    validate_test_conditions,
    validate_metadata,
)
from .schema_validators import (
    TestDataSchema,
    ModuleSpecSchema,
    EnvironmentalConditionsSchema,
    MeasurementSchema,
    ValidationResultSchema,
    ErrorDetailSchema,
)
from .compliance_checker import (
    ComplianceChecker,
    check_iso17025_compliance,
    check_nabl_compliance,
    check_iec_conformance,
    check_data_completeness,
)

__all__: List[str] = [
    # Data validators
    "DataValidator",
    "validate_voltage",
    "validate_current",
    "validate_power",
    "validate_irradiance",
    "validate_temperature",
    "validate_module_parameters",
    "validate_test_conditions",
    "validate_metadata",
    # Schema validators
    "TestDataSchema",
    "ModuleSpecSchema",
    "EnvironmentalConditionsSchema",
    "MeasurementSchema",
    "ValidationResultSchema",
    "ErrorDetailSchema",
    # Compliance checkers
    "ComplianceChecker",
    "check_iso17025_compliance",
    "check_nabl_compliance",
    "check_iec_conformance",
    "check_data_completeness",
]
