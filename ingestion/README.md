# Word & PDF Data Ingestion Engine

Comprehensive data extraction engine for PV test reports, calibration certificates, and technical documents.

## Features

### 📄 Document Format Support
- **Word Documents** (.docx) - Full text, tables, images, and formatting
- **PDF Documents** - Native PDFs with text and table extraction
- **Scanned Documents** - OCR support via Tesseract for scanned PDFs and images
- **Password-Protected PDFs** - Decrypt and parse secured documents

### 🔍 Data Extraction Capabilities

#### Word Documents (.docx)
- Extract text with paragraph structure preservation
- Parse tables and convert to pandas DataFrames
- Extract embedded images (charts, graphs, photos)
- Preserve formatting metadata (bold, italic, headings)
- Extract document properties (author, date, revision)
- Handle comments and track changes

#### PDF Documents
- Text extraction from native PDFs
- OCR for scanned PDFs using Tesseract
- Table detection and extraction (pdfplumber + tabula-py)
- Image extraction from PDF pages
- Metadata extraction (PDF info, properties)
- Multi-page processing
- Scanned PDF detection

#### Calibration Certificates (ISO 17025/NABL)
- Equipment information (model, serial, manufacturer)
- Calibration dates (calibration date, due date)
- Uncertainty values and measurement ranges
- Accreditation body identification (NABL, ILAC, etc.)
- Certificate number extraction
- Traceability chain parsing
- Calibration points extraction
- Environmental conditions
- Personnel information (calibrated by, approved by)

#### Test Reports
- Test results tables extraction
- Module specifications parsing
- Equipment lists with calibration status
- Test conditions (temperature, irradiance, humidity)
- IEC standard references
- Personnel and signatures

### 🛡️ Validation & Error Handling
- File corruption detection
- Data format validation
- OCR confidence scoring
- Incomplete data flagging
- Custom exception hierarchy
- Comprehensive warning system

## Installation

### System Requirements

1. **Python 3.8+**

2. **Tesseract OCR** (for scanned document support):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr

   # macOS
   brew install tesseract

   # Windows
   # Download from: https://github.com/UB-Mannheim/tesseract/wiki
   ```

3. **Java** (for tabula-py table extraction):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install default-jre

   # macOS
   brew install java
   ```

### Python Dependencies

Install all required packages:

```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Parse a Word Document

```python
from ingestion import WordDocumentParser

# Parse Word document
parser = WordDocumentParser("test_report.docx")
result = parser.parse()

print(f"Text: {result.text_content[:200]}...")
print(f"Tables: {len(result.tables)}")
print(f"Images: {len(result.images)}")
print(f"Author: {result.metadata.author}")

# Access tables as DataFrames
for table in result.tables:
    df = table.to_dataframe()
    print(df.head())
```

### 2. Parse a PDF Document

```python
from ingestion import PDFIngestion

# Parse native PDF
parser = PDFIngestion("technical_datasheet.pdf")
result = parser.parse(use_ocr_if_scanned=True)

print(f"Pages: {result.metadata.page_count}")
print(f"Extraction method: {result.extraction_method}")
print(f"OCR confidence: {result.ocr_confidence:.2%}")

# Extract tables from specific page
tables = parser.extract_tables(page_number=2)
for table in tables:
    print(table.to_dataframe())

# Extract images
images = parser.extract_images()
for img in images:
    print(f"Image: {img.format}, {img.width}x{img.height}")
```

### 3. Parse Calibration Certificate

```python
from ingestion import parse_calibration_certificate

# Parse ISO 17025/NABL calibration certificate
cert = parse_calibration_certificate("equipment_cal.pdf")

print(f"Certificate No: {cert.certificate_number}")
print(f"Equipment: {cert.equipment_name}")
print(f"Model: {cert.model}")
print(f"Serial: {cert.serial_number}")
print(f"Calibration Date: {cert.calibration_date}")
print(f"Due Date: {cert.due_date}")
print(f"Days until due: {cert.days_until_due()}")
print(f"Is valid: {cert.is_valid()}")
print(f"Accreditation: {cert.accreditation_body.value}")

