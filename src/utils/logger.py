"""
Logging utilities for PV test report automation.

Provides structured logging using loguru.
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from src.core.config import get_settings


def setup_logger(
    log_file: Optional[str] = None,
    rotation: str = "10 MB",
    retention: str = "30 days",
    level: Optional[str] = None
) -> None:
    """
    Configure the application logger.

    Args:
        log_file: Optional path to log file. If None, logs to stdout only.
        rotation: When to rotate log files (default: 10 MB)
        retention: How long to keep old log files (default: 30 days)
        level: Logging level override. If None, uses settings.log_level
    """
    settings = get_settings()

    # Remove default logger
    logger.remove()

    # Determine log level
    log_level = level or settings.log_level

    # Add console handler with color
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )

    # Add file handler if log_file specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_level,
            rotation=rotation,
            retention=retention,
            compression="zip"
        )

    logger.info(f"Logger initialized at {log_level} level")


def get_logger(name: str = __name__):
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logger.bind(name=name)


# Initialize default logger
setup_logger()
