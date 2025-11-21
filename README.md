# ⚡ PV Test Report Automation System

**World-Class Photovoltaic Module Testing & ISO 17025 Compliant Report Generation Platform**

[![ISO 17025](https://img.shields.io/badge/ISO_17025-Compliant-green)](https://www.iso.org/standard/66912.html)
[![NABL](https://img.shields.io/badge/NABL-Certified-blue)](https://www.nabl-india.org/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31-FF4B4B)](https://streamlit.io/)

## 🎯 Overview

The **PV Test Report Automation System** integrates **60+ specialized development sessions** into a production-ready platform for photovoltaic module testing laboratories.

### Key Features

- **8 IEC Protocol Standards** - Complete implementations (61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759)
- **Multi-format Data Ingestion** - Excel, Word, PDF, Images, JSON, CSV, Visio, Gantt, SmartSheet
- **LLM-Powered Analysis** - Claude, GPT-4, Gemini integration
- **ISO 17025 Compliant Workflows** - Complete Review → Approval → Export workflow
- **7 Export Formats** - PDF, LaTeX, Word, Excel, HTML, JSON, XML
- **Complete Audit Trail** - Full traceability and compliance logging

---

## 🚀 Quick Start

### Docker Deployment (Recommended)

```bash
# Clone repository
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation

# Configure environment
cp .env.example .env
nano .env  # Edit with your settings

# Start all services
docker-compose up -d

# Access Streamlit UI
# Open browser: http://localhost:8501
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run Streamlit app
streamlit run streamlit_app/main.py
```

---

## 📋 IEC Protocols Implemented

| Protocol | Description | Key Tests |
|----------|-------------|-----------|
| **IEC 61215** | Design Qualification | Visual, Power, UV, Thermal Cycling, Mechanical Load, Hail Impact |
| **IEC 61730** | Safety Qualification | Construction, Insulation, Fire Safety, Ground Continuity |
| **IEC 61853** | Performance Testing | IV Curves, Spectral Response, Angle of Incidence |
| **IEC 62716** | Ammonia Corrosion | NH₃ Exposure Testing |
| **IEC 61701** | Salt Mist Corrosion | NaCl Salt Spray Testing |
| **IEC 62804** | PID Testing | Potential Induced Degradation Detection |
| **IEC 60904** | IV Measurements | Precision Current-Voltage Characterization |
| **IEC 62759** | Transportation | Vibration, Shock, Drop Testing |

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────┐
│         STREAMLIT WEB INTERFACE (Port 8501)           │
│   Dashboard | Protocols | Upload | Test | Review      │
└────────────────────────────────────────────────────────┘
                         │
          ┌──────────────┴───────────────┐
          │                              │
┌─────────▼─────────┐         ┌─────────▼──────────┐
│  FASTAPI BACKEND  │         │  CELERY WORKERS    │
│   (Port 8000)     │         │  (Background)      │
└─────────┬─────────┘         └─────────┬──────────┘
          │                              │
          └──────────────┬───────────────┘
                         │
                ┌────────▼─────────┐
                │   POSTGRESQL     │
                │   (Port 5432)    │
                └──────────────────┘
```

### Technology Stack

- **Frontend**: Streamlit 1.31+
- **Backend**: FastAPI + Celery
- **Database**: PostgreSQL 15+
- **Cache/Queue**: Redis
- **LLM**: Anthropic Claude, OpenAI GPT-4, Google Gemini
- **Deployment**: Docker Compose

---

## 📊 Test Workflow

```
Sample Registration → Protocol Selection → Data Upload →
Test Execution → LLM Analysis → Review → Approval → Export
```

### Example: Running IEC 61215 Test

1. **Register Sample**: Enter manufacturer, model, serial, specs
2. **Select Protocol**: Choose IEC 61215
3. **Upload Data**: IV curves, EL images, equipment logs
4. **Execute Tests**: Run automated test sequence
5. **LLM Analysis**: AI-powered defect detection & compliance check
6. **Review**: Multi-level approval workflow
7. **Export**: Generate report in desired format

---

## 🔧 Configuration

### Required Environment Variables

```bash
# Database
DB_HOST=postgres
DB_PASSWORD=your_secure_password

# Security
SECRET_KEY=generate_random_key_here

# Accreditation
NABL_NUMBER=NABL-XXXXX
LAB_NAME=Your Laboratory Name

# LLM APIs (at least one required)
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx
GEMINI_API_KEY=xxx
```

See `.env.example` for complete configuration.

---

## 📁 Project Structure

```
pv-test-report-automation/
├── streamlit_app/          # Streamlit UI
│   ├── main.py
│   └── pages/              # Dashboard, Protocols, Upload, etc.
├── src/
│   ├── core/               # Config, Security, Database
│   ├── protocols/          # All 8 IEC implementations
│   ├── test_blocks/        # IV, EL, IR, etc.
│   ├── ingestion/          # Data importers
│   ├── llm/                # LLM integrations
│   ├── exports/            # Report generators
│   └── workflows/          # Review/Approval
├── api/                    # FastAPI backend
├── tests/                  # Unit, Integration, E2E tests
├── docker/                 # Docker configs
├── requirements.txt
├── docker-compose.yml
└── README.md
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

---

## 🔒 Security & Compliance

- **ISO 17025 Compliant**: Complete audit trail, data integrity
- **NABL Certified**: Supports NABL accreditation requirements
- **Data Integrity**: SHA-256 checksums, digital signatures
- **Role-Based Access**: Technician, Engineer, Reviewer, Approver, Admin
- **MFA Support**: Optional multi-factor authentication
- **Encrypted Storage**: All sensitive data encrypted at rest

---

## 📄 Export Formats

Generate professional reports in multiple formats:

- **PDF**: Print-ready with watermarks, signatures
- **LaTeX**: Publication-quality academic reports
- **Word (.docx)**: Editable Microsoft Word documents
- **Excel (.xlsx)**: Data-heavy analysis workbooks
- **HTML**: Web-viewable interactive reports
- **JSON/XML**: Machine-readable for system integrations

---

## 🤝 Integration Capabilities

- **60+ Feature Branches Integrated**: Database, Security, Protocols, Tests, Workflows, LLM, Export
- **Equipment Integration Ready**: Modbus, OPC-UA support (future)
- **LIMS Compatible**: Export to laboratory information management systems
- **API-First Design**: RESTful API for third-party integrations

---

## 📚 Documentation

- **User Manual**: Complete guide for lab technicians
- **API Reference**: FastAPI endpoint documentation
- **Protocol Guides**: Detailed IEC standard implementations
- **Developer Guide**: Contributing and extending the system

---

## 🎯 Development Sessions Integrated

This production system integrates **60+ specialized development sessions**:

### Foundation (Sessions 1-4)
- Database models & schema
- Configuration management system
- Security core implementation
- Audit trail & lineage

### Data Ingestion (Sessions 5-10)
- Data validation utilities
- Excel ingestion engine
- Word/PDF ingestion
- Image processor
- JSON/CSV ingestion
- Visio/Gantt/SmartSheet ingestion

### IEC Protocols (Sessions 11-18)
- All 8 IEC standard implementations
- Test matrices & acceptance criteria
- Protocol validation logic

### Test Blocks (Sessions 19-27)
- IV Curve, EL Detection, Visual Inspection
- IR Thermography, Insulation, Leakage, Ground
- Hot-spot, Bypass Diode, Mechanical, Hail

### Workflows (Sessions 28-33)
- Review workflow system
- Approval workflow engine
- Notification & alerts
- Equipment management
- Calibration tracking
- SPC & uncertainty analysis

### LLM Integration (Sessions 34-38)
- Claude API integration
- GPT-4 integration
- Gemini integration
- Compliance checker
- Report summarizer

### Export & UI (Sessions 39-60)
- LaTeX, PDF, Word, Excel, HTML, JSON/XML export
- Document/Excel/Flowchart/Gantt editors
- Complete Streamlit UI (9 pages)
- Integration tests, Unit tests, QA tests
- E2E workflows, Optimization, Deployment

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/ganeshgowri-ASA/pv-test-report-automation/issues)
- **Wiki**: [Documentation Wiki](https://github.com/ganeshgowri-ASA/pv-test-report-automation/wiki)

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built integrating knowledge from **60+ specialized development sessions** to create a world-class PV testing automation platform.

**Powering the Clean Energy Future** ⚡🌞

---

**Version**: 1.0.0
**Last Updated**: November 21, 2025
**Status**: Production Ready
