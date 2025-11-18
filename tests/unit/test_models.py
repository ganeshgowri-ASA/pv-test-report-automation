"""
Unit tests for core data models.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.core.models import (
    DiagramShape,
    DiagramShapeType,
    GanttIngestionResult,
    IngestionStatus,
    ProjectTask,
    SmartsheetColumn,
    SmartsheetIngestionResult,
    TaskStatus,
    VisioIngestionResult,
)


class TestDiagramShape:
    """Tests for DiagramShape model."""

    def test_create_diagram_shape(self, sample_diagram_shape):
        """Test creating a DiagramShape."""
        assert sample_diagram_shape.shape_id == "shape_001"
        assert sample_diagram_shape.name == "Test Step 1"
        assert sample_diagram_shape.shape_type == DiagramShapeType.RECTANGLE
        assert sample_diagram_shape.x == 100.0
        assert sample_diagram_shape.y == 200.0

    def test_diagram_shape_connections(self, sample_diagram_shape):
        """Test diagram shape connections."""
        assert len(sample_diagram_shape.connected_to) == 1
        assert "shape_002" in sample_diagram_shape.connected_to

    def test_diagram_shape_properties(self, sample_diagram_shape):
        """Test diagram shape custom properties."""
        assert "step_number" in sample_diagram_shape.properties
        assert sample_diagram_shape.properties["step_number"] == "1"


class TestVisioIngestionResult:
    """Tests for VisioIngestionResult model."""

    def test_create_visio_result(self, sample_visio_result):
        """Test creating a VisioIngestionResult."""
        assert sample_visio_result.diagram_name == "Test Flow Diagram"
        assert sample_visio_result.status == IngestionStatus.SUCCESS
        assert len(sample_visio_result.shapes) > 0

    def test_visio_result_metadata(self, sample_visio_result):
        """Test VisioIngestionResult metadata."""
        assert "author" in sample_visio_result.metadata
        assert sample_visio_result.metadata["author"] == "Test Engineer"

    def test_visio_result_svg_export(self, sample_visio_result):
        """Test SVG export field."""
        assert sample_visio_result.svg_export is not None
        assert "svg" in sample_visio_result.svg_export.lower()


class TestProjectTask:
    """Tests for ProjectTask model."""

    def test_create_project_task(self, sample_project_task):
        """Test creating a ProjectTask."""
        assert sample_project_task.task_id == "task_001"
        assert sample_project_task.name == "Equipment Setup"
        assert sample_project_task.status == TaskStatus.IN_PROGRESS
        assert sample_project_task.duration_days == 5.0

    def test_task_date_validation(self):
        """Test task date relationships."""
        task = ProjectTask(
            task_id="task_test",
            name="Test Task",
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 10),
            duration_days=9.0,
            percent_complete=0.0
        )
        assert task.start_date < task.end_date

    def test_task_percent_complete_bounds(self):
        """Test percent_complete validation."""
        # Valid percentage
        task = ProjectTask(
            task_id="task_test",
            name="Test Task",
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 10),
            duration_days=9.0,
            percent_complete=50.0
        )
        assert 0 <= task.percent_complete <= 100

        # Invalid percentage should be caught by Pydantic
        with pytest.raises(ValidationError):
            ProjectTask(
                task_id="task_test",
                name="Test Task",
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 1, 10),
                duration_days=9.0,
                percent_complete=150.0  # Invalid
            )

    def test_task_dependencies(self, sample_project_task):
        """Test task dependencies."""
        assert len(sample_project_task.dependencies) == 1
        assert "task_000" in sample_project_task.dependencies

    def test_task_resources(self, sample_project_task):
        """Test task resource assignments."""
        assert len(sample_project_task.resources) == 1
        resource = sample_project_task.resources[0]
        assert resource.name == "Test Engineer"
        assert resource.allocation_percent == 100.0


class TestGanttIngestionResult:
    """Tests for GanttIngestionResult model."""

    def test_create_gantt_result(self, sample_gantt_result):
        """Test creating a GanttIngestionResult."""
        assert sample_gantt_result.project_name == "PV Testing Project"
        assert sample_gantt_result.status == IngestionStatus.SUCCESS
        assert sample_gantt_result.total_tasks == 1

    def test_gantt_result_calculations(self, sample_gantt_result):
        """Test calculated fields in GanttIngestionResult."""
        assert sample_gantt_result.percent_complete == 50.0
        assert sample_gantt_result.completed_tasks == 0

    def test_gantt_result_dates(self, sample_gantt_result):
        """Test project date range."""
        assert sample_gantt_result.project_start < sample_gantt_result.project_end


class TestSmartsheetModels:
    """Tests for Smartsheet models."""

    def test_smartsheet_column(self):
        """Test SmartsheetColumn model."""
        column = SmartsheetColumn(
            column_id="col_001",
            title="Test Column",
            column_type="TEXT_NUMBER",
            primary=True
        )
        assert column.column_id == "col_001"
        assert column.primary is True

    def test_smartsheet_column_with_options(self):
        """Test SmartsheetColumn with dropdown options."""
        column = SmartsheetColumn(
            column_id="col_002",
            title="Status",
            column_type="DROPDOWN",
            options=["Pass", "Fail", "Pending"]
        )
        assert len(column.options) == 3
        assert "Pass" in column.options

    def test_smartsheet_result(self, sample_smartsheet_result):
        """Test SmartsheetIngestionResult."""
        assert sample_smartsheet_result.sheet_name == "Test Results"
        assert sample_smartsheet_result.total_rows == 1
        assert sample_smartsheet_result.total_columns == 2
        assert sample_smartsheet_result.status == IngestionStatus.SUCCESS


class TestIngestionStatus:
    """Tests for IngestionStatus enum."""

    def test_ingestion_status_values(self):
        """Test IngestionStatus enum values."""
        assert IngestionStatus.SUCCESS.value == "success"
        assert IngestionStatus.PARTIAL.value == "partial"
        assert IngestionStatus.FAILED.value == "failed"
        assert IngestionStatus.PENDING.value == "pending"


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_task_status_values(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.NOT_STARTED.value == "not_started"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.ON_HOLD.value == "on_hold"
        assert TaskStatus.CANCELLED.value == "cancelled"
