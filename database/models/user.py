"""
User Model

Manages user accounts, roles, permissions, and approval workflows for the test lab.
Supports multi-level review and approval processes for quality assurance.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from enum import Enum

from sqlmodel import SQLModel, Field, Relationship, Column, String, JSON
from sqlalchemy import Index, UniqueConstraint

if TYPE_CHECKING:
    from .audit import Audit


class UserRole(str, Enum):
    """User role definitions"""
    ADMIN = "admin"
    LAB_MANAGER = "lab_manager"
    TEST_ENGINEER = "test_engineer"
    REVIEWER = "reviewer"
    APPROVER = "approver"
    QUALITY_MANAGER = "quality_manager"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(SQLModel, table=True):
    """
    User model for authentication, authorization, and audit trails.

    Attributes:
        id: Unique user identifier
        username: Unique username for login
        email: User email address
        full_name: User's full name
        role: User role determining permissions
        status: Account status
        contact: Contact information (phone, extension, etc.)
        reviewer_flag: Whether user can perform reviews
        approver_flag: Whether user can approve reports
        approval_history: JSON array of approval actions
        signature_image_path: Path to digital signature image
        qualifications: User qualifications and certifications
        department: Department/team assignment
        employee_id: Employee ID number
        password_hash: Hashed password (stored securely)
        last_login: Last login timestamp
        failed_login_attempts: Count of failed login attempts
        account_locked_until: Account lock expiration timestamp
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "users"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Authentication
    username: str = Field(max_length=100, unique=True, index=True)
    email: str = Field(max_length=255, unique=True, index=True)
    password_hash: str = Field(max_length=255)

    # Personal information
    full_name: str = Field(max_length=200, index=True)
    employee_id: Optional[str] = Field(default=None, max_length=50, unique=True)
    department: Optional[str] = Field(default=None, max_length=100)

    # Role and permissions
    role: UserRole = Field(sa_column=Column(String(50)), index=True)
    status: UserStatus = Field(default=UserStatus.ACTIVE, sa_column=Column(String(50)))

    # Contact information
    contact: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Contact info: phone, mobile, extension, address"
    )

    # Review and approval flags
    reviewer_flag: bool = Field(default=False, index=True)
    approver_flag: bool = Field(default=False, index=True)

    # Approval history tracking
    approval_history: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Array of approval actions with report_id, action, timestamp"
    )

    # Digital signature
    signature_image_path: Optional[str] = Field(default=None, max_length=500)

    # Qualifications and certifications
    qualifications: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Certifications, training, qualifications"
    )

    # Security tracking
    last_login: Optional[datetime] = Field(default=None)
    failed_login_attempts: int = Field(default=0)
    account_locked_until: Optional[datetime] = Field(default=None)
    password_changed_at: Optional[datetime] = Field(default=None)

    # Additional information
    notes: Optional[str] = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    audit_logs: List["Audit"] = Relationship(back_populates="user")

    # Table constraints
    __table_args__ = (
        UniqueConstraint('username', name='uq_user_username'),
        UniqueConstraint('email', name='uq_user_email'),
        UniqueConstraint('employee_id', name='uq_user_employee_id'),
        Index('ix_user_role_status', 'role', 'status'),
        Index('ix_user_reviewer_approver', 'reviewer_flag', 'approver_flag'),
    )

    def can_review(self) -> bool:
        """Check if user has review permissions."""
        return self.reviewer_flag and self.status == UserStatus.ACTIVE

    def can_approve(self) -> bool:
        """Check if user has approval permissions."""
        return self.approver_flag and self.status == UserStatus.ACTIVE

    def is_active(self) -> bool:
        """Check if user account is active."""
        return self.status == UserStatus.ACTIVE

    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.account_locked_until is None:
            return False
        return datetime.utcnow() < self.account_locked_until

    def add_approval_action(self, report_id: int, action: str, comments: Optional[str] = None) -> None:
        """
        Add an approval action to the history.

        Args:
            report_id: ID of the report being approved
            action: Action taken (approved, rejected, returned)
            comments: Optional comments
        """
        if self.approval_history is None:
            self.approval_history = []

        approval_entry = {
            "report_id": report_id,
            "action": action,
            "timestamp": datetime.utcnow().isoformat(),
            "comments": comments
        }
        self.approval_history.append(approval_entry)
        self.updated_at = datetime.utcnow()

    def record_login(self, success: bool = True) -> None:
        """
        Record login attempt.

        Args:
            success: Whether login was successful
        """
        if success:
            self.last_login = datetime.utcnow()
            self.failed_login_attempts = 0
            self.updated_at = datetime.utcnow()
        else:
            self.failed_login_attempts += 1
            if self.failed_login_attempts >= 5:
                # Lock account for 30 minutes after 5 failed attempts
                from datetime import timedelta
                self.account_locked_until = datetime.utcnow() + timedelta(minutes=30)

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()

    class Config:
        json_schema_extra = {
            "example": {
                "username": "jsmith",
                "email": "jsmith@pvlab.com",
                "full_name": "John Smith",
                "employee_id": "EMP001",
                "role": "test_engineer",
                "status": "active",
                "reviewer_flag": True,
                "approver_flag": False,
                "contact": {
                    "phone": "+1-555-0100",
                    "mobile": "+1-555-0101",
                    "extension": "1234"
                },
                "department": "Testing Lab"
            }
        }
