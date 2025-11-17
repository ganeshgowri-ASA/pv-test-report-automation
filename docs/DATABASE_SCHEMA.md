# Database Schema Documentation

## Overview

The PV Test Report Automation system uses SQLModel (SQLAlchemy + Pydantic) for database modeling, providing type safety, data validation, and ORM capabilities.

## Database Models

### 1. Equipment Model

Manages test equipment inventory, calibration tracking, and uncertainty specifications.

**Table:** `equipment`

#### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | Primary Key, Auto-increment | Unique equipment identifier |
| name | String(200) | Indexed | Equipment name/description |
| model_number | String(100) | Optional | Manufacturer model number |
| serial_number | String(100) | Unique, Indexed | Unique serial number |
| manufacturer | String(200) | Optional | Equipment manufacturer |
| calibration_date | Date | Indexed | Last calibration date |
| calibration_due_date | Date | Indexed | Next calibration due date |
| calibration_interval_days | Integer | Default: 365, >= 1 | Days between calibrations |
| calibration_certificate_number | String(100) | Optional | Calibration certificate reference |
| uncertainty | Float | >= 0 | Measurement uncertainty |
| uncertainty_unit | String(20) | Required | Unit for uncertainty (%, mV, etc.) |
| uncertainty_description | String(500) | Optional | Detailed uncertainty description |
| status | Enum | Indexed | active, calibration_due, out_of_service, maintenance, retired |
| location | String(200) | Optional | Physical location |
| notes | Text | Optional | Additional notes |
| created_at | DateTime | Auto | Record creation timestamp |
| updated_at | DateTime | Auto | Last update timestamp |

#### Relationships

- `tests` → One-to-Many with Test model

#### Indexes

- `ix_equipment_status_calibration`: (status, calibration_due_date)
- `ix_equipment_name_status`: (name, status)

#### Methods

- `is_calibration_valid(test_date)`: Check if calibration is valid for a given date
- `days_until_calibration_due()`: Calculate days until calibration is due
- `update_timestamp()`: Update the updated_at timestamp

---

### 2. User Model

Manages user accounts, roles, permissions, and approval workflows.

**Table:** `users`

#### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | Primary Key, Auto-increment | Unique user identifier |
| username | String(100) | Unique, Indexed | Username for login |
| email | String(255) | Unique, Indexed | User email address |
| password_hash | String(255) | Required | Hashed password |
| full_name | String(200) | Indexed | User's full name |
| employee_id | String(50) | Unique | Employee ID number |
| department | String(100) | Optional | Department/team assignment |
| role | Enum | Indexed | admin, lab_manager, test_engineer, reviewer, approver, quality_manager, viewer |
| status | Enum | Default: active | active, inactive, suspended, pending |
| contact | JSON | Optional | Contact info: phone, mobile, extension, address |
| reviewer_flag | Boolean | Default: False, Indexed | Whether user can perform reviews |
| approver_flag | Boolean | Default: False, Indexed | Whether user can approve reports |
| approval_history | JSON Array | Optional | Array of approval actions |
| signature_image_path | String(500) | Optional | Path to digital signature image |
| qualifications | JSON Array | Optional | Certifications, training, qualifications |
| last_login | DateTime | Optional | Last login timestamp |
| failed_login_attempts | Integer | Default: 0 | Count of failed login attempts |
| account_locked_until | DateTime | Optional | Account lock expiration |
| password_changed_at | DateTime | Optional | Last password change timestamp |
| notes | Text | Optional | Additional notes |
| created_at | DateTime | Auto | Record creation timestamp |
| updated_at | DateTime | Auto | Last update timestamp |

#### Relationships

- `audit_logs` → One-to-Many with Audit model

#### Indexes

- `ix_user_role_status`: (role, status)
- `ix_user_reviewer_approver`: (reviewer_flag, approver_flag)

#### Methods

- `can_review()`: Check if user has review permissions
- `can_approve()`: Check if user has approval permissions
- `is_active()`: Check if user account is active
- `is_locked()`: Check if account is currently locked
- `add_approval_action(report_id, action, comments)`: Add approval action to history
- `record_login(success)`: Record login attempt
- `update_timestamp()`: Update the updated_at timestamp

---

### 3. Sample Model

Manages PV module samples received for testing.

**Table:** `samples`

#### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | Primary Key, Auto-increment | Unique sample identifier |
| sample_number | String(50) | Unique, Indexed | Human-readable sample number |
| sample_type | Enum | Default: module | module, cell, laminate, component |
| protocol | String(200) | Indexed | Test protocol/standard |
| scope | Text | Required | Testing scope and requirements |
| customer_name | String(200) | Indexed | Customer/client name |
| customer_po_number | String(100) | Optional | Customer purchase order |
| customer_contact | JSON | Optional | Customer contact information |
| manufacturer | String(200) | Indexed | Sample manufacturer |
| model_number | String(100) | Indexed | Manufacturer model number |
| serial_numbers | JSON Array | Required | Array of serial numbers |
| quantity | Integer | Default: 1, >= 1 | Number of samples |
| received_date | Date | Indexed | Date sample was received |
| expected_completion_date | Date | Optional | Expected completion date |
| actual_completion_date | Date | Optional | Actual completion date |
| package_images | JSON Array | Optional | Paths to packaging images |
| bom | JSON | Optional | Bill of materials |
| labels | JSON | Optional | Label information |
| nameplate_ratings | JSON | Optional | Electrical ratings |
| physical_dimensions | JSON | Optional | Dimensions and weight |
| storage_location | String(200) | Optional | Storage location |
| status | Enum | Default: received, Indexed | received, in_progress, testing_complete, report_pending, completed, on_hold, returned, disposed |
| special_handling_requirements | Text | Optional | Special handling notes |
| notes | Text | Optional | Additional notes |
| created_at | DateTime | Auto | Record creation timestamp |
| updated_at | DateTime | Auto | Last update timestamp |

#### Relationships

- `tests` → One-to-Many with Test model

#### Indexes

- `ix_sample_customer_status`: (customer_name, status)
- `ix_sample_protocol_status`: (protocol, status)
- `ix_sample_manufacturer_model`: (manufacturer, model_number)

#### Methods

- `is_testing_complete()`: Check if all testing is complete
- `days_in_lab()`: Calculate number of days in lab
- `is_overdue()`: Check if testing is overdue
- `update_status(new_status)`: Update sample status
- `update_timestamp()`: Update the updated_at timestamp

---

### 4. Test Model

Manages individual test execution records with full traceability.

**Table:** `tests`

#### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | Primary Key, Auto-increment | Unique test identifier |
| sample_id | Integer | Foreign Key → samples.id, Indexed | Reference to Sample |
| equipment_id | Integer | Foreign Key → equipment.id, Indexed | Reference to Equipment |
| performed_by_user_id | Integer | Foreign Key → users.id | User who performed test |
| reviewed_by_user_id | Integer | Foreign Key → users.id | User who reviewed test |
| test_number | String(100) | Unique, Indexed | Human-readable test number |
| type | Enum | Indexed | visual_inspection, electrical_performance, insulation_test, thermal_cycling, humidity_freeze, damp_heat, etc. |
| test_standard_reference | String(200) | Required | Reference to test standard |
| description | Text | Optional | Test description |
| test_date | Date | Indexed | Date test was performed |
| start_time | DateTime | Optional | Test start timestamp |
| end_time | DateTime | Optional | Test end timestamp |
| duration_hours | Float | Optional, >= 0 | Test duration in hours |
| calibration_valid | Boolean | Default: True | Equipment calibration validity |
| calibration_certificate_ref | String(100) | Optional | Calibration certificate reference |
| readings | JSON Array | Optional | Measurement readings |
| uncertainty | JSON | Optional | Measurement uncertainty |
| test_conditions | JSON | Optional | Test conditions |
| pass_fail | Enum | Default: pending, Indexed | pass, fail, conditional, not_applicable, pending |
| failure_mode | Text | Optional | Failure description |
| acceptance_criteria | JSON | Optional | Pass/fail criteria |
| results_summary | JSON | Optional | Summary of results |
| status | Enum | Default: scheduled, Indexed | scheduled, in_progress, completed, on_hold, cancelled, failed_execution |
| attachments | JSON Array | Optional | Paths to data files |
| reviewed | Boolean | Default: False | Whether test is reviewed |
| review_date | DateTime | Optional | Review timestamp |
| review_comments | Text | Optional | Review comments |
| notes | Text | Optional | Additional notes |
| deviations | Text | Optional | Deviations from standard |
| created_at | DateTime | Auto | Record creation timestamp |
| updated_at | DateTime | Auto | Last update timestamp |

#### Relationships

- `sample` → Many-to-One with Sample model
- `equipment` → Many-to-One with Equipment model

#### Indexes

- `ix_test_sample_type`: (sample_id, type)
- `ix_test_date_status`: (test_date, status)
- `ix_test_pass_fail_type`: (pass_fail, type)
- `ix_test_equipment_date`: (equipment_id, test_date)

