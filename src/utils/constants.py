"""
Standard constants for PV testing protocols
"""

from enum import Enum


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PassFailStatus(Enum):
    """Test result pass/fail status"""
    PASS = "pass"
    FAIL = "fail"
    CONDITIONAL = "conditional"
    NOT_TESTED = "not_tested"


# IEC 62759 Specific Constants
IEC_62759_EDGE_LOAD_PA = 600  # Pascal
IEC_62759_EDGE_LOAD_DURATION_HOURS = 1  # Hour
IEC_62759_DYNAMIC_LOAD_PA = 1000  # Pascal
IEC_62759_DYNAMIC_CYCLES = 1000  # Cycles
IEC_62759_THERMAL_CYCLES = 50  # Cycles
IEC_62759_THERMAL_LOW_TEMP = -40  # Celsius
IEC_62759_THERMAL_HIGH_TEMP = 85  # Celsius
IEC_62759_THERMAL_RAMP_RATE = 100  # Celsius per hour
IEC_62759_THERMAL_HOLD_TIME_MIN = 10  # Minutes (minimum)
IEC_62759_THERMAL_HOLD_TIME_MAX = 20  # Minutes (maximum)
IEC_62759_MAX_POWER_DEGRADATION_PCT = 5.0  # Maximum allowable power degradation %

# Dynamic load frequency range
IEC_62759_DYNAMIC_FREQ_MIN = 0.5  # Hz
IEC_62759_DYNAMIC_FREQ_MAX = 2.0  # Hz

# ISO 17025 Compliance
ISO_17025_REQUIRED_FIELDS = [
    "test_date",
    "technician_id",
    "equipment_id",
    "calibration_status",
    "environmental_conditions",
    "measurement_uncertainty"
]
