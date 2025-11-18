"""
Review Engine for ISO 17025 Compliant Report Review Workflow

This module provides comprehensive review workflow management including:
- Auto-assignment based on technician and test type
- Multi-level review support (technical, management, quality)
- Review status tracking with complete audit trail
- Version control for report iterations
- ISO 17025 compliance features
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Any
import json
import hashlib
from pathlib import Path


class ReviewStatus(Enum):
    """Review status enumeration"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    COMMENTS_ADDED = "comments_added"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUIRED = "revision_required"
    ESCALATED = "escalated"


class ReviewLevel(Enum):
    """Review level enumeration for multi-level review"""
    TECHNICAL = "technical"  # Technical review by peer technician
    MANAGEMENT = "management"  # Management review by supervisor
    QUALITY = "quality"  # Quality assurance review
    FINAL = "final"  # Final approval


class ReviewerRole(Enum):
    """Reviewer role types"""
    TECHNICIAN = "technician"
    SUPERVISOR = "supervisor"
    QUALITY_MANAGER = "quality_manager"
    TECHNICAL_DIRECTOR = "technical_director"


@dataclass
class Reviewer:
    """Reviewer information"""
    user_id: str
    name: str
    email: str
    role: ReviewerRole
    specializations: List[str] = field(default_factory=list)
    max_concurrent_reviews: int = 5

    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'role': self.role.value,
            'specializations': self.specializations,
            'max_concurrent_reviews': self.max_concurrent_reviews
        }


@dataclass
class ReportVersion:
    """Report version information for version control"""
    version_id: str
    version_number: int
    report_id: str
    created_at: datetime
    created_by: str
    changes_summary: str
    file_hash: str
    file_path: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'version_id': self.version_id,
            'version_number': self.version_number,
            'report_id': self.report_id,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'changes_summary': self.changes_summary,
            'file_hash': self.file_hash,
            'file_path': self.file_path,
            'metadata': self.metadata
        }


@dataclass
class ReviewAssignment:
    """Review assignment details"""
    assignment_id: str
    report_id: str
    version_id: str
    reviewer: Reviewer
    review_level: ReviewLevel
    assigned_at: datetime
    assigned_by: str
    due_date: datetime
    status: ReviewStatus
    completed_at: Optional[datetime] = None
    decision: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'assignment_id': self.assignment_id,
            'report_id': self.report_id,
            'version_id': self.version_id,
            'reviewer': self.reviewer.to_dict(),
            'review_level': self.review_level.value,
            'assigned_at': self.assigned_at.isoformat(),
            'assigned_by': self.assigned_by,
            'due_date': self.due_date.isoformat(),
            'status': self.status.value,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'decision': self.decision,
            'notes': self.notes
        }


@dataclass
class ReviewHistory:
    """Complete review history entry for audit trail"""
    history_id: str
    report_id: str
    version_id: str
    assignment_id: str
    action: str
    performed_by: str
    performed_at: datetime
    old_status: Optional[ReviewStatus]
    new_status: ReviewStatus
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'history_id': self.history_id,
            'report_id': self.report_id,
            'version_id': self.version_id,
            'assignment_id': self.assignment_id,
            'action': self.action,
            'performed_by': self.performed_by,
            'performed_at': self.performed_at.isoformat(),
            'old_status': self.old_status.value if self.old_status else None,
            'new_status': self.new_status.value,
            'details': self.details
        }


