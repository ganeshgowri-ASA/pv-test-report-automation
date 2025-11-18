"""Base test block classes for PV module testing.

This module provides the foundational abstract classes and enumerations
for implementing IEC 61215, IEC 61730, and other standard-compliant test blocks.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from ..models.base import BaseModel


class TestStatus(str, Enum):
    """Test execution status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ABORTED = "aborted"


class TestStandard(str, Enum):
    """International testing standards enumeration."""

    IEC_61215 = "IEC 61215"
    IEC_61730 = "IEC 61730"
    IEC_61853 = "IEC 61853"
    UL_1703 = "UL 1703"
    ISO_17025 = "ISO/IEC 17025"


class CalibrationStatus(str, Enum):
    """Equipment calibration status."""

    VALID = "valid"
    EXPIRED = "expired"
    DUE_SOON = "due_soon"
    NOT_CALIBRATED = "not_calibrated"


class BaseTestBlock(BaseModel, ABC):
    """Abstract base class for all PV test blocks.

    Provides common functionality for test execution, validation,
    reporting, and ISO 17025 traceability.

    Attributes:
        test_name: Human-readable name of the test
        test_standard: The standard this test complies with
        module_id: Identifier of the PV module being tested
        status: Current status of the test
        start_time: When the test started
        end_time: When the test completed
        duration_seconds: Total test duration
        operator_name: Name of the test operator
        equipment_ids: List of equipment used in the test
        environmental_conditions: Ambient conditions during test
        results: Dictionary of test results
        pass_criteria: Dictionary of pass/fail criteria
        error_messages: List of error messages if test failed
        warnings: List of warnings during test execution
        test_procedure_version: Version of the test procedure used
        notes: Additional notes about the test
    """

    # Test identification
    test_name: str = Field(..., description="Human-readable name of the test")
    test_standard: TestStandard = Field(..., description="Applicable testing standard")
    module_id: str = Field(..., description="Identifier of the PV module being tested")

    # Test status tracking
    status: TestStatus = Field(
        default=TestStatus.PENDING,
        description="Current status of the test"
    )
    start_time: Optional[datetime] = Field(
        default=None,
        description="When the test started"
    )
    end_time: Optional[datetime] = Field(
        default=None,
        description="When the test completed"
    )
    duration_seconds: Optional[float] = Field(
        default=None,
        description="Total test duration in seconds"
    )

    # ISO 17025 traceability
    operator_name: str = Field(..., description="Name of the test operator")
    equipment_ids: List[str] = Field(
        default_factory=list,
        description="List of equipment IDs used in the test"
    )
    test_procedure_version: str = Field(
        default="1.0",
        description="Version of the test procedure used"
    )

    # Environmental conditions
    environmental_conditions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Ambient conditions during test (temp, humidity, pressure)"
    )

    # Results and criteria
    results: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary of test results"
    )
    pass_criteria: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary of pass/fail criteria"
    )

    # Error handling
    error_messages: List[str] = Field(
        default_factory=list,
        description="List of error messages if test failed"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="List of warnings during test execution"
    )

    # Additional information
    notes: Optional[str] = Field(
        default=None,
        description="Additional notes about the test"
    )

    @field_validator("module_id")
    @classmethod
    def validate_module_id(cls, v: str) -> str:
        """Validate module ID is not empty."""
        if not v or not v.strip():
            raise ValueError("module_id cannot be empty")
        return v.strip()

    @abstractmethod
    def validate_input_data(self) -> bool:
        """Validate test input data and configuration.

        Returns:
            True if validation passes, False otherwise
        """
        pass

    @abstractmethod
    def execute(self) -> bool:
        """Execute the test block.

        Returns:
            True if test passes, False otherwise
        """
        pass

    @abstractmethod
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive test report.

        Returns:
            Dictionary containing all test data and results
        """
        pass

    def start_test(self) -> None:
        """Mark the test as started and record start time."""
        self.status = TestStatus.RUNNING
        self.start_time = datetime.utcnow()

    def complete_test(self, passed: bool) -> None:
        """Mark the test as complete and record end time.

        Args:
            passed: Whether the test passed or failed
        """
        self.end_time = datetime.utcnow()
        if self.start_time:
            self.duration_seconds = (self.end_time - self.start_time).total_seconds()

        self.status = TestStatus.PASSED if passed else TestStatus.FAILED
        self.update_timestamp()

    def abort_test(self, reason: str) -> None:
        """Abort the test and record reason.

        Args:
            reason: Reason for aborting the test
        """
        self.status = TestStatus.ABORTED
        self.end_time = datetime.utcnow()
        if self.start_time:
            self.duration_seconds = (self.end_time - self.start_time).total_seconds()
        self.error_messages.append(f"Test aborted: {reason}")
        self.update_timestamp()

    def add_warning(self, warning: str) -> None:
        """Add a warning message to the test.

        Args:
            warning: Warning message to add
        """
        self.warnings.append(f"{datetime.utcnow().isoformat()}: {warning}")

    def add_error(self, error: str) -> None:
        """Add an error message to the test.

        Args:
            error: Error message to add
        """
        self.error_messages.append(f"{datetime.utcnow().isoformat()}: {error}")
