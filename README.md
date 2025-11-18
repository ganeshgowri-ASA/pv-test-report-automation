# PV Test Report Automation

World-class photovoltaic (PV) module test laboratory report automation system with full ISO 17025, NABL, and IEC compliance.

## 🌟 Features

### Test Protocols (Phase 3)
- **IEC 61215** - Module Stress Testing (MST)
  - Damp Heat: 200 cycles @ 85°C/85% RH
  - Thermal Cycling: 200 cycles (-40°C to +85°C)
  - Humidity Freeze: 10 cycles
  - UV Preconditioning: 15 kWh/m²

- **IEC 61730** - Safety Qualification
  - Dielectric withstand voltage testing
  - Wet leakage current testing
  - Mechanical load testing
  - Impact resistance testing
  - Fire testing (Class T)

- **IEC 61853** - Performance Testing
  - Irradiance-temperature matrix
  - Angle of incidence (AOI) response
  - Spectral responsivity
  - Energy rating calculation

- **IEC 61701** - Salt Mist Corrosion
  - Severity levels 1-6
  - Cyclic salt spray exposure
  - Visual inspection protocols

### Advanced Features

#### Image Processing (Phase 4)
- **Electroluminescence (EL) Analysis**
  - Microcrack detection
  - Cell defect identification
  - Hot spot detection
  - Automated severity classification

#### Workflow Management (Phase 5)
- **Review Workflow**
  - Multi-level approval system
  - Comment and annotation system
  - Digital signatures (NABL compliant)
  - Revision tracking with full audit trail

#### LLM Integration (Phase 7)
- **AI-Powered Analysis**
  - Claude (Anthropic) - Compliance checking
  - GPT-4 (OpenAI) - Report summarization
  - Gemini (Google) - Data analysis
  - Multi-model orchestration with fallback
  - Secure API key vault with encryption

#### Export Engines (Phase 8)
- **Multi-Format Export**
  - PDF reports (ReportLab)
  - Word documents (.docx)
  - Excel spreadsheets (.xlsx)
  - HTML responsive reports
  - JSON/XML structured data
  - Batch export with parallel processing

#### User Interface (Phase 10)
- **Streamlit Components**
  - Protocol selection wizard
  - Data upload interface
  - Real-time test monitoring dashboard
  - Review & approval interface
  - System administration panel

#### Testing & Deployment (Phase 11)
- **Comprehensive Testing**
  - Unit tests with pytest
  - Integration tests
  - API endpoint tests
  - 80%+ code coverage

- **Production Deployment**
  - Docker containerization
  - Docker Compose orchestration
  - CI/CD with GitHub Actions
  - Production configuration templates

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (for containerized deployment)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
   cd pv-test-report-automation
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp deployment/production/.env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   python -m src.main db init
   ```

### Running the Application

#### Option 1: Docker Compose (Recommended)

```bash
cd deployment/docker
docker-compose up -d
```

Access:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Streamlit UI: http://localhost:8501

#### Option 2: Manual Launch

**Launch API Server:**
```bash
python -m src.main api --host 0.0.0.0 --port 8000
```

**Launch Streamlit UI:**
```bash
python -m src.main ui --port 8501
```

## 📦 Deployment

### Docker Deployment

```bash
# Build image
docker build -t pv-test-automation:latest .

# Run with Docker Compose
cd deployment/docker
docker-compose up -d
```

### Production Deployment

See [deployment/production/README.md](deployment/production/README.md) for detailed production deployment guide.

## 🔒 Security & Compliance

- **ISO 17025:2017** - Testing and calibration laboratory requirements
- **NABL** - National Accreditation Board for Testing and Calibration Laboratories
- **IEC Standards** - International Electrotechnical Commission compliance
- **Digital Signatures** - NABL-compliant digital signature support
- **Audit Trail** - Complete audit logging for all operations
- **Encrypted Storage** - AES-256 encryption for sensitive data

## 📊 Standards Compliance

✅ IEC 61215:2021 - Terrestrial PV modules - Design qualification
✅ IEC 61730:2016 - PV module safety qualification
✅ IEC 61853:2018 - PV module performance testing
✅ IEC 61701:2020 - Salt mist corrosion testing
✅ ISO 17025:2017 - Testing and calibration laboratories
✅ ISO 9001:2015 - Quality management systems
✅ NABL - Indian accreditation requirements

## 📧 Support

For support and inquiries:
- Issues: https://github.com/ganeshgowri-ASA/pv-test-report-automation/issues

---

**Built with ❤️ for the solar industry**

*Empowering PV testing laboratories worldwide with automation and AI*
