"""
Export Module Example Usage

Demonstrates how to use the export engines for various formats.
"""

from pathlib import Path
from datetime import datetime
import logging

from export import (
    PDFExporter,
    WordExporter,
    HTMLExporter,
    ExcelExporter,
    JSONExporter,
    XMLExporter,
    ExportOptions,
    ExportFormat,
    create_exporter,
    create_api_response
)


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def get_sample_data():
    """Get sample PV test report data."""
    return {
        "title": "PV System Test Report",
        "header": "Solar Installation Testing - Site A",
        "footer": f"Confidential - Generated {datetime.now().strftime('%Y-%m-%d')}",
        "author": "PV Test Automation System",
        "description": "Comprehensive testing and analysis of photovoltaic system",

        "summary": """
        This report presents the results of comprehensive testing performed on a 100kW
        photovoltaic system installation. Testing was conducted in accordance with
        IEC 62446 standards and local regulations. Overall system performance meets
        specifications with minor issues identified and documented below.
        """,

        "configuration": {
            "test_date": "2025-01-15",
            "location": "Test Site A, Solar Farm",
            "system_size_kw": 100,
            "module_count": 300,
            "module_type": "Monocrystalline 330W",
            "inverter_type": "String Inverter - 100kW",
            "inverter_count": 1,
            "mounting_type": "Ground Mount",
            "tilt_angle": 25,
            "azimuth": 180,
            "tested_by": "John Doe, Certified PV Inspector"
        },

        "test_results": [
            {
                "name": "Open Circuit Voltage (Voc)",
                "status": "PASS",
                "value": 42.5,
                "expected": 42.0,
                "unit": "V",
                "notes": "Within acceptable range (+1.2%)"
            },
            {
                "name": "Short Circuit Current (Isc)",
                "status": "PASS",
                "value": 9.8,
                "expected": 9.5,
                "unit": "A",
                "notes": "Good performance (+3.2%)"
            },
            {
                "name": "Maximum Power Point (Pmax)",
                "status": "PASS",
                "value": 325,
                "expected": 330,
                "unit": "W",
                "notes": "Within tolerance (-1.5%)"
            },
            {
                "name": "Insulation Resistance",
                "status": "FAIL",
                "value": 0.8,
                "expected": 1.0,
                "unit": "MΩ",
                "notes": "Below minimum threshold - requires attention"
            },
            {
                "name": "Ground Continuity",
                "status": "PASS",
                "value": 0.05,
                "expected": 0.1,
                "unit": "Ω",
                "notes": "Excellent ground connection"
            },
            {
                "name": "Polarity Check",
                "status": "PASS",
                "value": "Correct",
                "expected": "Correct",
                "unit": "",
                "notes": "All strings properly polarized"
            },
            {
                "name": "String Voltage Balance",
                "status": "PASS",
                "value": 0.5,
                "expected": 2.0,
                "unit": "%",
                "notes": "Excellent balance across strings"
            },
            {
                "name": "IV Curve Test",
                "status": "PASS",
                "value": "Normal",
                "expected": "Normal",
                "unit": "",
                "notes": "Curve shape indicates healthy modules"
            }
        ],

        "analysis": """
        Overall system performance is good with one area requiring immediate attention.
        The insulation resistance test failed to meet the minimum threshold of 1.0 MΩ,
        measuring only 0.8 MΩ. This could indicate moisture ingress or damaged module
        insulation and should be investigated promptly.

        All other electrical tests passed successfully. The system shows good voltage
        balance across strings and proper grounding. The IV curve analysis indicates
        healthy module performance with no signs of hot spots or significant degradation.
        """,

        "recommendations": [
            "Inspect and repair insulation on affected modules within 7 days",
            "Retest insulation resistance after repairs to confirm >1.0 MΩ",
            "Perform thermal imaging scan to identify any hot spots",
            "Schedule follow-up inspection in 30 days",
            "Document all repairs in system maintenance log"
        ],

        "charts": [
            {
                "title": "Test Results Summary",
                "description": "Distribution of test results",
                "type": "pie"
            },
            {
                "title": "String Voltage Comparison",
                "description": "Voltage measurements across all strings",
                "type": "bar"
            }
        ],

        "raw_data": [
            {"string": 1, "voltage": 420, "current": 9.7, "power": 4074},
            {"string": 2, "voltage": 421, "current": 9.8, "power": 4126},
            {"string": 3, "voltage": 419, "current": 9.6, "power": 4022},
            {"string": 4, "voltage": 422, "current": 9.9, "power": 4178}
        ],

        "appendix": {
            "test_equipment": "Fluke Solar Analyzer, Thermal Imager",
            "weather_conditions": "Clear sky, 25°C ambient, 1000 W/m² irradiance",
            "standards_referenced": "IEC 62446, NEC 690, Local Building Code"
        }
    }


def export_to_json(data, output_dir):
    """Export data to JSON format."""
    logger.info("=== Exporting to JSON ===")

    exporter = JSONExporter()

    # Basic export
    options = ExportOptions(
        output_path=output_dir / "report.json",
        include_metadata=True
    )

    result = exporter.export(data, options)
    logger.info(f"JSON exported: {result}")

    # Pretty printed version
    pretty_result = exporter.pretty_print(result)
    logger.info(f"Pretty JSON: {pretty_result}")

    # Minified version
    minified = exporter.minify(result)
    logger.info(f"Minified JSON: {minified}")

    # Generate schema
    schema = exporter.generate_schema(data)
    schema_path = output_dir / "schema.json"
    with open(schema_path, 'w') as f:
        import json
        json.dump(schema, f, indent=2)
    logger.info(f"Schema generated: {schema_path}")


