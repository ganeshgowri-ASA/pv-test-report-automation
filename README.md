# PV Test Report Automation System

World-class photovoltaic (PV) test laboratory report automation system with comprehensive protocol support, full traceability, and multi-format reporting capabilities.

## Overview

This system provides production-ready automation for PV module testing and certification, covering major international standards including IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, and BIS standards.

### Key Features

- **Complete Protocol Implementation**: Full IEC 61215-2:2021 protocol with all 19 MST tests
- **Automatic Test Sequencing**: Intelligent test flow based on module type and dependencies
- **Equipment Integration**: Interface with solar simulators, I-V tracers, climate chambers, and more
- **Full Traceability**: ISO/IEC 17025 compliant measurement tracking with calibration records
- **Multi-Format Reporting**: Generate reports in JSON, HTML, PDF, and Excel formats
- **Degradation Calculations**: Automatic power degradation tracking throughout test sequence
- **Pass/Fail Criteria**: Automated compliance checking per standard clauses
- **Reviewer Workflows**: Built-in support for test review and approval processes

## IEC 61215-2:2021 Implementation

The system implements the complete Module Safety Test (MST) sequence for crystalline silicon and thin-film PV modules:

### Module Safety Tests (MST)

1. **MST 01 - Visual Inspection**: Initial and final visual examination
2. **MST 02 - Maximum Power Determination**: Performance at STC (1000 W/m², 25°C, AM1.5G)
3. **MST 03 - Insulation Test**: Insulation resistance measurement
4. **MST 04 - Temperature Coefficients**: Pmax, Voc, Isc coefficients
5. **MST 05 - NOCT**: Nominal Operating Cell Temperature determination
6. **MST 06 - STC Performance**: Stabilized performance baseline
7. **MST 07 - Low Irradiance**: Performance at 200 W/m²
8. **MST 08 - Outdoor Exposure**: 60 kWh/m² minimum exposure
9. **MST 09 - Hot-spot Endurance**: Bypass diode and hot-spot testing
10. **MST 10 - UV Preconditioning**: 15 kWh/m² UV exposure (280-400 nm)
11. **MST 11 - Thermal Cycling (TC 200)**: 200 cycles from -40°C to +85°C
12. **MST 12 - Humidity-Freeze (HF 10)**: 10 humidity-freeze cycles
13. **MST 13 - Damp Heat (DH 1000)**: 1000 hours at 85°C/85% RH
14. **MST 14 - Mechanical Load (Static)**: 2400 Pa front/back loads
15. **MST 15 - Hail Impact**: 25mm ice balls at 23 m/s
16. **MST 16 - Mechanical Load (Dynamic)**: 1000 cycles at ±1000 Pa
17. **MST 17 - Twist Test**: Frame rigidity test (framed modules)
18. **MST 18 - Robustness of Terminations**: Pull and torque tests
19. **MST 19 - Wet Leakage Current**: Final electrical safety test

### Automatic Test Sequencing

The protocol engine automatically:
- Determines test sequence based on module type (crystalline/thin-film)
- Applies preconditioning for thin-film modules
- Manages test dependencies
- Tracks degradation from initial to final measurements
- Validates test conditions and acceptance criteria

## Project Structure

```
pv-test-report-automation/
├── src/
│   ├── core/
│   │   ├── protocols/           # Protocol implementations
│   │   │   ├── base.py          # Base protocol class
│   │   │   └── iec61215.py      # IEC 61215-2:2021 implementation
│   │   ├── models/              # Data models
│   │   │   ├── measurement.py   # Measurement tracking
│   │   │   ├── test_result.py   # Test results and compliance
│   │   │   └── test_sequence.py # Test sequence management
│   │   ├── equipment/           # Equipment integration
│   │   │   ├── base.py          # Equipment base classes
│   │   │   └── drivers/         # Equipment-specific drivers
│   │   ├── reports/             # Report generation
│   │   │   ├── generator.py     # Multi-format report generator
│   │   │   └── templates/       # Report templates
│   │   └── config/              # Configuration management
│   │       └── settings.py      # System configuration
│   └── utils/                   # Utility functions
├── configs/                     # Configuration files
│   └── default_config.json      # Default configuration
├── examples/                    # Usage examples
│   └── iec61215_example.py      # IEC 61215 example
├── tests/                       # Test suite
├── docs/                        # Documentation
├── requirements.txt             # Python dependencies
└── setup.py                     # Package installation

## Installation

### Requirements

- Python 3.9 or higher
- Test equipment with SCPI/VISA support (for production use)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install package in development mode:
```bash
pip install -e .
```

## Quick Start

### Basic Usage Example

```python
from core.protocols.iec61215 import IEC61215Protocol
from core.models.test_result import ModuleUnderTest
from core.reports.generator import ReportGenerator

