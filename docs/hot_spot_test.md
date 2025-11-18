# Hot Spot Endurance Test - IEC 61215

## Overview

The Hot Spot Endurance Test evaluates PV module behavior under partial shading conditions to verify bypass diode protection and ensure cells can withstand localized heating without permanent damage.

## Standard Compliance

- **IEC 61215**: PV Module Design Qualification and Type Approval
- **ISO 17025**: Testing and Calibration Laboratories Accreditation
- **NABL/ILAC**: Accreditation requirements

## Test Purpose

To verify that:
1. Bypass diodes activate properly when cells are shaded
2. Cell temperature remains within safe limits
3. No permanent damage occurs from hot spot conditions
4. Module can withstand partial shading encountered in field installations

## Test Conditions

### Environmental
- **Irradiance**: 1000 W/m² ± 10%
- **Spectrum**: AM 1.5 (solar simulator)
- **Duration**: 1 hour per shading configuration
- **Ambient Temperature**: 23°C ± 5°C

### Temperature Limits
- **Maximum Cell Temperature**: <85°C for bypass diode activation
- **Safety Limit**: 120°C (test abort threshold)

### Shading Patterns
- **Single Cell**: One cell fully shaded
- **Half Cell**: Half of one cell shaded
- **Two Cells**: Two adjacent cells in same string shaded
- **String**: Entire string shaded
- **Partial Module**: Quarter or half module shaded
- **Diagonal**: Diagonal shading pattern
- **Corner**: Corner cells shaded

## Equipment Required

### Solar Simulator
- Type: Xenon-Arc or LED-based
- Irradiance Range: 0-1200 W/m²
- Uniformity: ±2%
- Temporal Stability: ±1%
- Spectral Match: Class A (IEC 60904-9)

### Thermal Imaging Camera
- Temperature Range: -20°C to 150°C minimum
- Accuracy: ±2°C or ±2% of reading
- Resolution: 640x480 minimum
- Frame Rate: 30 Hz minimum
- Calibration: NIST-traceable

### Temperature Data Logger
- Channels: 8+ thermocouple inputs
- Sample Rate: 1 Hz minimum
- Accuracy: ±0.1°C
- Calibration: Annual

### Shading Masks
- Material: Opaque, heat-resistant
- Patterns: Various cell configurations
- Mounting: Secure, non-contact with module

## Test Procedure

### 1. Pre-Test Inspection
```python
# Document module condition
- Visual inspection for defects
- Electrical characterization (I-V curve)
- Infrared thermography baseline
- Physical measurements
```

### 2. Equipment Setup
```python
from src.test_blocks.iec_61215.hot_spot import HotSpotTest

# Initialize test
test = HotSpotTest(
    module_id="PV-001",
    operator="OP-12345",
    equipment_config={
        "thermal_camera": {...},
        "solar_simulator": {...},
        "temp_logger": {...}
    }
)
```

### 3. Test Execution
```python
# Run test with specified shading pattern
result = await test.run(
    shading_pattern="single_cell",
    duration_hours=1.0,
    irradiance_w_m2=1000.0,
    temperature_threshold_c=85.0
)
```

### 4. Data Collection
The test automatically collects:
- Thermal images every 5 minutes (configurable)
- Continuous temperature logging (1 Hz)
- Bypass diode voltage measurements
- Timestamps for all events

### 5. Post-Test Inspection
- Visual inspection for damage
- High-resolution photography
- Electroluminescence (EL) imaging
- I-V curve comparison

## Pass/Fail Criteria

### PASS Conditions
✓ Maximum temperature stays below threshold (<85°C) **OR** bypass diode activates
✓ No permanent damage (cell cracks, burn marks, glass breakage)
✓ Minor discoloration or delamination acceptable if module still functional
✓ Bypass diode operates within specifications

### FAIL Conditions
✗ Temperature exceeds threshold **AND** bypass diode does not activate
✗ Permanent damage detected (cell cracks, burn marks, glass breakage)
✗ Bypass diode failure
✗ Safety abort due to excessive temperature

## Usage Examples

### Basic Test
```python
from src.test_blocks.iec_61215.hot_spot import run_hot_spot_test

# Run test with defaults
result = await run_hot_spot_test(
    module_id="PV-001",
    operator="OP-12345",
    shading_pattern="single_cell"
)

print(f"Test Status: {result.status}")
print(f"Max Temperature: {result.max_temperature_c}°C")
print(f"Bypass Diode Activated: {result.bypass_diode_activated}")
```

