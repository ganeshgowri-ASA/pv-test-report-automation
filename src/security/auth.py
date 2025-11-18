"""
JWT Authentication and OAuth2 implementation for PV Test Report Automation
Provides token generation, validation, refresh, and OAuth2 password bearer flow
ISO 17025 and 21 CFR Part 11 compliant
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
from enum import Enum
import secrets

import jwt
from jwt.exceptions import (
    InvalidTokenError,
    ExpiredSignatureError,
    InvalidSignatureError,
    DecodeError
)
from pydantic import BaseModel, Field, validator, EmailStr
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import (
    OAuth2PasswordBearer,
    HTTPBearer,
    HTTPAuthorizationCredentials,
    SecurityScopes
)

from .crypto import PasswordHasher, SecureRandom, get_audit_logger, CryptoAlgorithm


class AuthenticationError(Exception):
    """Base exception for authentication errors"""
    pass


class TokenExpiredError(AuthenticationError):
    """Token has expired"""
    pass


class InvalidTokenError(AuthenticationError):
    """Token is invalid or malformed"""
    pass


class InsufficientPermissionsError(AuthenticationError):
    """User lacks required permissions"""
    pass


class TokenType(Enum):
    """Types of JWT tokens"""
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"
    RESET_PASSWORD = "reset_password"
    EMAIL_VERIFICATION = "email_verification"


class TokenStatus(Enum):
    """Token validation status"""
    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    REVOKED = "revoked"


class User(BaseModel):
    """User model for authentication"""
    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, description="Full name")
    roles: List[str] = Field(default_factory=list, description="User roles")
    scopes: List[str] = Field(default_factory=list, description="User permissions")
    is_active: bool = Field(default=True, description="Account active status")
    is_verified: bool = Field(default=False, description="Email verified status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserInDB(User):
    """User model with password hash for database storage"""
    password_hash: str = Field(..., description="Bcrypt password hash")


class TokenPayload(BaseModel):
    """JWT token payload structure"""
    sub: str = Field(..., description="Subject (user_id)")
    type: str = Field(..., description="Token type")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
    jti: str = Field(..., description="JWT ID (unique token identifier)")
    scopes: List[str] = Field(default_factory=list, description="Token scopes")
    roles: List[str] = Field(default_factory=list, description="User roles")
    fresh: bool = Field(default=False, description="Fresh login indicator")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TokenResponse(BaseModel):
    """Authentication token response"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    scope: str = Field(default="", description="Token scopes")


class JWTConfig(BaseModel):
    """JWT configuration settings"""
    secret_key: str = Field(..., description="JWT signing secret key")
    algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Access token TTL")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token TTL")
    api_key_token_expire_days: int = Field(default=365, description="API key token TTL")
    password_reset_expire_hours: int = Field(default=24, description="Password reset token TTL")
    email_verification_expire_hours: int = Field(default=48, description="Email verification token TTL")
    issuer: str = Field(default="pv-test-report-system", description="Token issuer")
    audience: str = Field(default="pv-test-api", description="Token audience")

    @validator('secret_key')
    def validate_secret_key(cls, v):
        """Ensure secret key is sufficiently strong"""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters")
        return v


