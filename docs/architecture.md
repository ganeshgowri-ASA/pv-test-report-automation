# System Architecture

## Overview
The PV Test Report Automation system is a comprehensive platform for managing photovoltaic module testing workflows, data analysis, and report generation in compliance with international standards.

## Architecture Layers

### 1. Presentation Layer (UI)
- **Streamlit Dashboard**: Main user interface for test engineers and lab managers
- **Customer Portal**: Read-only access for clients to view reports and status
- **Components**: Reusable UI widgets for file upload, report viewing, and workflow management

### 2. Application Layer (Core)

#### Data Ingestion
- File parsers for Excel, Word, PDF documents
- Image processors for EL, IR, and visual inspection images
- OCR engine for extracting data from scanned documents

#### Protocol Engines
Individual modules for each IEC standard:
- IEC 61215 (Design Qualification)
- IEC 61730 (Safety Qualification)
- IEC 61853 (Performance Testing)
- IEC 62716 (Ammonia Corrosion)
- IEC 61701 (Salt Mist)
- IEC 62804 (PID Testing)
- IEC 60904 (PV Device Measurements)
- IEC 62759 (Transportation Testing)

#### Test Block Processors
Specialized processors for each test type:
- IV Curve Analysis
- Electroluminescence (EL) Testing
- Visual Inspection (VI)
- Infrared (IR) Imaging
- Climate Chamber Tests
- Outdoor Exposure
- Insulation Testing
- Wet Leakage Test (WLT)
- Ground Continuity Test (GCT)

#### Workflow Management
- Multi-level review and approval system
- Role-based access control (RBAC)
- Email and SMS notifications
- Task assignment and tracking

#### Traceability & Audit
- Complete data lineage tracking
- Cryptographic hash generation for data integrity
- Comprehensive audit logs
- Change history tracking

#### Equipment Management
- Equipment calibration tracking
- Uncertainty calculation
- Maintenance scheduling
- Calibration certificate management

### 3. LLM Integration Layer
- **Claude Agent**: Compliance checking, report generation, technical analysis
- **GPT Agent**: Data extraction, summarization
- **Gemini Agent**: Multimodal analysis for image interpretation
- **Compliance Bot**: Automated standard compliance verification
- **Summarizer**: Executive summary generation

### 4. Export Layer
- **LaTeX Engine**: High-quality PDF generation
- **PDF Generator**: Direct PDF creation
- **Word Exporter**: Microsoft Word format reports
- **HTML Builder**: Web-based reports
- **Excel Exporter**: Data tables and graphs
- **JSON/XML Exporter**: Structured data export

### 5. Data Layer
- **SQLAlchemy ORM**: Database abstraction
- **PostgreSQL**: Production database
- **SQLite**: Development and testing
- **Models**: Sample, Test, Report, User, Audit, Equipment

## System Flow

```
┌─────────────────┐
│  Data Sources   │
│  (Excel, Word,  │
│   Images, PDFs) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Data Ingestion  │
│   & OCR         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Protocol Engine │
│ (IEC Standards) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Test Block     │
│  Processors     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LLM Analysis   │
│  & Compliance   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Review/Approval │
│    Workflow     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Report Export   │
│  (PDF, Word,    │
│   Excel, etc.)  │
└─────────────────┘
```

## Technology Stack

### Backend
- Python 3.10+
- FastAPI for REST APIs
- SQLAlchemy for ORM
- Celery for async tasks

### Frontend
- Streamlit for dashboards
- Plotly for interactive charts
- AG-Grid for data tables

### LLM Providers
- Anthropic (Claude)
- OpenAI (GPT-4)
- Google (Gemini)

### Database
- PostgreSQL (Production)
- SQLite (Development)

### Security
- JWT for authentication
- Bcrypt for password hashing
- Encrypted API key storage
- Role-based access control

## Deployment Architecture

### Development
- Local development with SQLite
- Streamlit dev server
- Environment-based configuration

### Production
- Docker containers
- PostgreSQL database
- Nginx reverse proxy
- Redis for caching and Celery
- Load balancing (if scaled)

## ISO 17025 & NABL Compliance

The system is designed to meet requirements of:
- ISO/IEC 17025:2017 (Laboratory competence)
- NABL 162 (Electrical testing lab criteria)
- ILAC-G8 (Assessment and reporting)

Key compliance features:
- Complete traceability
- Audit trails
- Calibration management
- Uncertainty calculations
- Quality control charts
- Review and approval workflows
- Secure data storage
- Backup and recovery

## Security Considerations

1. **Authentication**: Multi-factor authentication support
2. **Authorization**: Role-based access control
3. **Encryption**: Data encryption at rest and in transit
4. **Audit**: Complete audit logging
5. **API Security**: Rate limiting and API key management
6. **Data Privacy**: GDPR compliance support

## Scalability

The system is designed to scale:
- Horizontal scaling via Docker containers
- Async task processing with Celery
- Database connection pooling
- Caching layer with Redis
- CDN for static assets

## Future Enhancements

- Mobile app for field data capture
- Real-time equipment data integration
- Machine learning for defect detection
- Predictive maintenance for equipment
- Advanced SPC charting
- Integration with LIMS systems
