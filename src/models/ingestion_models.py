"""Pydantic models for data ingestion with ISO 17025 compliance."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from pydantic import BaseModel, Field, field_validator, ConfigDict


class DelimiterType(str, Enum):
    """Supported CSV delimiters."""

    COMMA = ","
    SEMICOLON = ";"
    TAB = "\t"
    PIPE = "|"
    SPACE = " "


class EncodingType(str, Enum):
    """Supported file encodings."""

    UTF8 = "utf-8"
    UTF16 = "utf-16"
    LATIN1 = "latin-1"
    ASCII = "ascii"
    ISO8859_1 = "iso-8859-1"
    CP1252 = "cp1252"


class DataFormat(str, Enum):
    """Supported data formats."""

    CSV = "csv"
    JSON = "json"
    JSONL = "jsonl"
    EXCEL = "excel"


class EquipmentType(str, Enum):
    """PV test equipment types."""

    IV_TRACER = "iv_tracer"
    THERMAL_CHAMBER = "thermal_chamber"
    SPECTRORADIOMETER = "spectroradiometer"
    MULTIMETER = "multimeter"
    PYRANOMETER = "pyranometer"
    CLIMATIC_CHAMBER = "climatic_chamber"
    FLASH_SIMULATOR = "flash_simulator"


class ISO17025Metadata(BaseModel):
    """ISO 17025 compliance metadata."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    lab_name: str = Field(..., description="Accredited laboratory name")
    lab_accreditation_number: str = Field(..., description="ISO 17025 accreditation number")
    test_method: str = Field(..., description="Standard test method (e.g., IEC 61215)")
    test_date: datetime = Field(..., description="Test execution date")
    operator_id: str = Field(..., description="Operator/technician identifier")
    equipment_id: str = Field(..., description="Equipment calibration ID")
    calibration_due_date: Optional[datetime] = Field(
        None, description="Next calibration due date"
    )
    environmental_conditions: Optional[Dict[str, float]] = Field(
        None, description="Temperature, humidity, etc."
    )
    uncertainty_budget: Optional[Dict[str, float]] = Field(
        None, description="Measurement uncertainties"
    )
    traceability_chain: Optional[List[str]] = Field(
        None, description="Calibration traceability to national standards"
    )


class CSVIngestionResult(BaseModel):
    """Result from CSV file ingestion."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    dataframe: pd.DataFrame = Field(..., description="Parsed data as pandas DataFrame")
    row_count: int = Field(..., description="Number of data rows")
    column_count: int = Field(..., description="Number of columns")
    delimiter_detected: str = Field(..., description="Auto-detected delimiter")
    encoding_detected: str = Field(..., description="Auto-detected encoding")
    file_hash: str = Field(..., description="SHA-256 hash for data integrity")
    parse_timestamp: datetime = Field(
        default_factory=datetime.now, description="When parsing completed"
    )
    has_header: bool = Field(True, description="Whether file has header row")
    data_types: Dict[str, str] = Field(
        default_factory=dict, description="Detected data types per column"
    )
    missing_values: Dict[str, int] = Field(
        default_factory=dict, description="Missing value counts per column"
    )
    iso17025_metadata: Optional[ISO17025Metadata] = Field(
        None, description="ISO 17025 compliance metadata"
    )

    @field_validator("row_count")
    @classmethod
    def validate_row_count(cls, v: int) -> int:
        """Ensure row count is non-negative."""
        if v < 0:
            raise ValueError("Row count must be non-negative")
        return v


class JSONIngestionResult(BaseModel):
    """Result from JSON/JSONL file ingestion."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    data: Union[Dict[str, Any], List[Dict[str, Any]]] = Field(
        ..., description="Parsed JSON data"
    )
    dataframe: Optional[pd.DataFrame] = Field(None, description="Data as DataFrame if tabular")
    record_count: int = Field(..., description="Number of records")
    file_hash: str = Field(..., description="SHA-256 hash for data integrity")
    encoding_detected: str = Field(..., description="Auto-detected encoding")
    parse_timestamp: datetime = Field(
        default_factory=datetime.now, description="When parsing completed"
    )
    is_jsonl: bool = Field(False, description="Whether file is JSON Lines format")
    schema_valid: bool = Field(True, description="Whether data matches expected schema")
    validation_errors: Optional[List[str]] = Field(None, description="Schema validation errors")
    iso17025_metadata: Optional[ISO17025Metadata] = Field(
        None, description="ISO 17025 compliance metadata"
    )


