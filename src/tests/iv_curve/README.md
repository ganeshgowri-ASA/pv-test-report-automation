# I-V Curve Analysis System

**Production-ready I-V curve analysis per IEC 60904-1:2020**

## Overview

Comprehensive photovoltaic I-V curve analysis system implementing international standards for solar module testing and characterization.

## Standards Compliance

- **IEC 60904-1:2020** - Measurement of photovoltaic current-voltage characteristics
- **IEC 60904-7** - Computation of spectral mismatch error
- **IEC 61215-2:2021** - Terrestrial photovoltaic modules - Design qualification and type approval
- **ISO/IEC 17025** - General requirements for testing and calibration laboratories

## Features

### 1. I-V Curve Analyzer (`analyzer.py`)

- **Data Parsing**: Multiple input formats (arrays, dictionaries, tuples)
- **Parameter Extraction**:
  - Open-circuit voltage (Voc)
  - Short-circuit current (Isc)
  - Maximum power point (Vmp, Imp, Pmax)
  - Fill factor (FF)
- **Series and Shunt Resistance**: Calculation using slope and derivative methods
- **Curve Fitting**: Single-diode equivalent circuit model
- **Smoothing**: Savitzky-Golay filtering for noise reduction
- **Visualization**: I-V and P-V curve plotting with MPP marking
- **Comparison Charts**: Before/after stress test analysis
- **Data Validation**: Quality checks per IEC 60904-1

### 2. STC Calculator (`stc_calculator.py`)

- **Translation Methods**:
  - IEC 60904-1 standard procedure
  - Linear approximation (fast)
  - Advanced non-linear corrections
- **Temperature Correction**:
  - Temperature coefficients (α, β, γ)
  - Absolute and relative coefficient support
- **Irradiance Correction**:
  - Linear current scaling
  - Logarithmic voltage correction
- **Spectral Mismatch**: IEC 60904-7 correction factor
- **Uncertainty Budget**: ISO/IEC 17025 compliant uncertainty analysis

### 3. NOCT Calculator (`noct_calculator.py`)

- **NOCT Determination**: From field measurements to standard conditions
- **Operating Temperature**: Prediction from ambient conditions
- **Thermal Modeling**:
  - Ross coefficient calculation
  - Heat loss coefficient
  - Thermal time constant
- **Mounting Corrections**: Open rack, roof integrated, BIPV, etc.
- **Power Prediction**: At real operating conditions
- **Validation**: Technology-specific NOCT range checking

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install specific requirements
pip install numpy scipy matplotlib pandas
```

## Quick Start

### Basic I-V Analysis

```python
import numpy as np
from src.tests.iv_curve import IVCurveAnalyzer, IVCurveData

# Create analyzer
analyzer = IVCurveAnalyzer(smoothing=True)

# Load your I-V data
voltage = np.array([0, 5, 10, 15, 20, 25, 30, 35, 40])
current = np.array([8.5, 8.4, 8.2, 7.8, 7.2, 6.0, 4.0, 1.5, 0])

# Create I-V curve object
iv_data = IVCurveData(
    voltage=voltage,
    current=current,
    temperature=25.0,
    irradiance=1000.0
)

# Calculate parameters
params = analyzer.calculate_parameters(iv_data)

print(f"Voc: {params['Voc']:.2f} V")
print(f"Isc: {params['Isc']:.2f} A")
print(f"Pmax: {params['Pmax']:.2f} W")
print(f"FF: {params['FF']:.4f}")

# Plot I-V curve
analyzer.plot_iv_curve(iv_data, params, save_path='iv_curve.png')
```

### Translate to STC

```python
from src.tests.iv_curve import STCCalculator, TemperatureCoefficients

calculator = STCCalculator()

# Measured parameters at non-STC conditions
measured = {
    'Isc': 8.2,
    'Voc': 36.5,
    'Imp': 7.5,
    'Vmp': 29.2,
    'Pmax': 219.0,
    'FF': 0.731
}

# Temperature coefficients (typical c-Si)
temp_coeff = TemperatureCoefficients(
    alpha_isc=0.05,     # %/°C
    beta_voc=-0.35,     # %/°C
    gamma_pmax=-0.45,   # %/°C
    is_relative=True
)

# Measurement conditions
conditions = {
    'temperature': 45.0,  # °C
    'irradiance': 800.0   # W/m²
}

# Translate to STC (25°C, 1000 W/m²)
stc_params = calculator.translate_to_stc(
    measured,
    temp_coeff,
    conditions,
    method='iec60904'
)

print(f"Pmax at STC: {stc_params['Pmax_stc']:.2f} W")
print(f"Voc at STC: {stc_params['Voc_stc']:.2f} V")
print(f"Isc at STC: {stc_params['Isc_stc']:.2f} A")
```

### NOCT Analysis

```python
from src.tests.iv_curve import NOCTCalculator, ThermalParameters

calculator = NOCTCalculator()

# Calculate NOCT from measurements
noct = calculator.calculate_noct_from_measurements(
    cell_temperature=55.0,
    ambient_temperature=28.0,
    irradiance=950.0,
    wind_speed=0.5
)

