# Configuration Directory

This directory contains all configuration files for the PV Test Report Automation system.

## Directory Structure

```
config/
├── standards/          # Testing standard definitions (IEC, ISO, NABL, BIS)
├── templates/          # Report templates
├── llm_config.yaml     # LLM API configuration
└── README.md          # This file
```

## Standards Directory

The `standards/` directory contains YAML files defining various testing standards:

### IEC Standards
- **iec_61215.yaml** - PV module design qualification and type approval
- **iec_61730.yaml** - PV module safety qualification
- **iec_61853.yaml** - PV module performance testing and energy rating
- **iec_62716.yaml** - Ammonia corrosion testing
- **iec_61701.yaml** - Salt mist corrosion testing
- **iec_62804.yaml** - Potential-induced degradation (PID) testing
- **iec_60904.yaml** - Photovoltaic devices - Measurement procedures
- **iec_62759.yaml** - Transportation testing

### Quality and Accreditation Standards
- **iso_17025.yaml** - Laboratory competence requirements
- **nabl_ilac_bis.yaml** - Indian accreditation and standards framework

## Templates Directory

The `templates/` directory contains report templates:

- **test_report_template.yaml** - Standard PV module test report template

## LLM Configuration

The `llm_config.yaml` file configures LLM providers and API settings:

- API key management (via environment variables)
- Model selection and parameters
- Task routing
- Cost management
- Rate limiting and caching

### Setting Up LLM Configuration

1. Copy `.env.example` to `.env` in the project root
2. Add your API keys to `.env`
3. Configure provider preferences in `llm_config.yaml`

Example `.env` file:
```bash
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

## Usage

### Loading Standards

```python
from src.utils.config_loader import ConfigLoader

loader = ConfigLoader()

# Load a specific standard
iec_61215 = loader.load_standard('iec_61215')
print(f"Standard: {iec_61215.code}")
print(f"Version: {iec_61215.version}")

# Load all standards
all_standards = loader.load_all_standards()
for code, config in all_standards.items():
    print(f"{code}: {config.full_name}")

# Search by standard code
standard = loader.get_standard_by_code("IEC 61215")
```

### Loading LLM Configuration

```python
from src.utils.config_loader import ConfigLoader

loader = ConfigLoader()

# Load LLM configuration
llm_config = loader.load_llm_config()

# Get specific provider
openai_config = loader.get_llm_provider_config('openai')
print(f"Provider: {openai_config.name}")
print(f"Enabled: {openai_config.enabled}")
print(f"Default Model: {openai_config.models['default']}")

# Get primary provider
primary = loader.get_primary_llm_provider()
print(f"Primary Provider: {primary.name}")
```

### Loading Templates

```python
from src.utils.config_loader import ConfigLoader

loader = ConfigLoader()

# Load a template
template = loader.load_template('test_report_template')

# List available templates
templates = loader.list_available_templates()
print(f"Available templates: {templates}")
```

### Configuration Summary

```python
from src.utils.config_loader import ConfigLoader

loader = ConfigLoader()

# Get comprehensive summary
summary = loader.get_config_summary()
print(f"Base Directory: {summary['base_directory']}")
print(f"Available Standards: {summary['available_standards']}")
print(f"Available Templates: {summary['available_templates']}")
print(f"Enabled LLM Providers: {summary['enabled_llm_providers']}")
```

## Security Best Practices

### API Keys
- **NEVER** commit API keys to version control
- Always use environment variables for sensitive data
- Use `.env` file for local development (already in `.gitignore`)
- Rotate API keys regularly
- Set up budget limits and alerts

### Configuration Files
- Review configurations before committing
- Use version control for configuration changes
- Document any deviations from standard configurations
- Test configuration changes in development first

## Adding New Standards

To add a new testing standard:

1. Create a new YAML file in `standards/` directory
2. Follow the existing structure:
   ```yaml
   standard:
     code: "STANDARD CODE"
     full_name: "Full Standard Name"
     version: "Version number"
     applicable_to:
       - "Application 1"
       - "Application 2"
     scope: "Scope description"

   # Add standard-specific sections
   test_sequence:
     # Define test procedures

   acceptance_criteria:
     # Define acceptance criteria
   ```

3. Validate the file:
   ```python
   from src.utils.config_loader import ConfigLoader
   loader = ConfigLoader()
   config = loader.load_standard('your_standard_name')
   ```

## Adding New Templates

To add a new report template:

1. Create a file in `templates/` directory (YAML, JSON, or TXT)
2. Define the template structure
3. Load and test:
   ```python
   from src.utils.config_loader import ConfigLoader
   loader = ConfigLoader()
   template = loader.load_template('your_template_name')
   ```

## Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| OPENAI_API_KEY | OpenAI API key | No* |
| OPENAI_ORG_ID | OpenAI organization ID | No |
| ANTHROPIC_API_KEY | Anthropic API key | No* |
| GOOGLE_AI_API_KEY | Google AI API key | No* |
| AZURE_OPENAI_API_KEY | Azure OpenAI API key | No* |
| AZURE_OPENAI_ENDPOINT | Azure OpenAI endpoint | No |
| AZURE_OPENAI_DEPLOYMENT | Azure deployment name | No |

*At least one LLM provider API key is required for full functionality

## Troubleshooting

### Issue: Standard not found
**Solution**: Check that the YAML file exists in `config/standards/` and the filename matches the code you're using.

### Issue: API key not loaded
**Solution**:
1. Verify `.env` file exists and contains the key
2. Check environment variable name matches `llm_config.yaml`
3. Restart the application after updating `.env`

### Issue: Template loading fails
**Solution**:
1. Check template file extension (.yaml, .json, .txt)
2. Verify template file is valid YAML/JSON
3. Check file permissions

### Issue: Validation errors
**Solution**:
1. Review error message for specific missing fields
2. Compare with example configurations
3. Check YAML syntax (indentation, colons, etc.)

## Testing

Run configuration tests:
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/test_config_loader.py -v

# Run with coverage
python -m pytest tests/test_config_loader.py --cov=src/utils --cov-report=html
```

## Maintenance

### Regular Tasks
- Review and update standard versions quarterly
- Rotate API keys as per security policy
- Monitor LLM usage and costs
- Update templates based on feedback
- Archive obsolete configurations

### Version Control
- Commit configuration changes with clear messages
- Tag major configuration updates
- Document breaking changes
- Maintain changelog for configurations

## Support

For configuration-related issues:
1. Check this README
2. Review example configurations
3. Check application logs
4. Consult standard documentation
5. Contact development team

## References

- [IEC Standards](https://www.iec.ch)
- [ISO Standards](https://www.iso.org)
- [NABL](https://www.nabl-india.org)
- [BIS](https://www.bis.gov.in)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Anthropic API Documentation](https://docs.anthropic.com)
