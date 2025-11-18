"""Encryption service for secure credential storage.

ISO 17025 Compliant Encryption
"""

import base64
import os
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)


class EncryptionService:
    """Secure encryption service using Fernet (AES-128-CBC)."""

    def __init__(self, master_key: Optional[str] = None):
        """Initialize encryption service.

        Args:
            master_key: Master encryption key (32 bytes base64 encoded).
                       If not provided, generates a new key.
        """
        if master_key:
            self._key = master_key.encode()
        else:
            self._key = Fernet.generate_key()

        self._fernet = Fernet(self._key)
        logger.info("EncryptionService initialized")

    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key.

        Returns:
            Base64 encoded encryption key.
        """
        return Fernet.generate_key().decode()

    @staticmethod
    def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> tuple[str, bytes]:
        """Derive encryption key from password using PBKDF2.

        Args:
            password: User password.
            salt: Salt for key derivation. Generated if not provided.

        Returns:
            Tuple of (derived_key, salt).
        """
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode(), salt

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext string.

        Args:
            plaintext: String to encrypt.

        Returns:
            Base64 encoded encrypted string.

        Raises:
            ValueError: If encryption fails.
        """
        try:
            encrypted = self._fernet.encrypt(plaintext.encode())
            logger.debug("Successfully encrypted data")
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError(f"Encryption failed: {e}")

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt encrypted string.

        Args:
            ciphertext: Base64 encoded encrypted string.

        Returns:
            Decrypted plaintext string.

        Raises:
            ValueError: If decryption fails.
        """
        try:
            decrypted = self._fernet.decrypt(ciphertext.encode())
            logger.debug("Successfully decrypted data")
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError(f"Decryption failed: {e}")

    def encrypt_dict(self, data: dict) -> dict:
        """Encrypt all string values in a dictionary.

        Args:
            data: Dictionary with string values.

        Returns:
            Dictionary with encrypted values.
        """
        encrypted_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                encrypted_data[key] = self.encrypt(value)
            else:
                encrypted_data[key] = value

        return encrypted_data

    def decrypt_dict(self, data: dict) -> dict:
        """Decrypt all encrypted values in a dictionary.

        Args:
            data: Dictionary with encrypted values.

        Returns:
            Dictionary with decrypted values.
        """
        decrypted_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                try:
                    decrypted_data[key] = self.decrypt(value)
                except ValueError:
                    # Not encrypted, keep original value
                    decrypted_data[key] = value
            else:
                decrypted_data[key] = value

        return decrypted_data

    def rotate_key(self, new_key: str) -> None:
        """Rotate encryption key.

        Args:
            new_key: New encryption key.

        Note:
            This only updates the key used for future operations.
            Existing encrypted data needs to be re-encrypted separately.
        """
        self._key = new_key.encode()
        self._fernet = Fernet(self._key)
        logger.info("Encryption key rotated successfully")

    def get_key(self) -> str:
        """Get current encryption key.

        Returns:
            Base64 encoded encryption key.

        Warning:
            Use with caution - exposing encryption keys is a security risk.
        """
        return self._key.decode()
