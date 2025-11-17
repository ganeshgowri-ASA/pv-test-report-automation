"""
Test Model

Manages individual test execution records with full traceability to samples,
equipment, personnel, and test conditions.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from enum import Enum

from sqlmodel import SQLModel, Field, Relationship, Column, String, JSON, Integer, ForeignKey
from sqlalchemy import Index

if TYPE_CHECKING:
    from .sample import Sample
    from .equipment import Equipment


class TestType(str, Enum):
    """Standard test types for PV modules"""
    # IEC 61215 Performance tests
    VISUAL_INSPECTION = "visual_inspection"
    ELECTRICAL_PERFORMANCE = "electrical_performance"
    INSULATION_TEST = "insulation_test"
    THERMAL_CYCLING = "thermal_cycling"
    HUMIDITY_FREEZE = "humidity_freeze"
    DAMP_HEAT = "damp_heat"
    UV_PRECONDITIONING = "uv_preconditioning"
    OUTDOOR_EXPOSURE = "outdoor_exposure"
    HOT_SPOT = "hot_spot"
    MECHANICAL_LOAD = "mechanical_load"
    HAIL_IMPACT = "hail_impact"
    BYPASS_DIODE = "bypass_diode"

    # IEC 61730 Safety tests
    FLAMMABILITY = "flammability"
    FIRE_TEST = "fire_test"
    ELECTRIC_SHOCK = "electric_shock"

    # IEC 61853 Performance testing
    SPECTRAL_RESPONSE = "spectral_response"
    ANGLE_OF_INCIDENCE = "angle_of_incidence"

    # Other specialized tests
    PID_TEST = "pid_test"
    LID_TEST = "lid_test"
    LIGHT_SOAKING = "light_soaking"
    CUSTOM = "custom"


class TestStatus(str, Enum):
    """Test execution status"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"
    FAILED_EXECUTION = "failed_execution"


class PassFailStatus(str, Enum):
    """Test result status"""
    PASS = "pass"
    FAIL = "fail"
    CONDITIONAL = "conditional"
    NOT_APPLICABLE = "not_applicable"
    PENDING = "pending"


