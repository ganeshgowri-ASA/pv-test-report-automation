"""Data models for calibration certificate management per ISO 17025."""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
from pathlib import Path


class AccreditationBody(Enum):
    """Recognized accreditation bodies for calibration laboratories."""
    NABL = "NABL"  # National Accreditation Board for Testing and Calibration Laboratories (India)
    ILAC = "ILAC"  # International Laboratory Accreditation Cooperation
    A2LA = "A2LA"  # American Association for Laboratory Accreditation
    UKAS = "UKAS"  # United Kingdom Accreditation Service
    DAkkS = "DAkkS"  # Deutsche Akkreditierungsstelle (Germany)
    CNAS = "CNAS"  # China National Accreditation Service
    ENAS = "ENAS"  # Emirates National Accreditation System
    OTHER = "OTHER"


class CertificateStatus(Enum):
    """Calibration certificate status."""
    VALID = "valid"
    DUE_SOON = "due_soon"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"


class UncertaintyType(Enum):
    """Types of uncertainty measurements."""
    EXPANDED = "expanded"  # k=2, 95% confidence
    STANDARD = "standard"  # k=1
    COMBINED = "combined"


@dataclass
class UncertaintyBudget:
    """Uncertainty budget tracking per ISO 17025."""
    value: float
    unit: str
    uncertainty_type: UncertaintyType
    coverage_factor: float = 2.0  # k-factor, typically 2 for 95% confidence
    confidence_level: float = 0.95  # 95% confidence level
    components: Dict[str, float] = field(default_factory=dict)  # Individual uncertainty sources

    def __post_init__(self):
        """Validate uncertainty budget."""
        if self.value < 0:
            raise ValueError("Uncertainty value must be non-negative")
        if self.coverage_factor <= 0:
            raise ValueError("Coverage factor must be positive")
        if not (0 < self.confidence_level <= 1):
            raise ValueError("Confidence level must be between 0 and 1")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "value": self.value,
            "unit": self.unit,
            "uncertainty_type": self.uncertainty_type.value,
            "coverage_factor": self.coverage_factor,
            "confidence_level": self.confidence_level,
            "components": self.components,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UncertaintyBudget':
        """Create from dictionary."""
        return cls(
            value=data["value"],
            unit=data["unit"],
            uncertainty_type=UncertaintyType(data["uncertainty_type"]),
            coverage_factor=data.get("coverage_factor", 2.0),
            confidence_level=data.get("confidence_level", 0.95),
            components=data.get("components", {}),
        )


@dataclass
class TraceabilityChain:
    """Traceability chain to national/international standards."""
    primary_standard: str  # e.g., "NIST", "NPL", "PTB"
    intermediate_standards: List[str] = field(default_factory=list)
    reference_certificate: Optional[str] = None
    uncertainty_propagation: List[float] = field(default_factory=list)

    def validate(self) -> bool:
        """Validate traceability chain completeness."""
        if not self.primary_standard:
            return False
        # Check that uncertainty propagation matches chain length
        if self.uncertainty_propagation and len(self.uncertainty_propagation) != len(self.intermediate_standards) + 1:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "primary_standard": self.primary_standard,
            "intermediate_standards": self.intermediate_standards,
            "reference_certificate": self.reference_certificate,
            "uncertainty_propagation": self.uncertainty_propagation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TraceabilityChain':
        """Create from dictionary."""
        return cls(
            primary_standard=data["primary_standard"],
            intermediate_standards=data.get("intermediate_standards", []),
            reference_certificate=data.get("reference_certificate"),
            uncertainty_propagation=data.get("uncertainty_propagation", []),
        )


@dataclass
class CalibrationPoint:
    """Individual calibration measurement point."""
    nominal_value: float
    measured_value: float
    uncertainty: float
    unit: str
    deviation: Optional[float] = None

    def __post_init__(self):
        """Calculate deviation."""
        if self.deviation is None:
            self.deviation = self.measured_value - self.nominal_value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "nominal_value": self.nominal_value,
            "measured_value": self.measured_value,
            "uncertainty": self.uncertainty,
            "unit": self.unit,
            "deviation": self.deviation,
        }