class IVCurveData(BaseModel):
    """I-V (Current-Voltage) curve measurement data."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    voltage: List[float] = Field(..., description="Voltage points (V)")
    current: List[float] = Field(..., description="Current points (A)")
    power: Optional[List[float]] = Field(None, description="Power points (W)")
    timestamp: datetime = Field(..., description="Measurement timestamp")
    irradiance: float = Field(..., description="Irradiance level (W/m²)", ge=0)
    temperature: float = Field(..., description="Module temperature (°C)")
    voc: float = Field(..., description="Open circuit voltage (V)", ge=0)
    isc: float = Field(..., description="Short circuit current (A)", ge=0)
    vmp: float = Field(..., description="Maximum power voltage (V)", ge=0)
    imp: float = Field(..., description="Maximum power current (A)", ge=0)
    pmax: float = Field(..., description="Maximum power (W)", ge=0)
    fill_factor: float = Field(..., description="Fill factor", ge=0, le=1)
    module_id: str = Field(..., description="Module under test identifier")
    test_standard: str = Field(default="IEC 60904-1", description="Test standard")
    equipment_type: EquipmentType = Field(
        default=EquipmentType.IV_TRACER, description="Equipment used"
    )
    iso17025_metadata: Optional[ISO17025Metadata] = None

    @field_validator("voltage", "current")
    @classmethod
    def validate_array_length(cls, v: List[float]) -> List[float]:
        """Ensure arrays have sufficient data points."""
        if len(v) < 10:
            raise ValueError("I-V curve must have at least 10 data points")
        return v

    def calculate_power(self) -> List[float]:
        """Calculate power from voltage and current."""
        return [v * i for v, i in zip(self.voltage, self.current)]


class ChamberLogData(BaseModel):
    """Thermal/climatic chamber time-series log data."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    timestamps: List[datetime] = Field(..., description="Time series timestamps")
    temperature: List[float] = Field(..., description="Temperature readings (°C)")
    humidity: Optional[List[float]] = Field(None, description="Relative humidity (%)")
    pressure: Optional[List[float]] = Field(None, description="Atmospheric pressure (Pa)")
    setpoint_temperature: float = Field(..., description="Target temperature (°C)")
    setpoint_humidity: Optional[float] = Field(None, description="Target humidity (%)")
    chamber_id: str = Field(..., description="Chamber equipment identifier")
    test_id: str = Field(..., description="Test sequence identifier")
    start_time: datetime = Field(..., description="Test start time")
    end_time: datetime = Field(..., description="Test end time")
    duration_seconds: float = Field(..., description="Total test duration", gt=0)
    test_standard: str = Field(default="IEC 61215", description="Test standard")
    equipment_type: EquipmentType = Field(
        default=EquipmentType.THERMAL_CHAMBER, description="Equipment type"
    )
    iso17025_metadata: Optional[ISO17025Metadata] = None

    @field_validator("timestamps", "temperature")
    @classmethod
    def validate_time_series(cls, v: List) -> List:
        """Ensure time series have sufficient data."""
        if len(v) < 2:
            raise ValueError("Time series must have at least 2 data points")
        return v


class BatchTestResult(BaseModel):
    """Batch test results for multiple modules."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    batch_id: str = Field(..., description="Batch identifier")
    test_date: datetime = Field(..., description="Test execution date")
    module_ids: List[str] = Field(..., description="List of module identifiers")
    test_results: pd.DataFrame = Field(..., description="Test results as DataFrame")
    pass_count: int = Field(..., description="Number of modules passed", ge=0)
    fail_count: int = Field(..., description="Number of modules failed", ge=0)
    total_count: int = Field(..., description="Total modules tested", ge=0)
    test_standard: str = Field(..., description="Test standard applied")
    test_parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Test conditions and parameters"
    )
    summary_statistics: Dict[str, float] = Field(
        default_factory=dict, description="Statistical summary of results"
    )
    iso17025_metadata: Optional[ISO17025Metadata] = None

    @field_validator("total_count")
    @classmethod
    def validate_counts(cls, v: int, info) -> int:
        """Ensure counts are consistent."""
        if "pass_count" in info.data and "fail_count" in info.data:
            expected = info.data["pass_count"] + info.data["fail_count"]
            if v != expected:
                raise ValueError(
                    f"Total count ({v}) must equal pass + fail ({expected})"
                )
        return v


class EquipmentData(BaseModel):
    """Generic equipment export data."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    equipment_type: EquipmentType = Field(..., description="Type of equipment")
    equipment_id: str = Field(..., description="Equipment identifier")
    manufacturer: str = Field(..., description="Equipment manufacturer")
    model: str = Field(..., description="Equipment model")
    serial_number: str = Field(..., description="Equipment serial number")
    calibration_date: datetime = Field(..., description="Last calibration date")
    calibration_due_date: datetime = Field(..., description="Next calibration due")
    measurement_data: pd.DataFrame = Field(..., description="Measurement data")
    measurement_units: Dict[str, str] = Field(
        ..., description="Units for each measurement parameter"
    )
    measurement_timestamp: datetime = Field(..., description="When measurements taken")
    test_standard: str = Field(..., description="Applicable test standard")
    raw_data_format: str = Field(..., description="Original data format")
    iso17025_metadata: Optional[ISO17025Metadata] = None

    @field_validator("calibration_due_date")
    @classmethod
    def validate_calibration(cls, v: datetime, info) -> datetime:
        """Ensure calibration is not overdue."""
        if "calibration_date" in info.data and v < info.data["calibration_date"]:
            raise ValueError("Calibration due date must be after calibration date")
        return v
