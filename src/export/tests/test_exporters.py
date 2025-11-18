"""
Exporter Integration Tests

Tests for all export engines (PDF, Word, HTML, Excel, JSON, XML).
"""

import unittest
from pathlib import Path
import tempfile
import shutil
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from export import (
    PDFExporter,
    WordExporter,
    HTMLExporter,
    ExcelExporter,
    JSONExporter,
    XMLExporter,
    ExportOptions,
    ExportFormat
)


class TestDataMixin:
    """Mixin providing test data."""

    @staticmethod
    def get_test_data():
        """Get sample test data."""
        return {
            "title": "PV Test Report - Sample",
            "summary": "This is a comprehensive test report for photovoltaic system testing.",
            "configuration": {
                "test_date": "2025-01-15",
                "location": "Test Site A",
                "system_size": "100 kW",
                "module_count": 300,
                "inverter_type": "String Inverter"
            },
            "test_results": [
                {
                    "name": "Open Circuit Voltage",
                    "status": "PASS",
                    "value": 42.5,
                    "expected": 42.0,
                    "notes": "Within acceptable range"
                },
                {
                    "name": "Short Circuit Current",
                    "status": "PASS",
                    "value": 9.8,
                    "expected": 9.5,
                    "notes": "Good performance"
                },
                {
                    "name": "Insulation Resistance",
                    "status": "FAIL",
                    "value": 0.8,
                    "expected": 1.0,
                    "notes": "Below minimum threshold"
                },
                {
                    "name": "Ground Continuity",
                    "status": "PASS",
                    "value": 0.05,
                    "expected": 0.1,
                    "notes": "Excellent"
                }
            ],
            "analysis": "Overall system performance is good with one minor issue in insulation resistance that requires attention.",
            "recommendations": [
                "Inspect and repair insulation on affected modules",
                "Retest insulation resistance after repairs",
                "Schedule follow-up inspection in 30 days"
            ]
        }


class TestJSONExporter(unittest.TestCase, TestDataMixin):
    """Test JSON exporter."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir)
        self.exporter = JSONExporter()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_basic_export(self):
        """Test basic JSON export."""
        data = self.get_test_data()
        output_path = self.output_dir / "test.json"
        options = ExportOptions(output_path=output_path)

        result = self.exporter.export(data, options)

        self.assertTrue(result.exists())
        self.assertTrue(self.exporter.validate_output(result))

        # Verify content
        with open(result, 'r') as f:
            loaded_data = json.load(f)
            self.assertEqual(loaded_data["title"], data["title"])

    def test_export_with_metadata(self):
        """Test JSON export with metadata."""
        data = self.get_test_data()
        output_path = self.output_dir / "test_metadata.json"
        options = ExportOptions(
            output_path=output_path,
            include_metadata=True
        )

        result = self.exporter.export(data, options)

        with open(result, 'r') as f:
            loaded_data = json.load(f)
            self.assertIn("_export_metadata", loaded_data)

    def test_schema_generation(self):
        """Test JSON schema generation."""
        data = self.get_test_data()
        schema = self.exporter.generate_schema(data)

        self.assertIn("$schema", schema)
        self.assertIn("type", schema)
        self.assertEqual(schema["type"], "object")

    def test_pretty_print(self):
        """Test JSON pretty printing."""
        data = {"test": "data", "nested": {"key": "value"}}
        output_path = self.output_dir / "test.json"
        options = ExportOptions(output_path=output_path)

        result = self.exporter.export(data, options)
        pretty_result = self.exporter.pretty_print(result)

        self.assertTrue(pretty_result.exists())

    def test_minify(self):
        """Test JSON minification."""
        data = self.get_test_data()
        output_path = self.output_dir / "test.json"
        options = ExportOptions(output_path=output_path)

        result = self.exporter.export(data, options)
        minified = self.exporter.minify(result)

        self.assertTrue(minified.exists())
        # Minified should be smaller
        self.assertLess(
            minified.stat().st_size,
            result.stat().st_size
        )


class TestXMLExporter(unittest.TestCase, TestDataMixin):
    """Test XML exporter."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir)
        self.exporter = XMLExporter()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_basic_export(self):
        """Test basic XML export."""
        data = self.get_test_data()
        output_path = self.output_dir / "test.xml"
        options = ExportOptions(output_path=output_path)

        result = self.exporter.export(data, options)

        self.assertTrue(result.exists())
        self.assertTrue(self.exporter.validate_output(result))

    def test_custom_root_element(self):
        """Test XML export with custom root element."""
        data = {"test": "data"}
        output_path = self.output_dir / "test_custom.xml"
        options = ExportOptions(
            output_path=output_path,
            custom_params={"root_element": "custom_root"}
        )

        result = self.exporter.export(data, options)

        with open(result, 'r') as f:
            content = f.read()
            self.assertIn("<custom_root>", content)

    def test_xml_to_dict(self):
        """Test XML to dictionary conversion."""
        data = self.get_test_data()
        output_path = self.output_dir / "test.xml"
        options = ExportOptions(output_path=output_path)

        result = self.exporter.export(data, options)
        converted = self.exporter.xml_to_dict(result)

        self.assertIsInstance(converted, dict)


