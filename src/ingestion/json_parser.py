"""JSON/JSONL parser with streaming support and schema validation."""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

import chardet
import pandas as pd
from jsonschema import ValidationError, validate

from ..models.ingestion_models import JSONIngestionResult, ISO17025Metadata


class JSONParser:
    """Parse JSON and JSON Lines files with streaming support."""

    def __init__(self, validate_schema: bool = True):
        """Initialize JSON parser.

        Args:
            validate_schema: Whether to validate against JSON schema
        """
        self.validate_schema = validate_schema

    def detect_encoding(self, file_path: Union[str, Path]) -> str:
        """Detect file encoding.

        Args:
            file_path: Path to file

        Returns:
            Detected encoding
        """
        file_path = Path(file_path)

        with open(file_path, "rb") as f:
            raw_data = f.read(100000)

        result = chardet.detect(raw_data)
        encoding = result["encoding"] or "utf-8"

        # Normalize encoding
        encoding = encoding.lower().replace("-", "_")
        if encoding == "ascii":
            encoding = "utf-8"

        return encoding

    def is_jsonl(self, file_path: Union[str, Path], encoding: str) -> bool:
        """Detect if file is JSON Lines format.

        Args:
            file_path: Path to file
            encoding: File encoding

        Returns:
            True if JSONL format
        """
        file_path = Path(file_path)

        try:
            with open(file_path, "r", encoding=encoding) as f:
                first_line = f.readline().strip()
                second_line = f.readline().strip()

                # Try parsing first two lines as separate JSON objects
                if first_line and second_line:
                    json.loads(first_line)
                    json.loads(second_line)
                    return True

        except (json.JSONDecodeError, StopIteration):
            pass

        return False

    def calculate_file_hash(self, file_path: Union[str, Path]) -> str:
        """Calculate SHA-256 hash of file.

        Args:
            file_path: Path to file

        Returns:
            Hex digest of file hash
        """
        sha256_hash = hashlib.sha256()
        file_path = Path(file_path)

        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def stream_jsonl(
        self, file_path: Union[str, Path], encoding: str
    ) -> Iterator[Dict[str, Any]]:
        """Stream JSONL file line by line.

        Args:
            file_path: Path to JSONL file
            encoding: File encoding

        Yields:
            Parsed JSON objects
        """
        file_path = Path(file_path)

        with open(file_path, "r", encoding=encoding) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError as e:
                        # Skip malformed lines but could log warning
                        continue

    def validate_against_schema(
        self, data: Union[Dict, List[Dict]], schema: Dict[str, Any]
    ) -> tuple[bool, Optional[List[str]]]:
        """Validate JSON data against schema.

        Args:
            data: JSON data to validate
            schema: JSON schema

        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []

        try:
            if isinstance(data, list):
                for i, item in enumerate(data):
                    try:
                        validate(instance=item, schema=schema)
                    except ValidationError as e:
                        errors.append(f"Record {i}: {e.message}")
            else:
                validate(instance=data, schema=schema)

        except ValidationError as e:
            errors.append(e.message)

        is_valid = len(errors) == 0
        return is_valid, errors if errors else None

    def parse(
        self,
        file_path: Union[str, Path],
        encoding: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        to_dataframe: bool = False,
        iso17025_metadata: Optional[ISO17025Metadata] = None,
    ) -> JSONIngestionResult:
        """Parse JSON or JSONL file.

        Args:
            file_path: Path to JSON file
            encoding: Optional encoding (auto-detected if None)
            schema: Optional JSON schema for validation
            stream: Whether to use streaming for JSONL
            to_dataframe: Convert to DataFrame if data is tabular
            iso17025_metadata: Optional ISO 17025 metadata

        Returns:
            JSONIngestionResult with parsed data
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Auto-detect encoding
        if encoding is None:
            encoding = self.detect_encoding(file_path)

        # Check if JSONL format
        is_jsonl_format = self.is_jsonl(file_path, encoding)

        # Calculate file hash
        file_hash = self.calculate_file_hash(file_path)

        # Parse data
        if is_jsonl_format and stream:
            # Stream JSONL
            data = list(self.stream_jsonl(file_path, encoding))
        elif is_jsonl_format:
            # Load all JSONL
            data = []
            with open(file_path, "r", encoding=encoding) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        else:
            # Standard JSON
            with open(file_path, "r", encoding=encoding) as f:
                data = json.load(f)

        # Validate schema
        schema_valid = True
        validation_errors = None

        if schema and self.validate_schema:
            schema_valid, validation_errors = self.validate_against_schema(data, schema)

        # Convert to DataFrame if requested and data is list of dicts
        dataframe = None
        if to_dataframe and isinstance(data, list) and all(isinstance(item, dict) for item in data):
            dataframe = pd.DataFrame(data)

        # Count records
        if isinstance(data, list):
            record_count = len(data)
        elif isinstance(data, dict):
            record_count = 1
        else:
            record_count = 0

        return JSONIngestionResult(
            data=data,
            dataframe=dataframe,
            record_count=record_count,
            file_hash=file_hash,
            encoding_detected=encoding,
            is_jsonl=is_jsonl_format,
            schema_valid=schema_valid,
            validation_errors=validation_errors,
            iso17025_metadata=iso17025_metadata,
        )

    def parse_from_string(
        self,
        json_string: str,
        schema: Optional[Dict[str, Any]] = None,
        to_dataframe: bool = False,
        iso17025_metadata: Optional[ISO17025Metadata] = None,
    ) -> JSONIngestionResult:
        """Parse JSON from string.

        Args:
            json_string: JSON data as string
            schema: Optional JSON schema for validation
            to_dataframe: Convert to DataFrame if tabular
            iso17025_metadata: Optional ISO 17025 metadata

        Returns:
            JSONIngestionResult with parsed data
        """
        # Calculate hash
        file_hash = hashlib.sha256(json_string.encode()).hexdigest()

        # Parse JSON
        data = json.loads(json_string)

        # Validate schema
        schema_valid = True
        validation_errors = None

        if schema and self.validate_schema:
            schema_valid, validation_errors = self.validate_against_schema(data, schema)

        # Convert to DataFrame
        dataframe = None
        if to_dataframe and isinstance(data, list) and all(isinstance(item, dict) for item in data):
            dataframe = pd.DataFrame(data)

        # Count records
        if isinstance(data, list):
            record_count = len(data)
        elif isinstance(data, dict):
            record_count = 1
        else:
            record_count = 0

        return JSONIngestionResult(
            data=data,
            dataframe=dataframe,
            record_count=record_count,
            file_hash=file_hash,
            encoding_detected="utf-8",
            is_jsonl=False,
            schema_valid=schema_valid,
            validation_errors=validation_errors,
            iso17025_metadata=iso17025_metadata,
        )

    def stream_parse(
        self,
        file_path: Union[str, Path],
        encoding: Optional[str] = None,
        batch_size: int = 1000,
    ) -> Iterator[List[Dict[str, Any]]]:
        """Stream parse JSONL file in batches.

        Args:
            file_path: Path to JSONL file
            encoding: Optional encoding
            batch_size: Number of records per batch

        Yields:
            Batches of parsed records
        """
        file_path = Path(file_path)

        if encoding is None:
            encoding = self.detect_encoding(file_path)

        batch = []
        for record in self.stream_jsonl(file_path, encoding):
            batch.append(record)
            if len(batch) >= batch_size:
                yield batch
                batch = []

        # Yield remaining records
        if batch:
            yield batch
