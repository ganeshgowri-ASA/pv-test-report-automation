"""
File validation utilities for PV test lab automation.

This module provides validators for uploaded files including size limits,
MIME type validation, image dimensions, CSV/Excel structure, and PDF metadata.
"""

import csv
import io
import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from .validation import ValidationResult, ValidationError


# ============================================================================
# Constants
# ============================================================================

# MIME type whitelist for security
ALLOWED_MIME_TYPES = {
    # Excel files
    "application/vnd.ms-excel",  # .xls
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/vnd.ms-excel.sheet.macroEnabled.12",  # .xlsm

    # Word files
    "application/msword",  # .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx

    # PDF files
    "application/pdf",

    # Image files
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/tiff",
    "image/bmp",

    # CSV files
    "text/csv",
    "application/csv",

    # Text files
    "text/plain",
}

# File extension to MIME type mapping
FILE_EXTENSIONS = {
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".xlsm": "application/vnd.ms-excel.sheet.macroEnabled.12",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc": "application/msword",
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
    ".bmp": "image/bmp",
    ".csv": "text/csv",
    ".txt": "text/plain",
}

# Maximum file sizes (in bytes)
MAX_FILE_SIZES = {
    "image": 10 * 1024 * 1024,      # 10 MB for images
    "document": 50 * 1024 * 1024,   # 50 MB for documents
    "excel": 25 * 1024 * 1024,      # 25 MB for Excel
    "pdf": 20 * 1024 * 1024,        # 20 MB for PDF
    "csv": 5 * 1024 * 1024,         # 5 MB for CSV
    "default": 10 * 1024 * 1024,    # 10 MB default
}


@dataclass
class FileInfo:
    """File information container."""
    path: str
    size_bytes: int
    mime_type: Optional[str]
    extension: str
    filename: str


# ============================================================================
# File Size Validators
# ============================================================================

def validate_file_size(
    file_path: str,
    max_size_bytes: Optional[int] = None,
    file_category: str = "default"
) -> ValidationResult:
    """
    Validate file size to prevent upload attacks.

    Args:
        file_path: Path to file
        max_size_bytes: Maximum allowed size (overrides category)
        file_category: File category (image, document, excel, pdf, csv, default)

    Returns:
        ValidationResult with file size info

    Example:
        >>> result = validate_file_size("test.xlsx", file_category="excel")
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value=None)

    # Check if file exists
    if not os.path.exists(file_path):
        result.add_error(f"File not found: {file_path}")
        return result

    try:
        # Get file size
        size_bytes = os.path.getsize(file_path)

        # Determine max size
        if max_size_bytes is None:
            max_size_bytes = MAX_FILE_SIZES.get(file_category, MAX_FILE_SIZES["default"])

        # Validate size
        if size_bytes > max_size_bytes:
            size_mb = size_bytes / (1024 * 1024)
            max_mb = max_size_bytes / (1024 * 1024)
            result.add_error(
                f"File size ({size_mb:.2f} MB) exceeds maximum allowed "
                f"({max_mb:.2f} MB) for {file_category} files"
            )
            return result

        if size_bytes == 0:
            result.add_error("File is empty (0 bytes)")
            return result

        result.value = size_bytes
        result.metadata["size_bytes"] = size_bytes
        result.metadata["size_mb"] = size_bytes / (1024 * 1024)
        result.metadata["max_bytes"] = max_size_bytes
        result.metadata["category"] = file_category

    except Exception as e:
        result.add_error(f"File size validation failed: {str(e)}")

    return result


# ============================================================================
# MIME Type Validators
# ============================================================================

def detect_mime_type(file_path: str) -> str:
    """
    Detect MIME type from file extension and content.

    Args:
        file_path: Path to file

    Returns:
        MIME type string

    Example:
        >>> mime = detect_mime_type("test.xlsx")
        >>> "spreadsheet" in mime
        True
    """
    # Try extension-based detection first
    ext = Path(file_path).suffix.lower()
    if ext in FILE_EXTENSIONS:
        return FILE_EXTENSIONS[ext]

    # Fallback to mimetypes library
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"


def validate_mime_type(
    file_path: str,
    allowed_types: Optional[Set[str]] = None,
    strict_mode: bool = True
) -> ValidationResult:
    """
    Validate file MIME type against whitelist.

    Args:
        file_path: Path to file
        allowed_types: Set of allowed MIME types (uses default if None)
        strict_mode: Reject files with unknown MIME types

    Returns:
        ValidationResult with MIME type info

    Example:
        >>> result = validate_mime_type("test.pdf")
        >>> assert result.is_valid
        >>> result.value
        'application/pdf'
    """
    result = ValidationResult(is_valid=True, value=None)

    if not os.path.exists(file_path):
        result.add_error(f"File not found: {file_path}")
        return result

    # Use default whitelist if none provided
    if allowed_types is None:
        allowed_types = ALLOWED_MIME_TYPES

    try:
        # Detect MIME type
        mime_type = detect_mime_type(file_path)

        # Validate against whitelist
        if mime_type not in allowed_types:
            if strict_mode:
                result.add_error(
                    f"MIME type '{mime_type}' is not allowed. "
                    f"File: {os.path.basename(file_path)}"
                )
            else:
                result.add_warning(
                    f"MIME type '{mime_type}' is not in whitelist"
                )

        result.value = mime_type
        result.metadata["mime_type"] = mime_type
        result.metadata["extension"] = Path(file_path).suffix.lower()
        result.metadata["strict_mode"] = strict_mode

    except Exception as e:
        result.add_error(f"MIME type validation failed: {str(e)}")

    return result


def validate_file_extension(
    file_path: str,
    allowed_extensions: List[str],
    case_sensitive: bool = False
) -> ValidationResult:
    """
    Validate file extension.

    Args:
        file_path: Path to file
        allowed_extensions: List of allowed extensions (e.g., ['.xlsx', '.xls'])
        case_sensitive: Case-sensitive comparison

    Returns:
        ValidationResult

    Example:
        >>> result = validate_file_extension("data.xlsx", [".xlsx", ".xls"])
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value=None)

    ext = Path(file_path).suffix
    if not case_sensitive:
        ext = ext.lower()
        allowed_extensions = [e.lower() for e in allowed_extensions]

    if ext not in allowed_extensions:
        result.add_error(
            f"File extension '{ext}' is not allowed. "
            f"Allowed: {', '.join(allowed_extensions)}"
        )
        return result

    result.value = ext
    result.metadata["extension"] = ext
    result.metadata["allowed"] = allowed_extensions

    return result


