"""
Audit Model

Comprehensive audit trail for all system actions, changes, and access.
Provides full traceability for ISO 17025 and quality management compliance.
"""

from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from enum import Enum

from sqlmodel import SQLModel, Field, Relationship, Column, String, JSON, Integer
from sqlalchemy import Index

if TYPE_CHECKING:
    from .user import User


class AuditAction(str, Enum):
    """Types of auditable actions"""
    # Create operations
    CREATE_SAMPLE = "create_sample"
    CREATE_TEST = "create_test"
    CREATE_REPORT = "create_report"
    CREATE_USER = "create_user"
    CREATE_EQUIPMENT = "create_equipment"

    # Update operations
    UPDATE_SAMPLE = "update_sample"
    UPDATE_TEST = "update_test"
    UPDATE_REPORT = "update_report"
    UPDATE_USER = "update_user"
    UPDATE_EQUIPMENT = "update_equipment"

    # Delete operations
    DELETE_SAMPLE = "delete_sample"
    DELETE_TEST = "delete_test"
    DELETE_REPORT = "delete_report"
    DELETE_USER = "delete_user"
    DELETE_EQUIPMENT = "delete_equipment"

    # Status changes
    CHANGE_SAMPLE_STATUS = "change_sample_status"
    CHANGE_TEST_STATUS = "change_test_status"
    CHANGE_REPORT_STATUS = "change_report_status"

    # Workflow actions
    SUBMIT_REPORT = "submit_report"
    REVIEW_REPORT = "review_report"
    APPROVE_REPORT = "approve_report"
    REJECT_REPORT = "reject_report"
    ISSUE_REPORT = "issue_report"
    REVISE_REPORT = "revise_report"

    # Test actions
    START_TEST = "start_test"
    COMPLETE_TEST = "complete_test"
    REVIEW_TEST = "review_test"
    ADD_TEST_READING = "add_test_reading"

    # Equipment actions
    CALIBRATE_EQUIPMENT = "calibrate_equipment"
    SERVICE_EQUIPMENT = "service_equipment"

    # Access and authentication
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    FAILED_LOGIN = "failed_login"
    PASSWORD_CHANGE = "password_change"
    PERMISSION_CHANGE = "permission_change"

    # Data export
    EXPORT_REPORT = "export_report"
    EXPORT_DATA = "export_data"

    # System actions
    BACKUP_DATABASE = "backup_database"
    RESTORE_DATABASE = "restore_database"
    SYSTEM_CONFIG_CHANGE = "system_config_change"

    # Custom action
    CUSTOM = "custom"


