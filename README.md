# PV Test Report Automation

World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## Project Status

✅ **Phase 2 Complete**: Word & PDF Data Ingestion Engine

## Project Structure

```
pv-test-report-automation/
├── ingestion/              # Word & PDF data ingestion engine ✓
│   ├── word_parser.py      # Word document parser
│   ├── pdf_parser.py       # PDF parser with table extraction
│   ├── ocr_engine.py       # OCR for scanned documents
│   ├── certificate_parser.py  # ISO 17025/NABL certificate parser
│   ├── document_validators.py # Validation functions
│   ├── models.py           # Pydantic data models
│   ├── exceptions.py       # Custom exceptions
│   ├── test_word_pdf.py    # Comprehensive unit tests
│   └── sample_data/        # Sample documents for testing
├── requirements.txt        # Python dependencies
├── LICENSE                 # MIT License
└── README.md              # This file
```

## Features

### Phase 2: Word & PDF Data Ingestion Engine ✓

Comprehensive document ingestion system supporting:

- **Word Documents (.docx)**: Text, tables, images, formatting, metadata
- **PDF Documents**: Native PDFs with text and table extraction
- **Scanned Documents**: OCR support using Tesseract
- **Calibration Certificates**: ISO 17025/NABL certificate parsing
- **Test Reports**: PV module test report data extraction
- **Validation**: Comprehensive data validation and error handling

📖 **[View Full Ingestion Module Documentation](ingestion/README.md)**

## Quick Start

### Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Tesseract OCR (for scanned documents):
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
```

3. Install Java (for table extraction):
```bash
# Ubuntu/Debian
sudo apt-get install default-jre

# macOS
brew install java
```

### Usage Examples

#### Parse a calibration certificate:

```python
from ingestion import parse_calibration_certificate

cert = parse_calibration_certificate("equipment_cal.pdf")
print(f"Certificate: {cert.certificate_number}")
print(f"Equipment: {cert.equipment_name} (S/N: {cert.serial_number})")
print(f"Calibration Date: {cert.calibration_date}")
print(f"Due Date: {cert.due_date}")
print(f"Days until due: {cert.days_until_due()}")
print(f"Valid: {cert.is_valid()}")
```

#### Parse a test report:

```python
from ingestion import PDFIngestion

parser = PDFIngestion("pv_test_report.pdf")
result = parser.parse(use_ocr_if_scanned=True)

print(f"Pages: {result.metadata.page_count}")
print(f"Tables found: {len(result.tables)}")

# Convert tables to DataFrames
for table in result.tables:
    df = table.to_dataframe()
    print(df.head())
```

#### Parse Word documents:

```python
from ingestion import WordDocumentParser

parser = WordDocumentParser("test_report.docx")
result = parser.parse()

print(f"Text content: {result.text_content[:200]}...")
print(f"Tables: {len(result.tables)}")
print(f"Images: {len(result.images)}")
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest ingestion/test_word_pdf.py -v

# Run with coverage
pytest ingestion/test_word_pdf.py --cov=ingestion --cov-report=html
```

## Technology Stack

- **Python 3.8+**
- **Document Processing**:
  - python-docx (Word documents)
  - PyPDF2, pdfplumber (PDF parsing)
  - tabula-py (PDF table extraction)
  - pytesseract (OCR)
  - PyMuPDF (image extraction)
- **Data & Validation**:
  - Pydantic (data models)
  - pandas (table data)
- **Testing**:
  - pytest (unit tests)
  - pytest-cov (coverage)

## Development Roadmap

- [x] **Phase 2**: Word & PDF Data Ingestion Engine
  - [x] Word document parsing (.docx)
  - [x] PDF parsing (native + scanned)
  - [x] OCR engine (Tesseract)
  - [x] Calibration certificate parser
  - [x] Document validators
  - [x] Comprehensive unit tests
  - [x] Documentation

- [ ] **Future Phases**:
  - [ ] Database integration
  - [ ] Report generation engine
  - [ ] Web interface
  - [ ] API endpoints
  - [ ] Automated workflows

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
