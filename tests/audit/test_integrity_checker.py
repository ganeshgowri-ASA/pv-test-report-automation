"""
Tests for IntegrityChecker.
"""
import pytest
from datetime import datetime, timezone, timedelta

from src.audit.trail_logger import AuditEvent, AuditEventType
from src.audit.lineage_tracker import DataNode, DataNodeType
from src.audit.integrity_checker import (
    IntegrityChecker,
    IntegrityCheckType,
    IntegrityIssueType,
)


class TestIntegrityChecker:
    """Test suite for IntegrityChecker"""

    def test_verify_hash_chain_valid(self, audit_logger, integrity_checker):
        """Test hash chain verification with valid chain."""
        # Create several events
        for i in range(5):
            event = AuditEvent(
                event_type=AuditEventType.CREATE,
                entity_type="Report",
                entity_id=f"RPT-{i:03d}",
                user_id="user123",
                user_name="John Doe",
                action=f"Action {i}"
            )
            audit_logger.log(event)

        # Verify hash chain
        result = integrity_checker.verify_hash_chain()

        assert result.passed is True
        assert result.total_records_checked == 5
        assert result.issues_found == 0
        assert len(result.issues) == 0

    def test_verify_sequence_integrity_valid(self, audit_logger, integrity_checker):
        """Test sequence integrity with valid sequences."""
        # Create events
        for i in range(10):
            event = AuditEvent(
                event_type=AuditEventType.CREATE,
                entity_type="Report",
                entity_id=f"RPT-{i:03d}",
                user_id="user123",
                user_name="John Doe",
                action=f"Action {i}"
            )
            audit_logger.log(event)

        # Verify sequence
        result = integrity_checker.verify_sequence_integrity()

        assert result.passed is True
        assert result.total_records_checked == 10
        assert result.issues_found == 0

    def test_verify_timestamp_ordering_valid(self, audit_logger, integrity_checker):
        """Test timestamp ordering with valid timestamps."""
        base_time = datetime.now(timezone.utc)

        for i in range(5):
            event = AuditEvent(
                event_type=AuditEventType.CREATE,
                entity_type="Report",
                entity_id=f"RPT-{i:03d}",
                user_id="user123",
                user_name="John Doe",
                action=f"Action {i}",
                timestamp=base_time + timedelta(seconds=i)
            )
            audit_logger.log(event)

        # Verify timestamp ordering
        result = integrity_checker.verify_timestamp_ordering()

        assert result.passed is True
        assert result.total_records_checked == 5
        assert result.issues_found == 0

    def test_verify_data_hashes(self, lineage_tracker, integrity_checker):
        """Test data hash verification."""
        # Create nodes with data
        for i in range(5):
            node = DataNode(
                node_type=DataNodeType.PARSED_DATA,
                name=f"Node {i}",
                created_by="user123",
                data_value={"value": i * 10}
            )
            lineage_tracker.create_node(node)

        # Verify data hashes
        result = integrity_checker.verify_data_hashes()

        assert result.passed is True
        assert result.total_records_checked == 5
        assert result.issues_found == 0

    def test_full_integrity_check_pass(self, audit_logger, lineage_tracker, integrity_checker):
        """Test full integrity check with passing results."""
        # Create audit events
        for i in range(5):
            event = AuditEvent(
                event_type=AuditEventType.CREATE,
                entity_type="Report",
                entity_id=f"RPT-{i:03d}",
                user_id="user123",
                user_name="John Doe",
                action=f"Action {i}"
            )
            audit_logger.log(event)

        # Create lineage nodes
        for i in range(3):
            node = DataNode(
                node_type=DataNodeType.PARSED_DATA,
                name=f"Node {i}",
                created_by="user123",
                data_value={"value": i}
            )
            lineage_tracker.create_node(node)

        # Run full check
        report = integrity_checker.run_full_integrity_check(
            generated_by="admin@example.com",
            include_data_hashes=True
        )

        assert report.overall_status == "PASS"
        assert report.total_checks >= 4
        assert report.checks_passed == report.total_checks
        assert report.checks_failed == 0
        assert len(report.critical_issues) == 0

    def test_integrity_score_perfect(self, audit_logger, integrity_checker):
        """Test integrity score with perfect audit trail."""
        # Create valid events
        for i in range(10):
            event = AuditEvent(
                event_type=AuditEventType.CREATE,
                entity_type="Report",
                entity_id=f"RPT-{i:03d}",
                user_id="user123",
                user_name="John Doe",
                action=f"Action {i}"
            )
            audit_logger.log(event)

        # Get integrity score
        score = integrity_checker.get_integrity_score()

        assert score == 100.0

    def test_verify_referential_integrity_valid(self, lineage_tracker, integrity_checker):
        """Test referential integrity with valid relationships."""
        # Create nodes
        parent = DataNode(
            node_type=DataNodeType.RAW_EQUIPMENT_OUTPUT,
            name="Parent",
            created_by="user123"
        )
        parent_id = lineage_tracker.create_node(parent)

        child = DataNode(
            node_type=DataNodeType.PARSED_DATA,
            name="Child",
            created_by="user123"
        )
        child_id = lineage_tracker.create_node(child)

        # Create relationship
        from src.audit.lineage_tracker import RelationshipType
        lineage_tracker.create_relationship(
            parent_id=parent_id,
            child_id=child_id,
            relationship_type=RelationshipType.DERIVED_FROM,
            created_by="user123"
        )

        # Verify referential integrity
        result = integrity_checker.verify_referential_integrity()

        # Should pass (no orphaned records)
        assert result.passed is True

    def test_check_execution_time(self, audit_logger, integrity_checker):
        """Test that checks record execution time."""
        # Create some events
        for i in range(5):
            event = AuditEvent(
                event_type=AuditEventType.CREATE,
                entity_type="Report",
                entity_id=f"RPT-{i:03d}",
                user_id="user123",
                user_name="John Doe",
                action=f"Action {i}"
            )
            audit_logger.log(event)

        # Run check
        result = integrity_checker.verify_hash_chain()

        assert result.execution_time_seconds >= 0
        assert result.execution_time_seconds < 60  # Should be fast

    def test_integrity_report_structure(self, audit_logger, integrity_checker):
        """Test integrity report structure."""
        # Create some events
        for i in range(3):
            event = AuditEvent(
                event_type=AuditEventType.CREATE,
                entity_type="Report",
                entity_id=f"RPT-{i:03d}",
                user_id="user123",
                user_name="John Doe",
                action=f"Action {i}"
            )
            audit_logger.log(event)

        # Run full check
        report = integrity_checker.run_full_integrity_check(
            generated_by="admin@example.com"
        )

        # Verify report structure
        assert report.report_id is not None
        assert report.generated_at is not None
        assert report.generated_by == "admin@example.com"
        assert report.overall_status in ["PASS", "FAIL", "WARNING"]
        assert report.total_checks > 0
        assert isinstance(report.check_results, list)
        assert isinstance(report.critical_issues, list)
        assert isinstance(report.summary, str)
        assert len(report.summary) > 0
