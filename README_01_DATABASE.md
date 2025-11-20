# Session 01: Database Models

## Overview

This module implements the complete database schema for the PV Test Report Automation System using SQLAlchemy ORM. The models are designed to be compliant with IEC 61215-2021, IEC 61730-2023, ISO 17025, and NABL standards.

## Structure

```
src/database/
├── __init__.py          # Module exports
├── base.py              # Database engine and session management
├── models/
│   ├── __init__.py      # Model exports
│   ├── sample.py        # Sample/module model
│   ├── test.py          # Test execution model
│   ├── user.py          # User, Role, Permission models
│   ├── report.py        # Report generation models
│   ├── audit.py         # Audit trail and lineage
│   └── equipment.py     # Equipment and calibration
├── migrations/          # Alembic migrations
└── schemas/             # Pydantic schemas (TODO)
```

## Models

### 1. Sample Model (`sample.py`)

Represents PV modules under test.

**Key Features:**
- Complete module identification (manufacturer, model, serial number)
- Physical characteristics (dimensions, weight, cell count)
- Electrical ratings (Pmax, Voc, Isc, Vmp, Imp)
- Module technology classification
- Test campaign tracking
- Sample status lifecycle
- Image and document attachments
- Flexible metadata with JSON fields

**Technology Types:**
- Monocrystalline, Polycrystalline
- Thin-film (CdTe, CIGS, a-Si)
- Advanced (PERC, TOPCon, HJT, IBC)
- Bifacial

**Status Workflow:**
Received → In Conditioning → Ready for Test → Testing → Test Complete → Returned/Disposed

### 2. Test Model (`test.py`)

Represents individual test executions.

**Key Features:**
- Test type classification (per IEC standards)
- Test execution tracking
- Equipment association
- Environmental conditions
- Measurement data storage (JSON)
- Pass/fail assessment
- Uncertainty calculation support
- Data file references

**Test Types (IEC 61215-2021):**
- Visual Inspection (MST 01)
- Performance at STC (MST 02)
- Insulation Test (MST 03)
- Temperature Coefficients (MST 04)
- NOCT (MST 05)
- Low Irradiance Performance (MST 06)
- Outdoor Exposure (MST 07)
- Hot-Spot Endurance (MST 08)
- UV Preconditioning/Test (MST 09)
- Thermal Cycling (MST 10)
- Humidity-Freeze (MST 11)
- Damp Heat (MST 12)
- Mechanical Load Test (MST 13)
- Hail Test (MST 14)
- Bypass Diode (MST 15)
- Wet Leakage Current (MST 16)
- Plus advanced tests (EL, IR, PID, etc.)

### 3. User Model (`user.py`)

Implements RBAC (Role-Based Access Control).

**Key Features:**
- User authentication with password hashing
- Role-based permissions
- Electronic signature support (21 CFR Part 11)
- API key management
- Account security (lockout, password expiry)
- Training and certification tracking

**Roles:**
- Super Admin, Lab Manager, Quality Manager
- Test Engineer, Technician
- Reviewer, Approver
- Viewer, Customer

### 4. Report Model (`report.py`)

Test report generation and management.

**Key Features:**
- IEC 61215 compliant report structure
- Version control
- Multi-language support
- Section-based content management
- Approval workflow
- Multiple export formats

**Report Status:**
Draft → Under Review → Approved → Issued

### 5. Audit Model (`audit.py`)

Immutable audit trail and data lineage.

**Key Features:**
- Complete CRUD operation logging
- User action tracking
- Change history (old/new values)
- Cryptographic hash chain for integrity
- Data provenance tracking
- Compliance with 21 CFR Part 11

### 6. Equipment Model (`equipment.py`)

Equipment inventory and calibration tracking.

**Key Features:**
- Equipment identification and specs
- Calibration due date tracking
- Calibration certificate storage
- Measurement uncertainty
- Maintenance history
- Automated alerts for calibration due

**Equipment Types:**
- Solar Simulator
- IV Tracer / Curve Tracer
- Multimeter, Insulation Tester
- Thermal Chamber, Humidity Chamber
- EL Camera, IR Camera
- Pyranometer, Temperature Sensors

## Implementation Guide

### Phase 1: Setup and Configuration

1. **Install Dependencies**
   ```bash
   pip install -r requirements_database.txt
   ```

