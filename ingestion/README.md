# JSON & CSV Data Ingestion Engine

Comprehensive data ingestion engine for PV (Photovoltaic) test report automation. Supports CSV, JSON, and JSON Lines formats with auto-detection, schema validation, and ISO 17025 traceability.

## Features

### CSV File Support
- ✓ Standard CSV parsing (comma, semicolon, tab, pipe delimiters)
- ✓ Auto-detect delimiter and encoding (UTF-8, Latin-1, Windows-1252)
- ✓ Multi-line field support
- ✓ Header row detection and validation
- ✓ Large file streaming (chunked processing)
- ✓ Various quote characters and escape sequences

### JSON File Support
- ✓ Parse standard JSON files
- ✓ JSON Lines (.jsonl) format support
- ✓ Nested JSON structure flattening
- ✓ JSON schema validation
- ✓ Handle malformed JSON gracefully
- ✓ Pretty-print for debugging

### Time-Series Data Ingestion
- ✓ I-V Curve Measurements
- ✓ Environmental Chamber Logs
- ✓ Data Logger Exports
- ✓ Power Output Monitoring
- ✓ Irradiance Sensor Data
- ✓ Automatic timestamp parsing
- ✓ Data resampling and aggregation

### Equipment Data Formats
- ✓ IV Tracer Output (Keysight, Pasan, etc.)
- ✓ Climate Chamber Logs
- ✓ Spectroradiometer Data
- ✓ Thermography Camera Data
- ✓ Data Acquisition System Exports

### Data Validation
- ✓ Column name validation
- ✓ Data type enforcement
- ✓ Range validation for numeric values
- ✓ Timestamp parsing and validation
- ✓ Missing value handling strategies
- ✓ Duplicate row detection
- ✓ Pydantic model validation

### Data Transformation
- ✓ Unit conversion (automatic detection)
- ✓ Column renaming/mapping
- ✓ Data aggregation
- ✓ Pivot table operations
- ✓ Missing data interpolation
- ✓ Outlier detection and removal

### ISO 17025 Traceability
- ✓ SHA-256 file hash calculation
- ✓ Metadata tracking (file size, timestamp, duration)
- ✓ Version tracking
- ✓ Audit trail support

## Installation

### Requirements

```bash
pip install pandas numpy pydantic chardet jsonschema
```

### Optional Dependencies

```bash
# For Excel export
pip install openpyxl

# For Parquet export
pip install pyarrow
```

## Quick Start

### CSV Ingestion

```python
from ingestion.csv_parser import CSVIngestion

# Parse I-V curve CSV with auto-detection
ingestion = CSVIngestion("data/iv_curve.csv")
result = ingestion.parse()

if result.is_valid:
    df = ingestion.get_dataframe()
    print(f"Imported {len(df)} data points")
    print(f"Detected delimiter: {result.delimiter_detected}")
    print(f"File hash: {result.metadata.file_hash}")
else:
    print("Errors:", result.errors)
```

### JSON Ingestion with Schema Validation

```python
from ingestion.json_parser import JSONIngestion

# Parse chamber log JSON with schema validation
ingestion = JSONIngestion("data/chamber_log.json")
result = ingestion.parse(schema="schemas/chamber_log_schema.json")

if result.is_valid and result.schema_validated:
    data = ingestion.get_data()
    print(f"Loaded {result.record_count} records")
else:
    print("Schema errors:", result.schema_errors)
```

### Time-Series Parsing

```python
from ingestion.timeseries_parser import TimeSeriesParser
from ingestion.models import TimeSeriesConfig

# Configure time-series parser
config = TimeSeriesConfig(
    timestamp_col="Time",
    value_cols=["Voltage", "Current", "Power"]
)

parser = TimeSeriesParser("data/iv_curve.csv", config)
df = parser.parse()

# Resample to 1-second intervals
df_resampled = parser.resample("1s", {"Power": "mean"})

# Detect outliers
outliers = parser.detect_outliers(method="zscore", threshold=3.0)
```

### Batch Test Results Import

```python
from ingestion.csv_parser import CSVIngestion

# Parse batch module test data
ingestion = CSVIngestion("data/batch_results.csv")
result = ingestion.parse_batch_results(serial_col="Serial")

if result.is_valid:
    df = ingestion.get_dataframe()
    print(f"Imported {len(df)} module test results")

    # Check for duplicates
    if result.warnings:
        print("Warnings:", result.warnings)
```

### Schema Validation

```python
from ingestion.schema_validator import SchemaValidator

# List available schemas
schemas = SchemaValidator.list_schemas()
print("Available schemas:", schemas)

# Validate DataFrame against IEC 61215 schema
validator = SchemaValidator("iec61215_module")
errors = validator.validate_dataframe(df)

if not errors:
    print("All data valid!")
else:
    print("Validation errors:", errors)
```

### Data Transformation

```python
from ingestion.data_transformers import DataTransformer

# Load data
transformer = DataTransformer(df)

# Convert units
df = transformer.convert_units({
    'power': ('W', 'kW'),
    'temperature': ('C', 'K')
})

# Rename columns
df = transformer.rename_columns({
    'V': 'Voltage',
    'I': 'Current'
})

# Filter data
df = transformer.filter_rows({
    'efficiency': ('>', 18.0),
    'grade': 'A'
})

# Remove outliers
df = transformer.remove_outliers(
    columns=['power'],
    method='zscore',
    threshold=3.0
)

# Calculate derived column
df = transformer.calculate_derived_column(
    'power_check',
    'voltage * current'
)

# Export
transformer.export("output.csv", format="csv")
```

