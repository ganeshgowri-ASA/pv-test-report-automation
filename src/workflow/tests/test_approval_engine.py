"""
Unit tests for approval workflow engine.
"""

import unittest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..models import (
    Base, WorkflowDefinition, WorkflowInstance, ApprovalRecord,
    WorkflowStatus, ApprovalStatus
)
from ..approval_engine import (
    ApprovalEngine, ApprovalLevel, ApprovalStep, DigitalSignature
)
from ..workflow_states import WorkflowStateMachine


class TestApprovalEngine(unittest.TestCase):
    """Test approval workflow engine."""

    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        """Set up test session and approval engine."""
        self.session = self.Session()
        self.state_machine = WorkflowStateMachine()
        self.approval_engine = ApprovalEngine(self.session, self.state_machine)

        # Create test workflow
        definition = WorkflowDefinition(
            name="Test Workflow",
            config={},
            created_by="test_user"
        )
        self.session.add(definition)
        self.session.commit()

        self.workflow = WorkflowInstance(
            definition_id=definition.id,
            entity_type="TestReport",
            entity_id="TR-001",
            status=WorkflowStatus.PENDING,
            initiated_by="test_user"
        )
        self.session.add(self.workflow)
        self.session.commit()

    def tearDown(self):
        """Clean up test session."""
        self.session.rollback()
        self.session.close()

    def test_create_simple_approval_workflow(self):
        """Test creating a simple approval workflow."""
        steps = [
            ApprovalStep(
                step_number=1,
                step_name="Technical Review",
                approval_level=ApprovalLevel.TECHNICAL_REVIEW,
                required_role="technical_reviewer",
                auto_assign=False
            ),
            ApprovalStep(
                step_number=2,
                step_name="Manager Approval",
                approval_level=ApprovalLevel.MANAGER_APPROVAL,
                required_role="manager",
                auto_assign=False
            )
        ]

        approvals = self.approval_engine.create_approval_workflow(
            self.workflow,
            steps,
            "test_user"
        )

        # No approvers assigned since auto_assign=False
        self.assertEqual(len(approvals), 0)
        self.assertEqual(self.workflow.current_step, 1)

    def test_create_approval_workflow_with_auto_assignment(self):
        """Test creating approval workflow with automatic assignment."""
        steps = [
            ApprovalStep(
                step_number=1,
                step_name="Review",
                approval_level=ApprovalLevel.TECHNICAL_REVIEW,
                required_role="reviewer",
                auto_assign=True,
                assignment_strategy="round_robin"
            )
        ]

        approvals = self.approval_engine.create_approval_workflow(
            self.workflow,
            steps,
            "test_user"
        )

        self.assertGreater(len(approvals), 0)
        self.assertEqual(approvals[0].step_number, 1)
        self.assertEqual(approvals[0].status, ApprovalStatus.PENDING)

    def test_submit_approval_success(self):
        """Test submitting an approval decision."""
        # Create approval
        approval = ApprovalRecord(
            workflow_id=self.workflow.id,
            step_number=1,
            step_name="Review",
            assigned_to="reviewer1",
            assigned_role="reviewer",
            status=ApprovalStatus.PENDING
        )
        self.session.add(approval)
        self.session.commit()

        # Update workflow state
        self.workflow.status = WorkflowStatus.IN_PROGRESS
        self.session.commit()

        # Submit approval
        updated_approval = self.approval_engine.submit_approval(
            approval.id,
            "reviewer1",
            "approved",
            comments="Looks good"
        )

        self.assertEqual(updated_approval.status, ApprovalStatus.APPROVED)
        self.assertEqual(updated_approval.decision, "approved")
        self.assertEqual(updated_approval.comments, "Looks good")
        self.assertIsNotNone(updated_approval.reviewed_at)
        self.assertEqual(updated_approval.reviewed_by, "reviewer1")

    def test_submit_approval_rejection(self):
        """Test rejecting an approval."""
        approval = ApprovalRecord(
            workflow_id=self.workflow.id,
            step_number=1,
            step_name="Review",
            assigned_to="reviewer1",
            status=ApprovalStatus.PENDING
        )
        self.session.add(approval)
        self.workflow.status = WorkflowStatus.IN_PROGRESS
        self.session.commit()

        # Submit rejection
        updated_approval = self.approval_engine.submit_approval(
            approval.id,
            "reviewer1",
            "rejected",
            comments="Does not meet requirements"
        )

        self.assertEqual(updated_approval.status, ApprovalStatus.REJECTED)
        self.assertEqual(self.workflow.status, WorkflowStatus.REJECTED)

    def test_submit_approval_unauthorized_reviewer(self):
        """Test submitting approval by unauthorized reviewer."""
        approval = ApprovalRecord(
            workflow_id=self.workflow.id,
            step_number=1,
            step_name="Review",
            assigned_to="reviewer1",
            status=ApprovalStatus.PENDING
        )
        self.session.add(approval)
        self.session.commit()

        # Try to submit as wrong reviewer
        with self.assertRaises(ValueError) as context:
            self.approval_engine.submit_approval(
                approval.id,
                "reviewer2",  # Wrong reviewer
                "approved"
            )
        self.assertIn("not authorized", str(context.exception))

    def test_submit_approval_already_processed(self):
        """Test submitting already processed approval."""
        approval = ApprovalRecord(
            workflow_id=self.workflow.id,
            step_number=1,
            step_name="Review",
            assigned_to="reviewer1",
            status=ApprovalStatus.APPROVED  # Already approved
        )
        self.session.add(approval)
        self.session.commit()

        with self.assertRaises(ValueError) as context:
            self.approval_engine.submit_approval(
                approval.id,
                "reviewer1",
                "approved"
            )
        self.assertIn("not pending", str(context.exception))

    def test_multi_step_approval_workflow(self):
        """Test multi-step approval progression."""
        # Create two approval steps
        approval1 = ApprovalRecord(
            workflow_id=self.workflow.id,
            step_number=1,
            step_name="Technical Review",
            assigned_to="reviewer1",
            status=ApprovalStatus.PENDING,
            metadata={"requires_all": True}
        )
        approval2 = ApprovalRecord(
            workflow_id=self.workflow.id,
            step_number=2,
            step_name="Manager Approval",
            assigned_to="manager1",
            status=ApprovalStatus.PENDING,
            metadata={"requires_all": True}
        )
        self.session.add_all([approval1, approval2])
        self.workflow.status = WorkflowStatus.IN_PROGRESS
        self.workflow.current_step = 1
        self.session.commit()

        # Approve step 1
        self.approval_engine.submit_approval(
            approval1.id,
            "reviewer1",
            "approved"
        )

        # Should move to step 2
        self.session.refresh(self.workflow)
        self.assertEqual(self.workflow.current_step, 2)

        # Approve step 2
        self.approval_engine.submit_approval(
            approval2.id,
            "manager1",
            "approved"
        )

        # Should complete workflow
        self.session.refresh(self.workflow)
        self.assertEqual(self.workflow.status, WorkflowStatus.APPROVED)

    def test_parallel_approvals(self):
        """Test parallel approval handling."""
        # Create multiple approvals for same step
        approval1 = ApprovalRecord(
            workflow_id=self.workflow.id,
            step_number=1,
            step_name="Review",
            assigned_to="reviewer1",
            status=ApprovalStatus.PENDING,
            metadata={"requires_all": True, "parallel": True}
        )
        approval2 = ApprovalRecord(
            workflow_id=self.workflow.id,
            step_number=1,
            step_name="Review",
            assigned_to="reviewer2",
            status=ApprovalStatus.PENDING,
            metadata={"requires_all": True, "parallel": True}
        )
        self.session.add_all([approval1, approval2])
        self.workflow.status = WorkflowStatus.IN_PROGRESS
        self.session.commit()

        # First approval
        self.approval_engine.submit_approval(
            approval1.id,
            "reviewer1",
            "approved"
        )

        # Should still be in progress
        self.session.refresh(self.workflow)
        self.assertEqual(self.workflow.status, WorkflowStatus.IN_PROGRESS)

        # Second approval
        self.approval_engine.submit_approval(
            approval2.id,
            "reviewer2",
            "approved"
        )

        # Now should be approved
        self.session.refresh(self.workflow)
        self.assertEqual(self.workflow.status, WorkflowStatus.APPROVED)

    def test_minimum_approvers_threshold(self):
        """Test minimum approvers threshold."""
        # Create 3 approvals, need minimum 2
        approvals = []
        for i in range(3):
            approval = ApprovalRecord(
                workflow_id=self.workflow.id,
                step_number=1,
                step_name="Review",
                assigned_to=f"reviewer{i+1}",
                status=ApprovalStatus.PENDING,
                metadata={"requires_all": False, "min_approvers": 2}
            )
            approvals.append(approval)
        self.session.add_all(approvals)
        self.workflow.status = WorkflowStatus.IN_PROGRESS
        self.session.commit()

        # First approval - not enough
        self.approval_engine.submit_approval(
            approvals[0].id,
            "reviewer1",
            "approved"
        )
        self.session.refresh(self.workflow)
        self.assertEqual(self.workflow.status, WorkflowStatus.IN_PROGRESS)

        # Second approval - threshold met
        self.approval_engine.submit_approval(
            approvals[1].id,
            "reviewer2",
            "approved"
        )
        self.session.refresh(self.workflow)
        self.assertEqual(self.workflow.status, WorkflowStatus.APPROVED)

    def test_delegate_approval(self):
        """Test delegating an approval."""
        approval = ApprovalRecord(
            workflow_id=self.workflow.id,
            step_number=1,
            step_name="Review",
            assigned_to="reviewer1",
            status=ApprovalStatus.PENDING
        )
        self.session.add(approval)
        self.session.commit()

        # Delegate to another reviewer
        new_approval = self.approval_engine.delegate_approval(
            approval.id,
            "reviewer1",
            "reviewer2",
            reason="On vacation"
        )

        self.assertEqual(new_approval.assigned_to, "reviewer2")
        self.assertEqual(new_approval.delegated_from, "reviewer1")
        self.assertEqual(new_approval.status, ApprovalStatus.PENDING)

        # Original approval should be marked as delegated
        self.session.refresh(approval)
        self.assertEqual(approval.status, ApprovalStatus.DELEGATED)

    def test_delegate_approval_unauthorized(self):
        """Test delegating approval by unauthorized user."""
        approval = ApprovalRecord(
            workflow_id=self.workflow.id,
            step_number=1,
            step_name="Review",
            assigned_to="reviewer1",
            status=ApprovalStatus.PENDING
        )
        self.session.add(approval)
        self.session.commit()

        with self.assertRaises(ValueError):
            self.approval_engine.delegate_approval(
                approval.id,
                "reviewer2",  # Not assigned
                "reviewer3"
            )

    def test_escalate_approval(self):
        """Test escalating an approval."""
        approval = ApprovalRecord(
            workflow_id=self.workflow.id,
            step_number=1,
            step_name="Review",
            assigned_to="reviewer1",
            status=ApprovalStatus.PENDING,
            approval_level=1
        )
        self.session.add(approval)
        self.session.commit()

        # Escalate
        escalated = self.approval_engine.escalate_approval(
            approval.id,
            "admin1",
            reason="Urgent approval needed"
        )

        self.assertEqual(escalated.approval_level, 2)
        self.assertIn("Escalated", escalated.step_name)
        self.assertEqual(escalated.status, ApprovalStatus.PENDING)

        # Original approval should be skipped
        self.session.refresh(approval)
        self.assertEqual(approval.status, ApprovalStatus.SKIPPED)

        # Workflow should be escalated
        self.session.refresh(self.workflow)
        self.assertEqual(self.workflow.status, WorkflowStatus.ESCALATED)

    def test_digital_signature(self):
        """Test digital signature functionality."""
        approval = ApprovalRecord(
            workflow_id=self.workflow.id,
            step_number=1,
            step_name="Review",
            assigned_to="reviewer1",
            status=ApprovalStatus.PENDING
        )
        self.session.add(approval)
        self.workflow.status = WorkflowStatus.IN_PROGRESS
        self.session.commit()

        # Create digital signature
        signature = DigitalSignature(
            signer_id="reviewer1",
            signature_data="encrypted_signature_data",
            certificate_thumbprint="ABC123"
        )

        # Submit with signature
        updated_approval = self.approval_engine.submit_approval(
            approval.id,
            "reviewer1",
            "approved",
            signature=signature
        )

        self.assertIsNotNone(updated_approval.signature_hash)
        self.assertIsNotNone(updated_approval.signature_metadata)
        self.assertEqual(updated_approval.signature_metadata["signer_id"], "reviewer1")

        # Verify signature
        approval_data = {
            "approval_id": updated_approval.id,
            "workflow_id": updated_approval.workflow_id,
            "decision": updated_approval.decision,
            "reviewed_by": updated_approval.reviewed_by,
            "reviewed_at": updated_approval.reviewed_at.isoformat(),
        }
        is_valid = signature.verify_signature(approval_data, updated_approval.signature_hash)
        self.assertTrue(is_valid)

    def test_get_approval_history(self):
        """Test getting complete approval history."""
        # Create multiple approvals
        approval1 = ApprovalRecord(
            workflow_id=self.workflow.id,
            step_number=1,
            step_name="Review",
            assigned_to="reviewer1",
            status=ApprovalStatus.APPROVED,
            decision="approved",
            reviewed_by="reviewer1",
            reviewed_at=datetime.utcnow()
        )
        approval2 = ApprovalRecord(
            workflow_id=self.workflow.id,
            step_number=2,
            step_name="Approval",
            assigned_to="manager1",
            status=ApprovalStatus.PENDING
        )
        self.session.add_all([approval1, approval2])
        self.session.commit()

        history = self.approval_engine.get_approval_history(self.workflow.id)

        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["step_number"], 1)
        self.assertEqual(history[0]["status"], "approved")
        self.assertEqual(history[1]["step_number"], 2)
        self.assertEqual(history[1]["status"], "pending")

    def test_get_pending_approvals(self):
        """Test getting pending approvals."""
        # Create approvals for different users
        approval1 = ApprovalRecord(
            workflow_id=self.workflow.id,
            step_number=1,
            step_name="Review",
            assigned_to="reviewer1",
            status=ApprovalStatus.PENDING
        )
        approval2 = ApprovalRecord(
            workflow_id=self.workflow.id,
            step_number=1,
            step_name="Review",
            assigned_to="reviewer2",
            status=ApprovalStatus.PENDING
        )
        approval3 = ApprovalRecord(
            workflow_id=self.workflow.id,
            step_number=1,
            step_name="Review",
            assigned_to="reviewer1",
            status=ApprovalStatus.APPROVED  # Not pending
        )
        self.session.add_all([approval1, approval2, approval3])
        self.session.commit()

        # Get all pending
        pending = self.approval_engine.get_pending_approvals()
        self.assertEqual(len(pending), 2)

        # Get for specific user
        user_pending = self.approval_engine.get_pending_approvals(user_id="reviewer1")
        self.assertEqual(len(user_pending), 1)
        self.assertEqual(user_pending[0].assigned_to, "reviewer1")

    def test_check_overdue_approvals(self):
        """Test checking for overdue approvals."""
        # Create overdue approval
        approval1 = ApprovalRecord(
            workflow_id=self.workflow.id,
            step_number=1,
            step_name="Review",
            assigned_to="reviewer1",
            status=ApprovalStatus.PENDING,
            due_at=datetime.utcnow() - timedelta(hours=1)
        )
        # Create on-time approval
        approval2 = ApprovalRecord(
            workflow_id=self.workflow.id,
            step_number=1,
            step_name="Review",
            assigned_to="reviewer2",
            status=ApprovalStatus.PENDING,
            due_at=datetime.utcnow() + timedelta(hours=1)
        )
        self.session.add_all([approval1, approval2])
        self.session.commit()

        overdue = self.approval_engine.check_overdue_approvals()
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].assigned_to, "reviewer1")


if __name__ == "__main__":
    unittest.main()
