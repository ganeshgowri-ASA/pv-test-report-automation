"""
Pydantic Schema Validators

Provides comprehensive Pydantic models for structured validation of PV test data,
module specifications, environmental conditions, and measurements.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ConfigDict,
)
import numpy as np


class TechnologyType(str, Enum):
    """PV module technology types."""
    MONO_SI = "mono-Si"
    POLY_SI = "poly-Si"
    CDTE = "CdTe"
    CIGS = "CIGS"
    PERC = "PERC"
    PERT = "PERT"
    HIT = "HIT"
    TOPCON = "TOPCon"
    BIFACIAL = "Bifacial"
    TANDEM = "Tandem"
    OTHER = "Other"


class TestType(str, Enum):
    """Types of PV module tests."""
    IV_CURVE = "IV_Curve"
    FLASH_TEST = "Flash_Test"
    STC_PERFORMANCE = "STC_Performance"
    PID_TEST = "PID_Test"
    DEGRADATION = "Degradation"
    THERMAL_CYCLING = "Thermal_Cycling"
    HUMIDITY_FREEZE = "Humidity_Freeze"
    UV_EXPOSURE = "UV_Exposure"
    MECHANICAL_LOAD = "Mechanical_Load"
    HOTSPOT = "Hotspot"
    OTHER = "Other"


class MeasurementUnit(str, Enum):
    """Standard measurement units."""
    VOLTAGE_V = "V"
    CURRENT_A = "A"
    POWER_W = "W"
    IRRADIANCE_WM2 = "W/m²"
    TEMPERATURE_C = "°C"
    TEMPERATURE_K = "K"
    PERCENTAGE = "%"
    HOURS = "hours"
    METERS_PER_SECOND = "m/s"


class ValidationSeverityEnum(str, Enum):
    """Severity levels for validation results."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorDetailSchema(BaseModel):
    """Schema for individual validation error details."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    severity: ValidationSeverityEnum = Field(
        ...,
        description="Severity level of the validation issue"
    )
    message: str = Field(
        ...,
        description="Human-readable error message"
    )
    field: Optional[str] = Field(
        None,
        description="Field name where the error occurred"
    )
    value: Optional[Any] = Field(
        None,
        description="The value that caused the validation error"
    )
    expected: Optional[str] = Field(
        None,
        description="Expected value or format description"
    )
    standard: Optional[str] = Field(
        None,
        description="Reference to IEC/ISO standard violated"
    )
    location: Optional[str] = Field(
        None,
        description="Location in data structure (e.g., row number)"
    )

    def __str__(self) -> str:
        """String representation of error."""
        parts = [f"[{self.severity.value.upper()}]"]
        if self.field:
            parts.append(f"{self.field}:")
        parts.append(self.message)
        if self.expected:
            parts.append(f"(Expected: {self.expected})")
        return " ".join(parts)


class ValidationResultSchema(BaseModel):
    """Schema for validation results."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    is_valid: bool = Field(
        ...,
        description="Overall validation status"
    )
    errors: List[ErrorDetailSchema] = Field(
        default_factory=list,
        description="List of validation errors"
    )
    warnings: List[ErrorDetailSchema] = Field(
        default_factory=list,
        description="List of validation warnings"
    )
    info: List[ErrorDetailSchema] = Field(
        default_factory=list,
        description="Informational messages"
    )
    validated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp of validation"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional validation metadata"
    )

    @property
    def error_count(self) -> int:
        """Total number of errors."""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """Total number of warnings."""
        return len(self.warnings)

    def get_summary(self) -> str:
        """Get validation summary."""
        status = "PASSED" if self.is_valid else "FAILED"
        return f"Validation {status}: {self.error_count} errors, {self.warning_count} warnings"

    def add_error(
        self,
        message: str,
        field: Optional[str] = None,
        severity: ValidationSeverityEnum = ValidationSeverityEnum.ERROR,
        **kwargs
    ) -> None:
        """Add an error to the result."""
        error = ErrorDetailSchema(
            severity=severity,
            message=message,
            field=field,
            **kwargs
        )

        if severity == ValidationSeverityEnum.ERROR or severity == ValidationSeverityEnum.CRITICAL:
            self.errors.append(error)
            self.is_valid = False
        elif severity == ValidationSeverityEnum.WARNING:
            self.warnings.append(error)
        else:
            self.info.append(error)


