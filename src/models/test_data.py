"""
Data models for PV test results and report generation.

Compliant with IEC 61215, IEC 61730, and ISO 17025 standards.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class TestResult(str, Enum):
    """Test result status."""
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_TESTED = "NOT TESTED"
    CONDITIONAL = "CONDITIONAL"


class AccreditationBody(str, Enum):
    """Accreditation body."""
    NABL = "NABL"
    ILAC = "ILAC"
    A2LA = "A2LA"
    UKAS = "UKAS"


class Measurement(BaseModel):
    """Single measurement data point."""
    parameter: str
    value: float
    unit: str
    uncertainty: Optional[float] = None
    specification: Optional[str] = None
    result: TestResult = TestResult.NOT_TESTED

    class Config:
        use_enum_values = True


class TestSequence(BaseModel):
    """IEC 61215 test sequence (MST-01 through MST-19)."""
    sequence_id: str = Field(..., description="Test sequence ID (e.g., MST-01)")
    sequence_name: str = Field(..., description="Test sequence name")
    standard_reference: str = Field(default="IEC 61215-2:2021")
    test_date: datetime
    operator: str
    measurements: List[Measurement] = []
    overall_result: TestResult = TestResult.NOT_TESTED
    remarks: Optional[str] = None
    test_conditions: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True

    @validator('sequence_id')
    def validate_sequence_id(cls, v):
        """Validate test sequence ID format."""
        if not v.startswith('MST-'):
            raise ValueError('Sequence ID must start with MST-')
        return v


class ModuleUnderTest(BaseModel):
    """PV module under test information."""
    manufacturer: str
    model: str
    serial_number: str
    rated_power: float = Field(..., description="Rated power in Watts")
    rated_voltage: float = Field(..., description="Rated voltage in Volts")
    rated_current: float = Field(..., description="Rated current in Amps")
    module_type: str = Field(default="Crystalline Silicon")
    cell_technology: str = Field(default="Monocrystalline")
    dimensions: Optional[str] = None
    weight: Optional[float] = None
    manufacturing_date: Optional[datetime] = None


class LabInformation(BaseModel):
    """Testing laboratory information."""
    lab_name: str
    lab_address: str
    accreditation_number: str
    accreditation_body: AccreditationBody
    iso17025_certified: bool = True
    logo_path: Optional[str] = None
    nabl_logo_path: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None

    class Config:
        use_enum_values = True


class ReportMetadata(BaseModel):
    """Report metadata and versioning."""
    report_number: str
    report_date: datetime
    report_version: str = "1.0"
    is_draft: bool = False
    prepared_by: str
    reviewed_by: Optional[str] = None
    approved_by: Optional[str] = None
    review_date: Optional[datetime] = None
    approval_date: Optional[datetime] = None
    customer_name: Optional[str] = None
    customer_reference: Optional[str] = None


class ChartData(BaseModel):
    """Data for generating charts and graphs."""
    chart_type: str = Field(..., description="Type of chart (line, bar, scatter, etc.)")
    title: str
    x_label: str
    y_label: str
    x_data: List[float]
    y_data: List[float]
    series_label: Optional[str] = None
    additional_series: Optional[List[Dict[str, Any]]] = None


class TestReport(BaseModel):
    """Complete test report data structure."""
    metadata: ReportMetadata
    lab_info: LabInformation
    module_info: ModuleUnderTest
    test_sequences: List[TestSequence] = []
    charts: List[ChartData] = []
    summary: Optional[str] = None
    conclusions: Optional[str] = None
    deviations: Optional[str] = None
    attachments: List[str] = Field(default_factory=list)

    def get_overall_result(self) -> TestResult:
        """Calculate overall test result."""
        if not self.test_sequences:
            return TestResult.NOT_TESTED

        results = [seq.overall_result for seq in self.test_sequences]

        if TestResult.FAIL in results:
            return TestResult.FAIL
        elif TestResult.CONDITIONAL in results:
            return TestResult.CONDITIONAL
        elif all(r == TestResult.PASS for r in results):
            return TestResult.PASS
        else:
            return TestResult.NOT_TESTED

    def get_test_statistics(self) -> Dict[str, int]:
        """Get statistics on test results."""
        stats = {
            "total": len(self.test_sequences),
            "passed": 0,
            "failed": 0,
            "not_tested": 0,
            "conditional": 0
        }

        for seq in self.test_sequences:
            if seq.overall_result == TestResult.PASS:
                stats["passed"] += 1
            elif seq.overall_result == TestResult.FAIL:
                stats["failed"] += 1
            elif seq.overall_result == TestResult.CONDITIONAL:
                stats["conditional"] += 1
            else:
                stats["not_tested"] += 1

        return stats


class BrandingConfig(BaseModel):
    """Custom branding configuration for reports."""
    primary_color: str = Field(default="#1f77b4", description="Primary color in hex")
    secondary_color: str = Field(default="#ff7f0e", description="Secondary color in hex")
    header_logo_path: Optional[str] = None
    footer_logo_path: Optional[str] = None
    watermark_text: Optional[str] = None
    watermark_opacity: float = Field(default=0.1, ge=0, le=1)
    font_family: str = Field(default="Arial")
    company_tagline: Optional[str] = None
