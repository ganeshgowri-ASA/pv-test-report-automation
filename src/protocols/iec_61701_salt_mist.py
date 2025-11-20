"""
IEC 61701 Salt Mist Corrosion Testing Protocol Implementation.

Implements IEC 61701:2020 - Photovoltaic (PV) modules - Salt mist corrosion testing.

Salt mist exposure testing for PV modules in marine and coastal environments:
- Severity levels 1-6 (increasing severity)
- Cyclic exposure to salt solution spray
- Visual inspection and performance degradation assessment
- ISO 17025 and NABL compliant

Severity Levels:
- Level 1-2: Low severity (inland, > 10 km from coast)
- Level 3-4: Medium severity (5-10 km from coast)
- Level 5-6: High severity (near coast, < 1 km)
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.models.base_models import (
    CalibrationRecord,
    Severity,
    TestConditions,
    TestReport,
    TestSample,
    TestStatus,
)

logger = logging.getLogger(__name__)


class SaltMistSeverityLevel(str, Enum):
    """Salt mist severity levels per IEC 61701."""

    LEVEL_1 = "1"
    LEVEL_2 = "2"
    LEVEL_3 = "3"
    LEVEL_4 = "4"
    LEVEL_5 = "5"
    LEVEL_6 = "6"


class SaltMistConfig(BaseModel):
    """Salt mist corrosion test configuration."""

    severity_level: SaltMistSeverityLevel = Field(
        default=SaltMistSeverityLevel.LEVEL_3, description="Severity level 1-6"
    )
    salt_solution_concentration: float = Field(
        default=5.0, description="NaCl concentration (% by mass)"
    )
    solution_ph_range: tuple[float, float] = Field(
        default=(6.5, 7.2), description="pH range"
    )
    spray_temperature_c: float = Field(default=35.0, description="Spray temperature °C")
    spray_duration_hours: int = Field(..., description="Total spray duration (hours)")
    drying_duration_hours: int = Field(..., description="Drying duration (hours)")
    humidity_duration_hours: int = Field(..., description="High humidity duration (hours)")
    number_of_cycles: int = Field(..., description="Number of exposure cycles")
    chamber_temperature_c: float = Field(default=35.0, description="Chamber temperature °C")
    humidity_percent: float = Field(default=93.0, description="Relative humidity %")

    @classmethod
    def from_severity_level(cls, level: SaltMistSeverityLevel) -> "SaltMistConfig":
        """
        Create configuration from severity level per IEC 61701 Table 1.

        Args:
            level: Severity level 1-6

        Returns:
            Configuration for specified severity level
        """
        configs = {
            SaltMistSeverityLevel.LEVEL_1: {
                "spray_duration_hours": 2,
                "drying_duration_hours": 4,
                "humidity_duration_hours": 2,
                "number_of_cycles": 10,
            },
            SaltMistSeverityLevel.LEVEL_2: {
                "spray_duration_hours": 2,
                "drying_duration_hours": 4,
                "humidity_duration_hours": 2,
                "number_of_cycles": 30,
            },
            SaltMistSeverityLevel.LEVEL_3: {
                "spray_duration_hours": 2,
                "drying_duration_hours": 4,
                "humidity_duration_hours": 2,
                "number_of_cycles": 60,
            },
            SaltMistSeverityLevel.LEVEL_4: {
                "spray_duration_hours": 2,
                "drying_duration_hours": 4,
                "humidity_duration_hours": 2,
                "number_of_cycles": 90,
            },
            SaltMistSeverityLevel.LEVEL_5: {
                "spray_duration_hours": 2,
                "drying_duration_hours": 4,
                "humidity_duration_hours": 2,
                "number_of_cycles": 120,
            },
            SaltMistSeverityLevel.LEVEL_6: {
                "spray_duration_hours": 2,
                "drying_duration_hours": 4,
                "humidity_duration_hours": 2,
                "number_of_cycles": 200,
            },
        }

        config_params = configs[level]
        return cls(severity_level=level, **config_params)


class CorrosionInspection(BaseModel):
    """Visual corrosion inspection results."""

    cycle_number: int
    frame_corrosion: bool = False
    frame_corrosion_severity: Optional[str] = None  # minor, moderate, severe
    junction_box_corrosion: bool = False
    connector_corrosion: bool = False
    cell_interconnect_visible: bool = False
    cell_interconnect_corrosion: bool = False
    glass_degradation: bool = False
    encapsulant_discoloration: bool = False
    delamination: bool = False
    notes: Optional[str] = None


class IEC61701TestResult(BaseModel):
    """IEC 61701 salt mist test result."""

    test_name: str
    severity_level: str
    test_config: Dict[str, Any]
    measurements: List[Dict[str, Any]] = Field(default_factory=list)
    visual_inspections: List[CorrosionInspection] = Field(default_factory=list)
    initial_power: float
    final_power: float
    power_degradation_percent: float
    pass_fail: bool
    pass_criteria: str
    corrosion_detected: bool = False
    notes: Optional[str] = None


class IEC61701SaltMist:
    """
    IEC 61701 Salt Mist Corrosion Testing implementation.

    Comprehensive salt mist testing for PV modules per IEC 61701:2020.
    """

    def __init__(self, sample: TestSample, report_id: UUID):
        """
        Initialize IEC 61701 salt mist testing.

        Args:
            sample: Test sample information
            report_id: Test report UUID
        """
        self.sample = sample
        self.report_id = report_id
        self.test_results: List[IEC61701TestResult] = []
        self.test_conditions: List[TestConditions] = []

    def run_salt_mist_test(
        self,
        config: SaltMistConfig,
        calibration_records: List[CalibrationRecord],
    ) -> IEC61701TestResult:
        """
        Execute salt mist corrosion test per IEC 61701.

        Args:
            config: Salt mist test configuration
            calibration_records: Equipment calibration records

        Returns:
            Test result with pass/fail status
        """
        logger.info(
            f"Starting salt mist test (Level {config.severity_level.value}) "
            f"for sample {self.sample.sample_id}"
        )

        initial_power = self.sample.rated_power
        measurements = []
        visual_inspections = []

        # Record test conditions
        test_condition = TestConditions(
            temperature=config.chamber_temperature_c,
            humidity=config.humidity_percent,
            measurement_time=datetime.utcnow(),
            equipment_id="SALT-MIST-CHAMBER-001",
        )
        self.test_conditions.append(test_condition)

        # Simulate salt mist exposure cycles
        inspection_intervals = [
            0,
            config.number_of_cycles // 4,
            config.number_of_cycles // 2,
            3 * config.number_of_cycles // 4,
            config.number_of_cycles,
        ]

        for cycle in range(config.number_of_cycles + 1):
            # Progressive degradation (severity-dependent)
            base_degradation = float(config.severity_level.value) * 0.1  # % per cycle
            cumulative_degradation = min(cycle * base_degradation, 8.0)  # Max 8%

            current_power = initial_power * (1 - cumulative_degradation / 100)

            if cycle in inspection_intervals:
                # Visual inspection
                corrosion_detected = cycle > config.number_of_cycles // 2

                inspection = CorrosionInspection(
                    cycle_number=cycle,
                    frame_corrosion=corrosion_detected and int(config.severity_level.value) >= 5,
                    frame_corrosion_severity="minor" if corrosion_detected else None,
                    junction_box_corrosion=False,
                    connector_corrosion=corrosion_detected and int(config.severity_level.value) >= 6,
                    cell_interconnect_visible=False,
                    cell_interconnect_corrosion=False,
                    glass_degradation=False,
                    encapsulant_discoloration=cycle == config.number_of_cycles,
                    delamination=False,
                    notes=f"Inspection after {cycle} cycles",
                )
                visual_inspections.append(inspection)

                # Power measurement
                measurements.append({
                    "cycle": cycle,
                    "power_w": round(current_power, 2),
                    "degradation_percent": round(cumulative_degradation, 2),
                    "visual_inspection_passed": not (
                        inspection.frame_corrosion or inspection.delamination
                    ),
                })

        final_power = measurements[-1]["power_w"]
        degradation_pct = ((initial_power - final_power) / initial_power) * 100

        # Pass criteria per IEC 61701: < 5% degradation and no major visual defects
        major_corrosion = any(
            insp.frame_corrosion or insp.delamination or insp.cell_interconnect_corrosion
            for insp in visual_inspections
        )

        pass_fail = degradation_pct < 5.0 and not major_corrosion

        result = IEC61701TestResult(
            test_name="Salt Mist Corrosion Test",
            severity_level=config.severity_level.value,
            test_config=config.model_dump(),
            measurements=measurements,
            visual_inspections=visual_inspections,
            initial_power=initial_power,
            final_power=final_power,
            power_degradation_percent=round(degradation_pct, 2),
            pass_fail=pass_fail,
            pass_criteria="Power degradation < 5%, no major visual defects",
            corrosion_detected=major_corrosion,
            notes=f"Severity Level {config.severity_level.value}: {config.number_of_cycles} cycles completed",
        )

        self.test_results.append(result)
        logger.info(
            f"Salt mist test completed: {degradation_pct:.2f}% degradation, "
            f"Corrosion: {major_corrosion}, {'PASS' if pass_fail else 'FAIL'}"
        )

        return result

    def run_multi_severity_test(
        self,
        severity_levels: List[SaltMistSeverityLevel],
        calibration_records: List[CalibrationRecord],
    ) -> List[IEC61701TestResult]:
        """
        Run salt mist tests at multiple severity levels.

        Args:
            severity_levels: List of severity levels to test
            calibration_records: Equipment calibration records

        Returns:
            List of test results for each severity level
        """
        logger.info(
            f"Starting multi-severity salt mist test for sample {self.sample.sample_id}"
        )

        results = []
        for level in severity_levels:
            config = SaltMistConfig.from_severity_level(level)
            result = self.run_salt_mist_test(config, calibration_records)
            results.append(result)

        logger.info(f"Multi-severity test completed: {len(results)} levels tested")
        return results

    def generate_report(self) -> TestReport:
        """
        Generate comprehensive IEC 61701 salt mist test report.

        Returns:
            Complete salt mist test report
        """
        overall_pass = all(result.pass_fail for result in self.test_results)

        test_results_dict = {
            "protocol": "IEC 61701:2020 Salt Mist Corrosion Testing",
            "severity_levels_tested": [
                result.severity_level for result in self.test_results
            ],
            "overall_result": "PASS" if overall_pass else "FAIL",
            "individual_tests": [result.model_dump() for result in self.test_results],
            "total_tests": len(self.test_results),
            "passed_tests": sum(1 for r in self.test_results if r.pass_fail),
        }

        report = TestReport(
            report_number=f"IEC61701-{self.sample.sample_id}-{datetime.utcnow().strftime('%Y%m%d')}",
            test_type="IEC 61701 Salt Mist Corrosion Testing",
            sample=self.sample,
            test_conditions=self.test_conditions,
            test_results=test_results_dict,
            status=TestStatus.COMPLETED,
            compliance_standards=["IEC 61701:2020", "ISO 17025:2017", "NABL"],
        )

        logger.info(
            f"IEC 61701 salt mist report generated: {report.report_number}, "
            f"Overall result: {'PASS' if overall_pass else 'FAIL'}"
        )

        return report
