# Database Models - PV Test Report Automation

## Overview

This directory contains the SQLModel database models for the PV (Photovoltaic) test report automation system. The models provide complete tracking and traceability for test lab operations in compliance with ISO/IEC 17025, ISO 9001, NABL, and ILAC standards.

## Directory Structure

```
database/
├── __init__.py           # Database configuration and session management
├── models/
│   ├── __init__.py       # Model exports
│   ├── equipment.py      # Equipment and calibration tracking
│   ├── user.py           # User accounts and permissions
│   ├── sample.py         # PV module samples
│   ├── test.py           # Test execution records
│   ├── report.py         # Test reports and workflow
│   └── audit.py          # Audit trail for compliance
└── README.md             # This file
```

## Models

### Equipment
Manages test equipment inventory with calibration tracking:
- Equipment identification and specifications
- Calibration dates and validity tracking
- Measurement uncertainty specifications
- Equipment status and location

**Key Features:**
- Automatic calibration validation
- Days-until-due calculations
- Uncertainty tracking per equipment

### User
User accounts with role-based access control:
- Authentication and authorization
- Multiple roles (admin, engineer, reviewer, approver, etc.)
- Digital signatures and approval workflows
- Qualification tracking

**Key Features:**
- Multi-level review and approval permissions
- Login attempt tracking and account locking
- Approval history for audit trails

### Sample
PV module samples under test:
- Sample identification and tracking
- Customer and manufacturer information
- Testing protocols and scope
- Physical specifications and bill of materials

**Key Features:**
- Multiple serial number tracking
- Package condition documentation
- Storage location management
- Days-in-lab calculations

### Test
Individual test execution records:
- Test type and standard reference
- Measurement readings and conditions
- Equipment and personnel traceability
- Pass/fail determination

**Key Features:**
- 20+ predefined test types (IEC 61215, 61730, 61853, etc.)
- Equipment calibration validation
- Measurement uncertainty tracking
- Review workflows

### Report
Test reports with multi-format export:
- Report structure and content
- Customer information
- Test result summaries
- Multi-level approval workflow

**Key Features:**
- Report versioning and revisions
- Multiple export formats (PDF, DOCX, HTML, etc.)
- Digital signatures
- Workflow tracking (draft → review → approval → issue)

### Audit
Comprehensive audit trail:
- All system actions and changes
- User, timestamp, and IP tracking
- Before/after snapshots
- Compliance tracking

**Key Features:**
- Field-level change tracking
- Configurable retention periods
- Severity levels
- Session tracking

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Initialize Database

```python
from database import init_db

# SQLite (default)
db_config = init_db()

# PostgreSQL
db_config = init_db(
    database_url="postgresql://user:pass@localhost/pvtestlab"
)
```

### Basic Usage

```python
from database import get_session
from database.models import Sample, SampleStatus

# Create a sample
with get_session() as session:
    sample = Sample(
        sample_number="S-2024-001",
        protocol="IEC 61215-2:2021",
        scope="Full type approval testing",
        customer_name="Solar Tech Industries",
        manufacturer="High Efficiency Solar Co.",
        model_number="HES-400W-MONO",
        serial_numbers=["SN001", "SN002"],
        quantity=2,
        received_date="2024-01-15",
        status=SampleStatus.RECEIVED
    )
    session.add(sample)
    session.commit()

# Query samples
with get_session() as session:
    samples = session.query(Sample).filter(
        Sample.status == SampleStatus.IN_PROGRESS
    ).all()

    for sample in samples:
        print(f"{sample.sample_number}: {sample.days_in_lab()} days in lab")
```

### Run Example

```bash
python examples/basic_usage.py
```

This will create a demonstration database with sample data and run various queries.

## Database Migrations

We use Alembic for database migrations:

```bash
# Create a migration after modifying models
alembic revision --autogenerate -m "Add new field"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# View history
alembic history
```

## Key Features

### Relationships
- Equipment → Tests (one-to-many)
- Sample → Tests (one-to-many)
- User → Tests (performed_by, reviewed_by)
- User → Reports (prepared_by, reviewed_by, approved_by)
- User → Audit Logs (one-to-many)
- Report → Report (revisions via parent_report_id)

### Constraints
- Unique constraints on critical identifiers
- Foreign key relationships ensure referential integrity
- Check constraints for data validation
- Composite unique constraints (e.g., report_number + revision)

### Indexes
Strategic indexes for common queries:
- Status-based filtering
- Date range queries
- Customer/manufacturer lookups
- Equipment calibration tracking
- Audit trail queries

### JSON Fields
Flexible JSON fields for:
- Test readings and measurements
- Sample specifications
- Report content structure
- User qualifications
- Audit change tracking

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=database --cov-report=html
```

## Documentation

Detailed schema documentation available in:
- `docs/DATABASE_SCHEMA.md` - Complete schema reference
- Each model file contains detailed docstrings
- Example usage in `examples/basic_usage.py`

## Compliance Standards

This database design supports compliance with:

- **ISO/IEC 17025:2017** - Testing and calibration laboratories
- **ISO 9001:2015** - Quality management systems
- **NABL** - National Accreditation Board for Testing and Calibration Laboratories
- **ILAC** - International Laboratory Accreditation Cooperation

### Compliance Features

1. **Full Traceability**: Complete chain from sample receipt to report issuance
2. **Audit Trail**: Every action logged with user, timestamp, and changes
3. **Calibration Control**: Equipment calibration validity enforced
4. **Review Workflows**: Multi-level review and approval processes
5. **Data Integrity**: Comprehensive constraints and validations
6. **Document Control**: Report versioning and change tracking
7. **Personnel Records**: Qualifications and training tracking
8. **Uncertainty Management**: Measurement uncertainty specifications

## Best Practices

1. **Always use context managers** for database sessions
2. **Commit transactions explicitly** after making changes
3. **Use relationships** instead of manual joins
4. **Validate calibration** before creating test records
5. **Log all significant actions** using the Audit model
6. **Review auto-generated migrations** before applying
7. **Use enums** for status and type fields
8. **Add indexes** for frequently queried fields

## Development

### Code Quality

```bash
# Format code
black database/

# Sort imports
isort database/

# Lint
flake8 database/

# Type checking
mypy database/
```

### Adding a New Model

1. Create model file in `database/models/`
2. Define model class inheriting from SQLModel
3. Add relationships and constraints
4. Export from `database/models/__init__.py`
5. Create migration: `alembic revision --autogenerate`
6. Review and apply migration
7. Update documentation

## Support

For issues or questions:
- See `docs/DATABASE_SCHEMA.md` for detailed schema documentation
- Review `examples/basic_usage.py` for usage patterns
- Check the main project README for contact information

## License

See LICENSE file in the repository root.
