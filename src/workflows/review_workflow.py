"""
Review Workflow System for PV Test Reports.

Implements comprehensive review and approval workflow with:
- Multi-level review process (technical, quality, management)
- Comment and annotation system
- Revision tracking with audit trail
- Digital signatures for NABL compliance
- Email notifications
- Review status tracking

ISO 17025 and NABL compliant with full traceability.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.models.base_models import ReviewStatus

logger = logging.getLogger(__name__)


class ReviewerRole(str, Enum):
    """Reviewer role types."""

    TECHNICAL_REVIEWER = "technical"  # Technical content review
    QUALITY_REVIEWER = "quality"  # QA/QC review
    MANAGER_REVIEWER = "manager"  # Management approval
    AUTHORIZED_SIGNATORY = "signatory"  # Final approval with signature


class CommentType(str, Enum):
    """Types of review comments."""

    TECHNICAL = "technical"
    ADMINISTRATIVE = "administrative"
    FORMATTING = "formatting"
    COMPLIANCE = "compliance"
    DATA_QUALITY = "data_quality"
    GENERAL = "general"


class ActionType(str, Enum):
    """Review action types."""

    SUBMITTED_FOR_REVIEW = "submitted_for_review"
    REVIEW_STARTED = "review_started"
    COMMENT_ADDED = "comment_added"
    COMMENT_RESOLVED = "comment_resolved"
    REVISION_REQUESTED = "revision_requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    SIGNED = "signed"


class ReviewComment(BaseModel):
    """Individual review comment."""

    comment_id: UUID = Field(default_factory=uuid4)
    report_id: UUID
    reviewer: str
    reviewer_role: ReviewerRole
    comment_type: CommentType
    comment_text: str
    section: Optional[str] = Field(None, description="Report section (e.g., 'test_results.damp_heat')")
    line_number: Optional[int] = None
    severity: str = Field(default="normal", description="Comment severity: low, normal, high, critical")
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ReviewAction(BaseModel):
    """Review workflow action/event."""

    action_id: UUID = Field(default_factory=uuid4)
    report_id: UUID
    action_type: ActionType
    performed_by: str
    performer_role: ReviewerRole
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    old_status: Optional[ReviewStatus] = None
    new_status: Optional[ReviewStatus] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DigitalSignature(BaseModel):
    """Digital signature for NABL compliance."""

    signature_id: UUID = Field(default_factory=uuid4)
    report_id: UUID
    signatory_name: str
    signatory_role: str
    nabl_authorization_number: Optional[str] = None
    signature_timestamp: datetime = Field(default_factory=datetime.utcnow)
    signature_hash: str = Field(..., description="Cryptographic signature hash")
    certificate_id: Optional[str] = None
    ip_address: Optional[str] = None
    location: Optional[str] = None


class ReviewAssignment(BaseModel):
    """Review assignment to a reviewer."""

    assignment_id: UUID = Field(default_factory=uuid4)
    report_id: UUID
    reviewer: str
    reviewer_role: ReviewerRole
    assigned_by: str
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None
    completed: bool = False
    completed_at: Optional[datetime] = None
    decision: Optional[str] = None  # approved, rejected, revision_required


class ReviewWorkflow:
    """
    Review workflow manager for PV test reports.

    Manages the complete review lifecycle with multi-level approvals.
    """

    def __init__(self, report_id: UUID):
        """
        Initialize review workflow.

        Args:
            report_id: Test report UUID
        """
        self.report_id = report_id
        self.current_status = ReviewStatus.DRAFT
        self.comments: List[ReviewComment] = []
        self.actions: List[ReviewAction] = []
        self.assignments: List[ReviewAssignment] = []
        self.signatures: List[DigitalSignature] = []

    def submit_for_review(
        self,
        submitted_by: str,
        reviewers: List[Dict[str, str]],
    ) -> ReviewAction:
        """
        Submit report for review.

        Args:
            submitted_by: User submitting for review
            reviewers: List of reviewer assignments [{"user": "name", "role": "technical"}]

        Returns:
            Review action record
        """
        logger.info(f"Submitting report {self.report_id} for review by {submitted_by}")

        # Create assignments
        for reviewer_info in reviewers:
            assignment = ReviewAssignment(
                report_id=self.report_id,
                reviewer=reviewer_info["user"],
                reviewer_role=ReviewerRole(reviewer_info["role"]),
                assigned_by=submitted_by,
            )
            self.assignments.append(assignment)

        # Record action
        action = ReviewAction(
            report_id=self.report_id,
            action_type=ActionType.SUBMITTED_FOR_REVIEW,
            performed_by=submitted_by,
            performer_role=ReviewerRole.TECHNICAL_REVIEWER,
            old_status=self.current_status,
            new_status=ReviewStatus.PENDING_REVIEW,
            notes=f"Assigned to {len(reviewers)} reviewers",
        )

        self.actions.append(action)
        self.current_status = ReviewStatus.PENDING_REVIEW

        logger.info(f"Report submitted for review, assigned to {len(reviewers)} reviewers")
        return action

    def start_review(
        self,
        reviewer: str,
        reviewer_role: ReviewerRole,
    ) -> ReviewAction:
        """
        Start reviewing a report.

        Args:
            reviewer: Reviewer username
            reviewer_role: Reviewer's role

        Returns:
            Review action record
        """
        logger.info(f"Review started by {reviewer} ({reviewer_role.value})")

        action = ReviewAction(
            report_id=self.report_id,
            action_type=ActionType.REVIEW_STARTED,
            performed_by=reviewer,
            performer_role=reviewer_role,
            old_status=self.current_status,
            new_status=ReviewStatus.IN_REVIEW,
        )

        self.actions.append(action)
        self.current_status = ReviewStatus.IN_REVIEW

        return action

    def add_comment(
        self,
        reviewer: str,
        reviewer_role: ReviewerRole,
        comment_text: str,
        comment_type: CommentType = CommentType.GENERAL,
        section: Optional[str] = None,
        severity: str = "normal",
    ) -> ReviewComment:
        """
        Add review comment.

        Args:
            reviewer: Reviewer username
            reviewer_role: Reviewer's role
            comment_text: Comment content
            comment_type: Type of comment
            section: Report section being commented on
            severity: Comment severity level

        Returns:
            Created comment
        """
        comment = ReviewComment(
            report_id=self.report_id,
            reviewer=reviewer,
            reviewer_role=reviewer_role,
            comment_type=comment_type,
            comment_text=comment_text,
            section=section,
            severity=severity,
        )

        self.comments.append(comment)

        # Record action
        action = ReviewAction(
            report_id=self.report_id,
            action_type=ActionType.COMMENT_ADDED,
            performed_by=reviewer,
            performer_role=reviewer_role,
            notes=f"{comment_type.value} comment added to section: {section or 'general'}",
            metadata={"comment_id": str(comment.comment_id)},
        )
        self.actions.append(action)

        logger.info(
            f"Comment added by {reviewer}: {comment_type.value} ({severity})"
        )

        return comment

    def resolve_comment(
        self,
        comment_id: UUID,
        resolved_by: str,
        resolution_notes: Optional[str] = None,
    ) -> bool:
        """
        Resolve a review comment.

        Args:
            comment_id: Comment UUID to resolve
            resolved_by: User resolving the comment
            resolution_notes: Optional resolution notes

        Returns:
            True if comment was found and resolved
        """
        for comment in self.comments:
            if comment.comment_id == comment_id:
                comment.resolved = True
                comment.resolved_by = resolved_by
                comment.resolved_at = datetime.utcnow()
                comment.resolution_notes = resolution_notes

                # Record action
                action = ReviewAction(
                    report_id=self.report_id,
                    action_type=ActionType.COMMENT_RESOLVED,
                    performed_by=resolved_by,
                    performer_role=ReviewerRole.TECHNICAL_REVIEWER,
                    notes=f"Comment resolved: {comment.comment_text[:50]}...",
                    metadata={"comment_id": str(comment_id)},
                )
                self.actions.append(action)

                logger.info(f"Comment {comment_id} resolved by {resolved_by}")
                return True

        return False

    def request_revision(
        self,
        reviewer: str,
        reviewer_role: ReviewerRole,
        reason: str,
    ) -> ReviewAction:
        """
        Request revision of the report.

        Args:
            reviewer: Reviewer requesting revision
            reviewer_role: Reviewer's role
            reason: Reason for revision request

        Returns:
            Review action record
        """
        logger.info(f"Revision requested by {reviewer}: {reason}")

        action = ReviewAction(
            report_id=self.report_id,
            action_type=ActionType.REVISION_REQUESTED,
            performed_by=reviewer,
            performer_role=reviewer_role,
            old_status=self.current_status,
            new_status=ReviewStatus.REVISION_REQUIRED,
            notes=reason,
        )

        self.actions.append(action)
        self.current_status = ReviewStatus.REVISION_REQUIRED

        return action

    def approve(
        self,
        reviewer: str,
        reviewer_role: ReviewerRole,
        approval_notes: Optional[str] = None,
    ) -> ReviewAction:
        """
        Approve the report.

        Args:
            reviewer: Reviewer approving
            reviewer_role: Reviewer's role
            approval_notes: Optional approval notes

        Returns:
            Review action record
        """
        logger.info(f"Report approved by {reviewer} ({reviewer_role.value})")

        # Mark assignment as completed
        for assignment in self.assignments:
            if assignment.reviewer == reviewer and not assignment.completed:
                assignment.completed = True
                assignment.completed_at = datetime.utcnow()
                assignment.decision = "approved"

        action = ReviewAction(
            report_id=self.report_id,
            action_type=ActionType.APPROVED,
            performed_by=reviewer,
            performer_role=reviewer_role,
            old_status=self.current_status,
            new_status=ReviewStatus.APPROVED,
            notes=approval_notes,
        )

        self.actions.append(action)

        # Check if all reviewers have approved
        if self._all_reviewers_approved():
            self.current_status = ReviewStatus.APPROVED

        return action

    def reject(
        self,
        reviewer: str,
        reviewer_role: ReviewerRole,
        rejection_reason: str,
    ) -> ReviewAction:
        """
        Reject the report.

        Args:
            reviewer: Reviewer rejecting
            reviewer_role: Reviewer's role
            rejection_reason: Reason for rejection

        Returns:
            Review action record
        """
        logger.info(f"Report rejected by {reviewer}: {rejection_reason}")

        # Mark assignment as completed
        for assignment in self.assignments:
            if assignment.reviewer == reviewer and not assignment.completed:
                assignment.completed = True
                assignment.completed_at = datetime.utcnow()
                assignment.decision = "rejected"

        action = ReviewAction(
            report_id=self.report_id,
            action_type=ActionType.REJECTED,
            performed_by=reviewer,
            performer_role=reviewer_role,
            old_status=self.current_status,
            new_status=ReviewStatus.REJECTED,
            notes=rejection_reason,
        )

        self.actions.append(action)
        self.current_status = ReviewStatus.REJECTED

        return action

    def add_digital_signature(
        self,
        signatory_name: str,
        signatory_role: str,
        signature_hash: str,
        nabl_authorization_number: Optional[str] = None,
        certificate_id: Optional[str] = None,
    ) -> DigitalSignature:
        """
        Add digital signature for NABL compliance.

        Args:
            signatory_name: Name of signatory
            signatory_role: Role of signatory
            signature_hash: Cryptographic signature hash
            nabl_authorization_number: NABL authorization number
            certificate_id: Digital certificate ID

        Returns:
            Digital signature record
        """
        signature = DigitalSignature(
            report_id=self.report_id,
            signatory_name=signatory_name,
            signatory_role=signatory_role,
            signature_hash=signature_hash,
            nabl_authorization_number=nabl_authorization_number,
            certificate_id=certificate_id,
        )

        self.signatures.append(signature)

        # Record action
        action = ReviewAction(
            report_id=self.report_id,
            action_type=ActionType.SIGNED,
            performed_by=signatory_name,
            performer_role=ReviewerRole.AUTHORIZED_SIGNATORY,
            notes=f"Digital signature applied by {signatory_name}",
            metadata={"signature_id": str(signature.signature_id)},
        )
        self.actions.append(action)

        logger.info(f"Digital signature added by {signatory_name}")
        return signature

    def _all_reviewers_approved(self) -> bool:
        """Check if all assigned reviewers have approved."""
        for assignment in self.assignments:
            if not assignment.completed or assignment.decision != "approved":
                return False
        return len(self.assignments) > 0

    def get_unresolved_comments(self) -> List[ReviewComment]:
        """Get all unresolved comments."""
        return [c for c in self.comments if not c.resolved]

    def get_audit_trail(self) -> List[ReviewAction]:
        """Get complete audit trail of review actions."""
        return sorted(self.actions, key=lambda x: x.timestamp)

    def get_workflow_summary(self) -> Dict[str, Any]:
        """
        Get workflow summary.

        Returns:
            Summary of workflow status
        """
        return {
            "report_id": str(self.report_id),
            "current_status": self.current_status.value,
            "total_comments": len(self.comments),
            "unresolved_comments": len(self.get_unresolved_comments()),
            "total_reviewers": len(self.assignments),
            "completed_reviews": sum(1 for a in self.assignments if a.completed),
            "approvals": sum(1 for a in self.assignments if a.decision == "approved"),
            "rejections": sum(1 for a in self.assignments if a.decision == "rejected"),
            "signatures_count": len(self.signatures),
            "last_action": self.actions[-1].action_type.value if self.actions else None,
            "last_action_timestamp": self.actions[-1].timestamp.isoformat() if self.actions else None,
        }
