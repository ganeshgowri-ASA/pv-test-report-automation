"""
Tests for Document Editor

Tests for rich text document editor with section management,
comments, templates, and version control.
"""

import pytest
from datetime import datetime
import json

from ..document_editor import (
    DocumentEditor,
    DocumentSection,
    Comment,
    DocumentTemplate,
)
from ..editor_utils import EditorState, EditorType


class TestDocumentSection:
    """Test DocumentSection class"""

    def test_init(self):
        """Test initialization"""
        section = DocumentSection(
            id="section1",
            title="Introduction",
            content="This is the introduction.",
            level=1,
            order=0,
        )

        assert section.id == "section1"
        assert section.title == "Introduction"
        assert section.content == "This is the introduction."
        assert section.level == 1
        assert section.order == 0

    def test_to_dict(self):
        """Test conversion to dictionary"""
        section = DocumentSection(
            id="section1",
            title="Test",
            content="Content",
        )

        data = section.to_dict()

        assert data["id"] == "section1"
        assert data["title"] == "Test"
        assert data["content"] == "Content"
        assert "comments" in data

    def test_from_dict(self):
        """Test creation from dictionary"""
        data = {
            "id": "section1",
            "title": "Test",
            "content": "Content",
            "level": 2,
            "order": 1,
            "metadata": {"author": "test"},
            "comments": [],
        }

        section = DocumentSection.from_dict(data)

        assert section.id == "section1"
        assert section.title == "Test"
        assert section.level == 2
        assert section.order == 1


class TestComment:
    """Test Comment class"""

    def test_init(self):
        """Test initialization"""
        comment = Comment(
            id="comment1",
            author="John Doe",
            content="Great section!",
            timestamp=datetime.now().timestamp(),
            section_id="section1",
        )

        assert comment.id == "comment1"
        assert comment.author == "John Doe"
        assert comment.content == "Great section!"
        assert comment.section_id == "section1"
        assert not comment.resolved

    def test_to_dict(self):
        """Test conversion to dictionary"""
        comment = Comment(
            id="comment1",
            author="John Doe",
            content="Test comment",
            timestamp=datetime.now().timestamp(),
            section_id="section1",
        )

        data = comment.to_dict()

        assert data["id"] == "comment1"
        assert data["author"] == "John Doe"
        assert data["content"] == "Test comment"
        assert "replies" in data

    def test_from_dict(self):
        """Test creation from dictionary"""
        data = {
            "id": "comment1",
            "author": "John Doe",
            "content": "Test",
            "timestamp": datetime.now().timestamp(),
            "section_id": "section1",
            "resolved": True,
            "replies": [],
        }

        comment = Comment.from_dict(data)

        assert comment.id == "comment1"
        assert comment.resolved

    def test_nested_replies(self):
        """Test nested comment replies"""
        reply = Comment(
            id="reply1",
            author="Jane Doe",
            content="I agree!",
            timestamp=datetime.now().timestamp(),
            section_id="section1",
        )

        comment = Comment(
            id="comment1",
            author="John Doe",
            content="Test comment",
            timestamp=datetime.now().timestamp(),
            section_id="section1",
            replies=[reply],
        )

        assert len(comment.replies) == 1
        assert comment.replies[0].id == "reply1"


class TestDocumentTemplate:
    """Test DocumentTemplate class"""

    def test_init(self):
        """Test initialization"""
        template = DocumentTemplate(
            name="Test Template",
            description="A test template",
            sections=[
                {"title": "Section 1", "level": 1, "order": 0},
                {"title": "Section 2", "level": 1, "order": 1},
            ],
        )

        assert template.name == "Test Template"
        assert len(template.sections) == 2

    def test_to_dict(self):
        """Test conversion to dictionary"""
        template = DocumentTemplate(
            name="Test",
            description="Description",
            sections=[],
        )

        data = template.to_dict()

        assert data["name"] == "Test"
        assert data["description"] == "Description"
        assert "sections" in data


