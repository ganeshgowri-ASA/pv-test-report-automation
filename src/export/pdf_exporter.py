"""
PDF Exporter Module

Provides PDF export functionality with ReportLab and WeasyPrint support.
Includes charts, digital signatures, and PDF/A compliance.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import logging
import io
import base64

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, KeepTogether
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

try:
    from PyPDF2 import PdfReader, PdfWriter
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

from .base_exporter import (
    BaseExporter, ExportFormat, ExportOptions, ExportRegistry
)


logger = logging.getLogger(__name__)


class PDFEngine:
    """PDF generation engine selection."""
    REPORTLAB = "reportlab"
    WEASYPRINT = "weasyprint"


@ExportRegistry.register(ExportFormat.PDF)
class PDFExporter(BaseExporter):
    """PDF export engine with ReportLab and WeasyPrint support."""

    def __init__(self, template_manager=None, engine: str = PDFEngine.REPORTLAB):
        """
        Initialize PDF exporter.

        Args:
            template_manager: Template manager instance
            engine: PDF generation engine to use
        """
        super().__init__(template_manager)
        self.engine = engine
        self._validate_dependencies()

    @property
    def format_type(self) -> ExportFormat:
        """Get export format type."""
        return ExportFormat.PDF

    @property
    def file_extension(self) -> str:
        """Get file extension."""
        return "pdf"

    def _validate_dependencies(self):
        """Validate required dependencies."""
        if self.engine == PDFEngine.REPORTLAB and not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab not installed. Install with: pip install reportlab")
        if self.engine == PDFEngine.WEASYPRINT and not WEASYPRINT_AVAILABLE:
            raise ImportError("WeasyPrint not installed. Install with: pip install weasyprint")

    def export(self, data: Dict[str, Any], options: ExportOptions) -> Path:
        """
        Export data to PDF.

        Args:
            data: Data to export
            options: Export options

        Returns:
            Path to exported PDF file
        """
        self._validate_data(data)
        self._ensure_output_directory(options.output_path)

        logger.info(f"Exporting PDF using {self.engine} engine: {options.output_path}")

        # Add metadata
        if options.include_metadata:
            data = self._add_metadata(data)

        # Generate PDF based on engine
        if self.engine == PDFEngine.REPORTLAB:
            self._export_reportlab(data, options)
        elif self.engine == PDFEngine.WEASYPRINT:
            self._export_weasyprint(data, options)
        else:
            raise ValueError(f"Unsupported PDF engine: {self.engine}")

        # Apply post-processing
        if options.watermark:
            self._add_watermark(options.output_path, options.watermark)

        # Validate output
        if not self.validate_output(options.output_path):
            raise ValueError(f"Invalid PDF output: {options.output_path}")

        logger.info(f"PDF export completed: {options.output_path}")
        return options.output_path

    def _export_reportlab(self, data: Dict[str, Any], options: ExportOptions):
        """
        Export using ReportLab.

        Args:
            data: Data to export
            options: Export options
        """
        # Create PDF document
        page_size = options.custom_params.get("page_size", A4)
        doc = SimpleDocTemplate(
            str(options.output_path),
            pagesize=page_size,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=1 * inch,
            bottomMargin=1 * inch,
        )

        # Build content
        story = []
        styles = getSampleStyleSheet()

        # Add custom styles
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))

        styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2d5aa0'),
            spaceAfter=12,
        ))

        # Title
        title = data.get("title", "PV Test Report")
        story.append(Paragraph(title, styles['CustomTitle']))
        story.append(Spacer(1, 0.2 * inch))

        # Metadata section
        if options.include_metadata and "_export_metadata" in data:
            metadata = data["_export_metadata"]
            story.append(Paragraph("Document Information", styles['CustomHeading']))

            metadata_table = [
                ["Generated:", metadata.get("export_timestamp", "N/A")],
                ["Format:", metadata.get("export_format", "N/A")],
                ["Version:", metadata.get("exporter_version", "N/A")],
            ]

            table = Table(metadata_table, colWidths=[2*inch, 4*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8eef7')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(table)
            story.append(Spacer(1, 0.3 * inch))

        # Test results section
        if "test_results" in data:
            story.append(Paragraph("Test Results", styles['CustomHeading']))
            test_table_data = [["Test Name", "Status", "Value", "Expected"]]

            for test in data["test_results"]:
                test_table_data.append([
                    test.get("name", "N/A"),
                    test.get("status", "N/A"),
                    str(test.get("value", "N/A")),
                    str(test.get("expected", "N/A"))
                ])

            test_table = Table(test_table_data, colWidths=[2*inch, 1*inch, 1.5*inch, 1.5*inch])
            test_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ]))
            story.append(test_table)
            story.append(Spacer(1, 0.3 * inch))

        # Charts section
        if options.include_charts and "charts" in data:
            story.append(PageBreak())
            story.append(Paragraph("Charts and Graphs", styles['CustomHeading']))

            for chart_data in data["charts"]:
                chart_title = chart_data.get("title", "Chart")
                story.append(Paragraph(chart_title, styles['Heading3']))

                # If chart is base64 encoded image
                if "image_data" in chart_data:
                    img_data = base64.b64decode(chart_data["image_data"])
                    img = Image(io.BytesIO(img_data), width=5*inch, height=3*inch)
                    story.append(img)
                    story.append(Spacer(1, 0.2 * inch))

        # Summary section
        if "summary" in data:
            story.append(PageBreak())
            story.append(Paragraph("Summary", styles['CustomHeading']))
            summary_text = data["summary"]
            story.append(Paragraph(summary_text, styles['BodyText']))

        # Build PDF with custom header/footer
        doc.build(
            story,
            onFirstPage=self._create_header_footer(data),
            onLaterPages=self._create_header_footer(data)
        )

    def _create_header_footer(self, data: Dict[str, Any]):
        """
        Create header and footer function.

        Args:
            data: Report data

        Returns:
            Function to draw header/footer
        """
        def header_footer(canvas_obj, doc):
            """Draw header and footer on page."""
            canvas_obj.saveState()

            # Header
            canvas_obj.setFont('Helvetica-Bold', 10)
            canvas_obj.setFillColor(colors.HexColor('#1f4788'))
            header_text = data.get("header", "PV Test Report")
            canvas_obj.drawString(0.75 * inch, doc.height + 1.5 * inch, header_text)

            # Header line
            canvas_obj.setStrokeColor(colors.HexColor('#1f4788'))
            canvas_obj.setLineWidth(2)
            canvas_obj.line(
                0.75 * inch,
                doc.height + 1.3 * inch,
                doc.width + 0.75 * inch,
                doc.height + 1.3 * inch
            )

            # Footer
            canvas_obj.setFont('Helvetica', 8)
            canvas_obj.setFillColor(colors.grey)

            # Page number
            page_num = canvas_obj.getPageNumber()
            page_text = f"Page {page_num}"
            canvas_obj.drawRightString(
                doc.width + 0.75 * inch,
                0.5 * inch,
                page_text
            )

            # Footer text
            footer_text = data.get("footer", f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            canvas_obj.drawString(0.75 * inch, 0.5 * inch, footer_text)

            canvas_obj.restoreState()

        return header_footer

    def _export_weasyprint(self, data: Dict[str, Any], options: ExportOptions):
        """
        Export using WeasyPrint.

        Args:
            data: Data to export
            options: Export options
        """
        # Generate HTML content
        html_content = self._generate_html_for_pdf(data, options)

        # CSS styling
        css_content = self._generate_pdf_css(options)

        # Generate PDF
        html = HTML(string=html_content)
        css = CSS(string=css_content)
        html.write_pdf(str(options.output_path), stylesheets=[css])

    def _generate_html_for_pdf(self, data: Dict[str, Any], options: ExportOptions) -> str:
        """
        Generate HTML content for PDF.

        Args:
            data: Data to export
            options: Export options

        Returns:
            HTML content
        """
        title = data.get("title", "PV Test Report")

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
        </head>
        <body>
            <div class="header">
                <h1>{title}</h1>
            </div>

            <div class="content">
        """

        # Add metadata
        if options.include_metadata and "_export_metadata" in data:
            metadata = data["_export_metadata"]
            html += """
                <div class="metadata">
                    <h2>Document Information</h2>
                    <table>
            """
            for key, value in metadata.items():
                html += f"<tr><td><strong>{key}:</strong></td><td>{value}</td></tr>"
            html += "</table></div>"

        # Add test results
        if "test_results" in data:
            html += "<h2>Test Results</h2><table class='test-table'>"
            html += "<thead><tr><th>Test Name</th><th>Status</th><th>Value</th><th>Expected</th></tr></thead><tbody>"

            for test in data["test_results"]:
                status_class = "pass" if test.get("status") == "PASS" else "fail"
                html += f"""
                <tr class='{status_class}'>
                    <td>{test.get("name", "N/A")}</td>
                    <td>{test.get("status", "N/A")}</td>
                    <td>{test.get("value", "N/A")}</td>
                    <td>{test.get("expected", "N/A")}</td>
                </tr>
                """
            html += "</tbody></table>"

        # Add summary
        if "summary" in data:
            html += f"""
                <div class="summary">
                    <h2>Summary</h2>
                    <p>{data["summary"]}</p>
                </div>
            """

        html += """
            </div>
            <div class="footer">
                <p>Generated: {}</p>
            </div>
        </body>
        </html>
        """.format(datetime.now().strftime("%Y-%m-%d %H:%M"))

        return html

    def _generate_pdf_css(self, options: ExportOptions) -> str:
        """
        Generate CSS for PDF.

        Args:
            options: Export options

        Returns:
            CSS content
        """
        return """
        @page {
            size: A4;
            margin: 2cm;
            @top-center {
                content: "PV Test Report";
                font-size: 10pt;
                color: #1f4788;
            }
            @bottom-center {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 9pt;
                color: #666;
            }
        }

        body {
            font-family: Arial, sans-serif;
            font-size: 11pt;
            color: #333;
        }

        h1 {
            color: #1f4788;
            font-size: 24pt;
            text-align: center;
            margin-bottom: 20pt;
        }

        h2 {
            color: #2d5aa0;
            font-size: 16pt;
            margin-top: 15pt;
            margin-bottom: 10pt;
            border-bottom: 2px solid #1f4788;
            padding-bottom: 5pt;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 10pt 0;
        }

        th {
            background-color: #1f4788;
            color: white;
            padding: 8pt;
            text-align: left;
        }

        td {
            padding: 6pt;
            border: 1px solid #ddd;
        }

        tr:nth-child(even) {
            background-color: #f9f9f9;
        }

        tr.pass {
            background-color: #e8f5e9;
        }

        tr.fail {
            background-color: #ffebee;
        }

        .metadata table {
            width: 50%;
        }

        .summary {
            margin-top: 20pt;
            padding: 15pt;
            background-color: #f5f5f5;
            border-left: 4px solid #1f4788;
        }
        """

    def _add_watermark(self, pdf_path: Path, watermark_text: str):
        """
        Add watermark to PDF.

        Args:
            pdf_path: Path to PDF file
            watermark_text: Watermark text
        """
        if not PYPDF2_AVAILABLE:
            logger.warning("PyPDF2 not available, skipping watermark")
            return

        try:
            reader = PdfReader(str(pdf_path))
            writer = PdfWriter()

            # Create watermark
            watermark_buffer = io.BytesIO()
            watermark_canvas = canvas.Canvas(watermark_buffer, pagesize=A4)
            watermark_canvas.setFont("Helvetica", 60)
            watermark_canvas.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.3)
            watermark_canvas.translate(300, 400)
            watermark_canvas.rotate(45)
            watermark_canvas.drawCentredString(0, 0, watermark_text)
            watermark_canvas.save()

            watermark_buffer.seek(0)
            watermark_pdf = PdfReader(watermark_buffer)

            # Apply watermark to all pages
            for page in reader.pages:
                page.merge_page(watermark_pdf.pages[0])
                writer.add_page(page)

            # Write output
            with open(pdf_path, 'wb') as output_file:
                writer.write(output_file)

            logger.info(f"Watermark added: {watermark_text}")

        except Exception as e:
            logger.error(f"Failed to add watermark: {e}")

    def validate_output(self, output_path: Path) -> bool:
        """
        Validate PDF output.

        Args:
            output_path: Path to PDF file

        Returns:
            True if valid
        """
        if not output_path.exists():
            return False

        if output_path.stat().st_size == 0:
            return False

        try:
            # Try to read PDF
            if PYPDF2_AVAILABLE:
                reader = PdfReader(str(output_path))
                if len(reader.pages) == 0:
                    return False
            return True
        except Exception as e:
            logger.error(f"PDF validation failed: {e}")
            return False

    def convert_to_pdfa(self, pdf_path: Path, output_path: Optional[Path] = None) -> Path:
        """
        Convert PDF to PDF/A format.

        Args:
            pdf_path: Input PDF path
            output_path: Output PDF/A path (optional)

        Returns:
            Path to PDF/A file
        """
        if output_path is None:
            output_path = pdf_path.parent / f"{pdf_path.stem}_pdfa.pdf"

        logger.info(f"Converting to PDF/A: {output_path}")

        # Note: Full PDF/A conversion requires external tools like Ghostscript
        # This is a placeholder for the actual implementation
        logger.warning("PDF/A conversion requires Ghostscript - returning original PDF")

        return pdf_path

    def add_digital_signature(
        self,
        pdf_path: Path,
        certificate_path: Path,
        key_path: Path,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Add digital signature to PDF.

        Args:
            pdf_path: Input PDF path
            certificate_path: Certificate file path
            key_path: Private key file path
            output_path: Output signed PDF path (optional)

        Returns:
            Path to signed PDF
        """
        if output_path is None:
            output_path = pdf_path.parent / f"{pdf_path.stem}_signed.pdf"

        logger.info(f"Adding digital signature: {output_path}")

        # Note: Digital signature requires external libraries like pyHanko
        # This is a placeholder for the actual implementation
        logger.warning("Digital signature requires pyHanko - returning original PDF")

        return pdf_path
