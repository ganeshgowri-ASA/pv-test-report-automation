"""
Notification System Examples

Demonstrates usage of the notification and alert system.
"""

import asyncio
from datetime import datetime
from workflow.notifications import NotificationService, NotificationType, NotificationPriority
from workflow.notifications.models import NotificationConfig
from workflow.notifications.config_loader import load_config


async def example_basic_notification():
    """
    Example 1: Send a basic notification
    """
    print("\n=== Example 1: Basic Notification ===")

    # Initialize service with configuration
    config = NotificationConfig(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_username="your-email@example.com",
        smtp_password="your-password",
        smtp_from_email="noreply@example.com"
    )
    service = NotificationService(config)

    # Send a simple notification
    notification = await service.send_notification(
        user_id=123,
        type=NotificationType.TEST_COMPLETE,
        message="Test PV-001 completed successfully",
        channels=["email", "in_app"],
        priority=NotificationPriority.MEDIUM,
        subject="Test Completion Notification",
        recipient_info={
            "email": "engineer@example.com"
        }
    )

    print(f"Notification sent with ID: {notification.notification_id}")
    print(f"Delivery status:")
    for delivery in notification.deliveries:
        print(f"  - {delivery.channel.value}: {delivery.status.value}")


async def example_template_notification():
    """
    Example 2: Send notification using a template
    """
    print("\n=== Example 2: Template-based Notification ===")

    service = NotificationService()

    # Send notification using pre-defined template
    notification = await service.send_from_template(
        user_id=123,
        template_id="review_request",
        template_variables={
            "report_id": "PV-001",
            "test_type": "IEC 61215",
            "module_id": "MOD-123",
            "submitted_by": "John Doe",
            "submitted_date": datetime.now().strftime("%Y-%m-%d %H:%M")
        },
        recipient_info={
            "email": "reviewer@example.com"
        }
    )

    print(f"Template notification sent: {notification.notification_id}")
    print(f"Subject: {notification.subject}")
    print(f"Message: {notification.message}")


async def example_multi_channel_notification():
    """
    Example 3: Send notification through multiple channels
    """
    print("\n=== Example 3: Multi-channel Notification ===")

    # Configure all channels
    config = NotificationConfig(
        # Email
        smtp_host="smtp.gmail.com",
        smtp_username="your-email@example.com",
        smtp_password="your-password",
        smtp_from_email="noreply@example.com",

        # SMS
        twilio_account_sid="AC...",
        twilio_auth_token="...",
        twilio_from_number="+1234567890",

        # Slack
        slack_webhook_url="https://hooks.slack.com/services/..."
    )

    service = NotificationService(config)

    # Send critical alert through multiple channels
    notification = await service.send_notification(
        user_id=123,
        type=NotificationType.TEST_FAILURE,
        message="CRITICAL: Test PV-001 has failed. Module MOD-123 showing anomalous behavior.",
        channels=["email", "sms", "slack"],
        priority=NotificationPriority.CRITICAL,
        subject="CRITICAL ALERT: Test Failure",
        metadata={
            "test_id": "PV-001",
            "module_id": "MOD-123",
            "failure_type": "voltage_anomaly",
            "timestamp": datetime.now().isoformat()
        },
        recipient_info={
            "email": "engineer@example.com",
            "phone_number": "+1234567890"
        }
    )

    print(f"Critical alert sent through {len(notification.delivery_channels)} channels")


async def example_priority_based_routing():
    """
    Example 4: Priority-based automatic channel selection
    """
    print("\n=== Example 4: Priority-based Routing ===")

    service = NotificationService()

    # Critical priority - automatically uses email + SMS
    critical_notif = await service.send_notification(
        user_id=123,
        type=NotificationType.SYSTEM_ERROR,
        message="Database connection lost",
        priority=NotificationPriority.CRITICAL,  # Auto-routes to email + SMS
        recipient_info={"email": "admin@example.com", "phone_number": "+1234567890"}
    )

    # Low priority - automatically uses in-app only
    low_notif = await service.send_notification(
        user_id=123,
        type=NotificationType.SYSTEM_WARNING,
        message="Disk space at 70%",
        priority=NotificationPriority.LOW,  # Auto-routes to in-app only
    )

    print(f"Critical notification channels: {[c.value for c in critical_notif.delivery_channels]}")
    print(f"Low priority notification channels: {[c.value for c in low_notif.delivery_channels]}")


