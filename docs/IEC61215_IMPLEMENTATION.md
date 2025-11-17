# IEC 61215-2:2021 Protocol Implementation Guide

## Overview

This document provides detailed technical information about the IEC 61215-2:2021 protocol implementation in the PV Test Report Automation System.

## Standard Reference

**IEC 61215-2:2021**: Terrestrial photovoltaic (PV) modules - Design qualification and type approval - Part 2: Test procedures

This standard defines the Module Safety Tests (MST) required for design qualification of terrestrial photovoltaic modules suitable for long-term operation in general open-air climates.

## Architecture

### Class Hierarchy

```
BaseProtocol (abstract)
    ├── IEC61215Protocol
    └── [Future protocols: IEC61730Protocol, IEC61853Protocol, ...]
```

### Core Components

#### 1. Protocol Engine (`IEC61215Protocol`)

The main protocol class that orchestrates the entire test sequence.

**Location**: `src/core/protocols/iec61215.py`

**Key Methods**:
- `initialize_sequence()`: Creates test sequence based on module type
- `define_test_steps()`: Defines all 19 MST tests with dependencies
- `execute_test()`: Executes individual test steps
- `generate_compliance_report()`: Creates comprehensive test report

#### 2. Data Models

**Location**: `src/core/models/`

- **`ModuleUnderTest`**: Complete module specification and nameplate data
- **`TestSequence`**: Test sequence management with progress tracking
- **`TestStep`**: Individual test definition with dependencies
- **`TestResult`**: Test execution results with measurements
- **`Measurement`**: Individual measurement with traceability
- **`AcceptanceCriteria`**: Pass/fail criteria per standard

#### 3. Equipment Integration

**Location**: `src/core/equipment/base.py`

Abstract base classes for test equipment:
- `SolarSimulator`: Solar simulator control
- `IVTracer`: I-V curve measurement
- `TemperatureChamber`: Climate chamber control
- `InsulationTester`: Insulation resistance testing

## Test Sequence

### Module Types

The protocol supports two module types:
1. **Crystalline Silicon**: Standard sequence with twist test
2. **Thin-Film**: Includes preconditioning/stabilization step

### Test Flow

```
Initial Tests
├── MST 01: Visual Inspection
├── MST 02: Maximum Power (Initial)
└── MST 03: Insulation Test (Initial)
    │
    ├─ (Thin-Film Only) Preconditioning
    │
Characterization Tests
├── MST 04: Temperature Coefficients
├── MST 05: NOCT Measurement
├── MST 06: STC Performance (Stabilized)
└── MST 07: Low Irradiance Performance
    │
Environmental Tests
├── MST 08: Outdoor Exposure
├── MST 09: Hot-spot Endurance
├── MST 10: UV Preconditioning
├── MST 11: Thermal Cycling (TC 200)
├── MST 12: Humidity-Freeze (HF 10)
└── MST 13: Damp Heat (DH 1000)
    │
Mechanical Tests
├── MST 14: Mechanical Load (Static)
├── MST 15: Hail Impact
├── MST 16: Mechanical Load (Dynamic)
├── MST 17: Twist Test (Crystalline only)
└── MST 18: Robustness of Terminations
    │
Final Tests
├── MST 01: Visual Inspection (Final)
├── MST 02: Maximum Power (Final)
├── MST 03: Insulation Test (Final)
└── MST 19: Wet Leakage Current
```

## Test Details

### MST 02: Maximum Power Determination

**Standard Conditions (STC)**:
- Irradiance: 1000 W/m² ± 10%
- Cell Temperature: 25°C ± 2°C
- Spectral Distribution: AM 1.5G

**Measured Parameters**:
- Pmax: Maximum power
- Voc: Open-circuit voltage
- Isc: Short-circuit current
- Vmp: Voltage at maximum power point
- Imp: Current at maximum power point
- FF: Fill factor

**Acceptance Criteria**:
- Power degradation ≤ 5% (general tests)
- Power degradation ≤ 2% (initial stabilization for thin-film)

**Implementation**:
```python
def _execute_max_power_determination(self, test_step, **kwargs) -> TestResult:
    # Configure solar simulator
    # Set STC conditions
    # Measure I-V curve
    # Extract performance parameters
    # Calculate degradation if final measurement
    # Evaluate compliance
```

### MST 03: Insulation Test

