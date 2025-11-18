# Audit Trail & Data Lineage System

**ISO 17025 & 21 CFR Part 11 Compliant**

A production-ready audit trail and data lineage tracking system for the PV Test Report Automation platform. This system provides complete traceability from raw equipment measurements to final test reports, with immutable audit logging and blockchain-style integrity verification.

## Features

### 🔒 Immutable Audit Trail
- **Blockchain-style hash chaining** using SHA-256
- **Tamper-evident logging** - any modification is immediately detectable
- **Event sourcing pattern** for complete history
- **PostgreSQL triggers** enforce immutability at database level
- **No updates or deletes** - audit events are write-once

### 📊 Data Lineage Tracking
- **Complete traceability** from raw equipment output → parsed data → calculations → report sections
- **Parent-child relationships** with version control
- **Bidirectional tracing** (forward and backward)
- **Impact analysis** - understand what's affected by data changes
- **Support for complex lineage graphs** (multiple sources, branching)

### 📋 Compliance Reporting
- **ISO 17025 assessment reports**
- **Export formats**: CSV, JSON, PDF
- **Advanced search and filtering**
- **Security issue detection**
- **Compliance dashboard** with statistics
- **GDPR compliance** features

### ✅ Integrity Verification
- **Hash chain verification**
- **Sequence integrity checks**
- **Timestamp ordering validation**
- **Data hash verification**
- **Referential integrity checks**
- **Digital signature support**
- **Comprehensive integrity scoring**

## Architecture

```
src/audit/
├── trail_logger.py          # Immutable audit log with hash chaining
├── lineage_tracker.py       # Data lineage tracking
├── compliance_reporter.py   # Audit reports and analytics
└── integrity_checker.py     # Integrity verification

migrations/
└── versions/
    └── 001_initial_audit_tables.py  # PostgreSQL schema with triggers

tests/audit/
├── test_trail_logger.py
├── test_lineage_tracker.py
├── test_compliance_reporter.py
└── test_integrity_checker.py
```

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set database URL
export DATABASE_URL="postgresql://user:password@localhost/pv_test_automation"

# Run migrations
alembic upgrade head
```

### Basic Usage

#### 1. Audit Trail Logging

```python
from src.audit import AuditTrailLogger, AuditEvent, AuditEventType

# Initialize logger
logger = AuditTrailLogger(db_url="postgresql://...")

# Log a simple event
event = AuditEvent(
    event_type=AuditEventType.REPORT_APPROVE,
    entity_type="Report",
    entity_id="RPT-001",
    user_id="user123",
    user_name="John Doe",
    action="Approved PV test report",
    reason="All test criteria met per IEC 61215"
)
logger.log(event)

# Log CRUD operations
logger.log_crud(
    operation="UPDATE",
    entity_type="Report",
    entity_id="RPT-001",
    user_id="user123",
    user_name="John Doe",
    old_values={"status": "draft"},
    new_values={"status": "approved"},
    reason="Technical review completed"
)

# Log authentication events
logger.log_auth(
    event_type=AuditEventType.LOGIN,
    user_id="user123",
    user_name="John Doe",
    success=True,
    ip_address="192.168.1.100"
)

# Log security events
logger.log_security_event(
    event_type=AuditEventType.UNAUTHORIZED_ACCESS,
    user_id="hacker",
    user_name="Unknown",
    description="Attempted to access restricted API endpoint",
    severity="CRITICAL",
    ip_address="10.0.0.50"
)
```

#### 2. Data Lineage Tracking

```python
from src.audit import DataLineageTracker, DataNode, DataNodeType, RelationshipType

# Initialize tracker
tracker = DataLineageTracker(db_url="postgresql://...")

# Create source data node (raw equipment output)
raw_data = DataNode(
    node_type=DataNodeType.RAW_EQUIPMENT_OUTPUT,
    name="IV Curve Raw Data - Module A",
    created_by="user123",
    source_system="Keysight B1500A",
    source_file="/data/measurements/2024-01-15/iv_curve_001.csv",
    data_value={
        "voltage": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
        "current": [9.2, 9.1, 9.0, 8.8, 8.5, 7.5, 0.0]
    }
)
raw_id = tracker.create_node(raw_data)

# Create parsed data node
parsed_data = DataNode(
    node_type=DataNodeType.PARSED_DATA,
    name="IV Curve Parameters",
    created_by="user123",
    data_value={
        "voc": 0.65,  # Open circuit voltage
        "isc": 9.2,   # Short circuit current
        "vmp": 0.54,  # Voltage at max power
        "imp": 8.8    # Current at max power
    }
)
parsed_id = tracker.create_node(parsed_data)

