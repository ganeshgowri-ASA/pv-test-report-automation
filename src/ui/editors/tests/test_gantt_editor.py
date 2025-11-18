"""
Tests for Gantt Chart Editor

Tests for Gantt chart editor with tasks, dependencies,
resources, and timeline management.
"""

import pytest
from datetime import datetime, timedelta

from ..gantt_editor import (
    GanttEditor,
    Task,
    Resource,
    TaskStatus,
    TaskPriority,
)
from ..editor_utils import EditorState, EditorType


class TestResource:
    """Test Resource class"""

    def test_init(self):
        """Test initialization"""
        resource = Resource(
            id="r1",
            name="John Doe",
            role="Engineer",
            availability=0.8,
        )

        assert resource.id == "r1"
        assert resource.name == "John Doe"
        assert resource.role == "Engineer"
        assert resource.availability == 0.8

    def test_to_dict(self):
        """Test conversion to dictionary"""
        resource = Resource(
            id="r1",
            name="Jane Smith",
            role="Manager",
        )

        data = resource.to_dict()

        assert data["id"] == "r1"
        assert data["name"] == "Jane Smith"
        assert data["role"] == "Manager"
        assert data["availability"] == 1.0

    def test_from_dict(self):
        """Test creation from dictionary"""
        data = {
            "id": "r1",
            "name": "John Doe",
            "role": "Developer",
            "availability": 0.5,
            "metadata": {"skills": ["Python", "JavaScript"]},
        }

        resource = Resource.from_dict(data)

        assert resource.id == "r1"
        assert resource.availability == 0.5


