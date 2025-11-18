# Equipment Management System Guide

## Overview

The Equipment Management System provides comprehensive tracking and management of test laboratory equipment in compliance with ISO/IEC 17025:2017 standards.

## Features

- **Equipment Registry**: Complete equipment database with detailed specifications
- **Usage Tracking**: Checkout/checkin system with usage history
- **Calibration Management**: Full calibration tracking with traceability
- **Maintenance Logs**: Comprehensive maintenance and service history
- **Availability Scheduling**: Equipment reservation system
- **ISO 17025 Compliance**: Built-in compliance features for laboratory accreditation

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from equipment.database import EquipmentDB
from equipment.models import Equipment, EquipmentCategory
from datetime import date, timedelta

# Initialize database
db = EquipmentDB("lab_equipment.db")

# Add new equipment
equipment = Equipment(
    name="IV Tracer Pro 3000",
    manufacturer="PV Test Systems",
    model="IVT-3000",
    serial_number="IVT3000-2024-001",
    category=EquipmentCategory.IV_TRACER,
    location="Lab A - Bench 1",
    calibration_due_date=date.today() + timedelta(days=365),
    specifications={
        "voltage_range": "0-1500V",
        "current_range": "0-20A",
        "accuracy": "±0.5%"
    }
)

equipment_id = db.add_equipment(equipment)
print(f"Equipment added with ID: {equipment_id}")
```

## Core Operations

### Equipment Management

#### Adding Equipment

```python
from equipment import Equipment, EquipmentCategory, EquipmentStatus
from datetime import date, timedelta

# Create equipment object
equipment = Equipment(
    name="Climate Chamber XL",
    manufacturer="Environmental Systems Inc",
    model="CC-XL-2000",
    serial_number="CC-2024-001",
    category=EquipmentCategory.CLIMATE_CHAMBER,
    location="Lab B",
    status=EquipmentStatus.AVAILABLE,
    calibration_due_date=date.today() + timedelta(days=180),
    calibration_interval_days=180,
    specifications={
        "temperature_range": "-40°C to +150°C",
        "humidity_range": "10% to 98% RH",
        "volume": "1000L"
    },
    accuracy="±0.5°C, ±2% RH",
    purchase_date=date(2024, 1, 15),
    purchase_cost=45000.00,
    responsible_person="Dr. Jane Smith",
    asset_tag="AST-CC-001"
)

equipment_id = db.add_equipment(equipment)
```

#### Retrieving Equipment

```python
# Get specific equipment
equipment = db.get_equipment(equipment_id)
print(f"Equipment: {equipment.name}")
print(f"Status: {equipment.status}")
print(f"Location: {equipment.location}")

# List all equipment
all_equipment = db.list_equipment()

# Filter by category
iv_tracers = db.list_equipment(category=EquipmentCategory.IV_TRACER)

# Filter by status
available = db.list_equipment(status=EquipmentStatus.AVAILABLE)

# Get available equipment by category
available_tracers = db.get_available(category=EquipmentCategory.IV_TRACER)
```

#### Updating Equipment

```python
# Update single field
db.update_equipment(equipment_id, location="Lab C - Bench 3")

# Update multiple fields
db.update_equipment(
    equipment_id,
    location="Lab C",
    responsible_person="Dr. John Doe",
    notes="Upgraded firmware to v2.1"
)
```

### Usage Tracking

#### Checkout Equipment

```python
# Checkout equipment for use
log_id = db.checkout(
    equipment_id=equipment_id,
    user_name="Jane Doe",
    test_id=12345,
    purpose="PV module performance testing",
    location_used="Test Field A"
)

print(f"Equipment checked out. Log ID: {log_id}")
```

#### Checkin Equipment

```python
# Return equipment in good condition
db.checkin(
    equipment_id=equipment_id,
    condition="good"
)

# Return equipment with issues
db.checkin(
    equipment_id=equipment_id,
    condition="damaged",
    issues_reported="Display flickering, needs repair"
)
# Note: Equipment status automatically set to MAINTENANCE when issues reported
```

#### View Usage History

```python
# Get usage history for specific equipment
history = db.get_usage_history(equipment_id=equipment_id)

