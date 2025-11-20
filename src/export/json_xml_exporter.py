"""
JSON/XML Exporter Module

Provides JSON and XML export functionality with schema validation.
Includes API-ready formats and schema validation.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False

from .base_exporter import (
    BaseExporter, ExportFormat, ExportOptions, ExportRegistry
)


logger = logging.getLogger(__name__)


@ExportRegistry.register(ExportFormat.JSON)
class JSONExporter(BaseExporter):
    """JSON export engine with schema validation."""

    def __init__(self, template_manager=None):
        """
        Initialize JSON exporter.

        Args:
            template_manager: Template manager instance
        """
        super().__init__(template_manager)
        self.schema: Optional[Dict[str, Any]] = None

    @property
    def format_type(self) -> ExportFormat:
        """Get export format type."""
        return ExportFormat.JSON

    @property
    def file_extension(self) -> str:
        """Get file extension."""
        return "json"

    def export(self, data: Dict[str, Any], options: ExportOptions) -> Path:
        """
        Export data to JSON.

        Args:
            data: Data to export
            options: Export options

        Returns:
            Path to exported JSON file
        """
        self._validate_data(data)
        self._ensure_output_directory(options.output_path)

        logger.info(f"Exporting JSON: {options.output_path}")

        # Add metadata
        if options.include_metadata:
            data = self._add_metadata(data)

        # Validate against schema if available
        if self.schema and JSONSCHEMA_AVAILABLE:
            try:
                jsonschema.validate(instance=data, schema=self.schema)
                logger.info("JSON schema validation passed")
            except jsonschema.exceptions.ValidationError as e:
                logger.error(f"JSON schema validation failed: {e}")
                if not options.custom_params.get("ignore_schema_errors", False):
                    raise

        # Prepare data for serialization
        serializable_data = self._make_serializable(data)

        # Write JSON file
        indent = options.custom_params.get("indent", 2)
        ensure_ascii = options.custom_params.get("ensure_ascii", False)

        with open(options.output_path, 'w', encoding='utf-8') as f:
            json.dump(
                serializable_data,
                f,
                indent=indent,
                ensure_ascii=ensure_ascii,
                sort_keys=options.custom_params.get("sort_keys", False)
            )

        # Validate output
        if not self.validate_output(options.output_path):
            raise ValueError(f"Invalid JSON output: {options.output_path}")

        logger.info(f"JSON export completed: {options.output_path}")
        return options.output_path

    def _make_serializable(self, data: Any) -> Any:
        """
        Convert data to JSON-serializable format.

        Args:
            data: Data to convert

        Returns:
            Serializable data
        """
        if isinstance(data, dict):
            return {key: self._make_serializable(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._make_serializable(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, Path):
            return str(data)
        elif hasattr(data, '__dict__'):
            return self._make_serializable(data.__dict__)
        else:
            return data

    def validate_output(self, output_path: Path) -> bool:
        """
        Validate JSON output.

        Args:
            output_path: Path to JSON file

        Returns:
            True if valid
        """
        if not output_path.exists():
            return False

        if output_path.stat().st_size == 0:
            return False

        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True
        except json.JSONDecodeError as e:
            logger.error(f"JSON validation failed: {e}")
            return False

    def set_schema(self, schema: Dict[str, Any]):
        """
        Set JSON schema for validation.

        Args:
            schema: JSON schema dictionary
        """
        self.schema = schema
        logger.info("JSON schema set")

    def load_schema(self, schema_path: Path):
        """
        Load JSON schema from file.

        Args:
            schema_path: Path to schema file
        """
        with open(schema_path, 'r', encoding='utf-8') as f:
            self.schema = json.load(f)
        logger.info(f"JSON schema loaded from: {schema_path}")

    def generate_schema(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate JSON schema from data structure.

        Args:
            data: Sample data

        Returns:
            Generated schema
        """
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": self._generate_properties_schema(data)
        }
        return schema

    def _generate_properties_schema(self, data: Any) -> Dict[str, Any]:
        """Generate schema properties from data."""
        if isinstance(data, dict):
            properties = {}
            for key, value in data.items():
                properties[key] = self._generate_type_schema(value)
            return properties
        return {}

    def _generate_type_schema(self, value: Any) -> Dict[str, Any]:
        """Generate schema for value type."""
        if isinstance(value, bool):
            return {"type": "boolean"}
        elif isinstance(value, int):
            return {"type": "integer"}
        elif isinstance(value, float):
            return {"type": "number"}
        elif isinstance(value, str):
            return {"type": "string"}
        elif isinstance(value, list):
            if value:
                return {
                    "type": "array",
                    "items": self._generate_type_schema(value[0])
                }
            return {"type": "array"}
        elif isinstance(value, dict):
            return {
                "type": "object",
                "properties": self._generate_properties_schema(value)
            }
        else:
            return {"type": "string"}

    def pretty_print(self, json_path: Path, output_path: Optional[Path] = None) -> Path:
        """
        Pretty print JSON file.

        Args:
            json_path: Input JSON path
            output_path: Output path (optional)

        Returns:
            Path to pretty-printed file
        """
        if output_path is None:
            output_path = json_path

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)

        logger.info(f"JSON pretty-printed: {output_path}")
        return output_path

    def minify(self, json_path: Path, output_path: Optional[Path] = None) -> Path:
        """
        Minify JSON file.

        Args:
            json_path: Input JSON path
            output_path: Output path (optional)

        Returns:
            Path to minified file
        """
        if output_path is None:
            output_path = json_path.parent / f"{json_path.stem}.min.json"

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, separators=(',', ':'), ensure_ascii=False)

        logger.info(f"JSON minified: {output_path}")
        return output_path