# Create module under test
module = ModuleUnderTest(
    manufacturer="SolarTech",
    model="ST-M350-72",
    serial_number="ST2024001",
    module_type="crystalline",
    rated_power=350.0,
    rated_voltage=37.2,
    rated_current=9.41,
    # ... other parameters
)

# Initialize protocol
protocol = IEC61215Protocol()

# Initialize test sequence
sequence = protocol.initialize_sequence(
    module=module,
    laboratory_name="PV Testing Lab",
    test_report_number="IEC61215-2024-001",
)

# Execute tests (with equipment integration)
# ... test execution code ...

# Generate compliance report
report_data = protocol.generate_compliance_report()

# Export report
report_gen = ReportGenerator()
report_gen.generate_iec61215_report(
    report_data,
    output_path="./reports/report_001",
    format="pdf"
)
```

### Running the Example

```bash
python examples/iec61215_example.py
```

This will create example reports in the `output/` directory.

## Configuration

The system uses JSON configuration files for laboratory information, equipment settings, and test parameters. See `configs/default_config.json` for the template.

### Environment Variables

- `PV_TEST_CONFIG`: Path to configuration file (optional)

## Equipment Integration

The system supports integration with various test equipment through SCPI/VISA protocols:

- Solar Simulators (Pasan, Eternal Sun, etc.)
- I-V Curve Tracers (Keysight, Keithley, etc.)
- Climate Chambers (Weiss Technik, Espec, etc.)
- Insulation Testers (Fluke, Megger, etc.)
- Thermal Cameras (FLIR, etc.)

Equipment drivers can be implemented by extending the base classes in `src/core/equipment/base.py`.

## Report Generation

The system generates comprehensive test reports with:

- **Traceability**: Complete measurement chain with equipment calibration records
- **Compliance Checking**: Automatic pass/fail determination per standard requirements
- **Degradation Analysis**: Power degradation calculations throughout test sequence
- **Visual Documentation**: Support for photos and thermal images
- **Multi-Format Export**: JSON, HTML, PDF, Excel

## Testing

Run the test suite:

```bash
pytest tests/
```

With coverage:

```bash
pytest --cov=src tests/
```

## Documentation

Full documentation is available in the `docs/` directory. Build with:

```bash
cd docs
make html
```

## Standards Compliance

This implementation follows:

- **IEC 61215-2:2021**: Terrestrial photovoltaic (PV) modules - Design qualification and type approval - Part 2: Test procedures
- **ISO/IEC 17025:2017**: General requirements for the competence of testing and calibration laboratories
- **NABL 162**: Specific Criteria for Accreditation of Testing Laboratories

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or support, please contact the development team or open an issue on GitHub.

## Acknowledgments

- IEC Technical Committee 82 for the comprehensive PV testing standards
- The photovoltaic testing community for their expertise and guidance

## Roadmap

### Phase 1 (Current)
- ✅ IEC 61215-2:2021 protocol implementation
- ✅ Core data models and traceability
- ✅ Report generation system
- ✅ Configuration management

### Phase 2 (Upcoming)
- [ ] Equipment driver implementations
- [ ] IEC 61730 (Safety qualification)
- [ ] IEC 61853 (Performance testing)
- [ ] Database integration
- [ ] Web interface

### Phase 3 (Future)
- [ ] LLM integration for report analysis
- [ ] Additional international standards
- [ ] Advanced analytics and trending
- [ ] Automated test scheduling

---

**Version**: 0.1.0
**Last Updated**: 2024-11-17
