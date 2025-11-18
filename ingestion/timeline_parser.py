"""
Timeline data parser for project schedules and test timelines.

Provides high-level parsing of project timelines from various sources.
Combines Gantt parser capabilities with additional timeline analysis.
"""

import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ingestion.gantt_parser import GanttIngestion
from ingestion.models import GanttTask, TimelineData

logger = logging.getLogger(__name__)


class TimelineParser:
    """
    High-level timeline parsing and analysis tool.

    Supports:
    - Test schedule extraction
    - Resource allocation analysis
    - Milestone tracking
    - Equipment booking timelines
    - Personnel assignment schedules
    """

    def __init__(self):
        """Initialize timeline parser"""
        self.supported_formats = ['.xml', '.mpp']

    def parse_timeline(self, file_path: str) -> TimelineData:
        """
        Parse timeline from project file.

        Args:
            file_path: Path to project file (.xml or .mpp)

        Returns:
            TimelineData with complete timeline information

        Raises:
            Exception: If parsing fails
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        gantt = GanttIngestion(str(path))
        return gantt.extract_timeline()

    def extract_test_schedule(self, file_path: str) -> Dict[str, any]:
        """
        Extract test schedule with test-specific categorization.

        Args:
            file_path: Path to project file

        Returns:
            Dictionary with test schedule data
        """
        timeline = self.parse_timeline(file_path)

        # Categorize tasks by test phase
        test_phases = {
            'preparation': [],
            'testing': [],
            'analysis': [],
            'reporting': [],
            'review': [],
        }

        for task in timeline.tasks:
            task_name_lower = task.task_name.lower()

            if any(keyword in task_name_lower for keyword in ['prep', 'setup', 'calibration']):
                test_phases['preparation'].append(task)
            elif any(keyword in task_name_lower for keyword in ['test', 'measurement', 'data collection']):
                test_phases['testing'].append(task)
            elif any(keyword in task_name_lower for keyword in ['analysis', 'calculation', 'evaluation']):
                test_phases['analysis'].append(task)
            elif any(keyword in task_name_lower for keyword in ['report', 'documentation', 'certificate']):
                test_phases['reporting'].append(task)
            elif any(keyword in task_name_lower for keyword in ['review', 'approval', 'verification']):
                test_phases['review'].append(task)

        return {
            'project_name': timeline.project_name,
            'start_date': timeline.start_date,
            'end_date': timeline.end_date,
            'total_duration_days': (timeline.end_date - timeline.start_date).days,
            'phases': {
                phase: {
                    'task_count': len(tasks),
                    'tasks': [
                        {
                            'id': t.task_id,
                            'name': t.task_name,
                            'start': t.start_date,
                            'end': t.end_date,
                            'duration': t.duration,
                            'status': t.status,
                            'completion': t.completion,
                        }
                        for t in tasks
                    ]
                }
                for phase, tasks in test_phases.items()
            }
        }

    def extract_equipment_booking(self, file_path: str) -> Dict[str, List[Dict]]:
        """
        Extract equipment booking schedule from timeline.

        Args:
            file_path: Path to project file

        Returns:
            Dictionary mapping equipment to booking slots
        """
        timeline = self.parse_timeline(file_path)

        # Group tasks by resources (equipment)
        equipment_schedule = {}

        for task in timeline.tasks:
            for resource in task.resources:
                # Filter for equipment (vs personnel)
                if self._is_equipment_resource(resource):
                    if resource not in equipment_schedule:
                        equipment_schedule[resource] = []

                    equipment_schedule[resource].append({
                        'task_id': task.task_id,
                        'task_name': task.task_name,
                        'start_date': task.start_date,
                        'end_date': task.end_date,
                        'duration_days': task.duration,
                    })

        # Sort bookings by date for each equipment
        for equipment in equipment_schedule:
            equipment_schedule[equipment].sort(key=lambda x: x['start_date'])

        return equipment_schedule

    def extract_personnel_assignment(self, file_path: str) -> Dict[str, List[Dict]]:
        """
        Extract personnel assignment schedule from timeline.

        Args:
            file_path: Path to project file

        Returns:
            Dictionary mapping personnel to task assignments
        """
        timeline = self.parse_timeline(file_path)

        # Group tasks by personnel
        personnel_schedule = {}

        for task in timeline.tasks:
            for resource in task.resources:
                # Filter for personnel (vs equipment)
                if not self._is_equipment_resource(resource):
                    if resource not in personnel_schedule:
                        personnel_schedule[resource] = []

                    personnel_schedule[resource].append({
                        'task_id': task.task_id,
                        'task_name': task.task_name,
                        'start_date': task.start_date,
                        'end_date': task.end_date,
                        'duration_days': task.duration,
                        'status': task.status,
                    })

        # Sort assignments by date for each person
        for person in personnel_schedule:
            personnel_schedule[person].sort(key=lambda x: x['start_date'])

        return personnel_schedule

    def extract_milestones(self, file_path: str) -> List[Dict[str, any]]:
        """
        Extract project milestones.

        Args:
            file_path: Path to project file

        Returns:
            List of milestone dictionaries
        """
        timeline = self.parse_timeline(file_path)

        milestones = []
        for milestone_data in timeline.milestones:
            # Add status based on date
            today = date.today()
            milestone_date = milestone_data['date']

            if milestone_date < today:
                status = 'completed'
            elif milestone_date == today:
                status = 'due_today'
            else:
                status = 'upcoming'

            milestones.append({
                'task_id': milestone_data['task_id'],
                'name': milestone_data['name'],
                'date': milestone_date,
                'status': status,
                'days_until': (milestone_date - today).days,
            })

        # Sort by date
        milestones.sort(key=lambda x: x['date'])

        return milestones

    def calculate_workload(self, file_path: str) -> Dict[str, Dict[str, int]]:
        """
        Calculate workload distribution by resource.

        Args:
            file_path: Path to project file

        Returns:
            Dictionary with workload statistics per resource
        """
        timeline = self.parse_timeline(file_path)

        workload = {}

        for task in timeline.tasks:
            for resource in task.resources:
                if resource not in workload:
                    workload[resource] = {
                        'total_tasks': 0,
                        'total_days': 0,
                        'active_tasks': 0,
                        'completed_tasks': 0,
                    }

                workload[resource]['total_tasks'] += 1
                workload[resource]['total_days'] += task.duration

                if task.status == 'in_progress':
                    workload[resource]['active_tasks'] += 1
                elif task.status == 'completed':
                    workload[resource]['completed_tasks'] += 1

        return workload

    def identify_conflicts(self, file_path: str) -> List[Dict[str, any]]:
        """
        Identify resource conflicts (over-allocation).

        Args:
            file_path: Path to project file

        Returns:
            List of conflicts with details
        """
        timeline = self.parse_timeline(file_path)

        conflicts = []

        # Group tasks by resource
        resource_tasks = {}
        for task in timeline.tasks:
            for resource in task.resources:
                if resource not in resource_tasks:
                    resource_tasks[resource] = []
                resource_tasks[resource].append(task)

        # Check for overlapping tasks per resource
        for resource, tasks in resource_tasks.items():
            # Sort by start date
            sorted_tasks = sorted(tasks, key=lambda t: t.start_date)

            for i in range(len(sorted_tasks)):
                for j in range(i + 1, len(sorted_tasks)):
                    task1 = sorted_tasks[i]
                    task2 = sorted_tasks[j]

                    # Check if tasks overlap
                    if task1.end_date >= task2.start_date:
                        conflicts.append({
                            'resource': resource,
                            'task1_id': task1.task_id,
                            'task1_name': task1.task_name,
                            'task1_dates': f"{task1.start_date} to {task1.end_date}",
                            'task2_id': task2.task_id,
                            'task2_name': task2.task_name,
                            'task2_dates': f"{task2.start_date} to {task2.end_date}",
                            'overlap_start': task2.start_date,
                            'overlap_end': min(task1.end_date, task2.end_date),
                        })

        return conflicts

    def generate_gantt_visualization_data(self, file_path: str) -> Dict[str, any]:
        """
        Generate data structure suitable for Gantt chart visualization.

        Args:
            file_path: Path to project file

        Returns:
            Dictionary with visualization-ready data
        """
        timeline = self.parse_timeline(file_path)

        # Build task hierarchy (if parent-child relationships exist)
        tasks_data = []
        for task in timeline.tasks:
            task_data = {
                'id': task.task_id,
                'name': task.task_name,
                'start': task.start_date.isoformat(),
                'end': task.end_date.isoformat(),
                'duration': task.duration,
                'progress': task.completion,
                'dependencies': task.dependencies,
                'resources': task.resources,
                'status': task.status,
            }

            # Add critical path indicator
            if timeline.critical_path and task.task_id in timeline.critical_path.critical_tasks:
                task_data['is_critical'] = True
            else:
                task_data['is_critical'] = False

            tasks_data.append(task_data)

        return {
            'project_name': timeline.project_name,
            'start_date': timeline.start_date.isoformat(),
            'end_date': timeline.end_date.isoformat(),
            'tasks': tasks_data,
            'milestones': [
                {
                    'name': m['name'],
                    'date': m['date'].isoformat(),
                }
                for m in timeline.milestones
            ],
        }

    def _is_equipment_resource(self, resource_name: str) -> bool:
        """
        Determine if resource is equipment vs personnel.

        Uses naming conventions to classify resources.
        """
        resource_lower = resource_name.lower()

        equipment_keywords = [
            'equipment', 'machine', 'tool', 'simulator', 'chamber',
            'meter', 'analyzer', 'tester', 'device', 'system',
            'module', 'panel', 'inverter', 'lamp', 'sensor'
        ]

        return any(keyword in resource_lower for keyword in equipment_keywords)

    def export_calendar_format(self, file_path: str, output_path: str) -> str:
        """
        Export timeline in iCalendar format (.ics).

        Args:
            file_path: Path to project file
            output_path: Output .ics file path

        Returns:
            Path to exported calendar file
        """
        timeline = self.parse_timeline(file_path)

        # Simple iCalendar format
        ical_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            f"PRODID:-//PV Test Automation//Timeline Parser//EN",
            f"X-WR-CALNAME:{timeline.project_name}",
        ]

        for task in timeline.tasks:
            # Convert dates to datetime format
            start_dt = f"{task.start_date.strftime('%Y%m%d')}T090000"
            end_dt = f"{task.end_date.strftime('%Y%m%d')}T170000"

            ical_lines.extend([
                "BEGIN:VEVENT",
                f"UID:task-{task.task_id}@pv-test-automation",
                f"DTSTART:{start_dt}",
                f"DTEND:{end_dt}",
                f"SUMMARY:{task.task_name}",
                f"DESCRIPTION:Duration: {task.duration} days\\nStatus: {task.status}\\nCompletion: {task.completion}%",
                f"STATUS:{self._map_status_to_ical(task.status)}",
                "END:VEVENT",
            ])

        ical_lines.append("END:VCALENDAR")

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(ical_lines))

        logger.info(f"Exported timeline to iCalendar: {output_path}")
        return output_path

    def _map_status_to_ical(self, status: str) -> str:
        """Map task status to iCalendar status"""
        status_map = {
            'not_started': 'TENTATIVE',
            'in_progress': 'CONFIRMED',
            'completed': 'CONFIRMED',
            'on_hold': 'TENTATIVE',
            'cancelled': 'CANCELLED',
        }
        return status_map.get(status, 'TENTATIVE')
