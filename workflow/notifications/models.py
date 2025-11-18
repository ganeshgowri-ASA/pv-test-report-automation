"""
Notification System Models

Defines data models for the notification and alert system.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator


class NotificationType(str, Enum):
    """Types of notifications"""
    TEST_COMPLETE = "test_complete"
    REVIEW_REQUEST = "review_request"
    CALIBRATION_DUE = "calibration_due"
    TEST_FAILURE = "test_failure"
    SYSTEM_ERROR = "system_error"
    SYSTEM_WARNING = "system_warning"
    APPROVAL_REQUEST = "approval_request"
    EQUIPMENT_ISSUE = "equipment_issue"
    COMPLIANCE_ALERT = "compliance_alert"


class NotificationPriority(str, Enum):
    """Priority levels for notifications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DeliveryChannel(str, Enum):
    """Available delivery channels"""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    TEAMS = "teams"
    IN_APP = "in_app"
    DASHBOARD = "dashboard"


class DeliveryStatus(str, Enum):
    """Status of notification delivery"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class NotificationDelivery(BaseModel):
    """Tracks delivery status for each channel"""
    channel: DeliveryChannel
    status: DeliveryStatus = DeliveryStatus.PENDING
    attempted_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


class Notification(BaseModel):
    """
    Core notification model for PV Test Lab Automation

    Attributes:
        notification_id: Unique identifier for the notification
        user_id: Target user ID
        type: Type of notification
        priority: Priority level
        message: Notification message content
        subject: Optional subject line for email notifications
        metadata: Additional contextual data
        sent_at: Timestamp when notification was created
        read_at: Timestamp when notification was read (in-app only)
        delivery_channels: List of channels to deliver through
        deliveries: Tracking information for each delivery channel
    """
    notification_id: Optional[int] = None
    user_id: int
    type: NotificationType
    priority: NotificationPriority = NotificationPriority.MEDIUM
    message: str
    subject: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None
    delivery_channels: List[DeliveryChannel] = Field(default_factory=list)
    deliveries: List[NotificationDelivery] = Field(default_factory=list)

    @validator('delivery_channels', pre=True)
    def validate_channels(cls, v):
        """Ensure delivery channels are unique and valid"""
        if isinstance(v, list):
            # Convert strings to DeliveryChannel enums if needed
            channels = []
            for channel in v:
                if isinstance(channel, str):
                    channels.append(DeliveryChannel(channel))
                else:
                    channels.append(channel)
            return list(set(channels))  # Remove duplicates
        return v

    @validator('message')
    def validate_message(cls, v):
        """Ensure message is not empty"""
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()

    class Config:
        use_enum_values = False
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class NotificationTemplate(BaseModel):
    """
    Template for notification messages

    Supports variable substitution for dynamic content.
    """
    template_id: str
    notification_type: NotificationType
    subject_template: str
    message_template: str
    priority: NotificationPriority = NotificationPriority.MEDIUM
    default_channels: List[DeliveryChannel] = Field(default_factory=list)
    variables: List[str] = Field(default_factory=list)

    def render(self, **kwargs) -> tuple[str, str]:
        """
        Render the template with provided variables

        Returns:
            Tuple of (subject, message)
        """
        subject = self.subject_template.format(**kwargs)
        message = self.message_template.format(**kwargs)
        return subject, message


class NotificationConfig(BaseModel):
    """Configuration for notification channels"""

    # Email (SMTP) Configuration
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    smtp_use_tls: bool = True

    # SMS (Twilio) Configuration
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_from_number: Optional[str] = None

    # Slack Configuration
    slack_webhook_url: Optional[str] = None
    slack_bot_token: Optional[str] = None
    slack_default_channel: str = "#general"

    # Microsoft Teams Configuration
    teams_webhook_url: Optional[str] = None

    # Retry Configuration
    max_retries: int = 3
    retry_delay_seconds: int = 60

    # Priority Routing
    critical_channels: List[DeliveryChannel] = Field(
        default_factory=lambda: [DeliveryChannel.EMAIL, DeliveryChannel.SMS]
    )
    high_channels: List[DeliveryChannel] = Field(
        default_factory=lambda: [DeliveryChannel.EMAIL, DeliveryChannel.SLACK]
    )
    medium_channels: List[DeliveryChannel] = Field(
        default_factory=lambda: [DeliveryChannel.EMAIL]
    )
    low_channels: List[DeliveryChannel] = Field(
        default_factory=lambda: [DeliveryChannel.IN_APP]
    )
