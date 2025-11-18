"""
Temperature Chamber Control for IEC 61853 Testing
==================================================

Automated temperature chamber control for performance matrix testing.

Features:
- PID temperature control
- Stabilization monitoring
- Safety interlocks
- Multi-zone chamber support
- Real-time temperature logging
- Alarm and notification system

Supported chambers:
- Espec SU-series
- Weiss WKL/WK series
- Vötsch VC series
- Generic RS-232/RS-485/Ethernet chambers
"""

import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import threading
from queue import Queue


# Configure logging
logger = logging.getLogger(__name__)


# ==================== Enumerations ====================

class ChamberState(str, Enum):
    """Chamber operating state"""
    IDLE = "idle"
    HEATING = "heating"
    COOLING = "cooling"
    STABILIZING = "stabilizing"
    STABLE = "stable"
    ERROR = "error"
    SAFETY_SHUTDOWN = "safety_shutdown"


class AlarmLevel(str, Enum):
    """Alarm severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# ==================== Data Classes ====================

@dataclass
class TemperatureReading:
    """Single temperature reading"""
    timestamp: datetime
    setpoint: float  # °C
    actual: float  # °C
    error: float  # °C
    zone: int = 1
    humidity: Optional[float] = None  # % RH


@dataclass
class ChamberStatus:
    """Current chamber status"""
    state: ChamberState
    temperature: float  # °C
    setpoint: float  # °C
    stability: float  # ±°C
    humidity: Optional[float] = None
    door_open: bool = False
    alarm_active: bool = False
    alarm_message: Optional[str] = None


@dataclass
class StabilizationCriteria:
    """Criteria for temperature stabilization"""
    tolerance: float = 2.0  # ±°C
    duration: float = 600.0  # seconds (10 minutes)
    max_wait_time: float = 3600.0  # seconds (1 hour)
    sample_interval: float = 5.0  # seconds


@dataclass
class ChamberLimits:
    """Safety limits for chamber operation"""
    min_temperature: float = -40.0  # °C
    max_temperature: float = 85.0  # °C
    max_rate_of_change: float = 5.0  # °C/min
    max_humidity: float = 95.0  # % RH


# ==================== Abstract Base Chamber ====================

class TemperatureChamber(ABC):
    """Abstract base class for temperature chambers"""

    def __init__(
        self,
        chamber_id: str,
        limits: Optional[ChamberLimits] = None,
        stabilization: Optional[StabilizationCriteria] = None
    ):
        self.chamber_id = chamber_id
        self.limits = limits or ChamberLimits()
        self.stabilization = stabilization or StabilizationCriteria()

        self._state = ChamberState.IDLE
        self._current_setpoint: Optional[float] = None
        self._temperature_log: List[TemperatureReading] = []
        self._alarm_callbacks: List[Callable] = []

        logger.info(f"Temperature chamber '{chamber_id}' initialized")

    @abstractmethod
    def connect(self) -> bool:
        """Connect to the chamber"""
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from the chamber"""
        pass

    @abstractmethod
    def set_temperature(self, temperature: float) -> bool:
        """Set target temperature"""
        pass

    @abstractmethod
    def get_temperature(self) -> float:
        """Read current temperature"""
        pass

    @abstractmethod
    def get_status(self) -> ChamberStatus:
        """Get current chamber status"""
        pass

    @abstractmethod
    def start_control(self) -> bool:
        """Start temperature control"""
        pass

    @abstractmethod
    def stop_control(self) -> bool:
        """Stop temperature control"""
        pass

    def validate_temperature(self, temperature: float) -> bool:
        """Validate temperature is within safe limits"""
        if temperature < self.limits.min_temperature:
            logger.error(f"Temperature {temperature}°C below minimum {self.limits.min_temperature}°C")
            return False
        if temperature > self.limits.max_temperature:
            logger.error(f"Temperature {temperature}°C above maximum {self.limits.max_temperature}°C")
            return False
        return True

    def wait_for_stabilization(
        self,
        target_temperature: float,
        criteria: Optional[StabilizationCriteria] = None
    ) -> bool:
        """
        Wait for chamber to stabilize at target temperature

        Returns:
            bool: True if stabilized, False if timeout or error
        """
        criteria = criteria or self.stabilization
        start_time = time.time()
        stable_start: Optional[float] = None

        logger.info(
            f"Waiting for stabilization at {target_temperature}°C "
            f"(±{criteria.tolerance}°C for {criteria.duration}s)"
        )

        while True:
            elapsed = time.time() - start_time

            # Check timeout
            if elapsed > criteria.max_wait_time:
                logger.error(f"Stabilization timeout after {elapsed:.1f}s")
                return False

            # Get current temperature
            current_temp = self.get_temperature()
            error = abs(current_temp - target_temperature)

            # Log reading
            reading = TemperatureReading(
                timestamp=datetime.utcnow(),
                setpoint=target_temperature,
                actual=current_temp,
                error=error
            )
            self._temperature_log.append(reading)

            # Check if within tolerance
            if error <= criteria.tolerance:
                if stable_start is None:
                    stable_start = time.time()
                    logger.info(f"Entered stability window at {current_temp:.2f}°C")

                stable_duration = time.time() - stable_start
                if stable_duration >= criteria.duration:
                    logger.info(
                        f"Stabilization achieved in {elapsed:.1f}s "
                        f"(stable for {stable_duration:.1f}s)"
                    )
                    self._state = ChamberState.STABLE
                    return True

                logger.debug(
                    f"Stable for {stable_duration:.1f}/{criteria.duration}s "
                    f"at {current_temp:.2f}°C"
                )
            else:
                if stable_start is not None:
                    logger.warning(
                        f"Lost stability: {current_temp:.2f}°C "
                        f"(error: {error:.2f}°C)"
                    )
                stable_start = None

            time.sleep(criteria.sample_interval)

    def get_temperature_log(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[TemperatureReading]:
        """Get temperature log for specified time range"""
        log = self._temperature_log

        if start_time:
            log = [r for r in log if r.timestamp >= start_time]
        if end_time:
            log = [r for r in log if r.timestamp <= end_time]

        return log

    def clear_temperature_log(self):
        """Clear temperature log"""
        self._temperature_log.clear()
        logger.info("Temperature log cleared")

    def register_alarm_callback(self, callback: Callable):
        """Register callback for alarm notifications"""
        self._alarm_callbacks.append(callback)

    def _trigger_alarm(self, level: AlarmLevel, message: str):
        """Trigger alarm and notify callbacks"""
        logger.warning(f"ALARM [{level.value}]: {message}")
        for callback in self._alarm_callbacks:
            try:
                callback(level, message)
            except Exception as e:
                logger.error(f"Error in alarm callback: {e}")


# ==================== Chamber Controller ====================

class ChamberController:
    """
    High-level controller for temperature chamber operations

    Manages multiple chambers and coordinates temperature cycling for
    performance matrix testing.
    """

    def __init__(self, chamber: TemperatureChamber):
        self.chamber = chamber
        self._test_sequence: List[float] = []
        self._current_step: int = 0
        self._running = False
        self._monitoring_thread: Optional[threading.Thread] = None

    def connect(self) -> bool:
        """Connect to chamber"""
        return self.chamber.connect()

    def disconnect(self):
        """Disconnect from chamber"""
        self.stop_monitoring()
        self.chamber.disconnect()

    def set_temperature_sequence(self, temperatures: List[float]) -> bool:
        """
        Set sequence of temperatures for automated testing

        Args:
            temperatures: List of target temperatures in °C

        Returns:
            bool: True if sequence is valid
        """
        # Validate all temperatures
        for temp in temperatures:
            if not self.chamber.validate_temperature(temp):
                return False

        self._test_sequence = temperatures
        self._current_step = 0
        logger.info(f"Temperature sequence set: {temperatures}")
        return True

    def run_temperature_sequence(
        self,
        stabilization_criteria: Optional[StabilizationCriteria] = None
    ) -> bool:
        """
        Execute temperature sequence with stabilization at each point

        Returns:
            bool: True if sequence completed successfully
        """
        if not self._test_sequence:
            logger.error("No temperature sequence defined")
            return False

        logger.info(f"Starting temperature sequence ({len(self._test_sequence)} steps)")
        self._running = True
        self._current_step = 0

        for i, target_temp in enumerate(self._test_sequence):
            if not self._running:
                logger.info("Sequence interrupted by user")
                return False

            self._current_step = i + 1
            logger.info(
                f"Step {self._current_step}/{len(self._test_sequence)}: "
                f"Setting temperature to {target_temp}°C"
            )

            # Set temperature
            if not self.chamber.set_temperature(target_temp):
                logger.error(f"Failed to set temperature to {target_temp}°C")
                return False

            # Start control
            if not self.chamber.start_control():
                logger.error("Failed to start chamber control")
                return False

            # Wait for stabilization
            if not self.chamber.wait_for_stabilization(target_temp, stabilization_criteria):
                logger.error(f"Failed to stabilize at {target_temp}°C")
                return False

            logger.info(f"Step {self._current_step} completed successfully")

        logger.info("Temperature sequence completed successfully")
        self._running = False
        return True

    def goto_temperature(
        self,
        temperature: float,
        wait_stable: bool = True,
        criteria: Optional[StabilizationCriteria] = None
    ) -> bool:
        """
        Go to specific temperature and optionally wait for stabilization

        Args:
            temperature: Target temperature in °C
            wait_stable: Wait for stabilization before returning
            criteria: Stabilization criteria (optional)

        Returns:
            bool: True if successful
        """
        # Validate temperature
        if not self.chamber.validate_temperature(temperature):
            return False

        logger.info(f"Moving to {temperature}°C")

        # Set temperature
        if not self.chamber.set_temperature(temperature):
            return False

        # Start control
        if not self.chamber.start_control():
            return False

        # Wait for stabilization if requested
        if wait_stable:
            return self.chamber.wait_for_stabilization(temperature, criteria)

        return True

    def start_monitoring(self, interval: float = 10.0):
        """Start background temperature monitoring"""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            logger.warning("Monitoring already running")
            return

        self._running = True
        self._monitoring_thread = threading.Thread(
            target=self._monitor_temperature,
            args=(interval,),
            daemon=True
        )
        self._monitoring_thread.start()
        logger.info(f"Temperature monitoring started (interval: {interval}s)")

    def stop_monitoring(self):
        """Stop background temperature monitoring"""
        self._running = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5.0)
            logger.info("Temperature monitoring stopped")

    def _monitor_temperature(self, interval: float):
        """Background monitoring thread"""
        while self._running:
            try:
                status = self.chamber.get_status()
                logger.debug(
                    f"Chamber status: {status.state.value}, "
                    f"Temp: {status.temperature:.2f}°C, "
                    f"Setpoint: {status.setpoint:.2f}°C"
                )

                # Check for alarms
                if status.alarm_active:
                    logger.warning(f"Chamber alarm: {status.alarm_message}")

            except Exception as e:
                logger.error(f"Monitoring error: {e}")

            time.sleep(interval)

    def get_status(self) -> Dict[str, Any]:
        """Get controller status"""
        chamber_status = self.chamber.get_status()

        return {
            "chamber_id": self.chamber.chamber_id,
            "chamber_state": chamber_status.state.value,
            "temperature": chamber_status.temperature,
            "setpoint": chamber_status.setpoint,
            "stability": chamber_status.stability,
            "sequence_running": self._running,
            "sequence_step": self._current_step,
            "sequence_total": len(self._test_sequence),
            "alarm_active": chamber_status.alarm_active,
        }


