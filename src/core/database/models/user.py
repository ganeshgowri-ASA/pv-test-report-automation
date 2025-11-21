"""
User, Role, and Permission Models
==================================

Implements RBAC (Role-Based Access Control) for the system.

Features:
    - User authentication and authorization
    - Role-based permissions
    - Password hashing and validation
    - Session management
    - Audit trail integration
    - API key management

Compliance:
    - ISO 17025: Personnel competence and authorization
    - 21 CFR Part 11: Electronic signatures and user authentication
    - NABL: Access control and data security
"""

import uuid
from datetime import datetime
from typing import Optional, List
import enum

from sqlalchemy import Column, String, DateTime, Boolean, Enum, ForeignKey, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database.base import Base


class UserRole(str, enum.Enum):
    """System roles with hierarchical permissions"""
    SUPER_ADMIN = "super_admin"
    LAB_MANAGER = "lab_manager"
    QUALITY_MANAGER = "quality_manager"
    TEST_ENGINEER = "test_engineer"
    TECHNICIAN = "technician"
    REVIEWER = "reviewer"
    APPROVER = "approver"
    VIEWER = "viewer"
    CUSTOMER = "customer"


class UserStatus(str, enum.Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_ACTIVATION = "pending_activation"


# Association table for many-to-many User-Role relationship
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True),
    Column("assigned_at", DateTime, default=datetime.utcnow),
    Column("assigned_by", UUID(as_uuid=True), ForeignKey("users.id"))
)

# Association table for Role-Permission relationship
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", UUID(as_uuid=True), ForeignKey("permissions.id"), primary_key=True)
)


class User(Base):
    """
    User Model

    Represents system users with authentication and authorization.

    Attributes:
        id: Primary key
        username: Unique username
        email: User email address
        password_hash: Hashed password
        first_name: User's first name
        last_name: User's last name
        employee_id: Employee identifier
        department: Department/unit
        position: Job title/position
        phone: Contact phone
        status: Account status
        email_verified: Email verification status
        last_login: Last login timestamp
        failed_login_attempts: Failed login counter
        locked_until: Account lock timestamp
        password_changed_at: Last password change
        must_change_password: Force password change flag
        api_key_hash: Hashed API key for programmatic access
        signature_image: Electronic signature image URL
        roles: Assigned roles
        permissions: Direct permissions (in addition to role permissions)
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    employee_id = Column(String(50), unique=True, nullable=True)
    department = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)

    # Account status
    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.PENDING_ACTIVATION)
    email_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Security
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
    must_change_password = Column(Boolean, default=False)

    # API access
    api_key_hash = Column(String(255), nullable=True)
    api_key_created_at = Column(DateTime, nullable=True)
    api_key_expires_at = Column(DateTime, nullable=True)

    # Electronic signature (21 CFR Part 11)
    signature_image = Column(String(500), nullable=True)
    signature_meaning = Column(String(255), nullable=True)

    # Certifications and qualifications
    certifications = Column(JSON, nullable=True)
    training_records = Column(JSON, nullable=True)

    # Preferences
    preferences = Column(JSON, nullable=True)
    notification_settings = Column(JSON, nullable=True)

    # Audit
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class Role(Base):
    """
    Role Model

    Represents user roles for RBAC.
    """

    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_system_role = Column(Boolean, default=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")


class Permission(Base):
    """
    Permission Model

    Granular permissions for fine-grained access control.
    """

    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    resource = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
