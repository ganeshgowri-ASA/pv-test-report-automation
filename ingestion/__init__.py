"""
Word and PDF Data Ingestion Engine for PV Test Reports and Calibration Certificates.

This package provides comprehensive tools for extracting structured data from:
- Word documents (.docx, .doc)
- PDF documents (native and scanned)
- Calibration certificates (ISO 17025/NABL)
- Test reports and datasheets
"""

from ingestion.word_parser import WordDocumentParser
from ingestion.pdf_parser import PDFIngestion
from ingestion.ocr_engine import OCREngine
from ingestion.certificate_parser import parse_calibration_certificate
from ingestion.models import (
    DocumentIngestionResult,
    CalibrationCertificate,
    TableData,
    ImageData,
    DocumentMetadata,
)
from ingestion.exceptions import (
    DocumentParsingError,
    UnsupportedFormatError,
    CorruptedFileError,
    OCRError,
    TableExtractionError,
)

__version__ = "1.0.0"

__all__ = [
    "WordDocumentParser",
    "PDFIngestion",
    "OCREngine",
    "parse_calibration_certificate",
    "DocumentIngestionResult",
    "CalibrationCertificate",
    "TableData",
    "ImageData",
    "DocumentMetadata",
    "DocumentParsingError",
    "UnsupportedFormatError",
    "CorruptedFileError",
    "OCRError",
    "TableExtractionError",
]
