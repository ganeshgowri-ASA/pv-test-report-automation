"""
Role-Based Access Control (RBAC) for PV Test Report Automation
Implements hierarchical roles and granular permissions
ISO 17025 and 21 CFR Part 11 compliant access control
"""

from enum import Enum
from typing import List, Set, Optional, Dict, Any, Callable
from functools import wraps
from datetime import datetime

from pydantic import BaseModel, Field
from fastapi import HTTPException, status

from .auth import User, get_audit_logger, CryptoAlgorithm


class Permission(str, Enum):
    """
    System permissions for granular access control
    Aligned with ISO 17025 and 21 CFR Part 11 requirements
    """
    # Test Management
    CREATE_TEST = "create_test"
    EXECUTE_TEST = "execute_test"
    VIEW_TEST = "view_test"
    EDIT_TEST = "edit_test"
    DELETE_TEST = "delete_test"

    # Report Management
    CREATE_REPORT = "create_report"
    REVIEW_REPORT = "review_report"
    APPROVE_REPORT = "approve_report"
    PUBLISH_REPORT = "publish_report"
    VIEW_REPORT = "view_report"
    EDIT_REPORT = "edit_report"
    DELETE_REPORT = "delete_report"
    SIGN_REPORT = "sign_report"  # 21 CFR Part 11 electronic signature

    # Audit and Compliance
    VIEW_AUDIT = "view_audit"
    EXPORT_AUDIT = "export_audit"
    MANAGE_AUDIT = "manage_audit"

    # User Management
    MANAGE_USERS = "manage_users"
    CREATE_USER = "create_user"
    EDIT_USER = "edit_user"
    DELETE_USER = "delete_user"
    ASSIGN_ROLES = "assign_roles"
    VIEW_USERS = "view_users"

    # Equipment Management
    MANAGE_EQUIPMENT = "manage_equipment"
    CREATE_EQUIPMENT = "create_equipment"
    EDIT_EQUIPMENT = "edit_equipment"
    DELETE_EQUIPMENT = "delete_equipment"
    CALIBRATE_EQUIPMENT = "calibrate_equipment"
    VIEW_EQUIPMENT = "view_equipment"

    # System Configuration
    MANAGE_SETTINGS = "manage_settings"
    VIEW_SETTINGS = "view_settings"
    MANAGE_API_KEYS = "manage_api_keys"

    # Data Management
    EXPORT_DATA = "export_data"
    IMPORT_DATA = "import_data"
    DELETE_DATA = "delete_data"
    BACKUP_DATA = "backup_data"

    # Quality Control
    CREATE_QC_CHECK = "create_qc_check"
    PERFORM_QC_CHECK = "perform_qc_check"
    APPROVE_QC_CHECK = "approve_qc_check"
    VIEW_QC_CHECK = "view_qc_check"


class Role(str, Enum):
    """
    Predefined system roles with hierarchical permissions
    """
    ADMIN = "admin"
    LAB_MANAGER = "lab_manager"
    TECHNICIAN = "technician"
    REVIEWER = "reviewer"
    APPROVER = "approver"
    AUDITOR = "auditor"
    VIEWER = "viewer"


class RoleDefinition(BaseModel):
    """Role definition with permissions and metadata"""
    role: Role = Field(..., description="Role identifier")
    display_name: str = Field(..., description="Human-readable role name")
    description: str = Field(..., description="Role description")
    permissions: Set[Permission] = Field(..., description="Set of permissions")
    inherits_from: Optional[List[Role]] = Field(None, description="Parent roles to inherit from")
    level: int = Field(..., description="Hierarchical level (higher = more privileged)")
    is_system_role: bool = Field(default=True, description="Whether role is system-defined")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PermissionCheck(BaseModel):
    """Result of permission check operation"""
    granted: bool = Field(..., description="Whether permission is granted")
    reason: Optional[str] = Field(None, description="Reason for denial")
    user_id: str = Field(..., description="User being checked")
    permission: Permission = Field(..., description="Permission being checked")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ISO 17025 and 21 CFR Part 11 compliant role definitions
