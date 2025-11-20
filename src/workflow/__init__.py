"""
Workflow management system for PV test report automation.

This package provides comprehensive workflow management capabilities:
- Multi-level approval workflows
- Role-based routing and assignment
- Digital signature support
- Multi-channel notifications
- State machine implementation
- Complete audit trails

ISO 17025 compliant workflow management.
"""

from .models import (
    # Base
    Base,
    # Enums
    WorkflowStatus,
    ApprovalStatus,
    NotificationStatus,
    NotificationChannel,
    # Models
    WorkflowDefinition,
    WorkflowInstance,
    ApprovalRecord,
    StateTransition,
    NotificationLog,
    NotificationPreference,
    NotificationSubscription,
)

from .workflow_states import (
    WorkflowStateMachine,
    WorkflowEvent,
    StateTransitionRule,
)

from .approval_engine import (
    ApprovalEngine,
    ApprovalLevel,
    ApprovalStep,
    DigitalSignature,
)

from .notification_system import (
    NotificationSystem,
    NotificationConfig,
    NotificationTemplate,
    NotificationPriority,
    NotificationEvent,
)


__version__ = "1.0.0"

__all__ = [
    # Models
    "Base",
    "WorkflowStatus",
    "ApprovalStatus",
    "NotificationStatus",
    "NotificationChannel",
    "WorkflowDefinition",
    "WorkflowInstance",
    "ApprovalRecord",
    "StateTransition",
    "NotificationLog",
    "NotificationPreference",
    "NotificationSubscription",
    # State Machine
    "WorkflowStateMachine",
    "WorkflowEvent",
    "StateTransitionRule",
    # Approval Engine
    "ApprovalEngine",
    "ApprovalLevel",
    "ApprovalStep",
    "DigitalSignature",
    # Notification System
    "NotificationSystem",
    "NotificationConfig",
    "NotificationTemplate",
    "NotificationPriority",
    "NotificationEvent",
]
