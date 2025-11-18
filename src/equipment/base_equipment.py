"""
Base equipment interface for all lab instruments
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import logging


class EquipmentStatus:
    """Equipment status constants"""
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    CALIBRATION_DUE = "calibration_due"


class BaseEquipment(ABC):
    """
    Base class for all lab equipment interfaces

    Ensures ISO 17025 compliance through calibration tracking
    and measurement uncertainty documentation
    """

    def __init__(self, equipment_id: str, name: str):
        self.equipment_id = equipment_id
        self.name = name
        self.status = EquipmentStatus.READY
        self.logger = logging.getLogger(self.__class__.__name__)
        self._last_calibration_date: Optional[datetime] = None
        self._measurement_uncertainty: Dict[str, float] = {}

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to equipment"""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from equipment"""
        pass

    @abstractmethod
    def get_status(self) -> str:
        """Get current equipment status"""
        pass

    @abstractmethod
    def self_test(self) -> bool:
        """Perform equipment self-test"""
        pass

    def set_calibration_info(self, calibration_date: datetime, uncertainty: Dict[str, float]):
        """Set calibration information for ISO 17025 compliance"""
        self._last_calibration_date = calibration_date
        self._measurement_uncertainty = uncertainty
        self.logger.info(f"Calibration info updated for {self.equipment_id}")

    def is_calibration_valid(self, validity_days: int = 365) -> bool:
        """Check if calibration is still valid"""
        if not self._last_calibration_date:
            return False

        days_since_calibration = (datetime.now() - self._last_calibration_date).days
        return days_since_calibration < validity_days

    def get_measurement_uncertainty(self, parameter: str) -> Optional[float]:
        """Get measurement uncertainty for a specific parameter"""
        return self._measurement_uncertainty.get(parameter)

    def log_event(self, event: str, data: Optional[Dict] = None):
        """Log equipment event"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'equipment_id': self.equipment_id,
            'event': event,
            'data': data or {}
        }
        self.logger.info(f"{self.equipment_id}: {event}")
        return log_entry
