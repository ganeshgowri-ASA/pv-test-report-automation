"""
Schema Validator

Comprehensive schema validation for PV test data using Pydantic models
and custom validation rules per IEC standards.
"""

from typing import Optional, List, Dict, Any, Type, Union
from pathlib import Path
import json
import pandas as pd
from pydantic import BaseModel, Field, field_validator, ValidationError as PydanticValidationError
from datetime import datetime

from .models import ValidationError as ValidationErrorModel
from .exceptions import SchemaError, ValidationError


# IEC 61215 Module Test Data Schema
class IEC61215ModuleData(BaseModel):
    """IEC 61215 module test data schema."""
    serial_number: str = Field(..., min_length=1)
    voc: float = Field(..., gt=0, description="Open circuit voltage (V)")
    isc: float = Field(..., gt=0, description="Short circuit current (A)")
    pmax: float = Field(..., gt=0, description="Maximum power (W)")
    vmax: float = Field(..., gt=0, description="Voltage at max power (V)")
    imax: float = Field(..., gt=0, description="Current at max power (A)")
    fill_factor: float = Field(..., ge=0, le=1, description="Fill factor")
    efficiency: float = Field(..., ge=0, le=100, description="Efficiency (%)")
    test_date: datetime
    test_temperature: float = Field(..., ge=-40, le=85, description="Test temperature (°C)")
    irradiance: float = Field(default=1000.0, ge=0, description="Irradiance (W/m²)")

    @field_validator('fill_factor')
    @classmethod
    def validate_fill_factor(cls, v, info):
        """Validate fill factor is physically reasonable."""
        if v < 0.5 or v > 0.9:
            raise ValueError(f"Fill factor {v} outside typical range [0.5, 0.9]")
        return v


# I-V Curve Data Point Schema
class IVCurvePoint(BaseModel):
    """Single I-V curve measurement point."""
    timestamp: datetime
    voltage: float = Field(..., ge=0, description="Voltage (V)")
    current: float = Field(..., ge=0, description="Current (A)")
    power: float = Field(..., ge=0, description="Power (W)")
    temperature: Optional[float] = Field(None, description="Module temperature (°C)")

    @field_validator('power')
    @classmethod
    def validate_power(cls, v, info):
        """Validate power = voltage * current."""
        data = info.data
        if 'voltage' in data and 'current' in data:
            expected_power = data['voltage'] * data['current']
            # Allow 1% tolerance
            if abs(v - expected_power) / max(expected_power, 0.01) > 0.01:
                raise ValueError(
                    f"Power {v}W inconsistent with V={data['voltage']}V * I={data['current']}A"
                )
        return v


# Environmental Chamber Log Schema
class ChamberLogEntry(BaseModel):
    """Environmental chamber log entry."""
    timestamp: datetime
    temperature: float = Field(..., ge=-70, le=200, description="Temperature (°C)")
    humidity: float = Field(..., ge=0, le=100, description="Relative humidity (%)")
    pressure: Optional[float] = Field(None, ge=0, description="Pressure (kPa)")
    setpoint_temperature: Optional[float] = Field(None, description="Temperature setpoint (°C)")
    setpoint_humidity: Optional[float] = Field(None, description="Humidity setpoint (%)")


# Flash Test Result Schema
class FlashTestResult(BaseModel):
    """Flash test result for a single module."""
    serial_number: str = Field(..., min_length=1)
    test_date: datetime
    pmax: float = Field(..., gt=0, description="Maximum power at STC (W)")
    voc: float = Field(..., gt=0, description="Open circuit voltage (V)")
    isc: float = Field(..., gt=0, description="Short circuit current (A)")
    vmax: float = Field(..., gt=0, description="Voltage at Pmax (V)")
    imax: float = Field(..., gt=0, description="Current at Pmax (A)")
    fill_factor: float = Field(..., ge=0, le=1)
    efficiency: float = Field(..., ge=0, le=100, description="Efficiency (%)")
    grade: Optional[str] = Field(None, pattern=r'^[A-D]$', description="Module grade")


# Irradiance Sensor Data Schema
class IrradianceData(BaseModel):
    """Irradiance sensor measurement."""
    timestamp: datetime
    ghi: Optional[float] = Field(None, ge=0, le=1500, description="Global Horizontal Irradiance (W/m²)")
    dhi: Optional[float] = Field(None, ge=0, le=1500, description="Diffuse Horizontal Irradiance (W/m²)")
    dni: Optional[float] = Field(None, ge=0, le=1500, description="Direct Normal Irradiance (W/m²)")
    module_temperature: Optional[float] = Field(None, description="Module temperature (°C)")
    ambient_temperature: Optional[float] = Field(None, description="Ambient temperature (°C)")


