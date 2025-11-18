# IEC 61701:2020 Salt Mist Corrosion Test Handler

## Overview

This module implements comprehensive salt mist corrosion resistance testing for photovoltaic (PV) modules according to **IEC 61701:2020** standard. The implementation supports all six severity levels for different marine and coastal environments.

## Standard Reference

**IEC 61701:2020** - *Salt mist corrosion testing of photovoltaic (PV) modules*

This standard specifies test methods for determining the resistance of PV modules to corrosion from salt mist. It applies to modules for use in different environments ranging from far inland to severe marine conditions.

## Features

### Severity Levels (1-6)

The handler supports all six severity levels defined in IEC 61701:2020:

| Level | Description | Environment | Distance from Coast | Exposure Duration |
|-------|-------------|-------------|---------------------|-------------------|
| 1 | Very low corrosivity | Far inland | >10 km | 12 hours |
| 2 | Low corrosivity | Inland areas | 5-10 km | 24 hours |
| 3 | Moderate corrosivity | Near coast | 1-5 km | 48 hours (2 cycles) |
| 4 | High corrosivity | Coastal zone | <1 km | 96 hours (4 cycles) |
| 5 | Very high corrosivity | Marine/offshore | Offshore | 168 hours (7 cycles) |
| 6 | Extreme corrosivity | Severe marine | Splash zone | 240 hours (10 cycles) |

### Test Conditions

The implementation follows ASTM B117 salt mist test specifications:

- **Salt concentration**: 5% NaCl (50 ± 5 g/L)
- **Temperature**: 35°C (± 2°C)
- **Humidity**: 95-100% RH
- **pH range**: 6.5-7.2
- **Spray rate**: 1-2 mL/80cm²/h

### Drying Phase

Between exposure cycles:
- **Temperature**: 25°C (± 2°C)
- **Humidity**: 50% RH (± 20%)
- **Duration**: 24 hours minimum

### Pass/Fail Criteria

Per IEC 61701:2020 requirements:

1. **Power Degradation**: < 5% allowed
   - Measured by comparing initial and final I-V curves at STC

2. **Insulation Resistance**: > 40 MΩ required
   - Or R × A > 400 MΩ·m² (area-corrected)
   - Measured at 1000V DC for 60 seconds

3. **Visual Inspection**:
   - No corrosion affecting safety or performance
   - No delamination > 2% of module area
   - No bubbles or mechanical damage
   - No discoloration indicating material degradation

## Test Sequence

The complete test sequence follows IEC 61701 methodology:

```
1. Initial I-V Curve Measurement
   ├─ Measure at STC (1000 W/m², 25°C, AM1.5)
   └─ Record Pmax, Voc, Isc, FF

2. Salt Mist Exposure (Cyclic)
   ├─ Salt spray: Duration based on severity level
   ├─ Conditions: 35°C, 95-100% RH, 5% NaCl
   ├─ Drying phase: 24h at 25°C, 50% RH
   └─ Repeat for specified number of cycles

3. Final I-V Curve Measurement
   ├─ Measure at STC (1000 W/m², 25°C, AM1.5)
   └─ Calculate power degradation

4. Visual Inspection
   ├─ Check for corrosion
   ├─ Check for delamination
   ├─ Check for bubbles
   └─ Check for mechanical damage

5. Insulation Resistance Test
   ├─ Apply 1000V DC for 60 seconds
   ├─ Measure resistance
   └─ Verify > 40 MΩ (or area-corrected)

6. Results Validation & Report Generation
   └─ Generate compliance statement
```

## Usage

### Basic Example

```python
from src.protocols.base import SpecimenInfo
from src.protocols.iec_61701_handler import IEC61701Handler, SeverityLevel

# Create specimen information
specimen = SpecimenInfo(
    specimen_id="PV-2024-001",
    manufacturer="Example Solar Inc.",
    model="ES-400M-72",
    serial_number="SN20240115-001",
    rated_power=400.0,
    rated_voltage=48.0,
    rated_current=8.33,
    technology="Mono-Si PERC",
    dimensions={'area': 2.012}  # m²
)

# Create test handler for Severity Level 4 (Coastal Zone)
handler = IEC61701Handler(
    specimen_info=specimen,
    severity_level=SeverityLevel.LEVEL_4,
    config={'operator': 'Jane Smith', 'facility': 'Test Lab'}
)

# Initialize equipment
handler.initialize_equipment()

# Setup test parameters
handler.setup_test_parameters()

# Execute complete test sequence
handler.execute_test_sequence()

# Validate results
is_pass = handler.validate_results()

# Generate report
report_path = handler.generate_report('./reports', format='json')

# Print summary
handler.print_summary()
```

### Running the Example

```bash
cd examples
python iec_61701_example.py
```

This will demonstrate:
- Overview of all severity levels
- Complete test execution for Severity Level 4
- Report generation in JSON format

## File Structure

