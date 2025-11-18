"""
Integration tests for complete workflows.

Tests end-to-end test execution, review, and export workflows.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from src.models.base_models import TestSample, CalibrationRecord
from src.protocols.iec_61215_mst import IEC61215MST, DampHeatTestConfig
from src.workflows.review_workflow import ReviewWorkflow, ReviewerRole, CommentType
from src.export.batch_export import BatchExporter, BatchExportConfig


@pytest.fixture
def test_report() -> dict:
    """Create a complete test report."""
    sample = TestSample(
        sample_id="INT-TEST-001",
        module_type="INT-MODULE-400W",
        manufacturer="Integration Test Co.",
        serial_number="INT123456",
        rated_power=400.0,
        voltage_oc=48.0,
        current_sc=11.0,
        voltage_mpp=40.0,
        current_mpp=10.0,
    )

    calibration = [
        CalibrationRecord(
            equipment_id="TEST-CHAMBER",
            equipment_name="Test Chamber",
            calibration_date=datetime(2024, 1, 1),
            due_date=datetime(2025, 1, 1),
            calibration_certificate="CAL-TEST-001",
            calibrated_by="Test Lab",
            calibration_lab="NABL Lab",
            traceability="NIST",
            uncertainty={"temp": 0.5},
        )
    ]

    tester = IEC61215MST(sample, uuid4())
    config = DampHeatTestConfig(cycles=200)
    tester.run_damp_heat_test(config, calibration)

    return tester.generate_report().model_dump()


class TestCompleteWorkflow:
    """Test complete test-review-export workflow."""

    def test_test_to_review_workflow(self, test_report: dict) -> None:
        """Test complete workflow from test to review."""
        report_id = uuid4()

        # Initialize review workflow
        workflow = ReviewWorkflow(report_id)

        # Submit for review
        reviewers = [
            {"user": "technical.reviewer", "role": "technical"},
            {"user": "quality.reviewer", "role": "quality"},
        ]

        action = workflow.submit_for_review("test.engineer", reviewers)

        assert action.action_type.value == "submitted_for_review"
        assert len(workflow.assignments) == 2

        # Start review
        workflow.start_review("technical.reviewer", ReviewerRole.TECHNICAL_REVIEWER)

        # Add comments
        comment = workflow.add_comment(
            reviewer="technical.reviewer",
            reviewer_role=ReviewerRole.TECHNICAL_REVIEWER,
            comment_text="Please verify calibration date",
            comment_type=CommentType.TECHNICAL,
            severity="high",
        )

        assert len(workflow.comments) == 1
        assert comment.comment_text == "Please verify calibration date"

        # Approve
        workflow.approve("technical.reviewer", ReviewerRole.TECHNICAL_REVIEWER)
        workflow.approve("quality.reviewer", ReviewerRole.QUALITY_REVIEWER)

        assert workflow.current_status.value == "approved"

    def test_review_to_export_workflow(self, test_report: dict) -> None:
        """Test workflow from review to export."""
        # Export to multiple formats
        config = BatchExportConfig(
            formats=["pdf", "docx", "xlsx", "json"],
            output_dir="./test_exports",
        )

        exporter = BatchExporter(config)
        results = exporter.export_report(test_report, "TEST-REPORT-001")

        assert len(results) == 4
        successful = [r for r in results if r.success]
        assert len(successful) >= 3  # At least 3 formats should succeed