# Access calibration points
for point in cert.calibration_points:
    print(f"Reference: {point.reference_value} {point.unit}")
    print(f"Measured: {point.measured_value} {point.unit}")
    print(f"Deviation: {point.deviation} {point.unit}")

# Uncertainty information
if cert.uncertainty:
    print(f"Uncertainty: ±{cert.uncertainty.value} {cert.uncertainty.unit}")
    print(f"Coverage factor: k={cert.uncertainty.coverage_factor}")
```

### 4. OCR Scanned Documents

```python
from ingestion import OCREngine

# Process scanned PDF with OCR
ocr = OCREngine("scanned_report.pdf", language="eng", dpi=300)
result = ocr.parse()

print(f"OCR Confidence: {result.ocr_confidence:.2%}")
print(f"Extracted text: {result.text_content}")

# Check for warnings
for warning in result.warnings:
    print(f"Warning: {warning}")
```

### 5. Password-Protected PDFs

```python
from ingestion import PDFIngestion

# Parse encrypted PDF
parser = PDFIngestion("protected_cert.pdf", password="secret123")
result = parser.parse()

print(f"Successfully decrypted and parsed: {result.file_path}")
```

## Data Models

### DocumentIngestionResult

Complete result of document parsing:

```python
class DocumentIngestionResult(BaseModel):
    text_content: str                    # Full extracted text
    tables: List[TableData]              # Extracted tables
    images: List[ImageData]              # Extracted images
    paragraphs: List[ParagraphData]      # Paragraphs with formatting
    metadata: DocumentMetadata           # Document properties
    extraction_method: ExtractionMethod  # "native", "ocr", or "hybrid"
    ocr_confidence: float                # 0-1 confidence score
    file_hash: str                       # SHA-256 hash
    file_path: str                       # Source file path
    warnings: List[str]                  # Extraction warnings
    errors: List[str]                    # Extraction errors
```

### CalibrationCertificate

ISO 17025/NABL calibration certificate data:

```python
class CalibrationCertificate(BaseModel):
    certificate_number: str
    equipment_id: str
    equipment_name: str
    manufacturer: Optional[str]
    model: Optional[str]
    serial_number: Optional[str]

    calibration_date: date
    due_date: Optional[date]
    calibration_interval_months: Optional[int]

    uncertainty: Optional[UncertaintyMeasurement]
    calibration_points: List[CalibrationPoint]

    traceability: Optional[TraceabilityInfo]
    accreditation_body: AccreditationBody

    laboratory_name: str
    laboratory_address: Optional[str]

    calibrated_by: Optional[str]
    reviewed_by: Optional[str]
    approved_by: Optional[str]

    environmental_conditions: Dict[str, Any]
    raw_text: Optional[str]
```

## Validation

### Validate Extraction Results

```python
from ingestion.document_validators import validate_ingestion_result

result = parser.parse()
is_valid, warnings = validate_ingestion_result(result)

if is_valid:
    print("✓ Document parsed successfully")
else:
    print("⚠ Validation warnings:")
    for warning in warnings:
        print(f"  - {warning}")
```

### Validate Calibration Certificates

```python
from ingestion.document_validators import validate_calibration_certificate

cert = parse_calibration_certificate("cert.pdf")
is_valid, warnings = validate_calibration_certificate(cert)

if not is_valid:
    print("Certificate validation issues:")
    for warning in warnings:
        print(f"  - {warning}")
```

## Error Handling

The engine provides specific exceptions for different error scenarios:

```python
from ingestion.exceptions import (
    DocumentParsingError,      # Base parsing error
    UnsupportedFormatError,    # Unsupported file format
    CorruptedFileError,        # Corrupted or unreadable file
    OCRError,                  # OCR processing failed
    TableExtractionError,      # Table extraction failed
    ValidationError,           # Data validation failed
    PasswordProtectedError,    # PDF password required
)

try:
    result = parse_pdf_document("report.pdf")
except PasswordProtectedError:
    result = PDFIngestion("report.pdf", password="password123").parse()
