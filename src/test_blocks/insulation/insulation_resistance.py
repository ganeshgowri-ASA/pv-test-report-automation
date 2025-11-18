"""Insulation Resistance Test Implementation

Standards:
- IEC 61215-2:2016 Section 10.x - Insulation test
- IEC 61730-2:2016 MST 01 - Wet leakage current test

Test Procedure:
1. Wet soaking: 24h water immersion
2. Apply DC test voltage (500V or 1000V)
3. Measure resistance after 1 minute stabilization
4. Record resistance, polarity, environmental conditions
5. Evaluate against pass/fail criteria

Pass Criteria:
- Wet condition: ≥ 40 MΩ
- Dry condition: ≥ 400 MΩ
"""

from datetime import datetime
from typing import Literal, Optional, Dict, Any, List
from pydantic import BaseModel, Field
import uuid

from ...models.test_block import BaseTestBlock, ComplianceData, TestBlockStatus
from ...models.measurement import EnvironmentalConditions, MeasurementResult
from ...equipment.megohmmeter import Megohmmeter, MegohmeterSimulator
from ...logging.data_logger import TestDataLogger
from ...compliance.iso17025 import ISO17025Logger, ISO17025Record, MeasurementUncertainty


class InsulationTest(BaseModel):
    """Individual insulation resistance measurement

    Model as specified in requirements
    """
    test_id: int = Field(..., description="Sequential test identifier")
    module_id: int = Field(..., description="PV module identifier")
    test_voltage: int = Field(..., description="Test voltage: 500 or 1000V")
    condition: str = Field(..., description="Test condition: 'wet' or 'dry'")
    resistance_mohm: float = Field(..., description="Measured resistance in MΩ")
    polarity: str = Field(..., description="Test polarity: 'positive' or 'negative'")
    pass_status: bool = Field(..., description="Pass/fail status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class InsulationTestResult(BaseModel):
    """Complete insulation test result"""
    test: InsulationTest
    environmental_conditions: Optional[EnvironmentalConditions] = None
    measurement_result: Optional[MeasurementResult] = None
    notes: Optional[str] = None


class InsulationResistanceTest:
    """
    Insulation Resistance Test Block

    Automated test sequence for measuring insulation resistance
    per IEC 61215/61730 standards.

    Features:
    - Automated test sequence
    - Equipment integration (Megohmmeter)
    - Pass/fail logic per IEC standards
    - Data logging
    - ISO 17025 compliance

    Example:
        >>> from test_blocks.insulation import InsulationResistanceTest
        >>> test = InsulationResistanceTest(module="PV-001")
        >>> result = test.measure(voltage=1000, condition="wet")
        >>> print(f"Resistance: {result.resistance_mohm} MΩ")
    """

    # Pass/fail criteria per IEC standards
    WET_MINIMUM_RESISTANCE_MOHM = 40.0  # MΩ
    DRY_MINIMUM_RESISTANCE_MOHM = 400.0  # MΩ

    def __init__(
        self,
        module: str,
        test_block_id: Optional[str] = None,
        megohmmeter: Optional[Megohmmeter] = None,
        operator: Optional[str] = None,
        enable_logging: bool = True,
        enable_iso17025: bool = True
    ):
        """
        Initialize insulation resistance test

        Args:
            module: Module identifier (e.g., "PV-001")
            test_block_id: Optional test block ID (auto-generated if not provided)
            megohmmeter: Megohmmeter instrument (uses simulator if not provided)
            operator: Operator name
            enable_logging: Enable data logging
            enable_iso17025: Enable ISO 17025 compliance logging
        """
        self.module = module
        self.test_block_id = test_block_id or f"INSUL-{uuid.uuid4().hex[:8].upper()}"
        self.operator = operator

        # Equipment setup
        if megohmmeter is None:
            # Use simulator by default
            self.megohmmeter = MegohmeterSimulator()
        else:
            self.megohmmeter = megohmmeter

        # Test results storage
        self.tests: List[InsulationTest] = []
        self.test_counter = 0

        # Test block tracking
        self.test_block: Optional[BaseTestBlock] = None

        # Logging
        self.enable_logging = enable_logging
        self.enable_iso17025 = enable_iso17025

        if self.enable_logging:
            self.data_logger = TestDataLogger(
                test_id=self.test_block_id,
                output_dir="./test_data/insulation"
            )

        if self.enable_iso17025:
            self.iso_logger = ISO17025Logger(
                output_dir="./compliance_records/insulation"
            )

    def initialize(self) -> bool:
        """
        Initialize test block and equipment

        Returns:
            True if initialization successful
        """
        # Create test block
        self.test_block = BaseTestBlock(
            test_block_id=self.test_block_id,
            test_name="Insulation Resistance Test",
            module_id=self.module,
            standard="IEC 61215-2:2016 / IEC 61730-2:2016",
            compliance_data=ComplianceData(
                standard="IEC 61215-2:2016 / IEC 61730-2:2016",
                standard_version="2016",
                test_procedure_id="MST-INSUL-001",
                accreditation="ISO/IEC 17025",
                calibration_refs=[]
            ),
            operator=self.operator
        )

        # Connect to equipment
        if not self.megohmmeter.connect():
            self.test_block.add_audit_entry(
                "equipment_connection_failed",
                user=self.operator,
                details={"instrument": "megohmmeter"}
            )
            return False

        # Verify calibration
        if not self.megohmmeter.is_calibration_valid():
            self.test_block.add_audit_entry(
                "calibration_invalid",
                user=self.operator,
                details={"instrument": self.megohmmeter.info.instrument_id}
            )
            return False

        # Add calibration reference
        if self.megohmmeter.info.calibration_certificate:
            self.test_block.compliance_data.calibration_refs.append(
                self.megohmmeter.info.calibration_certificate
            )

        self.test_block.add_audit_entry(
            "test_initialized",
            user=self.operator,
            details={
                "instrument": self.megohmmeter.info.model,
                "serial": self.megohmmeter.info.serial_number
            }
        )

        if self.enable_logging:
            self.data_logger.log_event(
                "test_initialized",
                f"Test block {self.test_block_id} initialized",
                metadata={
                    "module": self.module,
                    "instrument": self.megohmmeter.info.model
                }
            )

        return True

    def measure(
        self,
        voltage: Literal[500, 1000],
        condition: Literal["wet", "dry"],
        polarity: Literal["positive", "negative"] = "positive",
        measurement_time: int = 60,
        environmental_conditions: Optional[EnvironmentalConditions] = None
    ) -> InsulationTestResult:
        """
        Perform insulation resistance measurement

        Args:
            voltage: Test voltage (500V or 1000V)
            condition: Test condition ("wet" or "dry")
            polarity: Test polarity ("positive" or "negative")
            measurement_time: Measurement duration in seconds (default 60s per IEC)
            environmental_conditions: Environmental conditions during test

        Returns:
            InsulationTestResult containing test data and pass/fail status

        Raises:
            RuntimeError: If test not initialized or equipment not connected
        """
        if not self.test_block:
            raise RuntimeError("Test not initialized. Call initialize() first.")

        if not self.megohmmeter.connected:
            raise RuntimeError("Megohmmeter not connected")

        # Start test if not already started
        if self.test_block.status == TestBlockStatus.PENDING:
            self.test_block.start_test(operator=self.operator)

        self.test_counter += 1

        # Log test start
        if self.enable_logging:
            self.data_logger.log_event(
                "measurement_started",
                f"Starting measurement {self.test_counter}",
                metadata={
                    "voltage": voltage,
                    "condition": condition,
                    "polarity": polarity
                }
            )

        self.test_block.add_audit_entry(
            "measurement_started",
            user=self.operator,
            details={
                "test_id": self.test_counter,
                "voltage": voltage,
                "condition": condition,
                "polarity": polarity
            }
        )

        # Perform measurement
        resistance_mohm = self.megohmmeter.measure_resistance(
            test_voltage=voltage,
            measurement_time=measurement_time,
            polarity=polarity
        )

        if resistance_mohm is None:
            raise RuntimeError("Measurement failed")

        # Determine pass/fail
        if condition == "wet":
            minimum_resistance = self.WET_MINIMUM_RESISTANCE_MOHM
        else:  # dry
            minimum_resistance = self.DRY_MINIMUM_RESISTANCE_MOHM

        pass_status = resistance_mohm >= minimum_resistance

        # Create test record
        test = InsulationTest(
            test_id=self.test_counter,
            module_id=hash(self.module) % 100000,  # Simple numeric ID
            test_voltage=voltage,
            condition=condition,
            resistance_mohm=round(resistance_mohm, 2),
            polarity=polarity,
            pass_status=pass_status,
            timestamp=datetime.utcnow()
        )

        self.tests.append(test)

        # Create measurement result
        measurement_result = MeasurementResult(
            value=resistance_mohm,
            unit="MΩ",
            uncertainty=self.megohmmeter.info.uncertainty.get("resistance", 2.0) if self.megohmmeter.info.uncertainty else 2.0,
            timestamp=test.timestamp,
            instrument_id=self.megohmmeter.info.instrument_id,
            calibration_date=self.megohmmeter.info.calibration_date,
            metadata={
                "voltage": voltage,
                "condition": condition,
                "polarity": polarity,
                "minimum_required": minimum_resistance,
                "pass_status": pass_status
            }
        )

        # Log measurement
        if self.enable_logging:
            self.data_logger.log_measurement(
                measurement_type="insulation_resistance",
                value=resistance_mohm,
                unit="MΩ",
                metadata={
                    "test_id": self.test_counter,
                    "voltage": voltage,
                    "condition": condition,
                    "polarity": polarity,
                    "pass_status": pass_status,
                    "minimum_required": minimum_resistance
                }
            )

        self.test_block.add_audit_entry(
            "measurement_completed",
            user=self.operator,
            details={
                "test_id": self.test_counter,
                "resistance": resistance_mohm,
                "pass_status": pass_status
            }
        )

        # Create result
        result = InsulationTestResult(
            test=test,
            environmental_conditions=environmental_conditions,
            measurement_result=measurement_result
        )

        return result

    def run_full_test_sequence(
        self,
        voltage: Literal[500, 1000] = 1000,
        condition: Literal["wet", "dry"] = "wet",
        test_both_polarities: bool = True,
        environmental_conditions: Optional[EnvironmentalConditions] = None
    ) -> List[InsulationTestResult]:
        """
        Run complete test sequence

        Args:
            voltage: Test voltage (default 1000V)
            condition: Test condition (default "wet")
            test_both_polarities: Test both positive and negative polarity
            environmental_conditions: Environmental conditions

        Returns:
            List of test results
        """
        results: List[InsulationTestResult] = []

        polarities: List[Literal["positive", "negative"]] = ["positive", "negative"] if test_both_polarities else ["positive"]

        for polarity in polarities:
            result = self.measure(
                voltage=voltage,
                condition=condition,
                polarity=polarity,
                environmental_conditions=environmental_conditions
            )
            results.append(result)

        return results

    def finalize(self) -> Dict[str, Any]:
        """
        Finalize test and generate reports

        Returns:
            Summary of test results
        """
        if not self.test_block:
            raise RuntimeError("Test not initialized")

        # Determine overall pass/fail
        all_passed = all(test.pass_status for test in self.tests)

        self.test_block.complete_test(success=all_passed)

        # Generate summary
        summary = {
            "test_block_id": self.test_block_id,
            "module": self.module,
            "total_tests": len(self.tests),
            "passed": sum(1 for t in self.tests if t.pass_status),
            "failed": sum(1 for t in self.tests if not t.pass_status),
            "overall_status": "PASS" if all_passed else "FAIL",
            "tests": [t.model_dump() for t in self.tests],
            "test_block": self.test_block.model_dump()
        }

        # Save logs
        if self.enable_logging:
            self.data_logger.log_event(
                "test_finalized",
                f"Test {self.test_block_id} finalized",
                metadata=summary
            )
            self.data_logger.save_json_summary(summary)
            if self.data_logger.csv_data:
                self.data_logger.save_csv()

        # Generate ISO 17025 record
        if self.enable_iso17025 and self.tests:
            # Use first test for record (or aggregate if needed)
            first_test = self.tests[0]

            uncertainty_budget = [
                MeasurementUncertainty(
                    component="instrument",
                    source="Megohmmeter calibration",
                    value=2.0,  # 2% from calibration certificate
                    distribution="normal",
                    sensitivity_coefficient=1.0
                ),
                MeasurementUncertainty(
                    component="temperature",
                    source="Temperature coefficient",
                    value=0.5,  # 0.5% per °C
                    distribution="rectangular",
                    sensitivity_coefficient=1.0
                ),
                MeasurementUncertainty(
                    component="repeatability",
                    source="Measurement repeatability",
                    value=1.0,  # 1% from repeated measurements
                    distribution="normal",
                    sensitivity_coefficient=1.0
                )
            ]

            iso_record = ISO17025Record(
                record_id=self.test_block_id,
                test_id=self.test_block_id,
                test_date=self.test_block.started_at or datetime.utcnow(),
                test_method="Insulation Resistance Test",
                standard_reference="IEC 61215-2:2016 / IEC 61730-2:2016",
                operator=self.operator or "Unknown",
                operator_qualification="PV Testing Technician",
                equipment_used=[
                    {
                        "instrument_id": self.megohmmeter.info.instrument_id,
                        "type": "Megohmmeter",
                        "model": self.megohmmeter.info.model,
                        "serial": self.megohmmeter.info.serial_number,
                        "calibration_date": self.megohmmeter.info.calibration_date.isoformat() if self.megohmmeter.info.calibration_date else None,
                        "calibration_due_date": self.megohmmeter.info.calibration_due_date.isoformat() if self.megohmmeter.info.calibration_due_date else None
                    }
                ],
                calibration_valid=self.megohmmeter.is_calibration_valid(),
                environmental_conditions={},
                measurements=[t.model_dump() for t in self.tests],
                uncertainty_budget=uncertainty_budget,
                result=f"Insulation resistance: {first_test.resistance_mohm} MΩ",
                pass_fail=all_passed,
                acceptance_criteria=f"≥ {self.WET_MINIMUM_RESISTANCE_MOHM if first_test.condition == 'wet' else self.DRY_MINIMUM_RESISTANCE_MOHM} MΩ",
                reference_standards=["IEC 61215-2:2016", "IEC 61730-2:2016"],
                calibration_chain=[self.megohmmeter.info.calibration_certificate] if self.megohmmeter.info.calibration_certificate else []
            )

            iso_record = self.iso_logger.create_record(iso_record)
            self.iso_logger.save_record(iso_record)

        # Disconnect equipment
        self.megohmmeter.disconnect()

        return summary

    def __enter__(self) -> "InsulationResistanceTest":
        """Context manager entry"""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit"""
        if exc_type is None:
            self.finalize()
        else:
            if self.test_block:
                self.test_block.abort_test(reason=str(exc_val))
        self.megohmmeter.disconnect()
