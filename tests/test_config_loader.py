"""
Unit tests for configuration loader

Run with: python -m pytest tests/test_config_loader.py
"""

import pytest
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.config_loader import (
    ConfigLoader,
    ConfigurationError,
    ValidationError,
    StandardConfig,
    LLMProviderConfig
)


class TestConfigLoader:
    """Test suite for ConfigLoader"""

    @pytest.fixture
    def loader(self):
        """Create a ConfigLoader instance"""
        return ConfigLoader()

    def test_initialization(self, loader):
        """Test that ConfigLoader initializes correctly"""
        assert loader.base_dir.exists()
        assert loader.standards_dir.exists()
        assert loader.templates_dir.exists()
        assert loader.llm_config_file.exists()

    def test_list_available_standards(self, loader):
        """Test listing available standards"""
        standards = loader.list_available_standards()
        assert isinstance(standards, list)
        assert len(standards) > 0

        # Check for expected standards
        expected_standards = [
            'iec_61215', 'iec_61730', 'iec_61853',
            'iso_17025', 'nabl_ilac_bis'
        ]
        for std in expected_standards:
            assert std in standards, f"Standard {std} not found"

    def test_load_standard_iec_61215(self, loader):
        """Test loading IEC 61215 standard"""
        config = loader.load_standard('iec_61215')

        assert isinstance(config, StandardConfig)
        assert config.code == "IEC 61215"
        assert config.full_name != ""
        assert config.version != ""
        assert len(config.applicable_to) > 0
        assert config.scope != ""
        assert config.data is not None

    def test_load_standard_caching(self, loader):
        """Test that standards are cached"""
        # Load once
        config1 = loader.load_standard('iec_61215')

        # Load again
        config2 = loader.load_standard('iec_61215', use_cache=True)

        # Should be the same object
        assert config1 is config2

    def test_load_nonexistent_standard(self, loader):
        """Test loading a non-existent standard"""
        with pytest.raises(ConfigurationError):
            loader.load_standard('nonexistent_standard')

    def test_load_all_standards(self, loader):
        """Test loading all standards"""
        standards = loader.load_all_standards()

        assert isinstance(standards, dict)
        assert len(standards) > 0

        # Verify all are StandardConfig objects
        for std_code, config in standards.items():
            assert isinstance(config, StandardConfig)
            assert config.code != ""

    def test_get_standard_by_code(self, loader):
        """Test getting standard by code"""
        # Test with different code formats
        config1 = loader.get_standard_by_code("IEC 61215")
        config2 = loader.get_standard_by_code("iec_61215")

        assert config1 is not None
        assert config1.code == "IEC 61215"

    def test_load_llm_config(self, loader):
        """Test loading LLM configuration"""
        config = loader.load_llm_config()

        assert isinstance(config, dict)
        assert 'llm_providers' in config
        assert 'application' in config

        # Check for expected providers
        providers = config['llm_providers']
        assert 'openai' in providers
        assert 'anthropic' in providers

    def test_get_llm_provider_config(self, loader):
        """Test getting specific LLM provider config"""
        provider = loader.get_llm_provider_config('openai')

        assert isinstance(provider, LLMProviderConfig)
        assert provider.name == 'openai'
        assert isinstance(provider.enabled, bool)

    def test_get_primary_llm_provider(self, loader):
        """Test getting primary LLM provider"""
        provider = loader.get_primary_llm_provider()

        assert isinstance(provider, LLMProviderConfig)
        assert provider.name != ""

    def test_list_available_templates(self, loader):
        """Test listing available templates"""
        templates = loader.list_available_templates()

        assert isinstance(templates, list)
        # At least the test_report_template should be there
        assert 'test_report_template' in templates

    def test_load_template(self, loader):
        """Test loading a template"""
        template = loader.load_template('test_report_template')

        assert template is not None
        assert isinstance(template, dict)

    def test_config_summary(self, loader):
        """Test getting configuration summary"""
        summary = loader.get_config_summary()

        assert isinstance(summary, dict)
        assert 'base_directory' in summary
        assert 'available_standards' in summary
        assert 'available_templates' in summary

    def test_clear_cache(self, loader):
        """Test clearing cache"""
        # Load something to populate cache
        loader.load_standard('iec_61215')
        loader.load_llm_config()

        # Verify cache is populated
        assert len(loader._standards_cache) > 0
        assert loader._llm_config_cache is not None

        # Clear cache
        loader.clear_cache()

        # Verify cache is empty
        assert len(loader._standards_cache) == 0
        assert loader._llm_config_cache is None


def test_api_key_validation():
    """Test API key validation"""
    # Set a dummy API key for testing
    os.environ['OPENAI_API_KEY'] = 'test-key'

    loader = ConfigLoader()
    validation = loader.validate_api_keys()

    assert isinstance(validation, dict)
    # OpenAI should be valid since we set the key
    if 'openai' in validation:
        assert validation['openai'] == True

    # Clean up
    del os.environ['OPENAI_API_KEY']


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, '-v'])
