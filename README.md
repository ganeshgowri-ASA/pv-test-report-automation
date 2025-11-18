# PV Test Report Automation

> Automated Photovoltaic (PV) module test report generation and analysis system with Google Gemini LLM integration

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🌟 Features

### Core Capabilities

- **✅ Multi-Standard Support**: IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS
- **🤖 LLM Integration**: Google Gemini Pro for advanced AI analysis
- **👁️ Vision Analysis**: Multi-modal image analysis (EL, thermal, visual)
- **📊 Compliance Checking**: Automated verification against PV standards
- **🔮 Predictive Analysis**: Failure prediction and lifespan estimation
- **⚡ Batch Processing**: Concurrent processing of multiple images
- **📝 Multi-Format Export**: PDF, Excel, JSON report generation (planned)
- **🔒 Full Traceability**: Complete audit trail and version control

### Google Gemini Integration (Phase 7)

- **Visual Defect Analysis**: Analyze EL/thermal images using Gemini Vision
- **Multi-modal Reports**: Combine text and image understanding
- **Predictive Maintenance**: Identify failure patterns before they occur
- **Test Optimization**: AI-powered suggestions for test parameter improvements
- **Compliance Verification**: Automated checking against international standards

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Documentation](#documentation)
- [Testing](#testing)
- [Development](#development)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Installation

### Prerequisites

- Python 3.9 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Install from Source

```bash
# Clone the repository
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/base.txt

# Install in development mode (optional)
pip install -e .
```

### Install for Development

```bash
# Install with development dependencies
pip install -r requirements/dev.txt

# Install pre-commit hooks (optional)
pre-commit install
```

## ⚡ Quick Start

### 1. Set Up Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your Gemini API key
echo "GEMINI_API_KEY=your_api_key_here" >> .env
```

### 2. Basic Usage

```python
import asyncio
from pv_automation.services.llm import GeminiProvider
from pv_automation.models.llm_models import GeminiRequest

async def main():
    # Initialize Gemini provider
    provider = GeminiProvider()

    # Generate analysis
    request = GeminiRequest(
        prompt="Explain the importance of EL imaging in PV testing"
    )

    response = await provider.generate_text(request)
    print(response.content)

asyncio.run(main())
```

### 3. Analyze an Image

```python
from pv_automation.models.llm_models import VisionAnalysisRequest

async def analyze_el_image():
    provider = GeminiProvider()

    request = VisionAnalysisRequest(
        image_path="path/to/el_image.png",
        image_type="EL",
        standard="IEC 61215"
    )

    response = await provider.analyze_image(request)

    print(f"Compliance: {response.compliance_status}")
    print(f"Defects found: {len(response.defects)}")
    for defect in response.defects:
        print(f"  - {defect.defect_type}: {defect.severity}")

asyncio.run(analyze_el_image())
```

## ⚙️ Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Google Gemini API
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_VISION_MODEL=gemini-2.0-flash-exp

# LLM Settings
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048
ENABLE_SAFETY_FILTERS=true

# File Upload
MAX_IMAGE_SIZE_MB=10
ALLOWED_IMAGE_FORMATS=png,jpg,jpeg,tiff,bmp

# PV Standards
DEFAULT_STANDARD=IEC 61215
ENABLE_COMPLIANCE_CHECKING=true

# Features
ENABLE_VISION_ANALYSIS=true
ENABLE_PREDICTIVE_ANALYSIS=true
ENABLE_BATCH_PROCESSING=true
```

See `.env.example` for all available options.

## 📚 Usage Examples

### Text Generation

```python
from pv_automation.models.llm_models import GeminiRequest

request = GeminiRequest(
    prompt="Analyze this PV module test data for IEC 61215 compliance",
    temperature=0.7,
    max_tokens=2048
)

response = await provider.generate_text(request)
print(response.content)
```

### Compliance Checking

```python
from pv_automation.models.llm_models import ComplianceCheckRequest

request = ComplianceCheckRequest(
    report_data={
        "module_id": "PV-001",
        "power_output": 400,
        "efficiency": 20.5,
        # ... more test data
    },
    standard="IEC 61215"
)

response = await provider.check_compliance(request)
print(f"Status: {response.compliance_status}")
```

### Predictive Analysis

```python
from pv_automation.models.llm_models import PredictiveAnalysisRequest

request = PredictiveAnalysisRequest(
    test_data={
        "initial_power": 400,
        "current_power": 388,
        "degradation_rate": 0.61
    },
    module_age_years=5.5,
    warranty_period_years=25
)

response = await provider.predict_failures(request)
print(f"Failure Probability: {response.failure_probability:.1%}")
print(f"Estimated Lifespan: {response.estimated_lifespan_years} years")
```

### Batch Processing

```python
requests = [
    VisionAnalysisRequest(image_path=img, image_type="EL")
    for img in ["img1.png", "img2.png", "img3.png"]
]

responses = await provider.batch_analyze_images(requests)
for resp in responses:
    print(f"Defects: {len(resp.defects)}, Status: {resp.compliance_status}")
```

See `examples/gemini_basic_usage.py` for complete working examples.

## 📖 Documentation

- **[Gemini Integration Guide](docs/gemini_integration.md)**: Comprehensive guide for Gemini LLM integration
- **[API Reference](docs/api_reference.md)**: Full API documentation (coming soon)
- **[Standards Documentation](docs/standards.md)**: PV standards reference (coming soon)
- **[Architecture](docs/architecture.md)**: System architecture overview (coming soon)

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pv_automation --cov-report=html

# Run specific test file
pytest tests/unit/services/llm/test_gemini_provider.py

# Run only unit tests
pytest tests/unit/

# Skip tests requiring API key
pytest -m "not requires_api_key"

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 🛠️ Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -r requirements/dev.txt

# Install pre-commit hooks
pre-commit install

# Run code formatting
black src/ tests/

# Run linting
ruff check src/ tests/

# Run type checking
mypy src/
```

### Code Quality Tools

- **Black**: Code formatting
- **Ruff**: Fast Python linter
- **MyPy**: Static type checking
- **Pytest**: Testing framework
- **Pre-commit**: Git hooks for code quality

## 📁 Project Structure

```
pv-test-report-automation/
├── src/
│   └── pv_automation/
│       ├── config/              # Configuration management
│       │   ├── settings.py      # Application settings
│       │   └── constants.py     # PV standards and constants
│       ├── models/              # Data models
│       │   └── llm_models.py    # LLM request/response models
│       ├── services/            # Business logic
│       │   └── llm/
│       │       ├── base.py      # LLM provider interface
│       │       ├── gemini_provider.py  # Gemini implementation
│       │       └── prompts.py   # Prompt templates
│       └── utils/               # Utilities
├── tests/                       # Test suite
│   └── unit/
│       └── services/
│           └── llm/
│               └── test_gemini_provider.py
├── examples/                    # Usage examples
│   └── gemini_basic_usage.py
├── docs/                        # Documentation
│   └── gemini_integration.md
├── requirements/                # Dependencies
│   ├── base.txt
│   └── dev.txt
├── pyproject.toml              # Project metadata
├── .env.example                # Example configuration
└── README.md
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Run code quality checks (`black . && ruff check . && mypy .`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Write tests for new features
- Update documentation
- Add type hints
- Use descriptive commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Gemini**: For providing advanced AI capabilities
- **PV Testing Community**: For standards and best practices
- **Open Source Contributors**: For the amazing tools and libraries

## 📧 Contact

- **Author**: ganeshgowri-ASA
- **Repository**: [pv-test-report-automation](https://github.com/ganeshgowri-ASA/pv-test-report-automation)
- **Issues**: [GitHub Issues](https://github.com/ganeshgowri-ASA/pv-test-report-automation/issues)

---

**Note**: This project is under active development. Features and APIs may change.

## 🗺️ Roadmap

### Phase 7 ✅ (Current)
- [x] Google Gemini LLM integration
- [x] Vision-based defect analysis
- [x] Multi-modal analysis capabilities
- [x] Compliance checking
- [x] Predictive failure analysis

### Phase 8 (Planned)
- [ ] FastAPI REST API
- [ ] Web dashboard
- [ ] Multi-format report export (PDF, Excel)
- [ ] Database integration
- [ ] User authentication

### Phase 9 (Future)
- [ ] Claude AI integration
- [ ] OpenAI GPT integration
- [ ] Advanced analytics dashboard
- [ ] Real-time monitoring
- [ ] Mobile app

## ⭐ Star History

If you find this project useful, please consider giving it a star!

---

Made with ❤️ for the PV testing community
