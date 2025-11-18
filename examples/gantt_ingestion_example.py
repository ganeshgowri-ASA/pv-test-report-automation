"""
Example: Gantt/MS Project Ingestion

This example demonstrates how to ingest MS Project (.mpp) and other
project management files to extract tasks, timelines, and dependencies.
"""

import json
from pathlib import Path

from src.ingestion.gantt import GanttIngestionModule
from src.utils.logger import setup_logger, get_logger

# Setup logging
setup_logger(log_file="logs/gantt_ingestion.log")
logger = get_logger(__name__)


def main():
    """Main function demonstrating Gantt/MS Project ingestion."""

    # Initialize the Gantt ingestion module
    gantt_module = GanttIngestionModule()

    # Path to your project file
    project_file_path = "data/test_schedule.mpp"

    try:
        # Validate the file first
        file_path = Path(project_file_path)
        gantt_module.validate_file(file_path)
        logger.info(f"File validation successful: {project_file_path}")

        # Extract metadata without full ingestion
        metadata = gantt_module.extract_metadata(file_path)
        logger.info(f"Metadata: {metadata}")

        # Perform full ingestion
        logger.info("Starting Gantt ingestion...")
        result = gantt_module.ingest(file_path)

        # Check ingestion status
        logger.info(f"Ingestion status: {result.status.value}")
        logger.info(f"Project name: {result.project_name}")
        logger.info(f"Project duration: {result.project_start} to {result.project_end}")
        logger.info(f"Total tasks: {result.total_tasks}")
        logger.info(f"Completed tasks: {result.completed_tasks}")
        logger.info(f"Overall progress: {result.percent_complete}%")

        # Analyze tasks
        logger.info("\nTask Analysis:")
        milestones = [task for task in result.tasks if task.milestone]
        logger.info(f"  Milestones: {len(milestones)}")

        critical_tasks = [task for task in result.tasks if task.priority == 1]
        logger.info(f"  Critical tasks (priority 1): {len(critical_tasks)}")

        # Display task hierarchy
        logger.info("\nTask Hierarchy:")
        root_tasks = [task for task in result.tasks if task.parent_task_id is None]

        for task in root_tasks:
            display_task_tree(task, result.tasks, indent=0)

        # Resource utilization
        logger.info("\nResource Utilization:")
        all_resources = {}
        for task in result.tasks:
            for resource in task.resources:
                if resource.resource_id not in all_resources:
                    all_resources[resource.resource_id] = {
                        'name': resource.name,
                        'tasks': 0,
                        'total_allocation': 0.0
                    }
                all_resources[resource.resource_id]['tasks'] += 1
                all_resources[resource.resource_id]['total_allocation'] += resource.allocation_percent

        for res_id, res_info in all_resources.items():
            logger.info(f"  {res_info['name']}: {res_info['tasks']} tasks, "
                       f"avg allocation: {res_info['total_allocation'] / res_info['tasks']:.1f}%")

        # Save detailed report as JSON
        output_path = Path("output") / f"{result.project_name.replace(' ', '_')}_report.json"
        output_path.parent.mkdir(exist_ok=True)

        report = {
            'project_name': result.project_name,
            'project_start': result.project_start.isoformat(),
            'project_end': result.project_end.isoformat(),
            'total_tasks': result.total_tasks,
            'completed_tasks': result.completed_tasks,
            'percent_complete': result.percent_complete,
            'tasks': [
                {
                    'task_id': task.task_id,
                    'name': task.name,
                    'status': task.status.value,
                    'percent_complete': task.percent_complete,
                    'start_date': task.start_date.isoformat(),
                    'end_date': task.end_date.isoformat(),
                    'duration_days': task.duration_days,
                    'dependencies': task.dependencies,
                    'milestone': task.milestone
                }
                for task in result.tasks
            ]
        }

        output_path.write_text(json.dumps(report, indent=2))
        logger.info(f"\nDetailed report saved to: {output_path}")

        # Report errors if any
        if result.errors:
            logger.warning(f"Errors encountered: {len(result.errors)}")
            for error in result.errors:
                logger.warning(f"  - {error}")

    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        raise


def display_task_tree(task, all_tasks, indent=0):
    """Display task in hierarchical tree format."""
    prefix = "  " * indent
    status_icon = "✓" if task.status.value == "completed" else "○"
    milestone_icon = "◆" if task.milestone else "□"

    logger.info(f"{prefix}{status_icon} {milestone_icon} {task.name} "
               f"({task.percent_complete}% complete)")

    # Find and display child tasks
    child_tasks = [t for t in all_tasks if t.parent_task_id == task.task_id]
    for child in child_tasks:
        display_task_tree(child, all_tasks, indent + 1)


if __name__ == "__main__":
    main()
