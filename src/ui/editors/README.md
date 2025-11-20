# Editor Components Package

Production-ready Streamlit editor components for PV test report automation.

## Overview

This package provides a comprehensive suite of interactive editor components designed for managing PV (Photovoltaic) test reports and project documentation. Each editor is built with Streamlit and includes advanced features like undo/redo, auto-save, validation, and export capabilities.

## Components

### 1. Document Editor (`document_editor.py`)

Rich text document editor with section management and collaboration features.

**Features:**
- Section-based document structure
- Multiple heading levels (H1-H6)
- Comment and annotation system
- Version comparison
- Template library (PV Test Report, Protocol Document, etc.)
- Auto-save functionality
- Export formats: JSON, Markdown, HTML, Plain Text

**Usage:**
```python
from src.ui.editors import DocumentEditor

editor = DocumentEditor(
    editor_id="my_document",
    auto_save_interval=60,
    max_history=50
)

# In your Streamlit app
editor.render()
```

**Templates:**
- **PV Test Report**: Standard test report with Executive Summary, Introduction, Test Procedures, Results, Analysis, Conclusions
- **Protocol Document**: Test protocol with Overview, Setup, Safety, Procedures, Data Collection
- **Blank Document**: Start from scratch

### 2. Excel Editor (`excel_editor.py`)

Excel-like spreadsheet editor with AgGrid integration.

**Features:**
- Interactive grid editing with AgGrid
- Cell formulas (e.g., `=A1+B1`)
- Data validation rules (range, list, regex, custom)
- Import/Export (CSV, Excel)
- Bulk operations (add rows/columns, fill, clear)
- Conditional formatting
- Filtering and sorting

**Usage:**
```python
from src.ui.editors import ExcelEditor

editor = ExcelEditor(editor_id="my_spreadsheet")
editor.render()

# Access data
df = editor.get_dataframe()

# Set data
import pandas as pd
df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
editor.set_dataframe(df)
```

**Validation Types:**
- **Range**: Numeric range (min-max)
- **List**: Dropdown selection
- **Regex**: Pattern matching
- **Custom**: Custom validation function

### 3. Flowchart Editor (`flowchart_editor.py`)

Interactive flowchart editor for test procedures.

**Features:**
- Multiple node types (Start, End, Process, Decision, I/O, etc.)
- Drag-and-drop interface (position-based)
- Connection management
- Auto-layout (vertical/horizontal)
- Flow validation
- Export to Mermaid syntax (PNG/SVG exportable)
- Template library

**Usage:**
```python
from src.ui.editors import FlowchartEditor

editor = FlowchartEditor(editor_id="my_flowchart")
editor.render()
```

**Node Types:**
- **Start/End**: Flow start and end points
- **Process**: Standard process step
- **Decision**: Conditional branching
- **Input/Output**: Data input/output operations
- **Subprocess**: Subprocess reference
- **Document**: Document reference
- **Connector**: Flow connector

**Templates:**
- **Basic Test Procedure**: Linear test flow
- **Decision-Based Procedure**: Test with decision points
- **Blank Flowchart**: Empty canvas

### 4. Gantt Editor (`gantt_editor.py`)

Project timeline editor with task management and resource allocation.

**Features:**
- Interactive Gantt chart visualization (Plotly)
- Task dependencies
- Resource allocation
- Milestone tracking
- Progress tracking (0-100%)
- Task status management
- Priority levels
- Critical path calculation
- Export to JSON

**Usage:**
```python
from src.ui.editors import GanttEditor

editor = GanttEditor(editor_id="my_project")
editor.render()

# Access tasks
tasks = editor.get_tasks()

# Access resources
resources = editor.get_resources()
```

**Task Status:**
- Not Started
- In Progress
- Completed
- Blocked
- On Hold

**Priority Levels:**
- Low
- Medium
- High
- Critical

### 5. Editor Utilities (`editor_utils.py`)

Common utilities shared across all editors.

**Classes:**

#### `EditorState`
Manages editor state with versioning and change tracking.
```python
state = EditorState(
    editor_id="my_editor",
    editor_type=EditorType.DOCUMENT,
    content={"key": "value"}
)

# Check if modified
if state.is_modified():
    state.mark_saved()
```

#### `UndoRedoManager`
Manages undo/redo operations.
```python
manager = UndoRedoManager(max_history=50)

# Add action
action = EditorAction(
    action_type=ActionType.INSERT,
    timestamp=time.time(),
    data={"test": "data"},
    description="Add item"
)
manager.add_action(action)

# Undo/Redo
if manager.can_undo():
    manager.undo()

if manager.can_redo():
    manager.redo()
```

#### `AutoSaveManager`
Manages automatic saving.
```python
def save_callback(state):
    # Save logic here
    return True

manager = AutoSaveManager(
    save_callback=save_callback,
    auto_save_interval=60  # seconds
)

# Check and auto-save
if manager.auto_save(state):
    print("Auto-saved!")
```

#### `EditorValidator`
Validates editor content.
```python
validator = EditorValidator()

# Add validation rule
validator.add_rule("positive", lambda x: x > 0)

# Validate
if validator.validate(data):
    print("Valid!")
else:
    print(f"Errors: {validator.get_errors()}")
```

#### `EditorExporter`
Handles exporting to various formats.
```python
exporter = EditorExporter()

# Register custom exporter
def export_pdf(state, **kwargs):
    # Generate PDF
    return pdf_bytes

exporter.register_exporter("pdf", export_pdf)

# Export
data = exporter.export(state, "pdf", output_path=Path("output.pdf"))
```

