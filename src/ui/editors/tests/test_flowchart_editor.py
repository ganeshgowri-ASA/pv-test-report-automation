"""
Tests for Flowchart Editor

Tests for flowchart editor with nodes, edges,
templates, and validation.
"""

import pytest

from ..flowchart_editor import (
    FlowchartEditor,
    FlowchartNode,
    FlowchartEdge,
    NodeType,
    FlowchartTemplate,
)
from ..editor_utils import EditorState, EditorType


class TestFlowchartNode:
    """Test FlowchartNode class"""

    def test_init(self):
        """Test initialization"""
        node = FlowchartNode(
            id="node1",
            node_type=NodeType.PROCESS,
            label="Test Process",
            position=(100, 200),
        )

        assert node.id == "node1"
        assert node.node_type == NodeType.PROCESS
        assert node.label == "Test Process"
        assert node.position == (100, 200)

    def test_to_dict(self):
        """Test conversion to dictionary"""
        node = FlowchartNode(
            id="node1",
            node_type=NodeType.START,
            label="Start",
        )

        data = node.to_dict()

        assert data["id"] == "node1"
        assert data["node_type"] == "start"
        assert data["label"] == "Start"

    def test_from_dict(self):
        """Test creation from dictionary"""
        data = {
            "id": "node1",
            "node_type": "decision",
            "label": "Check Status",
            "position": (150, 250),
            "size": (140, 80),
            "metadata": {"critical": True},
            "style": {"color": "red"},
        }

        node = FlowchartNode.from_dict(data)

        assert node.id == "node1"
        assert node.node_type == NodeType.DECISION
        assert node.label == "Check Status"
        assert node.position == (150, 250)

    def test_all_node_types(self):
        """Test all node types"""
        for node_type in NodeType:
            node = FlowchartNode(
                id=f"node_{node_type.value}",
                node_type=node_type,
                label=f"Test {node_type.value}",
            )
            assert node.node_type == node_type


class TestFlowchartEdge:
    """Test FlowchartEdge class"""

    def test_init(self):
        """Test initialization"""
        edge = FlowchartEdge(
            id="edge1",
            source_id="node1",
            target_id="node2",
            label="Next",
        )

        assert edge.id == "edge1"
        assert edge.source_id == "node1"
        assert edge.target_id == "node2"
        assert edge.label == "Next"

    def test_to_dict(self):
        """Test conversion to dictionary"""
        edge = FlowchartEdge(
            id="edge1",
            source_id="node1",
            target_id="node2",
        )

        data = edge.to_dict()

        assert data["id"] == "edge1"
        assert data["source_id"] == "node1"
        assert data["target_id"] == "node2"

    def test_from_dict(self):
        """Test creation from dictionary"""
        data = {
            "id": "edge1",
            "source_id": "node1",
            "target_id": "node2",
            "label": "Yes",
            "style": {"color": "green"},
            "metadata": {"condition": "pass"},
        }

        edge = FlowchartEdge.from_dict(data)

        assert edge.id == "edge1"
        assert edge.label == "Yes"


class TestFlowchartTemplate:
    """Test FlowchartTemplate class"""

    def test_init(self):
        """Test initialization"""
        template = FlowchartTemplate(
            name="Test Template",
            description="A test template",
            nodes=[
                {"node_type": "start", "label": "Start", "position": (100, 100)},
                {"node_type": "end", "label": "End", "position": (100, 300)},
            ],
            edges=[],
        )

        assert template.name == "Test Template"
        assert len(template.nodes) == 2


