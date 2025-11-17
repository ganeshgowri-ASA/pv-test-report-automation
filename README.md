# PV Test Report Automation System

A comprehensive automation platform for photovoltaic (PV) module testing, data analysis, and report generation in compliance with international standards (IEC 61215, IEC 61730, ISO 17025, NABL, etc.).

## Features

### Core Capabilities
- **Multi-Standard Support**: IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759
- **Automated Data Ingestion**: Parse Excel, Word, PDF, and image files
- **LLM Integration**: Claude, GPT-4, and Gemini for intelligent analysis
- **Comprehensive Testing**: Support for IV curves, EL, IR, VI, climate chamber, and more
- **Professional Reports**: LaTeX/PDF, Word, HTML, and Excel export
- **ISO 17025 Compliant**: Full traceability and audit trail
- **NABL/ILAC Ready**: Meets accreditation requirements

### Key Modules
1. **Data Ingestion**: OCR, file parsing, image processing
2. **Protocol Engines**: Standards-based test execution
3. **Test Blocks**: Specialized processors for each test type
4. **LLM Analysis**: AI-powered compliance checking and report generation
5. **Workflow Management**: Multi-level review and approval
6. **Equipment Management**: Calibration tracking and uncertainty calculation
7. **Export Engine**: Multi-format report generation
8. **Audit System**: Complete traceability and change tracking

## Technology Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy
- **Frontend**: Streamlit, Plotly, AG-Grid
- **Database**: PostgreSQL (Production), SQLite (Development)
- **LLM**: Anthropic Claude, OpenAI GPT-4, Google Gemini
- **Export**: LaTeX, ReportLab, python-docx, Weasyprint
- **Testing**: pytest, pytest-cov

## Installation

### Prerequisites
- Python 3.10 or higher
- PostgreSQL (for production)
- Tesseract OCR
- LaTeX distribution (for PDF generation)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pv-test-report-automation.git
cd pv-test-report-automation
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

5. Initialize database:
```bash
alembic upgrade head
```

6. Run the application:
```bash
streamlit run src/ui/app.py
```

## Configuration

### Environment Variables
```env
# Database
DATABASE_URL=postgresql://user:password@localhost/pvtest

# LLM API Keys
ANTHROPIC_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_gemini_api_key

# Security
SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Email (optional)
SENDGRID_API_KEY=your_sendgrid_key
```

### LLM Configuration
Edit `config/llm_config.yaml` to customize LLM providers and usage.

## Usage

### Quick Start

1. **Upload Sample Data**
   - Navigate to Dashboard
   - Click "New Sample"
   - Enter sample details
   - Upload test data files

2. **Run Tests**
   - Select test standard (e.g., IEC 61215)
   - Upload measurement files
   - System processes data automatically

3. **Generate Reports**
   - Review processed data
   - Click "Generate Report"
   - Select template and format
   - Download final report

### Advanced Features

#### LLM-Assisted Analysis
```python
from src.llm.claude_agent import ClaudeAgent

agent = ClaudeAgent()
compliance_result = agent.check_compliance(test_data, standard="IEC 61215")
```

#### Custom Report Templates
Add custom templates to `config/templates/` using Jinja2 syntax.

#### API Usage
```python
import requests

# Authenticate
response = requests.post("http://localhost:8000/auth/login",
                        json={"username": "user", "password": "pass"})
token = response.json()["access_token"]

# Create sample
headers = {"Authorization": f"Bearer {token}"}
sample_data = {
    "manufacturer": "ABC Solar",
    "model_number": "ABC-550-M",
    "serial_number": "2024001"
}
response = requests.post("http://localhost:8000/api/v1/samples",
                        json=sample_data, headers=headers)
```

## Project Structure

```
pv-test-report-automation/
├── config/              # Configuration files and templates
├── src/                 # Source code
│   ├── ui/             # User interface
│   ├── core/           # Core business logic
│   ├── llm/            # LLM integration
│   ├── export/         # Report generation
│   └── utils/          # Utilities
├── database/           # Database models and migrations
├── tests/              # Test suite
├── docs/               # Documentation
└── deployment/         # Deployment configurations
```

## Testing

Run the test suite:
```bash
pytest tests/
```

With coverage:
```bash
pytest --cov=src tests/
```

## Documentation

- [Architecture](docs/architecture.md)
- [API Reference](docs/api_reference.md)
- [Workflows](docs/workflows.md)
- [Protocols](docs/protocols/)

## Standards Compliance

This system supports testing according to:
- IEC 61215: Terrestrial PV Modules - Design Qualification
- IEC 61730: PV Module Safety Qualification
- IEC 61853: PV Module Performance Testing
- IEC 62716: Ammonia Corrosion Testing
- IEC 61701: Salt Mist Corrosion Testing
- IEC 62804: Potential-Induced Degradation
- IEC 60904: Photovoltaic Devices
- IEC 62759: Transportation Testing
- ISO/IEC 17025: Laboratory Competence
- NABL/ILAC requirements

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email support@pvtestautomation.com or open an issue on GitHub.

## Acknowledgments

- IEC for international standards
- NABL and ILAC for accreditation frameworks
- Anthropic, OpenAI, and Google for LLM APIs
- Open source community for amazing tools