#### Methods

- `calculate_duration()`: Calculate test duration in hours
- `validate_calibration(equipment)`: Validate equipment calibration
- `mark_complete(pass_fail, reviewed_by)`: Mark test as complete
- `add_reading(reading)`: Add a measurement reading
- `update_timestamp()`: Update the updated_at timestamp

---

### 5. Report Model

Manages test reports with workflow and multi-format export.

**Table:** `reports`

#### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | Primary Key, Auto-increment | Unique report identifier |
| report_number | String(100) | Indexed | Human-readable report number |
| revision | Integer | Default: 0, >= 0 | Report revision number |
| type | Enum | Indexed | type_approval, sample_test, factory_inspection, surveillance, witness_test, custom |
| protocol | String(200) | Indexed | Test protocol/standard |
| additional_standards | JSON Array | Optional | Additional standards |
| sample_id | Integer | Foreign Key → samples.id, Indexed | Reference to Sample |
| customer | JSON | Required | Customer information |
| title | String(500) | Required | Report title |
| summary | Text | Optional | Executive summary |
| sections | JSON Array | Required | Report sections |
| tables | JSON Array | Optional | Data tables |
| graphs | JSON Array | Optional | Graph specifications |
| annex_links | JSON Array | Optional | Links to annexes |
| test_ids | JSON Array | Required | Array of test IDs |
| prepared_by_user_id | Integer | Foreign Key → users.id | User who prepared report |
| reviewed_by_user_id | Integer | Foreign Key → users.id | User who reviewed report |
| approved_by_user_id | Integer | Foreign Key → users.id | User who approved report |
| prepared_date | DateTime | Optional | Preparation timestamp |
| reviewed_date | DateTime | Optional | Review timestamp |
| approved_date | DateTime | Optional | Approval timestamp |
| issue_date | DateTime | Optional, Indexed | Issue timestamp |
| status | Enum | Default: draft, Indexed | draft, in_review, reviewed, pending_approval, approved, rejected, issued, revised, cancelled |
| review_history | JSON Array | Optional | Workflow history |
| export_formats | JSON Array | Default: ["pdf"] | Available export formats |
| generated_files | JSON | Optional | Mapping of format to file path |
| template_used | String(200) | Optional | Template identifier |
| metadata | JSON | Optional | Additional metadata |
| signatures | JSON | Optional | Digital signatures |
| parent_report_id | Integer | Foreign Key → reports.id | Reference to previous version |
| revision_reason | Text | Optional | Reason for revision |
| notes | Text | Optional | Additional notes |
| confidentiality_level | String(50) | Default: standard | Confidentiality level |
| created_at | DateTime | Auto | Record creation timestamp |
| updated_at | DateTime | Auto | Last update timestamp |

#### Constraints

- Unique: (report_number, revision)

#### Indexes

- `ix_report_sample_status`: (sample_id, status)
- `ix_report_type_protocol`: (type, protocol)
- `ix_report_issue_date`: (issue_date)

#### Methods

- `get_full_report_number()`: Get report number with revision
- `add_review_entry(user_id, action, comments, status_change)`: Add review history entry
- `submit_for_review(user_id)`: Submit report for review
- `approve_report(user_id, comments)`: Approve report
- `reject_report(user_id, comments)`: Reject report
- `issue_report(user_id)`: Issue approved report
- `create_revision(reason)`: Create new revision
- `add_generated_file(format, file_path)`: Add generated file path
- `update_timestamp()`: Update the updated_at timestamp

---

### 6. Audit Model

Comprehensive audit trail for compliance and traceability.

**Table:** `audit_logs`

#### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | Primary Key, Auto-increment | Unique audit identifier |
| user_id | Integer | Foreign Key → users.id, Indexed | User who performed action |
| action | Enum | Indexed | Action type (create, update, delete, etc.) |
| entity_type | String(50) | Indexed | Type of entity affected |
| entity_id | Integer | Indexed | ID of affected entity |
| branch | String(200) | Optional | Git/workflow branch |
| timestamp | DateTime | Auto, Indexed | When action occurred |
| ip_address | String(45) | Optional | User IP address |
| user_agent | String(500) | Optional | Browser/client user agent |
| session_id | String(100) | Indexed | Session identifier |
| severity | Enum | Default: info | info, warning, error, critical |
| description | String(1000) | Required | Human-readable description |
| pre_snapshot | JSON | Optional | State before change |
| post_snapshot | JSON | Optional | State after change |
| changes | JSON | Optional | Field-level changes |
| success | Boolean | Default: True | Whether action succeeded |
| error_message | Text | Optional | Error message if failed |
| metadata | JSON | Optional | Additional context |
| compliance_relevant | Boolean | Default: True | Compliance relevance flag |
| retention_years | Integer | Default: 10, >= 1 | Retention period |

