# PV Test Report Automation

Comprehensive automation system for photovoltaic (PV) module test data ingestion, validation, and reporting with focus on IEC standards compliance and ISO 17025 traceability.

## 🚀 Project Overview

This project provides production-ready tools for automating PV test data workflows:

- **Excel Data Ingestion Engine**: Multi-format Excel file parsing with IEC-specific protocols
- **Data Validation**: Statistical outlier detection, unit consistency, missing value handling
- **Data Transformation**: Unit conversion, timestamp parsing, data cleaning
- **ISO 17025 Compliance**: File hashing, audit trails, metadata preservation

## 📦 Current Implementation

### Phase 2 | Session 06: Excel Data Ingestion Engine ✓

Complete Excel data ingestion system with:

- Support for `.xlsx`, `.xls`, `.xlsm`, `.xlsb` formats
- Password-protected workbook handling
- Multi-sheet workbook support
- IEC-specific parsers:
  - IEC 61215 MST (Damp Heat)
  - IEC 61730 Mechanical Impact
  - IEC 62716 Ammonia Corrosion
  - IEC 61701 Salt Mist Corrosion
  - I-V Curve Measurements
- Comprehensive validation and transformation
- Full unit test coverage (27 tests passing)

[View detailed documentation →](ingestion/README.md)

## 🛠️ Installation

```bash
# Clone repository
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation

# Install dependencies
pip install -r requirements.txt

# Generate sample data
cd ingestion
python generate_sample_data.py

# Run tests
python test_excel_parser.py
```

## 📚 Quick Start

```python
from ingestion.excel_parser import ExcelIngestion

# Parse IEC 61215 MST data
ingestion = ExcelIngestion(file_path="iec61215_mst.xlsx")
result = ingestion.parse_iec61215_mst(sheet_name="DampHeat")

if result.is_valid:
    df = result.dataframe
    print(f"Duration: {result.metadata['test_duration_hours']} hours")
    print(f"Avg Temp: {result.metadata['avg_temperature']:.2f} °C")
else:
    print("Errors:", result.errors)
```

## 📁 Project Structure

```
pv-test-report-automation/
├── ingestion/                  # Excel data ingestion engine
│   ├── excel_parser.py         # Main parser with IEC-specific methods
│   ├── excel_validators.py     # Data validation utilities
│   ├── excel_extractors.py     # Data extraction functions
│   ├── excel_transformers.py   # Data transformation tools
│   ├── test_excel_parser.py    # Comprehensive unit tests
│   ├── generate_sample_data.py # Sample data generation
│   ├── sample_data/            # Sample Excel files
│   └── README.md               # Detailed ingestion docs
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── LICENSE                     # MIT License
└── .gitignore                  # Git ignore rules
```

## ✨ Key Features

### Excel File Support
- Multiple Excel formats (`.xlsx`, `.xls`, `.xlsm`, `.xlsb`)
- Password-protected workbooks
- Multi-sheet workbooks
- Cell formatting preservation
- Embedded charts and images extraction

### Data Extraction
- **Structured Tables**: DataFrame extraction from ranges
- **Key-Value Pairs**: Equipment specs and metadata parsing
- **Time-Series**: I-V curve and environmental data
- **Multi-Level Headers**: Merged cell handling
- **Cell Comments**: Notes and annotations extraction

### IEC-Specific Parsers
- **IEC 61215**: Module Stability Test (MST) damp heat data
- **IEC 61730**: Mechanical impact (ball drop) test results
- **IEC 62716**: Ammonia corrosion chamber logs
- **IEC 61701**: Salt mist corrosion and mass loss data
- **I-V Curves**: Voltage, current, power measurements with characteristic points (Voc, Isc, Vmp, Imp, Pmax, FF)

### Validation
- Missing value detection and reporting
- Data type consistency validation
- Duplicate entry detection
- Statistical outlier detection (Z-score, IQR methods)
- Unit consistency verification
- Timestamp format validation