def export_to_xml(data, output_dir):
    """Export data to XML format."""
    logger.info("=== Exporting to XML ===")

    exporter = XMLExporter()

    options = ExportOptions(
        output_path=output_dir / "report.xml",
        include_metadata=True,
        custom_params={"root_element": "pv_test_report"}
    )

    result = exporter.export(data, options)
    logger.info(f"XML exported: {result}")


def export_to_html(data, output_dir):
    """Export data to HTML format."""
    logger.info("=== Exporting to HTML ===")

    exporter = HTMLExporter()

    options = ExportOptions(
        output_path=output_dir / "report.html",
        include_metadata=True,
        include_charts=True
    )

    result = exporter.export(data, options)
    logger.info(f"HTML exported: {result}")
    logger.info(f"Open in browser: file://{result.absolute()}")


def export_to_pdf(data, output_dir):
    """Export data to PDF format."""
    logger.info("=== Exporting to PDF ===")

    try:
        from export.pdf_exporter import REPORTLAB_AVAILABLE, PDFEngine

        if not REPORTLAB_AVAILABLE:
            logger.warning("ReportLab not installed, skipping PDF export")
            logger.info("Install with: pip install reportlab")
            return

        exporter = PDFExporter(engine=PDFEngine.REPORTLAB)

        options = ExportOptions(
            output_path=output_dir / "report.pdf",
            include_metadata=True,
            include_charts=False,
            watermark=None
        )

        result = exporter.export(data, options)
        logger.info(f"PDF exported: {result}")

    except ImportError as e:
        logger.warning(f"PDF export not available: {e}")


def export_to_word(data, output_dir):
    """Export data to Word format."""
    logger.info("=== Exporting to Word ===")

    try:
        from export.word_exporter import DOCX_AVAILABLE

        if not DOCX_AVAILABLE:
            logger.warning("python-docx not installed, skipping Word export")
            logger.info("Install with: pip install python-docx")
            return

        exporter = WordExporter()

        options = ExportOptions(
            output_path=output_dir / "report.docx",
            include_metadata=True,
            include_charts=False
        )

        result = exporter.export(data, options)
        logger.info(f"Word exported: {result}")

    except ImportError as e:
        logger.warning(f"Word export not available: {e}")


def export_to_excel(data, output_dir):
    """Export data to Excel format."""
    logger.info("=== Exporting to Excel ===")

    try:
        from export.excel_exporter import OPENPYXL_AVAILABLE, ExcelEngine

        if not OPENPYXL_AVAILABLE:
            logger.warning("openpyxl not installed, skipping Excel export")
            logger.info("Install with: pip install openpyxl")
            return

        exporter = ExcelExporter(engine=ExcelEngine.OPENPYXL)

        options = ExportOptions(
            output_path=output_dir / "report.xlsx",
            include_metadata=True,
            include_charts=True
        )

        result = exporter.export(data, options)
        logger.info(f"Excel exported: {result}")

    except ImportError as e:
        logger.warning(f"Excel export not available: {e}")


def demonstrate_batch_export(output_dir):
    """Demonstrate batch export functionality."""
    logger.info("=== Demonstrating Batch Export ===")

    # Create multiple test reports
    data_items = [
        {**get_sample_data(), "name": f"report_{i}", "title": f"PV Test Report #{i}"}
        for i in range(1, 4)
    ]

    # Batch export to JSON
    exporter = JSONExporter()

    batch_dir = output_dir / "batch"
    options_template = ExportOptions(
        output_path=batch_dir / "dummy.json",
        include_metadata=True
    )

    results = exporter.batch_export(data_items, batch_dir, options_template)
    logger.info(f"Batch exported {len(results)} files to: {batch_dir}")


def demonstrate_progress_tracking(output_dir):
    """Demonstrate progress tracking."""
    logger.info("=== Demonstrating Progress Tracking ===")

    def progress_callback(progress):
        logger.info(
            f"Progress: {progress.progress_percentage:.1f}% - "
            f"{progress.current_item} ({progress.completed_items}/{progress.total_items})"
        )

    exporter = JSONExporter()
    exporter.add_progress_callback(progress_callback)

    data_items = [
        {**get_sample_data(), "name": f"report_{i}"}
        for i in range(5)
    ]

    progress_dir = output_dir / "progress"
    options_template = ExportOptions(output_path=progress_dir / "dummy.json")

    results = exporter.batch_export(data_items, progress_dir, options_template)
    logger.info(f"Completed with progress tracking: {len(results)} files")


def demonstrate_api_response():
    """Demonstrate API response format."""
    logger.info("=== Demonstrating API Response ===")

    data = get_sample_data()

    # Success response
    response = create_api_response(
        data=data,
        status="success",
        message="Report generated successfully"
    )

    logger.info("API Response:")
    import json
    logger.info(json.dumps(response, indent=2, default=str))


def main():
    """Main demonstration function."""
    # Create output directory
    output_dir = Path("./export_examples")
    output_dir.mkdir(exist_ok=True)

    logger.info("=" * 60)
    logger.info("PV Test Report Export Module - Example Usage")
    logger.info("=" * 60)

    # Get sample data
    data = get_sample_data()

    # Export to all formats
    export_to_json(data, output_dir)
    export_to_xml(data, output_dir)
    export_to_html(data, output_dir)
    export_to_pdf(data, output_dir)
    export_to_word(data, output_dir)
    export_to_excel(data, output_dir)

    # Demonstrate advanced features
    demonstrate_batch_export(output_dir)
    demonstrate_progress_tracking(output_dir)
    demonstrate_api_response()

    logger.info("=" * 60)
    logger.info(f"All examples completed! Check output in: {output_dir.absolute()}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
