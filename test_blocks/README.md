# PV Test Blocks Module

ISO 17025 compliant test blocks for photovoltaic module testing.

## Standards Compliance

- **IEC 61215**: Terrestrial photovoltaic (PV) modules - Design qualification and type approval
- **IEC 61730**: Photovoltaic (PV) module safety qualification
- **IEC 61853**: Photovoltaic (PV) module performance testing and energy rating
- **ISO 17025**: General requirements for the competence of testing and calibration laboratories
- **ISO 9001**: Quality management systems

## Available Test Blocks

### Bypass Diode Test (`bypass_diode.py`)

Comprehensive bypass diode testing per IEC 61215:

**Features:**
- Multi-diode testing (typically 3 per module)
- Forward V-I curve characterization (0-10A)
- Reverse leakage current measurement (-15V)
- Thermal performance monitoring
- Shading activation verification

**Test Sequence:**
1. Forward V-I curve measurement at multiple current points
2. Reverse bias test at -15V
3. Thermal performance under rated load
4. Shading response and activation test

**Pass Criteria:**
- Forward voltage ≤ 1.2V at rated current (8A)
- Reverse leakage ≤ 100µA at -15V
- Operating temperature ≤ 85°C
- Activation voltage ≤ 0.7V

**Usage:**
```python
from test_blocks.bypass_diode import BypassDiodeTest

# Create test instance
test = BypassDiodeTest(module="PV-001", diode_count=3)

# Set environmental conditions (ISO 17025)
test.set_environmental_conditions(
    temperature=25.0,
    humidity=45.0,
    pressure=1013.25
)

# Run test
result = test.test_all_diodes()

# Check results
print(f"Diodes tested: {len(result.forward_voltage)}")
print(f"Pass status: {result.pass_status}")
print(f"All activated: {result.activation_verified}")

# Export results
json_data = test.export_results(result, format='json')
csv_data = test.export_results(result, format='csv')
```

**Result Fields:**
- `test_id`: Unique test identifier
- `module_id`: Module identifier
- `diode_count`: Number of diodes tested
- `forward_voltage`: List of forward voltages at rated current
- `reverse_leakage_ua`: List of reverse leakage currents (µA)
- `activation_verified`: All diodes activate correctly
- `pass_status`: Overall test pass/fail
- `diode_characteristics`: Detailed per-diode results
- `vi_curve_data`: Complete V-I curve data
- `thermal_images`: Thermal image file paths
- `shading_response_time_ms`: Activation response times

## Base Classes

### `BaseTestModel`

Base class for all test implementations with:
- ISO 17025 metadata tracking
- Environmental conditions
- Equipment calibration tracking
- Measurement validation

### `TestResult`

Standard test result format with:
- Test identification
- Status tracking
- Metadata
- Measurements
- Traceability

## Development

### Running Tests

```bash
python -m unittest discover tests
```

### Running Examples

```bash
python examples/bypass_diode_example.py
```

## Future Test Blocks

Planned implementations:
- Hot Spot Endurance Test
- UV Preconditioning Test
- Thermal Cycling Test
- Damp Heat Test
- Mechanical Load Test
- Hail Impact Test
- Salt Mist Corrosion Test
- Ammonia Corrosion Test
- PID (Potential Induced Degradation) Test
- Light Soaking Test
- I-V Curve Measurement
- Electroluminescence Imaging

## License

See LICENSE file for details.
