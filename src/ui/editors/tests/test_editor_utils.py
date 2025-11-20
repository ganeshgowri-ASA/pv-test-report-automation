"""
Tests for Editor Utilities

Tests for common editor utilities including state management,
undo/redo, auto-save, validation, and export functionality.
"""

import pytest
import time
from datetime import datetime
from typing import Any, Dict

from ..editor_utils import (
    EditorType,
    ActionType,
    EditorAction,
    EditorState,
    UndoRedoManager,
    AutoSaveManager,
    EditorValidator,
    EditorExporter,
    EditorTheme,
    format_timestamp,
    get_time_ago,
)


class TestEditorState:
    """Test EditorState class"""

    def test_init(self):
        """Test initialization"""
        state = EditorState(
            editor_id="test_editor",
            editor_type=EditorType.DOCUMENT,
        )

        assert state.editor_id == "test_editor"
        assert state.editor_type == EditorType.DOCUMENT
        assert state.version == 1
        assert not state.modified
        assert state.content == {}

    def test_checksum_calculation(self):
        """Test checksum calculation"""
        state = EditorState(
            editor_id="test",
            editor_type=EditorType.DOCUMENT,
            content={"key": "value"},
        )

        checksum1 = state.checksum
        assert checksum1

        # Same content should have same checksum
        state.update_checksum()
        assert state.checksum == checksum1

        # Different content should have different checksum
        state.content["key"] = "new_value"
        state.update_checksum()
        assert state.checksum != checksum1

    def test_is_modified(self):
        """Test modification detection"""
        state = EditorState(
            editor_id="test",
            editor_type=EditorType.DOCUMENT,
            content={"key": "value"},
        )

        # Initially not modified (after checksum update)
        assert not state.is_modified()

        # Modify content
        state.content["key"] = "new_value"
        assert state.is_modified()

        # Update checksum
        state.update_checksum()
        assert not state.is_modified()

    def test_mark_saved(self):
        """Test marking as saved"""
        state = EditorState(
            editor_id="test",
            editor_type=EditorType.DOCUMENT,
        )

        state.modified = True
        state.mark_saved()

        assert not state.modified
        assert state.last_save_time is not None

    def test_mark_modified(self):
        """Test marking as modified"""
        state = EditorState(
            editor_id="test",
            editor_type=EditorType.DOCUMENT,
        )

        state.mark_modified()
        assert state.modified

    def test_increment_version(self):
        """Test version increment"""
        state = EditorState(
            editor_id="test",
            editor_type=EditorType.DOCUMENT,
        )

        assert state.version == 1
        state.increment_version()
        assert state.version == 2

    def test_to_dict(self):
        """Test conversion to dictionary"""
        state = EditorState(
            editor_id="test",
            editor_type=EditorType.DOCUMENT,
            content={"key": "value"},
        )

        data = state.to_dict()

        assert data["editor_id"] == "test"
        assert data["editor_type"] == "document"
        assert data["content"] == {"key": "value"}
        assert data["version"] == 1

    def test_from_dict(self):
        """Test creation from dictionary"""
        data = {
            "editor_id": "test",
            "editor_type": "excel",
            "content": {"key": "value"},
            "metadata": {"author": "test"},
            "version": 2,
            "modified": True,
            "last_save_time": time.time(),
            "checksum": "abc123",
        }

        state = EditorState.from_dict(data)

        assert state.editor_id == "test"
        assert state.editor_type == EditorType.EXCEL
        assert state.content == {"key": "value"}
        assert state.version == 2
        assert state.modified


