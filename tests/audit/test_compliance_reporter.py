"""
Tests for ComplianceReporter.
"""
import pytest
from datetime import datetime, timezone, timedelta

from src.audit.trail_logger import AuditEvent, AuditEventType


class TestComplianceReporter:
    """Test suite for ComplianceReporter"""

    def test_get_statistics_empty(self, compliance_reporter):
        """Test statistics with no events."""
        stats = compliance_reporter.get_statistics()

        assert stats.total_events == 0
        assert stats.unique_users == 0
        assert stats.security_events == 0

    def test_get_statistics_basic(self, audit_logger, compliance_reporter):
        """Test basic statistics collection."""
        # Create events
        for i in range(10):
            event = AuditEvent(
                event_type=AuditEventType.CREATE if i % 2 == 0 else AuditEventType.UPDATE,
                entity_type="Report",
                entity_id=f"RPT-{i:03d}",
                user_id=f"user{i % 3}",
                user_name=f"User {i % 3}",
                action=f"Action {i}"
            )
            audit_logger.log(event)

        stats = compliance_reporter.get_statistics()

        assert stats.total_events == 10
        assert stats.unique_users == 3
        assert stats.events_by_type["CREATE"] == 5
        assert stats.events_by_type["UPDATE"] == 5

    def test_get_statistics_security_events(self, audit_logger, compliance_reporter):
        """Test security event statistics."""
        # Create normal events
        for i in range(5):
            event = AuditEvent(
                event_type=AuditEventType.CREATE,
                entity_type="Report",
                entity_id=f"RPT-{i:03d}",
                user_id="user123",
                user_name="John Doe",
                action="Normal action"
            )
            audit_logger.log(event)

        # Create security events
        audit_logger.log_security_event(
            event_type=AuditEventType.UNAUTHORIZED_ACCESS,
            user_id="hacker",
            user_name="Hacker",
            description="Attempted unauthorized access"
        )

        audit_logger.log_auth(
            event_type=AuditEventType.LOGIN_FAILED,
            user_id="user123",
            user_name="John Doe",
            success=False
        )

        stats = compliance_reporter.get_statistics()

        assert stats.total_events == 7
        assert stats.security_events == 1
        assert stats.failed_logins == 1
        assert stats.unauthorized_access_attempts == 1

    def test_search_events_by_query(self, audit_logger, compliance_reporter):
        """Test text search in events."""
        # Create events with different descriptions
        event1 = AuditEvent(
            event_type=AuditEventType.CREATE,
            entity_type="Report",
            entity_id="RPT-001",
            user_id="user123",
            user_name="John Doe",
            action="Created solar panel report"
        )
        audit_logger.log(event1)

        event2 = AuditEvent(
            event_type=AuditEventType.UPDATE,
            entity_type="Report",
            entity_id="RPT-002",
            user_id="user123",
            user_name="John Doe",
            action="Updated battery test report"
        )
        audit_logger.log(event2)

        # Search for "solar"
        events, total = compliance_reporter.search_events(query="solar")
        assert total == 1
        assert events[0].entity_id == "RPT-001"

        # Search for "report"
        events, total = compliance_reporter.search_events(query="report")
        assert total == 2

    def test_search_events_by_type(self, audit_logger, compliance_reporter):
        """Test filtering events by type."""
        # Create mixed events
        for i in range(5):
            event = AuditEvent(
                event_type=AuditEventType.CREATE if i < 3 else AuditEventType.UPDATE,
                entity_type="Report",
                entity_id=f"RPT-{i:03d}",
                user_id="user123",
                user_name="John Doe",
                action=f"Action {i}"
            )
            audit_logger.log(event)

        # Filter by CREATE
        events, total = compliance_reporter.search_events(
            event_types=[AuditEventType.CREATE.value]
        )
        assert total == 3

        # Filter by UPDATE
        events, total = compliance_reporter.search_events(
            event_types=[AuditEventType.UPDATE.value]
        )
        assert total == 2

    def test_search_events_by_date_range(self, audit_logger, compliance_reporter):
        """Test filtering events by date range."""
        now = datetime.now(timezone.utc)

        # Create events at different times
        for i in range(5):
            event = AuditEvent(
                event_type=AuditEventType.CREATE,
                entity_type="Report",
                entity_id=f"RPT-{i:03d}",
                user_id="user123",
                user_name="John Doe",
                action=f"Action {i}",
                timestamp=now - timedelta(days=i)
            )
            audit_logger.log(event)

        # Search last 2 days
        start_date = now - timedelta(days=2)
        events, total = compliance_reporter.search_events(
            start_date=start_date,
            end_date=now + timedelta(hours=1)
        )
        assert total >= 2  # Events from day 0, 1, 2

    def test_generate_audit_report(self, audit_logger, compliance_reporter):
        """Test generating audit report."""
        # Create events
        for i in range(5):
            event = AuditEvent(
                event_type=AuditEventType.CREATE,
                entity_type="Report",
                entity_id=f"RPT-{i:03d}",
                user_id="user123",
                user_name="John Doe",
                action=f"Action {i}"
            )
            audit_logger.log(event)

        # Generate report
        start = datetime.now(timezone.utc) - timedelta(days=1)
        end = datetime.now(timezone.utc)

        report = compliance_reporter.generate_audit_report(
            period_start=start,
            period_end=end,
            title="Test Audit Report",
            generated_by="admin@example.com",
            description="Monthly audit report"
        )

        assert report.title == "Test Audit Report"
        assert report.generated_by == "admin@example.com"
        assert report.statistics.total_events == 5
        assert len(report.findings) > 0
        assert len(report.recommendations) > 0
        assert "ISO 17025" in report.compliance_standards

    def test_export_csv(self, audit_logger, compliance_reporter):
        """Test exporting events to CSV."""
        # Create events
        events_data = []
        for i in range(3):
            event = AuditEvent(
                event_type=AuditEventType.CREATE,
                entity_type="Report",
                entity_id=f"RPT-{i:03d}",
                user_id="user123",
                user_name="John Doe",
                action=f"Action {i}"
            )
            logged = audit_logger.log(event)
            events_data.append(logged)

        # Export to CSV
        csv_data = compliance_reporter.export_csv(events_data)

        assert len(csv_data) > 0
        assert "event_type" in csv_data
        assert "CREATE" in csv_data
        assert "user_name" in csv_data
        assert "John Doe" in csv_data

    def test_export_json(self, audit_logger, compliance_reporter):
        """Test exporting events to JSON."""
        # Create events
        events_data = []
        for i in range(3):
            event = AuditEvent(
                event_type=AuditEventType.CREATE,
                entity_type="Report",
                entity_id=f"RPT-{i:03d}",
                user_id="user123",
                user_name="John Doe",
                action=f"Action {i}"
            )
            logged = audit_logger.log(event)
            events_data.append(logged)

        # Export to JSON
        json_data = compliance_reporter.export_json(events_data)

        assert len(json_data) > 0
        assert '"event_type": "CREATE"' in json_data
        assert '"user_name": "John Doe"' in json_data

    def test_get_compliance_dashboard(self, audit_logger, compliance_reporter):
        """Test compliance dashboard generation."""
        # Create events
        for i in range(10):
            event = AuditEvent(
                event_type=AuditEventType.CREATE,
                entity_type="Report",
                entity_id=f"RPT-{i:03d}",
                user_id="user123",
                user_name="John Doe",
                action=f"Action {i}"
            )
            audit_logger.log(event)

        # Get dashboard
        dashboard = compliance_reporter.get_compliance_dashboard(days=7)

        assert "period" in dashboard
        assert "statistics" in dashboard
        assert "security_issues" in dashboard
        assert "compliance_status" in dashboard
        assert "trending" in dashboard

        assert dashboard["compliance_status"] in ["COMPLIANT", "NON_COMPLIANT", "AT_RISK", "UNKNOWN"]

    def test_detect_security_issues(self, audit_logger, compliance_reporter):
        """Test security issue detection."""
        # Create security events
        audit_logger.log_security_event(
            event_type=AuditEventType.UNAUTHORIZED_ACCESS,
            user_id="hacker",
            user_name="Hacker",
            description="Attempted unauthorized access",
            severity="CRITICAL"
        )

        # Create multiple failed logins
        for i in range(6):
            audit_logger.log_auth(
                event_type=AuditEventType.LOGIN_FAILED,
                user_id="user123",
                user_name="John Doe",
                success=False
            )

        # Detect issues
        issues = compliance_reporter.detect_security_issues(days=1)

        assert len(issues) >= 2  # Security event + excessive failed logins

        # Check for critical security event
        critical_issues = [i for i in issues if i["severity"] == "CRITICAL"]
        assert len(critical_issues) > 0

        # Check for failed login issue
        login_issues = [i for i in issues if i["type"] == "excessive_failed_logins"]
        assert len(login_issues) > 0

    def test_search_pagination(self, audit_logger, compliance_reporter):
        """Test search result pagination."""
        # Create 20 events
        for i in range(20):
            event = AuditEvent(
                event_type=AuditEventType.CREATE,
                entity_type="Report",
                entity_id=f"RPT-{i:03d}",
                user_id="user123",
                user_name="John Doe",
                action=f"Action {i}"
            )
            audit_logger.log(event)

        # Get first page
        events_page1, total = compliance_reporter.search_events(limit=10, offset=0)
        assert len(events_page1) == 10
        assert total == 20

        # Get second page
        events_page2, total = compliance_reporter.search_events(limit=10, offset=10)
        assert len(events_page2) == 10
        assert total == 20

        # Ensure pages are different
        page1_ids = {e.id for e in events_page1}
        page2_ids = {e.id for e in events_page2}
        assert len(page1_ids.intersection(page2_ids)) == 0

    def test_compliance_status_assessment(self, audit_logger, compliance_reporter):
        """Test compliance status assessment."""
        # Test COMPLIANT status (normal events)
        for i in range(5):
            event = AuditEvent(
                event_type=AuditEventType.CREATE,
                entity_type="Report",
                entity_id=f"RPT-{i:03d}",
                user_id="user123",
                user_name="John Doe",
                action=f"Action {i}"
            )
            audit_logger.log(event)

        dashboard = compliance_reporter.get_compliance_dashboard(days=7)
        assert dashboard["compliance_status"] == "COMPLIANT"
