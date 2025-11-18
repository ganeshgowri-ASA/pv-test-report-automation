# PV Test Report Automation

World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## Features

- **Automated Test Blocks**: Standardized test implementations per IEC standards
- **Safety Interlocks**: Comprehensive safety systems for high voltage testing
- **ISO 17025 Compliance**: Full traceability, calibration tracking, and quality management
- **Data Validation**: Automated validation of test parameters and environmental conditions
- **Pass/Fail Logic**: Automated determination per standard requirements
- **Multi-Format Export**: JSON, CSV, and database-ready outputs

## Current Implementation

### Wet Leakage Current Test Block

Implementation of IEC 61215-2:2016 and IEC 61730-2:2016 wet leakage current testing.

**Test Conditions:**
- Module immersed for 24 hours in water
- Applied voltage: 1000V DC + 1.2×Voc
- Measurement: Leakage current between frame and active parts
- Pass criteria: <50 μA leakage current
- Duration: Continuous measurement for minimum 2 minutes

**Safety Features:**
- High voltage safety interlocks
- Emergency stop capability
- Automatic limit checking
- Personnel safety verification

**ISO 17025 Compliance:**
- Equipment calibration tracking
- Operator identification
- Environmental condition recording
- Full test traceability

## Installation

```bash
# Clone the repository
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from test_blocks.wet_leakage import WetLeakageTest

# Initialize test
test = WetLeakageTest(module="PV-001")

# Execute measurement
result = test.measure(voltage=1200)

# Check results
print(f"Leakage: {result.leakage_current_ua} μA")
print(f"Status: {'PASS' if result.pass_status else 'FAIL'}")
```

### Automatic Voltage Calculation

```python
from test_blocks.wet_leakage import WetLeakageTest

# Provide module Voc for automatic calculation
test = WetLeakageTest(module="PV-002", module_voc=45.6)

# Voltage will be calculated as 1000V + 1.2×Voc
result = test.measure(
    operator_id="TECH-001",
    equipment_id="HV-SOURCE-001"
)
```

### Full ISO 17025 Compliant Test

```python
from test_blocks.wet_leakage import WetLeakageTest
from datetime import datetime, timedelta

test = WetLeakageTest(
    module="PV-003",
    module_voc=48.2,
    test_id=3003,
    module_id=3003
)

result = test.measure(
    voltage=1100,
    duration_sec=150,
    operator_id="TECH-003",
    equipment_id="HV-SOURCE-002",
    calibration_date=datetime.now() - timedelta(days=180),
    ambient_temp_c=23.5,
    humidity_percent=45.0,
    water_temp_c=20.0,
    water_resistivity_ohm_cm=1000.0,
    notes="Standard wet leakage test per IEC 61215-2:2016"
)

# Export to JSON
import json
print(json.dumps(result.model_dump(), indent=2, default=str))
```

## Examples

Run the comprehensive examples:

```bash
python examples/wet_leakage_example.py
```

This will demonstrate:
1. Basic test execution
2. Automatic voltage calculation
3. Full ISO 17025 compliant testing
4. Batch testing of multiple modules

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html

# Run specific test file
python -m pytest tests/test_wet_leakage.py -v
```

## Project Structure

```
pv-test-report-automation/
├── test_blocks/          # Test block implementations
│   ├── __init__.py
│   └── wet_leakage.py    # Wet leakage current test
├── models/               # Data models
│   ├── __init__.py
│   └── base.py           # Base test model with ISO 17025 fields
├── utils/                # Utilities
│   ├── __init__.py
│   ├── safety.py         # Safety interlocks and HV protection
│   └── validation.py     # ISO 17025 validators
├── examples/             # Usage examples
│   ├── __init__.py
│   └── wet_leakage_example.py
├── tests/                # Test suite
│   ├── __init__.py
│   └── test_wet_leakage.py
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── LICENSE              # License information
```

## Standards Compliance

### IEC 61215-2:2016
- Module design qualification
- Wet leakage current testing procedures
- Pass/fail criteria

### IEC 61730-2:2016
- Module safety qualification
- Electrical safety requirements
- Insulation testing

### ISO 17025:2017
- Testing laboratory competence
- Traceability requirements
- Equipment calibration
- Data integrity

## Safety

**WARNING: This software is designed for use with high voltage equipment.**

- Always verify safety interlocks before testing
- Ensure proper grounding of all equipment
- Follow local electrical safety regulations
- Use qualified personnel only
- Maintain proper calibration records

## Data Model

### WetLeakageTestResult

```python
{
    "test_id": int,              # Unique test identifier
    "module_id": int,            # Module identifier
    "test_date": datetime,       # Test execution timestamp
    "operator_id": str,          # Operator identifier
    "equipment_id": str,         # Equipment identifier
    "calibration_date": datetime,# Equipment calibration date

    "applied_voltage": float,    # Applied voltage (V)
    "module_voc": float,         # Module Voc (V)
    "leakage_current_ua": float, # Leakage current (μA)
    "duration_sec": int,         # Test duration (s)

    "ambient_temp_c": float,     # Ambient temperature (°C)
    "humidity_percent": float,   # Relative humidity (%)
    "water_temp_c": float,       # Water temperature (°C)
    "water_resistivity_ohm_cm": float,  # Water resistivity (Ω·cm)

    "pass_status": bool,         # Overall pass/fail
    "status": str,               # Test status (passed/failed/aborted)
    "notes": str                 # Additional notes
}
```

## Contributing

Contributions are welcome! Please ensure:
1. Code follows PEP 8 style guidelines
2. All tests pass
3. New features include tests
4. Documentation is updated

## License

See LICENSE file for details.

## Support

For issues and questions, please open an issue on GitHub.

## Roadmap

- [ ] Additional test blocks (thermal cycling, humidity-freeze, UV exposure)
- [ ] Database integration for test result storage
- [ ] Web-based dashboard for test monitoring
- [ ] Automated report generation (PDF, Excel)
- [ ] LLM integration for anomaly detection
- [ ] Multi-lab collaboration features
