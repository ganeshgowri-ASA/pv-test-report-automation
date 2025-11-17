# PV Test Report Automation

World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## Project Status

### Phase 1 - Database Models & Schema ✅ COMPLETED

Complete SQLAlchemy/SQLModel database models with full compliance support:

- ✅ **Equipment Model**: Test equipment with calibration tracking and uncertainty management
- ✅ **User Model**: User accounts with role-based access control and approval workflows
- ✅ **Sample Model**: PV module sample tracking with complete specifications
- ✅ **Test Model**: Individual test execution records with full traceability
- ✅ **Report Model**: Test reports with multi-level approval and export capabilities
- ✅ **Audit Model**: Comprehensive audit trail for compliance

**Features:**
- Full relationships between models
- Comprehensive constraints and indexes
- ISO/IEC 17025 compliance support
- Equipment calibration validation
- Multi-level review workflows
- Complete audit trail
- Database migration support (Alembic)

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from database import init_db; init_db()"

# Run example
python examples/basic_usage.py
```

### Database Usage

```python
from database import get_session
from database.models import Sample, Test, Equipment

# Create a session
with get_session() as session:
    # Query samples
    samples = session.query(Sample).all()

    # Create new test
    test = Test(
        sample_id=1,
        type=TestType.ELECTRICAL_PERFORMANCE,
        test_date="2024-01-20",
        # ... other fields
    )
    session.add(test)
    session.commit()
```

## Project Structure

```
pv-test-report-automation/
├── database/                   # Database models and configuration
│   ├── models/                # SQLModel database models
│   │   ├── equipment.py       # Equipment model
│   │   ├── user.py            # User model
│   │   ├── sample.py          # Sample model
│   │   ├── test.py            # Test model
│   │   ├── report.py          # Report model
│   │   └── audit.py           # Audit model
│   ├── __init__.py            # Database configuration
│   └── README.md              # Database documentation
├── alembic/                   # Database migrations
│   ├── versions/              # Migration scripts
│   ├── env.py                 # Alembic environment
│   └── README                 # Migration instructions
├── docs/                      # Documentation
│   └── DATABASE_SCHEMA.md     # Complete schema reference
├── examples/                  # Example scripts
│   └── basic_usage.py         # Usage demonstration
├── requirements.txt           # Python dependencies
├── alembic.ini               # Alembic configuration
├── LICENSE                    # MIT License
└── README.md                  # This file
```

## Models Overview

### Equipment
- Equipment identification and specifications
- Calibration tracking and validity
- Measurement uncertainty management
- Equipment status and location

### User
- Authentication and authorization
- Role-based access control
- Digital signatures
- Approval workflows
- Qualification tracking

### Sample
- Sample identification and tracking
- Customer and manufacturer info
- Testing protocols and scope
- Physical specifications and BOM

### Test
- Test execution records
- 20+ predefined test types
- Equipment and personnel traceability
- Measurement data and uncertainty
- Pass/fail determination

### Report
- Report structure and content
- Multi-level approval workflow
- Report versioning and revisions
- Multi-format export (PDF, DOCX, HTML)

### Audit
- Complete action tracking
- User, timestamp, IP logging
- Before/after state snapshots
- Field-level change tracking

## Standards Compliance

This system supports compliance with:

- **IEC 61215** - PV module design qualification and type approval
- **IEC 61730** - PV module safety qualification
- **IEC 61853** - PV module performance testing and energy rating
- **ISO/IEC 17025:2017** - General requirements for testing and calibration laboratories
- **ISO 9001:2015** - Quality management systems
- **NABL** - National Accreditation Board for Testing and Calibration Laboratories
- **ILAC** - International Laboratory Accreditation Cooperation

## Documentation

- **[Database Schema](docs/DATABASE_SCHEMA.md)** - Complete database schema reference
- **[Database README](database/README.md)** - Database usage guide
- **[Basic Usage Example](examples/basic_usage.py)** - Working code examples

## Development

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Code Quality

```bash
# Format code
black .

# Sort imports
isort .

# Lint
flake8 .

# Type checking
mypy database/
```

### Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=database --cov-report=html
```

## Technology Stack

- **SQLModel** - Database ORM (SQLAlchemy + Pydantic)
- **Alembic** - Database migrations
- **Pydantic** - Data validation
- **Python 3.9+** - Programming language

## Roadmap

- [x] Phase 1: Database Models & Schema
- [ ] Phase 2: API Layer (FastAPI)
- [ ] Phase 3: Test Data Processing
- [ ] Phase 4: Report Generation
- [ ] Phase 5: LLM Integration
- [ ] Phase 6: Web Interface
- [ ] Phase 7: Multi-format Export

## Contributing

Contributions are welcome! Please ensure all code follows the project's coding standards and includes appropriate tests.

## License

MIT License - see LICENSE file for details.

## Contact

For questions or support, please open an issue on GitHub.
