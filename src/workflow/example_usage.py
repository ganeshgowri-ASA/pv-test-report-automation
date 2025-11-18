"""
Example usage of the workflow management system.

This example demonstrates a complete workflow lifecycle:
1. Creating a workflow definition
2. Initiating a workflow instance
3. Setting up multi-level approvals
4. Processing approvals with digital signatures
5. Handling rejections and resubmissions
6. Managing notifications and subscriptions
7. Tracking approval history and audit trails
"""

from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.workflow import (
    # Models
    Base, WorkflowDefinition, WorkflowInstance, WorkflowStatus,
    # Approval Engine
    ApprovalEngine, ApprovalLevel, ApprovalStep, DigitalSignature,
    # State Machine
    WorkflowStateMachine, WorkflowEvent,
    # Notifications
    NotificationSystem, NotificationConfig, NotificationEvent,
    NotificationChannel, NotificationPriority
)


def setup_database():
    """Initialize the database."""
    print("Setting up database...")
    engine = create_engine("sqlite:///workflow_example.db", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def create_workflow_definition(session):
    """Create a reusable workflow definition."""
    print("\n=== Creating Workflow Definition ===")

    definition = WorkflowDefinition(
        name="PV Test Report Approval",
        description="Standard approval workflow for PV test reports",
        version="1.0.0",
        category="report_approval",
        config={
            "steps": [
                {
                    "step": 1,
                    "name": "Technical Review",
                    "role": "technical_reviewer",
                    "min_approvers": 1,
                    "timeout_hours": 48
                },
                {
                    "step": 2,
                    "name": "Quality Approval",
                    "role": "quality_manager",
                    "min_approvers": 1,
                    "requires_signature": True,
                    "timeout_hours": 24
                },
                {
                    "step": 3,
                    "name": "Manager Sign-off",
                    "role": "operations_manager",
                    "min_approvers": 1,
                    "requires_signature": True,
                    "timeout_hours": 24
                }
            ],
            "auto_escalate": True,
            "escalation_timeout_hours": 72
        },
        is_iso_compliant=True,
        requires_digital_signature=True,
        created_by="admin@example.com"
    )

    session.add(definition)
    session.commit()

    print(f"Created workflow definition: {definition.name} (v{definition.version})")
    print(f"ISO 17025 Compliant: {definition.is_iso_compliant}")
    print(f"Requires Digital Signatures: {definition.requires_digital_signature}")

    return definition


def create_workflow_instance(session, definition):
    """Create a workflow instance for a test report."""
    print("\n=== Creating Workflow Instance ===")

    workflow = WorkflowInstance(
        definition_id=definition.id,
        entity_type="TestReport",
        entity_id="TR-2024-001",
        reference_number="WF-2024-001",
        status=WorkflowStatus.DRAFT,
        initiated_by="engineer@example.com",
        priority=2,  # Normal priority
        due_date=datetime.utcnow() + timedelta(days=7),
        context_data={
            "report_type": "Module Performance Test",
            "customer": "Solar Corp",
            "test_date": "2024-01-15",
            "module_count": 48
        }
    )

    session.add(workflow)
    session.commit()

    print(f"Created workflow: {workflow.reference_number}")
    print(f"Entity: {workflow.entity_type} - {workflow.entity_id}")
    print(f"Status: {workflow.status.value}")
    print(f"Due: {workflow.due_date.strftime('%Y-%m-%d')}")

    return workflow


def setup_approval_workflow(session, workflow):
    """Set up multi-level approval workflow."""
    print("\n=== Setting Up Approval Workflow ===")

    state_machine = WorkflowStateMachine()
    approval_engine = ApprovalEngine(session, state_machine)

    # Define approval steps
    steps = [
        ApprovalStep(
            step_number=1,
            step_name="Technical Review",
            approval_level=ApprovalLevel.TECHNICAL_REVIEW,
            required_role="technical_reviewer",
            min_approvers=1,
            auto_assign=True,
            assignment_strategy="round_robin",
            escalation_timeout=48
        ),
        ApprovalStep(
            step_number=2,
            step_name="Quality Approval",
            approval_level=ApprovalLevel.QUALITY_APPROVAL,
            required_role="quality_manager",
            min_approvers=1,
            auto_assign=True,
            assignment_strategy="specific",
            escalation_timeout=24,
            metadata={"assigned_users": ["quality_mgr@example.com"]}
        ),
        ApprovalStep(
            step_number=3,
            step_name="Manager Sign-off",
            approval_level=ApprovalLevel.MANAGER_APPROVAL,
            required_role="operations_manager",
            min_approvers=1,
            auto_assign=True,
            assignment_strategy="specific",
            escalation_timeout=24,
            metadata={"assigned_users": ["ops_mgr@example.com"]}
        )
    ]

    # Create approval records
    approvals = approval_engine.create_approval_workflow(
        workflow,
        steps,
        "engineer@example.com"
    )

    print(f"Created {len(approvals)} approval steps")
    for approval in approvals:
        print(f"  Step {approval.step_number}: {approval.step_name} -> {approval.assigned_to}")

    return approval_engine, approvals


def submit_workflow(session, workflow, state_machine):
    """Submit workflow for approval."""
    print("\n=== Submitting Workflow ===")

    # Transition from DRAFT to PENDING
    state_machine.transition(
        workflow,
        WorkflowEvent.SUBMIT,
        context={
            "user_id": "engineer@example.com",
            "reason": "Test report completed and ready for review"
        },
        session=session
    )

    print(f"Workflow submitted: {workflow.reference_number}")
    print(f"New status: {workflow.status.value}")
    print(f"Current step: {workflow.current_step}")

    return workflow


def process_technical_review(session, approval_engine, workflow, approvals):
    """Process technical review approval."""
    print("\n=== Processing Technical Review ===")

    # Start review
    state_machine = WorkflowStateMachine()
    state_machine.transition(
        workflow,
        WorkflowEvent.START_REVIEW,
        context={
            "user_id": "tech_reviewer@example.com",
            "user_role": "reviewer"
        },
        session=session
    )

    print(f"Review started. Status: {workflow.status.value}")

    # Get first approval (technical review)
    tech_approval = approvals[0]

    # Create digital signature
    signature = DigitalSignature(
        signer_id="tech_reviewer@example.com",
        signature_data="BASE64_ENCRYPTED_SIGNATURE_DATA_HERE",
        certificate_thumbprint="1A2B3C4D5E6F7G8H9I0J",
        signature_method="SHA256-RSA"
    )

    # Submit approval
    updated_approval = approval_engine.submit_approval(
        tech_approval.id,
        "tech_reviewer@example.com",
        "approved",
        comments="Technical review completed. All test procedures followed correctly.",
        signature=signature,
        metadata={
            "review_duration_minutes": 45,
            "checklist_items": 12,
            "issues_found": 0
        }
    )

    print(f"Technical review approved by: {updated_approval.reviewed_by}")
    print(f"Comments: {updated_approval.comments}")
    print(f"Digital signature: {updated_approval.signature_hash[:16]}...")
    print(f"Workflow moved to step: {workflow.current_step}")

    return updated_approval


def process_quality_approval(session, approval_engine, workflow, approvals):
    """Process quality manager approval."""
    print("\n=== Processing Quality Approval ===")

    # Get second approval (quality)
    quality_approval = approvals[1] if len(approvals) > 1 else None
    if not quality_approval:
        # Query from database if not in list
        from src.workflow.models import ApprovalRecord, ApprovalStatus
        quality_approval = session.query(ApprovalRecord).filter_by(
            workflow_id=workflow.id,
            step_number=2,
            status=ApprovalStatus.PENDING
        ).first()

    if quality_approval:
        # Create digital signature
        signature = DigitalSignature(
            signer_id="quality_mgr@example.com",
            signature_data="QUALITY_SIGNATURE_DATA",
            certificate_thumbprint="Q1W2E3R4T5Y6U7I8O9P0",
            signature_method="SHA256-RSA"
        )

        # Submit approval
        updated_approval = approval_engine.submit_approval(
            quality_approval.id,
            "quality_mgr@example.com",
            "approved",
            comments="Quality review passed. Report meets ISO 17025 requirements.",
            signature=signature,
            metadata={
                "iso_compliance_check": "passed",
                "calibration_verification": "valid",
                "documentation_complete": True
            }
        )

        print(f"Quality approval by: {updated_approval.reviewed_by}")
        print(f"Comments: {updated_approval.comments}")
        print(f"Workflow moved to step: {workflow.current_step}")

        return updated_approval
    else:
        print("Quality approval not found")
        return None


def process_manager_signoff(session, approval_engine, workflow):
    """Process manager final sign-off."""
    print("\n=== Processing Manager Sign-off ===")

    # Get manager approval
    from src.workflow.models import ApprovalRecord, ApprovalStatus
    mgr_approval = session.query(ApprovalRecord).filter_by(
        workflow_id=workflow.id,
        step_number=3,
        status=ApprovalStatus.PENDING
    ).first()

    if mgr_approval:
        # Create digital signature
        signature = DigitalSignature(
            signer_id="ops_mgr@example.com",
            signature_data="MANAGER_SIGNATURE_DATA",
            certificate_thumbprint="M1N2B3V4C5X6Z7A8S9D0",
            signature_method="SHA256-RSA"
        )

        # Submit approval
        updated_approval = approval_engine.submit_approval(
            mgr_approval.id,
            "ops_mgr@example.com",
            "approved",
            comments="Final approval granted. Report authorized for release.",
            signature=signature
        )

        print(f"Manager sign-off by: {updated_approval.reviewed_by}")
        print(f"Final workflow status: {workflow.status.value}")

        # Complete workflow
        state_machine = WorkflowStateMachine()
        if workflow.status == WorkflowStatus.APPROVED:
            state_machine.transition(
                workflow,
                WorkflowEvent.COMPLETE,
                context={
                    "user_id": "system",
                    "user_role": "system"
                },
                session=session
            )
            print(f"Workflow completed: {workflow.status.value}")
            print(f"Completed at: {workflow.completed_at}")

        return updated_approval
    else:
        print("Manager approval not found")
        return None


def demonstrate_rejection_flow(session):
    """Demonstrate workflow rejection and resubmission."""
    print("\n=== Demonstrating Rejection Flow ===")

    # Create a separate workflow for rejection demo
    definition = session.query(WorkflowDefinition).first()

    workflow = WorkflowInstance(
        definition_id=definition.id,
        entity_type="TestReport",
        entity_id="TR-2024-002",
        reference_number="WF-2024-002",
        status=WorkflowStatus.IN_PROGRESS,
        initiated_by="engineer@example.com"
    )
    session.add(workflow)
    session.commit()

    # Create approval
    from src.workflow.models import ApprovalRecord, ApprovalStatus
    approval = ApprovalRecord(
        workflow_id=workflow.id,
        step_number=1,
        step_name="Technical Review",
        assigned_to="tech_reviewer@example.com",
        status=ApprovalStatus.PENDING,
        metadata={"requires_all": True}
    )
    session.add(approval)
    session.commit()

    # Reject the approval
    approval_engine = ApprovalEngine(session, WorkflowStateMachine())
    approval_engine.submit_approval(
        approval.id,
        "tech_reviewer@example.com",
        "rejected",
        comments="Test procedures not followed correctly. Please rerun tests with proper calibration."
    )

    print(f"Workflow rejected. Status: {workflow.status.value}")
    print(f"Rejection reason: {approval.comments}")

    # Resubmit workflow
    state_machine = WorkflowStateMachine()
    state_machine.transition(
        workflow,
        WorkflowEvent.RESUBMIT,
        context={
            "user_id": "engineer@example.com",
            "reason": "Tests rerun with proper calibration"
        },
        session=session
    )

    print(f"Workflow resubmitted. Status: {workflow.status.value}")


def setup_notifications(session, workflow):
    """Set up and demonstrate notification system."""
    print("\n=== Setting Up Notifications ===")

    config = NotificationConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        from_email="noreply@example.com",
        from_name="PV Test Automation System"
    )

    notif_system = NotificationSystem(session, config)

    # Subscribe users to workflow events
    subscriptions = [
        notif_system.subscribe_user(
            user_id="engineer@example.com",
            workflow_id=workflow.id,
            event_types=["approval_approved", "approval_rejected", "workflow_completed"]
        ),
        notif_system.subscribe_user(
            user_id="tech_reviewer@example.com",
            entity_type="TestReport",
            event_types=["approval_requested"]
        ),
        notif_system.subscribe_user(
            user_id="quality_mgr@example.com",
            entity_type="TestReport",
            event_types=["approval_requested", "approval_escalated"]
        )
    ]

    print(f"Created {len(subscriptions)} notification subscriptions")

    # Send workflow event notification
    notif_system.notify_workflow_event(
        workflow=workflow,
        event=NotificationEvent.WORKFLOW_COMPLETED,
        additional_data={
            "workflow_url": f"https://example.com/workflow/{workflow.id}"
        }
    )

    print("Sent workflow completion notifications")

    return notif_system


