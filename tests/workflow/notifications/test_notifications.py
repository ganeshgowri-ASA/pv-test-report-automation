"""
Unit tests for notification system
"""

import pytest
from datetime import datetime
from workflow.notifications import (
    NotificationService,
    Notification,
    NotificationType,
    NotificationPriority,
    DeliveryChannel,
    DeliveryStatus
)
from workflow.notifications.models import NotificationConfig
from workflow.notifications.channels import InAppChannel


class TestNotificationModels:
    """Test notification data models"""

    def test_notification_creation(self):
        """Test creating a notification"""
        notification = Notification(
            user_id=123,
            type=NotificationType.TEST_COMPLETE,
            priority=NotificationPriority.MEDIUM,
            message="Test completed successfully",
            subject="Test Completion",
            delivery_channels=[DeliveryChannel.EMAIL]
        )

        assert notification.user_id == 123
        assert notification.type == NotificationType.TEST_COMPLETE
        assert notification.priority == NotificationPriority.MEDIUM
        assert notification.message == "Test completed successfully"
        assert notification.subject == "Test Completion"
        assert DeliveryChannel.EMAIL in notification.delivery_channels

    def test_notification_validation(self):
        """Test notification validation"""
        # Empty message should raise error
        with pytest.raises(ValueError):
            Notification(
                user_id=123,
                type=NotificationType.TEST_COMPLETE,
                message="",  # Empty message
                delivery_channels=[DeliveryChannel.EMAIL]
            )

    def test_delivery_channels_deduplication(self):
        """Test that duplicate channels are removed"""
        notification = Notification(
            user_id=123,
            type=NotificationType.TEST_COMPLETE,
            message="Test message",
            delivery_channels=["email", "email", "slack"]
        )

        assert len(notification.delivery_channels) == 2
        assert DeliveryChannel.EMAIL in notification.delivery_channels
        assert DeliveryChannel.SLACK in notification.delivery_channels


class TestNotificationService:
    """Test notification service"""

    @pytest.mark.asyncio
    async def test_send_basic_notification(self):
        """Test sending a basic notification"""
        service = NotificationService()

        notification = await service.send_notification(
            user_id=123,
            type=NotificationType.TEST_COMPLETE,
            message="Test completed",
            channels=["in_app"]
        )

        assert notification.notification_id is not None
        assert notification.user_id == 123
        assert notification.type == NotificationType.TEST_COMPLETE
        assert len(notification.deliveries) == 1
        assert notification.deliveries[0].channel == DeliveryChannel.IN_APP

    @pytest.mark.asyncio
    async def test_priority_based_routing(self):
        """Test priority-based channel selection"""
        service = NotificationService()

        # Critical priority should use configured critical channels
        critical_notification = await service.send_notification(
            user_id=123,
            type=NotificationType.SYSTEM_ERROR,
            message="Critical error",
            priority=NotificationPriority.CRITICAL
        )

        # Default critical channels are email + SMS
        assert len(critical_notification.delivery_channels) >= 1

        # Low priority should use in-app only
        low_notification = await service.send_notification(
            user_id=123,
            type=NotificationType.SYSTEM_WARNING,
            message="Low priority warning",
            priority=NotificationPriority.LOW
        )

        assert DeliveryChannel.IN_APP in low_notification.delivery_channels

    @pytest.mark.asyncio
    async def test_send_from_template(self):
        """Test sending notification from template"""
        service = NotificationService()

        notification = await service.send_from_template(
            user_id=123,
            template_id="test_complete",
            template_variables={
                "test_id": "PV-001",
                "module_id": "MOD-123",
                "test_type": "IEC 61215",
                "duration": "2 hours",
                "status": "PASSED"
            }
        )

        assert notification.notification_id is not None
        assert "PV-001" in notification.message
        assert "MOD-123" in notification.message

    @pytest.mark.asyncio
    async def test_template_not_found(self):
        """Test error handling for missing template"""
        service = NotificationService()

        with pytest.raises(ValueError):
            await service.send_from_template(
                user_id=123,
                template_id="nonexistent_template",
                template_variables={}
            )

    @pytest.mark.asyncio
    async def test_get_user_notifications(self):
        """Test retrieving user notifications"""
        service = NotificationService()

        # Send multiple notifications
        for i in range(3):
            await service.send_notification(
                user_id=123,
                type=NotificationType.TEST_COMPLETE,
                message=f"Test {i} completed",
                channels=["in_app"]
            )

        # Retrieve notifications
        notifications = service.get_user_notifications(user_id=123)

        assert len(notifications) == 3

    @pytest.mark.asyncio
    async def test_get_notification_by_id(self):
        """Test retrieving notification by ID"""
        service = NotificationService()

        notification = await service.send_notification(
            user_id=123,
            type=NotificationType.TEST_COMPLETE,
            message="Test completed",
            channels=["in_app"]
        )

        retrieved = service.get_notification(notification.notification_id)

        assert retrieved is not None
        assert retrieved.notification_id == notification.notification_id
        assert retrieved.message == "Test completed"


