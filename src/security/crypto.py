"""
Cryptographic utilities for PV Test Report Automation System
Provides AES encryption, password hashing (bcrypt), and Fernet-based key vault
ISO 17025 and 21 CFR Part 11 compliant
"""

import os
import base64
import hashlib
import secrets
from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


class EncryptionError(Exception):
    """Base exception for encryption-related errors"""
    pass


class DecryptionError(Exception):
    """Base exception for decryption-related errors"""
    pass


class KeyDerivationError(Exception):
    """Exception for key derivation failures"""
    pass


class CryptoAlgorithm(Enum):
    """Supported cryptographic algorithms"""
    AES_256_CBC = "AES-256-CBC"
    FERNET = "Fernet"
    BCRYPT = "bcrypt"


class AESCipher:
    """
    AES-256-CBC encryption/decryption with PKCS7 padding
    Compliant with NIST FIPS 197 standards
    """

    BLOCK_SIZE = 128  # AES block size in bits
    KEY_SIZE = 32  # 256 bits
    IV_SIZE = 16  # 128 bits

    def __init__(self, key: Optional[bytes] = None):
        """
        Initialize AES cipher with optional key

        Args:
            key: 32-byte encryption key. If None, generates new key.

        Raises:
            EncryptionError: If key size is invalid
        """
        if key is None:
            self.key = self._generate_key()
        else:
            if len(key) != self.KEY_SIZE:
                raise EncryptionError(
                    f"Invalid key size. Expected {self.KEY_SIZE} bytes, got {len(key)}"
                )
            self.key = key

    @staticmethod
    def _generate_key() -> bytes:
        """Generate cryptographically secure 256-bit key"""
        return secrets.token_bytes(AESCipher.KEY_SIZE)

    @staticmethod
    def _generate_iv() -> bytes:
        """Generate cryptographically secure initialization vector"""
        return secrets.token_bytes(AESCipher.IV_SIZE)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext using AES-256-CBC

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded string containing IV + ciphertext

        Raises:
            EncryptionError: If encryption fails
        """
        try:
            # Generate random IV
            iv = self._generate_iv()

            # Convert plaintext to bytes
            plaintext_bytes = plaintext.encode('utf-8')

            # Apply PKCS7 padding
            padder = padding.PKCS7(self.BLOCK_SIZE).padder()
            padded_data = padder.update(plaintext_bytes) + padder.finalize()

            # Create cipher and encrypt
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.CBC(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()

            # Combine IV + ciphertext and encode as base64
            encrypted_data = iv + ciphertext
            return base64.b64encode(encrypted_data).decode('utf-8')

        except Exception as e:
            raise EncryptionError(f"AES encryption failed: {str(e)}") from e

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt AES-256-CBC ciphertext

        Args:
            ciphertext: Base64-encoded string containing IV + ciphertext

        Returns:
            Decrypted plaintext string

        Raises:
            DecryptionError: If decryption fails
        """
        try:
            # Decode base64
            encrypted_data = base64.b64decode(ciphertext.encode('utf-8'))

            # Extract IV and ciphertext
            iv = encrypted_data[:self.IV_SIZE]
            actual_ciphertext = encrypted_data[self.IV_SIZE:]

            # Create cipher and decrypt
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            padded_plaintext = decryptor.update(actual_ciphertext) + decryptor.finalize()

            # Remove PKCS7 padding
            unpadder = padding.PKCS7(self.BLOCK_SIZE).unpadder()
            plaintext_bytes = unpadder.update(padded_plaintext) + unpadder.finalize()

            return plaintext_bytes.decode('utf-8')

        except Exception as e:
            raise DecryptionError(f"AES decryption failed: {str(e)}") from e

    def get_key_base64(self) -> str:
        """Return base64-encoded key for storage"""
        return base64.b64encode(self.key).decode('utf-8')

    @classmethod
    def from_base64_key(cls, key_b64: str) -> 'AESCipher':
        """Create AESCipher from base64-encoded key"""
        key = base64.b64decode(key_b64.encode('utf-8'))
        return cls(key=key)


