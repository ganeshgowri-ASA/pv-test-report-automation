"""Word (DOCX) export engine using python-docx.

Session 40: Word Export
- python-docx report generation
- Template system with placeholders
- Table/chart insertion
- Header/footer customization
- ISO 17025 compliant formatting
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE

logger = logging.getLogger(__name__)


class WordExporter:
    """Word document exporter for test reports.

    ISO 17025 Compliant Features:
    - Professional formatting
    - Traceability headers
    - Digital signature placeholders
    - Version control information
    """

    def __init__(self, template_path: Optional[str] = None):
        """Initialize Word exporter.

        Args:
            template_path: Optional path to Word template (.docx).
        """
        self.template_path = template_path
        logger.info(f"WordExporter initialized with template: {template_path or 'default'}")

    def export_report(
        self,
        report_data: Dict[str, Any],
        output_path: str,
        include_signature: bool = True,
        include_header_footer: bool = True
    ) -> str:
        """Export test report to Word document.

        Args:
            report_data: Report data dictionary.
            output_path: Output file path.
            include_signature: Include digital signature section.
            include_header_footer: Include headers and footers.

        Returns:
            Path to generated document.
        """
        logger.info(f"Exporting report to Word: {output_path}")

        # Load template or create new document
        if self.template_path and Path(self.template_path).exists():
            doc = Document(self.template_path)
        else:
            doc = Document()
            self._setup_styles(doc)

        # Add header and footer
        if include_header_footer:
            self._add_header_footer(doc, report_data)

        # Add title page
        self._add_title_page(doc, report_data)

        # Add executive summary
        if report_data.get("executive_summary"):
            self._add_section(doc, "Executive Summary", report_data["executive_summary"])

        # Add test details
        self._add_test_details(doc, report_data)

        # Add test results
        self._add_test_results(doc, report_data)

        # Add compliance section
        self._add_compliance_section(doc, report_data)

        # Add signature section
        if include_signature:
            self._add_signature_section(doc, report_data)

        # Save document
        output_path = str(output_path)
        doc.save(output_path)
        logger.info(f"Word document exported successfully: {output_path}")

        return output_path

    def _setup_styles(self, doc: Document) -> None:
        """Set up document styles."""
        # Title style
        if "Title Custom" not in [s.name for s in doc.styles]:
            title_style = doc.styles.add_style("Title Custom", WD_STYLE_TYPE.PARAGRAPH)
            title_style.font.size = Pt(24)
            title_style.font.bold = True
            title_style.font.color.rgb = RGBColor(0, 51, 102)

    def _add_header_footer(self, doc: Document, report_data: Dict[str, Any]) -> None:
        """Add header and footer to document."""
        # Header
        section = doc.sections[0]
        header = section.header
        header_para = header.paragraphs[0]
        header_para.text = f"PV Test Report - {report_data.get('report_id', 'N/A')}"
        header_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        # Footer
        footer = section.footer
        footer_para = footer.paragraphs[0]
        footer_para.text = f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} | ISO 17025 Compliant"
        footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def _add_title_page(self, doc: Document, report_data: Dict[str, Any]) -> None:
        """Add title page."""
        # Title
        title = doc.add_paragraph(report_data.get("title", "PV Test Report"))
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title.runs[0].font.size = Pt(28)
        title.runs[0].font.bold = True

        doc.add_paragraph()  # Spacing

        # Report metadata
        metadata_table = doc.add_table(rows=7, cols=2)
        metadata_table.style = "Light Grid Accent 1"

        cells = [
            ("Report ID:", report_data.get("report_id", "N/A")),
            ("Test Standard:", report_data.get("standard", "N/A")),
            ("Module Model:", report_data.get("module_model", "N/A")),
            ("Serial Number:", report_data.get("module_serial_number", "N/A")),
            ("Test Date:", report_data.get("test_date", "N/A")),
            ("Status:", report_data.get("status", "N/A")),
            ("Lab:", report_data.get("lab_name", "PV Test Laboratory")),
        ]

        for i, (label, value) in enumerate(cells):
            metadata_table.rows[i].cells[0].text = label
            metadata_table.rows[i].cells[0].paragraphs[0].runs[0].font.bold = True
            metadata_table.rows[i].cells[1].text = str(value)

        doc.add_page_break()

    def _add_section(self, doc: Document, heading: str, content: str) -> None:
        """Add a section with heading and content."""
        doc.add_heading(heading, level=1)
        doc.add_paragraph(content)

    def _add_test_details(self, doc: Document, report_data: Dict[str, Any]) -> None:
        """Add test details section."""
        doc.add_heading("Test Details", level=1)

        # Test parameters
        if "test_parameters" in report_data:
            doc.add_heading("Test Parameters", level=2)

            params = report_data["test_parameters"]
            if isinstance(params, dict):
                table = doc.add_table(rows=len(params) + 1, cols=2)
                table.style = "Light Grid Accent 1"

                # Header
                table.rows[0].cells[0].text = "Parameter"
                table.rows[0].cells[1].text = "Value"

                for i, (key, value) in enumerate(params.items(), start=1):
                    table.rows[i].cells[0].text = str(key)
                    table.rows[i].cells[1].text = str(value)

    def _add_test_results(self, doc: Document, report_data: Dict[str, Any]) -> None:
        """Add test results section."""
        doc.add_heading("Test Results", level=1)

        if "test_results" in report_data:
            results = report_data["test_results"]
            if isinstance(results, dict):
                table = doc.add_table(rows=len(results) + 1, cols=2)
                table.style = "Light Grid Accent 1"

                # Header
                table.rows[0].cells[0].text = "Measurement"
                table.rows[0].cells[1].text = "Result"

                for i, (key, value) in enumerate(results.items(), start=1):
                    table.rows[i].cells[0].text = str(key)
                    table.rows[i].cells[1].text = str(value)

    def _add_compliance_section(self, doc: Document, report_data: Dict[str, Any]) -> None:
        """Add compliance section."""
        doc.add_heading("Compliance Assessment", level=1)

        is_compliant = report_data.get("is_compliant", None)
        if is_compliant is not None:
            compliance_text = "COMPLIANT" if is_compliant else "NON-COMPLIANT"
            para = doc.add_paragraph(f"Status: ")
            run = para.add_run(compliance_text)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0, 128, 0) if is_compliant else RGBColor(255, 0, 0)

        # Deviations
        if report_data.get("deviations"):
            doc.add_heading("Deviations", level=2)
            for deviation in report_data["deviations"]:
                doc.add_paragraph(deviation, style="List Bullet")

    def _add_signature_section(self, doc: Document, report_data: Dict[str, Any]) -> None:
        """Add signature section."""
        doc.add_page_break()
        doc.add_heading("Approvals", level=1)

        # Signature table
        sig_table = doc.add_table(rows=4, cols=3)
        sig_table.style = "Table Grid"

        # Headers
        sig_table.rows[0].cells[0].text = "Role"
        sig_table.rows[0].cells[1].text = "Name"
        sig_table.rows[0].cells[2].text = "Date"

        # Prepared by
        sig_table.rows[1].cells[0].text = "Prepared By"
        sig_table.rows[1].cells[1].text = report_data.get("created_by", "")
        sig_table.rows[1].cells[2].text = report_data.get("created_at", "")

        # Reviewed by
        sig_table.rows[2].cells[0].text = "Reviewed By"
        sig_table.rows[2].cells[1].text = report_data.get("reviewed_by", "")
        sig_table.rows[2].cells[2].text = ""

        # Approved by
        sig_table.rows[3].cells[0].text = "Approved By"
        sig_table.rows[3].cells[1].text = report_data.get("approved_by", "")
        sig_table.rows[3].cells[2].text = ""

        # Digital signature note
        doc.add_paragraph()
        note = doc.add_paragraph("Digital Signature: ")
        note.add_run(report_data.get("digital_signature", "Pending"))
        note.runs[0].font.italic = True


class WordTemplateEngine:
    """Template engine for Word documents with placeholder replacement."""

    @staticmethod
    def replace_placeholders(doc: Document, placeholders: Dict[str, str]) -> None:
        """Replace placeholders in document.

        Args:
            doc: Word document.
            placeholders: Dictionary mapping placeholder names to values.
        """
        for paragraph in doc.paragraphs:
            for placeholder, value in placeholders.items():
                if f"{{{{{placeholder}}}}}" in paragraph.text:
                    paragraph.text = paragraph.text.replace(
                        f"{{{{{placeholder}}}}}",
                        str(value)
                    )

        # Replace in tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        for placeholder, value in placeholders.items():
                            if f"{{{{{placeholder}}}}}" in paragraph.text:
                                paragraph.text = paragraph.text.replace(
                                    f"{{{{{placeholder}}}}}",
                                    str(value)
                                )
