"""
Approval Workflow Engine
Core workflow management with multi-level approvals
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from models.approval_models import (
    ApprovalWorkflow,
    ApprovalAction,
    Approver,
    ApprovalStage,
    WorkflowStatus,
    ActionType,
    ApprovalRoute,
    DigitalSignature,
    SectionLock,
    EscalationRule
)
from utils.signature_utils import SignatureGenerator
from utils.audit_utils import AuditLogger


class ApprovalWorkflowEngine:
    """
    Multi-level approval workflow engine for ISO 17025 compliance

    Features:
    - Sequential/parallel approval routes
    - Digital signatures with timestamps
    - Immutable audit trail
    - Auto-escalation on timeout
    - Section locking post-approval
    - Delegated authority
    """

    def __init__(
        self,
        signature_generator: Optional[SignatureGenerator] = None,
        audit_logger: Optional[AuditLogger] = None
    ):
        """
        Initialize workflow engine

        Args:
            signature_generator: Digital signature generator
            audit_logger: Audit trail logger
        """
        self.signature_generator = signature_generator or SignatureGenerator()
        self.audit_logger = audit_logger or AuditLogger()
        self._workflows: Dict[int, ApprovalWorkflow] = {}
        self._action_counter = 0

    def create_workflow(
        self,
        workflow_id: int,
        report_id: int,
        approvers: List[Approver],
        route_type: ApprovalRoute = ApprovalRoute.SEQUENTIAL,
        escalation_rules: Optional[List[EscalationRule]] = None
    ) -> ApprovalWorkflow:
        """
        Create new approval workflow

        Args:
            workflow_id: Unique workflow identifier
            report_id: Associated report ID
            approvers: List of approvers in hierarchy
            route_type: Approval routing strategy
            escalation_rules: Auto-escalation configuration

        Returns:
            Created workflow
        """
        # Sort approvers by stage hierarchy
        stage_order = {
            ApprovalStage.TECHNICIAN: 0,
            ApprovalStage.REVIEWER: 1,
            ApprovalStage.APPROVER: 2,
            ApprovalStage.MANAGEMENT: 3
        }
        sorted_approvers = sorted(approvers, key=lambda a: stage_order[a.role])

        # Determine starting stage
        initial_stage = sorted_approvers[0].role if sorted_approvers else ApprovalStage.TECHNICIAN

        workflow = ApprovalWorkflow(
            workflow_id=workflow_id,
            report_id=report_id,
            current_stage=initial_stage,
            status=WorkflowStatus.PENDING,
            route_type=route_type,
            approvers=sorted_approvers,
            escalation_rules=escalation_rules or [],
            created_at=datetime.utcnow()
        )

        self._workflows[workflow_id] = workflow
        return workflow

    def request_approval(
        self,
        workflow_id: int,
        approver_id: int,
        requested_by: int,
        comments: str = ""
    ) -> ApprovalAction:
        """
        Request approval from specific approver

        Args:
            workflow_id: Workflow identifier
            approver_id: Approver user ID
            requested_by: User requesting approval
            comments: Request comments

        Returns:
            Approval action record
        """
        workflow = self._get_workflow(workflow_id)

        # Find approver
        approver = next((a for a in workflow.approvers if a.user_id == approver_id), None)
        if not approver:
            raise ValueError(f"Approver {approver_id} not found in workflow")

        # Update workflow status
        workflow.status = WorkflowStatus.IN_PROGRESS
        workflow.updated_at = datetime.utcnow()

        return workflow

    def approve(
        self,
        workflow_id: int,
        user_id: int,
        comments: str = "",
        sections_to_lock: Optional[List[str]] = None,
        ip_address: Optional[str] = None
    ) -> ApprovalAction:
        """
        Approve current stage

        Args:
            workflow_id: Workflow identifier
            user_id: User approving
            comments: Approval comments
            sections_to_lock: Report sections to lock after approval
            ip_address: IP address of approver

        Returns:
            Approval action with digital signature
        """
        workflow = self._get_workflow(workflow_id)

        # Verify user is authorized approver for current stage
        approver = self._verify_approver(workflow, user_id)

        # Generate digital signature
        signature = self.signature_generator.generate_signature(
            user_id=user_id,
            action="approve",
            timestamp=datetime.utcnow(),
            data={
                "workflow_id": workflow_id,
                "stage": workflow.current_stage.value,
                "comments": comments
            },
            ip_address=ip_address
        )

        # Create approval action
        action = self._create_action(
            workflow=workflow,
            user_id=user_id,
            action=ActionType.APPROVE,
            comments=comments,
            signature=signature
        )

        # Lock sections if specified
        if sections_to_lock:
            self._lock_sections(workflow, sections_to_lock, user_id)

        # Advance workflow to next stage
        self._advance_workflow(workflow)

        # Log to audit trail
        self._log_to_audit_trail(action, workflow)

        return action

    def reject(
        self,
        workflow_id: int,
        user_id: int,
        comments: str,
        ip_address: Optional[str] = None
    ) -> ApprovalAction:
        """
        Reject current stage

        Args:
            workflow_id: Workflow identifier
            user_id: User rejecting
            comments: Rejection reason
            ip_address: IP address

        Returns:
            Rejection action
        """
        workflow = self._get_workflow(workflow_id)

        # Verify user is authorized approver
        approver = self._verify_approver(workflow, user_id)

        # Generate digital signature
        signature = self.signature_generator.generate_signature(
            user_id=user_id,
            action="reject",
            timestamp=datetime.utcnow(),
            data={
                "workflow_id": workflow_id,
                "stage": workflow.current_stage.value,
                "comments": comments
            },
            ip_address=ip_address
        )

        # Create rejection action
        action = self._create_action(
            workflow=workflow,
            user_id=user_id,
            action=ActionType.REJECT,
            comments=comments,
            signature=signature
        )

        # Update workflow status
        workflow.status = WorkflowStatus.REJECTED
        workflow.completed_at = datetime.utcnow()
        workflow.updated_at = datetime.utcnow()

        # Log to audit trail
        self._log_to_audit_trail(action, workflow)

        return action

    def request_changes(
        self,
        workflow_id: int,
        user_id: int,
        comments: str,
        ip_address: Optional[str] = None
    ) -> ApprovalAction:
        """
        Request changes to report

        Args:
            workflow_id: Workflow identifier
            user_id: User requesting changes
            comments: Change requests
            ip_address: IP address

        Returns:
            Request changes action
        """
        workflow = self._get_workflow(workflow_id)
        approver = self._verify_approver(workflow, user_id)

        signature = self.signature_generator.generate_signature(
            user_id=user_id,
            action="request_changes",
            timestamp=datetime.utcnow(),
            data={
                "workflow_id": workflow_id,
                "stage": workflow.current_stage.value,
                "comments": comments
            },
            ip_address=ip_address
        )

        action = self._create_action(
            workflow=workflow,
            user_id=user_id,
            action=ActionType.REQUEST_CHANGES,
            comments=comments,
            signature=signature
        )

        # Return workflow to technician stage
        workflow.current_stage = ApprovalStage.TECHNICIAN
        workflow.updated_at = datetime.utcnow()

        self._log_to_audit_trail(action, workflow)

        return action

    def delegate_approval(
        self,
        workflow_id: int,
        from_user_id: int,
        to_user_id: int,
        comments: str = ""
    ) -> ApprovalAction:
        """
        Delegate approval to another user

        Args:
            workflow_id: Workflow identifier
            from_user_id: User delegating
            to_user_id: User receiving delegation
            comments: Delegation reason

        Returns:
            Delegation action
        """
        workflow = self._get_workflow(workflow_id)

        # Verify delegator is authorized and can delegate
        delegator = self._verify_approver(workflow, from_user_id)
        if not delegator.delegation_enabled:
            raise PermissionError(f"User {from_user_id} cannot delegate approval")

        # Create delegated approver
        delegated_approver = Approver(
            user_id=to_user_id,
            name=f"Delegated Approver {to_user_id}",
            email=f"user{to_user_id}@example.com",
            role=delegator.role,
            authority_level=delegator.authority_level,
            delegated_from=from_user_id
        )

        workflow.approvers.append(delegated_approver)

        signature = self.signature_generator.generate_signature(
            user_id=from_user_id,
            action="delegate",
            timestamp=datetime.utcnow(),
            data={
                "workflow_id": workflow_id,
                "to_user": to_user_id,
                "comments": comments
            }
        )

        action = self._create_action(
            workflow=workflow,
            user_id=from_user_id,
            action=ActionType.DELEGATE,
            comments=comments,
            signature=signature
        )

        self._log_to_audit_trail(action, workflow)

        return action

    def check_escalations(self) -> List[ApprovalAction]:
        """
        Check all workflows for escalation timeouts

        Returns:
            List of auto-escalation actions
        """
        escalation_actions = []

        for workflow in self._workflows.values():
            if workflow.status not in [WorkflowStatus.PENDING, WorkflowStatus.IN_PROGRESS]:
                continue

            # Find escalation rule for current stage
            escalation_rule = next(
                (r for r in workflow.escalation_rules if r.from_stage == workflow.current_stage),
                None
            )

            if not escalation_rule:
                continue

            # Check if timeout exceeded
            last_action_time = workflow.updated_at
            timeout_threshold = last_action_time + timedelta(hours=escalation_rule.timeout_hours)

            if datetime.utcnow() > timeout_threshold:
                # Escalate workflow
                action = self._escalate_workflow(workflow, escalation_rule)
                escalation_actions.append(action)

        return escalation_actions

    def get_workflow_status(self, workflow_id: int) -> Dict[str, Any]:
        """
        Get current workflow status

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow status dictionary
        """
        workflow = self._get_workflow(workflow_id)

        return {
            "workflow_id": workflow.workflow_id,
            "report_id": workflow.report_id,
            "current_stage": workflow.current_stage.value,
            "status": workflow.status.value,
            "route_type": workflow.route_type.value,
            "approvers": [
                {
                    "user_id": a.user_id,
                    "name": a.name,
                    "role": a.role.value,
                    "authority_level": a.authority_level
                }
                for a in workflow.approvers
            ],
            "approval_history": [
                {
                    "action_id": action.action_id,
                    "user_id": action.user_id,
                    "action": action.action.value,
                    "stage": action.stage.value,
                    "timestamp": action.timestamp.isoformat(),
                    "comments": action.comments
                }
                for action in workflow.approval_history
            ],
            "locked_sections": [
                {
                    "section_id": lock.section_id,
                    "locked_at": lock.locked_at.isoformat(),
                    "stage": lock.stage.value
                }
                for lock in workflow.locked_sections
            ],
            "created_at": workflow.created_at.isoformat(),
            "updated_at": workflow.updated_at.isoformat(),
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None
        }

    def _get_workflow(self, workflow_id: int) -> ApprovalWorkflow:
        """Get workflow by ID"""
        if workflow_id not in self._workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        return self._workflows[workflow_id]

    def _verify_approver(self, workflow: ApprovalWorkflow, user_id: int) -> Approver:
        """Verify user is authorized approver for current stage"""
        current_approvers = workflow.get_current_approvers()
        approver = next((a for a in current_approvers if a.user_id == user_id), None)

        if not approver:
            # Check for delegated approvers
            approver = next(
                (a for a in workflow.approvers if a.user_id == user_id and a.role == workflow.current_stage),
                None
            )

        if not approver:
            raise PermissionError(
                f"User {user_id} not authorized for stage {workflow.current_stage.value}"
            )

        return approver

    def _create_action(
        self,
        workflow: ApprovalWorkflow,
        user_id: int,
        action: ActionType,
        comments: str,
        signature: DigitalSignature
    ) -> ApprovalAction:
        """Create approval action"""
        self._action_counter += 1

        approval_action = ApprovalAction(
            action_id=self._action_counter,
            workflow_id=workflow.workflow_id,
            user_id=user_id,
            action=action,
            stage=workflow.current_stage,
            comments=comments,
            timestamp=datetime.utcnow(),
            digital_signature=signature,
            previous_state=workflow.status.value,
            new_state=workflow.status.value,
            is_immutable=True
        )

        workflow.approval_history.append(approval_action)
        return approval_action

    def _lock_sections(
        self,
        workflow: ApprovalWorkflow,
        section_ids: List[str],
        user_id: int
    ):
        """Lock report sections after approval"""
        for section_id in section_ids:
            if not workflow.is_section_locked(section_id):
                lock = SectionLock(
                    section_id=section_id,
                    locked_by=user_id,
                    stage=workflow.current_stage,
                    unlock_requires_role=ApprovalStage.MANAGEMENT
                )
                workflow.locked_sections.append(lock)

    def _advance_workflow(self, workflow: ApprovalWorkflow):
        """Advance workflow to next stage"""
        next_stage = workflow.get_next_stage()

        if next_stage:
            workflow.current_stage = next_stage
            workflow.status = WorkflowStatus.IN_PROGRESS
        else:
            # Workflow complete
            workflow.status = WorkflowStatus.APPROVED
            workflow.completed_at = datetime.utcnow()

        workflow.updated_at = datetime.utcnow()

    def _escalate_workflow(
        self,
        workflow: ApprovalWorkflow,
        escalation_rule: EscalationRule
    ) -> ApprovalAction:
        """Escalate workflow due to timeout"""
        signature = self.signature_generator.generate_signature(
            user_id=0,  # System user
            action="escalate",
            timestamp=datetime.utcnow(),
            data={
                "workflow_id": workflow.workflow_id,
                "from_stage": escalation_rule.from_stage.value,
                "reason": "timeout"
            }
        )

        action = self._create_action(
            workflow=workflow,
            user_id=0,  # System
            action=ActionType.ESCALATE,
            comments=f"Auto-escalated after {escalation_rule.timeout_hours} hours",
            signature=signature
        )

        workflow.status = WorkflowStatus.ESCALATED

        if escalation_rule.to_stage:
            workflow.current_stage = escalation_rule.to_stage

        workflow.updated_at = datetime.utcnow()

        self._log_to_audit_trail(action, workflow)

        return action

    def _log_to_audit_trail(self, action: ApprovalAction, workflow: ApprovalWorkflow):
        """Log action to immutable audit trail"""
        self.audit_logger.log_action(
            workflow_id=workflow.workflow_id,
            action_id=action.action_id,
            user_id=action.user_id,
            action=action.action.value,
            stage=action.stage.value,
            previous_state=action.previous_state,
            new_state=action.new_state,
            signature_hash=action.digital_signature.signature_hash,
            metadata={
                "comments": action.comments,
                "timestamp": action.timestamp.isoformat()
            }
        )
