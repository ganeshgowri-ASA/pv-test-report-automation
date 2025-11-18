"""
Microsoft Teams Notification Channel

Implements Teams delivery using incoming webhooks.
"""

import logging
from typing import Dict, Any, Optional
import aiohttp

from .base import BaseChannel
from ..models import Notification, NotificationConfig

logger = logging.getLogger(__name__)


class TeamsChannel(BaseChannel):
    """
    Microsoft Teams notification channel using webhooks
    """

    def validate_config(self) -> bool:
        """Validate Teams configuration"""
        return bool(self.config.teams_webhook_url)

    async def send(self, notification: Notification, recipient: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Send Teams notification

        Args:
            notification: Notification to send
            recipient: Optional recipient information

        Returns:
            Tuple of (success, error_message)
        """
        if not self.validate_config():
            return False, "Teams channel not properly configured"

        try:
            # Build Teams message card
            payload = self._build_teams_payload(notification)

            # Send via webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.teams_webhook_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        logger.info("Teams message sent successfully")
                        return True, None
                    else:
                        error_msg = f"Teams webhook returned status {response.status}"
                        response_text = await response.text()
                        logger.error(f"{error_msg}: {response_text}")
                        return False, error_msg

        except Exception as e:
            error_msg = f"Error sending Teams notification: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def _build_teams_payload(self, notification: Notification) -> Dict[str, Any]:
        """
        Build Microsoft Teams adaptive card payload

        Args:
            notification: Notification instance

        Returns:
            Teams message card payload
        """
        # Theme color based on priority
        color_map = {
            'low': '28a745',      # Green
            'medium': 'ffc107',   # Yellow
            'high': 'fd7e14',     # Orange
            'critical': 'dc3545'  # Red
        }

        theme_color = color_map.get(notification.priority.value, '6c757d')

        # Build facts for the card
        facts = [
            {
                'name': 'Priority',
                'value': notification.priority.value.upper()
            },
            {
                'name': 'Type',
                'value': notification.type.value.replace('_', ' ').title()
            },
            {
                'name': 'Time',
                'value': notification.sent_at.strftime('%Y-%m-%d %H:%M:%S UTC')
            }
        ]

        # Add metadata as facts
        if notification.metadata:
            for key, value in notification.metadata.items():
                facts.append({
                    'name': key.replace('_', ' ').title(),
                    'value': str(value)
                })

        # Build the message card
        payload = {
            '@type': 'MessageCard',
            '@context': 'https://schema.org/extensions',
            'summary': notification.subject or f"PV Test Lab: {notification.type.value}",
            'themeColor': theme_color,
            'title': notification.subject or f"PV Test Lab Notification",
            'sections': [
                {
                    'activityTitle': notification.type.value.replace('_', ' ').title(),
                    'activitySubtitle': f"Priority: {notification.priority.value.upper()}",
                    'text': notification.message,
                    'facts': facts
                }
            ]
        }

        # Add potential action buttons if metadata contains URLs
        if notification.metadata.get('action_url'):
            payload['potentialAction'] = [
                {
                    '@type': 'OpenUri',
                    'name': 'View Details',
                    'targets': [
                        {
                            'os': 'default',
                            'uri': notification.metadata['action_url']
                        }
                    ]
                }
            ]

        return payload