async def example_calibration_reminder():
    """
    Example 5: Equipment calibration reminder
    """
    print("\n=== Example 5: Calibration Reminder ===")

    service = NotificationService()

    notification = await service.send_from_template(
        user_id=456,
        template_id="calibration_due",
        template_variables={
            "equipment_id": "EQ-001",
            "equipment_name": "Solar Simulator",
            "last_calibration_date": "2024-01-15",
            "due_date": "2025-01-15",
            "days_remaining": "30"
        },
        channels=["email", "in_app"],
        recipient_info={
            "email": "lab-manager@example.com"
        }
    )

    print(f"Calibration reminder sent: {notification.notification_id}")


async def example_delivery_tracking():
    """
    Example 6: Track delivery status and retry failures
    """
    print("\n=== Example 6: Delivery Tracking ===")

    service = NotificationService()

    # Send notification
    notification = await service.send_notification(
        user_id=123,
        type=NotificationType.REVIEW_REQUEST,
        message="Report ready for review",
        channels=["email", "slack"],
        recipient_info={"email": "reviewer@example.com"}
    )

    # Check delivery status
    print(f"\nDelivery Status for Notification {notification.notification_id}:")
    for delivery in notification.deliveries:
        print(f"  Channel: {delivery.channel.value}")
        print(f"  Status: {delivery.status.value}")
        print(f"  Attempts: {delivery.retry_count + 1}")
        if delivery.error_message:
            print(f"  Error: {delivery.error_message}")
        print()

    # Retry failed deliveries
    if any(d.status.value == 'failed' for d in notification.deliveries):
        print("Retrying failed deliveries...")
        updated_notification = await service.retry_failed_deliveries(notification.notification_id)
        print("Retry complete")


async def example_in_app_notifications():
    """
    Example 7: Working with in-app notifications
    """
    print("\n=== Example 7: In-app Notifications ===")

    from workflow.notifications.channels import InAppChannel

    service = NotificationService()

    # Send several in-app notifications
    for i in range(3):
        await service.send_notification(
            user_id=123,
            type=NotificationType.TEST_COMPLETE,
            message=f"Test {i+1} completed",
            channels=["in_app"]
        )

    # Retrieve user's notifications
    notifications = InAppChannel.get_user_notifications(user_id=123, limit=10)
    print(f"User has {len(notifications)} notifications")

    # Mark as read
    if notifications:
        InAppChannel.mark_as_read(user_id=123, notification_id=notifications[0].notification_id)
        print(f"Marked notification {notifications[0].notification_id} as read")

    # Get unread notifications
    unread = InAppChannel.get_user_notifications(user_id=123, unread_only=True)
    print(f"User has {len(unread)} unread notifications")


async def example_custom_template():
    """
    Example 8: Create and use a custom template
    """
    print("\n=== Example 8: Custom Template ===")

    from workflow.notifications.models import NotificationTemplate

    service = NotificationService()

    # Create custom template
    custom_template = NotificationTemplate(
        template_id="custom_approval",
        notification_type=NotificationType.APPROVAL_REQUEST,
        subject_template="Approval Required: {document_name}",
        message_template=(
            "A document requires your approval.\n\n"
            "Document: {document_name}\n"
            "Type: {document_type}\n"
            "Requester: {requester}\n\n"
            "Please review and approve by {deadline}."
        ),
        priority=NotificationPriority.HIGH,
        default_channels=["email", "slack"],
        variables=["document_name", "document_type", "requester", "deadline"]
    )

    # Add to template manager
    service.template_manager.add_template(custom_template)

    # Use custom template
    notification = await service.send_from_template(
        user_id=789,
        template_id="custom_approval",
        template_variables={
            "document_name": "Test Report PV-001",
            "document_type": "Final Test Report",
            "requester": "John Doe",
            "deadline": "2025-12-31"
        },
        recipient_info={"email": "approver@example.com"}
    )

    print(f"Custom template notification sent: {notification.notification_id}")


async def example_load_config_from_env():
    """
    Example 9: Load configuration from environment variables
    """
    print("\n=== Example 9: Load Config from Environment ===")

    # This will load from environment variables
    config = load_config(use_env=True)
    service = NotificationService(config)

    print("Configuration loaded from environment variables")
    print(f"SMTP configured: {bool(config.smtp_host)}")
    print(f"Twilio configured: {bool(config.twilio_account_sid)}")
    print(f"Slack configured: {bool(config.slack_webhook_url)}")


async def main():
    """
    Run all examples
    """
    print("=" * 60)
    print("PV Test Lab Automation - Notification System Examples")
    print("=" * 60)

    # Note: Most examples won't actually send notifications without proper credentials
    # They demonstrate the API and structure

    await example_basic_notification()
    await example_template_notification()
    await example_priority_based_routing()
    await example_calibration_reminder()
    await example_in_app_notifications()
    await example_custom_template()

    # Examples requiring actual channel configuration (commented out):
    # await example_multi_channel_notification()
    # await example_delivery_tracking()
    # await example_load_config_from_env()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