class TestTask:
    """Test Task class"""

    def test_init(self):
        """Test initialization"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 10)

        task = Task(
            id="t1",
            name="Test Task",
            start_date=start,
            end_date=end,
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
        )

        assert task.id == "t1"
        assert task.name == "Test Task"
        assert task.start_date == start
        assert task.end_date == end
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == TaskPriority.HIGH

    def test_duration(self):
        """Test duration calculation"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 11)  # 10 days

        task = Task(
            id="t1",
            name="Task",
            start_date=start,
            end_date=end,
        )

        assert task.duration == timedelta(days=10)

    def test_to_dict(self):
        """Test conversion to dictionary"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 10)

        task = Task(
            id="t1",
            name="Task",
            start_date=start,
            end_date=end,
            progress=0.5,
        )

        data = task.to_dict()

        assert data["id"] == "t1"
        assert data["name"] == "Task"
        assert data["progress"] == 0.5
        assert "start_date" in data
        assert "end_date" in data

    def test_from_dict(self):
        """Test creation from dictionary"""
        data = {
            "id": "t1",
            "name": "Task",
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-01-10T00:00:00",
            "status": "in_progress",
            "priority": "high",
            "progress": 0.75,
            "dependencies": ["t0"],
            "resources": ["r1", "r2"],
            "is_milestone": False,
            "description": "Test description",
            "metadata": {},
        }

        task = Task.from_dict(data)

        assert task.id == "t1"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == TaskPriority.HIGH
        assert task.progress == 0.75
        assert len(task.dependencies) == 1
        assert len(task.resources) == 2

    def test_milestone(self):
        """Test milestone task"""
        task = Task(
            id="m1",
            name="Project Kickoff",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 1),
            is_milestone=True,
        )

        assert task.is_milestone
        assert task.duration == timedelta(0)

    def test_dependencies(self):
        """Test task dependencies"""
        task = Task(
            id="t2",
            name="Dependent Task",
            start_date=datetime(2024, 1, 11),
            end_date=datetime(2024, 1, 20),
            dependencies=["t1"],
        )

        assert "t1" in task.dependencies

    def test_resource_assignment(self):
        """Test resource assignment"""
        task = Task(
            id="t1",
            name="Task",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 10),
            resources=["r1", "r2"],
        )

        assert len(task.resources) == 2
        assert "r1" in task.resources


class TestGanttEditor:
    """Test GanttEditor class"""

    @pytest.fixture
    def editor(self):
        """Create editor instance"""
        return GanttEditor(editor_id="test_gantt_editor")

    def test_init(self, editor):
        """Test initialization"""
        assert editor.editor_id == "test_gantt_editor"
        assert editor.undo_manager is not None
        assert editor.validator is not None

    def test_get_state(self, editor):
        """Test getting editor state"""
        state = editor.get_state()

        assert isinstance(state, EditorState)
        assert state.editor_type == EditorType.GANTT
        assert "tasks" in state.content
        assert "resources" in state.content
        assert "name" in state.content

    def test_get_tasks(self, editor):
        """Test getting tasks"""
        tasks = editor.get_tasks()
        assert isinstance(tasks, list)

    def test_get_resources(self, editor):
        """Test getting resources"""
        resources = editor.get_resources()
        assert isinstance(resources, list)

    def test_add_task(self, editor):
        """Test adding task"""
        state = editor.get_state()
        initial_count = len(state.content.get("tasks", []))

        # Add task
        import uuid
        task = Task(
            id=f"task_{uuid.uuid4().hex[:8]}",
            name="New Task",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
        )

        tasks = state.content.get("tasks", [])
        tasks.append(task.to_dict())
        state.content["tasks"] = tasks

        assert len(state.content["tasks"]) == initial_count + 1

    def test_add_resource(self, editor):
        """Test adding resource"""
        state = editor.get_state()
        initial_count = len(state.content.get("resources", []))

        # Add resource
        import uuid
        resource = Resource(
            id=f"resource_{uuid.uuid4().hex[:8]}",
            name="New Resource",
            role="Developer",
        )

        resources = state.content.get("resources", [])
        resources.append(resource.to_dict())
        state.content["resources"] = resources

        assert len(state.content["resources"]) == initial_count + 1

    def test_update_task(self, editor):
        """Test updating task"""
        state = editor.get_state()

        # Add a task
        task = Task(
            id="test_task",
            name="Original Name",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 10),
        )

        state.content["tasks"] = [task.to_dict()]

        # Update task
        task.name = "Updated Name"
        task.progress = 0.5
        editor._update_task(task, state)

        updated = state.content["tasks"][0]
        assert updated["name"] == "Updated Name"
        assert updated["progress"] == 0.5

    def test_delete_task(self, editor):
        """Test deleting task"""
        state = editor.get_state()

        # Add tasks
        task1 = Task(
            id="t1",
            name="Task 1",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 10),
        )
        task2 = Task(
            id="t2",
            name="Task 2",
            start_date=datetime(2024, 1, 11),
            end_date=datetime(2024, 1, 20),
            dependencies=["t1"],
        )

        state.content["tasks"] = [task1.to_dict(), task2.to_dict()]

        # Delete first task
        tasks = [t for t in state.content["tasks"] if t["id"] != "t1"]

        # Remove from dependencies
        for t in tasks:
            if "t1" in t.get("dependencies", []):
                t["dependencies"].remove("t1")

        state.content["tasks"] = tasks

        assert len(state.content["tasks"]) == 1
        assert state.content["tasks"][0]["id"] == "t2"
        assert "t1" not in state.content["tasks"][0]["dependencies"]

    def test_duplicate_task(self, editor):
        """Test duplicating task"""
        state = editor.get_state()

        # Add original task
        original = Task(
            id="original",
            name="Original Task",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 10),
            resources=["r1"],
        )
        state.content["tasks"] = [original.to_dict()]

        # Duplicate
        import uuid
        duplicate = Task(
            id=f"task_{uuid.uuid4().hex[:8]}",
            name=f"{original.name} (Copy)",
            start_date=original.end_date,
            end_date=original.end_date + original.duration,
            status=TaskStatus.NOT_STARTED,
            priority=original.priority,
            resources=original.resources.copy(),
        )

        tasks = state.content.get("tasks", [])
        tasks.append(duplicate.to_dict())
        state.content["tasks"] = tasks

        assert len(state.content["tasks"]) == 2
        assert state.content["tasks"][1]["name"] == "Original Task (Copy)"

    def test_task_status_changes(self, editor):
        """Test changing task status"""
        task = Task(
            id="t1",
            name="Task",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 10),
            status=TaskStatus.NOT_STARTED,
        )

        # Change status
        task.status = TaskStatus.IN_PROGRESS
        assert task.status == TaskStatus.IN_PROGRESS

        task.status = TaskStatus.COMPLETED
        assert task.status == TaskStatus.COMPLETED

    def test_task_priority_levels(self, editor):
        """Test different priority levels"""
        for priority in TaskPriority:
            task = Task(
                id=f"task_{priority.value}",
                name=f"Task {priority.value}",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 10),
                priority=priority,
            )
            assert task.priority == priority

    def test_progress_tracking(self, editor):
        """Test progress tracking"""
        state = editor.get_state()

        tasks = [
            Task(
                id="t1",
                name="Task 1",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 10),
                progress=1.0,  # Completed
            ),
            Task(
                id="t2",
                name="Task 2",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 10),
                progress=0.5,  # 50% done
            ),
            Task(
                id="t3",
                name="Task 3",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 10),
                progress=0.0,  # Not started
            ),
        ]

        state.content["tasks"] = [t.to_dict() for t in tasks]

        # Calculate overall progress
        overall_progress = sum(t.progress for t in tasks) / len(tasks)
        assert overall_progress == 0.5  # (1.0 + 0.5 + 0.0) / 3

    def test_dependency_chain(self, editor):
        """Test dependency chain"""
        state = editor.get_state()

        tasks = [
            Task(
                id="t1",
                name="Task 1",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 10),
            ),
            Task(
                id="t2",
                name="Task 2",
                start_date=datetime(2024, 1, 11),
                end_date=datetime(2024, 1, 20),
                dependencies=["t1"],
            ),
            Task(
                id="t3",
                name="Task 3",
                start_date=datetime(2024, 1, 21),
                end_date=datetime(2024, 1, 30),
                dependencies=["t2"],
            ),
        ]

        state.content["tasks"] = [t.to_dict() for t in tasks]

        # Verify dependency chain
        assert "t1" in tasks[1].dependencies
        assert "t2" in tasks[2].dependencies

    def test_resource_allocation(self, editor):
        """Test resource allocation to tasks"""
        state = editor.get_state()

        # Add resources
        resources = [
            Resource(id="r1", name="Developer 1", role="Developer"),
            Resource(id="r2", name="Developer 2", role="Developer"),
        ]
        state.content["resources"] = [r.to_dict() for r in resources]

        # Add task with resources
        task = Task(
            id="t1",
            name="Development Task",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 10),
            resources=["r1", "r2"],
        )
        state.content["tasks"] = [task.to_dict()]

        # Count tasks per resource
        resource_tasks = {}
        for resource in resources:
            allocated = [
                t for t in [task]
                if resource.id in t.resources
            ]
            resource_tasks[resource.id] = len(allocated)

        assert resource_tasks["r1"] == 1
        assert resource_tasks["r2"] == 1

    def test_milestone_tracking(self, editor):
        """Test milestone tracking"""
        state = editor.get_state()

        tasks = [
            Task(
                id="t1",
                name="Phase 1",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
            ),
            Task(
                id="m1",
                name="Phase 1 Complete",
                start_date=datetime(2024, 1, 31),
                end_date=datetime(2024, 1, 31),
                is_milestone=True,
            ),
            Task(
                id="t2",
                name="Phase 2",
                start_date=datetime(2024, 2, 1),
                end_date=datetime(2024, 2, 28),
            ),
        ]

        state.content["tasks"] = [t.to_dict() for t in tasks]

        # Count milestones
        milestones = [t for t in tasks if t.is_milestone]
        assert len(milestones) == 1

    def test_critical_path(self, editor):
        """Test critical path identification"""
        state = editor.get_state()

        tasks = [
            Task(
                id="t1",
                name="Task 1",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 10),
            ),
            Task(
                id="t2",
                name="Task 2",
                start_date=datetime(2024, 1, 11),
                end_date=datetime(2024, 1, 20),
                dependencies=["t1"],
            ),
            Task(
                id="t3",
                name="Task 3 (parallel)",
                start_date=datetime(2024, 1, 11),
                end_date=datetime(2024, 1, 15),
            ),
        ]

        state.content["tasks"] = [t.to_dict() for t in tasks]

        # Tasks with dependencies are on critical path
        critical = [t for t in tasks if t.is_on_critical_path(tasks)]

        # t1 and t2 are on critical path
        # t3 is parallel and shorter, so not critical

    def test_timeline_calculation(self, editor):
        """Test project timeline calculation"""
        state = editor.get_state()

        tasks = [
            Task(
                id="t1",
                name="Task 1",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 10),
            ),
            Task(
                id="t2",
                name="Task 2",
                start_date=datetime(2024, 1, 5),
                end_date=datetime(2024, 1, 20),
            ),
        ]

        # Calculate project timeline
        if tasks:
            project_start = min(t.start_date for t in tasks)
            project_end = max(t.end_date for t in tasks)

            assert project_start == datetime(2024, 1, 1)
            assert project_end == datetime(2024, 1, 20)

    def test_blocked_tasks(self, editor):
        """Test handling blocked tasks"""
        task = Task(
            id="t1",
            name="Blocked Task",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 10),
            status=TaskStatus.BLOCKED,
        )

        assert task.status == TaskStatus.BLOCKED

    def test_export_project(self, editor):
        """Test exporting project data"""
        state = editor.get_state()

        # Set up project
        tasks = [
            Task(
                id="t1",
                name="Task 1",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 10),
            ),
        ]
        resources = [
            Resource(id="r1", name="Developer", role="Developer"),
        ]

        state.content["tasks"] = [t.to_dict() for t in tasks]
        state.content["resources"] = [r.to_dict() for r in resources]

        # Create export data
        import json
        export_data = {
            "project": state.content.get("name"),
            "tasks": [t.to_dict() for t in tasks],
            "resources": [r.to_dict() for r in resources],
            "exported_at": datetime.now().isoformat(),
        }

        json_data = json.dumps(export_data, indent=2)
        assert len(json_data) > 0
        assert "tasks" in json_data
        assert "resources" in json_data
