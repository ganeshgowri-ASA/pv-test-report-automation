# PV Test Report Automation

World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## Features

### Phase 6: Statistical Process Control & Measurement Uncertainty

- **SPC Control Charts**
  - X-bar charts for process mean monitoring
  - R charts (Range) for process variability
  - S charts (Standard Deviation) for process variability
  - Western Electric control rules implementation
  - Automated out-of-control detection

- **Process Capability Analysis**
  - Cp (Process Capability Index)
  - Cpk (Process Capability Index with centering)
  - Pp (Process Performance Index)
  - Ppk (Process Performance Index with centering)
  - Cpm (Taguchi Capability Index)

- **Measurement Uncertainty per GUM**
  - Type A uncertainty (statistical evaluation)
  - Type B uncertainty (non-statistical evaluation)
  - Multiple probability distributions (Normal, Rectangular, Triangular, U-shaped)
  - Combined standard uncertainty calculation
  - Welch-Satterthwaite effective degrees of freedom
  - Coverage factor calculation (normal and t-distribution)
  - Expanded uncertainty (k=2 for ~95% confidence)
  - Complete uncertainty budget tables

- **ISO 17025 Compliance**
  - Full compliance with ISO/IEC 17025:2017 requirements
  - Traceability and uncertainty analysis
  - Comprehensive documentation and reporting

## Installation

```bash
# Clone the repository
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation

# Install dependencies
pip install -e .

# For development
pip install -e ".[dev]"
```

## Quick Start

### Basic Uncertainty Calculation

```python
from equipment.spc import SPCAnalyzer

# Initialize analyzer
spc = SPCAnalyzer()

# Calculate uncertainty from repeated measurements
result = spc.calculate_uncertainty(
    measurements=[100.1, 100.2, 100.0, 99.9, 100.1]
)

print(f"Expanded Uncertainty U (k=2): {result.expanded_uncertainty:.4f}")
```

### SPC Control Charts

```python
from equipment.spc import SPCAnalyzer
import numpy as np

spc = SPCAnalyzer()

# Process data: 10 subgroups of 5 measurements each
data = [
    [100.0, 100.2, 99.8, 100.1, 99.9],
    [100.1, 100.0, 100.2, 99.9, 100.0],
    # ... more subgroups
]

# Calculate control limits
xbar_limits, r_limits = spc.calculate_xbar_r_limits(data)

print(f"X-bar UCL: {xbar_limits.upper_control_limit:.4f}")
print(f"X-bar LCL: {xbar_limits.lower_control_limit:.4f}")
```

### Process Capability Analysis

```python
# Analyze process capability
result = spc.analyze_process(
    data=data,
    usl=102.0,  # Upper specification limit
    lsl=98.0,   # Lower specification limit
    target=100.0
)

print(f"Cpk: {result.capability.cpk:.3f}")
print(f"Process in control: {result.in_control}")
```

### Complete Uncertainty Budget (ISO 17025)

```python
from equipment.models import DistributionType

# Add Type B uncertainty sources
type_b_sources = [
    spc.calculate_type_b_uncertainty(
        half_width=0.5,
        distribution=DistributionType.RECTANGULAR,
        name="Calibration uncertainty",
    ),
    spc.calculate_type_b_uncertainty(
        half_width=0.1,
        distribution=DistributionType.NORMAL,
        name="Temperature effect",
    ),
]

# Calculate complete budget
budget = spc.calculate_uncertainty(
    measurements=[100.1, 100.2, 100.0],
    additional_sources=type_b_sources,
    confidence_level=95.0,
)

# Display uncertainty budget
for source in budget.sources:
    print(f"{source.name}: {source.value:.6f} ({source.uncertainty_type.value})")

print(f"\nCombined uncertainty (u_c): {budget.combined_uncertainty:.6f}")
print(f"Expanded uncertainty (U): {budget.expanded_uncertainty:.6f}")
```

## Examples

Comprehensive examples are provided in the `examples/` directory:

- **`basic_uncertainty.py`** - Simple uncertainty calculation with Type A and Type B sources
- **`spc_control_charts.py`** - Complete SPC control chart analysis
- **`iso17025_example.py`** - ISO 17025 compliant measurement uncertainty analysis

Run examples:

```bash
python examples/basic_uncertainty.py
python examples/spc_control_charts.py
python examples/iso17025_example.py
```

## API Reference

### SPCAnalyzer

Main class for statistical process control and uncertainty analysis.

#### Methods

- **`calculate_xbar_r_limits(data)`** - Calculate X-bar and R chart control limits
- **`calculate_xbar_s_limits(data)`** - Calculate X-bar and S chart control limits
- **`calculate_capability_indices(data, usl, lsl, target)`** - Calculate Cp, Cpk, Pp, Ppk, Cpm
- **`calculate_type_a_uncertainty(measurements)`** - Type A (statistical) uncertainty
- **`calculate_type_b_uncertainty(half_width, distribution)`** - Type B uncertainty
- **`calculate_combined_uncertainty(sources)`** - Combined standard uncertainty (RSS)
- **`calculate_uncertainty(measurements, additional_sources)`** - Complete uncertainty budget
- **`analyze_process(data, usl, lsl, target)`** - Complete SPC analysis

### Data Models

#### UncertaintySource

Individual uncertainty component in the budget.

```python
UncertaintySource(
    name="Source name",
    value=0.1,  # Standard uncertainty (1 sigma)
    uncertainty_type=UncertaintyType.TYPE_A,
    distribution=DistributionType.NORMAL,
    sensitivity_coefficient=1.0,
    degrees_of_freedom=9.0,
)
```

#### UncertaintyBudget

Complete uncertainty budget following GUM.

```python
UncertaintyBudget(
    measurement_id=1,
    sources=[...],
    combined_uncertainty=0.15,
    expanded_uncertainty=0.30,
    coverage_factor=2.0,
    confidence_level=95.0,
)
```

#### SPCResult

Results from complete SPC analysis.

```python
SPCResult(
    xbar_limits=ControlLimits(...),
    r_limits=ControlLimits(...),
    capability=CapabilityIndices(...),
    in_control=True,
    out_of_control_points=[],
    violations=[],
)
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=equipment --cov-report=html

# Run specific test file
pytest tests/test_spc.py -v
```

## Standards Compliance

This implementation follows:

- **GUM** (Guide to the Expression of Uncertainty in Measurement) - JCGM 100:2008
- **ISO/IEC 17025:2017** - General requirements for the competence of testing and calibration laboratories
- **ISO 9001** - Quality management systems
- **ILAC P14:09/2020** - ILAC Policy for Measurement Uncertainty in Calibration
- **Western Electric Rules** - Statistical process control rules

## Control Chart Constants

Control chart constants (A2, D3, D4, A3, B3, B4, d2, c4) are included for subgroup sizes 2-25, based on:
- Montgomery, D. C. (2009). Introduction to Statistical Quality Control, 6th Edition

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please ensure all tests pass and code follows the project standards.

## References

1. JCGM 100:2008 - Evaluation of measurement data — Guide to the expression of uncertainty in measurement
2. ISO/IEC 17025:2017 - General requirements for the competence of testing and calibration laboratories
3. Montgomery, D. C. (2009). Introduction to Statistical Quality Control
4. NIST Technical Note 1297 - Guidelines for Evaluating and Expressing the Uncertainty of NIST Measurement Results