class ModuleSpecSchema(BaseModel):
    """Schema for PV module specifications."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    manufacturer: str = Field(
        ...,
        min_length=1,
        description="Module manufacturer name"
    )
    model: str = Field(
        ...,
        min_length=1,
        description="Module model number"
    )
    serial_number: Optional[str] = Field(
        None,
        description="Module serial number"
    )
    technology: TechnologyType = Field(
        ...,
        description="PV technology type"
    )

    # Electrical characteristics at STC
    p_max: float = Field(
        ...,
        gt=0,
        le=1000,
        description="Maximum power at STC (W)"
    )
    v_oc: float = Field(
        ...,
        gt=0,
        le=100,
        description="Open circuit voltage at STC (V)"
    )
    i_sc: float = Field(
        ...,
        gt=0,
        le=50,
        description="Short circuit current at STC (A)"
    )
    v_mp: float = Field(
        ...,
        gt=0,
        le=100,
        description="Voltage at maximum power point (V)"
    )
    i_mp: float = Field(
        ...,
        gt=0,
        le=50,
        description="Current at maximum power point (A)"
    )
    efficiency: float = Field(
        ...,
        gt=0,
        le=30,
        description="Module efficiency (%)"
    )

    # Physical characteristics
    length: Optional[float] = Field(
        None,
        gt=0,
        description="Module length (mm)"
    )
    width: Optional[float] = Field(
        None,
        gt=0,
        description="Module width (mm)"
    )
    area: Optional[float] = Field(
        None,
        gt=0,
        description="Module area (m²)"
    )
    weight: Optional[float] = Field(
        None,
        gt=0,
        description="Module weight (kg)"
    )
    cells_in_series: Optional[int] = Field(
        None,
        gt=0,
        description="Number of cells in series"
    )

    # Temperature coefficients
    temp_coeff_pmax: Optional[float] = Field(
        None,
        description="Temperature coefficient of Pmax (%/°C)"
    )
    temp_coeff_voc: Optional[float] = Field(
        None,
        description="Temperature coefficient of Voc (%/°C)"
    )
    temp_coeff_isc: Optional[float] = Field(
        None,
        description="Temperature coefficient of Isc (%/°C)"
    )

    # Additional metadata
    manufacturing_date: Optional[datetime] = Field(
        None,
        description="Module manufacturing date"
    )
    certification: Optional[List[str]] = Field(
        default_factory=list,
        description="Certifications (e.g., IEC 61215, IEC 61730)"
    )
    notes: Optional[str] = Field(
        None,
        description="Additional notes"
    )

    @field_validator("p_max")
    @classmethod
    def validate_power(cls, v: float, info) -> float:
        """Validate maximum power is positive."""
        if v <= 0:
            raise ValueError("Maximum power must be positive")
        return v

    @model_validator(mode='after')
    def validate_electrical_consistency(self):
        """Validate electrical parameter consistency."""
        # Check Pmax ≈ Vmp * Imp
        calculated_p = self.v_mp * self.i_mp
        tolerance = 0.05  # 5% tolerance

        if abs(calculated_p - self.p_max) / self.p_max > tolerance:
            raise ValueError(
                f"Inconsistent power parameters: Vmp*Imp={calculated_p:.2f}W, "
                f"Pmax={self.p_max:.2f}W (difference > {tolerance*100}%)"
            )

        # Check Vmp < Voc
        if self.v_mp >= self.v_oc:
            raise ValueError(f"Vmp ({self.v_mp}V) must be less than Voc ({self.v_oc}V)")

        # Check Imp < Isc
        if self.i_mp >= self.i_sc:
            raise ValueError(f"Imp ({self.i_mp}A) must be less than Isc ({self.i_sc}A)")

        return self


class EnvironmentalConditionsSchema(BaseModel):
    """Schema for environmental test conditions."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    irradiance: float = Field(
        ...,
        ge=0,
        le=1500,
        description="Irradiance (W/m²)"
    )
    module_temperature: float = Field(
        ...,
        ge=-40,
        le=85,
        description="Module temperature (°C)"
    )
    ambient_temperature: Optional[float] = Field(
        None,
        ge=-40,
        le=60,
        description="Ambient temperature (°C)"
    )
    wind_speed: Optional[float] = Field(
        None,
        ge=0,
        le=25,
        description="Wind speed (m/s)"
    )
    relative_humidity: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Relative humidity (%)"
    )
    air_mass: Optional[float] = Field(
        1.5,
        ge=1.0,
        le=10.0,
        description="Air mass coefficient"
    )
    angle_of_incidence: Optional[float] = Field(
        0,
        ge=0,
        le=90,
        description="Angle of incidence (degrees)"
    )
    spectral_mismatch: Optional[float] = Field(
        None,
        ge=0.9,
        le=1.1,
        description="Spectral mismatch factor"
    )

    @field_validator("irradiance")
    @classmethod
    def validate_irradiance(cls, v: float) -> float:
        """Validate irradiance is non-negative."""
        if v < 0:
            raise ValueError("Irradiance must be non-negative")
        return v

    @model_validator(mode='after')
    def validate_temperature_relationship(self):
        """Validate module temperature is typically higher than ambient."""
        if self.ambient_temperature is not None:
            if self.module_temperature < self.ambient_temperature - 5:
                raise ValueError(
                    f"Module temperature ({self.module_temperature}°C) is "
                    f"significantly lower than ambient ({self.ambient_temperature}°C). "
                    "This is unusual under normal test conditions."
                )
        return self

    def is_stc(self, tolerance: Dict[str, float] = None) -> bool:
        """
        Check if conditions match Standard Test Conditions (STC).

        Args:
            tolerance: Dictionary of tolerances for each parameter

        Returns:
            True if conditions are within STC tolerances
        """
        if tolerance is None:
            tolerance = {
                "irradiance": 50,  # ±50 W/m²
                "module_temperature": 2,  # ±2 °C
            }

        is_irr_stc = abs(self.irradiance - 1000) <= tolerance["irradiance"]
        is_temp_stc = abs(self.module_temperature - 25) <= tolerance["module_temperature"]

        return is_irr_stc and is_temp_stc


