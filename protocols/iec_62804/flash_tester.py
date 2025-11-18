"""
IEC 62804 PID Testing Protocol - Flash Test / I-V Tracer Integration

This module provides interfaces for I-V curve measurement (flash testing)
used to detect power degradation in PID testing.
"""

import logging
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class IVCurvePoint:
    """Single I-V curve measurement point"""
    voltage: float  # V
    current: float  # A


@dataclass
class IVCurveData:
    """Complete I-V curve measurement"""
    timestamp: datetime
    points: List[IVCurvePoint]

    # Derived parameters
    voc: float  # Open circuit voltage (V)
    isc: float  # Short circuit current (A)
    vmp: float  # Voltage at max power (V)
    imp: float  # Current at max power (A)
    pmax: float  # Maximum power (W)
    ff: float  # Fill factor

    # Test conditions
    irradiance: float = 1000.0  # W/m² (STC)
    module_temperature: float = 25.0  # °C (STC)
    cell_temperature: Optional[float] = None  # °C

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "points": [(p.voltage, p.current) for p in self.points],
            "voc": self.voc,
            "isc": self.isc,
            "vmp": self.vmp,
            "imp": self.imp,
            "pmax": self.pmax,
            "ff": self.ff,
            "irradiance": self.irradiance,
            "module_temperature": self.module_temperature,
            "cell_temperature": self.cell_temperature
        }

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IVCurveData':
        """Create from dictionary"""
        points = [IVCurvePoint(v, i) for v, i in data["points"]]
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            points=points,
            voc=data["voc"],
            isc=data["isc"],
            vmp=data["vmp"],
            imp=data["imp"],
            pmax=data["pmax"],
            ff=data["ff"],
            irradiance=data.get("irradiance", 1000.0),
            module_temperature=data.get("module_temperature", 25.0),
            cell_temperature=data.get("cell_temperature")
        )


class FlashTesterBase(ABC):
    """
    Base class for I-V curve measurement systems.

    Supports various solar simulators and I-V tracers.
    """

    def __init__(
        self,
        tester_id: str,
        connection_params: Dict[str, Any]
    ):
        """
        Initialize flash tester.

        Args:
            tester_id: Unique identifier
            connection_params: Connection parameters
        """
        self.tester_id = tester_id
        self.connection_params = connection_params
        self._connected = False

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to I-V tracer"""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from I-V tracer"""
        pass

    @abstractmethod
    def measure_iv_curve(
        self,
        module_area: Optional[float] = None,
        expected_voc: Optional[float] = None,
        expected_isc: Optional[float] = None
    ) -> IVCurveData:
        """
        Measure I-V curve.

        Args:
            module_area: Module area in m² (for irradiance correction)
            expected_voc: Expected Voc for voltage range
            expected_isc: Expected Isc for current range

        Returns:
            Complete I-V curve data
        """
        pass

    @abstractmethod
    def get_irradiance(self) -> float:
        """
        Get current irradiance.

        Returns:
            Irradiance in W/m²
        """
        pass

    @abstractmethod
    def get_module_temperature(self) -> float:
        """
        Get module temperature.

        Returns:
            Temperature in °C
        """
        pass

    def is_connected(self) -> bool:
        """Check connection status"""
        return self._connected

    @staticmethod
    def calculate_parameters(
        voltages: np.ndarray,
        currents: np.ndarray
    ) -> Tuple[float, float, float, float, float, float]:
        """
        Calculate I-V curve parameters from raw data.

        Args:
            voltages: Array of voltages
            currents: Array of currents

        Returns:
            Tuple of (Voc, Isc, Vmp, Imp, Pmax, FF)
        """
        # Find Voc (current ≈ 0)
        voc_idx = np.argmin(np.abs(currents))
        voc = voltages[voc_idx]

        # Find Isc (voltage ≈ 0)
        isc_idx = np.argmin(np.abs(voltages))
        isc = currents[isc_idx]

        # Calculate power at each point
        power = voltages * currents

        # Find maximum power point
        pmax_idx = np.argmax(power)
        pmax = power[pmax_idx]
        vmp = voltages[pmax_idx]
        imp = currents[pmax_idx]

        # Calculate fill factor
        ff = pmax / (voc * isc) if (voc * isc) > 0 else 0.0

        return float(voc), float(isc), float(vmp), float(imp), float(pmax), float(ff)


