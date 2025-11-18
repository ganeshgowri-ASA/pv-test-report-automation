"""
Solar Simulator interface for flash testing
"""

from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from src.equipment.base_equipment import BaseEquipment


@dataclass
class FlashTestResult:
    """Flash test measurement results"""
    pmax: float  # Maximum power (W)
    voc: float  # Open circuit voltage (V)
    isc: float  # Short circuit current (A)
    vmp: float  # Voltage at max power (V)
    imp: float  # Current at max power (A)
    fill_factor: float  # Fill factor
    efficiency: Optional[float] = None  # Module efficiency (%)
    irradiance: float = 1000.0  # Irradiance (W/m²)
    spectrum: str = "AM1.5G"  # Spectral distribution
    temperature: float = 25.0  # Cell temperature (°C)
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

        # Calculate fill factor if not provided
        if self.fill_factor == 0:
            self.fill_factor = (self.pmax) / (self.voc * self.isc) if (self.voc * self.isc) > 0 else 0


class SolarSimulator(BaseEquipment):
    """
    Solar Simulator for IV curve measurement and flash testing

    Simulates STC (Standard Test Conditions):
    - Irradiance: 1000 W/m²
    - Spectrum: AM1.5G
    - Cell temperature: 25°C
    """

    def __init__(self, equipment_id: str = "SIM-001", name: str = "Solar Simulator"):
        super().__init__(equipment_id, name)
        self._is_connected = False
        self._irradiance_setpoint = 1000.0  # W/m²
        self._temperature_setpoint = 25.0  # °C

    def connect(self) -> bool:
        """Connect to solar simulator"""
        try:
            # In real implementation, establish communication with actual equipment
            # e.g., SCPI commands, proprietary SDK, etc.
            self.logger.info(f"Connecting to {self.name} ({self.equipment_id})")
            self._is_connected = True
            self.log_event("connected")
            return True
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            self._is_connected = False
            return False

    def disconnect(self) -> bool:
        """Disconnect from solar simulator"""
        try:
            self.logger.info(f"Disconnecting from {self.name}")
            self._is_connected = False
            self.log_event("disconnected")
            return True
        except Exception as e:
            self.logger.error(f"Disconnection failed: {e}")
            return False

    def get_status(self) -> str:
        """Get simulator status"""
        if not self._is_connected:
            return "disconnected"
        return self.status

    def self_test(self) -> bool:
        """Perform simulator self-test"""
        try:
            self.logger.info("Performing self-test")
            # Verify lamp status, temperature, etc.
            self.log_event("self_test", {"result": "pass"})
            return True
        except Exception as e:
            self.logger.error(f"Self-test failed: {e}")
            return False

    def set_irradiance(self, irradiance: float = 1000.0):
        """Set irradiance level (W/m²)"""
        self._irradiance_setpoint = irradiance
        self.logger.info(f"Irradiance set to {irradiance} W/m²")

    def set_temperature(self, temperature: float = 25.0):
        """Set temperature setpoint (°C)"""
        self._temperature_setpoint = temperature
        self.logger.info(f"Temperature set to {temperature}°C")

    def stabilize(self, timeout: int = 300) -> bool:
        """
        Wait for lamp to stabilize

        Args:
            timeout: Maximum wait time in seconds

        Returns:
            bool: True if stabilized
        """
        self.logger.info("Waiting for lamp stabilization...")
        # In real implementation, monitor lamp current/voltage until stable
        self.log_event("stabilization_complete", {"duration_seconds": 60})
        return True

    def measure_iv_curve(self, module_id: str) -> FlashTestResult:
        """
        Perform flash test and measure IV curve

        Args:
            module_id: Module identifier

        Returns:
            FlashTestResult: Measurement results
        """
        if not self._is_connected:
            raise RuntimeError("Solar simulator not connected")

        self.logger.info(f"Performing flash test on module {module_id}")

        # In real implementation:
        # 1. Trigger flash
        # 2. Measure IV curve
        # 3. Extract parameters from curve
        # 4. Apply temperature correction if needed

        # Simulated measurements (replace with actual hardware interface)
        result = FlashTestResult(
            pmax=300.5,
            voc=45.2,
            isc=8.95,
            vmp=37.8,
            imp=7.95,
            fill_factor=0.0,  # Will be calculated
            irradiance=self._irradiance_setpoint,
            temperature=self._temperature_setpoint
        )

        self.log_event("flash_test_complete", {
            "module_id": module_id,
            "pmax": result.pmax,
            "voc": result.voc,
            "isc": result.isc
        })

        return result

    def get_measurement_data(self) -> Dict[str, Any]:
        """Get detailed measurement data including uncertainty"""
        return {
            "equipment_id": self.equipment_id,
            "irradiance": self._irradiance_setpoint,
            "temperature": self._temperature_setpoint,
            "uncertainty": {
                "pmax": self.get_measurement_uncertainty("pmax") or 0.02,  # ±2%
                "voc": self.get_measurement_uncertainty("voc") or 0.01,  # ±1%
                "isc": self.get_measurement_uncertainty("isc") or 0.02,  # ±2%
            }
        }
