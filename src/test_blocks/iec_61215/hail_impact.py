"""
Hail Impact Test Block - IEC 61215 Section 10.17

Implements hail impact testing for PV modules according to IEC 61215 standard.

Test Procedure:
1. Pre-test flash measurement (I-V curve)
2. Visual inspection before impact
3. Ice ball preparation (25mm diameter)
4. Impact at 11 specified locations
5. Velocity verification (23 m/s ± 2.5%)
6. Visual inspection after impact
7. Post-test flash measurement
8. Pass/fail determination

Pass Criteria:
- No glass breakage
- No major visual defects
- Power degradation < 5%

Compliance:
- IEC 61215: Design qualification and type approval
- ISO 17025: Laboratory competence requirements
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.core.base_models import (
    BaseTestBlock,
    TestResult,
    TestParameter,
    EquipmentInfo,
    TestBlockStatus
)
from src.utils.constants import IEC61215Limits, TestEquipment, UncertaintyBudget
from src.utils.validators import (
    ParameterValidator,
    EquipmentValidator,
    EnvironmentalValidator,
    ResultValidator
)


@dataclass
class ImpactPoint:
    """Represents a single impact point on the module."""
    point_number: int
    location_description: str
    x_coordinate_mm: Optional[float] = None
    y_coordinate_mm: Optional[float] = None
    velocity_ms: Optional[float] = None
    visual_damage: bool = False
    damage_description: str = ""
    timestamp: Optional[datetime] = None


@dataclass
class FlashTestResult:
    """Results from flash test measurement."""
    timestamp: datetime
    pmax_w: float
    voc_v: float
    isc_a: float
    fill_factor: float
    irradiance_wm2: float
    cell_temperature_c: float
    efficiency_pct: float


class HailImpactTest(BaseTestBlock):
    """
    Hail Impact Test implementation per IEC 61215.

    Simulates hail impact using ice balls to verify module mechanical robustness.

    Attributes:
        module_id: Unique module identifier
        ball_diameter_mm: Ice ball diameter (default: 25mm)
        target_velocity_ms: Target impact velocity (default: 23 m/s)
        impact_count: Number of impact points (default: 11)
        flash_test_before: Pre-test flash measurement results
        flash_test_after: Post-test flash measurement results
        impact_points: List of impact point data
        glass_breakage: Whether glass breakage occurred
        power_degradation_pct: Measured power degradation percentage
    """

    STANDARD = "IEC 61215"
    TEST_TYPE = "Hail Impact Test"
    SECTION = "10.17"

    def __init__(
        self,
        block_id: str,
        operator: str,
        module_id: int,
        ball_diameter_mm: float = 25.0,
        target_velocity_ms: float = 23.0,
        impact_count: int = 11,
        sample_info: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Hail Impact Test.

        Args:
            block_id: Unique test block identifier
            operator: Name of test operator
            module_id: Module ID being tested
            ball_diameter_mm: Ice ball diameter in mm (default: 25)
            target_velocity_ms: Target impact velocity in m/s (default: 23)
            impact_count: Number of impact points (default: 11)
            sample_info: Additional sample information dictionary
        """
        if sample_info is None:
            sample_info = {}
        sample_info["module_id"] = module_id

        super().__init__(
            block_id=block_id,
            standard=f"{self.STANDARD} - {self.SECTION}",
            description=self.TEST_TYPE,
            operator=operator,
            sample_info=sample_info
        )

        self.module_id = module_id
        self.ball_diameter_mm = ball_diameter_mm
        self.target_velocity_ms = target_velocity_ms
        self.impact_count = impact_count

        # Test results
        self.flash_test_before: Optional[FlashTestResult] = None
        self.flash_test_after: Optional[FlashTestResult] = None
        self.impact_points: List[ImpactPoint] = []
        self.glass_breakage: bool = False
        self.power_degradation_pct: float = 0.0
        self.pass_status: bool = False

        # Visual inspection results
        self.visual_defects_before: List[str] = []
        self.visual_defects_after: List[str] = []

        self._setup_parameters()
        self._setup_equipment()

    def _setup_parameters(self) -> None:
        """Set up test parameters with tolerances."""
        limits = IEC61215Limits.HAIL_IMPACT

        self.parameters["ball_diameter_mm"] = TestParameter(
            name="Ice Ball Diameter",
            value=self.ball_diameter_mm,
            unit="mm",
            tolerance={
                "min": limits["standard_ball_diameter_mm"] - limits["ball_diameter_tolerance_mm"],
                "max": limits["standard_ball_diameter_mm"] + limits["ball_diameter_tolerance_mm"]
            },
            metadata={"standard_value": limits["standard_ball_diameter_mm"]}
        )

        self.parameters["impact_velocity_ms"] = TestParameter(
            name="Impact Velocity",
            value=self.target_velocity_ms,
            unit="m/s",
            tolerance={
                "min": self.target_velocity_ms * (1 - limits["velocity_tolerance_pct"] / 100),
                "max": self.target_velocity_ms * (1 + limits["velocity_tolerance_pct"] / 100)
            },
            metadata={"standard_value": limits["standard_impact_velocity_ms"]}
        )

        self.parameters["impact_count"] = TestParameter(
            name="Number of Impact Points",
            value=self.impact_count,
            unit="points",
            tolerance={"min": 11, "max": 11},
            metadata={"standard_value": limits["standard_impact_count"]}
        )

        self.parameters["max_power_degradation_pct"] = TestParameter(
            name="Maximum Power Degradation",
            value=limits["max_power_degradation_pct"],
            unit="%",
            tolerance={"min": 0, "max": limits["max_power_degradation_pct"]},
            metadata={"pass_criteria": True}
        )

    def _setup_equipment(self) -> None:
        """Set up required equipment with calibration info."""
        equipment_specs = TestEquipment.HAIL_TEST

        # Hail gun (pneumatic launcher)
        self.equipment_used.append(
            EquipmentInfo(
                equipment_id="HAIL-GUN-001",
                name="Pneumatic Hail Impact Launcher",
                calibration_date=datetime.now() - timedelta(days=180),
                calibration_due_date=datetime.now() + timedelta(days=185),
                calibration_certificate="CAL-2024-HG-001",
                uncertainty=equipment_specs["hail_gun"]["accuracy"]
            )
        )

        # Velocity measurement (chronograph)
        self.equipment_used.append(
            EquipmentInfo(
                equipment_id="CHRONO-001",
                name="Optical Chronograph Velocity Sensor",
                calibration_date=datetime.now() - timedelta(days=150),
                calibration_due_date=datetime.now() + timedelta(days=215),
                calibration_certificate="CAL-2024-CH-001",
                uncertainty="±0.5 m/s"
            )
        )

        # Flash tester (solar simulator)
        self.equipment_used.append(
            EquipmentInfo(
                equipment_id="FLASH-TEST-001",
                name="Class AAA Solar Simulator with IV Tracer",
                calibration_date=datetime.now() - timedelta(days=90),
                calibration_due_date=datetime.now() + timedelta(days=90),
                calibration_certificate="CAL-2024-FT-001",
                uncertainty="±2.0%"
            )
        )

        # Optional high-speed camera
        self.equipment_used.append(
            EquipmentInfo(
                equipment_id="HSCAM-001",
                name="High-Speed Impact Camera (Optional)",
                calibration_date=datetime.now(),
                calibration_due_date=datetime.now() + timedelta(days=365),
                calibration_certificate="N/A - Documentation only",
                uncertainty="N/A"
            )
        )

    def validate_parameters(self) -> bool:
        """
        Validate test parameters before execution.

        Returns:
            True if all parameters are valid, False otherwise
        """
        all_valid = True
        errors = []

        # Validate ball diameter
        is_valid, error = ParameterValidator.check_tolerance(
            self.ball_diameter_mm,
            self.parameters["ball_diameter_mm"].tolerance["min"],
            self.parameters["ball_diameter_mm"].tolerance["max"],
            "Ball diameter"
        )
        if not is_valid:
            all_valid = False
            errors.append(error)

        # Validate impact count
        if self.impact_count != 11:
            all_valid = False
            errors.append(f"Impact count must be 11 (got {self.impact_count})")

        # Validate equipment calibration
        if not self.validate_equipment_calibration():
            all_valid = False
            errors.append("One or more equipment calibrations expired")

        # Validate environmental conditions
        if self.environmental_conditions:
            env_valid, env_errors = EnvironmentalValidator.validate_conditions(
                temperature_celsius=self.environmental_conditions.get("temperature_celsius"),
                humidity_pct=self.environmental_conditions.get("humidity_pct"),
                pressure_kpa=self.environmental_conditions.get("pressure_kpa")
            )
            if not env_valid:
                all_valid = False
                errors.extend(env_errors)

        if not all_valid:
            self.notes += "Parameter validation failed:\n"
            for error in errors:
                self.notes += f"  - {error}\n"

        return all_valid

    def perform_flash_test(
        self,
        test_type: str = "before"
    ) -> FlashTestResult:
        """
        Perform flash test measurement (I-V curve characterization).

        Args:
            test_type: "before" or "after" impact

        Returns:
            FlashTestResult with measured parameters
        """
        # This is a placeholder implementation
        # In real system, this would interface with actual flash test equipment

        # Simulated measurements (would come from real equipment)
        result = FlashTestResult(
            timestamp=datetime.now(),
            pmax_w=450.5 if test_type == "before" else 430.2,
            voc_v=48.2,
            isc_a=10.5,
            fill_factor=0.815,
            irradiance_wm2=1000.0,
            cell_temperature_c=25.0,
            efficiency_pct=19.5 if test_type == "before" else 18.6
        )

        return result

    def perform_visual_inspection(
        self,
        inspection_type: str = "before"
    ) -> List[str]:
        """
        Perform visual inspection of module.

        Args:
            inspection_type: "before" or "after" impact

        Returns:
            List of detected defects
        """
        defects = []

        # This is a placeholder - in real system would use actual inspection
        # Could integrate with image analysis, checklist, etc.

        # Example defects (would be actual observations)
        if inspection_type == "after":
            # Check for glass breakage
            if self.glass_breakage:
                defects.append("Glass breakage detected")

        return defects

    def perform_impact(
        self,
        point_number: int,
        location_description: str,
        x_mm: Optional[float] = None,
        y_mm: Optional[float] = None
    ) -> ImpactPoint:
        """
        Perform single hail impact at specified location.

        Args:
            point_number: Impact point number (1-11)
            location_description: Description of impact location
            x_mm: X coordinate on module (optional)
            y_mm: Y coordinate on module (optional)

        Returns:
            ImpactPoint object with impact results
        """
        # This is a placeholder - in real system would control hail gun
        # and measure actual velocity

        # Simulated velocity measurement (would come from chronograph)
        import random
        velocity_variation = random.uniform(-0.5, 0.5)
        measured_velocity = self.target_velocity_ms + velocity_variation

        # Validate velocity
        is_valid, error = ParameterValidator.validate_velocity(
            measured_velocity,
            self.target_velocity_ms,
            tolerance_pct=IEC61215Limits.HAIL_IMPACT["velocity_tolerance_pct"]
        )

        if not is_valid:
            self.notes += f"Point {point_number}: {error}\n"

        # Simulated visual damage check (would be actual inspection)
        visual_damage = False
        damage_desc = ""

        impact_point = ImpactPoint(
            point_number=point_number,
            location_description=location_description,
            x_coordinate_mm=x_mm,
            y_coordinate_mm=y_mm,
            velocity_ms=measured_velocity,
            visual_damage=visual_damage,
            damage_description=damage_desc,
            timestamp=datetime.now()
        )

        return impact_point

    def execute(self) -> List[TestResult]:
        """
        Execute the complete hail impact test sequence.

        Returns:
            List of test results
        """
        self.status = TestBlockStatus.IN_PROGRESS
        self.start_time = datetime.now()

        try:
            # Step 1: Validate parameters
            if not self.validate_parameters():
                self.status = TestBlockStatus.FAILED
                self.notes += "Test aborted due to parameter validation failure\n"
                return self.results

            # Step 2: Pre-test flash measurement
            self.notes += "Performing pre-test flash measurement...\n"
            self.flash_test_before = self.perform_flash_test("before")

            # Step 3: Pre-test visual inspection
            self.notes += "Performing pre-test visual inspection...\n"
            self.visual_defects_before = self.perform_visual_inspection("before")

            # Step 4: Perform impacts at all specified locations
            self.notes += f"Performing {self.impact_count} impact points...\n"
            impact_locations = IEC61215Limits.HAIL_IMPACT["impact_locations"]

            for i, location in enumerate(impact_locations[:self.impact_count], 1):
                self.notes += f"  Impact point {i}: {location['description']}\n"
                impact_point = self.perform_impact(
                    point_number=i,
                    location_description=location["description"]
                )
                self.impact_points.append(impact_point)

            # Step 5: Post-test visual inspection
            self.notes += "Performing post-test visual inspection...\n"
            self.visual_defects_after = self.perform_visual_inspection("after")

            # Check for glass breakage
            for defect in self.visual_defects_after:
                if "glass breakage" in defect.lower():
                    self.glass_breakage = True

            # Step 6: Post-test flash measurement
            self.notes += "Performing post-test flash measurement...\n"
            self.flash_test_after = self.perform_flash_test("after")

            # Step 7: Calculate power degradation
            if self.flash_test_before and self.flash_test_after:
                is_valid, degradation, message = ResultValidator.validate_power_degradation(
                    self.flash_test_before.pmax_w,
                    self.flash_test_after.pmax_w,
                    max_degradation_pct=IEC61215Limits.HAIL_IMPACT["max_power_degradation_pct"]
                )
                self.power_degradation_pct = degradation
                self.notes += f"{message}\n"

                # Create power degradation test result
                self.results.append(TestResult(
                    passed=is_valid,
                    measurement_value=degradation,
                    specification_limit_max=IEC61215Limits.HAIL_IMPACT["max_power_degradation_pct"],
                    unit="%",
                    comments=message,
                    raw_data={
                        "power_before_w": self.flash_test_before.pmax_w,
                        "power_after_w": self.flash_test_after.pmax_w
                    }
                ))

            # Step 8: Glass breakage test result
            self.results.append(TestResult(
                passed=not self.glass_breakage,
                measurement_value=1 if self.glass_breakage else 0,
                specification_limit_max=0,
                unit="boolean",
                comments="No glass breakage allowed" if not self.glass_breakage else "FAILED: Glass breakage detected"
            ))

            # Step 9: Velocity compliance for all impacts
            velocity_compliant = all(
                ParameterValidator.validate_velocity(
                    point.velocity_ms,
                    self.target_velocity_ms
                )[0]
                for point in self.impact_points
                if point.velocity_ms is not None
            )

            self.results.append(TestResult(
                passed=velocity_compliant,
                measurement_value=sum(p.velocity_ms for p in self.impact_points if p.velocity_ms) / len(self.impact_points),
                specification_limit_min=self.target_velocity_ms * 0.975,
                specification_limit_max=self.target_velocity_ms * 1.025,
                unit="m/s",
                comments=f"Average velocity across {len(self.impact_points)} impacts"
            ))

            # Step 10: Determine overall pass/fail
            self.pass_status = all(r.passed for r in self.results)
            self.status = TestBlockStatus.COMPLETED if self.pass_status else TestBlockStatus.FAILED

            self.notes += f"\nTest {'PASSED' if self.pass_status else 'FAILED'}\n"

        except Exception as e:
            self.status = TestBlockStatus.FAILED
            self.notes += f"Error during test execution: {str(e)}\n"
            self.pass_status = False

        finally:
            self.end_time = datetime.now()

        return self.results

    def post_process(self) -> None:
        """Post-process results and generate detailed report."""
        self.notes += "\n=== POST-PROCESSING REPORT ===\n"

        # Summary statistics
        if self.flash_test_before and self.flash_test_after:
            self.notes += f"\nFlash Test Summary:\n"
            self.notes += f"  Before: Pmax = {self.flash_test_before.pmax_w:.2f} W\n"
            self.notes += f"  After:  Pmax = {self.flash_test_after.pmax_w:.2f} W\n"
            self.notes += f"  Power Degradation: {self.power_degradation_pct:.2f}%\n"

        # Impact statistics
        if self.impact_points:
            velocities = [p.velocity_ms for p in self.impact_points if p.velocity_ms is not None]
            avg_velocity = sum(velocities) / len(velocities) if velocities else 0
            min_velocity = min(velocities) if velocities else 0
            max_velocity = max(velocities) if velocities else 0

            self.notes += f"\nImpact Velocity Statistics:\n"
            self.notes += f"  Target: {self.target_velocity_ms} m/s\n"
            self.notes += f"  Average: {avg_velocity:.2f} m/s\n"
            self.notes += f"  Range: {min_velocity:.2f} - {max_velocity:.2f} m/s\n"

        # Visual inspection summary
        self.notes += f"\nVisual Inspection:\n"
        self.notes += f"  Defects before: {len(self.visual_defects_before)}\n"
        self.notes += f"  Defects after: {len(self.visual_defects_after)}\n"
        self.notes += f"  Glass breakage: {'YES - FAIL' if self.glass_breakage else 'NO - PASS'}\n"

        # Compliance statement
        self.notes += f"\nCompliance:\n"
        self.notes += f"  Standard: {self.standard}\n"
        self.notes += f"  Test Method: {self.TEST_TYPE}\n"
        self.notes += f"  Overall Result: {'PASS' if self.pass_status else 'FAIL'}\n"

    def get_detailed_report(self) -> Dict[str, Any]:
        """
        Get comprehensive test report with all data.

        Returns:
            Dictionary containing complete test report
        """
        report = self.to_dict()

        # Add hail-test specific data
        report["hail_impact_data"] = {
            "module_id": self.module_id,
            "ball_diameter_mm": self.ball_diameter_mm,
            "target_velocity_ms": self.target_velocity_ms,
            "impact_count": self.impact_count,
            "glass_breakage": self.glass_breakage,
            "power_degradation_pct": self.power_degradation_pct,
            "pass_status": self.pass_status,
            "flash_test_before": {
                "timestamp": self.flash_test_before.timestamp.isoformat() if self.flash_test_before else None,
                "pmax_w": self.flash_test_before.pmax_w if self.flash_test_before else None,
                "voc_v": self.flash_test_before.voc_v if self.flash_test_before else None,
                "isc_a": self.flash_test_before.isc_a if self.flash_test_before else None,
                "fill_factor": self.flash_test_before.fill_factor if self.flash_test_before else None,
                "efficiency_pct": self.flash_test_before.efficiency_pct if self.flash_test_before else None
            } if self.flash_test_before else None,
            "flash_test_after": {
                "timestamp": self.flash_test_after.timestamp.isoformat() if self.flash_test_after else None,
                "pmax_w": self.flash_test_after.pmax_w if self.flash_test_after else None,
                "voc_v": self.flash_test_after.voc_v if self.flash_test_after else None,
                "isc_a": self.flash_test_after.isc_a if self.flash_test_after else None,
                "fill_factor": self.flash_test_after.fill_factor if self.flash_test_after else None,
                "efficiency_pct": self.flash_test_after.efficiency_pct if self.flash_test_after else None
            } if self.flash_test_after else None,
            "impact_points": [
                {
                    "point_number": p.point_number,
                    "location": p.location_description,
                    "x_mm": p.x_coordinate_mm,
                    "y_mm": p.y_coordinate_mm,
                    "velocity_ms": p.velocity_ms,
                    "visual_damage": p.visual_damage,
                    "damage_description": p.damage_description,
                    "timestamp": p.timestamp.isoformat() if p.timestamp else None
                }
                for p in self.impact_points
            ],
            "visual_defects_before": self.visual_defects_before,
            "visual_defects_after": self.visual_defects_after
        }

        return report


# Convenience function for quick test execution
def run_hail_impact_test(
    module_id: int,
    operator: str,
    ball_diameter: float = 25.0,
    velocity: float = 23.0,
    block_id: Optional[str] = None
) -> HailImpactTest:
    """
    Convenience function to run a complete hail impact test.

    Args:
        module_id: Module identifier
        operator: Test operator name
        ball_diameter: Ice ball diameter in mm (default: 25)
        velocity: Impact velocity in m/s (default: 23)
        block_id: Optional test block ID (auto-generated if not provided)

    Returns:
        Completed HailImpactTest object

    Example:
        >>> test = run_hail_impact_test(module_id=1001, operator="John Doe")
        >>> print(f"Test passed: {test.pass_status}")
    """
    if block_id is None:
        block_id = f"HAIL-{module_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    test = HailImpactTest(
        block_id=block_id,
        operator=operator,
        module_id=module_id,
        ball_diameter_mm=ball_diameter,
        target_velocity_ms=velocity
    )

    test.execute()
    test.post_process()

    return test
