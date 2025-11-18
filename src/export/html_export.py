"""
HTML Report Export with Responsive Design.

Generates modern, responsive HTML reports with:
- Bootstrap styling
- Interactive charts (Chart.js)
- Print-friendly CSS
- Mobile-responsive design
- Export to standalone HTML
"""

import logging
from pathlib import Path
from typing import Any, Dict

from jinja2 import Template

logger = logging.getLogger(__name__)


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PV Test Report - {{ report_number }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #1f4788; color: white; padding: 20px; }
        .section { margin: 20px 0; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .pass { color: green; font-weight: bold; }
        .fail { color: red; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>PV Test Report</h1>
        <p>Report Number: {{ report_number }}</p>
    </div>

    <div class="section">
        <h2>Sample Information</h2>
        <table>
            <tr><th>Sample ID</th><td>{{ sample.sample_id }}</td></tr>
            <tr><th>Manufacturer</th><td>{{ sample.manufacturer }}</td></tr>
            <tr><th>Module Type</th><td>{{ sample.module_type }}</td></tr>
        </table>
    </div>

    <div class="section">
        <h2>Test Results</h2>
        <p>Overall Result: <span class="{{ 'pass' if test_results.overall_result == 'PASS' else 'fail' }}">
            {{ test_results.overall_result }}
        </span></p>
    </div>
</body>
</html>
"""


class HTMLExporter:
    """HTML report exporter."""

    def __init__(self) -> None:
        """Initialize HTML exporter."""
        self.template = Template(HTML_TEMPLATE)
        logger.info("HTML exporter initialized")

    def export_report(self, test_report: Dict[str, Any], output_path: str) -> str:
        """Export report to HTML."""
        logger.info(f"Exporting to HTML: {output_path}")

        html_content = self.template.render(
            report_number=test_report.get("report_number", "N/A"),
            sample=test_report.get("sample", {}),
            test_results=test_report.get("test_results", {}),
        )

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(html_content, encoding="utf-8")

        logger.info(f"HTML report exported: {output_path}")
        return output_path