# ============================================================================
# Image Validators
# ============================================================================

def validate_image_dimensions(
    file_path: str,
    min_width: Optional[int] = None,
    min_height: Optional[int] = None,
    max_width: Optional[int] = None,
    max_height: Optional[int] = None,
    aspect_ratio: Optional[float] = None,
    aspect_tolerance: float = 0.1
) -> ValidationResult:
    """
    Validate image dimensions for EL/IV curve images.

    Args:
        file_path: Path to image file
        min_width: Minimum width in pixels
        min_height: Minimum height in pixels
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        aspect_ratio: Expected aspect ratio (width/height)
        aspect_tolerance: Tolerance for aspect ratio (±)

    Returns:
        ValidationResult with image dimensions

    Example:
        >>> # Note: Requires PIL/Pillow library
        >>> # result = validate_image_dimensions("test.jpg", min_width=800, min_height=600)
    """
    result = ValidationResult(is_valid=True, value=None)

    try:
        # Try to import PIL for image processing
        try:
            from PIL import Image
        except ImportError:
            result.add_warning(
                "PIL/Pillow not installed. Install with: pip install Pillow"
            )
            return result

        # Open and get dimensions
        with Image.open(file_path) as img:
            width, height = img.size

            # Minimum dimensions
            if min_width and width < min_width:
                result.add_error(f"Image width ({width}px) is less than minimum ({min_width}px)")

            if min_height and height < min_height:
                result.add_error(f"Image height ({height}px) is less than minimum ({min_height}px)")

            # Maximum dimensions
            if max_width and width > max_width:
                result.add_error(f"Image width ({width}px) exceeds maximum ({max_width}px)")

            if max_height and height > max_height:
                result.add_error(f"Image height ({height}px) exceeds maximum ({max_height}px)")

            # Aspect ratio
            if aspect_ratio:
                actual_ratio = width / height
                ratio_diff = abs(actual_ratio - aspect_ratio)

                if ratio_diff > aspect_tolerance:
                    result.add_warning(
                        f"Aspect ratio {actual_ratio:.2f} differs from expected "
                        f"{aspect_ratio:.2f} by {ratio_diff:.2f}"
                    )

            result.value = {"width": width, "height": height}
            result.metadata["dimensions"] = f"{width}x{height}"
            result.metadata["aspect_ratio"] = width / height
            result.metadata["format"] = img.format
            result.metadata["mode"] = img.mode

    except Exception as e:
        result.add_error(f"Image dimension validation failed: {str(e)}")

    return result


# ============================================================================
# CSV/Excel Structure Validators
# ============================================================================

