# Notification & Alert System Guide

Comprehensive notification system for PV test lab automation with multi-channel delivery, priority-based routing, and delivery tracking.

## Features

✅ **Multi-channel Delivery**
- Email (SMTP)
- SMS (Twilio)
- Slack webhooks
- Microsoft Teams webhooks
- In-app notifications
- Dashboard notifications

✅ **Priority-based Routing**
- Automatic channel selection based on priority
- Critical: Email + SMS
- High: Email + Slack
- Medium: Email only
- Low: In-app only

✅ **Template System**
- Pre-defined templates for common scenarios
- Custom template support
- Variable substitution
- Rich HTML email formatting

✅ **Delivery Tracking**
- Per-channel delivery status
- Automatic retry with exponential backoff
- Error tracking and logging
- Delivery history

## Quick Start

### Basic Usage

```python
from workflow.notifications import NotificationService

# Initialize service
service = NotificationService()

# Send a notification
notification = await service.send_notification(
    user_id=123,
    type="review_request",
    message="Report PV-001 ready for review",
    channels=["email", "slack"],
    recipient_info={"email": "user@example.com"}
)
```

### Using Templates

```python
# Send using pre-defined template
notification = await service.send_from_template(
    user_id=123,
    template_id="test_complete",
    template_variables={
        "test_id": "PV-001",
        "module_id": "MOD-123",
        "test_type": "IEC 61215",
        "duration": "2 hours",
        "status": "PASSED"
    },
    recipient_info={"email": "engineer@example.com"}
)
```

## Configuration

### Environment Variables

```bash
# Email (SMTP)
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USERNAME="your-email@example.com"
export SMTP_PASSWORD="your-password"
export SMTP_FROM_EMAIL="noreply@example.com"

# SMS (Twilio)
export TWILIO_ACCOUNT_SID="AC..."
export TWILIO_AUTH_TOKEN="..."
export TWILIO_FROM_NUMBER="+1234567890"

# Slack
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."

# Microsoft Teams
export TEAMS_WEBHOOK_URL="https://outlook.office.com/webhook/..."
```

### Configuration File

```python
from workflow.notifications.config_loader import load_config

# Load from JSON file
config = load_config(config_file="config/notifications.json")

# Or from environment
config = load_config(use_env=True)

service = NotificationService(config)
```

## Notification Types

### Available Types

- `test_complete` - Test completion notifications
- `review_request` - Review/approval requests
- `calibration_due` - Equipment calibration reminders
- `test_failure` - Test failure alerts
- `system_error` - System errors
- `system_warning` - System warnings
- `approval_request` - Approval requests
- `equipment_issue` - Equipment issues
- `compliance_alert` - Compliance alerts

## Priority Levels

- `CRITICAL` - Immediate attention required (Email + SMS)
- `HIGH` - Important but not urgent (Email + Slack)
- `MEDIUM` - Normal priority (Email)
- `LOW` - Informational (In-app only)

## Delivery Channels

### Email (SMTP)

Rich HTML formatted emails with:
- Color-coded priority indicators
- Structured metadata display
- Responsive design
- Plain text fallback

Configuration:
```python
config = NotificationConfig(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_username="user@example.com",
    smtp_password="password",
    smtp_from_email="noreply@example.com",
    smtp_use_tls=True
)
```

### SMS (Twilio)

Concise text messages for urgent notifications:
- Priority prefixes
- Character limit management
- Automatic message truncation

```python
config = NotificationConfig(
    twilio_account_sid="AC...",
    twilio_auth_token="...",
    twilio_from_number="+1234567890"
)
```

### Slack

Rich formatted messages with:
- Color-coded attachments
- Structured fields
- Timestamp information
- Metadata display

```python
config = NotificationConfig(
    slack_webhook_url="https://hooks.slack.com/services/...",
    # Or use bot token
    slack_bot_token="xoxb-...",
    slack_default_channel="#general"
)
```

### Microsoft Teams

Adaptive cards with:
- Theme color coding
- Fact lists
- Action buttons
- Rich formatting

```python
config = NotificationConfig(
    teams_webhook_url="https://outlook.office.com/webhook/..."
)
```

### In-App Notifications

Stored notifications accessible within the application:

```python
from workflow.notifications.channels import InAppChannel

# Get user notifications
notifications = InAppChannel.get_user_notifications(
    user_id=123,
    unread_only=True,
    limit=10
)

# Mark as read
InAppChannel.mark_as_read(user_id=123, notification_id=1)

# Mark all as read
InAppChannel.mark_all_as_read(user_id=123)

# Delete notification
InAppChannel.delete_notification(user_id=123, notification_id=1)

# Clear old notifications
InAppChannel.clear_old_notifications(user_id=123, days=30)
```

