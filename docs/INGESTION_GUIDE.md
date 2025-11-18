# JSON & CSV Data Ingestion Guide

## Overview

This module provides comprehensive data ingestion capabilities for PV (Photovoltaic) test laboratory data with full ISO 17025 compliance support.

## Features

- **CSV Parsing** with auto-delimiter detection (`,`, `;`, `\t`, `|`)
- **JSON/JSONL Support** with streaming for large files
- **Time-Series Data Handlers** for I-V curves and chamber logs
- **Equipment Data Formats** (IV tracer, thermal chambers, etc.)
- **Batch Test Results** import and analysis
- **Schema Validation** using Pydantic models
- **ISO 17025 Compliance** checking and validation
- **Large File Streaming** support

## Quick Start

### CSV Ingestion

```python
from src.ingestion.csv_parser import CSVParser

# Initialize parser
parser = CSVParser()

# Parse CSV with auto-detection
result = parser.parse("test_data.csv")

print(f"Detected delimiter: {result.delimiter_detected}")
print(f"Detected encoding: {result.encoding_detected}")
print(f"Rows: {result.row_count}, Columns: {result.column_count}")
print(f"File hash: {result.file_hash}")

# Access data as pandas DataFrame
df = result.dataframe
```

### JSON/JSONL Ingestion

```python
from src.ingestion.json_parser import JSONParser

# Initialize parser
parser = JSONParser()

# Parse JSON file
result = parser.parse("test_data.json", to_dataframe=True)

print(f"Records: {result.record_count}")
print(f"Is JSONL: {result.is_jsonl}")

# Access DataFrame if converted
if result.dataframe is not None:
    df = result.dataframe
```

### Streaming Large Files

```python
# CSV streaming
parser = CSVParser(chunk_size=10000)
result = parser.parse("large_file.csv", stream=True)

# JSONL streaming
json_parser = JSONParser()
for batch in json_parser.stream_parse("large_file.jsonl", batch_size=1000):
    # Process batch
    print(f"Processing {len(batch)} records")
```

## Time-Series Data

### I-V Curve Ingestion

```python
from src.ingestion.timeseries_handler import TimeSeriesHandler

handler = TimeSeriesHandler()

# Parse I-V curve from CSV
iv_data = handler.parse_iv_curve_csv(
    "iv_curve.csv",
    module_id="PV-MODULE-001",
    irradiance=1000.0,  # W/m²
    temperature=25.0,   # °C
    voltage_col="Voltage",
    current_col="Current"
)

print(f"Voc: {iv_data.voc} V")
print(f"Isc: {iv_data.isc} A")
print(f"Pmax: {iv_data.pmax} W")
print(f"Fill Factor: {iv_data.fill_factor}")

# Interpolate I-V curve
iv_interpolated = handler.interpolate_iv_curve(iv_data, num_points=100)
```

### Chamber Log Ingestion

```python
# Parse chamber log
log_data = handler.parse_chamber_log_csv(
    "chamber_log.csv",
    chamber_id="TC-001",
    test_id="TEST-2024-001",
    setpoint_temperature=85.0,
    timestamp_col="Timestamp",
    temperature_col="Temperature",
    humidity_col="Humidity"
)

print(f"Test duration: {log_data.duration_seconds / 3600:.2f} hours")
print(f"Temperature range: {min(log_data.temperature)}-{max(log_data.temperature)} °C")

# Resample to uniform intervals
log_resampled = handler.resample_chamber_log(log_data, frequency="1T")  # 1 minute
```

## Equipment Data

### IV Tracer Export

```python
from src.ingestion.equipment_handler import EquipmentDataHandler
from datetime import datetime

handler = EquipmentDataHandler()

equipment_data = handler.parse_iv_tracer_export(
    "iv_tracer_export.csv",
    equipment_id="IV-001",
    manufacturer="Keysight",
    model="E4980AL",
    serial_number="MY12345678",
    calibration_date=datetime(2024, 1, 15),
    calibration_due_date=datetime(2025, 1, 15),
    test_standard="IEC 60904-1"
)

print(f"Equipment: {equipment_data.manufacturer} {equipment_data.model}")
print(f"Calibration valid until: {equipment_data.calibration_due_date}")
```

### Generic Equipment Export

```python
from src.models.ingestion_models import EquipmentType

equipment_data = handler.parse_generic_equipment_export(
    "equipment_export.csv",
    equipment_type=EquipmentType.SPECTRORADIOMETER,
    equipment_id="SPEC-001",
    manufacturer="Instrument Systems",
    model="CAS 140CT",
    serial_number="12345",
    calibration_date=datetime(2024, 6, 1),
    calibration_due_date=datetime(2025, 6, 1),
    test_standard="IEC 60904-9"
)
```

## Batch Test Results

```python
from src.ingestion.batch_handler import BatchTestHandler

handler = BatchTestHandler()

# Parse batch test results
batch_result = handler.parse_batch_csv(
    "batch_test_results.csv",
    batch_id="BATCH-2024-001",
    test_standard="IEC 61215-2",
    module_id_col="Module_ID",
    result_col="Result"
)

print(f"Total modules: {batch_result.total_count}")
print(f"Passed: {batch_result.pass_count}")
print(f"Failed: {batch_result.fail_count}")
print(f"Pass rate: {batch_result.pass_count / batch_result.total_count * 100:.1f}%")

# Export batch report
handler.export_batch_report(batch_result, "batch_report.json", format="json")
```