def validate_csv_structure(
    file_path: str,
    required_columns: List[str],
    min_rows: int = 1,
    delimiter: str = ",",
    case_sensitive: bool = False
) -> ValidationResult:
    """
    Validate CSV file structure and required columns.

    Args:
        file_path: Path to CSV file
        required_columns: List of required column names
        min_rows: Minimum number of data rows (excluding header)
        delimiter: CSV delimiter (default ',')
        case_sensitive: Case-sensitive column name matching

    Returns:
        ValidationResult with CSV structure info

    Example:
        >>> # result = validate_csv_structure(
        >>> #     "data.csv",
        >>> #     required_columns=["Module_ID", "Power_W", "Voltage_V"]
        >>> # )
    """
    result = ValidationResult(is_valid=True, value=None)

    if not os.path.exists(file_path):
        result.add_error(f"File not found: {file_path}")
        return result

    try:
        with open(file_path, 'r', newline='', encoding='utf-8-sig') as csvfile:
            # Detect dialect
            sample = csvfile.read(1024)
            csvfile.seek(0)

            try:
                dialect = csv.Sniffer().sniff(sample)
            except csv.Error:
                dialect = csv.excel

            reader = csv.DictReader(csvfile, dialect=dialect, delimiter=delimiter)

            # Get headers
            headers = reader.fieldnames
            if not headers:
                result.add_error("CSV file has no headers")
                return result

            # Normalize for comparison
            if not case_sensitive:
                headers_normalized = [h.lower().strip() for h in headers]
                required_normalized = [r.lower().strip() for r in required_columns]
            else:
                headers_normalized = [h.strip() for h in headers]
                required_normalized = [r.strip() for r in required_columns]

            # Check required columns
            missing_columns = []
            for req_col in required_normalized:
                if req_col not in headers_normalized:
                    # Find original name for error message
                    original_name = required_columns[required_normalized.index(req_col)]
                    missing_columns.append(original_name)

            if missing_columns:
                result.add_error(
                    f"Missing required columns: {', '.join(missing_columns)}. "
                    f"Found: {', '.join(headers)}"
                )
                return result

            # Count rows
            row_count = sum(1 for _ in reader)

            if row_count < min_rows:
                result.add_error(
                    f"CSV has {row_count} data rows, minimum required: {min_rows}"
                )
                return result

            result.value = {
                "headers": headers,
                "row_count": row_count,
                "column_count": len(headers)
            }
            result.metadata["file_path"] = file_path
            result.metadata["delimiter"] = delimiter

    except Exception as e:
        result.add_error(f"CSV structure validation failed: {str(e)}")

    return result


def validate_excel_structure(
    file_path: str,
    required_columns: List[str],
    sheet_name: Union[str, int] = 0,
    min_rows: int = 1,
    case_sensitive: bool = False
) -> ValidationResult:
    """
    Validate Excel file structure and required columns.

    Args:
        file_path: Path to Excel file
        required_columns: List of required column names
        sheet_name: Sheet name or index (default 0 for first sheet)
        min_rows: Minimum number of data rows (excluding header)
        case_sensitive: Case-sensitive column name matching

    Returns:
        ValidationResult with Excel structure info

    Example:
        >>> # Note: Requires openpyxl or pandas library
        >>> # result = validate_excel_structure(
        >>> #     "data.xlsx",
        >>> #     required_columns=["Module_ID", "Power_W"]
        >>> # )
    """
    result = ValidationResult(is_valid=True, value=None)

    if not os.path.exists(file_path):
        result.add_error(f"File not found: {file_path}")
        return result

    try:
        # Try openpyxl first
        try:
            import openpyxl
            wb = openpyxl.load_workbook(file_path, read_only=True)

            # Get sheet
            if isinstance(sheet_name, int):
                sheet = wb.worksheets[sheet_name]
            else:
                sheet = wb[sheet_name]

            # Get headers (first row)
            headers = [cell.value for cell in sheet[1]]
            headers = [str(h).strip() if h is not None else "" for h in headers]

            # Count rows (excluding header)
            row_count = sheet.max_row - 1

        except ImportError:
            # Fallback to pandas
            try:
                import pandas as pd
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                headers = df.columns.tolist()
                row_count = len(df)

            except ImportError:
                result.add_warning(
                    "Neither openpyxl nor pandas installed. "
                    "Install with: pip install openpyxl"
                )
                return result

        # Normalize for comparison
        if not case_sensitive:
            headers_normalized = [h.lower().strip() for h in headers]
            required_normalized = [r.lower().strip() for r in required_columns]
        else:
            headers_normalized = [h.strip() for h in headers]
            required_normalized = [r.strip() for r in required_columns]

        # Check required columns
        missing_columns = []
        for req_col in required_normalized:
            if req_col not in headers_normalized:
                original_name = required_columns[required_normalized.index(req_col)]
                missing_columns.append(original_name)

        if missing_columns:
            result.add_error(
                f"Missing required columns: {', '.join(missing_columns)}. "
                f"Found: {', '.join(headers)}"
            )
            return result

        # Check minimum rows
        if row_count < min_rows:
            result.add_error(
                f"Excel has {row_count} data rows, minimum required: {min_rows}"
            )
            return result

        result.value = {
            "headers": headers,
            "row_count": row_count,
            "column_count": len(headers)
        }
        result.metadata["file_path"] = file_path
        result.metadata["sheet_name"] = sheet_name

    except Exception as e:
        result.add_error(f"Excel structure validation failed: {str(e)}")

    return result


