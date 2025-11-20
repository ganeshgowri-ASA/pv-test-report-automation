# IEC Protocol Implementations for PV Testing

Production-ready implementations of IEC standards for photovoltaic module testing and characterization.

## Overview

This package provides comprehensive, standards-compliant implementations of major IEC protocols used in PV module testing:

- **IEC 60904-1**: I-V Characteristics Measurement
- **IEC 61853-1**: Performance Testing and Energy Rating
- **IEC 62804-1**: Potential Induced Degradation (PID) Testing
- **IEC 62759-1**: Transportation Testing

All implementations include:
- Accurate calculations per IEC standards
- Comprehensive uncertainty analysis (GUM-compliant)
- Data quality assessment
- Automated pass/fail criteria
- Full traceability and documentation

## Installation

```bash
pip install -r requirements.txt
```

### Dependencies

- numpy >= 1.20.0
- scipy >= 1.7.0
- pytest >= 7.0.0 (for testing)

## Quick Start

### IEC 60904 - I-V Characteristics

```python
from src.protocols import IEC60904
import numpy as np

# Create protocol handler
protocol = IEC60904()

# Prepare I-V curve data
iv_data = {
    'voltage': np.linspace(0, 45, 100).tolist(),
    'current': [9.5, 9.4, ...],  # Current values
    'irradiance': 1000.0,  # W/m²
    'temperature': 25.0,    # °C
    'area': 1.95,          # m²
    'spectrum': 'AM1.5G'
}

# Calculate parameters
result = protocol.calculate(iv_data)

# Access results
print(f"Isc: {result.measurements['Isc']}")
print(f"Voc: {result.measurements['Voc']}")
print(f"Pmp: {result.measurements['Pmp']}")
print(f"FF: {result.measurements['FF'].value:.4f}")
print(f"Efficiency: {result.measurements['Efficiency'].value:.2f}%")
```

### IEC 61853 - Performance Testing

```python
from src.protocols import IEC61853

# Create protocol handler
protocol = IEC61853()

# Prepare performance matrix data
performance_data = {
    'irradiances': [200, 400, 600, 800, 1000, 1100],  # W/m²
    'temperatures': [15, 25, 50, 75],  # °C
    'power_matrix': [[...], [...], ...],  # Power at each condition
    'voltage_matrix': [[...], [...], ...],
    'current_matrix': [[...], [...], ...]
}

# Calculate performance parameters
result = protocol.calculate(performance_data)

# Access results
print(f"P_STC: {result.measurements['P_STC']}")
print(f"Temperature coefficient (Pmp): {result.measurements['gamma_Pmp'].value:.4f} %/°C")
print(f"Low irradiance performance: {result.measurements['low_irradiance_performance']}")
```

### IEC 62804 - PID Testing

```python
from src.protocols import IEC62804

# Create protocol handler
protocol = IEC62804()

# Prepare PID test data
pid_data = {
    'initial_power': 305.0,
    'post_stress_power': 293.5,
    'stress_voltage': -1000,  # V
    'stress_duration_hours': 96,
    'stress_temperature': 85,  # °C
    'stress_humidity': 85      # %RH
}

# Calculate PID results
result = protocol.calculate(pid_data)

# Access results
print(f"Degradation: {result.measurements['power_degradation']}")
print(f"PID Classification: {result.measurements['PID_classification']}")
```

### IEC 62759 - Transportation Testing

```python
from src.protocols import IEC62759

# Create protocol handler
protocol = IEC62759()

# Prepare transportation test data
transport_data = {
    'initial_power': 305.0,
    'final_power': 302.0,
    'mechanical_tests': [...],
    'visual_inspections': [...],
    'insulation_resistance': {'value': 150.0}
}

# Calculate results
result = protocol.calculate(transport_data)

# Access results
print(f"Durability score: {result.measurements['durability_score']}")
print(f"Status: {result.status.value}")
```

## Detailed Documentation

### Base Protocol Class

All protocol implementations inherit from `BaseProtocol`, which provides:

#### Uncertainty Management
- Type A uncertainty (statistical)
- Type B uncertainty (systematic)
- Root-sum-of-squares combination
- GUM-compliant uncertainty propagation

#### Common Calculations
- Temperature corrections
- Irradiance corrections
- Spectral mismatch calculations
- Linear regression with uncertainties
- Interpolation methods

#### Data Quality Assessment
- EXCELLENT: < 1% uncertainty
- GOOD: 1-2% uncertainty
- ACCEPTABLE: 2-5% uncertainty
- POOR: > 5% uncertainty

### IEC 60904 - I-V Characteristics

**Standard Test Conditions:**
- Irradiance: 1000 W/m²
- Spectrum: AM1.5 Global
- Cell temperature: 25°C

**Calculated Parameters:**
- Isc (Short-circuit current)
- Voc (Open-circuit voltage)
- Pmp (Maximum power)
- Vmp, Imp (Voltage and current at MPP)
- FF (Fill factor)
- Efficiency (Conversion efficiency)
- Rs (Series resistance)
- Rsh (Shunt resistance)

**STC Correction:**
Automatically corrects non-STC measurements to standard conditions using temperature coefficients.

**Pass/Fail Criteria:**
- Data quality < 5% uncertainty
- Fill factor 0.50-0.90
- Series resistance < 10Ω
- Shunt resistance > 50Ω

