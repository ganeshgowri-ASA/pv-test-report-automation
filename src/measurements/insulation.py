"""
Insulation Resistance Measurement Module

Handles insulation resistance measurements for PV modules according to
IEC 61215 and IEC 61730 standards.
"""

from dataclasses import dataclass
from typing import Optional, Dict
from datetime import datetime
from enum import Enum


class InsulationTestVoltage(Enum):
    """Standard test voltages for insulation resistance"""
    V_500 = 500  # 500V DC
    V_1000 = 1000  # 1000V DC (most common for PV modules)
    V_2500 = 2500  # 2500V DC (high voltage modules)


@dataclass
class InsulationResistanceData:
    """
    Insulation resistance measurement data

    Contains resistance measurement and test conditions per IEC standards
    """
    resistance: float  # Ohms (Ω)
    test_voltage: float  # Volts DC
    measurement_duration: float  # seconds
    temperature: float  # Celsius
    humidity: float  # %RH
    timestamp: datetime
    pass_threshold: float  # Minimum acceptable resistance (Ω)
    location: str = "Frame to active parts"  # Measurement location
    stabilization_time: float = 60.0  # seconds

    @property
    def resistance_megohm(self) -> float:
        """Resistance in MegaOhms (MΩ)"""
        return self.resistance / 1e6

    @property
    def passes(self) -> bool:
        """Check if measurement meets pass threshold"""
        return self.resistance >= self.pass_threshold

    @property
    def pass_threshold_megohm(self) -> float:
        """Pass threshold in MegaOhms (MΩ)"""
        return self.pass_threshold / 1e6

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'resistance_ohm': self.resistance,
            'resistance_megohm': self.resistance_megohm,
            'test_voltage': self.test_voltage,
            'measurement_duration': self.measurement_duration,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'timestamp': self.timestamp.isoformat(),
            'pass_threshold_ohm': self.pass_threshold,
            'pass_threshold_megohm': self.pass_threshold_megohm,
            'location': self.location,
            'passes': self.passes,
            'status': 'PASS' if self.passes else 'FAIL'
        }


class InsulationResistanceMeasurement:
    """
    Insulation resistance measurement interface

    Provides methods to measure insulation resistance of PV modules
    per IEC 61215 and IEC 61730 requirements.
    """

    # IEC 61215 requirement: R > 40 MΩ or R × A > 400 MΩ·m²
    DEFAULT_THRESHOLD_OHM = 40e6  # 40 MΩ in Ohms
    DEFAULT_TEST_VOLTAGE = 1000  # 1000V DC
    DEFAULT_MEASUREMENT_DURATION = 60  # 60 seconds

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize insulation resistance measurement

        Args:
            config: Configuration dictionary with test parameters
        """
        self.config = config or {}
        self.test_voltage = self.config.get('test_voltage', self.DEFAULT_TEST_VOLTAGE)
        self.measurement_duration = self.config.get(
            'measurement_duration',
            self.DEFAULT_MEASUREMENT_DURATION
        )
        self.pass_threshold = self.config.get(
            'pass_threshold',
            self.DEFAULT_THRESHOLD_OHM
        )

    def measure(self,
                temperature: float,
                humidity: float,
                location: str = "Frame to active parts") -> InsulationResistanceData:
        """
        Perform insulation resistance measurement

        Args:
            temperature: Ambient temperature (°C)
            humidity: Relative humidity (%RH)
            location: Measurement location description

        Returns:
            InsulationResistanceData object

        Note:
            This is a placeholder implementation. In production, this would
            interface with actual insulation resistance meter equipment.
        """
        # Placeholder: In production, this would communicate with megohmmeter
        # For now, we return a structure that matches expected interface
        measured_resistance = 0.0  # Would be actual measurement

        return InsulationResistanceData(
            resistance=measured_resistance,
            test_voltage=self.test_voltage,
            measurement_duration=self.measurement_duration,
            temperature=temperature,
            humidity=humidity,
            timestamp=datetime.now(),
            pass_threshold=self.pass_threshold,
            location=location
        )

    def measure_with_area_correction(self,
                                     temperature: float,
                                     humidity: float,
                                     module_area: float,
                                     location: str = "Frame to active parts") -> InsulationResistanceData:
        """
        Perform insulation resistance measurement with area correction

        Per IEC 61215: R > 40 MΩ or R × A > 400 MΩ·m²

        Args:
            temperature: Ambient temperature (°C)
            humidity: Relative humidity (%RH)
            module_area: Module area in m²
            location: Measurement location description

        Returns:
            InsulationResistanceData object with area-corrected threshold
        """
        # Calculate area-corrected threshold
        # If R × A > 400 MΩ·m², then R > 400/A MΩ
        area_corrected_threshold = max(
            self.DEFAULT_THRESHOLD_OHM,
            (400e6 / module_area) if module_area > 0 else self.DEFAULT_THRESHOLD_OHM
        )

        # Temporarily set threshold
        original_threshold = self.pass_threshold
        self.pass_threshold = area_corrected_threshold

        # Perform measurement
        result = self.measure(temperature, humidity, location)

        # Restore original threshold
        self.pass_threshold = original_threshold

        return result

    def validate_measurement(self, data: InsulationResistanceData) -> bool:
        """
        Validate insulation resistance measurement

        Args:
            data: Measurement data to validate

        Returns:
            True if measurement is valid, False otherwise
        """
        # Check for reasonable resistance value (not open circuit)
        if data.resistance <= 0 or data.resistance > 1e12:  # > 1 TΩ is suspicious
            return False

        # Check environmental conditions are within acceptable range
        if data.temperature < -10 or data.temperature > 85:
            return False

        if data.humidity < 0 or data.humidity > 100:
            return False

        return True

    def calculate_leakage_current(self, resistance: float, test_voltage: float) -> float:
        """
        Calculate leakage current from resistance and test voltage

        Args:
            resistance: Measured resistance (Ω)
            test_voltage: Applied test voltage (V)

        Returns:
            Leakage current in microamperes (µA)
        """
        if resistance <= 0:
            return float('inf')

        # I = V / R
        leakage_current_a = test_voltage / resistance
        leakage_current_ua = leakage_current_a * 1e6  # Convert to µA

        return leakage_current_ua
