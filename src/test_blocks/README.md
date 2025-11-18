# PV Test Blocks Module

Production-ready test block implementations for photovoltaic module testing according to IEC standards.

## Overview

This module provides comprehensive test block implementations for all standard PV module test types, including:

- **V-I Curve Testing** (Session 21) - V-I curve acquisition, analysis, fitting, parameter extraction, and anomaly detection
- **Insulation Resistance** (Session 22) - IR testing procedures, resistance calculations, pass/fail criteria, and trend analysis
- **Climate Chamber** (Session 23) - Temperature cycling, humidity freeze, damp heat testing, and environmental conditioning
- **Outdoor Exposure** (Session 24) - Field testing protocols, weather data integration, performance ratio, and degradation tracking
- **Dielectric Testing** (Session 25) - High voltage testing, insulation integrity, and safety compliance
- **Wet Leakage** (Session 26) - WLT procedures, leakage current measurement, and safety assessment
- **Ground Continuity** (Session 27) - GCT implementation, resistance measurement, and grounding verification

## Features

✓ **Equipment Integration Stubs** - Standardized interfaces for test equipment
✓ **Real-time Data Collection** - Simulated data acquisition with realistic behavior
✓ **Statistical Analysis** - Comprehensive statistical processing and trend analysis
✓ **Automated Pass/Fail** - Intelligent determination based on IEC criteria
✓ **Anomaly Detection** - Advanced detection of test anomalies
✓ **Full Traceability** - Complete measurement and metadata logging

## Architecture

### Base Classes

- `BaseTestBlock` - Abstract base class for all test implementations
- `EquipmentInterface` - Abstract interface for test equipment
- `MeasurementData` - Data structure for measurements
- `TestBlockResult` - Comprehensive test result structure

### Test Implementations

Each test block inherits from `BaseTestBlock` and implements:
- Parameter initialization
- Data collection procedures
- Analysis algorithms
- Pass/fail determination
- Anomaly detection

## Usage Example

```python
from test_blocks import VICurveTest, SolarSimulator, SourceMeter

# Initialize equipment
simulator = SolarSimulator('SIM-001', {'irradiance': 1000})
source_meter = SourceMeter('SMU-001', {'compliance_current': 15})

# Connect equipment
simulator.connect()
source_meter.connect()

# Create and execute test
test = VICurveTest(
    test_id='VI-2024-001',
    operator='John Doe',
    config={'module_area': 1.94},
    simulator=simulator,
    source_meter=source_meter
)

result = test.execute()

# Access results
print(f"Test Result: {result.result}")
print(f"Fill Factor: {result.analysis_results['fill_factor']:.2f}%")
print(f"Pmax: {result.analysis_results['pmax']:.2f} W")
```

## Testing

Run the comprehensive test suite:

```bash
pytest src/test_blocks/tests/ -v
```

Run specific test file:

```bash
pytest src/test_blocks/tests/test_vi_curve.py -v
```

## Standards Compliance

All test implementations comply with:
- IEC 61215-2 (Design qualification and type approval)
- IEC 61730-2 (Module safety qualification)
- IEC 60904-1 (I-V characteristic measurements)
- IEC 61853 (Performance testing and energy rating)

## Equipment Stubs

The module includes equipment interface stubs that simulate realistic behavior for:
- Solar simulators
- Source-measure units (SMU)
- Megohmmeters
- Climate chambers
- Weather stations
- Hipot testers
- Ground continuity testers

These stubs can be replaced with actual equipment drivers for production use.

## Data Structures

### MeasurementData
```python
@dataclass
class MeasurementData:
    timestamp: datetime
    value: float
    unit: str
    parameter_name: str
    equipment_id: Optional[str]
    uncertainty: Optional[float]
    metadata: Dict[str, Any]
```

### TestBlockResult
```python
@dataclass
class TestBlockResult:
    test_name: str
    test_id: str
    result: TestResult
    start_time: datetime
    end_time: datetime
    measurements: List[MeasurementData]
    parameters: Dict[str, TestParameter]
    analysis_results: Dict[str, Any]
    pass_fail_criteria: Dict[str, bool]
    anomalies: List[str]
    severity: TestSeverity
    operator: str
    equipment_used: List[str]
```

## Statistical Analysis

Each test block includes advanced statistical analysis:
- Mean, median, standard deviation
- Outlier detection (IQR, Z-score, modified Z-score)
- Trend analysis (linear regression)
- Coefficient of variation
- Correlation analysis

## Anomaly Detection

Automatic detection of:
- Out-of-specification measurements
- Equipment malfunction indicators
- Environmental condition issues
- Data quality problems
- Trend anomalies

## Version

1.0.0 - Initial production release
