"""Time-series data handler for I-V curves and chamber logs."""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd

from ..models.ingestion_models import (
    IVCurveData,
    ChamberLogData,
    EquipmentType,
    ISO17025Metadata,
)
from .csv_parser import CSVParser
from .json_parser import JSONParser


class TimeSeriesHandler:
    """Handler for time-series PV test data."""

    def __init__(self):
        """Initialize time-series handler."""
        self.csv_parser = CSVParser()
        self.json_parser = JSONParser()

    def parse_iv_curve_csv(
        self,
        file_path: Union[str, Path],
        module_id: str,
        irradiance: float,
        temperature: float,
        voltage_col: str = "Voltage",
        current_col: str = "Current",
        test_standard: str = "IEC 60904-1",
        iso17025_metadata: Optional[ISO17025Metadata] = None,
    ) -> IVCurveData:
        """Parse I-V curve data from CSV file.

        Args:
            file_path: Path to CSV file
            module_id: Module identifier
            irradiance: Irradiance level (W/m²)
            temperature: Module temperature (°C)
            voltage_col: Column name for voltage data
            current_col: Column name for current data
            test_standard: Test standard applied
            iso17025_metadata: Optional ISO 17025 metadata

        Returns:
            IVCurveData object
        """
        # Parse CSV
        result = self.csv_parser.parse(file_path)
        df = result.dataframe

        # Extract voltage and current columns
        if voltage_col not in df.columns or current_col not in df.columns:
            raise ValueError(
                f"Required columns not found. Available: {list(df.columns)}"
            )

        voltage = df[voltage_col].tolist()
        current = df[current_col].tolist()

        # Calculate power
        power = [v * i for v, i in zip(voltage, current)]

        # Find key parameters
        voc = max(voltage)  # Open circuit voltage
        isc = max(current)  # Short circuit current

        # Find maximum power point
        max_power_idx = np.argmax(power)
        pmax = power[max_power_idx]
        vmp = voltage[max_power_idx]
        imp = current[max_power_idx]

        # Calculate fill factor
        fill_factor = pmax / (voc * isc) if (voc * isc) > 0 else 0.0

        return IVCurveData(
            voltage=voltage,
            current=current,
            power=power,
            timestamp=datetime.now(),
            irradiance=irradiance,
            temperature=temperature,
            voc=voc,
            isc=isc,
            vmp=vmp,
            imp=imp,
            pmax=pmax,
            fill_factor=fill_factor,
            module_id=module_id,
            test_standard=test_standard,
            equipment_type=EquipmentType.IV_TRACER,
            iso17025_metadata=iso17025_metadata,
        )

    def parse_iv_curve_json(
        self,
        file_path: Union[str, Path],
        iso17025_metadata: Optional[ISO17025Metadata] = None,
    ) -> IVCurveData:
        """Parse I-V curve data from JSON file.

        Args:
            file_path: Path to JSON file
            iso17025_metadata: Optional ISO 17025 metadata

        Returns:
            IVCurveData object
        """
        # Parse JSON
        result = self.json_parser.parse(file_path)
        data = result.data

        if not isinstance(data, dict):
            raise ValueError("JSON must contain a single object")

        # Extract data
        voltage = data.get("voltage", [])
        current = data.get("current", [])
        power = data.get("power")

        # Calculate power if not provided
        if power is None:
            power = [v * i for v, i in zip(voltage, current)]

        # Parse timestamp
        timestamp_str = data.get("timestamp")
        timestamp = (
            datetime.fromisoformat(timestamp_str)
            if timestamp_str
            else datetime.now()
        )

        return IVCurveData(
            voltage=voltage,
            current=current,
            power=power,
            timestamp=timestamp,
            irradiance=data.get("irradiance", 1000.0),
            temperature=data.get("temperature", 25.0),
            voc=data.get("voc", max(voltage)),
            isc=data.get("isc", max(current)),
            vmp=data.get("vmp", voltage[np.argmax(power)]),
            imp=data.get("imp", current[np.argmax(power)]),
            pmax=data.get("pmax", max(power)),
            fill_factor=data.get("fill_factor", 0.75),
            module_id=data.get("module_id", "unknown"),
            test_standard=data.get("test_standard", "IEC 60904-1"),
            equipment_type=EquipmentType(
                data.get("equipment_type", EquipmentType.IV_TRACER.value)
            ),
            iso17025_metadata=iso17025_metadata,
        )

    def parse_chamber_log_csv(
        self,
        file_path: Union[str, Path],
        chamber_id: str,
        test_id: str,
        setpoint_temperature: float,
        timestamp_col: str = "Timestamp",
        temperature_col: str = "Temperature",
        humidity_col: Optional[str] = "Humidity",
        pressure_col: Optional[str] = None,
        setpoint_humidity: Optional[float] = None,
        test_standard: str = "IEC 61215",
        iso17025_metadata: Optional[ISO17025Metadata] = None,
    ) -> ChamberLogData:
        """Parse chamber log data from CSV file.

        Args:
            file_path: Path to CSV file
            chamber_id: Chamber identifier
            test_id: Test sequence identifier
            setpoint_temperature: Target temperature
            timestamp_col: Column name for timestamps
            temperature_col: Column name for temperature
            humidity_col: Optional column name for humidity
            pressure_col: Optional column name for pressure
            setpoint_humidity: Optional target humidity
            test_standard: Test standard
            iso17025_metadata: Optional ISO 17025 metadata

        Returns:
            ChamberLogData object
        """
        # Parse CSV
        result = self.csv_parser.parse(file_path)
        df = result.dataframe

        # Extract timestamp column
        if timestamp_col not in df.columns:
            raise ValueError(f"Timestamp column '{timestamp_col}' not found")

        timestamps = pd.to_datetime(df[timestamp_col]).tolist()

        # Extract temperature
        if temperature_col not in df.columns:
            raise ValueError(f"Temperature column '{temperature_col}' not found")

        temperature = df[temperature_col].tolist()

        # Extract optional humidity
        humidity = None
        if humidity_col and humidity_col in df.columns:
            humidity = df[humidity_col].tolist()

        # Extract optional pressure
        pressure = None
        if pressure_col and pressure_col in df.columns:
            pressure = df[pressure_col].tolist()

        # Calculate duration
        start_time = min(timestamps)
        end_time = max(timestamps)
        duration_seconds = (end_time - start_time).total_seconds()

        return ChamberLogData(
            timestamps=timestamps,
            temperature=temperature,
            humidity=humidity,
            pressure=pressure,
            setpoint_temperature=setpoint_temperature,
            setpoint_humidity=setpoint_humidity,
            chamber_id=chamber_id,
            test_id=test_id,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration_seconds,
            test_standard=test_standard,
            equipment_type=EquipmentType.THERMAL_CHAMBER,
            iso17025_metadata=iso17025_metadata,
        )

    def parse_chamber_log_json(
        self,
        file_path: Union[str, Path],
        iso17025_metadata: Optional[ISO17025Metadata] = None,
    ) -> ChamberLogData:
        """Parse chamber log data from JSON file.

        Args:
            file_path: Path to JSON file
            iso17025_metadata: Optional ISO 17025 metadata

        Returns:
            ChamberLogData object
        """
        # Parse JSON
        result = self.json_parser.parse(file_path)
        data = result.data

        if not isinstance(data, dict):
            raise ValueError("JSON must contain a single object")

        # Parse timestamps
        timestamps = [
            datetime.fromisoformat(ts) for ts in data.get("timestamps", [])
        ]

        # Extract data
        temperature = data.get("temperature", [])
        humidity = data.get("humidity")
        pressure = data.get("pressure")

        # Parse dates
        start_time = datetime.fromisoformat(data.get("start_time", datetime.now().isoformat()))
        end_time = datetime.fromisoformat(data.get("end_time", datetime.now().isoformat()))

        return ChamberLogData(
            timestamps=timestamps,
            temperature=temperature,
            humidity=humidity,
            pressure=pressure,
            setpoint_temperature=data.get("setpoint_temperature", 25.0),
            setpoint_humidity=data.get("setpoint_humidity"),
            chamber_id=data.get("chamber_id", "unknown"),
            test_id=data.get("test_id", "unknown"),
            start_time=start_time,
            end_time=end_time,
            duration_seconds=data.get("duration_seconds", 0.0),
            test_standard=data.get("test_standard", "IEC 61215"),
            equipment_type=EquipmentType(
                data.get("equipment_type", EquipmentType.THERMAL_CHAMBER.value)
            ),
            iso17025_metadata=iso17025_metadata,
        )

    def interpolate_iv_curve(
        self, iv_data: IVCurveData, num_points: int = 100
    ) -> IVCurveData:
        """Interpolate I-V curve to uniform voltage points.

        Args:
            iv_data: Original I-V curve data
            num_points: Number of interpolated points

        Returns:
            New IVCurveData with interpolated values
        """
        # Create uniform voltage points
        v_uniform = np.linspace(0, iv_data.voc, num_points)

        # Interpolate current
        i_interp = np.interp(v_uniform, iv_data.voltage, iv_data.current)

        # Calculate power
        p_interp = v_uniform * i_interp

        return IVCurveData(
            voltage=v_uniform.tolist(),
            current=i_interp.tolist(),
            power=p_interp.tolist(),
            timestamp=iv_data.timestamp,
            irradiance=iv_data.irradiance,
            temperature=iv_data.temperature,
            voc=iv_data.voc,
            isc=iv_data.isc,
            vmp=iv_data.vmp,
            imp=iv_data.imp,
            pmax=iv_data.pmax,
            fill_factor=iv_data.fill_factor,
            module_id=iv_data.module_id,
            test_standard=iv_data.test_standard,
            equipment_type=iv_data.equipment_type,
            iso17025_metadata=iv_data.iso17025_metadata,
        )

    def resample_chamber_log(
        self, log_data: ChamberLogData, frequency: str = "1T"
    ) -> ChamberLogData:
        """Resample chamber log data to uniform time intervals.

        Args:
            log_data: Original chamber log data
            frequency: Resampling frequency (pandas offset string, e.g., '1T' = 1 minute)

        Returns:
            New ChamberLogData with resampled values
        """
        # Create DataFrame
        df = pd.DataFrame(
            {
                "timestamp": log_data.timestamps,
                "temperature": log_data.temperature,
            }
        )

        if log_data.humidity:
            df["humidity"] = log_data.humidity

        if log_data.pressure:
            df["pressure"] = log_data.pressure

        # Set timestamp as index
        df.set_index("timestamp", inplace=True)

        # Resample
        df_resampled = df.resample(frequency).mean().interpolate()

        # Extract resampled data
        timestamps = df_resampled.index.tolist()
        temperature = df_resampled["temperature"].tolist()
        humidity = df_resampled["humidity"].tolist() if "humidity" in df_resampled else None
        pressure = df_resampled["pressure"].tolist() if "pressure" in df_resampled else None

        return ChamberLogData(
            timestamps=timestamps,
            temperature=temperature,
            humidity=humidity,
            pressure=pressure,
            setpoint_temperature=log_data.setpoint_temperature,
            setpoint_humidity=log_data.setpoint_humidity,
            chamber_id=log_data.chamber_id,
            test_id=log_data.test_id,
            start_time=log_data.start_time,
            end_time=log_data.end_time,
            duration_seconds=log_data.duration_seconds,
            test_standard=log_data.test_standard,
            equipment_type=log_data.equipment_type,
            iso17025_metadata=log_data.iso17025_metadata,
        )
