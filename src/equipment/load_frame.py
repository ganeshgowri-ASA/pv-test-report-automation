"""
Load Frame interface for mechanical loading tests
"""

from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from src.equipment.base_equipment import BaseEquipment


class LoadType(Enum):
    """Type of mechanical load"""
    STATIC = "static"
    DYNAMIC = "dynamic"
    EDGE = "edge"


@dataclass
class LoadTestResult:
    """Load test measurement results"""
    load_type: str
    load_pa: float  # Applied load (Pascal)
    duration_hours: Optional[float] = None  # For static loads
    cycles: Optional[int] = None  # For dynamic loads
    frequency_hz: Optional[float] = None  # For dynamic loads
    max_deflection_mm: Optional[float] = None  # Maximum deflection
    permanent_deformation_mm: Optional[float] = None  # Permanent deformation
    breakage_detected: bool = False
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class LoadFrame(BaseEquipment):
    """
    Mechanical Load Frame for static and dynamic loading tests

    Capabilities:
    - Static edge loading (IEC 62759)
    - Dynamic mechanical loading (1000 cycles)
    - Pressure application: 0-5000 Pa
    - Deflection monitoring
    """

    def __init__(self, equipment_id: str = "LOAD-001", name: str = "Load Frame"):
        super().__init__(equipment_id, name)
        self._is_connected = False
        self._current_load_pa = 0.0
        self._max_load_capacity_pa = 5000.0

    def connect(self) -> bool:
        """Connect to load frame controller"""
        try:
            self.logger.info(f"Connecting to {self.name} ({self.equipment_id})")
            self._is_connected = True
            self.log_event("connected")
            return True
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False

    def disconnect(self) -> bool:
        """Disconnect from load frame"""
        try:
            self.logger.info(f"Disconnecting from {self.name}")
            self._is_connected = False
            self.log_event("disconnected")
            return True
        except Exception as e:
            self.logger.error(f"Disconnection failed: {e}")
            return False

    def get_status(self) -> str:
        """Get load frame status"""
        if not self._is_connected:
            return "disconnected"
        return self.status

    def self_test(self) -> bool:
        """Perform load frame self-test"""
        try:
            self.logger.info("Performing self-test")
            self.log_event("self_test", {"result": "pass"})
            return True
        except Exception as e:
            self.logger.error(f"Self-test failed: {e}")
            return False

    def apply_static_edge_load(
        self,
        load_pa: float,
        duration_hours: float = 1.0,
        module_id: Optional[str] = None
    ) -> LoadTestResult:
        """
        Apply static edge load for IEC 62759

        Args:
            load_pa: Load pressure in Pascal (typically 600 Pa)
            duration_hours: Load duration in hours (typically 1 hour)
            module_id: Module identifier

        Returns:
            LoadTestResult: Test results
        """
        if not self._is_connected:
            raise RuntimeError("Load frame not connected")

        if load_pa > self._max_load_capacity_pa:
            raise ValueError(f"Load {load_pa} Pa exceeds capacity {self._max_load_capacity_pa} Pa")

        self.logger.info(f"Applying edge load: {load_pa} Pa for {duration_hours} hours")
        self.log_event("edge_load_start", {
            "load_pa": load_pa,
            "duration_hours": duration_hours,
            "module_id": module_id
        })

        # In real implementation:
        # 1. Position module with edge support
        # 2. Apply load gradually
        # 3. Monitor deflection over time
        # 4. Check for breakage
        # 5. Release load gradually

        self._current_load_pa = load_pa

        # Simulated measurements (replace with actual hardware interface)
        result = LoadTestResult(
            load_type=LoadType.EDGE.value,
            load_pa=load_pa,
            duration_hours=duration_hours,
            max_deflection_mm=2.5,
            permanent_deformation_mm=0.1,
            breakage_detected=False
        )

        self._current_load_pa = 0.0  # Load released

        self.log_event("edge_load_complete", {
            "max_deflection_mm": result.max_deflection_mm,
            "breakage": result.breakage_detected
        })

        return result

    def apply_dynamic_load(
        self,
        load_pa: float,
        cycles: int = 1000,
        frequency_hz: float = 1.0,
        front_loading: bool = True,
        module_id: Optional[str] = None
    ) -> LoadTestResult:
        """
        Apply dynamic mechanical load for IEC 62759

        Args:
            load_pa: Load pressure in Pascal (typically 1000 Pa)
            cycles: Number of load cycles (typically 1000)
            frequency_hz: Load frequency in Hz (0.5-2 Hz)
            front_loading: True for front, False for rear
            module_id: Module identifier

        Returns:
            LoadTestResult: Test results
        """
        if not self._is_connected:
            raise RuntimeError("Load frame not connected")

        if not (0.5 <= frequency_hz <= 2.0):
            raise ValueError(f"Frequency {frequency_hz} Hz outside valid range [0.5, 2.0] Hz")

        side = "front" if front_loading else "rear"
        self.logger.info(f"Applying dynamic load: {load_pa} Pa, {cycles} cycles at {frequency_hz} Hz ({side})")

        self.log_event("dynamic_load_start", {
            "load_pa": load_pa,
            "cycles": cycles,
            "frequency_hz": frequency_hz,
            "side": side,
            "module_id": module_id
        })

        # In real implementation:
        # 1. Position module
        # 2. Run load cycling
        # 3. Monitor for breakage
        # 4. Track actual cycles completed

        # Simulated measurements
        result = LoadTestResult(
            load_type=LoadType.DYNAMIC.value,
            load_pa=load_pa,
            cycles=cycles,
            frequency_hz=frequency_hz,
            max_deflection_mm=3.2,
            breakage_detected=False
        )

        self.log_event("dynamic_load_complete", {
            "cycles_completed": cycles,
            "breakage": result.breakage_detected
        })

        return result

    def measure_deflection(self) -> float:
        """
        Measure current module deflection

        Returns:
            float: Deflection in mm
        """
        # In real implementation, read from LVDT or laser displacement sensor
        deflection_mm = 2.3  # Simulated value
        return deflection_mm

    def check_breakage(self) -> bool:
        """
        Check for module breakage using acoustic emission or other sensors

        Returns:
            bool: True if breakage detected
        """
        # In real implementation, monitor acoustic sensors, current drop, etc.
        breakage = False  # Simulated value
        if breakage:
            self.log_event("breakage_detected", {"timestamp": datetime.now().isoformat()})
        return breakage

    def release_load(self):
        """Gradually release applied load"""
        self.logger.info("Releasing load")
        self._current_load_pa = 0.0
        self.log_event("load_released")

    def get_measurement_data(self) -> Dict[str, Any]:
        """Get detailed measurement data including uncertainty"""
        return {
            "equipment_id": self.equipment_id,
            "current_load_pa": self._current_load_pa,
            "max_capacity_pa": self._max_load_capacity_pa,
            "uncertainty": {
                "load_pa": self.get_measurement_uncertainty("load") or 5.0,  # ±5 Pa
                "deflection_mm": self.get_measurement_uncertainty("deflection") or 0.1,  # ±0.1 mm
            }
        }
