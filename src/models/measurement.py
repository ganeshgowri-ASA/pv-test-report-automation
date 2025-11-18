"""Models for measurement results and environmental conditions"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class EnvironmentalConditions(BaseModel):
    """Environmental conditions during testing"""
    temperature_c: Optional[float] = Field(None, description="Temperature in Celsius")
    humidity_percent: Optional[float] = Field(None, description="Relative humidity %")
    pressure_hpa: Optional[float] = Field(None, description="Atmospheric pressure in hPa")
    irradiance_wm2: Optional[float] = Field(None, description="Irradiance in W/m²")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MeasurementResult(BaseModel):
    """Generic measurement result"""
    value: float = Field(..., description="Measured value")
    unit: str = Field(..., description="Unit of measurement")
    uncertainty: Optional[float] = Field(None, description="Measurement uncertainty")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    instrument_id: Optional[str] = Field(None, description="Instrument identifier")
    calibration_date: Optional[datetime] = Field(None, description="Last calibration date")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