@dataclass
class CalibrationCertificate:
    """
    Calibration certificate model per ISO 17025.

    Attributes:
        cert_id: Unique certificate identifier
        equipment_id: Reference to calibrated equipment
        cert_number: Certificate number from calibration lab
        calibration_date: Date of calibration
        due_date: Next calibration due date
        calibration_lab: Name of calibration laboratory
        accreditation_body: Accreditation authority (NABL, ILAC, etc.)
        uncertainty: Primary measurement uncertainty
        traceability_chain: Chain to national/international standards
        certificate_file: Path to certificate PDF/document
        status: Current certificate status
        uncertainty_budget: Detailed uncertainty analysis
        calibration_points: Individual measurement points
        environmental_conditions: Temperature, humidity during calibration
        calibration_procedure: Reference to calibration procedure
        technician: Name/ID of calibration technician
        reviewer: Name/ID of certificate reviewer
        notes: Additional notes or comments
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """

    cert_id: Optional[int]
    equipment_id: int
    cert_number: str
    calibration_date: date
    due_date: date
    calibration_lab: str
    accreditation_body: AccreditationBody
    uncertainty: float
    traceability_chain: str

    # Optional fields with defaults
    certificate_file: Optional[Path] = None
    status: CertificateStatus = CertificateStatus.VALID
    uncertainty_budget: Optional[UncertaintyBudget] = None
    calibration_points: List[CalibrationPoint] = field(default_factory=list)
    environmental_conditions: Dict[str, Any] = field(default_factory=dict)
    calibration_procedure: Optional[str] = None
    technician: Optional[str] = None
    reviewer: Optional[str] = None
    notes: Optional[str] = None
    traceability_chain_obj: Optional[TraceabilityChain] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Post-initialization validation."""
        self.validate()
        self.update_status()

    def validate(self) -> None:
        """Validate certificate data per ISO 17025 requirements."""
        # Date validation
        if self.calibration_date > date.today():
            raise ValueError("Calibration date cannot be in the future")

        if self.due_date <= self.calibration_date:
            raise ValueError("Due date must be after calibration date")

        # Uncertainty validation
        if self.uncertainty < 0:
            raise ValueError("Uncertainty must be non-negative")

        # Certificate number validation
        if not self.cert_number or not self.cert_number.strip():
            raise ValueError("Certificate number is required")

        # Traceability validation
        if self.traceability_chain_obj and not self.traceability_chain_obj.validate():
            raise ValueError("Invalid traceability chain")

    def update_status(self) -> CertificateStatus:
        """Update certificate status based on current date."""
        today = date.today()

        if self.status == CertificateStatus.REVOKED:
            return self.status

        if today > self.due_date:
            self.status = CertificateStatus.EXPIRED
        elif today >= self.due_date - timedelta(days=30):
            self.status = CertificateStatus.DUE_SOON
        else:
            self.status = CertificateStatus.VALID

        self.updated_at = datetime.now()
        return self.status

    def days_until_due(self) -> int:
        """Calculate days until calibration is due."""
        return (self.due_date - date.today()).days

    def is_valid(self) -> bool:
        """Check if certificate is currently valid."""
        self.update_status()
        return self.status in [CertificateStatus.VALID, CertificateStatus.DUE_SOON]

    def is_expired(self) -> bool:
        """Check if certificate is expired."""
        self.update_status()
        return self.status == CertificateStatus.EXPIRED

    def get_validity_period_days(self) -> int:
        """Get total validity period in days."""
        return (self.due_date - self.calibration_date).days

    def to_dict(self) -> Dict[str, Any]:
        """Convert certificate to dictionary for storage."""
        return {
            "cert_id": self.cert_id,
            "equipment_id": self.equipment_id,
            "cert_number": self.cert_number,
            "calibration_date": self.calibration_date.isoformat(),
            "due_date": self.due_date.isoformat(),
            "calibration_lab": self.calibration_lab,
            "accreditation_body": self.accreditation_body.value,
            "uncertainty": self.uncertainty,
            "traceability_chain": self.traceability_chain,
            "certificate_file": str(self.certificate_file) if self.certificate_file else None,
            "status": self.status.value,
            "uncertainty_budget": self.uncertainty_budget.to_dict() if self.uncertainty_budget else None,
            "calibration_points": [point.to_dict() for point in self.calibration_points],
            "environmental_conditions": self.environmental_conditions,
            "calibration_procedure": self.calibration_procedure,
            "technician": self.technician,
            "reviewer": self.reviewer,
            "notes": self.notes,
            "traceability_chain_obj": self.traceability_chain_obj.to_dict() if self.traceability_chain_obj else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CalibrationCertificate':
        """Create certificate from dictionary."""
        # Convert date strings to date objects
        calibration_date = datetime.fromisoformat(data["calibration_date"]).date() if isinstance(data["calibration_date"], str) else data["calibration_date"]
        due_date = datetime.fromisoformat(data["due_date"]).date() if isinstance(data["due_date"], str) else data["due_date"]

        # Convert enum strings to enum objects
        accreditation_body = AccreditationBody(data["accreditation_body"]) if isinstance(data["accreditation_body"], str) else data["accreditation_body"]
        status = CertificateStatus(data["status"]) if isinstance(data["status"], str) else data.get("status", CertificateStatus.VALID)

        # Parse optional complex objects
        uncertainty_budget = UncertaintyBudget.from_dict(data["uncertainty_budget"]) if data.get("uncertainty_budget") else None
        traceability_chain_obj = TraceabilityChain.from_dict(data["traceability_chain_obj"]) if data.get("traceability_chain_obj") else None

        return cls(
            cert_id=data.get("cert_id"),
            equipment_id=data["equipment_id"],
            cert_number=data["cert_number"],
            calibration_date=calibration_date,
            due_date=due_date,
            calibration_lab=data["calibration_lab"],
            accreditation_body=accreditation_body,
            uncertainty=data["uncertainty"],
            traceability_chain=data["traceability_chain"],
            certificate_file=Path(data["certificate_file"]) if data.get("certificate_file") else None,
            status=status,
            uncertainty_budget=uncertainty_budget,
            calibration_points=[],  # Would need to parse from data
            environmental_conditions=data.get("environmental_conditions", {}),
            calibration_procedure=data.get("calibration_procedure"),
            technician=data.get("technician"),
            reviewer=data.get("reviewer"),
            notes=data.get("notes"),
            traceability_chain_obj=traceability_chain_obj,
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
        )
