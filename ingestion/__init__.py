"""
PV Test Report Automation - Data Ingestion Module

This module provides comprehensive data ingestion capabilities for:
- Microsoft Visio diagrams (.vsdx, .vsd)
- Gantt charts and MS Project files (.mpp, .xml)
- Smartsheet collaborative sheets

Supports extraction of test procedures, schedules, and collaborative data
for PV testing automation workflows.
"""

from ingestion.models import (
    DiagramShape,
    DiagramConnector,
    VisioIngestionResult,
    GanttTask,
    SmartsheetData,
    ProcessFlowStep,
    TimelineData,
)
from ingestion.visio_parser import VisioIngestion
from ingestion.gantt_parser import GanttIngestion
from ingestion.smartsheet_client import SmartsheetClient
from ingestion.diagram_extractor import DiagramExtractor
from ingestion.timeline_parser import TimelineParser

__version__ = "1.0.0"
__all__ = [
    "DiagramShape",
    "DiagramConnector",
    "VisioIngestionResult",
    "GanttTask",
    "SmartsheetData",
    "ProcessFlowStep",
    "TimelineData",
    "VisioIngestion",
    "GanttIngestion",
    "SmartsheetClient",
    "DiagramExtractor",
    "TimelineParser",
]
