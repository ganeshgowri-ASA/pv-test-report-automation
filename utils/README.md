# PV Test Lab Data Validation Utilities

Comprehensive data validation utilities for photovoltaic test laboratory automation, designed for compliance with IEC/ISO standards and ISO/IEC 17025 accreditation requirements.

## Overview

This package provides production-ready validators for:

- ✅ **Numeric data validation** - Range checks, outliers, uncertainty propagation
- ✅ **String format validation** - Serial numbers, dates, standards, emails
- ✅ **File upload validation** - Size limits, MIME types, structure verification
- ✅ **Protocol compliance** - IEC 61215, IEC 61730, IEC 62716, IEC 61701, IEC 60904
- ✅ **ISO 17025 compliance** - Calibration, traceability, uncertainty budgets

## Installation

```bash
# Install required dependencies
pip install pydantic python-dateutil

# Optional dependencies for enhanced functionality
pip install openpyxl pandas Pillow PyPDF2
```

## Quick Start

### Basic Validation

```python
from utils.validation import validate_module_serial, validate_email

# Validate module serial number
result = validate_module_serial("PV-2025-001234")
if result.is_valid:
    print(f"Valid serial: {result.value}")
else:
    print(f"Errors: {result.errors}")

# Validate email
result = validate_email("technician@lab.com")
print(f"Valid: {result.is_valid}")
```

### Numeric Validation

```python
from utils.numeric_validators import validate_numeric_range, detect_outliers_zscore

# Validate temperature with tolerance
result = validate_numeric_range(
    value=85.2,
    min_value=83.0,
    max_value=87.0,
    tolerance=2.0,
    field_name="Temperature"
)

# Detect statistical outliers
data = [10.1, 10.2, 10.0, 10.3, 50.0]  # 50.0 is outlier
result = detect_outliers_zscore(data, threshold=3.0)
print(f"Outliers found: {len(result.value['outliers'])}")
```

### File Validation

```python
from utils.file_validators import validate_file, validate_csv_structure

# Validate uploaded file
result = validate_file(
    "test_data.xlsx",
    max_size_mb=25,
    allowed_extensions=[".xlsx", ".xls"]
)

# Validate CSV structure
result = validate_csv_structure(
    "measurements.csv",
    required_columns=["Module_ID", "Power_W", "Voltage_V"],
    min_rows=1
)
```

### Protocol-Specific Validation

```python
from utils.protocol_validators import (
    validate_mst_sequence,
    validate_stc_conditions,
    validate_module_power_rating
)

# Validate IEC 61215 MST sequence
result = validate_mst_sequence(
    cycles=200,
    temperature_celsius=85.0,
    humidity_percent=85.0,
    duration_hours=1000,
    test_type="MST-200"
)

# Validate Standard Test Conditions (STC)
result = validate_stc_conditions(
    irradiance_w_m2=1000,
    temperature_celsius=25,
    spectrum="AM1.5G"
)

# Validate module power rating
result = validate_module_power_rating(
    measured_power_w=320.5,
    nameplate_power_w=315.0,
    tolerance_percent=3.0
)
```

### ISO 17025 Compliance

```python
from datetime import datetime, timedelta
from utils.iso17025_validators import (
    validate_calibration_certificate,
    validate_traceability_chain,
    validate_accreditation_scope
)

# Validate calibration certificate
result = validate_calibration_certificate(
    certificate_number="CAL-2024-001",
    calibration_date=datetime(2024, 1, 1),
    due_date=datetime(2025, 1, 1),
    warning_days=30
)

# Validate measurement traceability
result = validate_traceability_chain(
    equipment_id="SIM-001",
    traceability_level="accredited_lab",
    reference_standard="NIST Reference Cell"
)

# Validate accreditation scope
scopes = [
    {"method": "PV Module Testing", "standard": "IEC 61215"},
    {"method": "IV Curve Measurement", "standard": "IEC 60904"}
]
result = validate_accreditation_scope(
    test_method="PV Module Testing",
    test_standard="IEC 61215",
    accredited_scopes=scopes,
    accreditation_body="NABL"
)
```

