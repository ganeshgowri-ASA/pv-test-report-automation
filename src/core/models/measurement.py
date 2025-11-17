"""
Data models for test measurements with full traceability.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class MeasurementUnit(Enum):
    """Standard measurement units for PV testing."""
    VOLTAGE = "V"
    CURRENT = "A"
    POWER = "W"
    RESISTANCE = "Ω"
    TEMPERATURE = "°C"
    IRRADIANCE = "W/m²"
    PERCENT = "%"
    TIME = "s"
    ANGLE = "°"
    PRESSURE = "Pa"
    HUMIDITY = "%RH"
    LENGTH = "mm"
    FORCE = "N"
    ENERGY = "kWh"


class MeasurementStatus(Enum):
    """Status of a measurement."""
    VALID = "valid"
    INVALID = "invalid"
    PENDING = "pending"
    ERROR = "error"
    OUT_OF_RANGE = "out_of_range"


@dataclass
class Uncertainty:
    """Measurement uncertainty information."""
    value: float
    coverage_factor: float = 2.0  # k=2 for 95% confidence
    distribution: str = "normal"

    def expanded_uncertainty(self) -> float:
        """Calculate expanded uncertainty."""
        return self.value * self.coverage_factor


@dataclass
class Equipment:
    """Test equipment information for traceability."""
    id: str
    name: str
    manufacturer: str
    model: str
    serial_number: str
    calibration_date: datetime
    calibration_due_date: datetime
    calibration_certificate: str
    accuracy: Optional[float] = None

    def is_calibration_valid(self, test_date: datetime) -> bool:
        """Check if calibration is valid for test date."""
        return self.calibration_date <= test_date <= self.calibration_due_date


@dataclass
class Measurement:
    """Single measurement with full traceability."""
    parameter: str
    value: float
    unit: MeasurementUnit
    timestamp: datetime
    equipment: Equipment
    uncertainty: Optional[Uncertainty] = None
    status: MeasurementStatus = MeasurementStatus.VALID
    environmental_conditions: Dict[str, Any] = field(default_factory=dict)
    operator: Optional[str] = None
    notes: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

    def is_valid(self) -> bool:
        """Check if measurement is valid."""
        return (
            self.status == MeasurementStatus.VALID and
            self.equipment.is_calibration_valid(self.timestamp)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert measurement to dictionary."""
        return {
            "parameter": self.parameter,
            "value": self.value,
            "unit": self.unit.value,
            "timestamp": self.timestamp.isoformat(),
            "equipment": {
                "id": self.equipment.id,
                "name": self.equipment.name,
                "serial_number": self.equipment.serial_number,
            },
            "uncertainty": {
                "value": self.uncertainty.value,
                "coverage_factor": self.uncertainty.coverage_factor,
            } if self.uncertainty else None,
            "status": self.status.value,
            "environmental_conditions": self.environmental_conditions,
            "operator": self.operator,
            "notes": self.notes,
        }


@dataclass
class MeasurementSeries:
    """Series of related measurements."""
    name: str
    measurements: List[Measurement] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    def add_measurement(self, measurement: Measurement) -> None:
        """Add measurement to series."""
        self.measurements.append(measurement)
        if not self.start_time or measurement.timestamp < self.start_time:
            self.start_time = measurement.timestamp
        if not self.end_time or measurement.timestamp > self.end_time:
            self.end_time = measurement.timestamp

    def get_average(self) -> Optional[float]:
        """Calculate average value of all measurements."""
        valid_measurements = [m for m in self.measurements if m.is_valid()]
        if not valid_measurements:
            return None
        return sum(m.value for m in valid_measurements) / len(valid_measurements)

    def get_std_deviation(self) -> Optional[float]:
        """Calculate standard deviation."""
        valid_measurements = [m for m in self.measurements if m.is_valid()]
        if len(valid_measurements) < 2:
            return None
        avg = self.get_average()
        variance = sum((m.value - avg) ** 2 for m in valid_measurements) / (len(valid_measurements) - 1)
        return variance ** 0.5
