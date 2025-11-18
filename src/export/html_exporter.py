"""
HTML Exporter Module

Provides HTML export functionality with Jinja2 templates.
Includes responsive design, interactive charts, and print optimization.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import json

try:
    from jinja2 import Environment, FileSystemLoader, Template
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

try:
    import plotly
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from .base_exporter import (
    BaseExporter, ExportFormat, ExportOptions, ExportRegistry
)


logger = logging.getLogger(__name__)


@ExportRegistry.register(ExportFormat.HTML)
class HTMLExporter(BaseExporter):
    """HTML export engine with Jinja2 templates and interactive charts."""

    def __init__(self, template_manager=None):
        """
        Initialize HTML exporter.

        Args:
            template_manager: Template manager instance
        """
        super().__init__(template_manager)
        self._validate_dependencies()
        self.jinja_env = None

    @property
    def format_type(self) -> ExportFormat:
        """Get export format type."""
        return ExportFormat.HTML

    @property
    def file_extension(self) -> str:
        """Get file extension."""
        return "html"

    def _validate_dependencies(self):
        """Validate required dependencies."""
        if not JINJA2_AVAILABLE:
            raise ImportError("Jinja2 not installed. Install with: pip install jinja2")

    def export(self, data: Dict[str, Any], options: ExportOptions) -> Path:
        """
        Export data to HTML.

        Args:
            data: Data to export
            options: Export options

        Returns:
            Path to exported HTML file
        """
        self._validate_data(data)
        self._ensure_output_directory(options.output_path)

        logger.info(f"Exporting HTML: {options.output_path}")

        # Add metadata
        if options.include_metadata:
            data = self._add_metadata(data)

        # Setup Jinja2 environment
        self._setup_jinja_environment(options)

        # Generate HTML content
        html_content = self._generate_html(data, options)

        # Write HTML file
        with open(options.output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Validate output
        if not self.validate_output(options.output_path):
            raise ValueError(f"Invalid HTML output: {options.output_path}")

        logger.info(f"HTML export completed: {options.output_path}")
        return options.output_path

    def _setup_jinja_environment(self, options: ExportOptions):
        """
        Setup Jinja2 environment.

        Args:
            options: Export options
        """
        if self.template_manager:
            template_dir = self.template_manager.template_dir / self.format_type.value
            if template_dir.exists():
                self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))
            else:
                self.jinja_env = Environment()
        else:
            self.jinja_env = Environment()

        # Add custom filters
        self.jinja_env.filters['format_datetime'] = self._format_datetime
        self.jinja_env.filters['format_number'] = self._format_number
        self.jinja_env.filters['status_class'] = self._get_status_class

    def _generate_html(self, data: Dict[str, Any], options: ExportOptions) -> str:
        """
        Generate HTML content.

        Args:
            data: Data to export
            options: Export options

        Returns:
            HTML content
        """
        # Try to load custom template
        if options.template_name and self.jinja_env:
            try:
                template = self.jinja_env.get_template(f"{options.template_name}.html")
                return template.render(data=data, options=options)
            except Exception as e:
                logger.warning(f"Failed to load custom template: {e}")

        # Use default template
        return self._generate_default_html(data, options)

    def _generate_default_html(self, data: Dict[str, Any], options: ExportOptions) -> str:
        """
        Generate HTML using default template.

        Args:
            data: Data to export
            options: Export options

        Returns:
            HTML content
        """
        title = data.get("title", "PV Test Report")

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {self._generate_css()}
    {self._generate_plotly_scripts() if options.include_charts and PLOTLY_AVAILABLE else ""}
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <h1>{title}</h1>
            <div class="subtitle">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </header>

        <!-- Navigation -->
        <nav class="nav">
            <a href="#summary">Summary</a>
            <a href="#configuration">Configuration</a>
            <a href="#results">Test Results</a>
            {f'<a href="#charts">Charts</a>' if options.include_charts and "charts" in data else ""}
            <a href="#analysis">Analysis</a>
        </nav>

        <!-- Main Content -->
        <main class="content">
"""

        # Metadata section
        if options.include_metadata and "_export_metadata" in data:
            html += self._generate_metadata_section(data["_export_metadata"])

        # Summary section
        if "summary" in data:
            html += self._generate_summary_section(data["summary"])

        # Configuration section
        if "configuration" in data:
            html += self._generate_configuration_section(data["configuration"])

        # Test Results section
        if "test_results" in data:
            html += self._generate_test_results_section(data["test_results"])

        # Charts section
        if options.include_charts and "charts" in data:
            html += self._generate_charts_section(data["charts"])

        # Analysis section
        if "analysis" in data:
            html += self._generate_analysis_section(data["analysis"])

        # Recommendations section
        if "recommendations" in data:
            html += self._generate_recommendations_section(data["recommendations"])

        html += """
        </main>

        <!-- Footer -->
        <footer class="footer">
            <p>&copy; 2025 PV Test Automation System</p>
        </footer>
    </div>

    {self._generate_javascript()}
</body>
</html>
"""
        return html

    def _generate_css(self) -> str:
        """
        Generate CSS styles.

        Returns:
            CSS content
        """
        return """
    <style>
        /* Reset and Base Styles */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
        }

        /* Header */
        .header {
            background: linear-gradient(135deg, #1f4788 0%, #2d5aa0 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }

        .subtitle {
            font-size: 0.9rem;
            opacity: 0.9;
        }

        /* Navigation */
        .nav {
            background-color: #34495e;
            padding: 1rem;
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .nav a {
            color: white;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            transition: background-color 0.3s;
        }

        .nav a:hover {
            background-color: #2c3e50;
        }

        /* Content */
        .content {
            padding: 2rem;
        }

        .section {
            margin-bottom: 3rem;
        }

        .section-title {
            color: #1f4788;
            font-size: 1.8rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 3px solid #1f4788;
        }

        /* Metadata */
        .metadata-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .metadata-item {
            background-color: #f8f9fa;
            padding: 1rem;
            border-left: 4px solid #1f4788;
        }

        .metadata-label {
            font-weight: bold;
            color: #555;
            font-size: 0.9rem;
        }

        .metadata-value {
            color: #333;
            margin-top: 0.25rem;
        }

        /* Summary */
        .summary-box {
            background-color: #e8f4f8;
            padding: 1.5rem;
            border-radius: 8px;
            border-left: 5px solid #1f4788;
            margin-bottom: 2rem;
        }

        /* Tables */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        thead {
            background-color: #1f4788;
            color: white;
        }

        th, td {
            padding: 0.75rem;
            text-align: left;
            border: 1px solid #ddd;
        }

        tbody tr:nth-child(even) {
            background-color: #f8f9fa;
        }

        tbody tr:hover {
            background-color: #e9ecef;
        }

        /* Status Badges */
        .status {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.85rem;
        }

        .status-pass {
            background-color: #d4edda;
            color: #155724;
        }

        .status-fail {
            background-color: #f8d7da;
            color: #721c24;
        }

        .status-warning {
            background-color: #fff3cd;
            color: #856404;
        }

        /* Charts */
        .chart-container {
            margin: 2rem 0;
            padding: 1rem;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .chart-title {
            font-size: 1.2rem;
            font-weight: bold;
            color: #2d5aa0;
            margin-bottom: 1rem;
        }

        /* Recommendations */
        .recommendation-list {
            list-style: none;
            counter-reset: recommendation;
        }

        .recommendation-list li {
            counter-increment: recommendation;
            padding: 1rem;
            margin-bottom: 1rem;
            background-color: #fff8e1;
            border-left: 4px solid #ffc107;
            border-radius: 4px;
        }

        .recommendation-list li::before {
            content: counter(recommendation) ". ";
            font-weight: bold;
            color: #f57c00;
        }

        /* Footer */
        .footer {
            background-color: #34495e;
            color: white;
            text-align: center;
            padding: 1.5rem;
            margin-top: 2rem;
        }

        /* Print Styles */
        @media print {
            body {
                background-color: white;
            }

            .container {
                box-shadow: none;
            }

            .nav {
                display: none;
            }

            .section {
                page-break-inside: avoid;
            }

            .chart-container {
                page-break-inside: avoid;
            }
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8rem;
            }

            .content {
                padding: 1rem;
            }

            .nav {
                flex-direction: column;
            }

            table {
                font-size: 0.9rem;
            }

            th, td {
                padding: 0.5rem;
            }
        }
    </style>
        """

    def _generate_plotly_scripts(self) -> str:
        """
        Generate Plotly script includes.

        Returns:
            Script tags
        """
        return """
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        """

    def _generate_javascript(self) -> str:
        """
        Generate JavaScript code.

        Returns:
            JavaScript content
        """
        return """
    <script>
        // Smooth scrolling for navigation links
        document.querySelectorAll('.nav a').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });

        // Print button
        function printReport() {
            window.print();
        }
    </script>
        """

    def _generate_metadata_section(self, metadata: Dict[str, Any]) -> str:
        """Generate metadata section HTML."""
        html = '<section id="metadata" class="section">'
        html += '<h2 class="section-title">Document Information</h2>'
        html += '<div class="metadata-grid">'

        for key, value in metadata.items():
            display_key = key.replace("_", " ").title()
            html += f'''
            <div class="metadata-item">
                <div class="metadata-label">{display_key}</div>
                <div class="metadata-value">{value}</div>
            </div>
            '''

        html += '</div></section>'
        return html

    def _generate_summary_section(self, summary: str) -> str:
        """Generate summary section HTML."""
        return f'''
        <section id="summary" class="section">
            <h2 class="section-title">Executive Summary</h2>
            <div class="summary-box">
                <p>{summary}</p>
            </div>
        </section>
        '''

    def _generate_configuration_section(self, configuration: Dict[str, Any]) -> str:
        """Generate configuration section HTML."""
        html = '<section id="configuration" class="section">'
        html += '<h2 class="section-title">Test Configuration</h2>'
        html += '<table><thead><tr><th>Parameter</th><th>Value</th></tr></thead><tbody>'

        for key, value in configuration.items():
            display_key = key.replace("_", " ").title()
            html += f'<tr><td>{display_key}</td><td>{value}</td></tr>'

        html += '</tbody></table></section>'
        return html

    def _generate_test_results_section(self, test_results: List[Dict[str, Any]]) -> str:
        """Generate test results section HTML."""
        html = '<section id="results" class="section">'
        html += '<h2 class="section-title">Test Results</h2>'
        html += '<table><thead><tr>'
        html += '<th>Test Name</th><th>Status</th><th>Value</th><th>Expected</th>'
        html += '</tr></thead><tbody>'

        for test in test_results:
            status = test.get("status", "N/A")
            status_class = self._get_status_class(status)

            html += f'''
            <tr>
                <td>{test.get("name", "N/A")}</td>
                <td><span class="status {status_class}">{status}</span></td>
                <td>{test.get("value", "N/A")}</td>
                <td>{test.get("expected", "N/A")}</td>
            </tr>
            '''

        html += '</tbody></table></section>'
        return html

    def _generate_charts_section(self, charts: List[Dict[str, Any]]) -> str:
        """Generate charts section HTML."""
        html = '<section id="charts" class="section">'
        html += '<h2 class="section-title">Charts and Graphs</h2>'

        for idx, chart_data in enumerate(charts):
            chart_title = chart_data.get("title", f"Chart {idx + 1}")
            html += f'<div class="chart-container">'
            html += f'<div class="chart-title">{chart_title}</div>'

            # Generate Plotly chart if data available
            if PLOTLY_AVAILABLE and "plotly_data" in chart_data:
                chart_id = f"chart_{idx}"
                plotly_json = json.dumps(chart_data["plotly_data"])
                html += f'<div id="{chart_id}"></div>'
                html += f'<script>Plotly.newPlot("{chart_id}", {plotly_json});</script>'
            elif "image_data" in chart_data:
                html += f'<img src="data:image/png;base64,{chart_data["image_data"]}" alt="{chart_title}" style="max-width: 100%;">'

            if "description" in chart_data:
                html += f'<p>{chart_data["description"]}</p>'

            html += '</div>'

        html += '</section>'
        return html

    def _generate_analysis_section(self, analysis: str) -> str:
        """Generate analysis section HTML."""
        return f'''
        <section id="analysis" class="section">
            <h2 class="section-title">Analysis</h2>
            <div class="summary-box">
                <p>{analysis}</p>
            </div>
        </section>
        '''

    def _generate_recommendations_section(self, recommendations: List[str]) -> str:
        """Generate recommendations section HTML."""
        html = '<section id="recommendations" class="section">'
        html += '<h2 class="section-title">Recommendations</h2>'
        html += '<ul class="recommendation-list">'

        for recommendation in recommendations:
            html += f'<li>{recommendation}</li>'

        html += '</ul></section>'
        return html

    def _format_datetime(self, value) -> str:
        """Format datetime filter."""
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return str(value)

    def _format_number(self, value, decimals: int = 2) -> str:
        """Format number filter."""
        try:
            return f"{float(value):.{decimals}f}"
        except (ValueError, TypeError):
            return str(value)

    def _get_status_class(self, status: str) -> str:
        """Get CSS class for status."""
        status_upper = str(status).upper()
        if status_upper == "PASS":
            return "status-pass"
        elif status_upper == "FAIL":
            return "status-fail"
        else:
            return "status-warning"

    def validate_output(self, output_path: Path) -> bool:
        """
        Validate HTML output.

        Args:
            output_path: Path to HTML file

        Returns:
            True if valid
        """
        if not output_path.exists():
            return False

        if output_path.stat().st_size == 0:
            return False

        try:
            # Check if file contains valid HTML
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    return False
                if '<!DOCTYPE html>' not in content and '<html' not in content:
                    return False
            return True
        except Exception as e:
            logger.error(f"HTML validation failed: {e}")
            return False

    def create_plotly_chart(
        self,
        chart_type: str,
        x_data: List,
        y_data: List,
        title: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create Plotly chart data.

        Args:
            chart_type: Type of chart (line, bar, scatter, etc.)
            x_data: X-axis data
            y_data: Y-axis data
            title: Chart title
            **kwargs: Additional chart parameters

        Returns:
            Chart data dictionary
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available")
            return {}

        if chart_type == "line":
            fig = go.Figure(data=go.Scatter(x=x_data, y=y_data, mode='lines'))
        elif chart_type == "bar":
            fig = go.Figure(data=go.Bar(x=x_data, y=y_data))
        elif chart_type == "scatter":
            fig = go.Figure(data=go.Scatter(x=x_data, y=y_data, mode='markers'))
        else:
            fig = go.Figure(data=go.Scatter(x=x_data, y=y_data))

        fig.update_layout(title=title, **kwargs)

        return {
            "title": title,
            "plotly_data": fig.to_dict()
        }
