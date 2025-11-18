"""
Custom exception classes for PV Test Report Automation.

Provides a hierarchy of exceptions for different error scenarios
with structured error information.
"""

from typing import Any, Dict, Optional


class PVReportException(Exception):
    """Base exception for PV reporting system."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details
        """
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class ConfigurationException(PVReportException):
    """Configuration or settings related errors."""

    pass


class ValidationException(PVReportException):
    """Data validation errors."""

    pass


class APIException(PVReportException):
    """API call failures."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize API exception.

        Args:
            message: Error message
            status_code: HTTP status code
            error_code: Error code
            details: Additional details
        """
        super().__init__(message, error_code, details)
        self.status_code = status_code


class ClaudeAPIException(APIException):
    """Claude API specific errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        tokens_used: Optional[Dict[str, int]] = None,
        request_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Claude API exception.

        Args:
            message: Error message
            status_code: HTTP status code
            error_code: Error code from Claude API
            tokens_used: Token usage before error
            request_id: Claude API request ID
            details: Additional details
        """
        details = details or {}
        if tokens_used:
            details["tokens_used"] = tokens_used
        if request_id:
            details["request_id"] = request_id

        super().__init__(message, status_code, error_code, details)
        self.tokens_used = tokens_used
        self.request_id = request_id


class RateLimitException(ClaudeAPIException):
    """Rate limiting errors."""

    def __init__(
        self,
        message: str = "API rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs: Any,
    ):
        """
        Initialize rate limit exception.

        Args:
            message: Error message
            retry_after: Seconds until retry is allowed
            **kwargs: Additional arguments for ClaudeAPIException
        """
        super().__init__(message, status_code=429, error_code="RATE_LIMIT_EXCEEDED", **kwargs)
        self.retry_after = retry_after


class AuthenticationException(ClaudeAPIException):
    """Authentication and authorization errors."""

    def __init__(self, message: str = "Authentication failed", **kwargs: Any):
        """
        Initialize authentication exception.

        Args:
            message: Error message
            **kwargs: Additional arguments for ClaudeAPIException
        """
        super().__init__(message, status_code=401, error_code="AUTHENTICATION_FAILED", **kwargs)


class DatabaseException(PVReportException):
    """Database operation errors."""

    pass


class ReportGenerationException(PVReportException):
    """Report generation errors."""

    pass


class ComplianceCheckException(PVReportException):
    """Compliance checking errors."""

    pass


class FileOperationException(PVReportException):
    """File upload, download, or processing errors."""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initialize file operation exception.

        Args:
            message: Error message
            file_path: Path to file that caused error
            operation: Operation being performed (read, write, etc.)
            **kwargs: Additional arguments for PVReportException
        """
        details = kwargs.get("details", {})
        if file_path:
            details["file_path"] = file_path
        if operation:
            details["operation"] = operation
        kwargs["details"] = details

        super().__init__(message, **kwargs)
        self.file_path = file_path
        self.operation = operation


class StandardNotFoundException(PVReportException):
    """Requested testing standard not found or supported."""

    def __init__(self, standard: str, **kwargs: Any):
        """
        Initialize standard not found exception.

        Args:
            standard: Standard identifier
            **kwargs: Additional arguments
        """
        message = f"Testing standard '{standard}' not found or not supported"
        super().__init__(message, error_code="STANDARD_NOT_FOUND", **kwargs)
        self.standard = standard


class InsufficientDataException(PVReportException):
    """Insufficient data for analysis or report generation."""

    pass


class TokenLimitException(ClaudeAPIException):
    """Token limit exceeded errors."""

    def __init__(
        self,
        message: str = "Token limit exceeded",
        token_count: Optional[int] = None,
        token_limit: Optional[int] = None,
        **kwargs: Any,
    ):
        """
        Initialize token limit exception.

        Args:
            message: Error message
            token_count: Number of tokens in request
            token_limit: Maximum allowed tokens
            **kwargs: Additional arguments
        """
        details = kwargs.get("details", {})
        if token_count:
            details["token_count"] = token_count
        if token_limit:
            details["token_limit"] = token_limit
        kwargs["details"] = details

        super().__init__(message, status_code=400, error_code="TOKEN_LIMIT_EXCEEDED", **kwargs)
        self.token_count = token_count
        self.token_limit = token_limit
