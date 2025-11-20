# Quick Start Guide - Phase 4: Test Blocks

## Installation

```bash
cd /home/user/pv-test-report-automation
pip install -r requirements.txt  # numpy, scipy, pytest
```

## Running Tests

### Run All Tests
```bash
pytest src/test_blocks/tests/ -v
```

### Run Specific Test
```bash
pytest src/test_blocks/tests/test_vi_curve.py -v
pytest src/test_blocks/tests/test_base_test_block.py -v
```

## Usage Examples

### Example 1: V-I Curve Test

```python
from src.test_blocks import VICurveTest, SolarSimulator, SourceMeter

# Initialize equipment
simulator = SolarSimulator('SIM-001', {
    'irradiance': 1000,
    'spectrum': 'AM1.5G',
    'temperature': 25
})

source_meter = SourceMeter('SMU-001', {
    'compliance_current': 15,
    'compliance_voltage': 60
})

# Connect
simulator.connect()
simulator.initialize()
source_meter.connect()
source_meter.initialize()

# Create test
test = VICurveTest(
    test_id='VI-2024-001',
    operator='John Doe',
    config={'module_area': 1.94},
    simulator=simulator,
    source_meter=source_meter
)

# Execute
result = test.execute()

# Results
print(f"Result: {result.result.value}")
print(f"Voc: {result.analysis_results['voc']:.2f} V")
print(f"Isc: {result.analysis_results['isc']:.2f} A")
print(f"Pmax: {result.analysis_results['pmax']:.2f} W")
print(f"Fill Factor: {result.analysis_results['fill_factor']:.2f}%")
print(f"Efficiency: {result.analysis_results['efficiency']:.2f}%")
```

### Example 2: Insulation Resistance Test

```python
from src.test_blocks import InsulationResistanceTest, Megohmmeter

# Initialize equipment
megohmmeter = Megohmmeter('MEGA-001', {
    'test_voltage': 1000,
    'measurement_time': 60
})

megohmmeter.connect()
megohmmeter.initialize()

# Create test
test = InsulationResistanceTest(
    test_id='IR-2024-001',
    operator='Jane Smith',
    config={},
    megohmmeter=megohmmeter
)

# Execute
result = test.execute()

# Results
print(f"Result: {result.result.value}")
print(f"Min Resistance: {result.analysis_results['min_resistance']/1e6:.1f} MΩ")
print(f"Mean Resistance: {result.analysis_results['mean_resistance']/1e6:.1f} MΩ")
```

### Example 3: Climate Chamber Test

```python
from src.test_blocks import ClimateChamberTest, ClimateChamber, TestType

# Initialize equipment
chamber = ClimateChamber('CHAMBER-001', {
    'temperature_range': (-40, 85),
    'humidity_range': (10, 95)
})

chamber.connect()
chamber.initialize()

# Create temperature cycling test
test = ClimateChamberTest(
    test_id='TC-2024-001',
    operator='Lab Tech',
    config={},
    chamber=chamber,
    test_type=TestType.TEMPERATURE_CYCLING
)

# Execute
result = test.execute()

# Results
print(f"Result: {result.result.value}")
print(f"Cycles: {result.analysis_results['completed_cycles']}")
print(f"Completion Rate: {result.analysis_results['completion_rate']:.1f}%")
```

## File Locations

- **Test Blocks**: `/home/user/pv-test-report-automation/src/test_blocks/`
- **Unit Tests**: `/home/user/pv-test-report-automation/src/test_blocks/tests/`
- **Documentation**: `/home/user/pv-test-report-automation/src/test_blocks/README.md`
- **Summary**: `/home/user/pv-test-report-automation/PHASE4_SUMMARY.md`

## Test Block Modules

1. `vi_curve_test.py` - V-I curve acquisition and analysis
2. `insulation_resistance.py` - IR testing
3. `climate_chamber.py` - Environmental testing (TC, HF, DH)
4. `outdoor_exposure.py` - Field testing and degradation
5. `dielectric_test.py` - High voltage testing
6. `wet_leakage.py` - Wet leakage current testing
7. `ground_continuity.py` - Ground continuity testing

## Available Equipment

- SolarSimulator
- SourceMeter
- Megohmmeter
- EnvironmentMonitor
- ClimateChamber
- DataLogger
- WeatherStation
- PowerMeter
- HipotTester
- LeakageCurrentMeter
- WaterSpraySystem
- HighVoltageSource
- GroundContinuityTester

## Next Phase

Phase 5 will integrate these test blocks with:
- Report generation
- Database storage
- Workflow management
- Multi-format export
