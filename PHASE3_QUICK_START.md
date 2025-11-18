# Phase 3: Protocol Handlers - Quick Start Guide

## What Was Built

Production-ready implementations of 4 IEC standards for PV module testing:
- **IEC 60904**: I-V characteristics (Isc, Voc, Pmp, FF, efficiency)
- **IEC 61853**: Performance testing (temperature coefficients, STC rating)
- **IEC 62804**: PID testing (degradation, recovery, classification)
- **IEC 62759**: Transportation testing (mechanical loads, durability)

## Quick Usage

### Example 1: I-V Characteristics (IEC 60904)
```python
from src.protocols import IEC60904
import numpy as np

protocol = IEC60904()

# Your I-V curve data
data = {
    'voltage': np.linspace(0, 45, 100).tolist(),
    'current': [9.5, 9.4, ...],  # 100 current values
    'irradiance': 1000.0,  # W/m²
    'temperature': 25.0,    # °C
    'area': 1.95           # m²
}

result = protocol.calculate(data)

# Results with uncertainties
print(f"Isc: {result.measurements['Isc']}")  # 9.52 ± 0.05 A
print(f"Voc: {result.measurements['Voc']}")  # 45.1 ± 0.09 V
print(f"Pmp: {result.measurements['Pmp']}")  # 305.2 ± 9.2 W
print(f"FF: {result.measurements['FF'].value:.3f}")  # 0.711
print(f"Efficiency: {result.measurements['Efficiency'].value:.2f}%")  # 15.65%
print(f"Status: {result.status.value}")  # PASS
```

### Example 2: Performance Testing (IEC 61853)
```python
from src.protocols import IEC61853

protocol = IEC61853()

# Performance matrix: power at different conditions
data = {
    'irradiances': [200, 400, 600, 800, 1000, 1100],  # W/m²
    'temperatures': [15, 25, 50, 75],  # °C
    'power_matrix': [
        [63.0, 126.0, 189.0, 252.0, 315.2, 346.7],  # 15°C
        [61.0, 122.0, 183.0, 244.0, 305.0, 335.5],  # 25°C
        [54.9, 109.8, 164.7, 219.6, 274.5, 302.0],  # 50°C
        [48.8, 97.6, 146.4, 195.2, 244.0, 268.4]    # 75°C
    ],
    'voltage_matrix': [...],  # Same structure
    'current_matrix': [...]   # Same structure
}

result = protocol.calculate(data)

print(f"P_STC: {result.measurements['P_STC']}")  # 305.0 ± 9.2 W
print(f"Temp coeff (Pmp): {result.measurements['gamma_Pmp'].value:.4f} %/°C")  # -0.400
print(f"Temp coeff (Isc): {result.measurements['alpha_Isc'].value:.4f} %/°C")  # +0.050
print(f"Temp coeff (Voc): {result.measurements['beta_Voc'].value:.4f} %/°C")  # -0.300
```

### Example 3: PID Testing (IEC 62804)
```python
from src.protocols import IEC62804

protocol = IEC62804()

data = {
    'initial_power': 305.0,        # W
    'post_stress_power': 294.5,    # W after 96h stress
    'stress_voltage': -1000,       # V
    'stress_duration_hours': 96,
    'stress_temperature': 85,      # °C
    'stress_humidity': 85          # %RH
}

result = protocol.calculate(data)

print(f"Degradation: {result.measurements['power_degradation']}")  # 3.44 ± 0.15%
print(f"Classification: {result.measurements['PID_classification']}")  # Class A
print(f"Status: {result.status.value}")  # PASS
```

### Example 4: Transportation Testing (IEC 62759)
```python
from src.protocols import IEC62759

protocol = IEC62759()

data = {
    'initial_power': 305.0,
    'final_power': 302.0,
    'mechanical_tests': [
        {'type': 'static_front', 'load': 2400, 'passed': True, 'defects_found': []},
        {'type': 'static_back', 'load': 2400, 'passed': True, 'defects_found': []},
        {'type': 'vibration', 'load': 1.5, 'passed': True, 'defects_found': []}
    ],
    'visual_inspections': [
        {'time': 'before', 'defects': [], 'overall_condition': 'excellent'},
        {'time': 'after', 'defects': [
            {'type': 'frame_scratch', 'severity': 'MINOR', 'location': 'corner'}
        ], 'overall_condition': 'good'}
    ],
    'insulation_resistance': {'value': 180.0}  # MΩ
}

result = protocol.calculate(data)

durability = result.measurements['durability_score']
print(f"Durability: {durability['score']:.0f}/100 ({durability['rating']})")  # 99/100 (EXCELLENT)
print(f"Status: {result.status.value}")  # PASS
```

## Key Features

1. **Uncertainty Analysis** - All values include ± uncertainties
2. **Data Quality** - Automatic assessment (EXCELLENT/GOOD/ACCEPTABLE/POOR)
3. **Pass/Fail Criteria** - Automated checks per IEC standards
4. **JSON Export** - `result.to_dict()` for easy serialization

## Run Examples

```bash
# See complete working examples
python -m src.protocols.examples
```

## File Locations

```
src/protocols/
├── base_protocol.py    # Common functionality
├── iec_60904.py       # I-V characteristics
├── iec_61853.py       # Performance testing
├── iec_62804.py       # PID testing
├── iec_62759.py       # Transportation testing
├── examples.py        # Complete examples
├── README.md          # Full documentation
└── tests/             # Comprehensive test suite
    ├── test_base_protocol.py
    ├── test_iec_60904.py
    ├── test_iec_61853.py
    ├── test_iec_62804.py
    └── test_iec_62759.py
```

## Calculation Examples

### Fill Factor
```
FF = Pmp / (Isc × Voc)
FF = 305.2 / (9.52 × 45.1) = 0.711 (71.1%)
```

### Temperature Coefficient
```
γ = (dP/dT) / P_ref × 100%
γ = -1.22 W/°C / 305.0 W × 100% = -0.400 %/°C
```

### PID Degradation
```
Deg = (P_initial - P_final) / P_initial × 100%
Deg = (305.0 - 294.5) / 305.0 × 100% = 3.44%
Class A: < 5% degradation ✓
```

### Durability Score
```
Base: 100 points
- Power degradation (0.98%): -1 point
- Minor defects (2): -5 points
+ All tests passed: +5 points
= 99/100 (EXCELLENT)
```

## Next Steps

1. Install dependencies: `pip install -r requirements.txt`
2. Run examples: `python -m src.protocols.examples`
3. Run tests: `pytest src/protocols/tests/ -v`
4. Read full docs: `src/protocols/README.md`
5. See detailed calculations: `PHASE3_SUMMARY.md`
