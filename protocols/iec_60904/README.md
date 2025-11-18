# IEC 60904 Series - PV Electrical Performance Measurement

Production-ready implementation of IEC 60904 series standards for photovoltaic device electrical performance measurement.

## Standards Implemented

- **IEC 60904-1**: I-V curve measurement with 4-wire Kelvin sensing
- **IEC 60904-2**: Reference solar cell calibration and management
- **IEC 60904-3**: Measurement principles for terrestrial PV devices
- **IEC 60904-5**: Open circuit voltage determination
- **IEC 60904-7**: Spectral mismatch computation
- **IEC 60904-8**: Spectral response measurement
- **IEC 60904-9**: Solar simulator performance verification
- **IEC 60904-10**: Linearity measurements

## Features

✓ Full 4-wire Kelvin sensing for accurate I-V measurements
✓ Minimum 100 data points per curve
✓ Automated parameter extraction (Voc, Isc, Vmp, Imp, Pmax, FF)
✓ Reference cell calibration with traceability
✓ Spectral mismatch factor calculation
✓ Solar simulator Class A/B/C verification
✓ ISO 17025 compliance
✓ Comprehensive unit tests

## Quick Start

### I-V Curve Measurement

```python
from protocols.iec_60904 import IVMeasurement

# Initialize measurement system
iv = IVMeasurement(
    module_serial="PV-001",
    area=1.6,  # m²
    wire_config=WireConfiguration.FOUR_WIRE_KELVIN
)

# Perform measurement at STC (1000 W/m², 25°C)
result = iv.measure_iv_curve(
    irradiance=1000.0,
    temperature=25.0
)

print(f"Pmax: {result.pmax:.2f} W")
print(f"Efficiency: {result.efficiency:.2f}%")
print(f"Fill Factor: {result.ff:.3f}")
print(f"Voc: {result.voc:.2f} V")
print(f"Isc: {result.isc:.2f} A")
```

### Reference Cell Calibration

```python
from protocols.iec_60904 import ReferenceCell, CellType

# Create primary reference cell
primary = ReferenceCell(
    cell_serial="PRIMARY-001",
    cell_type=CellType.PRIMARY,
    active_area=4.0  # cm²
)

# Calibrate using spectral response method
calibration = primary.calibrate_primary(
    spectral_response=spectral_response_data,
    reference_spectrum=am15g_spectrum,
    measured_current=0.400,  # A
    temperature=25.0,
    traceability="NIST"
)

# Measure irradiance
irradiance, uncertainty = primary.measure_irradiance(
    measured_current=0.395,
    temperature=26.0
)
print(f"Irradiance: {irradiance:.1f} ± {uncertainty:.1f}% W/m²")
```

### Spectral Mismatch Calculation

```python
from protocols.iec_60904 import SpectralMismatch

# Initialize calculator
sm = SpectralMismatch()

# Create simulator spectrum
test_spectrum = sm.create_simulator_spectrum(
    spectrum_type="xenon",
    class_rating="A"
)

# Create device spectral responses
dut_response = sm.create_typical_csi_response()
ref_response = sm.create_typical_csi_response()

# Calculate mismatch factor
result = sm.calculate_mismatch_factor(
    test_spectrum=test_spectrum,
    dut_spectral_response=dut_response,
    ref_cell_spectral_response=ref_response
)

print(f"Mismatch Factor M: {result['mismatch_factor']:.4f}")
print(f"Uncertainty: ±{result['uncertainty_percent']:.1f}%")

# Apply correction
corrected_isc, correction_pct = sm.apply_correction(
    measured_value=9.50,  # A
    mismatch_factor=result['mismatch_factor']
)
print(f"Corrected Isc: {corrected_isc:.3f} A ({correction_pct:+.1f}%)")
```

### Solar Simulator Verification

