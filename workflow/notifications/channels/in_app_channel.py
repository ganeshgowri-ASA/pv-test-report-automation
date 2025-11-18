"""
In-App Notification Channel

Stores notifications for display within the application.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base import BaseChannel
from ..models import Notification, NotificationConfig

logger = logging.getLogger(__name__)


class InAppChannel(BaseChannel):
    """
    In-app notification channel for storing notifications in the application

    This channel stores notifications that can be retrieved and displayed
    within the application UI. It maintains an in-memory store by default,
    but can be extended to use a database.
    """

    # Class-level storage for in-app notifications
    # In production, this should be replaced with database storage
    _notifications: Dict[int, List[Notification]] = {}

    def validate_config(self) -> bool:
        """In-app channel is always valid"""
        return True

    async def send(self, notification: Notification, recipient: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Store notification for in-app display

        Args:
            notification: Notification to store
            recipient: Must contain 'user_id'

        Returns:
            Tuple of (success, error_message)
        """
        try:
            user_id = recipient.get('user_id') or notification.user_id

            if user_id is None:
                return False, "User ID not provided for in-app notification"

            # Initialize user's notification list if not exists
            if user_id not in self._notifications:
                self._notifications[user_id] = []

            # Store the notification
            self._notifications[user_id].append(notification)

            logger.info(f"In-app notification stored for user {user_id}")
            return True, None

        except Exception as e:
            error_msg = f"Error storing in-app notification: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    @classmethod
    def get_user_notifications(
        cls,
        user_id: int,
        unread_only: bool = False,
        limit: Optional[int] = None
    ) -> List[Notification]:
        """
        Retrieve notifications for a user

        Args:
            user_id: User ID to retrieve notifications for
            unread_only: If True, only return unread notifications
            limit: Maximum number of notifications to return

        Returns:
            List of Notification objects
        """
        notifications = cls._notifications.get(user_id, [])

        if unread_only:
            notifications = [n for n in notifications if n.read_at is None]

        # Sort by sent_at descending (newest first)
        notifications.sort(key=lambda n: n.sent_at, reverse=True)

        if limit:
            notifications = notifications[:limit]

        return notifications

    @classmethod
    def mark_as_read(cls, user_id: int, notification_id: int) -> bool:
        """
        Mark a notification as read

        Args:
            user_id: User ID
            notification_id: Notification ID to mark as read

        Returns:
            True if notification was marked as read, False otherwise
        """
        notifications = cls._notifications.get(user_id, [])

        for notification in notifications:
            if notification.notification_id == notification_id:
                notification.read_at = datetime.utcnow()
                logger.info(f"Notification {notification_id} marked as read for user {user_id}")
                return True

        logger.warning(f"Notification {notification_id} not found for user {user_id}")
        return False

    @classmethod
    def mark_all_as_read(cls, user_id: int) -> int:
        """
        Mark all notifications as read for a user

        Args:
            user_id: User ID

        Returns:
            Number of notifications marked as read
        """
        notifications = cls._notifications.get(user_id, [])
        count = 0

        for notification in notifications:
            if notification.read_at is None:
                notification.read_at = datetime.utcnow()
                count += 1

        logger.info(f"Marked {count} notifications as read for user {user_id}")
        return count

    @classmethod
    def delete_notification(cls, user_id: int, notification_id: int) -> bool:
        """
        Delete a specific notification

        Args:
            user_id: User ID
            notification_id: Notification ID to delete

        Returns:
            True if deleted, False otherwise
        """
        notifications = cls._notifications.get(user_id, [])

        for i, notification in enumerate(notifications):
            if notification.notification_id == notification_id:
                del notifications[i]
                logger.info(f"Deleted notification {notification_id} for user {user_id}")
                return True

        logger.warning(f"Notification {notification_id} not found for user {user_id}")
        return False

    @classmethod
    def clear_old_notifications(cls, user_id: int, days: int = 30) -> int:
        """
        Clear notifications older than specified days

        Args:
            user_id: User ID
            days: Number of days (notifications older than this will be deleted)

        Returns:
            Number of notifications deleted
        """
        from datetime import timedelta

        notifications = cls._notifications.get(user_id, [])
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        original_count = len(notifications)
        cls._notifications[user_id] = [
            n for n in notifications if n.sent_at > cutoff_date
        ]
        deleted_count = original_count - len(cls._notifications[user_id])

        logger.info(f"Cleared {deleted_count} old notifications for user {user_id}")
        return deleted_count
