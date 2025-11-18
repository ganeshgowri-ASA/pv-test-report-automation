"""
Notification and Alert System for PV Test Lab Automation

This module provides comprehensive notification capabilities including:
- Multi-channel delivery (Email, SMS, Slack, Teams, In-app)
- Priority-based routing
- Template system
- Delivery tracking and retry mechanisms
"""

from .service import NotificationService
from .models import (
    Notification,
    NotificationType,
    NotificationPriority,
    DeliveryChannel,
    DeliveryStatus
)

__all__ = [
    'NotificationService',
    'Notification',
    'NotificationType',
    'NotificationPriority',
    'DeliveryChannel',
    'DeliveryStatus'
]
