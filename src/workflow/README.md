# Workflow Management System

Production-ready workflow management system for PV test report automation, fully compliant with ISO 17025 requirements.

## Overview

This workflow management system provides comprehensive capabilities for managing multi-level approval workflows with complete audit trails, role-based routing, digital signatures, and multi-channel notifications.

## Features

### ✅ Core Capabilities

- **Multi-level Approval Workflows**: Support for complex approval chains with parallel and sequential steps
- **Role-based Routing**: Automatic assignment of approvers based on roles and business rules
- **Digital Signature Support**: Cryptographic signing of approvals with verification
- **State Machine**: Robust workflow state management with transition validation
- **Audit Trails**: Complete history of all workflow actions and state changes
- **Multi-channel Notifications**: Email, Slack, Teams, SMS, and in-app notifications
- **Subscription Management**: User-configurable notification preferences
- **Escalation Procedures**: Automatic and manual escalation of overdue approvals
- **Delegation**: Transfer approval responsibilities to other users

### 🔒 ISO 17025 Compliance

- Complete approval history tracking
- Digital signature support for non-repudiation
- Audit trail for all workflow changes
- Role-based access control
- Configurable approval rules
- Rejection handling with mandatory comments

## Architecture

```
src/workflow/
├── models.py                 # SQLAlchemy database models
├── workflow_states.py        # State machine implementation
├── approval_engine.py        # Approval workflow engine
├── notification_system.py    # Multi-channel notifications
├── __init__.py              # Package exports
└── tests/                   # Comprehensive unit tests
    ├── test_models.py
    ├── test_workflow_states.py
    ├── test_approval_engine.py
    └── test_notification_system.py
```

## Database Models

### WorkflowDefinition
Reusable workflow templates with approval steps and routing rules.

### WorkflowInstance
Specific execution of a workflow for an entity (e.g., test report).

### ApprovalRecord
Individual approval records with digital signature support.

### StateTransition
Audit trail of all workflow state changes.

### NotificationLog
Complete history of all notifications sent.

### NotificationPreference
User notification preferences per channel.

### NotificationSubscription
Workflow notification subscriptions.

## Quick Start

### 1. Initialize Database

```python
from sqlalchemy import create_engine
from src.workflow.models import Base

engine = create_engine("postgresql://user:pass@localhost/db")
Base.metadata.create_all(engine)
```

### 2. Create Workflow Definition

```python
from src.workflow import WorkflowDefinition

definition = WorkflowDefinition(
    name="Test Report Approval",
    description="Standard test report approval workflow",
    version="1.0.0",
    category="report_approval",
    config={
        "steps": [
            {"step": 1, "name": "Technical Review", "role": "reviewer"},
            {"step": 2, "name": "Manager Approval", "role": "manager"}
        ]
    },
    created_by="admin"
)
session.add(definition)
session.commit()
```

### 3. Create Workflow Instance

```python
from src.workflow import WorkflowInstance, WorkflowStatus

workflow = WorkflowInstance(
    definition_id=definition.id,
    entity_type="TestReport",
    entity_id="TR-2024-001",
    reference_number="WF-001",
    status=WorkflowStatus.DRAFT,
    initiated_by="user@example.com"
)
session.add(workflow)
session.commit()
```

### 4. Create Approval Workflow

```python
from src.workflow import ApprovalEngine, ApprovalStep, ApprovalLevel

engine = ApprovalEngine(session)

steps = [
    ApprovalStep(
        step_number=1,
        step_name="Technical Review",
        approval_level=ApprovalLevel.TECHNICAL_REVIEW,
        required_role="technical_reviewer",
        min_approvers=1
    ),
    ApprovalStep(
        step_number=2,
        step_name="Manager Approval",
        approval_level=ApprovalLevel.MANAGER_APPROVAL,
        required_role="manager",
        min_approvers=1
    )
]

approvals = engine.create_approval_workflow(workflow, steps, "initiator@example.com")
```

### 5. Submit Approval

