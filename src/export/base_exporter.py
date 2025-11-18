"""
Base Exporter Module

Provides abstract base classes and common utilities for all export engines.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import logging
from enum import Enum


logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """Supported export formats."""
    PDF = "pdf"
    WORD = "docx"
    HTML = "html"
    EXCEL = "xlsx"
    JSON = "json"
    XML = "xml"


class ExportStatus(Enum):
    """Export operation status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExportProgress:
    """Progress tracking for export operations."""
    total_items: int
    completed_items: int
    current_item: str
    status: ExportStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    error: Optional[str] = None

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.completed_items / self.total_items) * 100

    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time in seconds."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()


@dataclass
class ExportOptions:
    """Common export options."""
    output_path: Path
    template_name: Optional[str] = None
    include_charts: bool = True
    include_images: bool = True
    include_metadata: bool = True
    compress: bool = False
    watermark: Optional[str] = None
    custom_params: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.custom_params is None:
            self.custom_params = {}
        if isinstance(self.output_path, str):
            self.output_path = Path(self.output_path)


class TemplateManager:
    """Manages export templates."""

    def __init__(self, template_dir: Path):
        """
        Initialize template manager.

        Args:
            template_dir: Directory containing templates
        """
        self.template_dir = Path(template_dir)
        self._template_cache: Dict[str, Any] = {}

    def get_template(self, template_name: str, format_type: ExportFormat) -> Path:
        """
        Get template path for format.

        Args:
            template_name: Name of template
            format_type: Export format type

        Returns:
            Path to template file
        """
        template_path = self.template_dir / format_type.value / f"{template_name}.template"

        if not template_path.exists():
            logger.warning(f"Template not found: {template_path}")
            # Return default template
            template_path = self.template_dir / format_type.value / "default.template"

        return template_path

    def list_templates(self, format_type: ExportFormat) -> List[str]:
        """
        List available templates for format.

        Args:
            format_type: Export format type

        Returns:
            List of template names
        """
        template_dir = self.template_dir / format_type.value
        if not template_dir.exists():
            return []

        return [
            f.stem for f in template_dir.glob("*.template")
        ]

    def validate_template(self, template_path: Path) -> bool:
        """
        Validate template file.

        Args:
            template_path: Path to template

        Returns:
            True if valid
        """
        if not template_path.exists():
            return False

        if not template_path.is_file():
            return False

        # Additional validation can be added here
        return True


