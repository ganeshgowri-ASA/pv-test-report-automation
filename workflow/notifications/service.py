"""
Notification Service

Core service for managing and delivering notifications across multiple channels.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .models import (
    Notification,
    NotificationType,
    NotificationPriority,
    DeliveryChannel,
    DeliveryStatus,
    NotificationDelivery,
    NotificationConfig
)
from .channels import (
    BaseChannel,
    EmailChannel,
    SMSChannel,
    SlackChannel,
    TeamsChannel,
    InAppChannel
)
from .templates import TemplateManager

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Comprehensive notification service for PV Test Lab Automation

    Features:
    - Multi-channel delivery (Email, SMS, Slack, Teams, In-app)
    - Priority-based routing
    - Template system
    - Delivery tracking and retry mechanisms
    - Configurable channels
    """

    def __init__(self, config: Optional[NotificationConfig] = None):
        """
        Initialize notification service

        Args:
            config: NotificationConfig instance. If None, uses default config.
        """
        self.config = config or NotificationConfig()
        self.template_manager = TemplateManager()

        # Initialize channels
        self.channels: Dict[DeliveryChannel, BaseChannel] = {
            DeliveryChannel.EMAIL: EmailChannel(self.config),
            DeliveryChannel.SMS: SMSChannel(self.config),
            DeliveryChannel.SLACK: SlackChannel(self.config),
            DeliveryChannel.TEAMS: TeamsChannel(self.config),
            DeliveryChannel.IN_APP: InAppChannel(self.config)
        }

        # Notification storage (in-memory, should be replaced with DB in production)
        self._notification_id_counter = 0
        self._notifications: Dict[int, Notification] = {}

        logger.info("NotificationService initialized")

    def _get_next_notification_id(self) -> int:
        """Generate next notification ID"""
        self._notification_id_counter += 1
        return self._notification_id_counter

    def _get_channels_for_priority(self, priority: NotificationPriority) -> List[DeliveryChannel]:
        """
        Get default delivery channels based on priority level

        Args:
            priority: NotificationPriority

        Returns:
            List of DeliveryChannel enums
        """
        priority_channel_map = {
            NotificationPriority.CRITICAL: self.config.critical_channels,
            NotificationPriority.HIGH: self.config.high_channels,
            NotificationPriority.MEDIUM: self.config.medium_channels,
            NotificationPriority.LOW: self.config.low_channels
        }
        return priority_channel_map.get(priority, [DeliveryChannel.EMAIL])

    async def send_notification(
        self,
        user_id: int,
        type: NotificationType,
        message: str,
        channels: Optional[List[str]] = None,
        priority: Optional[NotificationPriority] = None,
        subject: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        recipient_info: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """
        Send a notification through specified channels

        Args:
            user_id: Target user ID
            type: NotificationType enum
            message: Notification message
            channels: List of channel names (email, sms, slack, teams, in_app).
                     If None, uses priority-based default channels.
            priority: NotificationPriority. If None, defaults to MEDIUM.
            subject: Optional subject line
            metadata: Additional metadata
            recipient_info: Recipient contact information (email, phone_number, etc.)

        Returns:
            Notification object with delivery status

        Example:
            await ns.send_notification(
                user_id=123,
                type=NotificationType.REVIEW_REQUEST,
                message="Report PV-001 ready for review",
                channels=["email", "slack"],
                priority=NotificationPriority.HIGH
            )
        """
        # Set defaults
        priority = priority or NotificationPriority.MEDIUM
        metadata = metadata or {}
        recipient_info = recipient_info or {}

        # Determine channels
        if channels:
            delivery_channels = [DeliveryChannel(ch) for ch in channels]
        else:
            delivery_channels = self._get_channels_for_priority(priority)

        # Create notification
        notification = Notification(
            notification_id=self._get_next_notification_id(),
            user_id=user_id,
            type=type,
            priority=priority,
            message=message,
            subject=subject,
            metadata=metadata,
            delivery_channels=delivery_channels
        )

        # Store notification
        self._notifications[notification.notification_id] = notification

        # Send through all channels
        await self._deliver_notification(notification, recipient_info)

        return notification

    async def send_from_template(
        self,
        user_id: int,
        template_id: str,
        template_variables: Dict[str, Any],
        channels: Optional[List[str]] = None,
        recipient_info: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """
        Send a notification using a template

        Args:
            user_id: Target user ID
            template_id: Template identifier
            template_variables: Variables to render in the template
            channels: Optional list of channels (overrides template defaults)
            recipient_info: Recipient contact information

        Returns:
            Notification object

        Example:
            await ns.send_from_template(
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
        """
        template = self.template_manager.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        # Render template
        subject, message = template.render(**template_variables)

        # Use template defaults if channels not specified
        if channels is None:
            channels = [ch.value for ch in template.default_channels]

        # Send notification
        return await self.send_notification(
            user_id=user_id,
            type=template.notification_type,
            message=message,
            subject=subject,
            channels=channels,
            priority=template.priority,
            metadata=template_variables,
            recipient_info=recipient_info
        )

    async def _deliver_notification(
        self,
        notification: Notification,
        recipient_info: Dict[str, Any]
    ) -> None:
        """
        Deliver notification through all specified channels

        Args:
            notification: Notification to deliver
            recipient_info: Recipient contact information
        """
        # Add user_id to recipient_info if not present
        if 'user_id' not in recipient_info:
            recipient_info['user_id'] = notification.user_id

        # Create delivery tasks for all channels
        tasks = []
        for channel in notification.delivery_channels:
            delivery = NotificationDelivery(
                channel=channel,
                max_retries=self.config.max_retries
            )
            notification.deliveries.append(delivery)
            tasks.append(self._send_to_channel(notification, channel, delivery, recipient_info))

        # Execute all deliveries concurrently
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_to_channel(
        self,
        notification: Notification,
        channel: DeliveryChannel,
        delivery: NotificationDelivery,
        recipient_info: Dict[str, Any]
    ) -> None:
        """
        Send notification to a specific channel with retry logic

        Args:
            notification: Notification to send
            channel: DeliveryChannel to use
            delivery: NotificationDelivery tracking object
            recipient_info: Recipient information
        """
        channel_impl = self.channels.get(channel)
        if not channel_impl:
            logger.error(f"Channel not implemented: {channel}")
            delivery.status = DeliveryStatus.FAILED
            delivery.error_message = "Channel not implemented"
            return

        # Validate channel configuration
        if not channel_impl.validate_config():
            logger.warning(f"Channel {channel} not configured, skipping")
            delivery.status = DeliveryStatus.FAILED
            delivery.error_message = "Channel not configured"
            return

        # Retry loop
        while delivery.retry_count <= delivery.max_retries:
            try:
                delivery.attempted_at = datetime.utcnow()
                delivery.status = DeliveryStatus.RETRYING if delivery.retry_count > 0 else DeliveryStatus.PENDING

                # Send notification
                success, error_message = await channel_impl.send(notification, recipient_info)

                if success:
                    delivery.status = DeliveryStatus.DELIVERED
                    delivery.delivered_at = datetime.utcnow()
                    logger.info(
                        f"Notification {notification.notification_id} delivered via {channel} "
                        f"(attempt {delivery.retry_count + 1})"
                    )
                    return
                else:
                    delivery.error_message = error_message
                    delivery.retry_count += 1

                    if delivery.retry_count <= delivery.max_retries:
                        # Wait before retry (exponential backoff)
                        wait_time = self.config.retry_delay_seconds * (2 ** (delivery.retry_count - 1))
                        logger.info(
                            f"Retrying {channel} delivery for notification {notification.notification_id} "
                            f"in {wait_time} seconds (attempt {delivery.retry_count})"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        delivery.status = DeliveryStatus.FAILED
                        logger.error(
                            f"Failed to deliver notification {notification.notification_id} via {channel} "
                            f"after {delivery.max_retries} retries: {error_message}"
                        )
                        return

            except Exception as e:
                delivery.error_message = str(e)
                delivery.retry_count += 1
                logger.error(f"Error sending to {channel}: {e}")

                if delivery.retry_count > delivery.max_retries:
                    delivery.status = DeliveryStatus.FAILED
                    return

    def get_notification(self, notification_id: int) -> Optional[Notification]:
        """
        Get a notification by ID

        Args:
            notification_id: Notification ID

        Returns:
            Notification or None if not found
        """
        return self._notifications.get(notification_id)

    def get_user_notifications(
        self,
        user_id: int,
        notification_type: Optional[NotificationType] = None,
        priority: Optional[NotificationPriority] = None,
        limit: int = 50
    ) -> List[Notification]:
        """
        Get notifications for a user

        Args:
            user_id: User ID
            notification_type: Optional filter by type
            priority: Optional filter by priority
            limit: Maximum number of notifications to return

        Returns:
            List of Notification objects
        """
        notifications = [
            n for n in self._notifications.values()
            if n.user_id == user_id
        ]

        # Apply filters
        if notification_type:
            notifications = [n for n in notifications if n.type == notification_type]

        if priority:
            notifications = [n for n in notifications if n.priority == priority]

        # Sort by sent_at descending
        notifications.sort(key=lambda n: n.sent_at, reverse=True)

        return notifications[:limit]

    def get_delivery_status(self, notification_id: int) -> Optional[List[NotificationDelivery]]:
        """
        Get delivery status for a notification

        Args:
            notification_id: Notification ID

        Returns:
            List of NotificationDelivery objects or None if notification not found
        """
        notification = self.get_notification(notification_id)
        if notification:
            return notification.deliveries
        return None

    async def retry_failed_deliveries(self, notification_id: int) -> Notification:
        """
        Retry failed deliveries for a notification

        Args:
            notification_id: Notification ID

        Returns:
            Updated Notification object

        Raises:
            ValueError: If notification not found
        """
        notification = self.get_notification(notification_id)
        if not notification:
            raise ValueError(f"Notification not found: {notification_id}")

        # Find failed deliveries
        failed_deliveries = [
            d for d in notification.deliveries
            if d.status == DeliveryStatus.FAILED
        ]

        if not failed_deliveries:
            logger.info(f"No failed deliveries for notification {notification_id}")
            return notification

        # Reset retry counters and reattempt
        for delivery in failed_deliveries:
            delivery.retry_count = 0
            delivery.status = DeliveryStatus.PENDING
            delivery.error_message = None

        # Reattempt delivery
        recipient_info = {'user_id': notification.user_id}
        await self._deliver_notification(notification, recipient_info)

        return notification
