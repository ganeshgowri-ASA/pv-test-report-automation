"""
Notification System for Review Workflow

Features:
- Email notifications for review assignments
- Reminder emails for pending reviews
- Notifications when comments are added
- Escalation for overdue reviews
- Daily digest of review activities
- Configurable notification preferences
- Email templates for consistency
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Any
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
import logging


class NotificationType(Enum):
    """Notification type enumeration"""
    REVIEW_ASSIGNED = "review_assigned"
    REVIEW_REMINDER = "review_reminder"
    REVIEW_OVERDUE = "review_overdue"
    COMMENT_ADDED = "comment_added"
    MENTION = "mention"
    REVIEW_COMPLETED = "review_completed"
    REVIEW_APPROVED = "review_approved"
    REVIEW_REJECTED = "review_rejected"
    DAILY_DIGEST = "daily_digest"
    ESCALATION = "escalation"


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class NotificationPreferences:
    """User notification preferences"""
    user_id: str
    email: str
    enabled: bool = True
    email_enabled: bool = True
    digest_enabled: bool = True
    digest_frequency: str = "daily"  # daily, weekly
    immediate_notifications: List[NotificationType] = field(default_factory=lambda: [
        NotificationType.REVIEW_ASSIGNED,
        NotificationType.MENTION,
        NotificationType.REVIEW_OVERDUE
    ])
    quiet_hours_start: Optional[int] = None  # Hour (0-23)
    quiet_hours_end: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'email': self.email,
            'enabled': self.enabled,
            'email_enabled': self.email_enabled,
            'digest_enabled': self.digest_enabled,
            'digest_frequency': self.digest_frequency,
            'immediate_notifications': [n.value for n in self.immediate_notifications],
            'quiet_hours_start': self.quiet_hours_start,
            'quiet_hours_end': self.quiet_hours_end
        }


@dataclass
class Notification:
    """Individual notification"""
    notification_id: str
    user_id: str
    notification_type: NotificationType
    priority: NotificationPriority
    subject: str
    message: str
    created_at: datetime
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'notification_id': self.notification_id,
            'user_id': self.user_id,
            'notification_type': self.notification_type.value,
            'priority': self.priority.value,
            'subject': self.subject,
            'message': self.message,
            'created_at': self.created_at.isoformat(),
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'metadata': self.metadata
        }


class EmailTemplates:
    """Email templates for different notification types"""

    @staticmethod
    def review_assigned(reviewer_name: str, report_id: str, test_type: str,
                       due_date: str, review_level: str) -> tuple:
        """Template for review assignment notification"""
        subject = f"New Review Assignment: {report_id}"

        body = f"""
Dear {reviewer_name},

You have been assigned a new review for report {report_id}.

Review Details:
- Report ID: {report_id}
- Test Type: {test_type}
- Review Level: {review_level}
- Due Date: {due_date}

Please log in to the review system to begin your review.

Best regards,
PV Test Report Review System
"""
        return subject, body

    @staticmethod
    def review_reminder(reviewer_name: str, report_id: str, due_date: str,
                       hours_remaining: int) -> tuple:
        """Template for review reminder"""
        subject = f"Reminder: Review Due Soon - {report_id}"

        body = f"""
Dear {reviewer_name},

This is a reminder that your review for report {report_id} is due soon.

Due Date: {due_date}
Time Remaining: {hours_remaining} hours

Please complete your review at your earliest convenience.

Best regards,
PV Test Report Review System
"""
        return subject, body

    @staticmethod
    def review_overdue(reviewer_name: str, report_id: str, due_date: str,
                      hours_overdue: int, supervisor_name: str) -> tuple:
        """Template for overdue review escalation"""
        subject = f"URGENT: Review Overdue - {report_id}"

        body = f"""
Dear {reviewer_name},

Your review for report {report_id} is now overdue.

Original Due Date: {due_date}
Hours Overdue: {hours_overdue}

This review has been escalated to {supervisor_name}.

Please complete the review immediately or contact your supervisor if there are any issues.

