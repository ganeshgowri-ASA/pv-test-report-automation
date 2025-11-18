"""
Pydantic models for structured data extraction from documents.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import pandas as pd
from pydantic import BaseModel, Field, field_validator


class ExtractionMethod(str, Enum):
    """Method used to extract content from document."""

    NATIVE = "native"
    OCR = "ocr"
    HYBRID = "hybrid"


class AccreditationBody(str, Enum):
    """Recognized accreditation bodies."""

    NABL = "NABL"
    ILAC = "ILAC"
    A2LA = "A2LA"
    UKAS = "UKAS"
    DAkkS = "DAkkS"
    UNKNOWN = "UNKNOWN"


class ImageData(BaseModel):
    """Represents an extracted image from document."""

    image_bytes: bytes
    format: str  # PNG, JPEG, etc.
    width: int
    height: int
    page_number: Optional[int] = None
    description: Optional[str] = None


class TableData(BaseModel):
    """Represents an extracted table."""

    data: List[List[Any]]  # Raw table data
    headers: Optional[List[str]] = None
    page_number: Optional[int] = None
    table_index: int = 0
    confidence: float = 1.0  # For OCR-extracted tables

    def to_dataframe(self) -> pd.DataFrame:
        """Convert table data to pandas DataFrame."""
        if self.headers:
            return pd.DataFrame(self.data, columns=self.headers)
        return pd.DataFrame(self.data)

    class Config:
        arbitrary_types_allowed = True


class DocumentMetadata(BaseModel):
    """Document metadata extracted from file properties."""

    author: Optional[str] = None
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    title: Optional[str] = None
    subject: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    producer: Optional[str] = None  # For PDFs
    page_count: int = 0
    file_size_bytes: int = 0
    language: Optional[str] = None


class ParagraphData(BaseModel):
    """Represents a paragraph with formatting information."""

    text: str
    is_bold: bool = False
    is_italic: bool = False
    is_heading: bool = False
    heading_level: Optional[int] = None  # 1-9
    font_size: Optional[float] = None
    paragraph_index: int = 0


class DocumentIngestionResult(BaseModel):
    """Complete result of document ingestion process."""

    text_content: str
    tables: List[TableData] = Field(default_factory=list)
    images: List[ImageData] = Field(default_factory=list)
    paragraphs: List[ParagraphData] = Field(default_factory=list)
    metadata: DocumentMetadata
    extraction_method: ExtractionMethod
    ocr_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    file_hash: str  # SHA-256
    file_path: str
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    @field_validator("ocr_confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("OCR confidence must be between 0.0 and 1.0")
        return v

    class Config:
        arbitrary_types_allowed = True


class UncertaintyMeasurement(BaseModel):
    """Measurement uncertainty from calibration certificate."""

    value: float
    unit: str
    coverage_factor: float = 2.0  # k=2 is standard for 95% confidence
    confidence_level: float = 0.95


class CalibrationPoint(BaseModel):
    """Single calibration point with reference and measured values."""

    reference_value: float
    measured_value: float
    unit: str
    uncertainty: Optional[UncertaintyMeasurement] = None
    deviation: Optional[float] = None


class TraceabilityInfo(BaseModel):
    """Traceability chain information."""

    reference_standard: str
    standard_id: Optional[str] = None
    calibration_authority: Optional[str] = None
    certificate_number: Optional[str] = None


class CalibrationCertificate(BaseModel):
    """ISO 17025/NABL calibration certificate data."""

    certificate_number: str
    equipment_id: str
    equipment_name: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None

    calibration_date: date
    due_date: Optional[date] = None
    calibration_interval_months: Optional[int] = None

    uncertainty: Optional[UncertaintyMeasurement] = None
    calibration_points: List[CalibrationPoint] = Field(default_factory=list)

    traceability: Optional[TraceabilityInfo] = None
    accreditation_body: AccreditationBody = AccreditationBody.UNKNOWN
    accreditation_number: Optional[str] = None

    laboratory_name: str
    laboratory_address: Optional[str] = None

    calibrated_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    approved_by: Optional[str] = None

    environmental_conditions: Dict[str, Any] = Field(default_factory=dict)
    # e.g., {"temperature": "23 ± 2 °C", "humidity": "50 ± 10 %RH"}

    remarks: Optional[str] = None
    raw_text: Optional[str] = None  # Full extracted text for reference

    @field_validator("calibration_date", "due_date", mode="before")
    @classmethod
    def parse_dates(cls, v):
        """Parse date strings flexibly."""
        if v is None or isinstance(v, date):
            return v
        if isinstance(v, str):
            from dateutil import parser

            try:
                return parser.parse(v).date()
            except Exception:
                return None
        return v

    def is_valid(self) -> bool:
        """Check if certificate is currently valid."""
        if self.due_date:
            return date.today() <= self.due_date
        return True

    def days_until_due(self) -> Optional[int]:
        """Calculate days until calibration is due."""
        if self.due_date:
            return (self.due_date - date.today()).days
        return None


class TestConditions(BaseModel):
    """Test conditions for PV module testing."""

    temperature: Optional[float] = None  # °C
    irradiance: Optional[float] = None  # W/m²
    humidity: Optional[float] = None  # %RH
    wind_speed: Optional[float] = None  # m/s
    spectrum: Optional[str] = None  # AM1.5, etc.
    condition_type: Optional[str] = None  # STC, NOCT, etc.


class ModuleSpecification(BaseModel):
    """PV module specifications from datasheet."""

    manufacturer: str
    model: str
    serial_number: Optional[str] = None

    rated_power: Optional[float] = None  # Watts
    voltage_max_power: Optional[float] = None  # Vmp
    current_max_power: Optional[float] = None  # Imp
    open_circuit_voltage: Optional[float] = None  # Voc
    short_circuit_current: Optional[float] = None  # Isc

    tolerance: Optional[str] = None  # e.g., "±3%"
    efficiency: Optional[float] = None  # %
    technology: Optional[str] = None  # Mono-Si, Poly-Si, etc.

    dimensions: Optional[str] = None
    weight: Optional[float] = None  # kg
    cells_count: Optional[int] = None


class TestResult(BaseModel):
    """Single test result entry."""

    parameter: str
    value: float
    unit: str
    uncertainty: Optional[float] = None
    specification: Optional[float] = None  # Expected value
    deviation_percent: Optional[float] = None
    pass_fail: Optional[bool] = None


class TestReport(BaseModel):
    """Complete test report data."""

    report_number: str
    report_date: date
    test_start_date: Optional[datetime] = None
    test_end_date: Optional[datetime] = None

    module_spec: ModuleSpecification
    test_conditions: TestConditions

    test_results: List[TestResult] = Field(default_factory=list)

    iec_standards: List[str] = Field(default_factory=list)
    # e.g., ["IEC 61215", "IEC 61730"]

    technician: Optional[str] = None
    reviewer: Optional[str] = None
    approver: Optional[str] = None

    laboratory: str
    accreditation: Optional[str] = None

    remarks: Optional[str] = None
    conclusion: Optional[str] = None  # Pass/Fail verdict
