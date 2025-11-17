"""
Report Model

Manages test report generation, review workflows, and multi-format export
capabilities for PV module testing.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from sqlmodel import SQLModel, Field, Column, String, JSON, Integer
from sqlalchemy import Index, UniqueConstraint


class ReportType(str, Enum):
    """Type of test report"""
    TYPE_APPROVAL = "type_approval"
    SAMPLE_TEST = "sample_test"
    FACTORY_INSPECTION = "factory_inspection"
    SURVEILLANCE = "surveillance"
    WITNESS_TEST = "witness_test"
    CUSTOM = "custom"


class ReportStatus(str, Enum):
    """Report workflow status"""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    REVIEWED = "reviewed"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ISSUED = "issued"
    REVISED = "revised"
    CANCELLED = "cancelled"


class ReportFormat(str, Enum):
    """Export format for reports"""
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    LATEX = "latex"
    JSON = "json"
    XML = "xml"


class Report(SQLModel, table=True):
    """
    Report model for managing test reports with workflow and versioning.

    Attributes:
        id: Unique report identifier
        report_number: Human-readable report number (e.g., RPT-2024-001)
        revision: Report revision number
        type: Report type
        protocol: Test protocol/standard
        sample_id: Foreign key to Sample
        customer: Customer information
        title: Report title
        summary: Executive summary
        sections: Report sections structure (JSON)
        tables: Data tables for inclusion (JSON)
        graphs: Graph/chart specifications (JSON)
        annex_links: Links to annexes and supporting documents
        test_ids: Array of test IDs included in report
        prepared_by_user_id: User who prepared the report
        reviewed_by_user_id: User who reviewed the report
        approved_by_user_id: User who approved the report
        issue_date: Report issue date
        review_history: Review and approval workflow history
        status: Current report status
        export_formats: Available export formats
        generated_files: Paths to generated report files
        template_used: Template identifier used
        metadata: Additional metadata (standards, accreditations, etc.)
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "reports"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Report identification
    report_number: str = Field(max_length=100, index=True)
    revision: int = Field(default=0, ge=0)
    type: ReportType = Field(sa_column=Column(String(50)), index=True)

    # Protocol and standards
    protocol: str = Field(
        max_length=200,
        index=True,
        description="Primary test protocol (e.g., IEC 61215-2:2021)"
    )

    additional_standards: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Additional applicable standards"
    )

    # Sample reference
    sample_id: int = Field(foreign_key="samples.id", index=True)

    # Customer information
    customer: Dict[str, Any] = Field(
        sa_column=Column(JSON),
        description="Customer name, address, contact, PO number"
    )

    # Report content
    title: str = Field(max_length=500)
    summary: Optional[str] = Field(default=None, description="Executive summary")

    sections: List[Dict[str, Any]] = Field(
        sa_column=Column(JSON),
        description="Report sections with headings, content, order"
    )

    tables: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Data tables with headers, rows, formatting"
    )

    graphs: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Graph specifications: I-V curves, degradation plots, etc."
    )

    annex_links: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Links to annexes, raw data, calibration certificates"
    )

    # Test references
    test_ids: List[int] = Field(
        sa_column=Column(JSON),
        description="Array of test IDs included in this report"
    )

    # Personnel
    prepared_by_user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    reviewed_by_user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    approved_by_user_id: Optional[int] = Field(default=None, foreign_key="users.id")

    # Dates
    prepared_date: Optional[datetime] = Field(default=None)
    reviewed_date: Optional[datetime] = Field(default=None)
    approved_date: Optional[datetime] = Field(default=None)
    issue_date: Optional[datetime] = Field(default=None, index=True)

    # Workflow
    status: ReportStatus = Field(default=ReportStatus.DRAFT, sa_column=Column(String(50)), index=True)

    review_history: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Review and approval workflow history with timestamps and comments"
    )

    # Export and generation
    export_formats: List[str] = Field(
        default=["pdf"],
        sa_column=Column(JSON),
        description="Available export formats"
    )

    generated_files: Optional[Dict[str, str]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Mapping of format to file path for generated reports"
    )

    template_used: Optional[str] = Field(default=None, max_length=200)

    # Metadata
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Accreditations, lab info, certifications, QR codes, etc."
    )

    # Signatures
    signatures: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Digital signatures of prepared, reviewed, approved personnel"
    )

    # Version control
    parent_report_id: Optional[int] = Field(
        default=None,
        foreign_key="reports.id",
        description="Reference to previous version if this is a revision"
    )

    revision_reason: Optional[str] = Field(default=None, description="Reason for revision")

    # Additional information
    notes: Optional[str] = Field(default=None)
    confidentiality_level: Optional[str] = Field(default="standard", max_length=50)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Table constraints
    __table_args__ = (
        UniqueConstraint('report_number', 'revision', name='uq_report_number_revision'),
        Index('ix_report_sample_status', 'sample_id', 'status'),
        Index('ix_report_type_protocol', 'type', 'protocol'),
        Index('ix_report_issue_date', 'issue_date'),
        Index('ix_report_status', 'status'),
    )

    def get_full_report_number(self) -> str:
        """
        Get full report number with revision.

        Returns:
            Report number with revision (e.g., RPT-2024-001 Rev. 1)
        """
        if self.revision > 0:
            return f"{self.report_number} Rev. {self.revision}"
        return self.report_number

    def add_review_entry(
        self,
        user_id: int,
        action: str,
        comments: Optional[str] = None,
        status_change: Optional[str] = None
    ) -> None:
        """
        Add entry to review history.

        Args:
            user_id: ID of user performing action
            action: Action taken (submitted, reviewed, approved, rejected, etc.)
            comments: Review comments
            status_change: New status if changed
        """
        if self.review_history is None:
            self.review_history = []

        entry = {
            "user_id": user_id,
            "action": action,
            "timestamp": datetime.utcnow().isoformat(),
            "comments": comments,
            "status_change": status_change
        }
        self.review_history.append(entry)
        self.update_timestamp()

    def submit_for_review(self, user_id: int) -> None:
        """
        Submit report for review.

        Args:
            user_id: ID of user submitting report
        """
        self.status = ReportStatus.IN_REVIEW
        self.prepared_date = datetime.utcnow()
        self.prepared_by_user_id = user_id
        self.add_review_entry(user_id, "submitted_for_review", status_change="in_review")

    def approve_report(self, user_id: int, comments: Optional[str] = None) -> None:
        """
        Approve report.

        Args:
            user_id: ID of approving user
            comments: Approval comments
        """
        self.status = ReportStatus.APPROVED
        self.approved_by_user_id = user_id
        self.approved_date = datetime.utcnow()
        self.add_review_entry(user_id, "approved", comments, status_change="approved")

    def reject_report(self, user_id: int, comments: str) -> None:
        """
        Reject report.

        Args:
            user_id: ID of user rejecting report
            comments: Rejection reason
        """
        self.status = ReportStatus.REJECTED
        self.add_review_entry(user_id, "rejected", comments, status_change="rejected")

    def issue_report(self, user_id: int) -> None:
        """
        Issue approved report.

        Args:
            user_id: ID of user issuing report
        """
        if self.status != ReportStatus.APPROVED:
            raise ValueError("Report must be approved before issuing")

        self.status = ReportStatus.ISSUED
        self.issue_date = datetime.utcnow()
        self.add_review_entry(user_id, "issued", status_change="issued")

    def create_revision(self, reason: str) -> Dict[str, Any]:
        """
        Create a new revision of this report.

        Args:
            reason: Reason for creating revision

        Returns:
            Dictionary with new revision data
        """
        return {
            "report_number": self.report_number,
            "revision": self.revision + 1,
            "parent_report_id": self.id,
            "revision_reason": reason,
            "type": self.type,
            "protocol": self.protocol,
            "sample_id": self.sample_id,
            "customer": self.customer,
            "title": self.title,
            "status": ReportStatus.DRAFT
        }

    def add_generated_file(self, format: str, file_path: str) -> None:
        """
        Add generated file path.

        Args:
            format: Export format (pdf, docx, etc.)
            file_path: Path to generated file
        """
        if self.generated_files is None:
            self.generated_files = {}

        self.generated_files[format] = file_path
        self.update_timestamp()

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()

    class Config:
        json_schema_extra = {
            "example": {
                "report_number": "RPT-2024-001",
                "revision": 0,
                "type": "type_approval",
                "protocol": "IEC 61215-2:2021",
                "sample_id": 1,
                "customer": {
                    "name": "Solar Tech Industries",
                    "address": "123 Solar St, Tech City",
                    "contact": "John Doe",
                    "po_number": "PO-2024-1234"
                },
                "title": "Type Approval Test Report - HES-400W-MONO",
                "test_ids": [1, 2, 3, 4, 5],
                "export_formats": ["pdf", "docx"],
                "status": "draft"
            }
        }