print(f"Calculated NOCT: {noct:.1f}°C")

# Predict operating temperature
thermal_params = ThermalParameters(noct=45.0)

T_operating = calculator.calculate_operating_temperature(
    thermal_params,
    ambient_temperature=35.0,
    irradiance=1000.0,
    wind_speed=2.0
)

print(f"Operating temperature: {T_operating:.1f}°C")

# Predict power at operating conditions
power_results = calculator.predict_power_at_operating_conditions(
    rated_power_stc=300.0,
    thermal_params=thermal_params,
    temp_coefficient_power=-0.40,
    operating_conditions={
        'ambient_temperature': 35.0,
        'irradiance': 1000.0,
        'wind_speed': 2.0
    }
)

print(f"Operating power: {power_results['power_operating']:.1f} W")
print(f"Temperature loss: {power_results['power_loss_temperature']:.1f}%")
```

## Advanced Usage

### Series and Shunt Resistance

```python
# Calculate resistances
rs = analyzer.calculate_series_resistance(iv_data, method='slope')
rsh = analyzer.calculate_shunt_resistance(iv_data, method='slope')

print(f"Series resistance: {rs:.4f} Ω")
print(f"Shunt resistance: {rsh:.2f} Ω")
```

### Single-Diode Model Fitting

```python
# Fit single-diode equivalent circuit
model_params = analyzer.fit_single_diode_model(iv_data)

print(f"Light current (IL): {model_params['IL']:.3f} A")
print(f"Saturation current (I0): {model_params['I0']:.2e} A")
print(f"Ideality factor (n): {model_params['n']:.3f}")
```

### Comparison of Before/After Curves

```python
# Plot comparison (e.g., before and after stress test)
fig = analyzer.plot_comparison(
    iv_data_before,
    iv_data_after,
    labels=("Initial", "After 1000h DH"),
    title="Damp Heat Test Comparison",
    save_path='comparison.png'
)
```

### Uncertainty Analysis

```python
from src.tests.iv_curve import UncertaintyComponents

# Define uncertainty components
uncertainty = UncertaintyComponents(
    measurement_repeatability=0.5,
    voltage_measurement=0.3,
    current_measurement=0.5,
    temperature_measurement=0.2,
    irradiance_measurement=1.0,
    temperature_correction=0.5,
    irradiance_correction=0.8,
    spectral_mismatch=0.5
)

# Calculate total uncertainty
analysis = calculator.calculate_uncertainty(uncertainty, 'Pmax')

print(f"Expanded uncertainty (k=2): ±{analysis['expanded_uncertainty_k2']:.2f}%")
```

## Data Validation

```python
from src.tests.iv_curve import validate_iv_data

# Validate I-V curve data
is_valid, errors = validate_iv_data(
    iv_data,
    min_points=10,
    max_noise_ratio=0.1
)

if is_valid:
    print("Data validation: PASS")
else:
    print("Data validation: FAIL")
    for error in errors:
        print(f"  - {error}")
```

## Testing

```python
# Run module tests
python -m pytest src/tests/iv_curve/

# Run specific module
python src/tests/iv_curve/analyzer.py
python src/tests/iv_curve/stc_calculator.py
python src/tests/iv_curve/noct_calculator.py
```

## API Reference

### Main Classes

- **`IVCurveAnalyzer`**: Comprehensive I-V curve analysis
- **`STCCalculator`**: STC translation and uncertainty analysis
- **`NOCTCalculator`**: NOCT calculation and thermal modeling

### Data Classes

- **`IVCurveData`**: Container for I-V curve measurements
- **`TemperatureCoefficients`**: Temperature coefficient specification
- **`ThermalParameters`**: Module thermal characteristics
- **`UncertaintyComponents`**: Uncertainty budget components

### Utility Functions

- **`validate_iv_data()`**: Data quality validation
- **`estimate_temperature_coefficients()`**: Coefficient estimation from dual-temperature measurements
- **`calculate_inoct_power()`**: Power at INOCT conditions
- **`calculate_module_efficiency_at_noct()`**: Efficiency analysis

## Error Handling

All functions include comprehensive error checking:
- Input validation
- Physical constraint verification
- Range checking
- Warning generation for suspicious results

## Performance

- Efficient NumPy/SciPy operations
- Smoothing algorithms optimized for PV data
- Vectorized calculations where possible

## Contributing

Follow IEC standards when adding features:
1. Document standard compliance
2. Include validation against reference data
3. Add uncertainty analysis where applicable
4. Provide example usage

## References

1. IEC 60904-1:2020 - Photovoltaic devices - Part 1: Measurement of photovoltaic current-voltage characteristics
2. IEC 60904-7:2019 - Photovoltaic devices - Part 7: Computation of the spectral mismatch correction for measurements of photovoltaic devices
3. IEC 61215-2:2021 - Terrestrial photovoltaic (PV) modules - Design qualification and type approval
4. ISO/IEC 17025:2017 - General requirements for the competence of testing and calibration laboratories

## License

MIT License

## Version

1.0.0 - Production Release
