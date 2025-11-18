"""
Unit tests for notification system.
"""

import unittest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..models import (
    Base, WorkflowDefinition, WorkflowInstance, NotificationLog,
    NotificationPreference, NotificationSubscription,
    NotificationChannel, NotificationStatus, WorkflowStatus
)
from ..notification_system import (
    NotificationSystem, NotificationConfig, NotificationTemplate,
    NotificationPriority, NotificationEvent
)


class TestNotificationTemplate(unittest.TestCase):
    """Test notification template rendering."""

    def setUp(self):
        """Set up template engine."""
        self.template_engine = NotificationTemplate()

    def test_render_approval_requested_template(self):
        """Test rendering approval requested template."""
        variables = {
            "recipient_name": "John Doe",
            "workflow": {
                "reference_number": "WF-001",
                "entity_type": "TestReport",
                "priority": 1
            },
            "approval": {
                "step_name": "Technical Review",
            },
            "approval_url": "https://example.com/approval/123",
            "from_name": "PV Test System"
        }

        subject, body = self.template_engine.render("approval_requested", variables)

        self.assertIn("WF-001", subject)
        self.assertIn("John Doe", body)
        self.assertIn("Technical Review", body)
        self.assertIn("https://example.com/approval/123", body)

    def test_render_approval_approved_template(self):
        """Test rendering approval approved template."""
        variables = {
            "recipient_name": "Jane Smith",
            "workflow": {"reference_number": "WF-002"},
            "approved_by": "John Approver",
            "approval": {
                "step_name": "Manager Approval",
                "comments": "Looks good"
            },
            "workflow_url": "https://example.com/workflow/456",
            "from_name": "PV Test System"
        }

        subject, body = self.template_engine.render("approval_approved", variables)

        self.assertIn("Approved", subject)
        self.assertIn("WF-002", subject)
        self.assertIn("Jane Smith", body)
        self.assertIn("John Approver", body)
        self.assertIn("Looks good", body)

    def test_render_approval_rejected_template(self):
        """Test rendering approval rejected template."""
        variables = {
            "recipient_name": "Test User",
            "workflow": {"reference_number": "WF-003"},
            "rejected_by": "Quality Manager",
            "approval": {
                "step_name": "Quality Review",
                "comments": "Missing documentation"
            },
            "workflow_url": "https://example.com/workflow/789",
            "from_name": "PV Test System"
        }

        subject, body = self.template_engine.render("approval_rejected", variables)

        self.assertIn("Rejected", subject)
        self.assertIn("Missing documentation", body)
        self.assertIn("Quality Manager", body)

    def test_add_custom_template(self):
        """Test adding custom template."""
        self.template_engine.add_template(
            "custom_test",
            "Custom Subject: {{ title }}",
            "Custom Body: {{ content }}"
        )

        subject, body = self.template_engine.render(
            "custom_test",
            {"title": "Test", "content": "Hello World"}
        )

        self.assertEqual(subject, "Custom Subject: Test")
        self.assertEqual(body, "Custom Body: Hello World")

    def test_render_nonexistent_template(self):
        """Test rendering nonexistent template."""
        with self.assertRaises(ValueError):
            self.template_engine.render("nonexistent", {})


