# Mechanical Load Test Block - IEC 61215

## Overview

The Mechanical Load Test Block implements comprehensive mechanical load testing for photovoltaic (PV) modules according to **IEC 61215** standards. It supports both static and dynamic load testing with deflection monitoring, power degradation analysis, and full ISO 17025 traceability.

## Test Standards Compliance

- **IEC 61215**: Design qualification and type approval for terrestrial crystalline silicon PV modules
- **ISO/IEC 17025**: General requirements for the competence of testing and calibration laboratories

## Test Requirements

### Static Load Test
- **Front Load**: 2400 Pa
- **Rear Load**: 2400 Pa
- **Hold Time**: 1 hour (3600 seconds)
- **Purpose**: Simulate wind and snow loads

### Dynamic Load Test
- **Load**: ±1000 Pa
- **Cycles**: 1000 cycles
- **Purpose**: Simulate cyclic mechanical stress from wind

### Pass Criteria
- **Power Degradation**: < 5% from pre-test to post-test
- **Maximum Deflection**: < 40 mm (configurable)
- **No visual defects**: Cracks, delamination, junction box detachment

## Features

### ✓ Static and Dynamic Modes
- Static front load testing
- Static rear load testing
- Dynamic cyclic load testing

### ✓ Deflection Monitoring
- Real-time deflection measurements
- Multiple measurement positions (center, edge, corner)
- Statistical analysis of deflection data
- Maximum deflection tracking

### ✓ Power Degradation Analysis
- Pre-test IV curve measurement (flash test)
- Post-test IV curve measurement
- Automatic degradation calculation
- Pass/fail evaluation based on 5% threshold

### ✓ ISO 17025 Traceability
- Operator identification
- Equipment tracking with calibration IDs
- Environmental condition monitoring
- Test procedure version tracking
- Timestamp recording for all measurements

### ✓ Comprehensive Reporting
- Detailed test reports in JSON format
- Statistical analysis of deflection data
- Error and warning tracking
- Complete audit trail

## Installation

```bash
# Install the package
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

## Quick Start

### Example 1: Static Front Load Test

```python
from pv_automation.test_blocks.mechanical import (
    MechanicalLoadTest,
    LoadType,
    PowerMeasurement
)

# Create test instance
test = MechanicalLoadTest(
    module_id="PV-001",
    load_type=LoadType.STATIC_FRONT,
    load_pa=2400.0,
    operator_name="John Smith",
    equipment_ids=["PRESS-CHAMBER-001", "LVDT-001", "IV-TRACER-001"]
)

# Pre-test flash measurement
pre_power = PowerMeasurement(
    pmax_w=450.0,
    voc_v=48.5,
    isc_a=11.2,
    vmp_v=40.2,
    imp_a=11.19,
    fill_factor=0.827
)
test.set_pre_test_power(pre_power)

# Add deflection measurements during test
test.add_deflection_measurement(load_pa=0, deflection_mm=0)
test.add_deflection_measurement(load_pa=1200, deflection_mm=10.8)
test.add_deflection_measurement(load_pa=2400, deflection_mm=22.3)

# Post-test flash measurement
post_power = PowerMeasurement(
    pmax_w=448.5,
    voc_v=48.4,
    isc_a=11.18,
    vmp_v=40.1,
    imp_a=11.18,
    fill_factor=0.826
)
test.set_post_test_power(post_power)

# Execute test and get results
result = test.execute()
print(f"Test passed: {result}")
print(f"Power degradation: {test.power_degradation_pct:.2f}%")
print(f"Max deflection: {test.max_deflection_mm:.2f} mm")

# Generate report
report = test.generate_report()
```

### Example 2: Dynamic Load Test

```python
# Create dynamic test instance
test = MechanicalLoadTest(
    module_id="PV-002",
    load_type=LoadType.DYNAMIC,
    load_pa=1000.0,
    cycles=1000,
    operator_name="Jane Doe",
    equipment_ids=["CYCLIC-LOADER-001", "LVDT-002", "IV-TRACER-001"]
)

