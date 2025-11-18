# Insulation Resistance Test Block

## Overview

The Insulation Resistance Test Block implements automated testing for measuring electrical insulation resistance of PV modules according to IEC 61215-2:2016 and IEC 61730-2:2016 standards.

## Standards Compliance

- **IEC 61215-2:2016** - Section 10.x: Insulation test
- **IEC 61730-2:2016** - MST 01: Wet leakage current test
- **ISO/IEC 17025:2017** - General requirements for testing laboratories

## Test Procedure

### 1. Wet Soaking
- Module immersion in water for 24 hours
- Temperature: 20°C ± 5°C
- Ensures worst-case insulation conditions

### 2. Test Voltage Application
- Apply DC test voltage: 500V or 1000V
- Voltage selection based on module rating
- Allow 1 minute stabilization time

### 3. Resistance Measurement
- Measure insulation resistance after stabilization
- Test both polarities (positive and negative)
- Record environmental conditions

### 4. Pass/Fail Criteria
- **Wet condition**: Resistance ≥ 40 MΩ
- **Dry condition**: Resistance ≥ 400 MΩ

## Architecture

### Models

#### InsulationTest
```python
class InsulationTest(BaseModel):
    test_id: int              # Sequential test identifier
    module_id: int            # PV module identifier
    test_voltage: int         # 500 or 1000V
    condition: str            # "wet" or "dry"
    resistance_mohm: float    # Measured resistance in MΩ
    polarity: str             # "positive" or "negative"
    pass_status: bool         # Pass/fail status
    timestamp: datetime       # Measurement timestamp
```

### Test Class

#### InsulationResistanceTest
Main test automation class with the following features:

**Initialization**
- Equipment connection (Megohmmeter)
- Calibration validation
- Test block setup
- Audit trail initialization

**Measurement**
- Automated test sequence
- Environmental condition recording
- Real-time pass/fail evaluation
- Data logging

**Finalization**
- Summary generation
- ISO 17025 compliance records
- Equipment disconnection
- Data export

## Equipment Integration

### Supported Instruments
- Fluke 1550C
- Megger MIT1025
- Hioki IR4056
- Generic SCPI-compatible megohmmeters
- Simulated mode for testing

### Connection Methods
- VISA (USB/GPIB/Ethernet)
- Serial (RS-232)
- Simulated (no hardware required)

## Usage Examples

### Basic Usage
```python
from test_blocks.insulation import InsulationResistanceTest

# Create test instance
test = InsulationResistanceTest(module="PV-001", operator="John Doe")

# Initialize
test.initialize()

# Measure
result = test.measure(voltage=1000, condition="wet")

# Check result
print(f"Resistance: {result.test.resistance_mohm} MΩ")
print(f"Status: {'PASS' if result.test.pass_status else 'FAIL'}")

# Finalize
summary = test.finalize()
```

### Full Test Sequence
```python
# Test both polarities automatically
results = test.run_full_test_sequence(
    voltage=1000,
    condition="wet",
    test_both_polarities=True
)

for result in results:
    print(f"{result.test.polarity}: {result.test.resistance_mohm} MΩ")
```

### Context Manager
```python
# Automatic initialization and cleanup
with InsulationResistanceTest(module="PV-001") as test:
    result = test.measure(voltage=1000, condition="wet")
# Equipment automatically disconnected
```

### With Environmental Conditions
```python
from models.measurement import EnvironmentalConditions

env = EnvironmentalConditions(
    temperature_c=25.0,
    humidity_percent=50.0,
    pressure_hpa=1013.25
)

result = test.measure(
    voltage=1000,
    condition="wet",
    environmental_conditions=env
)
```

## Data Logging

### Structured JSON Logs
```json
{
  "test_id": "INSUL-A1B2C3D4",
  "measurement_type": "insulation_resistance",
  "value": 85.5,
  "unit": "MΩ",
  "timestamp": "2024-01-15T10:30:45.123456",
  "voltage": 1000,
  "condition": "wet",
  "pass_status": true
}
```

### CSV Export
Tabular data export for analysis in Excel, Python, R, etc.

### ISO 17025 Records
Complete compliance records including:
- Measurement uncertainty budget
- Equipment calibration chain
- Environmental conditions
- Operator qualifications
- Full audit trail

## Measurement Uncertainty

### Uncertainty Budget Components
1. **Instrument uncertainty**: ±2% (from calibration)
2. **Temperature coefficient**: ±0.5%/°C
3. **Repeatability**: ±1%
4. **Combined uncertainty**: ~2.3%
5. **Expanded uncertainty** (k=2, 95% confidence): ~4.6%

## Test Results

### Summary Output
```python
{
    "test_block_id": "INSUL-A1B2C3D4",
    "module": "PV-001",
    "total_tests": 2,
    "passed": 2,
    "failed": 0,
    "overall_status": "PASS",
    "tests": [...],
    "test_block": {...}
}
```

## Directory Structure

```
test_data/insulation/           # Test data logs
├── INSUL-XXX_20240115_103045.jsonl
├── INSUL-XXX_20240115_103045.csv
└── INSUL-XXX_summary_20240115_103045.json

compliance_records/insulation/  # ISO 17025 records
└── INSUL-XXX_20240115_103045.json
```

## Error Handling

The test block includes comprehensive error handling:
- Equipment connection failures
- Invalid calibration detection
- Measurement errors
- Automatic test abortion on critical failures
- Complete audit trail of errors

## Integration

### With Other Test Blocks
```python
# Can be integrated into larger test sequences
from test_blocks.insulation import InsulationResistanceTest
from test_blocks.performance import PerformanceTest

# Run multiple tests
insulation_test = InsulationResistanceTest(module="PV-001")
performance_test = PerformanceTest(module="PV-001")
```

### With Report Generation
```python
# Generate comprehensive reports
summary = test.finalize()
# Export to PDF, Excel, etc.
```

## Testing

Run unit tests:
```bash
pytest tests/test_blocks/test_insulation_resistance.py -v
```

Run with coverage:
```bash
pytest tests/test_blocks/test_insulation_resistance.py --cov=src.test_blocks.insulation
```

## References

1. IEC 61215-2:2016 - Terrestrial photovoltaic (PV) modules - Design qualification and type approval - Part 2: Test procedures
2. IEC 61730-2:2016 - Photovoltaic (PV) module safety qualification - Part 2: Requirements for testing
3. ISO/IEC 17025:2017 - General requirements for the competence of testing and calibration laboratories

## See Also

- [Base Test Block](./base_test_block.md)
- [Equipment Integration](./equipment_integration.md)
- [ISO 17025 Compliance](./iso17025_compliance.md)
- [Data Logging](./data_logging.md)
