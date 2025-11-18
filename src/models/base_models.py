"""
Base Pydantic models for PV Test Report Automation System.

ISO 17025 and NABL compliant data models with full traceability.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class TestStatus(str, Enum):
    """Test execution status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReviewStatus(str, Enum):
    """Review workflow status enumeration."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUIRED = "revision_required"


class Severity(str, Enum):
    """Test severity levels."""

    LEVEL_1 = "1"
    LEVEL_2 = "2"
    LEVEL_3 = "3"
    LEVEL_4 = "4"
    LEVEL_5 = "5"
    LEVEL_6 = "6"


class BaseMetadata(BaseModel):
    """Base metadata for all entities with ISO 17025 compliance."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    is_deleted: bool = False

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class TestSample(BaseModel):
    """PV module test sample information."""

    sample_id: str = Field(..., description="Unique sample identifier")
    module_type: str = Field(..., description="PV module type/model")
    manufacturer: str = Field(..., description="Module manufacturer")
    serial_number: str = Field(..., description="Module serial number")
    rated_power: float = Field(..., description="Rated power (W)", gt=0)
    voltage_oc: float = Field(..., description="Open circuit voltage (V)", gt=0)
    current_sc: float = Field(..., description="Short circuit current (A)", gt=0)
    voltage_mpp: float = Field(..., description="Maximum power point voltage (V)", gt=0)
    current_mpp: float = Field(..., description="Maximum power point current (A)", gt=0)
    dimensions: Dict[str, float] = Field(
        default_factory=dict, description="Module dimensions (mm)"
    )
    weight: Optional[float] = Field(None, description="Module weight (kg)", gt=0)
    cell_technology: Optional[str] = Field(None, description="Cell technology type")
    received_date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


class TestConditions(BaseModel):
    """Test environmental conditions per ISO 17025."""

    temperature: float = Field(..., description="Temperature (°C)")
    humidity: float = Field(..., description="Relative humidity (%)", ge=0, le=100)
    pressure: Optional[float] = Field(None, description="Atmospheric pressure (Pa)")
    irradiance: Optional[float] = Field(None, description="Solar irradiance (W/m²)")
    measurement_time: datetime = Field(default_factory=datetime.utcnow)
    calibration_date: Optional[datetime] = None
    equipment_id: Optional[str] = None


class CalibrationRecord(BaseModel):
    """Equipment calibration record for NABL compliance."""

    equipment_id: str = Field(..., description="Equipment identifier")
    equipment_name: str
    calibration_date: datetime
    due_date: datetime
    calibration_certificate: str = Field(..., description="Certificate number")
    calibrated_by: str
    calibration_lab: str
    traceability: str = Field(..., description="Traceability chain")
    uncertainty: Dict[str, float] = Field(
        default_factory=dict, description="Measurement uncertainty"
    )
    status: str = "valid"

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v: datetime, info: Any) -> datetime:
        """Validate calibration due date is after calibration date."""
        if "calibration_date" in info.data and v <= info.data["calibration_date"]:
            raise ValueError("Due date must be after calibration date")
        return v


class TestReport(BaseMetadata):
    """Complete test report metadata."""

    report_number: str = Field(..., description="Unique report number")
    test_type: str = Field(..., description="Test protocol type")
    sample: TestSample
    test_conditions: List[TestConditions] = Field(default_factory=list)
    test_results: Dict[str, Any] = Field(default_factory=dict)
    status: TestStatus = TestStatus.PENDING
    review_status: ReviewStatus = ReviewStatus.DRAFT
    test_start_date: Optional[datetime] = None
    test_end_date: Optional[datetime] = None
    test_engineer: Optional[str] = None
    reviewer: Optional[str] = None
    approver: Optional[str] = None
    compliance_standards: List[str] = Field(default_factory=list)
    calibration_records: List[CalibrationRecord] = Field(default_factory=list)
    attachments: List[str] = Field(default_factory=list)
    comments: List[Dict[str, Any]] = Field(default_factory=list)


class ExportRequest(BaseModel):
    """Export request configuration."""

    report_id: UUID
    format: str = Field(..., description="Export format (pdf, docx, xlsx, html, json, xml)")
    template: Optional[str] = None
    include_raw_data: bool = False
    include_images: bool = True
    watermark: Optional[str] = None
    compression: bool = True
    custom_options: Dict[str, Any] = Field(default_factory=dict)


class LLMRequest(BaseModel):
    """LLM processing request."""

    provider: str = Field(..., description="LLM provider (claude, gpt, gemini)")
    task: str = Field(..., description="Task type (compliance_check, summarize, analyze)")
    input_data: Dict[str, Any]
    model: Optional[str] = None
    temperature: float = Field(default=0.3, ge=0, le=2)
    max_tokens: int = Field(default=4096, gt=0, le=100000)
    context: Optional[str] = None
