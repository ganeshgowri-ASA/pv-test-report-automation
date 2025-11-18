# PV Test Report Export Module

Production-ready export engines for multiple formats with template customization, batch export support, and quality validation.

## Features

✅ **Multiple Export Formats**
- PDF (ReportLab/WeasyPrint)
- Word (.docx)
- HTML (responsive, interactive)
- Excel (.xlsx)
- JSON (with schema validation)
- XML (with XSD validation)

✅ **Advanced Capabilities**
- Template-based generation
- Batch export support
- Progress tracking
- Quality validation
- Custom styling
- Digital signatures (PDF)
- Interactive charts (Plotly)
- Multi-sheet workbooks (Excel)

## Installation

### Core Package
```bash
# Core export functionality (JSON/XML only)
pip install -r requirements.txt
```

### Optional Dependencies

Install specific exporters as needed:

```bash
# PDF Export
pip install reportlab PyPDF2
# OR
pip install weasyprint

# Word Export
pip install python-docx

# HTML Export with Charts
pip install jinja2 plotly

# Excel Export
pip install openpyxl
# OR
pip install xlsxwriter

# Enhanced Validation
pip install jsonschema lxml

# All exporters
pip install reportlab PyPDF2 python-docx jinja2 plotly openpyxl jsonschema lxml
```

## Quick Start

### Basic Export

```python
from export import JSONExporter, ExportOptions
from pathlib import Path

# Create exporter
exporter = JSONExporter()

# Prepare data
data = {
    "title": "PV Test Report",
    "test_results": [
        {"name": "Voltage Test", "status": "PASS", "value": 42.5}
    ]
}

# Export
options = ExportOptions(output_path=Path("report.json"))
result = exporter.export(data, options)
print(f"Exported to: {result}")
```

### Export to Multiple Formats

```python
from export import create_exporter, ExportFormat, ExportOptions

data = {"title": "My Report", "content": "..."}

for format_type in [ExportFormat.JSON, ExportFormat.XML, ExportFormat.HTML]:
    exporter = create_exporter(format_type)
    options = ExportOptions(
        output_path=f"report.{exporter.file_extension}"
    )
    exporter.export(data, options)
```

### Batch Export

```python
from export import JSONExporter, ExportOptions
from pathlib import Path

exporter = JSONExporter()

# Multiple reports
data_items = [
    {"name": "report_1", "data": "..."},
    {"name": "report_2", "data": "..."},
    {"name": "report_3", "data": "..."}
]

options_template = ExportOptions(output_path=Path("dummy.json"))
results = exporter.batch_export(data_items, Path("./output"), options_template)
```

### Progress Tracking

```python
from export import JSONExporter

def progress_callback(progress):
    print(f"Progress: {progress.progress_percentage:.1f}% - {progress.current_item}")

exporter = JSONExporter()
exporter.add_progress_callback(progress_callback)

# Export will now report progress
exporter.batch_export(data_items, output_dir, options_template)
```

## Export Formats

### PDF Export

```python
from export import PDFExporter, ExportOptions, PDFEngine

# Using ReportLab (recommended)
exporter = PDFExporter(engine=PDFEngine.REPORTLAB)

options = ExportOptions(
    output_path="report.pdf",
    include_charts=True,
    include_metadata=True,
    watermark="CONFIDENTIAL"  # Optional watermark
)

exporter.export(data, options)

# PDF/A compliance
exporter.convert_to_pdfa("report.pdf", "report_pdfa.pdf")

# Digital signatures
exporter.add_digital_signature(
    "report.pdf",
    "certificate.pem",
    "private_key.pem"
)
```

### Word Export

```python
from export import WordExporter, ExportOptions

exporter = WordExporter()

options = ExportOptions(
    output_path="report.docx",
    template_name="custom_template",  # Optional template
    include_charts=True,
    include_images=True
)

exporter.export(data, options)

# Merge multiple documents
exporter.merge_documents(
    [Path("doc1.docx"), Path("doc2.docx")],
    Path("merged.docx")
)
```

### HTML Export

```python
from export import HTMLExporter, ExportOptions

exporter = HTMLExporter()

options = ExportOptions(
    output_path="report.html",
    include_charts=True,  # Interactive Plotly charts
    include_metadata=True
)

exporter.export(data, options)

# Create Plotly chart
chart = exporter.create_plotly_chart(
    chart_type="line",
    x_data=[1, 2, 3, 4],
    y_data=[10, 20, 15, 25],
    title="Power Output"
)
```

### Excel Export

```python
from export import ExcelExporter, ExportOptions, ExcelEngine

exporter = ExcelExporter(engine=ExcelEngine.OPENPYXL)

options = ExportOptions(
    output_path="report.xlsx",
    include_charts=True,
    include_metadata=True
)

exporter.export(data, options)

# Add data validation
exporter.add_data_validation(
    "report.xlsx",
    "Sheet1",
    "A1:A10",
    "list",
    '"Option1,Option2,Option3"'
)
```

### JSON Export

```python
from export import JSONExporter, ExportOptions

exporter = JSONExporter()

# Basic export
options = ExportOptions(
    output_path="report.json",
    custom_params={
        "indent": 2,
        "sort_keys": True,
        "ensure_ascii": False
    }
)

exporter.export(data, options)

# Schema generation
schema = exporter.generate_schema(data)

# Schema validation
exporter.set_schema(schema)
exporter.export(data, options)  # Validates against schema

# Minify JSON
exporter.minify("report.json", "report.min.json")
```

