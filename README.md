# PV Test Report Automation

World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## Features

### Phase 5: Notification & Alert System ✅

Comprehensive multi-channel notification system with:

- **Multi-channel Delivery**
  - Email (SMTP) with rich HTML formatting
  - SMS alerts via Twilio
  - Slack webhooks with rich formatting
  - Microsoft Teams adaptive cards
  - In-app notifications
  - Dashboard notifications

- **Priority-based Routing**
  - Critical: Email + SMS
  - High: Email + Slack
  - Medium: Email
  - Low: In-app only

- **Template System**
  - 9 pre-defined templates for common scenarios
  - Custom template support
  - Variable substitution
  - Rich formatting

- **Delivery Tracking**
  - Per-channel delivery status
  - Automatic retry with exponential backoff
  - Error tracking and logging
  - Delivery history

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/ganeshgowri-ASA/pv-test-report-automation.git
cd pv-test-report-automation

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your configuration
```

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

## Documentation

- **[Notification Guide](NOTIFICATION_GUIDE.md)** - Comprehensive guide to the notification system
- **[Examples](examples/notification_examples.py)** - Code examples and usage patterns

## Project Structure

```
pv-test-report-automation/
├── workflow/
│   └── notifications/          # Notification & Alert System
│       ├── channels/           # Delivery channels (Email, SMS, Slack, Teams, In-app)
│       ├── templates/          # Notification templates
│       ├── models.py          # Data models
│       ├── service.py         # Main notification service
│       └── config_loader.py   # Configuration management
├── examples/
│   └── notification_examples.py
├── tests/
│   └── workflow/
│       └── notifications/
├── requirements.txt
├── .env.example
└── NOTIFICATION_GUIDE.md
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=workflow tests/

# Run specific test file
pytest tests/workflow/notifications/test_notifications.py -v
```

## Configuration

### Environment Variables

See `.env.example` for all configuration options. Key variables:

```bash
# Email
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-password

# SMS
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# Teams
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...
```

## Notification Types

- `test_complete` - Test completion alerts
- `review_request` - Review/approval requests
- `calibration_due` - Equipment calibration reminders
- `test_failure` - Test failure alerts
- `system_error` - System errors
- `system_warning` - System warnings
- `approval_request` - Approval requests
- `equipment_issue` - Equipment issues
- `compliance_alert` - Compliance alerts

## Contributing

Contributions are welcome! Please ensure:

1. All tests pass
2. Code follows PEP 8 style guide
3. Documentation is updated
4. Examples are provided for new features

## License

See [LICENSE](LICENSE) file for details.

## Support

For issues or questions, please open an issue on GitHub.
