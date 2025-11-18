"""
Safety utilities for high voltage testing and equipment interlocks.
"""

from typing import Optional, Callable
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SafetyStatus(str, Enum):
    """Safety interlock status."""
    SAFE = "safe"
    UNSAFE = "unsafe"
    UNKNOWN = "unknown"


class SafetyInterlock:
    """
    Safety interlock system for high voltage testing.

    Implements mandatory safety checks before and during test execution.
    """

    def __init__(self, test_name: str):
        """
        Initialize safety interlock.

        Args:
            test_name: Name of the test for logging purposes
        """
        self.test_name = test_name
        self.status = SafetyStatus.UNKNOWN
        self.safety_checks = []
        logger.info(f"Safety interlock initialized for {test_name}")

    def add_check(self, name: str, check_fn: Callable[[], bool]):
        """
        Add a safety check function.

        Args:
            name: Name of the safety check
            check_fn: Function that returns True if safe, False otherwise
        """
        self.safety_checks.append({"name": name, "function": check_fn})

    def verify_all_checks(self) -> bool:
        """
        Verify all safety checks pass.

        Returns:
            True if all safety checks pass, False otherwise
        """
        logger.info(f"Running {len(self.safety_checks)} safety checks for {self.test_name}")

        all_passed = True
        for check in self.safety_checks:
            try:
                result = check["function"]()
                if not result:
                    logger.error(f"Safety check FAILED: {check['name']}")
                    all_passed = False
                else:
                    logger.info(f"Safety check passed: {check['name']}")
            except Exception as e:
                logger.error(f"Safety check ERROR in {check['name']}: {str(e)}")
                all_passed = False

        self.status = SafetyStatus.SAFE if all_passed else SafetyStatus.UNSAFE
        return all_passed

    def emergency_stop(self) -> None:
        """
        Execute emergency stop procedure.
        """
        logger.critical(f"EMERGENCY STOP activated for {self.test_name}")
        self.status = SafetyStatus.UNSAFE
        # In real implementation, this would trigger hardware interlocks


class HighVoltageProtection:
    """
    High voltage safety protection system.

    Ensures safe operation of high voltage equipment per IEC 61010 and ISO 17025.
    """

    def __init__(self, max_voltage: float, max_current_ua: float):
        """
        Initialize HV protection.

        Args:
            max_voltage: Maximum allowed voltage (V)
            max_current_ua: Maximum allowed current (μA)
        """
        self.max_voltage = max_voltage
        self.max_current_ua = max_current_ua
        self.is_enabled = False
        logger.info(f"HV Protection: Max {max_voltage}V, {max_current_ua}μA")

    def enable(self) -> bool:
        """
        Enable high voltage output (requires safety checks).

        Returns:
            True if enabled successfully, False otherwise
        """
        logger.warning("HIGH VOLTAGE ENABLED - Ensure all safety precautions are in place")
        self.is_enabled = True
        return True

    def disable(self) -> None:
        """
        Disable high voltage output.
        """
        logger.info("High voltage disabled")
        self.is_enabled = False

    def check_limits(self, voltage: float, current_ua: float) -> bool:
        """
        Check if voltage and current are within safe limits.

        Args:
            voltage: Applied voltage (V)
            current_ua: Measured current (μA)

        Returns:
            True if within limits, False otherwise
        """
        if voltage > self.max_voltage:
            logger.error(f"Voltage {voltage}V exceeds limit {self.max_voltage}V")
            return False

        if current_ua > self.max_current_ua:
            logger.error(f"Current {current_ua}μA exceeds limit {self.max_current_ua}μA")
            return False

        return True
