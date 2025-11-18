"""
Unit tests for workflow database models.
"""

import unittest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..models import (
    Base, WorkflowDefinition, WorkflowInstance, ApprovalRecord,
    StateTransition, NotificationLog, NotificationPreference,
    NotificationSubscription, WorkflowStatus, ApprovalStatus,
    NotificationStatus, NotificationChannel
)


class TestWorkflowModels(unittest.TestCase):
    """Test workflow database models."""

    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        """Set up test session."""
        self.session = self.Session()

    def tearDown(self):
        """Clean up test session."""
        self.session.rollback()
        self.session.close()

    def test_workflow_definition_creation(self):
        """Test creating a workflow definition."""
        definition = WorkflowDefinition(
            name="Test Workflow",
            description="Test workflow definition",
            version="1.0.0",
            category="test",
            config={
                "steps": [
                    {"step": 1, "name": "Review", "role": "reviewer"},
                    {"step": 2, "name": "Approve", "role": "approver"}
                ]
            },
            created_by="test_user"
        )
        self.session.add(definition)
        self.session.commit()

        self.assertIsNotNone(definition.id)
        self.assertEqual(definition.name, "Test Workflow")
        self.assertTrue(definition.is_active)
        self.assertTrue(definition.is_iso_compliant)

    def test_workflow_instance_creation(self):
        """Test creating a workflow instance."""
        # Create definition first
        definition = WorkflowDefinition(
            name="Test Workflow",
            config={},
            created_by="test_user"
        )
        self.session.add(definition)
        self.session.commit()

        # Create instance
        instance = WorkflowInstance(
            definition_id=definition.id,
            entity_type="TestReport",
            entity_id="TR-001",
            reference_number="WF-001",
            status=WorkflowStatus.DRAFT,
            initiated_by="test_user"
        )
        self.session.add(instance)
        self.session.commit()

        self.assertIsNotNone(instance.id)
        self.assertEqual(instance.status, WorkflowStatus.DRAFT)
        self.assertEqual(instance.current_step, 0)
        self.assertIsNotNone(instance.created_at)

    def test_workflow_instance_is_overdue(self):
        """Test workflow overdue detection."""
        definition = WorkflowDefinition(
            name="Test Workflow",
            config={},
            created_by="test_user"
        )
        self.session.add(definition)
        self.session.commit()

        # Not overdue - no due date
        instance1 = WorkflowInstance(
            definition_id=definition.id,
            entity_type="TestReport",
            entity_id="TR-001",
            status=WorkflowStatus.PENDING,
            initiated_by="test_user"
        )
        self.assertFalse(instance1.is_overdue)

        # Not overdue - future due date
        instance2 = WorkflowInstance(
            definition_id=definition.id,
            entity_type="TestReport",
            entity_id="TR-002",
            status=WorkflowStatus.PENDING,
            due_date=datetime.utcnow() + timedelta(days=1),
            initiated_by="test_user"
        )
        self.assertFalse(instance2.is_overdue)

        # Overdue - past due date
        instance3 = WorkflowInstance(
            definition_id=definition.id,
            entity_type="TestReport",
            entity_id="TR-003",
            status=WorkflowStatus.PENDING,
            due_date=datetime.utcnow() - timedelta(days=1),
            initiated_by="test_user"
        )
        self.assertTrue(instance3.is_overdue)

        # Not overdue - completed
        instance4 = WorkflowInstance(
            definition_id=definition.id,
            entity_type="TestReport",
            entity_id="TR-004",
            status=WorkflowStatus.COMPLETED,
            due_date=datetime.utcnow() - timedelta(days=1),
            initiated_by="test_user"
        )
        self.assertFalse(instance4.is_overdue)

    def test_approval_record_creation(self):
        """Test creating an approval record."""
        # Create workflow instance
        definition = WorkflowDefinition(
            name="Test Workflow",
            config={},
            created_by="test_user"
        )
        instance = WorkflowInstance(
            definition_id=definition.id,
            entity_type="TestReport",
            entity_id="TR-001",
            initiated_by="test_user"
        )
        self.session.add_all([definition, instance])
        self.session.commit()

        # Create approval
        approval = ApprovalRecord(
            workflow_id=instance.id,
            step_number=1,
            step_name="Technical Review",
            approval_level=1,
            assigned_to="reviewer1",
            assigned_role="technical_reviewer",
            status=ApprovalStatus.PENDING
        )
        self.session.add(approval)
        self.session.commit()

        self.assertIsNotNone(approval.id)
        self.assertEqual(approval.status, ApprovalStatus.PENDING)
        self.assertIsNotNone(approval.assigned_at)

    def test_approval_record_is_overdue(self):
        """Test approval overdue detection."""
        definition = WorkflowDefinition(
            name="Test Workflow",
            config={},
            created_by="test_user"
        )
        instance = WorkflowInstance(
            definition_id=definition.id,
            entity_type="TestReport",
            entity_id="TR-001",
            initiated_by="test_user"
        )
        self.session.add_all([definition, instance])
        self.session.commit()

        # Overdue approval
        approval1 = ApprovalRecord(
            workflow_id=instance.id,
            step_number=1,
            step_name="Review",
            assigned_to="reviewer1",
            status=ApprovalStatus.PENDING,
            due_at=datetime.utcnow() - timedelta(hours=1)
        )
        self.assertTrue(approval1.is_overdue)

        # Not overdue - future due date
        approval2 = ApprovalRecord(
            workflow_id=instance.id,
            step_number=1,
            step_name="Review",
            assigned_to="reviewer1",
            status=ApprovalStatus.PENDING,
            due_at=datetime.utcnow() + timedelta(hours=1)
        )
        self.assertFalse(approval2.is_overdue)

        # Not overdue - approved
        approval3 = ApprovalRecord(
            workflow_id=instance.id,
            step_number=1,
            step_name="Review",
            assigned_to="reviewer1",
            status=ApprovalStatus.APPROVED,
            due_at=datetime.utcnow() - timedelta(hours=1)
        )
        self.assertFalse(approval3.is_overdue)

    def test_state_transition_creation(self):
        """Test creating a state transition."""
        definition = WorkflowDefinition(
            name="Test Workflow",
            config={},
            created_by="test_user"
        )
        instance = WorkflowInstance(
            definition_id=definition.id,
            entity_type="TestReport",
            entity_id="TR-001",
            initiated_by="test_user"
        )
        self.session.add_all([definition, instance])
        self.session.commit()

        transition = StateTransition(
            workflow_id=instance.id,
            from_state="draft",
            to_state="pending",
            event="submit",
            triggered_by="test_user",
            reason="Initial submission"
        )
        self.session.add(transition)
        self.session.commit()

        self.assertIsNotNone(transition.id)
        self.assertEqual(transition.from_state, "draft")
        self.assertEqual(transition.to_state, "pending")
        self.assertIsNotNone(transition.transitioned_at)

    def test_notification_log_creation(self):
        """Test creating a notification log."""
        definition = WorkflowDefinition(
            name="Test Workflow",
            config={},
            created_by="test_user"
        )
        instance = WorkflowInstance(
            definition_id=definition.id,
            entity_type="TestReport",
            entity_id="TR-001",
            initiated_by="test_user"
        )
        self.session.add_all([definition, instance])
        self.session.commit()

        notification = NotificationLog(
            workflow_id=instance.id,
            channel=NotificationChannel.EMAIL,
            recipient="user@example.com",
            subject="Test Notification",
            message="This is a test",
            status=NotificationStatus.PENDING
        )
        self.session.add(notification)
        self.session.commit()

        self.assertIsNotNone(notification.id)
        self.assertEqual(notification.channel, NotificationChannel.EMAIL)
        self.assertEqual(notification.status, NotificationStatus.PENDING)
        self.assertEqual(notification.retry_count, 0)

    def test_notification_preference_creation(self):
        """Test creating notification preferences."""
        pref = NotificationPreference(
            user_id="user123",
            channel=NotificationChannel.EMAIL,
            enabled=True,
            contact_info="user@example.com",
            quiet_hours_start="22:00",
            quiet_hours_end="08:00",
            timezone="America/New_York"
        )
        self.session.add(pref)
        self.session.commit()

        self.assertIsNotNone(pref.id)
        self.assertTrue(pref.enabled)
        self.assertEqual(pref.channel, NotificationChannel.EMAIL)

    def test_notification_subscription_creation(self):
        """Test creating a notification subscription."""
        definition = WorkflowDefinition(
            name="Test Workflow",
            config={},
            created_by="test_user"
        )
        self.session.add(definition)
        self.session.commit()

        subscription = NotificationSubscription(
            user_id="user123",
            workflow_definition_id=definition.id,
            event_types=["approval_requested", "approval_approved"],
            channels=["email", "slack"],
            is_active=True
        )
        self.session.add(subscription)
        self.session.commit()

        self.assertIsNotNone(subscription.id)
        self.assertTrue(subscription.is_active)
        self.assertIn("approval_requested", subscription.event_types)

    def test_relationships(self):
        """Test model relationships."""
        # Create workflow with all related records
        definition = WorkflowDefinition(
            name="Test Workflow",
            config={},
            created_by="test_user"
        )
        self.session.add(definition)
        self.session.commit()

        instance = WorkflowInstance(
            definition_id=definition.id,
            entity_type="TestReport",
            entity_id="TR-001",
            initiated_by="test_user"
        )
        self.session.add(instance)
        self.session.commit()

        approval = ApprovalRecord(
            workflow_id=instance.id,
            step_number=1,
            step_name="Review",
            assigned_to="reviewer1"
        )
        transition = StateTransition(
            workflow_id=instance.id,
            to_state="pending",
            triggered_by="test_user"
        )
        notification = NotificationLog(
            workflow_id=instance.id,
            channel=NotificationChannel.EMAIL,
            recipient="user@example.com",
            message="Test"
        )
        self.session.add_all([approval, transition, notification])
        self.session.commit()

        # Test relationships
        self.assertEqual(len(instance.approvals), 1)
        self.assertEqual(len(instance.state_history), 1)
        self.assertEqual(len(instance.notifications), 1)
        self.assertEqual(instance.definition.id, definition.id)


if __name__ == "__main__":
    unittest.main()
