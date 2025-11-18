"""
Excel Data Ingestion Engine for PV Test Report Automation

This package provides comprehensive Excel data ingestion functionality for
multi-format PV test data, including IEC-specific parsers and validators.
"""

from .excel_parser import ExcelIngestion, ExcelIngestionResult
from .excel_validators import ExcelValidator
from .excel_extractors import ExcelExtractor
from .excel_transformers import ExcelTransformer

__version__ = "1.0.0"
__all__ = [
    "ExcelIngestion",
    "ExcelIngestionResult",
    "ExcelValidator",
    "ExcelExtractor",
    "ExcelTransformer",
]
