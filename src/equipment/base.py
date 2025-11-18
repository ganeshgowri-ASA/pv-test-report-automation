"""
Base classes for test equipment integration.

Provides standardized interfaces for all test equipment with:
- Connection management
- Status monitoring
- Error handling
- ISO 17025 calibration tracking
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from src.models.base import EquipmentCalibration


class EquipmentError(Exception):
    """Base exception for equipment errors."""
    pass


class CalibrationError(EquipmentError):
    """Raised when equipment calibration is invalid or expired."""
    pass


class ConnectionError(EquipmentError):
    """Raised when equipment connection fails."""
    pass


class BaseEquipment(ABC):
    """Base class for all test equipment with ISO 17025 compliance."""

    def __init__(self, config: Dict[str, Any], calibration: Optional[EquipmentCalibration] = None):
        """
        Initialize equipment.

        Args:
            config: Equipment configuration dictionary
            calibration: Equipment calibration record (ISO 17025)
        """
        self.config = config
        self.calibration = calibration
        self.is_connected = False
        self.last_status_check = None

        # Validate calibration if provided
        if calibration:
            self._validate_calibration()

    def _validate_calibration(self) -> None:
        """Validate equipment calibration is current."""
        if self.calibration.next_calibration_date < datetime.now():
            raise CalibrationError(
                f"Equipment {self.calibration.equipment_id} calibration expired on "
                f"{self.calibration.next_calibration_date}"
            )

    @property
    @abstractmethod
    def equipment_type(self) -> str:
        """Return equipment type identifier."""
        pass

    @abstractmethod
    async def connect(self) -> None:
        """
        Establish connection to equipment.

        Raises:
            ConnectionError: If connection fails
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to equipment safely."""
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """
        Get current equipment status.

        Returns:
            Dictionary containing equipment status information
        """
        pass

    @abstractmethod
    async def reset(self) -> None:
        """Reset equipment to safe/default state."""
        pass

    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with guaranteed cleanup."""
        await self.disconnect()
        return False


class ThermalCamera(BaseEquipment):
    """Thermal imaging camera for temperature measurement."""

    @property
    def equipment_type(self) -> str:
        return "thermal_camera"

    async def connect(self) -> None:
        """Connect to thermal camera."""
        # Placeholder implementation
        self.is_connected = True

    async def disconnect(self) -> None:
        """Disconnect from thermal camera."""
        self.is_connected = False

    async def get_status(self) -> Dict[str, Any]:
        """Get camera status."""
        return {
            "connected": self.is_connected,
            "resolution": self.config.get("resolution", "640x480"),
            "framerate": self.config.get("framerate", 30)
        }

    async def reset(self) -> None:
        """Reset camera settings."""
        pass

    async def capture_thermal_image(self) -> Dict[str, Any]:
        """
        Capture thermal image.

        Returns:
            Dictionary containing temperature data and image metadata
        """
        if not self.is_connected:
            raise EquipmentError("Thermal camera not connected")

        # Placeholder implementation
        return {
            "timestamp": datetime.now(),
            "min_temp_c": 25.0,
            "max_temp_c": 85.0,
            "avg_temp_c": 45.0,
            "image_path": f"thermal_{datetime.now().timestamp()}.jpg"
        }

    async def get_max_temperature(self) -> float:
        """Get maximum temperature from thermal image."""
        image_data = await self.capture_thermal_image()
        return image_data["max_temp_c"]


class SolarSimulator(BaseEquipment):
    """Solar simulator for controlled irradiance testing."""

    @property
    def equipment_type(self) -> str:
        return "solar_simulator"

    async def connect(self) -> None:
        """Connect to solar simulator."""
        self.is_connected = True

    async def disconnect(self) -> None:
        """Disconnect from solar simulator."""
        self.is_connected = False

    async def get_status(self) -> Dict[str, Any]:
        """Get simulator status."""
        return {
            "connected": self.is_connected,
            "lamp_on": False,
            "current_irradiance": 0.0
        }

    async def reset(self) -> None:
        """Reset simulator to safe state."""
        await self.set_irradiance(0.0)

    async def set_irradiance(self, irradiance_w_m2: float) -> None:
        """
        Set solar irradiance level.

        Args:
            irradiance_w_m2: Target irradiance in W/m²
        """
        if not self.is_connected:
            raise EquipmentError("Solar simulator not connected")

        if not 0 <= irradiance_w_m2 <= 1200:
            raise ValueError(f"Irradiance {irradiance_w_m2} W/m² out of range [0, 1200]")

        # Placeholder implementation
        self.config["current_irradiance"] = irradiance_w_m2

    async def lamp_on(self) -> None:
        """Turn on simulator lamp."""
        pass

    async def lamp_off(self) -> None:
        """Turn off simulator lamp."""
        pass


class TemperatureDataLogger(BaseEquipment):
    """Temperature data logger for continuous monitoring."""

    @property
    def equipment_type(self) -> str:
        return "temperature_logger"

    async def connect(self) -> None:
        """Connect to data logger."""
        self.is_connected = True

    async def disconnect(self) -> None:
        """Disconnect from data logger."""
        self.is_connected = False

    async def get_status(self) -> Dict[str, Any]:
        """Get logger status."""
        return {
            "connected": self.is_connected,
            "channels": self.config.get("channels", 8),
            "sample_rate": self.config.get("sample_rate", 1.0)
        }

    async def reset(self) -> None:
        """Reset logger."""
        pass

    async def start_logging(self, duration_seconds: float, sample_rate: float = 1.0) -> None:
        """
        Start temperature logging.

        Args:
            duration_seconds: Logging duration
            sample_rate: Samples per second
        """
        if not self.is_connected:
            raise EquipmentError("Temperature logger not connected")

    async def get_temperature_data(self) -> Dict[str, Any]:
        """Get logged temperature data."""
        return {
            "timestamps": [],
            "temperatures_c": [],
            "max_temp_c": 0.0,
            "min_temp_c": 0.0,
            "avg_temp_c": 0.0
        }
