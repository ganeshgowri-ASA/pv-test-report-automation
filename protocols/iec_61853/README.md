# IEC 61853 Performance Testing Protocol

Comprehensive implementation of IEC 61853 series for photovoltaic module performance testing and energy rating.

## Overview

This package provides a complete, production-ready implementation of:

- **IEC 61853-1**: Performance at STC and varying irradiance/temperature conditions
- **IEC 61853-2**: Spectral responsivity and angle of incidence measurements
- **IEC 61853-3**: Energy rating calculations for multiple climate zones
- **IEC 61853-4**: Standard reference climatic profiles

## Features

### ✓ Automated Test Control
- Temperature chamber automation with PID control
- 35-point performance matrix (7 irradiance × 5 temperature)
- Real-time stabilization monitoring
- Safety interlocks and error handling

### ✓ Advanced Data Analysis
- 3D performance surface modeling: Pmax(G, T)
- Temperature coefficient extraction (α, β, γ)
- Polynomial regression with quality metrics (R², RMSE)
- Irradiance linearity analysis

### ✓ Comprehensive Characterization
- Spectral response measurement (300-1200 nm)
- Angular response testing (0-75°)
- Spectral mismatch factor calculation
- Incidence angle modifier (IAM) extraction

### ✓ Energy Rating
- Location-specific annual energy yield
- 4 standard climate zones (IEC 61853-4)
- Performance ratio calculations
- Energy rating classification (A+ to E)

### ✓ Professional Reporting
- 3D performance surface visualizations
- Temperature coefficient plots
- Performance matrix heatmaps
- Energy rating comparison charts
- ISO 17025 compliant reports

## Installation

```bash
# Clone repository
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

```
numpy >= 1.21.0
scipy >= 1.7.0
scikit-learn >= 1.0.0
matplotlib >= 3.4.0
pydantic >= 1.9.0
sqlalchemy >= 1.4.0
```

## Quick Start

### Basic Usage

```python
from protocols.iec_61853 import IEC61853TestController

# Initialize test
test = IEC61853TestController(
    module_serial="PV-2025-001234",
    test_lab="NABL Lab XYZ",
    module_manufacturer="SolarCorp",
    module_model="SC-300M",
    rated_power=300.0
)

# Run complete test series
results = test.run_complete_test_series(
    include_spectral=True,
    include_energy_rating=True
)

# Generate report
test.generate_report("iec61853_report.pdf")

# Export data
test.export_results(output_dir="./results")
```

### Step-by-Step Workflow

```python
# 1. Run performance matrix (IEC 61853-1)
matrix_results = test.run_performance_matrix()
print(f"Completed {matrix_results.successful_points} test points")

# 2. Analyze performance
analysis = test.analyze_performance()
print(f"γ (Pmax): {analysis['temperature_coefficients']['gamma_pmax']:.3f} %/°C")

# 3. Run spectral/angular tests (IEC 61853-2)
spectral_results = test.run_spectral_angular_tests()
print(f"IAM factor: {spectral_results['angular_response']['iam_factor']:.3f}")

# 4. Calculate energy ratings (IEC 61853-3)
energy_results = test.calculate_energy_ratings()
for location, data in energy_results['location_results'].items():
    print(f"{location}: {data['annual_energy_kwh']:.1f} kWh/year")
```

### Custom Test Configuration

```python
from protocols.iec_61853 import MatrixTestConfig, TestSequenceMode

# Custom matrix configuration
config = MatrixTestConfig(
    temperatures=[-10, 15, 25, 40, 60],  # Custom temp points
    irradiances=[100, 400, 800, 1000, 1200],  # Custom irradiance
    sequence_mode=TestSequenceMode.OPTIMIZED,  # Minimize thermal cycles
    max_retries=3,
    validation_enabled=True
)

test.run_performance_matrix(config=config)
```

## Architecture

### Module Structure

```
protocols/iec_61853/
├── __init__.py                 # Package initialization
├── models.py                   # Data models (Pydantic & SQLAlchemy)
├── temperature_control.py      # Chamber automation
├── performance_matrix.py       # 35-point matrix testing
├── spectral_response.py        # Spectral/angular measurements
├── data_analyzer.py            # Performance surface analysis
├── energy_rating.py            # Energy yield calculations
├── test_controller.py          # Main orchestration
├── report_generator.py         # Report generation
├── test_iec_61853.py          # Unit tests
└── README.md                   # This file
```

### Key Components

#### 1. Temperature Control
```python
from protocols.iec_61853.temperature_control import ChamberController

controller = ChamberController(chamber)
controller.goto_temperature(25.0, wait_stable=True)
```

#### 2. Performance Matrix
```python
from protocols.iec_61853.performance_matrix import PerformanceMatrixTest

matrix_test = PerformanceMatrixTest(
    chamber_controller=chamber_ctrl,
    iv_acquisition=iv_acq
)
results = matrix_test.run_matrix_test()
```

#### 3. Data Analysis
```python
from protocols.iec_61853.data_analyzer import PerformanceAnalyzer

analyzer = PerformanceAnalyzer(matrix_results)
surface = analyzer.fit_performance_surface(polynomial_degree=2)
temp_coeff = analyzer.extract_temperature_coefficients()
```

#### 4. Energy Rating
```python
from protocols.iec_61853.energy_rating import EnergyRatingCalculator