Best regards,
PV Test Report Review System
"""
        return subject, body

    @staticmethod
    def comment_added(user_name: str, report_id: str, comment_author: str,
                     comment_preview: str, section: str) -> tuple:
        """Template for comment notification"""
        subject = f"New Comment on {report_id}"

        body = f"""
Dear {user_name},

A new comment has been added to report {report_id}.

Comment by: {comment_author}
Section: {section}
Preview: {comment_preview[:200]}...

Please log in to view and respond to this comment.

Best regards,
PV Test Report Review System
"""
        return subject, body

    @staticmethod
    def mention_notification(user_name: str, report_id: str, mentioned_by: str,
                           comment_preview: str) -> tuple:
        """Template for @mention notification"""
        subject = f"You were mentioned in {report_id}"

        body = f"""
Dear {user_name},

You were mentioned in a comment on report {report_id}.

Mentioned by: {mentioned_by}
Comment: {comment_preview[:200]}...

Please log in to view the full comment and respond if needed.

Best regards,
PV Test Report Review System
"""
        return subject, body

    @staticmethod
    def daily_digest(user_name: str, pending_reviews: int, new_comments: int,
                    mentions: int, overdue: int, activities: List[str]) -> tuple:
        """Template for daily digest"""
        subject = f"Daily Review Activity Digest"

        activities_text = "\n".join(f"- {activity}" for activity in activities[:10])

        body = f"""
Dear {user_name},

Here is your daily review activity summary:

Summary:
- Pending Reviews: {pending_reviews}
- New Comments: {new_comments}
- Mentions: {mentions}
- Overdue Reviews: {overdue}

Recent Activities:
{activities_text}

Please log in to the review system to manage your pending items.

Best regards,
PV Test Report Review System
"""
        return subject, body

    @staticmethod
    def review_approved(technician_name: str, report_id: str, reviewer_name: str,
                       review_level: str) -> tuple:
        """Template for review approval notification"""
        subject = f"Review Approved: {report_id}"

        body = f"""
Dear {technician_name},

Your report {report_id} has been approved.

Approved by: {reviewer_name}
Review Level: {review_level}

You can view the approval details in the review system.

Best regards,
PV Test Report Review System
"""
        return subject, body

    @staticmethod
    def review_rejected(technician_name: str, report_id: str, reviewer_name: str,
                       review_level: str, reason: str) -> tuple:
        """Template for review rejection notification"""
        subject = f"Review Requires Revision: {report_id}"

        body = f"""
Dear {technician_name},

Your report {report_id} requires revision.

Reviewed by: {reviewer_name}
Review Level: {review_level}
Reason: {reason}

Please log in to view the detailed comments and make necessary revisions.

