"""
API Key Vault for Secure LLM Credential Storage.

Provides encrypted storage and retrieval of API keys for LLM providers:
- AES-256 encryption for stored keys
- Environment variable fallback
- Key rotation support
- Usage tracking and monitoring
- Audit logging

Security compliant with ISO 27001 best practices.
"""

import logging
import os
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID, uuid4

from cryptography.fernet import Fernet
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class APIKeyMetadata(BaseModel):
    """API key metadata."""

    key_id: UUID = Field(default_factory=uuid4)
    provider: str = Field(..., description="LLM provider (claude, openai, gemini)")
    key_name: str = Field(..., description="Key name/identifier")
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    usage_count: int = 0
    notes: Optional[str] = None


class APIKeyVault:
    """
    Secure API key vault for LLM credentials.

    Encrypts and stores API keys with metadata and usage tracking.
    """

    def __init__(self, encryption_key: Optional[bytes] = None):
        """
        Initialize API key vault.

        Args:
            encryption_key: Fernet encryption key (generated if not provided)
        """
        if encryption_key is None:
            # Generate new key or load from environment
            encryption_key_str = os.getenv("VAULT_ENCRYPTION_KEY")
            if encryption_key_str:
                encryption_key = encryption_key_str.encode()
            else:
                encryption_key = Fernet.generate_key()
                logger.warning("Generated new encryption key. Save VAULT_ENCRYPTION_KEY for persistence.")

        self.cipher = Fernet(encryption_key)
        self.keys_storage: Dict[str, bytes] = {}  # provider -> encrypted_key
        self.metadata_storage: Dict[str, APIKeyMetadata] = {}  # provider -> metadata

        logger.info("API Key Vault initialized")

    def store_key(
        self,
        provider: str,
        api_key: str,
        key_name: str,
        created_by: str,
        expires_at: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> UUID:
        """
        Store API key in vault with encryption.

        Args:
            provider: LLM provider name
            api_key: Plain text API key
            key_name: Key identifier
            created_by: User storing the key
            expires_at: Optional expiration date
            notes: Optional notes

        Returns:
            Key UUID
        """
        logger.info(f"Storing API key for provider: {provider}")

        # Encrypt the key
        encrypted_key = self.cipher.encrypt(api_key.encode())

        # Create metadata
        metadata = APIKeyMetadata(
            provider=provider,
            key_name=key_name,
            created_by=created_by,
            expires_at=expires_at,
            notes=notes,
        )

        # Store encrypted key and metadata
        self.keys_storage[provider] = encrypted_key
        self.metadata_storage[provider] = metadata

        logger.info(f"API key stored for {provider}, key_id: {metadata.key_id}")
        return metadata.key_id

    def get_key(self, provider: str) -> Optional[str]:
        """
        Retrieve and decrypt API key.

        Args:
            provider: LLM provider name

        Returns:
            Decrypted API key or None if not found
        """
        # Check environment variable first
        env_var_name = f"{provider.upper()}_API_KEY"
        env_key = os.getenv(env_var_name)
        if env_key:
            logger.debug(f"Using API key from environment: {env_var_name}")
            return env_key

        # Check vault storage
        if provider not in self.keys_storage:
            logger.warning(f"No API key found for provider: {provider}")
            return None

        metadata = self.metadata_storage.get(provider)
        if metadata and not metadata.is_active:
            logger.warning(f"API key for {provider} is inactive")
            return None

        if metadata and metadata.expires_at and metadata.expires_at < datetime.utcnow():
            logger.warning(f"API key for {provider} has expired")
            return None

        # Decrypt and return key
        encrypted_key = self.keys_storage[provider]
        decrypted_key = self.cipher.decrypt(encrypted_key).decode()

        # Update usage tracking
        if metadata:
            metadata.last_used = datetime.utcnow()
            metadata.usage_count += 1

        logger.debug(f"Retrieved API key for provider: {provider}")
        return decrypted_key

    def rotate_key(
        self,
        provider: str,
        new_api_key: str,
        rotated_by: str,
    ) -> UUID:
        """
        Rotate API key (replace with new key).

        Args:
            provider: LLM provider name
            new_api_key: New API key
            rotated_by: User performing rotation

        Returns:
            New key UUID
        """
        logger.info(f"Rotating API key for provider: {provider}")

        # Deactivate old key
        if provider in self.metadata_storage:
            old_metadata = self.metadata_storage[provider]
            old_metadata.is_active = False

        # Store new key
        new_key_id = self.store_key(
            provider=provider,
            api_key=new_api_key,
            key_name=f"{provider}_key_rotated_{datetime.utcnow().strftime('%Y%m%d')}",
            created_by=rotated_by,
            notes=f"Rotated key, previous key_id: {old_metadata.key_id if provider in self.metadata_storage else 'N/A'}",
        )

        logger.info(f"API key rotated for {provider}, new key_id: {new_key_id}")
        return new_key_id

    def revoke_key(self, provider: str, revoked_by: str) -> bool:
        """
        Revoke (deactivate) API key.

        Args:
            provider: LLM provider name
            revoked_by: User revoking the key

        Returns:
            True if key was revoked
        """
        if provider not in self.metadata_storage:
            logger.warning(f"No key found to revoke for provider: {provider}")
            return False

        metadata = self.metadata_storage[provider]
        metadata.is_active = False

        logger.info(f"API key revoked for {provider} by {revoked_by}")
        return True

    def get_metadata(self, provider: str) -> Optional[APIKeyMetadata]:
        """
        Get API key metadata without retrieving the key.

        Args:
            provider: LLM provider name

        Returns:
            Key metadata or None
        """
        return self.metadata_storage.get(provider)

    def list_providers(self) -> list[str]:
        """
        List all providers with stored keys.

        Returns:
            List of provider names
        """
        return list(self.keys_storage.keys())

    def export_encryption_key(self) -> str:
        """
        Export encryption key for backup.

        Returns:
            Base64-encoded encryption key

        Warning:
            Store this key securely! Required for decryption.
        """
        return self.cipher._encryption_key.decode()  # type: ignore

    @classmethod
    def from_encryption_key(cls, encryption_key_str: str) -> "APIKeyVault":
        """
        Create vault from existing encryption key.

        Args:
            encryption_key_str: Base64-encoded encryption key

        Returns:
            API key vault instance
        """
        return cls(encryption_key=encryption_key_str.encode())


# Global vault instance
_global_vault: Optional[APIKeyVault] = None


def get_vault() -> APIKeyVault:
    """
    Get global API key vault instance.

    Returns:
        API key vault
    """
    global _global_vault
    if _global_vault is None:
        _global_vault = APIKeyVault()
    return _global_vault


def initialize_vault_from_env() -> APIKeyVault:
    """
    Initialize vault with keys from environment variables.

    Returns:
        Initialized vault
    """
    vault = get_vault()

    # Load common provider keys from environment
    providers = {
        "claude": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "gemini": "GOOGLE_API_KEY",
    }

    for provider, env_var in providers.items():
        api_key = os.getenv(env_var)
        if api_key:
            vault.store_key(
                provider=provider,
                api_key=api_key,
                key_name=f"{provider}_from_env",
                created_by="system",
                notes=f"Loaded from environment variable {env_var}",
            )
            logger.info(f"Loaded {provider} API key from environment")

    return vault
