"""
IEC 62804 PID Testing Protocol - Climate Chamber Control

This module provides interfaces for controlling climate chambers used in
IEC 62804 PID testing. Supports temperature and humidity control with
safety monitoring and alarm management.
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ChamberAlarmType(Enum):
    """Chamber alarm types"""
    NONE = "none"
    TEMPERATURE_HIGH = "temperature_high"
    TEMPERATURE_LOW = "temperature_low"
    HUMIDITY_HIGH = "humidity_high"
    HUMIDITY_LOW = "humidity_low"
    DOOR_OPEN = "door_open"
    COMMUNICATION_ERROR = "communication_error"
    SENSOR_ERROR = "sensor_error"


@dataclass
class ChamberSetpoint:
    """Climate chamber setpoint configuration"""
    temperature: float  # °C
    humidity: Optional[float] = None  # %RH (None for dry tests)
    temperature_tolerance: float = 2.0  # ±°C
    humidity_tolerance: float = 5.0  # ±%RH


@dataclass
class ChamberReading:
    """Current chamber environmental readings"""
    timestamp: datetime
    temperature: float  # °C
    humidity: Optional[float]  # %RH
    door_open: bool = False
    alarm_active: bool = False
    alarm_type: ChamberAlarmType = ChamberAlarmType.NONE


class ChamberControllerBase(ABC):
    """
    Base class for climate chamber controllers.

    Implement this interface for specific chamber models (e.g., Espec, Weiss, etc.)
    """

    def __init__(self, chamber_id: str, connection_params: Dict[str, Any]):
        """
        Initialize chamber controller.

        Args:
            chamber_id: Unique identifier for the chamber
            connection_params: Connection parameters (IP, port, serial, etc.)
        """
        self.chamber_id = chamber_id
        self.connection_params = connection_params
        self._connected = False
        self._current_setpoint: Optional[ChamberSetpoint] = None

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the chamber.

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnect from the chamber.

        Returns:
            True if disconnection successful
        """
        pass

    @abstractmethod
    def set_temperature(self, temperature: float) -> bool:
        """
        Set chamber temperature setpoint.

        Args:
            temperature: Target temperature in °C

        Returns:
            True if setpoint accepted
        """
        pass

    @abstractmethod
    def set_humidity(self, humidity: float) -> bool:
        """
        Set chamber humidity setpoint.

        Args:
            humidity: Target relative humidity in %

        Returns:
            True if setpoint accepted
        """
        pass

    @abstractmethod
    def get_reading(self) -> ChamberReading:
        """
        Get current chamber readings.

        Returns:
            Current chamber environmental data
        """
        pass

    @abstractmethod
    def start(self) -> bool:
        """
        Start chamber operation (begin conditioning).

        Returns:
            True if chamber started successfully
        """
        pass

    @abstractmethod
    def stop(self) -> bool:
        """
        Stop chamber operation.

        Returns:
            True if chamber stopped successfully
        """
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get detailed chamber status.

        Returns:
            Dictionary with chamber status information
        """
        pass

    def is_connected(self) -> bool:
        """Check if chamber is connected"""
        return self._connected

    def set_setpoint(self, setpoint: ChamberSetpoint) -> bool:
        """
        Set complete chamber setpoint (temperature and humidity).

        Args:
            setpoint: Chamber setpoint configuration

        Returns:
            True if setpoint applied successfully
        """
        success = True

        # Set temperature
        if not self.set_temperature(setpoint.temperature):
            logger.error(f"Failed to set temperature to {setpoint.temperature}°C")
            success = False

        # Set humidity if specified
        if setpoint.humidity is not None:
            if not self.set_humidity(setpoint.humidity):
                logger.error(f"Failed to set humidity to {setpoint.humidity}%")
                success = False

        if success:
            self._current_setpoint = setpoint
            logger.info(f"Chamber setpoint: {setpoint.temperature}°C, {setpoint.humidity}%RH")

        return success

    def is_at_setpoint(self, reading: Optional[ChamberReading] = None) -> bool:
        """
        Check if chamber is at setpoint within tolerance.

        Args:
            reading: Chamber reading (if None, will get current reading)

        Returns:
            True if within tolerance
        """
        if self._current_setpoint is None:
            return False

        if reading is None:
            reading = self.get_reading()

        # Check temperature
        temp_diff = abs(reading.temperature - self._current_setpoint.temperature)
        if temp_diff > self._current_setpoint.temperature_tolerance:
            return False

        # Check humidity if applicable
        if self._current_setpoint.humidity is not None and reading.humidity is not None:
            humidity_diff = abs(reading.humidity - self._current_setpoint.humidity)
            if humidity_diff > self._current_setpoint.humidity_tolerance:
                return False

        return True

    def wait_for_setpoint(
        self,
        timeout: float = 3600,
        check_interval: float = 30
    ) -> bool:
        """
        Wait for chamber to reach setpoint.

        Args:
            timeout: Maximum time to wait in seconds (default: 1 hour)
            check_interval: Time between checks in seconds

        Returns:
            True if setpoint reached, False if timeout
        """
        start_time = time.time()

        while (time.time() - start_time) < timeout:
            reading = self.get_reading()

            if reading.alarm_active:
                logger.warning(f"Chamber alarm active: {reading.alarm_type}")
                return False

            if self.is_at_setpoint(reading):
                elapsed = time.time() - start_time
                logger.info(f"Chamber reached setpoint in {elapsed:.1f}s")
                return True

            time.sleep(check_interval)

        logger.error(f"Timeout waiting for chamber setpoint ({timeout}s)")
        return False


class SimulatedChamberController(ChamberControllerBase):
    """
    Simulated chamber controller for testing and development.

    Simulates realistic temperature and humidity ramping behavior.
    """

    def __init__(self, chamber_id: str, connection_params: Optional[Dict[str, Any]] = None):
        super().__init__(chamber_id, connection_params or {})
        self._temperature = 25.0  # °C
        self._humidity = 50.0  # %RH
        self._temperature_setpoint = 25.0
        self._humidity_setpoint = 50.0
        self._running = False
        self._door_open = False

    def connect(self) -> bool:
        """Simulate connection"""
        logger.info(f"Connecting to simulated chamber {self.chamber_id}")
        self._connected = True
        return True

    def disconnect(self) -> bool:
        """Simulate disconnection"""
        logger.info(f"Disconnecting from chamber {self.chamber_id}")
        self._connected = False
        return True

    def set_temperature(self, temperature: float) -> bool:
        """Set temperature setpoint"""
        if not self._connected:
            logger.error("Chamber not connected")
            return False

        if not (-40 <= temperature <= 180):
            logger.error(f"Temperature {temperature}°C out of range")
            return False

        self._temperature_setpoint = temperature
        logger.info(f"Temperature setpoint: {temperature}°C")
        return True

    def set_humidity(self, humidity: float) -> bool:
        """Set humidity setpoint"""
        if not self._connected:
            logger.error("Chamber not connected")
            return False

        if not (10 <= humidity <= 98):
            logger.error(f"Humidity {humidity}% out of range")
            return False

        self._humidity_setpoint = humidity
        logger.info(f"Humidity setpoint: {humidity}%")
        return True

    def get_reading(self) -> ChamberReading:
        """
        Get simulated reading with realistic ramping.

        Simulates exponential approach to setpoint.
        """
        if not self._connected:
            return ChamberReading(
                timestamp=datetime.utcnow(),
                temperature=0.0,
                humidity=0.0,
                alarm_active=True,
                alarm_type=ChamberAlarmType.COMMUNICATION_ERROR
            )

        # Simulate temperature ramping (10% approach per call)
        if self._running:
            temp_error = self._temperature_setpoint - self._temperature
            self._temperature += temp_error * 0.1

            humidity_error = self._humidity_setpoint - self._humidity
            self._humidity += humidity_error * 0.1

        return ChamberReading(
            timestamp=datetime.utcnow(),
            temperature=round(self._temperature, 1),
            humidity=round(self._humidity, 1),
            door_open=self._door_open,
            alarm_active=self._door_open,
            alarm_type=ChamberAlarmType.DOOR_OPEN if self._door_open else ChamberAlarmType.NONE
        )

    def start(self) -> bool:
        """Start chamber operation"""
        if not self._connected:
            logger.error("Chamber not connected")
            return False

        self._running = True
        logger.info(f"Chamber {self.chamber_id} started")
        return True

    def stop(self) -> bool:
        """Stop chamber operation"""
        if not self._connected:
            logger.error("Chamber not connected")
            return False

        self._running = False
        logger.info(f"Chamber {self.chamber_id} stopped")
        return True

    def get_status(self) -> Dict[str, Any]:
        """Get chamber status"""
        reading = self.get_reading()
        return {
            "chamber_id": self.chamber_id,
            "connected": self._connected,
            "running": self._running,
            "temperature": reading.temperature,
            "humidity": reading.humidity,
            "temperature_setpoint": self._temperature_setpoint,
            "humidity_setpoint": self._humidity_setpoint,
            "at_setpoint": self.is_at_setpoint(reading),
            "door_open": reading.door_open,
            "alarm_active": reading.alarm_active,
            "alarm_type": reading.alarm_type.value
        }

    def simulate_door_open(self, open: bool = True):
        """Simulate door open event (for testing)"""
        self._door_open = open
        logger.warning(f"Door {'opened' if open else 'closed'}")


class ChamberMonitor:
    """
    Monitor chamber conditions and log data.

    Provides continuous monitoring with alarm detection and data logging.
    """

    def __init__(
        self,
        controller: ChamberControllerBase,
        setpoint: ChamberSetpoint,
        alarm_callback=None
    ):
        """
        Initialize chamber monitor.

        Args:
            controller: Chamber controller instance
            setpoint: Target setpoint configuration
            alarm_callback: Function to call on alarm (receives ChamberReading)
        """
        self.controller = controller
        self.setpoint = setpoint
        self.alarm_callback = alarm_callback
        self._monitoring = False

    def check_conditions(self) -> tuple[bool, list[str]]:
        """
        Check if conditions are within acceptable range.

        Returns:
            Tuple of (conditions_ok, list_of_issues)
        """
        reading = self.controller.get_reading()
        issues = []

        # Check temperature
        temp_diff = abs(reading.temperature - self.setpoint.temperature)
        if temp_diff > self.setpoint.temperature_tolerance:
            issues.append(
                f"Temperature out of range: {reading.temperature}°C "
                f"(target: {self.setpoint.temperature}°C ± {self.setpoint.temperature_tolerance}°C)"
            )

        # Check humidity if applicable
        if self.setpoint.humidity is not None and reading.humidity is not None:
            humidity_diff = abs(reading.humidity - self.setpoint.humidity)
            if humidity_diff > self.setpoint.humidity_tolerance:
                issues.append(
                    f"Humidity out of range: {reading.humidity}% "
                    f"(target: {self.setpoint.humidity}% ± {self.setpoint.humidity_tolerance}%)"
                )

        # Check for alarms
        if reading.alarm_active:
            issues.append(f"Chamber alarm: {reading.alarm_type.value}")

        if reading.door_open:
            issues.append("Chamber door open")

        # Trigger callback if issues detected
        if issues and self.alarm_callback:
            self.alarm_callback(reading, issues)

        return len(issues) == 0, issues

    def get_reading(self) -> ChamberReading:
        """Get current chamber reading"""
        return self.controller.get_reading()


def create_chamber_controller(
    chamber_type: str,
    chamber_id: str,
    connection_params: Optional[Dict[str, Any]] = None
) -> ChamberControllerBase:
    """
    Factory function to create chamber controller instances.

    Args:
        chamber_type: Type of chamber ("simulated", "espec", "weiss", etc.)
        chamber_id: Unique chamber identifier
        connection_params: Connection parameters

    Returns:
        Chamber controller instance
    """
    if chamber_type.lower() == "simulated":
        return SimulatedChamberController(chamber_id, connection_params)
    else:
        # Placeholder for real chamber implementations
        logger.warning(f"Chamber type '{chamber_type}' not implemented, using simulated")
        return SimulatedChamberController(chamber_id, connection_params)
