"""
Validation functions for document ingestion results and extracted data.
"""

import hashlib
import os
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Tuple

from ingestion.exceptions import CorruptedFileError, ValidationError
from ingestion.models import (
    CalibrationCertificate,
    DocumentIngestionResult,
    TableData,
)


def validate_file_exists(file_path: str) -> bool:
    """
    Validate that file exists and is readable.

    Args:
        file_path: Path to file

    Returns:
        True if file exists and is readable

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file is not readable
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not os.access(path, os.R_OK):
        raise PermissionError(f"File is not readable: {file_path}")

    return True


def validate_file_size(file_path: str, max_size_mb: int = 100) -> bool:
    """
    Validate file size is within acceptable limits.

    Args:
        file_path: Path to file
        max_size_mb: Maximum file size in megabytes

    Returns:
        True if file size is acceptable

    Raises:
        ValidationError: If file is too large
    """
    path = Path(file_path)
    size_bytes = path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)

    if size_mb > max_size_mb:
        raise ValidationError(
            f"File too large: {size_mb:.2f}MB (max: {max_size_mb}MB)", "file_size"
        )

    return True


def validate_file_hash(file_path: str, expected_hash: str) -> bool:
    """
    Validate file integrity using SHA-256 hash.

    Args:
        file_path: Path to file
        expected_hash: Expected SHA-256 hash

    Returns:
        True if hash matches

    Raises:
        ValidationError: If hash doesn't match
    """
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    actual_hash = sha256_hash.hexdigest()

    if actual_hash != expected_hash:
        raise ValidationError(
            f"File hash mismatch. Expected: {expected_hash}, Got: {actual_hash}", "file_hash"
        )

    return True


def validate_ingestion_result(result: DocumentIngestionResult) -> Tuple[bool, List[str]]:
    """
    Validate document ingestion result for completeness and quality.

    Args:
        result: DocumentIngestionResult to validate

    Returns:
        Tuple of (is_valid, list of validation warnings)
    """
    warnings = []
    is_valid = True

    # Check text content
    if not result.text_content or len(result.text_content.strip()) < 10:
        warnings.append("Very little text content extracted")
        is_valid = False

    # Check OCR confidence
    if result.extraction_method.value == "ocr":
        if result.ocr_confidence < 0.5:
            warnings.append(f"Very low OCR confidence: {result.ocr_confidence:.2%}")
            is_valid = False
        elif result.ocr_confidence < 0.7:
            warnings.append(f"Low OCR confidence: {result.ocr_confidence:.2%}")

    # Check for errors
    if result.errors:
        warnings.append(f"Extraction errors occurred: {len(result.errors)} errors")
        is_valid = False

    # Check metadata
    if result.metadata.page_count == 0:
        warnings.append("No pages detected in document")

    # Check file hash
    if not result.file_hash:
        warnings.append("File hash not calculated")

    return is_valid, warnings


def validate_table_data(table: TableData) -> Tuple[bool, List[str]]:
    """
    Validate extracted table data.

    Args:
        table: TableData to validate

    Returns:
        Tuple of (is_valid, list of warnings)
    """
    warnings = []
    is_valid = True

    # Check if table has data
    if not table.data or len(table.data) == 0:
        warnings.append("Table has no data rows")
        is_valid = False
        return is_valid, warnings

    # Check column consistency
    if table.headers:
        header_count = len(table.headers)
        for idx, row in enumerate(table.data):
            if len(row) != header_count:
                warnings.append(
                    f"Row {idx} has {len(row)} columns, expected {header_count}"
                )

    # Check for empty cells
    total_cells = sum(len(row) for row in table.data)
    empty_cells = sum(1 for row in table.data for cell in row if not str(cell).strip())

    if empty_cells > 0:
        empty_percent = (empty_cells / total_cells) * 100
        if empty_percent > 50:
            warnings.append(f"Table has {empty_percent:.1f}% empty cells")

    # Check OCR confidence for OCR-extracted tables
    if table.confidence < 0.7:
        warnings.append(f"Low table extraction confidence: {table.confidence:.2%}")

    return is_valid, warnings


def validate_calibration_certificate(cert: CalibrationCertificate) -> Tuple[bool, List[str]]:
    """
    Validate calibration certificate data.

    Args:
        cert: CalibrationCertificate to validate

    Returns:
        Tuple of (is_valid, list of validation warnings)
    """
    warnings = []
    is_valid = True

    # Check required fields
    if not cert.certificate_number:
        warnings.append("Missing certificate number")
        is_valid = False

    if not cert.equipment_name:
        warnings.append("Missing equipment name")
        is_valid = False

    if not cert.laboratory_name:
        warnings.append("Missing laboratory name")
        is_valid = False

    # Check dates
    if not cert.calibration_date:
        warnings.append("Missing calibration date")
        is_valid = False
    else:
        # Check if calibration date is in the future
        if cert.calibration_date > date.today():
            warnings.append("Calibration date is in the future")
            is_valid = False

        # Check if calibration is overdue
        if cert.due_date:
            if cert.due_date < date.today():
                days_overdue = (date.today() - cert.due_date).days
                warnings.append(f"Calibration is overdue by {days_overdue} days")
                is_valid = False
            elif cert.due_date - date.today() < datetime.timedelta(days=30):
                days_remaining = (cert.due_date - date.today()).days
                warnings.append(f"Calibration due soon: {days_remaining} days remaining")

    # Check accreditation
    if cert.accreditation_body.value == "UNKNOWN":
        warnings.append("Accreditation body not identified")

    # Check traceability
    if not cert.traceability:
        warnings.append("No traceability information found")

    # Check calibration points
    if not cert.calibration_points or len(cert.calibration_points) == 0:
        warnings.append("No calibration points extracted")

    # Check uncertainty
    if not cert.uncertainty:
        warnings.append("Measurement uncertainty not found")

    # Check personnel
    if not cert.calibrated_by and not cert.approved_by:
        warnings.append("No personnel information found")

    return is_valid, warnings


def validate_date_range(
    start_date: date, end_date: date, max_days: int = 365
) -> Tuple[bool, Optional[str]]:
    """
    Validate date range is reasonable.

    Args:
        start_date: Start date
        end_date: End date
        max_days: Maximum allowed days between dates

    Returns:
        Tuple of (is_valid, warning message)
    """
    if end_date < start_date:
        return False, "End date is before start date"

    days_diff = (end_date - start_date).days

    if days_diff > max_days:
        return False, f"Date range too large: {days_diff} days (max: {max_days})"

    return True, None


def validate_numeric_value(
    value: float, min_value: Optional[float] = None, max_value: Optional[float] = None
) -> Tuple[bool, Optional[str]]:
    """
    Validate numeric value is within expected range.

    Args:
        value: Value to validate
        min_value: Minimum acceptable value
        max_value: Maximum acceptable value

    Returns:
        Tuple of (is_valid, warning message)
    """
    if min_value is not None and value < min_value:
        return False, f"Value {value} is below minimum {min_value}"

    if max_value is not None and value > max_value:
        return False, f"Value {value} is above maximum {max_value}"

    return True, None


def detect_corrupted_pdf(file_path: str) -> bool:
    """
    Attempt to detect if PDF is corrupted.

    Args:
        file_path: Path to PDF file

    Returns:
        True if PDF appears corrupted

    Raises:
        CorruptedFileError: If PDF is corrupted
    """
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(str(file_path))

        # Try to access first page
        if len(reader.pages) > 0:
            _ = reader.pages[0].extract_text()

        return False

    except Exception as e:
        raise CorruptedFileError(str(file_path), str(e))


def sanitize_extracted_text(text: str) -> str:
    """
    Clean and sanitize extracted text.

    Args:
        text: Raw extracted text

    Returns:
        Cleaned text
    """
    # Remove null bytes
    text = text.replace("\x00", "")

    # Remove excessive whitespace
    import re

    text = re.sub(r"\s+", " ", text)

    # Remove control characters except newlines and tabs
    text = "".join(char for char in text if char.isprintable() or char in "\n\t")

    return text.strip()


def normalize_unit(unit: str) -> str:
    """
    Normalize measurement unit representations.

    Args:
        unit: Raw unit string

    Returns:
        Normalized unit string
    """
    unit_mappings = {
        "deg c": "°C",
        "degrees c": "°C",
        "celsius": "°C",
        "percent": "%",
        "pct": "%",
        "volts": "V",
        "volt": "V",
        "amps": "A",
        "ampere": "A",
        "watts": "W",
        "watt": "W",
        "ohm": "Ω",
        "ohms": "Ω",
    }

    unit_lower = unit.lower().strip()

    return unit_mappings.get(unit_lower, unit)


def validate_equipment_id(equipment_id: str) -> bool:
    """
    Validate equipment ID format.

    Args:
        equipment_id: Equipment ID string

    Returns:
        True if valid format
    """
    # Basic validation - alphanumeric with common separators
    import re

    pattern = r"^[A-Z0-9\-_/]+$"
    return bool(re.match(pattern, equipment_id.upper()))


def check_data_completeness(
    extracted_data: dict, required_fields: List[str]
) -> Tuple[bool, List[str]]:
    """
    Check if all required fields are present in extracted data.

    Args:
        extracted_data: Dictionary of extracted data
        required_fields: List of required field names

    Returns:
        Tuple of (is_complete, list of missing fields)
    """
    missing_fields = []

    for field in required_fields:
        if field not in extracted_data or not extracted_data[field]:
            missing_fields.append(field)

    is_complete = len(missing_fields) == 0

    return is_complete, missing_fields