@ExportRegistry.register(ExportFormat.XML)
class XMLExporter(BaseExporter):
    """XML export engine with schema validation."""

    def __init__(self, template_manager=None):
        """
        Initialize XML exporter.

        Args:
            template_manager: Template manager instance
        """
        super().__init__(template_manager)
        self.xsd_schema: Optional[str] = None

    @property
    def format_type(self) -> ExportFormat:
        """Get export format type."""
        return ExportFormat.XML

    @property
    def file_extension(self) -> str:
        """Get file extension."""
        return "xml"

    def export(self, data: Dict[str, Any], options: ExportOptions) -> Path:
        """
        Export data to XML.

        Args:
            data: Data to export
            options: Export options

        Returns:
            Path to exported XML file
        """
        self._validate_data(data)
        self._ensure_output_directory(options.output_path)

        logger.info(f"Exporting XML: {options.output_path}")

        # Add metadata
        if options.include_metadata:
            data = self._add_metadata(data)

        # Generate XML
        root_name = options.custom_params.get("root_element", "pv_test_report")
        root = self._dict_to_xml(data, root_name)

        # Pretty print XML
        xml_string = self._prettify_xml(root)

        # Validate against XSD if available
        if self.xsd_schema and LXML_AVAILABLE:
            try:
                self._validate_against_xsd(xml_string)
                logger.info("XML schema validation passed")
            except Exception as e:
                logger.error(f"XML schema validation failed: {e}")
                if not options.custom_params.get("ignore_schema_errors", False):
                    raise

        # Write XML file
        with open(options.output_path, 'w', encoding='utf-8') as f:
            f.write(xml_string)

        # Validate output
        if not self.validate_output(options.output_path):
            raise ValueError(f"Invalid XML output: {options.output_path}")

        logger.info(f"XML export completed: {options.output_path}")
        return options.output_path

    def _dict_to_xml(self, data: Any, tag_name: str = "item") -> ET.Element:
        """
        Convert dictionary to XML element.

        Args:
            data: Data to convert
            tag_name: Root tag name

        Returns:
            XML Element
        """
        # Clean tag name (remove invalid characters)
        tag_name = self._clean_tag_name(tag_name)

        if isinstance(data, dict):
            element = ET.Element(tag_name)

            for key, value in data.items():
                clean_key = self._clean_tag_name(key)

                if isinstance(value, dict):
                    child = self._dict_to_xml(value, clean_key)
                    element.append(child)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            child = self._dict_to_xml(item, clean_key)
                            element.append(child)
                        else:
                            child = ET.Element(clean_key)
                            child.text = str(item)
                            element.append(child)
                else:
                    child = ET.Element(clean_key)
                    child.text = str(value) if value is not None else ""
                    element.append(child)

            return element

        elif isinstance(data, list):
            element = ET.Element(tag_name)
            for item in data:
                child = self._dict_to_xml(item, "item")
                element.append(child)
            return element

        else:
            element = ET.Element(tag_name)
            element.text = str(data) if data is not None else ""
            return element

    def _clean_tag_name(self, name: str) -> str:
        """
        Clean tag name to be XML-compliant.

        Args:
            name: Original name

        Returns:
            Cleaned name
        """
        # Replace spaces and special characters with underscores
        cleaned = name.replace(" ", "_")
        cleaned = ''.join(c if c.isalnum() or c == '_' else '_' for c in cleaned)

        # Ensure it doesn't start with a number
        if cleaned and cleaned[0].isdigit():
            cleaned = f"_{cleaned}"

        return cleaned or "element"

    def _prettify_xml(self, element: ET.Element) -> str:
        """
        Pretty print XML element.

        Args:
            element: XML element

        Returns:
            Formatted XML string
        """
        rough_string = ET.tostring(element, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ", encoding=None)

    def _validate_against_xsd(self, xml_string: str):
        """
        Validate XML against XSD schema.

        Args:
            xml_string: XML content

        Raises:
            Exception if validation fails
        """
        if not LXML_AVAILABLE:
            logger.warning("lxml not available, skipping XSD validation")
            return

        schema_root = etree.XML(self.xsd_schema.encode('utf-8'))
        schema = etree.XMLSchema(schema_root)

        xml_root = etree.XML(xml_string.encode('utf-8'))
        schema.assertValid(xml_root)

    def validate_output(self, output_path: Path) -> bool:
        """
        Validate XML output.

        Args:
            output_path: Path to XML file

        Returns:
            True if valid
        """
        if not output_path.exists():
            return False

        if output_path.stat().st_size == 0:
            return False

        try:
            tree = ET.parse(str(output_path))
            root = tree.getroot()
            return root is not None
        except ET.ParseError as e:
            logger.error(f"XML validation failed: {e}")
            return False

    def set_xsd_schema(self, xsd_content: str):
        """
        Set XSD schema for validation.

        Args:
            xsd_content: XSD schema content
        """
        self.xsd_schema = xsd_content
        logger.info("XSD schema set")

    def load_xsd_schema(self, xsd_path: Path):
        """
        Load XSD schema from file.

        Args:
            xsd_path: Path to XSD file
        """
        with open(xsd_path, 'r', encoding='utf-8') as f:
            self.xsd_schema = f.read()
        logger.info(f"XSD schema loaded from: {xsd_path}")

    def xml_to_dict(self, xml_path: Path) -> Dict[str, Any]:
        """
        Convert XML file to dictionary.

        Args:
            xml_path: Path to XML file

        Returns:
            Dictionary representation
        """
        tree = ET.parse(str(xml_path))
        root = tree.getroot()
        return self._element_to_dict(root)

    def _element_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        """
        Convert XML element to dictionary.

        Args:
            element: XML element

        Returns:
            Dictionary representation
        """
        result = {}

        # Add attributes
        if element.attrib:
            result['@attributes'] = element.attrib

        # Add text content
        if element.text and element.text.strip():
            if len(element) == 0:  # No children
                return element.text.strip()
            else:
                result['#text'] = element.text.strip()

        # Add children
        children = {}
        for child in element:
            child_data = self._element_to_dict(child)

            if child.tag in children:
                # Multiple elements with same tag
                if not isinstance(children[child.tag], list):
                    children[child.tag] = [children[child.tag]]
                children[child.tag].append(child_data)
            else:
                children[child.tag] = child_data

        result.update(children)

        # If result only has one key and it's the text, return just the text
        if len(result) == 1 and '#text' in result:
            return result['#text']

        return result if result else None

    def transform_with_xslt(
        self,
        xml_path: Path,
        xslt_path: Path,
        output_path: Path
    ) -> Path:
        """
        Transform XML using XSLT.

        Args:
            xml_path: Input XML path
            xslt_path: XSLT stylesheet path
            output_path: Output path

        Returns:
            Path to transformed file
        """
        if not LXML_AVAILABLE:
            logger.warning("lxml not available, XSLT transformation not supported")
            return xml_path

        xml_doc = etree.parse(str(xml_path))
        xslt_doc = etree.parse(str(xslt_path))
        transform = etree.XSLT(xslt_doc)

        result = transform(xml_doc)

        with open(output_path, 'wb') as f:
            f.write(etree.tostring(result, pretty_print=True))

        logger.info(f"XML transformed: {output_path}")
        return output_path

    def add_namespace(
        self,
        xml_path: Path,
        namespace: str,
        prefix: str,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Add namespace to XML.

        Args:
            xml_path: Input XML path
            namespace: Namespace URI
            prefix: Namespace prefix
            output_path: Output path (optional)

        Returns:
            Path to output file
        """
        if output_path is None:
            output_path = xml_path

        # Register namespace
        ET.register_namespace(prefix, namespace)

        tree = ET.parse(str(xml_path))
        root = tree.getroot()

        # Add namespace to root
        root.attrib[f'xmlns:{prefix}'] = namespace

        tree.write(str(output_path), encoding='utf-8', xml_declaration=True)

        logger.info(f"Namespace added: {output_path}")
        return output_path


def create_api_response(
    data: Dict[str, Any],
    status: str = "success",
    message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create standardized API response format.

    Args:
        data: Response data
        status: Response status
        message: Optional message

    Returns:
        API response dictionary
    """
    response = {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "data": data
    }

    if message:
        response["message"] = message

    return response
