# PV Test Report Automation

World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## Overview

This system provides comprehensive automation for photovoltaic module testing, ensuring compliance with international standards and ISO 17025 accreditation requirements.

### Supported Standards

#### IEC Standards (Implemented)
- **IEC 62759** - Transportation Testing ✓ *Fully Implemented*

#### IEC Standards (Planned)
- **IEC 61215** - Crystalline silicon module efficiency
- **IEC 61730** - PV module safety
- **IEC 61853** - Module characterization
- **IEC 62716** - Design qualification (hot spots)
- **IEC 61701** - Salt-fog corrosion testing
- **IEC 62804** - Mechanical load testing
- **IEC 60904** - Reference cells and light characteristics

#### ISO/Quality Standards
- **ISO 17025** - Testing laboratory competence and traceability
- **ISO 9001** - Quality management systems
- **NABL** - National Accreditation Board for Testing and Calibration Laboratories
- **ILAC** - International Laboratory Accreditation Cooperation
- **BIS** - Bureau of Indian Standards

## Features

✓ Complete IEC 62759 Transportation Testing implementation
✓ Full test sequence automation (6 steps)
✓ Equipment integration (Solar Simulator, Load Frame, Thermal Chamber)
✓ ISO 17025 compliance and traceability
✓ Database models with SQLAlchemy
✓ Comprehensive measurement uncertainty tracking
✓ Personnel competence management
✓ Automated pass/fail determination
✓ Detailed test reporting
✓ Event logging and audit trails

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation

# Install dependencies
pip install -r requirements.txt

# Or install with setup.py
pip install -e .
```

### Basic Usage - IEC 62759

```python
from src.protocols.iec.iec_62759 import IEC62759Controller

# Create test controller
test = IEC62759Controller(module_id="PV-001")

# Run full test sequence
test.run_full_sequence()

# Get results
print(f"Power Degradation: {test.degradation_pct:.2f}%")
print(f"Pass/Fail: {test.result.pass_fail.value}")

# Generate report
report = test.generate_report()
```

## IEC 62759 Transportation Testing

### Test Sequence

1. **Initial Flash Test** - Measure baseline performance at STC
2. **Edge Loading** - 600 Pa static load for 1 hour with edge support
3. **Dynamic Mechanical Loading** - 1000 cycles at 1000 Pa (front and rear)
4. **Thermal Cycling** - 50 cycles: -40°C to +85°C
5. **Final Flash Test** - Measure final performance
6. **Visual Inspection** - Check for physical damage

### Pass Criteria

- ✓ No breakage during edge loading
- ✓ No breakage during dynamic loading
- ✓ Thermal cycling completed successfully
- ✓ Power degradation < 5%
- ✓ Visual inspection shows no defects

### Example with Custom Parameters

```python
from src.protocols.iec.iec_62759 import IEC62759Controller

test = IEC62759Controller(
    module_id="PV-002",
    test_id=12345,
    technician_id="TECH-001"
)

test.connect_equipment()

# Run individual steps with custom parameters
test.step1_initial_flash_test()
test.step2_edge_loading(load_pa=750, duration_hours=2.0)
test.step3_dynamic_mechanical_loading(frequency_hz=1.5)
test.step4_thermal_cycling(cycles=50)
test.step5_final_flash_test()
test.step6_visual_inspection()

# Calculate results
pass_fail = test.calculate_pass_fail()

test.disconnect_equipment()
```

## Database Models

### IEC62759Test

```python
from src.models.iec_62759 import IEC62759Test

test_record = IEC62759Test(
    test_id=12345,
    module_id="PV-001",
    initial_pmax=300.5,
    final_pmax=296.2,
    edge_load_result="pass",
    dynamic_load_result="pass",
    thermal_result="pass",
    visual_inspection_result="pass",
    pass_status=True,
    technician_id="TECH-001",
    created_by="TECH-001",
    updated_by="TECH-001"
)

test_record.calculate_degradation()
# power_degradation_pct = 1.43%
```

## ISO 17025 Compliance

### Traceability

- Complete measurement chain documentation
- Equipment calibration tracking
- Measurement uncertainty quantification
- Personnel competence verification

### Example

```python
from src.compliance.iso_17025.traceability import TraceabilityManager

tm = TraceabilityManager()

# Record measurement with full traceability
measurement = tm.record_measurement(
    measurement_id="M-12345-001",
    parameter="pmax",
    value=300.5,
    unit="W",
    equipment_id="SIM-001",
    technician_id="TECH-001",
    environmental_conditions={"temperature": 23.5, "humidity": 45.0}
)

# Get traceability chain
chain = tm.get_traceability_chain("M-12345-001")
```

## Project Structure

```
pv-test-report-automation/
├── src/
│   ├── protocols/
│   │   ├── base.py                 # Base protocol class
│   │   └── iec/
│   │       └── iec_62759.py        # IEC 62759 implementation
│   ├── models/
│   │   ├── base.py                 # Base database model
│   │   └── iec_62759.py            # IEC 62759 models
│   ├── equipment/
│   │   ├── base_equipment.py       # Base equipment interface
│   │   ├── solar_simulator.py      # Solar simulator
│   │   ├── load_frame.py           # Load frame
│   │   └── thermal_chamber.py      # Thermal chamber
│   ├── compliance/
│   │   └── iso_17025/
│   │       ├── traceability.py     # Traceability management
│   │       └── competence.py       # Personnel competence
│   └── utils/
│       ├── constants.py            # Standard constants
│       └── validators.py           # Data validation
├── examples/
│   └── iec_62759_example.py        # Example usage
├── docs/
│   └── IEC_62759_GUIDE.md          # Complete guide
├── tests/
│   └── unit/
│       └── test_iec_62759.py       # Unit tests
├── requirements.txt
├── setup.py
└── README.md
```

## Equipment Integration

### Solar Simulator
- STC measurement (1000 W/m², AM1.5G, 25°C)
- IV curve measurement
- Pmax, Voc, Isc, Fill Factor extraction

### Load Frame
- Static edge loading (0-5000 Pa)
- Dynamic loading with frequency control
- Deflection measurement
- Breakage detection

### Thermal Chamber
- Temperature range: -70°C to +180°C
- Programmable cycling profiles
- IEC 62759 profile: -40°C to +85°C

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/unit/test_iec_62759.py -v
```

### Code Formatting

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint
flake8 src/ tests/
```

## Documentation

See `docs/` directory for detailed documentation:
- `IEC_62759_GUIDE.md` - Complete IEC 62759 testing guide
- More documentation coming soon

## Examples

See `examples/` directory for usage examples:
- `iec_62759_example.py` - Comprehensive examples for IEC 62759

## Contributing

1. Follow PEP 8 style guidelines
2. Add unit tests for new features
3. Update documentation
4. Ensure ISO 17025 compliance

## License

MIT License - See LICENSE file

## Contact

For questions or support, please contact the development team.

## Roadmap

### Phase 1 (Completed)
- ✓ IEC 62759 Transportation Testing
- ✓ Equipment integration framework
- ✓ ISO 17025 compliance foundation
- ✓ Database models

### Phase 2 (Planned)
- IEC 61215 implementation
- IEC 61730 implementation
- Report generation (PDF/Excel)
- Web interface

### Phase 3 (Planned)
- LLM integration for analysis
- Multi-format export
- Workflow management
- Complete ISO 17025 audit support

## Standards References

- IEC 62759:2015 - Photovoltaic (PV) modules - Transportation testing
- ISO/IEC 17025:2017 - Testing laboratory competence
- IEC 60904-9 - Solar simulator performance requirements
