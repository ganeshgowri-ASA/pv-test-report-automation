"""
Unit tests for Excel Parser module.
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np

from ..excel_parser import (
    ExcelParser,
    ExcelParserConfig,
    IVCurveData,
    TemperatureCoefficient,
    FlashTestData,
)


class TestIVCurveData:
    """Test IVCurveData model."""

    def test_valid_iv_curve(self):
        """Test creating valid I-V curve data."""
        iv_data = IVCurveData(
            voltage=[40.0, 35.0, 30.0, 20.0, 0.0],
            current=[0.0, 5.0, 7.0, 8.5, 9.0],
            voc=40.0,
            isc=9.0,
            vmp=30.0,
            imp=7.0,
            pmax=210.0,
            fill_factor=0.583,
            irradiance=1000.0,
            temperature=25.0,
        )

        assert iv_data.voc == 40.0
        assert iv_data.isc == 9.0
        assert len(iv_data.voltage) == 5
        assert len(iv_data.current) == 5
        assert len(iv_data.power) == 5  # Auto-calculated

    def test_power_auto_calculation(self):
        """Test automatic power calculation."""
        iv_data = IVCurveData(
            voltage=[40.0, 30.0],
            current=[0.0, 7.0],
            voc=40.0,
            isc=9.0,
            vmp=30.0,
            imp=7.0,
            pmax=210.0,
            fill_factor=0.583,
            irradiance=1000.0,
            temperature=25.0,
        )

        assert iv_data.power == [0.0, 210.0]

    def test_invalid_negative_values(self):
        """Test validation of negative values."""
        with pytest.raises(ValueError, match="cannot be negative"):
            IVCurveData(
                voltage=[-5.0, 30.0],
                current=[0.0, 7.0],
                voc=40.0,
                isc=9.0,
                vmp=30.0,
                imp=7.0,
                pmax=210.0,
                fill_factor=0.583,
                irradiance=1000.0,
                temperature=25.0,
            )


class TestTemperatureCoefficient:
    """Test TemperatureCoefficient model."""

    def test_valid_coefficients(self):
        """Test creating valid temperature coefficients."""
        temp_coeff = TemperatureCoefficient(
            alpha_isc=0.05,
            beta_voc=-0.32,
            gamma_pmax=-0.43,
            temperature_range=(15.0, 75.0),
        )

        assert temp_coeff.alpha_isc == 0.05
        assert temp_coeff.beta_voc == -0.32
        assert temp_coeff.gamma_pmax == -0.43

    def test_invalid_temperature_range(self):
        """Test validation of temperature range."""
        with pytest.raises(ValueError, match="less than maximum"):
            TemperatureCoefficient(
                alpha_isc=0.05,
                beta_voc=-0.32,
                gamma_pmax=-0.43,
                temperature_range=(75.0, 15.0),  # Invalid: min > max
            )


class TestExcelParser:
    """Test ExcelParser class."""

    def test_initialization(self):
        """Test parser initialization."""
        parser = ExcelParser()
        assert parser.config is not None
        assert isinstance(parser.config, ExcelParserConfig)

    def test_custom_config(self):
        """Test parser with custom config."""
        config = ExcelParserConfig(skip_rows=2, header_row=1)
        parser = ExcelParser(config)
        assert parser.config.skip_rows == 2
        assert parser.config.header_row == 1

    def test_progress_callback(self):
        """Test progress callback."""
        parser = ExcelParser()
        callback = Mock()
        parser.set_progress_callback(callback)

        parser._report_progress(5, 10, "Processing")
        callback.assert_called_once_with(5, 10, "Processing")

    @patch("pandas.read_excel")
    def test_parse_file(self, mock_read_excel):
        """Test parsing Excel file."""
        # Create mock DataFrame
        mock_df = pd.DataFrame(
            {
                "Voltage": [40.0, 30.0, 20.0],
                "Current": [0.0, 7.0, 9.0],
            }
        )
        mock_read_excel.return_value = mock_df

        parser = ExcelParser()

        # Create a temporary file
        with patch.object(Path, "exists", return_value=True):
            result = parser.parse_file("test.xlsx")

        assert isinstance(result, pd.DataFrame)
        assert "Voltage" in result.columns
        assert "Current" in result.columns

    def test_clean_dataframe(self):
        """Test DataFrame cleaning."""
        parser = ExcelParser()

        # Create DataFrame with issues
        df = pd.DataFrame(
            {
                " Voltage ": [40.0, None, 20.0],
                "Current": [0.0, 7.0, "  "],
            }
        )

        cleaned = parser._clean_dataframe(df)

        # Check whitespace removed from columns
        assert "Voltage" in cleaned.columns
        assert " Voltage " not in cleaned.columns

    @patch("pandas.read_excel")
    def test_extract_iv_curve(self, mock_read_excel):
        """Test I-V curve extraction."""
        mock_df = pd.DataFrame(
            {
                "Voltage": [40.0, 35.0, 30.0, 20.0, 0.0],
                "Current": [0.0, 5.0, 7.0, 8.5, 9.0],
            }
        )
        mock_read_excel.return_value = mock_df

        parser = ExcelParser()

        with patch.object(Path, "exists", return_value=True):
            iv_data = parser.extract_iv_curve("test.xlsx")

        assert isinstance(iv_data, IVCurveData)
        assert iv_data.voc > 0
        assert iv_data.isc > 0
        assert iv_data.pmax > 0

    def test_validate_iv_curve(self):
        """Test I-V curve validation."""
        parser = ExcelParser()

        iv_data = IVCurveData(
            voltage=[40.0, 35.0, 30.0, 20.0, 0.0],  # Monotonic decreasing
            current=[0.0, 5.0, 7.0, 8.5, 9.0],  # Monotonic increasing
            voc=40.0,
            isc=9.0,
            vmp=30.0,
            imp=7.0,
            pmax=210.0,
            fill_factor=0.75,  # Valid range
            irradiance=1000.0,
            temperature=25.0,
        )

        result = parser.validate_iv_curve(iv_data)

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_iv_curve_warnings(self):
        """Test I-V curve validation with warnings."""
        parser = ExcelParser()

        iv_data = IVCurveData(
            voltage=[40.0, 35.0, 30.0, 20.0, 0.0],
            current=[0.0, 5.0, 7.0, 8.5, 9.0],
            voc=40.0,
            isc=9.0,
            vmp=30.0,
            imp=7.0,
            pmax=210.0,
            fill_factor=0.75,
            irradiance=800.0,  # Deviation from STC
            temperature=35.0,  # Deviation from STC
        )

        result = parser.validate_iv_curve(iv_data)

        assert len(result["warnings"]) > 0


class TestFlashTestData:
    """Test FlashTestData model."""

    def test_valid_flash_data(self):
        """Test creating valid flash test data."""
        flash_data = FlashTestData(
            module_id="MOD-001",
            test_date=datetime(2025, 1, 15),
            pmax=250.0,
            voc=38.5,
            isc=8.9,
            vmp=31.2,
            imp=8.0,
            fill_factor=0.74,
        )

        assert flash_data.module_id == "MOD-001"
        assert flash_data.pmax == 250.0
        assert flash_data.irradiance == 1000.0  # Default value


@pytest.fixture
def sample_excel_file(tmp_path):
    """Create a sample Excel file for testing."""
    file_path = tmp_path / "test_data.xlsx"

    df = pd.DataFrame(
        {
            "Voltage": [40.0, 35.0, 30.0, 20.0, 0.0],
            "Current": [0.0, 5.0, 7.0, 8.5, 9.0],
        }
    )

    df.to_excel(file_path, index=False)
    return file_path


def test_integration_parse_real_file(sample_excel_file):
    """Integration test with real Excel file."""
    parser = ExcelParser()
    df = parser.parse_file(sample_excel_file)

    assert len(df) == 5
    assert "Voltage" in df.columns
    assert "Current" in df.columns