class PasswordHasher:
    """
    Bcrypt password hashing with configurable work factor
    Compliant with OWASP password storage guidelines
    """

    # Default work factor (cost parameter)
    # Higher = more secure but slower
    DEFAULT_ROUNDS = 12
    MIN_ROUNDS = 10
    MAX_ROUNDS = 16

    def __init__(self, rounds: int = DEFAULT_ROUNDS):
        """
        Initialize password hasher

        Args:
            rounds: Bcrypt work factor (10-16 recommended)

        Raises:
            ValueError: If rounds is outside valid range
        """
        if not self.MIN_ROUNDS <= rounds <= self.MAX_ROUNDS:
            raise ValueError(
                f"Rounds must be between {self.MIN_ROUNDS} and {self.MAX_ROUNDS}"
            )
        self.rounds = rounds

    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt

        Args:
            password: Plain text password

        Returns:
            Bcrypt hash string (includes salt)

        Raises:
            EncryptionError: If hashing fails
        """
        try:
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt(rounds=self.rounds)
            hashed = bcrypt.hashpw(password_bytes, salt)
            return hashed.decode('utf-8')
        except Exception as e:
            raise EncryptionError(f"Password hashing failed: {str(e)}") from e

    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify password against bcrypt hash

        Args:
            password: Plain text password to verify
            hashed: Bcrypt hash to check against

        Returns:
            True if password matches, False otherwise

        Raises:
            DecryptionError: If verification process fails
        """
        try:
            password_bytes = password.encode('utf-8')
            hashed_bytes = hashed.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception as e:
            raise DecryptionError(f"Password verification failed: {str(e)}") from e

    def needs_rehash(self, hashed: str) -> bool:
        """
        Check if password hash needs to be updated
        (e.g., if work factor has changed)

        Args:
            hashed: Existing bcrypt hash

        Returns:
            True if hash should be regenerated
        """
        try:
            # Extract rounds from hash
            # Bcrypt hash format: $2b$rounds$salt+hash
            parts = hashed.split('$')
            if len(parts) < 3:
                return True

            current_rounds = int(parts[2])
            return current_rounds != self.rounds
        except (ValueError, IndexError):
            return True


class FernetVault:
    """
    Fernet symmetric encryption for secure key vault
    Provides authenticated encryption with timestamp verification
    """

    def __init__(self, master_key: Optional[bytes] = None):
        """
        Initialize Fernet vault

        Args:
            master_key: 32-byte master key. If None, generates new key.
        """
        if master_key is None:
            self.master_key = Fernet.generate_key()
        else:
            self.master_key = master_key

        self.cipher = Fernet(self.master_key)

    def encrypt(self, data: str) -> str:
        """
        Encrypt data with Fernet (includes timestamp and MAC)

        Args:
            data: String to encrypt

        Returns:
            Base64-encoded Fernet token

        Raises:
            EncryptionError: If encryption fails
        """
        try:
            data_bytes = data.encode('utf-8')
            token = self.cipher.encrypt(data_bytes)
            return token.decode('utf-8')
        except Exception as e:
            raise EncryptionError(f"Fernet encryption failed: {str(e)}") from e

    def decrypt(self, token: str, ttl: Optional[int] = None) -> str:
        """
        Decrypt Fernet token with optional TTL verification

        Args:
            token: Fernet token to decrypt
            ttl: Optional time-to-live in seconds. If set, token must be
                 younger than TTL or decryption fails.

        Returns:
            Decrypted string

        Raises:
            DecryptionError: If decryption or TTL verification fails
        """
        try:
            token_bytes = token.encode('utf-8')

            if ttl is not None:
                data = self.cipher.decrypt(token_bytes, ttl=ttl)
            else:
                data = self.cipher.decrypt(token_bytes)

            return data.decode('utf-8')
        except Exception as e:
            raise DecryptionError(f"Fernet decryption failed: {str(e)}") from e

    def rotate_key(self, new_key: bytes, tokens: list[str]) -> list[str]:
        """
        Rotate encryption key by re-encrypting all tokens

        Args:
            new_key: New 32-byte master key
            tokens: List of tokens to re-encrypt

        Returns:
            List of re-encrypted tokens with new key

        Raises:
            EncryptionError: If key rotation fails
        """
        try:
            new_cipher = Fernet(new_key)
            rotated_tokens = []

            for token in tokens:
                # Decrypt with old key
                data = self.decrypt(token)
                # Encrypt with new key
                new_token = new_cipher.encrypt(data.encode('utf-8'))
                rotated_tokens.append(new_token.decode('utf-8'))

            # Update vault to use new key
            self.master_key = new_key
            self.cipher = new_cipher

            return rotated_tokens
        except Exception as e:
            raise EncryptionError(f"Key rotation failed: {str(e)}") from e

    def get_key_base64(self) -> str:
        """Return base64-encoded master key"""
        return self.master_key.decode('utf-8')

    @classmethod
    def from_base64_key(cls, key_b64: str) -> 'FernetVault':
        """Create FernetVault from base64-encoded key"""
        key = key_b64.encode('utf-8')
        return cls(master_key=key)