## Module Documentation

### 1. validation.py - Core Validators

**String Validators:**
- `validate_module_serial()` - Module serial number format validation
- `validate_datetime_format()` - ISO 8601 datetime validation
- `validate_standard_reference()` - IEC/ISO standard reference format
- `validate_equipment_id()` - Equipment identifier validation
- `validate_email()` - Email address validation
- `validate_username()` - Username format validation

**Cross-Field Validators:**
- `validate_date_range()` - Date range consistency (start < end)
- `validate_reviewer_hierarchy()` - Reviewer hierarchy validation (Technician → Reviewer → Approver)
- `batch_validate()` - Run multiple validators and aggregate results

### 2. numeric_validators.py - Numeric Validators

**Range Validators:**
- `validate_numeric_range()` - Range validation with tolerance
- `validate_percentage()` - Percentage value validation (0-100%)

**Statistical Validators:**
- `detect_outliers_zscore()` - Z-score outlier detection (threshold typically 3.0)
- `detect_outliers_iqr()` - Interquartile Range outlier detection

**Uncertainty Propagation:**
- `calculate_combined_uncertainty()` - Combined uncertainty per ISO GUM
- `propagate_uncertainty()` - Uncertainty propagation through operations
- `MeasurementUncertainty` - Dataclass for uncertainty management

**Significant Figures:**
- `count_significant_figures()` - Count sig figs in a number
- `round_to_sig_figs()` - Round to specified sig figs per IEC 60904
- `validate_significant_figures()` - Validate sig figs based on uncertainty

**Unit Conversion:**
- `convert_units()` - Convert between units (W/kW/mW, V/mV, A/mA)
- `validate_unit_consistency()` - Ensure consistent units across measurements

### 3. file_validators.py - File Validators

**File Size & Type:**
- `validate_file_size()` - Prevent upload attacks with size limits
- `validate_mime_type()` - MIME type whitelist validation
- `validate_file_extension()` - Extension validation

**Image Validators:**
- `validate_image_dimensions()` - Image dimension validation for EL/IV curves

**Structure Validators:**
- `validate_csv_structure()` - CSV required columns and row count
- `validate_excel_structure()` - Excel sheet structure validation
- `validate_pdf_metadata()` - PDF metadata extraction and validation

**Complete Validation:**
- `validate_file()` - Complete file validation (size + MIME + extension)

### 4. protocol_validators.py - IEC/ISO Protocol Validators

**IEC 61215 (Terrestrial PV Modules):**
- `validate_mst_sequence()` - Module Stability Test (200 cycles, 85°C/85%RH)
- `validate_thermal_cycle()` - Thermal cycling (-40°C to +85°C)

**IEC 61730 (PV Module Safety):**
- `validate_safety_test_voltage()` - Safety test voltage parameters
- `validate_dielectric_strength()` - Dielectric strength test

**IEC 62716 (Ammonia Corrosion):**
- `validate_ammonia_concentration()` - NH3 concentration validation (10-50 ppm)

**IEC 61701 (Salt Mist Corrosion):**
- `validate_salt_mist_severity()` - Severity level validation (1-6)

**IEC 60904 (Measurement Standards):**
- `validate_stc_conditions()` - Standard Test Conditions validation
- `validate_module_power_rating()` - Power rating vs measured output

**Test Sequencing:**
- `validate_test_sequence_dependency()` - Test prerequisite validation

### 5. iso17025_validators.py - Accreditation Compliance

**Calibration Validators:**
- `validate_calibration_certificate()` - Certificate expiry and status
- `validate_calibration_interval()` - Calibration frequency compliance

**Traceability Validators:**
- `validate_traceability_chain()` - Measurement traceability to SI units

**Uncertainty Validators:**
- `validate_uncertainty_budget()` - Uncertainty budget completeness per GUM

**Accreditation Validators:**
- `validate_accreditation_scope()` - NABL/ILAC scope validation
- `validate_equipment_qualification()` - Equipment IQ/OQ/PQ status