### Transformation
- Unit conversion (V/mV, A/mA, W/mW, °C/°F/K)
- Timestamp parsing (Excel serial dates, various formats)
- Column name cleaning and standardization
- Missing value interpolation
- Time-series aggregation
- Pivot table flattening

### ISO 17025 Traceability
- SHA-256 file hashing
- Extraction timestamps
- Metadata preservation
- Validation audit trails
- Transformation logging

## 🧪 Testing

```bash
# Run all tests
cd ingestion
python test_excel_parser.py

# Expected output: 27 tests passing
```

Test coverage includes:
- Excel validators (7 tests)
- Excel extractors (3 tests)
- Excel transformers (7 tests)
- Excel ingestion (8 tests)
- Integration workflows (2 tests)

## 📊 Sample Data

Sample Excel files are provided in `ingestion/sample_data/`:

- `iec61215_mst.xlsx` - IEC 61215 MST damp heat test (1000 hours)
- `iec61730_impact.xlsx` - IEC 61730 ball drop impact tests
- `iec62716_ammonia.xlsx` - IEC 62716 ammonia exposure logs
- `iec61701_salt_mist.xlsx` - IEC 61701 salt mist corrosion data
- `iv_curve_data.xlsx` - I-V curve measurements
- `multi_header_data.xlsx` - Multi-level header examples

## 🔧 Dependencies

Core dependencies:
- `openpyxl>=3.1.2` - Modern Excel formats
- `xlrd>=2.0.1` - Legacy Excel format (.xls)
- `pandas>=2.0.0` - Data processing
- `numpy>=1.24.0` - Numerical operations
- `scipy>=1.10.0` - Statistical analysis
- `pydantic>=2.0.0` - Data validation

See [requirements.txt](requirements.txt) for complete list.

## 🎯 Use Cases

### Laboratory Data Management
- Automated ingestion of test equipment outputs
- Standardized data validation across test protocols
- Traceability for accreditation audits

### Quality Assurance
- Outlier detection in production testing
- Unit consistency verification
- Duplicate test detection

### Research & Development
- I-V curve characteristic extraction
- Environmental stress test analysis
- Long-term stability monitoring

## 🔐 Error Handling

The system provides comprehensive error handling:

- `FileNotFoundError` - File doesn't exist
- `CorruptedFileError` - File cannot be read
- `InvalidSheetError` - Sheet doesn't exist
- `DataValidationError` - Data quality issues

All errors are logged with detailed messages for troubleshooting.

## 📈 Roadmap

Future enhancements:
- [ ] PDF report generation
- [ ] Database integration (PostgreSQL, MongoDB)
- [ ] REST API for data ingestion
- [ ] Real-time data validation dashboard
- [ ] Machine learning for anomaly detection
- [ ] Multi-language support
- [ ] Cloud storage integration (AWS S3, Azure Blob)

## 🤝 Contributing

Contributions are welcome! Please ensure:

1. All tests pass: `python test_excel_parser.py`
2. Code follows PEP 8: `black .` and `flake8 .`
3. Type hints are complete: `mypy .`
4. Documentation is updated

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Ganesh Gowri** - ASA (Advanced Solar Analytics)

## 🙏 Acknowledgments

- IEC standards documentation
- ISO/IEC 17025:2017 guidelines
- PV testing community
- Open source contributors

## 📞 Support

For issues, questions, or feature requests:
- Create an issue in this repository
- Contact: [Your contact information]

## 🔖 Version History

### Version 1.0.0 (2024-11-18)
- Initial release of Excel Data Ingestion Engine
- IEC-specific parsers for 61215, 61730, 62716, 61701
- I-V curve data parsing with characteristic points
- Comprehensive validation and transformation
- Full unit test coverage
- ISO 17025 compliant traceability

---

**Built with ❤️ for the PV testing community**