```
src/
├── protocols/
│   ├── __init__.py
│   ├── base.py                      # Base protocol handler
│   └── iec_61701_handler.py         # IEC 61701 implementation
├── measurements/
│   ├── __init__.py
│   ├── iv_curve.py                  # I-V curve measurements
│   └── insulation.py                # Insulation resistance
└── ...

examples/
└── iec_61701_example.py             # Usage demonstration

reports/
└── (generated test reports)
```

## Data Classes

### Key Data Structures

#### `SeverityLevel` (Enum)
```python
LEVEL_1 = 1  # Very low corrosivity
LEVEL_2 = 2  # Low corrosivity
LEVEL_3 = 3  # Moderate corrosivity
LEVEL_4 = 4  # High corrosivity
LEVEL_5 = 5  # Very high corrosivity
LEVEL_6 = 6  # Extreme corrosivity
```

#### `IVCurveData`
- `voltage`: List of voltage measurements (V)
- `current`: List of current measurements (A)
- `power`: Calculated power (W)
- `voc`: Open circuit voltage
- `isc`: Short circuit current
- `pmax`: Maximum power
- `vmpp`, `impp`: MPP voltage and current
- `fill_factor`: Fill factor

#### `InsulationResistanceData`
- `resistance`: Measured resistance (Ω)
- `test_voltage`: Applied voltage (V)
- `measurement_duration`: Test duration (s)
- `passes`: Boolean pass/fail status

#### `VisualInspectionResult`
- `corrosion_detected`: Boolean
- `delamination_detected`: Boolean
- `bubbles_detected`: Boolean
- `mechanical_damage`: Boolean
- `passes`: Overall visual pass/fail

#### `IEC61701TestReport`
Complete test report including:
- Specimen information
- Test conditions
- All measurements
- Pass/fail results
- Compliance statement

## Report Generation

The handler generates comprehensive JSON reports containing:

```json
{
  "standard": "IEC 61701:2020",
  "test_name": "Salt Mist Corrosion Resistance Test",
  "specimen": { ... },
  "test_parameters": {
    "severity_level": 4,
    "exposure_duration_hours": 96,
    "salt_mist_conditions": { ... },
    "drying_conditions": { ... }
  },
  "measurements": {
    "initial_iv_curve": { ... },
    "final_iv_curve": { ... },
    "power_degradation_percent": 2.5,
    "visual_inspection": { ... },
    "insulation_resistance": { ... }
  },
  "results": {
    "power_degradation_pass": true,
    "insulation_resistance_pass": true,
    "visual_inspection_pass": true,
    "overall_status": "PASS"
  },
  "compliance_statement": "The tested specimen COMPLIES with IEC 61701:2020..."
}
```

## Equipment Integration

The handler is designed to interface with:

1. **Salt Mist Chamber** (ASTM B117 compliant)
   - Temperature control (35°C ± 2°C)
   - Humidity control (95-100% RH)
   - Salt solution preparation and delivery
   - Environmental monitoring

2. **I-V Curve Tracer**
   - STC simulation (1000 W/m², 25°C, AM1.5)
   - High-resolution curve tracing
   - Multi-point sweep

3. **Insulation Resistance Meter** (Megohmmeter)
   - 1000V DC test capability
   - High resistance measurement (>1 TΩ)
   - Timed measurement (60s)

4. **Environmental Chamber** (for drying phase)
   - Temperature control (25°C ± 2°C)
   - Humidity control (50% ± 20% RH)

## Production Deployment

For production deployment, implement equipment interfaces:

```python
# Example equipment interface
class SaltMistChamber:
    def set_temperature(self, temp: float) -> None:
        # Interface with actual chamber
        pass

    def set_humidity(self, humidity: float) -> None:
        pass

    def start_salt_spray(self) -> None:
        pass

    def get_conditions(self) -> Dict:
        return {
            'temperature': ...,
            'humidity': ...,
            'salt_concentration': ...
        }
```

## Compliance and Traceability

The implementation ensures:

- ✓ Full traceability of test conditions
- ✓ Automated pass/fail determination
- ✓ Environmental condition logging
- ✓ Timestamped measurements
- ✓ Operator and facility identification
- ✓ Equipment identification
- ✓ Compliance statement generation

## References

1. **IEC 61701:2020** - Salt mist corrosion testing of photovoltaic (PV) modules
2. **ASTM B117** - Standard Practice for Operating Salt Spray (Fog) Apparatus
3. **IEC 61215** - Terrestrial photovoltaic (PV) modules - Design qualification and type approval
4. **IEC 60904** - Photovoltaic devices - Part 1: Measurement of photovoltaic current-voltage characteristics
5. **ISO 9223** - Corrosion of metals and alloys - Corrosivity of atmospheres

## License

This implementation is part of the PV Test Report Automation project.

## Author

Generated for production use in PV module qualification testing laboratories.

---

**Note**: This is a production-ready implementation framework. Equipment interfaces should be customized for your specific test equipment models and communication protocols.
