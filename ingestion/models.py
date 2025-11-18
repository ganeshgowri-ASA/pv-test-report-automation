"""
Data models for ingestion module using Pydantic.

Defines schemas for Visio diagrams, Gantt charts, and Smartsheet data.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ShapeType(str, Enum):
    """Visio shape types"""
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    DIAMOND = "diamond"
    PROCESS = "process"
    DECISION = "decision"
    START_END = "start_end"
    CONNECTOR = "connector"
    TEXT_BOX = "text_box"
    CUSTOM = "custom"


class ConnectorType(str, Enum):
    """Diagram connector types"""
    STRAIGHT = "straight"
    CURVED = "curved"
    RIGHT_ANGLE = "right_angle"
    DYNAMIC = "dynamic"


class DiagramShape(BaseModel):
    """Represents a shape in a Visio diagram"""
    shape_id: str = Field(..., description="Unique identifier for the shape")
    shape_type: str = Field(..., description="Type of shape (process, decision, etc.)")
    text: str = Field(default="", description="Text content within the shape")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional shape properties")
    position_x: Optional[float] = Field(None, description="X coordinate position")
    position_y: Optional[float] = Field(None, description="Y coordinate position")
    width: Optional[float] = Field(None, description="Shape width")
    height: Optional[float] = Field(None, description="Shape height")
    fill_color: Optional[str] = Field(None, description="Fill color")
    line_color: Optional[str] = Field(None, description="Line color")

    model_config = ConfigDict(use_enum_values=True)


class DiagramConnector(BaseModel):
    """Represents a connector between shapes"""
    connector_id: str = Field(..., description="Unique connector identifier")
    from_shape_id: str = Field(..., description="Source shape ID")
    to_shape_id: str = Field(..., description="Target shape ID")
    connector_type: str = Field(default="straight", description="Connector line type")
    label: Optional[str] = Field(None, description="Label on connector")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional connector properties")


class ProcessFlowStep(BaseModel):
    """Represents a step in a process flow diagram"""
    step_number: int = Field(..., description="Sequential step number")
    step_id: str = Field(..., description="Unique step identifier")
    step_type: str = Field(..., description="Type of step (process, decision, start, end)")
    description: str = Field(..., description="Step description/text")
    next_steps: List[str] = Field(default_factory=list, description="IDs of next steps")
    previous_steps: List[str] = Field(default_factory=list, description="IDs of previous steps")
    decision_options: Optional[Dict[str, str]] = Field(None, description="For decision nodes: option -> next step")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class VisioIngestionResult(BaseModel):
    """Result of Visio diagram ingestion"""
    diagram_name: str = Field(..., description="Name of the diagram")
    file_path: str = Field(..., description="Source file path")
    shapes: List[DiagramShape] = Field(default_factory=list, description="All shapes in diagram")
    connectors: List[DiagramConnector] = Field(default_factory=list, description="All connectors in diagram")
    text_content: List[str] = Field(default_factory=list, description="All text extracted from diagram")
    svg_export: Optional[str] = Field(None, description="SVG representation of diagram")
    png_export: Optional[str] = Field(None, description="PNG file path if exported")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Diagram metadata")
    file_hash: str = Field(..., description="SHA-256 hash of source file")
    ingestion_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When diagram was ingested")
    process_flow: Optional[List[ProcessFlowStep]] = Field(None, description="Structured process flow if applicable")


class TaskStatus(str, Enum):
    """Project task status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"


class GanttTask(BaseModel):
    """Represents a task from Gantt chart or MS Project"""
    task_id: int = Field(..., description="Unique task identifier")
    task_name: str = Field(..., description="Task name/description")
    start_date: date = Field(..., description="Task start date")
    end_date: date = Field(..., description="Task end date")
    duration: int = Field(..., description="Duration in days")
    dependencies: List[int] = Field(default_factory=list, description="IDs of predecessor tasks")
    resources: List[str] = Field(default_factory=list, description="Assigned resources/personnel")
    completion: float = Field(default=0.0, description="Completion percentage (0-100)")
    status: str = Field(default="not_started", description="Task status")
    priority: Optional[int] = Field(None, ge=1, le=5, description="Priority (1-5, 1=highest)")
    cost: Optional[float] = Field(None, description="Task cost")
    notes: Optional[str] = Field(None, description="Task notes")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom task fields")

    @field_validator('completion', mode='before')
    @classmethod
    def validate_completion(cls, v: float) -> float:
        """Ensure completion is between 0 and 100"""
        return max(0.0, min(100.0, float(v)))