class SchemaValidator:
    """
    Schema validator for PV test data.

    Features:
    - Pydantic model validation
    - Custom validation rules per IEC standard
    - Schema versioning support
    - Auto-generate schema from sample data
    - Batch validation for multiple records

    Example:
        >>> validator = SchemaValidator(IEC61215ModuleData)
        >>> errors = validator.validate_dataframe(df)
        >>> if not errors:
        ...     print("All data valid!")
    """

    # Registry of predefined schemas
    SCHEMAS = {
        'iec61215_module': IEC61215ModuleData,
        'iv_curve': IVCurvePoint,
        'chamber_log': ChamberLogEntry,
        'flash_test': FlashTestResult,
        'irradiance': IrradianceData,
    }

    def __init__(
        self,
        schema: Union[str, Type[BaseModel]],
        strict: bool = True,
    ):
        """
        Initialize schema validator.

        Args:
            schema: Schema name (from SCHEMAS) or Pydantic model class
            strict: Raise exception on first error if True
        """
        if isinstance(schema, str):
            if schema not in self.SCHEMAS:
                raise SchemaError(f"Unknown schema: {schema}. Available: {list(self.SCHEMAS.keys())}")
            self.schema_model = self.SCHEMAS[schema]
            self.schema_name = schema
        else:
            self.schema_model = schema
            self.schema_name = schema.__name__

        self.strict = strict

    def validate_dict(self, data: Dict[str, Any]) -> tuple[bool, List[ValidationErrorModel]]:
        """
        Validate a single dictionary against schema.

        Args:
            data: Data dictionary to validate

        Returns:
            Tuple of (is_valid, errors)
        """
        try:
            self.schema_model(**data)
            return True, []
        except PydanticValidationError as e:
            errors = []
            for error in e.errors():
                errors.append(ValidationErrorModel(
                    field='.'.join(str(loc) for loc in error['loc']),
                    error_type=error['type'],
                    message=error['msg'],
                    value=error.get('input'),
                ))
            return False, errors

    def validate_dataframe(
        self,
        df: pd.DataFrame,
        max_errors: int = 100,
    ) -> List[ValidationErrorModel]:
        """
        Validate DataFrame against schema.

        Args:
            df: DataFrame to validate
            max_errors: Maximum errors to collect

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        for idx, row in df.iterrows():
            row_dict = row.to_dict()

            is_valid, row_errors = self.validate_dict(row_dict)

            if not is_valid:
                for error in row_errors:
                    error.row = int(idx) if isinstance(idx, int) else None
                    errors.append(error)

                if len(errors) >= max_errors:
                    break

                if self.strict:
                    raise ValidationError(
                        f"Row {idx} validation failed: {row_errors[0].message}"
                    )

        return errors

    def validate_list(
        self,
        data_list: List[Dict[str, Any]],
        max_errors: int = 100,
    ) -> List[ValidationErrorModel]:
        """
        Validate list of dictionaries against schema.

        Args:
            data_list: List of data dictionaries
            max_errors: Maximum errors to collect

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        for idx, item in enumerate(data_list):
            is_valid, item_errors = self.validate_dict(item)

            if not is_valid:
                for error in item_errors:
                    error.row = idx
                    errors.append(error)

                if len(errors) >= max_errors:
                    break

                if self.strict:
                    raise ValidationError(
                        f"Item {idx} validation failed: {item_errors[0].message}"
                    )

        return errors

    @classmethod
    def get_schema_definition(cls, schema_name: str) -> Dict[str, Any]:
        """
        Get JSON Schema definition for a schema.

        Args:
            schema_name: Name of schema

        Returns:
            JSON Schema dictionary
        """
        if schema_name not in cls.SCHEMAS:
            raise SchemaError(f"Unknown schema: {schema_name}")

        model = cls.SCHEMAS[schema_name]
        return model.model_json_schema()

    @classmethod
    def save_schema_definition(
        cls,
        schema_name: str,
        output_path: Union[str, Path],
    ) -> None:
        """
        Save JSON Schema definition to file.

        Args:
            schema_name: Name of schema
            output_path: Output file path
        """
        schema_def = cls.get_schema_definition(schema_name)

        output_path = Path(output_path)
        with open(output_path, 'w') as f:
            json.dump(schema_def, f, indent=2)

    @classmethod
    def generate_schema_from_dataframe(
        cls,
        df: pd.DataFrame,
        schema_name: str = "AutoGeneratedSchema",
    ) -> Dict[str, Any]:
        """
        Auto-generate JSON Schema from DataFrame sample.

        Args:
            df: Sample DataFrame
            schema_name: Name for generated schema

        Returns:
            JSON Schema dictionary
        """
        properties = {}
        required = []

        for col in df.columns:
            dtype = df[col].dtype

            # Map pandas dtype to JSON Schema type
            if pd.api.types.is_integer_dtype(dtype):
                col_type = "integer"
            elif pd.api.types.is_float_dtype(dtype):
                col_type = "number"
            elif pd.api.types.is_bool_dtype(dtype):
                col_type = "boolean"
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                col_type = "string"
                properties[col] = {
                    "type": col_type,
                    "format": "date-time",
                }
                continue
            else:
                col_type = "string"

            properties[col] = {"type": col_type}

            # Add range constraints for numeric columns
            if col_type in ["integer", "number"]:
                min_val = float(df[col].min())
                max_val = float(df[col].max())
                properties[col]["minimum"] = min_val
                properties[col]["maximum"] = max_val

            # Mark as required if no missing values
            if df[col].notna().all():
                required.append(col)

        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": schema_name,
            "type": "object",
            "properties": properties,
            "required": required,
        }

        return schema

    @classmethod
    def list_schemas(cls) -> List[str]:
        """
        List available predefined schemas.

        Returns:
            List of schema names
        """
        return list(cls.SCHEMAS.keys())
