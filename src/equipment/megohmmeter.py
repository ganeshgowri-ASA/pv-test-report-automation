"""Megohmmeter (Insulation Tester) interface"""

import time
from typing import Optional, Literal
from datetime import datetime, timedelta
import random

from .base import BaseInstrument, InstrumentInfo


class Megohmmeter(BaseInstrument):
    """Interface for Megohmmeter (Insulation Resistance Tester)

    Supports both real instruments via VISA/Serial and simulated mode.
    Common instruments: Fluke 1550C, Megger MIT1025, Hioki IR4056
    """

    def __init__(
        self,
        instrument_info: InstrumentInfo,
        connection_string: Optional[str] = None,
        timeout: int = 5000
    ):
        super().__init__(instrument_info)
        self.connection_string = connection_string
        self.timeout = timeout
        self.instrument = None

    def connect(self) -> bool:
        """Connect to megohmmeter"""
        try:
            if self.connection_string:
                # Real instrument connection (requires pyvisa)
                try:
                    import pyvisa
                    rm = pyvisa.ResourceManager()
                    self.instrument = rm.open_resource(self.connection_string)
                    self.instrument.timeout = self.timeout
                    self.connected = True
                    return True
                except Exception as e:
                    print(f"Failed to connect to instrument: {e}")
                    return False
            else:
                # Simulated mode
                self.connected = True
                return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def disconnect(self) -> bool:
        """Disconnect from megohmmeter"""
        try:
            if self.instrument:
                self.instrument.close()
            self.connected = False
            return True
        except Exception:
            return False

    def reset(self) -> bool:
        """Reset instrument to default state"""
        if not self.connected:
            return False
        try:
            if self.instrument:
                self.instrument.write("*RST")
            return True
        except Exception:
            return False

    def self_test(self) -> bool:
        """Perform instrument self-test"""
        if not self.connected:
            return False
        try:
            if self.instrument:
                response = self.instrument.query("*TST?")
                return response.strip() == "0"
            return True  # Simulated mode
        except Exception:
            return False

    def set_test_voltage(self, voltage: Literal[500, 1000]) -> bool:
        """Set test voltage (500V or 1000V)"""
        if not self.connected:
            return False
        if voltage not in [500, 1000]:
            raise ValueError("Test voltage must be 500V or 1000V")
        try:
            if self.instrument:
                self.instrument.write(f"VOLT {voltage}")
            return True
        except Exception:
            return False

    def measure_resistance(
        self,
        test_voltage: Literal[500, 1000],
        measurement_time: int = 60,
        polarity: Literal["positive", "negative"] = "positive"
    ) -> Optional[float]:
        """
        Measure insulation resistance

        Args:
            test_voltage: Test voltage (500V or 1000V)
            measurement_time: Measurement duration in seconds (default 60s per IEC standard)
            polarity: Test polarity

        Returns:
            Resistance in MΩ, or None if measurement failed
        """
        if not self.connected:
            return None

        try:
            # Set test voltage
            self.set_test_voltage(test_voltage)

            if self.instrument:
                # Real instrument measurement
                self.instrument.write(f"MEAS:RES? {measurement_time}")
                time.sleep(measurement_time + 2)  # Wait for measurement
                response = self.instrument.query("FETCH?")
                resistance_ohms = float(response)
                resistance_mohms = resistance_ohms / 1e6
            else:
                # Simulated measurement
                time.sleep(1)  # Simulate measurement time (shortened for testing)
                # Simulate realistic values based on condition
                # Typical values: 50-100 MΩ (wet), 500-1000 MΩ (dry)
                base_resistance = random.uniform(50, 100)  # Will be adjusted by caller
                resistance_mohms = base_resistance

            return resistance_mohms

        except Exception as e:
            print(f"Measurement error: {e}")
            return None


class MegohmeterSimulator(Megohmmeter):
    """Simulated megohmmeter for testing without hardware"""

    def __init__(self, instrument_id: str = "SIM-MEG-001"):
        info = InstrumentInfo(
            instrument_id=instrument_id,
            manufacturer="Simulated",
            model="Virtual Megohmmeter",
            serial_number="SIM-12345",
            calibration_date=datetime.utcnow() - timedelta(days=180),
            calibration_due_date=datetime.utcnow() + timedelta(days=185),
            calibration_certificate="SIM-CERT-2024-001",
            uncertainty={"resistance": 2.0}  # 2% uncertainty
        )
        super().__init__(info, connection_string=None)

    def measure_resistance(
        self,
        test_voltage: Literal[500, 1000],
        measurement_time: int = 60,
        polarity: Literal["positive", "negative"] = "positive"
    ) -> Optional[float]:
        """
        Simulate resistance measurement with realistic values

        Returns values appropriate for wet/dry conditions:
        - Wet condition: 50-150 MΩ (above 40 MΩ minimum)
        - Dry condition: 450-900 MΩ (above 400 MΩ minimum)
        """
        if not self.connected:
            return None

        # Simulate measurement time (shortened for testing)
        time.sleep(0.1)

        # Generate realistic simulated values
        # Add slight voltage dependence (higher voltage -> slightly higher reading)
        voltage_factor = 1.0 if test_voltage == 500 else 1.05

        # Simulate both passing and occasional edge cases
        rand = random.random()
        if rand < 0.7:  # 70% dry condition (high resistance)
            base_resistance = random.uniform(450, 900)
        elif rand < 0.95:  # 25% wet condition (lower but passing)
            base_resistance = random.uniform(50, 150)
        else:  # 5% edge cases (near limits)
            base_resistance = random.choice([
                random.uniform(40, 50),   # Just passing wet
                random.uniform(380, 420)  # Near dry limit
            ])

        resistance = base_resistance * voltage_factor

        # Add measurement noise (±1%)
        noise = random.uniform(-0.01, 0.01) * resistance
        resistance += noise

        return round(resistance, 2)
