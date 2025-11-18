# PV Test Report Automation

World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## Features

### Data Ingestion Engine (Phase 2, Session 10)

Comprehensive data ingestion from multiple sources:

#### Microsoft Visio Support
- Parse .vsdx diagram files
- Extract process flow diagrams
- Parse equipment connection diagrams
- Extract test procedure flowcharts
- Convert diagrams to SVG/PNG
- Analyze decision trees

#### Gantt Chart & MS Project
- Parse MS Project XML files (.xml)
- Parse MS Project binary files (.mpp) with mpxj
- Extract task lists with dependencies
- Calculate critical path
- Resource allocation analysis
- Export to JSON, CSV, iCalendar formats

#### Smartsheet Integration
- Connect to Smartsheet API
- Extract collaborative test tracking sheets
- Parse test matrices
- Download comments and attachments
- Real-time data refresh
- Export to CSV/JSON

### Use Cases

1. **Test Procedure Import** - Import Visio test procedures into structured database records
2. **Schedule Synchronization** - Sync Gantt test schedules with lab booking systems
3. **Test Matrix Management** - Import Smartsheet test requirements into reports
4. **Equipment Diagrams** - Embed Visio equipment setup diagrams in test reports
5. **Timeline Visualization** - Generate test timelines from MS Project data

## Installation

```bash
# Clone repository
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation

# Install dependencies
pip install -r requirements.txt

# Optional: MS Project .mpp support (requires Java)
pip install mpxj JPype1

# Optional: PNG export from Visio diagrams
pip install cairosvg
```

## Quick Start

### Parse Visio Test Procedure

```python
from ingestion import VisioIngestion

visio = VisioIngestion("test_procedure.vsdx")
result = visio.extract_process_flow()

print(f"Extracted {len(result.process_flow)} test steps")
for step in result.process_flow:
    print(f"Step {step.step_number}: {step.description}")
```

### Parse Gantt Test Schedule

```python
from ingestion import GanttIngestion

gantt = GanttIngestion("test_schedule.xml")
timeline = gantt.extract_timeline()

print(f"Project: {timeline.project_name}")
print(f"Duration: {(timeline.end_date - timeline.start_date).days} days")

for task in timeline.tasks:
    print(f"{task.task_name}: {task.start_date} - {task.end_date}")
```

### Sync Smartsheet Test Matrix

```python
import os
from ingestion import SmartsheetClient

# Set API token
os.environ['SMARTSHEET_API_TOKEN'] = "your_api_token"

client = SmartsheetClient()
sheet = client.get_sheet(sheet_id=123456789)

print(f"Sheet: {sheet.sheet_name}")
print(f"Test statuses: {sheet.get_column_values('Status')}")
```

## Documentation

- [Complete Ingestion Guide](INGESTION_GUIDE.md) - Comprehensive usage guide
- [API Reference](ingestion/README.md) - Module documentation
- [Sample Data](ingestion/sample_data/README.md) - Example files

## Project Structure

```
pv-test-report-automation/
├── ingestion/                  # Data ingestion module
│   ├── __init__.py            # Module exports
│   ├── models.py              # Pydantic data models
│   ├── visio_parser.py        # Visio diagram parser
│   ├── gantt_parser.py        # Gantt/MS Project parser
│   ├── smartsheet_client.py   # Smartsheet API client
│   ├── diagram_extractor.py   # High-level diagram extraction
│   ├── timeline_parser.py     # Timeline analysis
│   ├── test_visio_gantt.py    # Unit tests
│   └── sample_data/           # Sample files for testing
├── requirements.txt           # Python dependencies
├── setup.py                   # Package setup
├── INGESTION_GUIDE.md        # Usage guide
└── README.md                  # This file
```

## Testing

```bash
# Run unit tests
python -m pytest ingestion/test_visio_gantt.py -v

# Run with coverage
python -m pytest ingestion/test_visio_gantt.py --cov=ingestion --cov-report=html

# Run specific test
python -m pytest ingestion/test_visio_gantt.py::TestGanttParser -v
```

## Technical Stack

- **Python 3.8+**
- **Pydantic** - Data validation and models
- **lxml** - XML parsing
- **requests** - HTTP client for Smartsheet API
- **mpxj** (optional) - MS Project .mpp file support
- **cairosvg** (optional) - SVG to PNG conversion

## Standards Compliance

The system supports the following PV testing standards:

- IEC 61215 (Design qualification and type approval)
- IEC 61730 (Photovoltaic module safety qualification)
- IEC 61853 (Performance testing and energy rating)
- IEC 62716 (Ammonia corrosion testing)
- IEC 61701 (Salt mist corrosion testing)
- IEC 62804 (Potential induced degradation)
- IEC 60904 (Photovoltaic devices)
- IEC 62759 (Transportation testing)
- ISO 17025 (Testing and calibration laboratories)
- ISO 9001 (Quality management systems)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - See [LICENSE](LICENSE) for details

## Support

For questions or issues:
- GitHub Issues: https://github.com/ganeshgowri-ASA/pv-test-report-automation/issues
- Documentation: [INGESTION_GUIDE.md](INGESTION_GUIDE.md)

## Acknowledgments

Developed for PV testing laboratories requiring comprehensive report automation with multi-source data ingestion capabilities.
