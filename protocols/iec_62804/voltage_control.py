"""
IEC 62804 PID Testing Protocol - High Voltage Control

This module provides interfaces for controlling high voltage power supplies
used in IEC 62804 PID testing. Includes safety interlocks and voltage monitoring.
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class VoltageSupplyStatus(Enum):
    """Voltage supply status"""
    OFF = "off"
    RAMPING = "ramping"
    ON = "on"
    FAULT = "fault"
    INTERLOCK_OPEN = "interlock_open"


class InterlockType(Enum):
    """Safety interlock types"""
    DOOR = "door"
    EMERGENCY_STOP = "emergency_stop"
    OVER_CURRENT = "over_current"
    GROUND_FAULT = "ground_fault"
    EXTERNAL = "external"


@dataclass
class VoltageReading:
    """Voltage supply measurement"""
    timestamp: datetime
    voltage: float  # V
    current: float  # A (leakage current)
    status: VoltageSupplyStatus
    output_enabled: bool = False
    interlock_closed: bool = True
    fault_active: bool = False


@dataclass
class VoltageSupplyConfig:
    """Voltage supply configuration"""
    max_voltage: float = 1500.0  # V
    max_current: float = 0.1  # A (100mA for safety)
    ramp_rate: float = 100.0  # V/s
    current_limit: float = 0.05  # A (50mA trip threshold)


class VoltageSupplyBase(ABC):
    """
    Base class for high voltage power supply controllers.

    Implements safety features and monitoring for PID testing.
    """

    def __init__(
        self,
        supply_id: str,
        connection_params: Dict[str, Any],
        config: Optional[VoltageSupplyConfig] = None
    ):
        """
        Initialize voltage supply controller.

        Args:
            supply_id: Unique identifier
            connection_params: Connection parameters
            config: Supply configuration
        """
        self.supply_id = supply_id
        self.connection_params = connection_params
        self.config = config or VoltageSupplyConfig()
        self._connected = False
        self._interlocks: Dict[InterlockType, bool] = {}
        self._emergency_stop = False

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to voltage supply"""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from voltage supply"""
        pass

    @abstractmethod
    def set_voltage(self, voltage: float) -> bool:
        """
        Set output voltage setpoint.

        Args:
            voltage: Target voltage (typically negative for PID testing)

        Returns:
            True if setpoint accepted
        """
        pass

    @abstractmethod
    def set_current_limit(self, current: float) -> bool:
        """
        Set current limit.

        Args:
            current: Maximum current in A

        Returns:
            True if limit set successfully
        """
        pass

    @abstractmethod
    def enable_output(self) -> bool:
        """
        Enable voltage output.

        Returns:
            True if output enabled
        """
        pass

    @abstractmethod
    def disable_output(self) -> bool:
        """
        Disable voltage output.

        Returns:
            True if output disabled
        """
        pass

    @abstractmethod
    def get_reading(self) -> VoltageReading:
        """
        Get current voltage and current readings.

        Returns:
            Voltage supply measurements
        """
        pass

    @abstractmethod
    def reset_fault(self) -> bool:
        """
        Reset fault condition.

        Returns:
            True if fault cleared
        """
        pass

    def is_connected(self) -> bool:
        """Check connection status"""
        return self._connected

    def check_interlocks(self) -> tuple[bool, list[str]]:
        """
        Check all safety interlocks.

        Returns:
            Tuple of (all_closed, list_of_open_interlocks)
        """
        open_interlocks = [
            name.value for name, closed in self._interlocks.items()
            if not closed
        ]

        if self._emergency_stop:
            open_interlocks.append("emergency_stop")

        return len(open_interlocks) == 0, open_interlocks

    def set_interlock(self, interlock_type: InterlockType, closed: bool):
        """
        Set interlock state.

        Args:
            interlock_type: Type of interlock
            closed: True if interlock closed (safe), False if open (unsafe)
        """
        self._interlocks[interlock_type] = closed

        if not closed:
            logger.warning(f"Interlock opened: {interlock_type.value}")
            # Automatically disable output when interlock opens
            self.disable_output()

    def emergency_stop(self):
        """
        Trigger emergency stop.

        Immediately disables output and sets emergency stop flag.
        """
        logger.critical("EMERGENCY STOP TRIGGERED")
        self._emergency_stop = True
        self.disable_output()

    def reset_emergency_stop(self) -> bool:
        """
        Reset emergency stop condition.

        Returns:
            True if reset successful
        """
        if self._emergency_stop:
            logger.info("Resetting emergency stop")
            self._emergency_stop = False
            return self.reset_fault()
        return True

    def ramp_to_voltage(
        self,
        target_voltage: float,
        timeout: float = 60.0,
        check_interval: float = 0.5
    ) -> bool:
        """
        Ramp voltage to target with monitoring.

        Args:
            target_voltage: Target voltage
            timeout: Maximum time to wait
            check_interval: Time between checks

        Returns:
            True if target reached
        """
        # Set the voltage setpoint
        if not self.set_voltage(target_voltage):
            logger.error("Failed to set voltage")
            return False

        # Enable output if not already enabled
        reading = self.get_reading()
        if not reading.output_enabled:
            if not self.enable_output():
                logger.error("Failed to enable output")
                return False

        # Wait for voltage to stabilize
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            reading = self.get_reading()

            # Check for faults
            if reading.fault_active:
                logger.error("Fault detected during voltage ramp")
                return False

            # Check if target reached (within 5V tolerance)
            if abs(reading.voltage - target_voltage) < 5.0:
                logger.info(f"Target voltage reached: {reading.voltage}V")
                return True

            time.sleep(check_interval)

        logger.error(f"Timeout ramping to {target_voltage}V")
        return False

    def safe_shutdown(self) -> bool:
        """
        Safely shut down voltage output.

        Returns:
            True if shutdown successful
        """
        logger.info("Initiating safe shutdown")

        # Disable output
        if not self.disable_output():
            logger.error("Failed to disable output")
            return False

        # Verify output is off
        time.sleep(1.0)
        reading = self.get_reading()

        if abs(reading.voltage) > 1.0:
            logger.warning(f"Voltage still present after shutdown: {reading.voltage}V")
            return False

        logger.info("Safe shutdown complete")
        return True


class SimulatedVoltageSupply(VoltageSupplyBase):
    """
    Simulated high voltage supply for testing and development.
    """

    def __init__(
        self,
        supply_id: str,
        connection_params: Optional[Dict[str, Any]] = None,
        config: Optional[VoltageSupplyConfig] = None
    ):
        super().__init__(supply_id, connection_params or {}, config)
        self._voltage_setpoint = 0.0
        self._voltage_actual = 0.0
        self._current_limit = 0.05  # 50mA
        self._current_actual = 0.0
        self._output_enabled = False
        self._fault = False

    def connect(self) -> bool:
        """Simulate connection"""
        logger.info(f"Connecting to simulated voltage supply {self.supply_id}")
        self._connected = True
        return True

    def disconnect(self) -> bool:
        """Simulate disconnection"""
        logger.info(f"Disconnecting from voltage supply {self.supply_id}")
        self._connected = False
        return True

    def set_voltage(self, voltage: float) -> bool:
        """Set voltage setpoint"""
        if not self._connected:
            logger.error("Supply not connected")
            return False

        if abs(voltage) > self.config.max_voltage:
            logger.error(f"Voltage {voltage}V exceeds maximum {self.config.max_voltage}V")
            return False

        self._voltage_setpoint = voltage
        logger.info(f"Voltage setpoint: {voltage}V")
        return True

    def set_current_limit(self, current: float) -> bool:
        """Set current limit"""
        if not self._connected:
            logger.error("Supply not connected")
            return False

        if current > self.config.max_current:
            logger.error(f"Current {current}A exceeds maximum {self.config.max_current}A")
            return False

        self._current_limit = current
        logger.info(f"Current limit: {current * 1000}mA")
        return True

    def enable_output(self) -> bool:
        """Enable output"""
        if not self._connected:
            logger.error("Supply not connected")
            return False

        # Check interlocks
        interlocks_ok, open_interlocks = self.check_interlocks()
        if not interlocks_ok:
            logger.error(f"Cannot enable output - interlocks open: {open_interlocks}")
            return False

        self._output_enabled = True
        logger.info("Output enabled")
        return True

    def disable_output(self) -> bool:
        """Disable output"""
        if not self._connected:
            logger.error("Supply not connected")
            return False

        self._output_enabled = False
        self._voltage_actual = 0.0
        self._current_actual = 0.0
        logger.info("Output disabled")
        return True

    def get_reading(self) -> VoltageReading:
        """
        Get simulated reading with realistic behavior.
        """
        if not self._connected:
            return VoltageReading(
                timestamp=datetime.utcnow(),
                voltage=0.0,
                current=0.0,
                status=VoltageSupplyStatus.FAULT,
                output_enabled=False,
                interlock_closed=False,
                fault_active=True
            )

        # Simulate voltage ramping
        if self._output_enabled:
            error = self._voltage_setpoint - self._voltage_actual
            ramp_step = min(abs(error), self.config.ramp_rate * 0.1)  # 100ms update
            if error > 0:
                self._voltage_actual += ramp_step
            elif error < 0:
                self._voltage_actual -= ramp_step

            # Simulate leakage current (proportional to voltage)
            self._current_actual = abs(self._voltage_actual) / 1000.0 * 0.01  # ~10mA at -1000V

            # Check current limit
            if self._current_actual > self._current_limit:
                logger.error(f"Current limit exceeded: {self._current_actual * 1000}mA")
                self._fault = True
                self._output_enabled = False
        else:
            self._voltage_actual = 0.0
            self._current_actual = 0.0

        # Determine status
        if self._fault:
            status = VoltageSupplyStatus.FAULT
        elif not self._output_enabled:
            status = VoltageSupplyStatus.OFF
        elif abs(self._voltage_actual - self._voltage_setpoint) > 5.0:
            status = VoltageSupplyStatus.RAMPING
        else:
            status = VoltageSupplyStatus.ON

        interlocks_ok, _ = self.check_interlocks()

        return VoltageReading(
            timestamp=datetime.utcnow(),
            voltage=round(self._voltage_actual, 2),
            current=round(self._current_actual, 6),
            status=status,
            output_enabled=self._output_enabled,
            interlock_closed=interlocks_ok,
            fault_active=self._fault
        )

    def reset_fault(self) -> bool:
        """Reset fault"""
        logger.info("Resetting fault")
        self._fault = False
        return True

    def simulate_fault(self):
        """Simulate a fault condition (for testing)"""
        logger.warning("Simulating fault condition")
        self._fault = True
        self._output_enabled = False


class VoltageMonitor:
    """
    Monitor voltage supply and detect unsafe conditions.
    """

    def __init__(
        self,
        supply: VoltageSupplyBase,
        current_threshold: float = 0.05,  # 50mA
        alarm_callback: Optional[Callable] = None
    ):
        """
        Initialize voltage monitor.

        Args:
            supply: Voltage supply instance
            current_threshold: Current threshold for alarm (A)
            alarm_callback: Function to call on alarm
        """
        self.supply = supply
        self.current_threshold = current_threshold
        self.alarm_callback = alarm_callback

    def check_safety(self) -> tuple[bool, list[str]]:
        """
        Check voltage supply safety conditions.

        Returns:
            Tuple of (safe, list_of_issues)
        """
        reading = self.supply.get_reading()
        issues = []

        # Check for faults
        if reading.fault_active:
            issues.append("Voltage supply fault active")

        # Check interlocks
        if not reading.interlock_closed:
            issues.append("Safety interlock open")

        # Check current
        if reading.current > self.current_threshold:
            issues.append(
                f"Excessive leakage current: {reading.current * 1000:.1f}mA "
                f"(threshold: {self.current_threshold * 1000:.1f}mA)"
            )

        # Trigger callback if issues detected
        if issues and self.alarm_callback:
            self.alarm_callback(reading, issues)

        return len(issues) == 0, issues

    def get_reading(self) -> VoltageReading:
        """Get current voltage reading"""
        return self.supply.get_reading()


def create_voltage_supply(
    supply_type: str,
    supply_id: str,
    connection_params: Optional[Dict[str, Any]] = None,
    config: Optional[VoltageSupplyConfig] = None
) -> VoltageSupplyBase:
    """
    Factory function to create voltage supply instances.

    Args:
        supply_type: Type of supply ("simulated", "keithley", "sorensen", etc.)
        supply_id: Unique supply identifier
        connection_params: Connection parameters
        config: Supply configuration

    Returns:
        Voltage supply instance
    """
    if supply_type.lower() == "simulated":
        return SimulatedVoltageSupply(supply_id, connection_params, config)
    else:
        # Placeholder for real supply implementations
        logger.warning(f"Supply type '{supply_type}' not implemented, using simulated")
        return SimulatedVoltageSupply(supply_id, connection_params, config)
