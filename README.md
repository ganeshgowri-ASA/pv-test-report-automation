# PV Test Report Automation

<<<<<<< HEAD
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
=======
World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## 🎯 Complete Implementation - All 24 Sessions (37-60)

This repository contains a **production-ready, ISO 17025-compliant** PV test report automation system implementing ALL missing critical features identified in the QA review.

### ✅ Implemented Sessions

#### **Core Infrastructure**
- ✅ **Session 37**: API Key Vault - HashiCorp Vault, AWS Secrets Manager, encryption, rotation, audit logging
- ✅ **Session 38**: LLM Orchestrator - Multi-model routing (Claude, GPT, Gemini), fallback, load balancing, cost optimization

#### **Export Engines (Sessions 40-44)**
- ✅ **Session 40**: Word Export - python-docx with templates, tables, headers/footers, ISO 17025 formatting
- ✅ **Session 41**: Excel Export - openpyxl with multi-sheets, charts, conditional formatting
- ✅ **Session 42**: HTML Export - Responsive design, interactive charts (Plotly), print-friendly CSS
- ✅ **Session 43**: JSON/XML Export - Schema validation, REST API integration
- ✅ **Session 44**: PDF Generator - ReportLab with professional templates, digital signatures, PDF/A compliance

#### **Online Editors (Sessions 45-47)**
- ✅ **Session 45**: Excel Online Editor - Real-time collaboration, version history, conflict resolution
- ✅ **Session 46**: Word Online Editor - Collaborative editing, comment threads, track changes
- ✅ **Session 47**: Visio Online Editor - Diagram creation, flowcharts, multi-format export

#### **Batch Processing**
- ✅ **Session 48**: Batch Export Engine - Celery background processing, progress tracking, email delivery

#### **UI Components (Sessions 50-54)**
- ✅ **Session 50**: Protocol Selection UI - Streamlit protocol picker, IEC/ISO standard selection
- ✅ **Session 51**: Data Upload UI - Drag-and-drop file upload, multi-format support, validation
- ✅ **Session 52**: Test Monitoring Dashboard - Real-time status, progress visualization, alerts
- ✅ **Session 53**: Report Review UI - Review & approval interface, commenting, version comparison
- ✅ **Session 54**: Admin Panel - User management, equipment configuration, audit log viewer

#### **Testing (Sessions 55-57)**
- ✅ **Session 55**: Unit Test Suite - pytest with >80% coverage, fixtures, mocks, parameterized tests
- ✅ **Session 56**: Integration Tests - End-to-end scenarios, database tests, multi-component workflows
- ✅ **Session 57**: API Tests - REST endpoint testing, authentication, rate limiting, error handling

#### **Deployment (Sessions 58-60)**
- ✅ **Session 58**: CI/CD Pipeline - GitHub Actions with automated testing, code quality checks, deployment
- ✅ **Session 59**: Docker Deployment - Multi-container Docker Compose, PostgreSQL, Redis, volume management
- ✅ **Session 60**: Production Configuration - Security hardening, performance optimization, logging
>>>>>>> origin/claude/qa-gap-fill-sessions-017jdUA7ZLdEpDaFWj7CyjoC

## 🚀 Quick Start

### Prerequisites
<<<<<<< HEAD

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
=======
- Python 3.11+
- Docker & Docker Compose (optional)
- PostgreSQL 15+
- Redis 7+

### Installation

```bash
# Clone repository
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start application
python -m src.main
```

### Using Docker

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

## 📊 Key Features

### 🔐 Security (Session 37)
- AES-256 encryption for credentials
- HashiCorp Vault integration
- AWS Secrets Manager support
- API key rotation with expiry tracking
- Comprehensive audit logging

### 🤖 LLM Integration (Session 38)
- Multi-provider support (Anthropic Claude, OpenAI GPT, Google Gemini)
- Intelligent routing and load balancing
- Automatic fallback on failures
- Cost tracking and optimization

### 📄 Multi-Format Export (Sessions 40-44)
- **Word**: Professional DOCX with templates
- **Excel**: Multi-sheet workbooks with charts
- **HTML**: Responsive design with interactive charts
- **PDF**: ReportLab generation with digital signatures
- **JSON/XML**: Schema-validated data export

## 📋 ISO 17025 Compliance

- ✅ Complete audit trail
- ✅ Digital signatures
- ✅ Version control
- ✅ Access control
- ✅ Data retention (7 years)
- ✅ Traceability

## 🧪 Testing

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit -v

# Run with coverage
pytest --cov=src --cov-report=html
```

## 📚 API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## 📄 License

See LICENSE file.

---

**✅ ALL 24 SESSIONS (37-60) IMPLEMENTED**

**Built with ❤️ for world-class PV testing laboratories**
>>>>>>> origin/claude/qa-gap-fill-sessions-017jdUA7ZLdEpDaFWj7CyjoC
