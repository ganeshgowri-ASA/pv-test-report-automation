"""
SQLAlchemy models for workflow management system.

This module defines database models for:
- Workflow definitions and instances
- Approval records and history
- Notification logs and preferences
- State transitions and audit trails

Compliant with ISO 17025 requirements for approval tracking and audit trails.
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean,
    ForeignKey, Enum, JSON, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()


class WorkflowStatus(PyEnum):
    """Workflow execution status enumeration."""
    DRAFT = "draft"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"
    COMPLETED = "completed"


class ApprovalStatus(PyEnum):
    """Approval record status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DELEGATED = "delegated"
    SKIPPED = "skipped"


class NotificationStatus(PyEnum):
    """Notification delivery status enumeration."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class NotificationChannel(PyEnum):
    """Notification delivery channel enumeration."""
    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    SMS = "sms"
    IN_APP = "in_app"


class WorkflowDefinition(Base):
    """
    Workflow template definition.

    Defines reusable workflow templates with approval steps,
    routing rules, and notification configurations.
    """
    __tablename__ = "workflow_definitions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    version = Column(String(50), nullable=False, default="1.0.0")
    category = Column(String(100))  # e.g., "report_approval", "calibration_approval"

    # Workflow configuration
    config = Column(JSON, nullable=False)  # Approval steps, routing rules, etc.

    # Status and metadata
    is_active = Column(Boolean, default=True)
    is_iso_compliant = Column(Boolean, default=True)
    requires_digital_signature = Column(Boolean, default=False)

    # Audit fields
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_by = Column(String(255))
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    instances = relationship("WorkflowInstance", back_populates="definition", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_workflow_def_name", "name"),
        Index("idx_workflow_def_category", "category"),
    )

    def __repr__(self):
        return f"<WorkflowDefinition(id={self.id}, name='{self.name}', version='{self.version}')>"


class WorkflowInstance(Base):
    """
    Workflow execution instance.

    Represents a specific execution of a workflow definition
    for a particular entity (e.g., test report, calibration record).
    """
    __tablename__ = "workflow_instances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    definition_id = Column(Integer, ForeignKey("workflow_definitions.id"), nullable=False)

    # Instance identification
    entity_type = Column(String(100), nullable=False)  # e.g., "TestReport", "CalibrationRecord"
    entity_id = Column(String(255), nullable=False)
    reference_number = Column(String(100))  # Human-readable reference

    # Current state
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.DRAFT, nullable=False)
    current_step = Column(Integer, default=0)
    current_approvers = Column(JSON)  # List of current pending approvers

    # Workflow data
    context_data = Column(JSON)  # Additional context for workflow execution

    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    due_date = Column(DateTime)

    # Priority and escalation
    priority = Column(Integer, default=0)  # Higher number = higher priority
    escalation_level = Column(Integer, default=0)
    escalated_at = Column(DateTime)

    # Audit fields
    initiated_by = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    definition = relationship("WorkflowDefinition", back_populates="instances")
    approvals = relationship("ApprovalRecord", back_populates="workflow", cascade="all, delete-orphan")
    state_history = relationship("StateTransition", back_populates="workflow", cascade="all, delete-orphan")
    notifications = relationship("NotificationLog", back_populates="workflow", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_workflow_inst_entity", "entity_type", "entity_id"),
        Index("idx_workflow_inst_status", "status"),
        Index("idx_workflow_inst_ref", "reference_number"),
    )

    @hybrid_property
    def is_overdue(self) -> bool:
        """Check if workflow is overdue."""
        if self.due_date and self.status in [WorkflowStatus.PENDING, WorkflowStatus.IN_PROGRESS]:
            return datetime.utcnow() > self.due_date
        return False

    def __repr__(self):
        return f"<WorkflowInstance(id={self.id}, entity='{self.entity_type}:{self.entity_id}', status='{self.status.value}')>"


class ApprovalRecord(Base):
    """
    Approval record for workflow steps.

    Tracks individual approvals required for workflow progression.
    Maintains complete audit trail for ISO 17025 compliance.
    """
    __tablename__ = "approval_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(Integer, ForeignKey("workflow_instances.id"), nullable=False)

    # Approval step information
    step_number = Column(Integer, nullable=False)
    step_name = Column(String(255), nullable=False)
    approval_level = Column(Integer, default=1)  # Multi-level approval support

    # Approver information
    assigned_to = Column(String(255), nullable=False)  # User ID or role
    assigned_role = Column(String(100))  # Role-based assignment
    delegated_from = Column(String(255))  # If approval was delegated

    # Approval decision
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False)
    decision = Column(String(50))  # "approved", "rejected", etc.
    comments = Column(Text)

    # Digital signature support
    signature_hash = Column(String(512))  # Cryptographic signature
    signature_metadata = Column(JSON)  # Signature details, certificate info, etc.

    # Timing
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reviewed_at = Column(DateTime)
    due_at = Column(DateTime)

    # Audit fields
    reviewed_by = Column(String(255))  # Actual reviewer (may differ from assigned_to)
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(String(512))

    # Metadata
    metadata = Column(JSON)  # Additional approval context

    # Relationships
    workflow = relationship("WorkflowInstance", back_populates="approvals")

    __table_args__ = (
        Index("idx_approval_workflow", "workflow_id"),
        Index("idx_approval_assignee", "assigned_to"),
        Index("idx_approval_status", "status"),
    )

    @hybrid_property
    def is_overdue(self) -> bool:
        """Check if approval is overdue."""
        if self.due_at and self.status == ApprovalStatus.PENDING:
            return datetime.utcnow() > self.due_at
        return False

    def __repr__(self):
        return f"<ApprovalRecord(id={self.id}, workflow_id={self.workflow_id}, step='{self.step_name}', status='{self.status.value}')>"


class StateTransition(Base):
    """
    Workflow state transition history.

    Maintains complete audit trail of all state changes
    for compliance and debugging purposes.
    """
    __tablename__ = "state_transitions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(Integer, ForeignKey("workflow_instances.id"), nullable=False)

    # State change information
    from_state = Column(String(50))
    to_state = Column(String(50), nullable=False)
    event = Column(String(100))  # Triggering event

    # Context
    triggered_by = Column(String(255), nullable=False)
    reason = Column(Text)
    metadata = Column(JSON)

    # Timing
    transitioned_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    workflow = relationship("WorkflowInstance", back_populates="state_history")

    __table_args__ = (
        Index("idx_state_transition_workflow", "workflow_id"),
        Index("idx_state_transition_time", "transitioned_at"),
    )

    def __repr__(self):
        return f"<StateTransition(id={self.id}, workflow_id={self.workflow_id}, {self.from_state}->{self.to_state})>"


class NotificationLog(Base):
    """
    Notification delivery log.

    Tracks all notifications sent through the system
    for audit and delivery tracking purposes.
    """
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(Integer, ForeignKey("workflow_instances.id"), nullable=True)

    # Notification details
    channel = Column(Enum(NotificationChannel), nullable=False)
    recipient = Column(String(255), nullable=False)  # Email, phone, user ID, etc.
    subject = Column(String(500))
    message = Column(Text, nullable=False)

    # Template information
    template_name = Column(String(255))
    template_vars = Column(JSON)

    # Delivery status
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Delivery tracking
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    failed_at = Column(DateTime)
    error_message = Column(Text)

    # External tracking
    external_id = Column(String(255))  # ID from email service, Slack, etc.
    external_response = Column(JSON)

    # Metadata
    priority = Column(Integer, default=0)
    metadata = Column(JSON)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    workflow = relationship("WorkflowInstance", back_populates="notifications")

    __table_args__ = (
        Index("idx_notification_workflow", "workflow_id"),
        Index("idx_notification_recipient", "recipient"),
        Index("idx_notification_status", "status"),
        Index("idx_notification_created", "created_at"),
    )

    def __repr__(self):
        return f"<NotificationLog(id={self.id}, channel='{self.channel.value}', recipient='{self.recipient}', status='{self.status.value}')>"


class NotificationPreference(Base):
    """
    User notification preferences.

    Allows users to configure their notification preferences
    per channel and event type.
    """
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False)

    # Channel preferences
    channel = Column(Enum(NotificationChannel), nullable=False)
    enabled = Column(Boolean, default=True)

    # Event type preferences
    event_types = Column(JSON)  # List of event types to receive notifications for

    # Contact information
    contact_info = Column(String(500))  # Email, phone, Slack handle, etc.

    # Preferences
    quiet_hours_start = Column(String(5))  # HH:MM format
    quiet_hours_end = Column(String(5))  # HH:MM format
    timezone = Column(String(50), default="UTC")

    # Metadata
    metadata = Column(JSON)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "channel", name="uq_user_channel"),
        Index("idx_notification_pref_user", "user_id"),
    )

    def __repr__(self):
        return f"<NotificationPreference(user_id='{self.user_id}', channel='{self.channel.value}', enabled={self.enabled})>"


class NotificationSubscription(Base):
    """
    Workflow notification subscriptions.

    Allows users to subscribe to notifications for specific
    workflows or workflow types.
    """
    __tablename__ = "notification_subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False)

    # Subscription scope
    workflow_definition_id = Column(Integer, ForeignKey("workflow_definitions.id"), nullable=True)
    workflow_instance_id = Column(Integer, ForeignKey("workflow_instances.id"), nullable=True)
    entity_type = Column(String(100))  # Subscribe to all workflows for entity type

    # Subscription preferences
    event_types = Column(JSON)  # Specific events to be notified about
    channels = Column(JSON)  # Preferred notification channels

    # Status
    is_active = Column(Boolean, default=True)

    # Audit fields
    subscribed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    unsubscribed_at = Column(DateTime)

    __table_args__ = (
        Index("idx_subscription_user", "user_id"),
        Index("idx_subscription_workflow_def", "workflow_definition_id"),
        Index("idx_subscription_workflow_inst", "workflow_instance_id"),
    )

    def __repr__(self):
        return f"<NotificationSubscription(user_id='{self.user_id}', active={self.is_active})>"
