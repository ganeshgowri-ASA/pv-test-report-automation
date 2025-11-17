"""
Report generation system for PV test reports.
Supports multiple output formats and compliance standards.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import json


class ReportGenerator:
    """
    Generate test reports in various formats.

    Supports:
    - PDF reports (using reportlab or weasyprint)
    - Excel spreadsheets (using openpyxl)
    - HTML reports
    - JSON data export
    - Compliance certificates
    """

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize report generator.

        Args:
            template_dir: Directory containing report templates
        """
        self.template_dir = template_dir or Path(__file__).parent / "templates"

    def generate_iec61215_report(
        self,
        report_data: Dict[str, Any],
        output_path: Path,
        format: str = "json"
    ) -> Path:
        """
        Generate IEC 61215 test report.

        Args:
            report_data: Report data from protocol
            output_path: Output file path
            format: Output format (json, html, pdf, excel)

        Returns:
            Path to generated report
        """
        if format == "json":
            return self._generate_json_report(report_data, output_path)
        elif format == "html":
            return self._generate_html_report(report_data, output_path)
        elif format == "pdf":
            return self._generate_pdf_report(report_data, output_path)
        elif format == "excel":
            return self._generate_excel_report(report_data, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_json_report(
        self,
        report_data: Dict[str, Any],
        output_path: Path
    ) -> Path:
        """Generate JSON format report."""
        output_path = output_path.with_suffix('.json')

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)

        return output_path

    def _generate_html_report(
        self,
        report_data: Dict[str, Any],
        output_path: Path
    ) -> Path:
        """
        Generate HTML format report.

        In production, would use Jinja2 templates for professional formatting.
        """
        output_path = output_path.with_suffix('.html')

        html_content = self._build_html_content(report_data)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return output_path

    def _build_html_content(self, report_data: Dict[str, Any]) -> str:
        """Build HTML content from report data."""
        metadata = report_data.get("report_metadata", {})
        module = report_data.get("module_information", {})
        compliance = report_data.get("compliance_summary", {})
        degradation = report_data.get("degradation_summary", {})

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IEC 61215 Test Report - {metadata.get('report_number', 'N/A')}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
        }}
        .section {{
            background-color: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .pass {{
            color: #27ae60;
            font-weight: bold;
        }}
        .fail {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .pending {{
            color: #f39c12;
            font-weight: bold;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }}
        .info-item {{
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 4px;
        }}
        .info-item label {{
            font-weight: bold;
            color: #2c3e50;
            display: block;
            margin-bottom: 5px;
        }}
        .compliance-badge {{
            display: inline-block;
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 18px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .compliance-pass {{
            background-color: #27ae60;
            color: white;
        }}
        .compliance-fail {{
            background-color: #e74c3c;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>IEC 61215-2:2021 Test Report</h1>
        <p><strong>Report Number:</strong> {metadata.get('report_number', 'N/A')}</p>
        <p><strong>Laboratory:</strong> {metadata.get('laboratory', 'N/A')}</p>
        <p><strong>Accreditation:</strong> {metadata.get('accreditation', 'N/A')}</p>
        <p><strong>Date:</strong> {metadata.get('generation_date', 'N/A')}</p>
    </div>

    <div class="section">
        <h2>Module Information</h2>
        <div class="info-grid">
            <div class="info-item">
                <label>Manufacturer:</label>
                <span>{module.get('manufacturer', 'N/A')}</span>
            </div>
            <div class="info-item">
                <label>Model:</label>
                <span>{module.get('model', 'N/A')}</span>
            </div>
            <div class="info-item">
                <label>Serial Number:</label>
                <span>{module.get('serial_number', 'N/A')}</span>
            </div>
            <div class="info-item">
                <label>Module Type:</label>
                <span>{module.get('module_type', 'N/A')}</span>
            </div>
            <div class="info-item">
                <label>Rated Power:</label>
                <span>{module.get('rated_power', 'N/A')} W</span>
            </div>
            <div class="info-item">
                <label>Cell Type:</label>
                <span>{module.get('cell_type', 'N/A')}</span>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Compliance Summary</h2>
        <div class="compliance-badge compliance-{compliance.get('overall_status', 'pending')}">
            Overall Status: {compliance.get('overall_status', 'PENDING').upper()}
        </div>
        <div class="info-grid">
            <div class="info-item">
                <label>Tests Passed:</label>
                <span class="pass">{compliance.get('tests_passed', 0)}</span>
            </div>
            <div class="info-item">
                <label>Tests Failed:</label>
                <span class="fail">{compliance.get('tests_failed', 0)}</span>
            </div>
            <div class="info-item">
                <label>Total Tests:</label>
                <span>{compliance.get('tests_total', 0)}</span>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Power Degradation Summary</h2>
        <div class="info-grid">
            <div class="info-item">
                <label>Initial Power:</label>
                <span>{degradation.get('initial_power', 'N/A')} W</span>
            </div>
            <div class="info-item">
                <label>Final Power:</label>
                <span>{degradation.get('final_power', 'N/A')} W</span>
            </div>
            <div class="info-item">
                <label>Degradation:</label>
                <span>{degradation.get('degradation_percent', 'N/A')}%</span>
            </div>
            <div class="info-item">
                <label>Limit:</label>
                <span>{degradation.get('limit_percent', 'N/A')}%</span>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Test Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Test ID</th>
                    <th>Test Name</th>
                    <th>Clause</th>
                    <th>Status</th>
                    <th>Compliance</th>
                    <th>Duration</th>
                </tr>
            </thead>
            <tbody>
"""

        # Add test results
        for result in report_data.get("test_results", []):
            status = result.get("status", "unknown")
            compliance = result.get("compliance_status", "pending")
            duration = result.get("duration", 0)
            duration_str = f"{duration:.0f}s" if duration else "N/A"

            html += f"""
                <tr>
                    <td>{result.get('test_id', 'N/A')}</td>
                    <td>{result.get('test_name', 'N/A')}</td>
                    <td>{result.get('clause_reference', 'N/A')}</td>
                    <td>{status}</td>
                    <td class="{compliance}">{compliance.upper()}</td>
                    <td>{duration_str}</td>
                </tr>
"""

        html += """
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>Report Footer</h2>
        <p><em>This report was generated automatically by the PV Test Report Automation System.</em></p>
        <p><em>All tests performed in accordance with IEC 61215-2:2021 standards.</em></p>
    </div>
</body>
</html>
"""

        return html

    def _generate_pdf_report(
        self,
        report_data: Dict[str, Any],
        output_path: Path
    ) -> Path:
        """
        Generate PDF format report.

        In production, would use reportlab or weasyprint.
        For now, generates HTML and notes that PDF conversion is needed.
        """
        # First generate HTML
        html_path = self._generate_html_report(report_data, output_path.with_suffix('.html'))

        # In production, convert HTML to PDF using weasyprint or reportlab
        # from weasyprint import HTML
        # HTML(str(html_path)).write_pdf(output_path.with_suffix('.pdf'))

        print(f"HTML report generated at {html_path}")
        print("Note: PDF generation requires weasyprint or reportlab library")

        return html_path

    def _generate_excel_report(
        self,
        report_data: Dict[str, Any],
        output_path: Path
    ) -> Path:
        """
        Generate Excel format report.

        In production, would use openpyxl for full Excel functionality.
        For now, generates CSV with key data.
        """
        output_path = output_path.with_suffix('.csv')

        # Simple CSV export of test results
        import csv

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                'Test ID', 'Test Name', 'Clause Reference',
                'Status', 'Compliance', 'Duration (s)', 'Notes'
            ])

            # Test results
            for result in report_data.get("test_results", []):
                writer.writerow([
                    result.get('test_id', ''),
                    result.get('test_name', ''),
                    result.get('clause_reference', ''),
                    result.get('status', ''),
                    result.get('compliance_status', ''),
                    result.get('duration', ''),
                    result.get('compliance_notes', ''),
                ])

        print(f"CSV report generated at {output_path}")
        print("Note: Full Excel generation requires openpyxl library")

        return output_path

    def generate_compliance_certificate(
        self,
        report_data: Dict[str, Any],
        output_path: Path
    ) -> Path:
        """
        Generate compliance certificate if module passes all tests.

        Args:
            report_data: Report data
            output_path: Output file path

        Returns:
            Path to certificate
        """
        compliance = report_data.get("compliance_summary", {})
        metadata = report_data.get("report_metadata", {})
        module = report_data.get("module_information", {})

        if compliance.get("overall_status") != "pass":
            raise ValueError("Cannot generate certificate - module did not pass all tests")

        certificate_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Compliance Certificate</title>
    <style>
        body {{
            font-family: 'Georgia', serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 40px;
            border: 10px solid #2c3e50;
            background-color: #f9f9f9;
        }}
        .certificate {{
            text-align: center;
        }}
        h1 {{
            color: #2c3e50;
            font-size: 36px;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #3498db;
            font-size: 20px;
            margin-bottom: 30px;
        }}
        .content {{
            text-align: left;
            margin: 30px 0;
            line-height: 1.8;
        }}
        .footer {{
            margin-top: 50px;
            border-top: 2px solid #2c3e50;
            padding-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="certificate">
        <h1>COMPLIANCE CERTIFICATE</h1>
        <div class="subtitle">IEC 61215-2:2021 Design Qualification</div>

        <div class="content">
            <p>This is to certify that the photovoltaic module:</p>

            <p><strong>Manufacturer:</strong> {module.get('manufacturer', 'N/A')}<br>
            <strong>Model:</strong> {module.get('model', 'N/A')}<br>
            <strong>Serial Number:</strong> {module.get('serial_number', 'N/A')}</p>

            <p>has successfully completed all required tests in accordance with
            IEC 61215-2:2021 standard for terrestrial photovoltaic modules.</p>

            <p><strong>Test Report Number:</strong> {metadata.get('report_number', 'N/A')}<br>
            <strong>Laboratory:</strong> {metadata.get('laboratory', 'N/A')}<br>
            <strong>Accreditation:</strong> {metadata.get('accreditation', 'N/A')}</p>
        </div>

        <div class="footer">
            <p><strong>Issued:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
        </div>
    </div>
</body>
</html>
"""

        output_path = output_path.with_suffix('.html')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(certificate_html)

        return output_path
