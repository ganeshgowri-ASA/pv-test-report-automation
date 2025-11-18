"""
JSON Data Ingestion Engine

Comprehensive JSON parsing with schema validation.
Supports standard JSON, JSON Lines (.jsonl), and nested structure flattening.
"""

import json
import hashlib
import os
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import pandas as pd
import chardet

from .models import (
    JSONIngestionResult,
    IngestionMetadata,
    ValidationError as ValidationErrorModel,
)
from .exceptions import (
    ParseError,
    SchemaError,
    EncodingError,
)


class JSONIngestion:
    """
    JSON data ingestion engine with schema validation.

    Features:
    - Parse standard JSON files
    - Parse JSON Lines (.jsonl) format
    - Schema validation using JSON Schema
    - Nested structure flattening
    - Graceful handling of malformed JSON
    - Pretty-print for debugging

    Example:
        >>> ingestion = JSONIngestion("data/chamber_log.json")
        >>> result = ingestion.parse(schema="schemas/chamber_log_schema.json")
        >>> if result.is_valid:
        ...     data = ingestion.get_data()
        ...     print(f"Loaded {result.record_count} records")
    """

    def __init__(self, file_path: Union[str, Path], encoding: Optional[str] = None):
        """
        Initialize JSON ingestion.

        Args:
            file_path: Path to JSON file
            encoding: File encoding (auto-detected if None)
        """
        self.file_path = Path(file_path)
        self.encoding = encoding
        self._data: Optional[Union[Dict, List]] = None
        self._dataframe: Optional[pd.DataFrame] = None
        self._detected_encoding: Optional[str] = None
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

    def _calculate_nested_depth(self, obj: Any, current_depth: int = 0) -> int:
        """
        Calculate maximum nesting depth of JSON structure.

        Args:
            obj: JSON object
            current_depth: Current depth level

        Returns:
            Maximum depth
        """
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(
                self._calculate_nested_depth(v, current_depth + 1)
                for v in obj.values()
            )
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(
                self._calculate_nested_depth(item, current_depth + 1)
                for item in obj
            )
        else:
            return current_depth

    def _validate_schema(
        self,
        data: Union[Dict, List],
        schema: Union[str, Path, Dict]
    ) -> tuple[bool, List[str]]:
        """
        Validate JSON data against schema.

        Args:
            data: JSON data to validate
            schema: Schema file path or schema dict

        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            import jsonschema
        except ImportError:
            return False, ["jsonschema package not installed. Install with: pip install jsonschema"]

        try:
            # Load schema if it's a file path
            if isinstance(schema, (str, Path)):
                schema_path = Path(schema)
                if not schema_path.exists():
                    return False, [f"Schema file not found: {schema}"]

                with open(schema_path, 'r') as f:
                    schema_dict = json.load(f)
            else:
                schema_dict = schema

            # Validate
            jsonschema.validate(instance=data, schema=schema_dict)
            return True, []

        except jsonschema.exceptions.ValidationError as e:
            return False, [f"Validation error: {e.message}"]
        except jsonschema.exceptions.SchemaError as e:
            return False, [f"Schema error: {e.message}"]
        except Exception as e:
            return False, [f"Validation failed: {str(e)}"]

    def _is_json_lines(self) -> bool:
        """
        Check if file is JSON Lines format (.jsonl).

        Returns:
            True if JSON Lines format
        """
        return self.file_path.suffix.lower() in ['.jsonl', '.ndjson']

    def parse(
        self,
        schema: Optional[Union[str, Path, Dict]] = None,
        json_lines: Optional[bool] = None,
        flatten: bool = False,
        max_records: Optional[int] = None,
    ) -> JSONIngestionResult:
        """
        Parse JSON file with optional schema validation.

        Args:
            schema: JSON schema file path or dict for validation
            json_lines: True for JSON Lines format (auto-detected if None)
            flatten: Flatten nested structures
            max_records: Maximum records to load (for JSON Lines)

        Returns:
            JSONIngestionResult with metadata and validation results
        """
        start_time = time.time()
        warnings = []
        errors = []
        schema_validated = False
        schema_errors = []

        try:
            # Detect encoding
            encoding = self._detect_encoding()

            # Determine if JSON Lines format
            if json_lines is None:
                json_lines = self._is_json_lines()

            # Parse JSON
            if json_lines:
                # JSON Lines format (one JSON object per line)
                records = []
                with open(self.file_path, 'r', encoding=encoding) as f:
                    for i, line in enumerate(f):
                        if max_records and i >= max_records:
                            break

                        line = line.strip()
                        if not line:
                            continue

                        try:
                            record = json.loads(line)
                            records.append(record)
                        except json.JSONDecodeError as e:
                            errors.append(ValidationErrorModel(
                                field="json",
                                error_type="parse_error",
                                message=f"Line {i+1}: {str(e)}",
                                row=i+1,
                            ))

                self._data = records
                record_count = len(records)

            else:
                # Standard JSON format
                with open(self.file_path, 'r', encoding=encoding) as f:
                    data = json.load(f)

                self._data = data
                record_count = len(data) if isinstance(data, list) else 1

            # Calculate nested depth
            nested_depth = self._calculate_nested_depth(self._data)

            # Validate schema if provided
            if schema:
                schema_validated, schema_errors = self._validate_schema(
                    self._data,
                    schema
                )
                if not schema_validated:
                    errors.extend([
                        ValidationErrorModel(
                            field="schema",
                            error_type="schema_validation",
                            message=err,
                        )
                        for err in schema_errors
                    ])

            # Flatten if requested
            if flatten and isinstance(self._data, (dict, list)):
                try:
                    if isinstance(self._data, list):
                        self._dataframe = pd.json_normalize(self._data)
                    else:
                        self._dataframe = pd.json_normalize([self._data])
                except Exception as e:
                    warnings.append(f"Failed to flatten JSON: {str(e)}")

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

            # Create data preview
            if isinstance(self._data, list):
                preview = self._data[:5] if len(self._data) > 0 else None
            elif isinstance(self._data, dict):
                preview = {k: v for i, (k, v) in enumerate(self._data.items()) if i < 5}
            else:
                preview = None

            # Create result
            result = JSONIngestionResult(
                success=len(errors) == 0,
                record_count=record_count,
                schema_validated=schema_validated,
                schema_errors=schema_errors,
                nested_depth=nested_depth,
                metadata=metadata,
                warnings=warnings,
                errors=errors,
                data_preview=preview,
            )

            return result

        except json.JSONDecodeError as e:
            # JSON parse error
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
                field="json",
                error_type="parse_error",
                message=f"JSON decode error: {str(e)}",
            )

            return JSONIngestionResult(
                success=False,
                record_count=0,
                schema_validated=False,
                nested_depth=0,
                metadata=metadata,
                errors=[error],
            )

        except Exception as e:
            # General error
            duration_ms = (time.time() - start_time) * 1000
            file_size = os.path.getsize(self.file_path) if self.file_path.exists() else 0

            metadata = IngestionMetadata(
                file_path=str(self.file_path),
                file_size_bytes=file_size,
                file_hash="",
                original_filename=self.file_path.name,
                ingestion_duration_ms=duration_ms,
            )

            error = ValidationErrorModel(
                field="parse",
                error_type="general_error",
                message=str(e),
            )

            return JSONIngestionResult(
                success=False,
                record_count=0,
                schema_validated=False,
                nested_depth=0,
                metadata=metadata,
                errors=[error],
            )

    def get_data(self) -> Union[Dict, List]:
        """
        Get parsed JSON data.

        Returns:
            Parsed JSON data (dict or list)

        Raises:
            ValueError: If parse() has not been called
        """
        if self._data is None:
            raise ValueError("JSON not yet parsed. Call parse() first.")
        return self._data

    def get_dataframe(self) -> pd.DataFrame:
        """
        Get parsed data as DataFrame (for flattened JSON).

        Returns:
            Parsed DataFrame

        Raises:
            ValueError: If parse() has not been called or flatten was not enabled
        """
        if self._dataframe is None:
            if self._data is None:
                raise ValueError("JSON not yet parsed. Call parse() first.")
            else:
                raise ValueError("DataFrame not available. Call parse() with flatten=True.")
        return self._dataframe

    def to_csv(self, output_path: Union[str, Path], **kwargs) -> None:
        """
        Export flattened JSON to CSV.

        Args:
            output_path: Output CSV file path
            **kwargs: Additional arguments for DataFrame.to_csv()
        """
        df = self.get_dataframe()
        df.to_csv(output_path, **kwargs)

    def pretty_print(self, indent: int = 2, max_items: Optional[int] = None) -> str:
        """
        Pretty-print JSON data for debugging.

        Args:
            indent: Indentation spaces
            max_items: Maximum items to print (for lists)

        Returns:
            Formatted JSON string
        """
        data = self.get_data()

        if max_items and isinstance(data, list):
            data = data[:max_items]

        return json.dumps(data, indent=indent, default=str)
