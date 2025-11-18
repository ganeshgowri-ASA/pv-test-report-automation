"""
Custom exceptions for the document ingestion engine.
"""


class DocumentParsingError(Exception):
    """Base exception for all document parsing errors."""

    def __init__(self, message: str, file_path: str = None):
        self.file_path = file_path
        super().__init__(message)


class UnsupportedFormatError(DocumentParsingError):
    """Raised when document format is not supported."""

    def __init__(self, file_path: str, format_type: str = None):
        message = f"Unsupported document format"
        if format_type:
            message += f": {format_type}"
        super().__init__(message, file_path)


class CorruptedFileError(DocumentParsingError):
    """Raised when document file is corrupted or unreadable."""

    def __init__(self, file_path: str, reason: str = None):
        message = f"File is corrupted or unreadable"
        if reason:
            message += f": {reason}"
        super().__init__(message, file_path)


class OCRError(DocumentParsingError):
    """Raised when OCR processing fails."""

    def __init__(self, message: str, file_path: str = None, confidence: float = None):
        self.confidence = confidence
        super().__init__(message, file_path)


class TableExtractionError(DocumentParsingError):
    """Raised when table extraction fails."""

    def __init__(self, message: str, file_path: str = None, page_number: int = None):
        self.page_number = page_number
        super().__init__(message, file_path)


class ValidationError(DocumentParsingError):
    """Raised when extracted data fails validation."""

    def __init__(self, message: str, field_name: str = None):
        self.field_name = field_name
        super().__init__(message)


class PasswordProtectedError(DocumentParsingError):
    """Raised when PDF is password protected."""

    def __init__(self, file_path: str):
        super().__init__("PDF is password protected and cannot be read", file_path)
