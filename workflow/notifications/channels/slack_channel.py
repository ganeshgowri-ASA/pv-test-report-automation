"""
Slack Notification Channel

Implements Slack delivery using webhooks or Slack API.
"""

import logging
import json
from typing import Dict, Any, Optional
import aiohttp

from .base import BaseChannel
from ..models import Notification, NotificationConfig

logger = logging.getLogger(__name__)


class SlackChannel(BaseChannel):
    """
    Slack notification channel using webhooks
    """

    def validate_config(self) -> bool:
        """Validate Slack configuration"""
        return bool(self.config.slack_webhook_url or self.config.slack_bot_token)

    async def send(self, notification: Notification, recipient: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Send Slack notification

        Args:
            notification: Notification to send
            recipient: May contain 'slack_channel' or 'slack_user_id'

        Returns:
            Tuple of (success, error_message)
        """
        if not self.validate_config():
            return False, "Slack channel not properly configured"

        try:
            # Build Slack message payload
            payload = self._build_slack_payload(notification, recipient)

            # Send via webhook
            if self.config.slack_webhook_url:
                return await self._send_via_webhook(payload)
            else:
                return await self._send_via_api(payload, recipient)

        except Exception as e:
            error_msg = f"Error sending Slack notification: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    async def _send_via_webhook(self, payload: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Send message via Slack webhook"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.slack_webhook_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        logger.info("Slack message sent successfully via webhook")
                        return True, None
                    else:
                        error_msg = f"Slack webhook returned status {response.status}"
                        logger.error(error_msg)
                        return False, error_msg

        except Exception as e:
            error_msg = f"Error sending Slack webhook: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    async def _send_via_api(self, payload: Dict[str, Any], recipient: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Send message via Slack API (using bot token)"""
        try:
            channel = recipient.get('slack_channel', self.config.slack_default_channel)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://slack.com/api/chat.postMessage',
                    json={**payload, 'channel': channel},
                    headers={
                        'Authorization': f'Bearer {self.config.slack_bot_token}',
                        'Content-Type': 'application/json'
                    }
                ) as response:
                    data = await response.json()

                    if data.get('ok'):
                        logger.info(f"Slack message sent successfully to {channel}")
                        return True, None
                    else:
                        error_msg = f"Slack API error: {data.get('error', 'Unknown error')}"
                        logger.error(error_msg)
                        return False, error_msg

        except Exception as e:
            error_msg = f"Error sending Slack API message: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def _build_slack_payload(self, notification: Notification, recipient: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build Slack message payload with rich formatting

        Args:
            notification: Notification instance
            recipient: Recipient information

        Returns:
            Slack message payload
        """
        # Color coding based on priority
        color_map = {
            'low': '#28a745',      # Green
            'medium': '#ffc107',   # Yellow
            'high': '#fd7e14',     # Orange
            'critical': '#dc3545' # Red
        }

        color = color_map.get(notification.priority.value, '#6c757d')

        # Build attachment
        attachment = {
            'color': color,
            'title': notification.subject or f"{notification.type.value.replace('_', ' ').title()}",
            'text': notification.message,
            'fields': [
                {
                    'title': 'Priority',
                    'value': notification.priority.value.upper(),
                    'short': True
                },
                {
                    'title': 'Type',
                    'value': notification.type.value.replace('_', ' ').title(),
                    'short': True
                }
            ],
            'footer': 'PV Test Lab Automation',
            'ts': int(notification.sent_at.timestamp())
        }

        # Add metadata as fields
        if notification.metadata:
            for key, value in notification.metadata.items():
                attachment['fields'].append({
                    'title': key.replace('_', ' ').title(),
                    'value': str(value),
                    'short': True
                })

        payload = {
            'attachments': [attachment]
        }

        # Add text for notifications
        if notification.priority.value == 'critical':
            payload['text'] = ':rotating_light: *CRITICAL ALERT*'
        elif notification.priority.value == 'high':
            payload['text'] = ':warning: *High Priority Notification*'

        return payload