## Module Structure

```
ingestion/
├── __init__.py              # Package initialization
├── csv_parser.py            # CSV ingestion engine
├── json_parser.py           # JSON ingestion engine
├── timeseries_parser.py     # Time-series specific parser
├── schema_validator.py      # Schema validation
├── data_transformers.py     # Transformation utilities
├── models.py                # Pydantic models
├── exceptions.py            # Custom exceptions
├── test_json_csv.py         # Unit tests
├── README.md                # This file
├── sample_data/
│   ├── iv_curve.csv         # Sample I-V curve data
│   ├── chamber_log.json     # Sample chamber log
│   ├── batch_results.csv    # Sample batch test data
│   ├── irradiance_data.csv  # Sample irradiance data
│   ├── flash_test.jsonl     # Sample JSON Lines
│   └── chamber_log_alternate.csv  # Alternate delimiter
└── schemas/
    ├── iv_curve_schema.json
    ├── chamber_log_schema.json
    ├── flash_test_schema.json
    ├── irradiance_schema.json
    └── iec61215_module_schema.json
```

## Advanced Usage

### Custom Validation Rules

```python
from ingestion.csv_parser import CSVIngestion

# Parse with custom validation
result = ingestion.parse(
    required_columns=['Serial', 'Voc', 'Isc', 'Pmax'],
    numeric_columns=['Voc', 'Isc', 'Pmax'],
    range_checks={
        'Voc': (0, 100),      # Voltage range
        'Isc': (0, 15),       # Current range
        'Efficiency': (0, 30) # Efficiency range
    }
)
```

### Large File Streaming

```python
# Enable streaming for large files
result = ingestion.parse(streaming=True)
```

### JSON Lines Processing

```python
from ingestion.json_parser import JSONIngestion

# Parse JSON Lines (.jsonl) format
ingestion = JSONIngestion("data/flash_test.jsonl")
result = ingestion.parse(json_lines=True)

# Flatten nested JSON
result = ingestion.parse(flatten=True)
df = ingestion.get_dataframe()
```

### Time-Series Gap Detection

```python
import pandas as pd

# Detect time gaps larger than 1 hour
gaps = parser.detect_gaps(max_gap=pd.Timedelta(hours=1))

for _, gap in gaps.iterrows():
    print(f"Gap from {gap['gap_start']} to {gap['gap_end']}: {gap['duration']}")
```

### Auto-Generate Schema

```python
from ingestion.schema_validator import SchemaValidator

# Auto-generate schema from sample data
schema = SchemaValidator.generate_schema_from_dataframe(
    df,
    schema_name="CustomTestSchema"
)

# Save schema
SchemaValidator.save_schema_definition("flash_test", "schemas/custom.json")
```

### Transformation Configuration

```python
from ingestion.models import TransformationConfig

# Define transformation pipeline
config = TransformationConfig(
    column_mapping={'V': 'Voltage', 'I': 'Current'},
    unit_conversions={'power': ('W', 'kW')},
    drop_columns=['unused_col'],
    filter_conditions={'grade': 'A'},
    aggregate_functions={'power': 'mean'}
)

# Apply configuration
transformer = DataTransformer(df)
df = transformer.apply_config(config)
```

## Pre-defined Schemas

The engine includes predefined schemas for common PV test types:

1. **iec61215_module** - IEC 61215 module test data
2. **iv_curve** - I-V curve measurements
3. **chamber_log** - Environmental chamber logs
4. **flash_test** - Flash test batch results
5. **irradiance** - Irradiance sensor data

## Testing

Run the comprehensive test suite:

```bash
cd ingestion
python test_json_csv.py
```

Tests cover:
- CSV parsing with various delimiters
- JSON and JSON Lines parsing
- Schema validation
- Time-series operations
- Data transformations
- Integration workflows

## Error Handling

All ingestion operations return structured results with validation errors:

```python
result = ingestion.parse()

if not result.is_valid:
    for error in result.errors:
        print(f"Error in {error.field}: {error.message}")
        if error.row:
            print(f"  Row: {error.row}")
```

## Performance

- **Streaming mode**: Process files larger than memory
- **Chunked reading**: 10,000 rows per chunk (configurable)
- **Efficient encoding detection**: Reads only first 100KB
- **Parallel processing**: Support for batch operations

## ISO 17025 Compliance

All ingested data includes traceability metadata:

```python
result = ingestion.parse()

print(f"File hash: {result.metadata.file_hash}")
print(f"File size: {result.metadata.file_size_bytes} bytes")
print(f"Ingestion time: {result.metadata.ingestion_timestamp}")
print(f"Duration: {result.metadata.ingestion_duration_ms} ms")
```

## Equipment Support

The engine has been tested with data from:

- **IV Tracers**: Keysight, Pasan, h.a.l.m
- **Climate Chambers**: Espec, Weiss Technik, Vötsch
- **Data Loggers**: Agilent, National Instruments
- **Irradiance Sensors**: Kipp & Zonen, EKO
- **Flash Testers**: Spire, Meyer Burger, Berger Lichttechnik

## Roadmap

- [ ] Support for Excel (.xlsx) ingestion
- [ ] Real-time data streaming from equipment
- [ ] Database integration (PostgreSQL, InfluxDB)
- [ ] Multi-file batch processing
- [ ] Advanced anomaly detection
- [ ] Report generation integration

## License

Part of the PV Test Report Automation System
Licensed under MIT License

## Support

For issues and feature requests, please file an issue on GitHub.

## Version

**v1.0.0** - Initial release with comprehensive CSV/JSON support
