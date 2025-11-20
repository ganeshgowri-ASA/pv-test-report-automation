# Equipment Management Module

Production-ready equipment management system for PV testing laboratories.

## Features

### 1. Equipment Manager (Session 31)
- **Equipment Registry**: Complete asset tracking with manufacturer, model, serial numbers
- **Equipment Tracking**: Status management (active, maintenance, calibration, retired)
- **Usage Logging**: Track equipment usage hours and test counts
- **Maintenance Scheduling**: Automated maintenance due dates and alerts
- **Asset Allocation**: Smart equipment allocation based on usage patterns

### 2. Calibration Tracker (Session 32)
- **Calibration Schedule Management**: Automated due date tracking
- **Certificate Storage**: Link to calibration certificates
- **Due Date Tracking**: Alerts for upcoming and overdue calibrations
- **Calibration History**: Complete audit trail
- **Traceability to Standards**: Full traceability chain
- **ISO 17025 Compliance**: Built-in compliance validation
- **Uncertainty Budgets**: Automated uncertainty calculations

### 3. SPC Controller (Session 33)
- **Statistical Process Control**: Real-time equipment performance monitoring
- **Control Charts**: X-bar R, Individuals, CUSUM support
- **Out-of-Control Detection**: Western Electric Rules implementation
- **Capability Analysis**: Cp, Cpk, Pp, Ppk calculations
- **Trend Analysis**: Automated trend detection
- **Quality Metrics**: Comprehensive performance metrics

## Quick Start

### Equipment Management

```python
from equipment import EquipmentManager, Equipment, EquipmentCategory

# Initialize manager
manager = EquipmentManager(storage_path="./data/equipment")

# Register new equipment
equipment = Equipment(
    asset_number="PV-001",
    name="Keysight B2900A IV Tracer",
    manufacturer="Keysight",
    model="B2900A",
    serial_number="MY12345678",
    category=EquipmentCategory.IV_TRACER,
    location="Lab 1"
)

equipment_id = manager.register_equipment(equipment)

# Start usage logging
log_id = manager.start_usage(
    equipment_id=equipment_id,
    operator="John Doe",
    test_id="test-001",
    test_type="IV curve measurement"
)

# End usage
manager.end_usage(log_id, notes="Test completed successfully")

# Check maintenance due
maintenance_due = manager.get_maintenance_due(days_ahead=30)
```

### Calibration Management

```python
from equipment import CalibrationTracker, CalibrationRecord
from datetime import date
from decimal import Decimal

# Initialize tracker
tracker = CalibrationTracker(
    storage_path="./data/calibration",
    alert_days_before=30
)

# Add calibration record
record = CalibrationRecord(
    equipment_id=equipment_id,
    calibration_date=date(2024, 1, 15),
    calibration_interval_days=365,
    laboratory_name="NABL Accredited Lab",
    laboratory_accreditation="NABL",
    certificate_number="CAL-2024-001",
    reference_standard="Fluke 8846A",
    performed_by="Tech Smith",
    approved_by="Manager Jones"
)

cal_id = tracker.add_calibration_record(record)

# Add uncertainty budget
uncertainty_components = {
    'repeatability': {
        'value': '0.02',
        'distribution': 'normal',
        'divisor': '1',
        'description': 'Measurement repeatability'
    },
    'resolution': {
        'value': '0.01',
        'distribution': 'rectangular',
        'divisor': '1.732',
        'description': 'Instrument resolution'
    }
}

tracker.add_uncertainty_budget(cal_id, uncertainty_components)

# Check calibration status
status = tracker.get_calibration_status(equipment_id)
print(f"Calibration valid: {status['is_valid']}")
print(f"Days until due: {status['days_until_due']}")

# Generate alerts
alerts = tracker.generate_alerts()
for alert in alerts:
    print(f"{alert.equipment_name}: {alert.message}")
```

### Statistical Process Control

```python
from equipment import SPCController, SPCDataPoint
from decimal import Decimal

# Initialize SPC controller
spc = SPCController(storage_path="./data/spc")

# Create control chart
chart_id = spc.create_control_chart(
    equipment_id=equipment_id,
    measurement_type="voltage_accuracy",
    chart_type="xbar_r"
)

# Add measurement data
data_point = SPCDataPoint(
    equipment_id=equipment_id,
    measurement_type="voltage_accuracy",
    measured_value=Decimal('10.05'),
    reference_value=Decimal('10.00'),
    error=Decimal('0.05'),
    operator="Test User"
)

spc.add_data_point(data_point)

# Update control limits (after collecting enough data)
spc.update_control_limits(chart_id)

# Check for control violations
violations = spc.check_control_violations(chart_id)
for violation in violations:
    print(f"Violation: {violation.message}")

# Calculate process capability
capability = spc.calculate_process_capability(
    chart_id=chart_id,
    upper_spec_limit=Decimal('0.10'),
    lower_spec_limit=Decimal('-0.10')
)

print(f"Cpk: {capability['cpk']:.2f}")
print(f"Interpretation: {capability['interpretation']}")

# Analyze trends
trend = spc.analyze_trend(equipment_id, "voltage_accuracy")
print(f"Trend: {trend.trend_type} - {trend.description}")
```