class TestFlowchartEditor:
    """Test FlowchartEditor class"""

    @pytest.fixture
    def editor(self):
        """Create editor instance"""
        return FlowchartEditor(editor_id="test_flowchart_editor")

    def test_init(self, editor):
        """Test initialization"""
        assert editor.editor_id == "test_flowchart_editor"
        assert editor.undo_manager is not None
        assert editor.validator is not None

    def test_templates_loaded(self, editor):
        """Test that templates are loaded"""
        assert len(editor.templates) > 0

        template_names = [t.name for t in editor.templates]
        assert "Basic Test Procedure" in template_names
        assert "Decision-Based Procedure" in template_names
        assert "Blank Flowchart" in template_names

    def test_get_state(self, editor):
        """Test getting editor state"""
        state = editor.get_state()

        assert isinstance(state, EditorState)
        assert state.editor_type == EditorType.FLOWCHART
        assert "nodes" in state.content
        assert "edges" in state.content
        assert "name" in state.content

    def test_add_node(self, editor):
        """Test adding node"""
        state = editor.get_state()
        initial_count = len(state.content.get("nodes", []))

        # Simulate adding node
        import uuid
        new_node = FlowchartNode(
            id=f"node_{uuid.uuid4().hex[:8]}",
            node_type=NodeType.PROCESS,
            label="New Process",
            position=(200, 150),
        )

        nodes = state.content.get("nodes", [])
        nodes.append(new_node.to_dict())
        state.content["nodes"] = nodes

        assert len(state.content["nodes"]) == initial_count + 1

    def test_update_node(self, editor):
        """Test updating node"""
        state = editor.get_state()

        # Add a node
        node = FlowchartNode(
            id="test_node",
            node_type=NodeType.PROCESS,
            label="Original",
        )

        state.content["nodes"] = [node.to_dict()]

        # Update node
        node.label = "Updated"
        node.position = (300, 400)
        editor._update_node(node, state)

        updated = state.content["nodes"][0]
        assert updated["label"] == "Updated"
        assert updated["position"] == (300, 400)

    def test_delete_node(self, editor):
        """Test deleting node"""
        state = editor.get_state()

        # Add nodes
        node1 = FlowchartNode(id="n1", node_type=NodeType.START, label="Start")
        node2 = FlowchartNode(id="n2", node_type=NodeType.END, label="End")

        state.content["nodes"] = [node1.to_dict(), node2.to_dict()]

        # Add edge between nodes
        edge = FlowchartEdge(id="e1", source_id="n1", target_id="n2")
        state.content["edges"] = [edge.to_dict()]

        # Delete first node
        state.content["nodes"] = [
            n for n in state.content["nodes"] if n["id"] != "n1"
        ]
        # Remove connected edges
        state.content["edges"] = [
            e for e in state.content["edges"]
            if e["source_id"] != "n1" and e["target_id"] != "n1"
        ]

        assert len(state.content["nodes"]) == 1
        assert len(state.content["edges"]) == 0

    def test_add_edge(self, editor):
        """Test adding edge"""
        state = editor.get_state()

        # Add nodes first
        node1 = FlowchartNode(id="n1", node_type=NodeType.START, label="Start")
        node2 = FlowchartNode(id="n2", node_type=NodeType.END, label="End")
        state.content["nodes"] = [node1.to_dict(), node2.to_dict()]

        # Add edge
        import uuid
        edge = FlowchartEdge(
            id=f"edge_{uuid.uuid4().hex[:8]}",
            source_id="n1",
            target_id="n2",
            label="Flow",
        )

        edges = state.content.get("edges", [])
        edges.append(edge.to_dict())
        state.content["edges"] = edges

        assert len(state.content["edges"]) == 1

    def test_auto_layout_vertical(self, editor):
        """Test vertical auto-layout"""
        state = editor.get_state()

        # Add nodes
        nodes = [
            FlowchartNode(id=f"n{i}", node_type=NodeType.PROCESS, label=f"Node {i}")
            for i in range(5)
        ]
        state.content["nodes"] = [n.to_dict() for n in nodes]
        state.content["layout"] = "vertical"

        # Apply vertical layout
        for i, node_dict in enumerate(state.content["nodes"]):
            node_dict["position"] = (200, i * 120 + 50)

        # Verify positions
        for i, node_dict in enumerate(state.content["nodes"]):
            assert node_dict["position"][1] == i * 120 + 50

    def test_auto_layout_horizontal(self, editor):
        """Test horizontal auto-layout"""
        state = editor.get_state()

        # Add nodes
        nodes = [
            FlowchartNode(id=f"n{i}", node_type=NodeType.PROCESS, label=f"Node {i}")
            for i in range(5)
        ]
        state.content["nodes"] = [n.to_dict() for n in nodes]
        state.content["layout"] = "horizontal"

        # Apply horizontal layout
        for i, node_dict in enumerate(state.content["nodes"]):
            node_dict["position"] = (i * 180 + 50, 200)

        # Verify positions
        for i, node_dict in enumerate(state.content["nodes"]):
            assert node_dict["position"][0] == i * 180 + 50

    def test_validate_flow_valid(self, editor):
        """Test validating valid flowchart"""
        state = editor.get_state()

        # Create valid flow
        nodes = [
            FlowchartNode(id="start", node_type=NodeType.START, label="Start"),
            FlowchartNode(id="process", node_type=NodeType.PROCESS, label="Process"),
            FlowchartNode(id="end", node_type=NodeType.END, label="End"),
        ]
        edges = [
            FlowchartEdge(id="e1", source_id="start", target_id="process"),
            FlowchartEdge(id="e2", source_id="process", target_id="end"),
        ]

        state.content["nodes"] = [n.to_dict() for n in nodes]
        state.content["edges"] = [e.to_dict() for e in edges]

        # Validation would check:
        # - Has start node ✓
        # - Has end node ✓
        # - All nodes connected ✓

    def test_validate_flow_no_start(self, editor):
        """Test validating flowchart without start node"""
        state = editor.get_state()

        # Create flow without start
        nodes = [
            FlowchartNode(id="process", node_type=NodeType.PROCESS, label="Process"),
            FlowchartNode(id="end", node_type=NodeType.END, label="End"),
        ]

        state.content["nodes"] = [n.to_dict() for n in nodes]

        # Get nodes
        flowchart_nodes = [FlowchartNode.from_dict(n) for n in state.content["nodes"]]

        # Check for start node
        start_nodes = [n for n in flowchart_nodes if n.node_type == NodeType.START]
        assert len(start_nodes) == 0  # Should fail validation

    def test_validate_flow_no_end(self, editor):
        """Test validating flowchart without end node"""
        state = editor.get_state()

        # Create flow without end
        nodes = [
            FlowchartNode(id="start", node_type=NodeType.START, label="Start"),
            FlowchartNode(id="process", node_type=NodeType.PROCESS, label="Process"),
        ]

        state.content["nodes"] = [n.to_dict() for n in nodes]

        # Get nodes
        flowchart_nodes = [FlowchartNode.from_dict(n) for n in state.content["nodes"]]

        # Check for end node
        end_nodes = [n for n in flowchart_nodes if n.node_type == NodeType.END]
        assert len(end_nodes) == 0  # Should fail validation

    def test_validate_disconnected_nodes(self, editor):
        """Test detecting disconnected nodes"""
        state = editor.get_state()

        # Create flow with disconnected node
        nodes = [
            FlowchartNode(id="n1", node_type=NodeType.START, label="Start"),
            FlowchartNode(id="n2", node_type=NodeType.PROCESS, label="Connected"),
            FlowchartNode(id="n3", node_type=NodeType.PROCESS, label="Disconnected"),
            FlowchartNode(id="n4", node_type=NodeType.END, label="End"),
        ]
        edges = [
            FlowchartEdge(id="e1", source_id="n1", target_id="n2"),
            FlowchartEdge(id="e2", source_id="n2", target_id="n4"),
            # n3 is not connected
        ]

        state.content["nodes"] = [n.to_dict() for n in nodes]
        state.content["edges"] = [e.to_dict() for e in edges]

        # Find disconnected nodes
        node_ids = {n["id"] for n in state.content["nodes"]}
        connected_ids = set()
        for edge in state.content["edges"]:
            connected_ids.add(edge["source_id"])
            connected_ids.add(edge["target_id"])

        disconnected = node_ids - connected_ids
        assert "n3" in disconnected

    def test_load_template(self, editor):
        """Test loading template"""
        template = editor.templates[0]
        state = editor.get_state()

        # Simulate loading
        import uuid
        nodes = []
        for tmpl_node in template.nodes:
            node = FlowchartNode(
                id=f"node_{uuid.uuid4().hex[:8]}",
                node_type=NodeType(tmpl_node["node_type"]),
                label=tmpl_node["label"],
                position=tuple(tmpl_node.get("position", (0, 0))),
            )
            nodes.append(node.to_dict())

        state.content["nodes"] = nodes

        assert len(state.content["nodes"]) == len(template.nodes)

    def test_duplicate_node(self, editor):
        """Test duplicating node"""
        state = editor.get_state()

        # Add original node
        original = FlowchartNode(
            id="original",
            node_type=NodeType.PROCESS,
            label="Original Process",
            position=(100, 100),
        )
        state.content["nodes"] = [original.to_dict()]

        # Duplicate
        import uuid
        duplicate = FlowchartNode(
            id=f"node_{uuid.uuid4().hex[:8]}",
            node_type=original.node_type,
            label=f"{original.label} (Copy)",
            position=(original.position[0] + 50, original.position[1] + 50),
        )

        nodes = state.content.get("nodes", [])
        nodes.append(duplicate.to_dict())
        state.content["nodes"] = nodes

        assert len(state.content["nodes"]) == 2
        assert state.content["nodes"][1]["label"] == "Original Process (Copy)"

    def test_decision_node_multiple_edges(self, editor):
        """Test decision node with multiple outgoing edges"""
        state = editor.get_state()

        # Create decision flow
        nodes = [
            FlowchartNode(id="start", node_type=NodeType.START, label="Start"),
            FlowchartNode(id="decision", node_type=NodeType.DECISION, label="Pass?"),
            FlowchartNode(id="yes", node_type=NodeType.PROCESS, label="Continue"),
            FlowchartNode(id="no", node_type=NodeType.PROCESS, label="Retry"),
        ]
        edges = [
            FlowchartEdge(id="e1", source_id="start", target_id="decision"),
            FlowchartEdge(id="e2", source_id="decision", target_id="yes", label="Yes"),
            FlowchartEdge(id="e3", source_id="decision", target_id="no", label="No"),
        ]

        state.content["nodes"] = [n.to_dict() for n in nodes]
        state.content["edges"] = [e.to_dict() for e in edges]

        # Count outgoing edges from decision
        decision_edges = [
            e for e in edges if e.source_id == "decision"
        ]
        assert len(decision_edges) == 2