## Architecture

### State Management

All editors use Streamlit's session state for persistence across reruns:

```python
# Initialize state
if "my_editor_state" not in st.session_state:
    st.session_state["my_editor_state"] = EditorState(...)

# Access state
state = st.session_state["my_editor_state"]
```

### Undo/Redo Pattern

Each editor implements undo/redo using the action pattern:

1. User performs action
2. Create `EditorAction` with previous and new state
3. Add to `UndoRedoManager`
4. On undo: restore previous state
5. On redo: restore new state

### Auto-Save Pattern

Auto-save is implemented using:

1. Check if content modified
2. Check if interval elapsed
3. Call save callback
4. Update last save timestamp

### Validation Pattern

Validation is rule-based:

1. Define validation rules
2. Register with `EditorValidator`
3. Validate data against rules
4. Collect errors/warnings
5. Display to user

## Testing

Comprehensive test suite included in `tests/` directory.

**Run all tests:**
```bash
pytest src/ui/editors/tests/
```

**Run specific test file:**
```bash
pytest src/ui/editors/tests/test_document_editor.py
```

**Run with coverage:**
```bash
pytest --cov=src/ui/editors src/ui/editors/tests/
```

**Test Files:**
- `test_editor_utils.py`: Utility classes tests
- `test_document_editor.py`: Document editor tests
- `test_excel_editor.py`: Excel editor tests
- `test_flowchart_editor.py`: Flowchart editor tests
- `test_gantt_editor.py`: Gantt editor tests

## Dependencies

### Required
- `streamlit`: Web framework
- `pandas`: Data manipulation
- `numpy`: Numerical operations
- `plotly`: Charting library
- `st-aggrid`: AgGrid integration for Streamlit

### Optional
- `openpyxl`: Excel file support
- `python-docx`: Word document export
- `reportlab`: PDF generation
- `mermaid`: Flowchart rendering

## Integration Example

Example of integrating all editors in a Streamlit app:

```python
import streamlit as st
from src.ui.editors import (
    DocumentEditor,
    ExcelEditor,
    FlowchartEditor,
    GanttEditor,
)

def main():
    st.title("PV Test Report Management")

    # Sidebar navigation
    editor_type = st.sidebar.selectbox(
        "Select Editor",
        ["Document", "Spreadsheet", "Flowchart", "Timeline"]
    )

    # Render selected editor
    if editor_type == "Document":
        editor = DocumentEditor()
        editor.render()

    elif editor_type == "Spreadsheet":
        editor = ExcelEditor()
        editor.render()

    elif editor_type == "Flowchart":
        editor = FlowchartEditor()
        editor.render()

    elif editor_type == "Timeline":
        editor = GanttEditor()
        editor.render()

if __name__ == "__main__":
    main()
```

## Best Practices

### 1. State Management
- Always use unique `editor_id` for each editor instance
- Clear session state when switching between documents
- Use `mark_modified()` and `mark_saved()` appropriately

### 2. Performance
- Limit auto-save frequency (recommended: 60 seconds)
- Use pagination for large datasets in Excel editor
- Limit undo history (recommended: 50 actions)

### 3. Validation
- Add validation rules before allowing user input
- Display validation errors clearly
- Prevent invalid data from being saved

### 4. Export
- Always validate data before export
- Provide multiple export formats
- Include metadata in exports

### 5. User Experience
- Show save status clearly
- Provide undo/redo feedback
- Use progress indicators for long operations
- Implement keyboard shortcuts where applicable

## Customization

### Custom Templates

Add custom document templates:
```python
from src.ui.editors.document_editor import DocumentTemplate

template = DocumentTemplate(
    name="Custom Template",
    description="My custom template",
    sections=[
        {"title": "Section 1", "level": 1, "order": 0},
        {"title": "Section 2", "level": 1, "order": 1},
    ]
)

editor = DocumentEditor()
editor.templates.append(template)
```

### Custom Validation Rules

Add custom validation:
```python
def validate_email(value):
    import re
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, value))

editor.validator.add_rule("email", validate_email)
```

### Custom Export Formats

Register custom exporter:
```python
def export_custom(state, **kwargs):
    # Custom export logic
    return custom_bytes

editor.exporter.register_exporter("custom", export_custom)
```

## Troubleshooting

### Editor not updating
- Check if `st.rerun()` is called after state changes
- Verify session state key is unique
- Ensure `mark_modified()` is called

### Auto-save not working
- Check if `modified` flag is set
- Verify save callback returns True
- Check auto-save interval

### Undo/redo not working
- Ensure actions are added to manager
- Verify previous/new state is captured
- Check history limit not exceeded

### Export fails
- Verify export format is registered
- Check data is valid
- Ensure required libraries installed

## Future Enhancements

Planned features for future versions:

1. **Real-time Collaboration**
   - Multi-user editing
   - Conflict resolution
   - User presence indicators

2. **Advanced Formatting**
   - Rich text formatting (bold, italic, etc.)
   - Tables and images
   - Code syntax highlighting

3. **Version Control**
   - Git-like version history
   - Branch and merge
   - Diff visualization

4. **AI Integration**
   - Auto-complete suggestions
   - Grammar checking
   - Content generation

5. **Cloud Storage**
   - Auto-sync to cloud
   - Offline support
   - Version backup

## License

This package is part of the PV Test Report Automation system.

## Support

For issues, questions, or contributions, please refer to the main project documentation.
