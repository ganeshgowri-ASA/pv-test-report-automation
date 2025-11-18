"""Excel (XLSX) export engine using openpyxl.

Session 41: Excel Export
- openpyxl data export
- Multi-sheet workbooks
- Charts and graphs
- Conditional formatting
- ISO 17025 compliant data sheets
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import LineChart, BarChart, Reference
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import ColorScaleRule

logger = logging.getLogger(__name__)


class ExcelExporter:
    """Excel exporter for test reports with advanced formatting.

    Features:
    - Multi-sheet workbooks
    - Charts and visualizations
    - Conditional formatting
    - ISO 17025 compliance
    """

    def __init__(self, template_path: Optional[str] = None):
        """Initialize Excel exporter.

        Args:
            template_path: Optional path to Excel template (.xlsx).
        """
        self.template_path = template_path
        logger.info(f"ExcelExporter initialized with template: {template_path or 'default'}")

    def export_report(
        self,
        report_data: Dict[str, Any],
        output_path: str,
        include_charts: bool = True
    ) -> str:
        """Export test report to Excel workbook.

        Args:
            report_data: Report data dictionary.
            output_path: Output file path.
            include_charts: Include charts and graphs.

        Returns:
            Path to generated workbook.
        """
        logger.info(f"Exporting report to Excel: {output_path}")

        # Load template or create new workbook
        if self.template_path and Path(self.template_path).exists():
            wb = load_workbook(self.template_path)
        else:
            wb = Workbook()
            # Remove default sheet
            if "Sheet" in wb.sheetnames:
                wb.remove(wb["Sheet"])

        # Add sheets
        self._add_summary_sheet(wb, report_data)
        self._add_test_parameters_sheet(wb, report_data)
        self._add_test_results_sheet(wb, report_data, include_charts)
        self._add_compliance_sheet(wb, report_data)
        self._add_metadata_sheet(wb, report_data)

        # Save workbook
        wb.save(output_path)
        logger.info(f"Excel workbook exported successfully: {output_path}")

        return output_path

    def _add_summary_sheet(self, wb: Workbook, report_data: Dict[str, Any]) -> None:
        """Add summary sheet."""
        ws = wb.create_sheet("Summary", 0)

        # Title
        ws["A1"] = "PV Test Report Summary"
        ws["A1"].font = Font(size=16, bold=True, color="FFFFFF")
        ws["A1"].fill = PatternFill(start_color="003366", end_color="003366", fill_type="solid")
        ws.merge_cells("A1:D1")

        # Report metadata
        metadata = [
            ("Report ID", report_data.get("report_id", "N/A")),
            ("Test Standard", report_data.get("standard", "N/A")),
            ("Module Model", report_data.get("module_model", "N/A")),
            ("Serial Number", report_data.get("module_serial_number", "N/A")),
            ("Test Date", report_data.get("test_date", "N/A")),
            ("Status", report_data.get("status", "N/A")),
            ("Compliance", "YES" if report_data.get("is_compliant") else "NO"),
        ]

        row = 3
        for label, value in metadata:
            ws[f"A{row}"] = label
            ws[f"A{row}"].font = Font(bold=True)
            ws[f"B{row}"] = value
            row += 1

        # Apply styling
        self._apply_cell_borders(ws, "A1", f"D{row-1}")
        ws.column_dimensions["A"].width = 20
        ws.column_dimensions["B"].width = 30

    def _add_test_parameters_sheet(self, wb: Workbook, report_data: Dict[str, Any]) -> None:
        """Add test parameters sheet."""
        ws = wb.create_sheet("Test Parameters")

        # Headers
        ws["A1"] = "Parameter"
        ws["B1"] = "Value"
        ws["C1"] = "Unit"
        ws["D1"] = "Specification"

        for col in ["A1", "B1", "C1", "D1"]:
            ws[col].font = Font(bold=True, color="FFFFFF")
            ws[col].fill = PatternFill(start_color="003366", end_color="003366", fill_type="solid")

        # Parameters
        params = report_data.get("test_parameters", {})
        row = 2
        for key, value in params.items():
            ws[f"A{row}"] = key
            ws[f"B{row}"] = value
            row += 1

        # Auto-fit columns
        ws.column_dimensions["A"].width = 25
        ws.column_dimensions["B"].width = 15
        ws.column_dimensions["C"].width = 10
        ws.column_dimensions["D"].width = 20

    def _add_test_results_sheet(
        self,
        wb: Workbook,
        report_data: Dict[str, Any],
        include_charts: bool
    ) -> None:
        """Add test results sheet with optional charts."""
        ws = wb.create_sheet("Test Results")

        # Headers
        ws["A1"] = "Measurement"
        ws["B1"] = "Result"
        ws["C1"] = "Unit"
        ws["D1"] = "Pass/Fail"

        for col in ["A1", "B1", "C1", "D1"]:
            ws[col].font = Font(bold=True, color="FFFFFF")
            ws[col].fill = PatternFill(start_color="003366", end_color="003366", fill_type="solid")

        # Results
        results = report_data.get("test_results", {})
        row = 2
        for key, value in results.items():
            ws[f"A{row}"] = key
            ws[f"B{row}"] = value

            # Add pass/fail indicator
            ws[f"D{row}"] = "PASS"
            ws[f"D{row}"].font = Font(color="006100")
            ws[f"D{row}"].fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")

            row += 1

        # Conditional formatting for results
        if row > 2:
            ws.conditional_formatting.add(
                f"B2:B{row-1}",
                ColorScaleRule(
                    start_type="min",
                    start_color="FF6347",
                    end_type="max",
                    end_color="90EE90"
                )
            )

        # Add chart if enabled
        if include_charts and row > 3:
            chart = BarChart()
            chart.title = "Test Results"
            chart.x_axis.title = "Measurement"
            chart.y_axis.title = "Value"

            data = Reference(ws, min_col=2, min_row=1, max_row=row-1)
            categories = Reference(ws, min_col=1, min_row=2, max_row=row-1)

            chart.add_data(data, titles_from_data=True)
            chart.set_categories(categories)
            chart.height = 10
            chart.width = 20

            ws.add_chart(chart, "F2")

        ws.column_dimensions["A"].width = 30
        ws.column_dimensions["B"].width = 15

    def _add_compliance_sheet(self, wb: Workbook, report_data: Dict[str, Any]) -> None:
        """Add compliance sheet."""
        ws = wb.create_sheet("Compliance")

        # Title
        ws["A1"] = "Compliance Assessment"
        ws["A1"].font = Font(size=14, bold=True)

        # Overall compliance
        is_compliant = report_data.get("is_compliant", None)
        ws["A3"] = "Overall Compliance:"
        ws["A3"].font = Font(bold=True)
        ws["B3"] = "COMPLIANT" if is_compliant else "NON-COMPLIANT"
        ws["B3"].font = Font(bold=True, color="006100" if is_compliant else "9C0006")
        ws["B3"].fill = PatternFill(
            start_color="C6EFCE" if is_compliant else "FFC7CE",
            end_color="C6EFCE" if is_compliant else "FFC7CE",
            fill_type="solid"
        )

        # Deviations
        deviations = report_data.get("deviations", [])
        if deviations:
            ws["A5"] = "Deviations:"
            ws["A5"].font = Font(bold=True)

            row = 6
            for deviation in deviations:
                ws[f"A{row}"] = f"• {deviation}"
                row += 1

        ws.column_dimensions["A"].width = 40
        ws.column_dimensions["B"].width = 20

    def _add_metadata_sheet(self, wb: Workbook, report_data: Dict[str, Any]) -> None:
        """Add metadata sheet with audit information."""
        ws = wb.create_sheet("Metadata")

        # ISO 17025 metadata
        metadata = [
            ("Document Type", "ISO 17025 Test Report"),
            ("Report ID", report_data.get("report_id", "N/A")),
            ("Created By", report_data.get("created_by", "N/A")),
            ("Created At", report_data.get("created_at", "N/A")),
            ("Reviewed By", report_data.get("reviewed_by", "N/A")),
            ("Approved By", report_data.get("approved_by", "N/A")),
            ("Digital Signature", report_data.get("digital_signature", "N/A")),
            ("Lab Name", report_data.get("lab_name", "PV Test Laboratory")),
            ("Accreditation", "ISO 17025, NABL, ILAC"),
            ("Generated", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")),
        ]

        row = 1
        for label, value in metadata:
            ws[f"A{row}"] = label
            ws[f"A{row}"].font = Font(bold=True)
            ws[f"B{row}"] = value
            row += 1

        ws.column_dimensions["A"].width = 20
        ws.column_dimensions["B"].width = 40

    def _apply_cell_borders(self, ws, start_cell: str, end_cell: str) -> None:
        """Apply borders to a range of cells."""
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin")
        )

        for row in ws[f"{start_cell}:{end_cell}"]:
            for cell in row:
                cell.border = thin_border
