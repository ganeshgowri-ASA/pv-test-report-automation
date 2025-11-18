# PV Test Report Automation

World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## Features

- **ISO 17025 Compliance**: Full traceability and metadata tracking
- **Multi-Standard Support**: IEC 61215, 61730, 61853, and more
- **Comprehensive Testing**: Multiple test blocks for complete PV module qualification
- **Data Export**: JSON, CSV, and PDF report generation
- **Reviewer Workflows**: Built-in quality assurance processes

## Installation

```bash
# Clone the repository
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Bypass Diode Test

```python
from test_blocks.bypass_diode import BypassDiodeTest

# Create test instance
test = BypassDiodeTest(module="PV-001", diode_count=3)

# Set environmental conditions (ISO 17025)
test.set_environmental_conditions(
    temperature=25.0,
    humidity=45.0,
    pressure=1013.25
)

# Run test
result = test.test_all_diodes()

# Check results
print(f"Diodes tested: {len(result.forward_voltage)}")
print(f"Pass status: {result.pass_status}")
```

## Available Test Blocks

### Phase 4: Bypass Diode Test (IEC 61215)

Comprehensive bypass diode testing with:
- Forward V-I curve characterization (0-10A)
- Reverse leakage current measurement (-15V)
- Thermal performance monitoring
- Shading activation verification
- Multi-diode testing (typically 3 per module)

**Test Sequence:**
1. Forward V-I curve measurement
2. Reverse bias test
3. Thermal performance under load
4. Shading response verification

**Pass Criteria:**
- Forward voltage ≤ 1.2V at 8A
- Reverse leakage ≤ 100µA
- Operating temperature ≤ 85°C
- Activation voltage ≤ 0.7V

See [test_blocks/README.md](test_blocks/README.md) for detailed documentation.

## Running Tests

```bash
# Run all unit tests
python -m unittest discover tests -v

# Run example
PYTHONPATH=. python examples/bypass_diode_example.py
```

## Project Structure

```
pv-test-report-automation/
├── test_blocks/          # Test block implementations
│   ├── base.py          # Base classes and models
│   ├── bypass_diode.py  # Bypass diode test block
│   └── README.md        # Test blocks documentation
├── examples/            # Usage examples
│   └── bypass_diode_example.py
├── tests/               # Unit tests
│   └── test_bypass_diode.py
└── requirements.txt     # Project dependencies
```

## Standards Compliance

- **IEC 61215**: Terrestrial PV modules - Design qualification
- **IEC 61730**: PV module safety qualification
- **IEC 61853**: PV module performance testing
- **ISO 17025**: Testing and calibration laboratories
- **ISO 9001**: Quality management systems

## License

See LICENSE file for details.
