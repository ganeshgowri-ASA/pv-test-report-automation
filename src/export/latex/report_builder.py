"""
Report builder that orchestrates the complete LaTeX report generation pipeline.

Features:
- Load and validate test data
- Generate charts and graphs
- Populate LaTeX templates
- Compile to PDF
- Add watermarks for draft reports
- Custom branding support
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from src.models.test_data import (
    TestReport, ChartData, BrandingConfig, TestResult
)
from src.export.latex.template_engine import LaTeXTemplateEngine
from src.export.latex.pdf_compiler import PDFCompiler, LaTeXEngine

logger = logging.getLogger(__name__)

# Set default style for plots
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['figure.dpi'] = 150


class ReportBuilder:
    """
    Orchestrate LaTeX report generation from test data to final PDF.

    Pipeline:
    1. Load and validate test data
    2. Generate charts/graphs as images
    3. Populate LaTeX template
    4. Compile to PDF
    5. Add watermarks (optional)
    6. Apply custom branding
    """

    def __init__(
        self,
        template_dir: Optional[str] = None,
        output_dir: Optional[str] = None,
        latex_engine: LaTeXEngine = LaTeXEngine.PDFLATEX,
        branding: Optional[BrandingConfig] = None
    ):
        """
        Initialize report builder.

        Args:
            template_dir: Directory containing LaTeX templates
            output_dir: Directory for output files
            latex_engine: LaTeX engine to use
            branding: Custom branding configuration
        """
        # Set template directory
        if template_dir is None:
            # Default to templates in this package
            template_dir = Path(__file__).parent / 'templates'

        self.template_dir = Path(template_dir)

        if not self.template_dir.exists():
            raise ValueError(f"Template directory not found: {template_dir}")

        # Set output directory
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.template_engine = LaTeXTemplateEngine(str(self.template_dir))
        self.pdf_compiler = PDFCompiler(engine=latex_engine, cleanup=True)

        # Branding configuration
        self.branding = branding or BrandingConfig()

        logger.info(f"ReportBuilder initialized with template_dir={self.template_dir}")

    def generate_report(
        self,
        test_report: TestReport,
        template_name: str = "iec_61215_report.tex",
        output_filename: Optional[str] = None
    ) -> str:
        """
        Generate complete PDF report from test data.

        Args:
            test_report: Test report data
            template_name: Name of LaTeX template to use
            output_filename: Output PDF filename (auto-generated if None)

        Returns:
            Path to generated PDF file
        """
        logger.info(f"Generating report {test_report.metadata.report_number}")

        # Generate output filename if not provided
        if output_filename is None:
            output_filename = f"{test_report.metadata.report_number}.pdf"

        output_path = self.output_dir / output_filename

        # Create temporary directory for work files
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Step 1: Generate charts and save to temp directory
            chart_files = self._generate_charts(
                test_report.charts,
                tmpdir_path
            )

            # Step 2: Prepare template context
            context = self._prepare_context(
                test_report,
                chart_files,
                tmpdir_path
            )

            # Step 3: Render LaTeX template
            latex_content = self.template_engine.render_template(
                template_name,
                context,
                escape_all=False  # We'll handle escaping in the template
            )

            # Step 4: Write LaTeX to temp file
            tex_file = tmpdir_path / "report.tex"
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)

            logger.debug(f"LaTeX file written to {tex_file}")

            # Step 5: Compile to PDF
            try:
                pdf_data = self.pdf_compiler.compile(
                    str(tex_file),
                    passes=2  # Two passes for TOC and references
                )
            except Exception as e:
                logger.error(f"PDF compilation failed: {e}")
                # Save LaTeX file for debugging
                debug_tex = self.output_dir / f"{output_filename}.debug.tex"
                with open(debug_tex, 'w', encoding='utf-8') as f:
                    f.write(latex_content)
                logger.info(f"LaTeX source saved to {debug_tex} for debugging")
                raise

            # Step 6: Add watermark if draft
            if test_report.metadata.is_draft:
                pdf_data = self._add_watermark(
                    pdf_data,
                    watermark_text=self.branding.watermark_text or "DRAFT"
                )

            # Step 7: Write final PDF
            with open(output_path, 'wb') as f:
                f.write(pdf_data)

        logger.info(f"Report generated successfully: {output_path}")

        return str(output_path)

    def _generate_charts(
        self,
        charts: List[ChartData],
        output_dir: Path
    ) -> List[Dict[str, str]]:
        """
        Generate chart images from chart data.

        Args:
            charts: List of chart data
            output_dir: Directory to save chart images

        Returns:
            List of chart file information
        """
        chart_files = []

        for idx, chart_data in enumerate(charts):
            try:
                # Create figure
                fig, ax = plt.subplots(figsize=(10, 6))

                # Generate chart based on type
                if chart_data.chart_type == 'line':
                    ax.plot(
                        chart_data.x_data,
                        chart_data.y_data,
                        marker='o',
                        label=chart_data.series_label or 'Data'
                    )

                elif chart_data.chart_type == 'bar':
                    ax.bar(
                        chart_data.x_data,
                        chart_data.y_data,
                        label=chart_data.series_label or 'Data'
                    )

                elif chart_data.chart_type == 'scatter':
                    ax.scatter(
                        chart_data.x_data,
                        chart_data.y_data,
                        label=chart_data.series_label or 'Data',
                        alpha=0.6
                    )

                # Add additional series if provided
                if chart_data.additional_series:
                    for series in chart_data.additional_series:
                        ax.plot(
                            series.get('x_data', chart_data.x_data),
                            series['y_data'],
                            marker='o',
                            label=series.get('label', 'Series')
                        )

                # Set labels and title
                ax.set_xlabel(chart_data.x_label)
                ax.set_ylabel(chart_data.y_label)
                ax.set_title(chart_data.title)

                # Add legend if there are labels
                if chart_data.series_label or chart_data.additional_series:
                    ax.legend()

                # Apply branding colors
                ax.spines['top'].set_color(self.branding.primary_color)
                ax.spines['right'].set_color(self.branding.primary_color)

                # Grid
                ax.grid(True, alpha=0.3)

                # Save figure
                chart_filename = f"chart_{idx + 1}.png"
                chart_path = output_dir / chart_filename

                fig.savefig(
                    chart_path,
                    dpi=300,
                    bbox_inches='tight',
                    facecolor='white'
                )

                plt.close(fig)

                chart_files.append({
                    'file_path': str(chart_path),
                    'title': chart_data.title,
                    'index': idx + 1
                })

                logger.debug(f"Generated chart: {chart_filename}")

            except Exception as e:
                logger.error(f"Failed to generate chart {idx}: {e}")
                continue

        return chart_files

    def _prepare_context(
        self,
        test_report: TestReport,
        chart_files: List[Dict[str, str]],
        work_dir: Path
    ) -> Dict[str, Any]:
        """
        Prepare template context from test report data.

        Args:
            test_report: Test report data
            chart_files: List of generated chart files
            work_dir: Working directory for files

        Returns:
            Template context dictionary
        """
        # Copy logo files to working directory if specified
        lab_info_dict = test_report.lab_info.dict()

        if test_report.lab_info.logo_path:
            logo_src = Path(test_report.lab_info.logo_path)
            if logo_src.exists():
                logo_dest = work_dir / logo_src.name
                import shutil
                shutil.copy(logo_src, logo_dest)
                lab_info_dict['logo_path'] = str(logo_dest)

        if test_report.lab_info.nabl_logo_path:
            nabl_src = Path(test_report.lab_info.nabl_logo_path)
            if nabl_src.exists():
                nabl_dest = work_dir / nabl_src.name
                import shutil
                shutil.copy(nabl_src, nabl_dest)
                lab_info_dict['nabl_logo_path'] = str(nabl_dest)

        # Build context
        context = {
            'metadata': test_report.metadata.dict(),
            'lab_info': lab_info_dict,
            'module_info': test_report.module_info.dict(),
            'test_sequences': [seq.dict() for seq in test_report.test_sequences],
            'charts': chart_files,
            'overall_result': test_report.get_overall_result(),
            'summary': test_report.summary,
            'conclusions': test_report.conclusions,
            'deviations': test_report.deviations,
            'attachments': test_report.attachments,
            'branding': self.branding.dict(),
        }

        return context

    def _add_watermark(
        self,
        pdf_data: bytes,
        watermark_text: str = "DRAFT",
        opacity: float = 0.1
    ) -> bytes:
        """
        Add watermark to PDF.

        Args:
            pdf_data: Original PDF data
            watermark_text: Text for watermark
            opacity: Watermark opacity (0-1)

        Returns:
            PDF data with watermark
        """
        try:
            import io

            # Create watermark PDF
            watermark_buffer = io.BytesIO()
            c = canvas.Canvas(watermark_buffer, pagesize=A4)

            # Set watermark properties
            c.setFont("Helvetica-Bold", 60)
            c.setFillColorRGB(0.5, 0.5, 0.5, alpha=opacity)

            # Rotate and draw text
            c.saveState()
            c.translate(297, 420)  # Center of A4 page
            c.rotate(45)
            c.drawCentredString(0, 0, watermark_text)
            c.restoreState()

            c.save()

            # Read watermark PDF
            watermark_buffer.seek(0)
            watermark_pdf = PdfReader(watermark_buffer)
            watermark_page = watermark_pdf.pages[0]

            # Read original PDF
            pdf_buffer = io.BytesIO(pdf_data)
            pdf_reader = PdfReader(pdf_buffer)
            pdf_writer = PdfWriter()

            # Apply watermark to each page
            for page in pdf_reader.pages:
                page.merge_page(watermark_page)
                pdf_writer.add_page(page)

            # Write output
            output_buffer = io.BytesIO()
            pdf_writer.write(output_buffer)

            return output_buffer.getvalue()

        except Exception as e:
            logger.warning(f"Failed to add watermark: {e}. Returning original PDF.")
            return pdf_data

    def generate_summary_statistics(
        self,
        test_report: TestReport
    ) -> Dict[str, Any]:
        """
        Generate summary statistics from test report.

        Args:
            test_report: Test report data

        Returns:
            Dictionary of statistics
        """
        stats = test_report.get_test_statistics()

        # Add additional metrics
        stats['overall_result'] = test_report.get_overall_result()
        stats['pass_rate'] = (
            stats['passed'] / stats['total'] * 100
            if stats['total'] > 0 else 0
        )

        # Chart statistics
        stats['num_charts'] = len(test_report.charts)

        # Measurement statistics
        total_measurements = sum(
            len(seq.measurements) for seq in test_report.test_sequences
        )
        stats['total_measurements'] = total_measurements

        return stats

    def validate_report_data(
        self,
        test_report: TestReport
    ) -> List[str]:
        """
        Validate test report data for completeness.

        Args:
            test_report: Test report data

        Returns:
            List of validation warnings/errors
        """
        issues = []

        # Check required fields
        if not test_report.test_sequences:
            issues.append("No test sequences found")

        if not test_report.metadata.report_number:
            issues.append("Report number is missing")

        if not test_report.lab_info.lab_name:
            issues.append("Laboratory name is missing")

        # Check for incomplete test sequences
        for seq in test_report.test_sequences:
            if seq.overall_result == TestResult.NOT_TESTED:
                issues.append(
                    f"Test sequence {seq.sequence_id} has no result"
                )

            if not seq.measurements:
                issues.append(
                    f"Test sequence {seq.sequence_id} has no measurements"
                )

        # Check approvals
        if not test_report.metadata.is_draft:
            if not test_report.metadata.reviewed_by:
                issues.append("Reviewed by field is missing for final report")

            if not test_report.metadata.approved_by:
                issues.append("Approved by field is missing for final report")

        return issues

    def export_latex_source(
        self,
        test_report: TestReport,
        template_name: str = "iec_61215_report.tex",
        output_filename: Optional[str] = None
    ) -> str:
        """
        Export rendered LaTeX source without compiling to PDF.

        Useful for debugging or manual compilation.

        Args:
            test_report: Test report data
            template_name: Template name
            output_filename: Output .tex filename

        Returns:
            Path to .tex file
        """
        if output_filename is None:
            output_filename = f"{test_report.metadata.report_number}.tex"

        output_path = self.output_dir / output_filename

        # Prepare context (without charts for simplicity)
        context = {
            'metadata': test_report.metadata.dict(),
            'lab_info': test_report.lab_info.dict(),
            'module_info': test_report.module_info.dict(),
            'test_sequences': [seq.dict() for seq in test_report.test_sequences],
            'charts': [],
            'overall_result': test_report.get_overall_result(),
            'summary': test_report.summary,
            'conclusions': test_report.conclusions,
            'deviations': test_report.deviations,
            'attachments': test_report.attachments,
        }

        # Render template
        latex_content = self.template_engine.render_template(
            template_name,
            context,
            escape_all=False
        )

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)

        logger.info(f"LaTeX source exported to {output_path}")

        return str(output_path)
