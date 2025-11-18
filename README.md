# PV Test Report Automation

World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## Features

### Phase 2 - Session 10: Visio/Gantt/Smartsheet Ingestion

This implementation provides comprehensive data ingestion capabilities for:

- **Visio Diagrams (.vsdx)**: Extract test procedures, equipment connection diagrams, and flowcharts
- **MS Project Files (.mpp)**: Import test schedules, timelines, and project dependencies
- **Smartsheet Integration**: Real-time data synchronization via Smartsheet API

## Installation

### Prerequisites

- Python 3.9 or higher
- Java Runtime Environment (JRE) 8+ (required for MS Project file processing)

### Install Dependencies

```bash
# Clone the repository
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation

# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (for testing)
pip install -r requirements-dev.txt
```

### Alternative Installation

```bash
# Install as a package
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

## Configuration

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Smartsheet API Configuration
SMARTSHEET_API_KEY=your_smartsheet_api_key_here
SMARTSHEET_WORKSPACE_ID=your_workspace_id_here

# Visio Configuration
VISIO_ENABLE=true
VISIO_DEFAULT_EXPORT_FORMAT=svg

# Gantt/MS Project Configuration
GANTT_DEFAULT_FORMAT=json
GANTT_ENABLE_BASELINE_COMPARISON=true

# Application Settings
LOG_LEVEL=INFO
ENVIRONMENT=development

# File Processing
MAX_FILE_SIZE_MB=100
TEMP_DIR=/tmp/pv-ingestion
```

## Usage

### Visio Diagram Ingestion

```python
from pathlib import Path
from src.ingestion.visio import VisioIngestionModule

# Initialize module
visio_module = VisioIngestionModule()

# Ingest Visio file
result = visio_module.ingest(Path("data/test_procedure.vsdx"))

# Access extracted data
print(f"Diagram: {result.diagram_name}")
print(f"Pages: {len(result.pages)}")
print(f"Total shapes: {len(result.shapes)}")

# Process shapes
for shape in result.shapes:
    print(f"  {shape.name}: {shape.text}")
    print(f"    Position: ({shape.x}, {shape.y})")
    print(f"    Connections: {shape.connected_to}")

# Save SVG export
Path("output/diagram.svg").write_text(result.svg_export)
```

### Gantt/MS Project Ingestion

```python
from pathlib import Path
from src.ingestion.gantt import GanttIngestionModule

# Initialize module
gantt_module = GanttIngestionModule()

# Ingest project file
result = gantt_module.ingest(Path("data/test_schedule.mpp"))

# Access project data
print(f"Project: {result.project_name}")
print(f"Duration: {result.project_start} to {result.project_end}")
print(f"Progress: {result.percent_complete}%")

# Process tasks
for task in result.tasks:
    print(f"  {task.name}")
    print(f"    Status: {task.status.value}")
    print(f"    Progress: {task.percent_complete}%")
    print(f"    Dependencies: {task.dependencies}")

    # Process resources
    for resource in task.resources:
        print(f"      Resource: {resource.name} ({resource.allocation_percent}%)")
```

### Smartsheet API Ingestion

```python
import os
from src.ingestion.smartsheet import SmartsheetIngestionModule

# Set API key
os.environ["SMARTSHEET_API_KEY"] = "your_api_key"

# Initialize module
smartsheet_module = SmartsheetIngestionModule()

# List available sheets
workspaces = smartsheet_module.list_workspaces()
sheets = smartsheet_module.list_sheets_in_workspace(workspaces[0]['id'])

# Ingest sheet data
result = smartsheet_module.ingest(sheets[0]['id'])

# Access sheet data
print(f"Sheet: {result.sheet_name}")
print(f"Rows: {result.total_rows}")
print(f"Columns: {result.total_columns}")

# Process columns
for column in result.columns:
    print(f"  {column.title} ({column.column_type})")

# Process rows
for row in result.rows:
    for cell in row.cells:
        print(f"    {cell.column_id}: {cell.value}")
```

## Examples

See the `examples/` directory for complete working examples:

- `visio_ingestion_example.py`: Comprehensive Visio diagram processing
- `gantt_ingestion_example.py`: MS Project file analysis with task trees
- `smartsheet_ingestion_example.py`: Smartsheet API integration

Run examples:

```bash
python examples/visio_ingestion_example.py
python examples/gantt_ingestion_example.py
python examples/smartsheet_ingestion_example.py
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Skip slow tests
```

## Architecture

```
pv-test-report-automation/
├── src/
│   ├── core/               # Core models and configuration
│   │   ├── models.py       # Pydantic data models
│   │   ├── config.py       # Configuration management
│   │   └── exceptions.py   # Custom exceptions
│   │
│   ├── ingestion/          # Data ingestion modules
│   │   ├── base.py         # Abstract base classes
│   │   ├── visio.py        # Visio diagram ingestion
│   │   ├── gantt.py        # MS Project ingestion
│   │   └── smartsheet.py   # Smartsheet API ingestion
│   │
│   └── utils/              # Utility functions
│       ├── logger.py       # Logging utilities
│       └── validators.py   # Data validation
│
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
│
├── examples/              # Usage examples
└── configs/               # Configuration files
```

## Data Models

### VisioIngestionResult

```python
class VisioIngestionResult(BaseModel):
    diagram_name: str
    file_path: str
    pages: List[VisioPage]
    shapes: List[DiagramShape]
    svg_export: str
    metadata: dict
    status: IngestionStatus
    errors: List[str]
```

### GanttIngestionResult

```python
class GanttIngestionResult(BaseModel):
    project_name: str
    file_path: str
    project_start: datetime
    project_end: datetime
    tasks: List[ProjectTask]
    metadata: dict
    total_tasks: int
    completed_tasks: int
    percent_complete: float
    status: IngestionStatus
```

### SmartsheetIngestionResult

```python
class SmartsheetIngestionResult(BaseModel):
    sheet_name: str
    sheet_id: str
    workspace_id: Optional[str]
    columns: List[SmartsheetColumn]
    rows: List[SmartsheetRow]
    metadata: dict
    total_rows: int
    total_columns: int
    status: IngestionStatus
```

## API Reference

See inline documentation in source files for detailed API reference.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the test suite
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Create an issue on GitHub
- Contact: info@pvtestlab.com

## Roadmap

### Completed
- ✅ Visio diagram ingestion (.vsdx)
- ✅ MS Project file ingestion (.mpp)
- ✅ Smartsheet API integration
- ✅ SVG export for diagrams
- ✅ Hierarchical task structures
- ✅ Resource allocation tracking

### Upcoming
- LLM integration for test report generation
- Multi-format export (PDF, DOCX, HTML)
- Advanced data validation against standards
- Automated reviewer workflows
- Real-time collaboration features
