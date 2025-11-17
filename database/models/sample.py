"""
Sample Model

Manages PV module samples received for testing, including tracking of physical
materials, documentation, and testing scope.
"""

from datetime import date, datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from enum import Enum

from sqlmodel import SQLModel, Field, Relationship, Column, String, JSON
from sqlalchemy import Index, UniqueConstraint

if TYPE_CHECKING:
    from .test import Test


class SampleStatus(str, Enum):
    """Sample processing status"""
    RECEIVED = "received"
    IN_PROGRESS = "in_progress"
    TESTING_COMPLETE = "testing_complete"
    REPORT_PENDING = "report_pending"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    RETURNED = "returned"
    DISPOSED = "disposed"


class SampleType(str, Enum):
    """Type of PV sample"""
    MODULE = "module"
    CELL = "cell"
    LAMINATE = "laminate"
    COMPONENT = "component"


class Sample(SQLModel, table=True):
    """
    Sample model for tracking PV modules and components under test.

    Attributes:
        id: Unique sample identifier
        sample_number: Human-readable sample number (e.g., S-2024-001)
        protocol: Test protocol/standard (IEC 61215, IEC 61730, etc.)
        scope: Testing scope and requirements
        customer_name: Customer/client name
        customer_po_number: Customer purchase order number
        sample_type: Type of sample (module, cell, etc.)
        manufacturer: Sample manufacturer
        model_number: Manufacturer model/type designation
        serial_numbers: List of serial numbers for modules tested
        quantity: Number of samples received
        received_date: Date sample was received
        expected_completion_date: Expected test completion date
        package_images: Paths to package/arrival condition images
        bom: Bill of materials (JSON structure)
        labels: Sample labels and markings information
        nameplate_ratings: Nameplate electrical ratings
        physical_dimensions: Physical dimensions and weight
        storage_location: Where sample is stored
        status: Current processing status
        notes: Additional notes and observations
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "samples"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Sample identification
    sample_number: str = Field(max_length=50, unique=True, index=True)
    sample_type: SampleType = Field(default=SampleType.MODULE, sa_column=Column(String(50)))

    # Protocol and scope
    protocol: str = Field(
        max_length=200,
        index=True,
        description="Test protocol (e.g., IEC 61215-2:2021, IEC 61730-2:2016)"
    )
    scope: str = Field(
        description="Testing scope, requirements, and test sequence"
    )

    # Customer information
    customer_name: str = Field(max_length=200, index=True)
    customer_po_number: Optional[str] = Field(default=None, max_length=100)
    customer_contact: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Customer contact information"
    )

    # Sample details
    manufacturer: str = Field(max_length=200, index=True)
    model_number: str = Field(max_length=100, index=True)
    serial_numbers: List[str] = Field(
        sa_column=Column(JSON),
        description="Array of serial numbers for modules under test"
    )
    quantity: int = Field(default=1, ge=1)

    # Dates
    received_date: date = Field(index=True)
    expected_completion_date: Optional[date] = Field(default=None)
    actual_completion_date: Optional[date] = Field(default=None)

    # Documentation and images
    package_images: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Paths to images of packaging and arrival condition"
    )

    # Bill of materials
    bom: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Bill of materials including cells, glass, backsheet, junction box, etc."
    )

    # Labels and markings
    labels: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Label information, certifications, warnings, ratings"
    )

    # Specifications
    nameplate_ratings: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Electrical ratings: Pmax, Voc, Isc, Vmp, Imp, etc."
    )

    physical_dimensions: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Length, width, thickness, weight, cell configuration"
    )

    # Storage and status
    storage_location: Optional[str] = Field(default=None, max_length=200)
    status: SampleStatus = Field(default=SampleStatus.RECEIVED, sa_column=Column(String(50)), index=True)

    # Additional information
    special_handling_requirements: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tests: List["Test"] = Relationship(back_populates="sample")

    # Table constraints
    __table_args__ = (
        UniqueConstraint('sample_number', name='uq_sample_number'),
        Index('ix_sample_customer_status', 'customer_name', 'status'),
        Index('ix_sample_protocol_status', 'protocol', 'status'),
        Index('ix_sample_received_date', 'received_date'),
        Index('ix_sample_manufacturer_model', 'manufacturer', 'model_number'),
    )

    def is_testing_complete(self) -> bool:
        """Check if all testing is complete."""
        return self.status in [
            SampleStatus.TESTING_COMPLETE,
            SampleStatus.REPORT_PENDING,
            SampleStatus.COMPLETED
        ]

    def days_in_lab(self) -> int:
        """Calculate number of days sample has been in the lab."""
        return (date.today() - self.received_date).days

    def is_overdue(self) -> bool:
        """Check if sample testing is overdue."""
        if self.expected_completion_date is None:
            return False
        if self.is_testing_complete():
            return False
        return date.today() > self.expected_completion_date

    def update_status(self, new_status: SampleStatus) -> None:
        """
        Update sample status and timestamp.

        Args:
            new_status: New status to set
        """
        self.status = new_status
        if new_status == SampleStatus.COMPLETED:
            self.actual_completion_date = date.today()
        self.updated_at = datetime.utcnow()

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()

    class Config:
        json_schema_extra = {
            "example": {
                "sample_number": "S-2024-001",
                "sample_type": "module",
                "protocol": "IEC 61215-2:2021",
                "scope": "Full type approval testing per IEC 61215-2:2021",
                "customer_name": "Solar Tech Industries",
                "customer_po_number": "PO-2024-1234",
                "manufacturer": "High Efficiency Solar Co.",
                "model_number": "HES-400W-MONO",
                "serial_numbers": ["SN001", "SN002", "SN003"],
                "quantity": 3,
                "received_date": "2024-01-15",
                "status": "received",
                "nameplate_ratings": {
                    "pmax": 400,
                    "voc": 49.5,
                    "isc": 10.5,
                    "vmp": 41.2,
                    "imp": 9.71
                }
            }
        }
