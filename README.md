# PV Test Report Automation System

World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## Phase 5: Review Workflow System (ISO 17025 Compliant)

### Overview

The Review Workflow System provides a comprehensive, production-ready solution for managing technical review of PV test reports in compliance with ISO 17025 requirements. The system includes:

- **Multi-level Review Workflow**: Technical, management, and quality review stages
- **Auto-Assignment**: Intelligent reviewer assignment based on specialization and workload
- **Comment System**: Inline comments with threading, @mentions, and file attachments
- **Version Control**: Complete version history with change tracking
- **Notifications**: Email alerts, reminders, and daily digests
- **Streamlit UI**: Interactive dashboard for review management
- **Audit Trail**: Complete audit trail for ISO 17025 compliance

### Features

#### 1. Review Engine (`src/workflow/review_engine.py`)

**Core Capabilities:**
- ✅ Auto-assignment based on technician, test type, and reviewer specialization
- ✅ Multi-level review support (technical, management, quality, final)
- ✅ Review status tracking (pending, in_review, comments_added, approved, rejected)
- ✅ Version control for report iterations with SHA-256 file hashing
- ✅ Complete review history with timestamps and user information
- ✅ SLA-based due date calculation
- ✅ Overdue review detection and escalation
- ✅ Configurable review workflow rules

**Review Levels:**
- **Technical Review**: Peer technician review for technical accuracy
- **Management Review**: Supervisor review for quality and compliance
- **Quality Review**: QA manager review for ISO 17025 compliance
- **Final Approval**: Technical director final sign-off

**Review Statuses:**
- Pending → In Review → Comments Added → Approved/Rejected/Revision Required

#### 2. Comment System (`src/workflow/comment_system.py`)

**Core Capabilities:**
- ✅ Inline comments on specific report sections
- ✅ Comment threads with replies and discussions
- ✅ @mentions for tagging reviewers (e.g., @john.tech)
- ✅ File/image attachments support
- ✅ Resolve/unresolve comment status tracking
- ✅ Comment categories (critical, suggestion, clarification, approval)
- ✅ Search and filter capabilities
- ✅ Export comments for archival

**Comment Categories:**
- **Critical**: Must be addressed before approval
- **Suggestion**: Recommended improvements
- **Clarification**: Questions requiring response
- **Approval**: Approval notes
- **General**: General feedback

#### 3. Notification System (`src/workflow/notifications.py`)

**Core Capabilities:**
- ✅ Email notifications for review assignments
- ✅ Reminder emails for pending reviews (24h before due)
- ✅ Notifications when comments are added
- ✅ Escalation emails for overdue reviews
- ✅ Daily digest of review activities
- ✅ Configurable notification preferences per user
- ✅ Quiet hours support
- ✅ Email templates for consistency

**Notification Types:**
- Review assigned, completed, approved, rejected
- Comments added, @mentions
- Review reminders, overdue escalations
- Daily digest summaries

#### 4. Review UI (`src/workflow/review_ui.py`)

**Core Capabilities:**
- ✅ Review dashboard showing assigned reports
- ✅ Side-by-side version comparison (previous vs current)
- ✅ Highlighted changes from last version (diff view)
- ✅ Comment panel with filters (category, status, section)
- ✅ Bulk approve/reject actions
- ✅ Export review summary
- ✅ Reviewer management interface
- ✅ Analytics dashboard with statistics

**UI Sections:**
- **My Reviews**: Pending, completed, and all reviews
- **Comments**: Comment threads and @mentions
- **Dashboard**: Analytics and statistics
- **Admin**: Reviewer management and system configuration

### Installation

```bash
# Clone repository
git clone <repository-url>
cd pv-test-report-automation

# Install dependencies
pip install -r requirements.txt

# Optional: Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Quick Start

#### 1. Launch Streamlit UI

```bash
streamlit run src/workflow/review_ui.py
```

#### 2. Using the Review Engine Programmatically

```python
from src.workflow import (
    ReviewEngine, ReviewLevel, ReviewerRole, Reviewer
)

# Initialize review engine
engine = ReviewEngine(data_dir="data/reviews")

# Register reviewers
tech_reviewer = Reviewer(
    user_id="tech1",
    name="John Technician",
    email="john@example.com",
    role=ReviewerRole.TECHNICIAN,
    specializations=["PV Testing", "Performance Analysis"]
)
engine.register_reviewer(tech_reviewer)

# Create report version
version = engine.create_report_version(
    report_id="RPT-2024-001",
    file_path="/path/to/report.pdf",
    created_by="tech1",
    changes_summary="Initial version"
)

# Initiate review workflow
assignments = engine.initiate_review_workflow(
    report_id="RPT-2024-001",
    version_id=version.version_id,
    test_type="PV Testing",
    technician_id="tech1",
    initiated_by="supervisor1"
)

# Get review status
status = engine.get_report_review_status("RPT-2024-001")
print(f"Overall status: {status['overall_status']}")
```

#### 3. Using the Comment System

```python
from src.workflow import CommentSystem, CommentCategory

# Initialize comment system
comments = CommentSystem(data_dir="data/comments")

# Add a comment
comment = comments.create_comment(
    report_id="RPT-2024-001",
    version_id="VER_001",
    author_id="reviewer1",
    author_name="Sarah Reviewer",
    content="Please verify the efficiency calculation @john.tech",
    category=CommentCategory.CLARIFICATION,
    section="test_results",
    line_number=42
)

# Reply to comment
reply = comments.reply_to_comment(
    parent_comment_id=comment.comment_id,
    author_id="tech1",
    author_name="John Technician",
    content="Calculation verified, using IEC 61215-1 method"
)