## ISO 17025 Compliance

### Adding Metadata

```python
from src.models.ingestion_models import ISO17025Metadata
from datetime import datetime

metadata = ISO17025Metadata(
    lab_name="Accredited PV Testing Laboratory",
    lab_accreditation_number="ISO17025-NABL-12345",
    test_method="IEC 61215-1:2021",
    test_date=datetime(2024, 11, 18),
    operator_id="OPERATOR-001",
    equipment_id="IV-TRACER-001",
    calibration_due_date=datetime(2025, 6, 1),
    environmental_conditions={
        "temperature": 23.0,  # °C
        "humidity": 45.0,     # %
        "pressure": 101325    # Pa
    },
    uncertainty_budget={
        "calibration": 0.5,
        "repeatability": 0.3,
        "resolution": 0.1,
        "drift": 0.2
    },
    traceability_chain=[
        "Working Standard WS-001 (Cal Cert: WS-2024-001)",
        "Reference Standard RS-001 (NIST Traceable)",
        "National Standard (NIST)"
    ]
)

# Use metadata with ingestion
result = parser.parse("test_data.csv", iso17025_metadata=metadata)
```

### Validating Compliance

```python
from src.ingestion.validators import ISO17025Validator

# Validate metadata
is_valid, errors = ISO17025Validator.validate_metadata(metadata)

if not is_valid:
    print("Validation errors:")
    for error in errors:
        print(f"  - {error}")

# Full compliance check
is_compliant, error_dict = ISO17025Validator.validate_full_compliance(
    metadata,
    calibration_date=datetime(2024, 6, 1),
    calibration_due_date=datetime(2025, 6, 1)
)

if is_compliant:
    print("✓ Fully ISO 17025 compliant")
else:
    print("Compliance issues found:")
    for category, errors in error_dict.items():
        print(f"\n{category.upper()}:")
        for error in errors:
            print(f"  - {error}")
```

## Schema Validation

```python
from src.ingestion.validators import SchemaValidator

# Validate I-V curve data
iv_dict = {
    "voltage": [0, 10, 20, 30, 35, 37, 38],
    "current": [8.5, 8.4, 8.2, 7.8, 5.0, 2.0, 0.0],
    "timestamp": datetime.now(),
    "irradiance": 1000.0,
    "temperature": 25.0,
    "voc": 38.0,
    "isc": 8.5,
    "vmp": 30.0,
    "imp": 7.8,
    "pmax": 234.0,
    "fill_factor": 0.75,
    "module_id": "TEST-001"
}

is_valid, errors = SchemaValidator.validate_iv_curve(iv_dict)

if not is_valid:
    print("Validation errors:")
    for error in errors:
        print(f"  - {error}")
```

## Advanced Features

### Auto-Detection Examples

```python
# CSV delimiter auto-detection
parser = CSVParser()

# Automatically detects comma, semicolon, tab, pipe, or space
result = parser.parse("unknown_format.csv")
print(f"Detected: {result.delimiter_detected}")

# Encoding auto-detection (UTF-8, UTF-16, Latin-1, etc.)
print(f"Encoding: {result.encoding_detected}")
```

### Data Quality Checks

```python
# Check missing values
result = parser.parse("data_with_gaps.csv")

for column, missing_count in result.missing_values.items():
    if missing_count > 0:
        print(f"{column}: {missing_count} missing values")

# Check data types
for column, dtype in result.data_types.items():
    print(f"{column}: {dtype}")
```

### File Integrity

```python
# File hash for data integrity tracking
result = parser.parse("important_data.csv")
print(f"File hash (SHA-256): {result.file_hash}")

# Use hash to verify data hasn't changed
result2 = parser.parse("important_data.csv")
assert result.file_hash == result2.file_hash, "File has been modified!"
```

## Supported Test Standards

- **IEC 60904** series (PV device measurements)
- **IEC 61215** series (Crystalline silicon terrestrial PV modules)
- **IEC 61730** (PV module safety qualification)
- **IEC 61853** (PV module performance testing)
- **IEC 62716** (Ammonia corrosion testing)
- **IEC 61701** (Salt mist corrosion testing)
- **IEC 62804** (Potential-induced degradation)
- **ISO 17025** (Testing laboratory competence)

## Best Practices

1. **Always use ISO 17025 metadata** for accredited laboratory testing
2. **Validate calibration status** before using equipment data
3. **Document environmental conditions** for all measurements
4. **Maintain traceability chain** to national standards
5. **Include uncertainty budgets** for all measurements
6. **Use file hashing** for data integrity verification
7. **Stream large files** to minimize memory usage
8. **Validate schemas** before processing critical data

## Error Handling

```python
from pathlib import Path

try:
    result = parser.parse("test_data.csv")
except FileNotFoundError:
    print("File not found")
except ValueError as e:
    print(f"Validation error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Tips

1. **Use streaming** for files > 100 MB
2. **Adjust chunk_size** based on available memory
3. **Pre-filter data** before expensive operations
4. **Use pandas efficiently** with appropriate dtypes
5. **Cache file hashes** to avoid recomputation

## Support

For issues, questions, or contributions, please refer to the main repository documentation.
