"""
Thermal Chamber interface for temperature cycling tests
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from src.equipment.base_equipment import BaseEquipment


class ChamberStatus(Enum):
    """Thermal chamber status"""
    IDLE = "idle"
    RAMPING = "ramping"
    HOLDING = "holding"
    CYCLING = "cycling"
    ERROR = "error"


@dataclass
class ThermalCycleProfile:
    """Thermal cycle profile definition"""
    low_temp: float  # Low temperature (°C)
    high_temp: float  # High temperature (°C)
    ramp_rate: float  # Ramp rate (°C/hour)
    hold_time_min: float  # Hold time at extremes (minutes)
    cycles: int  # Number of cycles


@dataclass
class ThermalTestResult:
    """Thermal cycling test results"""
    profile: ThermalCycleProfile
    cycles_completed: int
    actual_low_temp: float
    actual_high_temp: float
    average_ramp_rate: float
    temperature_log: Optional[List[Dict]] = None
    errors: Optional[List[str]] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.temperature_log is None:
            self.temperature_log = []
        if self.errors is None:
            self.errors = []


class ThermalChamber(BaseEquipment):
    """
    Environmental Thermal Chamber for temperature cycling tests

    Capabilities:
    - Temperature range: -70°C to +180°C
    - Humidity control: 10-95% RH
    - Programmable profiles
    - IEC 62759 thermal cycling: -40°C to +85°C
    """

    def __init__(self, equipment_id: str = "THERMAL-001", name: str = "Thermal Chamber"):
        super().__init__(equipment_id, name)
        self._is_connected = False
        self._current_temperature = 25.0  # °C
        self._current_humidity = 50.0  # %RH
        self._target_temperature = 25.0
        self._target_humidity = 50.0
        self._chamber_status = ChamberStatus.IDLE
        self._min_temp = -70.0
        self._max_temp = 180.0

    def connect(self) -> bool:
        """Connect to thermal chamber controller"""
        try:
            self.logger.info(f"Connecting to {self.name} ({self.equipment_id})")
            self._is_connected = True
            self.log_event("connected")
            return True
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False

    def disconnect(self) -> bool:
        """Disconnect from thermal chamber"""
        try:
            self.logger.info(f"Disconnecting from {self.name}")
            self._is_connected = False
            self.log_event("disconnected")
            return True
        except Exception as e:
            self.logger.error(f"Disconnection failed: {e}")
            return False

    def get_status(self) -> str:
        """Get chamber status"""
        if not self._is_connected:
            return "disconnected"
        return self._chamber_status.value

    def self_test(self) -> bool:
        """Perform chamber self-test"""
        try:
            self.logger.info("Performing self-test")
            self.log_event("self_test", {"result": "pass"})
            return True
        except Exception as e:
            self.logger.error(f"Self-test failed: {e}")
            return False

    def set_temperature(self, temperature: float):
        """
        Set target temperature

        Args:
            temperature: Target temperature in °C
        """
        if not (self._min_temp <= temperature <= self._max_temp):
            raise ValueError(
                f"Temperature {temperature}°C outside valid range [{self._min_temp}, {self._max_temp}]"
            )

        self._target_temperature = temperature
        self.logger.info(f"Target temperature set to {temperature}°C")
        self.log_event("temperature_setpoint", {"temperature": temperature})

    def set_humidity(self, humidity: float):
        """
        Set target humidity

        Args:
            humidity: Target humidity in %RH
        """
        if not (10.0 <= humidity <= 95.0):
            raise ValueError(f"Humidity {humidity}%RH outside valid range [10, 95]")

        self._target_humidity = humidity
        self.logger.info(f"Target humidity set to {humidity}%RH")
        self.log_event("humidity_setpoint", {"humidity": humidity})

    def get_current_conditions(self) -> Dict[str, float]:
        """
        Get current chamber conditions

        Returns:
            Dict: Current temperature and humidity
        """
        return {
            "temperature": self._current_temperature,
            "humidity": self._current_humidity,
            "timestamp": datetime.now().isoformat()
        }

    def wait_for_stabilization(
        self,
        tolerance_temp: float = 0.5,
        tolerance_humidity: float = 2.0,
        timeout: int = 1800
    ) -> bool:
        """
        Wait for chamber to stabilize at target conditions

        Args:
            tolerance_temp: Temperature tolerance (°C)
            tolerance_humidity: Humidity tolerance (%RH)
            timeout: Maximum wait time (seconds)

        Returns:
            bool: True if stabilized
        """
        self.logger.info("Waiting for chamber stabilization...")

        # In real implementation:
        # 1. Monitor temperature and humidity
        # 2. Check stability over time
        # 3. Ensure within tolerance

        # Simulated stabilization
        self._current_temperature = self._target_temperature
        self._current_humidity = self._target_humidity

        self.log_event("stabilization_complete", {
            "temperature": self._current_temperature,
            "humidity": self._current_humidity
        })

        return True

    def run_thermal_cycling(
        self,
        profile: ThermalCycleProfile,
        module_id: Optional[str] = None
    ) -> ThermalTestResult:
        """
        Run thermal cycling test per IEC 62759

        Args:
            profile: Thermal cycle profile
            module_id: Module identifier

        Returns:
            ThermalTestResult: Test results
        """
        if not self._is_connected:
            raise RuntimeError("Thermal chamber not connected")

        self.logger.info(
            f"Starting thermal cycling: {profile.cycles} cycles, "
            f"{profile.low_temp}°C to {profile.high_temp}°C"
        )

        self.log_event("thermal_cycling_start", {
            "cycles": profile.cycles,
            "low_temp": profile.low_temp,
            "high_temp": profile.high_temp,
            "ramp_rate": profile.ramp_rate,
            "hold_time_min": profile.hold_time_min,
            "module_id": module_id
        })

        self._chamber_status = ChamberStatus.CYCLING

        # In real implementation:
        # 1. Program chamber controller with profile
        # 2. Execute cycling
        # 3. Log temperature data
        # 4. Monitor for errors
        # 5. Check module integrity during cycling

        # Simulated cycling
        temperature_log = []
        for cycle in range(profile.cycles):
            # Log cycle progress
            if cycle % 10 == 0:  # Log every 10th cycle
                self.logger.info(f"Cycle {cycle + 1}/{profile.cycles} in progress")
                temperature_log.append({
                    "cycle": cycle + 1,
                    "timestamp": datetime.now().isoformat(),
                    "temperature": profile.low_temp if cycle % 2 == 0 else profile.high_temp
                })

        self._chamber_status = ChamberStatus.IDLE

        result = ThermalTestResult(
            profile=profile,
            cycles_completed=profile.cycles,
            actual_low_temp=profile.low_temp,
            actual_high_temp=profile.high_temp,
            average_ramp_rate=profile.ramp_rate,
            temperature_log=temperature_log
        )

        self.log_event("thermal_cycling_complete", {
            "cycles_completed": result.cycles_completed
        })

        return result

    def run_iec62759_thermal_cycling(
        self,
        cycles: int = 50,
        module_id: Optional[str] = None
    ) -> ThermalTestResult:
        """
        Run IEC 62759 standard thermal cycling profile

        Args:
            cycles: Number of cycles (default 50)
            module_id: Module identifier

        Returns:
            ThermalTestResult: Test results
        """
        profile = ThermalCycleProfile(
            low_temp=-40.0,
            high_temp=85.0,
            ramp_rate=100.0,  # °C/hour
            hold_time_min=15.0,  # Middle of 10-20 min range
            cycles=cycles
        )

        return self.run_thermal_cycling(profile, module_id)

    def emergency_stop(self):
        """Emergency stop - return to ambient conditions"""
        self.logger.warning("Emergency stop activated")
        self._chamber_status = ChamberStatus.IDLE
        self._target_temperature = 25.0
        self._target_humidity = 50.0
        self.log_event("emergency_stop")

    def get_measurement_data(self) -> Dict[str, Any]:
        """Get detailed measurement data including uncertainty"""
        return {
            "equipment_id": self.equipment_id,
            "current_temperature": self._current_temperature,
            "current_humidity": self._current_humidity,
            "target_temperature": self._target_temperature,
            "target_humidity": self._target_humidity,
            "status": self._chamber_status.value,
            "uncertainty": {
                "temperature": self.get_measurement_uncertainty("temperature") or 0.5,  # ±0.5°C
                "humidity": self.get_measurement_uncertainty("humidity") or 2.0,  # ±2%RH
            }
        }
