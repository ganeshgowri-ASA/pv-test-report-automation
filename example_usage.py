"""
Example Usage: Approval Workflow Engine for ISO 17025 Compliance

This example demonstrates the complete multi-level approval workflow
with digital signatures, audit trail, and auto-escalation.
"""

from datetime import datetime, timedelta
from models.approval_models import (
    Approver,
    ApprovalStage,
    ApprovalRoute
)
from workflow.approval import ApprovalWorkflowEngine
from workflow.escalation import EscalationManager


def main():
    """Demonstrate approval workflow usage"""

    print("=" * 80)
    print("PV Test Report Automation - Approval Workflow Engine")
    print("ISO 17025 Compliance Example")
    print("=" * 80)
    print()

    # Initialize workflow engine
    engine = ApprovalWorkflowEngine()
    escalation_manager = EscalationManager()

    # Step 1: Define approval hierarchy
    print("Step 1: Defining Approval Hierarchy")
    print("-" * 80)

    approvers = [
        Approver(
            user_id=1001,
            name="Alice Johnson",
            email="alice.johnson@pvlab.com",
            role=ApprovalStage.TECHNICIAN,
            authority_level=1
        ),
        Approver(
            user_id=2001,
            name="Bob Smith",
            email="bob.smith@pvlab.com",
            role=ApprovalStage.REVIEWER,
            authority_level=2,
            delegation_enabled=True,
            escalation_timeout_hours=24
        ),
        Approver(
            user_id=3001,
            name="Carol Davis",
            email="carol.davis@pvlab.com",
            role=ApprovalStage.APPROVER,
            authority_level=3,
            escalation_timeout_hours=48
        ),
        Approver(
            user_id=4001,
            name="David Wilson",
            email="david.wilson@pvlab.com",
            role=ApprovalStage.MANAGEMENT,
            authority_level=4
        )
    ]

    for approver in approvers:
        print(f"  {approver.role.value.upper()}: {approver.name} ({approver.email})")
    print()

    # Step 2: Create escalation rules
    print("Step 2: Configuring Auto-Escalation Rules")
    print("-" * 80)

    escalation_rules = [
        escalation_manager.create_escalation_rule(
            from_stage=ApprovalStage.TECHNICIAN,
            timeout_hours=12,
            notification_emails=["supervisor@pvlab.com"]
        ),
        escalation_manager.create_escalation_rule(
            from_stage=ApprovalStage.REVIEWER,
            timeout_hours=24,
            notification_emails=["manager@pvlab.com"]
        ),
        escalation_manager.create_escalation_rule(
            from_stage=ApprovalStage.APPROVER,
            timeout_hours=48,
            notification_emails=["director@pvlab.com"]
        )
    ]

    for rule in escalation_rules:
        print(f"  {rule.from_stage.value} → {rule.to_stage.value if rule.to_stage else 'N/A'} "
              f"({rule.timeout_hours}h timeout)")
    print()

    # Step 3: Create workflow
    print("Step 3: Creating Approval Workflow")
    print("-" * 80)

    workflow = engine.create_workflow(
        workflow_id=123,
        report_id=456,
        approvers=approvers,
        route_type=ApprovalRoute.SEQUENTIAL,
        escalation_rules=escalation_rules
    )

    print(f"  Workflow ID: {workflow.workflow_id}")
    print(f"  Report ID: {workflow.report_id}")
    print(f"  Route Type: {workflow.route_type.value}")
    print(f"  Current Stage: {workflow.current_stage.value}")
    print(f"  Status: {workflow.status.value}")
    print(f"  ISO 17025 Compliant: {workflow.iso_17025_compliant}")
    print()

    # Step 4: Technician approval
    print("Step 4: Technician Data Entry & Approval")
    print("-" * 80)

    tech_action = engine.approve(
        workflow_id=123,
        user_id=1001,
        comments="Test data collected and entered. All measurements verified.",
        sections_to_lock=["test_data", "measurements"],
        ip_address="192.168.1.101"
    )

    print(f"  Action: {tech_action.action.value}")
    print(f"  User: Alice Johnson (Technician)")
    print(f"  Comments: {tech_action.comments}")
    print(f"  Digital Signature: {tech_action.digital_signature.signature_hash[:32]}...")
    print(f"  Timestamp: {tech_action.timestamp}")
    print(f"  Locked Sections: test_data, measurements")
    print(f"  New Stage: {workflow.current_stage.value}")
    print()

    # Step 5: Reviewer approval
    print("Step 5: Technical Review & Approval")
    print("-" * 80)

    reviewer_action = engine.approve(
        workflow_id=123,
        user_id=2001,
        comments="Technical review completed. All calculations verified per ISO 17025.",
        sections_to_lock=["calculations", "analysis"],
        ip_address="192.168.1.102"
    )

    print(f"  Action: {reviewer_action.action.value}")
    print(f"  User: Bob Smith (Reviewer)")
    print(f"  Comments: {reviewer_action.comments}")
    print(f"  Digital Signature: {reviewer_action.digital_signature.signature_hash[:32]}...")
    print(f"  New Stage: {workflow.current_stage.value}")
    print()

    # Step 6: Approver approval
    print("Step 6: Final Approval")
    print("-" * 80)

    approver_action = engine.approve(
        workflow_id=123,
        user_id=3001,
        comments="Report approved for management sign-off.",
        sections_to_lock=["conclusions", "recommendations"],
        ip_address="192.168.1.103"
    )

    print(f"  Action: {approver_action.action.value}")
    print(f"  User: Carol Davis (Approver)")
    print(f"  Comments: {approver_action.comments}")
    print(f"  New Stage: {workflow.current_stage.value}")
    print()

    # Step 7: Management sign-off
    print("Step 7: Management NABL Report Sign-Off")
    print("-" * 80)

    mgmt_action = engine.approve(
        workflow_id=123,
        user_id=4001,
        comments="NABL report approved for issuance. Certificate number: NABL-2025-0123.",
        ip_address="192.168.1.104"
    )

    print(f"  Action: {mgmt_action.action.value}")
    print(f"  User: David Wilson (Management)")
    print(f"  Comments: {mgmt_action.comments}")
    print(f"  Workflow Status: {workflow.status.value}")
    print(f"  Completed At: {workflow.completed_at}")
    print()

    # Step 8: Display workflow status
    print("Step 8: Workflow Status Summary")
    print("-" * 80)

    status = engine.get_workflow_status(123)
    print(f"  Workflow ID: {status['workflow_id']}")
    print(f"  Report ID: {status['report_id']}")
    print(f"  Status: {status['status']}")
    print(f"  Current Stage: {status['current_stage']}")
    print(f"  Total Approvals: {len(status['approval_history'])}")
    print(f"  Locked Sections: {len(status['locked_sections'])}")
    print()

    # Step 9: Display audit trail
    print("Step 9: Immutable Audit Trail")
    print("-" * 80)

    for i, action in enumerate(workflow.approval_history, 1):
        print(f"  {i}. {action.stage.value.upper()}")
        print(f"     User ID: {action.user_id}")
        print(f"     Action: {action.action.value}")
        print(f"     Timestamp: {action.timestamp}")
        print(f"     Signature: {action.digital_signature.signature_hash[:32]}...")
        print(f"     Comments: {action.comments}")
        print(f"     Immutable: {action.is_immutable}")
        print()

    # Step 10: Demonstrate section locking
    print("Step 10: Section Locking Status")
    print("-" * 80)

    for lock in workflow.locked_sections:
        print(f"  Section: {lock.section_id}")
        print(f"    Locked By: User {lock.locked_by}")
        print(f"    Locked At: {lock.locked_at}")
        print(f"    Stage: {lock.stage.value}")
        print(f"    Status: {'LOCKED' if lock.is_locked else 'UNLOCKED'}")
        print()

    # Additional Examples
    print("=" * 80)
    print("Additional Examples")
    print("=" * 80)
    print()

    # Example: Request Changes
    print("Example A: Request Changes Workflow")
    print("-" * 80)

    workflow2 = engine.create_workflow(
        workflow_id=124,
        report_id=457,
        approvers=approvers
    )

    # Technician completes
    engine.approve(workflow_id=124, user_id=1001, comments="Completed")

    # Reviewer requests changes
    change_request = engine.request_changes(
        workflow_id=124,
        user_id=2001,
        comments="Please update section 3.2 with additional test data."
    )

    print(f"  Action: {change_request.action.value}")
    print(f"  Returned to Stage: {workflow2.current_stage.value}")
    print(f"  Comments: {change_request.comments}")
    print()

    # Example: Delegation
    print("Example B: Approval Delegation")
    print("-" * 80)

    workflow3 = engine.create_workflow(
        workflow_id=125,
        report_id=458,
        approvers=approvers
    )

    engine.approve(workflow_id=125, user_id=1001, comments="Done")

    # Reviewer delegates to another user
    delegation = engine.delegate_approval(
        workflow_id=125,
        from_user_id=2001,
        to_user_id=2002,
        comments="Delegating approval due to scheduled leave."
    )

    print(f"  Action: {delegation.action.value}")
    print(f"  Delegated From: User {delegation.user_id}")
    print(f"  Delegated To: User 2002")
    print(f"  Comments: {delegation.comments}")
    print()

    # Example: Rejection
    print("Example C: Workflow Rejection")
    print("-" * 80)

    workflow4 = engine.create_workflow(
        workflow_id=126,
        report_id=459,
        approvers=approvers
    )

    engine.approve(workflow_id=126, user_id=1001, comments="Done")

    # Reviewer rejects
    rejection = engine.reject(
        workflow_id=126,
        user_id=2001,
        comments="Critical errors found in test methodology. Report rejected."
    )

    print(f"  Action: {rejection.action.value}")
    print(f"  Workflow Status: {workflow4.status.value}")
    print(f"  Comments: {rejection.comments}")
    print(f"  Completed At: {workflow4.completed_at}")
    print()

    print("=" * 80)
    print("Workflow Engine Demo Complete")
    print("=" * 80)


if __name__ == "__main__":
    main()
