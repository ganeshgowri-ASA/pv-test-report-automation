"""
Tests for Approval Workflow Engine
ISO 17025 compliance verification
"""

import pytest
from datetime import datetime, timedelta
from models.approval_models import (
    ApprovalWorkflow,
    Approver,
    ApprovalStage,
    WorkflowStatus,
    ActionType,
    ApprovalRoute,
    EscalationRule
)
from workflow.approval import ApprovalWorkflowEngine
from workflow.escalation import EscalationManager


class TestApprovalWorkflowEngine:
    """Test suite for approval workflow engine"""

    @pytest.fixture
    def engine(self):
        """Create workflow engine"""
        return ApprovalWorkflowEngine()

    @pytest.fixture
    def sample_approvers(self):
        """Create sample approvers"""
        return [
            Approver(
                user_id=100,
                name="John Tech",
                email="john.tech@example.com",
                role=ApprovalStage.TECHNICIAN,
                authority_level=1
            ),
            Approver(
                user_id=200,
                name="Jane Reviewer",
                email="jane.reviewer@example.com",
                role=ApprovalStage.REVIEWER,
                authority_level=2,
                delegation_enabled=True
            ),
            Approver(
                user_id=300,
                name="Bob Approver",
                email="bob.approver@example.com",
                role=ApprovalStage.APPROVER,
                authority_level=3
            ),
            Approver(
                user_id=400,
                name="Alice Manager",
                email="alice.manager@example.com",
                role=ApprovalStage.MANAGEMENT,
                authority_level=4
            )
        ]

    def test_create_workflow(self, engine, sample_approvers):
        """Test workflow creation"""
        workflow = engine.create_workflow(
            workflow_id=1,
            report_id=123,
            approvers=sample_approvers,
            route_type=ApprovalRoute.SEQUENTIAL
        )

        assert workflow.workflow_id == 1
        assert workflow.report_id == 123
        assert workflow.current_stage == ApprovalStage.TECHNICIAN
        assert workflow.status == WorkflowStatus.PENDING
        assert len(workflow.approvers) == 4
        assert workflow.iso_17025_compliant is True

    def test_sequential_approval_flow(self, engine, sample_approvers):
        """Test sequential approval through all stages"""
        # Create workflow
        workflow = engine.create_workflow(
            workflow_id=2,
            report_id=124,
            approvers=sample_approvers
        )

        # Stage 1: Technician approval
        action1 = engine.approve(
            workflow_id=2,
            user_id=100,
            comments="Data entry completed",
            sections_to_lock=["data_entry"]
        )
        assert action1.action == ActionType.APPROVE
        assert action1.stage == ApprovalStage.TECHNICIAN
        assert workflow.current_stage == ApprovalStage.REVIEWER
        assert workflow.is_section_locked("data_entry")

        # Stage 2: Reviewer approval
        action2 = engine.approve(
            workflow_id=2,
            user_id=200,
            comments="Technical review passed",
            sections_to_lock=["technical_review"]
        )
        assert workflow.current_stage == ApprovalStage.APPROVER

        # Stage 3: Approver approval
        action3 = engine.approve(
            workflow_id=2,
            user_id=300,
            comments="Approved for release"
        )
        assert workflow.current_stage == ApprovalStage.MANAGEMENT

        # Stage 4: Management approval
        action4 = engine.approve(
            workflow_id=2,
            user_id=400,
            comments="NABL report approved"
        )
        assert workflow.status == WorkflowStatus.APPROVED
        assert workflow.completed_at is not None

    def test_rejection_flow(self, engine, sample_approvers):
        """Test rejection at reviewer stage"""
        workflow = engine.create_workflow(
            workflow_id=3,
            report_id=125,
            approvers=sample_approvers
        )

        # Technician approval
        engine.approve(workflow_id=3, user_id=100, comments="Completed")

        # Reviewer rejects
        rejection = engine.reject(
            workflow_id=3,
            user_id=200,
            comments="Data inconsistencies found"
        )

        assert rejection.action == ActionType.REJECT
        assert workflow.status == WorkflowStatus.REJECTED
        assert workflow.completed_at is not None

    def test_request_changes(self, engine, sample_approvers):
        """Test requesting changes"""
        workflow = engine.create_workflow(
            workflow_id=4,
            report_id=126,
            approvers=sample_approvers
        )

        # Technician approval
        engine.approve(workflow_id=4, user_id=100, comments="Done")
        assert workflow.current_stage == ApprovalStage.REVIEWER

        # Reviewer requests changes
        change_request = engine.request_changes(
            workflow_id=4,
            user_id=200,
            comments="Please update section 3.2"
        )

        assert change_request.action == ActionType.REQUEST_CHANGES
        assert workflow.current_stage == ApprovalStage.TECHNICIAN

    def test_delegation(self, engine, sample_approvers):
        """Test approval delegation"""
        workflow = engine.create_workflow(
            workflow_id=5,
            report_id=127,
            approvers=sample_approvers
        )

        # Technician approval
        engine.approve(workflow_id=5, user_id=100, comments="Done")

        # Reviewer delegates to another user
        delegation = engine.delegate_approval(
            workflow_id=5,
            from_user_id=200,
            to_user_id=250,
            comments="Delegating due to leave"
        )

        assert delegation.action == ActionType.DELEGATE
        # Check delegated approver added
        delegated = next(
            (a for a in workflow.approvers if a.user_id == 250),
            None
        )
        assert delegated is not None
        assert delegated.delegated_from == 200

    def test_digital_signatures(self, engine, sample_approvers):
        """Test digital signature generation"""
        workflow = engine.create_workflow(
            workflow_id=6,
            report_id=128,
            approvers=sample_approvers
        )

        action = engine.approve(
            workflow_id=6,
            user_id=100,
            comments="Approved",
            ip_address="192.168.1.100"
        )

        # Verify signature exists
        assert action.digital_signature is not None
        assert action.digital_signature.signature_hash != ""
        assert action.digital_signature.signing_algorithm == "SHA256"
        assert action.digital_signature.ip_address == "192.168.1.100"
        assert action.is_immutable is True

    def test_section_locking(self, engine, sample_approvers):
        """Test section locking after approval"""
        workflow = engine.create_workflow(
            workflow_id=7,
            report_id=129,
            approvers=sample_approvers
        )

        # Lock multiple sections
        engine.approve(
            workflow_id=7,
            user_id=100,
            comments="Done",
            sections_to_lock=["section_1", "section_2", "section_3"]
        )

        assert workflow.is_section_locked("section_1")
        assert workflow.is_section_locked("section_2")
        assert workflow.is_section_locked("section_3")
        assert not workflow.is_section_locked("section_4")

        # Verify lock details
        lock = workflow.locked_sections[0]
        assert lock.locked_by == 100
        assert lock.stage == ApprovalStage.TECHNICIAN

    def test_unauthorized_approval(self, engine, sample_approvers):
        """Test that unauthorized users cannot approve"""
        workflow = engine.create_workflow(
            workflow_id=8,
            report_id=130,
            approvers=sample_approvers
        )

        # Try to approve with wrong user for current stage
        with pytest.raises(PermissionError):
            engine.approve(
                workflow_id=8,
                user_id=999,  # User not in approvers list
                comments="Unauthorized"
            )

    def test_audit_trail(self, engine, sample_approvers):
        """Test immutable audit trail"""
        workflow = engine.create_workflow(
            workflow_id=9,
            report_id=131,
            approvers=sample_approvers
        )

        # Perform multiple actions
        engine.approve(workflow_id=9, user_id=100, comments="Action 1")
        engine.approve(workflow_id=9, user_id=200, comments="Action 2")
        engine.approve(workflow_id=9, user_id=300, comments="Action 3")

        # Verify audit trail
        assert len(workflow.approval_history) == 3
        assert all(action.is_immutable for action in workflow.approval_history)

        # Verify chronological order
        timestamps = [action.timestamp for action in workflow.approval_history]
        assert timestamps == sorted(timestamps)

    def test_workflow_status(self, engine, sample_approvers):
        """Test workflow status retrieval"""
        workflow = engine.create_workflow(
            workflow_id=10,
            report_id=132,
            approvers=sample_approvers
        )

        engine.approve(workflow_id=10, user_id=100, comments="Done")

        status = engine.get_workflow_status(10)

        assert status["workflow_id"] == 10
        assert status["report_id"] == 132
        assert status["current_stage"] == "reviewer"
        assert len(status["approvers"]) == 4
        assert len(status["approval_history"]) == 1


