# PV Test Report Automation

World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## Features

### I-V Curve Analysis System (IEC 60904-1:2020)

Production-ready I-V curve analysis with complete IEC 60904-1:2020 compliance:

- **Analyzer** (`src/tests/iv_curve/analyzer.py`)
  - Parse I-V curve data from multiple formats
  - Calculate key parameters: Voc, Isc, Vmp, Imp, Pmax, FF
  - Series/shunt resistance calculation
  - Single-diode model fitting
  - Curve smoothing and noise reduction
  - I-V and P-V curve plotting
  - Before/after comparison charts

- **STC Calculator** (`src/tests/iv_curve/stc_calculator.py`)
  - IEC 60904-1 translation procedures to Standard Test Conditions
  - Temperature coefficient application (α, β, γ)
  - Spectral mismatch correction per IEC 60904-7
  - Uncertainty budget calculation per ISO/IEC 17025
  - Multiple translation methods (IEC60904, linear, advanced)

- **NOCT Calculator** (`src/tests/iv_curve/noct_calculator.py`)
  - NOCT testing per IEC 61215-2:2021
  - Operating temperature prediction
  - Thermal performance analysis
  - Mounting correction factors
  - Power prediction at operating conditions

## Installation

```bash
# Clone the repository
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```python
from src.tests.iv_curve import IVCurveAnalyzer, IVCurveData

# Analyze I-V curve
analyzer = IVCurveAnalyzer()
iv_data = IVCurveData(voltage, current, temperature=25.0, irradiance=1000.0)
params = analyzer.calculate_parameters(iv_data)

print(f"Pmax: {params['Pmax']:.2f} W")
print(f"FF: {params['FF']:.4f}")
```

See `examples/iv_curve_example.py` for comprehensive usage examples.

## Documentation

- [I-V Curve Analysis Guide](src/tests/iv_curve/README.md)
- [API Reference](src/tests/iv_curve/__init__.py)

## Standards Compliance

- **IEC 60904-1:2020** - Measurement of photovoltaic current-voltage characteristics
- **IEC 60904-7:2019** - Computation of spectral mismatch correction
- **IEC 61215-2:2021** - Terrestrial photovoltaic modules - Design qualification
- **ISO/IEC 17025:2017** - Testing and calibration laboratories

## License

MIT License
