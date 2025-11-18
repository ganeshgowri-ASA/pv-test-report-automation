"""Integration tests for export workflow.

Session 56: Integration Test Suite
"""
import pytest
from pathlib import Path


class TestExportWorkflow:
    """Test end-to-end export workflow."""
    
    @pytest.mark.integration
    def test_multi_format_export(self, tmp_path):
        """Test exporting to multiple formats."""
        from src.export import WordExporter, ExcelExporter, HTMLExporter, JSONExporter
        
        report_data = {
            "report_id": "INT-001",
            "standard": "IEC 61215",
            "test_results": {"Power": 400}
        }
        
        # Export to all formats
        formats = {
            "word": WordExporter(),
            "excel": ExcelExporter(),
            "html": HTMLExporter(),
            "json": JSONExporter()
        }
        
        for fmt_name, exporter in formats.items():
            output = tmp_path / f"report.{fmt_name}"
            result = exporter.export_report(report_data, str(output))
            assert Path(result).exists()
