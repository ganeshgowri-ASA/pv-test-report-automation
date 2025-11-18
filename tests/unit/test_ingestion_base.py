"""
Unit tests for base ingestion module.
"""

from pathlib import Path

import pytest

from src.core.exceptions import FileSizeExceededError, UnsupportedFileFormatError
from src.ingestion.base import FileBasedIngestionModule


class MockFileIngestionModule(FileBasedIngestionModule):
    """Mock implementation for testing base class."""

    @property
    def supported_extensions(self):
        return ['.txt', '.csv']

    def _validate_configuration(self):
        pass

    def extract_metadata(self, source):
        return {"test": "metadata"}

    def ingest(self, source, **kwargs):
        return {"test": "result"}


class TestBaseIngestionModule:
    """Tests for BaseIngestionModule."""

    def test_check_file_extension_valid(self, temp_test_dir):
        """Test file extension validation with valid extension."""
        module = MockFileIngestionModule()
        file_path = temp_test_dir / "test.txt"
        file_path.touch()

        # Should not raise
        module.check_file_extension(file_path, ['.txt', '.csv'])

    def test_check_file_extension_invalid(self, temp_test_dir):
        """Test file extension validation with invalid extension."""
        module = MockFileIngestionModule()
        file_path = temp_test_dir / "test.pdf"
        file_path.touch()

        with pytest.raises(UnsupportedFileFormatError):
            module.check_file_extension(file_path, ['.txt', '.csv'])

    def test_check_file_size_valid(self, temp_test_dir):
        """Test file size validation with valid size."""
        module = MockFileIngestionModule()
        file_path = temp_test_dir / "test.txt"
        file_path.write_text("Small file content")

        # Should not raise
        module.check_file_size(file_path)

    def test_validate_file(self, temp_test_dir):
        """Test file validation."""
        module = MockFileIngestionModule()
        file_path = temp_test_dir / "test.txt"
        file_path.write_text("Test content")

        assert module.validate_file(file_path) is True

    def test_validate_file_wrong_extension(self, temp_test_dir):
        """Test file validation with wrong extension."""
        module = MockFileIngestionModule()
        file_path = temp_test_dir / "test.pdf"
        file_path.touch()

        with pytest.raises(UnsupportedFileFormatError):
            module.validate_file(file_path)

    def test_get_temp_dir(self):
        """Test getting temporary directory."""
        module = MockFileIngestionModule()
        temp_dir = module.get_temp_dir()
        assert temp_dir.exists()
        assert temp_dir.is_dir()

    def test_get_output_dir(self):
        """Test getting output directory."""
        module = MockFileIngestionModule()
        output_dir = module.get_output_dir()
        assert output_dir.exists()
        assert output_dir.is_dir()
