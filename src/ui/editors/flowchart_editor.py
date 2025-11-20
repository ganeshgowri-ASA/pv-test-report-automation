"""
Flowchart Editor Component

Interactive flowchart editor for test procedures with drag-and-drop,
process visualization, and export capabilities.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
from datetime import datetime
import base64

from .editor_utils import (
    EditorState,
    EditorType,
    UndoRedoManager,
    AutoSaveManager,
    EditorValidator,
    ActionType,
    EditorAction,
    EditorTheme,
    init_session_state,
)


class NodeType(Enum):
    """Flowchart node types"""
    START = "start"
    END = "end"
    PROCESS = "process"
    DECISION = "decision"
    INPUT_OUTPUT = "input_output"
    SUBPROCESS = "subprocess"
    DOCUMENT = "document"
    DATA = "data"
    CONNECTOR = "connector"


@dataclass
class FlowchartNode:
    """Flowchart node"""
    id: str
    node_type: NodeType
    label: str
    position: Tuple[float, float] = (0, 0)
    size: Tuple[float, float] = (120, 60)
    metadata: Dict[str, Any] = field(default_factory=dict)
    style: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "node_type": self.node_type.value,
            "label": self.label,
            "position": self.position,
            "size": self.size,
            "metadata": self.metadata,
            "style": self.style,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FlowchartNode":
        """Create from dictionary"""
        return cls(
            id=data["id"],
            node_type=NodeType(data["node_type"]),
            label=data["label"],
            position=tuple(data.get("position", (0, 0))),
            size=tuple(data.get("size", (120, 60))),
            metadata=data.get("metadata", {}),
            style=data.get("style", {}),
        )


@dataclass
class FlowchartEdge:
    """Flowchart edge/connection"""
    id: str
    source_id: str
    target_id: str
    label: str = ""
    style: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "label": self.label,
            "style": self.style,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FlowchartEdge":
        """Create from dictionary"""
        return cls(
            id=data["id"],
            source_id=data["source_id"],
            target_id=data["target_id"],
            label=data.get("label", ""),
            style=data.get("style", {}),
            metadata=data.get("metadata", {}),
        )


@dataclass
class FlowchartTemplate:
    """Flowchart template"""
    name: str
    description: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)


class FlowchartEditor:
    """
    Flowchart editor for test procedures.

    Features:
    - Drag-and-drop node placement
    - Multiple node types
    - Connection management
    - Auto-layout
    - Export to PNG/SVG
    - Template library
    - Process validation
    """

    def __init__(
        self,
        editor_id: str = "flowchart_editor",
        auto_save_interval: int = 60,
        max_history: int = 50,
    ):
        """
        Initialize flowchart editor.

        Args:
            editor_id: Unique editor identifier
            auto_save_interval: Auto-save interval in seconds
            max_history: Maximum undo/redo history
        """
        self.editor_id = editor_id
        self.state_key = f"{editor_id}_state"

        # Initialize state
        self._init_state()

        # Initialize managers
        self.undo_manager = UndoRedoManager(max_history=max_history)
        self.validator = EditorValidator()

        # Setup auto-save
        self.auto_save_manager = AutoSaveManager(
            save_callback=self._save_callback,
            auto_save_interval=auto_save_interval,
        )

        # Load templates
        self.templates = self._load_templates()

    def _init_state(self):
        """Initialize editor state"""
        if self.state_key not in st.session_state:
            state = EditorState(
                editor_id=self.editor_id,
                editor_type=EditorType.FLOWCHART,
                content={
                    "name": "Untitled Flowchart",
                    "nodes": [],
                    "edges": [],
                    "layout": "vertical",
                },
            )
            st.session_state[self.state_key] = state

    def _save_callback(self, state: EditorState) -> bool:
        """Save callback for auto-save"""
        try:
            state.mark_saved()
            return True
        except Exception:
            return False

    def _load_templates(self) -> List[FlowchartTemplate]:
        """Load flowchart templates"""
        return [
            FlowchartTemplate(
                name="Basic Test Procedure",
                description="Simple linear test procedure",
                nodes=[
                    {"node_type": "start", "label": "Start Test", "position": (200, 50)},
                    {"node_type": "process", "label": "Setup Equipment", "position": (200, 150)},
                    {"node_type": "process", "label": "Run Test", "position": (200, 250)},
                    {"node_type": "process", "label": "Record Data", "position": (200, 350)},
                    {"node_type": "end", "label": "End Test", "position": (200, 450)},
                ],
                edges=[],
            ),
            FlowchartTemplate(
                name="Decision-Based Procedure",
                description="Test procedure with decision points",
                nodes=[
                    {"node_type": "start", "label": "Start", "position": (200, 50)},
                    {"node_type": "process", "label": "Initialize", "position": (200, 150)},
                    {"node_type": "decision", "label": "Pass?", "position": (200, 250)},
                    {"node_type": "process", "label": "Continue", "position": (350, 350)},
                    {"node_type": "process", "label": "Troubleshoot", "position": (50, 350)},
                    {"node_type": "end", "label": "End", "position": (200, 450)},
                ],
                edges=[],
            ),
            FlowchartTemplate(
                name="Blank Flowchart",
                description="Start from scratch",
                nodes=[],
                edges=[],
            ),
        ]

    def get_state(self) -> EditorState:
        """Get current editor state"""
        return st.session_state[self.state_key]

    def render(self):
        """Render the flowchart editor"""
        st.subheader("📊 Flowchart Editor")

        state = self.get_state()

        # Toolbar
        self._render_toolbar(state)

        # Main area
        col1, col2 = st.columns([3, 1])

        with col1:
            self._render_canvas(state)

        with col2:
            self._render_sidebar(state)

        # Auto-save
        if self.auto_save_manager.auto_save(state):
            st.toast("✅ Auto-saved", icon="💾")

    def _render_toolbar(self, state: EditorState):
        """Render toolbar"""
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

        with col1:
            # Flowchart name
            new_name = st.text_input(
                "Flowchart Name",
                value=state.content.get("name", "Untitled Flowchart"),
                key=f"{self.editor_id}_name",
            )
            if new_name != state.content.get("name"):
                state.content["name"] = new_name
                state.mark_modified()

        with col2:
            # Save
            if st.button("💾 Save", use_container_width=True):
                if self.auto_save_manager.manual_save(state):
                    st.success("Saved!")

        with col3:
            # Auto-layout
            if st.button("🔄 Auto-layout", use_container_width=True):
                self._auto_layout(state)

        with col4:
            # Export PNG
            if st.button("📥 PNG", use_container_width=True):
                self._export_png(state)

        with col5:
            # Export SVG
            if st.button("📥 SVG", use_container_width=True):
                self._export_svg(state)

        # Status
        nodes = state.content.get("nodes", [])
        edges = state.content.get("edges", [])
        st.caption(f"Nodes: {len(nodes)} | Connections: {len(edges)} | Modified: {'Yes' if state.modified else 'No'}")

    def _render_canvas(self, state: EditorState):
        """Render flowchart canvas"""
        st.markdown("#### Canvas")

        nodes = [FlowchartNode.from_dict(n) for n in state.content.get("nodes", [])]
        edges = [FlowchartEdge.from_dict(e) for e in state.content.get("edges", [])]

        # Generate visual representation
        # In production, this would use a proper flowchart library like react-flow or mermaid
        self._render_mermaid_diagram(nodes, edges)

        # Node list
        st.markdown("---")
        st.markdown("#### Nodes")

        for idx, node in enumerate(nodes):
            with st.expander(f"{node.node_type.value.title()}: {node.label}"):
                self._render_node_editor(node, idx, state)

    def _render_node_editor(self, node: FlowchartNode, idx: int, state: EditorState):
        """Render node editor"""
        col1, col2 = st.columns(2)

        with col1:
            # Node label
            new_label = st.text_input(
                "Label",
                value=node.label,
                key=f"{self.editor_id}_node_{node.id}_label",
            )
            if new_label != node.label:
                node.label = new_label
                self._update_node(node, state)

        with col2:
            # Node type
            current_idx = list(NodeType).index(node.node_type)
            new_type = st.selectbox(
                "Type",
                options=[t.value.title() for t in NodeType],
                index=current_idx,
                key=f"{self.editor_id}_node_{node.id}_type",
            )
            new_type_enum = NodeType(new_type.lower())
            if new_type_enum != node.node_type:
                node.node_type = new_type_enum
                self._update_node(node, state)

        # Position
        pos_col1, pos_col2 = st.columns(2)
        with pos_col1:
            new_x = st.number_input(
                "X Position",
                value=node.position[0],
                key=f"{self.editor_id}_node_{node.id}_x",
            )
        with pos_col2:
            new_y = st.number_input(
                "Y Position",
                value=node.position[1],
                key=f"{self.editor_id}_node_{node.id}_y",
            )

        if (new_x, new_y) != node.position:
            node.position = (new_x, new_y)
            self._update_node(node, state)

        # Actions
        action_cols = st.columns(3)

        with action_cols[0]:
            if st.button("🔗 Connect", key=f"{self.editor_id}_connect_{node.id}"):
                self._show_connection_dialog(node, state)

        with action_cols[1]:
            if st.button("📋 Duplicate", key=f"{self.editor_id}_dup_{node.id}"):
                self._duplicate_node(node, state)

        with action_cols[2]:
            if st.button("🗑️ Delete", key=f"{self.editor_id}_del_{node.id}"):
                self._delete_node(node, state)

    def _render_sidebar(self, state: EditorState):
        """Render sidebar"""
        st.markdown("#### Add Node")

        node_type = st.selectbox(
            "Node Type",
            options=[t.value.title() for t in NodeType],
            key=f"{self.editor_id}_new_node_type",
        )

        label = st.text_input(
            "Label",
            value="New Node",
            key=f"{self.editor_id}_new_node_label",
        )

        if st.button("➕ Add Node", use_container_width=True):
            self._add_node(NodeType(node_type.lower()), label, state)

        st.markdown("---")
        st.markdown("#### Templates")

        template_names = [t.name for t in self.templates]
        selected = st.selectbox(
            "Load Template",
            options=["Select..."] + template_names,
            key=f"{self.editor_id}_template",
        )

        if selected != "Select...":
            template = next(t for t in self.templates if t.name == selected)
            if st.button("Load", key=f"{self.editor_id}_load_template"):
                self._load_template(template, state)

        st.markdown("---")
        st.markdown("#### Layout")

        layout = st.radio(
            "Direction",
            options=["Vertical", "Horizontal"],
            key=f"{self.editor_id}_layout",
        )

        if layout.lower() != state.content.get("layout"):
            state.content["layout"] = layout.lower()
            state.mark_modified()

        st.markdown("---")
        st.markdown("#### Validation")

        if st.button("✓ Validate Flow", use_container_width=True):
            self._validate_flow(state)

    def _render_mermaid_diagram(self, nodes: List[FlowchartNode], edges: List[FlowchartEdge]):
        """Render flowchart using Mermaid"""
        # Generate Mermaid syntax
        mermaid_lines = ["graph TD"]

        # Node shapes based on type
        shape_map = {
            NodeType.START: ("([", "])"),
            NodeType.END: ("([", "])"),
            NodeType.PROCESS: ("[", "]"),
            NodeType.DECISION: ("{", "}"),
            NodeType.INPUT_OUTPUT: ("[/", "/]"),
            NodeType.SUBPROCESS: ("[[", "]]"),
            NodeType.DOCUMENT: ("[", "]"),
            NodeType.DATA: ("[/", "/]"),
            NodeType.CONNECTOR: ("((", "))"),
        }

        # Add nodes
        for node in nodes:
            shape_start, shape_end = shape_map.get(node.node_type, ("[", "]"))
            mermaid_lines.append(
                f"    {node.id}{shape_start}\"{node.label}\"{shape_end}"
            )

        # Add edges
        for edge in edges:
            label = f"|{edge.label}|" if edge.label else ""
            mermaid_lines.append(f"    {edge.source_id} -->{label} {edge.target_id}")

        mermaid_code = "\n".join(mermaid_lines)

        # Render using Streamlit's mermaid support
        st.code(mermaid_code, language="mermaid")

        # Note: Streamlit doesn't natively support mermaid rendering yet
        # In production, you would use st.components.v1.html with mermaid.js
        st.info("💡 Tip: Copy the code above and paste it into a Mermaid viewer for visualization")

    def _add_node(self, node_type: NodeType, label: str, state: EditorState):
        """Add new node"""
        nodes = state.content.get("nodes", [])

        # Calculate position (stack vertically)
        y_pos = len(nodes) * 100 + 50

        new_node = FlowchartNode(
            id=f"node_{uuid.uuid4().hex[:8]}",
            node_type=node_type,
            label=label,
            position=(200, y_pos),
        )

        nodes.append(new_node.to_dict())
        state.content["nodes"] = nodes
        state.mark_modified()

        st.success(f"Added {node_type.value} node")
        st.rerun()

    def _update_node(self, node: FlowchartNode, state: EditorState):
        """Update node in state"""
        nodes = state.content.get("nodes", [])

        for i, n in enumerate(nodes):
            if n["id"] == node.id:
                nodes[i] = node.to_dict()
                break

        state.content["nodes"] = nodes
        state.mark_modified()

    def _delete_node(self, node: FlowchartNode, state: EditorState):
        """Delete node"""
        # Remove node
        nodes = state.content.get("nodes", [])
        nodes = [n for n in nodes if n["id"] != node.id]
        state.content["nodes"] = nodes

        # Remove connected edges
        edges = state.content.get("edges", [])
        edges = [
            e for e in edges
            if e["source_id"] != node.id and e["target_id"] != node.id
        ]
        state.content["edges"] = edges

        state.mark_modified()
        st.success("Node deleted")
        st.rerun()

    def _duplicate_node(self, node: FlowchartNode, state: EditorState):
        """Duplicate node"""
        new_node = FlowchartNode(
            id=f"node_{uuid.uuid4().hex[:8]}",
            node_type=node.node_type,
            label=f"{node.label} (Copy)",
            position=(node.position[0] + 50, node.position[1] + 50),
        )

        nodes = state.content.get("nodes", [])
        nodes.append(new_node.to_dict())
        state.content["nodes"] = nodes
        state.mark_modified()

        st.success("Node duplicated")
        st.rerun()

    def _show_connection_dialog(self, source_node: FlowchartNode, state: EditorState):
        """Show connection dialog"""
        nodes = [FlowchartNode.from_dict(n) for n in state.content.get("nodes", [])]

        # In production, this would be a modal dialog
        st.info(f"Connect from: {source_node.label}")

        target_options = [
            f"{n.id}: {n.label}"
            for n in nodes
            if n.id != source_node.id
        ]

        if target_options:
            selected = st.selectbox(
                "Target Node",
                options=target_options,
                key=f"{self.editor_id}_connect_target_{source_node.id}",
            )

            edge_label = st.text_input(
                "Connection Label",
                key=f"{self.editor_id}_edge_label_{source_node.id}",
            )

            if st.button("Create Connection", key=f"{self.editor_id}_do_connect_{source_node.id}"):
                target_id = selected.split(":")[0]
                self._add_edge(source_node.id, target_id, edge_label, state)

    def _add_edge(self, source_id: str, target_id: str, label: str, state: EditorState):
        """Add edge/connection"""
        edges = state.content.get("edges", [])

        new_edge = FlowchartEdge(
            id=f"edge_{uuid.uuid4().hex[:8]}",
            source_id=source_id,
            target_id=target_id,
            label=label,
        )

        edges.append(new_edge.to_dict())
        state.content["edges"] = edges
        state.mark_modified()

        st.success("Connection created")
        st.rerun()

    def _load_template(self, template: FlowchartTemplate, state: EditorState):
        """Load template"""
        # Assign unique IDs to template nodes
        nodes = []
        id_map = {}

        for tmpl_node in template.nodes:
            old_id = tmpl_node.get("id", f"node_{uuid.uuid4().hex[:8]}")
            new_id = f"node_{uuid.uuid4().hex[:8]}"
            id_map[old_id] = new_id

            node = FlowchartNode(
                id=new_id,
                node_type=NodeType(tmpl_node["node_type"]),
                label=tmpl_node["label"],
                position=tuple(tmpl_node.get("position", (0, 0))),
            )
            nodes.append(node.to_dict())

        # Update edge IDs
        edges = []
        for tmpl_edge in template.edges:
            edge = FlowchartEdge(
                id=f"edge_{uuid.uuid4().hex[:8]}",
                source_id=id_map.get(tmpl_edge["source_id"], tmpl_edge["source_id"]),
                target_id=id_map.get(tmpl_edge["target_id"], tmpl_edge["target_id"]),
                label=tmpl_edge.get("label", ""),
            )
            edges.append(edge.to_dict())

        state.content["nodes"] = nodes
        state.content["edges"] = edges
        state.mark_modified()

        st.success(f"Loaded template: {template.name}")
        st.rerun()

    def _auto_layout(self, state: EditorState):
        """Auto-layout nodes"""
        nodes = state.content.get("nodes", [])
        layout = state.content.get("layout", "vertical")

        if layout == "vertical":
            # Stack vertically
            for i, node in enumerate(nodes):
                node["position"] = (200, i * 120 + 50)
        else:
            # Arrange horizontally
            for i, node in enumerate(nodes):
                node["position"] = (i * 180 + 50, 200)

        state.content["nodes"] = nodes
        state.mark_modified()

        st.success("Auto-layout applied")
        st.rerun()

    def _validate_flow(self, state: EditorState):
        """Validate flowchart"""
        nodes = [FlowchartNode.from_dict(n) for n in state.content.get("nodes", [])]
        edges = [FlowchartEdge.from_dict(e) for e in state.content.get("edges", [])]

        errors = []

        # Check for start node
        start_nodes = [n for n in nodes if n.node_type == NodeType.START]
        if len(start_nodes) == 0:
            errors.append("❌ No start node found")
        elif len(start_nodes) > 1:
            errors.append("⚠️ Multiple start nodes found")

        # Check for end node
        end_nodes = [n for n in nodes if n.node_type == NodeType.END]
        if len(end_nodes) == 0:
            errors.append("❌ No end node found")

        # Check for disconnected nodes
        node_ids = {n.id for n in nodes}
        connected_ids = set()
        for edge in edges:
            connected_ids.add(edge.source_id)
            connected_ids.add(edge.target_id)

        disconnected = node_ids - connected_ids
        if disconnected and len(nodes) > 1:
            errors.append(f"⚠️ {len(disconnected)} disconnected node(s)")

        # Display results
        if errors:
            for error in errors:
                st.warning(error)
        else:
            st.success("✅ Flowchart is valid!")

    def _export_png(self, state: EditorState):
        """Export as PNG"""
        # In production, this would render the flowchart to PNG
        st.info("PNG export would generate an image of the flowchart")
        # Placeholder: would use a library like playwright or selenium
        # to render the mermaid diagram to PNG

    def _export_svg(self, state: EditorState):
        """Export as SVG"""
        # In production, this would render the flowchart to SVG
        st.info("SVG export would generate a vector image of the flowchart")
        # Placeholder: mermaid can generate SVG directly


# Export
__all__ = ["FlowchartEditor", "FlowchartNode", "FlowchartEdge", "NodeType", "FlowchartTemplate"]