## NABL Compliance

The calibration tracker includes built-in NABL/ISO 17025 compliance features:

```python
# Validate ISO 17025 compliance
validation = tracker.validate_iso17025_compliance(cal_id)

if validation['compliant']:
    print("✓ ISO 17025 Compliant")
else:
    print("✗ Non-compliant")
    for error in validation['errors']:
        print(f"  - {error}")

# View traceability chain
chain = tracker.get_traceability_chain(cal_id)
for link in chain:
    print(f"{link['level']}: {link['reference']}")
```

## Western Electric Rules

The SPC controller implements all Western Electric Rules for out-of-control detection:

1. One point beyond 3σ from center line
2. Two out of three consecutive points beyond 2σ (same side)
3. Four out of five consecutive points beyond 1σ (same side)
4. Eight consecutive points on same side of center line
5. Six consecutive points increasing or decreasing
6. Fifteen consecutive points within 1σ
7. Fourteen consecutive points alternating up and down
8. Eight consecutive points beyond 1σ (both sides)

## Data Storage

All data is stored in JSON format for easy portability:

- `equipment.json` - Equipment registry
- `usage_logs.json` - Usage history
- `calibrations.json` - Calibration records
- `data_points.json` - SPC measurements
- `control_charts.json` - Control chart configurations

## Testing

Run the comprehensive test suite:

```bash
# Run all equipment tests
python -m pytest src/equipment/tests/ -v

# Run specific test module
python -m pytest src/equipment/tests/test_equipment_manager.py -v
python -m pytest src/equipment/tests/test_calibration_tracker.py -v
python -m pytest src/equipment/tests/test_spc_controller.py -v

# Run with coverage
python -m pytest src/equipment/tests/ --cov=src/equipment --cov-report=html
```

## Streamlit Dashboard Integration

Example Streamlit dashboard stub for equipment monitoring:

```python
import streamlit as st
from equipment import EquipmentManager, CalibrationTracker, SPCController

st.title("Equipment Management Dashboard")

# Sidebar navigation
page = st.sidebar.selectbox("Select Page", [
    "Equipment Registry",
    "Calibration Status",
    "SPC Monitoring",
    "Alerts"
])

if page == "Equipment Registry":
    manager = EquipmentManager()
    equipment_list = manager.list_equipment()

    st.header("Equipment Registry")
    for eq in equipment_list:
        with st.expander(f"{eq.name} ({eq.asset_number})"):
            st.write(f"**Status:** {eq.status.value}")
            st.write(f"**Location:** {eq.location}")
            st.write(f"**Total Usage:** {eq.total_usage_hours} hours")
            st.write(f"**Test Count:** {eq.test_count}")

elif page == "Calibration Status":
    tracker = CalibrationTracker()

    st.header("Calibration Status")

    # Show overdue calibrations
    overdue = tracker.get_overdue_calibrations()
    if overdue:
        st.error(f"⚠️ {len(overdue)} overdue calibrations!")
        for cal in overdue:
            st.write(f"- Equipment {cal.equipment_id}: Due {cal.due_date}")

    # Show upcoming calibrations
    due_soon = tracker.get_calibrations_due_soon()
    if due_soon:
        st.warning(f"📅 {len(due_soon)} calibrations due soon")

elif page == "SPC Monitoring":
    spc = SPCController()

    st.header("SPC Monitoring")

    # Equipment selection
    equipment_id = st.text_input("Equipment ID")

    if equipment_id:
        # Get quality metrics
        metrics = spc.get_quality_metrics(equipment_id, "voltage_accuracy")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Mean Error", f"{metrics['mean_error']:.4f}")
        with col2:
            st.metric("Std Dev", f"{metrics['std_error']:.4f}")
        with col3:
            st.metric("Violations", metrics['violations_count'])

        # Trend analysis
        trend = spc.analyze_trend(equipment_id, "voltage_accuracy")
        st.info(f"**Trend:** {trend.description}")
```

## API Reference

See inline documentation in:
- `models.py` - Data models
- `equipment_manager.py` - Equipment management
- `calibration_tracker.py` - Calibration tracking
- `spc_controller.py` - Statistical process control

## License

Part of the PV Test Report Automation system.