ROLE_DEFINITIONS: Dict[Role, RoleDefinition] = {
    Role.ADMIN: RoleDefinition(
        role=Role.ADMIN,
        display_name="System Administrator",
        description="Full system access with all permissions",
        permissions={
            # All permissions
            Permission.CREATE_TEST, Permission.EXECUTE_TEST, Permission.VIEW_TEST,
            Permission.EDIT_TEST, Permission.DELETE_TEST,
            Permission.CREATE_REPORT, Permission.REVIEW_REPORT, Permission.APPROVE_REPORT,
            Permission.PUBLISH_REPORT, Permission.VIEW_REPORT, Permission.EDIT_REPORT,
            Permission.DELETE_REPORT, Permission.SIGN_REPORT,
            Permission.VIEW_AUDIT, Permission.EXPORT_AUDIT, Permission.MANAGE_AUDIT,
            Permission.MANAGE_USERS, Permission.CREATE_USER, Permission.EDIT_USER,
            Permission.DELETE_USER, Permission.ASSIGN_ROLES, Permission.VIEW_USERS,
            Permission.MANAGE_EQUIPMENT, Permission.CREATE_EQUIPMENT, Permission.EDIT_EQUIPMENT,
            Permission.DELETE_EQUIPMENT, Permission.CALIBRATE_EQUIPMENT, Permission.VIEW_EQUIPMENT,
            Permission.MANAGE_SETTINGS, Permission.VIEW_SETTINGS, Permission.MANAGE_API_KEYS,
            Permission.EXPORT_DATA, Permission.IMPORT_DATA, Permission.DELETE_DATA,
            Permission.BACKUP_DATA,
            Permission.CREATE_QC_CHECK, Permission.PERFORM_QC_CHECK,
            Permission.APPROVE_QC_CHECK, Permission.VIEW_QC_CHECK,
        },
        level=100,
        is_system_role=True
    ),

    Role.LAB_MANAGER: RoleDefinition(
        role=Role.LAB_MANAGER,
        display_name="Laboratory Manager",
        description="Manages laboratory operations, equipment, and personnel",
        permissions={
            Permission.CREATE_TEST, Permission.EXECUTE_TEST, Permission.VIEW_TEST,
            Permission.EDIT_TEST, Permission.DELETE_TEST,
            Permission.CREATE_REPORT, Permission.REVIEW_REPORT, Permission.APPROVE_REPORT,
            Permission.PUBLISH_REPORT, Permission.VIEW_REPORT, Permission.EDIT_REPORT,
            Permission.SIGN_REPORT,
            Permission.VIEW_AUDIT, Permission.EXPORT_AUDIT,
            Permission.CREATE_USER, Permission.EDIT_USER, Permission.VIEW_USERS,
            Permission.ASSIGN_ROLES,
            Permission.MANAGE_EQUIPMENT, Permission.CREATE_EQUIPMENT, Permission.EDIT_EQUIPMENT,
            Permission.CALIBRATE_EQUIPMENT, Permission.VIEW_EQUIPMENT,
            Permission.VIEW_SETTINGS,
            Permission.EXPORT_DATA, Permission.IMPORT_DATA,
            Permission.CREATE_QC_CHECK, Permission.PERFORM_QC_CHECK,
            Permission.APPROVE_QC_CHECK, Permission.VIEW_QC_CHECK,
        },
        level=80,
        is_system_role=True
    ),

    Role.TECHNICIAN: RoleDefinition(
        role=Role.TECHNICIAN,
        display_name="Laboratory Technician",
        description="Performs tests and creates reports",
        permissions={
            Permission.CREATE_TEST, Permission.EXECUTE_TEST, Permission.VIEW_TEST,
            Permission.EDIT_TEST,
            Permission.CREATE_REPORT, Permission.VIEW_REPORT, Permission.EDIT_REPORT,
            Permission.VIEW_EQUIPMENT, Permission.EDIT_EQUIPMENT,
            Permission.EXPORT_DATA,
            Permission.CREATE_QC_CHECK, Permission.PERFORM_QC_CHECK, Permission.VIEW_QC_CHECK,
        },
        level=40,
        is_system_role=True
    ),

    Role.REVIEWER: RoleDefinition(
        role=Role.REVIEWER,
        display_name="Technical Reviewer",
        description="Reviews and validates test reports for technical accuracy",
        permissions={
            Permission.VIEW_TEST, Permission.EDIT_TEST,
            Permission.REVIEW_REPORT, Permission.VIEW_REPORT, Permission.EDIT_REPORT,
            Permission.SIGN_REPORT,
            Permission.VIEW_AUDIT,
            Permission.VIEW_EQUIPMENT,
            Permission.EXPORT_DATA,
            Permission.VIEW_QC_CHECK, Permission.APPROVE_QC_CHECK,
        },
        level=60,
        is_system_role=True
    ),

    Role.APPROVER: RoleDefinition(
        role=Role.APPROVER,
        display_name="Report Approver",
        description="Final approval authority for test reports (21 CFR Part 11)",
        permissions={
            Permission.VIEW_TEST,
            Permission.REVIEW_REPORT, Permission.APPROVE_REPORT, Permission.PUBLISH_REPORT,
            Permission.VIEW_REPORT, Permission.SIGN_REPORT,
            Permission.VIEW_AUDIT, Permission.EXPORT_AUDIT,
            Permission.VIEW_EQUIPMENT,
            Permission.EXPORT_DATA,
            Permission.VIEW_QC_CHECK, Permission.APPROVE_QC_CHECK,
        },
        level=70,
        is_system_role=True
    ),

    Role.AUDITOR: RoleDefinition(
        role=Role.AUDITOR,
        display_name="Quality Auditor",
        description="Audits system operations and maintains compliance records",
        permissions={
            Permission.VIEW_TEST,
            Permission.VIEW_REPORT,
            Permission.VIEW_AUDIT, Permission.EXPORT_AUDIT, Permission.MANAGE_AUDIT,
            Permission.VIEW_USERS,
            Permission.VIEW_EQUIPMENT,
            Permission.VIEW_SETTINGS,
            Permission.EXPORT_DATA,
            Permission.VIEW_QC_CHECK,
        },
        level=50,
        is_system_role=True
    ),

    Role.VIEWER: RoleDefinition(
        role=Role.VIEWER,
        display_name="Read-Only Viewer",
        description="View-only access to tests and reports",
        permissions={
            Permission.VIEW_TEST,
            Permission.VIEW_REPORT,
            Permission.VIEW_EQUIPMENT,
            Permission.VIEW_QC_CHECK,
        },
        level=10,
        is_system_role=True
    ),
}


