"""API Key Rotation Service.

Automated key rotation and expiry management.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class KeyMetadata:
    """Metadata for an API key."""

    service: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    rotation_interval_days: Optional[int] = None
    last_rotated: Optional[datetime] = None
    rotation_count: int = 0


class KeyRotationService:
    """Service for managing API key rotation and expiry.

    ISO 17025 Compliance:
    - Automated key rotation
    - Expiry tracking
    - Rotation history
    - Security event logging
    """

    def __init__(self, vault_manager):
        """Initialize key rotation service.

        Args:
            vault_manager: VaultManager instance for key storage.
        """
        from .vault_manager import VaultManager
        self.vault: VaultManager = vault_manager
        self._metadata_cache: Dict[str, KeyMetadata] = {}
        logger.info("KeyRotationService initialized")

    def register_key(
        self,
        service: str,
        api_key: str,
        expiry_days: Optional[int] = 90,
        rotation_interval_days: Optional[int] = 30,
        user_id: str = "system"
    ) -> None:
        """Register an API key with rotation policy.

        Args:
            service: Service name.
            api_key: API key value.
            expiry_days: Days until key expires.
            rotation_interval_days: Days between automatic rotations.
            user_id: User ID for audit logging.
        """
        now = datetime.utcnow()
        metadata = KeyMetadata(
            service=service,
            created_at=now,
            expires_at=now + timedelta(days=expiry_days) if expiry_days else None,
            rotation_interval_days=rotation_interval_days,
            last_rotated=now,
            rotation_count=0
        )

        # Store key in vault
        self.vault.set_api_key(service, api_key, expiry_days, user_id)

        # Store metadata
        self._store_metadata(metadata, user_id)

        logger.info(f"Registered API key for service: {service}")

    def check_expiry(self, service: str) -> bool:
        """Check if API key is expired.

        Args:
            service: Service name.

        Returns:
            True if key is expired, False otherwise.
        """
        metadata = self._get_metadata(service)
        if not metadata or not metadata.expires_at:
            return False

        is_expired = datetime.utcnow() > metadata.expires_at
        if is_expired:
            logger.warning(f"API key expired for service: {service}")

        return is_expired

    def check_rotation_needed(self, service: str) -> bool:
        """Check if API key needs rotation.

        Args:
            service: Service name.

        Returns:
            True if rotation is needed, False otherwise.
        """
        metadata = self._get_metadata(service)
        if not metadata or not metadata.rotation_interval_days:
            return False

        if not metadata.last_rotated:
            return True

        days_since_rotation = (datetime.utcnow() - metadata.last_rotated).days
        needs_rotation = days_since_rotation >= metadata.rotation_interval_days

        if needs_rotation:
            logger.info(f"API key rotation needed for service: {service}")

        return needs_rotation

    def rotate_key(
        self,
        service: str,
        new_api_key: str,
        user_id: str = "system"
    ) -> None:
        """Rotate an API key.

        Args:
            service: Service name.
            new_api_key: New API key value.
            user_id: User ID for audit logging.
        """
        metadata = self._get_metadata(service)
        if not metadata:
            raise ValueError(f"No metadata found for service: {service}")

        # Update key in vault
        expiry_days = None
        if metadata.expires_at:
            remaining_days = (metadata.expires_at - datetime.utcnow()).days
            expiry_days = max(remaining_days, 0)

        self.vault.set_api_key(service, new_api_key, expiry_days, user_id)

        # Update metadata
        metadata.last_rotated = datetime.utcnow()
        metadata.rotation_count += 1
        self._store_metadata(metadata, user_id)

        logger.info(f"Rotated API key for service: {service} (rotation #{metadata.rotation_count})")

    def get_key_info(self, service: str) -> Optional[Dict[str, Any]]:
        """Get information about an API key.

        Args:
            service: Service name.

        Returns:
            Dictionary with key information or None if not found.
        """
        metadata = self._get_metadata(service)
        if not metadata:
            return None

        info = {
            "service": metadata.service,
            "created_at": metadata.created_at.isoformat(),
            "expires_at": metadata.expires_at.isoformat() if metadata.expires_at else None,
            "last_rotated": metadata.last_rotated.isoformat() if metadata.last_rotated else None,
            "rotation_count": metadata.rotation_count,
            "is_expired": self.check_expiry(service),
            "rotation_needed": self.check_rotation_needed(service),
        }

        if metadata.expires_at:
            days_until_expiry = (metadata.expires_at - datetime.utcnow()).days
            info["days_until_expiry"] = max(days_until_expiry, 0)

        if metadata.rotation_interval_days and metadata.last_rotated:
            days_since_rotation = (datetime.utcnow() - metadata.last_rotated).days
            info["days_since_rotation"] = days_since_rotation
            info["rotation_interval_days"] = metadata.rotation_interval_days

        return info

    def get_all_keys_info(self) -> List[Dict[str, Any]]:
        """Get information about all registered API keys.

        Returns:
            List of key information dictionaries.
        """
        try:
            services = self.vault.list_secrets("api_keys/")
            return [
                self.get_key_info(service.replace("api_keys/", ""))
                for service in services
            ]
        except Exception as e:
            logger.error(f"Failed to get all keys info: {e}")
            return []

    def _get_metadata(self, service: str) -> Optional[KeyMetadata]:
        """Get metadata for a service.

        Args:
            service: Service name.

        Returns:
            KeyMetadata or None if not found.
        """
        # Check cache first
        if service in self._metadata_cache:
            return self._metadata_cache[service]

        # Load from vault
        try:
            metadata_path = f"api_keys_metadata/{service}"
            data = self.vault.get_secret(metadata_path)

            metadata = KeyMetadata(
                service=service,
                created_at=datetime.fromisoformat(data["created_at"]),
                expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
                rotation_interval_days=data.get("rotation_interval_days"),
                last_rotated=datetime.fromisoformat(data["last_rotated"]) if data.get("last_rotated") else None,
                rotation_count=data.get("rotation_count", 0)
            )

            self._metadata_cache[service] = metadata
            return metadata

        except Exception as e:
            logger.debug(f"No metadata found for service {service}: {e}")
            return None

    def _store_metadata(self, metadata: KeyMetadata, user_id: str = "system") -> None:
        """Store metadata for a service.

        Args:
            metadata: KeyMetadata to store.
            user_id: User ID for audit logging.
        """
        metadata_path = f"api_keys_metadata/{metadata.service}"
        data = {
            "service": metadata.service,
            "created_at": metadata.created_at.isoformat(),
            "expires_at": metadata.expires_at.isoformat() if metadata.expires_at else None,
            "rotation_interval_days": metadata.rotation_interval_days,
            "last_rotated": metadata.last_rotated.isoformat() if metadata.last_rotated else None,
            "rotation_count": metadata.rotation_count,
        }

        self.vault.set_secret(metadata_path, data, user_id)
        self._metadata_cache[metadata.service] = metadata
