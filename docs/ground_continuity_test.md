# Ground Continuity Test - IEC 61730

## Overview

The Ground Continuity Test verifies electrical continuity between the photovoltaic module frame and grounding points to ensure safety under fault conditions. This implementation complies with IEC 61730 safety qualification standards.

## Test Specifications

### IEC 61730 Requirements

- **Test Current**: 25A DC for 60 seconds (minimum)
- **Maximum Resistance**: 0.1 Ohm
- **Measurement Method**: 4-wire Kelvin measurement (recommended)
- **Multiple Points**: Test all accessible grounding points
- **Temperature Monitoring**: Monitor temperature rise during test

### Safety Limits

- Maximum test current: 50A
- Maximum temperature rise: 50°C
- Emergency abort if limits exceeded

## Features

### ✓ 4-Wire Kelvin Measurement

The implementation supports 4-wire (Kelvin) measurement configuration, which eliminates lead resistance errors:

- **Current leads**: Carry the test current
- **Voltage leads**: Measure voltage drop directly at the test point
- **Accuracy**: Typically ±0.001 Ω or better

### ✓ Multiple Test Points

Standard measurement points include:

1. Frame to ground terminal
2. Frame to mounting holes (1-4)
3. Junction box to frame
4. Custom additional points

### ✓ Pass/Fail Logic

Automated evaluation per IEC 61730:
- All measurement points must be ≤ 0.1Ω
- Temperature rise must be within limits
- No safety violations during test

### ✓ Safety Features

- Pre-test safety validation
- Current limiting
- Temperature monitoring
- Post-test verification
- Emergency abort capability

### ✓ ISO 17025 Compliance

- Measurement uncertainty tracking
- Environmental conditions recording
- Equipment traceability
- Calibration status validation
- Complete audit trail

## Usage

### Basic Test

```python
from test_blocks.ground_continuity import GroundContinuityTest

# Create test instance
test = GroundContinuityTest(
    test_id="GC-001",
    module_id="PV-MODULE-12345",
    operator="John Doe"
)

# Run test
report = test.run_test(simulated=True)

# Check result
if report['result']['pass_status']:
    print("TEST PASSED")
else:
    print("TEST FAILED")
```

### Custom Parameters

```python
test = GroundContinuityTest(
    test_id="GC-002",
    module_id="PV-001",
    operator="Jane Smith",
    test_current=30.0,           # 30A test current
    test_duration=90.0,          # 90 second duration
    max_resistance_ohm=0.08,     # Stricter 0.08Ω limit
)
```

### Environmental Monitoring

```python
from test_blocks.base import EnvironmentalConditions

env = EnvironmentalConditions(
    temperature_celsius=23.5,
    humidity_percent=45.0,
    pressure_kpa=101.3
)

test = GroundContinuityTest(
    test_id="GC-003",
    module_id="PV-001",
    operator="Mike Johnson",
    environmental_conditions=env
)
```

### Specific Measurement Points

```python
from test_blocks.ground_continuity import MeasurementPoint

test = GroundContinuityTest(
    test_id="GC-004",
    module_id="PV-001",
    operator="Sarah Wilson",
    measurement_points=[
        MeasurementPoint.FRAME_TO_GROUND.value,
        MeasurementPoint.MOUNTING_HOLE_1.value,
        MeasurementPoint.MOUNTING_HOLE_2.value,
    ]
)
```

## Test Procedure

### Automated Test Sequence

1. **Validate Conditions**
   - Check environmental parameters
   - Verify measurement points defined
   - Validate test parameters

2. **Pre-Test Safety Check**
   - Verify current limits
   - Check duration settings
   - Validate resistance threshold

3. **Perform Measurements**
   - Configure 4-wire measurement
   - Apply test current (25A)
   - Measure resistance at each point
   - Monitor temperature rise

4. **Evaluate Results**
   - Compare to threshold (0.1Ω)
   - Check all measurement points
   - Verify temperature limits

5. **Post-Test Safety Check**
   - Verify no overheating
   - Check for anomalies

6. **Generate Report**
   - Compile measurement data
   - Calculate statistics
   - Create ISO 17025 compliant report

## Report Format

The test generates a comprehensive JSON report:

```json
{
  "test_information": {
    "test_id": "GC-001",
    "module_id": "PV-MODULE-12345",
    "standard": "IEC 61730",
    "operator": "John Doe",
    "test_date": "2025-11-18T10:30:00"
  },
  "test_parameters": {
    "test_current_amps": 25.0,
    "test_duration_seconds": 60.0,
    "max_resistance_threshold_ohm": 0.1,
    "wire_configuration": "4-wire-kelvin"
  },
  "measurements": [
    {
      "point": "frame_to_ground",
      "resistance_ohm": 0.0342,
      "uncertainty_ohm": 0.001,
      "voltage_drop_mv": 0.855,
      "temperature_rise_celsius": 8.3,
      "status": "passed"
    }
  ],
  "statistics": {
    "total_points_measured": 3,
    "average_resistance_ohm": 0.0398,
    "min_resistance_ohm": 0.0287,
    "max_resistance_ohm": 0.0521
  },
  "result": {
    "overall_status": "PASSED",
    "pass_status": true,
    "all_points_within_limit": true
  }
}
```

## Equipment Requirements

### Ground Continuity Tester

- **Current capacity**: Minimum 25A DC
- **Measurement range**: 0.001 - 1.0 Ω
- **Accuracy**: ±(0.1% + 0.001Ω)
- **Configuration**: 4-wire Kelvin
- **Calibration**: Valid NIST-traceable calibration

### Test Leads

- **Type**: 4-wire Kelvin clips
- **Current rating**: ≥ 30A
- **Resistance**: < 0.001Ω per lead
- **Quality**: Low-resistance, insulated

### Data Acquisition

- **Sampling rate**: ≥ 10 Hz
- **Resolution**: 0.0001Ω or better
- **Interface**: USB, GPIB, or Ethernet

## Safety Considerations

### Before Testing

- [ ] Verify module is electrically isolated
- [ ] Inspect test leads for damage
- [ ] Ensure adequate ventilation
- [ ] Check equipment calibration status

### During Testing

- [ ] Monitor current level continuously
- [ ] Watch for temperature rise
- [ ] Stay clear of current path
- [ ] Be ready to abort if needed

### After Testing

- [ ] Allow module to cool
- [ ] Verify no damage occurred
- [ ] Document any anomalies

## Troubleshooting

### High Resistance Readings

**Possible Causes:**
- Poor connection at test point
- Oxidation on contact surfaces
- Damaged grounding conductor
- Manufacturing defect

**Solutions:**
1. Clean contact surfaces
2. Inspect grounding path
3. Verify test lead connections
4. Retest with fresh contacts

### Excessive Temperature Rise

**Possible Causes:**
- High contact resistance
- Inadequate current path
- Test current too high
- Poor thermal dissipation

**Solutions:**
1. Reduce test current
2. Shorten test duration
3. Improve contact quality
4. Allow cooling between tests

### Unstable Measurements

**Possible Causes:**
- Loose connections
- Thermal effects
- Electrical interference
- Movement during test

**Solutions:**
1. Secure all connections
2. Allow thermal stabilization
3. Shield from interference
4. Ensure rigid setup

## Validation

### Equipment Validation

Verify equipment accuracy using calibrated reference resistors:

```python
# Test with 0.05Ω reference resistor
test = GroundContinuityTest(
    test_id="VALIDATION-001",
    module_id="REF-RESISTOR-0.05",
    operator="QA Engineer"
)

report = test.run_test(simulated=False)

# Verify measurement within specification
assert 0.049 <= report['statistics']['average_resistance_ohm'] <= 0.051
```

### Method Validation

- Repeatability: ≤ 2% variation
- Reproducibility: ≤ 5% between operators
- Linearity: R² ≥ 0.995
- Accuracy: Within ±5% of reference

## References

1. **IEC 61730-1:2016** - Photovoltaic (PV) module safety qualification - Part 1: Requirements for construction
2. **IEC 61730-2:2016** - Photovoltaic (PV) module safety qualification - Part 2: Requirements for testing
3. **ISO/IEC 17025:2017** - General requirements for the competence of testing and calibration laboratories
4. **NIST Handbook 150** - Procedures for Calibration and Testing Laboratories

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-18 | Claude | Initial implementation |