class AuditSeverity(str, Enum):
    """Severity level of audit event"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Audit(SQLModel, table=True):
    """
    Audit trail model for tracking all system actions and changes.

    Attributes:
        id: Unique audit record identifier
        user_id: Foreign key to User who performed action
        action: Type of action performed
        entity_type: Type of entity affected (sample, test, report, etc.)
        entity_id: ID of affected entity
        branch: Git branch or workflow branch (if applicable)
        timestamp: When action occurred
        ip_address: IP address of user
        user_agent: Browser/client user agent
        severity: Severity level of event
        description: Human-readable description
        pre_snapshot: State before change (JSON)
        post_snapshot: State after change (JSON)
        changes: Detailed field-level changes (JSON)
        success: Whether action succeeded
        error_message: Error message if action failed
        session_id: Session identifier for grouping related actions
        metadata: Additional metadata (compliance refs, etc.)
    """

    __tablename__ = "audit_logs"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # User and action
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    action: AuditAction = Field(sa_column=Column(String(100)), index=True)

    # Entity information
    entity_type: str = Field(max_length=50, index=True)
    entity_id: Optional[int] = Field(default=None, index=True)

    # Branch/workflow tracking
    branch: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Git branch or workflow branch identifier"
    )

    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Request information
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None, max_length=500)
    session_id: Optional[str] = Field(default=None, max_length=100, index=True)

    # Severity
    severity: AuditSeverity = Field(default=AuditSeverity.INFO, sa_column=Column(String(20)))

    # Description
    description: str = Field(max_length=1000)

    # State snapshots
    pre_snapshot: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Complete state before change"
    )

    post_snapshot: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Complete state after change"
    )

    # Detailed changes
    changes: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Field-level changes: {field: {old: value, new: value}}"
    )

    # Success tracking
    success: bool = Field(default=True)
    error_message: Optional[str] = Field(default=None)

    # Additional metadata
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Additional context: compliance refs, standards, reasons"
    )

    # Compliance tracking
    compliance_relevant: bool = Field(
        default=True,
        description="Whether this audit entry is relevant for compliance audits"
    )

    retention_years: int = Field(
        default=10,
        ge=1,
        description="Number of years to retain this audit record"
    )

    # Relationships
    user: Optional["User"] = Relationship(back_populates="audit_logs")

    # Table constraints
    __table_args__ = (
        Index('ix_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('ix_audit_entity', 'entity_type', 'entity_id'),
        Index('ix_audit_action_timestamp', 'action', 'timestamp'),
        Index('ix_audit_session', 'session_id', 'timestamp'),
        Index('ix_audit_severity_timestamp', 'severity', 'timestamp'),
        Index('ix_audit_compliance', 'compliance_relevant', 'timestamp'),
    )

    def calculate_changes(self, pre: Dict[str, Any], post: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate field-level changes between pre and post states.

        Args:
            pre: State before change
            post: State after change

        Returns:
            Dictionary of changes
        """
        changes = {}

        all_keys = set(pre.keys()) | set(post.keys())

        for key in all_keys:
            pre_val = pre.get(key)
            post_val = post.get(key)

            if pre_val != post_val:
                changes[key] = {
                    "old": pre_val,
                    "new": post_val
                }

        self.changes = changes
        return changes

    def is_within_retention_period(self) -> bool:
        """
        Check if audit record is still within retention period.

        Returns:
            True if within retention period, False otherwise
        """
        from datetime import timedelta
        retention_end = self.timestamp + timedelta(days=365 * self.retention_years)
        return datetime.utcnow() < retention_end

    @classmethod
    def log_action(
        cls,
        user_id: Optional[int],
        action: AuditAction,
        entity_type: str,
        entity_id: Optional[int],
        description: str,
        pre_snapshot: Optional[Dict[str, Any]] = None,
        post_snapshot: Optional[Dict[str, Any]] = None,
        branch: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> "Audit":
        """
        Create a new audit log entry.

        Args:
            user_id: ID of user performing action
            action: Type of action
            entity_type: Type of entity (sample, test, report, etc.)
            entity_id: ID of entity
            description: Human-readable description
            pre_snapshot: State before change
            post_snapshot: State after change
            branch: Branch identifier
            session_id: Session identifier
            ip_address: User IP address
            user_agent: User agent string
            severity: Event severity
            metadata: Additional metadata
            success: Whether action succeeded
            error_message: Error message if failed

        Returns:
            New Audit instance
        """
        audit = cls(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            pre_snapshot=pre_snapshot,
            post_snapshot=post_snapshot,
            branch=branch,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            severity=severity,
            metadata=metadata,
            success=success,
            error_message=error_message
        )

        # Calculate changes if both snapshots provided
        if pre_snapshot and post_snapshot:
            audit.calculate_changes(pre_snapshot, post_snapshot)

        return audit

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "action": "update_test",
                "entity_type": "test",
                "entity_id": 123,
                "timestamp": "2024-01-20T14:30:00",
                "description": "Updated test results and pass/fail status",
                "severity": "info",
                "changes": {
                    "pass_fail": {
                        "old": "pending",
                        "new": "pass"
                    },
                    "status": {
                        "old": "in_progress",
                        "new": "completed"
                    }
                },
                "success": True
            }
        }
