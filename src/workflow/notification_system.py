"""
Notification system for workflow management.

This module provides comprehensive notification capabilities:
- Email notifications
- Slack/Teams integration (stubs for production implementation)
- SMS alerts for critical events
- Template-based notification rendering
- Subscription management
- Delivery tracking and retry logic
- User notification preferences

Supports multi-channel notification delivery with audit trails.
"""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime, time, timedelta
from enum import Enum
import logging
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template, Environment, BaseLoader
from dataclasses import dataclass, field

from .models import (
    NotificationLog, NotificationChannel, NotificationStatus,
    NotificationPreference, NotificationSubscription,
    WorkflowInstance
)


logger = logging.getLogger(__name__)


class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class NotificationEvent(Enum):
    """Notification event types."""
    WORKFLOW_SUBMITTED = "workflow_submitted"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_APPROVED = "approval_approved"
    APPROVAL_REJECTED = "approval_rejected"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_CANCELLED = "workflow_cancelled"
    APPROVAL_ESCALATED = "approval_escalated"
    APPROVAL_OVERDUE = "approval_overdue"
    WORKFLOW_COMMENT = "workflow_comment"
    APPROVAL_DELEGATED = "approval_delegated"


@dataclass
class NotificationConfig:
    """
    Notification system configuration.

    Attributes:
        smtp_host: SMTP server hostname
        smtp_port: SMTP server port
        smtp_username: SMTP username
        smtp_password: SMTP password
        smtp_use_tls: Use TLS for SMTP
        from_email: Default sender email address
        from_name: Default sender name
        slack_webhook_url: Slack webhook URL
        teams_webhook_url: Microsoft Teams webhook URL
        sms_api_key: SMS service API key
        sms_api_url: SMS service API URL
        max_retries: Maximum retry attempts
        retry_delay: Delay between retries (seconds)
    """
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    from_email: str = "noreply@example.com"
    from_name: str = "PV Test Automation"
    slack_webhook_url: Optional[str] = None
    teams_webhook_url: Optional[str] = None
    sms_api_key: Optional[str] = None
    sms_api_url: Optional[str] = None
    max_retries: int = 3
    retry_delay: int = 300  # 5 minutes


