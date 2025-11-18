"""
Gantt chart and MS Project file ingestion module.

Processes .mpp, .xml, .json files to extract project tasks, timelines, and dependencies.
Uses MPXJ library for parsing various project file formats.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import jpype
    import jpype.imports
    from jpype.types import *
except ImportError:
    raise ImportError(
        "JPype is required for MPXJ. Install with: pip install JPype1"
    )

from src.core.config import get_settings
from src.core.exceptions import ConfigurationError, GanttIngestionError
from src.core.models import (
    GanttIngestionResult,
    IngestionStatus,
    ProjectTask,
    TaskResource,
    TaskStatus,
)
from src.ingestion.base import FileBasedIngestionModule


class GanttIngestionModule(FileBasedIngestionModule[GanttIngestionResult]):
    """
    Ingestion module for Gantt charts and MS Project files.

    Extracts:
    - Project tasks with hierarchical structure
    - Task durations and dates (planned vs. actual)
    - Task dependencies
    - Resource assignments
    - Project metadata
    - Timeline information
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Gantt ingestion module."""
        super().__init__(config)
        self._jvm_started = False

    @property
    def supported_extensions(self) -> List[str]:
        """Supported file extensions."""
        return ['.mpp', '.xml', '.mpx', '.json', '.planner']

    def _validate_configuration(self) -> None:
        """Validate Gantt-specific configuration."""
        # No specific validation needed currently
        pass

    def _ensure_jvm_started(self) -> None:
        """Ensure JVM is started for MPXJ."""
        if not self._jvm_started and not jpype.isJVMStarted():
            try:
                jpype.startJVM()
                self._jvm_started = True
            except Exception as e:
                raise GanttIngestionError(f"Failed to start JVM for MPXJ: {str(e)}")

    def _map_task_status(self, mpxj_task: Any) -> TaskStatus:
        """
        Map MPXJ task status to TaskStatus enum.

        Args:
            mpxj_task: MPXJ task object

        Returns:
            TaskStatus enum value
        """
        try:
            percent_complete = float(mpxj_task.getPercentageComplete() or 0)

            if percent_complete == 0:
                return TaskStatus.NOT_STARTED
            elif percent_complete == 100:
                return TaskStatus.COMPLETED
            else:
                return TaskStatus.IN_PROGRESS

        except Exception:
            return TaskStatus.NOT_STARTED

    def _extract_task_resources(self, mpxj_task: Any) -> List[TaskResource]:
        """
        Extract resource assignments from an MPXJ task.

        Args:
            mpxj_task: MPXJ task object

        Returns:
            List of TaskResource objects
        """
        resources = []

        try:
            assignments = mpxj_task.getResourceAssignments()
            if not assignments:
                return resources

            for assignment in assignments:
                try:
                    resource = assignment.getResource()
                    if resource:
                        resource_id = str(resource.getID() or f"resource_{id(resource)}")
                        name = str(resource.getName() or resource_id)

                        # Get allocation percentage
                        units = assignment.getUnits()
                        allocation_percent = float(units.doubleValue() if units else 100.0)

                        # Get cost if available
                        cost = assignment.getCost()
                        cost_per_hour = float(cost.doubleValue() if cost else None) if cost else None

                        resources.append(TaskResource(
                            resource_id=resource_id,
                            name=name,
                            allocation_percent=allocation_percent,
                            cost_per_hour=cost_per_hour
                        ))
                except Exception as e:
                    # Skip problematic resources
                    continue

        except Exception:
            pass

        return resources

    def _extract_task_dependencies(self, mpxj_task: Any) -> List[str]:
        """
        Extract task dependencies.

        Args:
            mpxj_task: MPXJ task object

        Returns:
            List of predecessor task IDs
        """
        dependencies = []

        try:
            predecessors = mpxj_task.getPredecessors()
            if predecessors:
                for pred in predecessors:
                    try:
                        pred_task = pred.getSourceTask()
                        if pred_task:
                            task_id = str(pred_task.getID())
                            dependencies.append(task_id)
                    except Exception:
                        continue

        except Exception:
            pass

        return dependencies

    def _convert_java_date(self, java_date: Any) -> Optional[datetime]:
        """
        Convert Java date to Python datetime.

        Args:
            java_date: Java date object

        Returns:
            Python datetime or None
        """
        if java_date is None:
            return None

        try:
            # Get timestamp in milliseconds
            timestamp_ms = java_date.getTime()
            # Convert to seconds
            timestamp_s = timestamp_ms / 1000.0
            return datetime.fromtimestamp(timestamp_s)
        except Exception:
            return None

    def _process_task(self, mpxj_task: Any) -> ProjectTask:
        """
        Process a single MPXJ task into ProjectTask model.

        Args:
            mpxj_task: MPXJ task object

        Returns:
            ProjectTask object
        """
        # Extract basic task information
        task_id = str(mpxj_task.getID() or f"task_{id(mpxj_task)}")
        name = str(mpxj_task.getName() or task_id)
        description = str(mpxj_task.getNotes() or "") or None

        # Extract dates
        start_date = self._convert_java_date(mpxj_task.getStart())
        end_date = self._convert_java_date(mpxj_task.getFinish())
        actual_start = self._convert_java_date(mpxj_task.getActualStart())
        actual_end = self._convert_java_date(mpxj_task.getActualFinish())

        # Default dates if not available
        if not start_date:
            start_date = datetime.now()
        if not end_date:
            end_date = start_date

        # Extract duration
        duration = mpxj_task.getDuration()
        duration_days = float(duration.getDuration() if duration else 0.0)

        # Get completion percentage
        percent_complete = float(mpxj_task.getPercentageComplete() or 0.0)

        # Map status
        status = self._map_task_status(mpxj_task)

        # Get priority
        priority_obj = mpxj_task.getPriority()
        priority = int(priority_obj.getValue() if priority_obj else None) if priority_obj else None

        # Get parent task
        parent_task = mpxj_task.getParentTask()
        parent_task_id = str(parent_task.getID()) if parent_task else None

        # Extract dependencies
        dependencies = self._extract_task_dependencies(mpxj_task)

        # Extract resources
        resources = self._extract_task_resources(mpxj_task)

        # Check if milestone
        milestone = bool(mpxj_task.getMilestone())

        # Extract custom fields
        custom_fields = {}
        try:
            # Try to get custom field values
            for i in range(1, 11):  # Text1 through Text10
                field_name = f"Text{i}"
                try:
                    field_value = mpxj_task.getText(i)
                    if field_value:
                        custom_fields[field_name] = str(field_value)
                except Exception:
                    continue
        except Exception:
            pass

        return ProjectTask(
            task_id=task_id,
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            actual_start=actual_start,
            actual_end=actual_end,
            duration_days=duration_days,
            percent_complete=percent_complete,
            status=status,
            priority=priority,
            parent_task_id=parent_task_id,
            dependencies=dependencies,
            resources=resources,
            milestone=milestone,
            custom_fields=custom_fields
        )

    def _process_project_file(self, project_file: Any, file_path: Path) -> GanttIngestionResult:
        """
        Process an MPXJ ProjectFile object.

        Args:
            project_file: MPXJ ProjectFile object
            file_path: Path to source file

        Returns:
            GanttIngestionResult
        """
        errors = []
        tasks = []

        # Extract project-level information
        project_name = str(project_file.getProjectProperties().getProjectTitle() or file_path.stem)

        # Extract project dates
        project_start = self._convert_java_date(project_file.getProjectProperties().getStartDate())
        project_end = self._convert_java_date(project_file.getProjectProperties().getFinishDate())

        if not project_start:
            project_start = datetime.now()
        if not project_end:
            project_end = project_start

        # Extract metadata
        metadata = {}
        try:
            props = project_file.getProjectProperties()
            metadata['manager'] = str(props.getManager() or "")
            metadata['company'] = str(props.getCompany() or "")
            metadata['author'] = str(props.getAuthor() or "")
            metadata['subject'] = str(props.getSubject() or "")
        except Exception as e:
            errors.append(f"Failed to extract metadata: {str(e)}")

        # Process all tasks
        try:
            all_tasks = project_file.getTasks()
            for mpxj_task in all_tasks:
                if mpxj_task and mpxj_task.getID():  # Skip null and summary tasks without IDs
                    try:
                        task = self._process_task(mpxj_task)
                        tasks.append(task)
                    except Exception as e:
                        errors.append(f"Failed to process task {mpxj_task.getID()}: {str(e)}")
        except Exception as e:
            errors.append(f"Failed to extract tasks: {str(e)}")

        # Calculate statistics
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task.status == TaskStatus.COMPLETED)
        percent_complete = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0

        # Determine status
        if errors and not tasks:
            status = IngestionStatus.FAILED
        elif errors:
            status = IngestionStatus.PARTIAL
        else:
            status = IngestionStatus.SUCCESS

        return GanttIngestionResult(
            project_name=project_name,
            file_path=str(file_path),
            project_start=project_start,
            project_end=project_end,
            tasks=tasks,
            metadata=metadata,
            ingestion_timestamp=datetime.now(),
            status=status,
            errors=errors,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            percent_complete=round(percent_complete, 2)
        )

    def extract_metadata(self, source: Path) -> Dict[str, Any]:
        """
        Extract metadata from project file.

        Args:
            source: Path to project file

        Returns:
            Dictionary of metadata
        """
        try:
            self._ensure_jvm_started()

            from net.sf.mpxj.reader import UniversalProjectReader

            reader = UniversalProjectReader()
            project_file = reader.read(str(source))

            metadata = {}
            props = project_file.getProjectProperties()

            metadata['project_title'] = str(props.getProjectTitle() or "")
            metadata['manager'] = str(props.getManager() or "")
            metadata['company'] = str(props.getCompany() or "")
            metadata['author'] = str(props.getAuthor() or "")
            metadata['file_name'] = source.name
            metadata['file_size'] = source.stat().st_size
            metadata['task_count'] = len(project_file.getTasks())

            return metadata

        except Exception as e:
            raise GanttIngestionError(f"Failed to extract metadata: {str(e)}")

    def ingest(self, source: Path, **kwargs: Any) -> GanttIngestionResult:
        """
        Ingest data from Gantt/MS Project file.

        Args:
            source: Path to project file
            **kwargs: Additional arguments

        Returns:
            GanttIngestionResult with extracted data
        """
        try:
            self._ensure_jvm_started()

            # Import MPXJ classes
            from net.sf.mpxj.reader import UniversalProjectReader

            # Create reader and read project file
            reader = UniversalProjectReader()
            project_file = reader.read(str(source))

            # Process the project file
            result = self._process_project_file(project_file, source)

            return result

        except Exception as e:
            raise GanttIngestionError(f"Failed to ingest Gantt file: {str(e)}")

    def __del__(self) -> None:
        """Cleanup: shutdown JVM if started."""
        if self._jvm_started and jpype.isJVMStarted():
            try:
                jpype.shutdownJVM()
            except Exception:
                pass
