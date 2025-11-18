"""Unit tests for export engines."""
import pytest
from pathlib import Path
from src.export import WordExporter, ExcelExporter, HTMLExporter, JSONExporter, PDFExporter


class TestExporters:
    """Test all exporters."""
    
    @pytest.fixture
    def sample_report_data(self):
        """Sample report data."""
        return {
            "report_id": "RPT-2024-001",
            "standard": "IEC 61215",
            "module_model": "TEST-400W",
            "module_serial_number": "SN001",
            "test_date": "2024-01-15",
            "status": "completed",
            "test_results": {"Power": "400W", "Efficiency": "21%"},
            "is_compliant": True,
            "deviations": [],
            "created_by": "engineer@test.com"
        }
    
    def test_json_export(self, sample_report_data, tmp_path):
        """Test JSON export."""
        exporter = JSONExporter()
        output = tmp_path / "report.json"
        result = exporter.export_report(sample_report_data, str(output))
        assert Path(result).exists()
    
    def test_html_export(self, sample_report_data, tmp_path):
        """Test HTML export."""
        exporter = HTMLExporter()
        output = tmp_path / "report.html"
        result = exporter.export_report(sample_report_data, str(output))
        assert Path(result).exists()
