"""
Base models for PV test automation with ISO 17025 compliance.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel as PydanticBaseModel, Field, field_validator
from enum import Enum


class TestStatus(str, Enum):
    """Test execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    ABORTED = "aborted"


class BaseTestModel(PydanticBaseModel):
    """
    Base model for all PV tests with ISO 17025 compliance.

    Includes traceability, metadata, and quality management fields.
    """

    test_id: int = Field(..., description="Unique test identifier")
    module_id: int = Field(..., description="PV module identifier")

    # ISO 17025 Traceability
    test_date: datetime = Field(
        default_factory=datetime.now,
        description="Test execution timestamp"
    )
    operator_id: Optional[str] = Field(
        None,
        description="Operator/technician identifier"
    )
    equipment_id: Optional[str] = Field(
        None,
        description="Test equipment identifier"
    )
    calibration_date: Optional[datetime] = Field(
        None,
        description="Equipment calibration date"
    )

    # Environmental conditions
    ambient_temp_c: Optional[float] = Field(
        None,
        description="Ambient temperature during test (°C)"
    )
    humidity_percent: Optional[float] = Field(
        None,
        description="Relative humidity during test (%)"
    )

    # Test status and results
    status: TestStatus = Field(
        default=TestStatus.PENDING,
        description="Test execution status"
    )
    pass_status: bool = Field(
        False,
        description="Overall pass/fail status"
    )

    # Notes and metadata
    notes: Optional[str] = Field(
        None,
        description="Additional test notes or observations"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "test_id": 1,
                "module_id": 101,
                "operator_id": "TECH-001",
                "equipment_id": "EQUIP-HV-001"
            }
        }

    @field_validator('ambient_temp_c')
    @classmethod
    def validate_temperature(cls, v):
        """Validate ambient temperature is within reasonable range."""
        if v is not None and not (-40 <= v <= 85):
            raise ValueError("Ambient temperature must be between -40°C and 85°C")
        return v

    @field_validator('humidity_percent')
    @classmethod
    def validate_humidity(cls, v):
        """Validate humidity is within valid range."""
        if v is not None and not (0 <= v <= 100):
            raise ValueError("Humidity must be between 0% and 100%")
        return v
