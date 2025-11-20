"""Unit tests for API Key Vault.

Session 55: Unit Test Suite
"""
import pytest
from src.api_key_vault import EncryptionService, VaultManager


class TestEncryptionService:
    """Test encryption service."""
    
    def test_generate_key(self):
        """Test key generation."""
        key = EncryptionService.generate_key()
        assert len(key) > 0
    
    def test_encrypt_decrypt(self):
        """Test encryption and decryption."""
        encryption = EncryptionService()
        plaintext = "secret_api_key"
        encrypted = encryption.encrypt(plaintext)
        decrypted = encryption.decrypt(encrypted)
        assert decrypted == plaintext
    
    def test_encrypt_dict(self):
        """Test dictionary encryption."""
        encryption = EncryptionService()
        data = {"api_key": "test123", "secret": "password"}
        encrypted_data = encryption.encrypt_dict(data)
        decrypted_data = encryption.decrypt_dict(encrypted_data)
        assert decrypted_data == data


class TestVaultManager:
    """Test vault manager."""
    
    def test_local_backend(self):
        """Test local encrypted backend."""
        vault = VaultManager(backend_type="local")
        vault.set_secret("test/secret", {"key": "value"})
        secret = vault.get_secret("test/secret")
        assert secret["key"] == "value"
