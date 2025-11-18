"""
Microsoft Visio file parser for extracting diagram data.

Supports .vsdx and .vsd files, extracting shapes, connectors, text,
and converting diagrams to SVG/PNG formats for embedding in reports.
"""

import hashlib
import io
import logging
import os
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

from ingestion.models import (
    DiagramConnector,
    DiagramShape,
    ProcessFlowStep,
    VisioIngestionResult,
    VisioParsingError,
)

logger = logging.getLogger(__name__)


class VisioIngestion:
    """
    Parse Microsoft Visio diagrams and extract structured data.

    Supports:
    - .vsdx files (Office Open XML format)
    - Shape and connector extraction
    - Text content extraction
    - SVG export
    - Process flow diagram analysis
    """

    # XML namespaces used in .vsdx files
    NAMESPACES = {
        'v': 'http://schemas.microsoft.com/office/visio/2012/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
    }

    # Shape type mapping based on master names
    SHAPE_TYPE_MAP = {
        'Process': 'process',
        'Decision': 'decision',
        'Start/End': 'start_end',
        'Document': 'document',
        'Data': 'data',
        'Predefined Process': 'predefined_process',
        'Connector': 'connector',
        'Rectangle': 'rectangle',
        'Circle': 'circle',
        'Diamond': 'diamond',
    }

    def __init__(self, file_path: str):
        """
        Initialize Visio parser.

        Args:
            file_path: Path to Visio file (.vsdx)

        Raises:
            VisioParsingError: If file doesn't exist or is invalid format
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise VisioParsingError(f"File not found: {file_path}")

        if self.file_path.suffix.lower() not in ['.vsdx']:
            raise VisioParsingError(f"Unsupported file format: {self.file_path.suffix}. Only .vsdx supported.")

        self.file_hash = self._calculate_file_hash()
        self.diagram_name = self.file_path.stem

    def _calculate_file_hash(self) -> str:
        """Calculate SHA-256 hash of the file"""
        sha256_hash = hashlib.sha256()
        with open(self.file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def extract_process_flow(self) -> VisioIngestionResult:
        """
        Extract complete diagram data including process flow analysis.

        Returns:
            VisioIngestionResult with all diagram data

        Raises:
            VisioParsingError: If parsing fails
        """
        try:
            shapes = []
            connectors = []
            text_content = []

            with zipfile.ZipFile(self.file_path, 'r') as vsdx_zip:
                # Extract pages
                pages = self._extract_pages(vsdx_zip)

                for page_name, page_xml in pages.items():
                    page_shapes, page_connectors, page_text = self._parse_page(page_xml)
                    shapes.extend(page_shapes)
                    connectors.extend(page_connectors)
                    text_content.extend(page_text)

            # Analyze process flow if this is a flowchart
            process_flow = self._analyze_process_flow(shapes, connectors)

            # Generate SVG representation
            svg_export = self._generate_svg(shapes, connectors)

            return VisioIngestionResult(
                diagram_name=self.diagram_name,
                file_path=str(self.file_path),
                shapes=shapes,
                connectors=connectors,
                text_content=text_content,
                svg_export=svg_export,
                metadata={
                    'page_count': len(pages),
                    'shape_count': len(shapes),
                    'connector_count': len(connectors),
                },
                file_hash=self.file_hash,
                process_flow=process_flow,
            )

        except zipfile.BadZipFile:
            raise VisioParsingError(f"Invalid .vsdx file: {self.file_path}")
        except Exception as e:
            raise VisioParsingError(f"Error parsing Visio file: {str(e)}")

    def _extract_pages(self, vsdx_zip: zipfile.ZipFile) -> Dict[str, ET.Element]:
        """Extract all pages from .vsdx file"""
        pages = {}

        try:
            # Read pages directory
            pages_dir = 'visio/pages/'
            for file_info in vsdx_zip.filelist:
                if file_info.filename.startswith(pages_dir) and file_info.filename.endswith('.xml'):
                    if 'page' in file_info.filename.lower() and 'rels' not in file_info.filename:
                        page_name = os.path.basename(file_info.filename)
                        with vsdx_zip.open(file_info.filename) as page_file:
                            page_xml = ET.parse(page_file).getroot()
                            pages[page_name] = page_xml
        except KeyError:
            logger.warning("No pages directory found in .vsdx file")

        return pages

    def _parse_page(self, page_xml: ET.Element) -> Tuple[List[DiagramShape], List[DiagramConnector], List[str]]:
        """Parse a single page to extract shapes and connectors"""
        shapes = []
        connectors = []
        text_content = []

        # Find all shapes in the page
        for shape_elem in page_xml.findall('.//v:Shape', self.NAMESPACES):
            shape_id = shape_elem.get('ID', '')

            # Extract text
            text = self._extract_shape_text(shape_elem)
            if text:
                text_content.append(text)

            # Check if this is a connector
            if self._is_connector(shape_elem):
                connector = self._parse_connector(shape_elem, text)
                if connector:
                    connectors.append(connector)
            else:
                # Regular shape
                shape = self._parse_shape(shape_elem, text)
                if shape:
                    shapes.append(shape)

        return shapes, connectors, text_content

    def _is_connector(self, shape_elem: ET.Element) -> bool:
        """Determine if a shape is a connector"""
        # Check for connector-specific elements
        line_elem = shape_elem.find('.//v:Cell[@N="BeginX"]', self.NAMESPACES)
        if line_elem is not None:
            return True

        # Check shape type
        shape_type = shape_elem.get('Type', '')
        if 'connector' in shape_type.lower():
            return True

        return False

    def _parse_shape(self, shape_elem: ET.Element, text: str) -> Optional[DiagramShape]:
        """Parse a shape element into DiagramShape model"""
        try:
            shape_id = shape_elem.get('ID', f'shape_{id(shape_elem)}')
            shape_type = self._determine_shape_type(shape_elem)

            # Extract position and size
            position_x = self._get_cell_value(shape_elem, 'PinX')
            position_y = self._get_cell_value(shape_elem, 'PinY')
            width = self._get_cell_value(shape_elem, 'Width')
            height = self._get_cell_value(shape_elem, 'Height')

            # Extract colors
            fill_color = self._get_cell_value(shape_elem, 'FillForegnd')
            line_color = self._get_cell_value(shape_elem, 'LineColor')

            properties = {
                'master': shape_elem.get('Master', ''),
                'name': shape_elem.get('Name', ''),
                'type': shape_elem.get('Type', ''),
            }

            return DiagramShape(
                shape_id=shape_id,
                shape_type=shape_type,
                text=text,
                properties=properties,
                position_x=position_x,
                position_y=position_y,
                width=width,
                height=height,
                fill_color=fill_color,
                line_color=line_color,
            )
        except Exception as e:
            logger.warning(f"Error parsing shape: {str(e)}")
            return None

    def _parse_connector(self, connector_elem: ET.Element, text: str) -> Optional[DiagramConnector]:
        """Parse a connector element into DiagramConnector model"""
        try:
            connector_id = connector_elem.get('ID', f'connector_{id(connector_elem)}')

            # Extract connection information
            from_shape = self._get_cell_value(connector_elem, 'BeginX')
            to_shape = self._get_cell_value(connector_elem, 'EndX')

            # Try to find actual connected shapes
            connects = connector_elem.findall('.//v:Connect', self.NAMESPACES)
            from_shape_id = ''
            to_shape_id = ''

            for connect in connects:
                if connect.get('FromSheet'):
                    if 'Begin' in connect.get('FromCell', ''):
                        from_shape_id = connect.get('ToSheet', '')
                    elif 'End' in connect.get('FromCell', ''):
                        to_shape_id = connect.get('ToSheet', '')

            if not from_shape_id:
                from_shape_id = f'unknown_from_{connector_id}'
            if not to_shape_id:
                to_shape_id = f'unknown_to_{connector_id}'

            connector_type = 'straight'  # Default

            properties = {
                'name': connector_elem.get('Name', ''),
            }

            return DiagramConnector(
                connector_id=connector_id,
                from_shape_id=from_shape_id,
                to_shape_id=to_shape_id,
                connector_type=connector_type,
                label=text if text else None,
                properties=properties,
            )
        except Exception as e:
            logger.warning(f"Error parsing connector: {str(e)}")
            return None

    def _extract_shape_text(self, shape_elem: ET.Element) -> str:
        """Extract text content from a shape"""
        text_parts = []

        # Look for text elements
        for text_elem in shape_elem.findall('.//v:Text', self.NAMESPACES):
            if text_elem.text:
                text_parts.append(text_elem.text.strip())
            # Also check for child elements with text
            for child in text_elem:
                if child.text:
                    text_parts.append(child.text.strip())
                if child.tail:
                    text_parts.append(child.tail.strip())

        return ' '.join(text_parts).strip()

    def _determine_shape_type(self, shape_elem: ET.Element) -> str:
        """Determine the type of shape based on its properties"""
        # Check master name
        master = shape_elem.get('Master', '')
        for master_key, shape_type in self.SHAPE_TYPE_MAP.items():
            if master_key.lower() in master.lower():
                return shape_type

        # Check shape name
        name = shape_elem.get('Name', '')
        for master_key, shape_type in self.SHAPE_TYPE_MAP.items():
            if master_key.lower() in name.lower():
                return shape_type

        return 'custom'

    def _get_cell_value(self, shape_elem: ET.Element, cell_name: str) -> Optional[float]:
        """Extract numeric value from a Cell element"""
        cell = shape_elem.find(f'.//v:Cell[@N="{cell_name}"]', self.NAMESPACES)
        if cell is not None:
            value = cell.get('V')
            if value:
                try:
                    return float(value)
                except ValueError:
                    pass
        return None

    def _analyze_process_flow(
        self,
        shapes: List[DiagramShape],
        connectors: List[DiagramConnector]
    ) -> Optional[List[ProcessFlowStep]]:
        """
        Analyze diagram to extract process flow steps.

        Returns None if this doesn't appear to be a process flow diagram.
        """
        # Check if this looks like a process flow
        process_shapes = [s for s in shapes if s.shape_type in ['process', 'decision', 'start_end']]
        if len(process_shapes) < 2:
            return None  # Not a process flow

        # Build connectivity map
        flow_map: Dict[str, List[str]] = {}
        reverse_map: Dict[str, List[str]] = {}

        for connector in connectors:
            if connector.from_shape_id not in flow_map:
                flow_map[connector.from_shape_id] = []
            flow_map[connector.from_shape_id].append(connector.to_shape_id)

            if connector.to_shape_id not in reverse_map:
                reverse_map[connector.to_shape_id] = []
            reverse_map[connector.to_shape_id].append(connector.from_shape_id)

        # Create shape lookup
        shape_map = {s.shape_id: s for s in shapes}

        # Build process flow steps
        steps = []
        step_number = 1

        for shape in shapes:
            if shape.shape_type in ['process', 'decision', 'start_end']:
                next_steps = flow_map.get(shape.shape_id, [])
                prev_steps = reverse_map.get(shape.shape_id, [])

                # For decision nodes, try to extract decision options
                decision_options = None
                if shape.shape_type == 'decision':
                    decision_options = {}
                    for next_id in next_steps:
                        # Try to find connector label
                        connector = next((c for c in connectors
                                        if c.from_shape_id == shape.shape_id
                                        and c.to_shape_id == next_id), None)
                        label = connector.label if connector and connector.label else "default"
                        decision_options[label] = next_id

                step = ProcessFlowStep(
                    step_number=step_number,
                    step_id=shape.shape_id,
                    step_type=shape.shape_type,
                    description=shape.text,
                    next_steps=next_steps,
                    previous_steps=prev_steps,
                    decision_options=decision_options,
                    metadata={
                        'position_x': shape.position_x,
                        'position_y': shape.position_y,
                    }
                )
                steps.append(step)
                step_number += 1

        return steps if steps else None

    def _generate_svg(self, shapes: List[DiagramShape], connectors: List[DiagramConnector]) -> str:
        """
        Generate basic SVG representation of the diagram.

        This is a simplified SVG for visualization purposes.
        """
        # Calculate bounds
        max_x = max([s.position_x or 0 for s in shapes] + [100])
        max_y = max([s.position_y or 0 for s in shapes] + [100])

        # Add padding
        width = max_x + 50
        height = max_y + 50

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<defs>',
            '<marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">',
            '<polygon points="0 0, 10 3, 0 6" fill="#333" />',
            '</marker>',
            '</defs>',
        ]

        # Draw connectors first (so they appear behind shapes)
        shape_map = {s.shape_id: s for s in shapes}
        for connector in connectors:
            from_shape = shape_map.get(connector.from_shape_id)
            to_shape = shape_map.get(connector.to_shape_id)

            if from_shape and to_shape:
                x1 = from_shape.position_x or 0
                y1 = from_shape.position_y or 0
                x2 = to_shape.position_x or 0
                y2 = to_shape.position_y or 0

                svg_parts.append(
                    f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                    f'stroke="#333" stroke-width="2" marker-end="url(#arrowhead)" />'
                )

        # Draw shapes
        for shape in shapes:
            x = shape.position_x or 0
            y = shape.position_y or 0
            w = shape.width or 30
            h = shape.height or 20

            # Adjust for center positioning
            x -= w / 2
            y -= h / 2

            fill = shape.fill_color or '#e0e0e0'
            if fill.startswith('#') is False:
                fill = '#e0e0e0'

            if shape.shape_type == 'decision':
                # Diamond
                points = f"{x+w/2},{y} {x+w},{y+h/2} {x+w/2},{y+h} {x},{y+h/2}"
                svg_parts.append(
                    f'<polygon points="{points}" fill="{fill}" stroke="#333" stroke-width="2" />'
                )
            elif shape.shape_type in ['start_end', 'circle']:
                # Ellipse
                svg_parts.append(
                    f'<ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" '
                    f'fill="{fill}" stroke="#333" stroke-width="2" />'
                )
            else:
                # Rectangle (default)
                svg_parts.append(
                    f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
                    f'fill="{fill}" stroke="#333" stroke-width="2" rx="5" />'
                )

            # Add text
            if shape.text:
                text = shape.text[:50]  # Truncate long text
                svg_parts.append(
                    f'<text x="{x+w/2}" y="{y+h/2}" '
                    f'text-anchor="middle" dominant-baseline="middle" '
                    f'font-family="Arial" font-size="10" fill="#333">{text}</text>'
                )

        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)

    def export_to_png(self, output_path: str, width: int = 1024, height: int = 768) -> str:
        """
        Export diagram to PNG format.

        Note: Requires cairosvg library for SVG to PNG conversion.

        Args:
            output_path: Output PNG file path
            width: Output width in pixels
            height: Output height in pixels

        Returns:
            Path to exported PNG file
        """
        try:
            import cairosvg
        except ImportError:
            raise VisioParsingError(
                "cairosvg library required for PNG export. "
                "Install with: pip install cairosvg"
            )

        result = self.extract_process_flow()
        if not result.svg_export:
            raise VisioParsingError("No SVG data available for export")

        cairosvg.svg2png(
            bytestring=result.svg_export.encode('utf-8'),
            write_to=output_path,
            output_width=width,
            output_height=height,
        )

        return output_path
