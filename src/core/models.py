"""
Core data models for PV test report automation.

This module defines Pydantic models for ingestion results from various sources
including Visio diagrams, MS Project files, and Smartsheet data.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# Enums for common types
class DiagramShapeType(str, Enum):
    """Types of shapes in diagrams."""
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    DIAMOND = "diamond"
    ARROW = "arrow"
    CONNECTOR = "connector"
    TEXT = "text"
    CUSTOM = "custom"
    GROUP = "group"


class TaskStatus(str, Enum):
    """Task status for project timelines."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"


class IngestionStatus(str, Enum):
    """Status of ingestion operations."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    PENDING = "pending"


# Visio-specific models
class DiagramShape(BaseModel):
    """Represents a shape in a Visio diagram."""
    shape_id: str = Field(..., description="Unique identifier for the shape")
    name: str = Field(..., description="Name/label of the shape")
    shape_type: DiagramShapeType = Field(..., description="Type of shape")
    text: Optional[str] = Field(None, description="Text content within the shape")
    x: float = Field(..., description="X coordinate position")
    y: float = Field(..., description="Y coordinate position")
    width: float = Field(..., description="Width of the shape")
    height: float = Field(..., description="Height of the shape")
    layer: Optional[str] = Field(None, description="Layer the shape belongs to")
    connected_to: List[str] = Field(
        default_factory=list,
        description="IDs of shapes this shape connects to"
    )
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional custom properties"
    )
    style_info: Dict[str, str] = Field(
        default_factory=dict,
        description="Style information (color, line width, etc.)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "shape_id": "shape_001",
                "name": "Test Procedure Start",
                "shape_type": "rectangle",
                "text": "Initialize Test Equipment",
                "x": 100.0,
                "y": 200.0,
                "width": 150.0,
                "height": 75.0,
                "layer": "Procedure Flow",
                "connected_to": ["shape_002"],
                "properties": {"test_step": "1"},
                "style_info": {"fill_color": "#0000FF", "line_width": "2"}
            }
        }


class VisioPage(BaseModel):
    """Represents a single page in a Visio document."""
    page_id: str = Field(..., description="Unique page identifier")
    page_name: str = Field(..., description="Name of the page")
    shapes: List[DiagramShape] = Field(default_factory=list, description="Shapes on this page")
    background_page: Optional[str] = Field(None, description="Background page reference")
    page_width: float = Field(..., description="Page width")
    page_height: float = Field(..., description="Page height")


class VisioIngestionResult(BaseModel):
    """Result of Visio diagram ingestion."""
    diagram_name: str = Field(..., description="Name of the diagram file")
    file_path: str = Field(..., description="Path to the source file")
    pages: List[VisioPage] = Field(default_factory=list, description="Pages in the diagram")
    shapes: List[DiagramShape] = Field(
        default_factory=list,
        description="All shapes across all pages (flattened)"
    )
    svg_export: str = Field(..., description="SVG representation of the diagram")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (author, created date, etc.)"
    )
    ingestion_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the ingestion occurred"
    )
    status: IngestionStatus = Field(
        default=IngestionStatus.SUCCESS,
        description="Status of the ingestion"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Any errors encountered during ingestion"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "diagram_name": "Test Procedure Flow",
                "file_path": "/data/procedures/test_flow.vsdx",
                "shapes": [],
                "svg_export": "<svg>...</svg>",
                "metadata": {
                    "author": "Test Engineer",
                    "created_date": "2025-01-15",
                    "standard": "IEC 61215"
                },
                "status": "success"
            }
        }


# Gantt/MS Project models
class TaskResource(BaseModel):
    """Resource assigned to a task."""
    resource_id: str = Field(..., description="Unique resource identifier")
    name: str = Field(..., description="Resource name")
    allocation_percent: float = Field(
        100.0,
        ge=0,
        le=100,
        description="Percentage allocation (0-100)"
    )
    cost_per_hour: Optional[float] = Field(None, description="Cost per hour for this resource")


class ProjectTask(BaseModel):
    """Represents a task in a project timeline."""
    task_id: str = Field(..., description="Unique task identifier")
    name: str = Field(..., description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    start_date: datetime = Field(..., description="Planned start date")
    end_date: datetime = Field(..., description="Planned end date")
    actual_start: Optional[datetime] = Field(None, description="Actual start date")
    actual_end: Optional[datetime] = Field(None, description="Actual end date")
    duration_days: float = Field(..., ge=0, description="Planned duration in days")
    percent_complete: float = Field(0.0, ge=0, le=100, description="Completion percentage")
    status: TaskStatus = Field(default=TaskStatus.NOT_STARTED, description="Task status")
    priority: Optional[int] = Field(None, ge=1, le=5, description="Priority (1=highest, 5=lowest)")
    parent_task_id: Optional[str] = Field(None, description="Parent task for hierarchical tasks")
    dependencies: List[str] = Field(
        default_factory=list,
        description="Task IDs this task depends on"
    )
    resources: List[TaskResource] = Field(
        default_factory=list,
        description="Resources assigned to this task"
    )
    milestone: bool = Field(False, description="Whether this is a milestone")
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom task fields"
    )


class GanttIngestionResult(BaseModel):
    """Result of Gantt/MS Project file ingestion."""
    project_name: str = Field(..., description="Name of the project")
    file_path: str = Field(..., description="Path to the source file")
    project_start: datetime = Field(..., description="Project start date")
    project_end: datetime = Field(..., description="Project end date")
    tasks: List[ProjectTask] = Field(default_factory=list, description="All project tasks")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Project metadata (manager, budget, etc.)"
    )
    ingestion_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the ingestion occurred"
    )
    status: IngestionStatus = Field(
        default=IngestionStatus.SUCCESS,
        description="Status of the ingestion"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Any errors encountered during ingestion"
    )
    total_tasks: int = Field(0, description="Total number of tasks")
    completed_tasks: int = Field(0, description="Number of completed tasks")
    percent_complete: float = Field(0.0, ge=0, le=100, description="Overall project completion")

    @field_validator('percent_complete', mode='before')
    @classmethod
    def calculate_percent_complete(cls, v: Any, info: Any) -> float:
        """Calculate percent complete if not provided."""
        if v == 0 and 'tasks' in info.data:
            tasks = info.data['tasks']
            if tasks:
                total_percent = sum(task.percent_complete for task in tasks)
                return round(total_percent / len(tasks), 2)
        return v


# Smartsheet models
class SmartsheetColumn(BaseModel):
    """Represents a column in a Smartsheet."""
    column_id: str = Field(..., description="Unique column identifier")
    title: str = Field(..., description="Column title")
    column_type: str = Field(..., description="Column type (TEXT_NUMBER, DATE, etc.)")
    primary: bool = Field(False, description="Whether this is the primary column")
    options: List[str] = Field(default_factory=list, description="Options for dropdown columns")


class SmartsheetCell(BaseModel):
    """Represents a cell in a Smartsheet row."""
    column_id: str = Field(..., description="Column this cell belongs to")
    value: Any = Field(None, description="Cell value")
    display_value: Optional[str] = Field(None, description="Formatted display value")


class SmartsheetRow(BaseModel):
    """Represents a row in a Smartsheet."""
    row_id: str = Field(..., description="Unique row identifier")
    row_number: int = Field(..., description="Row number in the sheet")
    cells: List[SmartsheetCell] = Field(default_factory=list, description="Cells in this row")
    parent_id: Optional[str] = Field(None, description="Parent row ID for hierarchical rows")
    created_at: Optional[datetime] = Field(None, description="When the row was created")
    modified_at: Optional[datetime] = Field(None, description="When the row was last modified")


class SmartsheetIngestionResult(BaseModel):
    """Result of Smartsheet ingestion."""
    sheet_name: str = Field(..., description="Name of the Smartsheet")
    sheet_id: str = Field(..., description="Unique sheet identifier")
    workspace_id: Optional[str] = Field(None, description="Workspace ID if applicable")
    columns: List[SmartsheetColumn] = Field(default_factory=list, description="Sheet columns")
    rows: List[SmartsheetRow] = Field(default_factory=list, description="Sheet rows")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Sheet metadata (owner, permissions, etc.)"
    )
    ingestion_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the ingestion occurred"
    )
    status: IngestionStatus = Field(
        default=IngestionStatus.SUCCESS,
        description="Status of the ingestion"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Any errors encountered during ingestion"
    )
    total_rows: int = Field(0, description="Total number of rows")
    total_columns: int = Field(0, description="Total number of columns")


# Base ingestion result for common fields
class BaseIngestionResult(BaseModel):
    """Base model for all ingestion results."""
    source_type: str = Field(..., description="Type of source (visio, gantt, smartsheet)")
    file_path: Optional[str] = Field(None, description="Path to source file if applicable")
    ingestion_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When ingestion occurred"
    )
    status: IngestionStatus = Field(
        default=IngestionStatus.SUCCESS,
        description="Status of ingestion"
    )
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