class SimulatedFlashTester(FlashTesterBase):
    """
    Simulated flash tester for testing and development.

    Generates realistic I-V curves with optional degradation.
    """

    def __init__(
        self,
        tester_id: str,
        connection_params: Optional[Dict[str, Any]] = None,
        nominal_pmax: float = 300.0,  # W
        nominal_voc: float = 40.0,  # V
        nominal_isc: float = 9.0  # A
    ):
        super().__init__(tester_id, connection_params or {})
        self.nominal_pmax = nominal_pmax
        self.nominal_voc = nominal_voc
        self.nominal_isc = nominal_isc
        self._degradation_factor = 1.0  # 1.0 = no degradation
        self._irradiance = 1000.0  # W/m²
        self._temperature = 25.0  # °C

    def connect(self) -> bool:
        """Simulate connection"""
        logger.info(f"Connecting to simulated flash tester {self.tester_id}")
        self._connected = True
        return True

    def disconnect(self) -> bool:
        """Simulate disconnection"""
        logger.info(f"Disconnecting from flash tester {self.tester_id}")
        self._connected = False
        return True

    def measure_iv_curve(
        self,
        module_area: Optional[float] = None,
        expected_voc: Optional[float] = None,
        expected_isc: Optional[float] = None
    ) -> IVCurveData:
        """
        Generate simulated I-V curve.

        Uses single-diode model with realistic behavior.
        """
        if not self._connected:
            raise RuntimeError("Flash tester not connected")

        # Generate voltage sweep (0 to Voc)
        voc_actual = self.nominal_voc * self._degradation_factor
        num_points = 100
        voltages = np.linspace(0, voc_actual * 1.05, num_points)

        # Generate realistic I-V curve using simplified model
        # I = Isc * (1 - exp((V - Voc) / (n * Vt)))
        isc_actual = self.nominal_isc * self._degradation_factor
        n = 1.2  # Ideality factor
        vt = 0.026  # Thermal voltage at 25°C

        currents = isc_actual * (1 - np.exp((voltages - voc_actual) / (n * vt * len(voltages))))
        currents = np.maximum(currents, 0)  # No negative current

        # Add realistic noise
        noise = np.random.normal(0, 0.01 * isc_actual, num_points)
        currents = currents + noise
        currents = np.maximum(currents, 0)

        # Calculate parameters
        voc, isc, vmp, imp, pmax, ff = self.calculate_parameters(voltages, currents)

        # Create I-V curve points
        points = [IVCurvePoint(v, i) for v, i in zip(voltages, currents)]

        return IVCurveData(
            timestamp=datetime.utcnow(),
            points=points,
            voc=voc,
            isc=isc,
            vmp=vmp,
            imp=imp,
            pmax=pmax,
            ff=ff,
            irradiance=self._irradiance,
            module_temperature=self._temperature
        )

    def get_irradiance(self) -> float:
        """Get simulated irradiance"""
        return self._irradiance

    def get_module_temperature(self) -> float:
        """Get simulated temperature"""
        return self._temperature

    def set_degradation(self, degradation_pct: float):
        """
        Set degradation level for simulation.

        Args:
            degradation_pct: Degradation percentage (0-100)
        """
        self._degradation_factor = 1.0 - (degradation_pct / 100.0)
        logger.info(f"Degradation set to {degradation_pct}% (factor: {self._degradation_factor})")

    def set_conditions(self, irradiance: float, temperature: float):
        """
        Set test conditions.

        Args:
            irradiance: Irradiance in W/m²
            temperature: Temperature in °C
        """
        self._irradiance = irradiance
        self._temperature = temperature


