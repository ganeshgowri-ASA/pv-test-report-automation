# PV Test Report Automation

World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## Features

- **Automated Test Blocks** - Pre-built test implementations for IEC standards
- **Equipment Integration** - Support for industry-standard test equipment
- **ISO 17025 Compliance** - Full traceability and uncertainty analysis
- **Data Logging** - Structured JSON and CSV data export
- **Report Generation** - Multi-format export (PDF, Excel, JSON)
- **Audit Trail** - Complete test history and operator tracking

## Implemented Test Blocks

### ✅ Insulation Resistance Test
**Standards**: IEC 61215-2:2016 / IEC 61730-2:2016

Automated testing of electrical insulation integrity with:
- Wet/dry condition testing
- 500V/1000V test voltage support
- Automatic pass/fail evaluation
- Equipment integration (Megohmmeter)
- ISO 17025 compliant records

**Quick Start**:
```python
from test_blocks.insulation import InsulationResistanceTest

with InsulationResistanceTest(module="PV-001") as test:
    result = test.measure(voltage=1000, condition="wet")
    print(f"Resistance: {result.test.resistance_mohm} MΩ - {'PASS' if result.test.pass_status else 'FAIL'}")
```

See [Documentation](docs/insulation_resistance_test.md) | [Examples](examples/insulation_test_example.py)

## Installation

```bash
# Clone repository
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e ".[dev]"
```

## Project Structure

```
pv-test-report-automation/
├── src/
│   ├── test_blocks/          # Test block implementations
│   │   └── insulation/       # Insulation resistance test
│   ├── models/               # Data models (Pydantic)
│   ├── equipment/            # Equipment drivers
│   ├── compliance/           # ISO 17025, NABL, etc.
│   └── logging/              # Data logging
├── tests/                    # Unit tests
├── examples/                 # Usage examples
├── docs/                     # Documentation
└── requirements.txt          # Dependencies
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test block
pytest tests/test_blocks/test_insulation_resistance.py -v
```

## Examples

See the [examples](examples/) directory for complete usage examples:

```bash
# Run insulation test example
python examples/insulation_test_example.py
```

## Documentation

- [Insulation Resistance Test](docs/insulation_resistance_test.md)

## Standards Coverage

### IEC Standards
- ✅ IEC 61215-2:2016 - PV module design qualification
- ✅ IEC 61730-2:2016 - PV module safety qualification
- 🚧 IEC 61853 - Performance testing (planned)
- 🚧 IEC 62716 - Ammonia corrosion (planned)
- 🚧 IEC 61701 - Salt mist corrosion (planned)

### Compliance & Accreditation
- ✅ ISO/IEC 17025:2017 - Testing laboratory competence
- 🚧 ISO 9001 - Quality management (planned)
- 🚧 NABL - National Accreditation Board for Testing and Calibration Laboratories (planned)
- 🚧 ILAC - International Laboratory Accreditation Cooperation (planned)

## Contributing

Contributions welcome! Please follow the existing code structure and include tests.

## License

MIT License - see LICENSE file for details