class TestEscalationManager:
    """Test suite for escalation manager"""

    @pytest.fixture
    def manager(self):
        """Create escalation manager"""
        return EscalationManager()

    def test_create_escalation_rule(self, manager):
        """Test escalation rule creation"""
        rule = manager.create_escalation_rule(
            from_stage=ApprovalStage.REVIEWER,
            timeout_hours=48,
            notification_emails=["manager@example.com"]
        )

        assert rule.from_stage == ApprovalStage.REVIEWER
        assert rule.timeout_hours == 48
        assert rule.to_stage == ApprovalStage.APPROVER
        assert "manager@example.com" in rule.notification_emails

    def test_check_workflow_escalation(self, manager):
        """Test escalation timeout check"""
        # Create workflow with escalation rule
        escalation_rule = manager.create_escalation_rule(
            from_stage=ApprovalStage.REVIEWER,
            timeout_hours=24
        )

        workflow = ApprovalWorkflow(
            workflow_id=1,
            report_id=100,
            current_stage=ApprovalStage.REVIEWER,
            status=WorkflowStatus.IN_PROGRESS,
            escalation_rules=[escalation_rule],
            updated_at=datetime.utcnow() - timedelta(hours=25)  # 25 hours ago
        )

        # Check escalation
        escalation = manager.check_workflow_escalation(workflow)

        assert escalation is not None
        assert escalation["workflow_id"] == 1
        assert escalation["current_stage"] == "reviewer"
        assert escalation["time_exceeded_by"] > 0

    def test_escalation_warnings(self, manager):
        """Test escalation warnings"""
        escalation_rule = manager.create_escalation_rule(
            from_stage=ApprovalStage.REVIEWER,
            timeout_hours=24,
            notification_emails=["admin@example.com"]
        )

        workflow = ApprovalWorkflow(
            workflow_id=2,
            report_id=101,
            current_stage=ApprovalStage.REVIEWER,
            status=WorkflowStatus.IN_PROGRESS,
            escalation_rules=[escalation_rule],
            updated_at=datetime.utcnow() - timedelta(hours=23)  # 23 hours ago
        )

        # Check for warning
        warning = manager.get_escalation_warnings(workflow, warning_threshold_hours=2)

        assert warning is not None
        assert warning["workflow_id"] == 2
        assert warning["hours_remaining"] < 2
        assert warning["warning_level"] in ["high", "medium"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