# Link raw data to parsed data
tracker.create_relationship(
    parent_id=raw_id,
    child_id=parsed_id,
    relationship_type=RelationshipType.DERIVED_FROM,
    created_by="user123",
    transformation_function="parse_iv_curve",
    transformation_params={"smoothing": "savitzky_golay"}
)

# Create calculated value
efficiency = DataNode(
    node_type=DataNodeType.CALCULATED_VALUE,
    name="Module Efficiency",
    created_by="user123",
    data_value={
        "efficiency_percent": 18.5,
        "area_cm2": 15625,
        "irradiance_w_m2": 1000
    }
)
eff_id = tracker.create_node(efficiency)

# Link to calculation
tracker.create_relationship(
    parent_id=parsed_id,
    child_id=eff_id,
    relationship_type=RelationshipType.CALCULATED_FROM,
    created_by="user123",
    transformation_function="calculate_efficiency",
    transformation_params={"area_cm2": 15625}
)

# Trace lineage backward from efficiency to source
lineage = tracker.trace_lineage(eff_id, direction="backward")
print(f"Found {len(lineage['nodes'])} nodes in lineage")
print(f"Relationships: {len(lineage['relationships'])}")

# Get original source data
sources = tracker.get_source_nodes(eff_id)
for source in sources:
    print(f"Source: {source.name} from {source.source_system}")

# Impact analysis - what's affected if we change parsed_data?
impact = tracker.get_impact_analysis(parsed_id)
print(f"Changing this node would impact {impact['total_impacted']} downstream nodes")
```

#### 3. Compliance Reporting

```python
from datetime import datetime, timedelta
from src.audit import ComplianceReporter

reporter = ComplianceReporter(db_url="postgresql://...")

# Get statistics for the last 30 days
stats = reporter.get_statistics(days=30)
print(f"Total events: {stats.total_events}")
print(f"Unique users: {stats.unique_users}")
print(f"Security events: {stats.security_events}")

# Generate monthly audit report
report = reporter.generate_audit_report(
    period_start=datetime(2024, 1, 1),
    period_end=datetime(2024, 1, 31),
    title="January 2024 Audit Report",
    generated_by="auditor@company.com",
    description="Monthly audit report for ISO 17025 compliance"
)

# Export to PDF
pdf_bytes = reporter.export_report_pdf(report)
with open("audit_report_jan_2024.pdf", "wb") as f:
    f.write(pdf_bytes)

# Search audit events
events, total = reporter.search_events(
    query="report approval",
    event_types=["REPORT_APPROVE", "REPORT_SIGN"],
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31),
    limit=100
)

# Export to CSV
csv_data = reporter.export_csv(events)
with open("audit_events.csv", "w") as f:
    f.write(csv_data)

# Get compliance dashboard
dashboard = reporter.get_compliance_dashboard(days=30)
print(f"Compliance status: {dashboard['compliance_status']}")

# Detect security issues
issues = reporter.detect_security_issues(days=7)
for issue in issues:
    print(f"{issue['severity']}: {issue['description']}")
```

#### 4. Integrity Verification

```python
from src.audit import IntegrityChecker

checker = IntegrityChecker(db_url="postgresql://...")

# Verify hash chain integrity
result = checker.verify_hash_chain()
if result.passed:
    print("✓ Hash chain integrity verified")
else:
    print(f"✗ Hash chain broken! {result.issues_found} issues found")
    for issue in result.issues:
        print(f"  - {issue.description}")

# Run full integrity check
report = checker.run_full_integrity_check(
    generated_by="admin@company.com",
    include_data_hashes=True
)

print(f"Overall status: {report.overall_status}")
print(f"Checks passed: {report.checks_passed}/{report.total_checks}")
print(f"Critical issues: {len(report.critical_issues)}")

if report.critical_issues:
    print("\nCritical Issues:")
    for issue in report.critical_issues:
        print(f"  - {issue.description}")

# Get integrity score (0-100)
score = checker.get_integrity_score()
print(f"Integrity score: {score}/100")