```python
from src.workflow import DigitalSignature

# Optional digital signature
signature = DigitalSignature(
    signer_id="reviewer@example.com",
    signature_data="encrypted_signature",
    certificate_thumbprint="ABC123"
)

approval = engine.submit_approval(
    approval_id=1,
    reviewer_id="reviewer@example.com",
    decision="approved",
    comments="Looks good",
    signature=signature
)
```

### 6. Send Notifications

```python
from src.workflow import NotificationSystem, NotificationEvent

notif_system = NotificationSystem(session)

notif_system.notify_workflow_event(
    workflow=workflow,
    event=NotificationEvent.APPROVAL_REQUESTED,
    additional_data={
        "approval": {"step_name": "Technical Review"},
        "approval_url": "https://example.com/approval/1"
    }
)
```

## State Machine

The workflow state machine manages valid transitions between workflow states:

### Workflow States
- `DRAFT`: Initial state
- `PENDING`: Submitted, awaiting review
- `IN_PROGRESS`: Under review
- `APPROVED`: All approvals completed
- `REJECTED`: Approval rejected
- `CANCELLED`: Workflow cancelled
- `ESCALATED`: Escalated to higher authority
- `COMPLETED`: Workflow fully completed

### Workflow Events
- `SUBMIT`: Submit workflow for approval
- `START_REVIEW`: Begin review process
- `APPROVE`: Approve current step
- `REJECT`: Reject workflow
- `REQUEST_CHANGES`: Request modifications
- `RESUBMIT`: Resubmit after rejection
- `CANCEL`: Cancel workflow
- `ESCALATE`: Escalate to higher authority
- `COMPLETE`: Mark as completed
- `DELEGATE`: Delegate approval

### Example: State Transitions

```python
from src.workflow import WorkflowStateMachine, WorkflowEvent

state_machine = WorkflowStateMachine()

# Transition from DRAFT to PENDING
state_machine.transition(
    workflow,
    WorkflowEvent.SUBMIT,
    context={"user_id": "user@example.com"},
    session=session
)

# Check available events
events = state_machine.get_available_events(workflow)
```

## Approval Features

### Multi-level Approvals

```python
steps = [
    ApprovalStep(
        step_number=1,
        step_name="Technical Review",
        approval_level=ApprovalLevel.TECHNICAL_REVIEW,
        required_role="technical_reviewer",
        min_approvers=2,  # Require 2 approvers
        requires_all=True  # All must approve
    ),
    ApprovalStep(
        step_number=2,
        step_name="Quality Approval",
        approval_level=ApprovalLevel.QUALITY_APPROVAL,
        required_role="quality_manager",
        min_approvers=1
    )
]
```

### Parallel Approvals

```python
step = ApprovalStep(
    step_number=1,
    step_name="Peer Review",
    approval_level=ApprovalLevel.TECHNICAL_REVIEW,
    required_role="reviewer",
    min_approvers=2,
    parallel=True  # Multiple reviewers can approve simultaneously
)
```

### Approval Delegation

```python
# Delegate approval to another user
new_approval = engine.delegate_approval(
    approval_id=1,
    from_user_id="original_reviewer@example.com",
    to_user_id="delegate_reviewer@example.com",
    reason="On vacation"
)
```

### Approval Escalation

```python
# Escalate overdue approval
escalated = engine.escalate_approval(
    approval_id=1,
    escalated_by="admin@example.com",
    reason="Approval overdue by 48 hours",
    escalate_to_role="manager"
)
```

## Notification System

### Configure Notification System

```python
from src.workflow import NotificationConfig, NotificationSystem

config = NotificationConfig(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_username="noreply@example.com",
    smtp_password="password",
    from_email="noreply@example.com",
    from_name="PV Test Automation"
)

notif_system = NotificationSystem(session, config)
```

### Send Email Notification

```python
from src.workflow import NotificationChannel

notification = notif_system.send_notification(
    channel=NotificationChannel.EMAIL,
    recipient="user@example.com",
    subject="Approval Required",
    message="You have a new approval request",
    workflow_id=workflow.id
)
```

### Use Notification Templates

