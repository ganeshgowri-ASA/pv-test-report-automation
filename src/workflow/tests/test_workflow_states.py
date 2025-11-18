"""
Unit tests for workflow state machine.
"""

import unittest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..models import (
    Base, WorkflowDefinition, WorkflowInstance, WorkflowStatus, StateTransition
)
from ..workflow_states import (
    WorkflowStateMachine, WorkflowEvent, StateTransitionRule
)


class TestWorkflowStateMachine(unittest.TestCase):
    """Test workflow state machine."""

    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        """Set up test session and state machine."""
        self.session = self.Session()
        self.state_machine = WorkflowStateMachine()

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
            status=WorkflowStatus.DRAFT,
            initiated_by="test_user"
        )
        self.session.add(self.workflow)
        self.session.commit()

    def tearDown(self):
        """Clean up test session."""
        self.session.rollback()
        self.session.close()

    def test_valid_transition_draft_to_pending(self):
        """Test valid transition from draft to pending."""
        can_transition, error = self.state_machine.can_transition(
            self.workflow,
            WorkflowEvent.SUBMIT
        )
        self.assertTrue(can_transition)
        self.assertIsNone(error)

    def test_invalid_transition_draft_to_approved(self):
        """Test invalid transition (no direct path)."""
        can_transition, error = self.state_machine.can_transition(
            self.workflow,
            WorkflowEvent.APPROVE
        )
        self.assertFalse(can_transition)
        self.assertIsNotNone(error)

    def test_transition_execution(self):
        """Test executing a state transition."""
        result = self.state_machine.transition(
            self.workflow,
            WorkflowEvent.SUBMIT,
            context={"user_id": "test_user"},
            session=self.session
        )

        self.assertTrue(result)
        self.assertEqual(self.workflow.status, WorkflowStatus.PENDING)

        # Check state transition was logged
        transitions = self.session.query(StateTransition).filter_by(
            workflow_id=self.workflow.id
        ).all()
        self.assertEqual(len(transitions), 1)
        self.assertEqual(transitions[0].from_state, WorkflowStatus.DRAFT.value)
        self.assertEqual(transitions[0].to_state, WorkflowStatus.PENDING.value)

    def test_transition_with_required_comment(self):
        """Test transition requiring a comment."""
        self.workflow.status = WorkflowStatus.IN_PROGRESS

        # Without comment - should fail
        with self.assertRaises(ValueError):
            self.state_machine.transition(
                self.workflow,
                WorkflowEvent.REJECT,
                context={"user_id": "approver1"},
                session=self.session
            )

        # With comment - should succeed
        result = self.state_machine.transition(
            self.workflow,
            WorkflowEvent.REJECT,
            context={
                "user_id": "approver1",
                "reason": "Does not meet requirements"
            },
            session=self.session
        )
        self.assertTrue(result)
        self.assertEqual(self.workflow.status, WorkflowStatus.REJECTED)

    def test_transition_with_role_check(self):
        """Test transition with role-based access control."""
        self.workflow.status = WorkflowStatus.PENDING

        # Wrong role - should fail
        can_transition, error = self.state_machine.can_transition(
            self.workflow,
            WorkflowEvent.START_REVIEW,
            context={"user_role": "viewer"}
        )
        self.assertFalse(can_transition)

        # Correct role - should succeed
        can_transition, error = self.state_machine.can_transition(
            self.workflow,
            WorkflowEvent.START_REVIEW,
            context={"user_role": "reviewer"}
        )
        self.assertTrue(can_transition)

    def test_transition_with_approval_required(self):
        """Test transition requiring approval."""
        self.workflow.status = WorkflowStatus.IN_PROGRESS

        # Without approval - should fail
        can_transition, error = self.state_machine.can_transition(
            self.workflow,
            WorkflowEvent.APPROVE,
            context={"user_role": "approver"}
        )
        self.assertFalse(can_transition)
        self.assertIn("approval", error.lower())

        # With approval - should succeed
        can_transition, error = self.state_machine.can_transition(
            self.workflow,
            WorkflowEvent.APPROVE,
            context={"user_role": "approver", "approved_by": "approver1"}
        )
        self.assertTrue(can_transition)

    def test_complete_workflow_path(self):
        """Test complete workflow from draft to completed."""
        # Draft -> Pending
        self.state_machine.transition(
            self.workflow,
            WorkflowEvent.SUBMIT,
            context={"user_id": "user1"},
            session=self.session
        )
        self.assertEqual(self.workflow.status, WorkflowStatus.PENDING)

        # Pending -> In Progress
        self.state_machine.transition(
            self.workflow,
            WorkflowEvent.START_REVIEW,
            context={"user_id": "reviewer1", "user_role": "reviewer"},
            session=self.session
        )
        self.assertEqual(self.workflow.status, WorkflowStatus.IN_PROGRESS)
        self.assertIsNotNone(self.workflow.started_at)

        # In Progress -> Approved
        self.state_machine.transition(
            self.workflow,
            WorkflowEvent.APPROVE,
            context={
                "user_id": "approver1",
                "user_role": "approver",
                "approved_by": "approver1"
            },
            session=self.session
        )
        self.assertEqual(self.workflow.status, WorkflowStatus.APPROVED)

        # Approved -> Completed
        self.state_machine.transition(
            self.workflow,
            WorkflowEvent.COMPLETE,
            context={"user_id": "system", "user_role": "system"},
            session=self.session
        )
        self.assertEqual(self.workflow.status, WorkflowStatus.COMPLETED)
        self.assertIsNotNone(self.workflow.completed_at)

        # Verify all transitions were logged
        transitions = self.session.query(StateTransition).filter_by(
            workflow_id=self.workflow.id
        ).order_by(StateTransition.id).all()
        self.assertEqual(len(transitions), 4)

    def test_rejection_and_resubmission(self):
        """Test rejection and resubmission flow."""
        # Move to in_progress
        self.workflow.status = WorkflowStatus.IN_PROGRESS

        # Reject
        self.state_machine.transition(
            self.workflow,
            WorkflowEvent.REJECT,
            context={
                "user_id": "approver1",
                "user_role": "approver",
                "reason": "Missing information"
            },
            session=self.session
        )
        self.assertEqual(self.workflow.status, WorkflowStatus.REJECTED)

        # Resubmit
        self.state_machine.transition(
            self.workflow,
            WorkflowEvent.RESUBMIT,
            context={"user_id": "user1"},
            session=self.session
        )
        self.assertEqual(self.workflow.status, WorkflowStatus.DRAFT)

    def test_escalation(self):
        """Test workflow escalation."""
        self.workflow.status = WorkflowStatus.PENDING

        self.state_machine.transition(
            self.workflow,
            WorkflowEvent.ESCALATE,
            context={
                "user_id": "admin1",
                "user_role": "admin",
                "reason": "Urgent approval needed"
            },
            session=self.session
        )

        self.assertEqual(self.workflow.status, WorkflowStatus.ESCALATED)
        self.assertIsNotNone(self.workflow.escalated_at)
        self.assertEqual(self.workflow.escalation_level, 1)

    def test_get_available_events(self):
        """Test getting available events for current state."""
        # Draft state
        events = self.state_machine.get_available_events(self.workflow)
        self.assertIn(WorkflowEvent.SUBMIT, events)
        self.assertIn(WorkflowEvent.CANCEL, events)

        # Pending state
        self.workflow.status = WorkflowStatus.PENDING
        events = self.state_machine.get_available_events(self.workflow)
        self.assertIn(WorkflowEvent.START_REVIEW, events)
        self.assertIn(WorkflowEvent.CANCEL, events)
        self.assertIn(WorkflowEvent.ESCALATE, events)

    def test_custom_transitions(self):
        """Test adding custom transition rules."""
        custom_rule = StateTransitionRule(
            from_state=WorkflowStatus.APPROVED,
            to_state=WorkflowStatus.PENDING,
            event=WorkflowEvent.REQUEST_CHANGES,
            requires_comment=True,
            allowed_roles={"quality_manager"}
        )

        custom_sm = WorkflowStateMachine(custom_transitions=[custom_rule])

        # Test custom transition
        self.workflow.status = WorkflowStatus.APPROVED
        can_transition, error = custom_sm.can_transition(
            self.workflow,
            WorkflowEvent.REQUEST_CHANGES,
            context={"user_role": "quality_manager", "reason": "Need corrections"}
        )
        self.assertTrue(can_transition)

    def test_transition_hooks(self):
        """Test registering and executing transition hooks."""
        hook_calls = []

        def before_hook(workflow, old_state, new_state, context):
            hook_calls.append(("before", old_state, new_state))

        def after_hook(workflow, old_state, new_state, context):
            hook_calls.append(("after", old_state, new_state))

        def on_enter_hook(workflow, old_state, new_state, context):
            hook_calls.append(("on_enter", new_state))

        self.state_machine.register_hook("before_transition", before_hook)
        self.state_machine.register_hook("after_transition", after_hook)
        self.state_machine.register_hook("on_enter", on_enter_hook, state="pending")

        self.state_machine.transition(
            self.workflow,
            WorkflowEvent.SUBMIT,
            context={"user_id": "test_user"},
            session=self.session
        )

        self.assertEqual(len(hook_calls), 3)
        self.assertEqual(hook_calls[0][0], "before")
        self.assertEqual(hook_calls[1][0], "on_enter")
        self.assertEqual(hook_calls[2][0], "after")

    def test_validate_workflow_path(self):
        """Test finding valid path between states."""
        # Find path from draft to completed
        path = self.state_machine.validate_workflow_path(
            WorkflowStatus.DRAFT,
            WorkflowStatus.COMPLETED
        )
        self.assertIsNotNone(path)
        self.assertTrue(len(path) > 0)

        # No valid path (in realistic scenario)
        # For this test, all states should have some path due to default transitions
        path = self.state_machine.validate_workflow_path(
            WorkflowStatus.DRAFT,
            WorkflowStatus.COMPLETED,
            max_depth=2  # Too short to reach
        )
        self.assertIsNone(path)

    def test_get_transition_graph(self):
        """Test getting complete transition graph."""
        graph = self.state_machine.get_transition_graph()

        self.assertIsInstance(graph, dict)
        self.assertIn(WorkflowStatus.DRAFT.value, graph)
        self.assertIn(WorkflowStatus.PENDING.value, graph)

        # Check draft transitions
        draft_transitions = graph[WorkflowStatus.DRAFT.value]
        self.assertTrue(any(t["event"] == WorkflowEvent.SUBMIT.value for t in draft_transitions))

    def test_conditional_transition(self):
        """Test transition with custom condition."""
        def approval_count_condition(workflow, context):
            # Custom condition: check if enough approvals
            return context.get("approval_count", 0) >= 2

        custom_rule = StateTransitionRule(
            from_state=WorkflowStatus.IN_PROGRESS,
            to_state=WorkflowStatus.APPROVED,
            event=WorkflowEvent.APPROVE,
            condition=approval_count_condition
        )

        custom_sm = WorkflowStateMachine(custom_transitions=[custom_rule])
        self.workflow.status = WorkflowStatus.IN_PROGRESS

        # Not enough approvals
        can_transition, error = custom_sm.can_transition(
            self.workflow,
            WorkflowEvent.APPROVE,
            context={"approval_count": 1}
        )
        self.assertFalse(can_transition)

        # Enough approvals
        can_transition, error = custom_sm.can_transition(
            self.workflow,
            WorkflowEvent.APPROVE,
            context={"approval_count": 2}
        )
        self.assertTrue(can_transition)


if __name__ == "__main__":
    unittest.main()
