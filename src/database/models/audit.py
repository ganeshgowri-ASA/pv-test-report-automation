"""
Audit Trail and Data Lineage Models

Implements immutable audit logging and complete data traceability
compliant with ISO 17025, 21 CFR Part 11, and NABL requirements.
"""

import uuid
from datetime import datetime
import enum
from sqlalchemy import Column, String, DateTime, Text, JSON, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
from src.database.base import Base


class AuditAction(str, enum.Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    APPROVE = "approve"
    REJECT = "reject"
    EXPORT = "export"


class AuditLog(Base):
    """Immutable Audit Trail - 21 CFR Part 11 compliant"""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Actor information
    user_id = Column(UUID(as_uuid=True), nullable=True)
    username = Column(String(50), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Action details
    action = Column(Enum(AuditAction), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    entity_name = Column(String(255), nullable=True)

    # Change tracking
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    changes = Column(JSON, nullable=True)

    # Context
    description = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)

    # Hash for integrity verification
    record_hash = Column(String(64), nullable=False)
    previous_hash = Column(String(64), nullable=True)

    __table_args__ = (
        Index('idx_audit_user_time', 'user_id', 'timestamp'),
        Index('idx_audit_entity', 'entity_type', 'entity_id'),
    )


class DataLineage(Base):
    """Data Lineage - Complete provenance tracking"""
    __tablename__ = "data_lineage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Source information
    source_type = Column(String(50), nullable=False)
    source_id = Column(UUID(as_uuid=True), nullable=False)
    source_file = Column(String(500), nullable=True)
    source_checksum = Column(String(64), nullable=True)

    # Derived information
    derived_type = Column(String(50), nullable=False)
    derived_id = Column(UUID(as_uuid=True), nullable=False)

    # Transformation
    transformation = Column(String(255), nullable=False)
    transformation_params = Column(JSON, nullable=True)

    # Provenance chain
    lineage_path = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)