for log in history:
    print(f"User: {log.user_name}")
    print(f"Checkout: {log.checkout_time}")
    print(f"Checkin: {log.checkin_time}")
    if log.usage_duration:
        print(f"Duration: {log.usage_duration:.2f} hours")
    print("---")

# Filter by date range
from datetime import date
history = db.get_usage_history(
    equipment_id=equipment_id,
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31)
)

# Filter by user
user_history = db.get_usage_history(user_name="Jane Doe")
```

### Calibration Management (ISO 17025)

#### Adding Calibration Record

```python
from equipment import CalibrationRecord
from datetime import date, timedelta

# Create calibration record
record = CalibrationRecord(
    equipment_id=equipment_id,
    calibration_date=date.today(),
    next_calibration_due=date.today() + timedelta(days=365),

    # ISO 17025 Requirements
    calibration_lab="NIST Traceable Calibration Lab",
    lab_accreditation="ISO/IEC 17025:2017 #A2LA-12345",
    certificate_number="CAL-2024-IV-001",
    traceability="NIST",
    standard_used="NIST Reference Standard RS-IV-2024",

    # Calibration Results
    calibration_results={
        "voltage_accuracy": "±0.48%",
        "current_accuracy": "±0.49%",
        "measurement_points": 10,
        "all_points_within_spec": True
    },
    measurement_uncertainty={
        "voltage": "±0.1%",
        "current": "±0.1%"
    },
    pass_fail=True,

    # Environmental Conditions
    temperature=23.5,
    humidity=45.0,

    # Personnel
    performed_by="John Smith, Senior Calibration Technician",
    verified_by="Dr. Jane Doe",

    # Documentation
    certificate_path="/docs/calibrations/CAL-2024-IV-001.pdf",
    notes="Annual calibration performed per procedure CAL-PRO-001"
)

record_id = db.add_calibration_record(record)
print(f"Calibration record added: {record_id}")
```

#### View Calibration History

```python
# Get calibration history
history = db.get_calibration_history(equipment_id)

for record in history:
    print(f"Date: {record.calibration_date}")
    print(f"Certificate: {record.certificate_number}")
    print(f"Lab: {record.calibration_lab}")
    print(f"Result: {'PASS' if record.pass_fail else 'FAIL'}")
    print(f"Next Due: {record.next_calibration_due}")
    print("---")
```

#### Check Calibration Due

```python
# Get equipment with calibration due in next 30 days
due_soon = db.get_calibration_due(days_ahead=30)

print(f"Equipment requiring calibration in next 30 days: {len(due_soon)}")
for equip in due_soon:
    print(f"- {equip.name} ({equip.serial_number})")
    print(f"  Due: {equip.calibration_due_date}")

    # Check if overdue
    days_until = (equip.calibration_due_date - date.today()).days
    if days_until < 0:
        print(f"  ⚠️ OVERDUE by {abs(days_until)} days")
    else:
        print(f"  Due in {days_until} days")
```

### Maintenance Management

#### Adding Maintenance Log

```python
from equipment import MaintenanceLog, MaintenanceType
from datetime import date, timedelta

# Preventive maintenance
log = MaintenanceLog(
    equipment_id=equipment_id,
    maintenance_type=MaintenanceType.PREVENTIVE,

    # Scheduling
    scheduled_date=date.today(),
    completed_date=date.today(),

    # Details
    performed_by="Maintenance Team - ABC Service Co",
    description="Annual preventive maintenance including cleaning, lubrication, and functional testing",

    # Parts and Cost
    parts_replaced=["Air filter", "Temperature sensor"],
    cost=850.00,

    # Verification (ISO 17025 requirement)
    verification_performed=True,
    verification_results="All functional tests passed. Temperature accuracy verified within ±0.3°C",

    # Next Maintenance
    next_maintenance_due=date.today() + timedelta(days=180),

    # Documentation
    attachments=[
        "/docs/maintenance/PM-2024-001-report.pdf",
        "/docs/maintenance/PM-2024-001-invoice.pdf"
    ],
    notes="Replaced temperature sensor due to drift detected during verification"
)

