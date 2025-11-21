"""
Report Model - Test report generation and management

Implements comprehensive test report models compliant with IEC/ISO standards.
Supports versioning, multi-language, and various export formats.
"""

import uuid
from datetime import datetime
import enum
from sqlalchemy import Column, String, DateTime, Text, JSON, Enum, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.database.base import Base


class ReportStatus(str, enum.Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ISSUED = "issued"
    REVISED = "revised"
    CANCELLED = "cancelled"


class Report(Base):
    """Test Report Model - IEC 61215 compliant reports"""
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_number = Column(String(50), unique=True, nullable=False, index=True)
    sample_id = Column(UUID(as_uuid=True), ForeignKey("samples.id"), nullable=False)
    title = Column(String(500), nullable=False)
    status = Column(Enum(ReportStatus), nullable=False, default=ReportStatus.DRAFT)
    version = Column(Integer, default=1)
    language = Column(String(10), default="en")
    template_id = Column(String(100), nullable=True)

    # Content
    executive_summary = Column(Text, nullable=True)
    test_results_summary = Column(JSON, nullable=True)
    conclusions = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)

    # Metadata
    generated_at = Column(DateTime, nullable=True)
    issued_at = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)

    # Personnel
    prepared_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sample = relationship("Sample", back_populates="reports")
    sections = relationship("ReportSection", back_populates="report", cascade="all, delete-orphan")


class ReportSection(Base):
    """Report Section Model - Individual sections of test reports"""
    __tablename__ = "report_sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False)
    section_number = Column(String(20), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    content_type = Column(String(50), default="markdown")  # markdown, html, latex
    order = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    report = relationship("Report", back_populates="sections")