# Verify specific checks
seq_result = checker.verify_sequence_integrity()
ts_result = checker.verify_timestamp_ordering()
data_result = checker.verify_data_hashes(limit=1000)
ref_result = checker.verify_referential_integrity()
```

## Database Schema

### audit_events Table
- **id**: UUID primary key
- **sequence_number**: Sequential integer (unique, immutable)
- **timestamp**: Event timestamp
- **event_type**: Type of event (CREATE, UPDATE, LOGIN, etc.)
- **entity_type**, **entity_id**: What was affected
- **user_id**, **user_name**, **user_role**: Who performed the action
- **ip_address**, **user_agent**, **session_id**: Where
- **action**, **description**, **reason**: What and why
- **old_values**, **new_values**: Change tracking (JSON)
- **previous_hash**, **event_hash**: Hash chain (SHA-256)
- **retention_until**: GDPR compliance
- **metadata**: Additional context (JSON)

### lineage_nodes Table
- **id**: UUID primary key
- **node_type**: Type of data node
- **name**, **description**: Human-readable info
- **version**, **version_group_id**: Version control
- **created_at**, **created_by**: Creation tracking
- **data_value**: The actual data (JSON)
- **data_hash**: SHA-256 of data_value
- **source_system**, **source_file**, **source_location**: Origin
- **quality_score**, **validation_status**: Quality metrics
- **entity_type**, **entity_id**: Business entity link

### lineage_relationships Table
- **id**: UUID primary key
- **relationship_type**: Type of relationship
- **parent_id**, **child_id**: Node references
- **transformation_type**, **transformation_function**: How derived
- **transformation_params**: Transformation parameters (JSON)
- **created_at**, **created_by**: Creation tracking

### PostgreSQL Triggers
1. **audit_events_immutable**: Prevents UPDATE/DELETE on audit_events
2. **audit_events_validate_chain**: Validates hash chain on INSERT
3. **lineage_nodes_change_trigger**: Logs lineage changes

## Security & Compliance

### ISO 17025 Compliance
- ✅ Complete traceability of all measurements and calculations
- ✅ Audit trail of all changes to test reports
- ✅ User authentication and authorization logging
- ✅ Equipment calibration and maintenance tracking capability
- ✅ Data integrity verification

### 21 CFR Part 11 Compliance
- ✅ Secure, computer-generated, time-stamped audit trails
- ✅ Immutable records (cannot be modified or deleted)
- ✅ Operator authentication and authorization
- ✅ Device and system checks for validity
- ✅ Education, training, and experience documentation capability

### GDPR Compliance
- ✅ Data retention policies
- ✅ Right to access (export user's audit events)
- ✅ Right to erasure (anonymization support)
- ✅ Data portability (CSV/JSON export)

## Performance Considerations

### Indexes
The system includes comprehensive indexes for:
- Time-based queries
- User-based queries
- Entity-based queries
- Event type filtering
- Hash chain verification

### Optimization Tips
1. **Partition audit_events** by month for large datasets
2. **Archive old events** according to retention policy
3. **Use connection pooling** for high concurrency
4. **Batch operations** when creating many lineage nodes
5. **Limit lineage depth** when tracing very large graphs

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test module
pytest tests/audit/test_trail_logger.py

# Run with coverage
pytest --cov=src/audit tests/

# Run integration tests (requires PostgreSQL)
TEST_DATABASE_URL="postgresql://..." pytest tests/
```

## Migration Guide

### Running Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current version
alembic current

# Show migration history
alembic history
```

### Production Deployment

1. **Set environment variables**:
   ```bash
   export DATABASE_URL="postgresql://user:password@host/database"
   export AUDIT_RETENTION_DAYS="2555"  # 7 years for ISO 17025
   ```

2. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

3. **Initialize audit logger in application**:
   ```python
   from src.audit import AuditTrailLogger

   audit_logger = AuditTrailLogger(
       db_url=os.getenv("DATABASE_URL"),
       auto_create_tables=False  # Tables created by migrations
   )
   ```

4. **Set up periodic integrity checks**:
   ```python
   # Run daily integrity check
   from src.audit import IntegrityChecker

   checker = IntegrityChecker(db_url=os.getenv("DATABASE_URL"))
   report = checker.run_full_integrity_check(generated_by="system")

   if report.overall_status != "PASS":
       # Alert administrators
       send_alert(report)
   ```

## API Reference

See individual module documentation:
- [trail_logger.py](src/audit/trail_logger.py) - Audit trail logging
- [lineage_tracker.py](src/audit/lineage_tracker.py) - Data lineage tracking
- [compliance_reporter.py](src/audit/compliance_reporter.py) - Compliance reporting
- [integrity_checker.py](src/audit/integrity_checker.py) - Integrity verification

## Contributing

1. All changes must maintain backward compatibility
2. Add tests for new features
3. Update documentation
4. Run integrity checks before committing
5. Follow ISO 17025 and 21 CFR Part 11 requirements

## License

See LICENSE file.

## Support

For issues and questions, please contact the development team.
