"""
Equipment and Calibration Models

Manages test equipment inventory, calibration tracking, and measurement uncertainty
compliant with ISO 17025 and NABL requirements.
"""

import uuid
from datetime import datetime
import enum
from sqlalchemy import Column, String, DateTime, Text, JSON, Enum, ForeignKey, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.database.base import Base


class EquipmentStatus(str, enum.Enum):
    OPERATIONAL = "operational"
    CALIBRATION_DUE = "calibration_due"
    OUT_OF_SERVICE = "out_of_service"
    UNDER_REPAIR = "under_repair"
    RETIRED = "retired"


class EquipmentType(str, enum.Enum):
    SOLAR_SIMULATOR = "solar_simulator"
    IV_TRACER = "iv_tracer"
    MULTIMETER = "multimeter"
    THERMAL_CHAMBER = "thermal_chamber"
    HUMIDITY_CHAMBER = "humidity_chamber"
    INSULATION_TESTER = "insulation_tester"
    EL_CAMERA = "el_camera"
    IR_CAMERA = "ir_camera"
    PYRANOMETER = "pyranometer"
    TEMPERATURE_SENSOR = "temperature_sensor"


class Equipment(Base):
    """Equipment Inventory - ISO 17025 compliant tracking"""
    __tablename__ = "equipment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    equipment_type = Column(Enum(EquipmentType), nullable=False)

    # Identification
    manufacturer = Column(String(255), nullable=True)
    model = Column(String(255), nullable=True)
    serial_number = Column(String(255), nullable=True)

    # Status and location
    status = Column(Enum(EquipmentStatus), nullable=False, default=EquipmentStatus.OPERATIONAL)
    location = Column(String(255), nullable=True)
    responsible_person = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Calibration requirements
    calibration_frequency_days = Column(Integer, nullable=False, default=365)
    next_calibration_date = Column(DateTime, nullable=True)
    calibration_alert_days = Column(Integer, default=30)

    # Specifications
    specifications = Column(JSON, nullable=True)
    measurement_range = Column(JSON, nullable=True)
    accuracy = Column(JSON, nullable=True)
    uncertainty = Column(JSON, nullable=True)

    # Maintenance
    last_maintenance_date = Column(DateTime, nullable=True)
    maintenance_notes = Column(Text, nullable=True)

    # Documentation
    manual_url = Column(String(500), nullable=True)
    certificate_url = Column(String(500), nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    calibrations = relationship("Calibration", back_populates="equipment", cascade="all, delete-orphan")


class Calibration(Base):
    """Calibration Records - ISO 17025 compliance"""
    __tablename__ = "calibrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_id = Column(UUID(as_uuid=True), ForeignKey("equipment.id"), nullable=False)

    # Calibration details
    calibration_date = Column(DateTime, nullable=False)
    next_calibration_date = Column(DateTime, nullable=False)
    calibration_lab = Column(String(255), nullable=False)
    certificate_number = Column(String(100), nullable=False)
    certificate_url = Column(String(500), nullable=True)

    # Results
    is_passed = Column(Boolean, nullable=False)
    calibration_results = Column(JSON, nullable=True)
    uncertainty = Column(JSON, nullable=True)
    traceability = Column(Text, nullable=True)

    # Personnel
    performed_by = Column(String(255), nullable=True)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    equipment = relationship("Equipment", back_populates="calibrations")
