"""
Sample Model
============

Represents PV module samples under test in the laboratory.

The Sample model tracks:
    - Module identification (sample ID, manufacturer, model)
    - Physical characteristics (technology, power rating, dimensions)
    - Test campaign information
    - Sample condition and history
    - Traceability to reports and test results

Compliance:
    - IEC 61215-2021: Module qualification requirements
    - ISO 17025: Sample identification and tracking
    - NABL: Sample management and chain of custody
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Text, JSON,
    Boolean, Enum, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from src.database.base import Base


class ModuleTechnology(str, enum.Enum):
    """PV module technology types per IEC 61215-2021"""
    MONOCRYSTALLINE = "monocrystalline"
    POLYCRYSTALLINE = "polycrystalline"
    THIN_FILM_CDTE = "thin_film_cdte"
    THIN_FILM_CIGS = "thin_film_cigs"
    THIN_FILM_AMORPHOUS_SI = "thin_film_amorphous_si"
    PERC = "perc"
    TOPCON = "topcon"
    HJT = "hjt"
    IBC = "ibc"
    BIFACIAL = "bifacial"
    OTHER = "other"


class SampleStatus(str, enum.Enum):
    """Sample lifecycle status"""
    RECEIVED = "received"
    IN_CONDITIONING = "in_conditioning"
    READY_FOR_TEST = "ready_for_test"
    TESTING = "testing"
    TEST_COMPLETE = "test_complete"
    FAILED = "failed"
    RETURNED = "returned"
    DISPOSED = "disposed"


class Sample(Base):
    """
    PV Module Sample Model

    Represents a photovoltaic module sample submitted for testing.
    Each sample is uniquely identified and tracked throughout the test campaign.

    Attributes:
        id (UUID): Primary key
        sample_id (str): Unique sample identifier (e.g., "PV-2024-001")
        manufacturer (str): Module manufacturer name
        model (str): Module model/type designation
        serial_number (str): Manufacturer's serial number
        technology (ModuleTechnology): PV technology type
        rated_power_wp (float): Nameplate power rating in watts peak
        rated_voltage_v (float): Rated voltage in volts
        rated_current_a (float): Rated current in amperes
        length_mm (float): Module length in millimeters
        width_mm (float): Module width in millimeters
        thickness_mm (float): Module thickness in millimeters
        weight_kg (float): Module weight in kilograms
        num_cells (int): Number of solar cells
        cell_technology (str): Cell technology details
        frame_type (str): Frame material and type
        junction_box_type (str): Junction box specifications
        cable_length_mm (float): Output cable length
        connector_type (str): Connector type (MC4, etc.)
        test_standard (str): Test standard to apply (IEC 61215, etc.)
        test_sequence (str): Test sequence identifier
        customer_name (str): Customer/client name
        customer_ref (str): Customer reference number
        received_date (datetime): Date sample received
        conditioning_start (datetime): Start of conditioning period
        conditioning_end (datetime): End of conditioning period
        test_start_date (datetime): Test campaign start date
        test_end_date (datetime): Test campaign end date
        status (SampleStatus): Current sample status
        location (str): Current physical location
        condition_notes (str): Notes on sample condition
        special_requirements (str): Special handling or test requirements
        metadata (dict): Additional flexible metadata (JSON)
        visual_inspection_images (list): URLs to inspection photos
        nameplate_image (str): URL to nameplate photo
        created_by (UUID): User who created the record
        created_at (datetime): Record creation timestamp
        updated_at (datetime): Last update timestamp
        deleted_at (datetime): Soft delete timestamp

    Relationships:
        tests: List of Test records associated with this sample
        reports: List of Report records for this sample
        audit_logs: Audit trail entries for this sample

    Example:
        >>> sample = Sample(
        ...     sample_id="PV-2024-001",
        ...     manufacturer="SolarTech Inc",
        ...     model="ST-400M-72",
        ...     technology=ModuleTechnology.MONOCRYSTALLINE,
        ...     rated_power_wp=400.0,
        ...     test_standard="IEC 61215-2021"
        ... )
        >>> session.add(sample)
        >>> session.commit()
    """

    __tablename__ = "samples"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Identification
    sample_id = Column(String(50), unique=True, nullable=False, index=True)
    manufacturer = Column(String(255), nullable=False)
    model = Column(String(255), nullable=False)
    serial_number = Column(String(255), nullable=True)

    # Technology classification
    technology = Column(Enum(ModuleTechnology), nullable=False)
    cell_technology = Column(String(255), nullable=True)

    # Electrical ratings
    rated_power_wp = Column(Float, nullable=True)
    rated_voltage_v = Column(Float, nullable=True)
    rated_current_a = Column(Float, nullable=True)
    open_circuit_voltage_v = Column(Float, nullable=True)
    short_circuit_current_a = Column(Float, nullable=True)
    max_power_voltage_v = Column(Float, nullable=True)
    max_power_current_a = Column(Float, nullable=True)

    # Physical dimensions
    length_mm = Column(Float, nullable=True)
    width_mm = Column(Float, nullable=True)
    thickness_mm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    area_m2 = Column(Float, nullable=True)

    # Construction details
    num_cells = Column(Integer, nullable=True)
    frame_type = Column(String(255), nullable=True)
    junction_box_type = Column(String(255), nullable=True)
    cable_length_mm = Column(Float, nullable=True)
    connector_type = Column(String(100), nullable=True)
    glass_type = Column(String(255), nullable=True)
    backsheet_type = Column(String(255), nullable=True)
    encapsulant_type = Column(String(255), nullable=True)

    # Test campaign
    test_standard = Column(String(100), nullable=False, default="IEC 61215-2021")
    test_sequence = Column(String(100), nullable=True)
    protocol_id = Column(UUID(as_uuid=True), ForeignKey("test_protocols.id"), nullable=True)

    # Customer information
    customer_name = Column(String(255), nullable=True)
    customer_ref = Column(String(255), nullable=True)
    purchase_order = Column(String(255), nullable=True)

    # Dates and timeline
    received_date = Column(DateTime, nullable=True)
    conditioning_start = Column(DateTime, nullable=True)
    conditioning_end = Column(DateTime, nullable=True)
    test_start_date = Column(DateTime, nullable=True)
    test_end_date = Column(DateTime, nullable=True)
    expected_completion = Column(DateTime, nullable=True)

    # Status and location
    status = Column(Enum(SampleStatus), nullable=False, default=SampleStatus.RECEIVED)
    location = Column(String(255), nullable=True)
    storage_location = Column(String(255), nullable=True)

    # Condition and notes
    condition_on_receipt = Column(Text, nullable=True)
    condition_notes = Column(Text, nullable=True)
    special_requirements = Column(Text, nullable=True)
    handling_precautions = Column(Text, nullable=True)

    # Images and attachments
    nameplate_image = Column(String(500), nullable=True)
    visual_inspection_images = Column(JSON, nullable=True)  # List of image URLs
    documentation = Column(JSON, nullable=True)  # Datasheet, certifications, etc.

    # Flexible metadata
    metadata = Column(JSON, nullable=True)
    custom_fields = Column(JSON, nullable=True)

    # Audit fields
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    tests = relationship("Test", back_populates="sample", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="sample", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", foreign_keys="AuditLog.entity_id",
                             primaryjoin="and_(Sample.id==AuditLog.entity_id, "
                                        "AuditLog.entity_type=='sample')",
                             viewonly=True)

    def __repr__(self) -> str:
        return f"<Sample(id={self.id}, sample_id='{self.sample_id}', " \
               f"manufacturer='{self.manufacturer}', model='{self.model}', " \
               f"status='{self.status}')>"

    def to_dict(self) -> dict:
        """Convert sample to dictionary representation"""
        return {
            "id": str(self.id),
            "sample_id": self.sample_id,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "serial_number": self.serial_number,
            "technology": self.technology.value if self.technology else None,
            "rated_power_wp": self.rated_power_wp,
            "status": self.status.value if self.status else None,
            "test_standard": self.test_standard,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
