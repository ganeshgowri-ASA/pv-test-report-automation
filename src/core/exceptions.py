"""
Custom exceptions for PV test report automation.

Defines specific exception types for different error scenarios.
"""


class PVTestAutomationError(Exception):
    """Base exception for all PV test automation errors."""
    pass


class IngestionError(PVTestAutomationError):
    """Raised when data ingestion fails."""
    pass


class VisioIngestionError(IngestionError):
    """Raised when Visio diagram ingestion fails."""
    pass


class GanttIngestionError(IngestionError):
    """Raised when Gantt/MS Project ingestion fails."""
    pass


class SmartsheetIngestionError(IngestionError):
    """Raised when Smartsheet ingestion fails."""
    pass


class FileProcessingError(PVTestAutomationError):
    """Raised when file processing fails."""
    pass


class FileSizeExceededError(FileProcessingError):
    """Raised when file size exceeds maximum allowed."""
    pass


class UnsupportedFileFormatError(FileProcessingError):
    """Raised when file format is not supported."""
    pass


class ValidationError(PVTestAutomationError):
    """Raised when data validation fails."""
    pass


class ConfigurationError(PVTestAutomationError):
    """Raised when configuration is invalid or missing."""
    pass


class APIError(PVTestAutomationError):
    """Raised when external API calls fail."""
    pass


class SmartsheetAPIError(APIError):
    """Raised when Smartsheet API calls fail."""
    pass
