"""CSV parser with auto-delimiter and encoding detection."""

import hashlib
import io
from pathlib import Path
from typing import Dict, Optional, Union

import chardet
import pandas as pd

from ..models.ingestion_models import CSVIngestionResult, DelimiterType, ISO17025Metadata


class CSVParser:
    """Parse CSV files with automatic delimiter and encoding detection."""

    # Common delimiters to try in order of likelihood
    COMMON_DELIMITERS = [",", ";", "\t", "|", " "]

    # Minimum confidence for encoding detection
    MIN_ENCODING_CONFIDENCE = 0.7

    def __init__(self, chunk_size: int = 10000):
        """Initialize CSV parser.

        Args:
            chunk_size: Chunk size for streaming large files
        """
        self.chunk_size = chunk_size

    def detect_encoding(self, file_path: Union[str, Path]) -> tuple[str, float]:
        """Detect file encoding using chardet.

        Args:
            file_path: Path to file

        Returns:
            Tuple of (encoding, confidence)
        """
        file_path = Path(file_path)

        # Read first 100KB for detection
        with open(file_path, "rb") as f:
            raw_data = f.read(100000)

        result = chardet.detect(raw_data)
        encoding = result["encoding"] or "utf-8"
        confidence = result["confidence"] or 0.0

        # Fallback to utf-8 if confidence too low
        if confidence < self.MIN_ENCODING_CONFIDENCE:
            encoding = "utf-8"

        # Normalize encoding names
        encoding = encoding.lower().replace("-", "_")
        if encoding == "ascii":
            encoding = "utf-8"  # ASCII is subset of UTF-8

        return encoding, confidence

    def detect_delimiter(
        self, file_path: Union[str, Path], encoding: str, sample_rows: int = 5
    ) -> str:
        """Detect CSV delimiter by analyzing first few rows.

        Args:
            file_path: Path to file
            encoding: File encoding
            sample_rows: Number of rows to sample

        Returns:
            Detected delimiter
        """
        file_path = Path(file_path)

        with open(file_path, "r", encoding=encoding, errors="replace") as f:
            # Read sample rows
            sample_lines = [f.readline() for _ in range(sample_rows)]

        # Count occurrences of each delimiter
        delimiter_counts: Dict[str, list[int]] = {d: [] for d in self.COMMON_DELIMITERS}

        for line in sample_lines:
            if not line.strip():
                continue
            for delim in self.COMMON_DELIMITERS:
                count = line.count(delim)
                delimiter_counts[delim].append(count)

        # Find delimiter with most consistent non-zero count
        best_delimiter = ","
        best_score = -1

        for delim, counts in delimiter_counts.items():
            if not counts or all(c == 0 for c in counts):
                continue

            # Score based on consistency and frequency
            avg_count = sum(counts) / len(counts)
            # Standard deviation
            variance = sum((c - avg_count) ** 2 for c in counts) / len(counts)
            std_dev = variance**0.5

            # Lower std dev and higher count is better
            score = avg_count / (std_dev + 1)

            if score > best_score:
                best_score = score
                best_delimiter = delim

        return best_delimiter

    def detect_header(
        self, file_path: Union[str, Path], encoding: str, delimiter: str
    ) -> bool:
        """Detect if CSV has header row.

        Args:
            file_path: Path to file
            encoding: File encoding
            delimiter: Delimiter to use

        Returns:
            True if header detected
        """
        try:
            # Try reading with and without header
            df_with_header = pd.read_csv(
                file_path, encoding=encoding, delimiter=delimiter, nrows=5
            )
            df_no_header = pd.read_csv(
                file_path, encoding=encoding, delimiter=delimiter, nrows=5, header=None
            )

            # If first row has different types than rest, likely header
            if len(df_no_header) > 1:
                first_row_types = df_no_header.iloc[0].apply(type)
                second_row_types = df_no_header.iloc[1].apply(type)

                # Count type differences
                type_diffs = sum(
                    t1 != t2 for t1, t2 in zip(first_row_types, second_row_types)
                )

                # If >50% different types, likely header
                if type_diffs / len(first_row_types) > 0.5:
                    return True

            return True  # Default to header present

        except Exception:
            return True

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
            # Read in chunks for large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def parse(
        self,
        file_path: Union[str, Path],
        encoding: Optional[str] = None,
        delimiter: Optional[str] = None,
        has_header: Optional[bool] = None,
        stream: bool = False,
        iso17025_metadata: Optional[ISO17025Metadata] = None,
        **pandas_kwargs,
    ) -> CSVIngestionResult:
        """Parse CSV file with auto-detection.

        Args:
            file_path: Path to CSV file
            encoding: Optional encoding (auto-detected if None)
            delimiter: Optional delimiter (auto-detected if None)
            has_header: Optional header flag (auto-detected if None)
            stream: Whether to use streaming for large files
            iso17025_metadata: Optional ISO 17025 metadata
            **pandas_kwargs: Additional arguments for pd.read_csv

        Returns:
            CSVIngestionResult with parsed data and metadata
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Auto-detect encoding
        if encoding is None:
            encoding, _ = self.detect_encoding(file_path)

        # Auto-detect delimiter
        if delimiter is None:
            delimiter = self.detect_delimiter(file_path, encoding)

        # Auto-detect header
        if has_header is None:
            has_header = self.detect_header(file_path, encoding, delimiter)

        # Calculate file hash
        file_hash = self.calculate_file_hash(file_path)

        # Parse CSV
        header_param = 0 if has_header else None

        if stream:
            # Stream large files in chunks
            chunks = []
            for chunk in pd.read_csv(
                file_path,
                encoding=encoding,
                delimiter=delimiter,
                header=header_param,
                chunksize=self.chunk_size,
                **pandas_kwargs,
            ):
                chunks.append(chunk)
            df = pd.concat(chunks, ignore_index=True)
        else:
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                delimiter=delimiter,
                header=header_param,
                **pandas_kwargs,
            )

        # Gather statistics
        row_count = len(df)
        column_count = len(df.columns)

        # Detect data types
        data_types = {col: str(dtype) for col, dtype in df.dtypes.items()}

        # Count missing values
        missing_values = {col: int(df[col].isna().sum()) for col in df.columns}

        return CSVIngestionResult(
            dataframe=df,
            row_count=row_count,
            column_count=column_count,
            delimiter_detected=delimiter,
            encoding_detected=encoding,
            file_hash=file_hash,
            has_header=has_header,
            data_types=data_types,
            missing_values=missing_values,
            iso17025_metadata=iso17025_metadata,
        )

    def parse_from_string(
        self,
        csv_string: str,
        delimiter: Optional[str] = None,
        has_header: bool = True,
        iso17025_metadata: Optional[ISO17025Metadata] = None,
        **pandas_kwargs,
    ) -> CSVIngestionResult:
        """Parse CSV from string.

        Args:
            csv_string: CSV data as string
            delimiter: Optional delimiter (auto-detected if None)
            has_header: Whether CSV has header row
            iso17025_metadata: Optional ISO 17025 metadata
            **pandas_kwargs: Additional arguments for pd.read_csv

        Returns:
            CSVIngestionResult with parsed data
        """
        # Auto-detect delimiter
        if delimiter is None:
            first_line = csv_string.split("\n")[0]
            delimiter_counts = {d: first_line.count(d) for d in self.COMMON_DELIMITERS}
            delimiter = max(delimiter_counts, key=delimiter_counts.get)  # type: ignore

        # Calculate hash
        file_hash = hashlib.sha256(csv_string.encode()).hexdigest()

        # Parse CSV
        header_param = 0 if has_header else None
        df = pd.read_csv(
            io.StringIO(csv_string),
            delimiter=delimiter,
            header=header_param,
            **pandas_kwargs,
        )

        # Gather statistics
        data_types = {col: str(dtype) for col, dtype in df.dtypes.items()}
        missing_values = {col: int(df[col].isna().sum()) for col in df.columns}

        return CSVIngestionResult(
            dataframe=df,
            row_count=len(df),
            column_count=len(df.columns),
            delimiter_detected=delimiter,
            encoding_detected="utf-8",
            file_hash=file_hash,
            has_header=has_header,
            data_types=data_types,
            missing_values=missing_values,
            iso17025_metadata=iso17025_metadata,
        )