class TestDocumentEditor:
    """Test DocumentEditor class"""

    @pytest.fixture
    def editor(self):
        """Create editor instance"""
        return DocumentEditor(editor_id="test_editor")

    def test_init(self, editor):
        """Test initialization"""
        assert editor.editor_id == "test_editor"
        assert editor.undo_manager is not None
        assert editor.validator is not None
        assert editor.exporter is not None

    def test_templates_loaded(self, editor):
        """Test that templates are loaded"""
        assert len(editor.templates) > 0

        # Check for default templates
        template_names = [t.name for t in editor.templates]
        assert "PV Test Report" in template_names
        assert "Protocol Document" in template_names
        assert "Blank Document" in template_names

    def test_get_state(self, editor):
        """Test getting editor state"""
        state = editor.get_state()

        assert isinstance(state, EditorState)
        assert state.editor_type == EditorType.DOCUMENT
        assert "sections" in state.content
        assert "title" in state.content

    def test_export_json(self, editor):
        """Test JSON export"""
        state = editor.get_state()
        state.content = {
            "title": "Test Document",
            "sections": [
                {
                    "id": "s1",
                    "title": "Section 1",
                    "content": "Content",
                    "level": 1,
                    "order": 0,
                    "metadata": {},
                    "comments": [],
                }
            ],
        }

        data = editor._export_json(state)
        assert isinstance(data, bytes)

        # Parse JSON
        parsed = json.loads(data.decode())
        assert parsed["title"] == "Test Document"
        assert len(parsed["sections"]) == 1

    def test_export_markdown(self, editor):
        """Test Markdown export"""
        state = editor.get_state()
        state.content = {
            "title": "Test Document",
            "sections": [
                {
                    "id": "s1",
                    "title": "Introduction",
                    "content": "This is the intro.",
                    "level": 1,
                    "order": 0,
                    "metadata": {},
                    "comments": [],
                },
                {
                    "id": "s2",
                    "title": "Details",
                    "content": "More details here.",
                    "level": 2,
                    "order": 1,
                    "metadata": {},
                    "comments": [],
                },
            ],
        }

        data = editor._export_markdown(state)
        content = data.decode()

        assert "# Test Document" in content
        assert "# Introduction" in content
        assert "## Details" in content
        assert "This is the intro." in content

    def test_export_html(self, editor):
        """Test HTML export"""
        state = editor.get_state()
        state.content = {
            "title": "Test Document",
            "sections": [
                {
                    "id": "s1",
                    "title": "Section",
                    "content": "Content",
                    "level": 1,
                    "order": 0,
                    "metadata": {},
                    "comments": [],
                }
            ],
        }

        data = editor._export_html(state)
        content = data.decode()

        assert "<!DOCTYPE html>" in content
        assert "<title>Test Document</title>" in content
        assert "<h1>Section</h1>" in content
        assert "<p>Content</p>" in content

    def test_export_txt(self, editor):
        """Test plain text export"""
        state = editor.get_state()
        state.content = {
            "title": "Test Document",
            "sections": [
                {
                    "id": "s1",
                    "title": "Section",
                    "content": "Content",
                    "level": 1,
                    "order": 0,
                    "metadata": {},
                    "comments": [],
                }
            ],
        }

        data = editor._export_txt(state)
        content = data.decode()

        assert "Test Document" in content
        assert "Section" in content
        assert "Content" in content

    def test_add_section(self, editor):
        """Test adding section"""
        state = editor.get_state()
        initial_count = len(state.content.get("sections", []))

        # Simulate adding section
        import uuid
        new_section = DocumentSection(
            id=str(uuid.uuid4()),
            title="New Section",
            content="",
            order=initial_count,
        )

        sections = state.content.get("sections", [])
        sections.append(new_section.to_dict())
        state.content["sections"] = sections

        assert len(state.content["sections"]) == initial_count + 1

    def test_update_section(self, editor):
        """Test updating section"""
        state = editor.get_state()

        # Add a section
        section = DocumentSection(
            id="test_section",
            title="Original Title",
            content="Original content",
        )

        state.content["sections"] = [section.to_dict()]

        # Update section
        section.title = "Updated Title"
        section.content = "Updated content"
        editor._update_section(section, state)

        updated = state.content["sections"][0]
        assert updated["title"] == "Updated Title"
        assert updated["content"] == "Updated content"

    def test_delete_section(self, editor):
        """Test deleting section"""
        state = editor.get_state()

        # Add sections
        section1 = DocumentSection(id="s1", title="Section 1", content="", order=0)
        section2 = DocumentSection(id="s2", title="Section 2", content="", order=1)

        state.content["sections"] = [section1.to_dict(), section2.to_dict()]

        # Delete first section
        sections = [s for s in state.content["sections"] if s["id"] != "s1"]
        state.content["sections"] = sections

        assert len(state.content["sections"]) == 1
        assert state.content["sections"][0]["id"] == "s2"

    def test_section_ordering(self, editor):
        """Test section ordering"""
        state = editor.get_state()

        # Add sections out of order
        sections = [
            DocumentSection(id="s1", title="Section 1", content="", order=2).to_dict(),
            DocumentSection(id="s2", title="Section 2", content="", order=0).to_dict(),
            DocumentSection(id="s3", title="Section 3", content="", order=1).to_dict(),
        ]

        state.content["sections"] = sections

        # Get sorted sections
        sorted_sections = [
            DocumentSection.from_dict(s)
            for s in state.content["sections"]
        ]
        sorted_sections.sort(key=lambda x: x.order)

        assert sorted_sections[0].id == "s2"
        assert sorted_sections[1].id == "s3"
        assert sorted_sections[2].id == "s1"

    def test_load_template(self, editor):
        """Test loading template"""
        # Get a template
        template = editor.templates[0]

        state = editor.get_state()

        # Simulate loading template
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

        assert len(state.content["sections"]) == len(template.sections)

    def test_document_validation(self, editor):
        """Test document validation"""
        state = editor.get_state()

        # Set up validation rules
        editor.validator.add_rule(
            "has_title",
            lambda data: bool(data.get("title"))
        )

        # Valid document
        state.content = {
            "title": "Test Document",
            "sections": [],
        }
        assert editor.validator.validate(state.content, ["has_title"])

        # Invalid document
        state.content = {
            "title": "",
            "sections": [],
        }
        assert not editor.validator.validate(state.content, ["has_title"])

    def test_word_count(self, editor):
        """Test word count calculation"""
        state = editor.get_state()

        sections = [
            DocumentSection(
                id="s1",
                title="Section 1",
                content="This is a test section.",
                order=0
            ).to_dict(),
            DocumentSection(
                id="s2",
                title="Section 2",
                content="Another section with more words here.",
                order=1
            ).to_dict(),
        ]

        state.content["sections"] = sections

        # Calculate word count
        word_count = sum(
            len(s.get("content", "").split())
            for s in state.content["sections"]
        )

        assert word_count == 11  # 5 + 6 words
