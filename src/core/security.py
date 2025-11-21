"""
Security Core Implementation
Authentication, Authorization, and Audit Trail
ISO 17025 Compliant Security Controls
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum
import jwt
import bcrypt


class Permission(Enum):
    """System permissions"""
    VIEW_TESTS = "view_tests"
    CREATE_TESTS = "create_tests"
    EXECUTE_TESTS = "execute_tests"
    REVIEW_REPORTS = "review_reports"
    APPROVE_REPORTS = "approve_reports"
    MANAGE_EQUIPMENT = "manage_equipment"
    MANAGE_USERS = "manage_users"
    EXPORT_DATA = "export_data"
    VIEW_AUDIT = "view_audit"
    SYSTEM_ADMIN = "system_admin"


class Role(Enum):
    """User roles with associated permissions"""
    GUEST = "guest"
    TECHNICIAN = "technician"
    ENGINEER = "engineer"
    REVIEWER = "reviewer"
    APPROVER = "approver"
    ADMIN = "admin"


# Role-Permission Matrix
ROLE_PERMISSIONS: Dict[Role, List[Permission]] = {
    Role.GUEST: [
        Permission.VIEW_TESTS,
    ],
    Role.TECHNICIAN: [
        Permission.VIEW_TESTS,
        Permission.CREATE_TESTS,
        Permission.EXECUTE_TESTS,
    ],
    Role.ENGINEER: [
        Permission.VIEW_TESTS,
        Permission.CREATE_TESTS,
        Permission.EXECUTE_TESTS,
        Permission.MANAGE_EQUIPMENT,
        Permission.EXPORT_DATA,
    ],
    Role.REVIEWER: [
        Permission.VIEW_TESTS,
        Permission.REVIEW_REPORTS,
        Permission.EXPORT_DATA,
        Permission.VIEW_AUDIT,
    ],
    Role.APPROVER: [
        Permission.VIEW_TESTS,
        Permission.REVIEW_REPORTS,
        Permission.APPROVE_REPORTS,
        Permission.EXPORT_DATA,
        Permission.VIEW_AUDIT,
    ],
    Role.ADMIN: [perm for perm in Permission],  # All permissions
}


@dataclass
class User:
    """User data model"""
    username: str
    email: str
    role: Role
    full_name: str
    employee_id: Optional[str] = None
    department: Optional[str] = None
    is_active: bool = True
    password_hash: Optional[str] = None
    created_at: datetime = None
    last_login: Optional[datetime] = None
    mfa_enabled: bool = False

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return permission in ROLE_PERMISSIONS.get(self.role, [])

    def get_permissions(self) -> List[Permission]:
        """Get all permissions for user's role"""
        return ROLE_PERMISSIONS.get(self.role, [])


class PasswordManager:
    """Secure password hashing and validation"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        password_bytes = password.encode('utf-8')
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        password_bytes = password.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """Validate password meets security requirements"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

        if not (has_upper and has_lower and has_digit):
            return False, "Password must contain uppercase, lowercase, and numbers"

        return True, "Password meets requirements"

    @staticmethod
    def generate_random_password(length: int = 16) -> str:
        """Generate secure random password"""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))


