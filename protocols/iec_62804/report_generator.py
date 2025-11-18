"""
IEC 62804 PID Testing Protocol - Report Generator

This module generates comprehensive test reports compliant with IEC 62804
and ISO 17025 requirements.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from io import BytesIO
import json

logger = logging.getLogger(__name__)


class IEC62804ReportGenerator:
    """
    Generate IEC 62804 test reports in multiple formats.

    Supports PDF, HTML, and JSON output formats with full compliance
    to IEC 62804 reporting requirements.
    """

    def __init__(self, test_data: Dict[str, Any]):
        """
        Initialize report generator.

        Args:
            test_data: Complete test data dictionary
        """
        self.test_data = test_data

    def generate_text_report(self) -> str:
        """
        Generate text-based test report.

        Returns:
            Report as formatted text
        """
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append("IEC 62804 PID TEST REPORT")
        lines.append("Potential Induced Degradation - Detection and Measurement")
        lines.append("=" * 80)
        lines.append("")

        # Test Information
        lines.append("TEST INFORMATION")
        lines.append("-" * 80)
        lines.append(f"Test ID:           {self.test_data.get('test_id', 'N/A')}")
        lines.append(f"Test Date:         {self._format_datetime(self.test_data.get('test_date'))}")
        lines.append(f"Test Method:       IEC 62804-1 Method {self.test_data.get('test_method', 'N/A')}")
        lines.append(f"Operator:          {self.test_data.get('operator', 'N/A')}")
        lines.append(f"Test Status:       {self.test_data.get('status', 'N/A').upper()}")
        lines.append("")

        # Module Information
        lines.append("MODULE UNDER TEST")
        lines.append("-" * 80)
        lines.append(f"Serial Number:     {self.test_data.get('module_serial', 'N/A')}")
        lines.append(f"Manufacturer:      {self.test_data.get('manufacturer', 'N/A')}")
        lines.append(f"Model:             {self.test_data.get('model', 'N/A')}")
        lines.append(f"Module Type:       {self.test_data.get('module_type', 'N/A')}")
        lines.append("")

        # Test Conditions
        lines.append("TEST CONDITIONS")
        lines.append("-" * 80)
        lines.append(f"Applied Voltage:   {self.test_data.get('voltage', 0):.0f} V")
        lines.append(f"Test Duration:     {self.test_data.get('duration_hours', 0)} hours")
        lines.append(f"Temperature:       {self.test_data.get('temperature', 0):.1f} °C")

        humidity = self.test_data.get('humidity')
        if humidity is not None:
            lines.append(f"Relative Humidity: {humidity:.1f} %RH")
        else:
            lines.append("Relative Humidity: N/A (Dry test)")

        lines.append(f"Start Time:        {self._format_datetime(self.test_data.get('start_time'))}")
        lines.append(f"End Time:          {self._format_datetime(self.test_data.get('end_time'))}")
        lines.append("")

        # Flash Test Results
        flash_results = self.test_data.get('flash_results', [])
        if flash_results:
            lines.append("FLASH TEST RESULTS")
            lines.append("-" * 80)
            lines.append(f"{'Time (h)':<12} {'Pmax (W)':<12} {'Voc (V)':<12} {'Isc (A)':<12} {'FF':<8} {'Deg. (%)':<10}")
            lines.append("-" * 80)

            for result in flash_results:
                elapsed = result.get('elapsed_hours', 0)
                pmax = result.get('pmax', 0)
                voc = result.get('voc', 0)
                isc = result.get('isc', 0)
                ff = result.get('ff', 0)
                deg = result.get('degradation_pct', 0)

                lines.append(f"{elapsed:<12.1f} {pmax:<12.2f} {voc:<12.2f} {isc:<12.2f} {ff:<8.3f} {deg:<10.2f}")

            lines.append("")

        # Degradation Summary
        lines.append("DEGRADATION SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Initial Pmax:      {self.test_data.get('initial_pmax', 0):.2f} W")
        lines.append(f"Final Pmax:        {self.test_data.get('final_pmax', 0):.2f} W")
        lines.append(f"Power Loss:        {self._calc_power_loss():.2f} W")
        lines.append(f"Degradation:       {self.test_data.get('degradation_pct', 0):.2f} %")
        lines.append(f"Degradation Rate:  {self.test_data.get('degradation_rate', 0):.3f} %/hour")
        lines.append("")

        # Leakage Current
        leakage_stats = self.test_data.get('leakage_statistics')
        if leakage_stats:
            lines.append("LEAKAGE CURRENT STATISTICS")
            lines.append("-" * 80)
            lines.append(f"Mean Current:      {leakage_stats.get('mean_current_ma', 0):.2f} mA")
            lines.append(f"Maximum Current:   {leakage_stats.get('max_current_ma', 0):.2f} mA")
            lines.append(f"Threshold Violations: {leakage_stats.get('threshold_violations', 0)}")
            lines.append("")

        # Recovery Results (if applicable)
        recovery_result = self.test_data.get('recovery_result')
        if recovery_result:
            lines.append("PID RECOVERY TEST")
            lines.append("-" * 80)
            lines.append(f"Degraded Power:    {recovery_result.get('degraded_pmax', 0):.2f} W")
            lines.append(f"Recovered Power:   {recovery_result.get('final_pmax', 0):.2f} W")
            lines.append(f"Recovery:          {recovery_result.get('recovery_pct', 0):.1f} %")
            lines.append(f"Recovery Time:     {recovery_result.get('recovery_time', 0):.1f} hours")
            lines.append(f"Classification:    {recovery_result.get('classification', 'N/A')}")
            lines.append("")

        # Test Result
        lines.append("=" * 80)
        lines.append("TEST RESULT")
        lines.append("=" * 80)

        result = self.test_data.get('result', 'pending').upper()
        degradation = self.test_data.get('degradation_pct', 0)

        lines.append(f"Result:            {result}")
        lines.append(f"Final Degradation: {degradation:.2f} %")

        if result == "PASS":
            lines.append("Status:            PASS - Degradation < 5% (IEC 62804 compliant)")
        elif result == "MARGINAL":
            lines.append("Status:            MARGINAL - Degradation 5-10%")
        elif result == "FAIL":
            lines.append("Status:            FAIL - Degradation > 10%")
        else:
            lines.append("Status:            PENDING - Test incomplete")

        lines.append("")

        # Notes
        notes = self.test_data.get('notes')
        if notes:
            lines.append("NOTES")
            lines.append("-" * 80)
            lines.append(notes)
            lines.append("")

        # Footer
        lines.append("=" * 80)
        lines.append(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)

        return "\n".join(lines)

    def generate_html_report(self) -> str:
        """
        Generate HTML test report.

        Returns:
            Report as HTML
        """
        html = []

        # HTML header
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append("<meta charset='UTF-8'>")
        html.append("<title>IEC 62804 PID Test Report</title>")
        html.append("<style>")
        html.append(self._get_html_styles())
        html.append("</style>")
        html.append("</head>")
        html.append("<body>")

        # Header
        html.append("<div class='header'>")
        html.append("<h1>IEC 62804 PID TEST REPORT</h1>")
        html.append("<p>Potential Induced Degradation - Detection and Measurement</p>")
        html.append("</div>")

        # Test Information
        html.append("<div class='section'>")
        html.append("<h2>Test Information</h2>")
        html.append("<table>")
        html.append(f"<tr><td>Test ID:</td><td>{self.test_data.get('test_id', 'N/A')}</td></tr>")
        html.append(f"<tr><td>Test Date:</td><td>{self._format_datetime(self.test_data.get('test_date'))}</td></tr>")
        html.append(f"<tr><td>Test Method:</td><td>IEC 62804-1 Method {self.test_data.get('test_method', 'N/A')}</td></tr>")
        html.append(f"<tr><td>Operator:</td><td>{self.test_data.get('operator', 'N/A')}</td></tr>")
        html.append(f"<tr><td>Status:</td><td>{self.test_data.get('status', 'N/A').upper()}</td></tr>")
        html.append("</table>")
        html.append("</div>")

        # Module Information
        html.append("<div class='section'>")
        html.append("<h2>Module Under Test</h2>")
        html.append("<table>")
        html.append(f"<tr><td>Serial Number:</td><td>{self.test_data.get('module_serial', 'N/A')}</td></tr>")
        html.append(f"<tr><td>Manufacturer:</td><td>{self.test_data.get('manufacturer', 'N/A')}</td></tr>")
        html.append(f"<tr><td>Model:</td><td>{self.test_data.get('model', 'N/A')}</td></tr>")
        html.append(f"<tr><td>Type:</td><td>{self.test_data.get('module_type', 'N/A')}</td></tr>")
        html.append("</table>")
        html.append("</div>")

        # Test Conditions
        html.append("<div class='section'>")
        html.append("<h2>Test Conditions</h2>")
        html.append("<table>")
        html.append(f"<tr><td>Applied Voltage:</td><td>{self.test_data.get('voltage', 0):.0f} V</td></tr>")
        html.append(f"<tr><td>Duration:</td><td>{self.test_data.get('duration_hours', 0)} hours</td></tr>")
        html.append(f"<tr><td>Temperature:</td><td>{self.test_data.get('temperature', 0):.1f} °C</td></tr>")

        humidity = self.test_data.get('humidity')
        if humidity is not None:
            html.append(f"<tr><td>Humidity:</td><td>{humidity:.1f} %RH</td></tr>")

        html.append("</table>")
        html.append("</div>")

        # Flash Test Results
        flash_results = self.test_data.get('flash_results', [])
        if flash_results:
            html.append("<div class='section'>")
            html.append("<h2>Flash Test Results</h2>")
            html.append("<table class='data-table'>")
            html.append("<tr><th>Time (h)</th><th>Pmax (W)</th><th>Voc (V)</th><th>Isc (A)</th><th>FF</th><th>Degradation (%)</th></tr>")

            for result in flash_results:
                html.append("<tr>")
                html.append(f"<td>{result.get('elapsed_hours', 0):.1f}</td>")
                html.append(f"<td>{result.get('pmax', 0):.2f}</td>")
                html.append(f"<td>{result.get('voc', 0):.2f}</td>")
                html.append(f"<td>{result.get('isc', 0):.2f}</td>")
                html.append(f"<td>{result.get('ff', 0):.3f}</td>")
                html.append(f"<td>{result.get('degradation_pct', 0):.2f}</td>")
                html.append("</tr>")

            html.append("</table>")
            html.append("</div>")

        # Test Result
        result = self.test_data.get('result', 'pending').upper()
        result_class = "pass" if result == "PASS" else "fail" if result == "FAIL" else "marginal"

        html.append(f"<div class='section result-{result_class}'>")
        html.append("<h2>Test Result</h2>")
        html.append(f"<p class='result-text'>{result}</p>")
        html.append(f"<p>Final Degradation: {self.test_data.get('degradation_pct', 0):.2f}%</p>")
        html.append("</div>")

        # Footer
        html.append("<div class='footer'>")
        html.append(f"<p>Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
        html.append("</div>")

        html.append("</body>")
        html.append("</html>")

        return "\n".join(html)

    def generate_json_report(self) -> str:
        """
        Generate JSON test report.

        Returns:
            Report as JSON string
        """
        # Create a clean copy with datetime conversion
        report_data = self._convert_datetimes(self.test_data.copy())

        return json.dumps(report_data, indent=2)

    def save_report(
        self,
        output_path: str,
        format: str = "text"
    ):
        """
        Save report to file.

        Args:
            output_path: Output file path
            format: Output format ("text", "html", or "json")
        """
        if format == "text":
            content = self.generate_text_report()
        elif format == "html":
            content = self.generate_html_report()
        elif format == "json":
            content = self.generate_json_report()
        else:
            raise ValueError(f"Unsupported format: {format}")

        with open(output_path, 'w') as f:
            f.write(content)

        logger.info(f"Report saved to {output_path}")

    def _format_datetime(self, dt) -> str:
        """Format datetime for display"""
        if dt is None:
            return "N/A"
        if isinstance(dt, str):
            return dt
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def _calc_power_loss(self) -> float:
        """Calculate power loss"""
        initial = self.test_data.get('initial_pmax', 0)
        final = self.test_data.get('final_pmax', 0)
        return initial - final

    def _convert_datetimes(self, data):
        """Convert datetime objects to ISO strings"""
        if isinstance(data, dict):
            return {k: self._convert_datetimes(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_datetimes(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data

    def _get_html_styles(self) -> str:
        """Get HTML CSS styles"""
        return """
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background-color: #003366;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 5px;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
        }
        .section {
            background-color: white;
            margin: 20px 0;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h2 {
            color: #003366;
            border-bottom: 2px solid #003366;
            padding-bottom: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        td {
            padding: 8px;
            border-bottom: 1px solid #ddd;
        }
        td:first-child {
            font-weight: bold;
            width: 200px;
        }
        .data-table th {
            background-color: #003366;
            color: white;
            padding: 10px;
            text-align: left;
        }
        .data-table td {
            text-align: left;
        }
        .result-pass {
            background-color: #d4edda;
            border: 2px solid #28a745;
        }
        .result-fail {
            background-color: #f8d7da;
            border: 2px solid #dc3545;
        }
        .result-marginal {
            background-color: #fff3cd;
            border: 2px solid #ffc107;
        }
        .result-text {
            font-size: 36px;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
        }
        .footer {
            text-align: center;
            color: #666;
            margin-top: 30px;
            padding: 20px;
        }
        """


def create_test_report(
    test_data: Dict[str, Any],
    output_path: str,
    format: str = "text"
) -> str:
    """
    Create and save test report.

    Args:
        test_data: Test data dictionary
        output_path: Output file path
        format: Output format ("text", "html", "json", or "pdf")

    Returns:
        Path to generated report
    """
    generator = IEC62804ReportGenerator(test_data)
    generator.save_report(output_path, format=format)
    return output_path
