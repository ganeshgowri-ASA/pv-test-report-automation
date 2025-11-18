"""
Structured logging configuration for PV Test Report Automation.

Provides JSON and colored console logging with support for audit trails
and LLM interaction logging.
"""

import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import colorlog
from pythonjsonlogger import jsonlogger

from src.config.settings import get_settings


class CustomJSONFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional context fields."""

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)

        # Add timestamp in ISO format
        if not log_record.get("timestamp"):
            log_record["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # Add level name
        if log_record.get("level"):
            log_record["level"] = record.levelname
        else:
            log_record["level"] = record.levelname

        # Add logger name
        log_record["logger"] = record.name

        # Add module and function info
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno


class StructuredLogger:
    """Wrapper for structured logging with custom methods for different event types."""

    def __init__(self, name: str):
        """
        Initialize structured logger.

        Args:
            name: Logger name (typically __name__ of the module)
        """
        self.logger = logging.getLogger(name)
        self.settings = get_settings()

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message with optional context."""
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message with optional context."""
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with optional context."""
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs: Any) -> None:
        """Log error message with optional context."""
        self.logger.error(message, exc_info=exc_info, extra=kwargs)

    def critical(self, message: str, exc_info: bool = False, **kwargs: Any) -> None:
        """Log critical message with optional context."""
        self.logger.critical(message, exc_info=exc_info, extra=kwargs)

    def log_llm_call(
        self,
        model: str,
        operation: str,
        tokens_used: Dict[str, int],
        duration: float,
        success: bool = True,
        error: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Log LLM API call with metadata.

        Args:
            model: Model name used
            operation: Type of operation (analysis, summary, etc.)
            tokens_used: Dictionary with input/output token counts
            duration: Duration in seconds
            success: Whether the call succeeded
            error: Error message if failed
            **kwargs: Additional context
        """
        log_data = {
            "event_type": "llm_call",
            "llm_model": model,
            "operation": operation,
            "tokens_input": tokens_used.get("input", 0),
            "tokens_output": tokens_used.get("output", 0),
            "tokens_total": tokens_used.get("input", 0) + tokens_used.get("output", 0),
            "duration_seconds": round(duration, 3),
            "success": success,
            **kwargs,
        }

        if error:
            log_data["error"] = error

        if success:
            self.logger.info("LLM API call completed", extra=log_data)
        else:
            self.logger.error("LLM API call failed", extra=log_data)

    def log_audit_event(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: str,
        status: str = "success",
        changes: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Log audit trail event.

        Args:
            action: Action performed (CREATE, UPDATE, DELETE, etc.)
            resource_type: Type of resource affected
            resource_id: ID of the resource
            user_id: User who performed the action
            status: Success or failure status
            changes: Dictionary of changes made
            **kwargs: Additional context
        """
        log_data = {
            "event_type": "audit",
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user_id": user_id,
            "status": status,
            **kwargs,
        }

        if changes:
            log_data["changes"] = changes

        # Use audit logger
        audit_logger = logging.getLogger("audit")
        audit_logger.info(f"Audit: {action} on {resource_type}", extra=log_data)

    def log_compliance_check(
        self,
        report_id: str,
        standard: str,
        compliance_score: float,
        issues_found: int,
        **kwargs: Any,
    ) -> None:
        """
        Log compliance check results.

        Args:
            report_id: Report being checked
            standard: Standard being checked against
            compliance_score: Compliance score (0-100)
            issues_found: Number of issues found
            **kwargs: Additional context
        """
        log_data = {
            "event_type": "compliance_check",
            "report_id": report_id,
            "standard": standard,
            "compliance_score": compliance_score,
            "issues_found": issues_found,
            **kwargs,
        }

        self.logger.info("Compliance check completed", extra=log_data)

    def log_report_generation(
        self,
        report_id: str,
        report_type: str,
        format: str,
        success: bool,
        duration: float,
        **kwargs: Any,
    ) -> None:
        """
        Log report generation event.

        Args:
            report_id: Report ID
            report_type: Type of report generated
            format: Output format (PDF, DOCX, etc.)
            success: Whether generation succeeded
            duration: Generation time in seconds
            **kwargs: Additional context
        """
        log_data = {
            "event_type": "report_generation",
            "report_id": report_id,
            "report_type": report_type,
            "format": format,
            "success": success,
            "duration_seconds": round(duration, 3),
            **kwargs,
        }

        if success:
            self.logger.info("Report generated successfully", extra=log_data)
        else:
            self.logger.error("Report generation failed", extra=log_data)


def setup_logging() -> None:
    """
    Configure application logging with file and console handlers.

    Sets up:
    - Console handler with colored output (development)
    - JSON file handler for application logs
    - Separate audit trail log file
    - Separate LLM interaction log file
    """
    settings = get_settings()

    # Create logs directory
    log_dir = settings.get_log_dir()

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler with colors (for development)
    if settings.is_development():
        console_handler = colorlog.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
        console_formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    else:
        # Simple console handler for production
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # Application log file handler (JSON format)
    app_log_file = log_dir / Path(settings.LOG_FILE_PATH).name
    file_handler = logging.handlers.RotatingFileHandler(
        app_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    json_formatter = CustomJSONFormatter(
        "%(timestamp)s %(level)s %(logger)s %(module)s %(function)s %(line)s %(message)s"
    )
    file_handler.setFormatter(json_formatter)
    root_logger.addHandler(file_handler)

    # Audit log file handler
    if settings.ENABLE_AUDIT_TRAIL:
        audit_log_file = log_dir / Path(settings.AUDIT_LOG_PATH).name
        audit_handler = logging.handlers.RotatingFileHandler(
            audit_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
            encoding="utf-8",
        )
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(json_formatter)

        # Create audit logger
        audit_logger = logging.getLogger("audit")
        audit_logger.setLevel(logging.INFO)
        audit_logger.addHandler(audit_handler)
        audit_logger.propagate = False

    # LLM interaction log file handler
    llm_log_file = log_dir / Path(settings.LLM_LOG_PATH).name
    llm_handler = logging.handlers.RotatingFileHandler(
        llm_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    llm_handler.setLevel(logging.DEBUG)
    llm_handler.setFormatter(json_formatter)

    # Create LLM logger
    llm_logger = logging.getLogger("llm")
    llm_logger.setLevel(logging.DEBUG)
    llm_logger.addHandler(llm_handler)
    llm_logger.propagate = False

    # Log startup
    logger = StructuredLogger(__name__)
    logger.info(
        "Logging configured",
        log_level=settings.LOG_LEVEL,
        environment=settings.ENVIRONMENT,
        audit_enabled=settings.ENABLE_AUDIT_TRAIL,
    )


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        StructuredLogger: Configured logger instance
    """
    return StructuredLogger(name)