class ReviewEngine:
    """
    Core review engine for managing report review workflow

    Features:
    - Auto-assignment based on technician workload and specialization
    - Multi-level review workflow
    - Version control and comparison
    - Complete audit trail
    - ISO 17025 compliance
    """

    def __init__(self, data_dir: str = "data/reviews"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.reviewers: Dict[str, Reviewer] = {}
        self.assignments: Dict[str, ReviewAssignment] = {}
        self.versions: Dict[str, List[ReportVersion]] = {}
        self.history: List[ReviewHistory] = []

        # Review configuration
        self.review_config = {
            'technical_review_required': True,
            'management_review_required': True,
            'quality_review_threshold': 'critical',  # critical, all, none
            'auto_assignment_enabled': True,
            'sla_hours': {
                ReviewLevel.TECHNICAL: 24,
                ReviewLevel.MANAGEMENT: 48,
                ReviewLevel.QUALITY: 72,
                ReviewLevel.FINAL: 24
            }
        }

        self._load_data()

    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID with timestamp"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        return f"{prefix}_{timestamp}"

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file for version control"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except FileNotFoundError:
            return ""

    def register_reviewer(self, reviewer: Reviewer) -> None:
        """Register a new reviewer in the system"""
        self.reviewers[reviewer.user_id] = reviewer
        self._save_data()

    def create_report_version(
        self,
        report_id: str,
        file_path: str,
        created_by: str,
        changes_summary: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ReportVersion:
        """Create a new version of a report"""
        if report_id not in self.versions:
            self.versions[report_id] = []

        version_number = len(self.versions[report_id]) + 1
        version_id = self._generate_id(f"VER_{report_id}")
        file_hash = self._calculate_file_hash(file_path)

        version = ReportVersion(
            version_id=version_id,
            version_number=version_number,
            report_id=report_id,
            created_at=datetime.now(),
            created_by=created_by,
            changes_summary=changes_summary,
            file_hash=file_hash,
            file_path=file_path,
            metadata=metadata or {}
        )

        self.versions[report_id].append(version)
        self._save_data()

        return version

    def get_latest_version(self, report_id: str) -> Optional[ReportVersion]:
        """Get the latest version of a report"""
        if report_id not in self.versions or not self.versions[report_id]:
            return None
        return self.versions[report_id][-1]

    def get_version_history(self, report_id: str) -> List[ReportVersion]:
        """Get complete version history for a report"""
        return self.versions.get(report_id, [])

    def auto_assign_reviewer(
        self,
        report_id: str,
        test_type: str,
        technician_id: str,
        review_level: ReviewLevel
    ) -> Optional[Reviewer]:
        """
        Auto-assign reviewer based on:
        - Specialization match
        - Current workload
        - Avoid self-review
        """
        eligible_reviewers = []

        # Filter reviewers based on role and level
        role_requirements = {
            ReviewLevel.TECHNICAL: [ReviewerRole.TECHNICIAN, ReviewerRole.SUPERVISOR],
            ReviewLevel.MANAGEMENT: [ReviewerRole.SUPERVISOR, ReviewerRole.TECHNICAL_DIRECTOR],
            ReviewLevel.QUALITY: [ReviewerRole.QUALITY_MANAGER],
            ReviewLevel.FINAL: [ReviewerRole.TECHNICAL_DIRECTOR]
        }

        required_roles = role_requirements.get(review_level, [])

        for reviewer in self.reviewers.values():
            # Skip if wrong role
            if reviewer.role not in required_roles:
                continue

            # Skip self-review
            if reviewer.user_id == technician_id:
                continue

            # Check specialization match
            if test_type and reviewer.specializations:
                if test_type not in reviewer.specializations:
                    continue

            # Check current workload
            current_assignments = sum(
                1 for a in self.assignments.values()
                if a.reviewer.user_id == reviewer.user_id
                and a.status in [ReviewStatus.PENDING, ReviewStatus.IN_REVIEW]
            )

            if current_assignments >= reviewer.max_concurrent_reviews:
                continue

            eligible_reviewers.append((reviewer, current_assignments))

        # Sort by workload (ascending) and return least loaded reviewer
        if eligible_reviewers:
            eligible_reviewers.sort(key=lambda x: x[1])
            return eligible_reviewers[0][0]

        return None

    def assign_review(
        self,
        report_id: str,
        version_id: str,
        reviewer: Reviewer,
        review_level: ReviewLevel,
        assigned_by: str,
        notes: str = ""
    ) -> ReviewAssignment:
        """Assign a review to a reviewer"""
        assignment_id = self._generate_id("ASGN")

        # Calculate due date based on SLA
        sla_hours = self.review_config['sla_hours'].get(review_level, 48)
        due_date = datetime.now() + timedelta(hours=sla_hours)

        assignment = ReviewAssignment(
            assignment_id=assignment_id,
            report_id=report_id,
            version_id=version_id,
            reviewer=reviewer,
            review_level=review_level,
            assigned_at=datetime.now(),
            assigned_by=assigned_by,
            due_date=due_date,
            status=ReviewStatus.PENDING,
            notes=notes
        )

        self.assignments[assignment_id] = assignment

        # Record in history
        self._add_history(
            report_id=report_id,
            version_id=version_id,
            assignment_id=assignment_id,
            action="review_assigned",
            performed_by=assigned_by,
            old_status=None,
            new_status=ReviewStatus.PENDING,
            details={
                'reviewer': reviewer.name,
                'review_level': review_level.value,
                'due_date': due_date.isoformat()
            }
        )

        self._save_data()
        return assignment

    def initiate_review_workflow(
        self,
        report_id: str,
        version_id: str,
        test_type: str,
        technician_id: str,
        initiated_by: str
    ) -> List[ReviewAssignment]:
        """
        Initiate complete multi-level review workflow
        Returns list of assignments created
        """
        assignments = []

        # Technical review
        if self.review_config['technical_review_required']:
            tech_reviewer = self.auto_assign_reviewer(
                report_id, test_type, technician_id, ReviewLevel.TECHNICAL
            )
            if tech_reviewer:
                assignment = self.assign_review(
                    report_id, version_id, tech_reviewer,
                    ReviewLevel.TECHNICAL, initiated_by,
                    "Technical peer review required"
                )
                assignments.append(assignment)

        # Management review
        if self.review_config['management_review_required']:
            mgmt_reviewer = self.auto_assign_reviewer(
                report_id, test_type, technician_id, ReviewLevel.MANAGEMENT
            )
            if mgmt_reviewer:
                assignment = self.assign_review(
                    report_id, version_id, mgmt_reviewer,
                    ReviewLevel.MANAGEMENT, initiated_by,
                    "Management review required"
                )
                assignments.append(assignment)

        return assignments

    def update_review_status(
        self,
        assignment_id: str,
        new_status: ReviewStatus,
        updated_by: str,
        decision: Optional[str] = None,
        notes: str = ""
    ) -> ReviewAssignment:
        """Update review status with audit trail"""
        if assignment_id not in self.assignments:
            raise ValueError(f"Assignment {assignment_id} not found")

        assignment = self.assignments[assignment_id]
        old_status = assignment.status

        assignment.status = new_status
        if decision:
            assignment.decision = decision
        if notes:
            assignment.notes = notes

        if new_status in [ReviewStatus.APPROVED, ReviewStatus.REJECTED]:
            assignment.completed_at = datetime.now()

        # Record in history
        self._add_history(
            report_id=assignment.report_id,
            version_id=assignment.version_id,
            assignment_id=assignment_id,
            action="status_updated",
            performed_by=updated_by,
            old_status=old_status,
            new_status=new_status,
            details={
                'decision': decision,
                'notes': notes
            }
        )

        self._save_data()
        return assignment

    def get_pending_reviews(self, reviewer_id: str) -> List[ReviewAssignment]:
        """Get all pending reviews for a reviewer"""
        return [
            a for a in self.assignments.values()
            if a.reviewer.user_id == reviewer_id
            and a.status in [ReviewStatus.PENDING, ReviewStatus.IN_REVIEW, ReviewStatus.COMMENTS_ADDED]
        ]

    def get_overdue_reviews(self) -> List[ReviewAssignment]:
        """Get all overdue reviews for escalation"""
        now = datetime.now()
        return [
            a for a in self.assignments.values()
            if a.status in [ReviewStatus.PENDING, ReviewStatus.IN_REVIEW]
            and a.due_date < now
        ]

    def get_report_review_status(self, report_id: str) -> Dict[str, Any]:
        """Get comprehensive review status for a report"""
        report_assignments = [
            a for a in self.assignments.values()
            if a.report_id == report_id
        ]

        if not report_assignments:
            return {
                'report_id': report_id,
                'overall_status': 'no_reviews',
                'assignments': []
            }

        # Determine overall status
        statuses = [a.status for a in report_assignments]
        if all(s == ReviewStatus.APPROVED for s in statuses):
            overall_status = 'fully_approved'
        elif any(s == ReviewStatus.REJECTED for s in statuses):
            overall_status = 'rejected'
        elif any(s == ReviewStatus.IN_REVIEW for s in statuses):
            overall_status = 'in_review'
        else:
            overall_status = 'pending'

        return {
            'report_id': report_id,
            'overall_status': overall_status,
            'assignments': [a.to_dict() for a in report_assignments],
            'version_history': [v.to_dict() for v in self.get_version_history(report_id)]
        }

    def _add_history(
        self,
        report_id: str,
        version_id: str,
        assignment_id: str,
        action: str,
        performed_by: str,
        old_status: Optional[ReviewStatus],
        new_status: ReviewStatus,
        details: Dict[str, Any]
    ) -> None:
        """Add entry to review history for audit trail"""
        history_id = self._generate_id("HIST")

        history_entry = ReviewHistory(
            history_id=history_id,
            report_id=report_id,
            version_id=version_id,
            assignment_id=assignment_id,
            action=action,
            performed_by=performed_by,
            performed_at=datetime.now(),
            old_status=old_status,
            new_status=new_status,
            details=details
        )

        self.history.append(history_entry)

    def get_audit_trail(
        self,
        report_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ReviewHistory]:
        """Get audit trail with optional filters"""
        filtered_history = self.history

        if report_id:
            filtered_history = [h for h in filtered_history if h.report_id == report_id]

        if start_date:
            filtered_history = [h for h in filtered_history if h.performed_at >= start_date]

        if end_date:
            filtered_history = [h for h in filtered_history if h.performed_at <= end_date]

        return sorted(filtered_history, key=lambda x: x.performed_at, reverse=True)

    def export_audit_report(
        self,
        report_id: str,
        output_path: str
    ) -> None:
        """Export complete audit report for ISO 17025 compliance"""
        audit_data = {
            'report_id': report_id,
            'generated_at': datetime.now().isoformat(),
            'review_status': self.get_report_review_status(report_id),
            'audit_trail': [h.to_dict() for h in self.get_audit_trail(report_id)],
            'version_history': [v.to_dict() for v in self.get_version_history(report_id)]
        }

        with open(output_path, 'w') as f:
            json.dump(audit_data, f, indent=2, default=str)

    def _save_data(self) -> None:
        """Save all data to disk"""
        data = {
            'reviewers': {k: v.to_dict() for k, v in self.reviewers.items()},
            'assignments': {k: v.to_dict() for k, v in self.assignments.items()},
            'versions': {
                k: [v.to_dict() for v in versions]
                for k, versions in self.versions.items()
            },
            'history': [h.to_dict() for h in self.history]
        }

        with open(self.data_dir / 'review_engine.json', 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def _load_data(self) -> None:
        """Load data from disk"""
        data_file = self.data_dir / 'review_engine.json'
        if not data_file.exists():
            return

        try:
            with open(data_file, 'r') as f:
                data = json.load(f)

            # Load reviewers
            for user_id, reviewer_data in data.get('reviewers', {}).items():
                self.reviewers[user_id] = Reviewer(
                    user_id=reviewer_data['user_id'],
                    name=reviewer_data['name'],
                    email=reviewer_data['email'],
                    role=ReviewerRole(reviewer_data['role']),
                    specializations=reviewer_data.get('specializations', []),
                    max_concurrent_reviews=reviewer_data.get('max_concurrent_reviews', 5)
                )

            # Load assignments
            for assignment_id, assignment_data in data.get('assignments', {}).items():
                reviewer_data = assignment_data['reviewer']
                self.assignments[assignment_id] = ReviewAssignment(
                    assignment_id=assignment_data['assignment_id'],
                    report_id=assignment_data['report_id'],
                    version_id=assignment_data['version_id'],
                    reviewer=Reviewer(
                        user_id=reviewer_data['user_id'],
                        name=reviewer_data['name'],
                        email=reviewer_data['email'],
                        role=ReviewerRole(reviewer_data['role']),
                        specializations=reviewer_data.get('specializations', [])
                    ),
                    review_level=ReviewLevel(assignment_data['review_level']),
                    assigned_at=datetime.fromisoformat(assignment_data['assigned_at']),
                    assigned_by=assignment_data['assigned_by'],
                    due_date=datetime.fromisoformat(assignment_data['due_date']),
                    status=ReviewStatus(assignment_data['status']),
                    completed_at=datetime.fromisoformat(assignment_data['completed_at']) if assignment_data.get('completed_at') else None,
                    decision=assignment_data.get('decision'),
                    notes=assignment_data.get('notes', '')
                )

            # Load versions
            for report_id, versions_data in data.get('versions', {}).items():
                self.versions[report_id] = [
                    ReportVersion(
                        version_id=v['version_id'],
                        version_number=v['version_number'],
                        report_id=v['report_id'],
                        created_at=datetime.fromisoformat(v['created_at']),
                        created_by=v['created_by'],
                        changes_summary=v['changes_summary'],
                        file_hash=v['file_hash'],
                        file_path=v['file_path'],
                        metadata=v.get('metadata', {})
                    )
                    for v in versions_data
                ]

            # Load history
            for history_data in data.get('history', []):
                self.history.append(ReviewHistory(
                    history_id=history_data['history_id'],
                    report_id=history_data['report_id'],
                    version_id=history_data['version_id'],
                    assignment_id=history_data['assignment_id'],
                    action=history_data['action'],
                    performed_by=history_data['performed_by'],
                    performed_at=datetime.fromisoformat(history_data['performed_at']),
                    old_status=ReviewStatus(history_data['old_status']) if history_data.get('old_status') else None,
                    new_status=ReviewStatus(history_data['new_status']),
                    details=history_data.get('details', {})
                ))

        except Exception as e:
            print(f"Error loading data: {e}")
