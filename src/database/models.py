"""
SQLAlchemy ORM models for PV Test Report Automation.

ISO 17025 and NABL compliant database schema with full audit trail.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class TestSampleDB(Base):
    """Test sample database model."""

    __tablename__ = "test_samples"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    sample_id = Column(String(100), unique=True, nullable=False, index=True)
    module_type = Column(String(200), nullable=False)
    manufacturer = Column(String(200), nullable=False)
    serial_number = Column(String(100), unique=True, nullable=False)
    rated_power = Column(Float, nullable=False)
    voltage_oc = Column(Float, nullable=False)
    current_sc = Column(Float, nullable=False)
    voltage_mpp = Column(Float, nullable=False)
    current_mpp = Column(Float, nullable=False)
    dimensions = Column(JSON)
    weight = Column(Float)
    cell_technology = Column(String(100))
    received_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    # Relationships
    reports = relationship("TestReportDB", back_populates="sample")


class TestReportDB(Base):
    """Test report database model."""

    __tablename__ = "test_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    report_number = Column(String(100), unique=True, nullable=False, index=True)
    test_type = Column(String(100), nullable=False, index=True)
    sample_id = Column(UUID(as_uuid=True), ForeignKey("test_samples.id"), nullable=False)

    # Test metadata
    test_start_date = Column(DateTime)
    test_end_date = Column(DateTime)
    test_engineer = Column(String(200))
    reviewer = Column(String(200))
    approver = Column(String(200))

    # Status fields
    status = Column(
        Enum("pending", "in_progress", "completed", "failed", "cancelled", name="test_status"),
        default="pending",
        nullable=False,
    )
    review_status = Column(
        Enum(
            "draft",
            "pending_review",
            "in_review",
            "approved",
            "rejected",
            "revision_required",
            name="review_status",
        ),
        default="draft",
        nullable=False,
    )

    # Data fields
    test_results = Column(JSON, default=dict)
    compliance_standards = Column(JSON, default=list)
    attachments = Column(JSON, default=list)

    # Audit trail
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(200))
    updated_by = Column(String(200))
    is_deleted = Column(Boolean, default=False)

    # Relationships
    sample = relationship("TestSampleDB", back_populates="reports")
    test_conditions = relationship("TestConditionDB", back_populates="report")
    calibration_records = relationship("CalibrationRecordDB", back_populates="report")
    comments = relationship("CommentDB", back_populates="report")


class TestConditionDB(Base):
    """Test conditions database model."""

    __tablename__ = "test_conditions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("test_reports.id"), nullable=False)

    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    pressure = Column(Float)
    irradiance = Column(Float)
    measurement_time = Column(DateTime, default=datetime.utcnow)
    calibration_date = Column(DateTime)
    equipment_id = Column(String(100))

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    report = relationship("TestReportDB", back_populates="test_conditions")


class CalibrationRecordDB(Base):
    """Calibration record database model."""

    __tablename__ = "calibration_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("test_reports.id"), nullable=False)

    equipment_id = Column(String(100), nullable=False, index=True)
    equipment_name = Column(String(200), nullable=False)
    calibration_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    calibration_certificate = Column(String(200), nullable=False)
    calibrated_by = Column(String(200))
    calibration_lab = Column(String(200))
    traceability = Column(Text)
    uncertainty = Column(JSON)
    status = Column(String(50), default="valid")

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    report = relationship("TestReportDB", back_populates="calibration_records")


class CommentDB(Base):
    """Comment/review comment database model."""

    __tablename__ = "comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("test_reports.id"), nullable=False)

    comment_text = Column(Text, nullable=False)
    comment_type = Column(String(50))  # review, technical, administrative
    author = Column(String(200), nullable=False)
    resolved = Column(Boolean, default=False)
    resolved_by = Column(String(200))
    resolved_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    report = relationship("TestReportDB", back_populates="comments")


class UserDB(Base):
    """User database model."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    full_name = Column(String(200))
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # admin, engineer, reviewer, viewer
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    # NABL compliance
    nabl_authorized = Column(Boolean, default=False)
    digital_signature = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)


class APIKeyDB(Base):
    """API key vault database model."""

    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    provider = Column(String(100), nullable=False, index=True)
    key_name = Column(String(200), nullable=False)
    encrypted_key = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(200))
    expires_at = Column(DateTime)


class ExportLogDB(Base):
    """Export operation log."""

    __tablename__ = "export_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    report_id = Column(UUID(as_uuid=True), nullable=False)
    format = Column(String(50), nullable=False)
    file_path = Column(String(500))
    file_size = Column(Integer)
    status = Column(String(50))
    error_message = Column(Text)
    exported_by = Column(String(200))

    created_at = Column(DateTime, default=datetime.utcnow)