```python
template_vars = {
    "recipient_name": "John Doe",
    "workflow": {
        "reference_number": workflow.reference_number,
        "entity_type": workflow.entity_type,
        "priority": workflow.priority
    },
    "approval": {"step_name": "Review"},
    "approval_url": "https://example.com/approval/1",
    "from_name": "PV Test System"
}

notification = notif_system.send_from_template(
    channel=NotificationChannel.EMAIL,
    recipient="user@example.com",
    template_name="approval_requested",
    template_vars=template_vars,
    workflow_id=workflow.id
)
```

### Subscribe to Notifications

```python
subscription = notif_system.subscribe_user(
    user_id="user@example.com",
    entity_type="TestReport",  # Subscribe to all test report workflows
    event_types=["approval_requested", "workflow_completed"],
    channels=["email", "slack"]
)
```

### Set Notification Preferences

```python
from src.workflow import NotificationPreference

preference = NotificationPreference(
    user_id="user@example.com",
    channel=NotificationChannel.EMAIL,
    enabled=True,
    contact_info="user@example.com",
    quiet_hours_start="22:00",
    quiet_hours_end="08:00",
    timezone="America/New_York"
)
session.add(preference)
session.commit()
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest src/workflow/tests/

# Run specific test file
python -m pytest src/workflow/tests/test_approval_engine.py

# Run with coverage
python -m pytest --cov=src/workflow src/workflow/tests/
```

## API Reference

### ApprovalEngine

- `create_approval_workflow(workflow, steps, initiator_id)`: Create approval workflow
- `submit_approval(approval_id, reviewer_id, decision, comments, signature)`: Submit approval
- `delegate_approval(approval_id, from_user_id, to_user_id, reason)`: Delegate approval
- `escalate_approval(approval_id, escalated_by, reason, escalate_to_role)`: Escalate approval
- `get_approval_history(workflow_id)`: Get complete approval history
- `get_pending_approvals(user_id, role)`: Get pending approvals
- `check_overdue_approvals()`: Check for overdue approvals

### WorkflowStateMachine

- `transition(workflow, event, context, session)`: Execute state transition
- `can_transition(workflow, event, context)`: Check if transition is valid
- `get_available_events(workflow)`: Get available events for current state
- `register_hook(hook_type, callback, state)`: Register event hook
- `validate_workflow_path(start_state, end_state, max_depth)`: Find valid path between states

### NotificationSystem

- `send_notification(channel, recipient, subject, message, ...)`: Send notification
- `send_from_template(channel, recipient, template_name, template_vars, ...)`: Send using template
- `notify_workflow_event(workflow, event, recipients, additional_data)`: Notify workflow event
- `subscribe_user(user_id, workflow_id, entity_type, event_types, channels)`: Subscribe user
- `unsubscribe_user(subscription_id)`: Unsubscribe user
- `retry_failed_notifications()`: Retry failed notifications

## Configuration

### Workflow Configuration

Workflow definitions support configurable approval rules:

```python
config = {
    "steps": [
        {
            "step": 1,
            "name": "Technical Review",
            "role": "technical_reviewer",
            "min_approvers": 2,
            "parallel": True,
            "timeout_hours": 48
        },
        {
            "step": 2,
            "name": "Quality Approval",
            "role": "quality_manager",
            "min_approvers": 1,
            "requires_signature": True
        }
    ],
    "auto_escalate": True,
    "escalation_timeout_hours": 72
}
```

## Best Practices

1. **Always use database transactions** for workflow operations
2. **Enable digital signatures** for critical approvals
3. **Configure escalation timeouts** to prevent bottlenecks
4. **Use notification subscriptions** instead of hardcoded recipients
5. **Implement approval delegation** for continuity during absences
6. **Monitor overdue approvals** regularly
7. **Maintain audit trails** for compliance
8. **Use role-based assignment** for scalability

## Dependencies

- SQLAlchemy >= 2.0
- Jinja2 >= 3.0 (for notification templates)
- Python >= 3.8

## License

See LICENSE file in repository root.

## Support

For issues or questions, please contact the development team.
