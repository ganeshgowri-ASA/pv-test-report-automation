"""HTML export engine with responsive design.

Session 42: HTML Export
- Responsive HTML reports
- CSS styling and themes
- Interactive charts (Chart.js/Plotly)
- Print-friendly CSS
- ISO 17025 compliant formatting
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from jinja2 import Template

logger = logging.getLogger(__name__)


class HTMLExporter:
    """HTML exporter for test reports with responsive design."""

    DEFAULT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ report_id }} - PV Test Report</title>
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        header { background: linear-gradient(135deg, #003366 0%, #005599 100%); color: white; padding: 30px; text-align: center; }
        h1 { margin-bottom: 10px; }
        .metadata { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 30px 0; }
        .card { background: white; border: 1px solid #ddd; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .card h2 { color: #003366; margin-bottom: 15px; border-bottom: 2px solid #003366; padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #003366; color: white; font-weight: 600; }
        tr:hover { background-color: #f5f5f5; }
        .compliant { color: #006100; font-weight: bold; background: #C6EFCE; padding: 5px 10px; border-radius: 4px; }
        .non-compliant { color: #9C0006; font-weight: bold; background: #FFC7CE; padding: 5px 10px; border-radius: 4px; }
        .signature-section { margin-top: 40px; padding: 20px; background: #f9f9f9; border-radius: 8px; }
        footer { text-align: center; margin-top: 40px; padding: 20px; background: #f5f5f5; font-size: 0.9em; }
        @media print { header { background: #003366; } .no-print { display: none; } }
        @media (max-width: 768px) { .metadata { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <header>
        <h1>PV Test Report</h1>
        <p>{{ standard }} | ISO 17025 Compliant</p>
    </header>

    <div class="container">
        <div class="metadata">
            <div class="card">
                <h2>Report Information</h2>
                <table>
                    <tr><td><strong>Report ID:</strong></td><td>{{ report_id }}</td></tr>
                    <tr><td><strong>Test Standard:</strong></td><td>{{ standard }}</td></tr>
                    <tr><td><strong>Test Date:</strong></td><td>{{ test_date }}</td></tr>
                    <tr><td><strong>Status:</strong></td><td>{{ status }}</td></tr>
                </table>
            </div>

            <div class="card">
                <h2>Module Information</h2>
                <table>
                    <tr><td><strong>Manufacturer:</strong></td><td>{{ module_manufacturer }}</td></tr>
                    <tr><td><strong>Model:</strong></td><td>{{ module_model }}</td></tr>
                    <tr><td><strong>Serial Number:</strong></td><td>{{ module_serial_number }}</td></tr>
                </table>
            </div>
        </div>

        <div class="card">
            <h2>Test Results</h2>
            <table>
                <thead>
                    <tr><th>Measurement</th><th>Result</th></tr>
                </thead>
                <tbody>
                    {% for key, value in test_results.items() %}
                    <tr><td>{{ key }}</td><td>{{ value }}</td></tr>
                    {% endfor %}
                </tbody>
            </table>
            <div id="results-chart"></div>
        </div>

        <div class="card">
            <h2>Compliance Assessment</h2>
            <p><strong>Overall Compliance:</strong> 
                <span class="{% if is_compliant %}compliant{% else %}non-compliant{% endif %}">
                    {% if is_compliant %}COMPLIANT{% else %}NON-COMPLIANT{% endif %}
                </span>
            </p>
            {% if deviations %}
            <h3>Deviations:</h3>
            <ul>
                {% for deviation in deviations %}
                <li>{{ deviation }}</li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>

        <div class="signature-section card">
            <h2>Approvals</h2>
            <table>
                <tr><td><strong>Prepared By:</strong></td><td>{{ created_by }}</td></tr>
                <tr><td><strong>Reviewed By:</strong></td><td>{{ reviewed_by }}</td></tr>
                <tr><td><strong>Approved By:</strong></td><td>{{ approved_by }}</td></tr>
                <tr><td><strong>Digital Signature:</strong></td><td>{{ digital_signature }}</td></tr>
            </table>
        </div>
    </div>

    <footer>
        <p>Generated: {{ generated_at }} | ISO 17025 Accredited Laboratory</p>
        <p>© PV Test Laboratory - NABL, ILAC Accredited</p>
    </footer>

    <script>
        // Create interactive chart
        var data = [{ 
            x: {{ result_keys|tojson }}, 
            y: {{ result_values|tojson }}, 
            type: 'bar',
            marker: { color: '#003366' }
        }];
        var layout = { title: 'Test Results Visualization', xaxis: { title: 'Measurement' }, yaxis: { title: 'Value' } };
        Plotly.newPlot('results-chart', data, layout);
    </script>
</body>
</html>
"""

    def __init__(self, template_path: Optional[str] = None):
        """Initialize HTML exporter."""
        if template_path and Path(template_path).exists():
            with open(template_path, 'r') as f:
                self.template = Template(f.read())
        else:
            self.template = Template(self.DEFAULT_TEMPLATE)
        logger.info("HTMLExporter initialized")

    def export_report(self, report_data: Dict[str, Any], output_path: str) -> str:
        """Export report to HTML."""
        logger.info(f"Exporting report to HTML: {output_path}")

        # Prepare data for template
        context = {
            **report_data,
            'generated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
            'result_keys': list(report_data.get('test_results', {}).keys()),
            'result_values': [float(str(v).replace('%', '')) if isinstance(v, (int, float)) or (isinstance(v, str) and v.replace('.','').replace('%','').isdigit()) else 0 for v in report_data.get('test_results', {}).values()],
        }

        # Render template
        html_content = self.template.render(**context)

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"HTML report exported successfully: {output_path}")
        return output_path