### Multiple Shading Patterns
```python
patterns = [
    "single_cell",
    "two_cells",
    "string",
    "partial_module"
]

results = []
for pattern in patterns:
    result = await run_hot_spot_test(
        module_id="PV-001",
        operator="OP-12345",
        shading_pattern=pattern
    )
    results.append(result)
    print(f"{pattern}: {result.status} - {result.max_temperature_c}°C")
```

### Custom Configuration
```python
from src.test_blocks.iec_61215.hot_spot import HotSpotTest

# Custom equipment configuration
equipment_config = {
    "thermal_camera": {
        "type": "FLIR-T1020",
        "resolution": "1024x768",
        "framerate": 60
    },
    "solar_simulator": {
        "type": "Xenon-Arc",
        "max_irradiance": 1200
    }
}

# Custom test parameters
test_parameters = {
    "irradiance_w_m2": 1100.0,  # Higher irradiance
    "duration_hours": 2.0,       # Longer duration
    "thermal_interval_seconds": 180  # Capture every 3 minutes
}

test = HotSpotTest(
    module_id="PV-001",
    operator="OP-12345",
    equipment_config=equipment_config,
    test_parameters=test_parameters
)

result = await test.run(shading_pattern="single_cell")
```

### Accessing Thermal Image Data
```python
result = await run_hot_spot_test(
    module_id="PV-001",
    operator="OP-12345",
    shading_pattern="single_cell"
)

# Iterate through thermal images
for i, image in enumerate(result.thermal_images):
    print(f"Image {i+1}:")
    print(f"  Timestamp: {image.timestamp}")
    print(f"  Max Temp: {image.max_temperature_c}°C")
    print(f"  Hot Spot Temp: {image.hot_spot_temperature_c}°C")
    print(f"  Image Path: {image.image_path}")
```

## Data Models

### HotSpotTestResult
Complete test result with ISO 17025 traceability:

```python
class HotSpotTestResult(BaseTestResult):
    # Identification
    test_id: str
    module_id: str
    operator: str

    # Test parameters
    shading_pattern: ShadingPattern
    test_duration_hours: float
    irradiance_w_m2: float

    # Temperature measurements
    max_temperature_c: float
    initial_temperature_c: float
    final_temperature_c: float

    # Bypass diode
    bypass_diode_activated: bool
    bypass_diode_status: BypassDiodeStatus
    diode_activation_time_seconds: Optional[float]

    # Visual inspection
    visual_damage: bool
    damage_types: List[VisualDamageType]

    # Thermal imaging
    thermal_images: List[ThermalImageData]

    # Pass/fail
    status: TestStatus  # Auto-determined
```

### ThermalImageData
Thermal imaging capture data:

```python
class ThermalImageData(BaseModel):
    timestamp: datetime
    min_temperature_c: float
    max_temperature_c: float
    avg_temperature_c: float
    hot_spot_temperature_c: float
    image_path: str
    shading_pattern: ShadingPattern
```

## Safety Considerations

### Emergency Shutdown
The test includes automatic safety shutdown if:
- Cell temperature exceeds 120°C
- Equipment malfunction detected
- Operator intervention required

### Safety Checks
- ✓ Equipment calibration verified before test
- ✓ Temperature monitoring throughout test
- ✓ Automatic shutdown on safety limits
- ✓ Manual abort capability
- ✓ Cool-down period after test

## Reporting

### ISO 17025 Compliance
All test reports include:
- Unique test identification
- Operator and reviewer signatures
- Equipment calibration records
- Environmental conditions
- Complete test parameters
- Raw data and analysis
- Uncertainty analysis
- Traceability chain

### Generated Data
- Test report (PDF)
- Raw data (CSV/JSON)
- Thermal images (JPEG/PNG)
- I-V curves (before/after)
- Inspection photos

## Quality Assurance

### Pre-Test Verification
- Equipment calibration current
- Module identification verified
- Test plan approved
- Safety checks complete

### During Test
- Real-time monitoring
- Data integrity checks
- Event logging
- Anomaly detection

### Post-Test Review
- Data completeness check
- Pass/fail verification
- Peer review
- Report approval

## References

1. **IEC 61215-2:2021** - Terrestrial photovoltaic (PV) modules - Design qualification and type approval - Part 2: Test procedures
2. **IEC 60904-9:2020** - Photovoltaic devices - Part 9: Solar simulator performance requirements
3. **ISO/IEC 17025:2017** - General requirements for the competence of testing and calibration laboratories
4. **ASTM E1036** - Standard Test Methods for Electrical Performance of Nonconcentrator Terrestrial Photovoltaic Modules and Arrays Using Reference Cells

## Support

For questions or issues:
- Documentation: `/docs`
- Issue Tracker: GitHub Issues
- Email: support@pvtest.example.com