# ============================================================================
# PDF Validators
# ============================================================================

def validate_pdf_metadata(
    file_path: str,
    required_metadata: Optional[List[str]] = None,
    max_pages: Optional[int] = None
) -> ValidationResult:
    """
    Extract and validate PDF metadata.

    Args:
        file_path: Path to PDF file
        required_metadata: List of required metadata fields (e.g., ['Title', 'Author'])
        max_pages: Maximum allowed number of pages

    Returns:
        ValidationResult with PDF metadata

    Example:
        >>> # Note: Requires PyPDF2 or pypdf library
        >>> # result = validate_pdf_metadata("report.pdf", max_pages=50)
    """
    result = ValidationResult(is_valid=True, value={})

    if not os.path.exists(file_path):
        result.add_error(f"File not found: {file_path}")
        return result

    try:
        # Try PyPDF2 or pypdf
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            try:
                from pypdf import PdfReader
            except ImportError:
                result.add_warning(
                    "PyPDF2 or pypdf not installed. "
                    "Install with: pip install PyPDF2"
                )
                return result

        # Read PDF
        reader = PdfReader(file_path)

        # Get metadata
        metadata = reader.metadata
        num_pages = len(reader.pages)

        # Check page count
        if max_pages and num_pages > max_pages:
            result.add_error(
                f"PDF has {num_pages} pages, maximum allowed: {max_pages}"
            )

        # Check required metadata
        if required_metadata:
            missing_metadata = []
            for field in required_metadata:
                if not metadata or not getattr(metadata, field, None):
                    missing_metadata.append(field)

            if missing_metadata:
                result.add_warning(
                    f"Missing PDF metadata fields: {', '.join(missing_metadata)}"
                )

        # Extract metadata
        pdf_info = {
            "num_pages": num_pages,
            "title": getattr(metadata, 'title', None) if metadata else None,
            "author": getattr(metadata, 'author', None) if metadata else None,
            "subject": getattr(metadata, 'subject', None) if metadata else None,
            "creator": getattr(metadata, 'creator', None) if metadata else None,
        }

        result.value = pdf_info
        result.metadata.update(pdf_info)

    except Exception as e:
        result.add_error(f"PDF metadata validation failed: {str(e)}")

    return result


# ============================================================================
# Complete File Validator
# ============================================================================

def validate_file(
    file_path: str,
    max_size_mb: Optional[float] = None,
    allowed_extensions: Optional[List[str]] = None,
    validate_mime: bool = True
) -> ValidationResult:
    """
    Complete file validation (size, extension, MIME type).

    Args:
        file_path: Path to file
        max_size_mb: Maximum size in MB
        allowed_extensions: List of allowed extensions
        validate_mime: Validate MIME type

    Returns:
        ValidationResult with complete file info

    Example:
        >>> result = validate_file("test.xlsx", max_size_mb=10, allowed_extensions=[".xlsx"])
        >>> assert result.is_valid
    """
    result = ValidationResult(is_valid=True, value=None)

    if not os.path.exists(file_path):
        result.add_error(f"File not found: {file_path}")
        return result

    # File size check
    if max_size_mb:
        size_result = validate_file_size(
            file_path,
            max_size_bytes=int(max_size_mb * 1024 * 1024)
        )
        if not size_result.is_valid:
            result.is_valid = False
            result.errors.extend(size_result.errors)

    # Extension check
    if allowed_extensions:
        ext_result = validate_file_extension(file_path, allowed_extensions)
        if not ext_result.is_valid:
            result.is_valid = False
            result.errors.extend(ext_result.errors)

    # MIME type check
    if validate_mime:
        mime_result = validate_mime_type(file_path)
        if not mime_result.is_valid:
            result.is_valid = False
            result.errors.extend(mime_result.errors)
        else:
            result.metadata["mime_type"] = mime_result.value

    # Create file info
    file_info = FileInfo(
        path=file_path,
        size_bytes=os.path.getsize(file_path),
        mime_type=result.metadata.get("mime_type"),
        extension=Path(file_path).suffix.lower(),
        filename=os.path.basename(file_path)
    )

    result.value = file_info
    result.metadata["file_info"] = file_info

    return result
