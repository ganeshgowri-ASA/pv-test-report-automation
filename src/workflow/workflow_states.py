"""
Workflow state machine implementation.

This module provides a robust state machine for workflow management with:
- State transition validation
- Event-driven state changes
- Automatic audit trail generation
- Configurable transition rules
- Event hooks and callbacks

Implements ISO 17025 compliant state tracking.
"""

from typing import Dict, List, Set, Optional, Callable, Any
from datetime import datetime
from enum import Enum
import logging
from dataclasses import dataclass, field

from .models import WorkflowStatus, WorkflowInstance, StateTransition


logger = logging.getLogger(__name__)


class WorkflowEvent(Enum):
    """Workflow state transition events."""
    SUBMIT = "submit"
    START_REVIEW = "start_review"
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"
    RESUBMIT = "resubmit"
    CANCEL = "cancel"
    ESCALATE = "escalate"
    COMPLETE = "complete"
    DELEGATE = "delegate"
    TIMEOUT = "timeout"


@dataclass
class StateTransitionRule:
    """
    Defines a valid state transition rule.

    Attributes:
        from_state: Source state
        to_state: Target state
        event: Triggering event
        condition: Optional condition function that must return True
        pre_action: Optional action to execute before transition
        post_action: Optional action to execute after transition
        requires_approval: Whether this transition requires approval
        requires_comment: Whether a comment is required for this transition
    """
    from_state: WorkflowStatus
    to_state: WorkflowStatus
    event: WorkflowEvent
    condition: Optional[Callable[[WorkflowInstance, Dict[str, Any]], bool]] = None
    pre_action: Optional[Callable[[WorkflowInstance, Dict[str, Any]], None]] = None
    post_action: Optional[Callable[[WorkflowInstance, Dict[str, Any]], None]] = None
    requires_approval: bool = False
    requires_comment: bool = False
    allowed_roles: Set[str] = field(default_factory=set)

    def can_transition(self, workflow: WorkflowInstance, context: Dict[str, Any]) -> bool:
        """
        Check if transition is allowed.

        Args:
            workflow: Workflow instance
            context: Transition context including user, reason, etc.

        Returns:
            True if transition is allowed, False otherwise
        """
        # Check role if specified
        if self.allowed_roles:
            user_role = context.get("user_role")
            if user_role not in self.allowed_roles:
                logger.warning(
                    f"User role '{user_role}' not in allowed roles {self.allowed_roles} "
                    f"for transition {self.from_state} -> {self.to_state}"
                )
                return False

        # Check custom condition if specified
        if self.condition:
            try:
                return self.condition(workflow, context)
            except Exception as e:
                logger.error(f"Condition check failed for transition: {e}")
                return False

        return True