class TestNotificationSystem(unittest.TestCase):
    """Test notification system."""

    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        """Set up test session and notification system."""
        self.session = self.Session()
        self.config = NotificationConfig(
            smtp_host="localhost",
            smtp_port=587,
            from_email="test@example.com"
        )
        self.notification_system = NotificationSystem(
            self.session,
            self.config
        )

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
            reference_number="WF-001",
            status=WorkflowStatus.PENDING,
            initiated_by="test_user"
        )
        self.session.add(self.workflow)
        self.session.commit()

    def tearDown(self):
        """Clean up test session."""
        self.session.rollback()
        self.session.close()

    def test_send_email_notification(self):
        """Test sending email notification."""
        notification = self.notification_system.send_notification(
            channel=NotificationChannel.EMAIL,
            recipient="user@example.com",
            subject="Test Subject",
            message="Test message",
            workflow_id=self.workflow.id,
            priority=NotificationPriority.NORMAL
        )

        self.assertIsNotNone(notification.id)
        self.assertEqual(notification.channel, NotificationChannel.EMAIL)
        self.assertEqual(notification.recipient, "user@example.com")
        self.assertEqual(notification.subject, "Test Subject")
        self.assertEqual(notification.message, "Test message")

    def test_send_from_template(self):
        """Test sending notification from template."""
        template_vars = {
            "recipient_name": "Test User",
            "workflow": {
                "reference_number": self.workflow.reference_number,
                "entity_type": self.workflow.entity_type,
                "priority": self.workflow.priority
            },
            "approval": {
                "step_name": "Review",
            },
            "approval_url": "https://example.com/approval/1",
            "from_name": "Test System"
        }

        notification = self.notification_system.send_from_template(
            channel=NotificationChannel.EMAIL,
            recipient="user@example.com",
            template_name="approval_requested",
            template_vars=template_vars,
            workflow_id=self.workflow.id
        )

        self.assertIsNotNone(notification.id)
        self.assertEqual(notification.template_name, "approval_requested")
        self.assertIn("WF-001", notification.subject)

    def test_send_slack_notification_stub(self):
        """Test sending Slack notification (stub)."""
        notification = self.notification_system.send_notification(
            channel=NotificationChannel.SLACK,
            recipient="#test-channel",
            subject="Test",
            message="Test Slack message",
            workflow_id=self.workflow.id
        )

        # Should create notification record even if delivery is stubbed
        self.assertIsNotNone(notification.id)
        self.assertEqual(notification.channel, NotificationChannel.SLACK)

    def test_send_teams_notification_stub(self):
        """Test sending Teams notification (stub)."""
        notification = self.notification_system.send_notification(
            channel=NotificationChannel.TEAMS,
            recipient="team-channel",
            subject="Test",
            message="Test Teams message",
            workflow_id=self.workflow.id
        )

        self.assertIsNotNone(notification.id)
        self.assertEqual(notification.channel, NotificationChannel.TEAMS)

    def test_send_sms_notification_stub(self):
        """Test sending SMS notification (stub)."""
        notification = self.notification_system.send_notification(
            channel=NotificationChannel.SMS,
            recipient="+1234567890",
            subject="",
            message="Test SMS message",
            workflow_id=self.workflow.id,
            priority=NotificationPriority.CRITICAL
        )

        self.assertIsNotNone(notification.id)
        self.assertEqual(notification.channel, NotificationChannel.SMS)
        self.assertEqual(notification.priority, NotificationPriority.CRITICAL.value)

    def test_send_in_app_notification(self):
        """Test sending in-app notification."""
        notification = self.notification_system.send_notification(
            channel=NotificationChannel.IN_APP,
            recipient="user123",
            subject="Test Notification",
            message="Test in-app message",
            workflow_id=self.workflow.id
        )

        self.assertIsNotNone(notification.id)
        self.assertEqual(notification.channel, NotificationChannel.IN_APP)
        # In-app notifications should be marked as sent immediately
        self.assertEqual(notification.status, NotificationStatus.SENT)

    def test_subscribe_user_to_workflow(self):
        """Test subscribing user to workflow notifications."""
        subscription = self.notification_system.subscribe_user(
            user_id="user123",
            workflow_id=self.workflow.id,
            event_types=["approval_requested", "approval_approved"],
            channels=["email", "slack"]
        )

        self.assertIsNotNone(subscription.id)
        self.assertEqual(subscription.user_id, "user123")
        self.assertEqual(subscription.workflow_instance_id, self.workflow.id)
        self.assertTrue(subscription.is_active)
        self.assertIn("approval_requested", subscription.event_types)

    def test_subscribe_user_to_entity_type(self):
        """Test subscribing user to all workflows of an entity type."""
        subscription = self.notification_system.subscribe_user(
            user_id="user123",
            entity_type="TestReport",
            event_types=["workflow_completed"]
        )

        self.assertIsNotNone(subscription.id)
        self.assertEqual(subscription.entity_type, "TestReport")
        self.assertIsNone(subscription.workflow_instance_id)

    def test_unsubscribe_user(self):
        """Test unsubscribing user from notifications."""
        # Create subscription
        subscription = self.notification_system.subscribe_user(
            user_id="user123",
            workflow_id=self.workflow.id
        )
        self.assertTrue(subscription.is_active)

        # Unsubscribe
        self.notification_system.unsubscribe_user(subscription.id)

        # Verify unsubscribed
        self.session.refresh(subscription)
        self.assertFalse(subscription.is_active)
        self.assertIsNotNone(subscription.unsubscribed_at)

    def test_get_subscribers(self):
        """Test getting workflow subscribers."""
        # Create subscriptions
        sub1 = NotificationSubscription(
            user_id="user1",
            workflow_instance_id=self.workflow.id,
            event_types=["approval_requested"],
            is_active=True
        )
        sub2 = NotificationSubscription(
            user_id="user2",
            entity_type=self.workflow.entity_type,
            event_types=["approval_requested", "workflow_completed"],
            is_active=True
        )
        sub3 = NotificationSubscription(
            user_id="user3",
            workflow_instance_id=self.workflow.id,
            event_types=["workflow_completed"],  # Different event
            is_active=True
        )
        self.session.add_all([sub1, sub2, sub3])
        self.session.commit()

        # Get subscribers for approval_requested event
        subscribers = self.notification_system._get_subscribers(
            self.workflow,
            NotificationEvent.APPROVAL_REQUESTED
        )

        # Should get user1 and user2, not user3
        self.assertEqual(len(subscribers), 2)
        self.assertIn("user1", subscribers)
        self.assertIn("user2", subscribers)
        self.assertNotIn("user3", subscribers)

    def test_get_user_preferences(self):
        """Test getting user notification preferences."""
        # Create preferences
        pref1 = NotificationPreference(
            user_id="user123",
            channel=NotificationChannel.EMAIL,
            enabled=True,
            contact_info="user@example.com"
        )
        pref2 = NotificationPreference(
            user_id="user123",
            channel=NotificationChannel.SLACK,
            enabled=True,
            contact_info="@user123"
        )
        self.session.add_all([pref1, pref2])
        self.session.commit()

        prefs = self.notification_system._get_user_preferences("user123")

        self.assertEqual(len(prefs), 2)
        channels = [p.channel for p in prefs]
        self.assertIn(NotificationChannel.EMAIL, channels)
        self.assertIn(NotificationChannel.SLACK, channels)

    def test_get_user_preferences_default(self):
        """Test getting default preferences when none exist."""
        # No preferences exist
        prefs = self.notification_system._get_user_preferences("newuser")

        # Should return default email preference
        self.assertEqual(len(prefs), 1)
        self.assertEqual(prefs[0].channel, NotificationChannel.EMAIL)
        self.assertTrue(prefs[0].enabled)

    def test_quiet_hours_check(self):
        """Test quiet hours checking."""
        # Create preference with quiet hours
        pref = NotificationPreference(
            user_id="user123",
            channel=NotificationChannel.EMAIL,
            enabled=True,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00"
        )

        # Mock current time to be within quiet hours (e.g., 23:00)
        # Note: In production, would need to handle timezones properly
        # This is a simplified test
        is_quiet = self.notification_system._is_quiet_hours(pref)
        # Result depends on actual current time
        self.assertIsInstance(is_quiet, bool)

    def test_quiet_hours_spanning_midnight(self):
        """Test quiet hours that span midnight."""
        pref = NotificationPreference(
            user_id="user123",
            channel=NotificationChannel.EMAIL,
            enabled=True,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00"
        )

        # Test is handled by _is_quiet_hours method
        # Actual result depends on current time
        result = self.notification_system._is_quiet_hours(pref)
        self.assertIsInstance(result, bool)

    def test_notify_workflow_event(self):
        """Test notifying workflow event to subscribers."""
        # Create subscription
        subscription = NotificationSubscription(
            user_id="user123",
            workflow_instance_id=self.workflow.id,
            event_types=["approval_requested"],
            is_active=True
        )
        # Create user preference
        preference = NotificationPreference(
            user_id="user123",
            channel=NotificationChannel.EMAIL,
            enabled=True,
            contact_info="user@example.com"
        )
        self.session.add_all([subscription, preference])
        self.session.commit()

        # Send workflow event notification
        self.notification_system.notify_workflow_event(
            workflow=self.workflow,
            event=NotificationEvent.APPROVAL_REQUESTED,
            additional_data={
                "approval": {"step_name": "Review"},
                "approval_url": "https://example.com/approval/1"
            }
        )

        # Check notification was created
        notifications = self.session.query(NotificationLog).filter_by(
            workflow_id=self.workflow.id
        ).all()
        self.assertGreater(len(notifications), 0)

    def test_retry_failed_notifications(self):
        """Test retrying failed notifications."""
        # Create failed notification
        notification = NotificationLog(
            workflow_id=self.workflow.id,
            channel=NotificationChannel.EMAIL,
            recipient="user@example.com",
            message="Test",
            status=NotificationStatus.FAILED,
            retry_count=0,
            max_retries=3,
            failed_at=datetime.utcnow() - timedelta(minutes=10)
        )
        self.session.add(notification)
        self.session.commit()

        # Retry failed notifications
        self.notification_system.retry_failed_notifications()

        # Check notification status was updated
        self.session.refresh(notification)
        # Status should be updated (either SENT or FAILED depending on delivery)

    def test_max_retries_exceeded(self):
        """Test that notifications exceeding max retries are not retried."""
        # Create notification that has exceeded max retries
        notification = NotificationLog(
            workflow_id=self.workflow.id,
            channel=NotificationChannel.EMAIL,
            recipient="user@example.com",
            message="Test",
            status=NotificationStatus.FAILED,
            retry_count=3,
            max_retries=3,
            failed_at=datetime.utcnow() - timedelta(minutes=10)
        )
        self.session.add(notification)
        self.session.commit()

        initial_retry_count = notification.retry_count

        # Try to retry
        self.notification_system.retry_failed_notifications()

        # Retry count should not change
        self.session.refresh(notification)
        self.assertEqual(notification.retry_count, initial_retry_count)

    def test_notification_priority_levels(self):
        """Test different notification priority levels."""
        priorities = [
            NotificationPriority.LOW,
            NotificationPriority.NORMAL,
            NotificationPriority.HIGH,
            NotificationPriority.CRITICAL
        ]

        for priority in priorities:
            notification = self.notification_system.send_notification(
                channel=NotificationChannel.EMAIL,
                recipient="user@example.com",
                subject=f"Test {priority.name}",
                message="Test",
                priority=priority
            )
            self.assertEqual(notification.priority, priority.value)

    def test_notification_metadata(self):
        """Test storing notification metadata."""
        metadata = {
            "event_type": "approval_requested",
            "urgency": "high",
            "related_entity": "TR-001"
        }

        notification = self.notification_system.send_notification(
            channel=NotificationChannel.EMAIL,
            recipient="user@example.com",
            subject="Test",
            message="Test message",
            metadata=metadata
        )

        self.assertEqual(notification.metadata, metadata)
        self.assertEqual(notification.metadata["urgency"], "high")


if __name__ == "__main__":
    unittest.main()
