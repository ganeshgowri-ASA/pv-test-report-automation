"""
PV Test Report Automation - Data Ingestion Engine

Comprehensive JSON and CSV data ingestion for structured PV test data.
Supports time-series data, equipment formats, batch imports, and schema validation.
"""

from .csv_parser import CSVIngestion, CSVIngestionResult
from .json_parser import JSONIngestion, JSONIngestionResult
from .timeseries_parser import TimeSeriesParser
from .schema_validator import SchemaValidator
from .data_transformers import DataTransformer
from .models import (
    IngestionResult,
    ValidationError,
    TransformationConfig,
)
from .exceptions import (
    IngestionError,
    ValidationError as IngestionValidationError,
    SchemaError,
    ParseError,
)

__version__ = "1.0.0"
__all__ = [
    "CSVIngestion",
    "CSVIngestionResult",
    "JSONIngestion",
    "JSONIngestionResult",
    "TimeSeriesParser",
    "SchemaValidator",
    "DataTransformer",
    "IngestionResult",
    "ValidationError",
    "TransformationConfig",
    "IngestionError",
    "IngestionValidationError",
    "SchemaError",
    "ParseError",
]
