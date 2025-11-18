# Data Ingestion Module - Usage Guide

Comprehensive guide for using the PV Test Report Automation data ingestion engine.

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Visio Diagram Parsing](#visio-diagram-parsing)
5. [Gantt Chart & MS Project](#gantt-chart--ms-project)
6. [Smartsheet Integration](#smartsheet-integration)
7. [Advanced Usage](#advanced-usage)
8. [API Reference](#api-reference)
9. [Error Handling](#error-handling)
10. [Best Practices](#best-practices)

## Overview

The ingestion module provides comprehensive data extraction capabilities for:

- **Microsoft Visio** (.vsdx) - Process diagrams, test procedures, equipment setups
- **MS Project** (.xml, .mpp) - Gantt charts, test schedules, resource allocation
- **Smartsheet API** - Collaborative test matrices, tracking sheets, team data

## Installation

### Basic Installation

```bash
pip install -r requirements.txt
```

### With Optional Features

```bash
# For MS Project .mpp file support (requires Java)
pip install -r requirements.txt mpxj JPype1

# For PNG export from Visio diagrams
pip install -r requirements.txt cairosvg

# Development dependencies
pip install -r requirements.txt pytest pytest-cov black mypy
```

### Verify Installation

```python
from ingestion import VisioIngestion, GanttIngestion, SmartsheetClient
print("Ingestion module loaded successfully!")
```

## Quick Start

### 1. Parse Visio Test Procedure

```python
from ingestion import VisioIngestion

# Load Visio diagram
visio = VisioIngestion("test_procedure.vsdx")

# Extract process flow
result = visio.extract_process_flow()

print(f"Diagram: {result.diagram_name}")
print(f"Shapes: {len(result.shapes)}")
print(f"Process steps: {len(result.process_flow)}")

# Access individual steps
for step in result.process_flow:
    print(f"Step {step.step_number}: {step.description}")
```

### 2. Parse Gantt Test Schedule

```python
from ingestion import GanttIngestion

# Load MS Project file
gantt = GanttIngestion("test_schedule.xml")

# Extract timeline
timeline = gantt.extract_timeline()

print(f"Project: {timeline.project_name}")
print(f"Duration: {timeline.start_date} to {timeline.end_date}")

# List all tasks
for task in timeline.tasks:
    print(f"{task.task_name}: {task.start_date} - {task.end_date} ({task.completion}%)")

# Get critical path
if timeline.critical_path:
    print(f"Critical tasks: {timeline.critical_path.critical_tasks}")
```

### 3. Sync Smartsheet Test Matrix

```python
import os
from ingestion import SmartsheetClient

# Initialize client (uses SMARTSHEET_API_TOKEN env var)
client = SmartsheetClient()

# Or provide token directly
# client = SmartsheetClient(api_token="your_token_here")

# Get sheet data
sheet = client.get_sheet(sheet_id=123456789)

print(f"Sheet: {sheet.sheet_name}")
print(f"Rows: {len(sheet.rows)}")
print(f"Comments: {len(sheet.comments)}")

# Extract test statuses
statuses = sheet.get_column_values("Status")
print(f"Test statuses: {statuses}")
```

## Visio Diagram Parsing

### Supported Features

- Process flow diagrams
- Equipment connection diagrams
- Test procedure flowcharts
- Decision trees
- Safety protocols

### Basic Usage

```python
from ingestion import VisioIngestion

visio = VisioIngestion("equipment_setup.vsdx")
result = visio.extract_process_flow()

# Access shapes
for shape in result.shapes:
    print(f"Shape: {shape.text} (Type: {shape.shape_type})")
    print(f"  Position: ({shape.position_x}, {shape.position_y})")
    print(f"  Properties: {shape.properties}")

# Access connectors
for conn in result.connectors:
    print(f"Connection: {conn.from_shape_id} -> {conn.to_shape_id}")
    if conn.label:
        print(f"  Label: {conn.label}")
```

### Extract Test Procedure Steps

```python
from ingestion import DiagramExtractor

extractor = DiagramExtractor()
steps = extractor.extract_test_procedure("test_procedure.vsdx")

for step in steps:
    print(f"\nStep {step.step_number}: {step.description}")
    print(f"  Type: {step.step_type}")

    if step.step_type == "decision":
        print(f"  Decision options: {step.decision_options}")

    if step.next_steps:
        print(f"  Next steps: {step.next_steps}")
```

### Export to SVG/PNG

```python
# SVG export (included)
result = visio.extract_process_flow()
svg_content = result.svg_export

with open("diagram.svg", "w") as f:
    f.write(svg_content)

# PNG export (requires cairosvg)
visio.export_to_png("diagram.png", width=1920, height=1080)
```

## Gantt Chart & MS Project

### Supported Features

- Task extraction with dependencies
- Resource assignment parsing
- Critical path calculation
- Milestone tracking
- Timeline visualization

### Extract Tasks

```python
from ingestion import GanttIngestion

gantt = GanttIngestion("project.xml")

# Get all tasks
tasks = gantt.extract_tasks()

for task in tasks:
    print(f"\nTask #{task.task_id}: {task.task_name}")
    print(f"  Dates: {task.start_date} to {task.end_date}")
    print(f"  Duration: {task.duration} days")
    print(f"  Status: {task.status}")
    print(f"  Completion: {task.completion}%")
    print(f"  Resources: {', '.join(task.resources)}")
    print(f"  Dependencies: {task.dependencies}")

    if task.cost:
        print(f"  Cost: ${task.cost:,.2f}")
```

### Analyze Timeline

```python
from ingestion import TimelineParser

parser = TimelineParser()

# Get test schedule by phase
schedule = parser.extract_test_schedule("test_schedule.xml")

print(f"Project: {schedule['project_name']}")
print(f"Total duration: {schedule['total_duration_days']} days\n")

for phase, data in schedule['phases'].items():
    print(f"{phase.upper()}: {data['task_count']} tasks")
    for task in data['tasks']:
        print(f"  - {task['name']} ({task['status']})")
```

### Equipment Booking Schedule

```python
equipment_schedule = parser.extract_equipment_booking("test_schedule.xml")

for equipment, bookings in equipment_schedule.items():
    print(f"\n{equipment}:")
    for booking in bookings:
        print(f"  {booking['start_date']} - {booking['end_date']}: {booking['task_name']}")
```

### Personnel Assignment

```python
personnel = parser.extract_personnel_assignment("test_schedule.xml")

for person, assignments in personnel.items():
    print(f"\n{person}:")
    for assignment in assignments:
        print(f"  {assignment['task_name']} ({assignment['status']})")
```

### Critical Path Analysis

```python
timeline = gantt.extract_timeline()

if timeline.critical_path:
    cp = timeline.critical_path
    print(f"Critical path tasks: {len(cp.critical_tasks)}")
    print(f"Total project duration: {cp.total_duration} days")

    # Show slack time for each task
    for task_id, slack in cp.slack_time.items():
        task = next(t for t in timeline.tasks if t.task_id == task_id)
        print(f"{task.task_name}: {slack} days slack")
```

### Export Formats

```python
# Export to JSON
gantt.export_to_json("timeline.json")

# Export to CSV
gantt.export_to_csv("tasks.csv")

# Export to iCalendar
parser.export_calendar_format("test_schedule.xml", "schedule.ics")
```

## Smartsheet Integration

### Setup API Token

```bash
# Set environment variable
export SMARTSHEET_API_TOKEN="your_api_token_here"
```

Or in Python:

```python
import os
os.environ['SMARTSHEET_API_TOKEN'] = "your_token"
```

### Initialize Client

```python
from ingestion import SmartsheetClient

# Using env variable
client = SmartsheetClient()

# Or provide token directly
client = SmartsheetClient(api_token="your_token")

# Validate connection
if client.validate_connection():
    print("Connected to Smartsheet!")
    user_info = client.get_user_info()
    print(f"Logged in as: {user_info}")
```

### List Available Sheets

```python
sheets = client.list_sheets()

for sheet in sheets:
    print(f"Sheet ID: {sheet['id']}")
    print(f"Name: {sheet['name']}")
    print(f"Modified: {sheet.get('modifiedAt')}")
```

### Search for Sheets

```python
results = client.search_sheets("IEC 61215")

for sheet in results:
    print(f"Found: {sheet['text']} (ID: {sheet['objectId']})")
```

### Get Sheet Data

```python
# Get complete sheet
sheet_data = client.get_sheet(sheet_id=123456789)

print(f"Sheet: {sheet_data.sheet_name}")
print(f"Owner: {sheet_data.owner}")
print(f"Last modified: {sheet_data.modified_date}")

# Access columns
for col in sheet_data.columns:
    print(f"Column: {col.title} ({col.column_type})")
    if col.options:
        print(f"  Options: {col.options}")

# Access rows
for row in sheet_data.rows:
    print(f"\nRow #{row.row_number}:")
    for col_name, value in row.cells.items():
        print(f"  {col_name}: {value}")
```

### Filter and Query Data

```python
# Get specific column values
test_ids = sheet_data.get_column_values("Test ID")
statuses = sheet_data.get_column_values("Status")

print(f"Test IDs: {test_ids}")
print(f"Statuses: {statuses}")

# Filter rows
completed_tests = client.filter_rows(
    sheet_id=123456789,
    filter_column="Status",
    filter_value="Completed"
)

print(f"Completed tests: {len(completed_tests)}")
for row in completed_tests:
    print(f"  {row.cells.get('Test Name')}")
```

### Access Comments and Attachments

```python
# Get comments
for comment in sheet_data.comments:
    print(f"\nComment by {comment.created_by}:")
    print(f"  {comment.text}")
    print(f"  Posted: {comment.created_at}")

# Get attachments
for attachment in sheet_data.attachments:
    print(f"\nAttachment: {attachment.name}")
    print(f"  Type: {attachment.mime_type}")
    print(f"  Size: {attachment.size_bytes / 1024:.1f} KB")

    # Download attachment
    client.download_attachment(attachment, output_dir="./downloads")
```

### Export Sheet Data

```python
# Export to CSV
client.export_to_csv(sheet_id=123456789, output_path="test_matrix.csv")

# Export to JSON
client.export_to_json(sheet_id=123456789, output_path="test_matrix.json")

# Convert to dict rows for processing
dict_rows = sheet_data.to_dict_rows()
```

### Refresh Data

```python
# Get latest data from Smartsheet
refreshed_data = client.refresh_sheet_data(sheet_id=123456789)
print(f"Data refreshed at: {refreshed_data.ingestion_timestamp}")
```

## Advanced Usage

### Batch Processing

```python
from pathlib import Path
from ingestion import GanttIngestion, VisioIngestion

# Process multiple Gantt files
project_dir = Path("./projects")
for xml_file in project_dir.glob("*.xml"):
    gantt = GanttIngestion(str(xml_file))
    timeline = gantt.extract_timeline()

    # Export to JSON
    output_file = xml_file.with_suffix(".json")
    gantt.export_to_json(str(output_file))
    print(f"Processed: {xml_file.name}")

# Process multiple Visio diagrams
diagram_dir = Path("./diagrams")
for vsdx_file in diagram_dir.glob("*.vsdx"):
    visio = VisioIngestion(str(vsdx_file))
    result = visio.extract_process_flow()

    # Save SVG export
    svg_file = vsdx_file.with_suffix(".svg")
    with open(svg_file, "w") as f:
        f.write(result.svg_export)
    print(f"Processed: {vsdx_file.name}")
```

### Compare Diagram Versions

```python
from ingestion import DiagramExtractor

extractor = DiagramExtractor()

# Compare two versions of a diagram
differences = extractor.compare_diagrams(
    "test_procedure_v1.vsdx",
    "test_procedure_v2.vsdx"
)

print(f"Shape count difference: {differences['shape_count_diff']}")
print(f"Connector count difference: {differences['connector_count_diff']}")

for change in differences['text_changes']:
    print(f"\nText {change['type']}:")
    for item in change['items']:
        print(f"  - {item}")
```

### Resource Conflict Detection

```python
from ingestion import TimelineParser

parser = TimelineParser()

# Identify scheduling conflicts
conflicts = parser.identify_conflicts("test_schedule.xml")

if conflicts:
    print(f"Found {len(conflicts)} resource conflicts!")
    for conflict in conflicts:
        print(f"\nConflict for {conflict['resource']}:")
        print(f"  Task 1: {conflict['task1_name']} ({conflict['task1_dates']})")
        print(f"  Task 2: {conflict['task2_name']} ({conflict['task2_dates']})")
        print(f"  Overlap: {conflict['overlap_start']} to {conflict['overlap_end']}")
else:
    print("No resource conflicts found.")
```

### Gantt Visualization Data

```python
# Generate data for frontend Gantt chart
viz_data = parser.generate_gantt_visualization_data("test_schedule.xml")

# Output JSON for web visualization
import json
with open("gantt_viz.json", "w") as f:
    json.dump(viz_data, f, indent=2)

# Data includes:
# - Task hierarchy
# - Critical path indicators
# - Progress percentages
# - Dependencies
# - Milestones
```

## Error Handling

### Graceful Error Handling

```python
from ingestion import (
    VisioIngestion,
    VisioParsingError,
    GanttIngestion,
    GanttParsingError,
    SmartsheetClient,
    SmartsheetAPIError
)

# Visio parsing
try:
    visio = VisioIngestion("diagram.vsdx")
    result = visio.extract_process_flow()
except VisioParsingError as e:
    print(f"Visio parsing error: {e}")
except FileNotFoundError:
    print("File not found")

# Gantt parsing
try:
    gantt = GanttIngestion("schedule.xml")
    tasks = gantt.extract_tasks()
except GanttParsingError as e:
    print(f"Gantt parsing error: {e}")

# Smartsheet API
try:
    client = SmartsheetClient()
    sheet = client.get_sheet(123456)
except SmartsheetAPIError as e:
    print(f"Smartsheet API error: {e}")
```

### Logging

```python
import logging

# Enable logging for ingestion module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ingestion')
logger.setLevel(logging.DEBUG)

# Now ingestion operations will log detailed information
visio = VisioIngestion("diagram.vsdx")
result = visio.extract_process_flow()
```

## Best Practices

### 1. File Validation

```python
from pathlib import Path

def safe_parse_visio(file_path):
    """Safely parse Visio file with validation"""
    path = Path(file_path)

    # Check file exists
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Check file extension
    if path.suffix.lower() != '.vsdx':
        raise ValueError(f"Invalid file type: {path.suffix}")

    # Check file size (avoid very large files)
    max_size_mb = 50
    if path.stat().st_size > max_size_mb * 1024 * 1024:
        raise ValueError(f"File too large (> {max_size_mb}MB)")

    # Parse file
    visio = VisioIngestion(str(path))
    return visio.extract_process_flow()
```

### 2. API Token Security

```python
# DON'T: Hard-code tokens
client = SmartsheetClient(api_token="abc123...")  # Bad!

# DO: Use environment variables
import os
api_token = os.environ.get('SMARTSHEET_API_TOKEN')
if not api_token:
    raise ValueError("SMARTSHEET_API_TOKEN not set")
client = SmartsheetClient(api_token=api_token)

# DO: Use .env files with python-dotenv
from dotenv import load_dotenv
load_dotenv()
client = SmartsheetClient()
```

### 3. Caching Results

```python
import json
from pathlib import Path
from datetime import datetime

def cached_timeline_extraction(xml_path, cache_dir="./cache"):
    """Extract timeline with caching"""
    cache_path = Path(cache_dir) / f"{Path(xml_path).stem}_timeline.json"

    # Check if cached version exists and is recent
    if cache_path.exists():
        cache_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        if cache_age.total_seconds() < 3600:  # 1 hour
            with open(cache_path) as f:
                return json.load(f)

    # Extract fresh data
    gantt = GanttIngestion(xml_path)
    timeline = gantt.extract_timeline()

    # Cache result
    cache_path.parent.mkdir(exist_ok=True)
    with open(cache_path, 'w') as f:
        json.dump(timeline.model_dump(mode='json'), f, default=str)

    return timeline.model_dump(mode='json')
```

### 4. Progress Tracking

```python
from tqdm import tqdm

def process_multiple_files(file_list):
    """Process multiple files with progress bar"""
    results = []

    for file_path in tqdm(file_list, desc="Processing files"):
        try:
            if file_path.endswith('.vsdx'):
                visio = VisioIngestion(file_path)
                result = visio.extract_process_flow()
            elif file_path.endswith('.xml'):
                gantt = GanttIngestion(file_path)
                result = gantt.extract_timeline()

            results.append({
                'file': file_path,
                'status': 'success',
                'result': result
            })
        except Exception as e:
            results.append({
                'file': file_path,
                'status': 'error',
                'error': str(e)
            })

    return results
```

## API Reference

See individual module documentation:

- `ingestion.visio_parser` - Visio diagram parsing
- `ingestion.gantt_parser` - Gantt chart parsing
- `ingestion.smartsheet_client` - Smartsheet API client
- `ingestion.diagram_extractor` - High-level diagram extraction
- `ingestion.timeline_parser` - Timeline analysis
- `ingestion.models` - Pydantic data models

## Support

For issues, questions, or contributions:
- GitHub: https://github.com/ganeshgowri-ASA/pv-test-report-automation
- Issues: https://github.com/ganeshgowri-ASA/pv-test-report-automation/issues

## License

MIT License - See LICENSE file for details
