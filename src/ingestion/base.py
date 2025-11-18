"""
Base ingestion module providing abstract interface for all data sources.

All ingestion modules (Visio, Gantt, Smartsheet) should inherit from BaseIngestionModule.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, TypeVar

from src.core.config import get_settings
from src.core.exceptions import FileSizeExceededError, UnsupportedFileFormatError
from src.core.models import BaseIngestionResult

# Type variable for specific ingestion result types
T = TypeVar('T', bound=BaseIngestionResult)


class BaseIngestionModule(ABC, Generic[T]):
    """
    Abstract base class for all ingestion modules.

    Provides common functionality and enforces interface contract.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the ingestion module.

        Args:
            config: Optional configuration dictionary to override defaults
        """
        self.settings = get_settings()
        self.config = config or {}
        self._validate_configuration()

    @abstractmethod
    def _validate_configuration(self) -> None:
        """
        Validate module-specific configuration.

        Should raise ConfigurationError if configuration is invalid.
        """
        pass

    @abstractmethod
    def validate_file(self, file_path: Path) -> bool:
        """
        Validate that the file can be processed.

        Args:
            file_path: Path to the file to validate

        Returns:
            True if file is valid

        Raises:
            UnsupportedFileFormatError: If file format is not supported
            FileSizeExceededError: If file size exceeds maximum
        """
        pass

    @abstractmethod
    def ingest(self, source: Any, **kwargs: Any) -> T:
        """
        Ingest data from the source.

        Args:
            source: Source to ingest from (file path, API endpoint, etc.)
            **kwargs: Additional arguments specific to the ingestion type

        Returns:
            Ingestion result with extracted data

        Raises:
            IngestionError: If ingestion fails
        """
        pass

    @abstractmethod
    def extract_metadata(self, source: Any) -> Dict[str, Any]:
        """
        Extract metadata from the source without full ingestion.

        Args:
            source: Source to extract metadata from

        Returns:
            Dictionary of metadata
        """
        pass

    def check_file_size(self, file_path: Path) -> None:
        """
        Check if file size is within acceptable limits.

        Args:
            file_path: Path to file to check

        Raises:
            FileSizeExceededError: If file is too large
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size_bytes = file_path.stat().st_size
        max_size_bytes = self.settings.max_file_size_bytes

        if file_size_bytes > max_size_bytes:
            file_size_mb = file_size_bytes / (1024 * 1024)
            max_size_mb = self.settings.max_file_size_mb
            raise FileSizeExceededError(
                f"File size ({file_size_mb:.2f} MB) exceeds maximum "
                f"allowed size ({max_size_mb} MB)"
            )

    def check_file_extension(self, file_path: Path, allowed_extensions: List[str]) -> None:
        """
        Check if file has an allowed extension.

        Args:
            file_path: Path to file to check
            allowed_extensions: List of allowed extensions (e.g., ['.vsdx', '.vsd'])

        Raises:
            UnsupportedFileFormatError: If extension is not allowed
        """
        file_extension = file_path.suffix.lower()
        allowed_extensions_lower = [ext.lower() for ext in allowed_extensions]

        if file_extension not in allowed_extensions_lower:
            raise UnsupportedFileFormatError(
                f"File extension '{file_extension}' not supported. "
                f"Allowed extensions: {', '.join(allowed_extensions)}"
            )

    def get_temp_dir(self) -> Path:
        """Get temporary directory for processing."""
        return self.settings.ensure_temp_dir()

    def get_output_dir(self) -> Path:
        """Get output directory for results."""
        return self.settings.ensure_output_dir()


class FileBasedIngestionModule(BaseIngestionModule[T], ABC):
    """
    Base class for file-based ingestion modules.

    Provides common file handling functionality.
    """

    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """List of supported file extensions."""
        pass

    def validate_file(self, file_path: Path) -> bool:
        """
        Validate file for processing.

        Args:
            file_path: Path to file to validate

        Returns:
            True if file is valid
        """
        self.check_file_extension(file_path, self.supported_extensions)
        self.check_file_size(file_path)
        return True

    def ingest_from_file(self, file_path: str, **kwargs: Any) -> T:
        """
        Ingest data from a file.

        Args:
            file_path: Path to file to ingest
            **kwargs: Additional ingestion arguments

        Returns:
            Ingestion result
        """
        path = Path(file_path)
        self.validate_file(path)
        return self.ingest(path, **kwargs)