# Resolve comment
comments.resolve_comment(
    comment_id=comment.comment_id,
    resolved_by="reviewer1",
    resolution_note="Confirmed correct"
)

# Get critical comments
critical = comments.get_critical_comments("RPT-2024-001")
print(f"Critical unresolved: {len(critical)}")
```

#### 4. Using the Notification System

```python
from src.workflow import (
    NotificationSystem, NotificationPreferences, NotificationType
)

# Initialize notification system
notifier = NotificationSystem(
    data_dir="data/notifications",
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    smtp_username="your-email@gmail.com",
    smtp_password="your-app-password"
)

# Set user preferences
prefs = NotificationPreferences(
    user_id="tech1",
    email="john@example.com",
    immediate_notifications=[
        NotificationType.REVIEW_ASSIGNED,
        NotificationType.MENTION,
        NotificationType.REVIEW_OVERDUE
    ],
    quiet_hours_start=22,
    quiet_hours_end=8
)
notifier.set_user_preferences(prefs)

# Send notification
notifier.notify_review_assigned(
    reviewer_id="tech1",
    reviewer_name="John Technician",
    reviewer_email="john@example.com",
    report_id="RPT-2024-001",
    test_type="PV Testing",
    due_date=datetime.now() + timedelta(days=2),
    review_level="technical"
)

# Send daily digest
notifier.send_daily_digest("tech1")
```

### Project Structure

```
pv-test-report-automation/
├── src/
│   └── workflow/
│       ├── __init__.py              # Package initialization
│       ├── review_engine.py         # Core review workflow engine
│       ├── comment_system.py        # Comment and threading system
│       ├── notifications.py         # Email notification system
│       └── review_ui.py             # Streamlit dashboard UI
├── data/
│   ├── reviews/                     # Review data storage
│   ├── comments/                    # Comment data storage
│   └── notifications/               # Notification data storage
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
└── LICENSE                          # License information
```

### Data Storage

The system uses JSON-based file storage for simplicity. For production environments, consider:

- **PostgreSQL/MySQL**: For relational data (reviews, comments, users)
- **MongoDB**: For flexible schema and document storage
- **Redis**: For caching and session management
- **S3/MinIO**: For file attachments and report versions

### ISO 17025 Compliance Features

#### Technical Review Requirements
✅ Multi-level review process
✅ Peer review by qualified technicians
✅ Management review and approval
✅ Complete audit trail with timestamps

#### Documentation Requirements
✅ Version control with change tracking
✅ Review history preservation
✅ Comment and resolution tracking
✅ Reviewer qualifications tracking

#### Traceability Requirements
✅ Unique IDs for all entities
✅ Complete action history
✅ User attribution for all changes
✅ Export capabilities for audits

### Configuration

#### Review Engine Configuration

Edit review configuration in `review_engine.py`:

```python
self.review_config = {
    'technical_review_required': True,
    'management_review_required': True,
    'quality_review_threshold': 'critical',  # critical, all, none
    'auto_assignment_enabled': True,
    'sla_hours': {
        ReviewLevel.TECHNICAL: 24,
        ReviewLevel.MANAGEMENT: 48,
        ReviewLevel.QUALITY: 72,
        ReviewLevel.FINAL: 24
    }
}
```

#### Email Configuration

Configure SMTP settings for notifications:

```python
notifier = NotificationSystem(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    smtp_username="your-email@gmail.com",
    smtp_password="your-app-password",
    from_email="noreply@pvlab.com"
)
```

### API Reference

See inline documentation in each module for detailed API reference:

- `review_engine.py`: Review workflow management
- `comment_system.py`: Comment and threading
- `notifications.py`: Email notifications
- `review_ui.py`: Streamlit dashboard

### Testing

```bash
# Run tests (when test suite is added)
pytest tests/

# Run with coverage
pytest --cov=src/workflow tests/

# Type checking
mypy src/workflow/

# Code formatting
black src/workflow/

# Linting
flake8 src/workflow/
```

### Production Deployment

#### Recommended Stack
- **Web Server**: Nginx or Apache
- **WSGI Server**: Gunicorn or uWSGI
- **Database**: PostgreSQL 14+
- **Cache**: Redis 7+
- **Queue**: Celery with Redis broker
- **Storage**: AWS S3 or MinIO
- **Monitoring**: Prometheus + Grafana

#### Deployment Steps
1. Set up database and run migrations
2. Configure environment variables
3. Deploy with Docker/Kubernetes
4. Set up HTTPS with Let's Encrypt
5. Configure backup and monitoring
6. Set up automated digest cron jobs

### Security Considerations

- ✅ User authentication required (integrate with LDAP/OAuth)
- ✅ Role-based access control (RBAC)
- ✅ Input validation and sanitization
- ✅ File upload restrictions
- ✅ Audit logging for all actions
- ✅ Encrypted storage for sensitive data
- ✅ Rate limiting for notifications

### Roadmap

- [ ] Database backend integration
- [ ] Advanced analytics and reporting
- [ ] Integration with LIMS systems
- [ ] Mobile app for review management
- [ ] AI-powered review suggestions
- [ ] Electronic signatures (21 CFR Part 11)
- [ ] Advanced search with Elasticsearch
- [ ] Real-time collaboration features

### Support & Documentation

For questions, issues, or feature requests:
- Create an issue on GitHub
- Email: support@pvlab.com
- Documentation: https://docs.pvlab.com

### License

See LICENSE file for details.

### Authors

PV Test Report Automation Team

### Acknowledgments

Built with compliance to:
- ISO/IEC 17025:2017
- ISO 9001:2015
- IEC 61215 series
- NABL/ILAC requirements
