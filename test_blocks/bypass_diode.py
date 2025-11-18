"""
Bypass Diode Test Block
IEC 61215 Compliant Bypass Diode Testing

Implements comprehensive bypass diode testing including:
- Forward voltage drop measurement
- Reverse leakage current test
- Thermal imaging during operation
- Shading response verification
- Multi-diode testing (typically 3 per module)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
import time

from .base import BaseTestModel, TestResult, TestStatus, Standard, TestMetadata


@dataclass
class DiodeCharacteristics:
    """Individual diode characteristics"""
    diode_index: int
    forward_voltage_at_currents: Dict[float, float]  # Current (A) -> Voltage (V)
    reverse_leakage_current_ua: float  # Leakage current at -15V (µA)
    thermal_temperature_c: float  # Operating temperature (°C)
    activation_voltage: float  # Voltage at which diode activates (V)
    activation_verified: bool
    pass_forward_vf: bool
    pass_reverse_leakage: bool
    pass_thermal: bool
    pass_activation: bool

    @property
    def overall_pass(self) -> bool:
        """Check if all diode tests passed"""
        return all([
            self.pass_forward_vf,
            self.pass_reverse_leakage,
            self.pass_thermal,
            self.pass_activation
        ])


@dataclass
class BypassDiodeResult:
    """
    Bypass diode test result model
    IEC 61215 compliance
    """
    test_id: int
    module_id: str
    diode_count: int
    forward_voltage: List[float]  # Forward voltage at rated current per diode
    reverse_leakage_ua: List[float]  # Reverse leakage current per diode (µA)
    activation_verified: bool  # All diodes activate correctly
    pass_status: bool  # Overall pass/fail

    # Extended characteristics
    diode_characteristics: List[DiodeCharacteristics] = field(default_factory=list)
    thermal_images: List[str] = field(default_factory=list)  # Thermal image file paths
    vi_curve_data: Dict[int, List[Tuple[float, float]]] = field(default_factory=dict)
    shading_response_time_ms: List[float] = field(default_factory=list)

    # Metadata
    test_timestamp: datetime = field(default_factory=datetime.now)
    test_duration_seconds: float = 0.0
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'test_id': self.test_id,
            'module_id': self.module_id,
            'diode_count': self.diode_count,
            'forward_voltage': self.forward_voltage,
            'reverse_leakage_ua': self.reverse_leakage_ua,
            'activation_verified': self.activation_verified,
            'pass_status': self.pass_status,
            'thermal_images': self.thermal_images,
            'shading_response_time_ms': self.shading_response_time_ms,
            'test_timestamp': self.test_timestamp.isoformat(),
            'test_duration_seconds': self.test_duration_seconds,
            'notes': self.notes,
            'diode_summary': [
                {
                    'diode_index': dc.diode_index,
                    'forward_voltage_at_rated': self.forward_voltage[dc.diode_index],
                    'reverse_leakage_ua': dc.reverse_leakage_current_ua,
                    'thermal_temp_c': dc.thermal_temperature_c,
                    'activation_verified': dc.activation_verified,
                    'overall_pass': dc.overall_pass
                }
                for dc in self.diode_characteristics
            ]
        }


class BypassDiodeTest(BaseTestModel):
    """
    Bypass Diode Test Implementation

    Per IEC 61215 standards for bypass diode testing:
    - Forward V-I curve (0-10A)
    - Reverse bias test (-15V)
    - Thermal performance under load
    - Shading activation test

    Typical PV modules have 3 bypass diodes
    """

    # IEC 61215 Specifications
    MAX_FORWARD_VOLTAGE_AT_RATED = 1.2  # V at rated current
    MAX_REVERSE_LEAKAGE_UA = 100.0  # µA at -15V
    MAX_OPERATING_TEMP_C = 85.0  # °C
    MAX_ACTIVATION_VOLTAGE = 0.7  # V (typical for silicon diode)
    RATED_CURRENT_A = 8.0  # A (typical for bypass diode)

    def __init__(self, module: str, test_id: int = 1, diode_count: int = 3,
                 operator: Optional[str] = None):
        """
        Initialize bypass diode test

        Args:
            module: Module identifier (e.g., "PV-001")
            test_id: Unique test identifier
            diode_count: Number of bypass diodes in module (default: 3)
            operator: Test operator name
        """
        super().__init__(module_id=module, test_id=test_id, operator=operator)
        self.diode_count = diode_count
        self.metadata.standards.append(Standard.IEC_61215)

        # Test configuration
        self.forward_test_currents = [1.0, 2.0, 4.0, 6.0, 8.0, 10.0]  # A
        self.reverse_test_voltage = -15.0  # V
        self.thermal_load_current = self.RATED_CURRENT_A  # A
        self.thermal_duration_seconds = 60  # Duration for thermal test

        # Results storage
        self.diode_results: List[DiodeCharacteristics] = []

    def measure_forward_vi_curve(self, diode_index: int) -> Dict[float, float]:
        """
        Measure forward V-I characteristic curve

        Args:
            diode_index: Index of diode being tested (0-based)

        Returns:
            Dictionary mapping current (A) to voltage (V)
        """
        print(f"  Measuring forward V-I curve for diode {diode_index + 1}...")
        vi_data = {}

        for current in self.forward_test_currents:
            # Simulate forward voltage measurement
            # Real implementation would interface with equipment
            # Vf ≈ 0.4V + (0.08V per amp) for silicon diode
            voltage = 0.4 + (current * 0.08) + (diode_index * 0.01)  # Small variation per diode
            vi_data[current] = round(voltage, 3)

            # In real implementation:
            # voltage = self.sourcemeter.measure_voltage(current)

        print(f"    V-I curve: {len(vi_data)} points measured")
        return vi_data

    def measure_reverse_leakage(self, diode_index: int) -> float:
        """
        Measure reverse leakage current at -15V

        Args:
            diode_index: Index of diode being tested

        Returns:
            Leakage current in microamperes (µA)
        """
        print(f"  Measuring reverse leakage for diode {diode_index + 1}...")

        # Simulate reverse leakage measurement
        # Real implementation would apply -15V and measure leakage
        # Good diodes: < 10 µA, acceptable: < 100 µA
        leakage_ua = 5.0 + (diode_index * 2.0)  # Simulated

        # In real implementation:
        # self.sourcemeter.set_voltage(self.reverse_test_voltage)
        # leakage_current_a = self.sourcemeter.measure_current()
        # leakage_ua = abs(leakage_current_a * 1e6)

        print(f"    Reverse leakage: {leakage_ua:.2f} µA")
        return round(leakage_ua, 2)

    def measure_thermal_performance(self, diode_index: int) -> float:
        """
        Measure thermal performance under load

        Args:
            diode_index: Index of diode being tested

        Returns:
            Operating temperature in °C
        """
        print(f"  Measuring thermal performance for diode {diode_index + 1}...")
        print(f"    Applying {self.thermal_load_current}A for {self.thermal_duration_seconds}s...")

        # Simulate thermal measurement
        # Real implementation would use thermal camera or thermocouple
        # Temperature rise depends on power dissipation and thermal resistance
        start_time = time.time()

        # Simulate load application
        time.sleep(0.1)  # Brief delay for simulation

        # Typical temperature: 40-70°C under load
        temperature_c = 55.0 + (diode_index * 3.0)

        elapsed = time.time() - start_time

        # In real implementation:
        # self.sourcemeter.set_current(self.thermal_load_current)
        # time.sleep(self.thermal_duration_seconds)
        # temperature_c = self.thermal_camera.measure_temperature(diode_position)

        print(f"    Operating temperature: {temperature_c:.1f}°C")
        return round(temperature_c, 1)

    def test_shading_activation(self, diode_index: int) -> Tuple[bool, float, float]:
        """
        Test bypass diode activation under shading conditions

        Args:
            diode_index: Index of diode being tested

        Returns:
            Tuple of (activation_verified, activation_voltage, response_time_ms)
        """
        print(f"  Testing shading activation for diode {diode_index + 1}...")

        # Simulate shading condition
        # Real implementation would shade portion of module and monitor
        # diode activation

        # Measure activation voltage (forward voltage at which diode conducts)
        activation_voltage = 0.6 + (diode_index * 0.02)  # Typical 0.6-0.7V

        # Measure response time (time for diode to activate after shading)
        response_time_ms = 50.0 + (diode_index * 10.0)  # Typical < 100ms

        # Verify activation occurred
        activation_verified = (activation_voltage < self.MAX_ACTIVATION_VOLTAGE and
                             response_time_ms < 200.0)

        # In real implementation:
        # self.shading_simulator.apply_shade(diode_index)
        # start_time = time.time()
        # activation_voltage = self.monitor.wait_for_activation()
        # response_time_ms = (time.time() - start_time) * 1000
        # activation_verified = self.verify_current_bypass()

        status = "PASS" if activation_verified else "FAIL"
        print(f"    Activation: {status} (Vf={activation_voltage:.3f}V, t={response_time_ms:.1f}ms)")
        return activation_verified, round(activation_voltage, 3), round(response_time_ms, 1)

    def test_single_diode(self, diode_index: int) -> DiodeCharacteristics:
        """
        Perform complete test sequence on single diode

        Args:
            diode_index: Index of diode to test (0-based)

        Returns:
            DiodeCharacteristics object with all test results
        """
        print(f"\nTesting diode {diode_index + 1}/{self.diode_count}:")

        # 1. Forward V-I curve
        vi_data = self.measure_forward_vi_curve(diode_index)
        forward_voltage_at_rated = vi_data.get(self.RATED_CURRENT_A, 0.0)
        pass_forward = forward_voltage_at_rated <= self.MAX_FORWARD_VOLTAGE_AT_RATED

        # 2. Reverse leakage
        reverse_leakage = self.measure_reverse_leakage(diode_index)
        pass_reverse = reverse_leakage <= self.MAX_REVERSE_LEAKAGE_UA

        # 3. Thermal performance
        temperature = self.measure_thermal_performance(diode_index)
        pass_thermal = temperature <= self.MAX_OPERATING_TEMP_C

        # 4. Shading activation
        activation_verified, activation_voltage, response_time = self.test_shading_activation(diode_index)
        pass_activation = activation_verified

        # Create characteristics object
        characteristics = DiodeCharacteristics(
            diode_index=diode_index,
            forward_voltage_at_currents=vi_data,
            reverse_leakage_current_ua=reverse_leakage,
            thermal_temperature_c=temperature,
            activation_voltage=activation_voltage,
            activation_verified=activation_verified,
            pass_forward_vf=pass_forward,
            pass_reverse_leakage=pass_reverse,
            pass_thermal=pass_thermal,
            pass_activation=pass_activation
        )

        # Print summary
        overall_status = "PASS" if characteristics.overall_pass else "FAIL"
        print(f"  Diode {diode_index + 1} overall: {overall_status}")

        return characteristics

    def test_all_diodes(self) -> BypassDiodeResult:
        """
        Test all bypass diodes in the module

        Returns:
            BypassDiodeResult with complete test results
        """
        print(f"\n{'='*60}")
        print(f"BYPASS DIODE TEST - Module {self.module_id}")
        print(f"IEC 61215 Compliance Test")
        print(f"Diodes to test: {self.diode_count}")
        print(f"{'='*60}")

        start_time = time.time()
        self.diode_results = []

        # Test each diode
        for i in range(self.diode_count):
            diode_char = self.test_single_diode(i)
            self.diode_results.append(diode_char)

        # Compile results
        forward_voltages = [dc.forward_voltage_at_currents.get(self.RATED_CURRENT_A, 0.0)
                           for dc in self.diode_results]
        reverse_leakages = [dc.reverse_leakage_current_ua for dc in self.diode_results]
        all_activated = all(dc.activation_verified for dc in self.diode_results)
        all_passed = all(dc.overall_pass for dc in self.diode_results)

        response_times = []
        vi_curves = {}
        for i, dc in enumerate(self.diode_results):
            # Extract response time from activation test
            response_times.append(50.0 + (i * 10.0))  # Simulated values
            vi_curves[i] = [(current, voltage)
                           for current, voltage in dc.forward_voltage_at_currents.items()]

        duration = time.time() - start_time

        # Create result object
        result = BypassDiodeResult(
            test_id=self.test_id,
            module_id=self.module_id,
            diode_count=self.diode_count,
            forward_voltage=forward_voltages,
            reverse_leakage_ua=reverse_leakages,
            activation_verified=all_activated,
            pass_status=all_passed,
            diode_characteristics=self.diode_results,
            thermal_images=[],  # Populated in real implementation
            vi_curve_data=vi_curves,
            shading_response_time_ms=response_times,
            test_duration_seconds=round(duration, 2)
        )

        # Print summary
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Module: {self.module_id}")
        print(f"Diodes tested: {self.diode_count}")
        print(f"All activated: {all_activated}")
        print(f"Overall status: {'PASS' if all_passed else 'FAIL'}")
        print(f"Test duration: {duration:.2f}s")
        print(f"\nForward voltages @ {self.RATED_CURRENT_A}A:")
        for i, vf in enumerate(forward_voltages):
            status = "PASS" if vf <= self.MAX_FORWARD_VOLTAGE_AT_RATED else "FAIL"
            print(f"  Diode {i+1}: {vf:.3f}V ({status})")
        print(f"\nReverse leakage @ -15V:")
        for i, leak in enumerate(reverse_leakages):
            status = "PASS" if leak <= self.MAX_REVERSE_LEAKAGE_UA else "FAIL"
            print(f"  Diode {i+1}: {leak:.2f}µA ({status})")
        print(f"{'='*60}\n")

        return result

    def export_results(self, result: BypassDiodeResult, format: str = 'json') -> str:
        """
        Export test results to specified format

        Args:
            result: Test result to export
            format: Export format ('json', 'csv', 'pdf')

        Returns:
            Exported data as string or file path
        """
        if format == 'json':
            import json
            return json.dumps(result.to_dict(), indent=2)
        elif format == 'csv':
            # CSV export implementation
            csv_data = "Diode,Forward_V,Reverse_Leakage_uA,Thermal_Temp_C,Activation,Pass\n"
            for dc in result.diode_characteristics:
                vf = result.forward_voltage[dc.diode_index]
                csv_data += f"{dc.diode_index+1},{vf},{dc.reverse_leakage_current_ua},"
                csv_data += f"{dc.thermal_temperature_c},{dc.activation_verified},{dc.overall_pass}\n"
            return csv_data
        else:
            raise ValueError(f"Unsupported export format: {format}")
