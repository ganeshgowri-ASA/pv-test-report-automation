# Calibration Certificate Management System

ISO 17025 compliant calibration certificate management for PV test laboratory equipment.

## Features

- **Certificate Management**: Upload, parse, and track calibration certificates
- **Due Date Tracking**: Automated alerts for upcoming and overdue calibrations
- **Traceability Chain**: Maintain traceability to national/international standards (NIST, NPL, etc.)
- **Uncertainty Budget**: Track measurement uncertainty with full budget analysis
- **Multi-Standard Support**: NABL, ILAC, A2LA, UKAS, DAkkS, CNAS accreditation
- **Compliance Reporting**: Generate ISO 17025 compliance reports
- **Auto-Flagging**: Automatically flag expired certificates
- **Alert System**: Configurable alerts with severity levels (Info, Warning, Critical, Urgent)

## Installation

```bash
pip install -r requirements.txt
```

For PDF certificate parsing, install optional dependencies:
```bash
pip install PyPDF2  # or pdfplumber
```

## Quick Start

```python
from equipment.calibration import CalibrationManager
from datetime import date

# Initialize manager
cm = CalibrationManager()

# Add certificate manually
cm.add_certificate(
    equipment_id=123,
    cert_number="CAL-2025-001",
    calibration_date=date(2025, 1, 1),
    due_date=date(2026, 1, 1),
    calibration_lab="ABC Calibration Lab",
    accreditation_body="NABL",
    uncertainty=0.05,
    traceability_chain="NIST"
)

# Or parse from PDF file
from pathlib import Path
cm.add_certificate(
    equipment_id=123,
    cert_file=Path("certificate.pdf")
)

# Get certificates due soon
alerts = cm.get_due_soon(days=30)
print(f"Found {len(alerts)} certificates due in next 30 days")

# Get critical alerts
critical = cm.get_critical_alerts()
for alert in critical:
    print(alert.message)

# Generate compliance report
report = cm.generate_compliance_report()
print(report)

# Export reports
cm.export_compliance_report("compliance_report.txt")
cm.export_alerts_report("alerts.txt")
```

## Certificate Parsing

The system can automatically parse calibration certificates from PDF or text files:

```python
from pathlib import Path

# Automatic parsing
cert = cm.add_certificate(
    equipment_id=123,
    cert_file=Path("cert.pdf")
)

# Override parsed values
cert = cm.add_certificate(
    equipment_id=123,
    cert_file=Path("cert.pdf"),
    cert_number="OVERRIDE-001",  # Override parsed cert number
    uncertainty=0.08  # Override parsed uncertainty
)
```

## Alert System

Alerts are generated automatically based on due dates:

- **Info** (30-16 days before due): Informational notification
- **Warning** (15-8 days before due): Warning notification
- **Critical** (7-2 days before due): Critical action required
- **Urgent** (1-0 days or overdue): Immediate action required

```python
# Get all critical alerts
critical = cm.get_critical_alerts()

# Get alerts by severity
from equipment.calibration import AlertSeverity
warnings = cm.get_alerts(severity=AlertSeverity.WARNING)

# Acknowledge an alert
cm.acknowledge_alert(alert_id=1, user="john.doe")

# Generate email report
report = cm.alert_manager.generate_email_report()
```

## Traceability Chain

Track complete traceability to national standards:

```python
from equipment.calibration.models import TraceabilityChain

chain = TraceabilityChain(
    primary_standard="NIST",
    intermediate_standards=["Primary Lab", "Secondary Lab"],
    reference_certificate="REF-2025-001",
    uncertainty_propagation=[0.01, 0.02, 0.05]
)

# Validate traceability
is_valid = cm.validate_traceability(cert_id=1)
print(f"Traceability valid: {is_valid['valid']}")
```

## Uncertainty Budget

Comprehensive uncertainty tracking:

```python
from equipment.calibration.models import UncertaintyBudget, UncertaintyType

budget = UncertaintyBudget(
    value=0.05,
    unit="V",
    uncertainty_type=UncertaintyType.EXPANDED,
    coverage_factor=2.0,
    confidence_level=0.95,
    components={
        "type_a_repeatability": 0.02,
        "type_b_resolution": 0.01,
        "type_b_stability": 0.015,
        "type_b_standard": 0.03
    }
)
```

## Calibration History

Track complete calibration history for each equipment:

```python
# Get history for equipment
history = cm.get_calibration_history(equipment_id=123)
for entry in history:
    print(f"{entry['action_date']}: {entry['action']} by {entry['performed_by']}")

# Get all certificates for equipment
certs = cm.get_certificates_for_equipment(equipment_id=123)
for cert in certs:
    print(f"{cert.calibration_date}: {cert.cert_number}")
```

## Statistics and Reporting

```python
# Get statistics
stats = cm.get_statistics()
print(f"Total certificates: {stats['total_certificates']}")
print(f"Valid: {stats['valid']}, Expired: {stats['expired']}")
print(f"Due in 30 days: {stats['due_soon_30']}")

# Generate compliance report
report = cm.generate_compliance_report()

# Export to file
cm.export_compliance_report("iso17025_compliance.txt")
```

## Database

The system uses SQLite for data persistence:

- `calibration_certificates`: Main certificate table
- `equipment`: Equipment registry
- `calibration_history`: Audit trail

All operations are ACID-compliant with proper indexing for performance.

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest tests/equipment/test_calibration.py -v

# Run with coverage
python -m pytest tests/equipment/test_calibration.py --cov=equipment.calibration

# Run specific test class
python -m pytest tests/equipment/test_calibration.py::TestCalibrationManager -v
```

## ISO 17025 Compliance

This system supports ISO 17025:2017 requirements:

- **6.4.6**: Records of calibration certificates
- **6.4.13**: Traceability to measurement standards
- **6.5**: Metrological traceability
- **7.8.2.1**: Calibration certificates
- **7.8.6**: Reporting measurement uncertainty

## Accreditation Bodies Supported

- NABL (National Accreditation Board, India)
- ILAC (International Laboratory Accreditation Cooperation)
- A2LA (American Association for Laboratory Accreditation)
- UKAS (United Kingdom Accreditation Service)
- DAkkS (Deutsche Akkreditierungsstelle, Germany)
- CNAS (China National Accreditation Service)
- ENAS (Emirates National Accreditation System)

## API Reference

See inline documentation in source files:
- `models.py`: Data models
- `manager.py`: Main CalibrationManager class
- `database.py`: Database operations
- `parser.py`: Certificate parsing
- `alerts.py`: Alert management

## License

See LICENSE file in repository root.