class NotificationTemplate:
    """
    Notification template with Jinja2 rendering.
    """

    # Default email templates
    DEFAULT_TEMPLATES = {
        "approval_requested": {
            "subject": "Approval Required: {{ workflow.reference_number }}",
            "body": """
Hello {{ recipient_name }},

You have been assigned an approval request:

Workflow: {{ workflow.reference_number }}
Type: {{ workflow.entity_type }}
Step: {{ approval.step_name }}
Priority: {{ workflow.priority }}

Please review and approve at your earliest convenience.

{{ approval_url }}

Best regards,
{{ from_name }}
            """.strip()
        },
        "approval_approved": {
            "subject": "Approved: {{ workflow.reference_number }}",
            "body": """
Hello {{ recipient_name }},

Your workflow has been approved:

Workflow: {{ workflow.reference_number }}
Approved by: {{ approved_by }}
Step: {{ approval.step_name }}
Comments: {{ approval.comments }}

{{ workflow_url }}

Best regards,
{{ from_name }}
            """.strip()
        },
        "approval_rejected": {
            "subject": "Rejected: {{ workflow.reference_number }}",
            "body": """
Hello {{ recipient_name }},

Your workflow has been rejected:

Workflow: {{ workflow.reference_number }}
Rejected by: {{ rejected_by }}
Step: {{ approval.step_name }}
Reason: {{ approval.comments }}

Please review the comments and resubmit if appropriate.

{{ workflow_url }}

Best regards,
{{ from_name }}
            """.strip()
        },
        "approval_overdue": {
            "subject": "OVERDUE: Approval Required - {{ workflow.reference_number }}",
            "body": """
Hello {{ recipient_name }},

You have an OVERDUE approval request:

Workflow: {{ workflow.reference_number }}
Step: {{ approval.step_name }}
Due Date: {{ approval.due_at }}
Days Overdue: {{ days_overdue }}

Please review and approve immediately.

{{ approval_url }}

Best regards,
{{ from_name }}
            """.strip()
        },
        "workflow_completed": {
            "subject": "Completed: {{ workflow.reference_number }}",
            "body": """
Hello {{ recipient_name }},

Your workflow has been completed:

Workflow: {{ workflow.reference_number }}
Type: {{ workflow.entity_type }}
Completed: {{ workflow.completed_at }}

{{ workflow_url }}

Best regards,
{{ from_name }}
            """.strip()
        },
    }

    def __init__(self, custom_templates: Optional[Dict[str, Dict[str, str]]] = None):
        """
        Initialize template engine.

        Args:
            custom_templates: Optional custom templates (extends defaults)
        """
        self.templates = self.DEFAULT_TEMPLATES.copy()
        if custom_templates:
            self.templates.update(custom_templates)
        self.env = Environment(loader=BaseLoader())

    def render(
        self,
        template_name: str,
        variables: Dict[str, Any]
    ) -> tuple[str, str]:
        """
        Render a notification template.

        Args:
            template_name: Template name
            variables: Template variables

        Returns:
            Tuple of (subject, body)
        """
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")

        template_data = self.templates[template_name]

        # Render subject
        subject_template = self.env.from_string(template_data["subject"])
        subject = subject_template.render(**variables)

        # Render body
        body_template = self.env.from_string(template_data["body"])
        body = body_template.render(**variables)

        return subject, body

    def add_template(self, name: str, subject: str, body: str):
        """Add or update a template."""
        self.templates[name] = {"subject": subject, "body": body}