# Set pre-test power
pre_power = PowerMeasurement(
    pmax_w=500.0,
    voc_v=49.0,
    isc_a=12.3,
    vmp_v=40.5,
    imp_a=12.35,
    fill_factor=0.829
)
test.set_pre_test_power(pre_power)

# Add deflection measurements for specific cycles
for cycle in [1, 100, 250, 500, 750, 1000]:
    # Positive load
    test.add_deflection_measurement(
        load_pa=1000,
        deflection_mm=12.5,
        position="center",
        cycle_number=cycle
    )
    # Negative load
    test.add_deflection_measurement(
        load_pa=-1000,
        deflection_mm=-12.3,
        position="center",
        cycle_number=cycle
    )

# Set post-test power
post_power = PowerMeasurement(
    pmax_w=478.0,
    voc_v=48.8,
    isc_a=12.25,
    vmp_v=40.3,
    imp_a=11.86,
    fill_factor=0.825
)
test.set_post_test_power(post_power)

# Execute and analyze
result = test.execute()
stats = test.calculate_statistics()
print(f"Mean deflection: {stats['mean_deflection_mm']:.2f} mm")
```

## API Reference

### MechanicalLoadTest Class

#### Constructor Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `module_id` | str | Yes | Unique identifier of the PV module |
| `load_type` | LoadType | Yes | Type of load test (STATIC_FRONT, STATIC_REAR, DYNAMIC) |
| `load_pa` | float | Yes | Applied load in Pascals |
| `cycles` | int | Conditional | Number of cycles (required for dynamic tests) |
| `operator_name` | str | Yes | Name of the test operator |
| `equipment_ids` | List[str] | No | List of equipment IDs used |
| `environmental_conditions` | Dict | No | Ambient conditions during test |

#### Key Methods

##### `set_pre_test_power(power_measurement: PowerMeasurement)`
Set the pre-test power measurement from flash test.

##### `set_post_test_power(power_measurement: PowerMeasurement)`
Set the post-test power measurement and calculate degradation.

##### `add_deflection_measurement(load_pa, deflection_mm, position="center", cycle_number=None)`
Add a deflection measurement during the test.

**Parameters:**
- `load_pa` (float): Applied load in Pascals
- `deflection_mm` (float): Measured deflection in millimeters
- `position` (str): Measurement position (center, edge, corner)
- `cycle_number` (int, optional): Cycle number for dynamic tests

##### `calculate_statistics() -> Dict[str, Any]`
Calculate statistical analysis of deflection measurements.

**Returns:** Dictionary containing:
- `mean_deflection_mm`: Average deflection
- `std_deflection_mm`: Standard deviation
- `max_deflection_mm`: Maximum absolute deflection
- `min_deflection_mm`: Minimum absolute deflection
- `measurement_count`: Number of measurements

##### `execute() -> bool`
Execute the complete test procedure.

**Returns:** `True` if test passes all criteria, `False` otherwise

##### `generate_report() -> Dict[str, Any]`
Generate comprehensive test report.

**Returns:** Dictionary containing all test data and results

### PowerMeasurement Class

Represents IV curve measurement from flash test.

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `pmax_w` | float | Maximum power (W) |
| `voc_v` | float | Open circuit voltage (V) |
| `isc_a` | float | Short circuit current (A) |
| `vmp_v` | float | Voltage at max power point (V) |
| `imp_a` | float | Current at max power point (A) |
| `fill_factor` | float | Fill factor (0-1) |
| `irradiance_wm2` | float | Irradiance (W/m²), default: 1000 |
| `temperature_c` | float | Module temperature (°C), default: 25 |

### DeflectionMeasurement Class

Represents a single deflection measurement.

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `load_pa` | float | Applied load (Pa) |
| `deflection_mm` | float | Measured deflection (mm) |
| `position` | str | Measurement position |
| `cycle_number` | int | Cycle number (for dynamic tests) |
| `timestamp` | datetime | Measurement timestamp |

### LoadType Enum

- `STATIC_FRONT`: Static load on front surface
- `STATIC_REAR`: Static load on rear surface
- `DYNAMIC`: Cyclic load test

## Test Equipment Integration

The test block is designed to interface with:

1. **Pressure Chamber or Load Frame**
   - Applies uniform load to module surface
   - Controlled pressure application
   - Equipment ID tracking for ISO 17025

2. **Deflection Sensors (LVDT)**
   - Linear Variable Differential Transformers
   - Real-time deflection monitoring
   - Multiple measurement positions

3. **Pressure Transducers**
   - Verify applied load
   - Monitor pressure uniformity

4. **IV Tracer (Flash Test)**
   - Pre-test power measurement
   - Post-test power measurement
   - STC conditions (1000 W/m², 25°C)

## Running Tests

### Run All Tests

```bash
pytest tests/test_mechanical_load.py -v
```

### Run with Coverage

```bash
pytest tests/test_mechanical_load.py --cov=src/pv_automation --cov-report=html
```

### Run Specific Test Class

```bash
pytest tests/test_mechanical_load.py::TestPowerDegradation -v
```

## Examples

Complete working examples are available in:
```
examples/mechanical_load_example.py
```

Run the examples:
```bash
python examples/mechanical_load_example.py
```

## ISO 17025 Compliance

The test block ensures ISO 17025 compliance through:

1. **Traceability**
   - Equipment identification and calibration tracking
   - Operator identification
   - Test procedure versioning
   - Complete timestamp recording

2. **Environmental Monitoring**
   - Temperature tracking
   - Humidity tracking
   - Atmospheric pressure

3. **Uncertainty Analysis**
   - Statistical analysis of measurements
   - Standard deviation calculation
   - Measurement repeatability

4. **Documentation**
   - Comprehensive test reports
   - Error and warning logging
   - Audit trail of all measurements

## Best Practices

1. **Always perform pre-test and post-test flash measurements** under Standard Test Conditions (STC: 1000 W/m², 25°C, AM1.5)

2. **Record deflection at multiple points** during static tests (0 Pa, 600 Pa, 1200 Pa, 1800 Pa, 2400 Pa)

3. **For dynamic tests**, record deflection at regular intervals (e.g., cycles 1, 100, 250, 500, 750, 1000)

4. **Track equipment calibration** and include calibration IDs in equipment_ids

5. **Monitor environmental conditions** throughout the test

6. **Visual inspection** before and after test for cracks, delamination, or junction box detachment

## Troubleshooting

### Test Fails Due to Missing Power Measurements

**Error**: "Pre-test power measurement required"

**Solution**: Call `set_pre_test_power()` before executing the test

### Dynamic Test Validation Error

**Error**: "Dynamic load test requires cycles to be specified"

**Solution**: Set `cycles` parameter when creating dynamic load test

### Power Degradation Exceeds Limit

**Error**: "Power degradation X% exceeds limit 5%"

**Possible Causes**:
- Module damage during test
- Microcracks in cells
- Delamination
- Junction box issues
- Measurement error in flash test

## Contributing

When extending the mechanical load test block:

1. Maintain ISO 17025 traceability
2. Add comprehensive unit tests
3. Update documentation
4. Follow IEC 61215 standards
5. Include error handling and validation

## References

- **IEC 61215-2:2021**: Terrestrial photovoltaic (PV) modules - Design qualification and type approval - Part 2: Test procedures
- **ISO/IEC 17025:2017**: General requirements for the competence of testing and calibration laboratories
- **IEC 61853**: Photovoltaic (PV) module performance testing and energy rating

## License

MIT License - See LICENSE file for details