#### Relationships

- `user` → Many-to-One with User model

#### Indexes

- `ix_audit_user_timestamp`: (user_id, timestamp)
- `ix_audit_entity`: (entity_type, entity_id)
- `ix_audit_action_timestamp`: (action, timestamp)
- `ix_audit_session`: (session_id, timestamp)
- `ix_audit_severity_timestamp`: (severity, timestamp)
- `ix_audit_compliance`: (compliance_relevant, timestamp)

#### Methods

- `calculate_changes(pre, post)`: Calculate field-level changes
- `is_within_retention_period()`: Check retention period
- `log_action(...)`: Create new audit log entry (class method)

---

## Entity Relationships

```
Equipment ──< Test >── Sample
                │
                └──> User (performed_by, reviewed_by)

Sample ──< Test
       └── Report

User ──< Audit
     └── Report (prepared_by, reviewed_by, approved_by)

Report ──> Report (parent_report_id for revisions)
```

## Relationship Details

1. **Equipment → Tests**: One equipment can be used in many tests
2. **Sample → Tests**: One sample can have many tests performed
3. **User → Tests**: Users perform and review tests
4. **User → Reports**: Users prepare, review, and approve reports
5. **User → Audits**: Users generate audit log entries
6. **Sample → Report**: One report per sample
7. **Report → Report**: Reports can have revisions

## JSON Field Structures

### Sample.bom (Bill of Materials)
```json
{
  "cells": "M10 monocrystalline PERC",
  "glass_front": "3.2mm tempered AR coated",
  "glass_back": "2.0mm tempered",
  "encapsulant": "POE",
  "frame": "Anodized aluminum",
  "junction_box": "IP68 rated with bypass diodes"
}
```

### Sample.nameplate_ratings
```json
{
  "pmax": 400,
  "pmax_tolerance": "+5/-0",
  "voc": 49.5,
  "isc": 10.5,
  "vmp": 41.2,
  "imp": 9.71,
  "efficiency": 20.5
}
```

### Test.readings (Array)
```json
[
  {
    "module": "HES400-001",
    "voc": 49.52,
    "isc": 10.48,
    "pmax": 402.5,
    "vmp": 41.18,
    "imp": 9.77,
    "ff": 77.5,
    "timestamp": "2024-01-17T10:30:00"
  }
]
```

### User.approval_history (Array)
```json
[
  {
    "report_id": 123,
    "action": "approved",
    "timestamp": "2024-01-20T14:30:00",
    "comments": "All requirements met"
  }
]
```

### Audit.changes
```json
{
  "pass_fail": {
    "old": "pending",
    "new": "pass"
  },
  "status": {
    "old": "in_progress",
    "new": "completed"
  }
}
```

## Database Initialization

```python
from database import init_db

# Initialize with SQLite (default)
db_config = init_db()

# Initialize with PostgreSQL
db_config = init_db(
    database_url="postgresql://user:pass@localhost/pvtestlab",
    echo=True
)
```

## Usage Example

```python
from database import get_session
from database.models import Sample, Test, Equipment

with get_session() as session:
    # Create a sample
    sample = Sample(
        sample_number="S-2024-001",
        protocol="IEC 61215-2:2021",
        # ... other fields
    )
    session.add(sample)
    session.commit()

    # Query samples
    samples = session.query(Sample).filter(
        Sample.status == SampleStatus.IN_PROGRESS
    ).all()
```

## Migration Support

Database migrations are managed using Alembic. See the `alembic/` directory for migration scripts.

```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Compliance and Quality

This database schema supports compliance with:

- **ISO/IEC 17025:2017**: General requirements for testing and calibration laboratories
- **ISO 9001:2015**: Quality management systems
- **NABL**: National Accreditation Board for Testing and Calibration Laboratories
- **ILAC**: International Laboratory Accreditation Cooperation

Key compliance features:

1. **Full Audit Trail**: Every action logged with user, timestamp, and changes
2. **Calibration Tracking**: Equipment calibration validity enforced
3. **Review Workflows**: Multi-level review and approval processes
4. **Traceability**: Complete chain from sample to test to report
5. **Data Integrity**: Constraints, validations, and relationships ensure data quality
6. **Retention Policies**: Configurable retention periods for audit logs
