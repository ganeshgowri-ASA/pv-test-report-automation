# pv-test-report-automation
World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## Features

### Equipment Database & Tracking System

Comprehensive ISO/IEC 17025 compliant equipment management system for PV test laboratories:

- **Equipment Registry**: Complete database of IV tracers, climate chambers, meters, and all test equipment
- **Usage Tracking**: Checkout/checkin system with full usage history and accountability
- **Calibration Management**: Full calibration tracking with traceability to national standards (NIST, PTB, etc.)
- **Maintenance Logs**: Service history, preventive and corrective maintenance tracking
- **Location Tracking**: Real-time equipment location and status
- **Availability Scheduling**: Equipment reservation system to prevent conflicts
- **ISO 17025 Compliance**: Built-in compliance features for laboratory accreditation

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from equipment.database import EquipmentDB
from equipment import Equipment, EquipmentCategory
from datetime import date, timedelta

# Initialize database
db = EquipmentDB("equipment.db")

# Add equipment
equipment = Equipment(
    name="IV Tracer Pro 3000",
    manufacturer="PV Test Systems",
    model="IVT-3000",
    serial_number="IVT3000-2024-001",
    category=EquipmentCategory.IV_TRACER,
    location="Lab A - Bench 1",
    calibration_due_date=date.today() + timedelta(days=365)
)
equipment_id = db.add_equipment(equipment)

# Get available equipment
available = db.get_available(category=EquipmentCategory.IV_TRACER)

# Checkout equipment
log_id = db.checkout(
    equipment_id=equipment_id,
    user_name="Jane Doe",
    test_id=123,
    purpose="PV module testing"
)

# Checkin equipment
db.checkin(equipment_id, condition="good")
```

## Documentation

- [Equipment Management Guide](docs/EQUIPMENT_GUIDE.md) - Complete guide with examples
- [Example Usage](examples/equipment_example.py) - Comprehensive demo script

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ --cov=equipment --cov-report=html
```

## Project Structure

```
pv-test-report-automation/
├── equipment/              # Equipment management system
│   ├── __init__.py
│   ├── models.py          # Data models (Equipment, UsageLog, etc.)
│   └── database.py        # Database interface and operations
├── tests/                 # Test suite
│   ├── __init__.py
│   └── test_equipment.py  # Comprehensive tests
├── docs/                  # Documentation
│   └── EQUIPMENT_GUIDE.md # User guide
├── examples/              # Usage examples
│   └── equipment_example.py
├── requirements.txt       # Dependencies
└── README.md
```

## ISO/IEC 17025 Compliance

The equipment management system is designed to meet ISO/IEC 17025:2017 requirements:

- ✓ Equipment identification and traceability
- ✓ Calibration status monitoring
- ✓ Maintenance records
- ✓ Usage history
- ✓ Traceability to national standards
- ✓ Verification after maintenance
- ✓ Prevents use of out-of-calibration equipment

## License

See [LICENSE](LICENSE) file for details.
