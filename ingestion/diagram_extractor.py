"""
Diagram metadata extractor for process flow analysis.

Provides high-level extraction and analysis of diagrams from various sources.
Combines capabilities of Visio parser and other diagram sources.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from ingestion.models import (
    DiagramExtractionError,
    DiagramShape,
    ProcessFlowStep,
    VisioIngestionResult,
)
from ingestion.visio_parser import VisioIngestion

logger = logging.getLogger(__name__)


class DiagramExtractor:
    """
    High-level diagram extraction and analysis tool.

    Supports:
    - Process flow extraction
    - Test procedure diagrams
    - Equipment setup diagrams
    - Safety protocol flowcharts
    - Decision tree analysis
    """

    def __init__(self):
        """Initialize diagram extractor"""
        self.supported_formats = ['.vsdx']

    def extract_from_file(self, file_path: str) -> VisioIngestionResult:
        """
        Extract diagram data from file.

        Automatically detects file format and uses appropriate parser.

        Args:
            file_path: Path to diagram file

        Returns:
            VisioIngestionResult with diagram data

        Raises:
            DiagramExtractionError: If extraction fails
        """
        path = Path(file_path)
        if not path.exists():
            raise DiagramExtractionError(f"File not found: {file_path}")

        file_ext = path.suffix.lower()

        if file_ext == '.vsdx':
            return self._extract_visio(file_path)
        else:
            raise DiagramExtractionError(
                f"Unsupported file format: {file_ext}. "
                f"Supported formats: {', '.join(self.supported_formats)}"
            )

    def _extract_visio(self, file_path: str) -> VisioIngestionResult:
        """Extract from Visio file"""
        try:
            visio = VisioIngestion(file_path)
            return visio.extract_process_flow()
        except Exception as e:
            raise DiagramExtractionError(f"Visio extraction failed: {str(e)}")

    def extract_test_procedure(self, file_path: str) -> List[ProcessFlowStep]:
        """
        Extract test procedure as sequential steps.

        Specifically designed for test procedure flowcharts used in PV testing.

        Args:
            file_path: Path to test procedure diagram

        Returns:
            List of ProcessFlowStep objects in execution order

        Raises:
            DiagramExtractionError: If extraction fails
        """
        result = self.extract_from_file(file_path)

        if not result.process_flow:
            raise DiagramExtractionError(
                "No process flow detected. File may not be a procedure flowchart."
            )

        # Sort steps by finding start node and following connections
        ordered_steps = self._order_process_steps(result.process_flow)

        return ordered_steps

    def extract_equipment_setup(self, file_path: str) -> Dict[str, any]:
        """
        Extract equipment setup diagram metadata.

        Args:
            file_path: Path to equipment diagram

        Returns:
            Dictionary with equipment connections and setup data

        Raises:
            DiagramExtractionError: If extraction fails
        """
        result = self.extract_from_file(file_path)

        # Build equipment map
        equipment = []
        connections = []

        for shape in result.shapes:
            # Identify equipment shapes (typically rectangles with equipment names)
            if shape.text and len(shape.text) > 0:
                equipment.append({
                    'id': shape.shape_id,
                    'name': shape.text,
                    'type': shape.shape_type,
                    'properties': shape.properties,
                })

        for connector in result.connectors:
            connections.append({
                'from': connector.from_shape_id,
                'to': connector.to_shape_id,
                'label': connector.label,
            })

        return {
            'diagram_name': result.diagram_name,
            'equipment': equipment,
            'connections': connections,
            'total_items': len(equipment),
        }

    def extract_decision_tree(self, file_path: str) -> Dict[str, any]:
        """
        Extract decision tree logic from diagram.

        Used for pass/fail decision logic in test procedures.

        Args:
            file_path: Path to decision tree diagram

        Returns:
            Dictionary with decision nodes and branches

        Raises:
            DiagramExtractionError: If extraction fails
        """
        result = self.extract_from_file(file_path)

        if not result.process_flow:
            raise DiagramExtractionError("No process flow detected in diagram")

        # Extract decision nodes
        decision_nodes = []
        for step in result.process_flow:
            if step.step_type == 'decision' and step.decision_options:
                decision_nodes.append({
                    'step_id': step.step_id,
                    'description': step.description,
                    'options': step.decision_options,
                    'branches': len(step.decision_options),
                })

        return {
            'diagram_name': result.diagram_name,
            'total_decisions': len(decision_nodes),
            'decision_nodes': decision_nodes,
        }

    def extract_safety_protocol(self, file_path: str) -> List[Dict[str, any]]:
        """
        Extract safety protocol steps from flowchart.

        Args:
            file_path: Path to safety protocol diagram

        Returns:
            List of safety steps in order

        Raises:
            DiagramExtractionError: If extraction fails
        """
        steps = self.extract_test_procedure(file_path)

        # Format as safety steps
        safety_steps = []
        for step in steps:
            safety_steps.append({
                'step_number': step.step_number,
                'description': step.description,
                'type': step.step_type,
                'is_critical': 'warning' in step.description.lower() or 'danger' in step.description.lower(),
            })

        return safety_steps

    def _order_process_steps(self, steps: List[ProcessFlowStep]) -> List[ProcessFlowStep]:
        """
        Order process steps by following flow from start to end.

        Uses breadth-first traversal from start node.

        Args:
            steps: Unordered list of process steps

        Returns:
            Ordered list of steps
        """
        if not steps:
            return []

        # Build step map
        step_map = {step.step_id: step for step in steps}

        # Find start node (start_end type with no previous steps)
        start_nodes = [s for s in steps if s.step_type == 'start_end' and not s.previous_steps]

        if not start_nodes:
            # If no clear start, use first step
            logger.warning("No clear start node found, using first step")
            return steps

        # Breadth-first traversal
        ordered = []
        visited = set()
        queue = [start_nodes[0].step_id]

        while queue:
            current_id = queue.pop(0)

            if current_id in visited:
                continue

            if current_id not in step_map:
                continue

            current_step = step_map[current_id]
            ordered.append(current_step)
            visited.add(current_id)

            # Add next steps to queue
            for next_id in current_step.next_steps:
                if next_id not in visited:
                    queue.append(next_id)

        # Add any unvisited steps at the end
        for step in steps:
            if step.step_id not in visited:
                ordered.append(step)

        # Renumber steps
        for i, step in enumerate(ordered, start=1):
            step.step_number = i

        return ordered

    def compare_diagrams(
        self,
        file_path1: str,
        file_path2: str
    ) -> Dict[str, any]:
        """
        Compare two diagrams and report differences.

        Useful for version control of test procedures.

        Args:
            file_path1: First diagram file
            file_path2: Second diagram file

        Returns:
            Dictionary with comparison results

        Raises:
            DiagramExtractionError: If comparison fails
        """
        result1 = self.extract_from_file(file_path1)
        result2 = self.extract_from_file(file_path2)

        differences = {
            'shape_count_diff': len(result2.shapes) - len(result1.shapes),
            'connector_count_diff': len(result2.connectors) - len(result1.connectors),
            'text_changes': [],
        }

        # Compare text content
        text1_set = set(result1.text_content)
        text2_set = set(result2.text_content)

        added_text = text2_set - text1_set
        removed_text = text1_set - text2_set

        if added_text:
            differences['text_changes'].append({
                'type': 'added',
                'items': list(added_text),
            })

        if removed_text:
            differences['text_changes'].append({
                'type': 'removed',
                'items': list(removed_text),
            })

        return differences

    def export_diagram_summary(self, file_path: str) -> Dict[str, any]:
        """
        Generate summary report of diagram contents.

        Args:
            file_path: Path to diagram file

        Returns:
            Summary dictionary

        Raises:
            DiagramExtractionError: If extraction fails
        """
        result = self.extract_from_file(file_path)

        # Count shape types
        shape_types = {}
        for shape in result.shapes:
            shape_type = shape.shape_type
            shape_types[shape_type] = shape_types.get(shape_type, 0) + 1

        # Analyze process flow
        has_process_flow = result.process_flow is not None
        decision_count = 0
        if has_process_flow:
            decision_count = sum(1 for step in result.process_flow if step.step_type == 'decision')

        summary = {
            'diagram_name': result.diagram_name,
            'file_path': result.file_path,
            'total_shapes': len(result.shapes),
            'total_connectors': len(result.connectors),
            'shape_types': shape_types,
            'has_process_flow': has_process_flow,
            'decision_points': decision_count,
            'text_elements': len(result.text_content),
            'file_hash': result.file_hash,
            'metadata': result.metadata,
        }

        return summary
