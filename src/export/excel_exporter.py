"""
Excel Exporter Module

Provides Excel export functionality using openpyxl and xlsxwriter.
Includes multi-sheet workbooks, charts, formatting, and data validation.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import logging

try:
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.chart import LineChart, BarChart, PieChart, Reference
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    import xlsxwriter
    XLSXWRITER_AVAILABLE = True
except ImportError:
    XLSXWRITER_AVAILABLE = False

from .base_exporter import (
    BaseExporter, ExportFormat, ExportOptions, ExportRegistry
)


logger = logging.getLogger(__name__)


class ExcelEngine:
    """Excel generation engine selection."""
    OPENPYXL = "openpyxl"
    XLSXWRITER = "xlsxwriter"


@ExportRegistry.register(ExportFormat.EXCEL)
class ExcelExporter(BaseExporter):
    """Excel export engine with openpyxl and xlsxwriter support."""

    def __init__(self, template_manager=None, engine: str = ExcelEngine.OPENPYXL):
        """
        Initialize Excel exporter.

        Args:
            template_manager: Template manager instance
            engine: Excel generation engine to use
        """
        super().__init__(template_manager)
        self.engine = engine
        self._validate_dependencies()

    @property
    def format_type(self) -> ExportFormat:
        """Get export format type."""
        return ExportFormat.EXCEL

    @property
    def file_extension(self) -> str:
        """Get file extension."""
        return "xlsx"

    def _validate_dependencies(self):
        """Validate required dependencies."""
        if self.engine == ExcelEngine.OPENPYXL and not OPENPYXL_AVAILABLE:
            raise ImportError("openpyxl not installed. Install with: pip install openpyxl")
        if self.engine == ExcelEngine.XLSXWRITER and not XLSXWRITER_AVAILABLE:
            raise ImportError("xlsxwriter not installed. Install with: pip install xlsxwriter")

    def export(self, data: Dict[str, Any], options: ExportOptions) -> Path:
        """
        Export data to Excel.

        Args:
            data: Data to export
            options: Export options

        Returns:
            Path to exported Excel file
        """
        self._validate_data(data)
        self._ensure_output_directory(options.output_path)

        logger.info(f"Exporting Excel using {self.engine} engine: {options.output_path}")

        # Add metadata
        if options.include_metadata:
            data = self._add_metadata(data)

        # Generate Excel based on engine
        if self.engine == ExcelEngine.OPENPYXL:
            self._export_openpyxl(data, options)
        elif self.engine == ExcelEngine.XLSXWRITER:
            self._export_xlsxwriter(data, options)
        else:
            raise ValueError(f"Unsupported Excel engine: {self.engine}")

        # Validate output
        if not self.validate_output(options.output_path):
            raise ValueError(f"Invalid Excel output: {options.output_path}")

        logger.info(f"Excel export completed: {options.output_path}")
        return options.output_path

    def _export_openpyxl(self, data: Dict[str, Any], options: ExportOptions):
        """
        Export using openpyxl.

        Args:
            data: Data to export
            options: Export options
        """
        # Create or load workbook
        if options.template_name and self.template_manager:
            template_path = self.template_manager.get_template(
                options.template_name, self.format_type
            )
            if template_path.exists() and template_path.suffix == '.xlsx':
                wb = load_workbook(str(template_path))
            else:
                wb = Workbook()
        else:
            wb = Workbook()

        # Remove default sheet if exists
        if 'Sheet' in wb.sheetnames:
            wb.remove(wb['Sheet'])

        # Create sheets
        self._create_summary_sheet_openpyxl(wb, data, options)
        self._create_configuration_sheet_openpyxl(wb, data, options)
        self._create_test_results_sheet_openpyxl(wb, data, options)

        if options.include_charts and "charts" in data:
            self._create_charts_sheet_openpyxl(wb, data, options)

        if "raw_data" in data:
            self._create_raw_data_sheet_openpyxl(wb, data, options)

        # Save workbook
        wb.save(str(options.output_path))

    def _create_summary_sheet_openpyxl(
        self,
        wb: 'Workbook',
        data: Dict[str, Any],
        options: ExportOptions
    ):
        """Create summary sheet using openpyxl."""
        ws = wb.create_sheet("Summary", 0)

        # Title
        ws['A1'] = data.get("title", "PV Test Report")
        ws['A1'].font = Font(size=18, bold=True, color="1F4788")
        ws.merge_cells('A1:D1')

        # Metadata
        row = 3
        if options.include_metadata and "_export_metadata" in data:
            ws[f'A{row}'] = "Document Information"
            ws[f'A{row}'].font = Font(size=14, bold=True, color="2D5AA0")
            row += 1

            metadata = data["_export_metadata"]
            for key, value in metadata.items():
                display_key = key.replace("_", " ").title()
                ws[f'A{row}'] = display_key
                ws[f'B{row}'] = str(value)
                ws[f'A{row}'].font = Font(bold=True)
                row += 1

            row += 1

        # Summary
        if "summary" in data:
            ws[f'A{row}'] = "Executive Summary"
            ws[f'A{row}'].font = Font(size=14, bold=True, color="2D5AA0")
            row += 1

            ws[f'A{row}'] = data["summary"]
            ws.merge_cells(f'A{row}:D{row}')
            ws[f'A{row}'].alignment = Alignment(wrap_text=True)
            row += 2

        # Test Statistics
        if "test_results" in data:
            test_results = data["test_results"]
            total_tests = len(test_results)
            passed_tests = sum(1 for t in test_results if t.get("status") == "PASS")
            failed_tests = total_tests - passed_tests

            ws[f'A{row}'] = "Test Statistics"
            ws[f'A{row}'].font = Font(size=14, bold=True, color="2D5AA0")
            row += 1

            stats = [
                ("Total Tests", total_tests),
                ("Passed", passed_tests),
                ("Failed", failed_tests),
                ("Pass Rate", f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
            ]

            for label, value in stats:
                ws[f'A{row}'] = label
                ws[f'B{row}'] = value
                ws[f'A{row}'].font = Font(bold=True)

                # Color code
                if label == "Passed" and passed_tests > 0:
                    ws[f'B{row}'].fill = PatternFill(start_color="C6EFCE", fill_type="solid")
                elif label == "Failed" and failed_tests > 0:
                    ws[f'B{row}'].fill = PatternFill(start_color="FFC7CE", fill_type="solid")

                row += 1

        # Set column widths
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 40
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 20

    def _create_configuration_sheet_openpyxl(
        self,
        wb: 'Workbook',
        data: Dict[str, Any],
        options: ExportOptions
    ):
        """Create configuration sheet using openpyxl."""
        if "configuration" not in data:
            return

        ws = wb.create_sheet("Configuration")

        # Title
        ws['A1'] = "Test Configuration"
        ws['A1'].font = Font(size=16, bold=True, color="1F4788")
        ws.merge_cells('A1:B1')

        # Headers
        ws['A3'] = "Parameter"
        ws['B3'] = "Value"
        self._apply_header_style(ws['A3'])
        self._apply_header_style(ws['B3'])

        # Configuration data
        row = 4
        configuration = data["configuration"]
        for key, value in configuration.items():
            display_key = key.replace("_", " ").title()
            ws[f'A{row}'] = display_key
            ws[f'B{row}'] = str(value)
            row += 1

        # Format as table
        self._apply_table_borders(ws, 3, row - 1, 1, 2)

        # Set column widths
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 40

    def _create_test_results_sheet_openpyxl(
        self,
        wb: 'Workbook',
        data: Dict[str, Any],
        options: ExportOptions
    ):
        """Create test results sheet using openpyxl."""
        if "test_results" not in data:
            return

        ws = wb.create_sheet("Test Results")

        # Title
        ws['A1'] = "Test Results"
        ws['A1'].font = Font(size=16, bold=True, color="1F4788")
        ws.merge_cells('A1:E1')

        # Headers
        headers = ["Test Name", "Status", "Value", "Expected", "Notes"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            self._apply_header_style(cell)

        # Test data
        row = 4
        for test in data["test_results"]:
            ws[f'A{row}'] = test.get("name", "N/A")
            ws[f'B{row}'] = test.get("status", "N/A")
            ws[f'C{row}'] = str(test.get("value", "N/A"))
            ws[f'D{row}'] = str(test.get("expected", "N/A"))
            ws[f'E{row}'] = test.get("notes", "")

            # Color code status
            status_cell = ws[f'B{row}']
            if test.get("status") == "PASS":
                status_cell.fill = PatternFill(start_color="C6EFCE", fill_type="solid")
                status_cell.font = Font(color="006100", bold=True)
            elif test.get("status") == "FAIL":
                status_cell.fill = PatternFill(start_color="FFC7CE", fill_type="solid")
                status_cell.font = Font(color="9C0006", bold=True)

            row += 1

        # Format as table
        self._apply_table_borders(ws, 3, row - 1, 1, 5)

        # Set column widths
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 12
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 40

        # Add auto-filter
        ws.auto_filter.ref = f"A3:E{row-1}"

        # Freeze panes
        ws.freeze_panes = "A4"

    def _create_charts_sheet_openpyxl(
        self,
        wb: 'Workbook',
        data: Dict[str, Any],
        options: ExportOptions
    ):
        """Create charts sheet using openpyxl."""
        if "test_results" not in data:
            return

        ws = wb.create_sheet("Charts")

        # Title
        ws['A1'] = "Charts and Graphs"
        ws['A1'].font = Font(size=16, bold=True, color="1F4788")

        # Create pass/fail pie chart
        test_results = data["test_results"]
        passed = sum(1 for t in test_results if t.get("status") == "PASS")
        failed = len(test_results) - passed

        # Data for chart
        ws['A3'] = "Status"
        ws['B3'] = "Count"
        ws['A4'] = "Passed"
        ws['B4'] = passed
        ws['A5'] = "Failed"
        ws['B5'] = failed

        # Create pie chart
        pie = PieChart()
        labels = Reference(ws, min_col=1, min_row=4, max_row=5)
        data_ref = Reference(ws, min_col=2, min_row=3, max_row=5)
        pie.add_data(data_ref, titles_from_data=True)
        pie.set_categories(labels)
        pie.title = "Test Results Distribution"
        ws.add_chart(pie, "D3")

        # Create test results bar chart if we have numeric values
        numeric_tests = [
            t for t in test_results
            if isinstance(t.get("value"), (int, float))
        ]

        if numeric_tests:
            chart_row = 20
            ws[f'A{chart_row}'] = "Test Name"
            ws[f'B{chart_row}'] = "Value"
            ws[f'C{chart_row}'] = "Expected"

            for idx, test in enumerate(numeric_tests[:10], 1):  # Limit to 10 tests
                row = chart_row + idx
                ws[f'A{row}'] = test.get("name", "N/A")
                ws[f'B{row}'] = test.get("value", 0)
                ws[f'C{row}'] = test.get("expected", 0)

            # Create bar chart
            bar = BarChart()
            bar.title = "Test Values vs Expected"
            bar.x_axis.title = "Tests"
            bar.y_axis.title = "Value"

            data_ref = Reference(ws, min_col=2, min_row=chart_row, max_row=chart_row + len(numeric_tests), max_col=3)
            cats = Reference(ws, min_col=1, min_row=chart_row + 1, max_row=chart_row + len(numeric_tests))

            bar.add_data(data_ref, titles_from_data=True)
            bar.set_categories(cats)
            ws.add_chart(bar, f"D{chart_row}")

    def _create_raw_data_sheet_openpyxl(
        self,
        wb: 'Workbook',
        data: Dict[str, Any],
        options: ExportOptions
    ):
        """Create raw data sheet using openpyxl."""
        if "raw_data" not in data:
            return

        ws = wb.create_sheet("Raw Data")

        # Title
        ws['A1'] = "Raw Data"
        ws['A1'].font = Font(size=16, bold=True, color="1F4788")

        # Add raw data
        raw_data = data["raw_data"]
        if isinstance(raw_data, list) and raw_data:
            # Assume list of dictionaries
            if isinstance(raw_data[0], dict):
                headers = list(raw_data[0].keys())

                # Headers
                for col, header in enumerate(headers, 1):
                    cell = ws.cell(row=3, column=col, value=header)
                    self._apply_header_style(cell)

                # Data rows
                for row_idx, item in enumerate(raw_data, 4):
                    for col_idx, header in enumerate(headers, 1):
                        ws.cell(row=row_idx, column=col_idx, value=str(item.get(header, "")))

                # Format as table
                self._apply_table_borders(ws, 3, len(raw_data) + 3, 1, len(headers))

                # Auto-fit columns
                for col in range(1, len(headers) + 1):
                    ws.column_dimensions[get_column_letter(col)].width = 20

    def _export_xlsxwriter(self, data: Dict[str, Any], options: ExportOptions):
        """
        Export using xlsxwriter.

        Args:
            data: Data to export
            options: Export options
        """
        workbook = xlsxwriter.Workbook(str(options.output_path))

        # Define formats
        formats = self._create_formats_xlsxwriter(workbook)

        # Create sheets
        self._create_summary_sheet_xlsxwriter(workbook, data, options, formats)
        self._create_test_results_sheet_xlsxwriter(workbook, data, options, formats)

        workbook.close()

    def _create_formats_xlsxwriter(self, workbook: 'xlsxwriter.Workbook') -> Dict[str, Any]:
        """Create cell formats for xlsxwriter."""
        return {
            'title': workbook.add_format({
                'bold': True,
                'font_size': 18,
                'font_color': '#1F4788',
                'align': 'center',
                'valign': 'vcenter'
            }),
            'header': workbook.add_format({
                'bold': True,
                'bg_color': '#1F4788',
                'font_color': 'white',
                'align': 'center',
                'valign': 'vcenter',
                'border': 1
            }),
            'pass': workbook.add_format({
                'bg_color': '#C6EFCE',
                'font_color': '#006100',
                'bold': True
            }),
            'fail': workbook.add_format({
                'bg_color': '#FFC7CE',
                'font_color': '#9C0006',
                'bold': True
            }),
            'bold': workbook.add_format({'bold': True}),
            'wrap': workbook.add_format({'text_wrap': True}),
        }

    def _create_summary_sheet_xlsxwriter(
        self,
        workbook: 'xlsxwriter.Workbook',
        data: Dict[str, Any],
        options: ExportOptions,
        formats: Dict[str, Any]
    ):
        """Create summary sheet using xlsxwriter."""
        worksheet = workbook.add_worksheet("Summary")

        # Title
        worksheet.merge_range('A1:D1', data.get("title", "PV Test Report"), formats['title'])

        # Set column widths
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 40)

    def _create_test_results_sheet_xlsxwriter(
        self,
        workbook: 'xlsxwriter.Workbook',
        data: Dict[str, Any],
        options: ExportOptions,
        formats: Dict[str, Any]
    ):
        """Create test results sheet using xlsxwriter."""
        if "test_results" not in data:
            return

        worksheet = workbook.add_worksheet("Test Results")

        # Headers
        headers = ["Test Name", "Status", "Value", "Expected"]
        for col, header in enumerate(headers):
            worksheet.write(2, col, header, formats['header'])

        # Data
        for row_idx, test in enumerate(data["test_results"], 3):
            worksheet.write(row_idx, 0, test.get("name", "N/A"))

            # Status with formatting
            status = test.get("status", "N/A")
            status_format = formats['pass'] if status == "PASS" else formats['fail']
            worksheet.write(row_idx, 1, status, status_format)

            worksheet.write(row_idx, 2, str(test.get("value", "N/A")))
            worksheet.write(row_idx, 3, str(test.get("expected", "N/A")))

        # Set column widths
        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:B', 12)
        worksheet.set_column('C:D', 15)

    def _apply_header_style(self, cell):
        """Apply header style to cell."""
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="1F4788", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")

    def _apply_table_borders(self, ws, min_row: int, max_row: int, min_col: int, max_col: int):
        """Apply borders to table range."""
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        for row in range(min_row, max_row + 1):
            for col in range(min_col, max_col + 1):
                ws.cell(row=row, column=col).border = thin_border

    def validate_output(self, output_path: Path) -> bool:
        """
        Validate Excel output.

        Args:
            output_path: Path to Excel file

        Returns:
            True if valid
        """
        if not output_path.exists():
            return False

        if output_path.stat().st_size == 0:
            return False

        try:
            # Try to load workbook
            if OPENPYXL_AVAILABLE:
                wb = load_workbook(str(output_path))
                if len(wb.sheetnames) == 0:
                    return False
            return True
        except Exception as e:
            logger.error(f"Excel validation failed: {e}")
            return False

    def add_data_validation(
        self,
        excel_path: Path,
        sheet_name: str,
        cell_range: str,
        validation_type: str,
        formula: str
    ):
        """
        Add data validation to cells.

        Args:
            excel_path: Excel file path
            sheet_name: Sheet name
            cell_range: Cell range (e.g., 'A1:A10')
            validation_type: Validation type
            formula: Validation formula
        """
        if not OPENPYXL_AVAILABLE:
            logger.warning("openpyxl not available")
            return

        wb = load_workbook(str(excel_path))
        ws = wb[sheet_name]

        dv = DataValidation(type=validation_type, formula1=formula)
        ws.add_data_validation(dv)
        dv.add(cell_range)

        wb.save(str(excel_path))
        logger.info(f"Data validation added to {cell_range}")
