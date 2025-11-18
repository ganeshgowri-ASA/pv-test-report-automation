"""
Gantt chart and MS Project file parser.

Supports:
- MS Project XML format (.xml)
- MS Project MPP format (.mpp) via mpxj
- Task extraction with dependencies
- Resource assignment parsing
- Critical path calculation
"""

import hashlib
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from xml.etree import ElementTree as ET

from ingestion.models import (
    CriticalPathInfo,
    GanttParsingError,
    GanttTask,
    TimelineData,
)

logger = logging.getLogger(__name__)


class GanttIngestion:
    """
    Parse Gantt charts and MS Project files to extract timeline data.

    Supports:
    - MS Project XML format
    - MS Project MPP format (via mpxj-python)
    - Task dependencies
    - Resource assignments
    - Critical path analysis
    """

    def __init__(self, file_path: str):
        """
        Initialize Gantt parser.

        Args:
            file_path: Path to project file (.xml or .mpp)

        Raises:
            GanttParsingError: If file doesn't exist or unsupported format
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise GanttParsingError(f"File not found: {file_path}")

        self.file_suffix = self.file_path.suffix.lower()
        if self.file_suffix not in ['.xml', '.mpp']:
            raise GanttParsingError(
                f"Unsupported file format: {self.file_suffix}. "
                f"Supported formats: .xml, .mpp"
            )

        self.file_hash = self._calculate_file_hash()
        self.project_name = self.file_path.stem

    def _calculate_file_hash(self) -> str:
        """Calculate SHA-256 hash of the file"""
        sha256_hash = hashlib.sha256()
        with open(self.file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def extract_tasks(self) -> List[GanttTask]:
        """
        Extract all tasks from the project file.

        Returns:
            List of GanttTask objects

        Raises:
            GanttParsingError: If parsing fails
        """
        if self.file_suffix == '.xml':
            return self._parse_xml()
        elif self.file_suffix == '.mpp':
            return self._parse_mpp()
        else:
            raise GanttParsingError(f"Unsupported format: {self.file_suffix}")

    def extract_timeline(self) -> TimelineData:
        """
        Extract complete timeline data including tasks, milestones, and critical path.

        Returns:
            TimelineData object with complete project timeline

        Raises:
            GanttParsingError: If parsing fails
        """
        tasks = self.extract_tasks()

        if not tasks:
            raise GanttParsingError("No tasks found in project file")

        # Calculate project bounds
        start_date = min(task.start_date for task in tasks)
        end_date = max(task.end_date for task in tasks)

        # Extract milestones (tasks with 0 duration)
        milestones = []
        for task in tasks:
            if task.duration == 0:
                milestones.append({
                    'task_id': task.task_id,
                    'name': task.task_name,
                    'date': task.start_date,
                })

        # Build resource allocation map
        resource_allocation: Dict[str, List[int]] = {}
        for task in tasks:
            for resource in task.resources:
                if resource not in resource_allocation:
                    resource_allocation[resource] = []
                resource_allocation[resource].append(task.task_id)

        # Calculate critical path
        critical_path = self._calculate_critical_path(tasks)

        return TimelineData(
            project_name=self.project_name,
            start_date=start_date,
            end_date=end_date,
            tasks=tasks,
            critical_path=critical_path,
            milestones=milestones,
            resource_allocation=resource_allocation,
            file_hash=self.file_hash,
        )

    def _parse_xml(self) -> List[GanttTask]:
        """Parse MS Project XML format"""
        try:
            tree = ET.parse(self.file_path)
            root = tree.getroot()

            # MS Project XML namespace
            ns = {'ms': 'http://schemas.microsoft.com/project'}

            tasks = []
            for task_elem in root.findall('.//ms:Task', ns):
                task = self._parse_xml_task(task_elem, ns)
                if task:
                    tasks.append(task)

            return tasks

        except ET.ParseError as e:
            raise GanttParsingError(f"XML parsing error: {str(e)}")
        except Exception as e:
            raise GanttParsingError(f"Error parsing XML file: {str(e)}")

    def _parse_xml_task(self, task_elem: ET.Element, ns: Dict[str, str]) -> Optional[GanttTask]:
        """Parse a single task from XML"""
        try:
            task_id_elem = task_elem.find('ms:UID', ns)
            if task_id_elem is None or not task_id_elem.text:
                return None

            task_id = int(task_id_elem.text)

            # Extract basic fields
            name = self._get_xml_text(task_elem, 'ms:Name', ns, 'Unnamed Task')
            start = self._get_xml_date(task_elem, 'ms:Start', ns)
            finish = self._get_xml_date(task_elem, 'ms:Finish', ns)

            if not start or not finish:
                return None

            # Calculate duration
            duration = (finish - start).days

            # Extract dependencies
            dependencies = []
            pred_links = task_elem.findall('.//ms:PredecessorLink', ns)
            for pred_link in pred_links:
                pred_uid = self._get_xml_text(pred_link, 'ms:PredecessorUID', ns)
                if pred_uid:
                    try:
                        dependencies.append(int(pred_uid))
                    except ValueError:
                        pass

            # Extract resources
            resources = []
            assignments = task_elem.findall('.//ms:Assignment', ns)
            for assignment in assignments:
                resource_uid = self._get_xml_text(assignment, 'ms:ResourceUID', ns)
                if resource_uid:
                    resources.append(f"Resource_{resource_uid}")

            # Extract completion percentage
            percent_complete = float(self._get_xml_text(task_elem, 'ms:PercentComplete', ns, '0'))

            # Extract priority
            priority_text = self._get_xml_text(task_elem, 'ms:Priority', ns, '500')
            priority = self._map_priority(int(priority_text))

            # Extract cost
            cost_text = self._get_xml_text(task_elem, 'ms:Cost', ns)
            cost = float(cost_text) if cost_text else None

            # Extract notes
            notes = self._get_xml_text(task_elem, 'ms:Notes', ns)

            # Determine status
            status = self._determine_status(percent_complete, start, finish)

            return GanttTask(
                task_id=task_id,
                task_name=name,
                start_date=start,
                end_date=finish,
                duration=duration,
                dependencies=dependencies,
                resources=resources,
                completion=percent_complete,
                status=status,
                priority=priority,
                cost=cost,
                notes=notes,
            )

        except Exception as e:
            logger.warning(f"Error parsing task: {str(e)}")
            return None

    def _parse_mpp(self) -> List[GanttTask]:
        """
        Parse MS Project MPP format using mpxj library.

        Requires: mpxj-python (pip install mpxj)
        """
        try:
            import jpype
            import mpxj
        except ImportError:
            raise GanttParsingError(
                "mpxj library required for .mpp files. "
                "Install with: pip install mpxj"
            )

        try:
            # Read project file
            from mpxj import ProjectReader

            project = ProjectReader(str(self.file_path))

            tasks = []
            for task in project.tasks:
                if task.id is None:
                    continue

                # Extract dates
                start = task.start
                finish = task.finish

                if not start or not finish:
                    continue

                # Convert to Python date objects
                if hasattr(start, 'date'):
                    start_date = start.date()
                else:
                    start_date = start

                if hasattr(finish, 'date'):
                    end_date = finish.date()
                else:
                    end_date = finish

                # Calculate duration
                duration = (end_date - start_date).days

                # Extract dependencies
                dependencies = []
                if hasattr(task, 'predecessors') and task.predecessors:
                    for pred in task.predecessors:
                        if hasattr(pred, 'source_task') and pred.source_task:
                            dependencies.append(pred.source_task.id)

                # Extract resources
                resources = []
                if hasattr(task, 'resource_assignments') and task.resource_assignments:
                    for assignment in task.resource_assignments:
                        if hasattr(assignment, 'resource') and assignment.resource:
                            resource_name = assignment.resource.name or f"Resource_{assignment.resource.id}"
                            resources.append(resource_name)

                # Extract completion
                percent_complete = float(task.percent_complete or 0)

                # Extract other fields
                priority = self._map_priority(task.priority or 500)
                cost = float(task.cost) if hasattr(task, 'cost') and task.cost else None
                notes = task.notes if hasattr(task, 'notes') else None
                status = self._determine_status(percent_complete, start_date, end_date)

                gantt_task = GanttTask(
                    task_id=task.id,
                    task_name=task.name or 'Unnamed Task',
                    start_date=start_date,
                    end_date=end_date,
                    duration=duration,
                    dependencies=dependencies,
                    resources=resources,
                    completion=percent_complete,
                    status=status,
                    priority=priority,
                    cost=cost,
                    notes=notes,
                )
                tasks.append(gantt_task)

            return tasks

        except Exception as e:
            raise GanttParsingError(f"Error parsing .mpp file: {str(e)}")

    def _get_xml_text(self, elem: ET.Element, tag: str, ns: Dict[str, str], default: str = '') -> str:
        """Safely get text content from XML element"""
        child = elem.find(tag, ns)
        if child is not None and child.text:
            return child.text.strip()
        return default

    def _get_xml_date(self, elem: ET.Element, tag: str, ns: Dict[str, str]) -> Optional[date]:
        """Parse date from XML element"""
        date_str = self._get_xml_text(elem, tag, ns)
        if not date_str:
            return None

        try:
            # MS Project XML date format: YYYY-MM-DDTHH:MM:SS
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.date()
        except ValueError:
            logger.warning(f"Invalid date format: {date_str}")
            return None

    def _map_priority(self, ms_priority: int) -> int:
        """
        Map MS Project priority (0-1000) to 1-5 scale.

        MS Project: 0-1000 (500 = medium)
        Our scale: 1-5 (1 = highest, 5 = lowest)
        """
        if ms_priority >= 800:
            return 1  # Highest
        elif ms_priority >= 600:
            return 2  # High
        elif ms_priority >= 400:
            return 3  # Medium
        elif ms_priority >= 200:
            return 4  # Low
        else:
            return 5  # Lowest

    def _determine_status(self, percent_complete: float, start_date: date, end_date: date) -> str:
        """Determine task status based on completion and dates"""
        today = date.today()

        if percent_complete >= 100:
            return 'completed'
        elif percent_complete > 0:
            return 'in_progress'
        elif start_date > today:
            return 'not_started'
        elif start_date <= today <= end_date:
            return 'in_progress'
        elif end_date < today:
            return 'on_hold'  # Should have started but hasn't
        else:
            return 'not_started'

    def _calculate_critical_path(self, tasks: List[GanttTask]) -> Optional[CriticalPathInfo]:
        """
        Calculate critical path using forward and backward pass algorithm.

        Returns:
            CriticalPathInfo with critical tasks and slack times
        """
        if not tasks:
            return None

        # Build task map
        task_map = {task.task_id: task for task in tasks}

        # Calculate early start/finish (forward pass)
        early_start: Dict[int, date] = {}
        early_finish: Dict[int, date] = {}

        # Find tasks with no dependencies (start tasks)
        start_tasks = [t for t in tasks if not t.dependencies]

        # Initialize start tasks
        for task in start_tasks:
            early_start[task.task_id] = task.start_date
            early_finish[task.task_id] = task.end_date

        # Forward pass
        changed = True
        iterations = 0
        max_iterations = len(tasks) * 2

        while changed and iterations < max_iterations:
            changed = False
            iterations += 1

            for task in tasks:
                if task.task_id in early_start:
                    continue

                # Check if all dependencies have been calculated
                deps_ready = all(dep_id in early_finish for dep_id in task.dependencies)

                if deps_ready and task.dependencies:
                    # Early start is the latest early finish of dependencies
                    max_dep_finish = max(early_finish[dep_id] for dep_id in task.dependencies)
                    early_start[task.task_id] = max_dep_finish
                    early_finish[task.task_id] = max_dep_finish + timedelta(days=task.duration)
                    changed = True

        # Calculate late start/finish (backward pass)
        # Project end is the latest early finish
        project_end = max(early_finish.values()) if early_finish else date.today()

        late_start: Dict[int, date] = {}
        late_finish: Dict[int, date] = {}

        # Find tasks with no successors (end tasks)
        all_successors: Set[int] = set()
        for task in tasks:
            all_successors.update(task.dependencies)

        end_tasks = [t for t in tasks if t.task_id not in all_successors]

        # Initialize end tasks
        for task in end_tasks:
            late_finish[task.task_id] = project_end
            late_start[task.task_id] = late_finish[task.task_id] - timedelta(days=task.duration)

        # Build reverse dependency map (successors)
        successors: Dict[int, List[int]] = {task.task_id: [] for task in tasks}
        for task in tasks:
            for dep_id in task.dependencies:
                if dep_id in successors:
                    successors[dep_id].append(task.task_id)

        # Backward pass
        changed = True
        iterations = 0

        while changed and iterations < max_iterations:
            changed = False
            iterations += 1

            for task in tasks:
                if task.task_id in late_finish:
                    continue

                # Check if all successors have been calculated
                task_successors = successors.get(task.task_id, [])
                succs_ready = all(succ_id in late_start for succ_id in task_successors)

                if succs_ready and task_successors:
                    # Late finish is the earliest late start of successors
                    min_succ_start = min(late_start[succ_id] for succ_id in task_successors)
                    late_finish[task.task_id] = min_succ_start
                    late_start[task.task_id] = late_finish[task.task_id] - timedelta(days=task.duration)
                    changed = True

        # Calculate slack time and identify critical path
        slack_time: Dict[int, int] = {}
        critical_tasks: List[int] = []

        for task in tasks:
            if task.task_id in early_start and task.task_id in late_start:
                slack = (late_start[task.task_id] - early_start[task.task_id]).days
                slack_time[task.task_id] = slack

                # Critical path tasks have zero slack
                if slack == 0:
                    critical_tasks.append(task.task_id)

        # Total project duration
        total_duration = (project_end - min(t.start_date for t in tasks)).days

        return CriticalPathInfo(
            critical_tasks=critical_tasks,
            total_duration=total_duration,
            slack_time=slack_time,
        )

    def export_to_json(self, output_path: str) -> str:
        """
        Export timeline data to JSON file.

        Args:
            output_path: Output JSON file path

        Returns:
            Path to exported JSON file
        """
        import json

        timeline = self.extract_timeline()

        # Convert to dict
        timeline_dict = timeline.model_dump(mode='json')

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(timeline_dict, f, indent=2, default=str)

        return output_path

    def export_to_csv(self, output_path: str) -> str:
        """
        Export tasks to CSV file.

        Args:
            output_path: Output CSV file path

        Returns:
            Path to exported CSV file
        """
        import csv

        tasks = self.extract_tasks()

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            if not tasks:
                return output_path

            # Define CSV columns
            fieldnames = [
                'task_id', 'task_name', 'start_date', 'end_date', 'duration',
                'completion', 'status', 'priority', 'cost', 'resources', 'dependencies', 'notes'
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for task in tasks:
                row = {
                    'task_id': task.task_id,
                    'task_name': task.task_name,
                    'start_date': task.start_date.isoformat(),
                    'end_date': task.end_date.isoformat(),
                    'duration': task.duration,
                    'completion': task.completion,
                    'status': task.status,
                    'priority': task.priority,
                    'cost': task.cost,
                    'resources': ', '.join(task.resources),
                    'dependencies': ', '.join(map(str, task.dependencies)),
                    'notes': task.notes or '',
                }
                writer.writerow(row)

        return output_path
