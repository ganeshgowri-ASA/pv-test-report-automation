"""
Base classes for test equipment integration.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from ..models.measurement import Equipment, Measurement, MeasurementUnit, MeasurementStatus, Uncertainty


class ConnectionStatus(Enum):
    """Equipment connection status."""
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    ERROR = "error"


class EquipmentType(Enum):
    """Types of test equipment."""
    SOLAR_SIMULATOR = "solar_simulator"
    IV_TRACER = "iv_tracer"
    MULTIMETER = "multimeter"
    TEMPERATURE_CHAMBER = "temperature_chamber"
    HUMIDITY_CHAMBER = "humidity_chamber"
    INSULATION_TESTER = "insulation_tester"
    THERMAL_CAMERA = "thermal_camera"
    POWER_SUPPLY = "power_supply"
    ELECTRONIC_LOAD = "electronic_load"
    PYRANOMETER = "pyranometer"
    THERMOMETER = "thermometer"
    HYGROMETER = "hygrometer"
    OSCILLOSCOPE = "oscilloscope"
    SPECTRUM_ANALYZER = "spectrum_analyzer"


class BaseEquipment(ABC):
    """
    Abstract base class for all test equipment.

    Provides common interface for equipment communication, calibration tracking,
    and measurement acquisition.
    """

    def __init__(self, equipment_info: Equipment):
        """
        Initialize equipment.

        Args:
            equipment_info: Equipment information including calibration data
        """
        self.info = equipment_info
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.last_error: Optional[str] = None

    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to equipment.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnect from equipment.

        Returns:
            True if disconnection successful, False otherwise
        """
        pass

    @abstractmethod
    def get_identification(self) -> Dict[str, str]:
        """
        Get equipment identification (manufacturer, model, serial number).

        Returns:
            Dictionary with identification info
        """
        pass

    @abstractmethod
    def reset(self) -> bool:
        """
        Reset equipment to default state.

        Returns:
            True if reset successful, False otherwise
        """
        pass

    def is_connected(self) -> bool:
        """Check if equipment is connected."""
        return self.connection_status == ConnectionStatus.CONNECTED

    def check_calibration(self, test_date: Optional[datetime] = None) -> bool:
        """
        Check if equipment calibration is valid.

        Args:
            test_date: Date of test (defaults to now)

        Returns:
            True if calibration valid, False otherwise
        """
        if test_date is None:
            test_date = datetime.now()

        return self.info.is_calibration_valid(test_date)

    def create_measurement(
        self,
        parameter: str,
        value: float,
        unit: MeasurementUnit,
        uncertainty: Optional[Uncertainty] = None,
        **kwargs
    ) -> Measurement:
        """
        Create a measurement record.

        Args:
            parameter: Parameter name
            value: Measured value
            unit: Measurement unit
            uncertainty: Measurement uncertainty
            **kwargs: Additional metadata

        Returns:
            Measurement object
        """
        return Measurement(
            parameter=parameter,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            equipment=self.info,
            uncertainty=uncertainty,
            status=MeasurementStatus.VALID if self.check_calibration() else MeasurementStatus.INVALID,
            **kwargs
        )


class SolarSimulator(BaseEquipment):
    """Solar simulator equipment interface."""

    @abstractmethod
    def set_irradiance(self, irradiance: float) -> bool:
        """
        Set irradiance level in W/m².

        Args:
            irradiance: Target irradiance

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def get_irradiance(self) -> float:
        """
        Get current irradiance level in W/m².

        Returns:
            Current irradiance
        """
        pass

    @abstractmethod
    def set_spectrum(self, spectrum: str = "AM1.5G") -> bool:
        """
        Set spectral distribution.

        Args:
            spectrum: Spectrum type (e.g., "AM1.5G")

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def enable_flash(self) -> bool:
        """Enable flash mode for testing."""
        pass

    @abstractmethod
    def trigger_flash(self) -> bool:
        """Trigger a flash."""
        pass


class IVTracer(BaseEquipment):
    """I-V curve tracer equipment interface."""

    @abstractmethod
    def measure_iv_curve(
        self,
        voltage_start: float = 0.0,
        voltage_end: Optional[float] = None,
        points: int = 100
    ) -> Dict[str, List[float]]:
        """
        Measure I-V curve.

        Args:
            voltage_start: Starting voltage
            voltage_end: Ending voltage (auto if None)
            points: Number of measurement points

        Returns:
            Dictionary with voltage and current arrays
        """
        pass

    @abstractmethod
    def get_max_power_point(self) -> Dict[str, float]:
        """
        Get maximum power point from I-V curve.

        Returns:
            Dictionary with Vmp, Imp, Pmp
        """
        pass

    @abstractmethod
    def get_voc(self) -> float:
        """Get open circuit voltage."""
        pass

    @abstractmethod
    def get_isc(self) -> float:
        """Get short circuit current."""
        pass


class TemperatureChamber(BaseEquipment):
    """Temperature/climate chamber equipment interface."""

    @abstractmethod
    def set_temperature(self, temperature: float) -> bool:
        """
        Set target temperature in °C.

        Args:
            temperature: Target temperature

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def get_temperature(self) -> float:
        """Get current temperature in °C."""
        pass

    @abstractmethod
    def set_humidity(self, humidity: float) -> bool:
        """
        Set relative humidity in %.

        Args:
            humidity: Target humidity (0-100)

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def get_humidity(self) -> float:
        """Get current relative humidity in %."""
        pass

    @abstractmethod
    def start_program(self, program_name: str) -> bool:
        """
        Start a predefined test program.

        Args:
            program_name: Name of program to run

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def wait_for_stable(self, tolerance: float = 2.0, duration: int = 300) -> bool:
        """
        Wait for stable conditions.

        Args:
            tolerance: Acceptable variation in °C
            duration: Stabilization time in seconds

        Returns:
            True when stable
        """
        pass


class InsulationTester(BaseEquipment):
    """Insulation resistance tester equipment interface."""

    @abstractmethod
    def measure_resistance(
        self,
        test_voltage: float = 1000.0,
        duration: int = 60
    ) -> float:
        """
        Measure insulation resistance.

        Args:
            test_voltage: Test voltage in V
            duration: Test duration in seconds

        Returns:
            Resistance in Ohms
        """
        pass

    @abstractmethod
    def measure_wet_leakage_current(
        self,
        test_voltage: float = 1000.0
    ) -> float:
        """
        Measure wet leakage current.

        Args:
            test_voltage: Test voltage in V

        Returns:
            Current in Amperes
        """
        pass
