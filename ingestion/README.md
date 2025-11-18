# Excel Data Ingestion Engine

Comprehensive Excel data ingestion engine for PV (Photovoltaic) test report automation. Supports multiple Excel formats, IEC-specific test data parsing, validation, and transformation.

## Features

### 📁 Excel File Support
- **Multiple Formats**: `.xlsx`, `.xls`, `.xlsm`, `.xlsb`
- **Password Protection**: Support for password-protected workbooks
- **Multi-Sheet Workbooks**: Extract data from multiple sheets
- **Cell Formatting**: Preserve cell formatting and styles
- **Charts & Images**: Extract embedded charts and images metadata

### 📊 Data Extraction Patterns
- **Structured Tables**: Extract DataFrames from defined ranges
- **Key-Value Pairs**: Parse equipment specs and metadata
- **Time-Series Data**: I-V curve measurements with timestamps
- **Metadata Headers**: Test date, operator, module serial
- **Multi-Level Headers**: Handle merged cells and grouped columns

### 🔬 IEC-Specific Parsers
- **IEC 61215 MST**: Module Stability Test (Damp Heat) data
- **IEC 61730**: Mechanical Impact Test (Ball Drop) results
- **IEC 62716**: Ammonia corrosion chamber concentration logs
- **IEC 61701**: Salt Mist corrosion (mass loss, visual inspection)
- **I-V Curve**: Raw voltage, current, power measurements

### ✅ Validation During Ingestion
- Missing columns/rows detection
- Data type validation (numeric vs string)
- Duplicate entry detection
- Statistical outlier detection (Z-score, IQR methods)
- Unit consistency verification

### 🛡️ Error Handling
- Corrupted file detection
- Missing worksheet handling
- Empty cell handling (NaN vs 0 vs "")
- Formula evaluation (calculate before import)
- Date format parsing (Excel serial dates)

### 📝 Metadata Extraction
- Workbook properties (author, dates)
- Sheet names and visibility
- Cell comments and notes
- Named ranges identification
- Conditional formatting rules

### 🔄 Data Transformation
- Pivot table flattening
- Multi-header column naming
- Unit conversion (V/mV, A/mA, etc.)
- Timestamp parsing (various formats)
- Numeric precision handling

## Installation

```bash
# Clone repository
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from ingestion.excel_parser import ExcelIngestion

# Initialize parser
ingestion = ExcelIngestion(file_path="test_data.xlsx")

# Parse a sheet
result = ingestion.parse_sheet(sheet_name="TestData")

if result.is_valid:
    df = result.dataframe
    metadata = result.metadata
    print(f"Loaded {len(df)} rows")
else:
    print("Errors:", result.errors)
```

### IEC 61215 MST (Damp Heat) Data

```python
from ingestion.excel_parser import ExcelIngestion

# Parse IEC 61215 MST data
ingestion = ExcelIngestion(file_path="iec61215_mst.xlsx")
result = ingestion.parse_iec61215_mst(
    sheet_name="DampHeat",
    data_range="A10:D210",
    time_column="Time (h)",
    temp_column="Temperature (°C)",
    humidity_column="Humidity (%RH)"
)

if result.is_valid:
    df = result.dataframe
    print(f"Test duration: {result.metadata['test_duration_hours']} hours")
    print(f"Avg temperature: {result.metadata['avg_temperature']:.2f} °C")
    print(f"Avg humidity: {result.metadata['avg_humidity']:.2f} %RH")

    # Check for warnings
    for warning in result.warnings:
        print(f"Warning: {warning}")
```

### IEC 61730 Impact Test

```python
result = ingestion.parse_iec61730_impact(
    sheet_name="ImpactTest",
    data_range="A6:F16"
)

print(f"Total tests: {result.metadata['total_tests']}")
print(f"Pass: {result.metadata['pass_count']}")
print(f"Fail: {result.metadata['fail_count']}")
```

### I-V Curve Data

