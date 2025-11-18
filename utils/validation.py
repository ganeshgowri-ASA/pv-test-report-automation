"""
Validation utilities for ISO 17025 compliance and data integrity.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ISO17025Validator:
    """
    Validates test data for ISO 17025 compliance.

    Ensures proper traceability, calibration status, and data integrity.
    """

    @staticmethod
    def validate_calibration(
        calibration_date: Optional[datetime],
        calibration_interval_days: int = 365
    ) -> bool:
        """
        Validate equipment calibration is current.

        Args:
            calibration_date: Date of last calibration
            calibration_interval_days: Required calibration interval

        Returns:
            True if calibration is current, False otherwise
        """
        if calibration_date is None:
            logger.warning("No calibration date provided")
            return False

        now = datetime.now()
        expiry = calibration_date + timedelta(days=calibration_interval_days)

        if now > expiry:
            logger.error(
                f"Calibration EXPIRED: Last calibrated {calibration_date}, "
                f"expired {expiry}"
            )
            return False

        days_remaining = (expiry - now).days
        logger.info(f"Calibration valid: {days_remaining} days remaining")
        return True

    @staticmethod
    def validate_traceability(test_data: Dict[str, Any]) -> bool:
        """
        Validate test has proper traceability information.

        Args:
            test_data: Dictionary containing test data

        Returns:
            True if traceability is complete, False otherwise
        """
        required_fields = [
            "test_id",
            "module_id",
            "test_date",
            "operator_id",
            "equipment_id"
        ]

        missing_fields = []
        for field in required_fields:
            if field not in test_data or test_data[field] is None:
                missing_fields.append(field)

        if missing_fields:
            logger.error(f"Missing traceability fields: {', '.join(missing_fields)}")
            return False

        logger.info("Traceability validation passed")
        return True

    @staticmethod
    def validate_environmental_conditions(
        ambient_temp_c: Optional[float],
        humidity_percent: Optional[float],
        required: bool = True
    ) -> bool:
        """
        Validate environmental conditions are recorded and within limits.

        Args:
            ambient_temp_c: Ambient temperature
            humidity_percent: Relative humidity
            required: Whether environmental data is required

        Returns:
            True if conditions are valid, False otherwise
        """
        if required and (ambient_temp_c is None or humidity_percent is None):
            logger.error("Environmental conditions required but not provided")
            return False

        if ambient_temp_c is not None:
            if not (15 <= ambient_temp_c <= 35):
                logger.warning(
                    f"Temperature {ambient_temp_c}°C outside standard range (15-35°C)"
                )

        if humidity_percent is not None:
            if not (25 <= humidity_percent <= 75):
                logger.warning(
                    f"Humidity {humidity_percent}% outside standard range (25-75%)"
                )

        return True


class DataIntegrityValidator:
    """
    Validates data integrity and measurement quality.
    """

    @staticmethod
    def validate_measurement_range(
        value: float,
        min_value: float,
        max_value: float,
        name: str = "Measurement"
    ) -> bool:
        """
        Validate measurement is within expected range.

        Args:
            value: Measured value
            min_value: Minimum expected value
            max_value: Maximum expected value
            name: Name of measurement for logging

        Returns:
            True if within range, False otherwise
        """
        if not (min_value <= value <= max_value):
            logger.error(
                f"{name} {value} outside valid range [{min_value}, {max_value}]"
            )
            return False

        logger.debug(f"{name} {value} within valid range")
        return True

    @staticmethod
    def validate_duration(
        duration_sec: int,
        min_duration_sec: int,
        name: str = "Test"
    ) -> bool:
        """
        Validate test duration meets minimum requirements.

        Args:
            duration_sec: Actual test duration
            min_duration_sec: Minimum required duration
            name: Name of test for logging

        Returns:
            True if duration is sufficient, False otherwise
        """
        if duration_sec < min_duration_sec:
            logger.error(
                f"{name} duration {duration_sec}s is less than "
                f"required {min_duration_sec}s"
            )
            return False

        logger.info(f"{name} duration {duration_sec}s meets requirement")
        return True
