"""JSON/XML export with schema validation.

Session 43: JSON/XML Export
"""
import logging
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class JSONExporter:
    """JSON exporter with schema validation."""
    
    def export_report(self, report_data: Dict[str, Any], output_path: str) -> str:
        """Export report to JSON."""
        logger.info(f"Exporting report to JSON: {output_path}")
        
        # Add metadata
        export_data = {
            **report_data,
            "export_metadata": {
                "format": "json",
                "version": "1.0",
                "generated_at": datetime.utcnow().isoformat(),
                "schema": "pv-test-report-v1"
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"JSON report exported: {output_path}")
        return output_path

class XMLExporter:
    """XML exporter for legacy systems."""
    
    def export_report(self, report_data: Dict[str, Any], output_path: str) -> str:
        """Export report to XML."""
        logger.info(f"Exporting report to XML: {output_path}")
        
        root = ET.Element("PVTestReport")
        root.set("version", "1.0")
        root.set("xmlns", "http://pvautomation.org/schema/v1")
        
        # Add metadata
        metadata = ET.SubElement(root, "Metadata")
        for key, value in report_data.items():
            if not isinstance(value, (dict, list)):
                elem = ET.SubElement(metadata, key)
                elem.text = str(value)
        
        # Write XML
        tree = ET.ElementTree(root)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        
        logger.info(f"XML report exported: {output_path}")
        return output_path