## Templates

### Using Default Templates

```python
# Available default templates:
# - test_complete
# - review_request
# - calibration_due
# - test_failure
# - system_error
# - system_warning
# - approval_request
# - equipment_issue
# - compliance_alert

notification = await service.send_from_template(
    user_id=123,
    template_id="calibration_due",
    template_variables={
        "equipment_id": "EQ-001",
        "equipment_name": "Solar Simulator",
        "due_date": "2025-01-15",
        "days_remaining": "30"
    }
)
```

### Creating Custom Templates

```python
from workflow.notifications.models import NotificationTemplate

custom_template = NotificationTemplate(
    template_id="custom_alert",
    notification_type="system_warning",
    subject_template="Alert: {alert_type}",
    message_template="Alert: {alert_type}\nDetails: {details}",
    priority="high",
    default_channels=["email", "slack"],
    variables=["alert_type", "details"]
)

service.template_manager.add_template(custom_template)
```

## Delivery Tracking

### Check Delivery Status

```python
# Get delivery status
deliveries = service.get_delivery_status(notification_id)

for delivery in deliveries:
    print(f"Channel: {delivery.channel}")
    print(f"Status: {delivery.status}")
    print(f"Attempts: {delivery.retry_count}")
    if delivery.error_message:
        print(f"Error: {delivery.error_message}")
```

### Retry Failed Deliveries

```python
# Retry failed deliveries
notification = await service.retry_failed_deliveries(notification_id)
```

## Advanced Usage

### Custom Priority Routing

```python
config = NotificationConfig(
    critical_channels=["email", "sms", "slack"],
    high_channels=["email", "teams"],
    medium_channels=["email", "in_app"],
    low_channels=["in_app"]
)
```

### Retry Configuration

```python
config = NotificationConfig(
    max_retries=5,
    retry_delay_seconds=30  # Exponential backoff from this base
)
```

## Examples

See `examples/notification_examples.py` for comprehensive examples including:

1. Basic notifications
2. Template-based notifications
3. Multi-channel delivery
4. Priority-based routing
5. Calibration reminders
6. Delivery tracking
7. In-app notification management
8. Custom templates
9. Configuration loading

## Architecture

```
workflow/notifications/
├── __init__.py              # Package exports
├── models.py                # Data models
├── service.py               # Main notification service
├── config_loader.py         # Configuration management
├── channels/                # Delivery channels
│   ├── base.py             # Base channel interface
│   ├── email_channel.py    # Email (SMTP)
│   ├── sms_channel.py      # SMS (Twilio)
│   ├── slack_channel.py    # Slack
│   ├── teams_channel.py    # Microsoft Teams
│   └── in_app_channel.py   # In-app notifications
└── templates/               # Template system
    ├── default_templates.py # Pre-defined templates
    └── template_manager.py  # Template management
```

## Best Practices

1. **Use Templates**: Define templates for recurring notification types
2. **Set Appropriate Priorities**: Use CRITICAL sparingly for true emergencies
3. **Provide Recipient Info**: Always include contact information for external channels
4. **Monitor Delivery**: Check delivery status for critical notifications
5. **Configure Retries**: Adjust retry settings based on importance
6. **Use Metadata**: Include contextual information in metadata field
7. **Test Channels**: Verify channel configuration before production use

## Testing

```python
# Test notification without actual delivery
from workflow.notifications import NotificationService

service = NotificationService()

# In-app channel doesn't require external configuration
notification = await service.send_notification(
    user_id=123,
    type="test_complete",
    message="Test message",
    channels=["in_app"]
)

assert notification.notification_id is not None
assert len(notification.deliveries) == 1
```

## Troubleshooting

### Email Not Sending

- Verify SMTP credentials
- Check SMTP_HOST and SMTP_PORT
- Ensure TLS/SSL settings are correct
- Check firewall rules

### SMS Not Sending

- Verify Twilio credentials
- Check phone number format (+1234567890)
- Verify Twilio account balance
- Check Twilio service status

### Slack/Teams Not Receiving

- Verify webhook URL is correct
- Check webhook permissions
- Ensure webhook is not disabled
- Test webhook with curl

### High Retry Rates

- Check network connectivity
- Verify service endpoints are accessible
- Review error messages in delivery logs
- Adjust retry configuration if needed

## Support

For issues or questions:
1. Check the examples in `examples/notification_examples.py`
2. Review delivery logs
3. Verify configuration settings
4. Test channels individually

## Dependencies

```
pydantic>=2.0.0
aiohttp>=3.8.0
twilio>=8.0.0  # Optional, for SMS
```

Install with: `pip install -r requirements.txt`
