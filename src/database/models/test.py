"""
Test Model
==========

Represents individual test executions and results.

The Test model tracks:
    - Test type and configuration
    - Test execution details
    - Results and measurements
    - Pass/fail status
    - Equipment used
    - Environmental conditions

Compliance:
    - IEC 61215-2021: Test sequence requirements
    - IEC 60904: I-V measurement standards
    - ISO 17025: Test method validation and uncertainty
"""

import uuid
from datetime import datetime
from typing import Optional
import enum

from sqlalchemy import Column, String, Float, DateTime, Text, JSON, Boolean, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database.base import Base


class TestType(str, enum.Enum):
    """Test types per IEC 61215-2021"""
    VISUAL_INSPECTION = "visual_inspection"
    PERFORMANCE_STC = "performance_stc"
    PERFORMANCE_NOCT = "performance_noct"
    PERFORMANCE_LOW_IRRADIANCE = "performance_low_irradiance"
    INSULATION_TEST = "insulation_test"
    WET_LEAKAGE_CURRENT = "wet_leakage_current"
    GROUND_CONTINUITY = "ground_continuity"
    THERMAL_CYCLING = "thermal_cycling"
    DAMP_HEAT = "damp_heat"
    HUMIDITY_FREEZE = "humidity_freeze"
    UV_PRECONDITIONING = "uv_preconditioning"
    OUTDOOR_EXPOSURE = "outdoor_exposure"
    HOT_SPOT_ENDURANCE = "hot_spot_endurance"
    UV_TEST = "uv_test"
    THERMAL_CYCLING_TEST = "thermal_cycling_test"
    MECHANICAL_LOAD_TEST = "mechanical_load_test"
    HAIL_IMPACT = "hail_impact"
    BYPASS_DIODE = "bypass_diode"
    ELECTROLUMINESCENCE = "electroluminescence"
    INFRARED_THERMOGRAPHY = "infrared_thermography"
    PID_TEST = "pid_test"
    SALT_MIST = "salt_mist"
    AMMONIA_CORROSION = "ammonia_corrosion"


class TestStatus(str, enum.Enum):
    """Test execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class TestResult(str, enum.Enum):
    """Test pass/fail result"""
    PASS = "pass"
    FAIL = "fail"
    CONDITIONAL_PASS = "conditional_pass"
    NOT_APPLICABLE = "not_applicable"
    INCONCLUSIVE = "inconclusive"


class Test(Base):
    """
    Test Execution Model

    Represents a single test execution on a sample.

    Attributes:
        id: Primary key
        test_id: Unique test identifier
        sample_id: Reference to Sample
        test_type: Type of test (from IEC standards)
        test_standard: Standard being followed
        test_sequence_number: Position in test sequence
        status: Execution status
        result: Pass/fail outcome
        start_time: Test start timestamp
        end_time: Test end timestamp
        duration_minutes: Test duration
        operator_id: User performing test
        supervisor_id: Supervising user
        equipment_ids: List of equipment used
        environmental_conditions: Temperature, humidity, etc.
        test_parameters: Test-specific parameters
        measurements: Raw measurement data
        analysis_results: Processed results
        pass_fail_criteria: Criteria used for assessment
        deviations: Any deviations from standard procedure
        comments: Additional notes
        data_files: Associated data files (IV curves, images, etc.)
        metadata: Additional flexible metadata
    """

    __tablename__ = "tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_id = Column(String(50), unique=True, nullable=False, index=True)

    # References
    sample_id = Column(UUID(as_uuid=True), ForeignKey("samples.id"), nullable=False)
    protocol_id = Column(UUID(as_uuid=True), ForeignKey("test_protocols.id"), nullable=True)

    # Test identification
    test_type = Column(Enum(TestType), nullable=False)
    test_standard = Column(String(100), nullable=False)
    test_sequence_number = Column(Integer, nullable=True)
    test_method = Column(String(255), nullable=True)

    # Execution details
    status = Column(Enum(TestStatus), nullable=False, default=TestStatus.PENDING)
    result = Column(Enum(TestResult), nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Float, nullable=True)

    # Personnel
    operator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    supervisor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Equipment and environment
    equipment_ids = Column(JSON, nullable=True)  # List of equipment UUIDs
    environmental_conditions = Column(JSON, nullable=True)
    calibration_valid = Column(Boolean, nullable=True)

    # Test data
    test_parameters = Column(JSON, nullable=False)
    measurements = Column(JSON, nullable=True)
    analysis_results = Column(JSON, nullable=True)
    uncertainty = Column(JSON, nullable=True)

    # Pass/fail assessment
    pass_fail_criteria = Column(JSON, nullable=False)
    actual_vs_criteria = Column(JSON, nullable=True)
    failure_modes = Column(JSON, nullable=True)

    # Documentation
    deviations = Column(Text, nullable=True)
    comments = Column(Text, nullable=True)
    data_files = Column(JSON, nullable=True)  # URLs to raw data files
    images = Column(JSON, nullable=True)  # URLs to images

    # Metadata
    metadata = Column(JSON, nullable=True)

    # Audit
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    sample = relationship("Sample", back_populates="tests")
    operator = relationship("User", foreign_keys=[operator_id])
    supervisor = relationship("User", foreign_keys=[supervisor_id])

    def __repr__(self) -> str:
        return f"<Test(id={self.id}, test_id='{self.test_id}', type='{self.test_type}', status='{self.status}')>"
