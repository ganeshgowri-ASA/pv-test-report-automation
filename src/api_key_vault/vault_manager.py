"""Vault Manager - HashiCorp Vault and AWS Secrets Manager integration.

ISO 17025 Compliant Credential Management
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json

try:
    import hvac
    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False

try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

from .encryption import EncryptionService
from .audit_logger import VaultAuditLogger

logger = logging.getLogger(__name__)


class VaultBackend:
    """Base class for vault backends."""

    def get_secret(self, path: str) -> Dict[str, Any]:
        """Get secret from vault."""
        raise NotImplementedError

    def set_secret(self, path: str, data: Dict[str, Any]) -> None:
        """Set secret in vault."""
        raise NotImplementedError

    def delete_secret(self, path: str) -> None:
        """Delete secret from vault."""
        raise NotImplementedError

    def list_secrets(self, path: str) -> list:
        """List secrets in vault."""
        raise NotImplementedError


class HashiCorpVaultBackend(VaultBackend):
    """HashiCorp Vault backend."""

    def __init__(self, url: str, token: str, namespace: str = ""):
        """Initialize HashiCorp Vault client.

        Args:
            url: Vault server URL.
            token: Vault authentication token.
            namespace: Vault namespace.
        """
        if not VAULT_AVAILABLE:
            raise RuntimeError("hvac package not installed. Install with: pip install hvac")

        self.client = hvac.Client(url=url, token=token, namespace=namespace)
        if not self.client.is_authenticated():
            raise ValueError("Vault authentication failed")

        logger.info(f"Connected to HashiCorp Vault at {url}")

    def get_secret(self, path: str) -> Dict[str, Any]:
        """Get secret from Vault."""
        try:
            response = self.client.secrets.kv.v2.read_secret_version(path=path)
            return response["data"]["data"]
        except Exception as e:
            logger.error(f"Failed to get secret from Vault: {e}")
            raise

    def set_secret(self, path: str, data: Dict[str, Any]) -> None:
        """Set secret in Vault."""
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=data
            )
            logger.info(f"Secret stored in Vault at path: {path}")
        except Exception as e:
            logger.error(f"Failed to set secret in Vault: {e}")
            raise

    def delete_secret(self, path: str) -> None:
        """Delete secret from Vault."""
        try:
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(path=path)
            logger.info(f"Secret deleted from Vault at path: {path}")
        except Exception as e:
            logger.error(f"Failed to delete secret from Vault: {e}")
            raise

    def list_secrets(self, path: str) -> list:
        """List secrets in Vault."""
        try:
            response = self.client.secrets.kv.v2.list_secrets(path=path)
            return response["data"]["keys"]
        except Exception as e:
            logger.error(f"Failed to list secrets in Vault: {e}")
            return []


class AWSSecretsManagerBackend(VaultBackend):
    """AWS Secrets Manager backend."""

    def __init__(self, region: str, prefix: str = ""):
        """Initialize AWS Secrets Manager client.

        Args:
            region: AWS region.
            prefix: Prefix for secret names.
        """
        if not AWS_AVAILABLE:
            raise RuntimeError("boto3 package not installed. Install with: pip install boto3")

        self.client = boto3.client("secretsmanager", region_name=region)
        self.prefix = prefix
        logger.info(f"Connected to AWS Secrets Manager in region {region}")

    def _get_full_path(self, path: str) -> str:
        """Get full secret path with prefix."""
        return f"{self.prefix}{path}" if self.prefix else path

    def get_secret(self, path: str) -> Dict[str, Any]:
        """Get secret from AWS Secrets Manager."""
        try:
            response = self.client.get_secret_value(SecretId=self._get_full_path(path))
            return json.loads(response["SecretString"])
        except ClientError as e:
            logger.error(f"Failed to get secret from AWS Secrets Manager: {e}")
            raise

    def set_secret(self, path: str, data: Dict[str, Any]) -> None:
        """Set secret in AWS Secrets Manager."""
        try:
            secret_id = self._get_full_path(path)
            try:
                self.client.update_secret(
                    SecretId=secret_id,
                    SecretString=json.dumps(data)
                )
                logger.info(f"Secret updated in AWS Secrets Manager: {secret_id}")
            except ClientError as e:
                if e.response["Error"]["Code"] == "ResourceNotFoundException":
                    self.client.create_secret(
                        Name=secret_id,
                        SecretString=json.dumps(data)
                    )
                    logger.info(f"Secret created in AWS Secrets Manager: {secret_id}")
                else:
                    raise
        except Exception as e:
            logger.error(f"Failed to set secret in AWS Secrets Manager: {e}")
            raise

    def delete_secret(self, path: str) -> None:
        """Delete secret from AWS Secrets Manager."""
        try:
            self.client.delete_secret(
                SecretId=self._get_full_path(path),
                ForceDeleteWithoutRecovery=True
            )
            logger.info(f"Secret deleted from AWS Secrets Manager: {path}")
        except ClientError as e:
            logger.error(f"Failed to delete secret from AWS Secrets Manager: {e}")
            raise

    def list_secrets(self, path: str) -> list:
        """List secrets in AWS Secrets Manager."""
        try:
            response = self.client.list_secrets()
            prefix = self._get_full_path(path)
            return [
                s["Name"].replace(self.prefix, "", 1)
                for s in response["SecretList"]
                if s["Name"].startswith(prefix)
            ]
        except Exception as e:
            logger.error(f"Failed to list secrets in AWS Secrets Manager: {e}")
            return []


class LocalEncryptedBackend(VaultBackend):
    """Local encrypted storage backend (for development/testing)."""

    def __init__(self, encryption_service: EncryptionService, storage_path: str = "secrets.json"):
        """Initialize local encrypted backend.

        Args:
            encryption_service: Encryption service for securing secrets.
            storage_path: Path to local storage file.
        """
        self.encryption = encryption_service
        self.storage_path = storage_path
        self._load_storage()
        logger.info(f"Local encrypted storage initialized at {storage_path}")

    def _load_storage(self) -> None:
        """Load secrets from local storage."""
        try:
            with open(self.storage_path, "r") as f:
                self._storage = json.load(f)
        except FileNotFoundError:
            self._storage = {}

    def _save_storage(self) -> None:
        """Save secrets to local storage."""
        with open(self.storage_path, "w") as f:
            json.dump(self._storage, f, indent=2)

    def get_secret(self, path: str) -> Dict[str, Any]:
        """Get secret from local storage."""
        if path not in self._storage:
            raise KeyError(f"Secret not found: {path}")

        encrypted_data = self._storage[path]
        return self.encryption.decrypt_dict(encrypted_data)

    def set_secret(self, path: str, data: Dict[str, Any]) -> None:
        """Set secret in local storage."""
        encrypted_data = self.encryption.encrypt_dict(data)
        self._storage[path] = encrypted_data
        self._save_storage()
        logger.info(f"Secret stored locally at path: {path}")

    def delete_secret(self, path: str) -> None:
        """Delete secret from local storage."""
        if path in self._storage:
            del self._storage[path]
            self._save_storage()
            logger.info(f"Secret deleted from local storage: {path}")

    def list_secrets(self, path: str) -> list:
        """List secrets in local storage."""
        return [k for k in self._storage.keys() if k.startswith(path)]


class VaultManager:
    """Unified vault manager supporting multiple backends.

    ISO 17025 Compliant Credential Management with:
    - HashiCorp Vault integration
    - AWS Secrets Manager integration
    - Local encrypted storage (development)
    - Access logging and audit trail
    - Key rotation support
    """

    def __init__(
        self,
        backend_type: str = "local",
        vault_url: Optional[str] = None,
        vault_token: Optional[str] = None,
        vault_namespace: str = "",
        aws_region: str = "us-east-1",
        aws_prefix: str = "",
        encryption_key: Optional[str] = None
    ):
        """Initialize vault manager.

        Args:
            backend_type: Backend type ('hashicorp', 'aws', 'local').
            vault_url: HashiCorp Vault URL.
            vault_token: HashiCorp Vault token.
            vault_namespace: HashiCorp Vault namespace.
            aws_region: AWS region.
            aws_prefix: AWS Secrets Manager prefix.
            encryption_key: Encryption key for local backend.
        """
        self.audit_logger = VaultAuditLogger()

        if backend_type == "hashicorp":
            self.backend = HashiCorpVaultBackend(vault_url, vault_token, vault_namespace)
        elif backend_type == "aws":
            self.backend = AWSSecretsManagerBackend(aws_region, aws_prefix)
        elif backend_type == "local":
            encryption = EncryptionService(encryption_key)
            self.backend = LocalEncryptedBackend(encryption)
        else:
            raise ValueError(f"Unknown backend type: {backend_type}")

        logger.info(f"VaultManager initialized with backend: {backend_type}")

    def get_secret(self, path: str, user_id: str = "system") -> Dict[str, Any]:
        """Get secret from vault with audit logging.

        Args:
            path: Secret path.
            user_id: User ID for audit logging.

        Returns:
            Secret data.
        """
        try:
            secret = self.backend.get_secret(path)
            self.audit_logger.log_access(user_id, path, "READ", success=True)
            return secret
        except Exception as e:
            self.audit_logger.log_access(user_id, path, "READ", success=False, error=str(e))
            raise

    def set_secret(self, path: str, data: Dict[str, Any], user_id: str = "system") -> None:
        """Set secret in vault with audit logging.

        Args:
            path: Secret path.
            data: Secret data.
            user_id: User ID for audit logging.
        """
        try:
            self.backend.set_secret(path, data)
            self.audit_logger.log_access(user_id, path, "WRITE", success=True)
        except Exception as e:
            self.audit_logger.log_access(user_id, path, "WRITE", success=False, error=str(e))
            raise

    def delete_secret(self, path: str, user_id: str = "system") -> None:
        """Delete secret from vault with audit logging.

        Args:
            path: Secret path.
            user_id: User ID for audit logging.
        """
        try:
            self.backend.delete_secret(path)
            self.audit_logger.log_access(user_id, path, "DELETE", success=True)
        except Exception as e:
            self.audit_logger.log_access(user_id, path, "DELETE", success=False, error=str(e))
            raise

    def list_secrets(self, path: str = "", user_id: str = "system") -> list:
        """List secrets in vault with audit logging.

        Args:
            path: Path prefix to list.
            user_id: User ID for audit logging.

        Returns:
            List of secret paths.
        """
        try:
            secrets = self.backend.list_secrets(path)
            self.audit_logger.log_access(user_id, path, "LIST", success=True)
            return secrets
        except Exception as e:
            self.audit_logger.log_access(user_id, path, "LIST", success=False, error=str(e))
            raise

    def get_api_key(self, service: str, user_id: str = "system") -> str:
        """Get API key for a specific service.

        Args:
            service: Service name (e.g., 'anthropic', 'openai').
            user_id: User ID for audit logging.

        Returns:
            API key.
        """
        secret_path = f"api_keys/{service}"
        secret = self.get_secret(secret_path, user_id)
        return secret.get("api_key", "")

    def set_api_key(self, service: str, api_key: str, expiry_days: Optional[int] = None, user_id: str = "system") -> None:
        """Set API key for a specific service.

        Args:
            service: Service name.
            api_key: API key value.
            expiry_days: Optional expiry in days.
            user_id: User ID for audit logging.
        """
        secret_path = f"api_keys/{service}"
        data = {
            "api_key": api_key,
            "created_at": datetime.utcnow().isoformat(),
        }

        if expiry_days:
            expiry_date = datetime.utcnow() + timedelta(days=expiry_days)
            data["expires_at"] = expiry_date.isoformat()

        self.set_secret(secret_path, data, user_id)