calculator = EnergyRatingCalculator(
    performance_surface=surface,
    temperature_coefficients=temp_coeff,
    rated_power=300.0
)
ratings = calculator.calculate_multiple_locations()
```

## Test Standards Compliance

### IEC 61853-1: Performance Testing
- ✓ 35-point matrix (7 irradiance × 5 temperature)
- ✓ Temperature range: -25°C to +75°C
- ✓ Irradiance range: 100 to 1100 W/m²
- ✓ Full I-V curve at each point
- ✓ AM1.5G reference spectrum

### IEC 61853-2: Spectral & Angular
- ✓ Spectral response: 300-1200 nm
- ✓ Angular response: 0-75°
- ✓ Spectral mismatch factor
- ✓ Incidence angle modifier

### IEC 61853-3: Energy Rating
- ✓ Annual energy yield calculation
- ✓ 4 standard climate zones
- ✓ Performance ratio
- ✓ Energy rating classification

### ISO 17025 Compliance
- ✓ Full traceability
- ✓ Uncertainty analysis
- ✓ Quality metrics
- ✓ Calibration tracking

## Data Models

### Performance Matrix Point
```python
@dataclass
class MatrixTestPointData:
    temperature: float  # °C
    irradiance: float  # W/m²
    iv_curve: IVCurve
    timestamp: datetime
    chamber_temp_actual: float
    chamber_temp_stability: float
    irradiance_uniformity: float
```

### Temperature Coefficients
```python
@dataclass
class TemperatureCoefficients:
    alpha_isc: float  # %/°C (current)
    beta_voc: float   # %/°C (voltage)
    gamma_pmax: float # %/°C (power)
    reference_temperature: float
    reference_irradiance: float
    r_squared_pmax: float
```

### Energy Rating
```python
@dataclass
class EnergyRatingData:
    location_profile: LocationProfileData
    annual_energy_kwh: float
    specific_yield_kwh_kwp: float
    performance_ratio: float
    energy_rating_class: str  # A+, A, B, C, D, E
```

## Testing

### Run Unit Tests
```bash
cd protocols/iec_61853
python -m pytest test_iec_61853.py -v
```

### Test Coverage
- Temperature control: 8 tests
- I-V acquisition: 3 tests
- Performance matrix: 3 tests
- Spectral/angular: 4 tests
- Data analysis: 3 tests
- Energy rating: 3 tests
- Integration: 1 test

## Hardware Integration

### Supported Equipment

#### Temperature Chambers
- Espec SU-series
- Weiss WKL/WK series
- Vötsch VC series
- Generic RS-232/RS-485/Ethernet

#### I-V Measurement
- Keithley 2400/2600 series
- Solar simulator integration
- Custom DAQ systems

#### Spectral Measurement
- Monochromator systems
- Reference cells
- Spectroradiometers

### Hardware Abstraction
All hardware interfaces use abstract base classes for easy integration:

```python
class TemperatureChamber(ABC):
    @abstractmethod
    def set_temperature(self, temperature: float) -> bool:
        pass

    @abstractmethod
    def get_temperature(self) -> float:
        pass
```

## Examples

### Example 1: Quick Performance Test
```python
# Quick performance characterization
test = IEC61853TestController(
    module_serial="TEST-001",
    test_lab="My Lab"
)

# Run matrix with default settings
test.run_performance_matrix()

# Get summary
summary = test.get_summary()
print(summary)
```

### Example 2: Custom Analysis
```python
# Run test
test.run_performance_matrix()
test.analyze_performance()

# Access analysis results
analyzer = test.analyzer
surface = analyzer.get_performance_surface()

# Predict performance at custom conditions
pmax_predicted = surface.predict(irradiance=850, temperature=35)
print(f"Predicted Pmax at 850W/m², 35°C: {pmax_predicted:.2f}W")
```

### Example 3: Energy Comparison
```python
# Calculate energy for specific locations
locations = ["Nicosia", "Phoenix", "Mumbai", "Aachen"]
energy_results = test.calculate_energy_ratings(locations=locations)

# Compare locations
for loc, data in energy_results['location_results'].items():
    print(f"{loc}:")
    print(f"  Energy: {data['annual_energy_kwh']:.0f} kWh/year")
    print(f"  Class: {data['energy_class']}")
    print(f"  PR: {data['performance_ratio']:.3f}")
```

## Troubleshooting

### Common Issues

1. **Chamber not stabilizing**
   - Check stabilization criteria
   - Verify chamber control is working
   - Increase max_wait_time

2. **Low R² in surface fit**
   - Check data quality
   - Verify all test points completed
   - Consider polynomial degree

3. **Import errors**
   - Install all dependencies
   - Check Python version (≥3.8)
   - Verify package installation

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Create Pull Request

## License

MIT License - See LICENSE file for details

## References

- IEC 61853-1:2011 - PV module performance testing at STC and varying conditions
- IEC 61853-2:2016 - Spectral responsivity and angle of incidence
- IEC 61853-3:2018 - Energy rating of PV modules
- IEC 61853-4:2018 - Standard reference climatic profiles
- ISO/IEC 17025:2017 - General requirements for testing laboratories

## Contact

For questions and support:
- GitHub Issues: https://github.com/ganeshgowri-ASA/pv-test-report-automation/issues
- Documentation: https://github.com/ganeshgowri-ASA/pv-test-report-automation/wiki

## Version History

### v1.0.0 (2025-01-18)
- Initial release
- Complete IEC 61853-1 implementation
- IEC 61853-2 spectral/angular testing
- IEC 61853-3 energy rating
- Comprehensive test suite
- Report generation
- ISO 17025 compliance
