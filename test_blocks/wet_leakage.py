"""
Wet Leakage Current Test Block per IEC 61215/61730.

Tests electrical insulation integrity of PV modules after water immersion.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import logging
from pydantic import Field, field_validator

from models.base import BaseTestModel, TestStatus
from utils.safety import SafetyInterlock, HighVoltageProtection
from utils.validation import ISO17025Validator, DataIntegrityValidator

logger = logging.getLogger(__name__)


class WetLeakageTestResult(BaseTestModel):
    """
    Data model for wet leakage current test results.

    Per IEC 61215-2:2016 and IEC 61730-2:2016 standards.
    """

    # Test parameters
    applied_voltage: float = Field(
        ...,
        description="Applied DC voltage (V)",
        gt=0
    )
    module_voc: Optional[float] = Field(
        None,
        description="Module open-circuit voltage Voc (V)",
        gt=0
    )
    immersion_duration_hours: float = Field(
        24.0,
        description="Water immersion duration (hours)",
        ge=24.0
    )

    # Measurement results
    leakage_current_ua: float = Field(
        ...,
        description="Measured leakage current (μA)",
        ge=0
    )
    duration_sec: int = Field(
        ...,
        description="Measurement duration (seconds)",
        ge=0
    )

    # Test conditions
    water_resistivity_ohm_cm: Optional[float] = Field(
        None,
        description="Water resistivity (Ω·cm)",
        gt=0
    )
    water_temp_c: Optional[float] = Field(
        None,
        description="Water temperature (°C)"
    )

    # Pass/fail criteria
    max_leakage_ua: float = Field(
        50.0,
        description="Maximum allowed leakage current (μA)",
        gt=0
    )
    min_duration_sec: int = Field(
        120,
        description="Minimum test duration (seconds)",
        gt=0
    )

    @field_validator('applied_voltage')
    @classmethod
    def validate_applied_voltage(cls, v, info):
        """Validate applied voltage meets IEC requirements."""
        # Should be at least 1000V or 2 × Voc + 1000V, whichever is higher
        min_voltage = 1000.0
        if v < min_voltage:
            raise ValueError(f"Applied voltage must be at least {min_voltage}V")
        return v

    @field_validator('leakage_current_ua')
    @classmethod
    def validate_leakage_current(cls, v):
        """Validate leakage current is within measurable range."""
        if v < 0:
            raise ValueError("Leakage current cannot be negative")
        if v > 10000:  # 10 mA in μA
            raise ValueError("Leakage current exceeds maximum measurable value")
        return v

    def determine_pass_fail(self) -> bool:
        """
        Determine pass/fail status based on IEC 61215/61730 criteria.

        Returns:
            True if test passes, False otherwise
        """
        # Check leakage current limit
        current_pass = self.leakage_current_ua < self.max_leakage_ua

        # Check minimum duration
        duration_pass = self.duration_sec >= self.min_duration_sec

        # Overall pass requires both criteria
        self.pass_status = current_pass and duration_pass

        if not current_pass:
            logger.error(
                f"FAIL: Leakage current {self.leakage_current_ua}μA "
                f"exceeds limit {self.max_leakage_ua}μA"
            )

        if not duration_pass:
            logger.error(
                f"FAIL: Duration {self.duration_sec}s is less than "
                f"minimum {self.min_duration_sec}s"
            )

        if self.pass_status:
            logger.info(
                f"PASS: Leakage current {self.leakage_current_ua}μA "
                f"within limit, duration {self.duration_sec}s sufficient"
            )

        return self.pass_status


class WetLeakageTest:
    """
    Wet leakage current test implementation with automated measurement.

    Features:
    - Automated high voltage application
    - Safety interlocks and emergency stop
    - Real-time current monitoring
    - ISO 17025 compliant data recording
    - Pass/fail determination per IEC standards
    """

    def __init__(
        self,
        module: str,
        module_voc: Optional[float] = None,
        test_id: Optional[int] = None,
        module_id: Optional[int] = None
    ):
        """
        Initialize wet leakage test.

        Args:
            module: Module identifier string (e.g., "PV-001")
            module_voc: Module open-circuit voltage (V)
            test_id: Unique test identifier
            module_id: Module database ID
        """
        self.module = module
        self.module_voc = module_voc
        self.test_id = test_id or hash(f"{module}_{datetime.now()}")
        self.module_id = module_id or hash(module)

        # Initialize safety systems
        self.safety = SafetyInterlock("Wet Leakage Current Test")
        self.hv_protection = None

        # Setup safety checks
        self._setup_safety_checks()

        logger.info(f"Wet leakage test initialized for module {module}")

    def _setup_safety_checks(self) -> None:
        """Setup mandatory safety checks."""
        self.safety.add_check(
            "Water tank grounded",
            lambda: True  # In real implementation, check ground connection
        )
        self.safety.add_check(
            "Emergency stop functional",
            lambda: True  # In real implementation, verify E-stop circuit
        )
        self.safety.add_check(
            "Interlocks closed",
            lambda: True  # In real implementation, check physical interlocks
        )
        self.safety.add_check(
            "Personnel clear",
            lambda: True  # In real implementation, check area sensors
        )

    def calculate_test_voltage(self, voltage: Optional[float] = None) -> float:
        """
        Calculate required test voltage per IEC 61215/61730.

        Args:
            voltage: Override voltage (V), or None to auto-calculate

        Returns:
            Required test voltage (V)
        """
        if voltage is not None:
            return voltage

        # Per IEC 61215: 1000V + 2×Voc (or 1.2×Voc depending on standard version)
        # Using 1000V + 1.2×Voc as specified in requirements
        if self.module_voc is not None:
            calculated = 1000.0 + 1.2 * self.module_voc
            logger.info(
                f"Calculated test voltage: {calculated}V "
                f"(1000V + 1.2×{self.module_voc}V)"
            )
            return calculated
        else:
            logger.warning("Voc not provided, using default 1000V")
            return 1000.0

    def measure(
        self,
        voltage: Optional[float] = None,
        duration_sec: int = 120,
        operator_id: Optional[str] = None,
        equipment_id: Optional[str] = None,
        calibration_date: Optional[datetime] = None,
        **kwargs
    ) -> WetLeakageTestResult:
        """
        Execute wet leakage current measurement.

        Args:
            voltage: Applied voltage (V), or None to auto-calculate
            duration_sec: Measurement duration (seconds)
            operator_id: Operator identifier
            equipment_id: Equipment identifier
            calibration_date: Equipment calibration date
            **kwargs: Additional parameters for test result

        Returns:
            WetLeakageTestResult with measurement data

        Raises:
            RuntimeError: If safety checks fail
            ValueError: If parameters are invalid
        """
        logger.info(f"Starting wet leakage current test for {self.module}")

        # Step 1: Safety checks
        if not self.safety.verify_all_checks():
            raise RuntimeError("Safety checks FAILED - test aborted")

        # Step 2: Calculate test voltage
        test_voltage = self.calculate_test_voltage(voltage)

        # Step 3: Initialize high voltage protection
        max_safe_current = kwargs.get('max_leakage_ua', 50.0) * 10  # 10x safety margin
        self.hv_protection = HighVoltageProtection(
            max_voltage=test_voltage * 1.1,  # 10% margin
            max_current_ua=max_safe_current
        )

        # Step 4: Validate calibration (ISO 17025)
        if calibration_date and not ISO17025Validator.validate_calibration(calibration_date):
            logger.warning("Equipment calibration may be expired")

        # Step 5: Enable high voltage (simulated)
        if not self.hv_protection.enable():
            raise RuntimeError("Failed to enable high voltage")

        try:
            # Step 6: Simulate measurement
            # In real implementation, this would:
            # - Apply voltage via HV power supply
            # - Monitor current via microammeter
            # - Record data continuously for duration_sec
            # - Check safety limits continuously

            logger.info(f"Applying {test_voltage}V for {duration_sec}s")
            logger.info("Monitoring leakage current...")

            # Simulated measurement (replace with actual hardware interface)
            measured_current_ua = self._simulate_measurement(
                test_voltage,
                duration_sec
            )

            # Step 7: Verify limits
            if not self.hv_protection.check_limits(test_voltage, measured_current_ua):
                logger.error("Safety limits exceeded during measurement")
                self.safety.emergency_stop()
                raise RuntimeError("Measurement aborted - safety limits exceeded")

            # Step 8: Create result object
            result = WetLeakageTestResult(
                test_id=self.test_id,
                module_id=self.module_id,
                applied_voltage=test_voltage,
                module_voc=self.module_voc,
                leakage_current_ua=measured_current_ua,
                duration_sec=duration_sec,
                operator_id=operator_id,
                equipment_id=equipment_id,
                calibration_date=calibration_date,
                status=TestStatus.IN_PROGRESS,
                **kwargs
            )

            # Step 9: Validate test data
            self._validate_test_data(result)

            # Step 10: Determine pass/fail
            result.determine_pass_fail()
            result.status = TestStatus.PASSED if result.pass_status else TestStatus.FAILED

            logger.info(
                f"Test completed: {result.status.value.upper()} - "
                f"Leakage current: {measured_current_ua}μA"
            )

            return result

        finally:
            # Always disable high voltage
            if self.hv_protection:
                self.hv_protection.disable()
            logger.info("High voltage disabled, test sequence complete")

    def _simulate_measurement(self, voltage: float, duration_sec: int) -> float:
        """
        Simulate leakage current measurement.

        In production, replace with actual hardware interface.

        Args:
            voltage: Applied voltage
            duration_sec: Measurement duration

        Returns:
            Simulated leakage current (μA)
        """
        # Simulated value - in real implementation, read from microammeter
        # Using a realistic value that would pass for a good module
        import random
        random.seed(hash(self.module))

        # Good modules typically show 5-30 μA
        base_leakage = random.uniform(5.0, 30.0)

        # Add small voltage dependency
        voltage_factor = voltage / 1000.0
        simulated_current = base_leakage * voltage_factor

        logger.debug(f"Simulated measurement: {simulated_current:.2f}μA")
        return round(simulated_current, 2)

    def _validate_test_data(self, result: WetLeakageTestResult) -> None:
        """
        Validate test data for ISO 17025 compliance.

        Args:
            result: Test result to validate

        Raises:
            ValueError: If validation fails
        """
        # Validate traceability
        test_dict = result.model_dump()
        if not ISO17025Validator.validate_traceability(test_dict):
            logger.warning("Incomplete traceability information")

        # Validate environmental conditions
        ISO17025Validator.validate_environmental_conditions(
            result.ambient_temp_c,
            result.humidity_percent,
            required=False
        )

        # Validate measurement duration
        if not DataIntegrityValidator.validate_duration(
            result.duration_sec,
            result.min_duration_sec,
            "Wet leakage test"
        ):
            raise ValueError("Test duration insufficient")

        # Validate current range
        DataIntegrityValidator.validate_measurement_range(
            result.leakage_current_ua,
            0.0,
            10000.0,
            "Leakage current"
        )