### XML Export

```python
from export import XMLExporter, ExportOptions

exporter = XMLExporter()

options = ExportOptions(
    output_path="report.xml",
    custom_params={
        "root_element": "pv_test_report"
    }
)

exporter.export(data, options)

# XSD validation
exporter.load_xsd_schema("schema.xsd")
exporter.export(data, options)  # Validates against XSD

# XML to dictionary
data_dict = exporter.xml_to_dict("report.xml")

# XSLT transformation
exporter.transform_with_xslt(
    "report.xml",
    "transform.xslt",
    "output.html"
)
```

## Template Customization

### Using Templates

```python
from export import TemplateManager, WordExporter, ExportOptions
from pathlib import Path

# Setup template manager
template_manager = TemplateManager(Path("./templates"))

# List available templates
templates = template_manager.list_templates(ExportFormat.WORD)

# Use template
exporter = WordExporter(template_manager)
options = ExportOptions(
    output_path="report.docx",
    template_name="custom_template"
)

exporter.export(data, options)
```

### Template Structure

Templates should be organized by format:

```
templates/
├── pdf/
│   ├── default.template
│   └── custom.template
├── docx/
│   ├── default.template
│   └── branded.template
└── html/
    ├── default.html
    └── modern.html
```

## Data Structure

### Expected Data Format

```python
data = {
    # Required
    "title": "Report Title",

    # Optional sections
    "summary": "Executive summary text",

    "configuration": {
        "param1": "value1",
        "param2": "value2"
    },

    "test_results": [
        {
            "name": "Test Name",
            "status": "PASS",  # or "FAIL"
            "value": 42.5,
            "expected": 42.0,
            "unit": "V",
            "notes": "Optional notes"
        }
    ],

    "charts": [
        {
            "title": "Chart Title",
            "description": "Chart description",
            "image_data": "base64_encoded_image",
            "plotly_data": {...}  # For HTML export
        }
    ],

    "analysis": "Analysis text",

    "recommendations": [
        "Recommendation 1",
        "Recommendation 2"
    ],

    "raw_data": [
        {"col1": "val1", "col2": "val2"}
    ],

    "appendix": {
        "section1": "content1"
    }
}
```

## API Response Format

For API integrations:

```python
from export import create_api_response

response = create_api_response(
    data={"report_id": 123, "status": "generated"},
    status="success",
    message="Report generated successfully"
)

# Returns:
# {
#     "status": "success",
#     "timestamp": "2025-01-15T10:30:00",
#     "message": "Report generated successfully",
#     "data": {...}
# }
```

## Quality Validation

All exporters include output validation:

```python
exporter = JSONExporter()
result = exporter.export(data, options)

# Automatic validation
if exporter.validate_output(result):
    print("Export successful and valid!")
else:
    print("Export validation failed!")
```

## Error Handling

```python
from export import JSONExporter, ExportOptions

try:
    exporter = JSONExporter()
    options = ExportOptions(output_path="report.json")
    result = exporter.export(data, options)
except ValueError as e:
    print(f"Validation error: {e}")
except IOError as e:
    print(f"File system error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Testing

Run the test suite:

```bash
# Run all tests
python -m unittest discover src/export/tests

# Run specific test file
python -m unittest src/export/tests/test_base_exporter.py

# Run with coverage
pip install coverage
coverage run -m unittest discover src/export/tests
coverage report
coverage html
```

## Examples

See `example_usage.py` for comprehensive examples:

```bash
cd src/export
python example_usage.py
```

This will generate sample reports in all formats with various features demonstrated.

## Performance Considerations

- **Batch Export**: Use `batch_export()` for multiple reports - it's more efficient than individual exports
- **Progress Tracking**: Add callbacks only when needed; they add slight overhead
- **Large Files**: For very large datasets, consider streaming or chunked processing
- **Charts**: Image generation can be slow; disable with `include_charts=False` if not needed

## Best Practices

1. **Always validate output** - Use `validate_output()` after export
2. **Use templates** - Create reusable templates for consistent branding
3. **Handle errors gracefully** - Wrap exports in try-except blocks
4. **Track progress** - Use callbacks for long-running batch operations
5. **Clean up** - Delete temporary files after processing
6. **Version control** - Include export format version in metadata

## Architecture

```
export/
├── base_exporter.py      # Abstract base class, common utilities
├── pdf_exporter.py       # PDF generation (ReportLab/WeasyPrint)
├── word_exporter.py      # Word documents (python-docx)
├── html_exporter.py      # HTML reports (Jinja2, Plotly)
├── excel_exporter.py     # Excel workbooks (openpyxl/xlsxwriter)
├── json_xml_exporter.py  # JSON/XML with schema validation
├── templates/            # Export templates by format
├── tests/                # Comprehensive test suite
└── example_usage.py      # Usage examples
```

## Contributing

When adding new exporters:

1. Inherit from `BaseExporter`
2. Implement required abstract methods
3. Register with `@ExportRegistry.register()`
4. Add comprehensive tests
5. Update documentation

## License

See LICENSE file in project root.

## Version

1.0.0

## Support

For issues, questions, or contributions, please refer to the main project repository.