log_id = db.add_maintenance_log(log)
```

#### Corrective Maintenance

```python
# Corrective maintenance (repair)
log = MaintenanceLog(
    equipment_id=equipment_id,
    maintenance_type=MaintenanceType.CORRECTIVE,
    scheduled_date=date.today(),
    completed_date=date.today(),
    performed_by="In-house technician",
    description="Repaired display flickering issue",
    parts_replaced=["Display controller board"],
    cost=425.00,
    verification_performed=True,
    verification_results="Display functioning normally. All menus accessible."
)

db.add_maintenance_log(log)

# Update equipment status back to available
db.update_status(equipment_id, EquipmentStatus.AVAILABLE)
```

#### View Maintenance History

```python
# Get maintenance history
history = db.get_maintenance_history(equipment_id)

for log in history:
    print(f"Date: {log.scheduled_date}")
    print(f"Type: {log.maintenance_type}")
    print(f"Description: {log.description}")
    print(f"Performed by: {log.performed_by}")
    if log.cost:
        print(f"Cost: ${log.cost:.2f}")
    print("---")
```

### Equipment Reservations

#### Making Reservations

```python
from equipment import EquipmentReservation
from datetime import datetime, timedelta

# Reserve equipment
reservation = EquipmentReservation(
    equipment_id=equipment_id,
    reserved_by="Jane Doe",
    test_id=789,
    start_time=datetime.now() + timedelta(hours=2),
    end_time=datetime.now() + timedelta(hours=6),
    purpose="Temperature cycling tests for new module design"
)

try:
    reservation_id = db.add_reservation(reservation)
    print(f"Reservation confirmed: {reservation_id}")
except ValueError as e:
    print(f"Reservation failed: {e}")
```

#### Checking Availability

```python
from datetime import datetime, timedelta

# Check if equipment is available for a time period
start = datetime.now() + timedelta(hours=1)
end = datetime.now() + timedelta(hours=4)

conflicts = db.check_availability(equipment_id, start, end)

if conflicts:
    print("Equipment not available. Conflicting reservations:")
    for conflict in conflicts:
        print(f"- {conflict.reserved_by}: {conflict.start_time} to {conflict.end_time}")
else:
    print("Equipment is available!")
```

#### View Reservations

```python
from datetime import date, timedelta

# Get all reservations for next 7 days
reservations = db.get_reservations(
    start_date=date.today(),
    end_date=date.today() + timedelta(days=7)
)

# Get reservations for specific equipment
equipment_reservations = db.get_reservations(equipment_id=equipment_id)
```

### Status Management

```python
from equipment import EquipmentStatus

# Update equipment status
db.update_status(equipment_id, EquipmentStatus.MAINTENANCE)
db.update_status(equipment_id, EquipmentStatus.CALIBRATION_DUE)
db.update_status(equipment_id, EquipmentStatus.OUT_OF_SERVICE)
db.update_status(equipment_id, EquipmentStatus.AVAILABLE)

# Get all equipment by status
in_maintenance = db.get_equipment_by_status(EquipmentStatus.MAINTENANCE)
calibration_due = db.get_equipment_by_status(EquipmentStatus.CALIBRATION_DUE)
```

### Reporting & Analytics

#### Equipment Utilization

```python
from datetime import date, timedelta

# Calculate utilization for last 30 days
start_date = date.today() - timedelta(days=30)
end_date = date.today()

stats = db.get_equipment_utilization(equipment_id, start_date, end_date)

print(f"Equipment Utilization Report")
print(f"Period: {stats['period_start']} to {stats['period_end']}")
print(f"Total uses: {stats['total_uses']}")
print(f"Total hours: {stats['total_hours']}")
print(f"Utilization: {stats['utilization_percentage']:.1f}%")
print(f"Average use duration: {stats['average_use_duration']:.1f} hours")
```

## ISO/IEC 17025 Compliance

### Required Documentation

The system maintains the following ISO 17025 required records:

1. **Equipment Records**
   - Unique identification (equipment_id, serial_number)
   - Manufacturer and model information
   - Current location
   - Calibration status and history

2. **Calibration Records**
   - Calibration dates and intervals
   - Calibrating laboratory accreditation
   - Certificate numbers
   - Traceability to national/international standards
   - Measurement uncertainty
   - Environmental conditions

3. **Maintenance Records**
   - Scheduled and completed maintenance
   - Parts replaced
   - Verification after maintenance
   - Service provider information

4. **Usage Records**
   - Equipment checkout/checkin tracking
   - User identification
   - Test association
   - Condition reporting

### Compliance Features

#### Preventing Use of Out-of-Calibration Equipment

```python
# System automatically prevents checkout if calibration is overdue
try:
    db.checkout(equipment_id, user_name="User")
