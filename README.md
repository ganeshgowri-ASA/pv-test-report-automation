# ⚡ PV Test Report Automation System

World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)
[![ISO 17025](https://img.shields.io/badge/ISO%2017025-Compliant-green.svg)](https://www.iso.org/standard/66912.html)

## 🌟 Features

### 📋 IEC Protocol Standards (8 Protocols)
- **IEC 61215** - Terrestrial PV Modules Design Qualification
- **IEC 61730** - PV Module Safety Qualification
- **IEC 61853** - PV Module Performance Testing & Energy Rating
- **IEC 62716** - Ammonia (NH₃) Corrosion Testing
- **IEC 61701** - Salt Mist Corrosion Testing
- **IEC 62804** - Potential-Induced Degradation (PID) Testing
- **IEC 60904** - PV Device I-V Characteristics Measurement
- **IEC 62759** - Transportation Testing for PV Modules

### 🔬 Test Block Modules (9 Modules)
1. **I-V Curve Analysis** - Current-voltage characteristic measurements
2. **Electroluminescence (EL) Imaging** - Cell crack and defect detection
3. **Insulation Testing** - High voltage insulation resistance
4. **Leakage Current** - Wet leakage current measurements
5. **Ground Continuity** - Protective grounding verification
6. **Hot-Spot Endurance** - Thermal stress testing
7. **Bypass Diode Testing** - Diode thermal and functional tests
8. **Mechanical Load Testing** - Static and dynamic load testing
9. **Hail Impact Testing** - Ice ball impact resistance

### 📤 Multi-Format Data Ingestion
- ✅ **Excel** (.xlsx, .xls, .xlsm) - Test data spreadsheets
- ✅ **Word** (.docx, .doc) - Report templates and documents
- ✅ **PDF** - Equipment outputs and certificates
- ✅ **Images** (JPG, PNG, TIFF, BMP) - EL images, visual inspection
- ✅ **JSON/CSV** - Structured data exchange
- ✅ **XML** - Equipment data exports
- ✅ **Visio** (.vsdx) - System diagrams and schematics

### 🤖 LLM Integration
- **Claude (Anthropic)** - Advanced reasoning and analysis
- **GPT-4 (OpenAI)** - Natural language processing
- **Gemini (Google)** - Multi-modal understanding
- **Features**:
  - Automated anomaly detection
  - Intelligent test result interpretation
  - Standards compliance verification
  - Report narrative generation
  - Technical recommendation generation

### 📄 Multi-Format Report Export
- 📕 **PDF** - ISO 17025 compliant reports
- 📘 **Word** (.docx) - Editable report documents
- 📗 **Excel** (.xlsx) - Data tables and analysis
- 🌐 **HTML** - Web-viewable reports
- 📰 **LaTeX** - Publication-ready documents
- 💾 **JSON/XML** - Structured data export

### ✅ ISO 17025 / NABL Compliance
- Complete audit trail with immutable logging
- Equipment calibration tracking
- Traceability to national/international standards
- Reviewer/Approver workflow with digital signatures
- Uncertainty analysis and SPC
- NABL, ILAC, and BIS logo integration
- Accreditation number on all reports

### 🔧 Equipment & Calibration Management
- Equipment inventory tracking
- Calibration certificate management
- Automated calibration reminders
- Equipment usage history
- Maintenance logging
- Traceability chains

### 👥 Reviewer/Approver Workflow
- Multi-level review process
- Technical reviewer validation
- Management approval workflow
- Comment and revision system
- Digital signature capture
- Immutable audit trails

## 🏗️ Architecture

### Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                     Nginx (Reverse Proxy)                   │
│                    Port 80/443 (HTTP/HTTPS)                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼────────┐          ┌─────────▼──────────┐
│  Streamlit UI  │          │   FastAPI Server   │
│   Port 8501    │          │     Port 8000      │
└────────┬───────┘          └──────────┬─────────┘
         │                             │
         └──────────────┬──────────────┘
                        │
        ┌───────────────┼───────────────┬──────────────┐
        │               │               │              │
┌───────▼────┐  ┌──────▼──────┐  ┌────▼─────┐  ┌─────▼──────┐
│ PostgreSQL │  │    Redis    │  │  MinIO   │  │  RabbitMQ  │
│   (Data)   │  │   (Cache)   │  │ (Storage)│  │  (Queue)   │
└────────────┘  └─────────────┘  └──────────┘  └────────────┘
                                                      │
                                              ┌───────▼────────┐
                                              │ Celery Workers │
                                              │ (Background)   │
                                              └────────────────┘
```

### Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Streamlit | Interactive web UI |
| **API Server** | FastAPI | RESTful API backend |
| **Database** | PostgreSQL 15+ | Primary data store |
| **Cache** | Redis 7 | Session & performance cache |
| **Storage** | MinIO/S3 | Object storage for files |
| **Queue** | Celery + RabbitMQ | Async task processing |
| **Proxy** | Nginx | Reverse proxy & load balancer |

## 🚀 Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ RAM
- 100GB+ Storage

### Installation

```bash
# Clone repository
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation

# Configure environment
cp .env.example .env
nano .env  # Update with your configuration

# Start services
docker-compose up -d

# Check status
docker-compose ps
python healthcheck.py
```

### Access Application

- **Web UI**: http://localhost
- **API Docs**: http://localhost/api/docs
- **Default Login**: admin / admin123 (⚠️ change immediately)

## 📖 Documentation

- [Deployment Guide](DEPLOYMENT.md) - Production deployment instructions
- [API Documentation](http://localhost/api/docs) - Interactive API documentation
- [User Manual](docs/USER_MANUAL.md) - End-user guide (coming soon)
- [Developer Guide](docs/DEVELOPER.md) - Development setup (coming soon)

## 🔧 Configuration

### Environment Variables

Key configuration in `.env`:

```env
# Database
DB_USER=pv_admin
DB_PASSWORD=your_secure_password

# LLM API Keys
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
GOOGLE_API_KEY=your_key

# Accreditation
ACCREDITATION_NUMBER=TC-XXXX
LAB_NAME=Your Lab Name
```

See [.env.example](.env.example) for complete configuration options.

## 🧪 Testing Workflow

### Complete Test Process

1. **Protocol Selection** → Choose IEC standard (e.g., IEC 61215)
2. **Sample Registration** → Register module details
3. **Data Upload** → Import test data (Excel, PDF, images)
4. **Test Execution** → Run automated test sequence
5. **LLM Analysis** → AI-powered result interpretation
6. **Review** → Technical reviewer validation
7. **Approval** → Management approval
8. **Report Generation** → Multi-format report export

### Data Flow

```
Raw Data → Ingestion → Validation → Processing → Analysis →
Review → Approval → Report Generation → Archive
```

## 🏆 Compliance & Standards

### Accreditation Bodies
- ✅ **NABL** (National Accreditation Board for Testing and Calibration Laboratories)
- ✅ **ILAC** (International Laboratory Accreditation Cooperation)
- ✅ **ISO/IEC 17025:2017** (General requirements for testing and calibration laboratories)
- ✅ **BIS** (Bureau of Indian Standards)

### Quality Management
- Complete traceability chains
- Measurement uncertainty analysis
- Statistical Process Control (SPC)
- Calibration management
- Equipment verification
- Method validation
- Proficiency testing integration

## 📊 System Capabilities

| Capability | Specification |
|-----------|---------------|
| **Protocols Supported** | 8 IEC standards |
| **Test Modules** | 9 specialized modules |
| **Input Formats** | 8+ file formats |
| **Output Formats** | 7+ export formats |
| **LLM Providers** | 3 (Claude, GPT-4, Gemini) |
| **Max File Size** | 100 MB (configurable) |
| **Concurrent Users** | 50+ (scalable) |
| **Data Retention** | Unlimited (configurable) |

## 🔐 Security Features

- ✅ Role-based access control (RBAC)
- ✅ JWT authentication
- ✅ Password hashing (bcrypt)
- ✅ Audit logging (immutable)
- ✅ Data encryption at rest
- ✅ HTTPS/TLS support
- ✅ Digital signatures
- ✅ Session management
- ✅ Input validation
- ✅ SQL injection protection

## 📈 Performance

### Optimizations
- Redis caching for frequently accessed data
- Asynchronous task processing with Celery
- Database connection pooling
- CDN-ready static assets
- Nginx reverse proxy with compression
- Horizontal scaling support

### Benchmarks
- Report generation: < 30 seconds (typical)
- LLM analysis: < 60 seconds (typical)
- Data upload: < 10 seconds (100MB file)
- Dashboard load: < 2 seconds

## 🛠️ Development

### Project Structure

```
pv-test-report-automation/
├── api/                    # FastAPI backend
│   ├── main.py            # API application
│   ├── celery_app.py      # Celery configuration
│   └── tasks.py           # Background tasks
├── streamlit_app/         # Streamlit frontend
│   ├── main.py           # Main application
│   └── pages/            # Page modules
├── src/                   # Core business logic
│   ├── core/             # Core functionality
│   ├── models/           # Data models
│   ├── services/         # Business services
│   └── utils/            # Utilities
├── database/             # Database schemas
│   └── init/             # Initialization scripts
├── config/               # Configuration files
├── nginx/                # Nginx configuration
├── docker-compose.yml    # Docker orchestration
├── requirements.txt      # Python dependencies
└── .env.example          # Environment template
```

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run Streamlit (development)
streamlit run streamlit_app/main.py

# Run API (development)
uvicorn api.main:app --reload

# Run Celery worker
celery -A api.celery_app worker --loglevel=info
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **ASA Team** - Initial work - [ganeshgowri-ASA](https://github.com/ganeshgowri-ASA)

## 🙏 Acknowledgments

- IEC for photovoltaic testing standards
- ISO for laboratory quality standards
- NABL for accreditation framework
- Open source community for amazing tools

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/ganeshgowri-ASA/pv-test-report-automation/issues)
- **Documentation**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Email**: support@pvtesting.com

## 🗺️ Roadmap

### Current Version (v1.0.0)
- ✅ 8 IEC protocol implementations
- ✅ 9 test block modules
- ✅ Multi-format ingestion and export
- ✅ LLM integration (3 providers)
- ✅ ISO 17025 compliance
- ✅ Docker deployment

### Future Enhancements (v1.1.0+)
- [ ] Mobile application (iOS/Android)
- [ ] Advanced AI anomaly detection
- [ ] Real-time equipment integration
- [ ] Blockchain-based audit trails
- [ ] Multi-language support
- [ ] Advanced SPC dashboards
- [ ] Cloud deployment templates (AWS, Azure, GCP)
- [ ] Automated proficiency testing

---

**⚡ Built with passion for photovoltaic testing excellence**

**Version**: 1.0.0 | **Status**: Production Ready | **Last Updated**: November 2024
