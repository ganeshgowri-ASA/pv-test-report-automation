"""
Tests for AuditTrailLogger.
"""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from src.audit.trail_logger import (
    AuditTrailLogger,
    AuditEvent,
    AuditEventType,
)


class TestAuditTrailLogger:
    """Test suite for AuditTrailLogger"""

    def test_log_single_event(self, audit_logger):
        """Test logging a single audit event."""
        event = AuditEvent(
            event_type=AuditEventType.CREATE,
            entity_type="Report",
            entity_id="RPT-001",
            user_id="user123",
            user_name="John Doe",
            action="Created test report"
        )

        logged_event = audit_logger.log(event)

        assert logged_event.sequence_number == 1
        assert logged_event.event_hash is not None
        assert len(logged_event.event_hash) == 64  # SHA-256
        assert logged_event.previous_hash == "0" * 64  # Genesis

    def test_hash_chain_integrity(self, audit_logger):
        """Test that hash chain is maintained across multiple events."""
        events = []

        for i in range(5):
            event = AuditEvent(
                event_type=AuditEventType.UPDATE,
                entity_type="Report",
                entity_id=f"RPT-{i:03d}",
                user_id="user123",
                user_name="John Doe",
                action=f"Update {i}"
            )
            logged = audit_logger.log(event)
            events.append(logged)

        # Verify chain
        for i in range(1, len(events)):
            assert events[i].previous_hash == events[i-1].event_hash
            assert events[i].sequence_number == events[i-1].sequence_number + 1

    def test_log_crud_operations(self, audit_logger):
        """Test CRUD operation logging."""
        # CREATE
        create_event = audit_logger.log_crud(
            operation="CREATE",
            entity_type="User",
            entity_id="USR-001",
            user_id="admin",
            user_name="Admin User",
            new_values={"name": "Test User", "email": "test@example.com"}
        )

        assert create_event.event_type == AuditEventType.CREATE
        assert create_event.new_values["name"] == "Test User"

        # UPDATE
        update_event = audit_logger.log_crud(
            operation="UPDATE",
            entity_type="User",
            entity_id="USR-001",
            user_id="admin",
            user_name="Admin User",
            old_values={"email": "test@example.com"},
            new_values={"email": "newemail@example.com"},
            reason="User requested email change"
        )

        assert update_event.event_type == AuditEventType.UPDATE
        assert update_event.old_values["email"] == "test@example.com"
        assert update_event.new_values["email"] == "newemail@example.com"
        assert update_event.reason == "User requested email change"

    def test_log_authentication_events(self, audit_logger):
        """Test authentication event logging."""
        # Successful login
        login_event = audit_logger.log_auth(
            event_type=AuditEventType.LOGIN,
            user_id="user123",
            user_name="John Doe",
            success=True,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0"
        )

        assert login_event.event_type == AuditEventType.LOGIN
        assert login_event.metadata["success"] is True
        assert login_event.ip_address == "192.168.1.100"

        # Failed login
        failed_login = audit_logger.log_auth(
            event_type=AuditEventType.LOGIN_FAILED,
            user_id="user123",
            user_name="John Doe",
            success=False,
            ip_address="192.168.1.100",
            reason="Invalid password"
        )

        assert failed_login.event_type == AuditEventType.LOGIN_FAILED
        assert failed_login.metadata["success"] is False

    def test_log_security_events(self, audit_logger):
        """Test security event logging."""
        security_event = audit_logger.log_security_event(
            event_type=AuditEventType.UNAUTHORIZED_ACCESS,
            user_id="user123",
            user_name="John Doe",
            description="Attempted to access admin panel without authorization",
            severity="HIGH",
            ip_address="192.168.1.100"
        )

        assert security_event.event_type == AuditEventType.UNAUTHORIZED_ACCESS
        assert security_event.metadata["severity"] == "HIGH"
        assert security_event.description == "Attempted to access admin panel without authorization"

    def test_get_events_with_filters(self, audit_logger):
        """Test retrieving events with various filters."""
        # Create events for different users
        for i in range(10):
            user_id = f"user{i % 3}"  # 3 different users
            event = AuditEvent(
                event_type=AuditEventType.CREATE if i % 2 == 0 else AuditEventType.UPDATE,
                entity_type="Report",
                entity_id=f"RPT-{i:03d}",
                user_id=user_id,
                user_name=f"User {user_id}",
                action=f"Action {i}"
            )
            audit_logger.log(event)

        # Filter by user
        user0_events = audit_logger.get_events(user_id="user0")
        assert len(user0_events) == 4  # 0, 3, 6, 9

        # Filter by event type
        create_events = audit_logger.get_events(event_type=AuditEventType.CREATE)
        assert len(create_events) == 5  # 0, 2, 4, 6, 8

        # Test limit
        limited_events = audit_logger.get_events(limit=3)
        assert len(limited_events) == 3

    def test_get_events_by_time_range(self, audit_logger):
        """Test retrieving events by time range."""
        now = datetime.now(timezone.utc)
        past = now - timedelta(hours=1)
        future = now + timedelta(hours=1)

        # Create event
        event = AuditEvent(
            event_type=AuditEventType.CREATE,
            entity_type="Report",
            entity_id="RPT-001",
            user_id="user123",
            user_name="John Doe",
            action="Test action",
            timestamp=now
        )
        audit_logger.log(event)

        # Query with time range
        events = audit_logger.get_events(start_time=past, end_time=future)
        assert len(events) == 1

        # Query outside range
        events = audit_logger.get_events(
            start_time=future,
            end_time=future + timedelta(hours=1)
        )
        assert len(events) == 0

    def test_get_event_by_id(self, audit_logger):
        """Test retrieving a specific event by ID."""
        event = AuditEvent(
            event_type=AuditEventType.CREATE,
            entity_type="Report",
            entity_id="RPT-001",
            user_id="user123",
            user_name="John Doe",
            action="Test action"
        )
        logged = audit_logger.log(event)

        # Retrieve by ID
        retrieved = audit_logger.get_event_by_id(logged.id)
        assert retrieved is not None
        assert retrieved.id == logged.id
        assert retrieved.event_hash == logged.event_hash

        # Non-existent ID
        missing = audit_logger.get_event_by_id(uuid4())
        assert missing is None

    def test_gdpr_compliance_fields(self, audit_logger):
        """Test GDPR compliance fields."""
        future_date = datetime.now(timezone.utc) + timedelta(days=365)

        event = AuditEvent(
            event_type=AuditEventType.GDPR_DATA_ACCESS,
            entity_type="User",
            entity_id="USR-001",
            user_id="user123",
            user_name="John Doe",
            action="Accessed personal data",
            retention_until=future_date,
            is_anonymized=False
        )

        logged = audit_logger.log(event)

        assert logged.retention_until == future_date
        assert logged.is_anonymized is False

        # Retrieve and verify
        retrieved = audit_logger.get_event_by_id(logged.id)
        assert retrieved.retention_until is not None
        assert retrieved.is_anonymized is False

    def test_event_with_metadata(self, audit_logger):
        """Test events with custom metadata."""
        metadata = {
            "source": "web_ui",
            "browser": "Chrome",
            "location": "US-East",
            "custom_field": "value"
        }

        event = AuditEvent(
            event_type=AuditEventType.CREATE,
            entity_type="Report",
            entity_id="RPT-001",
            user_id="user123",
            user_name="John Doe",
            action="Created report with metadata",
            metadata=metadata
        )

        logged = audit_logger.log(event)
        retrieved = audit_logger.get_event_by_id(logged.id)

        assert retrieved.metadata == metadata
        assert retrieved.metadata["source"] == "web_ui"

    def test_sequential_sequence_numbers(self, audit_logger):
        """Test that sequence numbers are always sequential."""
        sequence_numbers = []

        for i in range(20):
            event = AuditEvent(
                event_type=AuditEventType.CREATE,
                entity_type="Report",
                entity_id=f"RPT-{i:03d}",
                user_id="user123",
                user_name="John Doe",
                action=f"Action {i}"
            )
            logged = audit_logger.log(event)
            sequence_numbers.append(logged.sequence_number)

        # Verify all sequence numbers are unique and sequential
        assert sequence_numbers == list(range(1, 21))
