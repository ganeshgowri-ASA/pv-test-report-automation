"""Tests for time-series data handler."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.ingestion.timeseries_handler import TimeSeriesHandler


class TestTimeSeriesHandler:
    """Test time-series handler functionality."""

    def test_parse_iv_curve_csv(self):
        """Test parsing I-V curve from CSV."""
        handler = TimeSeriesHandler()

        csv_content = "Voltage,Current\n0.0,8.5\n10.0,8.4\n20.0,8.2\n30.0,7.8\n35.0,5.0\n37.0,2.0\n38.0,0.0\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            iv_data = handler.parse_iv_curve_csv(
                temp_path,
                module_id="TEST-001",
                irradiance=1000.0,
                temperature=25.0,
            )

            assert iv_data.module_id == "TEST-001"
            assert iv_data.irradiance == 1000.0
            assert iv_data.temperature == 25.0
            assert len(iv_data.voltage) == 7
            assert len(iv_data.current) == 7
            assert iv_data.voc > 0
            assert iv_data.isc > 0
            assert iv_data.pmax > 0
            assert 0 <= iv_data.fill_factor <= 1
        finally:
            Path(temp_path).unlink()

    def test_parse_chamber_log_csv(self):
        """Test parsing chamber log from CSV."""
        handler = TimeSeriesHandler()

        csv_content = """Timestamp,Temperature,Humidity
2024-01-01 10:00:00,25.0,50.0
2024-01-01 10:01:00,25.2,50.5
2024-01-01 10:02:00,25.5,51.0
2024-01-01 10:03:00,25.8,51.5
2024-01-01 10:04:00,26.0,52.0
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            log_data = handler.parse_chamber_log_csv(
                temp_path,
                chamber_id="CHAMBER-01",
                test_id="TEST-001",
                setpoint_temperature=25.0,
                setpoint_humidity=50.0,
            )

            assert log_data.chamber_id == "CHAMBER-01"
            assert log_data.test_id == "TEST-001"
            assert log_data.setpoint_temperature == 25.0
            assert len(log_data.timestamps) == 5
            assert len(log_data.temperature) == 5
            assert log_data.humidity is not None
            assert len(log_data.humidity) == 5
            assert log_data.duration_seconds > 0
        finally:
            Path(temp_path).unlink()

    def test_interpolate_iv_curve(self):
        """Test I-V curve interpolation."""
        handler = TimeSeriesHandler()

        csv_content = "Voltage,Current\n" + "\n".join(
            [f"{v},{10-v/5}" for v in range(0, 51, 5)]
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            iv_data = handler.parse_iv_curve_csv(
                temp_path,
                module_id="TEST-001",
                irradiance=1000.0,
                temperature=25.0,
            )

            # Interpolate to 50 points
            iv_interp = handler.interpolate_iv_curve(iv_data, num_points=50)

            assert len(iv_interp.voltage) == 50
            assert len(iv_interp.current) == 50
            assert iv_interp.voc == iv_data.voc
            assert iv_interp.isc == iv_data.isc
        finally:
            Path(temp_path).unlink()