**Measurement Reporting:**
- `validate_measurement_result_reporting()` - ISO 17025 compliant result reporting

## ValidationResult Object

All validators return a `ValidationResult` object with:

```python
@dataclass
class ValidationResult:
    is_valid: bool                    # Validation passed/failed
    value: Any                        # Validated/normalized value
    errors: List[str]                 # Error messages
    warnings: List[str]               # Warning messages
    metadata: dict                    # Additional context

    def add_error(message, severity)  # Add error and mark invalid
    def add_warning(message)          # Add warning without invalidating
```

### Example Usage:

```python
result = validate_module_serial("PV-2025-001234")

if result.is_valid:
    print(f"✓ Valid: {result.value}")
    if result.warnings:
        print(f"⚠ Warnings: {result.warnings}")
else:
    print(f"✗ Errors: {result.errors}")

# Access metadata
print(f"Metadata: {result.metadata}")
```

## Error Handling

```python
from utils.validation import ValidationError

try:
    result = validate_module_serial("PV-2025-001234")
    if not result.is_valid:
        raise ValidationError(
            message="; ".join(result.errors),
            field="module_serial",
            value="PV-2025-001234"
        )
except ValidationError as e:
    print(f"Validation failed: {e.format_message()}")
```

## Running Tests

```bash
# Install pytest
pip install pytest pytest-cov

# Run all tests
pytest utils/test_validation.py -v

# Run with coverage
pytest utils/test_validation.py --cov=utils --cov-report=html

# Run specific test class
pytest utils/test_validation.py::TestCoreValidation -v

# Run parameterized tests
pytest utils/test_validation.py -k "parametrized" -v
```

## Standards Compliance

### IEC Standards Implemented:
- **IEC 61215** - Terrestrial PV modules - Design qualification
- **IEC 61730** - PV module safety qualification
- **IEC 62716** - Ammonia corrosion testing
- **IEC 61701** - Salt mist corrosion testing
- **IEC 60904** - PV device measurement standards

### ISO Standards Implemented:
- **ISO/IEC 17025:2017** - Testing and calibration laboratories
- **ISO/IEC Guide 98-3 (GUM)** - Measurement uncertainty

### Accreditation Bodies Supported:
- NABL (India)
- ILAC (International)
- A2LA (USA)
- UKAS (UK)
- DAkkS (Germany)

## Best Practices

1. **Always check `is_valid`** before using validated values
2. **Handle both errors and warnings** - warnings don't invalidate results
3. **Use batch_validate()** for multiple related validations
4. **Leverage metadata** for additional context and debugging
5. **Set appropriate tolerances** for measurement validations
6. **Document custom patterns** when using regex validators

## Example: Complete Test Report Validation

```python
from utils import (
    validate_module_serial,
    validate_stc_conditions,
    validate_module_power_rating,
    validate_reviewer_hierarchy,
    validate_calibration_certificate,
    batch_validate
)

# Define all validations
validators = [
    # Module identification
    (validate_module_serial, ("PV-2025-001234",), {}),

    # Test conditions
    (validate_stc_conditions, (1000, 25, "AM1.5G"), {}),

    # Power measurement
    (validate_module_power_rating, (320.5, 315.0), {"tolerance_percent": 3.0}),

    # Review workflow
    (validate_reviewer_hierarchy, ("tech01", "reviewer01", "manager01"), {}),
]

# Run batch validation
result = batch_validate(validators, stop_on_first_error=False)

if result.is_valid:
    print("✓ All validations passed")
    print(f"Passed: {result.metadata['passed']}/{result.metadata['total_validators']}")
else:
    print("✗ Validation failed")
    for error in result.errors:
        print(f"  - {error}")
```

## Contributing

When adding new validators:

1. Follow the existing function signature pattern
2. Return `ValidationResult` objects
3. Include comprehensive docstrings with examples
4. Add corresponding test cases in `test_validation.py`
5. Update `__init__.py` to export new functions
6. Document in this README

## License

See LICENSE file in repository root.

## Support

For issues or questions, please contact the PV Test Lab Automation Team.