class CriticalPathInfo(BaseModel):
    """Critical path information for project"""
    critical_tasks: List[int] = Field(..., description="Task IDs on critical path")
    total_duration: int = Field(..., description="Total project duration in days")
    slack_time: Dict[int, int] = Field(default_factory=dict, description="Slack time per task (task_id -> days)")


class TimelineData(BaseModel):
    """Project timeline data extracted from Gantt charts"""
    project_name: str = Field(..., description="Project name")
    start_date: date = Field(..., description="Project start date")
    end_date: date = Field(..., description="Project end date")
    tasks: List[GanttTask] = Field(default_factory=list, description="All project tasks")
    critical_path: Optional[CriticalPathInfo] = Field(None, description="Critical path analysis")
    milestones: List[Dict[str, Any]] = Field(default_factory=list, description="Project milestones")
    resource_allocation: Dict[str, List[int]] = Field(default_factory=dict, description="Resource -> task IDs")
    file_hash: str = Field(..., description="SHA-256 hash of source file")
    ingestion_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When data was ingested")


class SmartsheetColumn(BaseModel):
    """Smartsheet column definition"""
    column_id: int = Field(..., description="Column ID")
    title: str = Field(..., description="Column title")
    column_type: str = Field(..., description="Column type (TEXT_NUMBER, DATE, PICKLIST, etc.)")
    options: Optional[List[str]] = Field(None, description="Options for PICKLIST columns")
    is_primary: bool = Field(default=False, description="Is primary column")


class SmartsheetRow(BaseModel):
    """Smartsheet row data"""
    row_id: int = Field(..., description="Row ID")
    row_number: int = Field(..., description="Row number")
    cells: Dict[str, Any] = Field(..., description="Column title -> cell value mapping")
    created_at: Optional[datetime] = Field(None, description="Row creation timestamp")
    modified_at: Optional[datetime] = Field(None, description="Last modification timestamp")
    created_by: Optional[str] = Field(None, description="Creator email")
    modified_by: Optional[str] = Field(None, description="Last modifier email")


class SmartsheetComment(BaseModel):
    """Smartsheet comment/discussion"""
    comment_id: int = Field(..., description="Comment ID")
    text: str = Field(..., description="Comment text")
    created_by: str = Field(..., description="Comment author email")
    created_at: datetime = Field(..., description="Comment timestamp")
    row_id: Optional[int] = Field(None, description="Associated row ID if applicable")


class SmartsheetAttachment(BaseModel):
    """Smartsheet attachment metadata"""
    attachment_id: int = Field(..., description="Attachment ID")
    name: str = Field(..., description="File name")
    url: Optional[str] = Field(None, description="Download URL")
    mime_type: str = Field(..., description="MIME type")
    size_bytes: int = Field(..., description="File size in bytes")
    created_at: datetime = Field(..., description="Upload timestamp")
    created_by: str = Field(..., description="Uploader email")


class SmartsheetData(BaseModel):
    """Complete Smartsheet data extraction"""
    sheet_id: int = Field(..., description="Sheet ID")
    sheet_name: str = Field(..., description="Sheet name")
    columns: List[SmartsheetColumn] = Field(default_factory=list, description="Column definitions")
    rows: List[SmartsheetRow] = Field(default_factory=list, description="Row data")
    comments: List[SmartsheetComment] = Field(default_factory=list, description="Comments/discussions")
    attachments: List[SmartsheetAttachment] = Field(default_factory=list, description="Attachments")
    modified_date: datetime = Field(..., description="Last modification date")
    created_date: Optional[datetime] = Field(None, description="Sheet creation date")
    owner: Optional[str] = Field(None, description="Sheet owner email")
    permalink: Optional[str] = Field(None, description="Permanent link to sheet")
    ingestion_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When data was ingested")

    def to_dict_rows(self) -> List[Dict[str, Any]]:
        """Convert rows to list of dictionaries"""
        return [row.cells for row in self.rows]

    def get_column_values(self, column_title: str) -> List[Any]:
        """Extract all values from a specific column"""
        return [row.cells.get(column_title) for row in self.rows if column_title in row.cells]


class IngestionException(Exception):
    """Base exception for ingestion errors"""
    pass


class VisioParsingError(IngestionException):
    """Error parsing Visio file"""
    pass


class GanttParsingError(IngestionException):
    """Error parsing Gantt/MS Project file"""
    pass


class SmartsheetAPIError(IngestionException):
    """Error communicating with Smartsheet API"""
    pass


class DiagramExtractionError(IngestionException):
    """Error extracting diagram metadata"""
    pass
