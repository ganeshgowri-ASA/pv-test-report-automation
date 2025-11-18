# PV Test Report Automation

World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## Overview

This system provides comprehensive automation for photovoltaic module testing and report generation, designed for accredited test laboratories requiring compliance with international standards.

### Key Features

- **LaTeX Report Export Engine**: Professional PDF generation with IEC/ISO compliance
- **Multiple Standards Support**: IEC 61215, 61730, 61853, ISO 17025, NABL, ILAC
- **Data Models**: Pydantic-based validation for test data
- **Chart Generation**: Automatic visualization of test results
- **Custom Branding**: Laboratory logo, colors, and watermark support
- **Draft Management**: Automatic watermarking for draft reports
- **Error Handling**: Comprehensive validation and error reporting

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
# or
pip install -e .
```

3. Install LaTeX distribution (required for PDF generation):

**Ubuntu/Debian:**
```bash
sudo apt-get install texlive-full
```

**macOS:**
```bash
brew install --cask mactex
```

**Windows:**
Download and install [MiKTeX](https://miktex.org/)

### Generate Your First Report

```bash
python examples/generate_report_example.py
```

This will:
1. Create sample test data
2. Generate charts and graphs
3. Compile a professional PDF report
4. Save to `output/reports/sample_report.pdf`

## Project Structure

```
pv-test-report-automation/
├── src/
│   ├── models/
│   │   └── test_data.py              # Data models for test results
│   ├── export/
│   │   └── latex/
│   │       ├── template_engine.py    # Jinja2 LaTeX template engine
│   │       ├── pdf_compiler.py       # PDF compilation engine
│   │       ├── report_builder.py     # Report generation pipeline
│   │       └── templates/
│   │           └── iec_61215_report.tex  # IEC 61215 report template
│   └── utils/                        # Utility functions
├── data/
│   └── sample/
│       └── sample_test_data.py       # Sample test data generator
├── examples/
│   └── generate_report_example.py    # Example usage script
├── output/                           # Generated reports (created automatically)
├── tests/                           # Unit tests (to be added)
├── requirements.txt                  # Python dependencies
├── pyproject.toml                   # Project configuration
└── README.md                        # This file
```

## LaTeX Report Export Engine

### Components

#### 1. Template Engine (`template_engine.py`)

Jinja2-based engine with LaTeX-specific features:

```python
from src.export.latex.template_engine import LaTeXTemplateEngine

engine = LaTeXTemplateEngine("templates/")
latex = engine.render_template("report.tex", context)
```

Features:
- LaTeX-safe variable substitution
- Loop and conditional logic
- Custom filters (format_number, pass_fail, etc.)
- Automatic escaping of special characters

#### 2. PDF Compiler (`pdf_compiler.py`)

Handles LaTeX to PDF compilation:

```python
from src.export.latex.pdf_compiler import PDFCompiler, LaTeXEngine

compiler = PDFCompiler(engine=LaTeXEngine.PDFLATEX)
pdf_data = compiler.compile("report.tex", passes=2)
```

Features:
- Multiple LaTeX engines (pdflatex, xelatex, lualatex)
- Multi-pass compilation for references
- Error log parsing
- Automatic cleanup

#### 3. Report Builder (`report_builder.py`)

Orchestrates the complete pipeline:

```python
from src.export.latex.report_builder import ReportBuilder

builder = ReportBuilder(output_dir="output/")
pdf_path = builder.generate_report(test_report)
```

Features:
- Chart/graph generation
- Template population
- PDF compilation
- Watermark support
- Data validation

### Usage Example

```python
from src.models.test_data import (
    TestReport, ReportMetadata, LabInformation,
    ModuleUnderTest, TestSequence, Measurement
)
from src.export.latex.report_builder import ReportBuilder

# Create test data
metadata = ReportMetadata(
    report_number="TR-2025-001",
    report_date=datetime.now(),
    prepared_by="Dr. John Doe"
)

lab_info = LabInformation(
    lab_name="National Solar Testing Lab",
    accreditation_number="TC-1234",
    accreditation_body=AccreditationBody.NABL
)

module_info = ModuleUnderTest(
    manufacturer="SolarCorp",
    model="SC-500M",
    serial_number="SC2025-001",
    rated_power=500.0,
    rated_voltage=40.0,
    rated_current=12.5
)

# Create test report
report = TestReport(
    metadata=metadata,
    lab_info=lab_info,
    module_info=module_info,
    test_sequences=[...]  # Add test sequences
)

# Generate PDF
builder = ReportBuilder()
pdf_path = builder.generate_report(report)
print(f"Report generated: {pdf_path}")
```

## Standards Compliance

### IEC 61215-2:2021

Module Sequence Testing (MST):
- MST-01: Visual Inspection
- MST-02: Maximum Power Determination
- MST-03: Insulation Test
- MST-04: Temperature Coefficients
- MST-05: Hot-Spot Endurance Test
- MST-06 through MST-19: Additional test sequences

### ISO/IEC 17025

The report template includes:
- Laboratory accreditation information
- Measurement uncertainty reporting
- Traceability statements
- Signature blocks for review and approval
- ISO 17025 compliance footer

## Data Models

All test data is validated using Pydantic models:

```python
from src.models.test_data import TestSequence, Measurement, TestResult

sequence = TestSequence(
    sequence_id="MST-02",
    sequence_name="Maximum Power Determination",
    test_date=datetime.now(),
    operator="John Doe",
    measurements=[
        Measurement(
            parameter="Maximum Power",
            value=502.3,
            unit="W",
            uncertainty=2.5,
            specification="≥ 495 W",
            result=TestResult.PASS
        )
    ],
    overall_result=TestResult.PASS
)
```

## Custom Branding

Customize reports with your laboratory's branding:

```python
from src.models.test_data import BrandingConfig

branding = BrandingConfig(
    primary_color="#0066cc",
    secondary_color="#ff6600",
    header_logo_path="path/to/logo.png",
    watermark_text="CONFIDENTIAL",
    watermark_opacity=0.15
)

builder = ReportBuilder(branding=branding)
```

## Development

### Running Tests

```bash
pytest tests/ -v --cov=src
```

### Code Quality

```bash
# Format code
black src/ examples/

# Check style
flake8 src/ examples/

# Type checking
mypy src/
```

## Roadmap

- [ ] Additional report templates (IEC 61730, 61853)
- [ ] HTML export format
- [ ] JSON/XML data export
- [ ] LLM integration for report analysis
- [ ] Reviewer workflow system
- [ ] Web interface
- [ ] Database integration
- [ ] Batch report generation
- [ ] API endpoints

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Support

For issues or questions:
- GitHub Issues: [pv-test-report-automation](https://github.com/ganeshgowri-ASA/pv-test-report-automation/issues)

## Acknowledgments

Developed for world-class PV test laboratories requiring compliance with international testing and accreditation standards.

## Documentation

- [LaTeX Export Engine Documentation](src/export/latex/README.md)
- [Data Models Documentation](src/models/test_data.py)
- [Example Scripts](examples/)

---

**Note**: This is Phase 8 (Session 39) focusing on the LaTeX Report Export Engine. Additional features will be added in future phases.
