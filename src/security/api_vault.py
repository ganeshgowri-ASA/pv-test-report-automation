"""
Secure API Key Vault for LLM API Keys
Provides encrypted storage for Claude, OpenAI, Gemini, and other LLM API keys
ISO 17025 and 21 CFR Part 11 compliant with encryption at rest
"""

import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, validator, SecretStr
from cryptography.fernet import InvalidToken

from .crypto import (
    FernetVault,
    AESCipher,
    SecureRandom,
    EncryptionError,
    DecryptionError,
    get_audit_logger,
    CryptoAlgorithm
)


class APIKeyError(Exception):
    """Base exception for API key vault errors"""
    pass


class APIKeyNotFoundError(APIKeyError):
    """API key not found in vault"""
    pass


class APIKeyExpiredError(APIKeyError):
    """API key has expired"""
    pass


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    ANTHROPIC = "anthropic"  # Claude
    OPENAI = "openai"  # GPT models
    GOOGLE = "google"  # Gemini
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"
    AZURE_OPENAI = "azure_openai"
    CUSTOM = "custom"


class APIKeyStatus(str, Enum):
    """API key status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"


class APIKeyMetadata(BaseModel):
    """Metadata for API key"""
    key_id: str = Field(..., description="Unique key identifier")
    provider: LLMProvider = Field(..., description="LLM provider")
    name: str = Field(..., description="Human-readable key name")
    description: Optional[str] = Field(None, description="Key description")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="User who created the key")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    last_used: Optional[datetime] = Field(None, description="Last usage timestamp")
    usage_count: int = Field(default=0, description="Number of times key used")
    status: APIKeyStatus = Field(default=APIKeyStatus.ACTIVE)
    tags: List[str] = Field(default_factory=list, description="Key tags for organization")
    rate_limit: Optional[int] = Field(None, description="Optional rate limit per hour")
    allowed_models: Optional[List[str]] = Field(None, description="Allowed model IDs")
    environment: str = Field(default="production", description="Environment (dev/staging/prod)")
    rotation_policy_days: Optional[int] = Field(None, description="Auto-rotation policy in days")
    last_rotated: Optional[datetime] = Field(None, description="Last rotation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    def is_expired(self) -> bool:
        """Check if key is expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def needs_rotation(self) -> bool:
        """Check if key needs rotation based on policy"""
        if self.rotation_policy_days is None:
            return False

        if self.last_rotated is None:
            rotation_date = self.created_at
        else:
            rotation_date = self.last_rotated

        next_rotation = rotation_date + timedelta(days=self.rotation_policy_days)
        return datetime.utcnow() > next_rotation


class StoredAPIKey(BaseModel):
    """Encrypted API key storage model"""
    metadata: APIKeyMetadata = Field(..., description="Key metadata")
    encrypted_key: str = Field(..., description="Encrypted API key")
    encryption_algorithm: str = Field(default="Fernet", description="Encryption algorithm used")
    checksum: str = Field(..., description="Integrity checksum")