class RBACManager:
    """
    Role-Based Access Control Manager
    Handles permission checks, role assignments, and audit logging
    """

    def __init__(self):
        """Initialize RBAC manager"""
        self.role_definitions = ROLE_DEFINITIONS.copy()
        self.custom_roles: Dict[str, RoleDefinition] = {}
        self._audit_logger = get_audit_logger()

    def get_role_definition(self, role: Role) -> Optional[RoleDefinition]:
        """
        Get role definition by role enum

        Args:
            role: Role enum value

        Returns:
            RoleDefinition or None if not found
        """
        return self.role_definitions.get(role)

    def get_role_permissions(self, role: Role) -> Set[Permission]:
        """
        Get all permissions for a role, including inherited permissions

        Args:
            role: Role enum value

        Returns:
            Set of all permissions for the role
        """
        role_def = self.get_role_definition(role)
        if not role_def:
            return set()

        permissions = role_def.permissions.copy()

        # Add inherited permissions
        if role_def.inherits_from:
            for parent_role in role_def.inherits_from:
                permissions.update(self.get_role_permissions(parent_role))

        return permissions

    def get_user_permissions(self, user: User) -> Set[Permission]:
        """
        Get all permissions for a user based on their roles

        Args:
            user: User object

        Returns:
            Set of all user permissions
        """
        all_permissions: Set[Permission] = set()

        # Add permissions from user's scopes (direct permissions)
        for scope in user.scopes:
            try:
                all_permissions.add(Permission(scope))
            except ValueError:
                # Skip invalid permission strings
                pass

        # Add permissions from user's roles
        for role_str in user.roles:
            try:
                role = Role(role_str)
                role_permissions = self.get_role_permissions(role)
                all_permissions.update(role_permissions)
            except ValueError:
                # Skip invalid role strings
                pass

        return all_permissions

    def has_permission(
        self,
        user: User,
        permission: Permission,
        log_check: bool = True
    ) -> bool:
        """
        Check if user has specific permission

        Args:
            user: User object
            permission: Permission to check
            log_check: Whether to log the permission check

        Returns:
            True if user has permission, False otherwise
        """
        user_permissions = self.get_user_permissions(user)
        has_perm = permission in user_permissions

        if log_check:
            self._audit_logger.log_decryption(
                algorithm=CryptoAlgorithm.BCRYPT,
                data_type='permission_check',
                success=has_perm,
                user_id=user.user_id,
                metadata={
                    'permission': permission.value,
                    'result': 'granted' if has_perm else 'denied'
                }
            )

        return has_perm

    def has_any_permission(
        self,
        user: User,
        permissions: List[Permission]
    ) -> bool:
        """
        Check if user has any of the specified permissions

        Args:
            user: User object
            permissions: List of permissions to check

        Returns:
            True if user has at least one permission, False otherwise
        """
        user_permissions = self.get_user_permissions(user)
        return any(perm in user_permissions for perm in permissions)

    def has_all_permissions(
        self,
        user: User,
        permissions: List[Permission]
    ) -> bool:
        """
        Check if user has all specified permissions

        Args:
            user: User object
            permissions: List of permissions to check

        Returns:
            True if user has all permissions, False otherwise
        """
        user_permissions = self.get_user_permissions(user)
        return all(perm in user_permissions for perm in permissions)

    def has_role(self, user: User, role: Role) -> bool:
        """
        Check if user has specific role

        Args:
            user: User object
            role: Role to check

        Returns:
            True if user has role, False otherwise
        """
        return role.value in user.roles

    def has_any_role(self, user: User, roles: List[Role]) -> bool:
        """
        Check if user has any of the specified roles

        Args:
            user: User object
            roles: List of roles to check

        Returns:
            True if user has at least one role, False otherwise
        """
        return any(role.value in user.roles for role in roles)

    def check_permission(
        self,
        user: User,
        permission: Permission,
        resource: Optional[str] = None
    ) -> PermissionCheck:
        """
        Perform detailed permission check with reasoning

        Args:
            user: User object
            permission: Permission to check
            resource: Optional resource identifier

        Returns:
            PermissionCheck object with details
        """
        if not user.is_active:
            return PermissionCheck(
                granted=False,
                reason="User account is inactive",
                user_id=user.user_id,
                permission=permission
            )

        has_perm = self.has_permission(user, permission, log_check=True)

        if has_perm:
            return PermissionCheck(
                granted=True,
                user_id=user.user_id,
                permission=permission
            )
        else:
            return PermissionCheck(
                granted=False,
                reason=f"User lacks required permission: {permission.value}",
                user_id=user.user_id,
                permission=permission
            )

    def require_permission(
        self,
        permission: Permission,
        error_message: Optional[str] = None
    ):
        """
        Decorator to require specific permission for route/function

        Args:
            permission: Required permission
            error_message: Optional custom error message

        Returns:
            Decorator function

        Example:
            @rbac.require_permission(Permission.CREATE_TEST)
            async def create_test(user: User = Depends(get_current_user)):
                ...
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract user from kwargs (assumes user is passed as dependency)
                user = kwargs.get('user') or kwargs.get('current_user')

                if user is None:
                    # Try to find user in args
                    for arg in args:
                        if isinstance(arg, User):
                            user = arg
                            break

                if user is None:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )

                if not self.has_permission(user, permission):
                    msg = error_message or f"Permission denied: {permission.value} required"
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=msg
                    )

                return await func(*args, **kwargs)
            return wrapper
        return decorator

    def require_any_permission(self, permissions: List[Permission]):
        """
        Decorator to require any of the specified permissions

        Args:
            permissions: List of acceptable permissions

        Returns:
            Decorator function
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                user = kwargs.get('user') or kwargs.get('current_user')

                if user is None:
                    for arg in args:
                        if isinstance(arg, User):
                            user = arg
                            break

                if user is None:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )

                if not self.has_any_permission(user, permissions):
                    perm_list = ", ".join(p.value for p in permissions)
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: One of [{perm_list}] required"
                    )

                return await func(*args, **kwargs)
            return wrapper
        return decorator

    def require_role(self, role: Role):
        """
        Decorator to require specific role

        Args:
            role: Required role

        Returns:
            Decorator function
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                user = kwargs.get('user') or kwargs.get('current_user')

                if user is None:
                    for arg in args:
                        if isinstance(arg, User):
                            user = arg
                            break

                if user is None:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )

                if not self.has_role(user, role):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Role required: {role.value}"
                    )

                return await func(*args, **kwargs)
            return wrapper
        return decorator

    def create_custom_role(
        self,
        role_name: str,
        display_name: str,
        description: str,
        permissions: Set[Permission],
        level: int = 50
    ) -> RoleDefinition:
        """
        Create custom role definition

        Args:
            role_name: Unique role identifier
            display_name: Human-readable name
            description: Role description
            permissions: Set of permissions
            level: Hierarchical level

        Returns:
            Created RoleDefinition
        """
        custom_role = RoleDefinition(
            role=role_name,  # type: ignore
            display_name=display_name,
            description=description,
            permissions=permissions,
            level=level,
            is_system_role=False
        )

        self.custom_roles[role_name] = custom_role

        # Audit log
        self._audit_logger.log_key_operation(
            operation='create_role',
            algorithm=CryptoAlgorithm.BCRYPT,
            metadata={
                'role_name': role_name,
                'permissions_count': len(permissions)
            }
        )

        return custom_role

    def get_all_roles(self) -> List[RoleDefinition]:
        """Get all role definitions (system + custom)"""
        all_roles = list(self.role_definitions.values())
        all_roles.extend(self.custom_roles.values())
        return sorted(all_roles, key=lambda r: r.level, reverse=True)

    def get_role_hierarchy(self) -> Dict[str, int]:
        """
        Get role hierarchy mapping

        Returns:
            Dictionary mapping role names to hierarchy levels
        """
        hierarchy = {}
        for role_def in self.get_all_roles():
            hierarchy[role_def.role.value if isinstance(role_def.role, Enum) else role_def.role] = role_def.level
        return hierarchy


# Global RBAC manager instance
_rbac_manager = RBACManager()


def get_rbac_manager() -> RBACManager:
    """Get global RBAC manager instance"""
    return _rbac_manager


# Convenience decorators using global manager
def require_permission(permission: Permission):
    """Convenience decorator using global RBAC manager"""
    return _rbac_manager.require_permission(permission)


def require_any_permission(permissions: List[Permission]):
    """Convenience decorator using global RBAC manager"""
    return _rbac_manager.require_any_permission(permissions)


def require_role(role: Role):
    """Convenience decorator using global RBAC manager"""
    return _rbac_manager.require_role(role)
