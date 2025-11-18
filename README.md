# PV Test Report Automation

World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## Features

- **ISO 17025 Compliant**: Full measurement uncertainty tracking and traceability
- **IEC Standards Support**: Comprehensive test blocks for major IEC standards
- **4-Wire Kelvin Measurement**: High-precision resistance measurements
- **Safety Features**: Built-in pre/post-test safety checks
- **Automated Reporting**: Generate professional test reports in multiple formats
- **Equipment Traceability**: Track calibration status and equipment history

## Test Blocks

### Ground Continuity Test (IEC 61730)

Verifies electrical continuity between PV module frame and grounding points.

**Specifications:**
- Test current: 25A DC for 60 seconds
- Maximum resistance: 0.1 Ohm
- 4-wire Kelvin measurement
- Multiple measurement points
- Temperature monitoring

**Quick Start:**

```python
from test_blocks.ground_continuity import GroundContinuityTest

# Create test instance
test = GroundContinuityTest(
    test_id="GC-001",
    module_id="PV-MODULE-12345",
    operator="John Doe"
)

# Run test
report = test.run_test(simulated=True)

# Check result
print(f"Result: {report['result']['overall_status']}")
print(f"Avg Resistance: {report['statistics']['average_resistance_ohm']:.4f} Ω")
```

See [Ground Continuity Test Documentation](docs/ground_continuity_test.md) for details.

## Installation

### From Source

```bash
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation
pip install -e .
```

### With Dependencies

```bash
pip install -r requirements.txt
```

### Development Installation

```bash
pip install -e ".[dev]"
```

## Project Structure

```
pv-test-report-automation/
├── src/
│   ├── test_blocks/           # Test block implementations
│   │   ├── base.py           # Base classes and ISO 17025 support
│   │   └── ground_continuity/ # Ground continuity test
│   └── core/                  # Core functionality
├── tests/
│   └── unit/                  # Unit tests
├── examples/                  # Example scripts
├── docs/                      # Documentation
├── requirements.txt           # Python dependencies
└── setup.py                   # Package configuration
```

## Usage Examples

See the [examples](examples/) directory for comprehensive usage examples:

- `ground_continuity_example.py` - Ground continuity test examples

## Documentation

- [Ground Continuity Test](docs/ground_continuity_test.md) - Complete guide
- [API Reference](docs/api/) - Detailed API documentation

## Testing

Run unit tests:

```bash
pytest tests/unit/
```

With coverage:

```bash
pytest tests/unit/ --cov=src --cov-report=html
```

## Standards Compliance

This system implements testing per:

- **IEC 61730**: PV module safety qualification
- **IEC 61215**: Crystalline silicon terrestrial PV modules
- **IEC 61853**: PV module performance testing
- **ISO/IEC 17025**: Testing and calibration laboratories

## Safety

Always follow safety procedures when testing PV modules:

- Verify electrical isolation before testing
- Use properly rated equipment
- Monitor temperature during high-current tests
- Follow local electrical safety regulations

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Contact

For issues and questions:
- GitHub Issues: https://github.com/ganeshgowri-ASA/pv-test-report-automation/issues

## Acknowledgments

Developed following IEC standards and ISO 17025 requirements for testing and calibration laboratories.
