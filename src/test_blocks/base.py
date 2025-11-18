"""
Base model for PV test blocks with ISO 17025 compliance.

This module provides the foundational classes for all photovoltaic
test blocks in accordance with ISO/IEC 17025 standards for testing
and calibration laboratories.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class TestStatus(Enum):
    """Test execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    ABORTED = "aborted"


class MeasurementUncertainty(BaseModel):
    """ISO 17025 measurement uncertainty tracking."""
    value: float = Field(..., description="Measured value")
    uncertainty: float = Field(..., description="Measurement uncertainty")
    confidence_level: float = Field(default=0.95, description="Confidence level (typically 95%)")
    unit: str = Field(..., description="Unit of measurement")

    @validator('confidence_level')
    def validate_confidence_level(cls, v):
        if not 0 < v < 1:
            raise ValueError('Confidence level must be between 0 and 1')
        return v


class EnvironmentalConditions(BaseModel):
    """Environmental conditions during testing (ISO 17025 requirement)."""
    temperature_celsius: Optional[float] = Field(None, description="Ambient temperature")
    humidity_percent: Optional[float] = Field(None, description="Relative humidity")
    pressure_kpa: Optional[float] = Field(None, description="Atmospheric pressure")
    timestamp: datetime = Field(default_factory=datetime.now)


class Equipment(BaseModel):
    """Equipment information for traceability (ISO 17025)."""
    equipment_id: str = Field(..., description="Unique equipment identifier")
    name: str = Field(..., description="Equipment name")
    manufacturer: str = Field(..., description="Manufacturer")
    model: str = Field(..., description="Model number")
    serial_number: str = Field(..., description="Serial number")
    calibration_date: datetime = Field(..., description="Last calibration date")
    calibration_due_date: datetime = Field(..., description="Next calibration due date")
    certificate_number: Optional[str] = Field(None, description="Calibration certificate number")

    @validator('calibration_due_date')
    def validate_calibration(cls, v, values):
        if 'calibration_date' in values and v <= values['calibration_date']:
            raise ValueError('Calibration due date must be after calibration date')
        if v < datetime.now():
            raise ValueError('Equipment calibration is overdue')
        return v


class TestResult(BaseModel):
    """Base test result model."""
    test_id: str = Field(..., description="Unique test identifier")
    test_name: str = Field(..., description="Test name")
    standard: str = Field(..., description="Test standard (e.g., IEC 61730)")
    status: TestStatus = Field(default=TestStatus.PENDING)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    operator: str = Field(..., description="Test operator name")
    environmental_conditions: Optional[EnvironmentalConditions] = None
    equipment_used: List[Equipment] = Field(default_factory=list)
    notes: Optional[str] = None

    class Config:
        use_enum_values = True


class BaseTestBlock(ABC, BaseModel):
    """
    Abstract base class for all PV test blocks.

    Provides common functionality for:
    - Test execution workflow
    - Data validation
    - ISO 17025 compliance
    - Safety checks
    - Result reporting
    """

    test_id: str = Field(..., description="Unique test identifier")
    module_id: str = Field(..., description="Module under test identifier")
    operator: str = Field(..., description="Test operator name")
    standard: str = Field(..., description="Applicable test standard")
    environmental_conditions: Optional[EnvironmentalConditions] = None

    class Config:
        arbitrary_types_allowed = True
        use_enum_values = True

    @abstractmethod
    def validate_test_conditions(self) -> bool:
        """
        Validate that test conditions meet requirements.

        Returns:
            bool: True if conditions are valid, False otherwise
        """
        pass

    @abstractmethod
    def perform_measurement(self) -> Dict[str, Any]:
        """
        Perform the actual measurement.

        Returns:
            Dict containing measurement results
        """
        pass

    @abstractmethod
    def evaluate_pass_fail(self, measurement: Dict[str, Any]) -> bool:
        """
        Evaluate pass/fail criteria.

        Args:
            measurement: Dictionary containing measurement results

        Returns:
            bool: True if test passes, False otherwise
        """
        pass

    @abstractmethod
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate test report.

        Returns:
            Dict containing report data
        """
        pass

    def pre_test_safety_check(self) -> bool:
        """
        Perform pre-test safety checks.

        Override in subclasses for specific safety requirements.

        Returns:
            bool: True if safe to proceed, False otherwise
        """
        return True

    def post_test_safety_check(self) -> bool:
        """
        Perform post-test safety checks.

        Override in subclasses for specific safety requirements.

        Returns:
            bool: True if safe, False otherwise
        """
        return True


class CalibrationRecord(BaseModel):
    """Calibration record for ISO 17025 traceability."""
    calibration_date: datetime
    calibration_authority: str = Field(..., description="Organization performing calibration")
    certificate_number: str
    reference_standards: List[str] = Field(default_factory=list)
    measurement_points: List[Dict[str, float]] = Field(default_factory=list)
    validity_period_days: int = Field(default=365)

    @property
    def is_valid(self) -> bool:
        """Check if calibration is still valid."""
        expiry_date = self.calibration_date.timestamp() + (self.validity_period_days * 24 * 3600)
        return datetime.now().timestamp() < expiry_date