class TokenManager:
    """JWT token generation and validation"""

    def __init__(self, secret_key: str, algorithm: str = "HS256", expiration_minutes: int = 60):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expiration_minutes = expiration_minutes

    def generate_token(self, user: User) -> str:
        """Generate JWT token for user"""
        payload = {
            'username': user.username,
            'email': user.email,
            'role': user.role.value,
            'exp': datetime.utcnow() + timedelta(minutes=self.expiration_minutes),
            'iat': datetime.utcnow(),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def generate_api_key(self) -> str:
        """Generate API key for external integrations"""
        return secrets.token_urlsafe(32)


@dataclass
class AuditEvent:
    """Audit trail event"""
    timestamp: datetime
    user: str
    action: str
    resource: str
    details: Optional[Dict] = None
    ip_address: Optional[str] = None
    success: bool = True

    def to_dict(self) -> Dict:
        """Convert to dictionary for logging"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'user': self.user,
            'action': self.action,
            'resource': self.resource,
            'details': self.details,
            'ip_address': self.ip_address,
            'success': self.success,
        }


class AuditLogger:
    """ISO 17025 compliant audit logging"""

    def __init__(self):
        self.events: List[AuditEvent] = []

    def log_event(
        self,
        user: str,
        action: str,
        resource: str,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        success: bool = True
    ):
        """Log an audit event"""
        event = AuditEvent(
            timestamp=datetime.utcnow(),
            user=user,
            action=action,
            resource=resource,
            details=details,
            ip_address=ip_address,
            success=success
        )
        self.events.append(event)

        # In production, write to database or file
        print(f"[AUDIT] {event.timestamp} | {user} | {action} | {resource} | Success: {success}")

    def log_login(self, username: str, success: bool, ip_address: Optional[str] = None):
        """Log login attempt"""
        self.log_event(
            user=username,
            action="LOGIN",
            resource="Authentication",
            success=success,
            ip_address=ip_address
        )

    def log_data_access(self, username: str, resource_type: str, resource_id: str):
        """Log data access"""
        self.log_event(
            user=username,
            action="ACCESS",
            resource=f"{resource_type}:{resource_id}"
        )

    def log_data_modification(self, username: str, resource_type: str, resource_id: str, changes: Dict):
        """Log data modification"""
        self.log_event(
            user=username,
            action="MODIFY",
            resource=f"{resource_type}:{resource_id}",
            details={'changes': changes}
        )

    def log_export(self, username: str, export_format: str, resource_id: str):
        """Log data export"""
        self.log_event(
            user=username,
            action="EXPORT",
            resource=resource_id,
            details={'format': export_format}
        )

    def log_approval(self, username: str, resource_id: str, approved: bool):
        """Log approval action"""
        self.log_event(
            user=username,
            action="APPROVE" if approved else "REJECT",
            resource=resource_id
        )

    def get_events(
        self,
        user: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditEvent]:
        """Query audit events with filters"""
        filtered = self.events

        if user:
            filtered = [e for e in filtered if e.user == user]
        if action:
            filtered = [e for e in filtered if e.action == action]
        if start_date:
            filtered = [e for e in filtered if e.timestamp >= start_date]
        if end_date:
            filtered = [e for e in filtered if e.timestamp <= end_date]

        return filtered


class DataIntegrityValidator:
    """Ensure data integrity through checksums"""

    @staticmethod
    def generate_checksum(data: bytes) -> str:
        """Generate SHA-256 checksum"""
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def verify_checksum(data: bytes, expected_checksum: str) -> bool:
        """Verify data integrity"""
        actual_checksum = DataIntegrityValidator.generate_checksum(data)
        return actual_checksum == expected_checksum

    @staticmethod
    def generate_file_hash(file_path: str) -> str:
        """Generate hash for file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


# Global instances
audit_logger = AuditLogger()
password_manager = PasswordManager()


def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    def decorator(func):
        def wrapper(user: User, *args, **kwargs):
            if not user.has_permission(permission):
                raise PermissionError(f"User {user.username} lacks permission: {permission.value}")
            return func(user, *args, **kwargs)
        return wrapper
    return decorator


def authenticate_user(username: str, password: str, user_database: Dict[str, User]) -> Optional[User]:
    """Authenticate user with username and password"""
    user = user_database.get(username)

    if not user or not user.is_active:
        audit_logger.log_login(username, success=False)
        return None

    if user.password_hash and password_manager.verify_password(password, user.password_hash):
        user.last_login = datetime.utcnow()
        audit_logger.log_login(username, success=True)
        return user

    audit_logger.log_login(username, success=False)
    return None
