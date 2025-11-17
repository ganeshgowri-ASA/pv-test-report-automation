"""
Equipment Model

Manages test equipment inventory, calibration tracking, and uncertainty specifications.
Ensures all test equipment is calibrated and within valid calibration periods.
"""

from datetime import date, datetime
from typing import Optional, List, TYPE_CHECKING
from enum import Enum

from sqlmodel import SQLModel, Field, Relationship, Column, String, Index
from sqlalchemy import UniqueConstraint

if TYPE_CHECKING:
    from .test import Test


class EquipmentStatus(str, Enum):
    """Equipment operational status"""
    ACTIVE = "active"
    CALIBRATION_DUE = "calibration_due"
    OUT_OF_SERVICE = "out_of_service"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class Equipment(SQLModel, table=True):
    """
    Test equipment model with calibration tracking.

    Attributes:
        id: Unique equipment identifier
        name: Equipment name/description
        model_number: Manufacturer model number
        serial_number: Unique serial number
        manufacturer: Equipment manufacturer
        calibration_date: Last calibration date
        calibration_due_date: Next calibration due date
        calibration_interval_days: Days between calibrations
        uncertainty: Measurement uncertainty specification
        uncertainty_unit: Unit for uncertainty (%, mV, etc.)
        status: Current operational status
        location: Physical location of equipment
        notes: Additional notes or specifications
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "equipment"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Equipment identification
    name: str = Field(max_length=200, index=True)
    model_number: Optional[str] = Field(default=None, max_length=100)
    serial_number: str = Field(max_length=100, unique=True, index=True)
    manufacturer: Optional[str] = Field(default=None, max_length=200)

    # Calibration tracking
    calibration_date: date = Field(index=True)
    calibration_due_date: date = Field(index=True)
    calibration_interval_days: int = Field(default=365, ge=1)
    calibration_certificate_number: Optional[str] = Field(default=None, max_length=100)

    # Uncertainty specifications
    uncertainty: float = Field(ge=0)
    uncertainty_unit: str = Field(max_length=20)
    uncertainty_description: Optional[str] = Field(default=None, max_length=500)

    # Status and location
    status: EquipmentStatus = Field(default=EquipmentStatus.ACTIVE, sa_column=Column(String(50)))
    location: Optional[str] = Field(default=None, max_length=200)

    # Additional information
    notes: Optional[str] = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tests: List["Test"] = Relationship(back_populates="equipment")

    # Table constraints
    __table_args__ = (
        UniqueConstraint('serial_number', name='uq_equipment_serial'),
        Index('ix_equipment_status_calibration', 'status', 'calibration_due_date'),
        Index('ix_equipment_name_status', 'name', 'status'),
    )

    def is_calibration_valid(self, test_date: Optional[date] = None) -> bool:
        """
        Check if calibration is valid for a given date.

        Args:
            test_date: Date to check validity for (defaults to today)

        Returns:
            True if calibration is valid, False otherwise
        """
        check_date = test_date or date.today()
        return self.calibration_date <= check_date <= self.calibration_due_date

    def days_until_calibration_due(self) -> int:
        """Calculate days until calibration is due."""
        return (self.calibration_due_date - date.today()).days

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Solar Simulator AAA Class",
                "model_number": "SS-1000X",
                "serial_number": "SS1000-2023-001",
                "manufacturer": "Newport Corporation",
                "calibration_date": "2024-01-15",
                "calibration_due_date": "2025-01-15",
                "calibration_interval_days": 365,
                "uncertainty": 2.0,
                "uncertainty_unit": "%",
                "status": "active",
                "location": "Testing Lab A"
            }
        }