class KeyDerivation:
    """
    PBKDF2-HMAC key derivation for generating encryption keys from passwords
    Compliant with NIST SP 800-132
    """

    DEFAULT_ITERATIONS = 600000  # OWASP 2023 recommendation for PBKDF2-HMAC-SHA256
    SALT_SIZE = 32  # 256 bits
    KEY_SIZE = 32  # 256 bits

    @staticmethod
    def derive_key(
        password: str,
        salt: Optional[bytes] = None,
        iterations: int = DEFAULT_ITERATIONS
    ) -> Tuple[bytes, bytes]:
        """
        Derive encryption key from password using PBKDF2-HMAC-SHA256

        Args:
            password: Password to derive key from
            salt: Optional salt. If None, generates new salt.
            iterations: Number of PBKDF2 iterations

        Returns:
            Tuple of (derived_key, salt)

        Raises:
            KeyDerivationError: If key derivation fails
        """
        try:
            if salt is None:
                salt = secrets.token_bytes(KeyDerivation.SALT_SIZE)

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=KeyDerivation.KEY_SIZE,
                salt=salt,
                iterations=iterations,
                backend=default_backend()
            )

            key = kdf.derive(password.encode('utf-8'))
            return key, salt

        except Exception as e:
            raise KeyDerivationError(f"Key derivation failed: {str(e)}") from e

    @staticmethod
    def derive_key_base64(
        password: str,
        salt_b64: Optional[str] = None,
        iterations: int = DEFAULT_ITERATIONS
    ) -> Tuple[str, str]:
        """
        Derive key with base64-encoded inputs/outputs

        Args:
            password: Password to derive key from
            salt_b64: Optional base64-encoded salt
            iterations: Number of PBKDF2 iterations

        Returns:
            Tuple of (key_base64, salt_base64)
        """
        salt = None
        if salt_b64 is not None:
            salt = base64.b64decode(salt_b64.encode('utf-8'))

        key, salt = KeyDerivation.derive_key(password, salt, iterations)

        return (
            base64.b64encode(key).decode('utf-8'),
            base64.b64encode(salt).decode('utf-8')
        )


class SecureRandom:
    """
    Cryptographically secure random number and token generation
    """

    @staticmethod
    def generate_token(nbytes: int = 32) -> str:
        """
        Generate cryptographically secure random token

        Args:
            nbytes: Number of random bytes (default 32)

        Returns:
            URL-safe base64-encoded token
        """
        return secrets.token_urlsafe(nbytes)

    @staticmethod
    def generate_hex(nbytes: int = 32) -> str:
        """
        Generate cryptographically secure random hex string

        Args:
            nbytes: Number of random bytes (default 32)

        Returns:
            Hexadecimal string
        """
        return secrets.token_hex(nbytes)

    @staticmethod
    def generate_bytes(nbytes: int = 32) -> bytes:
        """
        Generate cryptographically secure random bytes

        Args:
            nbytes: Number of random bytes (default 32)

        Returns:
            Random bytes
        """
        return secrets.token_bytes(nbytes)

    @staticmethod
    def generate_pin(digits: int = 6) -> str:
        """
        Generate cryptographically secure numeric PIN

        Args:
            digits: Number of digits (default 6)

        Returns:
            Numeric PIN string
        """
        # Generate random number with exact digit count
        min_value = 10 ** (digits - 1)
        max_value = 10 ** digits - 1
        return str(secrets.randbelow(max_value - min_value + 1) + min_value)


class AuditLogger:
    """
    Cryptographic audit logging for 21 CFR Part 11 compliance
    Records all encryption/decryption operations with timestamps
    """

    def __init__(self):
        self.logs: list[Dict[str, Any]] = []

    def log_encryption(
        self,
        algorithm: CryptoAlgorithm,
        data_type: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log encryption operation

        Args:
            algorithm: Cryptographic algorithm used
            data_type: Type of data encrypted
            user_id: Optional user identifier
            metadata: Optional additional metadata
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'operation': 'ENCRYPT',
            'algorithm': algorithm.value,
            'data_type': data_type,
            'user_id': user_id,
            'metadata': metadata or {}
        }
        self.logs.append(log_entry)

    def log_decryption(
        self,
        algorithm: CryptoAlgorithm,
        data_type: str,
        success: bool,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log decryption operation

        Args:
            algorithm: Cryptographic algorithm used
            data_type: Type of data decrypted
            success: Whether decryption succeeded
            user_id: Optional user identifier
            metadata: Optional additional metadata
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'operation': 'DECRYPT',
            'algorithm': algorithm.value,
            'data_type': data_type,
            'success': success,
            'user_id': user_id,
            'metadata': metadata or {}
        }
        self.logs.append(log_entry)

    def log_key_operation(
        self,
        operation: str,
        algorithm: CryptoAlgorithm,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log key management operation (generation, rotation, etc.)

        Args:
            operation: Type of key operation
            algorithm: Cryptographic algorithm
            user_id: Optional user identifier
            metadata: Optional additional metadata
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'operation': f'KEY_{operation.upper()}',
            'algorithm': algorithm.value,
            'user_id': user_id,
            'metadata': metadata or {}
        }
        self.logs.append(log_entry)

    def get_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        operation: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """
        Retrieve audit logs with optional filtering

        Args:
            start_time: Optional start timestamp filter
            end_time: Optional end timestamp filter
            operation: Optional operation type filter

        Returns:
            Filtered list of audit log entries
        """
        filtered_logs = self.logs

        if start_time:
            filtered_logs = [
                log for log in filtered_logs
                if datetime.fromisoformat(log['timestamp']) >= start_time
            ]

        if end_time:
            filtered_logs = [
                log for log in filtered_logs
                if datetime.fromisoformat(log['timestamp']) <= end_time
            ]

        if operation:
            filtered_logs = [
                log for log in filtered_logs
                if log['operation'] == operation
            ]

        return filtered_logs

    def clear_logs(self) -> None:
        """Clear all audit logs (use with caution in production)"""
        self.logs.clear()


# Singleton audit logger instance
_audit_logger = AuditLogger()


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance"""
    return _audit_logger
