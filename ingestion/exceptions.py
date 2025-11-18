"""
Custom exceptions for data ingestion engine.
"""


class IngestionError(Exception):
    """Base exception for ingestion errors."""
    pass


class ValidationError(IngestionError):
    """Raised when data validation fails."""
    pass


class SchemaError(IngestionError):
    """Raised when schema validation fails."""
    pass


class ParseError(IngestionError):
    """Raised when parsing fails."""
    pass


class EncodingError(IngestionError):
    """Raised when encoding detection or conversion fails."""
    pass


class DelimiterError(IngestionError):
    """Raised when delimiter detection fails."""
    pass


class TimeSeriesError(IngestionError):
    """Raised when time-series parsing fails."""
    pass


class TransformationError(IngestionError):
    """Raised when data transformation fails."""
    pass
