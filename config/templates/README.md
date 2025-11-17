# Report Templates

This directory contains templates for generating PV test reports.

## Available Templates

### test_report_template.yaml
Standard template for PV module test reports following IEC and ISO standards.

## Template Usage

Templates can be loaded using the ConfigLoader:

```python
from src.utils.config_loader import ConfigLoader

loader = ConfigLoader()
template = loader.load_template('test_report_template')
```

## Creating New Templates

Templates can be in YAML, JSON, or plain text format. Follow these guidelines:

1. Use descriptive names
2. Include metadata section
3. Define clear structure
4. Specify required vs optional fields
5. Include validation rules where applicable
