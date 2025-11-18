"""
SMS Notification Channel

Implements SMS delivery using Twilio.
"""

import logging
from typing import Dict, Any, Optional

from .base import BaseChannel
from ..models import Notification, NotificationConfig

logger = logging.getLogger(__name__)


class SMSChannel(BaseChannel):
    """
    SMS notification channel using Twilio
    """

    def validate_config(self) -> bool:
        """Validate Twilio configuration"""
        required_fields = [
            self.config.twilio_account_sid,
            self.config.twilio_auth_token,
            self.config.twilio_from_number
        ]
        return all(required_fields)

    async def send(self, notification: Notification, recipient: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Send SMS notification via Twilio

        Args:
            notification: Notification to send
            recipient: Must contain 'phone_number' key with recipient phone number

        Returns:
            Tuple of (success, error_message)
        """
        if not self.validate_config():
            return False, "SMS channel not properly configured"

        phone_number = recipient.get('phone_number')
        if not phone_number:
            return False, "Recipient phone number not provided"

        try:
            # Import Twilio client (lazy import to avoid dependency if not used)
            try:
                from twilio.rest import Client
            except ImportError:
                return False, "Twilio library not installed. Install with: pip install twilio"

            # Initialize Twilio client
            client = Client(
                self.config.twilio_account_sid,
                self.config.twilio_auth_token
            )

            # Format message for SMS (plain text, limited length)
            sms_message = self._format_sms_message(notification)

            # Send SMS
            message = client.messages.create(
                body=sms_message,
                from_=self.config.twilio_from_number,
                to=phone_number
            )

            logger.info(f"SMS sent successfully to {phone_number}. SID: {message.sid}")
            return True, None

        except Exception as e:
            error_msg = f"Error sending SMS: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def _format_sms_message(self, notification: Notification) -> str:
        """
        Format notification for SMS delivery

        SMS messages should be concise and limited to 160 characters when possible.

        Args:
            notification: Notification instance

        Returns:
            Formatted SMS message
        """
        # Priority indicator
        priority_prefix = ""
        if notification.priority.value == 'critical':
            priority_prefix = "[CRITICAL] "
        elif notification.priority.value == 'high':
            priority_prefix = "[HIGH] "

        # Type indicator
        type_name = notification.type.value.replace('_', ' ').title()

        # Build message
        message = f"{priority_prefix}{type_name}: {notification.message}"

        # Truncate if too long (SMS limit is typically 160 chars, but can be up to 1600)
        # We'll use 300 as a reasonable limit for segmented messages
        if len(message) > 300:
            message = message[:297] + "..."

        return message
