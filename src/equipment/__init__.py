"""
Equipment Management Module

Production-ready equipment management system for PV testing with:
- Equipment registry and tracking
- Calibration management with NABL/ISO 17025 compliance
- Statistical Process Control (SPC)
- Automated alerts and reporting

Sessions 31-33: Equipment Management System
"""

from .models import (
    Equipment,
    EquipmentStatus,
    EquipmentCategory,
    CalibrationRecord,
    CalibrationStatus,
    SPCDataPoint,
    SPCControlChart,
    UsageLog,
)

from .equipment_manager import EquipmentManager

from .calibration_tracker import (
    CalibrationTracker,
    CalibrationAlert,
)

from .spc_controller import (
    SPCController,
    ControlViolation,
    TrendAnalysis,
)


__all__ = [
    # Models
    'Equipment',
    'EquipmentStatus',
    'EquipmentCategory',
    'CalibrationRecord',
    'CalibrationStatus',
    'SPCDataPoint',
    'SPCControlChart',
    'UsageLog',

    # Managers
    'EquipmentManager',
    'CalibrationTracker',
    'SPCController',

    # Data classes
    'CalibrationAlert',
    'ControlViolation',
    'TrendAnalysis',
]


__version__ = "1.0.0"