```python
result = ingestion.parse_iv_curve(
    sheet_name="IV_Curve",
    data_range="A7:C107",
    voltage_column="Voltage (V)",
    current_column="Current (A)"
)

if result.is_valid:
    # Extract characteristic points
    print(f"Voc: {result.metadata['voc']:.2f} V")
    print(f"Isc: {result.metadata['isc']:.2f} A")
    print(f"Vmp: {result.metadata['vmp']:.2f} V")
    print(f"Imp: {result.metadata['imp']:.2f} A")
    print(f"Pmax: {result.metadata['pmax']:.2f} W")
    print(f"Fill Factor: {result.metadata['fill_factor']:.3f}")
```

### Data Transformation

```python
from ingestion.excel_transformers import ExcelTransformer

transformer = ExcelTransformer()

# Convert voltage units from mV to V
df = transformer.convert_units(
    df=df,
    column="Voltage (mV)",
    from_unit="mV",
    to_unit="V",
    unit_type="voltage"
)

# Clean column names
df = transformer.clean_column_names(
    df=df,
    lowercase=True,
    remove_special_chars=True,
    replace_spaces="_"
)

# Parse timestamps
df = transformer.parse_timestamp(
    df=df,
    column="test_date",
    handle_excel_serial=True
)
```

### Data Validation

```python
from ingestion.excel_validators import ExcelValidator

validator = ExcelValidator()

# Validate DataFrame
validation_result = validator.validate_dataframe(df)

# Check for issues
for warning in validation_result['warnings']:
    print(f"Warning: {warning}")

for error in validation_result['errors']:
    print(f"Error: {error}")

# Check unit consistency
unit_check = validator.validate_unit_consistency(
    df=df,
    column="Voltage (V)",
    expected_range=(30, 45),
    unit_multipliers={'mV': 0.001, 'V': 1.0}
)

if unit_check['suggested_conversion']:
    unit, multiplier = unit_check['suggested_conversion']
    print(f"Suggested conversion: multiply by {multiplier} ({unit} to V)")
```

## File Structure

```
ingestion/
├── __init__.py                 # Package initialization
├── excel_parser.py             # Main Excel parser with IEC-specific methods
├── excel_validators.py         # Data validation functions
├── excel_extractors.py         # Data extraction utilities
├── excel_transformers.py       # Data transformation utilities
├── test_excel_parser.py        # Comprehensive unit tests
├── generate_sample_data.py     # Sample data generation script
├── README.md                   # This file
└── sample_data/                # Sample Excel files
    ├── iec61215_mst.xlsx       # IEC 61215 MST sample
    ├── iec61730_impact.xlsx    # IEC 61730 impact test sample
    ├── iec62716_ammonia.xlsx   # IEC 62716 ammonia test sample
    ├── iec61701_salt_mist.xlsx # IEC 61701 salt mist sample
    ├── iv_curve_data.xlsx      # I-V curve sample
    └── multi_header_data.xlsx  # Multi-level header sample
```

## Generating Sample Data

```bash
cd ingestion
python generate_sample_data.py
```

This will create sample Excel files in the `sample_data/` directory for testing and development.

## Running Tests

```bash
# Run all tests
cd ingestion
python test_excel_parser.py

# Run with pytest (if installed)
pytest test_excel_parser.py -v

# Run with coverage
pytest test_excel_parser.py --cov=. --cov-report=html
```

## API Reference

### ExcelIngestion

Main class for Excel data ingestion.

#### Methods

- `__init__(file_path, password=None)`: Initialize with Excel file
- `get_sheet_names()`: Get list of sheet names
- `extract_metadata()`: Extract workbook metadata
- `parse_sheet(sheet_name, data_range, header_row, skip_rows, validate)`: Parse any sheet
- `parse_iec61215_mst(...)`: Parse IEC 61215 MST data
- `parse_iec61730_impact(...)`: Parse IEC 61730 impact test data
- `parse_iec62716_ammonia(...)`: Parse IEC 62716 ammonia test data
- `parse_iec61701_salt_mist(...)`: Parse IEC 61701 salt mist data
- `parse_iv_curve(...)`: Parse I-V curve measurements
- `parse_key_value_metadata(...)`: Extract key-value metadata