Best regards,
PV Test Report Review System
"""
        return subject, body


class NotificationSystem:
    """
    Comprehensive notification system for review workflow

    Features:
    - Multiple notification channels (email, in-app)
    - Configurable user preferences
    - Email templates
    - Daily digests
    - Escalation handling
    - Audit trail
    """

    def __init__(
        self,
        data_dir: str = "data/notifications",
        smtp_server: Optional[str] = None,
        smtp_port: int = 587,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: str = "noreply@pvtestreview.com"
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Email configuration
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.from_email = from_email

        # Storage
        self.preferences: Dict[str, NotificationPreferences] = {}
        self.notifications: Dict[str, Notification] = {}
        self.pending_digest: Dict[str, List[Notification]] = {}

        # Configure logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        self._load_data()

    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID with timestamp"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        return f"{prefix}_{timestamp}"

    def set_user_preferences(self, preferences: NotificationPreferences) -> None:
        """Set notification preferences for a user"""
        self.preferences[preferences.user_id] = preferences
        self._save_data()

    def get_user_preferences(self, user_id: str) -> Optional[NotificationPreferences]:
        """Get notification preferences for a user"""
        return self.preferences.get(user_id)

    def _is_quiet_hours(self, user_id: str) -> bool:
        """Check if current time is within user's quiet hours"""
        prefs = self.preferences.get(user_id)
        if not prefs or prefs.quiet_hours_start is None:
            return False

        current_hour = datetime.now().hour
        start = prefs.quiet_hours_start
        end = prefs.quiet_hours_end or 0

        if start < end:
            return start <= current_hour < end
        else:
            return current_hour >= start or current_hour < end

    def _should_send_immediate(
        self,
        user_id: str,
        notification_type: NotificationType
    ) -> bool:
        """Determine if notification should be sent immediately"""
        prefs = self.preferences.get(user_id)
        if not prefs or not prefs.enabled or not prefs.email_enabled:
            return False

        if self._is_quiet_hours(user_id):
            return False

        return notification_type in prefs.immediate_notifications

    def create_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        priority: NotificationPriority,
        subject: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """Create a new notification"""
        notification_id = self._generate_id("NOTIF")

        notification = Notification(
            notification_id=notification_id,
            user_id=user_id,
            notification_type=notification_type,
            priority=priority,
            subject=subject,
            message=message,
            created_at=datetime.now(),
            metadata=metadata or {}
        )

        self.notifications[notification_id] = notification

        # Decide whether to send immediately or queue for digest
        if self._should_send_immediate(user_id, notification_type):
            self._send_email_notification(notification)
        else:
            if user_id not in self.pending_digest:
                self.pending_digest[user_id] = []
            self.pending_digest[user_id].append(notification)

        self._save_data()
        return notification

    def notify_review_assigned(
        self,
        reviewer_id: str,
        reviewer_name: str,
        reviewer_email: str,
        report_id: str,
        test_type: str,
        due_date: datetime,
        review_level: str
    ) -> None:
        """Send review assignment notification"""
        subject, message = EmailTemplates.review_assigned(
            reviewer_name, report_id, test_type,
            due_date.strftime("%Y-%m-%d %H:%M"),
            review_level
        )

        self.create_notification(
            user_id=reviewer_id,
            notification_type=NotificationType.REVIEW_ASSIGNED,
            priority=NotificationPriority.NORMAL,
            subject=subject,
            message=message,
            metadata={
                'report_id': report_id,
                'test_type': test_type,
                'due_date': due_date.isoformat(),
                'review_level': review_level
            }
        )

    def notify_review_reminder(
        self,
        reviewer_id: str,
        reviewer_name: str,
        report_id: str,
        due_date: datetime
    ) -> None:
        """Send review reminder notification"""
        hours_remaining = int((due_date - datetime.now()).total_seconds() / 3600)

        subject, message = EmailTemplates.review_reminder(
            reviewer_name, report_id,
            due_date.strftime("%Y-%m-%d %H:%M"),
            hours_remaining
        )

        self.create_notification(
            user_id=reviewer_id,
            notification_type=NotificationType.REVIEW_REMINDER,
            priority=NotificationPriority.NORMAL,
            subject=subject,
            message=message,
            metadata={
                'report_id': report_id,
                'due_date': due_date.isoformat(),
                'hours_remaining': hours_remaining
            }
        )

    def notify_review_overdue(
        self,
        reviewer_id: str,
        reviewer_name: str,
        report_id: str,
        due_date: datetime,
        supervisor_name: str
    ) -> None:
        """Send overdue review escalation notification"""
        hours_overdue = int((datetime.now() - due_date).total_seconds() / 3600)

        subject, message = EmailTemplates.review_overdue(
            reviewer_name, report_id,
            due_date.strftime("%Y-%m-%d %H:%M"),
            hours_overdue, supervisor_name
        )

        self.create_notification(
            user_id=reviewer_id,
            notification_type=NotificationType.REVIEW_OVERDUE,
            priority=NotificationPriority.URGENT,
            subject=subject,
            message=message,
            metadata={
                'report_id': report_id,
                'due_date': due_date.isoformat(),
                'hours_overdue': hours_overdue,
                'supervisor_name': supervisor_name
            }
        )

    def notify_comment_added(
        self,
        user_id: str,
        user_name: str,
        report_id: str,
        comment_author: str,
        comment_preview: str,
        section: str
    ) -> None:
        """Send comment notification"""
        subject, message = EmailTemplates.comment_added(
            user_name, report_id, comment_author,
            comment_preview, section
        )

        self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.COMMENT_ADDED,
            priority=NotificationPriority.NORMAL,
            subject=subject,
            message=message,
            metadata={
                'report_id': report_id,
                'comment_author': comment_author,
                'section': section
            }
        )

    def notify_mention(
        self,
        user_id: str,
        user_name: str,
        report_id: str,
        mentioned_by: str,
        comment_preview: str
    ) -> None:
        """Send @mention notification"""
        subject, message = EmailTemplates.mention_notification(
            user_name, report_id, mentioned_by, comment_preview
        )

        self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.MENTION,
            priority=NotificationPriority.HIGH,
            subject=subject,
            message=message,
            metadata={
                'report_id': report_id,
                'mentioned_by': mentioned_by
            }
        )

    def notify_review_completed(
        self,
        technician_id: str,
        technician_name: str,
        report_id: str,
        reviewer_name: str,
        review_level: str,
        approved: bool,
        reason: str = ""
    ) -> None:
        """Send review completion notification"""
        if approved:
            subject, message = EmailTemplates.review_approved(
                technician_name, report_id, reviewer_name, review_level
            )
            notification_type = NotificationType.REVIEW_APPROVED
        else:
            subject, message = EmailTemplates.review_rejected(
                technician_name, report_id, reviewer_name, review_level, reason
            )
            notification_type = NotificationType.REVIEW_REJECTED

        self.create_notification(
            user_id=technician_id,
            notification_type=notification_type,
            priority=NotificationPriority.HIGH,
            subject=subject,
            message=message,
            metadata={
                'report_id': report_id,
                'reviewer_name': reviewer_name,
                'review_level': review_level,
                'approved': approved,
                'reason': reason
            }
        )

    def send_daily_digest(self, user_id: str) -> None:
        """Send daily digest to a user"""
        prefs = self.preferences.get(user_id)
        if not prefs or not prefs.digest_enabled:
            return

        pending_notifications = self.pending_digest.get(user_id, [])
        if not pending_notifications:
            return

        # Gather statistics
        pending_reviews = sum(
            1 for n in pending_notifications
            if n.notification_type == NotificationType.REVIEW_ASSIGNED
        )
        new_comments = sum(
            1 for n in pending_notifications
            if n.notification_type == NotificationType.COMMENT_ADDED
        )
        mentions = sum(
            1 for n in pending_notifications
            if n.notification_type == NotificationType.MENTION
        )
        overdue = sum(
            1 for n in pending_notifications
            if n.notification_type == NotificationType.REVIEW_OVERDUE
        )

        # Format activities
        activities = [n.subject for n in pending_notifications[:20]]

        # Get user name from first notification or preferences
        user_name = prefs.email.split('@')[0]  # Simple fallback

        subject, message = EmailTemplates.daily_digest(
            user_name, pending_reviews, new_comments, mentions, overdue, activities
        )

        # Create and send digest notification
        digest_notification = Notification(
            notification_id=self._generate_id("NOTIF"),
            user_id=user_id,
            notification_type=NotificationType.DAILY_DIGEST,
            priority=NotificationPriority.NORMAL,
            subject=subject,
            message=message,
            created_at=datetime.now(),
            metadata={'notification_count': len(pending_notifications)}
        )

        self._send_email_notification(digest_notification)

        # Clear pending digest for this user
        self.pending_digest[user_id] = []
        self._save_data()

    def send_all_daily_digests(self) -> None:
        """Send daily digests to all users"""
        for user_id in self.preferences.keys():
            try:
                self.send_daily_digest(user_id)
            except Exception as e:
                self.logger.error(f"Failed to send digest to {user_id}: {e}")

    def _send_email_notification(self, notification: Notification) -> bool:
        """Send email notification"""
        prefs = self.preferences.get(notification.user_id)
        if not prefs or not prefs.email:
            self.logger.warning(f"No email found for user {notification.user_id}")
            return False

        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = prefs.email
            msg['Subject'] = notification.subject

            # Add body
            msg.attach(MIMEText(notification.message, 'plain'))

            # Send email
            if self.smtp_server:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    if self.smtp_username and self.smtp_password:
                        server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)

                notification.sent_at = datetime.now()
                self.logger.info(f"Email sent to {prefs.email}: {notification.subject}")
                return True
            else:
                # No SMTP configured - log only
                self.logger.info(f"Would send email to {prefs.email}: {notification.subject}")
                notification.sent_at = datetime.now()
                return True

        except Exception as e:
            self.logger.error(f"Failed to send email to {prefs.email}: {e}")
            return False

    def check_and_send_reminders(self, hours_before_due: int = 24) -> None:
        """Check for reviews due soon and send reminders"""
        # This would integrate with ReviewEngine to check due dates
        # Placeholder for integration
        pass

    def check_and_escalate_overdue(self) -> None:
        """Check for overdue reviews and send escalation notifications"""
        # This would integrate with ReviewEngine to check overdue reviews
        # Placeholder for integration
        pass

    def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for a user"""
        notifications = [
            n for n in self.notifications.values()
            if n.user_id == user_id
        ]

        if unread_only:
            notifications = [n for n in notifications if n.read_at is None]

        return sorted(notifications, key=lambda x: x.created_at, reverse=True)

    def mark_as_read(self, notification_id: str) -> None:
        """Mark a notification as read"""
        if notification_id in self.notifications:
            self.notifications[notification_id].read_at = datetime.now()
            self._save_data()

    def _save_data(self) -> None:
        """Save all data to disk"""
        data = {
            'preferences': {k: v.to_dict() for k, v in self.preferences.items()},
            'notifications': {k: v.to_dict() for k, v in self.notifications.items()},
            'pending_digest': {
                k: [n.to_dict() for n in notifications]
                for k, notifications in self.pending_digest.items()
            }
        }

        with open(self.data_dir / 'notifications.json', 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def _load_data(self) -> None:
        """Load data from disk"""
        data_file = self.data_dir / 'notifications.json'
        if not data_file.exists():
            return

        try:
            with open(data_file, 'r') as f:
                data = json.load(f)

            # Load preferences
            for user_id, prefs_data in data.get('preferences', {}).items():
                self.preferences[user_id] = NotificationPreferences(
                    user_id=prefs_data['user_id'],
                    email=prefs_data['email'],
                    enabled=prefs_data.get('enabled', True),
                    email_enabled=prefs_data.get('email_enabled', True),
                    digest_enabled=prefs_data.get('digest_enabled', True),
                    digest_frequency=prefs_data.get('digest_frequency', 'daily'),
                    immediate_notifications=[
                        NotificationType(n)
                        for n in prefs_data.get('immediate_notifications', [])
                    ],
                    quiet_hours_start=prefs_data.get('quiet_hours_start'),
                    quiet_hours_end=prefs_data.get('quiet_hours_end')
                )

            # Load notifications
            for notif_id, notif_data in data.get('notifications', {}).items():
                self.notifications[notif_id] = Notification(
                    notification_id=notif_data['notification_id'],
                    user_id=notif_data['user_id'],
                    notification_type=NotificationType(notif_data['notification_type']),
                    priority=NotificationPriority(notif_data['priority']),
                    subject=notif_data['subject'],
                    message=notif_data['message'],
                    created_at=datetime.fromisoformat(notif_data['created_at']),
                    sent_at=datetime.fromisoformat(notif_data['sent_at']) if notif_data.get('sent_at') else None,
                    read_at=datetime.fromisoformat(notif_data['read_at']) if notif_data.get('read_at') else None,
                    metadata=notif_data.get('metadata', {})
                )

            # Load pending digests
            for user_id, notifications_data in data.get('pending_digest', {}).items():
                self.pending_digest[user_id] = [
                    Notification(
                        notification_id=n['notification_id'],
                        user_id=n['user_id'],
                        notification_type=NotificationType(n['notification_type']),
                        priority=NotificationPriority(n['priority']),
                        subject=n['subject'],
                        message=n['message'],
                        created_at=datetime.fromisoformat(n['created_at']),
                        sent_at=datetime.fromisoformat(n['sent_at']) if n.get('sent_at') else None,
                        read_at=datetime.fromisoformat(n['read_at']) if n.get('read_at') else None,
                        metadata=n.get('metadata', {})
                    )
                    for n in notifications_data
                ]

        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