class JWTManager:
    """
    JWT token generation and validation manager
    Supports access tokens, refresh tokens, and API keys
    """

    def __init__(self, config: JWTConfig):
        """
        Initialize JWT manager

        Args:
            config: JWT configuration settings
        """
        self.config = config
        self.revoked_tokens: set[str] = set()  # In-memory revocation list
        self._audit_logger = get_audit_logger()

    def create_access_token(
        self,
        user: User,
        expires_delta: Optional[timedelta] = None,
        fresh: bool = False,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create JWT access token

        Args:
            user: User object
            expires_delta: Optional custom expiration time
            fresh: Whether this is a fresh login
            additional_claims: Optional additional JWT claims

        Returns:
            Encoded JWT access token

        Raises:
            AuthenticationError: If token creation fails
        """
        try:
            if expires_delta is None:
                expires_delta = timedelta(
                    minutes=self.config.access_token_expire_minutes
                )

            now = datetime.utcnow()
            expire = now + expires_delta

            payload = {
                'sub': user.user_id,
                'type': TokenType.ACCESS.value,
                'exp': int(expire.timestamp()),
                'iat': int(now.timestamp()),
                'jti': SecureRandom.generate_token(16),
                'scopes': user.scopes,
                'roles': user.roles,
                'fresh': fresh,
                'iss': self.config.issuer,
                'aud': self.config.audience,
            }

            if additional_claims:
                payload.update(additional_claims)

            token = jwt.encode(
                payload,
                self.config.secret_key,
                algorithm=self.config.algorithm
            )

            # Audit log
            self._audit_logger.log_encryption(
                algorithm=CryptoAlgorithm.BCRYPT,
                data_type='access_token',
                user_id=user.user_id,
                metadata={'fresh': fresh, 'expires': expire.isoformat()}
            )

            return token

        except Exception as e:
            raise AuthenticationError(f"Failed to create access token: {str(e)}") from e

    def create_refresh_token(
        self,
        user: User,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT refresh token

        Args:
            user: User object
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT refresh token

        Raises:
            AuthenticationError: If token creation fails
        """
        try:
            if expires_delta is None:
                expires_delta = timedelta(
                    days=self.config.refresh_token_expire_days
                )

            now = datetime.utcnow()
            expire = now + expires_delta

            payload = {
                'sub': user.user_id,
                'type': TokenType.REFRESH.value,
                'exp': int(expire.timestamp()),
                'iat': int(now.timestamp()),
                'jti': SecureRandom.generate_token(16),
                'iss': self.config.issuer,
                'aud': self.config.audience,
            }

            token = jwt.encode(
                payload,
                self.config.secret_key,
                algorithm=self.config.algorithm
            )

            # Audit log
            self._audit_logger.log_encryption(
                algorithm=CryptoAlgorithm.BCRYPT,
                data_type='refresh_token',
                user_id=user.user_id,
                metadata={'expires': expire.isoformat()}
            )

            return token

        except Exception as e:
            raise AuthenticationError(f"Failed to create refresh token: {str(e)}") from e

    def create_api_key_token(
        self,
        user: User,
        key_name: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create long-lived API key token

        Args:
            user: User object
            key_name: Name/description of API key
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT API key token

        Raises:
            AuthenticationError: If token creation fails
        """
        try:
            if expires_delta is None:
                expires_delta = timedelta(
                    days=self.config.api_key_token_expire_days
                )

            now = datetime.utcnow()
            expire = now + expires_delta

            payload = {
                'sub': user.user_id,
                'type': TokenType.API_KEY.value,
                'exp': int(expire.timestamp()),
                'iat': int(now.timestamp()),
                'jti': SecureRandom.generate_token(16),
                'scopes': user.scopes,
                'roles': user.roles,
                'key_name': key_name,
                'iss': self.config.issuer,
                'aud': self.config.audience,
            }

            token = jwt.encode(
                payload,
                self.config.secret_key,
                algorithm=self.config.algorithm
            )

            # Audit log
            self._audit_logger.log_encryption(
                algorithm=CryptoAlgorithm.BCRYPT,
                data_type='api_key_token',
                user_id=user.user_id,
                metadata={'key_name': key_name, 'expires': expire.isoformat()}
            )

            return token

        except Exception as e:
            raise AuthenticationError(f"Failed to create API key token: {str(e)}") from e

    def verify_token(
        self,
        token: str,
        expected_type: Optional[TokenType] = None,
        verify_fresh: bool = False
    ) -> TokenPayload:
        """
        Verify and decode JWT token

        Args:
            token: JWT token to verify
            expected_type: Optional expected token type
            verify_fresh: Whether to require fresh token

        Returns:
            Decoded token payload

        Raises:
            TokenExpiredError: If token has expired
            InvalidTokenError: If token is invalid
            AuthenticationError: If token is revoked or type mismatch
        """
        try:
            # Decode token
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                issuer=self.config.issuer,
                audience=self.config.audience
            )

            # Check if token is revoked
            jti = payload.get('jti')
            if jti and jti in self.revoked_tokens:
                self._audit_logger.log_decryption(
                    algorithm=CryptoAlgorithm.BCRYPT,
                    data_type='token',
                    success=False,
                    metadata={'reason': 'revoked', 'jti': jti}
                )
                raise AuthenticationError("Token has been revoked")

            # Verify token type if specified
            if expected_type:
                token_type = payload.get('type')
                if token_type != expected_type.value:
                    raise AuthenticationError(
                        f"Invalid token type. Expected {expected_type.value}, got {token_type}"
                    )

            # Verify fresh token if required
            if verify_fresh and not payload.get('fresh', False):
                raise AuthenticationError("Fresh token required")

            # Audit log
            self._audit_logger.log_decryption(
                algorithm=CryptoAlgorithm.BCRYPT,
                data_type='token',
                success=True,
                user_id=payload.get('sub'),
                metadata={'type': payload.get('type')}
            )

            return TokenPayload(**payload)

        except ExpiredSignatureError as e:
            self._audit_logger.log_decryption(
                algorithm=CryptoAlgorithm.BCRYPT,
                data_type='token',
                success=False,
                metadata={'reason': 'expired'}
            )
            raise TokenExpiredError("Token has expired") from e

        except (InvalidSignatureError, DecodeError) as e:
            self._audit_logger.log_decryption(
                algorithm=CryptoAlgorithm.BCRYPT,
                data_type='token',
                success=False,
                metadata={'reason': 'invalid'}
            )
            raise InvalidTokenError("Invalid token") from e

        except Exception as e:
            raise AuthenticationError(f"Token verification failed: {str(e)}") from e

    def refresh_access_token(self, refresh_token: str, user: User) -> str:
        """
        Generate new access token from refresh token

        Args:
            refresh_token: Valid refresh token
            user: User object

        Returns:
            New access token

        Raises:
            AuthenticationError: If refresh token is invalid
        """
        # Verify refresh token
        payload = self.verify_token(refresh_token, expected_type=TokenType.REFRESH)

        # Verify user ID matches
        if payload.sub != user.user_id:
            raise AuthenticationError("Token user mismatch")

        # Create new access token (not fresh)
        return self.create_access_token(user, fresh=False)

    def revoke_token(self, token: str) -> None:
        """
        Revoke a token by adding its JTI to revocation list

        Args:
            token: Token to revoke

        Raises:
            AuthenticationError: If token cannot be decoded
        """
        try:
            # Decode without verification to get JTI
            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            jti = payload.get('jti')

            if jti:
                self.revoked_tokens.add(jti)

                # Audit log
                self._audit_logger.log_key_operation(
                    operation='revoke',
                    algorithm=CryptoAlgorithm.BCRYPT,
                    user_id=payload.get('sub'),
                    metadata={'jti': jti, 'type': payload.get('type')}
                )

        except Exception as e:
            raise AuthenticationError(f"Failed to revoke token: {str(e)}") from e

    def revoke_all_user_tokens(self, user_id: str) -> None:
        """
        Revoke all tokens for a specific user
        Note: This requires storing user's token JTIs in production

        Args:
            user_id: User identifier
        """
        # Audit log
        self._audit_logger.log_key_operation(
            operation='revoke_all',
            algorithm=CryptoAlgorithm.BCRYPT,
            user_id=user_id
        )

    def get_token_status(self, token: str) -> TokenStatus:
        """
        Check token status without raising exceptions

        Args:
            token: Token to check

        Returns:
            Token status enum
        """
        try:
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                issuer=self.config.issuer,
                audience=self.config.audience
            )

            jti = payload.get('jti')
            if jti and jti in self.revoked_tokens:
                return TokenStatus.REVOKED

            return TokenStatus.VALID

        except ExpiredSignatureError:
            return TokenStatus.EXPIRED
        except Exception:
            return TokenStatus.INVALID


class AuthenticationService:
    """
    Complete authentication service with user management
    Integrates password hashing and JWT token management
    """

    def __init__(self, jwt_config: JWTConfig, password_rounds: int = 12):
        """
        Initialize authentication service

        Args:
            jwt_config: JWT configuration
            password_rounds: Bcrypt work factor
        """
        self.jwt_manager = JWTManager(jwt_config)
        self.password_hasher = PasswordHasher(rounds=password_rounds)
        self._audit_logger = get_audit_logger()

    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        roles: Optional[List[str]] = None,
        scopes: Optional[List[str]] = None
    ) -> UserInDB:
        """
        Register new user with password hashing

        Args:
            username: Username
            email: Email address
            password: Plain text password
            full_name: Optional full name
            roles: Optional user roles
            scopes: Optional user permissions

        Returns:
            User object with hashed password

        Raises:
            AuthenticationError: If registration fails
        """
        try:
            # Hash password
            password_hash = self.password_hasher.hash_password(password)

            # Create user
            user = UserInDB(
                user_id=SecureRandom.generate_token(16),
                username=username,
                email=email,
                password_hash=password_hash,
                full_name=full_name,
                roles=roles or [],
                scopes=scopes or [],
                is_active=True,
                is_verified=False
            )

            # Audit log
            self._audit_logger.log_encryption(
                algorithm=CryptoAlgorithm.BCRYPT,
                data_type='password',
                user_id=user.user_id,
                metadata={'username': username}
            )

            return user

        except Exception as e:
            raise AuthenticationError(f"User registration failed: {str(e)}") from e

    def authenticate_user(
        self,
        username: str,
        password: str,
        user_db: UserInDB
    ) -> Optional[User]:
        """
        Authenticate user with username and password

        Args:
            username: Username
            password: Plain text password
            user_db: User from database with password hash

        Returns:
            User object if authentication succeeds, None otherwise
        """
        try:
            # Verify username matches
            if user_db.username != username:
                self._audit_logger.log_decryption(
                    algorithm=CryptoAlgorithm.BCRYPT,
                    data_type='password',
                    success=False,
                    metadata={'reason': 'username_mismatch'}
                )
                return None

            # Verify password
            if not self.password_hasher.verify_password(password, user_db.password_hash):
                self._audit_logger.log_decryption(
                    algorithm=CryptoAlgorithm.BCRYPT,
                    data_type='password',
                    success=False,
                    user_id=user_db.user_id,
                    metadata={'reason': 'invalid_password'}
                )
                return None

            # Check if account is active
            if not user_db.is_active:
                self._audit_logger.log_decryption(
                    algorithm=CryptoAlgorithm.BCRYPT,
                    data_type='password',
                    success=False,
                    user_id=user_db.user_id,
                    metadata={'reason': 'account_inactive'}
                )
                return None

            # Successful authentication
            self._audit_logger.log_decryption(
                algorithm=CryptoAlgorithm.BCRYPT,
                data_type='password',
                success=True,
                user_id=user_db.user_id,
                metadata={'username': username}
            )

            # Return user without password hash
            return User(**user_db.dict(exclude={'password_hash'}))

        except Exception as e:
            self._audit_logger.log_decryption(
                algorithm=CryptoAlgorithm.BCRYPT,
                data_type='password',
                success=False,
                metadata={'error': str(e)}
            )
            return None

    def login(self, user: User) -> TokenResponse:
        """
        Generate authentication tokens for successful login

        Args:
            user: Authenticated user object

        Returns:
            Token response with access and refresh tokens
        """
        # Update last login
        user.last_login = datetime.utcnow()

        # Create tokens
        access_token = self.jwt_manager.create_access_token(user, fresh=True)
        refresh_token = self.jwt_manager.create_refresh_token(user)

        expires_in = self.jwt_manager.config.access_token_expire_minutes * 60

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=expires_in,
            scope=" ".join(user.scopes)
        )

    def refresh_token(self, refresh_token: str, user: User) -> TokenResponse:
        """
        Refresh access token using refresh token

        Args:
            refresh_token: Valid refresh token
            user: User object

        Returns:
            Token response with new access token
        """
        access_token = self.jwt_manager.refresh_access_token(refresh_token, user)
        expires_in = self.jwt_manager.config.access_token_expire_minutes * 60

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
            scope=" ".join(user.scopes)
        )

    def change_password(
        self,
        user_db: UserInDB,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password

        Args:
            user_db: User from database
            old_password: Current password
            new_password: New password

        Returns:
            True if password changed successfully

        Raises:
            AuthenticationError: If old password is incorrect
        """
        # Verify old password
        if not self.password_hasher.verify_password(old_password, user_db.password_hash):
            raise AuthenticationError("Current password is incorrect")

        # Hash new password
        new_hash = self.password_hasher.hash_password(new_password)
        user_db.password_hash = new_hash

        # Audit log
        self._audit_logger.log_key_operation(
            operation='password_change',
            algorithm=CryptoAlgorithm.BCRYPT,
            user_id=user_db.user_id
        )

        return True

    def reset_password(self, user_db: UserInDB, new_password: str) -> bool:
        """
        Reset user password (without requiring old password)

        Args:
            user_db: User from database
            new_password: New password

        Returns:
            True if password reset successfully
        """
        # Hash new password
        new_hash = self.password_hasher.hash_password(new_password)
        user_db.password_hash = new_hash

        # Audit log
        self._audit_logger.log_key_operation(
            operation='password_reset',
            algorithm=CryptoAlgorithm.BCRYPT,
            user_id=user_db.user_id
        )

        return True


# OAuth2 scheme for FastAPI dependency injection
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scopes={
        "create_test": "Create new tests",
        "execute_test": "Execute tests",
        "review_report": "Review test reports",
        "approve_report": "Approve test reports",
        "view_audit": "View audit logs",
        "manage_users": "Manage users",
        "manage_equipment": "Manage equipment"
    }
)

# HTTP Bearer scheme for API key authentication
http_bearer = HTTPBearer()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    jwt_manager: Optional[JWTManager] = None
) -> User:
    """
    FastAPI dependency to get current authenticated user from token

    Args:
        token: JWT token from Authorization header
        jwt_manager: Optional JWT manager instance

    Returns:
        Current user object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    if jwt_manager is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT manager not configured"
        )

    try:
        payload = jwt_manager.verify_token(token, expected_type=TokenType.ACCESS)

        # In production, fetch user from database using payload.sub
        # For now, return minimal user from token
        user = User(
            user_id=payload.sub,
            username=payload.sub,
            email=f"{payload.sub}@example.com",
            roles=payload.roles,
            scopes=payload.scopes
        )

        return user

    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    FastAPI dependency to get current active user

    Args:
        current_user: User from get_current_user dependency

    Returns:
        Active user object

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    return current_user


def require_scopes(required_scopes: List[str]):
    """
    FastAPI dependency factory to require specific scopes

    Args:
        required_scopes: List of required permission scopes

    Returns:
        Dependency function that validates scopes
    """
    async def scope_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        user_scopes = set(current_user.scopes)
        required_scopes_set = set(required_scopes)

        if not required_scopes_set.issubset(user_scopes):
            missing_scopes = required_scopes_set - user_scopes
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Missing scopes: {', '.join(missing_scopes)}"
            )

        return current_user

    return scope_checker


def require_roles(required_roles: List[str]):
    """
    FastAPI dependency factory to require specific roles

    Args:
        required_roles: List of required user roles

    Returns:
        Dependency function that validates roles
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        user_roles = set(current_user.roles)
        required_roles_set = set(required_roles)

        if not required_roles_set.intersection(user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(required_roles)}"
            )

        return current_user

    return role_checker
