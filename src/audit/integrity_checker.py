"""
Integrity Checker
Verify audit trail integrity and detect tampering.

Features:
- Verify blockchain-style hash chain integrity
- Detect any modifications to audit logs
- Validate digital signatures
- Check data consistency across database
- Generate integrity reports
"""

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import create_engine, select, and_, func
from sqlalchemy.orm import Session

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.backends import default_backend
    from cryptography.exceptions import InvalidSignature
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

from .trail_logger import AuditEventModel, AuditEvent
from .lineage_tracker import DataNodeModel


class IntegrityCheckType(str, Enum):
    """Types of integrity checks"""

    HASH_CHAIN = "HASH_CHAIN"  # Verify hash chain integrity
    SEQUENCE = "SEQUENCE"  # Verify sequence numbers
    DATA_HASH = "DATA_HASH"  # Verify data hashes
    SIGNATURE = "SIGNATURE"  # Verify digital signatures
    FOREIGN_KEY = "FOREIGN_KEY"  # Verify referential integrity
    TIMESTAMP = "TIMESTAMP"  # Verify timestamp ordering


class IntegrityIssueType(str, Enum):
    """Types of integrity issues"""

    HASH_MISMATCH = "HASH_MISMATCH"  # Hash doesn't match
    SEQUENCE_GAP = "SEQUENCE_GAP"  # Missing sequence number
    SEQUENCE_DUPLICATE = "SEQUENCE_DUPLICATE"  # Duplicate sequence
    TIMESTAMP_ANOMALY = "TIMESTAMP_ANOMALY"  # Timestamp out of order
    DATA_MODIFIED = "DATA_MODIFIED"  # Data appears modified
    SIGNATURE_INVALID = "SIGNATURE_INVALID"  # Invalid signature
    ORPHANED_RECORD = "ORPHANED_RECORD"  # Missing parent record
    CHAIN_BROKEN = "CHAIN_BROKEN"  # Hash chain is broken


class IntegrityIssue(BaseModel):
    """Integrity issue found during verification"""

    issue_type: IntegrityIssueType
    severity: str = Field(description="CRITICAL, HIGH, MEDIUM, LOW")
    description: str
    affected_record_id: Optional[UUID] = None
    affected_table: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IntegrityCheckResult(BaseModel):
    """Result of integrity verification"""

    check_type: IntegrityCheckType
    passed: bool
    total_records_checked: int
    issues_found: int
    issues: List[IntegrityIssue] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    execution_time_seconds: float = 0.0
    details: Optional[Dict[str, Any]] = None


class IntegrityReport(BaseModel):
    """Comprehensive integrity report"""

    report_id: UUID
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    generated_by: str

    overall_status: str = Field(description="PASS, FAIL, WARNING")
    total_checks: int = 0
    checks_passed: int = 0
    checks_failed: int = 0

    check_results: List[IntegrityCheckResult] = Field(default_factory=list)
    critical_issues: List[IntegrityIssue] = Field(default_factory=list)

    summary: str = ""