class NotificationSystem:
    """
    Multi-channel notification system.

    Handles notification delivery across multiple channels with
    retry logic, delivery tracking, and user preferences.
    """

    def __init__(
        self,
        session,
        config: Optional[NotificationConfig] = None,
        template_engine: Optional[NotificationTemplate] = None
    ):
        """
        Initialize notification system.

        Args:
            session: Database session
            config: Notification configuration
            template_engine: Template engine
        """
        self.session = session
        self.config = config or NotificationConfig()
        self.template_engine = template_engine or NotificationTemplate()

    def send_notification(
        self,
        channel: NotificationChannel,
        recipient: str,
        subject: str,
        message: str,
        workflow_id: Optional[int] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        template_name: Optional[str] = None,
        template_vars: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> NotificationLog:
        """
        Send a notification.

        Args:
            channel: Notification channel
            recipient: Recipient identifier (email, phone, user ID, etc.)
            subject: Notification subject
            message: Notification message
            workflow_id: Optional workflow ID
            priority: Notification priority
            template_name: Optional template name
            template_vars: Optional template variables
            metadata: Additional metadata

        Returns:
            Notification log record
        """
        logger.info(f"Sending {channel.value} notification to {recipient}")

        # Create notification log
        notification = NotificationLog(
            workflow_id=workflow_id,
            channel=channel,
            recipient=recipient,
            subject=subject,
            message=message,
            template_name=template_name,
            template_vars=template_vars,
            status=NotificationStatus.PENDING,
            priority=priority.value,
            metadata=metadata or {},
            max_retries=self.config.max_retries,
        )
        self.session.add(notification)
        self.session.commit()

        # Attempt to send
        self._deliver_notification(notification)

        return notification

    def send_from_template(
        self,
        channel: NotificationChannel,
        recipient: str,
        template_name: str,
        template_vars: Dict[str, Any],
        workflow_id: Optional[int] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> NotificationLog:
        """
        Send a notification using a template.

        Args:
            channel: Notification channel
            recipient: Recipient identifier
            template_name: Template name
            template_vars: Template variables
            workflow_id: Optional workflow ID
            priority: Notification priority
            metadata: Additional metadata

        Returns:
            Notification log record
        """
        # Render template
        subject, message = self.template_engine.render(template_name, template_vars)

        # Send notification
        return self.send_notification(
            channel=channel,
            recipient=recipient,
            subject=subject,
            message=message,
            workflow_id=workflow_id,
            priority=priority,
            template_name=template_name,
            template_vars=template_vars,
            metadata=metadata
        )

    def notify_workflow_event(
        self,
        workflow: WorkflowInstance,
        event: NotificationEvent,
        recipients: Optional[List[str]] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """
        Send notifications for a workflow event.

        Args:
            workflow: Workflow instance
            event: Event type
            recipients: Optional specific recipients (otherwise uses subscriptions)
            additional_data: Additional template variables
        """
        logger.info(f"Notifying workflow event: {event.value} for workflow {workflow.id}")

        # Determine recipients
        if not recipients:
            recipients = self._get_subscribers(workflow, event)

        if not recipients:
            logger.debug("No recipients for notification")
            return

        # Prepare template variables
        template_vars = {
            "workflow": {
                "id": workflow.id,
                "reference_number": workflow.reference_number,
                "entity_type": workflow.entity_type,
                "entity_id": workflow.entity_id,
                "status": workflow.status.value,
                "priority": workflow.priority,
                "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            },
            "from_name": self.config.from_name,
        }

        if additional_data:
            template_vars.update(additional_data)

        # Map event to template
        template_map = {
            NotificationEvent.APPROVAL_REQUESTED: "approval_requested",
            NotificationEvent.APPROVAL_APPROVED: "approval_approved",
            NotificationEvent.APPROVAL_REJECTED: "approval_rejected",
            NotificationEvent.APPROVAL_OVERDUE: "approval_overdue",
            NotificationEvent.WORKFLOW_COMPLETED: "workflow_completed",
        }

        template_name = template_map.get(event)
        if not template_name:
            logger.warning(f"No template mapping for event: {event.value}")
            return

        # Send to each recipient
        for recipient in recipients:
            # Get user preferences
            prefs = self._get_user_preferences(recipient)

            # Check if notifications are enabled
            for pref in prefs:
                if not pref.enabled:
                    continue

                # Check quiet hours
                if self._is_quiet_hours(pref):
                    logger.debug(f"Skipping notification to {recipient} due to quiet hours")
                    continue

                # Prepare recipient-specific variables
                recipient_vars = template_vars.copy()
                recipient_vars["recipient_name"] = recipient

                # Determine priority
                priority = NotificationPriority.NORMAL
                if event == NotificationEvent.APPROVAL_OVERDUE:
                    priority = NotificationPriority.HIGH
                elif event in [NotificationEvent.APPROVAL_ESCALATED]:
                    priority = NotificationPriority.CRITICAL

                # Send notification
                try:
                    self.send_from_template(
                        channel=pref.channel,
                        recipient=pref.contact_info or recipient,
                        template_name=template_name,
                        template_vars=recipient_vars,
                        workflow_id=workflow.id,
                        priority=priority,
                        metadata={"event": event.value}
                    )
                except Exception as e:
                    logger.error(f"Failed to send notification to {recipient}: {e}")

    def retry_failed_notifications(self):
        """Retry failed notifications that haven't exceeded max retries."""
        now = datetime.utcnow()

        # Find notifications to retry
        to_retry = self.session.query(NotificationLog).filter(
            NotificationLog.status.in_([NotificationStatus.FAILED, NotificationStatus.RETRYING]),
            NotificationLog.retry_count < NotificationLog.max_retries
        ).all()

        logger.info(f"Found {len(to_retry)} notifications to retry")

        for notification in to_retry:
            # Check retry delay
            if notification.failed_at:
                time_since_failure = (now - notification.failed_at).total_seconds()
                if time_since_failure < self.config.retry_delay:
                    continue

            notification.status = NotificationStatus.RETRYING
            notification.retry_count += 1
            self.session.commit()

            self._deliver_notification(notification)

    def _deliver_notification(self, notification: NotificationLog):
        """
        Deliver a notification based on channel.

        Args:
            notification: Notification log record
        """
        try:
            if notification.channel == NotificationChannel.EMAIL:
                self._send_email(notification)
            elif notification.channel == NotificationChannel.SLACK:
                self._send_slack(notification)
            elif notification.channel == NotificationChannel.TEAMS:
                self._send_teams(notification)
            elif notification.channel == NotificationChannel.SMS:
                self._send_sms(notification)
            elif notification.channel == NotificationChannel.IN_APP:
                self._send_in_app(notification)
            else:
                raise ValueError(f"Unsupported notification channel: {notification.channel}")

            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            # Most channels don't provide delivery confirmation immediately
            # For email/SMS, this would be updated via webhooks/callbacks

        except Exception as e:
            logger.error(f"Failed to deliver notification {notification.id}: {e}")
            notification.status = NotificationStatus.FAILED
            notification.failed_at = datetime.utcnow()
            notification.error_message = str(e)

        self.session.commit()

    def _send_email(self, notification: NotificationLog):
        """Send email notification."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = notification.subject
            msg["From"] = f"{self.config.from_name} <{self.config.from_email}>"
            msg["To"] = notification.recipient

            # Add plain text part
            text_part = MIMEText(notification.message, "plain")
            msg.attach(text_part)

            # Connect and send
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                if self.config.smtp_use_tls:
                    server.starttls()
                if self.config.smtp_username and self.config.smtp_password:
                    server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent to {notification.recipient}")

        except Exception as e:
            logger.error(f"Email send failed: {e}")
            raise

    def _send_slack(self, notification: NotificationLog):
        """
        Send Slack notification (stub for production implementation).

        In production, this would use the Slack API or webhook to send messages.
        """
        if not self.config.slack_webhook_url:
            raise ValueError("Slack webhook URL not configured")

        # Stub implementation
        logger.info(f"[STUB] Would send Slack message to {notification.recipient}")
        logger.debug(f"Message: {notification.message}")

        # Production implementation would use:
        # import requests
        # payload = {
        #     "text": notification.message,
        #     "channel": notification.recipient,
        # }
        # response = requests.post(self.config.slack_webhook_url, json=payload)
        # notification.external_id = response.headers.get("X-Slack-Message-Id")

        notification.external_response = {"stub": True, "message": "Slack integration stub"}

    def _send_teams(self, notification: NotificationLog):
        """
        Send Microsoft Teams notification (stub for production implementation).

        In production, this would use Teams webhook or Microsoft Graph API.
        """
        if not self.config.teams_webhook_url:
            raise ValueError("Teams webhook URL not configured")

        # Stub implementation
        logger.info(f"[STUB] Would send Teams message to {notification.recipient}")
        logger.debug(f"Message: {notification.message}")

        # Production implementation would use:
        # import requests
        # payload = {
        #     "@type": "MessageCard",
        #     "@context": "http://schema.org/extensions",
        #     "summary": notification.subject,
        #     "title": notification.subject,
        #     "text": notification.message
        # }
        # response = requests.post(self.config.teams_webhook_url, json=payload)

        notification.external_response = {"stub": True, "message": "Teams integration stub"}

    def _send_sms(self, notification: NotificationLog):
        """
        Send SMS notification (stub for production implementation).

        In production, this would use Twilio, AWS SNS, or similar SMS service.
        """
        if not self.config.sms_api_key:
            raise ValueError("SMS API key not configured")

        # Stub implementation
        logger.info(f"[STUB] Would send SMS to {notification.recipient}")
        logger.debug(f"Message: {notification.message[:160]}")  # SMS truncated

        # Production implementation would use Twilio:
        # from twilio.rest import Client
        # client = Client(account_sid, auth_token)
        # message = client.messages.create(
        #     body=notification.message[:160],
        #     from_=twilio_phone,
        #     to=notification.recipient
        # )
        # notification.external_id = message.sid

        notification.external_response = {"stub": True, "message": "SMS integration stub"}

    def _send_in_app(self, notification: NotificationLog):
        """
        Send in-app notification.

        This creates a notification record that would be displayed
        in the application UI.
        """
        logger.info(f"In-app notification created for {notification.recipient}")
        # Notification is already in database, just mark as sent
        notification.external_response = {"type": "in_app"}

    def _get_subscribers(
        self,
        workflow: WorkflowInstance,
        event: NotificationEvent
    ) -> List[str]:
        """Get list of users subscribed to workflow events."""
        # Query subscriptions
        subscriptions = self.session.query(NotificationSubscription).filter(
            NotificationSubscription.is_active == True,
            NotificationSubscription.workflow_instance_id == workflow.id
        ).all()

        # Also get subscriptions for workflow type
        type_subscriptions = self.session.query(NotificationSubscription).filter(
            NotificationSubscription.is_active == True,
            NotificationSubscription.entity_type == workflow.entity_type
        ).all()

        all_subscriptions = subscriptions + type_subscriptions

        # Filter by event type
        recipients = set()
        for sub in all_subscriptions:
            if sub.event_types:
                if event.value in sub.event_types:
                    recipients.add(sub.user_id)
            else:
                # No event filter = subscribe to all events
                recipients.add(sub.user_id)

        return list(recipients)

    def _get_user_preferences(self, user_id: str) -> List[NotificationPreference]:
        """Get user's notification preferences."""
        prefs = self.session.query(NotificationPreference).filter_by(
            user_id=user_id,
            enabled=True
        ).all()

        # If no preferences, return default (email only)
        if not prefs:
            return [NotificationPreference(
                user_id=user_id,
                channel=NotificationChannel.EMAIL,
                enabled=True,
                contact_info=user_id  # Assume user_id is email
            )]

        return prefs

    def _is_quiet_hours(self, preference: NotificationPreference) -> bool:
        """Check if current time is within user's quiet hours."""
        if not preference.quiet_hours_start or not preference.quiet_hours_end:
            return False

        now = datetime.utcnow().time()
        start = time.fromisoformat(preference.quiet_hours_start)
        end = time.fromisoformat(preference.quiet_hours_end)

        # Handle quiet hours spanning midnight
        if start <= end:
            return start <= now <= end
        else:
            return now >= start or now <= end

    def subscribe_user(
        self,
        user_id: str,
        workflow_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        event_types: Optional[List[str]] = None,
        channels: Optional[List[str]] = None
    ) -> NotificationSubscription:
        """
        Subscribe user to workflow notifications.

        Args:
            user_id: User ID
            workflow_id: Optional specific workflow ID
            entity_type: Optional entity type (subscribe to all of this type)
            event_types: Optional specific event types
            channels: Optional preferred channels

        Returns:
            Subscription record
        """
        subscription = NotificationSubscription(
            user_id=user_id,
            workflow_instance_id=workflow_id,
            entity_type=entity_type,
            event_types=event_types,
            channels=channels,
            is_active=True
        )
        self.session.add(subscription)
        self.session.commit()

        logger.info(f"Created subscription for user {user_id}")
        return subscription

    def unsubscribe_user(self, subscription_id: int):
        """Unsubscribe user from notifications."""
        subscription = self.session.query(NotificationSubscription).filter_by(
            id=subscription_id
        ).first()

        if subscription:
            subscription.is_active = False
            subscription.unsubscribed_at = datetime.utcnow()
            self.session.commit()
            logger.info(f"Unsubscribed subscription {subscription_id}")
