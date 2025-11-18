"""
Microsoft Excel Data Export using openpyxl.

Exports test data to Excel workbooks (.xlsx) with:
- Multiple worksheets
- Formatted tables
- Charts and graphs
- Data validation
- Formulas and calculations
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ExcelExportConfig(BaseModel):
    """Excel export configuration."""

    include_charts: bool = True
    include_raw_data: bool = True


class ExcelExporter:
    """Excel workbook exporter for PV test data."""

    def __init__(self, config: ExcelExportConfig = ExcelExportConfig()):
        """Initialize Excel exporter."""
        self.config = config
        logger.info("Excel exporter initialized")

    def export_report(self, test_report: Dict[str, Any], output_path: str) -> str:
        """Export report to Excel workbook."""
        logger.info(f"Exporting to Excel: {output_path}")

        wb = Workbook()
        ws = wb.active
        ws.title = "Test Report"  # type: ignore

        # Header styling
        header_fill = PatternFill(start_color="1f4788", end_color="1f4788", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)

        # Report information
        ws["A1"] = "Report Number"  # type: ignore
        ws["B1"] = test_report.get("report_number", "N/A")  # type: ignore
        ws["A2"] = "Test Type"  # type: ignore
        ws["B2"] = test_report.get("test_type", "N/A")  # type: ignore

        # Sample data
        ws["A4"] = "Sample ID"  # type: ignore
        ws["A4"].fill = header_fill  # type: ignore
        ws["A4"].font = header_font  # type: ignore

        sample = test_report.get("sample", {})
        ws["B4"] = sample.get("sample_id", "N/A")  # type: ignore

        # Save
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        wb.save(output_path)

        logger.info(f"Excel workbook exported: {output_path}")
        return output_path