class IntegrityChecker:
    """
    Verify integrity of audit trail and data lineage.

    Provides:
    - Hash chain verification (blockchain-style)
    - Tamper detection
    - Digital signature validation
    - Data consistency checks
    - Comprehensive integrity reporting

    Example:
        checker = IntegrityChecker(db_url="postgresql://...")

        # Verify hash chain
        result = checker.verify_hash_chain()
        if not result.passed:
            print(f"Hash chain broken! {result.issues_found} issues found")

        # Full integrity check
        report = checker.run_full_integrity_check(
            generated_by="admin@company.com"
        )

        if report.overall_status != "PASS":
            print(f"Integrity issues detected: {len(report.critical_issues)} critical")
    """

    def __init__(self, db_url: str):
        """Initialize integrity checker"""
        self.engine = create_engine(db_url, echo=False)

    def _compute_event_hash(self, event: AuditEventModel) -> str:
        """
        Compute expected hash for an audit event.

        Must match the hashing algorithm in AuditTrailLogger.
        """
        hash_data = {
            "id": str(event.id),
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "user_id": event.user_id,
            "action": event.action,
            "old_values": event.old_values,
            "new_values": event.new_values,
            "previous_hash": event.previous_hash,
        }

        hash_string = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(hash_string.encode()).hexdigest()

    def verify_hash_chain(
        self,
        start_sequence: Optional[int] = None,
        end_sequence: Optional[int] = None
    ) -> IntegrityCheckResult:
        """
        Verify the integrity of the audit log hash chain.

        Args:
            start_sequence: Starting sequence number (None = from beginning)
            end_sequence: Ending sequence number (None = to end)

        Returns:
            IntegrityCheckResult with any issues found
        """
        import time
        start_time = time.time()

        result = IntegrityCheckResult(
            check_type=IntegrityCheckType.HASH_CHAIN,
            passed=True,
            total_records_checked=0,
            issues_found=0
        )

        with Session(self.engine) as session:
            # Build query
            stmt = select(AuditEventModel).order_by(AuditEventModel.sequence_number)

            if start_sequence is not None:
                stmt = stmt.where(AuditEventModel.sequence_number >= start_sequence)
            if end_sequence is not None:
                stmt = stmt.where(AuditEventModel.sequence_number <= end_sequence)

            events = session.execute(stmt).scalars().all()
            result.total_records_checked = len(events)

            previous_event = None
            for event in events:
                # Check hash matches computed hash
                computed_hash = self._compute_event_hash(event)
                if computed_hash != event.event_hash:
                    issue = IntegrityIssue(
                        issue_type=IntegrityIssueType.HASH_MISMATCH,
                        severity="CRITICAL",
                        description=f"Hash mismatch for event sequence {event.sequence_number}",
                        affected_record_id=event.id,
                        affected_table="audit_events",
                        details={
                            "expected_hash": computed_hash,
                            "actual_hash": event.event_hash,
                            "sequence_number": event.sequence_number
                        }
                    )
                    result.issues.append(issue)
                    result.issues_found += 1
                    result.passed = False

                # Check chain links to previous event
                if previous_event is not None:
                    if event.previous_hash != previous_event.event_hash:
                        issue = IntegrityIssue(
                            issue_type=IntegrityIssueType.CHAIN_BROKEN,
                            severity="CRITICAL",
                            description=f"Hash chain broken at sequence {event.sequence_number}",
                            affected_record_id=event.id,
                            affected_table="audit_events",
                            details={
                                "expected_previous_hash": previous_event.event_hash,
                                "actual_previous_hash": event.previous_hash,
                                "sequence_number": event.sequence_number
                            }
                        )
                        result.issues.append(issue)
                        result.issues_found += 1
                        result.passed = False

                previous_event = event

        result.execution_time_seconds = time.time() - start_time
        return result

    def verify_sequence_integrity(self) -> IntegrityCheckResult:
        """
        Verify sequence numbers are consecutive with no gaps or duplicates.

        Returns:
            IntegrityCheckResult with any issues found
        """
        import time
        start_time = time.time()

        result = IntegrityCheckResult(
            check_type=IntegrityCheckType.SEQUENCE,
            passed=True,
            total_records_checked=0,
            issues_found=0
        )

        with Session(self.engine) as session:
            # Get all sequence numbers
            stmt = select(AuditEventModel.sequence_number).order_by(AuditEventModel.sequence_number)
            sequences = session.execute(stmt).scalars().all()

            result.total_records_checked = len(sequences)

            if not sequences:
                result.execution_time_seconds = time.time() - start_time
                return result

            # Check for duplicates
            seen: Set[int] = set()
            for seq in sequences:
                if seq in seen:
                    issue = IntegrityIssue(
                        issue_type=IntegrityIssueType.SEQUENCE_DUPLICATE,
                        severity="CRITICAL",
                        description=f"Duplicate sequence number: {seq}",
                        affected_table="audit_events",
                        details={"sequence_number": seq}
                    )
                    result.issues.append(issue)
                    result.issues_found += 1
                    result.passed = False
                seen.add(seq)

            # Check for gaps
            expected_seq = 1
            for seq in sequences:
                if seq != expected_seq:
                    issue = IntegrityIssue(
                        issue_type=IntegrityIssueType.SEQUENCE_GAP,
                        severity="HIGH",
                        description=f"Sequence gap: expected {expected_seq}, found {seq}",
                        affected_table="audit_events",
                        details={
                            "expected": expected_seq,
                            "found": seq,
                            "gap_size": seq - expected_seq
                        }
                    )
                    result.issues.append(issue)
                    result.issues_found += 1
                    result.passed = False
                expected_seq = seq + 1

        result.execution_time_seconds = time.time() - start_time
        return result

    def verify_timestamp_ordering(self) -> IntegrityCheckResult:
        """
        Verify timestamps are in correct chronological order.

        Returns:
            IntegrityCheckResult with any issues found
        """
        import time
        start_time = time.time()

        result = IntegrityCheckResult(
            check_type=IntegrityCheckType.TIMESTAMP,
            passed=True,
            total_records_checked=0,
            issues_found=0
        )

        with Session(self.engine) as session:
            stmt = select(AuditEventModel).order_by(AuditEventModel.sequence_number)
            events = session.execute(stmt).scalars().all()

            result.total_records_checked = len(events)

            previous_event = None
            for event in events:
                if previous_event is not None:
                    # Timestamp should not go backward
                    if event.timestamp < previous_event.timestamp:
                        issue = IntegrityIssue(
                            issue_type=IntegrityIssueType.TIMESTAMP_ANOMALY,
                            severity="MEDIUM",
                            description=f"Timestamp went backward at sequence {event.sequence_number}",
                            affected_record_id=event.id,
                            affected_table="audit_events",
                            details={
                                "previous_timestamp": previous_event.timestamp.isoformat(),
                                "current_timestamp": event.timestamp.isoformat(),
                                "sequence_number": event.sequence_number
                            }
                        )
                        result.issues.append(issue)
                        result.issues_found += 1
                        result.passed = False

                previous_event = event

        result.execution_time_seconds = time.time() - start_time
        return result

    def verify_data_hashes(self, limit: Optional[int] = None) -> IntegrityCheckResult:
        """
        Verify data hashes in lineage nodes.

        Args:
            limit: Maximum number of nodes to check (None = all)

        Returns:
            IntegrityCheckResult with any issues found
        """
        import time
        start_time = time.time()

        result = IntegrityCheckResult(
            check_type=IntegrityCheckType.DATA_HASH,
            passed=True,
            total_records_checked=0,
            issues_found=0
        )

        with Session(self.engine) as session:
            stmt = select(DataNodeModel).where(DataNodeModel.data_hash.isnot(None))
            if limit:
                stmt = stmt.limit(limit)

            nodes = session.execute(stmt).scalars().all()
            result.total_records_checked = len(nodes)

            for node in nodes:
                if node.data_value is not None and node.data_hash is not None:
                    # Recompute hash
                    data_str = json.dumps(node.data_value, sort_keys=True, default=str)
                    computed_hash = hashlib.sha256(data_str.encode()).hexdigest()

                    if computed_hash != node.data_hash:
                        issue = IntegrityIssue(
                            issue_type=IntegrityIssueType.DATA_MODIFIED,
                            severity="CRITICAL",
                            description=f"Data hash mismatch for node {node.name}",
                            affected_record_id=node.id,
                            affected_table="lineage_nodes",
                            details={
                                "expected_hash": computed_hash,
                                "actual_hash": node.data_hash,
                                "node_name": node.name
                            }
                        )
                        result.issues.append(issue)
                        result.issues_found += 1
                        result.passed = False

        result.execution_time_seconds = time.time() - start_time
        return result

    def verify_referential_integrity(self) -> IntegrityCheckResult:
        """
        Verify referential integrity of lineage relationships.

        Ensures all parent_id and child_id references point to existing nodes.

        Returns:
            IntegrityCheckResult with any issues found
        """
        import time
        start_time = time.time()

        result = IntegrityCheckResult(
            check_type=IntegrityCheckType.FOREIGN_KEY,
            passed=True,
            total_records_checked=0,
            issues_found=0
        )

        with Session(self.engine) as session:
            # This query finds relationships where parent doesn't exist
            from sqlalchemy import text
            orphaned_query = text("""
                SELECT r.id, r.parent_id, r.child_id
                FROM lineage_relationships r
                LEFT JOIN lineage_nodes n ON r.parent_id = n.id
                WHERE n.id IS NULL
            """)
            orphaned_parents = session.execute(orphaned_query).fetchall()

            for row in orphaned_parents:
                issue = IntegrityIssue(
                    issue_type=IntegrityIssueType.ORPHANED_RECORD,
                    severity="HIGH",
                    description=f"Lineage relationship has missing parent node",
                    affected_record_id=row[0],
                    affected_table="lineage_relationships",
                    details={
                        "relationship_id": str(row[0]),
                        "missing_parent_id": str(row[1])
                    }
                )
                result.issues.append(issue)
                result.issues_found += 1
                result.passed = False

            # Check for missing children
            orphaned_child_query = text("""
                SELECT r.id, r.parent_id, r.child_id
                FROM lineage_relationships r
                LEFT JOIN lineage_nodes n ON r.child_id = n.id
                WHERE n.id IS NULL
            """)
            orphaned_children = session.execute(orphaned_child_query).fetchall()

            for row in orphaned_children:
                issue = IntegrityIssue(
                    issue_type=IntegrityIssueType.ORPHANED_RECORD,
                    severity="HIGH",
                    description=f"Lineage relationship has missing child node",
                    affected_record_id=row[0],
                    affected_table="lineage_relationships",
                    details={
                        "relationship_id": str(row[0]),
                        "missing_child_id": str(row[2])
                    }
                )
                result.issues.append(issue)
                result.issues_found += 1
                result.passed = False

            result.total_records_checked = len(orphaned_parents) + len(orphaned_children)

        result.execution_time_seconds = time.time() - start_time
        return result

    def run_full_integrity_check(
        self,
        generated_by: str,
        include_data_hashes: bool = True,
        data_hash_limit: Optional[int] = 10000
    ) -> IntegrityReport:
        """
        Run comprehensive integrity check on all audit data.

        Args:
            generated_by: User running the check
            include_data_hashes: Whether to verify data hashes (can be slow)
            data_hash_limit: Maximum data nodes to check hashes for

        Returns:
            IntegrityReport with all findings
        """
        from uuid import uuid4

        report = IntegrityReport(
            report_id=uuid4(),
            generated_by=generated_by
        )

        # Run all checks
        checks = [
            self.verify_hash_chain(),
            self.verify_sequence_integrity(),
            self.verify_timestamp_ordering(),
            self.verify_referential_integrity(),
        ]

        if include_data_hashes:
            checks.append(self.verify_data_hashes(limit=data_hash_limit))

        report.check_results = checks
        report.total_checks = len(checks)

        # Analyze results
        for check_result in checks:
            if check_result.passed:
                report.checks_passed += 1
            else:
                report.checks_failed += 1

            # Collect critical issues
            for issue in check_result.issues:
                if issue.severity == "CRITICAL":
                    report.critical_issues.append(issue)

        # Determine overall status
        if report.checks_failed == 0:
            report.overall_status = "PASS"
        elif len(report.critical_issues) > 0:
            report.overall_status = "FAIL"
        else:
            report.overall_status = "WARNING"

        # Generate summary
        report.summary = self._generate_summary(report)

        return report

    def _generate_summary(self, report: IntegrityReport) -> str:
        """Generate human-readable summary of integrity report"""
        if report.overall_status == "PASS":
            return (
                f"All {report.total_checks} integrity checks passed successfully. "
                f"No issues detected in audit trail or data lineage."
            )
        elif report.overall_status == "FAIL":
            return (
                f"CRITICAL: {len(report.critical_issues)} critical integrity issues detected. "
                f"{report.checks_failed} of {report.total_checks} checks failed. "
                f"Immediate investigation required."
            )
        else:
            total_issues = sum(len(cr.issues) for cr in report.check_results)
            return (
                f"WARNING: {total_issues} integrity issues detected. "
                f"{report.checks_failed} of {report.total_checks} checks failed. "
                f"No critical issues found. Review recommended."
            )

    def verify_event_signature(
        self,
        event_id: UUID,
        signature: bytes,
        public_key_pem: bytes
    ) -> bool:
        """
        Verify digital signature of an audit event.

        Args:
            event_id: ID of event to verify
            signature: Digital signature bytes
            public_key_pem: Public key in PEM format

        Returns:
            True if signature is valid, False otherwise

        Raises:
            ImportError: If cryptography library not available
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            raise ImportError(
                "cryptography library required for signature verification. "
                "Install with: pip install cryptography"
            )

        with Session(self.engine) as session:
            stmt = select(AuditEventModel).where(AuditEventModel.id == event_id)
            event = session.execute(stmt).scalar_one_or_none()

            if not event:
                return False

            # Load public key
            public_key = serialization.load_pem_public_key(
                public_key_pem,
                backend=default_backend()
            )

            # Prepare message (event hash)
            message = event.event_hash.encode()

            # Verify signature
            try:
                public_key.verify(
                    signature,
                    message,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
                return True
            except InvalidSignature:
                return False
            except Exception:
                return False

    def get_integrity_score(self) -> float:
        """
        Calculate an overall integrity score (0-100).

        Returns:
            Integrity score as percentage
        """
        report = self.run_full_integrity_check(
            generated_by="system",
            include_data_hashes=False  # Fast check
        )

        if report.total_checks == 0:
            return 100.0

        # Weight critical issues more heavily
        critical_count = len(report.critical_issues)
        total_issues = sum(len(cr.issues) for cr in report.check_results)

        # Score calculation
        if critical_count > 0:
            # Any critical issue drops score significantly
            score = max(0, 50 - (critical_count * 10))
        else:
            # Deduct points for non-critical issues
            score = 100 - (total_issues * 2)

        return max(0.0, min(100.0, score))