class BaseExporter(ABC):
    """Abstract base class for all exporters."""

    def __init__(self, template_manager: Optional[TemplateManager] = None):
        """
        Initialize exporter.

        Args:
            template_manager: Template manager instance
        """
        self.template_manager = template_manager
        self.progress_callbacks: List[Callable[[ExportProgress], None]] = []
        self._current_progress: Optional[ExportProgress] = None

    @property
    @abstractmethod
    def format_type(self) -> ExportFormat:
        """Get export format type."""
        pass

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Get file extension for this format."""
        pass

    @abstractmethod
    def export(self, data: Dict[str, Any], options: ExportOptions) -> Path:
        """
        Export data to file.

        Args:
            data: Data to export
            options: Export options

        Returns:
            Path to exported file
        """
        pass

    @abstractmethod
    def validate_output(self, output_path: Path) -> bool:
        """
        Validate exported file.

        Args:
            output_path: Path to exported file

        Returns:
            True if valid
        """
        pass

    def batch_export(
        self,
        data_items: List[Dict[str, Any]],
        output_dir: Path,
        options_template: ExportOptions
    ) -> List[Path]:
        """
        Export multiple items in batch.

        Args:
            data_items: List of data items to export
            output_dir: Output directory
            options_template: Template for export options

        Returns:
            List of exported file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        exported_files = []
        total_items = len(data_items)

        # Initialize progress tracking
        self._current_progress = ExportProgress(
            total_items=total_items,
            completed_items=0,
            current_item="Starting batch export",
            status=ExportStatus.IN_PROGRESS,
            start_time=datetime.now()
        )
        self._notify_progress()

        for idx, data in enumerate(data_items, 1):
            try:
                # Create unique filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                item_name = data.get("name", f"item_{idx}")
                filename = f"{item_name}_{timestamp}.{self.file_extension}"

                # Update options with unique output path
                item_options = ExportOptions(
                    output_path=output_dir / filename,
                    template_name=options_template.template_name,
                    include_charts=options_template.include_charts,
                    include_images=options_template.include_images,
                    include_metadata=options_template.include_metadata,
                    compress=options_template.compress,
                    watermark=options_template.watermark,
                    custom_params=options_template.custom_params.copy()
                )

                # Update progress
                self._current_progress.current_item = item_name
                self._notify_progress()

                # Export item
                output_path = self.export(data, item_options)
                exported_files.append(output_path)

                # Update progress
                self._current_progress.completed_items = idx
                self._notify_progress()

                logger.info(f"Exported {idx}/{total_items}: {output_path}")

            except Exception as e:
                logger.error(f"Failed to export item {idx}: {e}")
                self._current_progress.status = ExportStatus.FAILED
                self._current_progress.error = str(e)
                self._notify_progress()
                raise

        # Finalize progress
        self._current_progress.status = ExportStatus.COMPLETED
        self._current_progress.end_time = datetime.now()
        self._notify_progress()

        logger.info(f"Batch export completed: {len(exported_files)} files")
        return exported_files

    def add_progress_callback(self, callback: Callable[[ExportProgress], None]):
        """
        Add progress callback.

        Args:
            callback: Function to call on progress updates
        """
        self.progress_callbacks.append(callback)

    def remove_progress_callback(self, callback: Callable[[ExportProgress], None]):
        """
        Remove progress callback.

        Args:
            callback: Callback to remove
        """
        if callback in self.progress_callbacks:
            self.progress_callbacks.remove(callback)

    def _notify_progress(self):
        """Notify all progress callbacks."""
        if self._current_progress:
            for callback in self.progress_callbacks:
                try:
                    callback(self._current_progress)
                except Exception as e:
                    logger.error(f"Progress callback error: {e}")

    def get_current_progress(self) -> Optional[ExportProgress]:
        """
        Get current progress.

        Returns:
            Current progress or None
        """
        return self._current_progress

    def _ensure_output_directory(self, output_path: Path):
        """
        Ensure output directory exists.

        Args:
            output_path: Output file path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

    def _add_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add export metadata to data.

        Args:
            data: Original data

        Returns:
            Data with metadata
        """
        metadata = {
            "export_timestamp": datetime.now().isoformat(),
            "export_format": self.format_type.value,
            "exporter_version": "1.0.0"
        }

        return {
            **data,
            "_export_metadata": metadata
        }

    def _validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate input data.

        Args:
            data: Data to validate

        Returns:
            True if valid
        """
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        return True


class ExportRegistry:
    """Registry for export formats."""

    _exporters: Dict[ExportFormat, type] = {}

    @classmethod
    def register(cls, format_type: ExportFormat):
        """
        Decorator to register exporter class.

        Args:
            format_type: Export format type
        """
        def wrapper(exporter_class):
            cls._exporters[format_type] = exporter_class
            return exporter_class
        return wrapper

    @classmethod
    def get_exporter(cls, format_type: ExportFormat) -> type:
        """
        Get exporter class for format.

        Args:
            format_type: Export format type

        Returns:
            Exporter class
        """
        if format_type not in cls._exporters:
            raise ValueError(f"No exporter registered for format: {format_type}")
        return cls._exporters[format_type]

    @classmethod
    def list_formats(cls) -> List[ExportFormat]:
        """
        List registered formats.

        Returns:
            List of export formats
        """
        return list(cls._exporters.keys())


def create_exporter(
    format_type: ExportFormat,
    template_manager: Optional[TemplateManager] = None
) -> BaseExporter:
    """
    Factory function to create exporter instance.

    Args:
        format_type: Export format type
        template_manager: Template manager instance

    Returns:
        Exporter instance
    """
    exporter_class = ExportRegistry.get_exporter(format_type)
    return exporter_class(template_manager)
