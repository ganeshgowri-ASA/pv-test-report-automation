# IEC 62804 PID Testing Protocol

Comprehensive implementation of IEC 62804 Potential Induced Degradation (PID) testing protocol for photovoltaic modules.

## Overview

This package provides a complete automated testing solution for IEC 62804 PID testing, including:

- ✅ Full IEC 62804-1 implementation (Methods A, B, C)
- ✅ Automated climate chamber control
- ✅ High voltage application with safety interlocks
- ✅ Continuous leakage current monitoring
- ✅ Automated flash testing at 24h intervals
- ✅ Real-time degradation tracking and analysis
- ✅ PID recovery testing (reversibility)
- ✅ Emergency shutdown on safety violations
- ✅ Comprehensive reporting (text, HTML, JSON)
- ✅ ISO 17025 compliance features
- ✅ Extensive unit test coverage

## IEC 62804 Standard

The IEC 62804 standard defines test methods for detecting Potential Induced Degradation (PID) in photovoltaic modules:

### Test Methods

**Method A**: Outdoor exposure with voltage bias
**Method B**: Climate chamber with humidity (60°C, 85% RH) - Most common
**Method C**: Climate chamber dry (85°C)

### Test Duration

Minimum 96 hours with flash tests at 0, 24, 48, 72, and 96 hours.

### Pass/Fail Criteria

- **PASS**: < 5% power degradation after 96 hours
- **MARGINAL**: 5-10% power degradation
- **FAIL**: > 10% power degradation

### Reversibility Testing

- **Reversible PID**: > 80% power recovery within 24 hours
- **Partially Reversible**: 20-80% recovery
- **Irreversible PID**: < 20% recovery

## Installation

```bash
# Install dependencies
pip install numpy matplotlib pydantic sqlalchemy

# Optional: for advanced analysis
pip install scipy pandas
```

## Quick Start

```python
from protocols.iec_62804 import (
    IEC62804TestController,
    TestConfiguration,
    TestMethod,
    create_chamber_controller,
    create_voltage_supply,
    create_flash_tester
)

# Configure test
config = TestConfiguration(
    module_serial="PV-2025-001234",
    test_method=TestMethod.METHOD_B,
    voltage=-1000,  # -1000V typical
    duration_hours=96,
    temperature=60.0,
    humidity=85.0,
    flash_intervals=[0, 24, 48, 72, 96],
    recovery_enabled=True
)

# Initialize equipment (simulated for testing)
chamber = create_chamber_controller("simulated", "CHAMBER-01")
voltage_supply = create_voltage_supply("simulated", "SUPPLY-01")
flash_tester = create_flash_tester("simulated", "TESTER-01",
                                   nominal_pmax=300.0,
                                   nominal_voc=40.0,
                                   nominal_isc=9.0)

# Create test controller
controller = IEC62804TestController(
    config=config,
    chamber=chamber,
    voltage_supply=voltage_supply,
    flash_tester=flash_tester
)

# Initialize and run test
if controller.initialize():
    controller.run_test()

    # Monitor progress
    while controller._running:
        status = controller.get_status()
        print(f"Elapsed: {status['elapsed_hours']:.1f}h")
        print(f"Degradation: {status['current_degradation_pct']:.2f}%")
        print(f"Result: {status['test_result']}")
        time.sleep(60)

    # Generate report
    from protocols.iec_62804 import create_test_report

    test_data = {
        "test_id": 1,
        "module_serial": config.module_serial,
        "test_method": config.test_method.value,
        "initial_pmax": controller.initial_pmax,
        "final_pmax": controller.final_pmax,
        "degradation_pct": status['current_degradation_pct'],
        "result": status['test_result'],
        # ... additional data
    }

    create_test_report(test_data, "iec62804_report.txt", format="text")
    create_test_report(test_data, "iec62804_report.html", format="html")
```

## Architecture

### Module Structure

```
protocols/iec_62804/
├── __init__.py              # Package exports
├── models.py                # Database models (SQLAlchemy + Pydantic)
├── chamber_control.py       # Climate chamber interface
├── voltage_control.py       # High voltage supply control
├── flash_tester.py          # I-V tracer integration
├── leakage_monitor.py       # Current monitoring with safety
├── degradation_analyzer.py  # Power degradation analysis
├── recovery_test.py         # PID recovery testing
├── test_controller.py       # Main test orchestration
├── report_generator.py      # Report generation
├── test_iec_62804.py        # Unit tests
└── README.md               # This file
```

### Key Components

#### 1. Climate Chamber Control

```python
from protocols.iec_62804 import ChamberSetpoint, SimulatedChamberController

chamber = SimulatedChamberController("CHAMBER-01")
chamber.connect()

setpoint = ChamberSetpoint(temperature=60.0, humidity=85.0)
chamber.set_setpoint(setpoint)
chamber.start()

# Wait for stabilization
chamber.wait_for_setpoint(timeout=3600)
```

#### 2. Voltage Supply Control

```python
from protocols.iec_62804 import SimulatedVoltageSupply, InterlockType

supply = SimulatedVoltageSupply("SUPPLY-01")
supply.connect()

# Set safety interlocks
supply.set_interlock(InterlockType.DOOR, True)

# Apply voltage
supply.set_voltage(-1000.0)
supply.set_current_limit(0.05)  # 50mA
supply.enable_output()

# Monitor
reading = supply.get_reading()
print(f"Voltage: {reading.voltage}V, Current: {reading.current*1000}mA")
```

