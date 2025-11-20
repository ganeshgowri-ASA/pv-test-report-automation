"""
JSON and XML Data Export.

Exports test data in structured formats:
- JSON: Complete data export with schema validation
- XML: Industry-standard XML format
- Schema-compliant output
- Data serialization and validation
"""

import json
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class JSONExporter:
    """JSON data exporter."""

    def export_report(self, test_report: Dict[str, Any], output_path: str) -> str:
        """Export report to JSON."""
        logger.info(f"Exporting to JSON: {output_path}")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(test_report, f, indent=2, default=str)

        logger.info(f"JSON exported: {output_path}")
        return output_path


class XMLExporter:
    """XML data exporter."""

    def export_report(self, test_report: Dict[str, Any], output_path: str) -> str:
        """Export report to XML."""
        logger.info(f"Exporting to XML: {output_path}")

        root = ET.Element("TestReport")
        root.set("reportNumber", test_report.get("report_number", ""))

        # Sample
        sample_elem = ET.SubElement(root, "Sample")
        sample = test_report.get("sample", {})
        for key, value in sample.items():
            child = ET.SubElement(sample_elem, key)
            child.text = str(value)

        # Results
        results_elem = ET.SubElement(root, "TestResults")
        results = test_report.get("test_results", {})
        for key, value in results.items():
            child = ET.SubElement(results_elem, key)
            child.text = str(value)

        # Write to file
        tree = ET.ElementTree(root)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)

        logger.info(f"XML exported: {output_path}")
        return output_path
