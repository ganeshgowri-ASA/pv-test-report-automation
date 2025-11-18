# PV Test Report Automation

World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## 🚀 Features

- **Standards Compliance**: IEC 61215, IEC 61730, IEC 61853, ISO/IEC 17025
- **Mechanical Load Testing**: Static and dynamic load tests with deflection monitoring
- **Power Degradation Analysis**: Pre/post flash measurements with automatic degradation calculation
- **ISO 17025 Traceability**: Complete equipment, operator, and environmental tracking
- **Comprehensive Reporting**: JSON-based reports with full audit trails
- **Extensible Architecture**: Modular test block design for easy extension

## 📋 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation

# Install the package
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

### Basic Usage

```python
from pv_automation.test_blocks.mechanical import MechanicalLoadTest, LoadType, PowerMeasurement

# Create a mechanical load test
test = MechanicalLoadTest(
    module_id="PV-001",
    load_type=LoadType.STATIC_FRONT,
    load_pa=2400.0,
    operator_name="John Smith"
)

# Set pre-test power measurement
pre_power = PowerMeasurement(
    pmax_w=450.0,
    voc_v=48.5,
    isc_a=11.2,
    vmp_v=40.2,
    imp_a=11.19,
    fill_factor=0.827
)
test.set_pre_test_power(pre_power)

# Add deflection measurements
test.add_deflection_measurement(load_pa=2400, deflection_mm=22.3)

# Set post-test power measurement
post_power = PowerMeasurement(
    pmax_w=448.5,
    voc_v=48.4,
    isc_a=11.18,
    vmp_v=40.1,
    imp_a=11.18,
    fill_factor=0.826
)
test.set_post_test_power(post_power)

# Execute test
result = test.execute()
print(f"Power Degradation: {test.power_degradation_pct}%")
print(f"Test Passed: {result}")
```

## 🧪 Test Blocks

### Mechanical Load Test (IEC 61215)

Comprehensive mechanical load testing for PV modules:

- **Static Load Testing**: Front and rear load at 2400 Pa
- **Dynamic Load Testing**: 1000 cycles at ±1000 Pa
- **Deflection Monitoring**: Real-time measurement with LVDT sensors
- **Pass Criteria**: < 5% power degradation

[Full Documentation](docs/mechanical_load_test.md)

#### Key Features

✓ Static and dynamic modes
✓ Deflection monitoring
✓ Power degradation analysis
✓ ISO 17025 traceability
✓ Comprehensive reporting

## 📁 Project Structure

```
pv-test-report-automation/
├── src/
│   └── pv_automation/
│       ├── models/               # Data models
│       │   ├── base.py          # Base Pydantic models
│       │   └── __init__.py
│       ├── test_blocks/          # Test implementations
│       │   ├── base_test_block.py  # Abstract base class
│       │   ├── mechanical/
│       │   │   ├── load_test.py    # Mechanical load test
│       │   │   └── __init__.py
│       │   └── __init__.py
│       ├── validators/           # IEC standard validators
│       ├── equipment/            # Equipment interfaces
│       └── utils/                # Utility functions
├── tests/                        # Unit tests
│   ├── test_mechanical_load.py
│   └── __init__.py
├── examples/                     # Example scripts
│   └── mechanical_load_example.py
├── docs/                         # Documentation
│   └── mechanical_load_test.md
├── pyproject.toml               # Project configuration
├── README.md
└── LICENSE
```

## 🧩 Architecture

### BaseModel

All data models inherit from `BaseModel` which provides:
- Unique ID generation
- Timestamp tracking (created_at, updated_at)
- Version tracking for migrations
- Pydantic validation

### BaseTestBlock

Abstract base class for all test blocks providing:
- Test lifecycle management (pending, running, passed, failed)
- ISO 17025 traceability fields
- Environmental condition tracking
- Error and warning handling
- Abstract methods: `validate_input_data()`, `execute()`, `generate_report()`

### MechanicalLoadTest

Concrete implementation for IEC 61215 mechanical load testing:
- Static and dynamic load modes
- Deflection measurement tracking
- Power degradation calculation
- Statistical analysis
- Pass/fail evaluation

## 📊 Test Equipment Integration

The system is designed to interface with:

1. **Pressure Chambers/Load Frames**: Apply uniform mechanical loads
2. **LVDT Sensors**: Monitor deflection in real-time
3. **Pressure Transducers**: Verify applied loads
4. **IV Tracers**: Pre/post flash measurements

## 🔬 ISO 17025 Compliance

Full traceability support:
- Equipment ID tracking with calibration records
- Operator identification
- Environmental monitoring (temperature, humidity, pressure)
- Test procedure versioning
- Complete audit trails with timestamps
- Statistical analysis of measurements

## 📝 Examples

### Static Front Load Test

```bash
python examples/mechanical_load_example.py
```

This runs three complete examples:
1. Static front load test (passing)
2. Dynamic load test (passing)
3. Failed test due to excessive degradation

### Run Unit Tests

```bash
# Run all tests
pytest tests/test_mechanical_load.py -v

# Run with coverage
pytest tests/test_mechanical_load.py --cov=src/pv_automation --cov-report=html

# Run specific test class
pytest tests/test_mechanical_load.py::TestPowerDegradation -v
```

## 📖 Documentation

- [Mechanical Load Test Block](docs/mechanical_load_test.md) - Complete API reference and usage guide

## 🛠️ Development

### Setup Development Environment

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check src/

# Format code
black src/ tests/

# Type checking
mypy src/
```

### Running Tests

```bash
# Run all tests with coverage
pytest --cov=src/pv_automation --cov-report=term-missing

# Run specific test file
pytest tests/test_mechanical_load.py -v

# Run tests matching a pattern
pytest -k "deflection" -v
```

## 🤝 Contributing

1. Follow IEC 61215, IEC 61730, and ISO 17025 standards
2. Add comprehensive unit tests for new features
3. Update documentation
4. Maintain backwards compatibility
5. Include error handling and validation

## 📋 Standards Coverage

- ✅ **IEC 61215**: Mechanical load testing
- 🔄 **IEC 61730**: Safety qualification (planned)
- 🔄 **IEC 61853**: Performance testing (planned)
- ✅ **ISO/IEC 17025**: Laboratory traceability
- 🔄 **IEC 62716**: Ammonia corrosion (planned)
- 🔄 **IEC 61701**: Salt mist corrosion (planned)

## 📜 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🔗 References

- [IEC 61215-2:2021](https://webstore.iec.ch/publication/68559) - PV module design qualification
- [ISO/IEC 17025:2017](https://www.iso.org/standard/66912.html) - Testing laboratory requirements
- [IEC 61853](https://webstore.iec.ch/publication/6035) - PV module performance testing

## 📞 Support

For questions or issues, please open an issue on GitHub.

---

**Phase 4 | Session 26 | Mechanical Load Test Block** ✅