class TestUndoRedoManager:
    """Test UndoRedoManager class"""

    def test_init(self):
        """Test initialization"""
        manager = UndoRedoManager(max_history=10)
        assert manager.max_history == 10
        assert len(manager.undo_stack) == 0
        assert len(manager.redo_stack) == 0

    def test_add_action(self):
        """Test adding actions"""
        manager = UndoRedoManager()

        action = EditorAction(
            action_type=ActionType.INSERT,
            timestamp=time.time(),
            data={"test": "data"},
            description="Test action",
        )

        manager.add_action(action)
        assert len(manager.undo_stack) == 1
        assert manager.can_undo()

    def test_undo(self):
        """Test undo operation"""
        manager = UndoRedoManager()

        action = EditorAction(
            action_type=ActionType.INSERT,
            timestamp=time.time(),
            data={"test": "data"},
            previous_state={"old": "state"},
            new_state={"new": "state"},
            description="Test action",
        )

        manager.add_action(action)
        undone = manager.undo()

        assert undone == action
        assert len(manager.undo_stack) == 0
        assert len(manager.redo_stack) == 1
        assert manager.can_redo()

    def test_redo(self):
        """Test redo operation"""
        manager = UndoRedoManager()

        action = EditorAction(
            action_type=ActionType.INSERT,
            timestamp=time.time(),
            data={"test": "data"},
            description="Test action",
        )

        manager.add_action(action)
        manager.undo()

        redone = manager.redo()
        assert redone == action
        assert len(manager.undo_stack) == 1
        assert len(manager.redo_stack) == 0

    def test_max_history(self):
        """Test history limit"""
        manager = UndoRedoManager(max_history=3)

        for i in range(5):
            action = EditorAction(
                action_type=ActionType.INSERT,
                timestamp=time.time(),
                data={"index": i},
                description=f"Action {i}",
            )
            manager.add_action(action)

        assert len(manager.undo_stack) == 3

    def test_clear_redo_on_new_action(self):
        """Test that redo stack clears on new action"""
        manager = UndoRedoManager()

        # Add and undo
        action1 = EditorAction(
            action_type=ActionType.INSERT,
            timestamp=time.time(),
            data={"test": 1},
            description="Action 1",
        )
        manager.add_action(action1)
        manager.undo()

        assert manager.can_redo()

        # Add new action
        action2 = EditorAction(
            action_type=ActionType.INSERT,
            timestamp=time.time(),
            data={"test": 2},
            description="Action 2",
        )
        manager.add_action(action2)

        assert not manager.can_redo()

    def test_clear_history(self):
        """Test clearing history"""
        manager = UndoRedoManager()

        action = EditorAction(
            action_type=ActionType.INSERT,
            timestamp=time.time(),
            data={"test": "data"},
            description="Test action",
        )

        manager.add_action(action)
        manager.clear_history()

        assert len(manager.undo_stack) == 0
        assert len(manager.redo_stack) == 0


class TestAutoSaveManager:
    """Test AutoSaveManager class"""

    def test_init(self):
        """Test initialization"""
        save_count = [0]

        def save_callback(state):
            save_count[0] += 1
            return True

        manager = AutoSaveManager(
            save_callback=save_callback,
            auto_save_interval=10,
        )

        assert manager.auto_save_interval == 10
        assert manager.enabled

    def test_should_auto_save(self):
        """Test auto-save condition"""
        def save_callback(state):
            return True

        manager = AutoSaveManager(
            save_callback=save_callback,
            auto_save_interval=1,
        )

        state = EditorState(
            editor_id="test",
            editor_type=EditorType.DOCUMENT,
        )

        # Not modified, should not save
        assert not manager.should_auto_save(state)

        # Modified, should save
        state.mark_modified()
        assert manager.should_auto_save(state)

    def test_manual_save(self):
        """Test manual save"""
        save_count = [0]

        def save_callback(state):
            save_count[0] += 1
            return True

        manager = AutoSaveManager(save_callback=save_callback)

        state = EditorState(
            editor_id="test",
            editor_type=EditorType.DOCUMENT,
        )

        result = manager.manual_save(state)
        assert result
        assert save_count[0] == 1

    def test_enable_disable(self):
        """Test enable/disable"""
        def save_callback(state):
            return True

        manager = AutoSaveManager(save_callback=save_callback)

        assert manager.enabled

        manager.disable()
        assert not manager.enabled

        manager.enable()
        assert manager.enabled


