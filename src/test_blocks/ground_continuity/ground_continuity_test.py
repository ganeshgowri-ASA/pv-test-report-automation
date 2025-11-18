"""
Ground Continuity Test Implementation per IEC 61730.

This module implements ground continuity testing for photovoltaic modules
in accordance with IEC 61730 safety qualification standards.

Test Specifications:
- Test current: 25A DC for 60 seconds
- Maximum acceptable resistance: 0.1 Ohm
- Measurement method: 4-wire Kelvin measurement
- Multiple measurement points required
- ISO 17025 compliant measurement uncertainty tracking
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import Field, validator
from enum import Enum

from ..base import (
    BaseTestBlock,
    TestResult,
    TestStatus,
    MeasurementUncertainty,
    EnvironmentalConditions,
    Equipment,
)


class MeasurementPoint(str, Enum):
    """Standard measurement points for ground continuity testing."""
    FRAME_TO_GROUND = "frame_to_ground"
    FRAME_TO_TERMINAL = "frame_to_terminal"
    MOUNTING_HOLE_1 = "mounting_hole_1"
    MOUNTING_HOLE_2 = "mounting_hole_2"
    MOUNTING_HOLE_3 = "mounting_hole_3"
    MOUNTING_HOLE_4 = "mounting_hole_4"
    J_BOX_TO_FRAME = "junction_box_to_frame"


class WireConfiguration(Enum):
    """Wire configuration for measurement."""
    TWO_WIRE = "2-wire"
    FOUR_WIRE_KELVIN = "4-wire-kelvin"


class GroundContinuityMeasurement(TestResult):
    """Individual ground continuity measurement result."""
    measurement_point: str = Field(..., description="Location of measurement")
    test_current_amps: float = Field(..., description="Applied test current in Amps")
    measured_resistance: MeasurementUncertainty = Field(..., description="Measured resistance with uncertainty")
    test_duration_seconds: float = Field(..., description="Duration of current application")
    voltage_drop_mv: Optional[float] = Field(None, description="Measured voltage drop in millivolts")
    wire_configuration: WireConfiguration = Field(
        default=WireConfiguration.FOUR_WIRE_KELVIN,
        description="Measurement wire configuration"
    )
    temperature_rise_celsius: Optional[float] = Field(
        None,
        description="Temperature rise during test"
    )

    @validator('test_current_amps')
    def validate_test_current(cls, v):
        if v < 0:
            raise ValueError('Test current must be positive')
        if v > 50:
            raise ValueError('Test current exceeds safety limit of 50A')
        return v

    @validator('measured_resistance')
    def validate_resistance(cls, v):
        if v.value < 0:
            raise ValueError('Resistance cannot be negative')
        return v


class GroundContinuityTest(BaseTestBlock):
    """
    Ground Continuity Test Block per IEC 61730.

    This test verifies electrical continuity between the module frame
    and grounding points to ensure safety under fault conditions.

    Attributes:
        test_current: Test current in Amps (default 25.0A per IEC 61730)
        test_duration: Duration of current application in seconds (default 60s)
        max_resistance_ohm: Maximum acceptable resistance (default 0.1Ω)
        measurement_points: List of points to measure
        wire_configuration: Measurement method (4-wire Kelvin recommended)
    """

    # Test parameters per IEC 61730
    test_current: float = Field(
        default=25.0,
        description="Test current in Amps (IEC 61730 requirement)"
    )
    test_duration: float = Field(
        default=60.0,
        description="Duration of test current application in seconds"
    )
    max_resistance_ohm: float = Field(
        default=0.1,
        description="Maximum acceptable resistance in Ohms"
    )
    measurement_points: List[str] = Field(
        default_factory=lambda: [
            MeasurementPoint.FRAME_TO_GROUND.value,
            MeasurementPoint.FRAME_TO_TERMINAL.value,
            MeasurementPoint.J_BOX_TO_FRAME.value,
        ],
        description="List of measurement points to test"
    )
    wire_configuration: WireConfiguration = Field(
        default=WireConfiguration.FOUR_WIRE_KELVIN,
        description="Wire configuration for measurement"
    )

    # Test results
    measurements: List[GroundContinuityMeasurement] = Field(
        default_factory=list,
        description="List of measurements performed"
    )
    overall_pass_status: Optional[bool] = Field(
        None,
        description="Overall test pass/fail status"
    )

    # Safety parameters
    max_temperature_rise: float = Field(
        default=50.0,
        description="Maximum acceptable temperature rise in Celsius"
    )
    emergency_current_limit: float = Field(
        default=30.0,
        description="Emergency current limit in Amps"
    )

    standard: str = Field(
        default="IEC 61730",
        description="Test standard"
    )

    class Config:
        use_enum_values = True

    @validator('test_current')
    def validate_test_current(cls, v):
        if v <= 0:
            raise ValueError('Test current must be positive')
        if v > 50:
            raise ValueError('Test current exceeds maximum safe limit of 50A')
        if v < 10:
            raise ValueError('Test current below minimum requirement of 10A for IEC 61730')
        return v

    @validator('test_duration')
    def validate_test_duration(cls, v):
        if v < 30:
            raise ValueError('Test duration must be at least 30 seconds per IEC 61730')
        if v > 300:
            raise ValueError('Test duration exceeds maximum of 300 seconds')
        return v

    @validator('max_resistance_ohm')
    def validate_max_resistance(cls, v):
        if v <= 0:
            raise ValueError('Maximum resistance must be positive')
        if v > 1.0:
            raise ValueError('Maximum resistance threshold too high (should be ≤ 0.1Ω per IEC 61730)')
        return v

    def validate_test_conditions(self) -> bool:
        """
        Validate test conditions before starting.

        Returns:
            bool: True if conditions are valid
        """
        # Check environmental conditions if provided
        if self.environmental_conditions:
            temp = self.environmental_conditions.temperature_celsius
            humidity = self.environmental_conditions.humidity_percent

            if temp is not None:
                if temp < 15 or temp > 35:
                    raise ValueError(
                        f'Ambient temperature {temp}°C outside acceptable range (15-35°C)'
                    )

            if humidity is not None:
                if humidity < 20 or humidity > 80:
                    raise ValueError(
                        f'Relative humidity {humidity}% outside acceptable range (20-80%)'
                    )

        # Validate measurement points
        if not self.measurement_points:
            raise ValueError('At least one measurement point must be specified')

        # Validate wire configuration
        if self.wire_configuration != WireConfiguration.FOUR_WIRE_KELVIN:
            print(
                "WARNING: 4-wire Kelvin measurement recommended for accuracy. "
                f"Current configuration: {self.wire_configuration.value}"
            )

        return True

    def pre_test_safety_check(self) -> bool:
        """
        Perform pre-test safety checks.

        Returns:
            bool: True if safe to proceed
        """
        safety_checks = {
            "Test current within limits": self.test_current <= self.emergency_current_limit,
            "Test duration valid": 30 <= self.test_duration <= 300,
            "Resistance threshold valid": self.max_resistance_ohm <= 1.0,
            "Measurement points defined": len(self.measurement_points) > 0,
        }

        failed_checks = [check for check, passed in safety_checks.items() if not passed]

        if failed_checks:
            print("SAFETY CHECK FAILED:")
            for check in failed_checks:
                print(f"  - {check}")
            return False

        print("Pre-test safety checks: PASSED")
        return True

    def perform_measurement(
        self,
        measurement_point: Optional[str] = None,
        simulated: bool = True,
        simulated_resistance: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Perform ground continuity measurement.

        Args:
            measurement_point: Specific point to measure (if None, measures all points)
            simulated: If True, returns simulated data (for testing/development)
            simulated_resistance: Resistance value for simulation

        Returns:
            Dict containing measurement results
        """
        if measurement_point:
            points_to_measure = [measurement_point]
        else:
            points_to_measure = self.measurement_points

        measurements = []

        for point in points_to_measure:
            print(f"\nMeasuring: {point}")
            print(f"  Configuration: {self.wire_configuration.value}")
            print(f"  Test current: {self.test_current}A")
            print(f"  Test duration: {self.test_duration}s")

            if simulated:
                # Simulate measurement
                result = self._simulate_measurement(point, simulated_resistance)
            else:
                # Real measurement (would interface with actual equipment)
                result = self._perform_real_measurement(point)

            measurements.append(result)

        return {
            "measurements": measurements,
            "total_points": len(measurements),
            "test_current": self.test_current,
            "wire_configuration": self.wire_configuration.value,
        }

    def _simulate_measurement(
        self,
        point: str,
        simulated_resistance: Optional[float] = None
    ) -> GroundContinuityMeasurement:
        """
        Simulate a measurement for testing purposes.

        Args:
            point: Measurement point
            simulated_resistance: Override resistance value

        Returns:
            GroundContinuityMeasurement object
        """
        import random

        # Simulate measurement delay
        time.sleep(0.1)

        # Generate realistic resistance value
        if simulated_resistance is not None:
            base_resistance = simulated_resistance
        else:
            # Typical values: 0.01-0.15 Ohm
            base_resistance = random.uniform(0.01, 0.15)

        # Add measurement uncertainty (typical ±2-5%)
        uncertainty = base_resistance * 0.03

        # Calculate voltage drop (V = I × R)
        voltage_drop_mv = self.test_current * base_resistance * 1000  # Convert to mV

        # Simulate temperature rise (more current = more heating)
        temp_rise = (self.test_current / 25.0) * random.uniform(5, 15)

        measurement = GroundContinuityMeasurement(
            test_id=f"{self.test_id}-{point}",
            test_name=f"Ground Continuity - {point}",
            standard=self.standard,
            operator=self.operator,
            measurement_point=point,
            test_current_amps=self.test_current,
            measured_resistance=MeasurementUncertainty(
                value=base_resistance,
                uncertainty=uncertainty,
                confidence_level=0.95,
                unit="Ohm"
            ),
            test_duration_seconds=self.test_duration,
            voltage_drop_mv=voltage_drop_mv,
            wire_configuration=self.wire_configuration,
            temperature_rise_celsius=temp_rise,
            environmental_conditions=self.environmental_conditions,
            status=TestStatus.PASSED if base_resistance <= self.max_resistance_ohm else TestStatus.FAILED,
            end_time=datetime.now()
        )

        # Store measurement
        self.measurements.append(measurement)

        return measurement

    def _perform_real_measurement(self, point: str) -> GroundContinuityMeasurement:
        """
        Perform real measurement using test equipment.

        This method would interface with actual ground continuity test equipment
        via appropriate communication protocols (SCPI, Modbus, etc.).

        Args:
            point: Measurement point

        Returns:
            GroundContinuityMeasurement object
        """
        raise NotImplementedError(
            "Real measurement interface not implemented. "
            "Use simulated=True for development/testing."
        )

    def evaluate_pass_fail(self, measurement: Dict[str, Any]) -> bool:
        """
        Evaluate pass/fail criteria for measurements.

        Per IEC 61730: All measurement points must have resistance ≤ max_resistance_ohm

        Args:
            measurement: Dictionary containing measurement results

        Returns:
            bool: True if all measurements pass
        """
        measurements = measurement.get("measurements", [])

        if not measurements:
            return False

        all_passed = True

        for m in measurements:
            resistance = m.measured_resistance.value
            passed = resistance <= self.max_resistance_ohm

            status_symbol = "✓" if passed else "✗"
            print(
                f"{status_symbol} {m.measurement_point}: "
                f"{resistance:.4f} ± {m.measured_resistance.uncertainty:.4f} Ω "
                f"(limit: {self.max_resistance_ohm} Ω)"
            )

            if not passed:
                all_passed = False

            # Check temperature rise
            if m.temperature_rise_celsius and m.temperature_rise_celsius > self.max_temperature_rise:
                print(
                    f"  WARNING: Temperature rise {m.temperature_rise_celsius:.1f}°C "
                    f"exceeds limit of {self.max_temperature_rise}°C"
                )
                all_passed = False

        self.overall_pass_status = all_passed
        return all_passed

    def post_test_safety_check(self) -> bool:
        """
        Perform post-test safety checks.

        Returns:
            bool: True if safe
        """
        # Check for excessive temperature rise
        max_temp_rise = max(
            (m.temperature_rise_celsius for m in self.measurements if m.temperature_rise_celsius),
            default=0
        )

        if max_temp_rise > self.max_temperature_rise:
            print(
                f"WARNING: Maximum temperature rise {max_temp_rise:.1f}°C "
                f"exceeds safety limit of {self.max_temperature_rise}°C"
            )
            return False

        print("Post-test safety checks: PASSED")
        return True

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive test report.

        Returns:
            Dict containing complete test report data
        """
        if not self.measurements:
            raise ValueError("No measurements available for report generation")

        # Calculate statistics
        resistances = [m.measured_resistance.value for m in self.measurements]
        avg_resistance = sum(resistances) / len(resistances)
        max_measured_resistance = max(resistances)
        min_measured_resistance = min(resistances)

        report = {
            "test_information": {
                "test_id": self.test_id,
                "module_id": self.module_id,
                "standard": self.standard,
                "operator": self.operator,
                "test_date": datetime.now().isoformat(),
            },
            "test_parameters": {
                "test_current_amps": self.test_current,
                "test_duration_seconds": self.test_duration,
                "max_resistance_threshold_ohm": self.max_resistance_ohm,
                "wire_configuration": self.wire_configuration.value,
                "measurement_points": self.measurement_points,
            },
            "environmental_conditions": (
                self.environmental_conditions.dict() if self.environmental_conditions else None
            ),
            "measurements": [
                {
                    "point": m.measurement_point,
                    "resistance_ohm": m.measured_resistance.value,
                    "uncertainty_ohm": m.measured_resistance.uncertainty,
                    "voltage_drop_mv": m.voltage_drop_mv,
                    "temperature_rise_celsius": m.temperature_rise_celsius,
                    "status": m.status.value,
                }
                for m in self.measurements
            ],
            "statistics": {
                "total_points_measured": len(self.measurements),
                "average_resistance_ohm": avg_resistance,
                "min_resistance_ohm": min_measured_resistance,
                "max_resistance_ohm": max_measured_resistance,
            },
            "result": {
                "overall_status": "PASSED" if self.overall_pass_status else "FAILED",
                "pass_status": self.overall_pass_status,
                "all_points_within_limit": all(
                    m.measured_resistance.value <= self.max_resistance_ohm
                    for m in self.measurements
                ),
            },
            "iso_17025_compliance": {
                "measurement_uncertainty_reported": True,
                "environmental_conditions_recorded": self.environmental_conditions is not None,
                "traceability": "Measurements performed per IEC 61730",
            },
        }

        return report

    def run_test(
        self,
        simulated: bool = True,
        simulated_resistance: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute complete test sequence.

        Args:
            simulated: Use simulated measurements
            simulated_resistance: Override resistance for simulation

        Returns:
            Dict containing complete test results
        """
        print(f"\n{'='*60}")
        print(f"Ground Continuity Test - {self.test_id}")
        print(f"Module: {self.module_id}")
        print(f"Standard: {self.standard}")
        print(f"{'='*60}\n")

        # Step 1: Validate conditions
        print("Step 1: Validating test conditions...")
        self.validate_test_conditions()
        print("  ✓ Test conditions valid\n")

        # Step 2: Pre-test safety check
        print("Step 2: Pre-test safety check...")
        if not self.pre_test_safety_check():
            raise RuntimeError("Pre-test safety check failed. Test aborted.")
        print()

        # Step 3: Perform measurements
        print("Step 3: Performing measurements...")
        measurement_results = self.perform_measurement(
            simulated=simulated,
            simulated_resistance=simulated_resistance
        )
        print()

        # Step 4: Evaluate results
        print("Step 4: Evaluating pass/fail criteria...")
        pass_status = self.evaluate_pass_fail(measurement_results)
        print()

        # Step 5: Post-test safety check
        print("Step 5: Post-test safety check...")
        self.post_test_safety_check()
        print()

        # Step 6: Generate report
        print("Step 6: Generating report...")
        report = self.generate_report()
        print("  ✓ Report generated\n")

        print(f"{'='*60}")
        print(f"TEST RESULT: {'PASSED' if pass_status else 'FAILED'}")
        print(f"{'='*60}\n")

        return report
