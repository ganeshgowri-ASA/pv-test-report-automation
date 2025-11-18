"""ISO/IEC 17025 compliance logging and validation

ISO/IEC 17025 is the international standard for testing and calibration laboratories.
Key requirements:
- Full traceability of measurements
- Calibrated equipment with valid certificates
- Measurement uncertainty estimation
- Complete audit trail
- Operator qualification tracking
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import json
from pathlib import Path


class MeasurementUncertainty(BaseModel):
    """Measurement uncertainty budget per ISO/IEC 17025"""
    component: str
    source: str
    value: float
    distribution: str = "normal"  # normal, rectangular, triangular
    sensitivity_coefficient: float = 1.0
    degrees_of_freedom: Optional[int] = None

    def standard_uncertainty(self) -> float:
        """Calculate standard uncertainty"""
        if self.distribution == "normal":
            return self.value
        elif self.distribution == "rectangular":
            return self.value / (3 ** 0.5)
        elif self.distribution == "triangular":
            return self.value / (6 ** 0.5)
        return self.value


class ISO17025Record(BaseModel):
    """ISO/IEC 17025 compliant test record"""
    record_id: str
    test_id: str
    test_date: datetime
    test_method: str
    standard_reference: str

    # Personnel
    operator: str
    operator_qualification: Optional[str] = None
    reviewer: Optional[str] = None
    approver: Optional[str] = None

    # Equipment
    equipment_used: List[Dict[str, str]]
    calibration_valid: bool = True

    # Environmental conditions
    environmental_conditions: Dict[str, Any]

    # Measurements
    measurements: List[Dict[str, Any]]
    uncertainty_budget: List[MeasurementUncertainty]
    combined_uncertainty: Optional[float] = None
    expanded_uncertainty: Optional[float] = None
    coverage_factor: float = 2.0  # k=2 for 95% confidence

    # Results
    result: str
    pass_fail: bool
    acceptance_criteria: str

    # Traceability
    reference_standards: List[str] = Field(default_factory=list)
    calibration_chain: List[str] = Field(default_factory=list)

    # Metadata
    notes: Optional[str] = None
    deviations: List[str] = Field(default_factory=list)
    attachments: List[str] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ISO17025Logger:
    """Logger for ISO/IEC 17025 compliant records"""

    def __init__(self, output_dir: str = "./compliance_records"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def calculate_combined_uncertainty(
        self,
        uncertainty_budget: List[MeasurementUncertainty]
    ) -> float:
        """Calculate combined standard uncertainty"""
        sum_of_squares = sum(
            (uc.standard_uncertainty() * uc.sensitivity_coefficient) ** 2
            for uc in uncertainty_budget
        )
        return sum_of_squares ** 0.5

    def calculate_expanded_uncertainty(
        self,
        combined_uncertainty: float,
        coverage_factor: float = 2.0
    ) -> float:
        """Calculate expanded uncertainty (U = k × uc)"""
        return coverage_factor * combined_uncertainty

    def create_record(
        self,
        record: ISO17025Record
    ) -> ISO17025Record:
        """Create and validate ISO/IEC 17025 record"""

        # Calculate uncertainties if not provided
        if record.uncertainty_budget and not record.combined_uncertainty:
            record.combined_uncertainty = self.calculate_combined_uncertainty(
                record.uncertainty_budget
            )
            record.expanded_uncertainty = self.calculate_expanded_uncertainty(
                record.combined_uncertainty,
                record.coverage_factor
            )

        return record

    def save_record(self, record: ISO17025Record) -> Path:
        """Save record to file"""
        filename = f"{record.record_id}_{record.test_date.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename

        with open(filepath, 'w') as f:
            json.dump(record.model_dump(), f, indent=2, default=str)

        return filepath

    def validate_calibration(self, equipment_list: List[Dict[str, Any]]) -> bool:
        """Validate that all equipment has valid calibration"""
        for equipment in equipment_list:
            cal_due = equipment.get('calibration_due_date')
            if cal_due:
                if isinstance(cal_due, str):
                    cal_due = datetime.fromisoformat(cal_due)
                if datetime.utcnow() > cal_due:
                    return False
        return True
