"""Integration tests for vault."""
import pytest


class TestVaultIntegration:
    """Test vault integration."""
    
    @pytest.mark.integration
    def test_api_key_storage_retrieval(self):
        """Test storing and retrieving API keys."""
        from src.api_key_vault import VaultManager
        
        vault = VaultManager(backend_type="local")
        vault.set_api_key("test_service", "test_key_123")
        retrieved = vault.get_api_key("test_service")
        assert retrieved == "test_key_123"