**Test Parameters**:
- Test Voltage: max(System Voltage + 1000V, 2 × System Voltage)
- Duration: 60 seconds
- Temperature: Ambient
- Humidity: Record

**Acceptance Criteria**:
- Insulation resistance ≥ 40 MΩ·m² / module area

**Example**:
- Module area: 2.0 m²
- Required resistance: 40 MΩ·m² × 2.0 m² = 80 MΩ

### MST 11: Thermal Cycling (TC 200)

**Test Profile**:
```
Temperature: -40°C to +85°C
Number of cycles: 200
Cycle time: ~6 hours
Transition rate: 100°C/hour (typical)

Each cycle:
1. Ramp from 25°C to 85°C
2. Stabilize at 85°C (≥10 min)
3. Ramp from 85°C to -40°C
4. Stabilize at -40°C (≥10 min)
5. Ramp from -40°C to 25°C
```

**Acceptance Criteria**:
- Complete all 200 cycles
- Power degradation ≤ 5%
- No visual defects

### MST 13: Damp Heat (DH 1000)

**Test Conditions**:
- Temperature: 85°C ± 2°C
- Relative Humidity: 85% ± 5%
- Duration: 1000 hours
- Stabilization: ±2°C, ±5% RH

**Acceptance Criteria**:
- Power degradation ≤ 5%
- Insulation resistance maintained
- No corrosion or delamination

### MST 15: Hail Impact

**Test Parameters**:
```
Ice ball diameter: 25 mm
Impact velocity: 23 m/s (82.8 km/h)
Impact angle: 90° (perpendicular)
Number of impacts: 11

Impact locations (per IEC 61215-2):
- Center of module
- Corners (4 locations)
- Cell edges (6 locations)
```

**Acceptance Criteria**:
- No breakage, cracks, or delamination
- Major visual defects are cause for failure

## Degradation Calculations

### Power Degradation Formula

```python
degradation_percent = ((P_initial - P_final) / P_initial) × 100
```

### Measurement Points

1. **Initial**: After visual inspection, before any stress tests
2. **Stabilized**: After preconditioning (thin-film) or outdoor exposure
3. **Intermediate**: After specific test sequences (optional)
4. **Final**: After all stress tests

### Degradation Limits

| Test Sequence | Maximum Degradation |
|--------------|---------------------|
| Initial stabilization (thin-film) | 2% |
| Environmental tests | 5% |
| Mechanical tests | 5% |
| Overall (initial to final) | 5% |

## Traceability Requirements

### ISO/IEC 17025 Compliance

Every measurement must include:

1. **Equipment Information**:
   - Manufacturer, model, serial number
   - Calibration date and due date
   - Calibration certificate number
   - Equipment accuracy specification

2. **Measurement Conditions**:
   - Ambient temperature
   - Relative humidity
   - Barometric pressure (if applicable)
   - Test voltage/current/irradiance

3. **Uncertainty Budget**:
   - Type A uncertainty (statistical)
   - Type B uncertainty (systematic)
   - Combined uncertainty
   - Expanded uncertainty (coverage factor k=2)

4. **Personnel**:
   - Operator name
   - Reviewer name
   - Approval signatures

### Example Measurement Record

```python
Measurement(
    parameter="Pmax",
    value=350.5,
    unit=MeasurementUnit.POWER,
    timestamp=datetime(2024, 1, 15, 14, 30, 0),
    equipment=Equipment(
        id="IV-001",
        name="I-V Curve Tracer",
        manufacturer="Keysight",
        model="B2900A",
        serial_number="MY12345678",
        calibration_date=datetime(2023, 12, 1),
        calibration_due_date=datetime(2024, 12, 1),
        calibration_certificate="CAL-2023-1234",
        accuracy=0.025,  # ±2.5%
    ),
    uncertainty=Uncertainty(
        value=3.0,  # W
        coverage_factor=2.0,
    ),
    environmental_conditions={
        "ambient_temperature": 23.5,  # °C
        "relative_humidity": 45.0,    # %
        "irradiance": 1000.0,          # W/m²
    },
    operator="John Smith",
)
```

## Report Generation

### Report Formats

1. **JSON**: Complete data export with all measurements
2. **HTML**: Interactive web report with charts
3. **PDF**: Professional printable report
4. **Excel**: Tabular data for analysis

### Report Sections

