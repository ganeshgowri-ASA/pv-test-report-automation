"""
CSV Data Ingestion Engine

Comprehensive CSV parsing with auto-detection, validation, and large file streaming.
Supports various delimiters, encodings, and PV test equipment formats.
"""

import csv
import hashlib
import os
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, IO
import pandas as pd
import chardet
from io import StringIO

from .models import (
    CSVIngestionResult,
    IngestionMetadata,
    ValidationError as ValidationErrorModel,
)
from .exceptions import (
    ParseError,
    EncodingError,
    DelimiterError,
    ValidationError,
)


class CSVIngestion:
    """
    CSV data ingestion engine with auto-detection and validation.

    Features:
    - Auto-detect delimiter (comma, semicolon, tab, pipe)
    - Auto-detect encoding (UTF-8, Latin-1, Windows-1252, etc.)
    - Handle multi-line fields and various quote characters
    - Large file streaming support
    - Header row detection
    - Data validation and type checking

    Example:
        >>> ingestion = CSVIngestion("data/iv_curve.csv")
        >>> result = ingestion.parse()
        >>> if result.is_valid:
        ...     df = ingestion.get_dataframe()
        ...     print(f"Loaded {len(df)} rows")
    """

    COMMON_DELIMITERS = [',', ';', '\t', '|']
    CHUNK_SIZE = 10000  # Rows per chunk for streaming

    def __init__(self, file_path: Union[str, Path], encoding: Optional[str] = None):
        """
        Initialize CSV ingestion.

        Args:
            file_path: Path to CSV file
            encoding: File encoding (auto-detected if None)
        """
        self.file_path = Path(file_path)
        self.encoding = encoding
        self._dataframe: Optional[pd.DataFrame] = None
        self._detected_encoding: Optional[str] = None
        self._detected_delimiter: Optional[str] = None
        self._file_hash: Optional[str] = None

        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

    def _detect_encoding(self) -> str:
        """
        Auto-detect file encoding using chardet.

        Returns:
            Detected encoding name
        """
        if self.encoding:
            return self.encoding

        try:
            with open(self.file_path, 'rb') as f:
                # Read first 100KB for detection
                raw_data = f.read(100000)
                result = chardet.detect(raw_data)
                detected = result['encoding']
                confidence = result['confidence']

                if confidence < 0.7:
                    # Low confidence, try UTF-8 as fallback
                    detected = 'utf-8'

                self._detected_encoding = detected
                return detected

        except Exception as e:
            raise EncodingError(f"Failed to detect encoding: {e}")

    def _detect_delimiter(self, sample_lines: List[str], num_lines: int = 5) -> str:
        """
        Auto-detect CSV delimiter by analyzing sample lines.

        Args:
            sample_lines: Sample lines from file
            num_lines: Number of lines to analyze

        Returns:
            Detected delimiter character
        """
        if not sample_lines:
            raise DelimiterError("No sample lines provided for delimiter detection")

        # Use csv.Sniffer for detection
        try:
            sniffer = csv.Sniffer()
            sample = '\n'.join(sample_lines[:num_lines])
            dialect = sniffer.sniff(sample, delimiters=''.join(self.COMMON_DELIMITERS))
            self._detected_delimiter = dialect.delimiter
            return dialect.delimiter
        except Exception:
            # Fallback: count occurrences of each delimiter
            delimiter_counts = {delim: 0 for delim in self.COMMON_DELIMITERS}

            for line in sample_lines[:num_lines]:
                for delim in self.COMMON_DELIMITERS:
                    delimiter_counts[delim] += line.count(delim)

            # Choose delimiter with most consistent count
            best_delimiter = max(delimiter_counts, key=delimiter_counts.get)

            if delimiter_counts[best_delimiter] == 0:
                raise DelimiterError("Could not detect delimiter")

            self._detected_delimiter = best_delimiter
            return best_delimiter

    def _calculate_file_hash(self) -> str:
        """
        Calculate SHA-256 hash of file for traceability.

        Returns:
            Hexadecimal hash string
        """
        if self._file_hash:
            return self._file_hash

        sha256_hash = hashlib.sha256()
        with open(self.file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        self._file_hash = sha256_hash.hexdigest()
        return self._file_hash

    def _validate_dataframe(
        self,
        df: pd.DataFrame,
        required_columns: Optional[List[str]] = None,
        numeric_columns: Optional[List[str]] = None,
        range_checks: Optional[Dict[str, tuple]] = None,
    ) -> List[ValidationErrorModel]:
        """
        Validate DataFrame contents.

        Args:
            df: DataFrame to validate
            required_columns: Columns that must exist
            numeric_columns: Columns that should be numeric
            range_checks: {column: (min, max)} for range validation

        Returns:
            List of validation errors
        """
        errors = []

        # Check required columns
        if required_columns:
            missing = set(required_columns) - set(df.columns)
            if missing:
                errors.append(ValidationErrorModel(
                    field="columns",
                    error_type="missing_columns",
                    message=f"Missing required columns: {missing}",
                ))

        # Check numeric columns
        if numeric_columns:
            for col in numeric_columns:
                if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
                    errors.append(ValidationErrorModel(
                        field=col,
                        error_type="type_error",
                        message=f"Column '{col}' should be numeric",
                    ))

        # Range checks
        if range_checks:
            for col, (min_val, max_val) in range_checks.items():
                if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                    out_of_range = df[
                        (df[col] < min_val) | (df[col] > max_val)
                    ]
                    if len(out_of_range) > 0:
                        errors.append(ValidationErrorModel(
                            field=col,
                            error_type="range_error",
                            message=f"Column '{col}' has {len(out_of_range)} values outside range [{min_val}, {max_val}]",
                        ))

        return errors

    def parse(
        self,
        delimiter: Optional[str] = None,
        header_row: int = 0,
        skip_rows: Optional[List[int]] = None,
        use_columns: Optional[List[str]] = None,
        dtype: Optional[Dict[str, type]] = None,
        required_columns: Optional[List[str]] = None,
        numeric_columns: Optional[List[str]] = None,
        range_checks: Optional[Dict[str, tuple]] = None,
        streaming: bool = False,
    ) -> CSVIngestionResult:
        """
        Parse CSV file with validation.

        Args:
            delimiter: Column delimiter (auto-detected if None)
            header_row: Row number containing column headers
            skip_rows: Rows to skip
            use_columns: Only load these columns
            dtype: Column data types
            required_columns: Columns that must exist
            numeric_columns: Columns that should be numeric
            range_checks: {column: (min, max)} for validation
            streaming: Use chunked reading for large files

        Returns:
            CSVIngestionResult with metadata and validation results
        """
        start_time = time.time()
        warnings = []
        errors = []

        try:
            # Detect encoding
            encoding = self._detect_encoding()

            # Read sample for delimiter detection
            with open(self.file_path, 'r', encoding=encoding) as f:
                sample_lines = [f.readline() for _ in range(10)]

            # Detect delimiter
            if delimiter is None:
                delimiter = self._detect_delimiter(sample_lines)
                warnings.append(f"Auto-detected delimiter: '{delimiter}'")

            # Parse CSV
            if streaming:
                # Streaming mode for large files
                chunks = []
                for chunk in pd.read_csv(
                    self.file_path,
                    delimiter=delimiter,
                    encoding=encoding,
                    header=header_row,
                    skiprows=skip_rows,
                    usecols=use_columns,
                    dtype=dtype,
                    chunksize=self.CHUNK_SIZE,
                    on_bad_lines='warn',
                ):
                    chunks.append(chunk)
                df = pd.concat(chunks, ignore_index=True)
            else:
                # Standard mode
                df = pd.read_csv(
                    self.file_path,
                    delimiter=delimiter,
                    encoding=encoding,
                    header=header_row,
                    skiprows=skip_rows,
                    usecols=use_columns,
                    dtype=dtype,
                    on_bad_lines='warn',
                )

            self._dataframe = df

            # Validate DataFrame
            validation_errors = self._validate_dataframe(
                df,
                required_columns=required_columns,
                numeric_columns=numeric_columns,
                range_checks=range_checks,
            )
            errors.extend(validation_errors)

            # Check for duplicate rows
            duplicates = df.duplicated().sum()
            if duplicates > 0:
                warnings.append(f"Found {duplicates} duplicate rows")

            # Create metadata
            file_size = os.path.getsize(self.file_path)
            file_hash = self._calculate_file_hash()
            duration_ms = (time.time() - start_time) * 1000

            metadata = IngestionMetadata(
                file_path=str(self.file_path),
                file_size_bytes=file_size,
                file_hash=file_hash,
                original_filename=self.file_path.name,
                ingestion_duration_ms=duration_ms,
            )

            # Create data preview (first 5 rows)
            preview = df.head(5).to_dict(orient='records') if len(df) > 0 else None

            # Create result
            result = CSVIngestionResult(
                success=True,
                row_count=len(df),
                column_count=len(df.columns),
                columns=df.columns.tolist(),
                delimiter_detected=delimiter,
                encoding_detected=encoding,
                header_row=header_row,
                metadata=metadata,
                warnings=warnings,
                errors=errors,
                data_preview=preview,
            )

            return result

        except Exception as e:
            # Parse failed
            duration_ms = (time.time() - start_time) * 1000
            file_size = os.path.getsize(self.file_path)

            metadata = IngestionMetadata(
                file_path=str(self.file_path),
                file_size_bytes=file_size,
                file_hash="",
                original_filename=self.file_path.name,
                ingestion_duration_ms=duration_ms,
            )

            error = ValidationErrorModel(
                field="parse",
                error_type="parse_error",
                message=str(e),
            )

            return CSVIngestionResult(
                success=False,
                row_count=0,
                column_count=0,
                columns=[],
                delimiter_detected=delimiter or "",
                encoding_detected=encoding if self._detected_encoding else "",
                metadata=metadata,
                errors=[error],
            )

    def get_dataframe(self) -> pd.DataFrame:
        """
        Get parsed DataFrame.

        Returns:
            Parsed DataFrame

        Raises:
            ValueError: If parse() has not been called
        """
        if self._dataframe is None:
            raise ValueError("CSV not yet parsed. Call parse() first.")
        return self._dataframe

    def parse_timeseries(
        self,
        timestamp_col: str,
        value_cols: List[str],
        timestamp_format: Optional[str] = None,
        **parse_kwargs
    ) -> CSVIngestionResult:
        """
        Parse CSV as time-series data.

        Args:
            timestamp_col: Column containing timestamps
            value_cols: Columns containing values
            timestamp_format: Timestamp format string (auto-detected if None)
            **parse_kwargs: Additional arguments for parse()

        Returns:
            CSVIngestionResult
        """
        result = self.parse(**parse_kwargs)

        if result.is_valid and self._dataframe is not None:
            try:
                # Parse timestamps
                self._dataframe[timestamp_col] = pd.to_datetime(
                    self._dataframe[timestamp_col],
                    format=timestamp_format,
                    errors='coerce'
                )

                # Check for invalid timestamps
                invalid_ts = self._dataframe[timestamp_col].isna().sum()
                if invalid_ts > 0:
                    result.warnings.append(
                        f"Found {invalid_ts} invalid timestamps in '{timestamp_col}'"
                    )

                # Set timestamp as index
                self._dataframe = self._dataframe.set_index(timestamp_col)

            except Exception as e:
                error = ValidationErrorModel(
                    field=timestamp_col,
                    error_type="timestamp_parse_error",
                    message=str(e),
                )
                result.errors.append(error)
                result.success = False

        return result

    def parse_batch_results(
        self,
        serial_col: str = "Serial",
        **parse_kwargs
    ) -> CSVIngestionResult:
        """
        Parse batch test results CSV.

        Typical columns: Serial, Voc, Isc, Pmax, FF, Efficiency

        Args:
            serial_col: Column containing module serial numbers
            **parse_kwargs: Additional arguments for parse()

        Returns:
            CSVIngestionResult
        """
        result = self.parse(**parse_kwargs)

        if result.is_valid and self._dataframe is not None:
            # Validate serial column exists
            if serial_col not in self._dataframe.columns:
                error = ValidationErrorModel(
                    field=serial_col,
                    error_type="missing_column",
                    message=f"Serial column '{serial_col}' not found",
                )
                result.errors.append(error)
                result.success = False
            else:
                # Check for duplicate serials
                duplicates = self._dataframe[serial_col].duplicated().sum()
                if duplicates > 0:
                    result.warnings.append(
                        f"Found {duplicates} duplicate serial numbers"
                    )

        return result