except CorruptedFileError as e:
    print(f"File is corrupted: {e}")
except UnsupportedFormatError as e:
    print(f"Unsupported format: {e}")
```

## Advanced Usage

### Extract Tables with Multiple Methods

```python
# Try both pdfplumber and tabula for best results
parser = PDFIngestion("complex_report.pdf")

# Method 1: pdfplumber (better for simple tables)
tables_plumber = parser.extract_tables(page_number=3)

# Method 2: tabula-py (better for complex tables)
tables_tabula = parser.extract_tables_with_tabula(page_number=3)

# Combine results
all_tables = tables_plumber + tables_tabula
```

### Custom OCR Configuration

```python
from ingestion import OCREngine

# High-resolution OCR for better accuracy
ocr = OCREngine(
    "scanned_cert.pdf",
    language="eng",  # Tesseract language
    dpi=600          # Higher DPI for better quality
)

result = ocr.parse()
```

### Batch Processing

```python
from pathlib import Path
from ingestion import parse_pdf_document

results = []
for pdf_file in Path("certificates/").glob("*.pdf"):
    try:
        result = parse_pdf_document(str(pdf_file), use_ocr=True)
        results.append(result)
        print(f"✓ Processed: {pdf_file.name}")
    except Exception as e:
        print(f"✗ Failed: {pdf_file.name} - {e}")

print(f"\nSuccessfully processed {len(results)} documents")
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest ingestion/test_word_pdf.py -v

# Run specific test class
pytest ingestion/test_word_pdf.py::TestModels -v

# Run with coverage
pytest ingestion/test_word_pdf.py --cov=ingestion --cov-report=html
```

## File Structure

```
ingestion/
├── __init__.py                  # Package initialization
├── models.py                    # Pydantic data models
├── exceptions.py                # Custom exceptions
├── word_parser.py               # Word document parser
├── pdf_parser.py                # PDF parser
├── ocr_engine.py                # OCR engine
├── certificate_parser.py        # Calibration certificate parser
├── document_validators.py       # Validation functions
├── test_word_pdf.py            # Unit tests
├── README.md                    # This file
└── sample_data/
    ├── sample_calibration_cert.txt
    ├── sample_test_report.txt
    └── test_document.txt
```

## Limitations & Notes

1. **OCR Accuracy**: OCR quality depends on:
   - Image resolution (recommended: 300+ DPI)
   - Document clarity and contrast
   - Tesseract language data availability

2. **Table Extraction**: Complex tables may require manual review:
   - Merged cells may not parse correctly
   - Multi-line cells can be challenging
   - Nested tables are not supported

3. **Word Document**: Only .docx format supported:
   - Legacy .doc files not supported
   - Use LibreOffice/Word to convert .doc → .docx

4. **Performance**:
   - OCR processing is CPU-intensive
   - Large PDFs (>100 pages) may take several minutes
   - Consider parallel processing for batch operations

## Troubleshooting

### Tesseract Not Found

```bash
# Verify Tesseract installation
tesseract --version

# Add to PATH (Windows)
# Add Tesseract installation directory to system PATH

# Specify path in code (if needed)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### Java Not Found (tabula-py)

```bash
# Verify Java installation
java -version

# Install OpenJDK
sudo apt-get install default-jre
```

### Low OCR Confidence

```python
# Try with higher DPI
ocr = OCREngine("scan.pdf", dpi=600)

# Or preprocess images manually
from PIL import Image, ImageEnhance

img = Image.open("scan.png")
img = img.convert("L")  # Grayscale
enhancer = ImageEnhance.Contrast(img)
img = enhancer.enhance(2.0)  # Increase contrast
```

## Contributing

Contributions are welcome! Areas for improvement:

- [ ] Support for .doc (legacy Word) files
- [ ] Advanced table detection using ML models
- [ ] Multi-language OCR support
- [ ] Parallel processing for batch operations
- [ ] Excel file parsing
- [ ] Image-based table extraction

## License

This project is part of the PV Test Report Automation system.

## Support

For issues, questions, or contributions, please refer to the main project repository.
