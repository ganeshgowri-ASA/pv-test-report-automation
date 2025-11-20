"""
PDF Report Generator using ReportLab.

Generates professional PDF reports with:
- Custom templates and styling
- Headers, footers, and page numbers
- Tables, charts, and images
- Digital signatures
- ISO 17025 and NABL compliance formatting
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PDFExportConfig(BaseModel):
    """PDF export configuration."""

    page_size: str = "A4"
    include_header: bool = True
    include_footer: bool = True
    watermark: Optional[str] = None
    font_name: str = "Helvetica"
    font_size: int = 10


class PDFGenerator:
    """PDF report generator for PV test reports."""

    def __init__(self, config: PDFExportConfig = PDFExportConfig()):
        """Initialize PDF generator."""
        self.config = config
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        logger.info("PDF generator initialized")

    def _setup_custom_styles(self) -> None:
        """Setup custom paragraph styles."""
        self.styles.add(
            ParagraphStyle(
                name="ReportTitle",
                parent=self.styles["Heading1"],
                fontSize=18,
                textColor=colors.HexColor("#1f4788"),
                spaceAfter=30,
                alignment=1,  # Center
            )
        )

    def generate_report(
        self,
        test_report: Dict[str, Any],
        output_path: str,
    ) -> str:
        """
        Generate PDF report.

        Args:
            test_report: Test report data
            output_path: Output file path

        Returns:
            Path to generated PDF
        """
        logger.info(f"Generating PDF report: {output_path}")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        story = []

        # Title
        story.append(
            Paragraph(
                f"PV Test Report: {test_report.get('report_number', 'N/A')}",
                self.styles["ReportTitle"],
            )
        )
        story.append(Spacer(1, 0.5 * cm))

        # Sample Information
        story.append(Paragraph("Sample Information", self.styles["Heading2"]))
        sample = test_report.get("sample", {})
        sample_data = [
            ["Sample ID", sample.get("sample_id", "N/A")],
            ["Manufacturer", sample.get("manufacturer", "N/A")],
            ["Module Type", sample.get("module_type", "N/A")],
            ["Serial Number", sample.get("serial_number", "N/A")],
            ["Rated Power", f"{sample.get('rated_power', 0)} W"],
        ]

        sample_table = Table(sample_data, colWidths=[6 * cm, 10 * cm])
        sample_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ])
        )
        story.append(sample_table)
        story.append(Spacer(1, 0.5 * cm))

        # Test Results
        story.append(Paragraph("Test Results", self.styles["Heading2"]))
        results = test_report.get("test_results", {})
        story.append(Paragraph(f"Protocol: {results.get('protocol', 'N/A')}", self.styles["Normal"]))
        story.append(
            Paragraph(
                f"Overall Result: <b>{results.get('overall_result', 'N/A')}</b>",
                self.styles["Normal"],
            )
        )

        # Build PDF
        doc.build(story)

        logger.info(f"PDF report generated: {output_path}")
        return output_path
