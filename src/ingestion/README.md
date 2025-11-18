# Data Ingestion Module

Production-ready data ingestion system for PV (Photovoltaic) test automation, supporting IEC 61215, 61730, ISO 17025, and other international standards.

## Overview

This module provides comprehensive data ingestion capabilities for PV test lab automation, including:

- **Excel parsing** with I-V curve extraction
- **Document processing** for PDF and Word reports
- **Image processing** with OCR and chart analysis
- **Database storage** with SQLAlchemy ORM
- **Traceability tracking** for ISO 17025 compliance

## Modules

### 1. Excel Parser (`excel_parser.py`)
Parses Excel test data files with support for:
- I-V curve data extraction
- Temperature coefficient parsing
- Flash test results
- Multiple sheet formats
- Data cleaning and normalization
- Progress tracking
- Async batch processing

**Key Classes:**
- `ExcelParser`: Main parser class
- `IVCurveData`: I-V curve data model
- `TemperatureCoefficient`: Temperature coefficient model
- `FlashTestData`: Flash test data model

**Example:**
```python
from src.ingestion import ExcelParser, IVCurveData

parser = ExcelParser()
iv_data = parser.extract_iv_curve("test_data.xlsx")
print(f"Pmax: {iv_data.pmax} W")
print(f"Fill Factor: {iv_data.fill_factor}")
```

### 2. Document Processor (`document_processor.py`)
Processes PDF and Word documents with:
- Text extraction
- Table extraction
- Metadata extraction (report ID, standards, etc.)
- Section identification
- Search functionality
- Async batch processing

**Key Classes:**
- `DocumentProcessor`: Main processor class
- `TestReportDocument`: Complete document structure
- `DocumentMetadata`: Document metadata
- `TableData`: Extracted table data
- `SectionData`: Document section structure

**Example:**
```python
from src.ingestion import DocumentProcessor

processor = DocumentProcessor()
document = processor.process_pdf("test_report.pdf")
print(f"Report ID: {document.metadata.report_id}")
print(f"Tables found: {len(document.tables)}")
```

### 3. Image Processor (`image_processor.py`)
Handles image processing with:
- Test chart/graph extraction
- OCR for scanned reports
- Image preprocessing and enhancement
- Visual quality control
- Metadata extraction
- Async batch processing

**Key Classes:**
- `ImageProcessor`: Main processor class
- `TestChart`: Chart extraction result
- `OCRResult`: OCR extraction result
- `VisualQCResult`: Quality control result
- `ImageMetadata`: Image metadata

**Example:**
```python
from src.ingestion import ImageProcessor

processor = ImageProcessor()
chart = processor.extract_test_chart("iv_curve.png", chart_type="IV_curve")
qc_result = processor.perform_visual_qc("module_image.jpg")
print(f"QC Passed: {qc_result.qc_passed}")
```

### 4. Storage Manager (`storage_manager.py`)
Database integration with:
- SQLAlchemy ORM models
- File and blob storage
- Data versioning
- Transaction management
- Async support
- Batch operations

**Key Classes:**
- `StorageManager`: Main storage manager
- `TestDataModel`: Test data database model
- `ReportModel`: Report database model
- `BlobStorageModel`: Binary/image storage model
- `DataVersionModel`: Version control model
- `AuditLogModel`: Audit trail model

**Example:**
```python
from src.ingestion import StorageManager, TestDataCreate

manager = StorageManager("sqlite:///pv_data.db")
manager.create_tables()

test_data = TestDataCreate(
    module_id="MOD-001",
    test_type="flash_test",
    test_date=datetime.utcnow(),
    test_standard="IEC 61215",
    results={"voc": 38.5, "isc": 8.9},
    voc=38.5,
    isc=8.9,
    pmax=300.0
)

result = manager.create_test_data(test_data)
print(f"Created test data ID: {result.id}")
```

### 5. Traceability Tracker (`traceability_tracker.py`)
ISO 17025 compliant traceability with:
- Comprehensive audit logging
- Data lineage tracking
- Change history
- Equipment and calibration tracking
- Checksum verification
- Compliance validation

**Key Classes:**
- `TraceabilityTracker`: Main tracker class
- `AuditLog`: Audit log entry
- `DataLineage`: Data lineage record
- `ChangeHistory`: Change tracking
- `ISO17025Traceability`: ISO 17025 compliance record

**Example:**
```python
from src.ingestion import TraceabilityTracker, ActionType, EntityType

tracker = TraceabilityTracker()

# Log action
log = tracker.log_action(
    action=ActionType.CREATE,
    entity_type=EntityType.TEST_DATA,
    entity_id="test_001",
    user_id="engineer@lab.com",
    new_value={"voc": 38.5}
)

# Create lineage
lineage = tracker.create_lineage("test_001", EntityType.TEST_DATA)
lineage.add_source(EntityType.DOCUMENT, "doc_001", "Test Report PDF")

# ISO 17025 record
iso_record = tracker.create_iso17025_record(
    test_id="test_001",
    report_id="rpt_001",
    performed_by="John Doe",
    test_date=datetime.utcnow(),
    test_procedure="TP-IEC61215",
    test_method="Flash Test"
)
```

