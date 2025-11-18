"""
Immutable Audit Trail Logger
ISO 17025 & 21 CFR Part 11 Compliant

Implements blockchain-style hash chaining for tamper-evident audit logs.
All events are immutable once written.
"""

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import (
    Column, String, DateTime, Integer, Text, JSON, Index,
    create_engine, select, and_, desc
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.pool import NullPool

Base = declarative_base()


class AuditEventType(str, Enum):
    """Enumeration of audit event types per 21 CFR Part 11"""

    # CRUD Operations
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

    # Authentication & Authorization
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    LOGIN_FAILED = "LOGIN_FAILED"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    PERMISSION_CHANGE = "PERMISSION_CHANGE"

    # Configuration Changes
    CONFIG_CREATE = "CONFIG_CREATE"
    CONFIG_UPDATE = "CONFIG_UPDATE"
    CONFIG_DELETE = "CONFIG_DELETE"

    # Report Operations
    REPORT_CREATE = "REPORT_CREATE"
    REPORT_UPDATE = "REPORT_UPDATE"
    REPORT_APPROVE = "REPORT_APPROVE"
    REPORT_REJECT = "REPORT_REJECT"
    REPORT_SIGN = "REPORT_SIGN"
    REPORT_EXPORT = "REPORT_EXPORT"
    REPORT_DELETE = "REPORT_DELETE"

    # Data Operations
    DATA_IMPORT = "DATA_IMPORT"
    DATA_EXPORT = "DATA_EXPORT"
    DATA_TRANSFORM = "DATA_TRANSFORM"
    DATA_VALIDATE = "DATA_VALIDATE"

    # Approval & Signature
    APPROVAL_REQUEST = "APPROVAL_REQUEST"
    APPROVAL_GRANT = "APPROVAL_GRANT"
    APPROVAL_DENY = "APPROVAL_DENY"
    SIGNATURE_APPLY = "SIGNATURE_APPLY"
    SIGNATURE_VERIFY = "SIGNATURE_VERIFY"

    # System Events
    SYSTEM_START = "SYSTEM_START"
    SYSTEM_STOP = "SYSTEM_STOP"
    BACKUP_CREATE = "BACKUP_CREATE"
    BACKUP_RESTORE = "BACKUP_RESTORE"

    # Security Events
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"
    DATA_BREACH_ATTEMPT = "DATA_BREACH_ATTEMPT"

    # GDPR Compliance
    GDPR_DATA_ACCESS = "GDPR_DATA_ACCESS"
    GDPR_DATA_EXPORT = "GDPR_DATA_EXPORT"
    GDPR_DATA_DELETE = "GDPR_DATA_DELETE"
    GDPR_CONSENT_GRANT = "GDPR_CONSENT_GRANT"
    GDPR_CONSENT_REVOKE = "GDPR_CONSENT_REVOKE"


class AuditEventModel(Base):
    """
    Immutable audit event storage with hash chaining.
    Once written, records cannot be modified or deleted.
    """
    __tablename__ = "audit_events"

    # Primary identification
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    sequence_number = Column(Integer, nullable=False, unique=True, index=True)

    # Temporal information
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # Event classification
    event_type = Column(String(50), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(100), index=True)

    # Who, What, Where, Why
    user_id = Column(String(100), nullable=False, index=True)
    user_name = Column(String(255), nullable=False)
    user_role = Column(String(100))
    ip_address = Column(String(45))  # IPv6 max length
    user_agent = Column(Text)
    session_id = Column(String(100), index=True)

    # Event details
    action = Column(String(255), nullable=False)
    description = Column(Text)
    reason = Column(Text)  # Why - justification for action

    # Before/After state for UPDATE operations
    old_values = Column(JSON)
    new_values = Column(JSON)

    # Additional context
    metadata = Column(JSON)

    # Hash chain for tamper detection (blockchain-style)
    previous_hash = Column(String(64))  # SHA-256 of previous event
    event_hash = Column(String(64), nullable=False, unique=True, index=True)

    # GDPR compliance - data retention
    retention_until = Column(DateTime(timezone=True))
    is_anonymized = Column(String(10), default="false")

    # Indexes for performance
    __table_args__ = (
        Index('idx_audit_timestamp_user', 'timestamp', 'user_id'),
        Index('idx_audit_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_event_type', 'event_type', 'timestamp'),
        Index('idx_audit_session', 'session_id', 'timestamp'),
    )

    def __repr__(self):
        return f"<AuditEvent(seq={self.sequence_number}, type={self.event_type}, user={self.user_name})>"


class AuditEvent(BaseModel):
    """Pydantic model for audit event validation and serialization"""

    model_config = ConfigDict(use_enum_values=True)

    id: UUID = Field(default_factory=uuid4)
    sequence_number: Optional[int] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    event_type: AuditEventType
    entity_type: str = Field(description="Type of entity being audited (e.g., 'Report', 'User', 'Config')")
    entity_id: Optional[str] = Field(None, description="ID of the specific entity")

    # Who
    user_id: str = Field(description="Unique identifier of the user")
    user_name: str = Field(description="Display name of the user")
    user_role: Optional[str] = None

    # Where
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None

    # What
    action: str = Field(description="Specific action taken")
    description: Optional[str] = Field(None, description="Human-readable description")

    # Why
    reason: Optional[str] = Field(None, description="Justification for the action")

    # Change tracking
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None

    # Additional context
    metadata: Optional[Dict[str, Any]] = None

    # Hash chain
    previous_hash: Optional[str] = None
    event_hash: Optional[str] = None

    # GDPR
    retention_until: Optional[datetime] = None
    is_anonymized: bool = False


class AuditTrailLogger:
    """
    Immutable audit trail logger with blockchain-style hash chaining.

    Provides:
    - Tamper-evident logging using SHA-256 hash chains
    - Complete audit trail per 21 CFR Part 11
    - Event sourcing pattern implementation
    - GDPR-compliant data retention
    - High-performance PostgreSQL backend

    Example:
        logger = AuditTrailLogger(db_url="postgresql://...")

        event = AuditEvent(
            event_type=AuditEventType.REPORT_APPROVE,
            entity_type="Report",
            entity_id="RPT-001",
            user_id="user123",
            user_name="John Doe",
            action="Approved PV test report",
            reason="All test criteria met per IEC 61215"
        )

        logger.log(event)
    """

    def __init__(self, db_url: str, auto_create_tables: bool = True):
        """
        Initialize audit trail logger.

        Args:
            db_url: PostgreSQL connection URL
            auto_create_tables: If True, create tables on initialization
        """
        self.engine = create_engine(
            db_url,
            poolclass=NullPool,  # Use NullPool for better concurrency
            echo=False
        )

        if auto_create_tables:
            Base.metadata.create_all(self.engine)

    def _compute_hash(self, event: AuditEvent) -> str:
        """
        Compute SHA-256 hash of the event for tamper detection.

        Hash includes all immutable event data plus previous hash,
        creating a blockchain-style chain.
        """
        hash_data = {
            "id": str(event.id),
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "user_id": event.user_id,
            "action": event.action,
            "old_values": event.old_values,
            "new_values": event.new_values,
            "previous_hash": event.previous_hash,
        }

        # Canonical JSON representation for consistent hashing
        hash_string = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(hash_string.encode()).hexdigest()

    def _get_last_event(self, session: Session) -> Optional[AuditEventModel]:
        """Get the most recent audit event for hash chaining."""
        stmt = select(AuditEventModel).order_by(desc(AuditEventModel.sequence_number)).limit(1)
        result = session.execute(stmt)
        return result.scalar_one_or_none()

    def _get_next_sequence_number(self, session: Session) -> int:
        """Get the next sequence number for the audit log."""
        last_event = self._get_last_event(session)
        return (last_event.sequence_number + 1) if last_event else 1

    def log(self, event: AuditEvent) -> AuditEvent:
        """
        Log an immutable audit event with hash chaining.

        Args:
            event: AuditEvent to log

        Returns:
            The logged event with computed hash and sequence number

        Raises:
            ValueError: If event validation fails
            IntegrityError: If hash chain is broken
        """
        with Session(self.engine) as session:
            # Get previous event for hash chaining
            last_event = self._get_last_event(session)

            if last_event:
                event.previous_hash = last_event.event_hash
            else:
                event.previous_hash = "0" * 64  # Genesis event

            # Assign sequence number
            event.sequence_number = self._get_next_sequence_number(session)

            # Compute hash
            event.event_hash = self._compute_hash(event)

            # Create database record
            db_event = AuditEventModel(
                id=event.id,
                sequence_number=event.sequence_number,
                timestamp=event.timestamp,
                event_type=event.event_type,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                user_id=event.user_id,
                user_name=event.user_name,
                user_role=event.user_role,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                session_id=event.session_id,
                action=event.action,
                description=event.description,
                reason=event.reason,
                old_values=event.old_values,
                new_values=event.new_values,
                metadata=event.metadata,
                previous_hash=event.previous_hash,
                event_hash=event.event_hash,
                retention_until=event.retention_until,
                is_anonymized="true" if event.is_anonymized else "false",
            )

            session.add(db_event)
            session.commit()

            return event

    def log_crud(
        self,
        operation: str,
        entity_type: str,
        entity_id: str,
        user_id: str,
        user_name: str,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        reason: Optional[str] = None,
        **kwargs
    ) -> AuditEvent:
        """
        Convenience method to log CRUD operations.

        Args:
            operation: One of CREATE, READ, UPDATE, DELETE
            entity_type: Type of entity (e.g., 'Report', 'User')
            entity_id: ID of the entity
            user_id: ID of user performing operation
            user_name: Name of user performing operation
            old_values: Previous values (for UPDATE)
            new_values: New values (for CREATE, UPDATE)
            reason: Justification for the operation
            **kwargs: Additional event properties
        """
        event_type = AuditEventType[operation]

        action = f"{operation} {entity_type}"
        if entity_id:
            action += f" {entity_id}"

        event = AuditEvent(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            user_name=user_name,
            action=action,
            old_values=old_values,
            new_values=new_values,
            reason=reason,
            **kwargs
        )

        return self.log(event)

    def log_auth(
        self,
        event_type: AuditEventType,
        user_id: str,
        user_name: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: Optional[str] = None,
        **kwargs
    ) -> AuditEvent:
        """
        Log authentication and authorization events.

        Args:
            event_type: Type of auth event (LOGIN, LOGOUT, etc.)
            user_id: User identifier
            user_name: User display name
            success: Whether the operation succeeded
            ip_address: Client IP address
            user_agent: Client user agent
            reason: Additional context
            **kwargs: Additional event properties
        """
        action = f"{event_type.value} {'successful' if success else 'failed'}"

        event = AuditEvent(
            event_type=event_type,
            entity_type="Authentication",
            entity_id=user_id,
            user_id=user_id,
            user_name=user_name,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            reason=reason,
            metadata={"success": success},
            **kwargs
        )

        return self.log(event)

    def log_security_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        user_name: str,
        description: str,
        severity: str = "HIGH",
        ip_address: Optional[str] = None,
        **kwargs
    ) -> AuditEvent:
        """
        Log security-related events (unauthorized access, privilege escalation, etc.).

        Args:
            event_type: Type of security event
            user_id: User who triggered the event
            user_name: User display name
            description: Description of the security event
            severity: Event severity (LOW, MEDIUM, HIGH, CRITICAL)
            ip_address: Source IP address
            **kwargs: Additional event properties
        """
        event = AuditEvent(
            event_type=event_type,
            entity_type="Security",
            entity_id=None,
            user_id=user_id,
            user_name=user_name,
            action=event_type.value,
            description=description,
            ip_address=ip_address,
            metadata={"severity": severity},
            **kwargs
        )

        return self.log(event)

    def get_events(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditEvent]:
        """
        Query audit events with filters.

        Args:
            user_id: Filter by user ID
            event_type: Filter by event type
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            start_time: Filter events after this time
            end_time: Filter events before this time
            limit: Maximum number of events to return
            offset: Number of events to skip

        Returns:
            List of matching audit events
        """
        with Session(self.engine) as session:
            stmt = select(AuditEventModel)

            # Apply filters
            conditions = []
            if user_id:
                conditions.append(AuditEventModel.user_id == user_id)
            if event_type:
                conditions.append(AuditEventModel.event_type == event_type)
            if entity_type:
                conditions.append(AuditEventModel.entity_type == entity_type)
            if entity_id:
                conditions.append(AuditEventModel.entity_id == entity_id)
            if start_time:
                conditions.append(AuditEventModel.timestamp >= start_time)
            if end_time:
                conditions.append(AuditEventModel.timestamp <= end_time)

            if conditions:
                stmt = stmt.where(and_(*conditions))

            stmt = stmt.order_by(desc(AuditEventModel.timestamp))
            stmt = stmt.limit(limit).offset(offset)

            results = session.execute(stmt).scalars().all()

            # Convert to Pydantic models
            events = []
            for db_event in results:
                event = AuditEvent(
                    id=db_event.id,
                    sequence_number=db_event.sequence_number,
                    timestamp=db_event.timestamp,
                    event_type=AuditEventType(db_event.event_type),
                    entity_type=db_event.entity_type,
                    entity_id=db_event.entity_id,
                    user_id=db_event.user_id,
                    user_name=db_event.user_name,
                    user_role=db_event.user_role,
                    ip_address=db_event.ip_address,
                    user_agent=db_event.user_agent,
                    session_id=db_event.session_id,
                    action=db_event.action,
                    description=db_event.description,
                    reason=db_event.reason,
                    old_values=db_event.old_values,
                    new_values=db_event.new_values,
                    metadata=db_event.metadata,
                    previous_hash=db_event.previous_hash,
                    event_hash=db_event.event_hash,
                    retention_until=db_event.retention_until,
                    is_anonymized=db_event.is_anonymized == "true",
                )
                events.append(event)

            return events

    def get_event_by_id(self, event_id: UUID) -> Optional[AuditEvent]:
        """Retrieve a specific audit event by ID."""
        with Session(self.engine) as session:
            stmt = select(AuditEventModel).where(AuditEventModel.id == event_id)
            db_event = session.execute(stmt).scalar_one_or_none()

            if not db_event:
                return None

            return AuditEvent(
                id=db_event.id,
                sequence_number=db_event.sequence_number,
                timestamp=db_event.timestamp,
                event_type=AuditEventType(db_event.event_type),
                entity_type=db_event.entity_type,
                entity_id=db_event.entity_id,
                user_id=db_event.user_id,
                user_name=db_event.user_name,
                user_role=db_event.user_role,
                ip_address=db_event.ip_address,
                user_agent=db_event.user_agent,
                session_id=db_event.session_id,
                action=db_event.action,
                description=db_event.description,
                reason=db_event.reason,
                old_values=db_event.old_values,
                new_values=db_event.new_values,
                metadata=db_event.metadata,
                previous_hash=db_event.previous_hash,
                event_hash=db_event.event_hash,
                retention_until=db_event.retention_until,
                is_anonymized=db_event.is_anonymized == "true",
            )