class MeasurementSchema(BaseModel):
    """Schema for individual measurement points."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Measurement timestamp"
    )
    voltage: float = Field(
        ...,
        description="Measured voltage (V)"
    )
    current: float = Field(
        ...,
        description="Measured current (A)"
    )
    power: Optional[float] = Field(
        None,
        description="Measured or calculated power (W)"
    )
    irradiance: Optional[float] = Field(
        None,
        ge=0,
        description="Irradiance during measurement (W/m²)"
    )
    temperature: Optional[float] = Field(
        None,
        description="Temperature during measurement (°C)"
    )
    measurement_uncertainty: Optional[Dict[str, float]] = Field(
        None,
        description="Measurement uncertainties for each parameter"
    )
    quality_flag: Optional[str] = Field(
        None,
        description="Quality flag (e.g., 'good', 'suspect', 'bad')"
    )

    @model_validator(mode='after')
    def calculate_power(self):
        """Calculate power if not provided."""
        if self.power is None:
            self.power = self.voltage * self.current
        else:
            # Validate provided power matches V*I
            calculated = self.voltage * self.current
            tolerance = 0.01  # 1%
            if abs(self.power - calculated) / (calculated + 1e-10) > tolerance:
                raise ValueError(
                    f"Power inconsistent with V*I: P={self.power}W, "
                    f"V*I={calculated:.2f}W"
                )
        return self

    @field_validator("quality_flag")
    @classmethod
    def validate_quality_flag(cls, v: Optional[str]) -> Optional[str]:
        """Validate quality flag values."""
        if v is not None:
            valid_flags = ["good", "suspect", "bad", "outlier"]
            if v.lower() not in valid_flags:
                raise ValueError(
                    f"Invalid quality flag '{v}'. Must be one of: {', '.join(valid_flags)}"
                )
        return v


class TestDataSchema(BaseModel):
    """Schema for complete test data."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    test_id: str = Field(
        ...,
        min_length=1,
        description="Unique test identifier"
    )
    test_type: TestType = Field(
        ...,
        description="Type of test performed"
    )
    test_date: datetime = Field(
        ...,
        description="Date and time of test"
    )
    test_facility: str = Field(
        ...,
        min_length=1,
        description="Testing facility name"
    )
    operator: str = Field(
        ...,
        min_length=1,
        description="Operator name or ID"
    )
    equipment_id: str = Field(
        ...,
        min_length=1,
        description="Test equipment identifier"
    )

    # Module and conditions
    module_spec: ModuleSpecSchema = Field(
        ...,
        description="Module specifications"
    )
    conditions: EnvironmentalConditionsSchema = Field(
        ...,
        description="Environmental test conditions"
    )

    # Measurements
    measurements: List[MeasurementSchema] = Field(
        ...,
        min_length=1,
        description="List of measurement points"
    )

    # Standards compliance
    standard_reference: List[str] = Field(
        default_factory=list,
        description="Applicable IEC/ISO standards"
    )
    calibration_date: Optional[datetime] = Field(
        None,
        description="Last equipment calibration date"
    )
    calibration_certificate: Optional[str] = Field(
        None,
        description="Calibration certificate number"
    )

    # Results summary
    peak_power: Optional[float] = Field(
        None,
        description="Peak power from measurements (W)"
    )
    fill_factor: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Fill factor"
    )
    efficiency: Optional[float] = Field(
        None,
        ge=0,
        le=30,
        description="Measured efficiency (%)"
    )

    # Quality and compliance
    quality_assurance_passed: bool = Field(
        default=False,
        description="QA check status"
    )
    iso17025_compliant: bool = Field(
        default=False,
        description="ISO 17025 compliance status"
    )
    nabl_compliant: bool = Field(
        default=False,
        description="NABL compliance status"
    )

    # Additional metadata
    notes: Optional[str] = Field(
        None,
        description="Additional test notes"
    )
    attachments: Optional[List[str]] = Field(
        default_factory=list,
        description="Paths to attachment files"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    @field_validator("test_date", "calibration_date")
    @classmethod
    def validate_date_not_future(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Validate dates are not in the future."""
        if v is not None and v > datetime.now():
            raise ValueError("Date cannot be in the future")
        return v

    @model_validator(mode='after')
    def validate_calibration(self):
        """Validate equipment calibration is current."""
        if self.calibration_date is not None:
            # Check calibration is not more than 1 year old
            days_since_cal = (self.test_date - self.calibration_date).days
            if days_since_cal > 365:
                raise ValueError(
                    f"Equipment calibration expired ({days_since_cal} days old). "
                    "Maximum allowed: 365 days"
                )
            elif days_since_cal < 0:
                raise ValueError("Calibration date cannot be after test date")

        return self

    @model_validator(mode='after')
    def calculate_derived_parameters(self):
        """Calculate fill factor and other derived parameters."""
        if len(self.measurements) > 0:
            # Find peak power
            powers = [m.power for m in self.measurements if m.power is not None]
            if powers:
                self.peak_power = max(powers)

                # Calculate fill factor
                if hasattr(self.module_spec, 'v_oc') and hasattr(self.module_spec, 'i_sc'):
                    theoretical_max = self.module_spec.v_oc * self.module_spec.i_sc
                    if theoretical_max > 0:
                        self.fill_factor = self.peak_power / theoretical_max

        return self

    def get_stc_measurements(self) -> List[MeasurementSchema]:
        """
        Get measurements taken at or near STC conditions.

        Returns:
            List of measurements at STC
        """
        if not self.conditions.is_stc():
            return []

        # Return all measurements if test conditions are STC
        return self.measurements

    def validate_data_quality(self) -> ValidationResultSchema:
        """
        Perform comprehensive data quality validation.

        Returns:
            ValidationResultSchema with detailed results
        """
        result = ValidationResultSchema(is_valid=True)

        # Check measurement count
        if len(self.measurements) < 10:
            result.add_error(
                "Insufficient measurements for reliable analysis",
                field="measurements",
                severity=ValidationSeverityEnum.WARNING,
                expected="At least 10 measurement points recommended"
            )

        # Check for outliers in measurements
        if len(self.measurements) > 2:
            powers = np.array([m.power for m in self.measurements if m.power is not None])
            if len(powers) > 0:
                mean_power = np.mean(powers)
                std_power = np.std(powers)
                outliers = np.abs(powers - mean_power) > 3 * std_power

                if np.any(outliers):
                    result.add_error(
                        f"Found {np.sum(outliers)} potential outlier(s) in power measurements",
                        field="measurements",
                        severity=ValidationSeverityEnum.WARNING
                    )

        # Check standard references
        required_standards = ["IEC 60904", "IEC 61215"]
        missing_standards = [s for s in required_standards if s not in self.standard_reference]
        if missing_standards:
            result.add_error(
                f"Missing standard references: {', '.join(missing_standards)}",
                field="standard_reference",
                severity=ValidationSeverityEnum.WARNING
            )

        return result
