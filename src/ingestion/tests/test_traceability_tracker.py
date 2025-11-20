"""
Unit tests for Traceability Tracker module.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from ..traceability_tracker import (
    TraceabilityTracker,
    AuditLog,
    DataLineage,
    ChangeHistory,
    ISO17025Traceability,
    ActionType,
    EntityType,
    ComplianceStandard,
)


class TestAuditLog:
    """Test AuditLog model."""

    def test_create_audit_log(self):
        """Test creating audit log."""
        log = AuditLog(
            action=ActionType.CREATE,
            entity_type=EntityType.TEST_DATA,
            entity_id="123",
            user_id="user001",
            new_value={"voc": 38.5, "isc": 8.9},
        )

        assert log.action == ActionType.CREATE
        assert log.entity_type == EntityType.TEST_DATA
        assert log.user_id == "user001"
        assert log.id is not None

    def test_audit_log_with_changes(self):
        """Test audit log with old and new values."""
        log = AuditLog(
            action=ActionType.UPDATE,
            entity_type=EntityType.TEST_DATA,
            entity_id="123",
            user_id="user001",
            old_value={"voc": 38.0},
            new_value={"voc": 38.5},
            changes={"voc": {"old": 38.0, "new": 38.5}},
        )

        assert log.changes["voc"]["old"] == 38.0
        assert log.changes["voc"]["new"] == 38.5

    def test_calculate_checksum(self):
        """Test checksum calculation."""
        log = AuditLog(
            action=ActionType.CREATE,
            entity_type=EntityType.TEST_DATA,
            entity_id="123",
            user_id="user001",
            new_value={"voc": 38.5},
        )

        checksum = log.calculate_checksum()

        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA-256

    def test_verify_checksum(self):
        """Test checksum verification."""
        log = AuditLog(
            action=ActionType.CREATE,
            entity_type=EntityType.TEST_DATA,
            entity_id="123",
            user_id="user001",
            new_value={"voc": 38.5},
        )

        # Set checksum
        log.checksum = log.calculate_checksum()

        # Verify
        assert log.verify_checksum() is True

    def test_verify_invalid_checksum(self):
        """Test invalid checksum detection."""
        log = AuditLog(
            action=ActionType.CREATE,
            entity_type=EntityType.TEST_DATA,
            entity_id="123",
            user_id="user001",
            new_value={"voc": 38.5},
        )

        log.checksum = "invalid_checksum"

        assert log.verify_checksum() is False

    def test_compliance_standards(self):
        """Test compliance standards tracking."""
        log = AuditLog(
            action=ActionType.CREATE,
            entity_type=EntityType.TEST_DATA,
            entity_id="123",
            user_id="user001",
            compliance_standards=[
                ComplianceStandard.ISO_17025,
                ComplianceStandard.IEC_61215,
            ],
        )

        assert ComplianceStandard.ISO_17025 in log.compliance_standards
        assert len(log.compliance_standards) == 2


class TestDataLineage:
    """Test DataLineage model."""

    def test_create_lineage(self):
        """Test creating data lineage."""
        lineage = DataLineage(
            entity_id="test_001",
            entity_type=EntityType.TEST_DATA,
        )

        assert lineage.entity_id == "test_001"
        assert lineage.entity_type == EntityType.TEST_DATA
        assert len(lineage.source_entities) == 0

    def test_add_source(self):
        """Test adding source entity."""
        lineage = DataLineage(
            entity_id="test_001",
            entity_type=EntityType.TEST_DATA,
        )

        lineage.add_source(
            EntityType.DOCUMENT,
            "doc_001",
            "Test Report PDF",
        )

        assert len(lineage.source_entities) == 1
        assert lineage.source_entities[0]["id"] == "doc_001"

    def test_add_derived(self):
        """Test adding derived entity."""
        lineage = DataLineage(
            entity_id="test_001",
            entity_type=EntityType.TEST_DATA,
        )

        lineage.add_derived(
            EntityType.REPORT,
            "rpt_001",
            "Final Report",
        )

        assert len(lineage.derived_entities) == 1
        assert lineage.derived_entities[0]["id"] == "rpt_001"

    def test_add_processing_step(self):
        """Test adding processing step."""
        lineage = DataLineage(
            entity_id="test_001",
            entity_type=EntityType.TEST_DATA,
        )

        lineage.add_processing_step(
            "data_extraction",
            "Extract I-V curve from PDF",
            metadata={"tool": "excel_parser"},
        )

        assert len(lineage.processing_steps) == 1
        assert lineage.processing_steps[0]["step"] == "data_extraction"


class TestChangeHistory:
    """Test ChangeHistory model."""

    def test_create_change_history(self):
        """Test creating change history."""
        history = ChangeHistory(
            entity_id="test_001",
            entity_type=EntityType.TEST_DATA,
            version=1,
            changes=[{"field": "voc", "old": 38.0, "new": 38.5}],
        )

        assert history.entity_id == "test_001"
        assert history.version == 1
        assert len(history.changes) == 1


class TestISO17025Traceability:
    """Test ISO17025Traceability model."""

    def test_create_iso17025_record(self):
        """Test creating ISO 17025 traceability record."""
        record = ISO17025Traceability(
            test_id="TEST-001",
            report_id="RPT-001",
            performed_by="John Doe",
            test_date=datetime(2025, 1, 15),
            test_procedure="TP-IEC61215",
            test_method="Flash Test",
        )

        assert record.test_id == "TEST-001"
        assert record.performed_by == "John Doe"

    def test_equipment_tracking(self):
        """Test equipment traceability."""
        record = ISO17025Traceability(
            test_id="TEST-001",
            report_id="RPT-001",
            performed_by="John Doe",
            test_date=datetime.utcnow(),
            test_procedure="TP-001",
            test_method="Flash Test",
            equipment_used=[
                {
                    "equipment_id": "SIM-001",
                    "calibration_date": "2025-01-01",
                    "certificate": "CAL-2025-001",
                }
            ],
        )

        assert len(record.equipment_used) == 1
        assert record.equipment_used[0]["equipment_id"] == "SIM-001"


class TestTraceabilityTracker:
    """Test TraceabilityTracker class."""

    def test_initialization(self):
        """Test tracker initialization."""
        tracker = TraceabilityTracker()

        assert tracker._audit_logs == []
        assert tracker._lineage_records == {}

    def test_log_action(self):
        """Test logging an action."""
        tracker = TraceabilityTracker()

        log = tracker.log_action(
            action=ActionType.CREATE,
            entity_type=EntityType.TEST_DATA,
            entity_id="test_001",
            user_id="user001",
            new_value={"voc": 38.5},
            reason="Initial data entry",
        )

        assert isinstance(log, AuditLog)
        assert len(tracker._audit_logs) == 1
        assert log.checksum is not None

    def test_log_action_with_changes(self):
        """Test logging action with changes."""
        tracker = TraceabilityTracker()

        log = tracker.log_action(
            action=ActionType.UPDATE,
            entity_type=EntityType.TEST_DATA,
            entity_id="test_001",
            user_id="user001",
            old_value={"voc": 38.0, "isc": 8.9},
            new_value={"voc": 38.5, "isc": 8.9},
            reason="Correction",
        )

        assert "voc" in log.changes
        assert log.changes["voc"]["old"] == 38.0
        assert log.changes["voc"]["new"] == 38.5

    def test_get_audit_logs(self):
        """Test retrieving audit logs."""
        tracker = TraceabilityTracker()

        # Create multiple logs
        for i in range(5):
            tracker.log_action(
                action=ActionType.CREATE,
                entity_type=EntityType.TEST_DATA,
                entity_id=f"test_{i:03d}",
                user_id="user001",
            )

        logs = tracker.get_audit_logs()

        assert len(logs) == 5

    def test_get_audit_logs_filtered(self):
        """Test filtering audit logs."""
        tracker = TraceabilityTracker()

        # Create logs for different entities
        tracker.log_action(
            ActionType.CREATE,
            EntityType.TEST_DATA,
            "test_001",
            "user001",
        )
        tracker.log_action(
            ActionType.UPDATE,
            EntityType.TEST_DATA,
            "test_001",
            "user002",
        )
        tracker.log_action(
            ActionType.CREATE,
            EntityType.REPORT,
            "rpt_001",
            "user001",
        )

        # Filter by entity_id
        logs = tracker.get_audit_logs(entity_id="test_001")
        assert len(logs) == 2

        # Filter by action
        logs = tracker.get_audit_logs(action=ActionType.CREATE)
        assert len(logs) == 2

        # Filter by user
        logs = tracker.get_audit_logs(user_id="user001")
        assert len(logs) == 2

    def test_get_audit_logs_date_range(self):
        """Test filtering audit logs by date range."""
        tracker = TraceabilityTracker()

        now = datetime.utcnow()

        # Create log with specific timestamp
        log = AuditLog(
            action=ActionType.CREATE,
            entity_type=EntityType.TEST_DATA,
            entity_id="test_001",
            user_id="user001",
            timestamp=now - timedelta(days=5),
        )
        log.checksum = log.calculate_checksum()
        tracker._audit_logs.append(log)

        # Create recent log
        tracker.log_action(
            ActionType.CREATE,
            EntityType.TEST_DATA,
            "test_002",
            "user001",
        )

        # Filter by date
        logs = tracker.get_audit_logs(
            start_date=now - timedelta(days=1)
        )

        assert len(logs) == 1

    def test_create_lineage(self):
        """Test creating data lineage."""
        tracker = TraceabilityTracker()

        lineage = tracker.create_lineage(
            entity_id="test_001",
            entity_type=EntityType.TEST_DATA,
            metadata={"source": "excel_import"},
        )

        assert isinstance(lineage, DataLineage)
        assert lineage.entity_id == "test_001"
        assert tracker.get_lineage("test_001") is not None

    def test_trace_lineage_upstream(self):
        """Test tracing lineage upstream."""
        tracker = TraceabilityTracker()

        # Create lineage chain
        doc_lineage = tracker.create_lineage("doc_001", EntityType.DOCUMENT)

        excel_lineage = tracker.create_lineage("excel_001", EntityType.BLOB)
        excel_lineage.add_source(EntityType.DOCUMENT, "doc_001", "Source PDF")

        test_lineage = tracker.create_lineage("test_001", EntityType.TEST_DATA)
        test_lineage.add_source(EntityType.BLOB, "excel_001", "Excel Data")

        # Trace upstream
        upstream = tracker.trace_lineage_upstream("test_001")

        assert len(upstream) >= 2  # Should include excel and doc

    def test_trace_lineage_downstream(self):
        """Test tracing lineage downstream."""
        tracker = TraceabilityTracker()

        # Create lineage chain
        test_lineage = tracker.create_lineage("test_001", EntityType.TEST_DATA)

        report_lineage = tracker.create_lineage("rpt_001", EntityType.REPORT)
        report_lineage.add_source(EntityType.TEST_DATA, "test_001", "Test Data")

        # Update test lineage with derived entity
        test_lineage.add_derived(EntityType.REPORT, "rpt_001", "Final Report")

        # Trace downstream
        downstream = tracker.trace_lineage_downstream("test_001")

        assert len(downstream) >= 1

    def test_record_change(self):
        """Test recording changes."""
        tracker = TraceabilityTracker()

        change = tracker.record_change(
            entity_id="test_001",
            entity_type=EntityType.TEST_DATA,
            changes={"voc": {"old": 38.0, "new": 38.5}},
            user_id="user001",
        )

        assert isinstance(change, ChangeHistory)
        assert change.version == 1

    def test_get_change_history(self):
        """Test retrieving change history."""
        tracker = TraceabilityTracker()

        # Record multiple changes
        for i in range(3):
            tracker.record_change(
                entity_id="test_001",
                entity_type=EntityType.TEST_DATA,
                changes={"voc": {"old": 38.0 + i, "new": 38.0 + i + 0.5}},
                user_id="user001",
            )

        history = tracker.get_change_history("test_001")

        assert len(history) == 3

    def test_create_iso17025_record(self):
        """Test creating ISO 17025 record."""
        tracker = TraceabilityTracker()

        record = tracker.create_iso17025_record(
            test_id="TEST-001",
            report_id="RPT-001",
            performed_by="John Doe",
            test_date=datetime(2025, 1, 15),
            test_procedure="TP-IEC61215",
            test_method="Flash Test",
            equipment_used=[{"equipment_id": "SIM-001"}],
        )

        assert isinstance(record, ISO17025Traceability)
        assert record.test_id == "TEST-001"

    def test_validate_iso17025_compliance(self):
        """Test ISO 17025 compliance validation."""
        tracker = TraceabilityTracker()

        # Create incomplete record
        record = tracker.create_iso17025_record(
            test_id="TEST-001",
            report_id="RPT-001",
            performed_by="John Doe",
            test_date=datetime.utcnow(),
            test_procedure="TP-001",
            test_method="Flash Test",
        )

        is_compliant, issues = tracker.validate_iso17025_compliance("TEST-001")

        assert is_compliant is False
        assert len(issues) > 0
        assert "Equipment information missing" in issues

    def test_validate_iso17025_compliance_complete(self):
        """Test ISO 17025 validation with complete record."""
        tracker = TraceabilityTracker()

        record = tracker.create_iso17025_record(
            test_id="TEST-001",
            report_id="RPT-001",
            performed_by="John Doe",
            reviewed_by="Jane Smith",
            approved_by="Bob Johnson",
            test_date=datetime.utcnow(),
            test_procedure="TP-001",
            test_method="Flash Test",
            equipment_used=[{"equipment_id": "SIM-001"}],
            measurement_standards=[{"standard": "NIST"}],
            measurement_uncertainty={"voc": 0.5},
            calibration_chain=[{"equipment": "SIM-001", "calibrated_by": "NIST"}],
        )

        is_compliant, issues = tracker.validate_iso17025_compliance("TEST-001")

        assert is_compliant is True
        assert len(issues) == 0

    def test_generate_audit_report(self):
        """Test generating audit report."""
        tracker = TraceabilityTracker()

        # Create logs
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        for i in range(5):
            tracker.log_action(
                ActionType.CREATE,
                EntityType.TEST_DATA,
                f"test_{i:03d}",
                "user001",
            )

        report = tracker.generate_audit_report(start_date, end_date)

        assert "total_actions" in report
        assert report["total_actions"] == 5
        assert "action_breakdown" in report
        assert "user_activity" in report

    def test_generate_lineage_report(self):
        """Test generating lineage report."""
        tracker = TraceabilityTracker()

        lineage = tracker.create_lineage("test_001", EntityType.TEST_DATA)
        lineage.add_source(EntityType.DOCUMENT, "doc_001", "Source PDF")
        lineage.add_processing_step("extraction", "Extract data from PDF")

        report = tracker.generate_lineage_report("test_001")

        assert "entity_id" in report
        assert report["entity_id"] == "test_001"
        assert "processing_steps" in report
        assert len(report["processing_steps"]) == 1

    def test_verify_audit_integrity(self):
        """Test audit log integrity verification."""
        tracker = TraceabilityTracker()

        # Create logs with valid checksums
        for i in range(3):
            tracker.log_action(
                ActionType.CREATE,
                EntityType.TEST_DATA,
                f"test_{i:03d}",
                "user001",
            )

        all_valid, invalid_logs = tracker.verify_audit_integrity()

        assert all_valid is True
        assert len(invalid_logs) == 0

    def test_verify_audit_integrity_tampered(self):
        """Test detection of tampered audit logs."""
        tracker = TraceabilityTracker()

        # Create a log
        tracker.log_action(
            ActionType.CREATE,
            EntityType.TEST_DATA,
            "test_001",
            "user001",
        )

        # Tamper with the log
        tracker._audit_logs[0].new_value = {"tampered": "data"}

        all_valid, invalid_logs = tracker.verify_audit_integrity()

        assert all_valid is False
        assert len(invalid_logs) == 1


class TestComplianceIntegration:
    """Integration tests for compliance features."""

    def test_full_compliance_workflow(self):
        """Test complete compliance tracking workflow."""
        tracker = TraceabilityTracker()

        # 1. Create lineage
        lineage = tracker.create_lineage("test_001", EntityType.TEST_DATA)
        lineage.add_source(EntityType.DOCUMENT, "doc_001", "Test Report")
        lineage.add_processing_step("data_extraction", "Extract I-V curve")

        # 2. Log action
        log = tracker.log_action(
            ActionType.CREATE,
            EntityType.TEST_DATA,
            "test_001",
            "user001",
            new_value={"voc": 38.5, "isc": 8.9},
            compliance_standards=[ComplianceStandard.ISO_17025],
        )

        # 3. Create ISO 17025 record
        iso_record = tracker.create_iso17025_record(
            test_id="test_001",
            report_id="rpt_001",
            performed_by="John Doe",
            test_date=datetime.utcnow(),
            test_procedure="TP-IEC61215",
            test_method="Flash Test",
            equipment_used=[{"equipment_id": "SIM-001"}],
            measurement_standards=[{"standard": "NIST"}],
            measurement_uncertainty={"voc": 0.5},
            calibration_chain=[{"equipment": "SIM-001"}],
            reviewed_by="Jane Smith",
            approved_by="Bob Johnson",
        )

        # 4. Validate compliance
        is_compliant, issues = tracker.validate_iso17025_compliance("test_001")

        # 5. Verify integrity
        all_valid, invalid = tracker.verify_audit_integrity()

        assert is_compliant is True
        assert all_valid is True
        assert len(tracker._audit_logs) > 0