class TestInAppChannel:
    """Test in-app notification channel"""

    @pytest.mark.asyncio
    async def test_in_app_notification_storage(self):
        """Test storing in-app notifications"""
        service = NotificationService()

        notification = await service.send_notification(
            user_id=123,
            type=NotificationType.TEST_COMPLETE,
            message="Test completed",
            channels=["in_app"]
        )

        # Retrieve from in-app channel
        notifications = InAppChannel.get_user_notifications(user_id=123)

        assert len(notifications) >= 1
        assert any(n.notification_id == notification.notification_id for n in notifications)

    def test_mark_as_read(self):
        """Test marking notification as read"""
        # Clear existing notifications
        InAppChannel._notifications.clear()

        notification = Notification(
            notification_id=1,
            user_id=123,
            type=NotificationType.TEST_COMPLETE,
            message="Test completed",
            delivery_channels=[DeliveryChannel.IN_APP]
        )

        # Store notification
        InAppChannel._notifications[123] = [notification]

        # Mark as read
        result = InAppChannel.mark_as_read(user_id=123, notification_id=1)

        assert result is True
        assert notification.read_at is not None

    def test_get_unread_notifications(self):
        """Test retrieving unread notifications"""
        # Clear existing notifications
        InAppChannel._notifications.clear()

        # Create notifications
        notif1 = Notification(
            notification_id=1,
            user_id=123,
            type=NotificationType.TEST_COMPLETE,
            message="Test 1",
            delivery_channels=[DeliveryChannel.IN_APP]
        )

        notif2 = Notification(
            notification_id=2,
            user_id=123,
            type=NotificationType.TEST_COMPLETE,
            message="Test 2",
            delivery_channels=[DeliveryChannel.IN_APP],
            read_at=datetime.utcnow()
        )

        InAppChannel._notifications[123] = [notif1, notif2]

        # Get unread only
        unread = InAppChannel.get_user_notifications(user_id=123, unread_only=True)

        assert len(unread) == 1
        assert unread[0].notification_id == 1


class TestTemplateManager:
    """Test template management"""

    def test_get_default_templates(self):
        """Test that default templates are loaded"""
        service = NotificationService()

        templates = service.template_manager.list_templates()

        assert len(templates) > 0
        assert "test_complete" in templates
        assert "review_request" in templates
        assert "calibration_due" in templates

    def test_add_custom_template(self):
        """Test adding a custom template"""
        from workflow.notifications.models import NotificationTemplate

        service = NotificationService()

        custom_template = NotificationTemplate(
            template_id="custom_test",
            notification_type=NotificationType.SYSTEM_WARNING,
            subject_template="Custom: {title}",
            message_template="Message: {body}",
            priority=NotificationPriority.MEDIUM,
            variables=["title", "body"]
        )

        service.template_manager.add_template(custom_template)

        retrieved = service.template_manager.get_template("custom_test")

        assert retrieved is not None
        assert retrieved.template_id == "custom_test"

    def test_render_template(self):
        """Test template rendering"""
        service = NotificationService()

        subject, message = service.template_manager.render_template(
            "test_complete",
            test_id="PV-001",
            module_id="MOD-123",
            test_type="IEC 61215",
            duration="2 hours",
            status="PASSED"
        )

        assert "PV-001" in subject
        assert "PV-001" in message
        assert "MOD-123" in message


class TestConfigLoader:
    """Test configuration loading"""

    def test_default_config(self):
        """Test default configuration"""
        config = NotificationConfig()

        assert config.smtp_port == 587
        assert config.smtp_use_tls is True
        assert config.max_retries == 3
        assert config.retry_delay_seconds == 60

    def test_config_from_dict(self):
        """Test loading config from dictionary"""
        from workflow.notifications.config_loader import ConfigLoader

        config_dict = {
            "smtp_host": "smtp.example.com",
            "smtp_port": 25,
            "smtp_username": "user",
            "smtp_password": "pass",
            "smtp_from_email": "noreply@example.com"
        }

        config = ConfigLoader.from_dict(config_dict)

        assert config.smtp_host == "smtp.example.com"
        assert config.smtp_port == 25
        assert config.smtp_username == "user"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