class APIKeyVault:
    """
    Secure vault for storing and managing LLM API keys
    Implements encryption at rest with Fernet and AES-256
    """

    def __init__(
        self,
        master_key: Optional[bytes] = None,
        storage_path: Optional[Path] = None,
        use_aes: bool = False
    ):
        """
        Initialize API key vault

        Args:
            master_key: Optional master encryption key. If None, generates new key.
            storage_path: Optional path to persist vault data
            use_aes: Whether to use AES-256-CBC instead of Fernet
        """
        self.use_aes = use_aes

        if use_aes:
            self.cipher = AESCipher(master_key)
        else:
            self.cipher = FernetVault(master_key)

        self.storage_path = storage_path
        self.keys: Dict[str, StoredAPIKey] = {}
        self._audit_logger = get_audit_logger()

        # Load existing keys if storage path exists
        if storage_path and storage_path.exists():
            self._load_from_disk()

    def add_key(
        self,
        provider: LLMProvider,
        api_key: str,
        name: str,
        created_by: str,
        description: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        allowed_models: Optional[List[str]] = None,
        environment: str = "production",
        rotation_policy_days: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add new API key to vault

        Args:
            provider: LLM provider
            api_key: Plain text API key
            name: Human-readable key name
            created_by: User creating the key
            description: Optional description
            expires_at: Optional expiration date
            tags: Optional tags
            allowed_models: Optional list of allowed model IDs
            environment: Environment (dev/staging/prod)
            rotation_policy_days: Auto-rotation policy
            metadata: Additional metadata

        Returns:
            Generated key ID

        Raises:
            APIKeyError: If key addition fails
        """
        try:
            # Generate unique key ID
            key_id = SecureRandom.generate_token(16)

            # Create metadata
            key_metadata = APIKeyMetadata(
                key_id=key_id,
                provider=provider,
                name=name,
                description=description,
                created_by=created_by,
                expires_at=expires_at,
                tags=tags or [],
                allowed_models=allowed_models,
                environment=environment,
                rotation_policy_days=rotation_policy_days,
                metadata=metadata or {}
            )

            # Encrypt API key
            encrypted_key = self.cipher.encrypt(api_key)

            # Generate checksum for integrity verification
            checksum = self._generate_checksum(api_key)

            # Store encrypted key
            stored_key = StoredAPIKey(
                metadata=key_metadata,
                encrypted_key=encrypted_key,
                encryption_algorithm="AES-256-CBC" if self.use_aes else "Fernet",
                checksum=checksum
            )

            self.keys[key_id] = stored_key

            # Persist to disk if storage path is set
            if self.storage_path:
                self._save_to_disk()

            # Audit log
            self._audit_logger.log_encryption(
                algorithm=CryptoAlgorithm.FERNET,
                data_type='api_key',
                user_id=created_by,
                metadata={
                    'key_id': key_id,
                    'provider': provider.value,
                    'name': name,
                    'environment': environment
                }
            )

            return key_id

        except Exception as e:
            raise APIKeyError(f"Failed to add API key: {str(e)}") from e

    def get_key(
        self,
        key_id: str,
        user_id: Optional[str] = None,
        verify_expiration: bool = True
    ) -> str:
        """
        Retrieve decrypted API key

        Args:
            key_id: Key identifier
            user_id: Optional user ID for audit logging
            verify_expiration: Whether to check expiration

        Returns:
            Decrypted API key

        Raises:
            APIKeyNotFoundError: If key not found
            APIKeyExpiredError: If key is expired
            DecryptionError: If decryption fails
        """
        stored_key = self.keys.get(key_id)

        if stored_key is None:
            self._audit_logger.log_decryption(
                algorithm=CryptoAlgorithm.FERNET,
                data_type='api_key',
                success=False,
                user_id=user_id,
                metadata={'key_id': key_id, 'reason': 'not_found'}
            )
            raise APIKeyNotFoundError(f"API key not found: {key_id}")

        # Check expiration
        if verify_expiration and stored_key.metadata.is_expired():
            self._audit_logger.log_decryption(
                algorithm=CryptoAlgorithm.FERNET,
                data_type='api_key',
                success=False,
                user_id=user_id,
                metadata={'key_id': key_id, 'reason': 'expired'}
            )
            raise APIKeyExpiredError(f"API key expired: {key_id}")

        # Check status
        if stored_key.metadata.status != APIKeyStatus.ACTIVE:
            self._audit_logger.log_decryption(
                algorithm=CryptoAlgorithm.FERNET,
                data_type='api_key',
                success=False,
                user_id=user_id,
                metadata={
                    'key_id': key_id,
                    'reason': f'status_{stored_key.metadata.status.value}'
                }
            )
            raise APIKeyError(f"API key is {stored_key.metadata.status.value}: {key_id}")

        try:
            # Decrypt key
            decrypted_key = self.cipher.decrypt(stored_key.encrypted_key)

            # Verify integrity
            if not self._verify_checksum(decrypted_key, stored_key.checksum):
                raise DecryptionError("API key integrity check failed")

            # Update usage stats
            stored_key.metadata.last_used = datetime.utcnow()
            stored_key.metadata.usage_count += 1

            # Persist updated stats
            if self.storage_path:
                self._save_to_disk()

            # Audit log
            self._audit_logger.log_decryption(
                algorithm=CryptoAlgorithm.FERNET,
                data_type='api_key',
                success=True,
                user_id=user_id,
                metadata={
                    'key_id': key_id,
                    'provider': stored_key.metadata.provider.value,
                    'name': stored_key.metadata.name
                }
            )

            return decrypted_key

        except Exception as e:
            self._audit_logger.log_decryption(
                algorithm=CryptoAlgorithm.FERNET,
                data_type='api_key',
                success=False,
                user_id=user_id,
                metadata={'key_id': key_id, 'error': str(e)}
            )
            raise DecryptionError(f"Failed to decrypt API key: {str(e)}") from e

    def get_key_by_provider(
        self,
        provider: LLMProvider,
        environment: str = "production",
        user_id: Optional[str] = None
    ) -> str:
        """
        Get API key for specific provider and environment

        Args:
            provider: LLM provider
            environment: Environment filter
            user_id: Optional user ID for audit logging

        Returns:
            Decrypted API key

        Raises:
            APIKeyNotFoundError: If no matching key found
        """
        # Find active keys for provider/environment
        matching_keys = [
            (key_id, stored_key)
            for key_id, stored_key in self.keys.items()
            if stored_key.metadata.provider == provider
            and stored_key.metadata.environment == environment
            and stored_key.metadata.status == APIKeyStatus.ACTIVE
            and not stored_key.metadata.is_expired()
        ]

        if not matching_keys:
            raise APIKeyNotFoundError(
                f"No active API key found for provider={provider.value}, env={environment}"
            )

        # Get most recently used key
        key_id, _ = max(
            matching_keys,
            key=lambda x: x[1].metadata.last_used or x[1].metadata.created_at
        )

        return self.get_key(key_id, user_id=user_id)

    def list_keys(
        self,
        provider: Optional[LLMProvider] = None,
        environment: Optional[str] = None,
        status: Optional[APIKeyStatus] = None,
        include_expired: bool = False
    ) -> List[APIKeyMetadata]:
        """
        List API key metadata (without decrypting keys)

        Args:
            provider: Optional provider filter
            environment: Optional environment filter
            status: Optional status filter
            include_expired: Whether to include expired keys

        Returns:
            List of API key metadata
        """
        results = []

        for stored_key in self.keys.values():
            metadata = stored_key.metadata

            # Apply filters
            if provider and metadata.provider != provider:
                continue
            if environment and metadata.environment != environment:
                continue
            if status and metadata.status != status:
                continue
            if not include_expired and metadata.is_expired():
                continue

            results.append(metadata)

        return results

    def rotate_key(
        self,
        key_id: str,
        new_api_key: str,
        rotated_by: str
    ) -> None:
        """
        Rotate API key with new value

        Args:
            key_id: Key identifier
            new_api_key: New API key value
            rotated_by: User performing rotation

        Raises:
            APIKeyNotFoundError: If key not found
        """
        stored_key = self.keys.get(key_id)

        if stored_key is None:
            raise APIKeyNotFoundError(f"API key not found: {key_id}")

        try:
            # Encrypt new key
            encrypted_key = self.cipher.encrypt(new_api_key)
            checksum = self._generate_checksum(new_api_key)

            # Update stored key
            stored_key.encrypted_key = encrypted_key
            stored_key.checksum = checksum
            stored_key.metadata.last_rotated = datetime.utcnow()

            # Persist changes
            if self.storage_path:
                self._save_to_disk()

            # Audit log
            self._audit_logger.log_key_operation(
                operation='rotate',
                algorithm=CryptoAlgorithm.FERNET,
                user_id=rotated_by,
                metadata={
                    'key_id': key_id,
                    'provider': stored_key.metadata.provider.value
                }
            )

        except Exception as e:
            raise APIKeyError(f"Failed to rotate API key: {str(e)}") from e

    def revoke_key(self, key_id: str, revoked_by: str) -> None:
        """
        Revoke API key

        Args:
            key_id: Key identifier
            revoked_by: User performing revocation

        Raises:
            APIKeyNotFoundError: If key not found
        """
        stored_key = self.keys.get(key_id)

        if stored_key is None:
            raise APIKeyNotFoundError(f"API key not found: {key_id}")

        stored_key.metadata.status = APIKeyStatus.REVOKED

        # Persist changes
        if self.storage_path:
            self._save_to_disk()

        # Audit log
        self._audit_logger.log_key_operation(
            operation='revoke',
            algorithm=CryptoAlgorithm.FERNET,
            user_id=revoked_by,
            metadata={
                'key_id': key_id,
                'provider': stored_key.metadata.provider.value
            }
        )

    def delete_key(self, key_id: str, deleted_by: str) -> None:
        """
        Permanently delete API key

        Args:
            key_id: Key identifier
            deleted_by: User performing deletion

        Raises:
            APIKeyNotFoundError: If key not found
        """
        stored_key = self.keys.get(key_id)

        if stored_key is None:
            raise APIKeyNotFoundError(f"API key not found: {key_id}")

        # Audit log before deletion
        self._audit_logger.log_key_operation(
            operation='delete',
            algorithm=CryptoAlgorithm.FERNET,
            user_id=deleted_by,
            metadata={
                'key_id': key_id,
                'provider': stored_key.metadata.provider.value
            }
        )

        # Delete key
        del self.keys[key_id]

        # Persist changes
        if self.storage_path:
            self._save_to_disk()

    def export_vault(self, include_keys: bool = False) -> Dict[str, Any]:
        """
        Export vault data (for backup or migration)

        Args:
            include_keys: Whether to include encrypted keys (WARNING: sensitive)

        Returns:
            Dictionary containing vault data
        """
        export_data = {
            'version': '1.0',
            'exported_at': datetime.utcnow().isoformat(),
            'encryption_algorithm': 'AES-256-CBC' if self.use_aes else 'Fernet',
            'key_count': len(self.keys),
            'keys': {}
        }

        for key_id, stored_key in self.keys.items():
            key_data = {
                'metadata': stored_key.metadata.dict()
            }

            if include_keys:
                key_data['encrypted_key'] = stored_key.encrypted_key
                key_data['checksum'] = stored_key.checksum

            export_data['keys'][key_id] = key_data

        return export_data

    def import_vault(self, vault_data: Dict[str, Any]) -> int:
        """
        Import vault data from backup

        Args:
            vault_data: Vault data dictionary

        Returns:
            Number of keys imported
        """
        imported_count = 0

        for key_id, key_data in vault_data.get('keys', {}).items():
            if 'encrypted_key' in key_data and 'metadata' in key_data:
                metadata = APIKeyMetadata(**key_data['metadata'])
                stored_key = StoredAPIKey(
                    metadata=metadata,
                    encrypted_key=key_data['encrypted_key'],
                    checksum=key_data['checksum']
                )
                self.keys[key_id] = stored_key
                imported_count += 1

        # Persist imported keys
        if self.storage_path:
            self._save_to_disk()

        return imported_count

    def _generate_checksum(self, data: str) -> str:
        """Generate SHA-256 checksum for integrity verification"""
        import hashlib
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def _verify_checksum(self, data: str, checksum: str) -> bool:
        """Verify data integrity against checksum"""
        return self._generate_checksum(data) == checksum

    def _save_to_disk(self) -> None:
        """Persist vault to disk"""
        if self.storage_path is None:
            return

        try:
            # Create parent directory if needed
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            # Export vault data with encrypted keys
            vault_data = self.export_vault(include_keys=True)

            # Write to temporary file first
            temp_path = self.storage_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(vault_data, f, indent=2)

            # Atomic rename
            temp_path.replace(self.storage_path)

        except Exception as e:
            raise APIKeyError(f"Failed to save vault to disk: {str(e)}") from e

    def _load_from_disk(self) -> None:
        """Load vault from disk"""
        if self.storage_path is None or not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, 'r') as f:
                vault_data = json.load(f)

            self.import_vault(vault_data)

        except Exception as e:
            raise APIKeyError(f"Failed to load vault from disk: {str(e)}") from e

    def get_master_key(self) -> str:
        """
        Get base64-encoded master key for backup
        WARNING: Keep this secure!
        """
        return self.cipher.get_key_base64()

    @classmethod
    def from_master_key(
        cls,
        master_key_b64: str,
        storage_path: Optional[Path] = None,
        use_aes: bool = False
    ) -> 'APIKeyVault':
        """
        Create vault from base64-encoded master key

        Args:
            master_key_b64: Base64-encoded master key
            storage_path: Optional storage path
            use_aes: Whether to use AES-256-CBC

        Returns:
            Initialized APIKeyVault
        """
        if use_aes:
            cipher = AESCipher.from_base64_key(master_key_b64)
            vault = cls(master_key=cipher.key, storage_path=storage_path, use_aes=True)
        else:
            master_key = master_key_b64.encode('utf-8')
            vault = cls(master_key=master_key, storage_path=storage_path, use_aes=False)

        return vault


# Convenience function to create vault with environment variable key
def create_vault_from_env(
    env_var: str = "API_VAULT_MASTER_KEY",
    storage_path: Optional[Path] = None,
    use_aes: bool = False
) -> APIKeyVault:
    """
    Create API vault from environment variable

    Args:
        env_var: Environment variable name containing master key
        storage_path: Optional storage path
        use_aes: Whether to use AES-256-CBC

    Returns:
        Initialized APIKeyVault

    Raises:
        APIKeyError: If environment variable not set
    """
    master_key_b64 = os.getenv(env_var)

    if master_key_b64 is None:
        raise APIKeyError(f"Environment variable {env_var} not set")

    return APIKeyVault.from_master_key(master_key_b64, storage_path, use_aes)
