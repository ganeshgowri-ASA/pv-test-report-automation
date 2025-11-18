"""
Validation utilities for PV test report automation.

Provides common validation functions for data integrity.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.exceptions import ValidationError


def validate_file_exists(file_path: str) -> Path:
    """
    Validate that a file exists.

    Args:
        file_path: Path to file

    Returns:
        Path object

    Raises:
        ValidationError: If file does not exist
    """
    path = Path(file_path)
    if not path.exists():
        raise ValidationError(f"File does not exist: {file_path}")
    if not path.is_file():
        raise ValidationError(f"Path is not a file: {file_path}")
    return path


def validate_directory_exists(dir_path: str, create: bool = False) -> Path:
    """
    Validate that a directory exists.

    Args:
        dir_path: Path to directory
        create: If True, create directory if it doesn't exist

    Returns:
        Path object

    Raises:
        ValidationError: If directory does not exist and create=False
    """
    path = Path(dir_path)

    if not path.exists():
        if create:
            path.mkdir(parents=True, exist_ok=True)
        else:
            raise ValidationError(f"Directory does not exist: {dir_path}")
    elif not path.is_dir():
        raise ValidationError(f"Path is not a directory: {dir_path}")

    return path


def validate_date_range(
    start_date: datetime,
    end_date: datetime,
    allow_equal: bool = True
) -> bool:
    """
    Validate that start_date is before or equal to end_date.

    Args:
        start_date: Start date
        end_date: End date
        allow_equal: If True, start_date == end_date is valid

    Returns:
        True if valid

    Raises:
        ValidationError: If date range is invalid
    """
    if allow_equal:
        if start_date > end_date:
            raise ValidationError(
                f"Start date ({start_date}) must be before or equal to end date ({end_date})"
            )
    else:
        if start_date >= end_date:
            raise ValidationError(
                f"Start date ({start_date}) must be before end date ({end_date})"
            )

    return True


def validate_percentage(value: float, field_name: str = "value") -> bool:
    """
    Validate that a value is a valid percentage (0-100).

    Args:
        value: Value to validate
        field_name: Name of field for error message

    Returns:
        True if valid

    Raises:
        ValidationError: If value is not between 0 and 100
    """
    if not 0 <= value <= 100:
        raise ValidationError(
            f"{field_name} must be between 0 and 100, got {value}"
        )
    return True


def validate_non_empty_string(value: str, field_name: str = "value") -> bool:
    """
    Validate that a string is not empty or whitespace only.

    Args:
        value: String to validate
        field_name: Name of field for error message

    Returns:
        True if valid

    Raises:
        ValidationError: If string is empty or whitespace
    """
    if not value or not value.strip():
        raise ValidationError(f"{field_name} cannot be empty")
    return True


def validate_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If email format is invalid
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError(f"Invalid email address: {email}")
    return True


def validate_url(url: str) -> bool:
    """
    Validate URL format.

    Args:
        url: URL to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If URL format is invalid
    """
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if not re.match(pattern, url, re.IGNORECASE):
        raise ValidationError(f"Invalid URL: {url}")
    return True


def validate_required_fields(
    data: Dict[str, Any],
    required_fields: List[str]
) -> bool:
    """
    Validate that all required fields are present in data.

    Args:
        data: Dictionary to validate
        required_fields: List of required field names

    Returns:
        True if all required fields present

    Raises:
        ValidationError: If any required field is missing
    """
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing_fields)}"
        )

    return True


def validate_api_key(api_key: str, min_length: int = 20) -> bool:
    """
    Validate API key format.

    Args:
        api_key: API key to validate
        min_length: Minimum length for API key

    Returns:
        True if valid

    Raises:
        ValidationError: If API key is invalid
    """
    if not api_key or len(api_key) < min_length:
        raise ValidationError(
            f"API key must be at least {min_length} characters"
        )

    # Check for common placeholder values
    placeholders = ['your_api_key', 'api_key_here', 'xxx', 'placeholder']
    if api_key.lower() in placeholders:
        raise ValidationError(
            "API key appears to be a placeholder value"
        )

    return True


def validate_positive_number(value: float, field_name: str = "value") -> bool:
    """
    Validate that a number is positive (> 0).

    Args:
        value: Number to validate
        field_name: Name of field for error message

    Returns:
        True if valid

    Raises:
        ValidationError: If number is not positive
    """
    if value <= 0:
        raise ValidationError(f"{field_name} must be positive, got {value}")
    return True


def validate_non_negative_number(value: float, field_name: str = "value") -> bool:
    """
    Validate that a number is non-negative (>= 0).

    Args:
        value: Number to validate
        field_name: Name of field for error message

    Returns:
        True if valid

    Raises:
        ValidationError: If number is negative
    """
    if value < 0:
        raise ValidationError(f"{field_name} must be non-negative, got {value}")
    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing/replacing invalid characters.

    Args:
        filename: Filename to sanitize

    Returns:
        Sanitized filename
    """
    # Remove or replace characters that are invalid in filenames
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)

    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip('. ')

    # Ensure filename is not empty
    if not sanitized:
        sanitized = "unnamed_file"

    return sanitized