class FlashTestScheduler:
    """
    Schedule and execute flash tests at specified intervals.
    """

    def __init__(
        self,
        tester: FlashTesterBase,
        test_start_time: datetime,
        test_intervals: List[float]  # Hours from start
    ):
        """
        Initialize flash test scheduler.

        Args:
            tester: Flash tester instance
            test_start_time: Test start time
            test_intervals: List of hours from start to perform flash tests
        """
        self.tester = tester
        self.test_start_time = test_start_time
        self.test_intervals = sorted(test_intervals)
        self._completed_intervals: List[float] = []

    def get_next_test_time(self) -> Optional[datetime]:
        """
        Get time of next scheduled flash test.

        Returns:
            Next test time or None if all tests completed
        """
        for interval in self.test_intervals:
            if interval not in self._completed_intervals:
                from datetime import timedelta
                return self.test_start_time + timedelta(hours=interval)
        return None

    def is_test_due(self, current_time: datetime, tolerance_minutes: float = 30) -> bool:
        """
        Check if a flash test is due.

        Args:
            current_time: Current time
            tolerance_minutes: Tolerance window in minutes

        Returns:
            True if test should be performed
        """
        next_test = self.get_next_test_time()
        if next_test is None:
            return False

        from datetime import timedelta
        time_diff = abs((current_time - next_test).total_seconds() / 60)
        return time_diff <= tolerance_minutes

    def get_current_interval(self, current_time: datetime) -> Optional[float]:
        """
        Get the interval (hours from start) for current time.

        Args:
            current_time: Current time

        Returns:
            Hours from start, or None if before first test
        """
        elapsed = (current_time - self.test_start_time).total_seconds() / 3600

        # Find the interval we're at or past
        for interval in self.test_intervals:
            if interval not in self._completed_intervals and elapsed >= interval:
                return interval

        return None

    def mark_completed(self, interval: float):
        """
        Mark a flash test interval as completed.

        Args:
            interval: Hours from start
        """
        if interval not in self._completed_intervals:
            self._completed_intervals.append(interval)
            logger.info(f"Flash test at {interval}h marked complete")

    def get_progress(self) -> Dict[str, Any]:
        """
        Get test progress.

        Returns:
            Progress information
        """
        return {
            "total_tests": len(self.test_intervals),
            "completed_tests": len(self._completed_intervals),
            "remaining_tests": len(self.test_intervals) - len(self._completed_intervals),
            "completed_intervals": sorted(self._completed_intervals),
            "remaining_intervals": [
                i for i in self.test_intervals if i not in self._completed_intervals
            ]
        }


def create_flash_tester(
    tester_type: str,
    tester_id: str,
    connection_params: Optional[Dict[str, Any]] = None,
    **kwargs
) -> FlashTesterBase:
    """
    Factory function to create flash tester instances.

    Args:
        tester_type: Type of tester ("simulated", "spire", "pasan", etc.)
        tester_id: Unique tester identifier
        connection_params: Connection parameters
        **kwargs: Additional parameters for specific tester types

    Returns:
        Flash tester instance
    """
    if tester_type.lower() == "simulated":
        return SimulatedFlashTester(tester_id, connection_params, **kwargs)
    else:
        # Placeholder for real tester implementations
        logger.warning(f"Tester type '{tester_type}' not implemented, using simulated")
        return SimulatedFlashTester(tester_id, connection_params)


def correct_to_stc(
    measured_pmax: float,
    measured_irradiance: float,
    measured_temp: float,
    temp_coeff_pmax: float = -0.4  # %/°C typical for crystalline Si
) -> float:
    """
    Correct measured power to Standard Test Conditions (STC).

    STC: 1000 W/m², 25°C cell temperature

    Args:
        measured_pmax: Measured maximum power (W)
        measured_irradiance: Measured irradiance (W/m²)
        measured_temp: Measured cell temperature (°C)
        temp_coeff_pmax: Temperature coefficient of Pmax (%/°C)

    Returns:
        Power corrected to STC (W)
    """
    # Irradiance correction (linear)
    irradiance_corrected = measured_pmax * (1000.0 / measured_irradiance)

    # Temperature correction
    temp_diff = measured_temp - 25.0
    temp_correction = 1.0 - (temp_coeff_pmax / 100.0) * temp_diff
    stc_power = irradiance_corrected * temp_correction

    return stc_power
