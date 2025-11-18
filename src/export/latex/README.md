# LaTeX Report Export Engine

Professional LaTeX report generation system for IEC/ISO compliant PV test reports.

## Features

- **Template Engine**: Jinja2-based templating with LaTeX-specific escaping
- **Professional Templates**: IEC 61215 compliant report structure
- **PDF Compilation**: Support for pdflatex, xelatex, and lualatex
- **Chart Generation**: Automatic chart/graph generation from test data
- **Custom Branding**: Logo, colors, and watermark support
- **Draft Watermarks**: Automatic watermarking for draft reports
- **Error Handling**: Comprehensive error detection and reporting

## Quick Start

```python
from src.export.latex.report_builder import ReportBuilder
from src.models.test_data import TestReport

# Create report builder
builder = ReportBuilder(
    output_dir="output/reports",
    latex_engine=LaTeXEngine.PDFLATEX
)

# Load your test data
test_report = TestReport(...)  # Your test data

# Generate PDF
pdf_path = builder.generate_report(
    test_report,
    output_filename="my_report.pdf"
)

print(f"Report generated: {pdf_path}")
```

## Components

### 1. Template Engine (`template_engine.py`)

Jinja2-based engine with LaTeX-specific features:

- **Variable substitution**: `\VAR{variable_name}`
- **Blocks**: `\BLOCK{if condition}...\BLOCK{endif}`
- **Loops**: `\BLOCK{for item in items}...\BLOCK{endfor}`
- **Comments**: `\#{comment}`
- **Custom filters**: `latex_escape`, `format_number`, `pass_fail`, etc.

Example usage:

```python
from src.export.latex.template_engine import LaTeXTemplateEngine

engine = LaTeXTemplateEngine("templates/")

context = {
    "title": "Test Report",
    "value": 123.456
}

latex = engine.render_template("report.tex", context)
```

### 2. Report Template (`templates/iec_61215_report.tex`)

Professional template with:

- Title page with lab logo and accreditation marks
- Table of contents
- Lists of figures and tables
- Test sequence sections (MST-01 through MST-19)
- Results tables with pass/fail indicators
- Signature blocks for reviewer/approver
- ISO 17025 compliance footer
- Draft watermark support

### 3. PDF Compiler (`pdf_compiler.py`)

Handles LaTeX compilation:

```python
from src.export.latex.pdf_compiler import PDFCompiler, LaTeXEngine

compiler = PDFCompiler(engine=LaTeXEngine.PDFLATEX)

# Compile .tex file to PDF
pdf_data = compiler.compile("report.tex", passes=2)

# Or compile from string
pdf_data = compiler.compile_string(latex_content)
```

Features:
- Multiple compilation passes for references/TOC
- Error log parsing
- Automatic cleanup of intermediate files
- Support for multiple engines

### 4. Report Builder (`report_builder.py`)

Orchestrates the complete pipeline:

```python
from src.export.latex.report_builder import ReportBuilder

builder = ReportBuilder(output_dir="output/")

# Generate complete report
pdf_path = builder.generate_report(test_report)

# Validate report data
issues = builder.validate_report_data(test_report)

# Get statistics
stats = builder.generate_summary_statistics(test_report)

# Export LaTeX source (for debugging)
tex_path = builder.export_latex_source(test_report)
```

## Requirements

### Python Packages

```bash
pip install -r requirements.txt
```

Required packages:
- Jinja2 >= 3.1.2
- Pillow >= 10.0.0
- matplotlib >= 3.7.0
- seaborn >= 0.12.0
- PyPDF2 >= 3.0.0
- pydantic >= 2.0.0
- reportlab >= 4.0.0

### LaTeX Distribution

Install a LaTeX distribution:

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

### Required LaTeX Packages

The template uses these packages (usually included in full distributions):
- graphicx, xcolor, fancyhdr
- booktabs, longtable, array, multirow
- siunitx (for units)
- hyperref (for links)
- tikz (for graphics)

## Customization

### Custom Branding

```python
from src.models.test_data import BrandingConfig

branding = BrandingConfig(
    primary_color="#0066cc",
    secondary_color="#ff6600",
    watermark_text="CONFIDENTIAL",
    watermark_opacity=0.15,
    company_tagline="Excellence in Testing"
)

builder = ReportBuilder(branding=branding)
```

### Custom Templates

1. Create a new template in `src/export/latex/templates/`
2. Use Jinja2 syntax with LaTeX-specific delimiters
3. Reference it when generating:

```python
pdf_path = builder.generate_report(
    test_report,
    template_name="my_custom_template.tex"
)
```

### Custom Filters

Add custom formatting filters:

```python
engine = LaTeXTemplateEngine("templates/")

def my_custom_filter(value):
    return f"\\textbf{{{value}}}"

engine.add_filter("bold", my_custom_filter)
```

## Examples

See `examples/generate_report_example.py` for a complete working example.

## Error Handling

The system provides comprehensive error handling:

```python
try:
    pdf_path = builder.generate_report(test_report)
except TemplateError as e:
    print(f"Template error: {e}")
except CompilationError as e:
    print(f"LaTeX compilation failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Debugging

If PDF generation fails:

1. **Export LaTeX source:**
   ```python
   tex_path = builder.export_latex_source(test_report)
   ```

2. **Compile manually:**
   ```bash
   pdflatex -interaction=nonstopmode report.tex
   ```

3. **Check log file:**
   ```bash
   less report.log
   ```

4. **Enable debug logging:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

## Performance

- Template rendering: ~100ms
- Chart generation: ~500ms (5 charts)
- LaTeX compilation: ~2-5 seconds (2 passes)
- Total time: ~5-10 seconds for typical report

## Production Deployment

For production use:

1. **Cache compiled templates:**
   ```python
   engine = LaTeXTemplateEngine(
       template_dir,
       enable_cache=True
   )
   ```

2. **Use async processing** for large batches

3. **Monitor compilation errors** and alert on failures

4. **Store PDFs** in secure storage with access controls

5. **Version control** report templates

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
- GitHub Issues: [pv-test-report-automation](https://github.com/ganeshgowri-ASA/pv-test-report-automation)
- Email: support@example.com

## Credits

Developed for world-class PV test lab report automation, compliant with:
- IEC 61215 (PV Module Design Qualification)
- IEC 61730 (PV Module Safety Qualification)
- ISO/IEC 17025 (Testing Laboratory Competence)
- NABL/ILAC Accreditation Requirements
