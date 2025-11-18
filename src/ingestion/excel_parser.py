"""
Excel Parser for PV Test Data (Session 06)

Parses Excel test data files including I-V curves, temperature coefficients,
and various PV module test parameters according to IEC 61215, 61730, and related standards.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from pydantic import BaseModel, Field, validator


class IVCurveData(BaseModel):
    """I-V Curve data structure following IEC 60904-1."""

    voltage: List[float] = Field(..., description="Voltage points in V")
    current: List[float] = Field(..., description="Current points in A")
    power: Optional[List[float]] = Field(None, description="Power points in W")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    irradiance: float = Field(..., description="Irradiance in W/m²", ge=0)
    temperature: float = Field(..., description="Cell temperature in °C")
    voc: float = Field(..., description="Open circuit voltage in V")
    isc: float = Field(..., description="Short circuit current in A")
    vmp: float = Field(..., description="Voltage at maximum power in V")
    imp: float = Field(..., description="Current at maximum power in A")
    pmax: float = Field(..., description="Maximum power in W")
    fill_factor: float = Field(..., description="Fill factor", ge=0, le=1)
    test_standard: str = Field(default="IEC 60904-1", description="Test standard")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("power", always=True)
    def calculate_power(cls, v, values):
        """Calculate power if not provided."""
        if v is None and "voltage" in values and "current" in values:
            return [
                vi * ci for vi, ci in zip(values["voltage"], values["current"])
            ]
        return v

    @validator("voltage", "current")
    def validate_arrays(cls, v):
        """Ensure voltage and current arrays are valid."""
        if len(v) == 0:
            raise ValueError("Array cannot be empty")
        if any(x < 0 for x in v):
            raise ValueError("Values cannot be negative")
        return v

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class TemperatureCoefficient(BaseModel):
    """Temperature coefficient data following IEC 61215-1."""

    alpha_isc: float = Field(..., description="Temperature coefficient of Isc in %/°C")
    beta_voc: float = Field(..., description="Temperature coefficient of Voc in %/°C")
    gamma_pmax: float = Field(..., description="Temperature coefficient of Pmax in %/°C")
    temperature_range: tuple[float, float] = Field(
        ..., description="Temperature range (min, max) in °C"
    )
    reference_temperature: float = Field(default=25.0, description="Reference temperature in °C")
    test_standard: str = Field(default="IEC 61215-1", description="Test standard")
    measurement_uncertainty: Optional[Dict[str, float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("temperature_range")
    def validate_temp_range(cls, v):
        """Validate temperature range."""
        if v[0] >= v[1]:
            raise ValueError("Minimum temperature must be less than maximum")
        return v


class FlashTestData(BaseModel):
    """Flash test data structure."""

    module_id: str
    test_date: datetime
    irradiance: float = Field(default=1000.0, description="Irradiance in W/m²")
    temperature: float = Field(default=25.0, description="Temperature in °C")
    pmax: float
    voc: float
    isc: float
    vmp: float
    imp: float
    fill_factor: float
    efficiency: Optional[float] = None
    area: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExcelParserConfig(BaseModel):
    """Configuration for Excel parser."""

    skip_rows: int = Field(default=0, description="Number of rows to skip")
    header_row: int = Field(default=0, description="Header row index")
    data_start_row: int = Field(default=1, description="Data start row")
    sheet_name: Optional[str] = None
    column_mapping: Dict[str, str] = Field(
        default_factory=dict, description="Custom column name mapping"
    )
    date_format: str = Field(default="%Y-%m-%d %H:%M:%S")
    decimal_separator: str = Field(default=".")
    thousands_separator: Optional[str] = None
    encoding: str = Field(default="utf-8")


class ExcelParser:
    """
    Production-ready Excel parser for PV test data.

    Supports:
    - I-V curve data extraction
    - Temperature coefficient parsing
    - Flash test results
    - Multiple sheet formats
    - Data cleaning and normalization
    - Progress tracking
    - Async batch processing
    """

    def __init__(self, config: Optional[ExcelParserConfig] = None):
        """Initialize Excel parser."""
        self.config = config or ExcelParserConfig()
        self._progress_callback = None

    def set_progress_callback(self, callback):
        """Set callback for progress tracking."""
        self._progress_callback = callback

    def _report_progress(self, current: int, total: int, message: str = ""):
        """Report progress if callback is set."""
        if self._progress_callback:
            self._progress_callback(current, total, message)

    def parse_file(
        self, file_path: Union[str, Path], sheet_name: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Parse Excel file and return cleaned DataFrame.

        Args:
            file_path: Path to Excel file
            sheet_name: Specific sheet to parse (None for all sheets)

        Returns:
            Cleaned pandas DataFrame

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            # Determine sheet name
            sheet = sheet_name or self.config.sheet_name

            # Read Excel file
            df = pd.read_excel(
                file_path,
                sheet_name=sheet,
                skiprows=self.config.skip_rows,
                header=self.config.header_row,
            )

            # Clean and normalize
            df = self._clean_dataframe(df)

            return df

        except Exception as e:
            raise ValueError(f"Failed to parse Excel file: {e}") from e

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize DataFrame."""
        # Remove completely empty rows and columns
        df = df.dropna(how="all").dropna(axis=1, how="all")

        # Strip whitespace from column names
        df.columns = df.columns.str.strip()

        # Apply column mapping if provided
        if self.config.column_mapping:
            df = df.rename(columns=self.config.column_mapping)

        # Replace empty strings with NaN
        df = df.replace(r"^\s*$", np.nan, regex=True)

        # Handle decimal and thousands separators
        if self.config.decimal_separator != ".":
            for col in df.select_dtypes(include=["object"]).columns:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace(self.config.decimal_separator, ".")
                )

        return df

    def extract_iv_curve(
        self,
        file_path: Union[str, Path],
        sheet_name: str = "IV_Curve",
        voltage_col: str = "Voltage",
        current_col: str = "Current",
        metadata_cols: Optional[List[str]] = None,
    ) -> IVCurveData:
        """
        Extract I-V curve data from Excel file.

        Args:
            file_path: Path to Excel file
            sheet_name: Sheet containing I-V data
            voltage_col: Column name for voltage
            current_col: Column name for current
            metadata_cols: Additional metadata columns to extract

        Returns:
            IVCurveData object
        """
        df = self.parse_file(file_path, sheet_name)

        # Extract voltage and current arrays
        voltage = df[voltage_col].dropna().tolist()
        current = df[current_col].dropna().tolist()

        # Ensure equal length
        min_len = min(len(voltage), len(current))
        voltage = voltage[:min_len]
        current = current[:min_len]

        # Calculate key parameters
        power = [v * i for v, i in zip(voltage, current)]
        pmax = max(power)
        pmax_idx = power.index(pmax)

        voc = voltage[0] if voltage else 0.0
        isc = current[-1] if current else 0.0
        vmp = voltage[pmax_idx]
        imp = current[pmax_idx]
        fill_factor = pmax / (voc * isc) if (voc * isc > 0) else 0.0

        # Extract metadata
        metadata = {}
        if metadata_cols:
            for col in metadata_cols:
                if col in df.columns:
                    metadata[col] = df[col].iloc[0]

        # Default values for required fields
        irradiance = metadata.get("irradiance", 1000.0)
        temperature = metadata.get("temperature", 25.0)

        return IVCurveData(
            voltage=voltage,
            current=current,
            power=power,
            voc=voc,
            isc=isc,
            vmp=vmp,
            imp=imp,
            pmax=pmax,
            fill_factor=fill_factor,
            irradiance=irradiance,
            temperature=temperature,
            metadata=metadata,
        )

    def extract_temperature_coefficients(
        self,
        file_path: Union[str, Path],
        sheet_name: str = "Temp_Coefficients",
    ) -> TemperatureCoefficient:
        """
        Extract temperature coefficient data.

        Args:
            file_path: Path to Excel file
            sheet_name: Sheet containing temperature coefficient data

        Returns:
            TemperatureCoefficient object
        """
        df = self.parse_file(file_path, sheet_name)

        # Try to find coefficient values (flexible parsing)
        alpha_isc = self._find_value(df, ["alpha_isc", "Alpha Isc", "Temp Coeff Isc"])
        beta_voc = self._find_value(df, ["beta_voc", "Beta Voc", "Temp Coeff Voc"])
        gamma_pmax = self._find_value(
            df, ["gamma_pmax", "Gamma Pmax", "Temp Coeff Pmax"]
        )

        # Extract temperature range
        temp_min = self._find_value(df, ["temp_min", "Min Temperature", "T_min"], default=15.0)
        temp_max = self._find_value(df, ["temp_max", "Max Temperature", "T_max"], default=75.0)

        return TemperatureCoefficient(
            alpha_isc=alpha_isc,
            beta_voc=beta_voc,
            gamma_pmax=gamma_pmax,
            temperature_range=(temp_min, temp_max),
        )

    def _find_value(
        self, df: pd.DataFrame, possible_names: List[str], default: Any = None
    ) -> Any:
        """Find value from DataFrame using multiple possible column names."""
        for name in possible_names:
            # Check columns
            if name in df.columns:
                value = df[name].iloc[0]
                if pd.notna(value):
                    return float(value)

            # Check index (for transposed data)
            if name in df.index:
                value = df.loc[name].iloc[0]
                if pd.notna(value):
                    return float(value)

        if default is not None:
            return default

        raise ValueError(f"Could not find value for any of: {possible_names}")

    def extract_flash_test_data(
        self,
        file_path: Union[str, Path],
        sheet_name: str = "Flash_Test",
    ) -> List[FlashTestData]:
        """
        Extract flash test data for multiple modules.

        Args:
            file_path: Path to Excel file
            sheet_name: Sheet containing flash test data

        Returns:
            List of FlashTestData objects
        """
        df = self.parse_file(file_path, sheet_name)

        results = []
        total_rows = len(df)

        for idx, row in df.iterrows():
            self._report_progress(idx + 1, total_rows, f"Processing row {idx + 1}")

            try:
                flash_data = FlashTestData(
                    module_id=str(row.get("module_id", f"MODULE_{idx}")),
                    test_date=pd.to_datetime(row.get("test_date", datetime.utcnow())),
                    pmax=float(row["pmax"]),
                    voc=float(row["voc"]),
                    isc=float(row["isc"]),
                    vmp=float(row["vmp"]),
                    imp=float(row["imp"]),
                    fill_factor=float(row["fill_factor"]),
                    irradiance=float(row.get("irradiance", 1000.0)),
                    temperature=float(row.get("temperature", 25.0)),
                    efficiency=float(row["efficiency"]) if "efficiency" in row else None,
                    area=float(row["area"]) if "area" in row else None,
                )
                results.append(flash_data)
            except (KeyError, ValueError) as e:
                # Log error but continue processing
                print(f"Warning: Skipping row {idx} due to error: {e}")
                continue

        return results

    def parse_multi_sheet(
        self, file_path: Union[str, Path]
    ) -> Dict[str, pd.DataFrame]:
        """
        Parse all sheets in an Excel file.

        Args:
            file_path: Path to Excel file

        Returns:
            Dictionary mapping sheet names to DataFrames
        """
        file_path = Path(file_path)
        workbook = load_workbook(file_path, data_only=True)

        results = {}
        total_sheets = len(workbook.sheetnames)

        for idx, sheet_name in enumerate(workbook.sheetnames):
            self._report_progress(
                idx + 1, total_sheets, f"Processing sheet: {sheet_name}"
            )

            df = self.parse_file(file_path, sheet_name)
            results[sheet_name] = df

        return results

    async def parse_batch_async(
        self, file_paths: List[Union[str, Path]]
    ) -> List[Dict[str, pd.DataFrame]]:
        """
        Asynchronously parse multiple Excel files.

        Args:
            file_paths: List of file paths to parse

        Returns:
            List of dictionaries mapping sheet names to DataFrames
        """
        tasks = []
        for file_path in file_paths:
            task = asyncio.to_thread(self.parse_multi_sheet, file_path)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log them
        valid_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error parsing {file_paths[idx]}: {result}")
            else:
                valid_results.append(result)

        return valid_results

    def validate_iv_curve(self, iv_data: IVCurveData) -> Dict[str, Any]:
        """
        Validate I-V curve data against IEC 60904-1 requirements.

        Returns:
            Dictionary with validation results and warnings
        """
        warnings = []
        errors = []

        # Check voltage monotonicity
        if not all(
            iv_data.voltage[i] >= iv_data.voltage[i + 1]
            for i in range(len(iv_data.voltage) - 1)
        ):
            warnings.append("Voltage is not monotonically decreasing")

        # Check current monotonicity
        if not all(
            iv_data.current[i] <= iv_data.current[i + 1]
            for i in range(len(iv_data.current) - 1)
        ):
            warnings.append("Current is not monotonically increasing")

        # Check fill factor range
        if iv_data.fill_factor < 0.5 or iv_data.fill_factor > 0.9:
            warnings.append(
                f"Fill factor {iv_data.fill_factor:.3f} is outside typical range (0.5-0.9)"
            )

        # Check irradiance
        if abs(iv_data.irradiance - 1000.0) > 50:
            warnings.append(
                f"Irradiance {iv_data.irradiance} W/m² deviates from STC (1000 W/m²)"
            )

        # Check temperature
        if abs(iv_data.temperature - 25.0) > 5:
            warnings.append(
                f"Temperature {iv_data.temperature}°C deviates from STC (25°C)"
            )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }
