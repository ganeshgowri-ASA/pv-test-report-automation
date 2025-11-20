"""
Gantt Chart Editor Component

Interactive Gantt chart editor for project timelines with task dependencies,
resource allocation, milestone tracking, and critical path display.
"""

import streamlit as st
import pandas as pd
import plotly.figure_factory as ff
import plotly.graph_objects as go
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid

from .editor_utils import (
    EditorState,
    EditorType,
    UndoRedoManager,
    AutoSaveManager,
    EditorValidator,
    EditorTheme,
    ActionType,
    EditorAction,
    init_session_state,
)


class TaskStatus(Enum):
    """Task status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    ON_HOLD = "on_hold"


class TaskPriority(Enum):
    """Task priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Resource:
    """Project resource"""
    id: str
    name: str
    role: str
    availability: float = 1.0  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "availability": self.availability,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Resource":
        """Create from dictionary"""
        return cls(
            id=data["id"],
            name=data["name"],
            role=data["role"],
            availability=data.get("availability", 1.0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Task:
    """Gantt chart task"""
    id: str
    name: str
    start_date: datetime
    end_date: datetime
    status: TaskStatus = TaskStatus.NOT_STARTED
    priority: TaskPriority = TaskPriority.MEDIUM
    progress: float = 0.0  # 0.0 to 1.0
    dependencies: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    is_milestone: bool = False
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "status": self.status.value,
            "priority": self.priority.value,
            "progress": self.progress,
            "dependencies": self.dependencies,
            "resources": self.resources,
            "is_milestone": self.is_milestone,
            "description": self.description,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create from dictionary"""
        return cls(
            id=data["id"],
            name=data["name"],
            start_date=datetime.fromisoformat(data["start_date"]),
            end_date=datetime.fromisoformat(data["end_date"]),
            status=TaskStatus(data.get("status", "not_started")),
            priority=TaskPriority(data.get("priority", "medium")),
            progress=data.get("progress", 0.0),
            dependencies=data.get("dependencies", []),
            resources=data.get("resources", []),
            is_milestone=data.get("is_milestone", False),
            description=data.get("description", ""),
            metadata=data.get("metadata", {}),
        )

    @property
    def duration(self) -> timedelta:
        """Get task duration"""
        return self.end_date - self.start_date

    def is_on_critical_path(self, all_tasks: List["Task"]) -> bool:
        """Check if task is on critical path"""
        # Simplified critical path determination
        # In production, use proper CPM algorithm
        if not self.dependencies:
            return True
        return any(
            dep_task.is_on_critical_path(all_tasks)
            for dep_task in all_tasks
            if dep_task.id in self.dependencies
        )


class GanttEditor:
    """
    Gantt chart editor for project timelines.

    Features:
    - Interactive timeline editing
    - Task dependencies
    - Resource allocation
    - Milestone tracking
    - Critical path display
    - Progress tracking
    - Export capabilities
    """

    def __init__(
        self,
        editor_id: str = "gantt_editor",
        auto_save_interval: int = 60,
        max_history: int = 50,
    ):
        """
        Initialize Gantt editor.

        Args:
            editor_id: Unique editor identifier
            auto_save_interval: Auto-save interval in seconds
            max_history: Maximum undo/redo history
        """
        self.editor_id = editor_id
        self.state_key = f"{editor_id}_state"

        # Initialize state
        self._init_state()

        # Initialize managers
        self.undo_manager = UndoRedoManager(max_history=max_history)
        self.validator = EditorValidator()

        # Setup auto-save
        self.auto_save_manager = AutoSaveManager(
            save_callback=self._save_callback,
            auto_save_interval=auto_save_interval,
        )

    def _init_state(self):
        """Initialize editor state"""
        if self.state_key not in st.session_state:
            # Create sample project
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            state = EditorState(
                editor_id=self.editor_id,
                editor_type=EditorType.GANTT,
                content={
                    "name": "Untitled Project",
                    "tasks": [],
                    "resources": [],
                    "start_date": today.isoformat(),
                    "end_date": (today + timedelta(days=90)).isoformat(),
                },
            )
            st.session_state[self.state_key] = state

    def _save_callback(self, state: EditorState) -> bool:
        """Save callback for auto-save"""
        try:
            state.mark_saved()
            return True
        except Exception:
            return False

    def get_state(self) -> EditorState:
        """Get current editor state"""
        return st.session_state[self.state_key]

    def get_tasks(self) -> List[Task]:
        """Get all tasks"""
        state = self.get_state()
        return [Task.from_dict(t) for t in state.content.get("tasks", [])]

    def get_resources(self) -> List[Resource]:
        """Get all resources"""
        state = self.get_state()
        return [Resource.from_dict(r) for r in state.content.get("resources", [])]

    def render(self):
        """Render the Gantt editor"""
        st.subheader("📅 Gantt Chart Editor")

        state = self.get_state()

        # Toolbar
        self._render_toolbar(state)

        # Gantt chart
        self._render_gantt_chart(state)

        # Task management
        col1, col2 = st.columns([2, 1])

        with col1:
            self._render_task_list(state)

        with col2:
            self._render_sidebar(state)

        # Auto-save
        if self.auto_save_manager.auto_save(state):
            st.toast("✅ Auto-saved", icon="💾")

    def _render_toolbar(self, state: EditorState):
        """Render toolbar"""
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

        with col1:
            # Project name
            new_name = st.text_input(
                "Project Name",
                value=state.content.get("name", "Untitled Project"),
                key=f"{self.editor_id}_name",
            )
            if new_name != state.content.get("name"):
                state.content["name"] = new_name
                state.mark_modified()

        with col2:
            # Save
            if st.button("💾 Save", use_container_width=True):
                if self.auto_save_manager.manual_save(state):
                    st.success("Saved!")

        with col3:
            # Add task
            if st.button("➕ Task", use_container_width=True):
                self._add_task_dialog(state)

        with col4:
            # Add resource
            if st.button("👤 Resource", use_container_width=True):
                self._add_resource_dialog(state)

        with col5:
            # Export
            if st.button("📥 Export", use_container_width=True):
                self._export_project(state)

        # Project timeline
        start_date = datetime.fromisoformat(state.content.get("start_date"))
        end_date = datetime.fromisoformat(state.content.get("end_date"))

        st.caption(
            f"Timeline: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} "
            f"({(end_date - start_date).days} days)"
        )

    def _render_gantt_chart(self, state: EditorState):
        """Render Gantt chart using Plotly"""
        st.markdown("#### Timeline")

        tasks = self.get_tasks()

        if not tasks:
            st.info("No tasks yet. Add tasks to see the Gantt chart.")
            return

        # Prepare data for Plotly
        df_tasks = []
        colors = []

        status_colors = {
            TaskStatus.NOT_STARTED: "#808080",
            TaskStatus.IN_PROGRESS: "#4472C4",
            TaskStatus.COMPLETED: "#70AD47",
            TaskStatus.BLOCKED: "#C5504B",
            TaskStatus.ON_HOLD: "#FFC000",
        }

        for task in tasks:
            df_tasks.append(dict(
                Task=task.name,
                Start=task.start_date.strftime('%Y-%m-%d'),
                Finish=task.end_date.strftime('%Y-%m-%d'),
                Resource=", ".join(task.resources) if task.resources else "Unassigned",
                Progress=int(task.progress * 100),
            ))
            colors.append(status_colors.get(task.status, "#808080"))

        # Create Gantt chart
        fig = ff.create_gantt(
            df_tasks,
            colors=colors,
            index_col='Resource',
            show_colorbar=True,
            showgrid_x=True,
            showgrid_y=True,
            height=400,
        )

        # Update layout
        fig.update_layout(
            xaxis_title="Timeline",
            yaxis_title="Tasks",
            hovermode='closest',
        )

        st.plotly_chart(fig, use_container_width=True)

        # Legend
        legend_cols = st.columns(len(TaskStatus))
        for i, status in enumerate(TaskStatus):
            with legend_cols[i]:
                color = status_colors.get(status, "#808080")
                st.markdown(
                    f'<div style="background-color: {color}; padding: 5px; '
                    f'border-radius: 3px; text-align: center; color: white;">'
                    f'{status.value.replace("_", " ").title()}</div>',
                    unsafe_allow_html=True
                )

    def _render_task_list(self, state: EditorState):
        """Render task list"""
        st.markdown("#### Tasks")

        tasks = self.get_tasks()

        if not tasks:
            st.info("No tasks. Click '➕ Task' to add one.")
            return

        # Sort options
        sort_by = st.selectbox(
            "Sort by",
            options=["Start Date", "Priority", "Status", "Name"],
            key=f"{self.editor_id}_sort",
        )

        if sort_by == "Start Date":
            tasks.sort(key=lambda t: t.start_date)
        elif sort_by == "Priority":
            priority_order = {p: i for i, p in enumerate(TaskPriority)}
            tasks.sort(key=lambda t: priority_order[t.priority], reverse=True)
        elif sort_by == "Status":
            tasks.sort(key=lambda t: t.status.value)
        else:
            tasks.sort(key=lambda t: t.name)

        # Display tasks
        for idx, task in enumerate(tasks):
            with st.expander(
                f"{'⭐' if task.is_milestone else '📌'} {task.name} "
                f"({task.status.value.replace('_', ' ').title()})"
            ):
                self._render_task_editor(task, idx, state)

    def _render_task_editor(self, task: Task, idx: int, state: EditorState):
        """Render task editor"""
        col1, col2 = st.columns(2)

        with col1:
            # Task name
            new_name = st.text_input(
                "Task Name",
                value=task.name,
                key=f"{self.editor_id}_task_{task.id}_name",
            )
            if new_name != task.name:
                task.name = new_name
                self._update_task(task, state)

            # Start date
            new_start = st.date_input(
                "Start Date",
                value=task.start_date.date(),
                key=f"{self.editor_id}_task_{task.id}_start",
            )
            new_start_dt = datetime.combine(new_start, datetime.min.time())
            if new_start_dt != task.start_date:
                task.start_date = new_start_dt
                self._update_task(task, state)

            # Status
            status_idx = list(TaskStatus).index(task.status)
            new_status = st.selectbox(
                "Status",
                options=[s.value.replace("_", " ").title() for s in TaskStatus],
                index=status_idx,
                key=f"{self.editor_id}_task_{task.id}_status",
            )
            new_status_enum = TaskStatus(new_status.lower().replace(" ", "_"))
            if new_status_enum != task.status:
                task.status = new_status_enum
                self._update_task(task, state)

        with col2:
            # Duration
            duration_days = st.number_input(
                "Duration (days)",
                min_value=1,
                value=(task.end_date - task.start_date).days,
                key=f"{self.editor_id}_task_{task.id}_duration",
            )
            new_end = task.start_date + timedelta(days=duration_days)
            if new_end != task.end_date:
                task.end_date = new_end
                self._update_task(task, state)

            # Priority
            priority_idx = list(TaskPriority).index(task.priority)
            new_priority = st.selectbox(
                "Priority",
                options=[p.value.title() for p in TaskPriority],
                index=priority_idx,
                key=f"{self.editor_id}_task_{task.id}_priority",
            )
            new_priority_enum = TaskPriority(new_priority.lower())
            if new_priority_enum != task.priority:
                task.priority = new_priority_enum
                self._update_task(task, state)

            # Progress
            new_progress = st.slider(
                "Progress %",
                min_value=0,
                max_value=100,
                value=int(task.progress * 100),
                key=f"{self.editor_id}_task_{task.id}_progress",
            )
            if new_progress / 100.0 != task.progress:
                task.progress = new_progress / 100.0
                self._update_task(task, state)

        # Description
        new_desc = st.text_area(
            "Description",
            value=task.description,
            key=f"{self.editor_id}_task_{task.id}_desc",
            height=100,
        )
        if new_desc != task.description:
            task.description = new_desc
            self._update_task(task, state)

        # Dependencies
        st.markdown("**Dependencies:**")
        all_tasks = self.get_tasks()
        available_tasks = [t for t in all_tasks if t.id != task.id]

        if available_tasks:
            dep_options = [f"{t.id}: {t.name}" for t in available_tasks]
            selected_deps = st.multiselect(
                "Depends on",
                options=dep_options,
                default=[
                    f"{t.id}: {t.name}"
                    for t in available_tasks
                    if t.id in task.dependencies
                ],
                key=f"{self.editor_id}_task_{task.id}_deps",
            )

            new_deps = [d.split(":")[0] for d in selected_deps]
            if set(new_deps) != set(task.dependencies):
                task.dependencies = new_deps
                self._update_task(task, state)

        # Resources
        st.markdown("**Resources:**")
        resources = self.get_resources()

        if resources:
            resource_options = [f"{r.id}: {r.name}" for r in resources]
            selected_resources = st.multiselect(
                "Assigned to",
                options=resource_options,
                default=[
                    f"{r.id}: {r.name}"
                    for r in resources
                    if r.id in task.resources
                ],
                key=f"{self.editor_id}_task_{task.id}_resources",
            )

            new_resources = [r.split(":")[0] for r in selected_resources]
            if set(new_resources) != set(task.resources):
                task.resources = new_resources
                self._update_task(task, state)

        # Milestone
        new_milestone = st.checkbox(
            "Milestone",
            value=task.is_milestone,
            key=f"{self.editor_id}_task_{task.id}_milestone",
        )
        if new_milestone != task.is_milestone:
            task.is_milestone = new_milestone
            self._update_task(task, state)

        # Actions
        action_cols = st.columns(3)

        with action_cols[0]:
            if st.button("📋 Duplicate", key=f"{self.editor_id}_dup_{task.id}"):
                self._duplicate_task(task, state)

        with action_cols[1]:
            if st.button("🗑️ Delete", key=f"{self.editor_id}_del_{task.id}"):
                self._delete_task(task, state)

    def _render_sidebar(self, state: EditorState):
        """Render sidebar"""
        st.markdown("#### Statistics")

        tasks = self.get_tasks()

        # Task statistics
        total_tasks = len(tasks)
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
        blocked = sum(1 for t in tasks if t.status == TaskStatus.BLOCKED)

        st.metric("Total Tasks", total_tasks)
        st.metric("Completed", completed)
        st.metric("In Progress", in_progress)
        if blocked > 0:
            st.metric("⚠️ Blocked", blocked)

        # Progress
        if tasks:
            overall_progress = sum(t.progress for t in tasks) / len(tasks)
            st.metric("Overall Progress", f"{int(overall_progress * 100)}%")

        st.markdown("---")
        st.markdown("#### Resources")

        resources = self.get_resources()
        st.metric("Total Resources", len(resources))

        if resources:
            for resource in resources:
                allocated_tasks = [
                    t for t in tasks if resource.id in t.resources
                ]
                st.text(f"{resource.name}: {len(allocated_tasks)} task(s)")

        st.markdown("---")
        st.markdown("#### Critical Path")

        if st.button("Calculate", use_container_width=True):
            self._show_critical_path(tasks)

    def _add_task_dialog(self, state: EditorState):
        """Add task dialog"""
        st.info("➕ Add New Task")

        with st.form(f"{self.editor_id}_add_task_form"):
            task_name = st.text_input("Task Name", value="New Task")

            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=datetime.now().date())
            with col2:
                duration = st.number_input("Duration (days)", min_value=1, value=7)

            priority = st.selectbox(
                "Priority",
                options=[p.value.title() for p in TaskPriority],
            )

            is_milestone = st.checkbox("Milestone")

            submitted = st.form_submit_button("Add Task")

            if submitted and task_name:
                self._add_task(
                    name=task_name,
                    start_date=datetime.combine(start_date, datetime.min.time()),
                    duration=duration,
                    priority=TaskPriority(priority.lower()),
                    is_milestone=is_milestone,
                    state=state,
                )

    def _add_resource_dialog(self, state: EditorState):
        """Add resource dialog"""
        st.info("👤 Add New Resource")

        with st.form(f"{self.editor_id}_add_resource_form"):
            resource_name = st.text_input("Name", value="New Resource")
            role = st.text_input("Role", value="Team Member")
            availability = st.slider("Availability %", 0, 100, 100)

            submitted = st.form_submit_button("Add Resource")

            if submitted and resource_name:
                self._add_resource(
                    name=resource_name,
                    role=role,
                    availability=availability / 100.0,
                    state=state,
                )

    def _add_task(
        self,
        name: str,
        start_date: datetime,
        duration: int,
        priority: TaskPriority,
        is_milestone: bool,
        state: EditorState,
    ):
        """Add new task"""
        tasks = state.content.get("tasks", [])

        new_task = Task(
            id=f"task_{uuid.uuid4().hex[:8]}",
            name=name,
            start_date=start_date,
            end_date=start_date + timedelta(days=duration),
            priority=priority,
            is_milestone=is_milestone,
        )

        tasks.append(new_task.to_dict())
        state.content["tasks"] = tasks
        state.mark_modified()

        st.success(f"Added task: {name}")
        st.rerun()

    def _add_resource(
        self,
        name: str,
        role: str,
        availability: float,
        state: EditorState,
    ):
        """Add new resource"""
        resources = state.content.get("resources", [])

        new_resource = Resource(
            id=f"resource_{uuid.uuid4().hex[:8]}",
            name=name,
            role=role,
            availability=availability,
        )

        resources.append(new_resource.to_dict())
        state.content["resources"] = resources
        state.mark_modified()

        st.success(f"Added resource: {name}")
        st.rerun()

    def _update_task(self, task: Task, state: EditorState):
        """Update task in state"""
        tasks = state.content.get("tasks", [])

        for i, t in enumerate(tasks):
            if t["id"] == task.id:
                tasks[i] = task.to_dict()
                break

        state.content["tasks"] = tasks
        state.mark_modified()

    def _delete_task(self, task: Task, state: EditorState):
        """Delete task"""
        tasks = state.content.get("tasks", [])
        tasks = [t for t in tasks if t["id"] != task.id]

        # Remove from dependencies
        for t in tasks:
            if task.id in t.get("dependencies", []):
                t["dependencies"].remove(task.id)

        state.content["tasks"] = tasks
        state.mark_modified()

        st.success("Task deleted")
        st.rerun()

    def _duplicate_task(self, task: Task, state: EditorState):
        """Duplicate task"""
        new_task = Task(
            id=f"task_{uuid.uuid4().hex[:8]}",
            name=f"{task.name} (Copy)",
            start_date=task.end_date,
            end_date=task.end_date + task.duration,
            status=TaskStatus.NOT_STARTED,
            priority=task.priority,
            progress=0.0,
            dependencies=[],
            resources=task.resources.copy(),
            is_milestone=task.is_milestone,
            description=task.description,
        )

        tasks = state.content.get("tasks", [])
        tasks.append(new_task.to_dict())
        state.content["tasks"] = tasks
        state.mark_modified()

        st.success("Task duplicated")
        st.rerun()

    def _show_critical_path(self, tasks: List[Task]):
        """Show critical path"""
        if not tasks:
            st.warning("No tasks to analyze")
            return

        # Simple critical path: tasks with dependencies
        critical = [t for t in tasks if t.is_on_critical_path(tasks)]

        if critical:
            st.success(f"Critical path contains {len(critical)} task(s):")
            for task in critical:
                st.text(f"• {task.name} ({task.duration.days} days)")
        else:
            st.info("No critical path identified")

    def _export_project(self, state: EditorState):
        """Export project"""
        tasks = self.get_tasks()
        resources = self.get_resources()

        # Create export data
        export_data = {
            "project": state.content.get("name"),
            "tasks": [t.to_dict() for t in tasks],
            "resources": [r.to_dict() for r in resources],
            "exported_at": datetime.now().isoformat(),
        }

        # Convert to JSON
        json_data = json.dumps(export_data, indent=2)

        st.download_button(
            label="Download JSON",
            data=json_data,
            file_name=f"{state.content.get('name', 'project')}_gantt.json",
            mime="application/json",
        )


# Export
__all__ = ["GanttEditor", "Task", "Resource", "TaskStatus", "TaskPriority"]