class TestEditorValidator:
    """Test EditorValidator class"""

    def test_init(self):
        """Test initialization"""
        validator = EditorValidator()
        assert len(validator.validation_rules) == 0
        assert len(validator.errors) == 0

    def test_add_rule(self):
        """Test adding validation rule"""
        validator = EditorValidator()

        def is_positive(value):
            return value > 0

        validator.add_rule("positive", is_positive)
        assert "positive" in validator.validation_rules

    def test_validate(self):
        """Test validation"""
        validator = EditorValidator()

        def is_positive(value):
            return value > 0

        validator.add_rule("positive", is_positive)

        # Valid
        assert validator.validate(5)
        assert len(validator.errors) == 0

        # Invalid
        assert not validator.validate(-5)
        assert len(validator.errors) > 0

    def test_validate_required_fields(self):
        """Test required fields validation"""
        validator = EditorValidator()

        data = {"name": "Test", "age": 30}

        # All required fields present
        assert validator.validate_required_fields(data, ["name", "age"])
        assert len(validator.errors) == 0

        # Missing field
        assert not validator.validate_required_fields(data, ["name", "email"])
        assert len(validator.errors) > 0

    def test_validate_field_types(self):
        """Test field type validation"""
        validator = EditorValidator()

        data = {"name": "Test", "age": 30}

        # Correct types
        assert validator.validate_field_types(data, {"name": str, "age": int})
        assert len(validator.errors) == 0

        # Incorrect type
        assert not validator.validate_field_types(data, {"name": str, "age": str})
        assert len(validator.errors) > 0

    def test_clear(self):
        """Test clearing errors"""
        validator = EditorValidator()

        validator.errors.append("Error 1")
        validator.warnings.append("Warning 1")

        validator.clear()

        assert len(validator.errors) == 0
        assert len(validator.warnings) == 0


class TestEditorExporter:
    """Test EditorExporter class"""

    def test_init(self):
        """Test initialization"""
        exporter = EditorExporter()
        assert len(exporter.exporters) == 0

    def test_register_exporter(self):
        """Test registering exporter"""
        exporter = EditorExporter()

        def export_json(state, **kwargs):
            return b"{}"

        exporter.register_exporter("json", export_json)
        assert "json" in exporter.exporters

    def test_export(self):
        """Test export"""
        exporter = EditorExporter()

        def export_json(state, **kwargs):
            return b'{"test": "data"}'

        exporter.register_exporter("json", export_json)

        state = EditorState(
            editor_id="test",
            editor_type=EditorType.DOCUMENT,
        )

        result = exporter.export(state, "json")
        assert result == b'{"test": "data"}'

    def test_export_unknown_format(self):
        """Test export with unknown format"""
        exporter = EditorExporter()

        state = EditorState(
            editor_id="test",
            editor_type=EditorType.DOCUMENT,
        )

        with pytest.raises(ValueError):
            exporter.export(state, "unknown")

    def test_available_formats(self):
        """Test getting available formats"""
        exporter = EditorExporter()

        def export_json(state, **kwargs):
            return b"{}"

        def export_xml(state, **kwargs):
            return b"<xml/>"

        exporter.register_exporter("json", export_json)
        exporter.register_exporter("xml", export_xml)

        formats = exporter.available_formats()
        assert "json" in formats
        assert "xml" in formats


class TestEditorTheme:
    """Test EditorTheme class"""

    def test_colors(self):
        """Test color constants"""
        assert EditorTheme.PRIMARY
        assert EditorTheme.SECONDARY
        assert EditorTheme.SUCCESS
        assert EditorTheme.ERROR

    def test_get_color_palette(self):
        """Test getting color palette"""
        colors = EditorTheme.get_color_palette(5)
        assert len(colors) == 5

        # Test with more colors than default
        colors = EditorTheme.get_color_palette(15)
        assert len(colors) == 15


class TestUtilityFunctions:
    """Test utility functions"""

    def test_format_timestamp(self):
        """Test timestamp formatting"""
        timestamp = datetime(2024, 1, 15, 10, 30, 0).timestamp()
        formatted = format_timestamp(timestamp)
        assert "2024-01-15" in formatted
        assert "10:30:00" in formatted

        # Test None
        assert format_timestamp(None) == "Never"

    def test_get_time_ago(self):
        """Test time ago formatting"""
        # Just now
        timestamp = time.time()
        assert "seconds ago" in get_time_ago(timestamp)

        # Minutes ago
        timestamp = time.time() - 120
        assert "minute" in get_time_ago(timestamp)

        # Hours ago
        timestamp = time.time() - 7200
        assert "hour" in get_time_ago(timestamp)

        # Days ago
        timestamp = time.time() - 86400
        assert "day" in get_time_ago(timestamp)

        # None
        assert get_time_ago(None) == "Never"
