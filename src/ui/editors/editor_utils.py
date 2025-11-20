"""
Editor Utilities Module

Common utilities for all editor components including state management,
undo/redo support, auto-save, validation, and export functionality.
"""

import json
import hashlib
import time
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
import streamlit as st


class EditorType(Enum):
    """Types of editors"""
    DOCUMENT = "document"
    EXCEL = "excel"
    FLOWCHART = "flowchart"
    GANTT = "gantt"


class ActionType(Enum):
    """Types of editor actions for undo/redo"""
    INSERT = "insert"
    DELETE = "delete"
    MODIFY = "modify"
    MOVE = "move"
    FORMAT = "format"
    BULK = "bulk"


@dataclass
class EditorAction:
    """Represents a single editor action for undo/redo"""
    action_type: ActionType
    timestamp: float
    data: Dict[str, Any]
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "action_type": self.action_type.value,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_state": self.previous_state,
            "new_state": self.new_state,
            "description": self.description,
        }


@dataclass
class EditorState:
    """
    Manages editor state with versioning and change tracking.

    Attributes:
        editor_id: Unique identifier for the editor
        editor_type: Type of editor
        content: Current editor content
        metadata: Additional metadata
        version: Current version number
        modified: Whether content has been modified
        last_save_time: Timestamp of last save
        checksum: Content checksum for change detection
    """
    editor_id: str
    editor_type: EditorType
    content: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    modified: bool = False
    last_save_time: Optional[float] = None
    checksum: str = ""

    def __post_init__(self):
        """Initialize checksum"""
        self.update_checksum()

    def update_checksum(self) -> str:
        """Calculate and update content checksum"""
        content_str = json.dumps(self.content, sort_keys=True)
        self.checksum = hashlib.md5(content_str.encode()).hexdigest()
        return self.checksum

    def is_modified(self) -> bool:
        """Check if content has been modified since last save"""
        current_checksum = hashlib.md5(
            json.dumps(self.content, sort_keys=True).encode()
        ).hexdigest()
        return current_checksum != self.checksum

    def mark_saved(self):
        """Mark current state as saved"""
        self.modified = False
        self.last_save_time = time.time()
        self.update_checksum()

    def mark_modified(self):
        """Mark state as modified"""
        self.modified = True

    def increment_version(self):
        """Increment version number"""
        self.version += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "editor_id": self.editor_id,
            "editor_type": self.editor_type.value,
            "content": self.content,
            "metadata": self.metadata,
            "version": self.version,
            "modified": self.modified,
            "last_save_time": self.last_save_time,
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EditorState":
        """Create from dictionary"""
        return cls(
            editor_id=data["editor_id"],
            editor_type=EditorType(data["editor_type"]),
            content=data.get("content", {}),
            metadata=data.get("metadata", {}),
            version=data.get("version", 1),
            modified=data.get("modified", False),
            last_save_time=data.get("last_save_time"),
            checksum=data.get("checksum", ""),
        )


