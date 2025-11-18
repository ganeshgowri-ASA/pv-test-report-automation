"""
Escalation Manager for Auto-Escalation
Handles timeout-based escalation and notifications
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from models.approval_models import (
    ApprovalWorkflow,
    EscalationRule,
    ApprovalStage,
    WorkflowStatus
)


class EscalationManager:
    """
    Manages workflow escalation based on timeout rules
    Sends notifications and auto-escalates pending approvals
    """

    def __init__(self):
        """Initialize escalation manager"""
        self.escalation_history: List[Dict[str, Any]] = []

    def create_escalation_rule(
        self,
        from_stage: ApprovalStage,
        timeout_hours: int = 24,
        to_stage: Optional[ApprovalStage] = None,
        escalation_user_id: Optional[int] = None,
        notification_emails: Optional[List[str]] = None,
        auto_approve: bool = False
    ) -> EscalationRule:
        """
        Create escalation rule

        Args:
            from_stage: Stage to escalate from
            timeout_hours: Hours before escalation
            to_stage: Stage to escalate to (default: next in hierarchy)
            escalation_user_id: User to escalate to
            notification_emails: Email addresses for notifications
            auto_approve: Automatically approve on escalation

        Returns:
            Escalation rule
        """
        if to_stage is None:
            # Default to next stage in hierarchy
            next_stage_str = ApprovalStage.get_next_stage(from_stage.value)
            to_stage = ApprovalStage(next_stage_str) if next_stage_str else None

        return EscalationRule(
            from_stage=from_stage,
            to_stage=to_stage,
            timeout_hours=timeout_hours,
            escalation_user_id=escalation_user_id,
            notification_emails=notification_emails or [],
            auto_approve=auto_approve
        )

    def check_workflow_escalation(
        self,
        workflow: ApprovalWorkflow,
        current_time: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Check if workflow needs escalation

        Args:
            workflow: Workflow to check
            current_time: Current time (default: now)

        Returns:
            Escalation details if needed, None otherwise
        """
        if current_time is None:
            current_time = datetime.utcnow()

        # Skip if workflow is not in progress
        if workflow.status not in [WorkflowStatus.PENDING, WorkflowStatus.IN_PROGRESS]:
            return None

        # Find escalation rule for current stage
        escalation_rule = next(
            (r for r in workflow.escalation_rules if r.from_stage == workflow.current_stage),
            None
        )

        if not escalation_rule:
            return None

        # Check timeout
        last_update = workflow.updated_at
        timeout_threshold = last_update + timedelta(hours=escalation_rule.timeout_hours)

        if current_time > timeout_threshold:
            return {
                "workflow_id": workflow.workflow_id,
                "current_stage": workflow.current_stage.value,
                "timeout_hours": escalation_rule.timeout_hours,
                "escalate_to_stage": escalation_rule.to_stage.value if escalation_rule.to_stage else None,
                "escalate_to_user": escalation_rule.escalation_user_id,
                "notification_emails": escalation_rule.notification_emails,
                "auto_approve": escalation_rule.auto_approve,
                "time_exceeded_by": (current_time - timeout_threshold).total_seconds() / 3600
            }

        return None

    def get_escalation_warnings(
        self,
        workflow: ApprovalWorkflow,
        warning_threshold_hours: int = 2,
        current_time: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get early warning before escalation

        Args:
            workflow: Workflow to check
            warning_threshold_hours: Hours before timeout to warn
            current_time: Current time

        Returns:
            Warning details if approaching timeout
        """
        if current_time is None:
            current_time = datetime.utcnow()

        escalation_rule = next(
            (r for r in workflow.escalation_rules if r.from_stage == workflow.current_stage),
            None
        )

        if not escalation_rule:
            return None

        last_update = workflow.updated_at
        timeout_threshold = last_update + timedelta(hours=escalation_rule.timeout_hours)
        warning_threshold = timeout_threshold - timedelta(hours=warning_threshold_hours)

        if warning_threshold <= current_time < timeout_threshold:
            hours_remaining = (timeout_threshold - current_time).total_seconds() / 3600
            return {
                "workflow_id": workflow.workflow_id,
                "current_stage": workflow.current_stage.value,
                "hours_remaining": round(hours_remaining, 2),
                "notification_emails": escalation_rule.notification_emails,
                "warning_level": "high" if hours_remaining < 1 else "medium"
            }

        return None

    def send_escalation_notification(
        self,
        escalation_details: Dict[str, Any]
    ) -> bool:
        """
        Send escalation notification

        Args:
            escalation_details: Escalation information

        Returns:
            True if notification sent successfully
        """
        # In production, integrate with email service
        notification = {
            "timestamp": datetime.utcnow().isoformat(),
            "workflow_id": escalation_details["workflow_id"],
            "stage": escalation_details["current_stage"],
            "recipients": escalation_details["notification_emails"],
            "message": f"Workflow {escalation_details['workflow_id']} has been escalated "
                      f"from stage {escalation_details['current_stage']} after "
                      f"{escalation_details['timeout_hours']} hours timeout"
        }

        self.escalation_history.append(notification)

        # TODO: Integrate with actual email service (SMTP, SendGrid, etc.)
        print(f"[ESCALATION NOTIFICATION] {notification['message']}")
        print(f"  Recipients: {', '.join(notification['recipients'])}")

        return True

    def get_escalation_statistics(self) -> Dict[str, Any]:
        """
        Get escalation statistics

        Returns:
            Statistics dictionary
        """
        return {
            "total_escalations": len(self.escalation_history),
            "escalations_by_stage": self._group_by_stage(),
            "recent_escalations": self.escalation_history[-10:]
        }

    def _group_by_stage(self) -> Dict[str, int]:
        """Group escalations by stage"""
        stage_counts = {}
        for escalation in self.escalation_history:
            stage = escalation.get("stage", "unknown")
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
        return stage_counts