class Test(SQLModel, table=True):
    """
    Test execution model with full traceability and measurement data.

    Attributes:
        id: Unique test identifier
        sample_id: Foreign key to Sample
        test_number: Human-readable test number
        type: Test type/name
        test_standard_reference: Reference to test standard section
        description: Test description
        test_date: Date test was performed
        start_time: Test start timestamp
        end_time: Test end timestamp
        performed_by_user_id: User who performed the test
        reviewed_by_user_id: User who reviewed the test
        equipment_id: Foreign key to Equipment used
        calibration_valid: Whether equipment calibration was valid
        readings: Test measurement readings (JSON)
        uncertainty: Measurement uncertainty
        test_conditions: Environmental/test conditions (JSON)
        pass_fail: Test result (pass/fail/conditional)
        failure_mode: Description of failure if failed
        acceptance_criteria: Criteria for pass/fail determination
        status: Test execution status
        attachments: Paths to data files, images, charts
        notes: Additional observations and notes
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "tests"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign keys
    sample_id: int = Field(foreign_key="samples.id", index=True)
    equipment_id: Optional[int] = Field(default=None, foreign_key="equipment.id", index=True)
    performed_by_user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    reviewed_by_user_id: Optional[int] = Field(default=None, foreign_key="users.id")

    # Test identification
    test_number: str = Field(max_length=100, unique=True, index=True)
    type: TestType = Field(sa_column=Column(String(100)), index=True)
    test_standard_reference: str = Field(
        max_length=200,
        description="Reference to test standard (e.g., IEC 61215-2:2021 MQT 01)"
    )
    description: Optional[str] = Field(default=None)

    # Test execution timing
    test_date: date = Field(index=True)
    start_time: Optional[datetime] = Field(default=None)
    end_time: Optional[datetime] = Field(default=None)
    duration_hours: Optional[float] = Field(default=None, ge=0)

    # Equipment and calibration
    calibration_valid: bool = Field(default=True)
    calibration_certificate_ref: Optional[str] = Field(default=None, max_length=100)

    # Test data and readings
    readings: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Array of measurement readings with timestamps and values"
    )

    # Uncertainty
    uncertainty: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Measurement uncertainty calculations and values"
    )

    # Test conditions
    test_conditions: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Temperature, humidity, irradiance, and other conditions"
    )

    # Results
    pass_fail: PassFailStatus = Field(
        default=PassFailStatus.PENDING,
        sa_column=Column(String(50)),
        index=True
    )
    failure_mode: Optional[str] = Field(default=None, description="Description of failure if test failed")

    acceptance_criteria: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Pass/fail criteria per standard"
    )

    # Calculated results
    results_summary: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Summary of key results and calculated values"
    )

    # Status
    status: TestStatus = Field(default=TestStatus.SCHEDULED, sa_column=Column(String(50)), index=True)

    # Documentation
    attachments: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Paths to data files, images, I-V curves, graphs"
    )

    # Review and approval
    reviewed: bool = Field(default=False)
    review_date: Optional[datetime] = Field(default=None)
    review_comments: Optional[str] = Field(default=None)

    # Additional information
    notes: Optional[str] = Field(default=None)
    deviations: Optional[str] = Field(default=None, description="Any deviations from standard procedure")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    sample: "Sample" = Relationship(back_populates="tests")
    equipment: Optional["Equipment"] = Relationship(back_populates="tests")

    # Table constraints
    __table_args__ = (
        Index('ix_test_sample_type', 'sample_id', 'type'),
        Index('ix_test_date_status', 'test_date', 'status'),
        Index('ix_test_pass_fail_type', 'pass_fail', 'type'),
        Index('ix_test_equipment_date', 'equipment_id', 'test_date'),
    )

    def calculate_duration(self) -> Optional[float]:
        """
        Calculate test duration in hours.

        Returns:
            Duration in hours or None if times not set
        """
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            self.duration_hours = delta.total_seconds() / 3600
            return self.duration_hours
        return None

    def validate_calibration(self, equipment: "Equipment") -> bool:
        """
        Validate equipment calibration was valid on test date.

        Args:
            equipment: Equipment object to check

        Returns:
            True if calibration valid, False otherwise
        """
        self.calibration_valid = equipment.is_calibration_valid(self.test_date)
        return self.calibration_valid

    def mark_complete(self, pass_fail: PassFailStatus, reviewed_by: Optional[int] = None) -> None:
        """
        Mark test as complete with result.

        Args:
            pass_fail: Test result
            reviewed_by: User ID who reviewed the test
        """
        self.status = TestStatus.COMPLETED
        self.pass_fail = pass_fail
        self.end_time = datetime.utcnow()
        self.calculate_duration()

        if reviewed_by:
            self.reviewed = True
            self.reviewed_by_user_id = reviewed_by
            self.review_date = datetime.utcnow()

        self.update_timestamp()

    def add_reading(self, reading: Dict[str, Any]) -> None:
        """
        Add a measurement reading.

        Args:
            reading: Dictionary containing measurement data
        """
        if self.readings is None:
            self.readings = []

        reading['timestamp'] = datetime.utcnow().isoformat()
        self.readings.append(reading)
        self.update_timestamp()

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()

    class Config:
        json_schema_extra = {
            "example": {
                "sample_id": 1,
                "equipment_id": 1,
                "test_number": "T-2024-001-001",
                "type": "electrical_performance",
                "test_standard_reference": "IEC 61215-2:2021 MQT 01",
                "test_date": "2024-01-20",
                "calibration_valid": True,
                "readings": [
                    {
                        "voc": 49.52,
                        "isc": 10.48,
                        "pmax": 402.5,
                        "vmp": 41.18,
                        "imp": 9.77,
                        "ff": 77.5,
                        "irradiance": 1000,
                        "temperature": 25
                    }
                ],
                "test_conditions": {
                    "irradiance": 1000,
                    "spectrum": "AM 1.5G",
                    "module_temperature": 25,
                    "ambient_temperature": 23,
                    "humidity": 45
                },
                "pass_fail": "pass",
                "status": "completed"
            }
        }