### ExcelValidator

Data validation utilities.

#### Methods

- `validate_dataframe(df, strict)`: Comprehensive DataFrame validation
- `validate_missing_values(df)`: Check for missing values
- `validate_data_types(df)`: Validate data type consistency
- `validate_duplicates(df, subset)`: Check for duplicate rows
- `detect_outliers(df, columns, method)`: Detect statistical outliers
- `validate_unit_consistency(df, column, expected_range, unit_multipliers)`: Check unit consistency
- `validate_timestamp_format(df, column)`: Validate timestamp formats

### ExcelExtractor

Data extraction utilities.

#### Methods

- `extract_range(workbook, sheet_name, cell_range, header_row)`: Extract specific range
- `extract_key_value_pairs(workbook, sheet_name, search_range)`: Extract metadata
- `extract_time_series(...)`: Extract time-series data
- `extract_multi_level_headers(...)`: Handle multi-level headers
- `extract_cell_comments(...)`: Extract cell comments
- `extract_named_ranges(...)`: Extract named ranges
- `extract_cell_styles(...)`: Extract cell formatting

### ExcelTransformer

Data transformation utilities.

#### Methods

- `convert_units(df, column, from_unit, to_unit, unit_type)`: Unit conversion
- `clean_column_names(df, lowercase, remove_special_chars, replace_spaces)`: Clean column names
- `parse_timestamp(df, column, format, handle_excel_serial)`: Parse timestamps
- `fill_missing_values(df, method, columns, limit)`: Fill missing values
- `interpolate_missing_data(df, column, method)`: Interpolate data
- `aggregate_time_series(...)`: Aggregate time-series data

### ExcelIngestionResult

Result object from ingestion operations.

#### Attributes

- `dataframe`: Extracted pandas DataFrame
- `metadata`: Dictionary of metadata
- `sheet_count`: Number of sheets in workbook
- `extraction_timestamp`: When data was extracted
- `file_hash`: SHA-256 hash for traceability
- `warnings`: List of warnings
- `errors`: List of errors
- `is_valid`: Boolean indicating success

## ISO 17025 Traceability

The engine provides ISO 17025 compliant traceability through:

- **File Hash**: SHA-256 hash of source file
- **Timestamps**: Extraction timestamp for each operation
- **Metadata Preservation**: Original file properties and metadata
- **Validation Logs**: Complete record of warnings and errors
- **Audit Trail**: All transformations and conversions recorded

## Error Handling

The engine uses custom exception classes:

- `ExcelIngestionError`: Base exception
- `FileNotFoundError`: File doesn't exist
- `CorruptedFileError`: File cannot be read
- `InvalidSheetError`: Sheet doesn't exist
- `DataValidationError`: Data validation failed

## Best Practices

1. **Always validate**: Use `validate=True` when parsing to catch data quality issues
2. **Check warnings**: Review warnings even for successful ingestion
3. **Preserve file hash**: Store the file hash for traceability
4. **Handle units carefully**: Use unit conversion to standardize measurements
5. **Document transformations**: Keep records of all data transformations

## Contributing

Contributions are welcome! Please ensure:

- All tests pass: `python test_excel_parser.py`
- Code follows PEP 8: `black .` and `flake8 .`
- Type hints are complete: `mypy .`
- Documentation is updated

## License

See LICENSE file in repository root.

## Support

For issues, questions, or feature requests, please create an issue in the GitHub repository.

## Changelog

### Version 1.0.0 (2024-11-18)
- Initial release
- Support for .xlsx, .xls, .xlsm, .xlsb formats
- IEC-specific parsers for 61215, 61730, 62716, 61701
- I-V curve data parsing
- Comprehensive validation and transformation
- Full test coverage