### IEC 61853 - Performance Testing

**Test Matrix:**
- Irradiances: 100-1100 W/m²
- Temperatures: 15-75°C
- Multiple operating points

**Calculated Parameters:**
- P_STC (Power rating at STC)
- α (Isc temperature coefficient)
- β (Voc temperature coefficient)
- γ (Pmp temperature coefficient)
- Low irradiance performance (200, 400 W/m²)
- NOCT (Nominal Operating Cell Temperature)
- AOI modifier (Angle of incidence effects)

**Pass/Fail Criteria:**
- STC power uncertainty < 3%
- Temperature coefficients in typical ranges
- Low irradiance loss < 15%

### IEC 62804 - PID Testing

**Standard Test Conditions:**
- Stress voltage: ±1000V
- Duration: 96 hours
- Temperature: 85°C
- Humidity: 85%RH

**PID Classification:**
- Class A: < 5% degradation
- Class B: < 20% degradation
- Fail: ≥ 20% degradation

**Calculated Parameters:**
- Power degradation
- Degradation rate (%/hour)
- Time-series analysis
- Leakage current monitoring
- Recovery analysis

**Pass/Fail Criteria:**
- Class A or B rating
- Full recovery possible
- Test duration ≥ 96 hours

### IEC 62759 - Transportation Testing

**Test Types:**
- Static load (front/back: 2400 Pa)
- Edge load (100 N/m)
- Vibration (1-200 Hz)
- Environmental exposure

**Visual Defect Classification:**
- NONE: No defects
- MINOR: Cosmetic only
- MODERATE: May affect performance
- MAJOR: Significant impact
- CRITICAL: Safety hazard

**Calculated Parameters:**
- Power degradation
- Mechanical test results
- Visual inspection summary
- Insulation resistance
- Durability score (0-100)

**Pass/Fail Criteria:**
- Power degradation < 5%
- No critical defects
- Insulation resistance ≥ 40 MΩ
- Durability score ≥ 60

## Uncertainty Analysis

All measurements include comprehensive uncertainty analysis:

```python
# Example uncertainty object
uncertainty = result.measurements['Pmp']

print(f"Value: {uncertainty.value} W")
print(f"Standard uncertainty: {uncertainty.standard_uncertainty} W")
print(f"Expanded uncertainty (k=2): {uncertainty.expanded_uncertainty} W")
print(f"Relative uncertainty: {uncertainty.relative_uncertainty:.2f}%")
print(f"Sources: {uncertainty.sources}")
```

## Result Serialization

All results can be serialized to JSON:

```python
result_dict = result.to_dict()

# Save to file
import json
with open('test_results.json', 'w') as f:
    json.dump(result_dict, f, indent=2)
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest src/protocols/tests/ -v

# Run specific protocol tests
pytest src/protocols/tests/test_iec_60904.py -v

# Run with coverage
pytest src/protocols/tests/ --cov=src/protocols --cov-report=html
```

## Examples

See `examples.py` for comprehensive usage examples of all protocols:

```bash
python -m src.protocols.examples
```

This will run complete calculations for all four protocols with realistic test data.

## Calculation Examples

### Temperature Coefficient Calculation (IEC 61853)

Given power measurements at different temperatures:

| Temperature (°C) | Power (W) |
|-----------------|-----------|
| 15              | 315.2     |
| 25              | 305.0     |
| 50              | 274.5     |
| 75              | 244.0     |

Linear regression yields:
- Slope: -1.22 W/°C
- Temperature coefficient: γ = -0.40 %/°C

### Fill Factor Calculation (IEC 60904)

```
FF = Pmp / (Isc × Voc)

Given:
- Isc = 9.5 A
- Voc = 45.0 V
- Pmp = 305.0 W

FF = 305.0 / (9.5 × 45.0) = 0.713 (71.3%)
```

### PID Degradation Rate (IEC 62804)

```
Degradation (%) = (P_initial - P_final) / P_initial × 100

Given:
- P_initial = 305.0 W
- P_final = 293.5 W
- Duration = 96 hours

Degradation = (305.0 - 293.5) / 305.0 × 100 = 3.77%
Rate = 3.77% / 96 hours = 0.039 %/hour
Classification: Class A (< 5%)
```

## Standards Compliance

This implementation follows:

- IEC 60904-1:2020 - Photovoltaic devices - Part 1: Measurement of photovoltaic current-voltage characteristics
- IEC 61853-1:2011 - Photovoltaic (PV) module performance testing and energy rating - Part 1: Irradiance and temperature performance measurements and power rating
- IEC 62804-1:2015 - Photovoltaic (PV) modules - Test methods for the detection of potential-induced degradation - Part 1: Crystalline silicon
- IEC 62759-1:2015 - Photovoltaic (PV) modules - Transportation testing - Part 1: Transportation and shipping of module package units
- ISO/IEC Guide 98-3:2008 (GUM) - Uncertainty of measurement

## Contributing

When adding new protocols or extending existing ones:

1. Inherit from `BaseProtocol`
2. Implement `validate_data()` and `calculate()` methods
3. Include comprehensive uncertainty analysis
4. Add thorough unit tests
5. Document all calculations with standard references
6. Include realistic examples

## License

Copyright (c) 2024. All rights reserved.

## Support

For issues, questions, or contributions, please contact the development team.
