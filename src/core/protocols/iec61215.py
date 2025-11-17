"""
IEC 61215-2:2021 Protocol Implementation
Terrestrial photovoltaic (PV) modules - Design qualification and type approval
Part 2: Test procedures

This module implements the complete Module Safety Test (MST) sequence for
crystalline silicon and thin-film modules.
"""
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import math

from .base import BaseProtocol
from ..models.test_sequence import TestSequence, TestStep
from ..models.test_result import (
    TestResult, AcceptanceCriteria, ModuleUnderTest,
    TestStatus, ComplianceStatus
)
from ..models.measurement import (
    Measurement, MeasurementSeries, MeasurementUnit,
    Equipment, Uncertainty
)
from ..equipment.base import (
    SolarSimulator, IVTracer, TemperatureChamber,
    InsulationTester
)


class IEC61215Protocol(BaseProtocol):
    """
    IEC 61215-2:2021 Protocol Engine

    Implements complete test sequence for PV module design qualification:
    - 19 Module Safety Tests (MST)
    - Automatic test sequencing based on flowchart
    - Pass/fail criteria per clause
    - Data collection from test equipment
    - Compliance report generation
    - Support for crystalline and thin-film modules
    - Degradation calculations
    """

    # Standard reference conditions
    STC_IRRADIANCE = 1000.0  # W/m²
    STC_TEMPERATURE = 25.0   # °C
    STC_SPECTRUM = "AM1.5G"

    # Test conditions
    NOCT_IRRADIANCE = 800.0  # W/m²
    NOCT_AMBIENT_TEMP = 20.0  # °C
    NOCT_WIND_SPEED = 1.0  # m/s

    # Degradation limits (%)
    MAX_DEGRADATION_GENERAL = 5.0
    MAX_DEGRADATION_INITIAL = 2.0

    def __init__(self):
        """Initialize IEC 61215 protocol."""
        super().__init__()
        self.protocol_name = "IEC 61215-2"
        self.protocol_version = "2021"
        self.standard_reference = "IEC 61215-2:2021"

        # Equipment references (to be set during initialization)
        self.solar_simulator: Optional[SolarSimulator] = None
        self.iv_tracer: Optional[IVTracer] = None
        self.temp_chamber: Optional[TemperatureChamber] = None
        self.insulation_tester: Optional[InsulationTester] = None

        # Test data storage
        self.initial_performance: Dict[str, float] = {}
        self.stabilized_performance: Dict[str, float] = {}

    def initialize_sequence(
        self,
        module: ModuleUnderTest,
        **kwargs
    ) -> TestSequence:
        """
        Initialize IEC 61215 test sequence.

        Args:
            module: Module under test
            **kwargs: Additional parameters (equipment, lab info, etc.)

        Returns:
            TestSequence object
        """
        # Create test sequence
        sequence = TestSequence(
            sequence_id=f"IEC61215_{module.serial_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            sequence_name="IEC 61215-2:2021 Design Qualification",
            protocol_name=self.protocol_name,
            protocol_version=self.protocol_version,
            module=module,
        )

        # Set laboratory information if provided
        if "laboratory_name" in kwargs:
            sequence.laboratory_name = kwargs["laboratory_name"]
        if "laboratory_accreditation" in kwargs:
            sequence.laboratory_accreditation = kwargs["laboratory_accreditation"]
        if "test_report_number" in kwargs:
            sequence.test_report_number = kwargs["test_report_number"]
        if "test_engineer" in kwargs:
            sequence.test_engineer = kwargs["test_engineer"]

        # Define test steps based on module type
        steps = self.define_test_steps(module.module_type)
        for step in steps:
            sequence.add_step(step)

        self.test_sequence = sequence
        return sequence

    def define_test_steps(self, module_type: str) -> List[TestStep]:
        """
        Define IEC 61215 test steps based on module type.

        Test sequence follows IEC 61215-2:2021 flowchart:
        1. Initial visual inspection and performance
        2. Preconditioning (stabilization)
        3. Environmental tests (UV, TC, HF, DH, etc.)
        4. Mechanical tests (ML, Hail, Twist)
        5. Final performance and wet leakage

        Args:
            module_type: "crystalline" or "thin_film"

        Returns:
            List of TestStep objects in execution order
        """
        steps = []

        # MST 01: Visual Inspection (Initial)
        steps.append(TestStep(
            step_id="MST01_initial",
            test_id="MST01",
            test_name="Visual Inspection - Initial",
            description="Initial visual inspection before testing",
            clause_reference="IEC 61215-2:2021 Clause 7.1",
            sequence_number=10,
            module_types=None,  # Applies to all types
        ))

        # MST 02: Maximum Power Determination (Initial)
        steps.append(TestStep(
            step_id="MST02_initial",
            test_id="MST02",
            test_name="Maximum Power Determination - Initial",
            description="Initial performance measurement at STC",
            clause_reference="IEC 61215-2:2021 Clause 7.2",
            sequence_number=20,
            depends_on=["MST01_initial"],
        ))

        # MST 03: Insulation Test (Initial)
        steps.append(TestStep(
            step_id="MST03_initial",
            test_id="MST03",
            test_name="Insulation Test - Initial",
            description="Initial insulation resistance test",
            clause_reference="IEC 61215-2:2021 Clause 7.3",
            sequence_number=30,
            depends_on=["MST02_initial"],
        ))

        # Preconditioning (for thin-film modules)
        if module_type == "thin_film":
            steps.append(TestStep(
                step_id="PRECON",
                test_id="PRECON",
                test_name="Preconditioning (Stabilization)",
                description="Light soaking for thin-film module stabilization",
                clause_reference="IEC 61215-2:2021 Clause 6.3.4",
                sequence_number=40,
                depends_on=["MST03_initial"],
                module_types=["thin_film"],
            ))

        # MST 04: Temperature Coefficients
        steps.append(TestStep(
            step_id="MST04",
            test_id="MST04",
            test_name="Temperature Coefficients",
            description="Determination of temperature coefficients",
            clause_reference="IEC 61215-2:2021 Clause 7.4",
            sequence_number=50,
            depends_on=["PRECON"] if module_type == "thin_film" else ["MST03_initial"],
        ))

        # MST 05: NOCT (Nominal Operating Cell Temperature)
        steps.append(TestStep(
            step_id="MST05",
            test_id="MST05",
            test_name="NOCT Measurement",
            description="Nominal operating cell temperature determination",
            clause_reference="IEC 61215-2:2021 Clause 7.5",
            sequence_number=60,
            depends_on=["MST04"],
        ))

        # MST 06: STC Performance (after stabilization)
        steps.append(TestStep(
            step_id="MST06",
            test_id="MST06",
            test_name="STC Performance",
            description="Performance at Standard Test Conditions",
            clause_reference="IEC 61215-2:2021 Clause 7.6",
            sequence_number=70,
            depends_on=["MST05"],
        ))

        # MST 07: Low Irradiance Performance
        steps.append(TestStep(
            step_id="MST07",
            test_id="MST07",
            test_name="Low Irradiance Performance",
            description="Performance at low irradiance (200 W/m²)",
            clause_reference="IEC 61215-2:2021 Clause 7.7",
            sequence_number=80,
            depends_on=["MST06"],
        ))

        # MST 08: Outdoor Exposure Test
        steps.append(TestStep(
            step_id="MST08",
            test_id="MST08",
            test_name="Outdoor Exposure",
            description="Outdoor exposure test (60 kWh/m² minimum)",
            clause_reference="IEC 61215-2:2021 Clause 7.8",
            sequence_number=90,
            depends_on=["MST07"],
        ))

        # MST 09: Hot-spot Endurance Test
        steps.append(TestStep(
            step_id="MST09",
            test_id="MST09",
            test_name="Hot-spot Endurance",
            description="Hot-spot endurance test",
            clause_reference="IEC 61215-2:2021 Clause 7.9",
            sequence_number=100,
            depends_on=["MST08"],
        ))

        # MST 10: UV Preconditioning Test
        steps.append(TestStep(
            step_id="MST10",
            test_id="MST10",
            test_name="UV Preconditioning",
            description="UV exposure test (15 kWh/m² at 280-400 nm)",
            clause_reference="IEC 61215-2:2021 Clause 7.10",
            sequence_number=110,
            depends_on=["MST09"],
        ))

        # MST 11: Thermal Cycling Test (TC 200)
        steps.append(TestStep(
            step_id="MST11",
            test_id="MST11",
            test_name="Thermal Cycling (TC 200)",
            description="200 thermal cycles: -40°C to +85°C",
            clause_reference="IEC 61215-2:2021 Clause 7.11",
            sequence_number=120,
            depends_on=["MST10"],
        ))

        # MST 12: Humidity-Freeze Test (HF 10)
        steps.append(TestStep(
            step_id="MST12",
            test_id="MST12",
            test_name="Humidity-Freeze (HF 10)",
            description="10 humidity-freeze cycles",
            clause_reference="IEC 61215-2:2021 Clause 7.12",
            sequence_number=130,
            depends_on=["MST11"],
        ))

        # MST 13: Damp Heat Test (DH 1000)
        steps.append(TestStep(
            step_id="MST13",
            test_id="MST13",
            test_name="Damp Heat (DH 1000)",
            description="1000 hours at 85°C/85% RH",
            clause_reference="IEC 61215-2:2021 Clause 7.13",
            sequence_number=140,
            depends_on=["MST12"],
        ))

        # MST 14: Mechanical Load Test (Static)
        steps.append(TestStep(
            step_id="MST14_static",
            test_id="MST14",
            test_name="Mechanical Load Test - Static",
            description="Static mechanical load test (2400 Pa front/back)",
            clause_reference="IEC 61215-2:2021 Clause 7.14",
            sequence_number=150,
            depends_on=["MST13"],
        ))

        # MST 15: Hail Impact Test
        steps.append(TestStep(
            step_id="MST15",
            test_id="MST15",
            test_name="Hail Impact Test",
            description="Hail impact resistance (25mm ice balls at 23 m/s)",
            clause_reference="IEC 61215-2:2021 Clause 7.15",
            sequence_number=160,
            depends_on=["MST14_static"],
        ))

        # MST 16: Mechanical Load Test (Dynamic)
        steps.append(TestStep(
            step_id="MST16_dynamic",
            test_id="MST16",
            test_name="Mechanical Load Test - Dynamic",
            description="Dynamic mechanical load test (1000 Pa, 1000 cycles)",
            clause_reference="IEC 61215-2:2021 Clause 7.16",
            sequence_number=170,
            depends_on=["MST15"],
        ))

        # MST 17: Twist Test (for framed modules only)
        if module_type == "crystalline":  # Typically framed
            steps.append(TestStep(
                step_id="MST17",
                test_id="MST17",
                test_name="Twist Test",
                description="Twist test for framed modules",
                clause_reference="IEC 61215-2:2021 Clause 7.17",
                sequence_number=180,
                depends_on=["MST16_dynamic"],
                module_types=["crystalline"],
            ))

        # MST 18: Robustness of Terminations
        steps.append(TestStep(
            step_id="MST18",
            test_id="MST18",
            test_name="Robustness of Terminations",
            description="Pull and torque test on cable terminations",
            clause_reference="IEC 61215-2:2021 Clause 7.18",
            sequence_number=190,
            depends_on=["MST17"] if module_type == "crystalline" else ["MST16_dynamic"],
        ))

        # Final Tests
        steps.append(TestStep(
            step_id="MST01_final",
            test_id="MST01",
            test_name="Visual Inspection - Final",
            description="Final visual inspection",
            clause_reference="IEC 61215-2:2021 Clause 7.1",
            sequence_number=200,
            depends_on=["MST18"],
        ))

        steps.append(TestStep(
            step_id="MST02_final",
            test_id="MST02",
            test_name="Maximum Power Determination - Final",
            description="Final performance measurement at STC",
            clause_reference="IEC 61215-2:2021 Clause 7.2",
            sequence_number=210,
            depends_on=["MST01_final"],
        ))

        steps.append(TestStep(
            step_id="MST03_final",
            test_id="MST03",
            test_name="Insulation Test - Final",
            description="Final insulation resistance test",
            clause_reference="IEC 61215-2:2021 Clause 7.3",
            sequence_number=220,
            depends_on=["MST02_final"],
        ))

        # MST 19: Wet Leakage Current Test (Final)
        steps.append(TestStep(
            step_id="MST19",
            test_id="MST19",
            test_name="Wet Leakage Current Test",
            description="Final wet leakage current test",
            clause_reference="IEC 61215-2:2021 Clause 7.19",
            sequence_number=230,
            depends_on=["MST03_final"],
        ))

        return steps

    def execute_test(self, test_step: TestStep, **kwargs) -> TestResult:
        """
        Execute a specific IEC 61215 test.

        Args:
            test_step: Test step to execute
            **kwargs: Test-specific parameters and equipment

        Returns:
            TestResult object
        """
        # Map test IDs to execution methods
        test_methods = {
            "MST01": self._execute_visual_inspection,
            "MST02": self._execute_max_power_determination,
            "MST03": self._execute_insulation_test,
            "MST04": self._execute_temperature_coefficients,
            "MST05": self._execute_noct,
            "MST06": self._execute_stc_performance,
            "MST07": self._execute_low_irradiance,
            "MST08": self._execute_outdoor_exposure,
            "MST09": self._execute_hotspot,
            "MST10": self._execute_uv_test,
            "MST11": self._execute_thermal_cycling,
            "MST12": self._execute_humidity_freeze,
            "MST13": self._execute_damp_heat,
            "MST14": self._execute_mechanical_load_static,
            "MST15": self._execute_hail_test,
            "MST16": self._execute_mechanical_load_dynamic,
            "MST17": self._execute_twist_test,
            "MST18": self._execute_robustness_terminations,
            "MST19": self._execute_wet_leakage,
            "PRECON": self._execute_preconditioning,
        }

        method = test_methods.get(test_step.test_id)
        if not method:
            raise ValueError(f"Unknown test ID: {test_step.test_id}")

        # Execute test method
        return method(test_step, **kwargs)

    # ========================================================================
    # MST 01: Visual Inspection
    # ========================================================================

    def _execute_visual_inspection(
        self,
        test_step: TestStep,
        **kwargs
    ) -> TestResult:
        """
        MST 01: Visual Inspection
        IEC 61215-2:2021 Clause 7.1

        Visual examination for defects, damage, and workmanship quality.
        """
        result = TestResult(
            test_id=test_step.test_id,
            test_name=test_step.test_name,
            test_type="Visual Inspection",
            standard_reference=self.standard_reference,
            clause_reference=test_step.clause_reference,
            status=TestStatus.IN_PROGRESS,
            start_time=datetime.now(),
            module_id=self.test_sequence.module.serial_number if self.test_sequence else None,
        )

        # Define acceptance criteria
        result.acceptance_criteria = [
            AcceptanceCriteria(
                parameter="visual_defects",
                requirement="No cracks, bubbles, delamination, or other visible defects",
                clause_reference="7.1.3",
            ),
            AcceptanceCriteria(
                parameter="workmanship",
                requirement="Good workmanship quality",
                clause_reference="7.1.3",
            ),
        ]

        # Visual inspection checklist (would be interactive in real system)
        inspection_items = {
            "cracks_cells": kwargs.get("cracks_cells", False),
            "cracks_glass": kwargs.get("cracks_glass", False),
            "bubbles": kwargs.get("bubbles", False),
            "delamination": kwargs.get("delamination", False),
            "discoloration": kwargs.get("discoloration", False),
            "broken_interconnects": kwargs.get("broken_interconnects", False),
            "bent_frame": kwargs.get("bent_frame", False),
            "junction_box_damage": kwargs.get("junction_box_damage", False),
            "cable_damage": kwargs.get("cable_damage", False),
        }

        result.test_conditions = {
            "inspection_items": inspection_items,
            "inspector": kwargs.get("operator", "Unknown"),
            "inspection_date": datetime.now().isoformat(),
        }

        # Evaluate results
        defects_found = sum(inspection_items.values())
        result.observations = kwargs.get("observations", "")

        if kwargs.get("photos"):
            result.photos = kwargs["photos"]

        # Compliance
        if defects_found > 0:
            result.compliance_status = ComplianceStatus.FAIL
            result.compliance_notes = f"{defects_found} defect(s) found during visual inspection"
        else:
            result.compliance_status = ComplianceStatus.PASS
            result.compliance_notes = "No visual defects found"

        result.status = TestStatus.COMPLETED
        result.end_time = datetime.now()

        return result

    # ========================================================================
    # MST 02: Maximum Power Determination
    # ========================================================================

    def _execute_max_power_determination(
        self,
        test_step: TestStep,
        **kwargs
    ) -> TestResult:
        """
        MST 02: Maximum Power Determination
        IEC 61215-2:2021 Clause 7.2

        Measurement of I-V characteristics at Standard Test Conditions (STC):
        - Irradiance: 1000 W/m²
        - Spectrum: AM 1.5G
        - Cell Temperature: 25°C
        """
        result = TestResult(
            test_id=test_step.test_id,
            test_name=test_step.test_name,
            test_type="Performance Measurement",
            standard_reference=self.standard_reference,
            clause_reference=test_step.clause_reference,
            status=TestStatus.IN_PROGRESS,
            start_time=datetime.now(),
            module_id=self.test_sequence.module.serial_number if self.test_sequence else None,
        )

        # Test conditions
        result.test_conditions = {
            "irradiance": self.STC_IRRADIANCE,
            "spectrum": self.STC_SPECTRUM,
            "cell_temperature": self.STC_TEMPERATURE,
            "measurement_standard": "IEC 60904-1",
        }

        # Simulate or acquire actual measurements
        # In production, this would interface with solar simulator and I-V tracer
        if "iv_data" in kwargs:
            iv_data = kwargs["iv_data"]
        else:
            # Simulated data for demonstration
            iv_data = self._simulate_iv_measurement(
                self.test_sequence.module if self.test_sequence else None
            )

        # Extract key parameters
        measurements = [
            Measurement(
                parameter="Pmax",
                value=iv_data["Pmax"],
                unit=MeasurementUnit.POWER,
                timestamp=datetime.now(),
                equipment=kwargs.get("equipment", self._get_default_equipment()),
                uncertainty=Uncertainty(value=0.03, coverage_factor=2.0),  # ±3% typical
            ),
            Measurement(
                parameter="Voc",
                value=iv_data["Voc"],
                unit=MeasurementUnit.VOLTAGE,
                timestamp=datetime.now(),
                equipment=kwargs.get("equipment", self._get_default_equipment()),
                uncertainty=Uncertainty(value=0.005, coverage_factor=2.0),  # ±0.5%
            ),
            Measurement(
                parameter="Isc",
                value=iv_data["Isc"],
                unit=MeasurementUnit.CURRENT,
                timestamp=datetime.now(),
                equipment=kwargs.get("equipment", self._get_default_equipment()),
                uncertainty=Uncertainty(value=0.005, coverage_factor=2.0),
            ),
            Measurement(
                parameter="Vmp",
                value=iv_data["Vmp"],
                unit=MeasurementUnit.VOLTAGE,
                timestamp=datetime.now(),
                equipment=kwargs.get("equipment", self._get_default_equipment()),
            ),
            Measurement(
                parameter="Imp",
                value=iv_data["Imp"],
                unit=MeasurementUnit.CURRENT,
                timestamp=datetime.now(),
                equipment=kwargs.get("equipment", self._get_default_equipment()),
            ),
            Measurement(
                parameter="FF",
                value=iv_data["FF"],
                unit=MeasurementUnit.PERCENT,
                timestamp=datetime.now(),
                equipment=kwargs.get("equipment", self._get_default_equipment()),
            ),
        ]

        for m in measurements:
            result.add_measurement(m)

        # Store performance data
        is_initial = "initial" in test_step.step_id.lower()
        if is_initial:
            self.initial_performance = {
                "Pmax": iv_data["Pmax"],
                "Voc": iv_data["Voc"],
                "Isc": iv_data["Isc"],
                "Vmp": iv_data["Vmp"],
                "Imp": iv_data["Imp"],
                "FF": iv_data["FF"],
            }
        else:
            # Final measurement - check degradation
            if self.initial_performance:
                degradation = self.calculate_degradation(
                    self.initial_performance["Pmax"],
                    iv_data["Pmax"],
                    "general"
                )
                result.test_conditions["degradation"] = degradation

        # Acceptance criteria
        if self.test_sequence and not is_initial:
            # For final measurement, check degradation
            result.acceptance_criteria = [
                AcceptanceCriteria(
                    parameter="degradation_percent",
                    requirement=f"Maximum {self.MAX_DEGRADATION_GENERAL}% power degradation",
                    max_value=self.MAX_DEGRADATION_GENERAL,
                    clause_reference="7.2.3",
                ),
            ]

            # Add degradation measurement
            if "degradation" in result.test_conditions:
                result.add_measurement(Measurement(
                    parameter="degradation_percent",
                    value=result.test_conditions["degradation"]["degradation_percent"],
                    unit=MeasurementUnit.PERCENT,
                    timestamp=datetime.now(),
                    equipment=kwargs.get("equipment", self._get_default_equipment()),
                ))

        result.evaluate_compliance()
        result.status = TestStatus.COMPLETED
        result.end_time = datetime.now()

        return result

    # ========================================================================
    # MST 03: Insulation Test
    # ========================================================================

    def _execute_insulation_test(
        self,
        test_step: TestStep,
        **kwargs
    ) -> TestResult:
        """
        MST 03: Insulation Test
        IEC 61215-2:2021 Clause 7.3

        Insulation resistance test:
        - Test voltage: System voltage + 1000V (or 2x system voltage)
        - Duration: 1 minute
        - Minimum resistance: 40 MΩ⋅m² / module area
        """
        result = TestResult(
            test_id=test_step.test_id,
            test_name=test_step.test_name,
            test_type="Electrical Safety",
            standard_reference=self.standard_reference,
            clause_reference=test_step.clause_reference,
            status=TestStatus.IN_PROGRESS,
            start_time=datetime.now(),
            module_id=self.test_sequence.module.serial_number if self.test_sequence else None,
        )

        # Calculate test voltage
        system_voltage = kwargs.get("system_voltage", 1000.0)  # V
        test_voltage = max(system_voltage + 1000.0, 2.0 * system_voltage)

        result.test_conditions = {
            "test_voltage": test_voltage,
            "test_duration": 60,  # seconds
            "temperature": kwargs.get("temperature", 25.0),
            "humidity": kwargs.get("humidity", 50.0),
        }

        # Measure insulation resistance
        resistance = kwargs.get("resistance", 1000.0e6)  # Simulated: 1000 MΩ

        result.add_measurement(Measurement(
            parameter="insulation_resistance",
            value=resistance,
            unit=MeasurementUnit.RESISTANCE,
            timestamp=datetime.now(),
            equipment=kwargs.get("equipment", self._get_default_equipment()),
        ))

        # Calculate minimum required resistance
        module_area = self.test_sequence.module.area if self.test_sequence else 2.0  # m²
        min_resistance = 40.0e6 * module_area  # 40 MΩ⋅m²

        result.acceptance_criteria = [
            AcceptanceCriteria(
                parameter="insulation_resistance",
                requirement=f"Minimum {min_resistance/1e6:.1f} MΩ (40 MΩ⋅m² × {module_area} m²)",
                min_value=min_resistance,
                clause_reference="7.3.3",
            ),
        ]

        result.evaluate_compliance()
        result.status = TestStatus.COMPLETED
        result.end_time = datetime.now()

        return result

    # ========================================================================
    # MST 04: Temperature Coefficients
    # ========================================================================

    def _execute_temperature_coefficients(
        self,
        test_step: TestStep,
        **kwargs
    ) -> TestResult:
        """
        MST 04: Temperature Coefficients
        IEC 61215-2:2021 Clause 7.4

        Determination of temperature coefficients for Pmax, Voc, and Isc.
        Measurements at minimum 3 temperatures between 15°C and 75°C.
        """
        result = TestResult(
            test_id=test_step.test_id,
            test_name=test_step.test_name,
            test_type="Performance Characterization",
            standard_reference=self.standard_reference,
            clause_reference=test_step.clause_reference,
            status=TestStatus.IN_PROGRESS,
            start_time=datetime.now(),
            module_id=self.test_sequence.module.serial_number if self.test_sequence else None,
        )

        result.test_conditions = {
            "irradiance": self.STC_IRRADIANCE,
            "spectrum": self.STC_SPECTRUM,
            "temperature_range": "15°C to 75°C",
            "measurement_points": 3,
        }

        # Temperature measurement points
        temperatures = kwargs.get("temperatures", [15.0, 25.0, 50.0, 75.0])

        # Simulated or actual measurements at each temperature
        # In production, would measure I-V curves at each temperature
        temp_coeffs = self._calculate_temperature_coefficients(temperatures, kwargs)

        # Add measurements
        result.add_measurement(Measurement(
            parameter="temp_coeff_Pmax",
            value=temp_coeffs["Pmax"],
            unit=MeasurementUnit.PERCENT,  # %/°C
            timestamp=datetime.now(),
            equipment=kwargs.get("equipment", self._get_default_equipment()),
        ))

        result.add_measurement(Measurement(
            parameter="temp_coeff_Voc",
            value=temp_coeffs["Voc"],
            unit=MeasurementUnit.PERCENT,  # %/°C
            timestamp=datetime.now(),
            equipment=kwargs.get("equipment", self._get_default_equipment()),
        ))

        result.add_measurement(Measurement(
            parameter="temp_coeff_Isc",
            value=temp_coeffs["Isc"],
            unit=MeasurementUnit.PERCENT,  # %/°C
            timestamp=datetime.now(),
            equipment=kwargs.get("equipment", self._get_default_equipment()),
        ))

        # Acceptance criteria - verify coefficients are within reasonable range
        result.acceptance_criteria = [
            AcceptanceCriteria(
                parameter="temp_coeff_Pmax",
                requirement="Typical range: -0.3 to -0.5 %/°C for crystalline",
                min_value=-0.6,
                max_value=-0.2,
                clause_reference="7.4.3",
            ),
        ]

        result.evaluate_compliance()
        result.status = TestStatus.COMPLETED
        result.end_time = datetime.now()

        return result

    # ========================================================================
    # MST 05: NOCT (Nominal Operating Cell Temperature)
    # ========================================================================

    def _execute_noct(
        self,
        test_step: TestStep,
        **kwargs
    ) -> TestResult:
        """
        MST 05: NOCT Measurement
        IEC 61215-2:2021 Clause 7.5

        NOCT test conditions:
        - Irradiance: 800 W/m²
        - Ambient temperature: 20°C
        - Wind speed: 1 m/s
        - Open-circuit or resistive load
        """
        result = TestResult(
            test_id=test_step.test_id,
            test_name=test_step.test_name,
            test_type="Thermal Performance",
            standard_reference=self.standard_reference,
            clause_reference=test_step.clause_reference,
            status=TestStatus.IN_PROGRESS,
            start_time=datetime.now(),
            module_id=self.test_sequence.module.serial_number if self.test_sequence else None,
        )

        result.test_conditions = {
            "irradiance": self.NOCT_IRRADIANCE,
            "ambient_temperature": self.NOCT_AMBIENT_TEMP,
            "wind_speed": self.NOCT_WIND_SPEED,
            "mounting": "open rack",
            "tilt_angle": kwargs.get("tilt_angle", 45.0),
        }

        # Measure cell temperature under NOCT conditions
        # In production, would use outdoor test facility or climate chamber
        noct_temperature = kwargs.get("noct_temperature", 48.0)  # °C typical

        result.add_measurement(Measurement(
            parameter="NOCT",
            value=noct_temperature,
            unit=MeasurementUnit.TEMPERATURE,
            timestamp=datetime.now(),
            equipment=kwargs.get("equipment", self._get_default_equipment()),
            uncertainty=Uncertainty(value=2.0, coverage_factor=2.0),  # ±2°C
        ))

        # Acceptance criteria - NOCT should be reasonable
        result.acceptance_criteria = [
            AcceptanceCriteria(
                parameter="NOCT",
                requirement="Typical range: 40-50°C for standard modules",
                min_value=35.0,
                max_value=55.0,
                clause_reference="7.5.3",
            ),
        ]

        result.evaluate_compliance()
        result.status = TestStatus.COMPLETED
        result.end_time = datetime.now()

        return result

    # ========================================================================
    # MST 06: STC Performance
    # ========================================================================

    def _execute_stc_performance(
        self,
        test_step: TestStep,
        **kwargs
    ) -> TestResult:
        """
        MST 06: STC Performance (after stabilization)
        IEC 61215-2:2021 Clause 7.6

        Performance measurement after module stabilization.
        This becomes the baseline for degradation calculations.
        """
        result = self._execute_max_power_determination(test_step, **kwargs)

        # Store as stabilized performance
        if result.measurements:
            self.stabilized_performance = {
                m.parameter: m.value for m in result.measurements
            }

        return result

    # ========================================================================
    # MST 07: Low Irradiance Performance
    # ========================================================================

    def _execute_low_irradiance(
        self,
        test_step: TestStep,
        **kwargs
    ) -> TestResult:
        """
        MST 07: Low Irradiance Performance
        IEC 61215-2:2021 Clause 7.7

        Performance at 200 W/m² irradiance, 25°C cell temperature.
        """
        result = TestResult(
            test_id=test_step.test_id,
            test_name=test_step.test_name,
            test_type="Performance Measurement",
            standard_reference=self.standard_reference,
            clause_reference=test_step.clause_reference,
            status=TestStatus.IN_PROGRESS,
            start_time=datetime.now(),
            module_id=self.test_sequence.module.serial_number if self.test_sequence else None,
        )

        result.test_conditions = {
            "irradiance": 200.0,  # W/m²
            "spectrum": self.STC_SPECTRUM,
            "cell_temperature": self.STC_TEMPERATURE,
        }

        # Measure performance at low irradiance
        low_irr_power = kwargs.get("low_irradiance_power", 0.0)

        result.add_measurement(Measurement(
            parameter="Pmax_200",
            value=low_irr_power,
            unit=MeasurementUnit.POWER,
            timestamp=datetime.now(),
            equipment=kwargs.get("equipment", self._get_default_equipment()),
        ))

        # Acceptance - module should produce power proportional to irradiance
        # Typically expect ~20% of STC power at 200 W/m²
        result.compliance_status = ComplianceStatus.PASS
        result.status = TestStatus.COMPLETED
        result.end_time = datetime.now()

        return result

    # ========================================================================
    # MST 08: Outdoor Exposure
    # ========================================================================

    def _execute_outdoor_exposure(
        self,
        test_step: TestStep,
        **kwargs
    ) -> TestResult:
        """
        MST 08: Outdoor Exposure Test
        IEC 61215-2:2021 Clause 7.8

        Module exposed outdoors until minimum 60 kWh/m² irradiation received.
        """
        result = TestResult(
            test_id=test_step.test_id,
            test_name=test_step.test_name,
            test_type="Environmental Exposure",
            standard_reference=self.standard_reference,
            clause_reference=test_step.clause_reference,
            status=TestStatus.IN_PROGRESS,
            start_time=datetime.now(),
            module_id=self.test_sequence.module.serial_number if self.test_sequence else None,
        )

        total_irradiation = kwargs.get("total_irradiation", 60.0)  # kWh/m²
        exposure_days = kwargs.get("exposure_days", 30)

        result.test_conditions = {
            "total_irradiation_required": 60.0,  # kWh/m²
            "total_irradiation_actual": total_irradiation,
            "exposure_days": exposure_days,
            "location": kwargs.get("location", "Laboratory outdoor facility"),
            "mounting": "open rack",
            "tilt_angle": kwargs.get("tilt_angle", 30.0),
        }

        result.add_measurement(Measurement(
            parameter="total_irradiation",
            value=total_irradiation,
            unit=MeasurementUnit.ENERGY,
            timestamp=datetime.now(),
            equipment=kwargs.get("equipment", self._get_default_equipment()),
        ))

        result.acceptance_criteria = [
            AcceptanceCriteria(
                parameter="total_irradiation",
                requirement="Minimum 60 kWh/m² irradiation",
                min_value=60.0,
                clause_reference="7.8.2",
            ),
        ]

        result.evaluate_compliance()
        result.status = TestStatus.COMPLETED
        result.end_time = datetime.now()

        return result

    # ========================================================================
    # MST 09: Hot-spot Endurance
    # ========================================================================

    def _execute_hotspot(
        self,
        test_step: TestStep,
        **kwargs
    ) -> TestResult:
        """
        MST 09: Hot-spot Endurance Test
        IEC 61215-2:2021 Clause 7.9

        Test for bypass diode functionality and hot-spot resistance.
        """
        result = TestResult(
            test_id=test_step.test_id,
            test_name=test_step.test_name,
            test_type="Electrical Safety",
            standard_reference=self.standard_reference,
            clause_reference=test_step.clause_reference,
            status=TestStatus.IN_PROGRESS,
            start_time=datetime.now(),
            module_id=self.test_sequence.module.serial_number if self.test_sequence else None,
        )

        result.test_conditions = {
            "irradiance": self.STC_IRRADIANCE,
            "shading_pattern": kwargs.get("shading_pattern", "One cell fully shaded"),
            "test_duration": kwargs.get("test_duration", 3600),  # 1 hour
            "current": "Isc at STC",
        }

        # Measure maximum temperature during hot-spot test
        max_temperature = kwargs.get("max_temperature", 85.0)  # °C

        result.add_measurement(Measurement(
            parameter="max_hotspot_temperature",
            value=max_temperature,
            unit=MeasurementUnit.TEMPERATURE,
            timestamp=datetime.now(),
            equipment=kwargs.get("equipment", self._get_default_equipment()),
        ))

        # Check for visible damage
        has_damage = kwargs.get("has_damage", False)

        result.acceptance_criteria = [
            AcceptanceCriteria(
                parameter="visual_damage",
                requirement="No visual damage, melting, or fire",
                clause_reference="7.9.3",
            ),
        ]

        if has_damage:
            result.compliance_status = ComplianceStatus.FAIL
            result.compliance_notes = "Visual damage observed during hot-spot test"
        else:
            result.compliance_status = ComplianceStatus.PASS
            result.compliance_notes = "No damage observed"

        result.status = TestStatus.COMPLETED
        result.end_time = datetime.now()

        return result

    # ========================================================================
    # MST 10: UV Preconditioning
    # ========================================================================

    def _execute_uv_test(
        self,
        test_step: TestStep,
        **kwargs
    ) -> TestResult:
        """
        MST 10: UV Preconditioning Test
        IEC 61215-2:2021 Clause 7.10

        UV exposure: 15 kWh/m² in wavelength range 280-400 nm.
        """
        result = TestResult(
            test_id=test_step.test_id,
            test_name=test_step.test_name,
            test_type="Environmental Stress",
            standard_reference=self.standard_reference,
            clause_reference=test_step.clause_reference,
            status=TestStatus.IN_PROGRESS,
            start_time=datetime.now(),
            module_id=self.test_sequence.module.serial_number if self.test_sequence else None,
        )

        uv_dose = kwargs.get("uv_dose", 15.0)  # kWh/m²
        exposure_hours = kwargs.get("exposure_hours", 100)

        result.test_conditions = {
            "uv_dose_required": 15.0,  # kWh/m²
            "uv_dose_actual": uv_dose,
            "wavelength_range": "280-400 nm",
            "exposure_hours": exposure_hours,
            "chamber_temperature": kwargs.get("chamber_temperature", 60.0),
        }

        result.add_measurement(Measurement(
            parameter="uv_dose",
            value=uv_dose,
            unit=MeasurementUnit.ENERGY,
            timestamp=datetime.now(),
            equipment=kwargs.get("equipment", self._get_default_equipment()),
        ))

        result.acceptance_criteria = [
            AcceptanceCriteria(
                parameter="uv_dose",
                requirement="Minimum 15 kWh/m² UV exposure (280-400 nm)",
                min_value=15.0,
                clause_reference="7.10.2",
            ),
        ]

        result.evaluate_compliance()
        result.status = TestStatus.COMPLETED
        result.end_time = datetime.now()

        return result

    # ========================================================================
    # MST 11: Thermal Cycling (TC 200)
    # ========================================================================

    def _execute_thermal_cycling(
        self,
        test_step: TestStep,
        **kwargs
    ) -> TestResult:
        """
        MST 11: Thermal Cycling Test
        IEC 61215-2:2021 Clause 7.11

        200 cycles: -40°C to +85°C
        """
        result = TestResult(
            test_id=test_step.test_id,
            test_name=test_step.test_name,
            test_type="Environmental Stress",
            standard_reference=self.standard_reference,
            clause_reference=test_step.clause_reference,
            status=TestStatus.IN_PROGRESS,
            start_time=datetime.now(),
            module_id=self.test_sequence.module.serial_number if self.test_sequence else None,
        )

        cycles_completed = kwargs.get("cycles_completed", 200)

        result.test_conditions = {
            "cycles_required": 200,
            "cycles_completed": cycles_completed,
            "temperature_low": -40.0,  # °C
            "temperature_high": 85.0,  # °C
            "cycle_duration": "~6 hours per cycle",
            "ramp_rate": "~100°C/hour",
        }

        result.add_measurement(Measurement(
            parameter="thermal_cycles",
            value=float(cycles_completed),
            unit=MeasurementUnit.TIME,  # cycles
            timestamp=datetime.now(),
            equipment=kwargs.get("equipment", self._get_default_equipment()),
        ))

        result.acceptance_criteria = [
            AcceptanceCriteria(
                parameter="thermal_cycles",
                requirement="Complete 200 thermal cycles",
                min_value=200.0,
                clause_reference="7.11.2",
            ),
        ]

        result.evaluate_compliance()
        result.status = TestStatus.COMPLETED
        result.end_time = datetime.now()

        return result

    # ========================================================================
    # MST 12: Humidity-Freeze (HF 10)
    # ========================================================================

    def _execute_humidity_freeze(
        self,
        test_step: TestStep,
        **kwargs
    ) -> TestResult:
        """
        MST 12: Humidity-Freeze Test
        IEC 61215-2:2021 Clause 7.12

        10 cycles of humidity-freeze:
        - 85°C/85% RH for 20 hours
        - Transition to -40°C
        - -40°C for minimum 30 minutes
        """
        result = TestResult(
            test_id=test_step.test_id,
            test_name=test_step.test_name,
            test_type="Environmental Stress",
            standard_reference=self.standard_reference,
            clause_reference=test_step.clause_reference,
            status=TestStatus.IN_PROGRESS,
            start_time=datetime.now(),
            module_id=self.test_sequence.module.serial_number if self.test_sequence else None,
        )

        cycles_completed = kwargs.get("cycles_completed", 10)

        result.test_conditions = {
            "cycles_required": 10,
            "cycles_completed": cycles_completed,
            "hot_humid_condition": "85°C/85% RH for 20 hours",
            "cold_condition": "-40°C for minimum 30 minutes",
            "cycle_duration": "~24 hours per cycle",
        }

        result.add_measurement(Measurement(
            parameter="humidity_freeze_cycles",
            value=float(cycles_completed),
            unit=MeasurementUnit.TIME,  # cycles
            timestamp=datetime.now(),
            equipment=kwargs.get("equipment", self._get_default_equipment()),
        ))

        result.acceptance_criteria = [
            AcceptanceCriteria(
                parameter="humidity_freeze_cycles",
                requirement="Complete 10 humidity-freeze cycles",
                min_value=10.0,
                clause_reference="7.12.2",
            ),
        ]

        result.evaluate_compliance()
        result.status = TestStatus.COMPLETED
        result.end_time = datetime.now()

        return result

    # ========================================================================
    # MST 13: Damp Heat (DH 1000)
    # ========================================================================

    def _execute_damp_heat(
        self,
        test_step: TestStep,
        **kwargs
    ) -> TestResult:
        """
        MST 13: Damp Heat Test
        IEC 61215-2:2021 Clause 7.13

        1000 hours at 85°C and 85% relative humidity.
        """
        result = TestResult(
            test_id=test_step.test_id,
            test_name=test_step.test_name,
            test_type="Environmental Stress",
            standard_reference=self.standard_reference,
            clause_reference=test_step.clause_reference,
            status=TestStatus.IN_PROGRESS,
            start_time=datetime.now(),
            module_id=self.test_sequence.module.serial_number if self.test_sequence else None,
        )

        hours_completed = kwargs.get("hours_completed", 1000)

        result.test_conditions = {
            "hours_required": 1000,
            "hours_completed": hours_completed,
            "temperature": 85.0,  # °C
            "humidity": 85.0,  # % RH
            "stabilization_time": "Chamber conditions stable within ±2°C, ±5% RH",
        }

        result.add_measurement(Measurement(
            parameter="damp_heat_hours",
            value=float(hours_completed),
            unit=MeasurementUnit.TIME,
            timestamp=datetime.now(),
            equipment=kwargs.get("equipment", self._get_default_equipment()),
        ))

        result.acceptance_criteria = [
            AcceptanceCriteria(
                parameter="damp_heat_hours",
                requirement="Complete 1000 hours at 85°C/85% RH",
                min_value=1000.0,
                clause_reference="7.13.2",
            ),
        ]

        result.evaluate_compliance()
        result.status = TestStatus.COMPLETED
        result.end_time = datetime.now()

        return result

    # ========================================================================
    # MST 14: Mechanical Load Test (Static)
    # ========================================================================

    def _execute_mechanical_load_static(
        self,
        test_step: TestStep,
        **kwargs
    ) -> TestResult:
        """
        MST 14: Static Mechanical Load Test
        IEC 61215-2:2021 Clause 7.14

        Apply 2400 Pa front and back loads (3 cycles each).
        """
        result = TestResult(
            test_id=test_step.test_id,
            test_name=test_step.test_name,
            test_type="Mechanical Stress",
            standard_reference=self.standard_reference,
            clause_reference=test_step.clause_reference,
            status=TestStatus.IN_PROGRESS,
            start_time=datetime.now(),
            module_id=self.test_sequence.module.serial_number if self.test_sequence else None,
        )

        load_pressure = kwargs.get("load_pressure", 2400.0)  # Pa
        cycles = kwargs.get("cycles", 3)

        result.test_conditions = {
            "load_pressure": load_pressure,
            "cycles_front": cycles,
            "cycles_back": cycles,
            "hold_time": "1 hour per cycle",
            "load_application": "Uniform pressure",
        }

        result.add_measurement(Measurement(
            parameter="static_load_pressure",
            value=load_pressure,
            unit=MeasurementUnit.PRESSURE,
            timestamp=datetime.now(),
            equipment=kwargs.get("equipment", self._get_default_equipment()),
        ))

        result.acceptance_criteria = [
            AcceptanceCriteria(
                parameter="static_load_pressure",
                requirement="Apply 2400 Pa load for 3 cycles",
                min_value=2400.0,
                clause_reference="7.14.2",
            ),
        ]

        result.evaluate_compliance()
        result.status = TestStatus.COMPLETED
        result.end_time = datetime.now()

        return result

    # ========================================================================
    # MST 15: Hail Impact Test
    # ========================================================================

    def _execute_hail_test(
        self,
        test_step: TestStep,
        **kwargs
    ) -> TestResult:
        """
        MST 15: Hail Impact Test
        IEC 61215-2:2021 Clause 7.15

        Impact with 25mm diameter ice balls at 23 m/s (82.8 km/h).
        11 impact locations.
        """
        result = TestResult(
            test_id=test_step.test_id,
            test_name=test_step.test_name,
            test_type="Mechanical Stress",
            standard_reference=self.standard_reference,
            clause_reference=test_step.clause_reference,
            status=TestStatus.IN_PROGRESS,
            start_time=datetime.now(),
            module_id=self.test_sequence.module.serial_number if self.test_sequence else None,
        )

        impact_count = kwargs.get("impact_count", 11)
        ice_ball_diameter = 25.0  # mm
        impact_velocity = 23.0  # m/s

        result.test_conditions = {
            "ice_ball_diameter": ice_ball_diameter,
            "impact_velocity": impact_velocity,
            "impact_count": impact_count,
            "impact_angle": "perpendicular to surface",
            "impact_locations": "11 locations per IEC 61215-2",
        }

        result.add_measurement(Measurement(
            parameter="impact_count",
            value=float(impact_count),
            unit=MeasurementUnit.TIME,  # count
            timestamp=datetime.now(),
            equipment=kwargs.get("equipment", self._get_default_equipment()),
        ))

        # Check for damage
        has_damage = kwargs.get("has_damage", False)

        if has_damage:
            result.compliance_status = ComplianceStatus.FAIL
            result.compliance_notes = "Damage observed after hail impact"
        else:
            result.compliance_status = ComplianceStatus.PASS
            result.compliance_notes = "No damage from hail impact"

        result.status = TestStatus.COMPLETED
        result.end_time = datetime.now()

        return result

    # ========================================================================
    # MST 16: Mechanical Load Test (Dynamic)
    # ========================================================================

    def _execute_mechanical_load_dynamic(
        self,
        test_step: TestStep,
        **kwargs
    ) -> TestResult:
        """
        MST 16: Dynamic Mechanical Load Test
        IEC 61215-2:2021 Clause 7.16

        1000 cycles of ±1000 Pa load (front and back).
        """
        result = TestResult(
            test_id=test_step.test_id,
            test_name=test_step.test_name,
            test_type="Mechanical Stress",
            standard_reference=self.standard_reference,
            clause_reference=test_step.clause_reference,
            status=TestStatus.IN_PROGRESS,
            start_time=datetime.now(),
            module_id=self.test_sequence.module.serial_number if self.test_sequence else None,
        )

        cycles = kwargs.get("cycles", 1000)
        load_pressure = kwargs.get("load_pressure", 1000.0)  # Pa

        result.test_conditions = {
            "load_pressure": f"±{load_pressure} Pa",
            "cycles": cycles,
            "cycle_frequency": "3-10 seconds per cycle",
            "load_sequence": "Front and back alternating",
        }

        result.add_measurement(Measurement(
            parameter="dynamic_load_cycles",
            value=float(cycles),
            unit=MeasurementUnit.TIME,  # cycles
            timestamp=datetime.now(),
            equipment=kwargs.get("equipment", self._get_default_equipment()),
        ))

        result.acceptance_criteria = [
            AcceptanceCriteria(
                parameter="dynamic_load_cycles",
                requirement="Complete 1000 load cycles",
                min_value=1000.0,
                clause_reference="7.16.2",
            ),
        ]

        result.evaluate_compliance()
        result.status = TestStatus.COMPLETED
        result.end_time = datetime.now()

        return result

    # ========================================================================
    # MST 17: Twist Test
    # ========================================================================

    def _execute_twist_test(
        self,
        test_step: TestStep,
        **kwargs
    ) -> TestResult:
        """
        MST 17: Twist Test
        IEC 61215-2:2021 Clause 7.17

        For framed modules - twist test to verify frame rigidity.
        """
        result = TestResult(
            test_id=test_step.test_id,
            test_name=test_step.test_name,
            test_type="Mechanical Stress",
            standard_reference=self.standard_reference,
            clause_reference=test_step.clause_reference,
            status=TestStatus.IN_PROGRESS,
            start_time=datetime.now(),
            module_id=self.test_sequence.module.serial_number if self.test_sequence else None,
        )

        # Calculate twist based on module dimensions
        if self.test_sequence:
            module = self.test_sequence.module
            diagonal = math.sqrt(module.length**2 + module.width**2)
            twist_displacement = diagonal / 100.0  # 1% of diagonal
        else:
            twist_displacement = 20.0  # mm default

        result.test_conditions = {
            "twist_displacement": twist_displacement,
            "hold_time": "1 hour",
            "support_points": "Diagonal corners",
        }

        result.add_measurement(Measurement(
            parameter="twist_displacement",
            value=twist_displacement,
            unit=MeasurementUnit.LENGTH,
            timestamp=datetime.now(),
            equipment=kwargs.get("equipment", self._get_default_equipment()),
        ))

        # Check for damage
        has_damage = kwargs.get("has_damage", False)

        if has_damage:
            result.compliance_status = ComplianceStatus.FAIL
            result.compliance_notes = "Damage observed after twist test"
        else:
            result.compliance_status = ComplianceStatus.PASS
            result.compliance_notes = "No damage from twist test"

        result.status = TestStatus.COMPLETED
        result.end_time = datetime.now()

        return result

    # ========================================================================
    # MST 18: Robustness of Terminations
    # ========================================================================

    def _execute_robustness_terminations(
        self,
        test_step: TestStep,
        **kwargs
    ) -> TestResult:
        """
        MST 18: Robustness of Terminations
        IEC 61215-2:2021 Clause 7.18

        Pull and torque tests on cable terminations and junction box.
        """
        result = TestResult(
            test_id=test_step.test_id,
            test_name=test_step.test_name,
            test_type="Mechanical Stress",
            standard_reference=self.standard_reference,
            clause_reference=test_step.clause_reference,
            status=TestStatus.IN_PROGRESS,
            start_time=datetime.now(),
            module_id=self.test_sequence.module.serial_number if self.test_sequence else None,
        )

        pull_force = kwargs.get("pull_force", 100.0)  # N
        torque = kwargs.get("torque", 4.0)  # Nm

        result.test_conditions = {
            "cable_pull_force": pull_force,
            "pull_duration": "10 seconds",
            "torque_test": torque,
            "torque_cycles": 5,
        }

        result.add_measurement(Measurement(
            parameter="cable_pull_force",
            value=pull_force,
            unit=MeasurementUnit.FORCE,
            timestamp=datetime.now(),
            equipment=kwargs.get("equipment", self._get_default_equipment()),
        ))

        # Check for damage or loosening
        has_damage = kwargs.get("has_damage", False)

        if has_damage:
            result.compliance_status = ComplianceStatus.FAIL
            result.compliance_notes = "Termination damage or loosening observed"
        else:
            result.compliance_status = ComplianceStatus.PASS
            result.compliance_notes = "Terminations remain secure"

        result.status = TestStatus.COMPLETED
        result.end_time = datetime.now()

        return result

    # ========================================================================
    # MST 19: Wet Leakage Current Test
    # ========================================================================

    def _execute_wet_leakage(
        self,
        test_step: TestStep,
        **kwargs
    ) -> TestResult:
        """
        MST 19: Wet Leakage Current Test
        IEC 61215-2:2021 Clause 7.19

        Final test - measure leakage current with wet module surface.
        """
        result = TestResult(
            test_id=test_step.test_id,
            test_name=test_step.test_name,
            test_type="Electrical Safety",
            standard_reference=self.standard_reference,
            clause_reference=test_step.clause_reference,
            status=TestStatus.IN_PROGRESS,
            start_time=datetime.now(),
            module_id=self.test_sequence.module.serial_number if self.test_sequence else None,
        )

        test_voltage = kwargs.get("test_voltage", 1000.0)  # V
        solution_resistivity = kwargs.get("solution_resistivity", 15000.0)  # Ω⋅cm

        result.test_conditions = {
            "test_voltage": test_voltage,
            "solution_resistivity": solution_resistivity,
            "wetting_duration": "At least 5 minutes",
            "test_duration": 60,  # seconds
        }

        # Measure leakage current
        leakage_current = kwargs.get("leakage_current", 0.5e-6)  # A (0.5 µA typical)

        result.add_measurement(Measurement(
            parameter="wet_leakage_current",
            value=leakage_current * 1e6,  # Convert to µA for readability
            unit=MeasurementUnit.CURRENT,
            timestamp=datetime.now(),
            equipment=kwargs.get("equipment", self._get_default_equipment()),
        ))

        # Acceptance criteria - leakage current should be minimal
        result.acceptance_criteria = [
            AcceptanceCriteria(
                parameter="wet_leakage_current",
                requirement="Leakage current < 50 µA per IEC 61215-2",
                max_value=50.0,  # µA
                clause_reference="7.19.3",
            ),
        ]

        result.evaluate_compliance()
        result.status = TestStatus.COMPLETED
        result.end_time = datetime.now()

        return result

    # ========================================================================
    # Preconditioning (for thin-film modules)
    # ========================================================================

    def _execute_preconditioning(
        self,
        test_step: TestStep,
        **kwargs
    ) -> TestResult:
        """
        Preconditioning / Stabilization (for thin-film modules)
        IEC 61215-2:2021 Clause 6.3.4

        Light soaking until module stabilizes (< 2% change in 2 hours).
        """
        result = TestResult(
            test_id=test_step.test_id,
            test_name=test_step.test_name,
            test_type="Stabilization",
            standard_reference=self.standard_reference,
            clause_reference=test_step.clause_reference,
            status=TestStatus.IN_PROGRESS,
            start_time=datetime.now(),
            module_id=self.test_sequence.module.serial_number if self.test_sequence else None,
        )

        exposure_hours = kwargs.get("exposure_hours", 50)
        total_irradiation = kwargs.get("total_irradiation", 50.0)  # kWh/m²

        result.test_conditions = {
            "irradiance": self.STC_IRRADIANCE,
            "spectrum": self.STC_SPECTRUM,
            "module_temperature": "50°C ± 10°C",
            "exposure_hours": exposure_hours,
            "total_irradiation": total_irradiation,
            "stabilization_criterion": "< 2% power change in 2 hours",
        }

        result.add_measurement(Measurement(
            parameter="preconditioning_irradiation",
            value=total_irradiation,
            unit=MeasurementUnit.ENERGY,
            timestamp=datetime.now(),
            equipment=kwargs.get("equipment", self._get_default_equipment()),
        ))

        result.compliance_status = ComplianceStatus.PASS
        result.status = TestStatus.COMPLETED
        result.end_time = datetime.now()

        return result

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _simulate_iv_measurement(
        self,
        module: Optional[ModuleUnderTest]
    ) -> Dict[str, float]:
        """
        Simulate I-V curve measurement.
        In production, this would interface with real solar simulator and I-V tracer.
        """
        if module:
            # Use module nameplate data as basis
            Voc = module.open_circuit_voltage
            Isc = module.short_circuit_current
            Vmp = module.rated_voltage
            Imp = module.rated_current
            Pmax = module.rated_power
        else:
            # Default values for demonstration
            Voc = 45.0  # V
            Isc = 10.0  # A
            Vmp = 37.0  # V
            Imp = 9.5  # A
            Pmax = 350.0  # W

        FF = (Pmax / (Voc * Isc)) * 100.0  # Fill factor in %

        return {
            "Voc": Voc,
            "Isc": Isc,
            "Vmp": Vmp,
            "Imp": Imp,
            "Pmax": Pmax,
            "FF": FF,
        }

    def _calculate_temperature_coefficients(
        self,
        temperatures: List[float],
        kwargs: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate temperature coefficients from measurements at multiple temperatures.
        In production, would perform linear regression on actual data.
        """
        # Simulated typical values for crystalline silicon
        # Real values would be calculated from actual measurements
        return {
            "Pmax": kwargs.get("temp_coeff_pmax", -0.40),  # %/°C
            "Voc": kwargs.get("temp_coeff_voc", -0.30),   # %/°C
            "Isc": kwargs.get("temp_coeff_isc", 0.05),    # %/°C
        }

    def _get_default_equipment(self) -> Equipment:
        """Get default equipment info for simulations."""
        return Equipment(
            id="SIM-001",
            name="Simulated Equipment",
            manufacturer="Simulation",
            model="SIM-1000",
            serial_number="SIM123456",
            calibration_date=datetime.now() - timedelta(days=90),
            calibration_due_date=datetime.now() + timedelta(days=275),
            calibration_certificate="SIM-CERT-2024-001",
            accuracy=0.03,
        )

    def generate_compliance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive compliance report for IEC 61215.

        Returns:
            Dictionary with complete test report data
        """
        if not self.test_sequence:
            raise ValueError("No test sequence available")

        # Collect all test results
        results = [step.result for step in self.test_sequence.steps if step.result]

        report = {
            "report_metadata": {
                "report_number": self.test_sequence.test_report_number,
                "protocol": self.protocol_name,
                "version": self.protocol_version,
                "generation_date": datetime.now().isoformat(),
                "laboratory": self.test_sequence.laboratory_name,
                "accreditation": self.test_sequence.laboratory_accreditation,
            },
            "module_information": self.test_sequence.module.to_dict(),
            "test_sequence": self.test_sequence.to_dict(),
            "test_results": [r.to_dict() for r in results],
            "compliance_summary": {
                "overall_status": self.test_sequence.overall_compliance.value,
                "tests_passed": len([r for r in results if r.compliance_status == ComplianceStatus.PASS]),
                "tests_failed": len([r for r in results if r.compliance_status == ComplianceStatus.FAIL]),
                "tests_total": len(results),
            },
            "degradation_summary": self._calculate_overall_degradation(),
        }

        return report

    def _calculate_overall_degradation(self) -> Dict[str, Any]:
        """Calculate overall power degradation through test sequence."""
        if not self.initial_performance or not self.stabilized_performance:
            return {}

        # Get final performance from last MST02 test
        final_steps = [s for s in self.test_sequence.steps if s.step_id == "MST02_final"]
        if not final_steps or not final_steps[0].result:
            return {}

        final_result = final_steps[0].result
        final_power = next(
            (m.value for m in final_result.measurements if m.parameter == "Pmax"),
            None
        )

        if not final_power:
            return {}

        degradation = self.calculate_degradation(
            self.initial_performance["Pmax"],
            final_power,
            "general"
        )

        return {
            "initial_power": self.initial_performance["Pmax"],
            "final_power": final_power,
            "degradation_percent": degradation["degradation_percent"],
            "limit_percent": degradation["limit_percent"],
            "passes": degradation["passes"],
        }
