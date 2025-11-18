# PV Test Report Automation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

World-class photovoltaic (PV) test lab report automation system with Claude AI integration for intelligent analysis, compliance checking, and automated report generation.

## 🌟 Features

### Comprehensive Standards Coverage
- **IEC Standards**: 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759
- **ISO Standards**: 17025, 9001
- **Accreditation**: NABL, ILAC, BIS compliance

### Claude AI Integration
- ✅ **Compliance Checking**: Automated validation against IEC/ISO requirements
- ✅ **Report Summarization**: Auto-generate executive summaries in multiple languages
- ✅ **Intelligent Assistant**: Answer questions about test procedures and standards
- ✅ **Key Finding Extraction**: Automatically identify critical failures and deviations
- ✅ **Test Planning**: AI-suggested test sequences based on module type

### Core Capabilities
- **Full Traceability**: Complete audit trail for all operations
- **Reviewer Workflows**: Multi-level review and approval process
- **Multi-format Export**: PDF, DOCX, XLSX, HTML, JSON
- **Cost Tracking**: Token usage and cost monitoring for LLM operations
- **Secure API Management**: Encrypted API keys and secure configuration

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- Anthropic Claude API key ([Get one here](https://console.anthropic.com/))

### Installation

1. Clone the repository:
```bash
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
# or for development
pip install -e ".[dev]"
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your Claude API key
```

4. Set up logging directories:
```bash
mkdir -p logs uploads
```

### Basic Usage

#### 1. Compliance Checking

```python
from src.llm.compliance_checker import ComplianceChecker
from src.models.test_report import TestReport

# Load your test report
report = TestReport(...)

# Check compliance
checker = ComplianceChecker()
compliance = checker.check_compliance(report)

print(f"Compliance Score: {compliance.compliance_score}%")
print(f"Status: {compliance.overall_status}")
print(f"Issues: {compliance.critical_failures}")
```

#### 2. Report Summarization

```python
from src.llm.report_summarizer import ReportSummarizer, SummaryType

summarizer = ReportSummarizer()

# Generate executive summary
summary = summarizer.generate_summary(
    report=report,
    summary_type=SummaryType.EXECUTIVE,
    language="en"
)

print(summary)
```

#### 3. Intelligent Assistant

```python
from src.llm.intelligent_assistant import IntelligentAssistant

assistant = IntelligentAssistant()

# Ask questions
answer = assistant.ask("What are the requirements for thermal cycling test in IEC 61215?")
print(answer)

# Get test sequence
sequence = assistant.suggest_test_sequence(
    module_type=ModuleType.CRYSTALLINE_SILICON
)
```

## 📖 Documentation

- **[LLM Integration Guide](docs/LLM_INTEGRATION.md)**: Comprehensive guide to Claude AI integration
- **[API Reference](docs/API_REFERENCE.md)**: Complete API documentation
- **[Configuration Guide](docs/CONFIGURATION.md)**: Environment and settings configuration *(coming soon)*
- **[Testing Guide](docs/TESTING.md)**: Testing strategies and examples *(coming soon)*

## 🏗️ Architecture

```
pv-test-report-automation/
├── src/
│   ├── config/           # Configuration management
│   ├── models/           # Data models (Pydantic)
│   ├── llm/              # Claude AI integration
│   │   ├── claude_client.py        # Core API client
│   │   ├── compliance_checker.py   # Compliance validation
│   │   ├── report_summarizer.py    # Report summarization
│   │   └── intelligent_assistant.py # AI assistant
│   ├── services/         # Business logic
│   ├── utils/            # Utilities and helpers
│   └── logging/          # Logging infrastructure
├── tests/                # Test suite
├── docs/                 # Documentation
└── config/               # Configuration files
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file:

```bash
# Claude API
CLAUDE_API_KEY=your-api-key-here
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=4096

# Application
DEBUG=false
LOG_LEVEL=INFO

# Cost Management
ENABLE_COST_TRACKING=true
COST_ALERT_THRESHOLD=100.0

# Audit Trail
ENABLE_AUDIT_TRAIL=true
AUDIT_LOG_LLM_PROMPTS=true
```

See `.env.example` for all available options.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests
pytest -m llm          # LLM tests (requires API key)
```

## 📊 Token Usage & Costs

Track LLM usage and costs:

```python
from src.llm.claude_client import ClaudeClient

client = ClaudeClient()

# After operations
summary = client.get_usage_summary()
print(f"Total Cost: ${summary['total_cost_usd']}")
print(f"Total Tokens: {summary['total_tokens']}")
```

**Pricing** (Claude 3.5 Sonnet):
- Input: $3 / million tokens
- Output: $15 / million tokens

## 🔒 Security

- **API Key Management**: Secure storage with encryption support
- **Audit Trail**: Complete logging of all LLM interactions
- **Data Privacy**: Configurable prompt/response logging
- **Access Control**: Role-based access for sensitive operations

## 🌍 Multi-language Support

Generate reports in multiple languages:

```python
summaries = await summarizer.generate_multi_language_summaries(
    report=report,
    languages=["en", "es", "fr", "de", "zh", "ja", "hi"]
)
```

Supported languages: English, Spanish, French, German, Chinese, Japanese, Hindi

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines *(coming soon)*.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 Standards Compliance

This system implements testing and reporting according to:

- **IEC 61215**: Terrestrial photovoltaic modules - Design qualification and type approval
- **IEC 61730**: Photovoltaic module safety qualification
- **IEC 61853**: Photovoltaic module performance testing and energy rating
- **ISO 17025**: General requirements for the competence of testing and calibration laboratories
- **ISO 9001**: Quality management systems

## 🎯 Roadmap

- [x] Claude API integration
- [x] Compliance checking
- [x] Report summarization
- [x] Intelligent assistant
- [ ] Database integration (PostgreSQL)
- [ ] Web UI dashboard
- [ ] Real-time streaming analysis
- [ ] PDF report generation
- [ ] Multi-model LLM support
- [ ] Advanced analytics and trends

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Anthropic Claude](https://www.anthropic.com/claude)
- Testing standards from [IEC](https://www.iec.ch/) and [ISO](https://www.iso.org/)
- Python ecosystem and open-source community

## 📧 Support

For questions or support:
- Open an issue on GitHub
- Contact: [Project maintainers]

## 🔗 Links

- [Claude API Documentation](https://docs.anthropic.com/)
- [IEC Webstore](https://webstore.iec.ch/)
- [ISO Standards](https://www.iso.org/standards.html)

---

**Made with ❤️ for the solar energy industry**
