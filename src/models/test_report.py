"""
Data models for PV test reports.

Defines Pydantic models for test reports, test results, and related data structures
following IEC/ISO standards.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class StandardType(str, Enum):
    """Supported PV testing standards."""

    IEC_61215 = "IEC 61215"  # Terrestrial PV modules - Design qualification
    IEC_61730 = "IEC 61730"  # PV module safety qualification
    IEC_61853 = "IEC 61853"  # PV module performance testing
    IEC_62716 = "IEC 62716"  # Ammonia corrosion testing
    IEC_61701 = "IEC 61701"  # Salt mist corrosion testing
    IEC_62804 = "IEC 62804"  # Potential induced degradation testing
    IEC_60904 = "IEC 60904"  # PV devices measurement
    IEC_62759 = "IEC 62759"  # Transportation testing
    ISO_17025 = "ISO 17025"  # Testing laboratory competence
    ISO_9001 = "ISO 9001"  # Quality management systems


class TestStatus(str, Enum):
    """Test execution status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"


class PassFailStatus(str, Enum):
    """Individual test result pass/fail status."""

    PASS = "PASS"
    FAIL = "FAIL"
    CONDITIONAL_PASS = "CONDITIONAL_PASS"
    NOT_APPLICABLE = "N/A"
    PENDING = "PENDING"


class ModuleType(str, Enum):
    """PV module type classification."""

    CRYSTALLINE_SILICON = "Crystalline Silicon"
    THIN_FILM = "Thin Film"
    CPV = "Concentrator PV"
    BIFACIAL = "Bifacial"
    FLEXIBLE = "Flexible"
    BUILDING_INTEGRATED = "Building Integrated (BIPV)"


class TestResult(BaseModel):
    """Individual test measurement result."""

    test_id: str = Field(..., description="Unique test identifier")
    test_name: str = Field(..., description="Test procedure name")
    parameter: str = Field(..., description="Parameter being measured")
    specification: str = Field(..., description="Required specification/limit")
    measured_value: Optional[float] = Field(None, description="Measured value")
    measured_value_str: Optional[str] = Field(
        None, description="Measured value as string (for non-numeric)"
    )
    unit: str = Field(..., description="Unit of measurement")
    status: PassFailStatus = Field(..., description="Test pass/fail status")
    tolerance: Optional[str] = Field(None, description="Acceptable tolerance")
    uncertainty: Optional[str] = Field(None, description="Measurement uncertainty")
    equipment_used: Optional[str] = Field(None, description="Test equipment identifier")
    test_date: datetime = Field(default_factory=datetime.utcnow, description="Test execution date")
    operator_id: Optional[str] = Field(None, description="Test operator identifier")
    comments: Optional[str] = Field(None, description="Additional comments")
    attachments: Optional[List[str]] = Field(
        default_factory=list, description="Paths to attachments (photos, graphs)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "test_id": "TC-001",
                "test_name": "Visual Inspection",
                "parameter": "Module Appearance",
                "specification": "No defects per IEC 61215",
                "measured_value_str": "Pass",
                "unit": "categorical",
                "status": "PASS",
                "test_date": "2024-01-15T10:30:00Z",
                "operator_id": "OP-123",
                "comments": "No visible defects observed",
            }
        }


class EnvironmentalConditions(BaseModel):
    """Environmental conditions during testing."""

    temperature: Optional[float] = Field(None, description="Temperature in Celsius")
    humidity: Optional[float] = Field(None, description="Relative humidity in %")
    pressure: Optional[float] = Field(None, description="Atmospheric pressure in kPa")
    irradiance: Optional[float] = Field(None, description="Solar irradiance in W/m²")
    wind_speed: Optional[float] = Field(None, description="Wind speed in m/s")
    recorded_at: datetime = Field(
        default_factory=datetime.utcnow, description="When conditions were recorded"
    )


class SpecimenInfo(BaseModel):
    """Information about the test specimen (PV module)."""

    specimen_id: str = Field(..., description="Unique specimen identifier")
    manufacturer: str = Field(..., description="Module manufacturer")
    model: str = Field(..., description="Module model number")
    serial_number: str = Field(..., description="Module serial number")
    module_type: ModuleType = Field(..., description="Type of PV module")
    rated_power: float = Field(..., description="Rated power in Watts")
    dimensions: Optional[str] = Field(None, description="Module dimensions (LxWxH)")
    weight: Optional[float] = Field(None, description="Module weight in kg")
    cell_technology: Optional[str] = Field(None, description="Cell technology type")
    manufacturing_date: Optional[datetime] = Field(None, description="Manufacturing date")
    received_date: Optional[datetime] = Field(None, description="Date received at lab")
    condition_on_receipt: Optional[str] = Field(
        None, description="Condition when received at lab"
    )


