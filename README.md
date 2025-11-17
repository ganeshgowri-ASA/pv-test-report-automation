# PV Test Report Automation

World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## Phase 1: Core Streamlit App

This is Phase 1 of the PV Test Report Automation system, featuring a working Streamlit application with:

- **Multi-page Navigation**: Dashboard, Upload Data, Create Report, Review, Export
- **File Upload System**: Support for Excel, PDF, images, and Word documents
- **Data Parsing**: Automatic file parsing and metadata extraction
- **Session State Management**: Persistent data throughout the session
- **Dashboard**: Overview with statistics and activity charts

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd pv-test-report-automation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the App

Run the Streamlit app with:
```bash
streamlit run src/ui/app.py
```

The app will open in your default browser at `http://localhost:8501`

## Project Structure

```
pv-test-report-automation/
├── src/
│   ├── core/
│   │   └── data_ingestion/
│   │       └── file_parser.py      # File parsing logic
│   └── ui/
│       ├── app.py                  # Main entry point
│       └── pages/
│           ├── dashboard.py        # Dashboard page
│           ├── upload.py           # File upload page
│           ├── create_report.py    # Create report (Phase 2)
│           ├── review.py           # Review page (Phase 2)
│           └── export.py           # Export page (Phase 2)
├── .streamlit/
│   └── config.toml                 # Streamlit configuration
└── requirements.txt                # Python dependencies
```

## Features

### ✅ Implemented (Phase 1)

- **Dashboard**: Overview with statistics, recent reports, and activity charts
- **File Upload**: Upload Excel, PDF, images, and Word documents
- **File Parsing**: Automatic parsing with metadata extraction
- **Session Management**: Persistent state across pages
- **Multi-page Navigation**: Easy navigation between sections

### 🚧 Coming Soon (Phase 2+)

- Report template selection and creation
- Data field mapping
- Report review and approval workflow
- Export to multiple formats (PDF, Word, Excel)
- Advanced authentication
- Database integration
- LLM-powered report generation

## Supported File Types

- **Excel**: .xlsx, .xls, .xlsm
- **Images**: .jpg, .jpeg, .png, .gif, .bmp, .tiff
- **PDF**: .pdf
- **Word**: .docx, .doc

## Requirements

- Python 3.8+
- Streamlit 1.31.0
- Pandas 2.2.0
- Pillow 10.2.0
- python-docx 1.1.0
- openpyxl 3.1.2
- plotly 5.18.0

See `requirements.txt` for complete list.

## License

See LICENSE file for details.