class TestHTMLExporter(unittest.TestCase, TestDataMixin):
    """Test HTML exporter."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir)
        self.exporter = HTMLExporter()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_basic_export(self):
        """Test basic HTML export."""
        data = self.get_test_data()
        output_path = self.output_dir / "test.html"
        options = ExportOptions(output_path=output_path)

        result = self.exporter.export(data, options)

        self.assertTrue(result.exists())
        self.assertTrue(self.exporter.validate_output(result))

        # Verify HTML structure
        with open(result, 'r') as f:
            content = f.read()
            self.assertIn("<!DOCTYPE html>", content)
            self.assertIn("<html", content)
            self.assertIn(data["title"], content)

    def test_html_with_sections(self):
        """Test HTML export with all sections."""
        data = self.get_test_data()
        output_path = self.output_dir / "test_full.html"
        options = ExportOptions(
            output_path=output_path,
            include_metadata=True,
            include_charts=True
        )

        result = self.exporter.export(data, options)

        with open(result, 'r') as f:
            content = f.read()
            self.assertIn("Test Results", content)
            self.assertIn("Configuration", content)
            self.assertIn("Summary", content)

    def test_responsive_design(self):
        """Test HTML includes responsive design."""
        data = self.get_test_data()
        output_path = self.output_dir / "test_responsive.html"
        options = ExportOptions(output_path=output_path)

        result = self.exporter.export(data, options)

        with open(result, 'r') as f:
            content = f.read()
            self.assertIn("viewport", content)
            self.assertIn("@media", content)


class TestPDFExporter(unittest.TestCase, TestDataMixin):
    """Test PDF exporter."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_reportlab_available(self):
        """Test if ReportLab is available."""
        try:
            from export.pdf_exporter import REPORTLAB_AVAILABLE
            if REPORTLAB_AVAILABLE:
                self.assertTrue(True)
            else:
                self.skipTest("ReportLab not available")
        except ImportError:
            self.skipTest("ReportLab not installed")

    def test_basic_export(self):
        """Test basic PDF export."""
        try:
            from export.pdf_exporter import REPORTLAB_AVAILABLE
            if not REPORTLAB_AVAILABLE:
                self.skipTest("ReportLab not available")

            from export.pdf_exporter import PDFEngine
            exporter = PDFExporter(engine=PDFEngine.REPORTLAB)

            data = self.get_test_data()
            output_path = self.output_dir / "test.pdf"
            options = ExportOptions(output_path=output_path)

            result = exporter.export(data, options)

            self.assertTrue(result.exists())
            self.assertTrue(exporter.validate_output(result))
        except ImportError:
            self.skipTest("ReportLab not installed")


class TestWordExporter(unittest.TestCase, TestDataMixin):
    """Test Word exporter."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_docx_available(self):
        """Test if python-docx is available."""
        try:
            from export.word_exporter import DOCX_AVAILABLE
            if DOCX_AVAILABLE:
                self.assertTrue(True)
            else:
                self.skipTest("python-docx not available")
        except ImportError:
            self.skipTest("python-docx not installed")

    def test_basic_export(self):
        """Test basic Word export."""
        try:
            from export.word_exporter import DOCX_AVAILABLE
            if not DOCX_AVAILABLE:
                self.skipTest("python-docx not available")

            exporter = WordExporter()

            data = self.get_test_data()
            output_path = self.output_dir / "test.docx"
            options = ExportOptions(output_path=output_path)

            result = exporter.export(data, options)

            self.assertTrue(result.exists())
            self.assertTrue(exporter.validate_output(result))
        except ImportError:
            self.skipTest("python-docx not installed")


class TestExcelExporter(unittest.TestCase, TestDataMixin):
    """Test Excel exporter."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_openpyxl_available(self):
        """Test if openpyxl is available."""
        try:
            from export.excel_exporter import OPENPYXL_AVAILABLE
            if OPENPYXL_AVAILABLE:
                self.assertTrue(True)
            else:
                self.skipTest("openpyxl not available")
        except ImportError:
            self.skipTest("openpyxl not installed")

    def test_basic_export(self):
        """Test basic Excel export."""
        try:
            from export.excel_exporter import OPENPYXL_AVAILABLE, ExcelEngine
            if not OPENPYXL_AVAILABLE:
                self.skipTest("openpyxl not available")

            exporter = ExcelExporter(engine=ExcelEngine.OPENPYXL)

            data = self.get_test_data()
            output_path = self.output_dir / "test.xlsx"
            options = ExportOptions(output_path=output_path)

            result = exporter.export(data, options)

            self.assertTrue(result.exists())
            self.assertTrue(exporter.validate_output(result))
        except ImportError:
            self.skipTest("openpyxl not installed")


class TestBatchExport(unittest.TestCase, TestDataMixin):
    """Test batch export functionality across all formats."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_json_batch_export(self):
        """Test batch export for JSON."""
        exporter = JSONExporter()

        data_items = [
            {**self.get_test_data(), "name": f"test_{i}"}
            for i in range(3)
        ]

        options_template = ExportOptions(
            output_path=self.output_dir / "dummy.json"
        )

        results = exporter.batch_export(data_items, self.output_dir, options_template)

        self.assertEqual(len(results), 3)
        for result in results:
            self.assertTrue(result.exists())


if __name__ == '__main__':
    unittest.main()
