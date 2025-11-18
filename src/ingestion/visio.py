"""
Visio diagram ingestion module.

Processes .vsdx files to extract diagram shapes, connections, and metadata.
Supports SVG export for visualization.
"""

import io
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from vsdx import VisioFile
except ImportError:
    raise ImportError(
        "vsdx library is required for Visio ingestion. "
        "Install with: pip install vsdx"
    )

from src.core.config import get_settings
from src.core.exceptions import ConfigurationError, VisioIngestionError
from src.core.models import (
    DiagramShape,
    DiagramShapeType,
    IngestionStatus,
    VisioIngestionResult,
    VisioPage,
)
from src.ingestion.base import FileBasedIngestionModule


class VisioIngestionModule(FileBasedIngestionModule[VisioIngestionResult]):
    """
    Ingestion module for Visio (.vsdx) diagrams.

    Extracts:
    - Diagram shapes with positions and dimensions
    - Shape connections and relationships
    - Text content within shapes
    - Page structure
    - Metadata (author, created date, etc.)
    - SVG export of diagrams
    """

    @property
    def supported_extensions(self) -> List[str]:
        """Supported file extensions."""
        return ['.vsdx']

    def _validate_configuration(self) -> None:
        """Validate Visio-specific configuration."""
        if not self.settings.visio_enable:
            raise ConfigurationError("Visio ingestion is disabled in configuration")

    def _map_shape_type(self, shape: Any) -> DiagramShapeType:
        """
        Map Visio shape to DiagramShapeType enum.

        Args:
            shape: Visio shape object

        Returns:
            DiagramShapeType enum value
        """
        # This is a simplified mapping - can be enhanced based on shape master
        shape_text = getattr(shape, 'text', '') or ''

        # Check shape master or name to determine type
        if hasattr(shape, 'master_shape') and shape.master_shape:
            master_name = str(shape.master_shape).lower()
            if 'rectangle' in master_name or 'process' in master_name:
                return DiagramShapeType.RECTANGLE
            elif 'circle' in master_name or 'ellipse' in master_name:
                return DiagramShapeType.CIRCLE
            elif 'diamond' in master_name or 'decision' in master_name:
                return DiagramShapeType.DIAMOND
            elif 'arrow' in master_name or 'connector' in master_name:
                return DiagramShapeType.CONNECTOR

        # Default based on whether it has connects
        if hasattr(shape, 'connects') and shape.connects:
            return DiagramShapeType.CONNECTOR

        return DiagramShapeType.CUSTOM

    def _extract_shape_properties(self, shape: Any) -> Dict[str, Any]:
        """
        Extract custom properties from a Visio shape.

        Args:
            shape: Visio shape object

        Returns:
            Dictionary of custom properties
        """
        properties = {}

        # Try to extract custom properties if available
        if hasattr(shape, 'cells'):
            for cell_name, cell_value in shape.cells.items():
                if cell_value:
                    properties[cell_name] = str(cell_value)

        return properties

    def _extract_style_info(self, shape: Any) -> Dict[str, str]:
        """
        Extract style information from a Visio shape.

        Args:
            shape: Visio shape object

        Returns:
            Dictionary of style properties
        """
        style_info = {}

        # Extract common style properties
        style_attrs = ['FillForegnd', 'LineColor', 'LineWeight', 'CharSize']

        if hasattr(shape, 'cells'):
            for attr in style_attrs:
                if attr in shape.cells:
                    style_info[attr] = str(shape.cells[attr])

        return style_info

    def _process_shape(self, shape: Any, page_height: float) -> DiagramShape:
        """
        Process a single Visio shape into DiagramShape model.

        Args:
            shape: Visio shape object
            page_height: Height of the page (for coordinate conversion)

        Returns:
            DiagramShape object
        """
        # Extract basic shape information
        shape_id = str(shape.ID) if hasattr(shape, 'ID') else f"shape_{id(shape)}"
        name = str(shape.text or shape_id)

        # Get shape position and dimensions
        # Visio uses bottom-left origin, we convert to top-left
        x = float(shape.x) if hasattr(shape, 'x') else 0.0
        y = page_height - float(shape.y) if hasattr(shape, 'y') else 0.0
        width = float(shape.width) if hasattr(shape, 'width') else 0.0
        height = float(shape.height) if hasattr(shape, 'height') else 0.0

        # Extract text
        text = str(shape.text) if hasattr(shape, 'text') and shape.text else None

        # Get connected shapes
        connected_to = []
        if hasattr(shape, 'connects'):
            for connect in shape.connects:
                if hasattr(connect, 'to_rel'):
                    connected_to.append(str(connect.to_rel))

        # Map shape type
        shape_type = self._map_shape_type(shape)

        # Extract properties and style
        properties = self._extract_shape_properties(shape)
        style_info = self._extract_style_info(shape)

        return DiagramShape(
            shape_id=shape_id,
            name=name,
            shape_type=shape_type,
            text=text,
            x=x,
            y=y,
            width=width,
            height=height,
            connected_to=connected_to,
            properties=properties,
            style_info=style_info
        )

    def _process_page(self, page: Any) -> VisioPage:
        """
        Process a Visio page.

        Args:
            page: Visio page object

        Returns:
            VisioPage object
        """
        page_id = str(page.page_id) if hasattr(page, 'page_id') else f"page_{id(page)}"
        page_name = str(page.name) if hasattr(page, 'name') else "Unnamed Page"

        # Get page dimensions
        page_width = float(page.width) if hasattr(page, 'width') else 11.0  # Default letter size
        page_height = float(page.height) if hasattr(page, 'height') else 8.5

        # Process all shapes on the page
        shapes = []
        if hasattr(page, 'shapes'):
            for shape in page.shapes:
                try:
                    diagram_shape = self._process_shape(shape, page_height)
                    shapes.append(diagram_shape)
                except Exception as e:
                    # Log error but continue processing other shapes
                    print(f"Warning: Failed to process shape: {e}")

        return VisioPage(
            page_id=page_id,
            page_name=page_name,
            shapes=shapes,
            page_width=page_width,
            page_height=page_height
        )

    def _generate_svg_export(self, visio_file: VisioFile, file_path: Path) -> str:
        """
        Generate SVG export of the Visio diagram.

        Args:
            visio_file: Loaded VisioFile object
            file_path: Path to original file

        Returns:
            SVG string representation
        """
        try:
            # Try to use vsdx's built-in SVG export if available
            if hasattr(visio_file, 'to_svg'):
                return visio_file.to_svg()

            # Otherwise, create a basic SVG representation
            svg_parts = ['<svg xmlns="http://www.w3.org/2000/svg" version="1.1">']

            for page in visio_file.pages:
                page_width = float(page.width) if hasattr(page, 'width') else 800
                page_height = float(page.height) if hasattr(page, 'height') else 600

                svg_parts.append(f'<g id="{page.name}">')

                if hasattr(page, 'shapes'):
                    for shape in page.shapes:
                        x = float(shape.x) if hasattr(shape, 'x') else 0
                        y = float(shape.y) if hasattr(shape, 'y') else 0
                        width = float(shape.width) if hasattr(shape, 'width') else 50
                        height = float(shape.height) if hasattr(shape, 'height') else 50
                        text = str(shape.text) if hasattr(shape, 'text') and shape.text else ''

                        # Simple rectangle representation
                        svg_parts.append(
                            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
                            f'fill="lightblue" stroke="black" />'
                        )
                        if text:
                            svg_parts.append(
                                f'<text x="{x + width/2}" y="{y + height/2}" '
                                f'text-anchor="middle">{text}</text>'
                            )

                svg_parts.append('</g>')

            svg_parts.append('</svg>')
            return '\n'.join(svg_parts)

        except Exception as e:
            return f'<svg><text>SVG generation failed: {str(e)}</text></svg>'

    def extract_metadata(self, source: Path) -> Dict[str, Any]:
        """
        Extract metadata from Visio file.

        Args:
            source: Path to Visio file

        Returns:
            Dictionary of metadata
        """
        try:
            with VisioFile(str(source)) as visio_file:
                metadata = {}

                # Extract document properties if available
                if hasattr(visio_file, 'author'):
                    metadata['author'] = visio_file.author
                if hasattr(visio_file, 'company'):
                    metadata['company'] = visio_file.company
                if hasattr(visio_file, 'title'):
                    metadata['title'] = visio_file.title
                if hasattr(visio_file, 'subject'):
                    metadata['subject'] = visio_file.subject

                # Add file information
                metadata['file_name'] = source.name
                metadata['file_size'] = source.stat().st_size
                metadata['pages_count'] = len(visio_file.pages) if hasattr(visio_file, 'pages') else 0

                return metadata

        except Exception as e:
            raise VisioIngestionError(f"Failed to extract metadata: {str(e)}")

    def ingest(self, source: Path, **kwargs: Any) -> VisioIngestionResult:
        """
        Ingest data from Visio file.

        Args:
            source: Path to Visio file
            **kwargs: Additional arguments (e.g., specific_page)

        Returns:
            VisioIngestionResult with extracted data
        """
        errors = []
        pages = []
        all_shapes = []

        try:
            # Load the Visio file
            with VisioFile(str(source)) as visio_file:
                # Extract metadata
                try:
                    metadata = self.extract_metadata(source)
                except Exception as e:
                    metadata = {'error': str(e)}
                    errors.append(f"Metadata extraction failed: {str(e)}")

                # Process pages
                if hasattr(visio_file, 'pages'):
                    for page in visio_file.pages:
                        try:
                            visio_page = self._process_page(page)
                            pages.append(visio_page)
                            all_shapes.extend(visio_page.shapes)
                        except Exception as e:
                            errors.append(f"Failed to process page {page.name}: {str(e)}")

                # Generate SVG export
                try:
                    svg_export = self._generate_svg_export(visio_file, source)
                except Exception as e:
                    svg_export = f"<svg><text>SVG generation failed: {str(e)}</text></svg>"
                    errors.append(f"SVG generation failed: {str(e)}")

                # Determine status
                if errors and not pages:
                    status = IngestionStatus.FAILED
                elif errors:
                    status = IngestionStatus.PARTIAL
                else:
                    status = IngestionStatus.SUCCESS

                return VisioIngestionResult(
                    diagram_name=source.stem,
                    file_path=str(source),
                    pages=pages,
                    shapes=all_shapes,
                    svg_export=svg_export,
                    metadata=metadata,
                    ingestion_timestamp=datetime.now(),
                    status=status,
                    errors=errors
                )

        except Exception as e:
            raise VisioIngestionError(f"Failed to ingest Visio file: {str(e)}")