2. **Configure Database Connection**
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost:5432/pv_automation"
   # Or use SQLite for development:
   export DATABASE_URL="sqlite:///./pv_test_automation.db"
   ```

3. **Initialize Database**
   ```python
   from src.database.base import init_db
   init_db()
   ```

### Phase 2: Database Migration Setup

1. **Initialize Alembic**
   ```bash
   alembic init src/database/migrations
   ```

2. **Configure alembic.ini**
   ```ini
   sqlalchemy.url = postgresql://user:password@localhost:5432/pv_automation
   ```

3. **Create Initial Migration**
   ```bash
   alembic revision --autogenerate -m "Initial schema"
   alembic upgrade head
   ```

### Phase 3: Model Enhancement

1. **Add missing relationships**
   - Test → Equipment (many-to-many)
   - Sample → Protocol
   - User → Department/Organization

2. **Implement model methods**
   - `Sample.calculate_area()`
   - `Test.calculate_uncertainty()`
   - `User.check_password()`
   - `Equipment.is_calibration_valid()`

3. **Add database indexes**
   - Sample: sample_id, manufacturer, status
   - Test: test_id, test_type, status, start_time
   - User: username, email
   - Equipment: equipment_id, status

### Phase 4: Pydantic Schemas

Create Pydantic schemas for API validation:
- `SampleCreate`, `SampleUpdate`, `SampleResponse`
- `TestCreate`, `TestUpdate`, `TestResponse`
- Similar for all models

### Phase 5: Repository Pattern

Implement repository classes for data access:
```python
class SampleRepository:
    def create(self, sample: SampleCreate) -> Sample
    def get_by_id(self, sample_id: UUID) -> Sample
    def list(self, filters: dict) -> List[Sample]
    def update(self, sample_id: UUID, data: SampleUpdate) -> Sample
    def delete(self, sample_id: UUID) -> bool
```

### Phase 6: Testing

1. **Unit Tests**
   - Test each model's creation and validation
   - Test relationships and cascades
   - Test constraints and uniqueness

2. **Integration Tests**
   - Test complete workflows
   - Test with real database
   - Test migrations

3. **Performance Tests**
   - Bulk data insertion
   - Complex queries
   - Index effectiveness

## Database Design Principles

### 1. Normalization
- Properly normalized to 3NF
- Avoid data redundancy
- Use JSON for flexible, non-queryable data

### 2. Integrity
- Foreign key constraints
- Check constraints for enums
- Unique constraints for identifiers
- NOT NULL for required fields

### 3. Audit Trail
- All tables have created_at, updated_at
- Soft delete with deleted_at
- Changes logged to audit_logs table

### 4. Scalability
- UUID primary keys for distributed systems
- Proper indexing strategy
- JSON fields for extensibility

### 5. Compliance
- ISO 17025: Complete traceability
- 21 CFR Part 11: Audit trail, electronic signatures
- NABL: Data integrity, security
- IEC Standards: Test data requirements

## Security Considerations

1. **Password Security**
   - Use bcrypt for password hashing
   - Minimum 12 character passwords
   - Password expiry and history

2. **API Keys**
   - Hash API keys in database
   - Support key rotation
   - Set expiration dates

3. **Data Encryption**
   - Encrypt sensitive fields
   - TLS for database connections
   - Encrypted backups

4. **Access Control**
   - Row-level security (RLS) in PostgreSQL
   - Audit all data access
   - Implement principle of least privilege

## Next Steps

1. Complete Pydantic schema definitions
2. Implement Alembic migrations
3. Add database seeders for test data
4. Create repository classes
5. Add database indexes and optimization
6. Implement full test coverage
7. Add database documentation generation
8. Setup database backup and recovery procedures

## Dependencies

This module integrates with:
- **Session 02**: Config system for database configuration
- **Session 03**: Security module for encryption
- **Session 04**: Audit trail for logging
- **Session 05**: Validation for data validation

## Compliance Mapping

| Requirement | Implementation |
|------------|----------------|
| ISO 17025 5.5.4 (Equipment Records) | Equipment, Calibration models |
| ISO 17025 7.5 (Technical Records) | Test, AuditLog models |
| 21 CFR Part 11 | AuditLog with hash chain |
| NABL 112 | Complete audit trail |
| IEC 61215-2021 | Sample, Test models with all test types |

## Notes

- All timestamps are in UTC
- Use UUIDs for primary keys
- JSON fields use PostgreSQL's JSONB for performance
- SQLite supported for development, PostgreSQL for production
- All models support soft delete