class UndoRedoManager:
    """
    Manages undo/redo operations for editors.

    Provides:
    - Action history tracking
    - Undo/redo functionality
    - History limits
    - State snapshots
    """

    def __init__(self, max_history: int = 50):
        """
        Initialize manager.

        Args:
            max_history: Maximum number of actions to keep in history
        """
        self.max_history = max_history
        self.undo_stack: List[EditorAction] = []
        self.redo_stack: List[EditorAction] = []

    def add_action(self, action: EditorAction):
        """
        Add action to undo stack.

        Args:
            action: Action to add
        """
        self.undo_stack.append(action)
        # Clear redo stack when new action is added
        self.redo_stack.clear()

        # Limit history size
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)

    def can_undo(self) -> bool:
        """Check if undo is available"""
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is available"""
        return len(self.redo_stack) > 0

    def undo(self) -> Optional[EditorAction]:
        """
        Undo last action.

        Returns:
            Action that was undone, or None if nothing to undo
        """
        if not self.can_undo():
            return None

        action = self.undo_stack.pop()
        self.redo_stack.append(action)
        return action

    def redo(self) -> Optional[EditorAction]:
        """
        Redo last undone action.

        Returns:
            Action that was redone, or None if nothing to redo
        """
        if not self.can_redo():
            return None

        action = self.redo_stack.pop()
        self.undo_stack.append(action)
        return action

    def clear_history(self):
        """Clear all history"""
        self.undo_stack.clear()
        self.redo_stack.clear()

    def get_undo_description(self) -> Optional[str]:
        """Get description of next undo action"""
        if self.can_undo():
            return self.undo_stack[-1].description
        return None

    def get_redo_description(self) -> Optional[str]:
        """Get description of next redo action"""
        if self.can_redo():
            return self.redo_stack[-1].description
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "max_history": self.max_history,
            "undo_stack": [action.to_dict() for action in self.undo_stack],
            "redo_stack": [action.to_dict() for action in self.redo_stack],
        }


class AutoSaveManager:
    """
    Manages auto-save functionality for editors.

    Provides:
    - Automatic saving at intervals
    - Save on change detection
    - Save callbacks
    - Recovery support
    """

    def __init__(
        self,
        save_callback: Callable[[EditorState], bool],
        auto_save_interval: int = 60,
        save_on_change: bool = True,
    ):
        """
        Initialize manager.

        Args:
            save_callback: Function to call for saving
            auto_save_interval: Interval in seconds for auto-save
            save_on_change: Whether to save on content change
        """
        self.save_callback = save_callback
        self.auto_save_interval = auto_save_interval
        self.save_on_change = save_on_change
        self.last_auto_save: Optional[float] = None
        self.enabled = True

    def should_auto_save(self, state: EditorState) -> bool:
        """
        Check if auto-save should be triggered.

        Args:
            state: Current editor state

        Returns:
            True if auto-save should happen
        """
        if not self.enabled or not state.modified:
            return False

        if self.last_auto_save is None:
            return True

        time_since_save = time.time() - self.last_auto_save
        return time_since_save >= self.auto_save_interval

    def auto_save(self, state: EditorState) -> bool:
        """
        Perform auto-save if needed.

        Args:
            state: Current editor state

        Returns:
            True if save was performed
        """
        if self.should_auto_save(state):
            success = self.save_callback(state)
            if success:
                self.last_auto_save = time.time()
                return True
        return False

    def manual_save(self, state: EditorState) -> bool:
        """
        Perform manual save.

        Args:
            state: Current editor state

        Returns:
            True if save was successful
        """
        success = self.save_callback(state)
        if success:
            self.last_auto_save = time.time()
        return success

    def enable(self):
        """Enable auto-save"""
        self.enabled = True

    def disable(self):
        """Disable auto-save"""
        self.enabled = False

    def get_time_since_save(self) -> Optional[int]:
        """
        Get time in seconds since last auto-save.

        Returns:
            Seconds since last save, or None if never saved
        """
        if self.last_auto_save is None:
            return None
        return int(time.time() - self.last_auto_save)


class EditorValidator:
    """
    Validates editor content and operations.

    Provides:
    - Content validation
    - Schema validation
    - Custom validation rules
    - Error reporting
    """

    def __init__(self):
        """Initialize validator"""
        self.validation_rules: Dict[str, Callable] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_rule(self, name: str, validator: Callable[[Any], bool]):
        """
        Add validation rule.

        Args:
            name: Rule name
            validator: Validation function
        """
        self.validation_rules[name] = validator

    def validate(self, data: Any, rules: Optional[List[str]] = None) -> bool:
        """
        Validate data against rules.

        Args:
            data: Data to validate
            rules: Specific rules to apply (None = all rules)

        Returns:
            True if validation passed
        """
        self.errors.clear()
        self.warnings.clear()

        rules_to_check = rules or list(self.validation_rules.keys())

        for rule_name in rules_to_check:
            if rule_name in self.validation_rules:
                try:
                    if not self.validation_rules[rule_name](data):
                        self.errors.append(f"Validation failed: {rule_name}")
                except Exception as e:
                    self.errors.append(f"Validation error in {rule_name}: {str(e)}")

        return len(self.errors) == 0

    def validate_required_fields(self, data: Dict, required: List[str]) -> bool:
        """
        Validate that required fields are present.

        Args:
            data: Data dictionary
            required: List of required field names

        Returns:
            True if all required fields present
        """
        missing = [field for field in required if field not in data]
        if missing:
            self.errors.append(f"Missing required fields: {', '.join(missing)}")
            return False
        return True

    def validate_field_types(
        self, data: Dict, type_map: Dict[str, type]
    ) -> bool:
        """
        Validate field types.

        Args:
            data: Data dictionary
            type_map: Map of field names to expected types

        Returns:
            True if all types match
        """
        for field, expected_type in type_map.items():
            if field in data and not isinstance(data[field], expected_type):
                self.errors.append(
                    f"Field '{field}' has wrong type: "
                    f"expected {expected_type.__name__}, "
                    f"got {type(data[field]).__name__}"
                )

        return len(self.errors) == 0

    def get_errors(self) -> List[str]:
        """Get validation errors"""
        return self.errors.copy()

    def get_warnings(self) -> List[str]:
        """Get validation warnings"""
        return self.warnings.copy()

    def clear(self):
        """Clear errors and warnings"""
        self.errors.clear()
        self.warnings.clear()


class EditorExporter:
    """
    Handles exporting editor content to various formats.

    Provides:
    - Multiple format support
    - Custom exporters
    - Template-based export
    - Batch export
    """

    def __init__(self):
        """Initialize exporter"""
        self.exporters: Dict[str, Callable] = {}

    def register_exporter(self, format_name: str, exporter: Callable):
        """
        Register custom exporter.

        Args:
            format_name: Name of export format (e.g., 'pdf', 'docx')
            exporter: Export function
        """
        self.exporters[format_name] = exporter

    def export(
        self,
        state: EditorState,
        format_name: str,
        output_path: Optional[Path] = None,
        **kwargs
    ) -> Optional[bytes]:
        """
        Export editor content.

        Args:
            state: Editor state to export
            format_name: Export format
            output_path: Optional output file path
            **kwargs: Additional export options

        Returns:
            Exported bytes if successful, None otherwise
        """
        if format_name not in self.exporters:
            raise ValueError(f"Unknown export format: {format_name}")

        try:
            data = self.exporters[format_name](state, **kwargs)

            if output_path and data:
                output_path.write_bytes(data)

            return data
        except Exception as e:
            raise RuntimeError(f"Export failed: {str(e)}")

    def export_json(self, state: EditorState, **kwargs) -> bytes:
        """Export as JSON"""
        data = state.to_dict()
        return json.dumps(data, indent=2).encode('utf-8')

    def available_formats(self) -> List[str]:
        """Get list of available export formats"""
        return list(self.exporters.keys())


def init_session_state(key: str, default_value: Any) -> Any:
    """
    Initialize Streamlit session state key.

    Args:
        key: Session state key
        default_value: Default value if key doesn't exist

    Returns:
        Current value of session state key
    """
    if key not in st.session_state:
        st.session_state[key] = default_value
    return st.session_state[key]


def get_session_state(key: str, default: Any = None) -> Any:
    """
    Get value from Streamlit session state.

    Args:
        key: Session state key
        default: Default value if key doesn't exist

    Returns:
        Session state value or default
    """
    return st.session_state.get(key, default)


def set_session_state(key: str, value: Any):
    """
    Set Streamlit session state value.

    Args:
        key: Session state key
        value: Value to set
    """
    st.session_state[key] = value


def clear_session_state(prefix: Optional[str] = None):
    """
    Clear session state keys.

    Args:
        prefix: If provided, only clear keys with this prefix
    """
    if prefix:
        keys_to_delete = [k for k in st.session_state.keys() if k.startswith(prefix)]
        for key in keys_to_delete:
            del st.session_state[key]
    else:
        st.session_state.clear()


def format_timestamp(timestamp: Optional[float]) -> str:
    """
    Format timestamp for display.

    Args:
        timestamp: Unix timestamp

    Returns:
        Formatted datetime string
    """
    if timestamp is None:
        return "Never"

    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_time_ago(timestamp: Optional[float]) -> str:
    """
    Get human-readable time ago string.

    Args:
        timestamp: Unix timestamp

    Returns:
        Time ago string (e.g., "5 minutes ago")
    """
    if timestamp is None:
        return "Never"

    seconds_ago = int(time.time() - timestamp)

    if seconds_ago < 60:
        return f"{seconds_ago} seconds ago"
    elif seconds_ago < 3600:
        minutes = seconds_ago // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds_ago < 86400:
        hours = seconds_ago // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = seconds_ago // 86400
        return f"{days} day{'s' if days != 1 else ''} ago"


class EditorTheme:
    """Editor theme configuration"""

    # Colors
    PRIMARY = "#1f77b4"
    SECONDARY = "#ff7f0e"
    SUCCESS = "#2ca02c"
    WARNING = "#ff9800"
    ERROR = "#d62728"
    INFO = "#17a2b8"

    # Editor colors
    BACKGROUND = "#ffffff"
    TEXT = "#333333"
    BORDER = "#dddddd"
    HIGHLIGHT = "#ffffcc"
    SELECTION = "#b3d9ff"

    # Chart colors
    CHART_COLORS = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
    ]

    @classmethod
    def get_color_palette(cls, n: int = 10) -> List[str]:
        """
        Get color palette.

        Args:
            n: Number of colors needed

        Returns:
            List of color hex codes
        """
        colors = cls.CHART_COLORS.copy()
        while len(colors) < n:
            colors.extend(cls.CHART_COLORS)
        return colors[:n]


# Export main classes
__all__ = [
    "EditorType",
    "ActionType",
    "EditorAction",
    "EditorState",
    "UndoRedoManager",
    "AutoSaveManager",
    "EditorValidator",
    "EditorExporter",
    "EditorTheme",
    "init_session_state",
    "get_session_state",
    "set_session_state",
    "clear_session_state",
    "format_timestamp",
    "get_time_ago",
]
