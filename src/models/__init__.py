"""Data models for PV Test Report Automation.

ISO 17025 Compliant Data Models
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class TestStandard(str, Enum):
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


class ExportFormat(str, Enum):
    """Supported export formats."""
    WORD = "word"
    EXCEL = "excel"
    HTML = "html"
    PDF = "pdf"
    JSON = "json"
    XML = "xml"


class TestStatus(str, Enum):
    """Test execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEW_REQUIRED = "review_required"
    APPROVED = "approved"


class UserRole(str, Enum):
    """User roles for access control."""
    ADMIN = "admin"
    TEST_ENGINEER = "test_engineer"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


class TestReport(BaseModel):
    """Test report data model."""

    id: str = Field(..., description="Unique report ID")
    standard: TestStandard
    test_date: datetime
    status: TestStatus = TestStatus.PENDING

    # Module information
    module_manufacturer: str
    module_model: str
    module_serial_number: str

    # Test parameters
    test_parameters: dict = Field(default_factory=dict)
    test_results: dict = Field(default_factory=dict)

    # Compliance
    is_compliant: Optional[bool] = None
    deviations: List[str] = Field(default_factory=list)

    # Workflow
    created_by: str
    reviewed_by: Optional[str] = None
    approved_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Digital signature (ISO 17025 requirement)
    digital_signature: Optional[str] = None
    signature_timestamp: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "RPT-2024-001",
                "standard": "IEC 61215",
                "test_date": "2024-01-15T10:30:00Z",
                "status": "completed",
                "module_manufacturer": "SolarTech Inc.",
                "module_model": "ST-400W-PERC",
                "module_serial_number": "ST400-2024-001",
                "created_by": "engineer@example.com"
            }
        }


class ExportJob(BaseModel):
    """Export job tracking model."""

    job_id: str
    report_id: str
    format: ExportFormat
    status: str = "pending"
    progress: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    file_path: Optional[str] = None
    error_message: Optional[str] = None


class AuditLog(BaseModel):
    """Audit log entry for ISO 17025 compliance."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    details: dict = Field(default_factory=dict)
    ip_address: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2024-01-15T10:30:00Z",
                "user_id": "engineer@example.com",
                "action": "REPORT_APPROVED",
                "resource_type": "TestReport",
                "resource_id": "RPT-2024-001",
                "details": {"reviewer": "reviewer@example.com"},
                "ip_address": "192.168.1.100"
            }
        }


__all__ = [
    "TestStandard",
    "ExportFormat",
    "TestStatus",
    "UserRole",
    "TestReport",
    "ExportJob",
    "AuditLog",
]