#### 3. Flash Testing (I-V Curves)

```python
from protocols.iec_62804 import SimulatedFlashTester

tester = SimulatedFlashTester("TESTER-01", nominal_pmax=300.0)
tester.connect()

# Measure I-V curve
iv_data = tester.measure_iv_curve()
print(f"Pmax: {iv_data.pmax}W")
print(f"Voc: {iv_data.voc}V")
print(f"Isc: {iv_data.isc}A")
print(f"FF: {iv_data.ff}")
```

#### 4. Leakage Current Monitoring

```python
from protocols.iec_62804 import LeakageCurrentMonitor

monitor = LeakageCurrentMonitor(
    voltage_supply=supply,
    threshold_ma=50.0,
    critical_threshold_ma=100.0,
    sample_interval=60.0
)

monitor.start_monitoring()

# Get statistics
stats = monitor.get_statistics()
print(f"Mean: {stats.mean_current_ma}mA")
print(f"Max: {stats.max_current_ma}mA")
```

#### 5. Degradation Analysis

```python
from protocols.iec_62804 import DegradationAnalyzer

analyzer = DegradationAnalyzer(initial_pmax=300.0)

# Add measurements
analyzer.add_measurement(
    timestamp=datetime.utcnow(),
    elapsed_hours=0.0,
    pmax=300.0,
    voc=40.0,
    isc=9.0,
    ff=0.83
)

analyzer.add_measurement(
    timestamp=datetime.utcnow(),
    elapsed_hours=96.0,
    pmax=285.0,
    voc=39.5,
    isc=8.9,
    ff=0.82
)

# Analyze
result = analyzer.analyze(test_complete=True)
print(f"Degradation: {result.degradation_pct}%")
print(f"Result: {result.test_result.value}")
```

#### 6. Recovery Testing

```python
from protocols.iec_62804 import PIDRecoveryTest, RecoveryMethod

recovery = PIDRecoveryTest(
    flash_tester=tester,
    initial_pmax=300.0,
    degraded_pmax=270.0,
    recovery_method=RecoveryMethod.PASSIVE
)

recovery.start_recovery()

# Add recovery measurements
recovery.add_measurement(270.0)  # 0h
recovery.add_measurement(285.0)  # 24h

result = recovery.analyze()
print(f"Recovery: {result.recovery_pct}%")
print(f"Classification: {result.classification.value}")
```

## Safety Features

### 1. Emergency Shutdown

Automatic shutdown triggered by:
- Excessive leakage current (> critical threshold)
- Chamber door open
- Temperature/humidity out of range
- Communication errors

### 2. Safety Interlocks

- Door interlock (prevents voltage when open)
- Emergency stop button
- Current limit protection
- Ground fault detection

### 3. Continuous Monitoring

- Leakage current (logged every 60 seconds)
- Chamber temperature and humidity
- Voltage supply status
- Automatic alarm notifications

## Testing

Run unit tests:

```bash
python -m pytest protocols/iec_62804/test_iec_62804.py -v
```

Or using unittest:

```bash
python protocols/iec_62804/test_iec_62804.py
```

## Report Generation

### Text Report

```python
from protocols.iec_62804 import create_test_report

create_test_report(test_data, "report.txt", format="text")
```

### HTML Report

```python
create_test_report(test_data, "report.html", format="html")
```

### JSON Export

```python
create_test_report(test_data, "report.json", format="json")
```

## Database Integration

The package includes SQLAlchemy ORM models for database storage:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from protocols.iec_62804 import Base, IEC62804TestORM

# Create database
engine = create_engine('sqlite:///iec62804_tests.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

# Create test record
test = IEC62804TestORM(
    module_serial="PV-2025-001234",
    test_method="B",
    voltage=-1000.0,
    temperature=60.0,
    humidity=85.0
)

session.add(test)
session.commit()
```

## Hardware Integration

To integrate with real hardware, implement the base classes:

### Custom Chamber Controller

```python
from protocols.iec_62804 import ChamberControllerBase

class MyChambererController(ChamberControllerBase):
    def connect(self):
        # Your implementation
        pass

    def set_temperature(self, temperature):
        # Your implementation
        pass

    # ... implement other methods
```

### Custom Voltage Supply

```python
from protocols.iec_62804 import VoltageSupplyBase

class MyVoltageSupply(VoltageSupplyBase):
    def connect(self):
        # Your implementation
        pass

    def set_voltage(self, voltage):
        # Your implementation
        pass

    # ... implement other methods
```

## Standards Compliance

This implementation complies with:

- **IEC 62804-1**: Test methods for PID detection
- **IEC 62804-1-1**: Crystalline silicon modules
- **ISO/IEC 17025**: Testing laboratory requirements

## License

See LICENSE file for details.

## Support

For issues and questions, please refer to the project documentation or contact the development team.

## Version History

### v1.0.0 (2025)
- Initial release
- Full IEC 62804-1 Methods A, B, C implementation
- Automated test sequencing
- Safety features and monitoring
- Comprehensive reporting
- Unit test coverage