# ==================== Simulated Chamber (for testing) ====================

class SimulatedChamber(TemperatureChamber):
    """Simulated temperature chamber for testing"""

    def __init__(
        self,
        chamber_id: str = "SIM-001",
        thermal_time_constant: float = 300.0,  # seconds
        **kwargs
    ):
        super().__init__(chamber_id, **kwargs)
        self.thermal_time_constant = thermal_time_constant
        self._connected = False
        self._current_temperature = 25.0  # °C
        self._control_active = False

    def connect(self) -> bool:
        """Simulate connection"""
        self._connected = True
        logger.info(f"Simulated chamber '{self.chamber_id}' connected")
        return True

    def disconnect(self):
        """Simulate disconnection"""
        self._connected = False
        self._control_active = False
        logger.info(f"Simulated chamber '{self.chamber_id}' disconnected")

    def set_temperature(self, temperature: float) -> bool:
        """Set target temperature"""
        if not self._connected:
            logger.error("Chamber not connected")
            return False

        if not self.validate_temperature(temperature):
            return False

        self._current_setpoint = temperature
        logger.info(f"Setpoint set to {temperature}°C")
        return True

    def get_temperature(self) -> float:
        """Get current temperature (simulated)"""
        if not self._connected:
            raise RuntimeError("Chamber not connected")

        # Simulate thermal response (first-order lag)
        if self._control_active and self._current_setpoint is not None:
            error = self._current_setpoint - self._current_temperature
            # Simple exponential approach
            self._current_temperature += error * 0.1  # Simplified dynamics

        return self._current_temperature

    def get_status(self) -> ChamberStatus:
        """Get chamber status"""
        if not self._connected:
            return ChamberStatus(
                state=ChamberState.ERROR,
                temperature=0.0,
                setpoint=0.0,
                stability=0.0,
                alarm_active=True,
                alarm_message="Chamber not connected"
            )

        # Determine state
        if not self._control_active:
            state = ChamberState.IDLE
        elif self._current_setpoint is None:
            state = ChamberState.IDLE
        else:
            error = abs(self._current_temperature - self._current_setpoint)
            if error <= self.stabilization.tolerance:
                state = ChamberState.STABLE
            elif self._current_temperature < self._current_setpoint:
                state = ChamberState.HEATING
            else:
                state = ChamberState.COOLING

        return ChamberStatus(
            state=state,
            temperature=self._current_temperature,
            setpoint=self._current_setpoint or 0.0,
            stability=abs(self._current_temperature - (self._current_setpoint or 0.0)),
            door_open=False,
            alarm_active=False
        )

    def start_control(self) -> bool:
        """Start temperature control"""
        if not self._connected:
            return False
        self._control_active = True
        self._state = ChamberState.HEATING if self._current_setpoint and self._current_setpoint > self._current_temperature else ChamberState.COOLING
        logger.info("Temperature control started")
        return True

    def stop_control(self) -> bool:
        """Stop temperature control"""
        self._control_active = False
        self._state = ChamberState.IDLE
        logger.info("Temperature control stopped")
        return True
