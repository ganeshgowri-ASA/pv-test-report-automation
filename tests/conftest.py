"""
Pytest configuration and fixtures for PV test report automation tests.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import pytest

from src.core.models import (
    DiagramShape,
    DiagramShapeType,
    GanttIngestionResult,
    IngestionStatus,
    ProjectTask,
    SmartsheetIngestionResult,
    TaskResource,
    TaskStatus,
    VisioIngestionResult,
    VisioPage,
)


@pytest.fixture
def sample_diagram_shape() -> DiagramShape:
    """Fixture providing a sample DiagramShape."""
    return DiagramShape(
        shape_id="shape_001",
        name="Test Step 1",
        shape_type=DiagramShapeType.RECTANGLE,
        text="Initialize Equipment",
        x=100.0,
        y=200.0,
        width=150.0,
        height=75.0,
        layer="Main Flow",
        connected_to=["shape_002"],
        properties={"step_number": "1"},
        style_info={"fill_color": "#0000FF"}
    )


@pytest.fixture
def sample_visio_page(sample_diagram_shape: DiagramShape) -> VisioPage:
    """Fixture providing a sample VisioPage."""
    return VisioPage(
        page_id="page_001",
        page_name="Test Procedure",
        shapes=[sample_diagram_shape],
        page_width=11.0,
        page_height=8.5
    )


@pytest.fixture
def sample_visio_result(sample_visio_page: VisioPage) -> VisioIngestionResult:
    """Fixture providing a sample VisioIngestionResult."""
    return VisioIngestionResult(
        diagram_name="Test Flow Diagram",
        file_path="/path/to/diagram.vsdx",
        pages=[sample_visio_page],
        shapes=sample_visio_page.shapes,
        svg_export="<svg>Sample SVG</svg>",
        metadata={
            "author": "Test Engineer",
            "created_date": "2025-01-01"
        },
        status=IngestionStatus.SUCCESS
    )


@pytest.fixture
def sample_task_resource() -> TaskResource:
    """Fixture providing a sample TaskResource."""
    return TaskResource(
        resource_id="resource_001",
        name="Test Engineer",
        allocation_percent=100.0,
        cost_per_hour=75.0
    )


@pytest.fixture
def sample_project_task(sample_task_resource: TaskResource) -> ProjectTask:
    """Fixture providing a sample ProjectTask."""
    return ProjectTask(
        task_id="task_001",
        name="Equipment Setup",
        description="Set up test equipment",
        start_date=datetime(2025, 1, 15),
        end_date=datetime(2025, 1, 20),
        duration_days=5.0,
        percent_complete=50.0,
        status=TaskStatus.IN_PROGRESS,
        priority=1,
        dependencies=["task_000"],
        resources=[sample_task_resource],
        milestone=False
    )


@pytest.fixture
def sample_gantt_result(sample_project_task: ProjectTask) -> GanttIngestionResult:
    """Fixture providing a sample GanttIngestionResult."""
    return GanttIngestionResult(
        project_name="PV Testing Project",
        file_path="/path/to/project.mpp",
        project_start=datetime(2025, 1, 1),
        project_end=datetime(2025, 12, 31),
        tasks=[sample_project_task],
        metadata={
            "manager": "Project Manager",
            "company": "PV Test Lab"
        },
        status=IngestionStatus.SUCCESS,
        total_tasks=1,
        completed_tasks=0,
        percent_complete=50.0
    )


@pytest.fixture
def sample_smartsheet_result() -> SmartsheetIngestionResult:
    """Fixture providing a sample SmartsheetIngestionResult."""
    from src.core.models import SmartsheetColumn, SmartsheetRow, SmartsheetCell

    columns = [
        SmartsheetColumn(
            column_id="col_001",
            title="Test ID",
            column_type="TEXT_NUMBER",
            primary=True
        ),
        SmartsheetColumn(
            column_id="col_002",
            title="Status",
            column_type="DROPDOWN",
            options=["Pass", "Fail", "Pending"]
        )
    ]

    cells = [
        SmartsheetCell(column_id="col_001", value="TEST-001"),
        SmartsheetCell(column_id="col_002", value="Pass")
    ]

    rows = [
        SmartsheetRow(
            row_id="row_001",
            row_number=1,
            cells=cells
        )
    ]

    return SmartsheetIngestionResult(
        sheet_name="Test Results",
        sheet_id="12345",
        columns=columns,
        rows=rows,
        metadata={"owner": "Test Manager"},
        status=IngestionStatus.SUCCESS,
        total_rows=1,
        total_columns=2
    )


@pytest.fixture
def temp_test_dir(tmp_path: Path) -> Path:
    """Fixture providing a temporary directory for tests."""
    test_dir = tmp_path / "test_data"
    test_dir.mkdir(exist_ok=True)
    return test_dir


@pytest.fixture
def mock_visio_file(temp_test_dir: Path) -> Path:
    """Fixture providing a mock Visio file path."""
    file_path = temp_test_dir / "test.vsdx"
    file_path.touch()
    return file_path


@pytest.fixture
def mock_gantt_file(temp_test_dir: Path) -> Path:
    """Fixture providing a mock Gantt file path."""
    file_path = temp_test_dir / "test.mpp"
    file_path.touch()
    return file_path


@pytest.fixture
def mock_config() -> Dict[str, Any]:
    """Fixture providing mock configuration."""
    return {
        "max_file_size_mb": 100,
        "temp_dir": "/tmp/test",
        "log_level": "DEBUG"
    }


@pytest.fixture(autouse=True)
def reset_settings():
    """Reset settings before each test."""
    from src.core.config import reload_settings
    reload_settings()
    yield
    reload_settings()