```python
from protocols.iec_60904 import SimulatorVerification, SimulatorType
import numpy as np

# Initialize verification system
sim = SimulatorVerification(
    simulator_id="SIM-AAA-001",
    simulator_type=SimulatorType.CONTINUOUS
)

# Perform spectral match verification
spectral_result = sim.verify_spectral_match(
    measured_spectrum=measured_spectrum_data,
    reference_spectrum=am15g_spectrum
)
print(f"Spectral Class: {spectral_result['spectral_classification']}")

# Verify spatial uniformity
irradiance_grid = np.array([...])  # 2D grid measurements
uniformity_result = sim.verify_non_uniformity(
    irradiance_grid=irradiance_grid,
    test_plane_area_cm2=1600.0
)
print(f"Non-uniformity: {uniformity_result['non_uniformity_percent']:.1f}%")
print(f"Uniformity Class: {uniformity_result['uniformity_classification']}")

# Verify temporal stability
irradiance_time_series = np.array([...])  # Time series data
stability_result = sim.verify_temporal_instability(
    irradiance_time_series=irradiance_time_series,
    sampling_rate_hz=1000.0,
    measurement_duration_s=10.0
)
print(f"Temporal Instability: {stability_result['temporal_instability_percent']:.1f}%")
print(f"Stability Class: {stability_result['stability_classification']}")

# Full verification
verification = sim.perform_full_verification(
    measured_spectrum=measured_spectrum,
    reference_spectrum=reference_spectrum,
    irradiance_grid=irradiance_grid,
    test_plane_area_cm2=1600.0,
    irradiance_time_series=irradiance_time_series,
    sampling_rate_hz=1000.0,
    measurement_duration_s=10.0
)

print(f"Overall Classification: {verification.classification.value}")
print(f"Compliant: {verification.compliant}")
print("Recommendations:")
for rec in verification.recommendations:
    print(f"  - {rec}")
```

### Linearity Test (IEC 60904-10)

```python
# Test linearity at multiple irradiance levels
irradiance_levels = [200, 400, 600, 800, 1000]
linearity_result = iv.perform_linearity_test(
    irradiance_levels=irradiance_levels,
    temperature=25.0
)

print(f"R²: {linearity_result['linearity']['r_squared']:.4f}")
print(f"Max Deviation: {linearity_result['linearity']['max_deviation_percent']:.2f}%")
print(f"Compliant: {linearity_result['compliant']}")
```

## Key Parameters

### I-V Measurement (IEC 60904-1)
- **Voltage sweep**: 0V to Voc + 10%
- **Current range**: 0 to Isc + 10%
- **Minimum points**: 100 per curve
- **Measurement speed**: <20ms per point
- **Wire configuration**: 4-wire Kelvin sensing (recommended)

### Solar Simulator Classes (IEC 60904-9)

| Parameter | Class A | Class B | Class C |
|-----------|---------|---------|---------|
| Spectral Match | 0.75-1.25 | 0.6-1.4 | 0.4-2.0 |
| Non-uniformity | ≤2% | ≤5% | ≤10% |
| Temporal Instability | ≤2% | ≤5% | ≤10% |

### Reference Cell Calibration (IEC 60904-2)
- **Traceability**: NIST/NPL/PTB
- **Uncertainty**: <1% for primary, <2% for secondary
- **Recalibration**: Annually for primary, bi-annually for secondary
- **Temperature coefficient**: Determined by multi-point measurement

## ISO 17025 Compliance

All modules include features for ISO 17025 compliance:
- ✓ Traceability to national standards
- ✓ Uncertainty budgets
- ✓ Calibration records and certificates
- ✓ Measurement validation
- ✓ Quality control checks

## Testing

Run comprehensive unit tests:

```bash
python -m pytest protocols/iec_60904/test_iec_60904.py -v
```

Or using unittest:

```bash
python protocols/iec_60904/test_iec_60904.py
```

## Data Export

All results support JSON export for integration with reporting systems:

```python
# I-V result export
result_json = result.to_json()

# Calibration certificate export
certificate = reference_cell.get_calibration_certificate()

# Verification report export
verification_json = verification.to_json()
```

## Requirements

- Python 3.8+
- NumPy ≥1.21.0
- SciPy ≥1.7.0 (optional, for advanced analysis)

## Standards References

- IEC 60904-1:2020 - Photovoltaic devices - Part 1: Measurement of photovoltaic current-voltage characteristics
- IEC 60904-2:2023 - Photovoltaic devices - Part 2: Requirements for photovoltaic reference devices
- IEC 60904-7:2019 - Photovoltaic devices - Part 7: Computation of the spectral mismatch correction for measurements of photovoltaic devices
- IEC 60904-9:2020 - Photovoltaic devices - Part 9: Classification of solar simulator characteristics
- IEC 60904-10:2020 - Photovoltaic devices - Part 10: Methods of linearity measurement

## License

See LICENSE file in repository root.
