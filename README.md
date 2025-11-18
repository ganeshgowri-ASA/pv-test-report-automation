# PV Test Report Automation

World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## Phase 2 - JSON & CSV Data Ingestion ✅

### Features

- ✅ **CSV Parsing** with automatic delimiter detection (`,`, `;`, `\t`, `|`, space)
- ✅ **Encoding Auto-Detection** (UTF-8, UTF-16, Latin-1, ASCII, ISO-8859-1, CP1252)
- ✅ **JSON/JSONL Support** with streaming for large files
- ✅ **Time-Series Data Handlers**
  - I-V curve parsing and analysis
  - Chamber log data processing
  - Data interpolation and resampling
- ✅ **Equipment Data Formats**
  - IV tracer exports
  - Thermal/climatic chamber data
  - Generic equipment data handlers
- ✅ **Batch Test Results** import and analysis
- ✅ **Schema Validation** with Pydantic models
- ✅ **ISO 17025 Compliance** validation and checking
- ✅ **Large File Streaming** support
- ✅ **Data Integrity** with SHA-256 file hashing

### Quick Start

#### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

#### Basic Usage

```python
from src.ingestion.csv_parser import CSVParser

# Parse CSV with auto-detection
parser = CSVParser()
result = parser.parse("test_data.csv")

print(f"Rows: {result.row_count}")
print(f"Delimiter: {result.delimiter_detected}")
print(f"Encoding: {result.encoding_detected}")
```

#### I-V Curve Analysis

```python
from src.ingestion.timeseries_handler import TimeSeriesHandler

handler = TimeSeriesHandler()
iv_data = handler.parse_iv_curve_csv(
    "iv_curve.csv",
    module_id="MODULE-001",
    irradiance=1000.0,
    temperature=25.0
)

print(f"Pmax: {iv_data.pmax} W")
print(f"Fill Factor: {iv_data.fill_factor}")
```

#### ISO 17025 Compliance

```python
from src.models.ingestion_models import ISO17025Metadata
from src.ingestion.validators import ISO17025Validator

metadata = ISO17025Metadata(
    lab_name="Accredited PV Lab",
    lab_accreditation_number="ISO17025-12345",
    test_method="IEC 61215",
    test_date=datetime.now(),
    operator_id="OP-001",
    equipment_id="EQ-001",
    environmental_conditions={"temperature": 23.0, "humidity": 45.0},
    uncertainty_budget={"calibration": 0.5, "repeatability": 0.3},
    traceability_chain=["Working Std", "NIST Reference"]
)

is_compliant, errors = ISO17025Validator.validate_full_compliance(metadata)
```

### Documentation

- **[Ingestion Guide](docs/INGESTION_GUIDE.md)** - Comprehensive usage guide
- **[Example Usage](examples/example_usage.py)** - Working code examples

### Running Examples

```bash
python examples/example_usage.py
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_csv_parser.py -v
```

### Project Structure

```
pv-test-report-automation/
├── src/
│   ├── models/
│   │   └── ingestion_models.py      # Pydantic data models
│   └── ingestion/
│       ├── csv_parser.py             # CSV parser with auto-detection
│       ├── json_parser.py            # JSON/JSONL parser
│       ├── timeseries_handler.py     # Time-series data (I-V, chamber)
│       ├── equipment_handler.py      # Equipment data formats
│       ├── batch_handler.py          # Batch test results
│       └── validators.py             # Schema & ISO 17025 validators
├── tests/
│   ├── test_csv_parser.py
│   ├── test_json_parser.py
│   ├── test_timeseries_handler.py
│   └── test_validators.py
├── docs/
│   └── INGESTION_GUIDE.md
├── examples/
│   └── example_usage.py
├── requirements.txt
└── pyproject.toml
```

### Supported Test Standards

- **IEC 60904** - PV device measurements
- **IEC 61215** - Crystalline silicon PV modules
- **IEC 61730** - PV module safety qualification
- **IEC 61853** - PV module performance testing
- **IEC 62716** - Ammonia corrosion testing
- **IEC 61701** - Salt mist corrosion testing
- **IEC 62804** - Potential-induced degradation
- **IEC 62759** - Transportation testing
- **ISO 17025** - Testing laboratory competence
- **ISO 9001** - Quality management systems
- **NABL** - National Accreditation Board for Testing
- **ILAC** - International Laboratory Accreditation Cooperation
- **BIS** - Bureau of Indian Standards

### Data Models

#### CSVIngestionResult
```python
{
    "dataframe": pd.DataFrame,
    "row_count": int,
    "column_count": int,
    "delimiter_detected": str,
    "encoding_detected": str,
    "file_hash": str,
    "has_header": bool,
    "data_types": Dict[str, str],
    "missing_values": Dict[str, int],
    "iso17025_metadata": Optional[ISO17025Metadata]
}
```

#### IVCurveData
```python
{
    "voltage": List[float],
    "current": List[float],
    "power": List[float],
    "voc": float,
    "isc": float,
    "vmp": float,
    "imp": float,
    "pmax": float,
    "fill_factor": float,
    "module_id": str,
    "irradiance": float,
    "temperature": float,
    "test_standard": str
}
```

### Key Features in Detail

#### Auto-Detection
- **Delimiter Detection**: Automatically detects `,`, `;`, `\t`, `|`, space
- **Encoding Detection**: Supports UTF-8, UTF-16, Latin-1, and more
- **Header Detection**: Identifies if CSV has header row

#### Streaming Support
- CSV files: Configurable chunk size
- JSONL files: Line-by-line streaming
- Batch processing for large datasets

#### ISO 17025 Compliance
- Metadata validation
- Calibration status checking
- Traceability chain validation
- Uncertainty budget documentation
- Environmental conditions tracking

#### Data Integrity
- SHA-256 file hashing
- Checksum verification
- Missing value detection
- Data type validation

### Performance

- **Memory Efficient**: Streaming support for files > 100 MB
- **Fast Parsing**: Optimized pandas operations
- **Scalable**: Handles millions of records
- **Configurable**: Adjustable chunk sizes and batch processing

### Contributing

This project follows ISO 17025 and IEC test standards. All contributions should maintain compliance with these standards.

### License

See [LICENSE](LICENSE) file for details.

### Support

For issues or questions, please open an issue in the repository.

---

**Note**: This is Phase 2 of the PV Test Report Automation system. Additional phases will include PDF parsing, LLM integration, reviewer workflows, and multi-format exports.
