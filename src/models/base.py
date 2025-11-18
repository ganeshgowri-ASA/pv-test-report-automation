"""
Base models for PV test report automation system.

Provides foundational data structures compliant with:
- IEC 61215 (PV module design qualification)
- ISO 17025 (Testing and calibration laboratories)
- NABL/ILAC accreditation requirements
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator


class TestStatus(str, Enum):
    """Test execution status."""
    PASSED = "passed"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    INCOMPLETE = "incomplete"
    ABORTED = "aborted"


class Standard(str, Enum):
    """Supported test standards."""
    IEC_61215 = "IEC 61215"
    IEC_61730 = "IEC 61730"
    IEC_61853 = "IEC 61853"
    IEC_62716 = "IEC 62716"
    IEC_61701 = "IEC 61701"
    IEC_62804 = "IEC 62804"
    IEC_60904 = "IEC 60904"
    IEC_62759 = "IEC 62759"
    ISO_17025 = "ISO 17025"
    ISO_9001 = "ISO 9001"


class BaseTestResult(BaseModel):
    """Base model for all test results with ISO 17025 traceability."""

    test_id: str = Field(..., description="Unique test identifier")
    test_name: str = Field(..., description="Test name/designation")
    standard: str = Field(..., description="Test standard (e.g., IEC 61215)")
    status: TestStatus = Field(..., description="Test pass/fail status")

    # ISO 17025 traceability fields
    timestamp: datetime = Field(default_factory=datetime.now, description="Test execution timestamp")
    operator: str = Field(..., description="Test operator name/ID")
    reviewer: Optional[str] = Field(None, description="Test reviewer name/ID")
    lab_id: str = Field(default="LAB-001", description="Laboratory identification")

    # Environmental conditions (ISO 17025 requirement)
    ambient_temperature_c: Optional[float] = Field(None, description="Ambient temperature during test")
    relative_humidity_percent: Optional[float] = Field(None, description="Relative humidity during test")

    # Test metadata
    module_id: str = Field(..., description="Module under test identifier")
    notes: Optional[str] = Field(None, description="Additional test notes")
    attachments: List[str] = Field(default_factory=list, description="File paths to test attachments")

    class Config:
        json_schema_extra = {
            "example": {
                "test_id": "IEC-61215-HS-001",
                "test_name": "Hot Spot Endurance Test",
                "standard": "IEC 61215",
                "status": "passed",
                "operator": "OP-12345",
                "module_id": "PV-001",
                "timestamp": "2025-01-15T10:30:00"
            }
        }


class EquipmentCalibration(BaseModel):
    """Equipment calibration record for ISO 17025 compliance."""

    equipment_id: str = Field(..., description="Equipment identifier")
    equipment_name: str = Field(..., description="Equipment name")
    calibration_date: datetime = Field(..., description="Last calibration date")
    next_calibration_date: datetime = Field(..., description="Next calibration due date")
    calibration_certificate: str = Field(..., description="Calibration certificate number")
    uncertainty: Optional[float] = Field(None, description="Measurement uncertainty")
    accredited_lab: str = Field(..., description="Calibration lab accreditation")

    @validator('next_calibration_date')
    def validate_calibration_current(cls, v, values):
        """Ensure equipment calibration is current."""
        if v < datetime.now():
            raise ValueError(f"Equipment calibration expired on {v}")
        return v


class TestParameters(BaseModel):
    """Base test parameters model."""

    irradiance_w_m2: float = Field(1000.0, description="Solar irradiance (W/m²)")
    temperature_c: float = Field(25.0, description="Test temperature (°C)")
    duration_hours: Optional[float] = Field(None, description="Test duration (hours)")

    class Config:
        json_schema_extra = {
            "example": {
                "irradiance_w_m2": 1000.0,
                "temperature_c": 25.0,
                "duration_hours": 1.0
            }
        }
