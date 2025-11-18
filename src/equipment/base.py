"""Base classes for equipment integration"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class InstrumentInfo(BaseModel):
    """Instrument identification and calibration info"""
    instrument_id: str
    manufacturer: str
    model: str
    serial_number: str
    calibration_date: Optional[datetime] = None
    calibration_due_date: Optional[datetime] = None
    calibration_certificate: Optional[str] = None
    uncertainty: Optional[Dict[str, float]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BaseInstrument(ABC):
    """Base class for all test instruments"""

    def __init__(self, instrument_info: InstrumentInfo):
        self.info = instrument_info
        self.connected = False

    @abstractmethod
    def connect(self) -> bool:
        """Connect to the instrument"""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from the instrument"""
        pass

    @abstractmethod
    def reset(self) -> bool:
        """Reset the instrument to default state"""
        pass

    @abstractmethod
    def self_test(self) -> bool:
        """Perform instrument self-test"""
        pass

    def is_calibration_valid(self) -> bool:
        """Check if calibration is still valid"""
        if not self.info.calibration_due_date:
            return True
        return datetime.utcnow() < self.info.calibration_due_date

    def get_info(self) -> InstrumentInfo:
        """Get instrument information"""
        return self.info