class TestReportHeader(BaseModel):
    """Test report metadata and header information."""

    report_id: str = Field(..., description="Unique report identifier")
    report_number: str = Field(..., description="Human-readable report number")
    revision: int = Field(default=1, description="Report revision number")
    date_issued: datetime = Field(
        default_factory=datetime.utcnow, description="Report issue date"
    )
    test_standard: StandardType = Field(..., description="Testing standard applied")
    lab_name: str = Field(..., description="Testing laboratory name")
    lab_accreditation: Optional[str] = Field(
        None, description="Lab accreditation (NABL, ILAC, etc.)"
    )
    lab_address: Optional[str] = Field(None, description="Laboratory address")
    client_name: str = Field(..., description="Client/customer name")
    client_reference: Optional[str] = Field(None, description="Client reference number")
    test_duration: Optional[str] = Field(None, description="Total test duration")
    test_start_date: Optional[datetime] = Field(None, description="Test start date")
    test_end_date: Optional[datetime] = Field(None, description="Test completion date")
    performed_by: str = Field(..., description="Primary test performer")
    reviewed_by: Optional[str] = Field(None, description="Technical reviewer")
    approved_by: Optional[str] = Field(None, description="Report approver")
    certification_level: Optional[str] = Field(
        None, description="Certification level (if applicable)"
    )


class ComplianceSummary(BaseModel):
    """Compliance summary generated by LLM."""

    overall_status: PassFailStatus = Field(..., description="Overall compliance status")
    compliance_score: float = Field(
        ..., ge=0.0, le=100.0, description="Compliance score (0-100)"
    )
    total_tests: int = Field(..., description="Total number of tests")
    tests_passed: int = Field(..., description="Number of tests passed")
    tests_failed: int = Field(..., description="Number of tests failed")
    critical_failures: List[str] = Field(
        default_factory=list, description="List of critical failures"
    )
    warnings: List[str] = Field(default_factory=list, description="Compliance warnings")
    missing_tests: List[str] = Field(
        default_factory=list, description="Tests required but not performed"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Recommendations for improvement"
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="When summary was generated"
    )
    generated_by_llm: bool = Field(default=True, description="Whether generated by LLM")


class TestReport(BaseModel):
    """Complete PV test report."""

    header: TestReportHeader = Field(..., description="Report header and metadata")
    specimen: SpecimenInfo = Field(..., description="Specimen information")
    test_results: List[TestResult] = Field(
        default_factory=list, description="Individual test results"
    )
    environmental_conditions: Optional[List[EnvironmentalConditions]] = Field(
        default_factory=list, description="Environmental conditions during tests"
    )
    executive_summary: Optional[str] = Field(None, description="Executive summary")
    detailed_findings: Optional[str] = Field(None, description="Detailed findings and analysis")
    compliance_summary: Optional[ComplianceSummary] = Field(
        None, description="Compliance summary"
    )
    conclusions: Optional[str] = Field(None, description="Conclusions")
    recommendations: Optional[str] = Field(None, description="Recommendations")
    attachments: Optional[List[str]] = Field(
        default_factory=list, description="Report attachments"
    )
    status: TestStatus = Field(default=TestStatus.PENDING, description="Report status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator("test_results")
    @classmethod
    def validate_test_results(cls, v: List[TestResult]) -> List[TestResult]:
        """Ensure test results have unique test IDs."""
        test_ids = [result.test_id for result in v]
        if len(test_ids) != len(set(test_ids)):
            raise ValueError("Test results must have unique test_id values")
        return v

    def calculate_pass_rate(self) -> float:
        """Calculate the pass rate percentage."""
        if not self.test_results:
            return 0.0
        passed = sum(1 for r in self.test_results if r.status == PassFailStatus.PASS)
        return (passed / len(self.test_results)) * 100

    def get_failed_tests(self) -> List[TestResult]:
        """Get list of failed tests."""
        return [r for r in self.test_results if r.status == PassFailStatus.FAIL]

    def get_pending_tests(self) -> List[TestResult]:
        """Get list of pending tests."""
        return [r for r in self.test_results if r.status == PassFailStatus.PENDING]

    class Config:
        json_schema_extra = {
            "example": {
                "header": {
                    "report_id": "RPT-2024-001",
                    "report_number": "PV-TEST-2024-001",
                    "test_standard": "IEC 61215",
                    "lab_name": "ABC Solar Testing Laboratory",
                    "client_name": "Solar Modules Inc.",
                    "performed_by": "John Doe",
                },
                "specimen": {
                    "specimen_id": "SPEC-001",
                    "manufacturer": "Solar Tech Ltd",
                    "model": "ST-300W-Mono",
                    "serial_number": "SN123456",
                    "module_type": "Crystalline Silicon",
                    "rated_power": 300.0,
                },
                "status": "completed",
            }
        }


class ReviewerFeedback(BaseModel):
    """Reviewer feedback and workflow tracking."""

    feedback_id: str = Field(..., description="Unique feedback identifier")
    report_id: str = Field(..., description="Associated report ID")
    reviewer_id: str = Field(..., description="Reviewer identifier")
    reviewer_name: str = Field(..., description="Reviewer name")
    review_timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Review timestamp"
    )
    status: TestStatus = Field(..., description="Review status/decision")
    feedback: str = Field(..., description="Detailed feedback")
    suggested_corrections: Optional[List[str]] = Field(
        default_factory=list, description="Suggested corrections"
    )
    critical_issues: Optional[List[str]] = Field(
        default_factory=list, description="Critical issues identified"
    )
    approval_level: Optional[str] = Field(None, description="Approval level/authority")

    class Config:
        json_schema_extra = {
            "example": {
                "feedback_id": "FB-001",
                "report_id": "RPT-2024-001",
                "reviewer_id": "REV-123",
                "reviewer_name": "Jane Smith",
                "status": "approved",
                "feedback": "Report is complete and meets all requirements.",
                "suggested_corrections": [],
            }
        }
