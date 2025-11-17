# PV Test Report Automation System

World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## Overview

This system automates the generation and management of photovoltaic module test reports, ensuring compliance with international standards and providing AI-powered analysis and documentation.

## Features

### Phase 1: Configuration Management System ✅

- **Comprehensive Standards Library**: Complete YAML definitions for all major PV testing standards
  - IEC 61215 (Design Qualification)
  - IEC 61730 (Safety Qualification)
  - IEC 61853 (Performance Testing and Energy Rating)
  - IEC 62716 (Ammonia Corrosion Testing)
  - IEC 61701 (Salt Mist Corrosion Testing)
  - IEC 62804 (PID Testing)
  - IEC 60904 (Measurement Procedures)
  - IEC 62759 (Transportation Testing)
  - ISO/IEC 17025 (Laboratory Competence)
  - NABL/ILAC/BIS (Indian Standards Framework)

- **Advanced Configuration Loader**: Python-based configuration management
  - Load and validate standards
  - Environment variable support
  - LLM provider configuration
  - Template management
  - Built-in caching
  - Comprehensive error handling

- **LLM Integration Ready**: Multi-provider LLM support
  - OpenAI (GPT-4, GPT-3.5)
  - Anthropic (Claude 3)
  - Google AI (Gemini)
  - Azure OpenAI
  - Local LLM support (Ollama)

- **Report Templates**: Professional report templates
  - ISO/IEC 17025 compliant formats
  - Customizable sections
  - NABL accreditation ready

## Project Structure

```
pv-test-report-automation/
├── config/                      # Configuration files
│   ├── standards/              # Testing standard definitions
│   │   ├── iec_61215.yaml     # Design qualification
│   │   ├── iec_61730.yaml     # Safety qualification
│   │   ├── iec_61853.yaml     # Performance testing
│   │   ├── iec_62716.yaml     # Ammonia corrosion
│   │   ├── iec_61701.yaml     # Salt mist corrosion
│   │   ├── iec_62804.yaml     # PID testing
│   │   ├── iec_60904.yaml     # Measurement procedures
│   │   ├── iec_62759.yaml     # Transportation testing
│   │   ├── iso_17025.yaml     # Laboratory competence
│   │   └── nabl_ilac_bis.yaml # Indian standards
│   ├── templates/              # Report templates
│   │   ├── test_report_template.yaml
│   │   └── README.md
│   ├── llm_config.yaml         # LLM API configuration
│   └── README.md               # Configuration documentation
├── src/                        # Source code
│   ├── utils/                  # Utility modules
│   │   ├── config_loader.py   # Configuration loader
│   │   └── __init__.py
│   └── __init__.py
├── tests/                      # Test suite
│   ├── test_config_loader.py  # Configuration tests
│   └── __init__.py
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── LICENSE                     # License file
├── README.md                   # This file
└── requirements.txt            # Python dependencies
```

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your API keys
```

### Basic Usage

```python
from src.utils.config_loader import ConfigLoader

# Initialize the config loader
loader = ConfigLoader()

# Load a testing standard
iec_61215 = loader.load_standard('iec_61215')
print(f"Standard: {iec_61215.code}")
print(f"Version: {iec_61215.version}")

# Load all standards
all_standards = loader.load_all_standards()
print(f"Loaded {len(all_standards)} standards")

# Load LLM configuration
llm_config = loader.load_llm_config()
primary_provider = loader.get_primary_llm_provider()
print(f"Primary LLM: {primary_provider.name}")

# Load a report template
template = loader.load_template('test_report_template')
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test
python -m pytest tests/test_config_loader.py -v
```

## Configuration

### Standards Configuration

Each testing standard is defined in a YAML file with complete details:
- Test procedures and sequences
- Acceptance criteria
- Measurement requirements
- Equipment specifications
- Reporting requirements

See [config/README.md](config/README.md) for detailed documentation.

### LLM Configuration

Configure LLM providers in `config/llm_config.yaml`:
- API endpoints and keys (via environment variables)
- Model selection and parameters
- Task routing (which model for which task)
- Cost management and budgets
- Rate limiting and caching

### Environment Variables

Create a `.env` file from `.env.example`:

```bash
# OpenAI
OPENAI_API_KEY=sk-your-key-here

# Anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Google AI
GOOGLE_AI_API_KEY=your-google-key-here

# Azure OpenAI (optional)
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

**Important**: Never commit the `.env` file with actual API keys!

## Standards Covered

### IEC Standards

- **IEC 61215**: Terrestrial PV modules - Design qualification and type approval
  - Complete test sequence (17+ tests)
  - Acceptance criteria
  - Measurement conditions

- **IEC 61730**: PV module safety qualification
  - Safety classes (A, B, C)
  - Construction requirements
  - Safety testing procedures (MST 01-23)

- **IEC 61853**: Performance testing and energy rating
  - Irradiance/temperature characterization
  - Spectral responsivity
  - Annual energy yield calculations

- **IEC 62716**: Ammonia corrosion testing
  - Agricultural environment simulation
  - 672-hour exposure test

- **IEC 61701**: Salt mist corrosion testing
  - 4 severity levels
  - Coastal/marine environment testing

- **IEC 62804**: Potential-induced degradation (PID)
  - Crystalline silicon and thin-film
  - Delamination-type PID

- **IEC 60904**: Measurement procedures
  - IV characteristics
  - Reference devices
  - Solar simulator requirements

- **IEC 62759**: Transportation testing
  - Vibration, shock, compression, drop tests
  - Package integrity verification

### Quality Standards

- **ISO/IEC 17025**: Laboratory competence requirements
  - Management system requirements
  - Technical requirements
  - Accreditation process

- **NABL/ILAC/BIS**: Indian standards framework
  - NABL accreditation process
  - ILAC mutual recognition
  - BIS certification requirements

## Development Roadmap

### Phase 1: Configuration Management System ✅ COMPLETED
- Standards library
- Configuration loader
- LLM integration
- Report templates

### Phase 2: Data Extraction (Upcoming)
- PDF report parsing
- Data extraction from test reports
- Structured data storage
- Validation and verification

### Phase 3: Report Generation (Upcoming)
- Automated report generation
- Template-based formatting
- Multi-format export (PDF, Word, Excel)
- Digital signatures

### Phase 4: AI Analysis (Upcoming)
- LLM-powered analysis
- Compliance checking
- Trend analysis
- Anomaly detection

### Phase 5: Workflow Management (Upcoming)
- Reviewer workflows
- Approval processes
- Audit trails
- Document version control

## Testing

The system includes comprehensive unit tests:

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Security

### API Key Management
- Never commit API keys to version control
- Use environment variables for all secrets
- Rotate API keys regularly
- Set up budget alerts for LLM usage

### Data Handling
- Sanitize all inputs
- Validate configuration files
- Implement proper error handling
- Log security-relevant events

## License

See [LICENSE](LICENSE) file for details.

## Standards References

- [IEC 61215](https://www.iec.ch) - PV module design qualification
- [IEC 61730](https://www.iec.ch) - PV module safety
- [ISO/IEC 17025](https://www.iso.org) - Laboratory competence
- [NABL](https://www.nabl-india.org) - National Accreditation Board
- [BIS](https://www.bis.gov.in) - Bureau of Indian Standards

## Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Contact: [Project maintainers]

## Acknowledgments

This project implements testing standards developed by:
- International Electrotechnical Commission (IEC)
- International Organization for Standardization (ISO)
- National Accreditation Board for Testing and Calibration Laboratories (NABL)
- Bureau of Indian Standards (BIS)

## Changelog

### Version 0.1.0 (Phase 1)
- ✅ Complete configuration management system
- ✅ All major PV testing standards (IEC, ISO)
- ✅ LLM integration framework
- ✅ Report templates
- ✅ Comprehensive documentation
- ✅ Unit tests and validation

---

**Status**: Phase 1 Complete | Phase 2 In Planning
