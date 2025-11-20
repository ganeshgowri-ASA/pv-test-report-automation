# Export Module - Quick Reference

## Quick Import
```python
from export import (
    JSONExporter, XMLExporter, HTMLExporter,
    PDFExporter, WordExporter, ExcelExporter,
    ExportOptions, ExportFormat, create_exporter
)
```

## Basic Export (All Formats)

### JSON
```python
exporter = JSONExporter()
options = ExportOptions(output_path="report.json")
exporter.export(data, options)
```

### XML
```python
exporter = XMLExporter()
options = ExportOptions(output_path="report.xml")
exporter.export(data, options)
```

### HTML
```python
exporter = HTMLExporter()
options = ExportOptions(output_path="report.html", include_charts=True)
exporter.export(data, options)
```

### PDF (requires: reportlab)
```python
from export.pdf_exporter import PDFEngine
exporter = PDFExporter(engine=PDFEngine.REPORTLAB)
options = ExportOptions(output_path="report.pdf", watermark="DRAFT")
exporter.export(data, options)
```

### Word (requires: python-docx)
```python
exporter = WordExporter()
options = ExportOptions(output_path="report.docx")
exporter.export(data, options)
```

### Excel (requires: openpyxl)
```python
from export.excel_exporter import ExcelEngine
exporter = ExcelExporter(engine=ExcelEngine.OPENPYXL)
options = ExportOptions(output_path="report.xlsx", include_charts=True)
exporter.export(data, options)
```

## Batch Export
```python
data_items = [{"name": "report1"}, {"name": "report2"}]
options_template = ExportOptions(output_path="dummy.json")
results = exporter.batch_export(data_items, output_dir, options_template)
```

## Progress Tracking
```python
def progress_callback(progress):
    print(f"{progress.progress_percentage:.1f}%")

exporter.add_progress_callback(progress_callback)
```

## Multi-Format Export
```python
for fmt in [ExportFormat.JSON, ExportFormat.PDF, ExportFormat.HTML]:
    exp = create_exporter(fmt)
    exp.export(data, options)
```

## Sample Data Structure
```python
data = {
    "title": "PV Test Report",
    "summary": "Executive summary text",
    "configuration": {"param": "value"},
    "test_results": [
        {
            "name": "Test Name",
            "status": "PASS",  # or "FAIL"
            "value": 42.5,
            "expected": 42.0,
            "unit": "V"
        }
    ],
    "analysis": "Analysis text",
    "recommendations": ["Recommendation 1"]
}
```

## Installation

### Core (no dependencies)
```bash
# JSON, XML, HTML work out of the box
```

### All Features
```bash
pip install reportlab PyPDF2 python-docx jinja2 plotly openpyxl jsonschema lxml
```

## Verification
```bash
python src/export/verify_installation.py
```

## Testing
```bash
python -m unittest discover src/export/tests
```

## File Locations
- Module: `/home/user/pv-test-report-automation/src/export/`
- Docs: `/home/user/pv-test-report-automation/src/export/README.md`
- Tests: `/home/user/pv-test-report-automation/src/export/tests/`
- Examples: `/home/user/pv-test-report-automation/src/export/example_usage.py`