def display_approval_history(session, workflow):
    """Display complete approval history."""
    print("\n=== Approval History ===")

    approval_engine = ApprovalEngine(session, WorkflowStateMachine())
    history = approval_engine.get_approval_history(workflow.id)

    print(f"Workflow: {workflow.reference_number}")
    print(f"Entity: {workflow.entity_type} - {workflow.entity_id}")
    print(f"Status: {workflow.status.value}")
    print("\nApproval Steps:")

    for record in history:
        print(f"\nStep {record['step_number']}: {record['step_name']}")
        print(f"  Assigned to: {record['assigned_to']}")
        print(f"  Status: {record['status']}")
        if record['reviewed_by']:
            print(f"  Reviewed by: {record['reviewed_by']}")
            print(f"  Reviewed at: {record['reviewed_at']}")
            print(f"  Decision: {record['decision']}")
            print(f"  Comments: {record['comments']}")
            if record['signature_hash']:
                print(f"  Digital Signature: {record['signature_hash'][:16]}...")


def display_state_transitions(session, workflow):
    """Display workflow state transition history."""
    print("\n=== State Transition History ===")

    from src.workflow.models import StateTransition
    transitions = session.query(StateTransition).filter_by(
        workflow_id=workflow.id
    ).order_by(StateTransition.transitioned_at).all()

    print(f"Workflow: {workflow.reference_number}")
    print(f"Total transitions: {len(transitions)}\n")

    for trans in transitions:
        print(f"{trans.transitioned_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  {trans.from_state or 'None'} -> {trans.to_state}")
        print(f"  Event: {trans.event}")
        print(f"  Triggered by: {trans.triggered_by}")
        if trans.reason:
            print(f"  Reason: {trans.reason}")
        print()


def main():
    """Main example execution."""
    print("=" * 60)
    print("WORKFLOW MANAGEMENT SYSTEM - EXAMPLE USAGE")
    print("=" * 60)

    # Initialize
    session = setup_database()

    try:
        # Create workflow definition
        definition = create_workflow_definition(session)

        # Create workflow instance
        workflow = create_workflow_instance(session, definition)

        # Set up approval workflow
        approval_engine, approvals = setup_approval_workflow(session, workflow)

        # Initialize state machine
        state_machine = WorkflowStateMachine()

        # Submit workflow
        workflow = submit_workflow(session, workflow, state_machine)

        # Process approvals
        tech_approval = process_technical_review(session, approval_engine, workflow, approvals)
        quality_approval = process_quality_approval(session, approval_engine, workflow, approvals)
        mgr_approval = process_manager_signoff(session, approval_engine, workflow)

        # Set up notifications
        notif_system = setup_notifications(session, workflow)

        # Display results
        display_approval_history(session, workflow)
        display_state_transitions(session, workflow)

        # Demonstrate rejection flow
        demonstrate_rejection_flow(session)

        print("\n" + "=" * 60)
        print("EXAMPLE COMPLETED SUCCESSFULLY")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    main()
