# IEC 62759 Transportation Testing Guide

## Overview

IEC 62759 Transportation Testing for PV modules ensures that photovoltaic modules can withstand the mechanical stresses encountered during transportation and handling.

## Test Sequence

### 1. Initial Flash Test
- **Purpose**: Establish baseline electrical performance
- **Parameters**:
  - STC conditions (1000 W/m², AM1.5G, 25°C)
  - Measure Pmax, Voc, Isc, Vmp, Imp, Fill Factor

### 2. Edge Loading (Static Load)
- **Purpose**: Verify structural integrity with edge support
- **Parameters**:
  - Load: 600 Pa
  - Duration: 1 hour
  - Edge support configuration
  - Deflection monitoring
- **Pass Criteria**: No breakage, deflection within limits

### 3. Dynamic Mechanical Loading
- **Purpose**: Simulate vibration during transport
- **Parameters**:
  - Load: 1000 Pa
  - Cycles: 1000
  - Frequency: 0.5-2 Hz
  - Front and rear loading
- **Pass Criteria**: No breakage or cell cracks

### 4. Thermal Cycling
- **Purpose**: Verify resistance to temperature variations
- **Parameters**:
  - Cycles: 50
  - Temperature range: -40°C to +85°C
  - Ramp rate: 100°C/hour
  - Hold time: 10-20 minutes
- **Pass Criteria**: Complete all cycles without damage

### 5. Final Flash Test
- **Purpose**: Measure final electrical performance
- **Parameters**: Same as initial flash test
- **Pass Criteria**: Power degradation < 5%

### 6. Visual Inspection
- **Purpose**: Detect any physical damage
- **Check for**:
  - Cell cracks
  - Delamination
  - Junction box damage
  - Frame damage
- **Pass Criteria**: No defects found

## Pass/Fail Criteria

Module **PASSES** if ALL of the following are met:
1. ✓ No breakage during edge loading
2. ✓ No breakage during dynamic loading
3. ✓ All thermal cycles completed successfully
4. ✓ Power degradation < 5%
5. ✓ Visual inspection shows no defects

Module **FAILS** if ANY criterion is not met.

## ISO 17025 Compliance

### Required Documentation
- Technician competence records
- Equipment calibration certificates
- Environmental conditions during test
- Measurement uncertainty budget
- Complete test event log

### Traceability Requirements
- All measurements traceable to SI units
- Calibration chain documented
- Raw data retention
- Test procedure version control

## Example Usage

### Basic Test

```python
from src.protocols.iec.iec_62759 import IEC62759Controller

# Create test controller
test = IEC62759Controller(module_id="PV-001")

# Run full test sequence
test.run_full_sequence()

# Get results
print(f"Power Degradation: {test.degradation_pct}%")
print(f"Pass/Fail: {test.result.pass_fail.value}")
```

### Custom Parameters

```python
# Run with custom parameters
test = IEC62759Controller(
    module_id="PV-002",
    test_id=12345,
    technician_id="TECH-001"
)

test.connect_equipment()

# Custom edge loading
test.step2_edge_loading(load_pa=750, duration_hours=2.0)

# Custom dynamic loading
test.step3_dynamic_mechanical_loading(
    load_pa=1000,
    cycles=1000,
    frequency_hz=1.5
)

test.disconnect_equipment()
```

## Equipment Requirements

### Solar Simulator
- Class A or better (per IEC 60904-9)
- Irradiance: 1000 W/m² ± 2%
- Spectral match: AM1.5G
- Temperature control: 25°C ± 2°C

### Load Frame
- Pressure range: 0-5000 Pa
- Frequency control: 0.5-2 Hz
- Deflection measurement: ±0.1 mm
- Both static and dynamic capability

### Thermal Chamber
- Temperature range: -70°C to +180°C
- Temperature uniformity: ±3°C
- Ramp rate: 100°C/hour minimum
- Programmable cycling

## Database Models

### IEC62759Test Table

```python
from src.models.iec_62759 import IEC62759Test

test_record = IEC62759Test(
    test_id=12345,
    module_id="PV-001",
    initial_pmax=300.5,
    final_pmax=296.2,
    edge_load_result="pass",
    dynamic_load_result="pass",
    thermal_result="pass",
    visual_inspection_result="pass",
    pass_status=True
)

test_record.calculate_degradation()
# power_degradation_pct = 1.43%
```

## Report Generation

```python
# Generate comprehensive report
report = test.generate_report()

# Report includes:
# - Test identification
# - Initial/final measurements
# - Power degradation analysis
# - Edge loading results
# - Dynamic loading results
# - Thermal cycling results
# - Visual inspection findings
# - ISO 17025 compliance data
# - Complete test event log
```

## Best Practices

1. **Pre-Test Checks**
   - Verify equipment calibration
   - Check environmental conditions
   - Document module condition

2. **During Test**
   - Monitor for abnormal events
   - Record real-time data
   - Document any deviations

3. **Post-Test**
   - Complete visual inspection
   - Generate report promptly
   - Archive raw data

4. **Quality Assurance**
   - Peer review of results
   - Verify calculations
   - Check ISO 17025 compliance

## References

- IEC 62759:2015 - Photovoltaic (PV) modules - Transportation testing
- ISO/IEC 17025:2017 - General requirements for the competence of testing laboratories
- IEC 60904-9 - Solar simulator performance requirements
