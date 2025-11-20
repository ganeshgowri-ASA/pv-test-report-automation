"""
Document Editor Component

Rich text editor for PV test reports with section management,
commenting, version comparison, templates, and auto-save.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import re
from pathlib import Path

from .editor_utils import (
    EditorState,
    EditorType,
    UndoRedoManager,
    AutoSaveManager,
    EditorValidator,
    EditorExporter,
    ActionType,
    EditorAction,
    init_session_state,
    get_session_state,
    set_session_state,
    format_timestamp,
    get_time_ago,
)


@dataclass
class DocumentSection:
    """Represents a document section"""
    id: str
    title: str
    content: str
    level: int = 1  # Heading level (1-6)
    order: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    comments: List["Comment"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "level": self.level,
            "order": self.order,
            "metadata": self.metadata,
            "comments": [c.to_dict() for c in self.comments],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentSection":
        """Create from dictionary"""
        comments = [Comment.from_dict(c) for c in data.get("comments", [])]
        return cls(
            id=data["id"],
            title=data["title"],
            content=data["content"],
            level=data.get("level", 1),
            order=data.get("order", 0),
            metadata=data.get("metadata", {}),
            comments=comments,
        )


@dataclass
class Comment:
    """Represents a comment/annotation"""
    id: str
    author: str
    content: str
    timestamp: float
    section_id: str
    resolved: bool = False
    replies: List["Comment"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "author": self.author,
            "content": self.content,
            "timestamp": self.timestamp,
            "section_id": self.section_id,
            "resolved": self.resolved,
            "replies": [r.to_dict() for r in self.replies],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Comment":
        """Create from dictionary"""
        replies = [cls.from_dict(r) for r in data.get("replies", [])]
        return cls(
            id=data["id"],
            author=data["author"],
            content=data["content"],
            timestamp=data["timestamp"],
            section_id=data["section_id"],
            resolved=data.get("resolved", False),
            replies=replies,
        )


@dataclass
class DocumentTemplate:
    """Document template"""
    name: str
    description: str
    sections: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "sections": self.sections,
            "metadata": self.metadata,
        }


class DocumentEditor:
    """
    Rich text document editor component.

    Features:
    - Section-based document structure
    - Rich text editing
    - Comment and annotation system
    - Version comparison
    - Template support
    - Auto-save functionality
    - Export to multiple formats
    """

    def __init__(
        self,
        editor_id: str = "document_editor",
        auto_save_interval: int = 60,
        max_history: int = 50,
    ):
        """
        Initialize document editor.

        Args:
            editor_id: Unique editor identifier
            auto_save_interval: Auto-save interval in seconds
            max_history: Maximum undo/redo history
        """
        self.editor_id = editor_id
        self.state_key = f"{editor_id}_state"
        self.undo_key = f"{editor_id}_undo"

        # Initialize state
        self._init_state()

        # Initialize managers
        self.undo_manager = UndoRedoManager(max_history=max_history)
        self.validator = EditorValidator()
        self.exporter = EditorExporter()

        # Setup auto-save
        self.auto_save_manager = AutoSaveManager(
            save_callback=self._save_callback,
            auto_save_interval=auto_save_interval,
        )

        # Register exporters
        self._register_exporters()

        # Load templates
        self.templates = self._load_templates()

    def _init_state(self):
        """Initialize editor state"""
        if self.state_key not in st.session_state:
            state = EditorState(
                editor_id=self.editor_id,
                editor_type=EditorType.DOCUMENT,
                content={
                    "sections": [],
                    "title": "Untitled Document",
                    "metadata": {},
                },
            )
            st.session_state[self.state_key] = state

    def _save_callback(self, state: EditorState) -> bool:
        """
        Save callback for auto-save.

        Args:
            state: Editor state to save

        Returns:
            True if save successful
        """
        try:
            # In production, this would save to database/file
            state.mark_saved()
            return True
        except Exception:
            return False

    def _register_exporters(self):
        """Register export formats"""
        self.exporter.register_exporter("json", self._export_json)
        self.exporter.register_exporter("markdown", self._export_markdown)
        self.exporter.register_exporter("html", self._export_html)
        self.exporter.register_exporter("txt", self._export_txt)

    def _export_json(self, state: EditorState, **kwargs) -> bytes:
        """Export as JSON"""
        return json.dumps(state.content, indent=2).encode('utf-8')

    def _export_markdown(self, state: EditorState, **kwargs) -> bytes:
        """Export as Markdown"""
        sections = [
            DocumentSection.from_dict(s)
            for s in state.content.get("sections", [])
        ]

        lines = [f"# {state.content.get('title', 'Untitled')}\n"]

        for section in sorted(sections, key=lambda x: x.order):
            heading = "#" * section.level
            lines.append(f"\n{heading} {section.title}\n")
            lines.append(f"{section.content}\n")

        return "\n".join(lines).encode('utf-8')

    def _export_html(self, state: EditorState, **kwargs) -> bytes:
        """Export as HTML"""
        sections = [
            DocumentSection.from_dict(s)
            for s in state.content.get("sections", [])
        ]

        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>{state.content.get('title', 'Untitled')}</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }",
            "h1, h2, h3, h4, h5, h6 { color: #333; }",
            "p { line-height: 1.6; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{state.content.get('title', 'Untitled')}</h1>",
        ]

        for section in sorted(sections, key=lambda x: x.order):
            html_parts.append(f"<h{section.level}>{section.title}</h{section.level}>")
            # Convert newlines to paragraphs
            paragraphs = section.content.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    html_parts.append(f"<p>{para.strip()}</p>")

        html_parts.extend(["</body>", "</html>"])

        return "\n".join(html_parts).encode('utf-8')

    def _export_txt(self, state: EditorState, **kwargs) -> bytes:
        """Export as plain text"""
        sections = [
            DocumentSection.from_dict(s)
            for s in state.content.get("sections", [])
        ]

        lines = [state.content.get('title', 'Untitled'), "=" * 80, ""]

        for section in sorted(sections, key=lambda x: x.order):
            lines.append(section.title)
            lines.append("-" * len(section.title))
            lines.append(section.content)
            lines.append("")

        return "\n".join(lines).encode('utf-8')

    def _load_templates(self) -> List[DocumentTemplate]:
        """Load document templates"""
        # Default templates
        return [
            DocumentTemplate(
                name="PV Test Report",
                description="Standard PV test report template",
                sections=[
                    {"title": "Executive Summary", "level": 1, "order": 0},
                    {"title": "Introduction", "level": 1, "order": 1},
                    {"title": "Test Objectives", "level": 2, "order": 2},
                    {"title": "Test Procedures", "level": 1, "order": 3},
                    {"title": "Results", "level": 1, "order": 4},
                    {"title": "Analysis", "level": 1, "order": 5},
                    {"title": "Conclusions", "level": 1, "order": 6},
                    {"title": "Recommendations", "level": 1, "order": 7},
                ],
            ),
            DocumentTemplate(
                name="Protocol Document",
                description="Test protocol template",
                sections=[
                    {"title": "Overview", "level": 1, "order": 0},
                    {"title": "Test Setup", "level": 1, "order": 1},
                    {"title": "Safety Requirements", "level": 2, "order": 2},
                    {"title": "Procedure Steps", "level": 1, "order": 3},
                    {"title": "Data Collection", "level": 1, "order": 4},
                    {"title": "Quality Control", "level": 1, "order": 5},
                ],
            ),
            DocumentTemplate(
                name="Blank Document",
                description="Start with a blank document",
                sections=[],
            ),
        ]

    def get_state(self) -> EditorState:
        """Get current editor state"""
        return st.session_state[self.state_key]

    def render(self):
        """Render the document editor"""
        st.subheader("📝 Document Editor")

        state = self.get_state()

        # Toolbar
        self._render_toolbar(state)

        # Main editing area
        col1, col2 = st.columns([3, 1])

        with col1:
            self._render_editor_area(state)

        with col2:
            self._render_sidebar(state)

        # Auto-save
        if self.auto_save_manager.auto_save(state):
            st.toast("✅ Auto-saved", icon="💾")

    def _render_toolbar(self, state: EditorState):
        """Render editor toolbar"""
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

        with col1:
            # Document title
            new_title = st.text_input(
                "Document Title",
                value=state.content.get("title", "Untitled Document"),
                key=f"{self.editor_id}_title",
            )
            if new_title != state.content.get("title"):
                state.content["title"] = new_title
                state.mark_modified()

        with col2:
            # Save button
            if st.button("💾 Save", use_container_width=True):
                if self.auto_save_manager.manual_save(state):
                    st.success("Saved successfully!")

        with col3:
            # Undo/Redo
            undo_disabled = not self.undo_manager.can_undo()
            if st.button("↶ Undo", disabled=undo_disabled, use_container_width=True):
                self._undo()

        with col4:
            redo_disabled = not self.undo_manager.can_redo()
            if st.button("↷ Redo", disabled=redo_disabled, use_container_width=True):
                self._redo()

        with col5:
            # Export
            export_format = st.selectbox(
                "Export",
                options=["Select...", "JSON", "Markdown", "HTML", "Text"],
                key=f"{self.editor_id}_export_format",
            )
            if export_format != "Select...":
                self._export_document(state, export_format.lower())

        # Status bar
        status_cols = st.columns([2, 2, 2])
        with status_cols[0]:
            if state.modified:
                st.caption("⚠️ Unsaved changes")
            else:
                st.caption("✅ All changes saved")

        with status_cols[1]:
            last_save = get_time_ago(state.last_save_time)
            st.caption(f"Last saved: {last_save}")

        with status_cols[2]:
            section_count = len(state.content.get("sections", []))
            st.caption(f"Sections: {section_count}")

    def _render_editor_area(self, state: EditorState):
        """Render main editing area"""
        st.markdown("---")

        sections = [
            DocumentSection.from_dict(s)
            for s in state.content.get("sections", [])
        ]
        sections.sort(key=lambda x: x.order)

        # Add section button
        if st.button("➕ Add Section"):
            self._add_section()

        # Render sections
        for idx, section in enumerate(sections):
            self._render_section(section, idx, state)

    def _render_section(self, section: DocumentSection, idx: int, state: EditorState):
        """Render a document section"""
        with st.container():
            st.markdown(f"### Section {idx + 1}")

            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                # Section title
                new_title = st.text_input(
                    "Title",
                    value=section.title,
                    key=f"{self.editor_id}_section_{section.id}_title",
                    label_visibility="collapsed",
                )
                if new_title != section.title:
                    section.title = new_title
                    self._update_section(section, state)

            with col2:
                # Heading level
                new_level = st.selectbox(
                    "Level",
                    options=[1, 2, 3, 4, 5, 6],
                    index=section.level - 1,
                    key=f"{self.editor_id}_section_{section.id}_level",
                    label_visibility="collapsed",
                )
                if new_level != section.level:
                    section.level = new_level
                    self._update_section(section, state)

            with col3:
                # Move up/down
                if idx > 0:
                    if st.button("⬆️", key=f"{self.editor_id}_up_{section.id}"):
                        self._move_section(section, idx, -1, state)

            with col4:
                if idx < len(state.content.get("sections", [])) - 1:
                    if st.button("⬇️", key=f"{self.editor_id}_down_{section.id}"):
                        self._move_section(section, idx, 1, state)

            # Section content
            new_content = st.text_area(
                "Content",
                value=section.content,
                height=150,
                key=f"{self.editor_id}_section_{section.id}_content",
                label_visibility="collapsed",
            )
            if new_content != section.content:
                section.content = new_content
                self._update_section(section, state)

            # Section actions
            action_cols = st.columns([1, 1, 1, 3])

            with action_cols[0]:
                if st.button("💬 Comment", key=f"{self.editor_id}_comment_{section.id}"):
                    self._show_comments(section)

            with action_cols[1]:
                if st.button("📋 Duplicate", key=f"{self.editor_id}_dup_{section.id}"):
                    self._duplicate_section(section, state)

            with action_cols[2]:
                if st.button("🗑️ Delete", key=f"{self.editor_id}_del_{section.id}"):
                    self._delete_section(section, state)

            st.markdown("---")

    def _render_sidebar(self, state: EditorState):
        """Render sidebar with templates and info"""
        st.markdown("#### 📋 Templates")

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
        st.markdown("#### 📊 Document Info")

        sections = state.content.get("sections", [])
        word_count = sum(
            len(s.get("content", "").split())
            for s in sections
        )

        st.metric("Word Count", word_count)
        st.metric("Sections", len(sections))
        st.metric("Version", state.version)

        # Comments
        all_comments = []
        for section_dict in sections:
            section = DocumentSection.from_dict(section_dict)
            all_comments.extend(section.comments)

        unresolved = sum(1 for c in all_comments if not c.resolved)
        st.metric("Unresolved Comments", unresolved)

    def _add_section(self):
        """Add new section"""
        import uuid

        state = self.get_state()
        sections = state.content.get("sections", [])

        new_section = DocumentSection(
            id=str(uuid.uuid4()),
            title="New Section",
            content="",
            order=len(sections),
        )

        sections.append(new_section.to_dict())
        state.content["sections"] = sections
        state.mark_modified()

        # Add to undo history
        action = EditorAction(
            action_type=ActionType.INSERT,
            timestamp=datetime.now().timestamp(),
            data={"section_id": new_section.id},
            description="Add section",
        )
        self.undo_manager.add_action(action)

    def _update_section(self, section: DocumentSection, state: EditorState):
        """Update section in state"""
        sections = state.content.get("sections", [])
        for i, s in enumerate(sections):
            if s["id"] == section.id:
                sections[i] = section.to_dict()
                break

        state.content["sections"] = sections
        state.mark_modified()

    def _delete_section(self, section: DocumentSection, state: EditorState):
        """Delete section"""
        sections = state.content.get("sections", [])
        sections = [s for s in sections if s["id"] != section.id]

        # Re-order
        for i, s in enumerate(sections):
            s["order"] = i

        state.content["sections"] = sections
        state.mark_modified()

        st.rerun()

    def _duplicate_section(self, section: DocumentSection, state: EditorState):
        """Duplicate section"""
        import uuid

        new_section = DocumentSection(
            id=str(uuid.uuid4()),
            title=f"{section.title} (Copy)",
            content=section.content,
            level=section.level,
            order=section.order + 1,
        )

        sections = state.content.get("sections", [])
        sections.insert(section.order + 1, new_section.to_dict())

        # Re-order
        for i, s in enumerate(sections):
            s["order"] = i

        state.content["sections"] = sections
        state.mark_modified()

        st.rerun()

    def _move_section(self, section: DocumentSection, idx: int, direction: int, state: EditorState):
        """Move section up or down"""
        sections = state.content.get("sections", [])
        new_idx = idx + direction

        if 0 <= new_idx < len(sections):
            sections[idx], sections[new_idx] = sections[new_idx], sections[idx]

            # Update order
            for i, s in enumerate(sections):
                s["order"] = i

            state.content["sections"] = sections
            state.mark_modified()

            st.rerun()

    def _load_template(self, template: DocumentTemplate, state: EditorState):
        """Load template"""
        import uuid

        sections = []
        for tmpl_section in template.sections:
            section = DocumentSection(
                id=str(uuid.uuid4()),
                title=tmpl_section["title"],
                content="",
                level=tmpl_section["level"],
                order=tmpl_section["order"],
            )
            sections.append(section.to_dict())

        state.content["sections"] = sections
        state.mark_modified()

        st.rerun()

    def _show_comments(self, section: DocumentSection):
        """Show comments for section"""
        st.info(f"Comments for: {section.title}")
        # In a real implementation, this would open a modal or sidebar
        # with the comment interface

    def _undo(self):
        """Undo last action"""
        action = self.undo_manager.undo()
        if action and action.previous_state:
            state = self.get_state()
            state.content = action.previous_state.copy()
            state.mark_modified()
            st.rerun()

    def _redo(self):
        """Redo last undone action"""
        action = self.undo_manager.redo()
        if action and action.new_state:
            state = self.get_state()
            state.content = action.new_state.copy()
            state.mark_modified()
            st.rerun()

    def _export_document(self, state: EditorState, format_name: str):
        """Export document"""
        try:
            data = self.exporter.export(state, format_name)
            if data:
                filename = f"{state.content.get('title', 'document')}.{format_name}"
                st.download_button(
                    label=f"Download {format_name.upper()}",
                    data=data,
                    file_name=filename,
                    mime=f"application/{format_name}",
                )
        except Exception as e:
            st.error(f"Export failed: {str(e)}")


# Export
__all__ = ["DocumentEditor", "DocumentSection", "Comment", "DocumentTemplate"]
