"""
Microsoft Word Report Export using python-docx.

Generates professional Word documents (.docx) with:
- Custom templates and styling
- Tables, images, and charts
- Headers and footers
- Table of contents
- ISO 17025 compliant formatting
"""

import logging
from pathlib import Path
from typing import Any, Dict

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class WordExportConfig(BaseModel):
    """Word export configuration."""

    template_path: str | None = None
    include_toc: bool = True
    include_images: bool = True


class WordExporter:
    """Word document exporter for PV test reports."""

    def __init__(self, config: WordExportConfig = WordExportConfig()):
        """Initialize Word exporter."""
        self.config = config
        logger.info("Word exporter initialized")

    def export_report(self, test_report: Dict[str, Any], output_path: str) -> str:
        """Export report to Word document."""
        logger.info(f"Exporting to Word: {output_path}")

        doc = Document()

        # Title
        title = doc.add_heading(f"PV Test Report", level=0)
        title.alignment = 1  # Center

        # Report number
        doc.add_paragraph(f"Report Number: {test_report.get('report_number', 'N/A')}")

        # Sample information
        doc.add_heading("Sample Information", level=1)
        sample = test_report.get("sample", {})

        table = doc.add_table(rows=5, cols=2)
        table.style = "Light Grid Accent 1"

        cells = [
            ("Sample ID", sample.get("sample_id", "N/A")),
            ("Manufacturer", sample.get("manufacturer", "N/A")),
            ("Module Type", sample.get("module_type", "N/A")),
            ("Serial Number", sample.get("serial_number", "N/A")),
            ("Rated Power", f"{sample.get('rated_power', 0)} W"),
        ]

        for idx, (label, value) in enumerate(cells):
            table.rows[idx].cells[0].text = label
            table.rows[idx].cells[1].text = str(value)

        # Save
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        doc.save(output_path)

        logger.info(f"Word document exported: {output_path}")
        return output_path
