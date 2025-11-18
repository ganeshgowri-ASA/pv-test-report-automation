"""Mechanical Load Test Block - IEC 61215 Compliance.

This module implements static and dynamic mechanical load testing for PV modules
according to IEC 61215 standards. It includes deflection monitoring, power
degradation analysis, and comprehensive ISO 17025 traceability.

Test Requirements:
- Static Load: 2400 Pa (front), 2400 Pa (rear)
- Dynamic Load: 1000 cycles at ±1000 Pa
- Pass Criteria: <5% power degradation
- Deflection monitoring during test
- Pre/post flash measurements (IV curve)
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
from pydantic import Field, field_validator

from ...models.base import BaseModel
from ..base_test_block import BaseTestBlock, TestStandard, TestStatus


class LoadType(str, Enum):
    """Type of mechanical load test."""

    STATIC_FRONT = "static_front"
    STATIC_REAR = "static_rear"
    DYNAMIC = "dynamic"


class LoadSurface(str, Enum):
    """Surface on which load is applied."""

    FRONT = "front"
    REAR = "rear"
    BOTH = "both"


class DeflectionMeasurement(BaseModel):
    """Individual deflection measurement during load test.

    Attributes:
        timestamp: When the measurement was taken
        load_pa: Applied load in Pascals
        deflection_mm: Measured deflection in millimeters
        position: Measurement position (center, edge, corner)
        cycle_number: Cycle number for dynamic tests
    """

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the measurement was taken"
    )
    load_pa: float = Field(..., description="Applied load in Pascals")
    deflection_mm: float = Field(..., description="Measured deflection in millimeters")
    position: str = Field(
        default="center",
        description="Measurement position (center, edge, corner)"
    )
    cycle_number: Optional[int] = Field(
        default=None,
        description="Cycle number for dynamic tests"
    )


class PowerMeasurement(BaseModel):
    """Power measurement from IV curve (flash test).

    Attributes:
        timestamp: When the measurement was taken
        pmax_w: Maximum power in Watts
        voc_v: Open circuit voltage in Volts
        isc_a: Short circuit current in Amps
        vmp_v: Voltage at maximum power point in Volts
        imp_a: Current at maximum power point in Amps
        fill_factor: Fill factor (Pmax / (Voc * Isc))
        irradiance_wm2: Irradiance during measurement
        temperature_c: Module temperature during measurement
    """

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the measurement was taken"
    )
    pmax_w: float = Field(..., description="Maximum power in Watts", gt=0)
    voc_v: float = Field(..., description="Open circuit voltage in Volts", gt=0)
    isc_a: float = Field(..., description="Short circuit current in Amps", gt=0)
    vmp_v: float = Field(..., description="Voltage at maximum power point in Volts", gt=0)
    imp_a: float = Field(..., description="Current at maximum power point in Amps", gt=0)
    fill_factor: float = Field(
        ...,
        description="Fill factor (Pmax / (Voc * Isc))",
        ge=0,
        le=1
    )
    irradiance_wm2: float = Field(
        default=1000.0,
        description="Irradiance during measurement in W/m²"
    )
    temperature_c: float = Field(
        default=25.0,
        description="Module temperature during measurement in °C"
    )


class MechanicalLoadTest(BaseTestBlock):
    """IEC 61215 Mechanical Load Test Block.

    Implements comprehensive mechanical load testing with both static and
    dynamic modes, including deflection monitoring and power degradation analysis.

    The test evaluates the module's ability to withstand mechanical loads from
    wind and snow according to IEC 61215 requirements.

    Attributes:
        load_type: Type of load test (static_front, static_rear, dynamic)
        load_pa: Applied load in Pascals
        cycles: Number of cycles for dynamic tests (default: 1000)
        max_deflection_mm: Maximum measured deflection
        power_degradation_pct: Power degradation percentage
        pass_status: Whether the test passed (<5% degradation)
        deflection_measurements: List of deflection measurements
        pre_test_power: Power measurement before test
        post_test_power: Power measurement after test
        load_surface: Surface where load is applied
        pressure_uniformity_pct: Uniformity of applied pressure
    """

    # Override test identification
    test_name: str = Field(
        default="Mechanical Load Test",
        description="Human-readable name of the test"
    )
    test_standard: TestStandard = Field(
        default=TestStandard.IEC_61215,
        description="Applicable testing standard"
    )

    # Test parameters
    load_type: LoadType = Field(
        ...,
        description="Type of load test (static_front, static_rear, dynamic)"
    )
    load_pa: float = Field(
        ...,
        description="Applied load in Pascals",
        gt=0
    )
    load_surface: LoadSurface = Field(
        default=LoadSurface.FRONT,
        description="Surface where load is applied"
    )
    cycles: Optional[int] = Field(
        default=None,
        description="Number of cycles for dynamic tests (typically 1000)",
        ge=1
    )
    hold_time_seconds: float = Field(
        default=3600.0,
        description="Hold time for static load in seconds (default: 1 hour)",
        gt=0
    )

    # Deflection measurements
    deflection_measurements: List[DeflectionMeasurement] = Field(
        default_factory=list,
        description="List of deflection measurements during test"
    )
    max_deflection_mm: Optional[float] = Field(
        default=None,
        description="Maximum measured deflection in millimeters"
    )
    deflection_limit_mm: float = Field(
        default=40.0,
        description="Maximum allowed deflection in millimeters"
    )

    # Power measurements
    pre_test_power: Optional[PowerMeasurement] = Field(
        default=None,
        description="Power measurement before test (flash test)"
    )
    post_test_power: Optional[PowerMeasurement] = Field(
        default=None,
        description="Power measurement after test (flash test)"
    )
    power_degradation_pct: Optional[float] = Field(
        default=None,
        description="Power degradation percentage"
    )
    power_degradation_limit_pct: float = Field(
        default=5.0,
        description="Maximum allowed power degradation percentage"
    )

    # Test results
    pass_status: Optional[bool] = Field(
        default=None,
        description="Whether the test passed all criteria"
    )
    pressure_uniformity_pct: Optional[float] = Field(
        default=None,
        description="Uniformity of applied pressure (percentage)"
    )

    @field_validator("load_pa")
    @classmethod
    def validate_load_pa(cls, v: float, info) -> float:
        """Validate load is within reasonable range for PV testing."""
        if v < 0:
            raise ValueError("load_pa must be positive")
        if v > 10000:
            raise ValueError("load_pa exceeds typical PV testing range (10000 Pa)")
        return v

    @field_validator("cycles")
    @classmethod
    def validate_cycles(cls, v: Optional[int], info) -> Optional[int]:
        """Validate cycle count for dynamic tests."""
        if v is not None and v < 1:
            raise ValueError("cycles must be at least 1")
        if v is not None and v > 10000:
            raise ValueError("cycles exceeds typical testing range (10000)")
        return v

    def validate_input_data(self) -> bool:
        """Validate test configuration and input data.

        Returns:
            True if validation passes, False otherwise
        """
        # Validate load type and cycles consistency
        if self.load_type == LoadType.DYNAMIC and self.cycles is None:
            self.add_error("Dynamic load test requires cycles to be specified")
            return False

        if self.load_type in [LoadType.STATIC_FRONT, LoadType.STATIC_REAR]:
            if self.cycles is not None:
                self.add_warning("Cycles specified for static test will be ignored")

        # Validate IEC 61215 compliance
        if self.load_type == LoadType.DYNAMIC:
            if self.load_pa < 900 or self.load_pa > 1100:
                self.add_warning(
                    f"IEC 61215 specifies ±1000 Pa for dynamic tests. "
                    f"Current: {self.load_pa} Pa"
                )

        if self.load_type in [LoadType.STATIC_FRONT, LoadType.STATIC_REAR]:
            if abs(self.load_pa - 2400) > 100:
                self.add_warning(
                    f"IEC 61215 specifies 2400 Pa for static tests. "
                    f"Current: {self.load_pa} Pa"
                )

        # Validate equipment IDs
        if not self.equipment_ids:
            self.add_warning("No equipment IDs specified - traceability may be incomplete")

        return True

    def add_deflection_measurement(
        self,
        load_pa: float,
        deflection_mm: float,
        position: str = "center",
        cycle_number: Optional[int] = None
    ) -> None:
        """Add a deflection measurement to the test record.

        Args:
            load_pa: Applied load in Pascals
            deflection_mm: Measured deflection in millimeters
            position: Measurement position (center, edge, corner)
            cycle_number: Cycle number for dynamic tests
        """
        measurement = DeflectionMeasurement(
            load_pa=load_pa,
            deflection_mm=deflection_mm,
            position=position,
            cycle_number=cycle_number
        )
        self.deflection_measurements.append(measurement)

        # Update max deflection
        if self.max_deflection_mm is None or abs(deflection_mm) > abs(self.max_deflection_mm):
            self.max_deflection_mm = abs(deflection_mm)

    def set_pre_test_power(self, power_measurement: PowerMeasurement) -> None:
        """Set the pre-test power measurement.

        Args:
            power_measurement: Power measurement from flash test before mechanical load
        """
        self.pre_test_power = power_measurement
        self.results["pre_test_pmax_w"] = power_measurement.pmax_w

    def set_post_test_power(self, power_measurement: PowerMeasurement) -> None:
        """Set the post-test power measurement and calculate degradation.

        Args:
            power_measurement: Power measurement from flash test after mechanical load
        """
        self.post_test_power = power_measurement
        self.results["post_test_pmax_w"] = power_measurement.pmax_w

        # Calculate power degradation
        if self.pre_test_power is not None:
            pre_power = self.pre_test_power.pmax_w
            post_power = power_measurement.pmax_w
            self.power_degradation_pct = ((pre_power - post_power) / pre_power) * 100
            self.results["power_degradation_pct"] = self.power_degradation_pct

    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate statistical analysis of deflection measurements.

        Returns:
            Dictionary containing deflection statistics
        """
        if not self.deflection_measurements:
            return {}

        deflections = [m.deflection_mm for m in self.deflection_measurements]
        deflections_array = np.array(deflections)

        stats = {
            "mean_deflection_mm": float(np.mean(deflections_array)),
            "std_deflection_mm": float(np.std(deflections_array)),
            "max_deflection_mm": float(np.max(np.abs(deflections_array))),
            "min_deflection_mm": float(np.min(np.abs(deflections_array))),
            "measurement_count": len(deflections)
        }

        # For dynamic tests, analyze by cycle
        if self.load_type == LoadType.DYNAMIC:
            cycle_deflections = {}
            for m in self.deflection_measurements:
                if m.cycle_number is not None:
                    if m.cycle_number not in cycle_deflections:
                        cycle_deflections[m.cycle_number] = []
                    cycle_deflections[m.cycle_number].append(m.deflection_mm)

            if cycle_deflections:
                stats["cycles_analyzed"] = len(cycle_deflections)

        return stats

    def evaluate_pass_criteria(self) -> bool:
        """Evaluate all pass/fail criteria for the test.

        Returns:
            True if test passes all criteria, False otherwise
        """
        passed = True

        # Check power degradation
        if self.power_degradation_pct is not None:
            if self.power_degradation_pct > self.power_degradation_limit_pct:
                self.add_error(
                    f"Power degradation {self.power_degradation_pct:.2f}% exceeds "
                    f"limit {self.power_degradation_limit_pct}%"
                )
                passed = False
            else:
                self.results["power_degradation_pass"] = True
        else:
            self.add_warning("Power degradation not calculated - missing measurements")

        # Check deflection
        if self.max_deflection_mm is not None:
            if self.max_deflection_mm > self.deflection_limit_mm:
                self.add_error(
                    f"Max deflection {self.max_deflection_mm:.2f} mm exceeds "
                    f"limit {self.deflection_limit_mm} mm"
                )
                passed = False
            else:
                self.results["deflection_pass"] = True
        else:
            self.add_warning("Deflection not measured")

        # Store pass criteria
        self.pass_criteria = {
            "max_power_degradation_pct": self.power_degradation_limit_pct,
            "max_deflection_mm": self.deflection_limit_mm,
            "required_cycles": self.cycles if self.load_type == LoadType.DYNAMIC else None,
            "required_load_pa": self.load_pa
        }

        self.pass_status = passed
        return passed

    def execute(self) -> bool:
        """Execute the mechanical load test.

        This is a template method that orchestrates the test execution.
        In a real implementation, this would interface with actual equipment.

        Returns:
            True if test passes, False otherwise
        """
        try:
            # Validate inputs
            if not self.validate_input_data():
                self.status = TestStatus.FAILED
                return False

            self.start_test()

            # Check pre-test power measurement exists
            if self.pre_test_power is None:
                self.add_error("Pre-test power measurement required")
                self.complete_test(False)
                return False

            # Execute test based on type
            if self.load_type == LoadType.DYNAMIC:
                self._execute_dynamic_test()
            else:
                self._execute_static_test()

            # Check post-test power measurement exists
            if self.post_test_power is None:
                self.add_error("Post-test power measurement required")
                self.complete_test(False)
                return False

            # Calculate statistics
            self.results["deflection_statistics"] = self.calculate_statistics()

            # Evaluate pass/fail
            passed = self.evaluate_pass_criteria()

            self.complete_test(passed)
            return passed

        except Exception as e:
            self.add_error(f"Test execution failed: {str(e)}")
            self.abort_test(str(e))
            return False

    def _execute_static_test(self) -> None:
        """Execute static load test procedure.

        Note: This is a template. In production, this would interface with
        actual pressure chamber or load frame equipment.
        """
        self.results["test_mode"] = "static"
        self.results["hold_time_seconds"] = self.hold_time_seconds
        self.results["load_pa"] = self.load_pa

        # In production: Apply static load and monitor deflection
        # For now, this is a placeholder for equipment integration

    def _execute_dynamic_test(self) -> None:
        """Execute dynamic load test procedure.

        Note: This is a template. In production, this would interface with
        actual cyclic loading equipment.
        """
        self.results["test_mode"] = "dynamic"
        self.results["target_cycles"] = self.cycles
        self.results["load_pa"] = self.load_pa

        # In production: Apply cyclic load and monitor deflection
        # For now, this is a placeholder for equipment integration

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report.

        Returns:
            Dictionary containing complete test data and results
        """
        report = {
            # Test identification
            "test_id": str(self.id),
            "test_name": self.test_name,
            "test_standard": self.test_standard.value,
            "module_id": self.module_id,
            "test_procedure_version": self.test_procedure_version,

            # Test status
            "status": self.status.value,
            "pass_status": self.pass_status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,

            # Test parameters
            "load_type": self.load_type.value,
            "load_pa": self.load_pa,
            "load_surface": self.load_surface.value,
            "cycles": self.cycles,
            "hold_time_seconds": self.hold_time_seconds,

            # Measurements
            "pre_test_power": (
                self.pre_test_power.model_dump() if self.pre_test_power else None
            ),
            "post_test_power": (
                self.post_test_power.model_dump() if self.post_test_power else None
            ),
            "power_degradation_pct": self.power_degradation_pct,
            "max_deflection_mm": self.max_deflection_mm,
            "deflection_measurements_count": len(self.deflection_measurements),

            # Pass criteria
            "pass_criteria": self.pass_criteria,

            # Results and statistics
            "results": self.results,

            # ISO 17025 traceability
            "operator_name": self.operator_name,
            "equipment_ids": self.equipment_ids,
            "environmental_conditions": self.environmental_conditions,

            # Errors and warnings
            "errors": self.error_messages,
            "warnings": self.warnings,
            "notes": self.notes,

            # Metadata
            "created_at": self.created_at.isoformat(),
            "version": self.version
        }

        return report