## Installation

```bash
pip install -r requirements.txt
```

### Optional Dependencies

For OCR functionality:
```bash
# Install Tesseract OCR engine
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr

# macOS:
brew install tesseract

# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
```

For PostgreSQL support:
```bash
pip install psycopg2-binary
```

## Testing

Run all tests:
```bash
pytest src/ingestion/tests/
```

Run with coverage:
```bash
pytest src/ingestion/tests/ --cov=src/ingestion --cov-report=html
```

Run specific test module:
```bash
pytest src/ingestion/tests/test_excel_parser.py -v
```

## Usage Examples

### Complete Workflow Example

```python
from datetime import datetime
from src.ingestion import (
    ExcelParser,
    DocumentProcessor,
    ImageProcessor,
    StorageManager,
    TraceabilityTracker,
    TestDataCreate,
    ActionType,
    EntityType
)

# Initialize components
excel_parser = ExcelParser()
doc_processor = DocumentProcessor()
img_processor = ImageProcessor()
storage = StorageManager("sqlite:///pv_lab.db")
tracker = TraceabilityTracker()

# Create database
storage.create_tables()

# Process Excel data
iv_data = excel_parser.extract_iv_curve("test_data.xlsx")

# Process PDF report
report_doc = doc_processor.process_pdf("test_report.pdf")

# Process test chart image
chart = img_processor.extract_test_chart("iv_curve.png", "IV_curve")

# Store in database
test_data = TestDataCreate(
    module_id=report_doc.metadata.module_serial,
    test_type="flash_test",
    test_date=datetime.utcnow(),
    test_standard="IEC 61215",
    results=iv_data.dict(),
    voc=iv_data.voc,
    isc=iv_data.isc,
    pmax=iv_data.pmax,
    created_by="test_engineer"
)

db_record = storage.create_test_data(test_data)

# Track traceability
lineage = tracker.create_lineage(str(db_record.id), EntityType.TEST_DATA)
lineage.add_source(EntityType.DOCUMENT, "pdf_001", "Original Test Report")
lineage.add_processing_step("data_extraction", "Extracted I-V curve from PDF")

audit_log = tracker.log_action(
    action=ActionType.CREATE,
    entity_type=EntityType.TEST_DATA,
    entity_id=str(db_record.id),
    user_id="engineer@lab.com",
    new_value=test_data.dict()
)

print(f"Test data stored with ID: {db_record.id}")
print(f"Audit log created: {audit_log.id}")
```

### Async Batch Processing

```python
import asyncio
from src.ingestion import ExcelParser, DocumentProcessor

async def process_batch():
    excel_parser = ExcelParser()
    doc_processor = DocumentProcessor()
    
    # Process multiple Excel files
    excel_files = ["test1.xlsx", "test2.xlsx", "test3.xlsx"]
    excel_results = await excel_parser.parse_batch_async(excel_files)
    
    # Process multiple PDFs
    pdf_files = ["report1.pdf", "report2.pdf", "report3.pdf"]
    pdf_results = await doc_processor.process_batch_async(pdf_files)
    
    return excel_results, pdf_results

# Run async processing
excel_data, pdf_data = asyncio.run(process_batch())
```

## Compliance Standards

This module supports the following standards:

- **IEC 61215**: PV module design qualification and type approval
- **IEC 61730**: PV module safety qualification
- **IEC 61853**: PV module performance testing
- **IEC 60904**: PV devices measurement procedures
- **ISO 17025**: Testing and calibration laboratory competence
- **ISO 9001**: Quality management systems
- **NABL**: National Accreditation Board for Testing
- **ILAC**: International Laboratory Accreditation Cooperation

## Architecture

```
src/ingestion/
├── __init__.py
├── excel_parser.py          # Excel data parsing
├── document_processor.py    # PDF/Word processing
├── image_processor.py       # Image and OCR processing
├── storage_manager.py       # Database integration
├── traceability_tracker.py  # Audit and lineage tracking
└── tests/
    ├── __init__.py
    ├── test_excel_parser.py
    ├── test_document_processor.py
    ├── test_image_processor.py
    ├── test_storage_manager.py
    └── test_traceability_tracker.py
```

## Performance Considerations

- **Async support**: All modules support async batch processing for improved throughput
- **Progress tracking**: Long-running operations provide progress callbacks
- **Database connection pooling**: Efficient database connection management
- **Blob deduplication**: Hash-based deduplication for images/documents
- **Lazy loading**: Relationships loaded on demand to optimize memory

## Error Handling

All modules implement comprehensive error handling:

```python
from src.ingestion import ExcelParser

parser = ExcelParser()

try:
    iv_data = parser.extract_iv_curve("test.xlsx")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except ValueError as e:
    print(f"Invalid data format: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Contributing

When adding new features:

1. Follow Pydantic model patterns for data validation
2. Implement progress tracking for long operations
3. Add comprehensive error handling
4. Write unit tests with >80% coverage
5. Update this README with examples

## License

See LICENSE file in the root directory.
