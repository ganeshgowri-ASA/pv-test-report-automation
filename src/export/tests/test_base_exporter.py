"""
Base Exporter Tests

Tests for base exporter functionality and common utilities.
"""

import unittest
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from export.base_exporter import (
    BaseExporter,
    ExportFormat,
    ExportStatus,
    ExportOptions,
    ExportProgress,
    TemplateManager,
    ExportRegistry,
    create_exporter
)


class MockExporter(BaseExporter):
    """Mock exporter for testing."""

    @property
    def format_type(self) -> ExportFormat:
        return ExportFormat.JSON

    @property
    def file_extension(self) -> str:
        return "json"

    def export(self, data, options):
        output_path = options.output_path
        self._ensure_output_directory(output_path)

        # Simple export
        with open(output_path, 'w') as f:
            f.write('{"test": "data"}')

        return output_path

    def validate_output(self, output_path):
        return output_path.exists() and output_path.stat().st_size > 0


class TestExportProgress(unittest.TestCase):
    """Test ExportProgress class."""

    def test_progress_percentage(self):
        """Test progress percentage calculation."""
        progress = ExportProgress(
            total_items=10,
            completed_items=5,
            current_item="test",
            status=ExportStatus.IN_PROGRESS,
            start_time=datetime.now()
        )

        self.assertEqual(progress.progress_percentage, 50.0)

    def test_progress_percentage_zero_total(self):
        """Test progress percentage with zero total items."""
        progress = ExportProgress(
            total_items=0,
            completed_items=0,
            current_item="test",
            status=ExportStatus.PENDING,
            start_time=datetime.now()
        )

        self.assertEqual(progress.progress_percentage, 0.0)

    def test_elapsed_time(self):
        """Test elapsed time calculation."""
        start = datetime.now()
        progress = ExportProgress(
            total_items=10,
            completed_items=5,
            current_item="test",
            status=ExportStatus.IN_PROGRESS,
            start_time=start
        )

        elapsed = progress.elapsed_time
        self.assertGreaterEqual(elapsed, 0)


class TestExportOptions(unittest.TestCase):
    """Test ExportOptions class."""

    def test_default_options(self):
        """Test default export options."""
        options = ExportOptions(output_path=Path("/tmp/test.json"))

        self.assertEqual(options.output_path, Path("/tmp/test.json"))
        self.assertIsNone(options.template_name)
        self.assertTrue(options.include_charts)
        self.assertTrue(options.include_images)
        self.assertTrue(options.include_metadata)
        self.assertFalse(options.compress)
        self.assertIsNone(options.watermark)
        self.assertEqual(options.custom_params, {})

    def test_string_path_conversion(self):
        """Test automatic conversion of string path to Path."""
        options = ExportOptions(output_path="/tmp/test.json")
        self.assertIsInstance(options.output_path, Path)


class TestTemplateManager(unittest.TestCase):
    """Test TemplateManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.template_dir = Path(self.temp_dir)

        # Create template directories
        (self.template_dir / "json").mkdir(parents=True)
        (self.template_dir / "pdf").mkdir(parents=True)

        # Create template files
        (self.template_dir / "json" / "test_template.template").touch()
        (self.template_dir / "json" / "default.template").touch()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_get_template(self):
        """Test getting template path."""
        manager = TemplateManager(self.template_dir)
        template_path = manager.get_template("test_template", ExportFormat.JSON)

        self.assertTrue(template_path.exists())
        self.assertEqual(template_path.name, "test_template.template")

    def test_get_default_template(self):
        """Test getting default template when requested template doesn't exist."""
        manager = TemplateManager(self.template_dir)
        template_path = manager.get_template("nonexistent", ExportFormat.JSON)

        self.assertEqual(template_path.name, "default.template")

    def test_list_templates(self):
        """Test listing available templates."""
        manager = TemplateManager(self.template_dir)
        templates = manager.list_templates(ExportFormat.JSON)

        self.assertIn("test_template", templates)
        self.assertIn("default", templates)

    def test_validate_template(self):
        """Test template validation."""
        manager = TemplateManager(self.template_dir)

        valid_path = self.template_dir / "json" / "test_template.template"
        self.assertTrue(manager.validate_template(valid_path))

        invalid_path = self.template_dir / "json" / "nonexistent.template"
        self.assertFalse(manager.validate_template(invalid_path))


class TestBaseExporter(unittest.TestCase):
    """Test BaseExporter class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir)
        self.exporter = MockExporter()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_export(self):
        """Test basic export functionality."""
        output_path = self.output_dir / "test.json"
        options = ExportOptions(output_path=output_path)
        data = {"test": "data"}

        result = self.exporter.export(data, options)

        self.assertTrue(result.exists())
        self.assertEqual(result, output_path)

    def test_batch_export(self):
        """Test batch export functionality."""
        data_items = [
            {"name": "test1", "value": 1},
            {"name": "test2", "value": 2},
            {"name": "test3", "value": 3}
        ]

        options_template = ExportOptions(output_path=self.output_dir / "dummy.json")

        results = self.exporter.batch_export(data_items, self.output_dir, options_template)

        self.assertEqual(len(results), 3)
        for result in results:
            self.assertTrue(result.exists())

    def test_progress_tracking(self):
        """Test progress tracking during export."""
        progress_updates = []

        def progress_callback(progress):
            progress_updates.append(progress.completed_items)

        self.exporter.add_progress_callback(progress_callback)

        data_items = [
            {"name": f"test{i}", "value": i} for i in range(5)
        ]

        options_template = ExportOptions(output_path=self.output_dir / "dummy.json")
        self.exporter.batch_export(data_items, self.output_dir, options_template)

        # Should have progress updates
        self.assertGreater(len(progress_updates), 0)

    def test_metadata_addition(self):
        """Test metadata addition to data."""
        data = {"test": "data"}
        result = self.exporter._add_metadata(data)

        self.assertIn("_export_metadata", result)
        self.assertIn("export_timestamp", result["_export_metadata"])
        self.assertIn("export_format", result["_export_metadata"])
        self.assertIn("exporter_version", result["_export_metadata"])

    def test_data_validation(self):
        """Test data validation."""
        # Valid data
        valid_data = {"test": "data"}
        self.assertTrue(self.exporter._validate_data(valid_data))

        # Invalid data
        with self.assertRaises(ValueError):
            self.exporter._validate_data("not a dict")


class TestExportRegistry(unittest.TestCase):
    """Test ExportRegistry class."""

    def test_register_decorator(self):
        """Test exporter registration."""
        @ExportRegistry.register(ExportFormat.JSON)
        class TestExporter(BaseExporter):
            @property
            def format_type(self):
                return ExportFormat.JSON

            @property
            def file_extension(self):
                return "json"

            def export(self, data, options):
                pass

            def validate_output(self, output_path):
                pass

        exporter_class = ExportRegistry.get_exporter(ExportFormat.JSON)
        self.assertIsNotNone(exporter_class)

    def test_list_formats(self):
        """Test listing registered formats."""
        formats = ExportRegistry.list_formats()
        self.assertIsInstance(formats, list)


class TestCreateExporter(unittest.TestCase):
    """Test create_exporter factory function."""

    def test_create_json_exporter(self):
        """Test creating JSON exporter."""
        exporter = create_exporter(ExportFormat.JSON)
        self.assertIsNotNone(exporter)
        self.assertEqual(exporter.format_type, ExportFormat.JSON)


if __name__ == '__main__':
    unittest.main()
