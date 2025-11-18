"""
Approval Workflow Models for ISO 17025 Compliance
Multi-level approval system with digital signatures and audit trail
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class WorkflowStatus(str, Enum):
    """Workflow status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"


class ActionType(str, Enum):
    """Approval action types"""
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"
    DELEGATE = "delegate"
    ESCALATE = "escalate"
    COMMENT = "comment"


class ApprovalStage(str, Enum):
    """ISO 17025 compliant approval hierarchy"""
    TECHNICIAN = "technician"
    REVIEWER = "reviewer"
    APPROVER = "approver"
    MANAGEMENT = "management"

    @classmethod
    def get_hierarchy(cls) -> List[str]:
        """Return stages in hierarchical order"""
        return [
            cls.TECHNICIAN.value,
            cls.REVIEWER.value,
            cls.APPROVER.value,
            cls.MANAGEMENT.value
        ]

    @classmethod
    def get_next_stage(cls, current_stage: str) -> Optional[str]:
        """Get next stage in hierarchy"""
        hierarchy = cls.get_hierarchy()
        try:
            current_idx = hierarchy.index(current_stage)
            if current_idx < len(hierarchy) - 1:
                return hierarchy[current_idx + 1]
        except ValueError:
            pass
        return None


class ApprovalRoute(str, Enum):
    """Approval routing strategies"""
    SEQUENTIAL = "sequential"  # One stage at a time
    PARALLEL = "parallel"      # All stages simultaneously
    HYBRID = "hybrid"          # Custom routing logic


class DigitalSignature(BaseModel):
    """Digital signature with cryptographic hash"""
    signature_hash: str = Field(..., description="Cryptographic signature hash")
    signing_algorithm: str = Field(default="SHA256", description="Signature algorithm")
    certificate_id: Optional[str] = Field(None, description="Digital certificate ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = Field(None, description="IP address of signer")

    class Config:
        json_schema_extra = {
            "example": {
                "signature_hash": "a3d4e5f6...",
                "signing_algorithm": "SHA256",
                "timestamp": "2025-01-18T10:30:00Z"
            }
        }


class Approver(BaseModel):
    """Approver information with authority level"""
    user_id: int = Field(..., description="User identifier")
    name: str = Field(..., description="Approver name")
    email: str = Field(..., description="Approver email")
    role: ApprovalStage = Field(..., description="Approval stage/role")
    authority_level: int = Field(default=1, ge=1, le=5, description="Authority level (1-5)")
    delegation_enabled: bool = Field(default=False, description="Can delegate approval")
    delegated_from: Optional[int] = Field(None, description="Delegated from user_id")
    escalation_timeout_hours: int = Field(default=24, description="Hours before auto-escalation")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation"""
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 456,
                "name": "John Doe",
                "email": "john.doe@example.com",
                "role": "reviewer",
                "authority_level": 3
            }
        }


class ApprovalAction(BaseModel):
    """Individual approval action with audit trail"""
    action_id: int = Field(..., description="Unique action identifier")
    workflow_id: int = Field(..., description="Associated workflow ID")
    user_id: int = Field(..., description="User performing action")
    action: ActionType = Field(..., description="Type of action")
    stage: ApprovalStage = Field(..., description="Approval stage")
    comments: str = Field(default="", description="Action comments")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    digital_signature: DigitalSignature = Field(..., description="Digital signature")
    previous_state: Optional[str] = Field(None, description="Previous workflow state")
    new_state: str = Field(..., description="New workflow state")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    is_immutable: bool = Field(default=True, description="Action cannot be modified")

    class Config:
        json_schema_extra = {
            "example": {
                "action_id": 1,
                "workflow_id": 123,
                "user_id": 456,
                "action": "approve",
                "stage": "reviewer",
                "comments": "Technical review completed",
                "timestamp": "2025-01-18T10:30:00Z"
            }
        }


class SectionLock(BaseModel):
    """Section locking after approval"""
    section_id: str = Field(..., description="Section identifier")
    locked_at: datetime = Field(default_factory=datetime.utcnow)
    locked_by: int = Field(..., description="User who locked section")
    stage: ApprovalStage = Field(..., description="Stage at which locked")
    is_locked: bool = Field(default=True)
    unlock_requires_role: Optional[ApprovalStage] = Field(None, description="Role required to unlock")


class EscalationRule(BaseModel):
    """Auto-escalation configuration"""
    from_stage: ApprovalStage = Field(..., description="Stage to escalate from")
    to_stage: Optional[ApprovalStage] = Field(None, description="Stage to escalate to")
    timeout_hours: int = Field(default=24, description="Hours before escalation")
    escalation_user_id: Optional[int] = Field(None, description="User to escalate to")
    notification_emails: List[str] = Field(default_factory=list, description="Email notifications")
    auto_approve: bool = Field(default=False, description="Auto-approve on escalation")


class ApprovalWorkflow(BaseModel):
    """Main approval workflow for ISO 17025 compliance"""
    workflow_id: int = Field(..., description="Unique workflow identifier")
    report_id: int = Field(..., description="Associated report ID")
    current_stage: ApprovalStage = Field(..., description="Current approval stage")
    status: WorkflowStatus = Field(default=WorkflowStatus.PENDING, description="Workflow status")
    route_type: ApprovalRoute = Field(default=ApprovalRoute.SEQUENTIAL, description="Approval routing")

    # Approvers and history
    approvers: List[Approver] = Field(default_factory=list, description="List of approvers")
    approval_history: List[ApprovalAction] = Field(default_factory=list, description="Immutable audit trail")

    # Section locking
    locked_sections: List[SectionLock] = Field(default_factory=list, description="Locked report sections")

    # Escalation
    escalation_rules: List[EscalationRule] = Field(default_factory=list, description="Escalation configuration")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None, description="Workflow completion time")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional workflow data")
    iso_17025_compliant: bool = Field(default=True, description="ISO 17025 compliance flag")

    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": 1,
                "report_id": 123,
                "current_stage": "technician",
                "status": "pending",
                "route_type": "sequential",
                "iso_17025_compliant": True
            }
        }

    def get_current_approvers(self) -> List[Approver]:
        """Get approvers for current stage"""
        return [a for a in self.approvers if a.role == self.current_stage]

    def is_stage_approved(self, stage: ApprovalStage) -> bool:
        """Check if a stage is approved"""
        stage_actions = [
            action for action in self.approval_history
            if action.stage == stage and action.action == ActionType.APPROVE
        ]
        return len(stage_actions) > 0

    def get_next_stage(self) -> Optional[ApprovalStage]:
        """Get next stage in workflow"""
        next_stage_str = ApprovalStage.get_next_stage(self.current_stage.value)
        if next_stage_str:
            return ApprovalStage(next_stage_str)
        return None

    def is_section_locked(self, section_id: str) -> bool:
        """Check if a section is locked"""
        for lock in self.locked_sections:
            if lock.section_id == section_id and lock.is_locked:
                return True
        return False