class WorkflowStateMachine:
    """
    State machine for workflow management.

    Manages workflow state transitions with validation, audit trail,
    and event hooks. Supports configurable transition rules and
    custom business logic.
    """

    # Default transition rules for standard workflow
    DEFAULT_TRANSITIONS = [
        # From DRAFT
        StateTransitionRule(
            WorkflowStatus.DRAFT,
            WorkflowStatus.PENDING,
            WorkflowEvent.SUBMIT,
            requires_comment=False
        ),
        StateTransitionRule(
            WorkflowStatus.DRAFT,
            WorkflowStatus.CANCELLED,
            WorkflowEvent.CANCEL,
            requires_comment=True
        ),

        # From PENDING
        StateTransitionRule(
            WorkflowStatus.PENDING,
            WorkflowStatus.IN_PROGRESS,
            WorkflowEvent.START_REVIEW,
            allowed_roles={"reviewer", "approver", "admin"}
        ),
        StateTransitionRule(
            WorkflowStatus.PENDING,
            WorkflowStatus.CANCELLED,
            WorkflowEvent.CANCEL,
            requires_comment=True
        ),
        StateTransitionRule(
            WorkflowStatus.PENDING,
            WorkflowStatus.ESCALATED,
            WorkflowEvent.ESCALATE,
            requires_comment=True,
            allowed_roles={"admin", "manager"}
        ),

        # From IN_PROGRESS
        StateTransitionRule(
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.APPROVED,
            WorkflowEvent.APPROVE,
            requires_approval=True,
            allowed_roles={"approver", "admin"}
        ),
        StateTransitionRule(
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.REJECTED,
            WorkflowEvent.REJECT,
            requires_comment=True,
            allowed_roles={"approver", "admin"}
        ),
        StateTransitionRule(
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.PENDING,
            WorkflowEvent.REQUEST_CHANGES,
            requires_comment=True,
            allowed_roles={"reviewer", "approver", "admin"}
        ),
        StateTransitionRule(
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.ESCALATED,
            WorkflowEvent.ESCALATE,
            requires_comment=True,
            allowed_roles={"admin", "manager"}
        ),
        StateTransitionRule(
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.CANCELLED,
            WorkflowEvent.CANCEL,
            requires_comment=True,
            allowed_roles={"admin"}
        ),

        # From APPROVED
        StateTransitionRule(
            WorkflowStatus.APPROVED,
            WorkflowStatus.COMPLETED,
            WorkflowEvent.COMPLETE,
            allowed_roles={"system", "admin"}
        ),

        # From REJECTED
        StateTransitionRule(
            WorkflowStatus.REJECTED,
            WorkflowStatus.DRAFT,
            WorkflowEvent.RESUBMIT,
            requires_comment=False
        ),

        # From ESCALATED
        StateTransitionRule(
            WorkflowStatus.ESCALATED,
            WorkflowStatus.IN_PROGRESS,
            WorkflowEvent.START_REVIEW,
            allowed_roles={"admin", "manager"}
        ),
        StateTransitionRule(
            WorkflowStatus.ESCALATED,
            WorkflowStatus.APPROVED,
            WorkflowEvent.APPROVE,
            requires_approval=True,
            allowed_roles={"admin", "manager"}
        ),
        StateTransitionRule(
            WorkflowStatus.ESCALATED,
            WorkflowStatus.REJECTED,
            WorkflowEvent.REJECT,
            requires_comment=True,
            allowed_roles={"admin", "manager"}
        ),
    ]

    def __init__(self, custom_transitions: Optional[List[StateTransitionRule]] = None):
        """
        Initialize state machine.

        Args:
            custom_transitions: Optional custom transition rules (extends defaults)
        """
        self.transitions: Dict[tuple, StateTransitionRule] = {}
        self.event_hooks: Dict[str, List[Callable]] = {
            "before_transition": [],
            "after_transition": [],
            "on_enter": {},
            "on_exit": {},
        }

        # Load default transitions
        for rule in self.DEFAULT_TRANSITIONS:
            self._add_transition(rule)

        # Add custom transitions
        if custom_transitions:
            for rule in custom_transitions:
                self._add_transition(rule)

    def _add_transition(self, rule: StateTransitionRule):
        """Add a transition rule to the state machine."""
        key = (rule.from_state, rule.event)
        if key in self.transitions:
            logger.warning(f"Overriding existing transition rule for {key}")
        self.transitions[key] = rule

    def can_transition(
        self,
        workflow: WorkflowInstance,
        event: WorkflowEvent,
        context: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if a transition is valid.

        Args:
            workflow: Workflow instance
            event: Triggering event
            context: Transition context

        Returns:
            Tuple of (is_valid, error_message)
        """
        context = context or {}
        current_state = workflow.status

        # Check if transition rule exists
        key = (current_state, event)
        if key not in self.transitions:
            return False, f"No transition defined from {current_state.value} on event {event.value}"

        rule = self.transitions[key]

        # Check if transition is allowed
        if not rule.can_transition(workflow, context):
            return False, f"Transition not allowed by rule conditions"

        # Check if comment is required
        if rule.requires_comment and not context.get("reason"):
            return False, "Comment/reason is required for this transition"

        # Check if approval is required
        if rule.requires_approval and not context.get("approved_by"):
            return False, "Approval is required for this transition"

        return True, None

    def transition(
        self,
        workflow: WorkflowInstance,
        event: WorkflowEvent,
        context: Optional[Dict[str, Any]] = None,
        session=None
    ) -> bool:
        """
        Execute a state transition.

        Args:
            workflow: Workflow instance
            event: Triggering event
            context: Transition context
            session: Database session for persistence

        Returns:
            True if transition successful, False otherwise

        Raises:
            ValueError: If transition is invalid
        """
        context = context or {}
        current_state = workflow.status

        # Validate transition
        can_transition, error = self.can_transition(workflow, event, context)
        if not can_transition:
            raise ValueError(f"Invalid transition: {error}")

        key = (current_state, event)
        rule = self.transitions[key]
        new_state = rule.to_state

        logger.info(
            f"Transitioning workflow {workflow.id} from {current_state.value} "
            f"to {new_state.value} via event {event.value}"
        )

        # Execute before_transition hooks
        self._execute_hooks("before_transition", workflow, current_state, new_state, context)

        # Execute on_exit hooks for current state
        if current_state.value in self.event_hooks["on_exit"]:
            self._execute_hooks(
                "on_exit",
                workflow,
                current_state,
                new_state,
                context,
                state=current_state.value
            )

        # Execute pre-action if defined
        if rule.pre_action:
            try:
                rule.pre_action(workflow, context)
            except Exception as e:
                logger.error(f"Pre-action failed for transition: {e}")
                raise

        # Update workflow state
        old_state = workflow.status
        workflow.status = new_state
        workflow.updated_at = datetime.utcnow()

        # Update timing fields
        if new_state == WorkflowStatus.IN_PROGRESS and not workflow.started_at:
            workflow.started_at = datetime.utcnow()
        elif new_state in [WorkflowStatus.COMPLETED, WorkflowStatus.CANCELLED]:
            workflow.completed_at = datetime.utcnow()
        elif new_state == WorkflowStatus.ESCALATED:
            workflow.escalated_at = datetime.utcnow()
            workflow.escalation_level = workflow.escalation_level + 1

        # Create state transition record
        if session:
            transition_record = StateTransition(
                workflow_id=workflow.id,
                from_state=old_state.value,
                to_state=new_state.value,
                event=event.value,
                triggered_by=context.get("user_id", "system"),
                reason=context.get("reason"),
                metadata=context.get("metadata", {})
            )
            session.add(transition_record)

        # Execute post-action if defined
        if rule.post_action:
            try:
                rule.post_action(workflow, context)
            except Exception as e:
                logger.error(f"Post-action failed for transition: {e}")
                # Don't raise - transition already completed

        # Execute on_enter hooks for new state
        if new_state.value in self.event_hooks["on_enter"]:
            self._execute_hooks(
                "on_enter",
                workflow,
                old_state,
                new_state,
                context,
                state=new_state.value
            )

        # Execute after_transition hooks
        self._execute_hooks("after_transition", workflow, old_state, new_state, context)

        logger.info(f"Workflow {workflow.id} successfully transitioned to {new_state.value}")
        return True

    def _execute_hooks(
        self,
        hook_type: str,
        workflow: WorkflowInstance,
        old_state: WorkflowStatus,
        new_state: WorkflowStatus,
        context: Dict[str, Any],
        state: Optional[str] = None
    ):
        """Execute registered hooks for an event."""
        if hook_type in ["on_enter", "on_exit"]:
            hooks = self.event_hooks[hook_type].get(state, [])
        else:
            hooks = self.event_hooks.get(hook_type, [])

        for hook in hooks:
            try:
                hook(workflow, old_state, new_state, context)
            except Exception as e:
                logger.error(f"Hook execution failed ({hook_type}): {e}")

    def register_hook(
        self,
        hook_type: str,
        callback: Callable,
        state: Optional[str] = None
    ):
        """
        Register an event hook.

        Args:
            hook_type: Type of hook (before_transition, after_transition, on_enter, on_exit)
            callback: Callback function
            state: State for on_enter/on_exit hooks
        """
        if hook_type in ["on_enter", "on_exit"]:
            if not state:
                raise ValueError(f"State must be specified for {hook_type} hooks")
            if state not in self.event_hooks[hook_type]:
                self.event_hooks[hook_type][state] = []
            self.event_hooks[hook_type][state].append(callback)
        else:
            if hook_type not in self.event_hooks:
                self.event_hooks[hook_type] = []
            self.event_hooks[hook_type].append(callback)

    def get_available_events(self, workflow: WorkflowInstance) -> List[WorkflowEvent]:
        """
        Get list of available events for current workflow state.

        Args:
            workflow: Workflow instance

        Returns:
            List of available events
        """
        current_state = workflow.status
        available = []

        for (from_state, event), rule in self.transitions.items():
            if from_state == current_state:
                available.append(event)

        return available

    def get_transition_graph(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get state transition graph for visualization.

        Returns:
            Dictionary mapping states to possible transitions
        """
        graph = {}

        for (from_state, event), rule in self.transitions.items():
            state_key = from_state.value
            if state_key not in graph:
                graph[state_key] = []

            graph[state_key].append({
                "event": event.value,
                "to_state": rule.to_state.value,
                "requires_approval": rule.requires_approval,
                "requires_comment": rule.requires_comment,
                "allowed_roles": list(rule.allowed_roles) if rule.allowed_roles else None
            })

        return graph

    def validate_workflow_path(
        self,
        start_state: WorkflowStatus,
        end_state: WorkflowStatus,
        max_depth: int = 10
    ) -> Optional[List[WorkflowEvent]]:
        """
        Find a valid path from start_state to end_state.

        Args:
            start_state: Starting state
            end_state: Target state
            max_depth: Maximum path length to search

        Returns:
            List of events to reach end_state, or None if no path exists
        """
        # BFS to find shortest path
        queue = [(start_state, [])]
        visited = {start_state}

        while queue:
            current_state, path = queue.pop(0)

            if len(path) > max_depth:
                continue

            if current_state == end_state:
                return path

            for (from_state, event), rule in self.transitions.items():
                if from_state == current_state and rule.to_state not in visited:
                    visited.add(rule.to_state)
                    queue.append((rule.to_state, path + [event]))

        return None