except ValueError as e:
    print(f"Cannot use equipment: {e}")
    # Error: "Equipment calibration is overdue"
```

#### Calibration Traceability

```python
# All calibrations must specify traceability
record = CalibrationRecord(
    equipment_id=equipment_id,
    calibration_date=date.today(),
    next_calibration_due=date.today() + timedelta(days=365),

    # Required traceability information
    calibration_lab="Accredited Lab Name",
    lab_accreditation="ISO/IEC 17025:2017 #12345",
    traceability="NIST",  # Or other national standard
    standard_used="Reference standard details",

    # ... other required fields
)
```

#### Verification After Maintenance

```python
# ISO 17025 requires verification after maintenance
log = MaintenanceLog(
    equipment_id=equipment_id,
    maintenance_type=MaintenanceType.CORRECTIVE,
    # ... other fields ...

    # Required verification
    verification_performed=True,
    verification_results="Equipment performance verified within specifications"
)
```

## Best Practices

### 1. Regular Calibration Monitoring

```python
# Daily check for upcoming calibrations
due_soon = db.get_calibration_due(days_ahead=30)
if due_soon:
    print("⚠️ Equipment requiring calibration:")
    for equip in due_soon:
        print(f"- {equip.name}: Due {equip.calibration_due_date}")
```

### 2. Usage Tracking

Always use checkout/checkin for accountability:

```python
# ✅ Good practice
log_id = db.checkout(equipment_id, user_name="Jane Doe", test_id=123)
# ... use equipment ...
db.checkin(equipment_id, condition="good")

# ❌ Avoid: Using equipment without checkout
```

### 3. Document Everything

```python
# Include detailed notes and attachments
log = MaintenanceLog(
    equipment_id=equipment_id,
    # ... other fields ...
    description="Detailed description of work performed",
    notes="Any special observations or recommendations",
    attachments=["/path/to/report.pdf", "/path/to/invoice.pdf"]
)
```

### 4. Report Issues Immediately

```python
# Report issues during checkin
db.checkin(
    equipment_id=equipment_id,
    condition="damaged",
    issues_reported="Specific description of the issue"
)
# Equipment automatically marked for maintenance
```

## API Reference

See the model definitions in `equipment/models.py` for complete field documentation.

### Key Classes

- `Equipment`: Main equipment model
- `EquipmentDB`: Database interface
- `UsageLog`: Usage tracking records
- `CalibrationRecord`: Calibration documentation
- `MaintenanceLog`: Maintenance records
- `EquipmentReservation`: Scheduling records

### Enumerations

- `EquipmentStatus`: available, in_use, maintenance, calibration_due, out_of_service, retired
- `EquipmentCategory`: iv_tracer, climate_chamber, multimeter, pyranometer, power_analyzer, etc.
- `MaintenanceType`: preventive, corrective, calibration, inspection, repair

## Troubleshooting

### Cannot Checkout Equipment

**Error**: "Equipment not available"
- Check equipment status: `db.get_equipment(equipment_id).status`
- Verify equipment is in AVAILABLE status
- Check if equipment is already checked out

**Error**: "Calibration is overdue"
- Add calibration record to update calibration status
- Equipment cannot be used until calibration is current

### Database Issues

If database becomes corrupted:

```python
# Create new database and initialize schema
db = EquipmentDB("equipment_new.db")
# Database schema created automatically
```

## Support

For issues or questions:
- Check this documentation
- Review test cases in `tests/test_equipment.py`
- Examine model definitions in `equipment/models.py`
