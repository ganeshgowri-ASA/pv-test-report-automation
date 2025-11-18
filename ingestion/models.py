"""
Pydantic models for data ingestion results and configuration.
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import pandas as pd


class ValidationError(BaseModel):
    """Validation error details."""
    field: str
    error_type: str
    message: str
    row: Optional[int] = None
    value: Optional[Any] = None


class IngestionMetadata(BaseModel):
    """Metadata for ingested data."""
    ingestion_timestamp: datetime = Field(default_factory=datetime.utcnow)
    file_path: str
    file_size_bytes: int
    file_hash: str  # SHA-256
    original_filename: str
    ingestion_duration_ms: float
    ingestion_version: str = "1.0.0"


class CSVIngestionResult(BaseModel):
    """Result of CSV ingestion operation."""
    success: bool
    row_count: int
    column_count: int
    columns: List[str]
    delimiter_detected: str
    encoding_detected: str
    header_row: int = 0
    metadata: IngestionMetadata
    warnings: List[str] = Field(default_factory=list)
    errors: List[ValidationError] = Field(default_factory=list)
    data_preview: Optional[Dict[str, Any]] = None  # First 5 rows as dict

    class Config:
        arbitrary_types_allowed = True

    @property
    def is_valid(self) -> bool:
        """Check if ingestion was successful with no errors."""
        return self.success and len(self.errors) == 0


class JSONIngestionResult(BaseModel):
    """Result of JSON ingestion operation."""
    success: bool
    record_count: int  # Number of records (for JSON Lines) or 1 for standard JSON
    schema_validated: bool
    schema_errors: List[str] = Field(default_factory=list)
    nested_depth: int
    metadata: IngestionMetadata
    warnings: List[str] = Field(default_factory=list)
    errors: List[ValidationError] = Field(default_factory=list)
    data_preview: Optional[Dict[str, Any]] = None

    @property
    def is_valid(self) -> bool:
        """Check if ingestion was successful with no errors."""
        return self.success and len(self.errors) == 0


class TimeSeriesConfig(BaseModel):
    """Configuration for time-series data parsing."""
    timestamp_col: str
    value_cols: List[str]
    timestamp_format: Optional[str] = None  # Auto-detect if None
    timezone: Optional[str] = None
    resample_frequency: Optional[str] = None  # e.g., '1min', '1H'
    interpolation_method: str = "linear"
    outlier_std_threshold: float = 3.0  # Standard deviations for outlier detection


class TransformationConfig(BaseModel):
    """Configuration for data transformations."""
    column_mapping: Optional[Dict[str, str]] = None  # Rename columns
    unit_conversions: Optional[Dict[str, tuple]] = None  # {column: (from_unit, to_unit)}
    drop_columns: Optional[List[str]] = None
    filter_conditions: Optional[Dict[str, Any]] = None
    aggregate_functions: Optional[Dict[str, str]] = None  # {column: 'mean'/'sum'/etc}
    pivot_config: Optional[Dict[str, Any]] = None


class IngestionResult(BaseModel):
    """Generic ingestion result wrapper."""
    result_type: str  # 'csv' or 'json'
    csv_result: Optional[CSVIngestionResult] = None
    json_result: Optional[JSONIngestionResult] = None

    @property
    def is_valid(self) -> bool:
        """Check if ingestion was successful."""
        if self.result_type == 'csv' and self.csv_result:
            return self.csv_result.is_valid
        elif self.result_type == 'json' and self.json_result:
            return self.json_result.is_valid
        return False

    @property
    def errors(self) -> List[ValidationError]:
        """Get all errors."""
        if self.result_type == 'csv' and self.csv_result:
            return self.csv_result.errors
        elif self.result_type == 'json' and self.json_result:
            return self.json_result.errors
        return []


class BatchImportResult(BaseModel):
    """Result of batch import operation."""
    total_files: int
    successful: int
    failed: int
    results: List[IngestionResult]
    duration_ms: float
    summary: Dict[str, Any]
