"""
Email Notification Channel

Implements email delivery using SMTP.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional

from .base import BaseChannel
from ..models import Notification, NotificationConfig

logger = logging.getLogger(__name__)


class EmailChannel(BaseChannel):
    """
    Email notification channel using SMTP
    """

    def validate_config(self) -> bool:
        """Validate SMTP configuration"""
        required_fields = [
            self.config.smtp_host,
            self.config.smtp_username,
            self.config.smtp_password,
            self.config.smtp_from_email
        ]
        return all(required_fields)

    async def send(self, notification: Notification, recipient: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Send email notification

        Args:
            notification: Notification to send
            recipient: Must contain 'email' key with recipient email address

        Returns:
            Tuple of (success, error_message)
        """
        if not self.validate_config():
            return False, "Email channel not properly configured"

        recipient_email = recipient.get('email')
        if not recipient_email:
            return False, "Recipient email address not provided"

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = notification.subject or f"Notification: {notification.type.value}"
            msg['From'] = self.config.smtp_from_email
            msg['To'] = recipient_email

            # Add priority headers based on notification priority
            if notification.priority.value in ['high', 'critical']:
                msg['X-Priority'] = '1'
                msg['Importance'] = 'high'

            # Create HTML and plain text versions
            text_part = MIMEText(notification.message, 'plain')
            html_content = self._create_html_content(notification)
            html_part = MIMEText(html_content, 'html')

            msg.attach(text_part)
            msg.attach(html_part)

            # Connect to SMTP server and send
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                if self.config.smtp_use_tls:
                    server.starttls()

                server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {recipient_email}")
            return True, None

        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            error_msg = f"Unexpected error sending email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def _create_html_content(self, notification: Notification) -> str:
        """
        Create HTML formatted email content

        Args:
            notification: Notification instance

        Returns:
            HTML formatted string
        """
        priority_colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#fd7e14',
            'critical': '#dc3545'
        }

        color = priority_colors.get(notification.priority.value, '#6c757d')

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: {color};
                    color: white;
                    padding: 15px;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    border: 1px solid #dee2e6;
                    border-top: none;
                    border-radius: 0 0 5px 5px;
                }}
                .footer {{
                    margin-top: 20px;
                    padding-top: 10px;
                    border-top: 1px solid #dee2e6;
                    font-size: 12px;
                    color: #6c757d;
                }}
                .metadata {{
                    background-color: #e9ecef;
                    padding: 10px;
                    margin-top: 15px;
                    border-radius: 3px;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin: 0;">PV Test Lab Notification</h2>
                    <p style="margin: 5px 0 0 0;">Priority: {notification.priority.value.upper()}</p>
                </div>
                <div class="content">
                    <p><strong>Type:</strong> {notification.type.value.replace('_', ' ').title()}</p>
                    <p>{notification.message}</p>
                    {self._format_metadata(notification.metadata)}
                </div>
                <div class="footer">
                    <p>This is an automated notification from PV Test Lab Automation System</p>
                    <p>Sent: {notification.sent_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """Format metadata for HTML display"""
        if not metadata:
            return ""

        items = []
        for key, value in metadata.items():
            formatted_key = key.replace('_', ' ').title()
            items.append(f"<p><strong>{formatted_key}:</strong> {value}</p>")

        return f'<div class="metadata">{"".join(items)}</div>'
