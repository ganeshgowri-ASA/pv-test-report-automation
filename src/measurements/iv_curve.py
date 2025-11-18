"""
I-V Curve Measurement Module

Handles I-V curve data acquisition, processing, and analysis for PV modules
according to IEC 60904 standards.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json


@dataclass
class IVCurveData:
    """
    I-V curve measurement data with derived parameters

    Contains voltage, current, and power measurements along with
    calculated key performance parameters.
    """
    voltage: List[float]  # Volts
    current: List[float]  # Amperes
    power: List[float] = field(init=False)
    timestamp: datetime = field(default_factory=datetime.now)
    conditions: Dict[str, float] = field(default_factory=dict)
    irradiance: Optional[float] = None  # W/m²
    cell_temperature: Optional[float] = None  # °C

    def __post_init__(self):
        """Calculate power from voltage and current"""
        if len(self.voltage) != len(self.current):
            raise ValueError("Voltage and current arrays must have same length")
        self.power = [v * i for v, i in zip(self.voltage, self.current)]

    @property
    def voc(self) -> float:
        """Open circuit voltage (V)"""
        return max(self.voltage) if self.voltage else 0.0

    @property
    def isc(self) -> float:
        """Short circuit current (A)"""
        return max(self.current) if self.current else 0.0

    @property
    def pmax(self) -> float:
        """Maximum power point (W)"""
        return max(self.power) if self.power else 0.0

    @property
    def vmpp(self) -> float:
        """Voltage at maximum power point (V)"""
        if not self.power:
            return 0.0
        max_idx = self.power.index(self.pmax)
        return self.voltage[max_idx]

    @property
    def impp(self) -> float:
        """Current at maximum power point (A)"""
        if not self.power:
            return 0.0
        max_idx = self.power.index(self.pmax)
        return self.current[max_idx]

    @property
    def fill_factor(self) -> float:
        """Fill factor (dimensionless)"""
        if self.voc == 0 or self.isc == 0:
            return 0.0
        return self.pmax / (self.voc * self.isc)

    def calculate_efficiency(self, module_area: float) -> float:
        """
        Calculate module efficiency

        Args:
            module_area: Module area in m²

        Returns:
            Efficiency as percentage
        """
        if not self.irradiance or self.irradiance == 0 or module_area == 0:
            return 0.0
        return (self.pmax / (self.irradiance * module_area)) * 100

    def calculate_power_degradation(self, baseline_curve: 'IVCurveData') -> float:
        """
        Calculate power degradation compared to baseline

        Args:
            baseline_curve: Baseline I-V curve for comparison

        Returns:
            Power degradation as percentage (positive means degradation)
        """
        if baseline_curve.pmax == 0:
            return 0.0
        degradation = ((baseline_curve.pmax - self.pmax) / baseline_curve.pmax) * 100
        return degradation

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'voltage': self.voltage,
            'current': self.current,
            'power': self.power,
            'voc': self.voc,
            'isc': self.isc,
            'pmax': self.pmax,
            'vmpp': self.vmpp,
            'impp': self.impp,
            'fill_factor': self.fill_factor,
            'irradiance': self.irradiance,
            'cell_temperature': self.cell_temperature,
            'conditions': self.conditions
        }

    def to_json(self) -> str:
        """Export to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict) -> 'IVCurveData':
        """Create IVCurveData from dictionary"""
        return cls(
            voltage=data['voltage'],
            current=data['current'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            conditions=data.get('conditions', {}),
            irradiance=data.get('irradiance'),
            cell_temperature=data.get('cell_temperature')
        )


class IVCurveMeasurement:
    """
    I-V curve measurement interface

    This class provides methods to acquire and process I-V curve data
    from PV modules under test.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize I-V curve measurement

        Args:
            config: Configuration dictionary for measurement parameters
        """
        self.config = config or {}
        self.sweep_points = self.config.get('sweep_points', 100)
        self.sweep_delay = self.config.get('sweep_delay_ms', 10)  # milliseconds
        self.settling_time = self.config.get('settling_time_ms', 100)  # milliseconds

    def acquire(self, irradiance: float, cell_temp: float) -> IVCurveData:
        """
        Acquire I-V curve data

        Args:
            irradiance: Irradiance in W/m²
            cell_temp: Cell temperature in °C

        Returns:
            IVCurveData object containing measurement

        Note:
            This is a placeholder implementation. In production, this would
            interface with actual I-V curve tracer equipment.
        """
        # Placeholder: In production, this would communicate with I-V tracer
        # For now, we'll return a structure that matches expected interface
        voltage = []
        current = []

        return IVCurveData(
            voltage=voltage,
            current=current,
            irradiance=irradiance,
            cell_temperature=cell_temp,
            conditions={
                'sweep_points': self.sweep_points,
                'sweep_delay_ms': self.sweep_delay
            }
        )

    def validate(self, curve_data: IVCurveData) -> bool:
        """
        Validate I-V curve data quality

        Args:
            curve_data: I-V curve data to validate

        Returns:
            True if data is valid, False otherwise
        """
        # Check for minimum number of points
        if len(curve_data.voltage) < 10:
            return False

        # Check for monotonic voltage increase
        if not all(curve_data.voltage[i] <= curve_data.voltage[i+1]
                   for i in range(len(curve_data.voltage)-1)):
            return False

        # Check for reasonable fill factor
        if curve_data.fill_factor < 0.4 or curve_data.fill_factor > 0.9:
            return False

        # Check for positive Voc and Isc
        if curve_data.voc <= 0 or curve_data.isc <= 0:
            return False

        return True
