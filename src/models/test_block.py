"""Base models for test blocks"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class TestBlockStatus(str, Enum):
    """Status of test block execution"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class ComplianceData(BaseModel):
    """Compliance and traceability data"""
    standard: str = Field(..., description="Testing standard (e.g., IEC 61215-2)")
    standard_version: Optional[str] = Field(None, description="Version of the standard")
    test_procedure_id: Optional[str] = Field(None, description="Internal procedure reference")
    accreditation: Optional[str] = Field(None, description="Accreditation body (e.g., NABL, ILAC)")
    uncertainty_budget: Optional[Dict[str, float]] = Field(None, description="Measurement uncertainty")
    calibration_refs: Optional[List[str]] = Field(default_factory=list, description="Calibration certificates")


class AuditTrailEntry(BaseModel):
    """Single entry in audit trail"""
    timestamp: datetime
    action: str
    user: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class BaseTestBlock(BaseModel):
    """Base class for all test blocks"""
    test_block_id: str = Field(..., description="Unique identifier for test block")
    test_name: str = Field(..., description="Human-readable test name")
    module_id: str = Field(..., description="PV module identifier")
    standard: str = Field(..., description="Testing standard")
    status: TestBlockStatus = Field(default=TestBlockStatus.PENDING)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Compliance and traceability
    compliance_data: ComplianceData
    audit_trail: List[AuditTrailEntry] = Field(default_factory=list)

    # Operator information
    operator: Optional[str] = None
    reviewer: Optional[str] = None
    approved_by: Optional[str] = None

    # Metadata
    notes: Optional[str] = None
    attachments: List[str] = Field(default_factory=list, description="Paths to attached files")

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def add_audit_entry(self, action: str, user: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        """Add an entry to the audit trail"""
        entry = AuditTrailEntry(
            timestamp=datetime.utcnow(),
            action=action,
            user=user,
            details=details
        )
        self.audit_trail.append(entry)

    def start_test(self, operator: Optional[str] = None) -> None:
        """Mark test as started"""
        self.status = TestBlockStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
        if operator:
            self.operator = operator
        self.add_audit_entry("test_started", user=operator)

    def complete_test(self, success: bool = True) -> None:
        """Mark test as completed or failed"""
        self.status = TestBlockStatus.COMPLETED if success else TestBlockStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.add_audit_entry("test_completed" if success else "test_failed")

    def abort_test(self, reason: Optional[str] = None) -> None:
        """Abort the test"""
        self.status = TestBlockStatus.ABORTED
        self.completed_at = datetime.utcnow()
        self.add_audit_entry("test_aborted", details={"reason": reason} if reason else None)