1. **Cover Page**:
   - Laboratory information
   - Module identification
   - Report number and date
   - Accreditation logos

2. **Module Information**:
   - Manufacturer and model
   - Nameplate ratings
   - Physical characteristics
   - Cell technology

3. **Test Summary**:
   - Overall compliance status
   - Tests performed
   - Pass/fail summary
   - Degradation summary

4. **Detailed Results**:
   - Individual test results
   - Measurements with uncertainty
   - I-V curves
   - Acceptance criteria evaluation

5. **Traceability**:
   - Equipment calibration records
   - Environmental conditions
   - Personnel records

6. **Compliance Statement**:
   - Standard reference
   - Deviations (if any)
   - Final compliance declaration

### Certificate Generation

For modules that pass all tests, a compliance certificate is generated:

```python
report_gen = ReportGenerator()
certificate_path = report_gen.generate_compliance_certificate(
    report_data,
    output_path="certificate.pdf"
)
```

## Equipment Integration

### Solar Simulator Interface

```python
class MySolarSimulator(SolarSimulator):
    def connect(self) -> bool:
        # Establish SCPI connection
        # Initialize equipment
        pass

    def set_irradiance(self, irradiance: float) -> bool:
        # Set target irradiance
        # Wait for stabilization
        pass

    def trigger_flash(self) -> bool:
        # Trigger flash for measurement
        pass
```

### I-V Tracer Interface

```python
class MyIVTracer(IVTracer):
    def measure_iv_curve(self, voltage_start, voltage_end, points) -> Dict:
        # Sweep voltage
        # Measure current
        # Return voltage/current arrays
        pass

    def get_max_power_point(self) -> Dict:
        # Calculate Pmax, Vmp, Imp from I-V curve
        pass
```

## Configuration

### Test Parameters

```json
{
  "test": {
    "stc_irradiance": 1000.0,
    "stc_temperature": 25.0,
    "stc_spectrum": "AM1.5G",
    "max_degradation_general": 5.0,
    "thermal_cycles": 200,
    "damp_heat_hours": 1000
  }
}
```

### Equipment Configuration

```json
{
  "equipment": {
    "solar_simulator": {
      "manufacturer": "Pasan",
      "model": "HighLIGHT LED+",
      "address": "TCPIP::192.168.1.100::INSTR",
      "calibration_interval_days": 365
    }
  }
}
```

## Best Practices

### 1. Measurement Quality

- Always verify equipment calibration before testing
- Record environmental conditions
- Perform multiple measurements for critical parameters
- Calculate and report measurement uncertainty

### 2. Test Sequence

- Follow standard test order for consistency
- Allow sufficient stabilization time between tests
- Document any deviations from standard procedure
- Photograph defects immediately when observed

### 3. Data Management

- Store raw data separately from reports
- Maintain backup of all test data
- Use version control for test procedures
- Archive equipment calibration records

### 4. Report Review

- Have results reviewed by qualified personnel
- Verify all calculations independently
- Check compliance evaluation logic
- Ensure traceability chain is complete

## Troubleshooting

### Common Issues

**Issue**: Degradation exceeds 5% limit
- Check for actual module damage
- Verify measurement conditions
- Review equipment calibration
- Check for systematic errors

**Issue**: Insulation resistance failure
- Ensure module is dry
- Check humidity conditions
- Verify test voltage
- Inspect for physical damage

**Issue**: Hot-spot temperature excessive
- Verify bypass diode function
- Check shading pattern
- Review current setting
- Monitor thermal imaging

## Future Enhancements

1. **Database Integration**: Store all test results in SQL database
2. **Automated Scheduling**: Queue tests based on chamber availability
3. **Real-time Monitoring**: Track test progress via web interface
4. **Advanced Analytics**: Trend analysis across multiple modules
5. **LLM Integration**: Automated report analysis and anomaly detection

## References

1. IEC 61215-2:2021 - Terrestrial photovoltaic (PV) modules - Design qualification and type approval - Part 2: Test procedures
2. IEC 60904-1:2020 - Photovoltaic devices - Part 1: Measurement of photovoltaic current-voltage characteristics
3. ISO/IEC 17025:2017 - General requirements for the competence of testing and calibration laboratories
4. NABL 162 - Specific Criteria for Accreditation of Testing Laboratories

---

**Document Version**: 1.0
**Last Updated**: 2024-11-17
**Author**: PV Test Automation Team
