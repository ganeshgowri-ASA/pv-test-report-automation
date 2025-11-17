"""
Test sequence management for protocol execution.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from enum import Enum

from .test_result import TestResult, ModuleUnderTest, ComplianceStatus


class SequenceStatus(Enum):
    """Test sequence execution status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABORTED = "aborted"
    FAILED = "failed"


@dataclass
class TestStep:
    """Individual step in a test sequence."""
    step_id: str
    test_id: str
    test_name: str
    description: str
    clause_reference: str

    # Execution order
    sequence_number: int

    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    skip_conditions: List[Callable[[List[TestResult]], bool]] = field(default_factory=list)

    # Conditional execution based on module type
    module_types: Optional[List[str]] = None  # None means all types

    # Test result
    result: Optional[TestResult] = None

    # Status
    is_completed: bool = False
    is_skipped: bool = False
    skip_reason: Optional[str] = None

    def can_execute(self, completed_steps: List['TestStep'], module_type: str) -> tuple[bool, str]:
        """
        Check if this step can be executed.

        Args:
            completed_steps: List of already completed steps
            module_type: Type of module being tested

        Returns:
            Tuple of (can_execute, reason)
        """
        # Check module type compatibility
        if self.module_types and module_type not in self.module_types:
            return False, f"Not applicable for {module_type} modules"

        # Check dependencies
        completed_step_ids = {step.step_id for step in completed_steps}
        for dependency in self.depends_on:
            if dependency not in completed_step_ids:
                return False, f"Waiting for {dependency} to complete"

        # Check skip conditions
        completed_results = [step.result for step in completed_steps if step.result]
        for skip_condition in self.skip_conditions:
            if skip_condition(completed_results):
                return False, "Skip condition met"

        return True, "Ready to execute"

    def mark_completed(self, result: TestResult) -> None:
        """Mark step as completed with result."""
        self.result = result
        self.is_completed = True

    def mark_skipped(self, reason: str) -> None:
        """Mark step as skipped."""
        self.is_skipped = True
        self.skip_reason = reason


@dataclass
class TestSequence:
    """Test sequence for a protocol."""
    sequence_id: str
    sequence_name: str
    protocol_name: str
    protocol_version: str

    # Module information
    module: ModuleUnderTest

    # Test steps
    steps: List[TestStep] = field(default_factory=list)

    # Sequence execution
    status: SequenceStatus = SequenceStatus.NOT_STARTED
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # Overall compliance
    overall_compliance: ComplianceStatus = ComplianceStatus.PENDING

    # Laboratory information
    laboratory_name: Optional[str] = None
    laboratory_accreditation: Optional[str] = None
    test_report_number: Optional[str] = None

    # Personnel
    test_engineer: Optional[str] = None
    reviewer: Optional[str] = None
    approver: Optional[str] = None

    # Documentation
    notes: Optional[str] = None
    deviations: List[str] = field(default_factory=list)

    def add_step(self, step: TestStep) -> None:
        """Add test step to sequence."""
        self.steps.append(step)
        # Sort steps by sequence number
        self.steps.sort(key=lambda s: s.sequence_number)

    def get_next_step(self) -> Optional[TestStep]:
        """Get next executable test step."""
        completed_steps = [s for s in self.steps if s.is_completed or s.is_skipped]

        for step in self.steps:
            if step.is_completed or step.is_skipped:
                continue

            can_execute, reason = step.can_execute(completed_steps, self.module.module_type)
            if can_execute:
                return step

        return None

    def get_completed_steps(self) -> List[TestStep]:
        """Get list of completed steps."""
        return [s for s in self.steps if s.is_completed]

    def get_skipped_steps(self) -> List[TestStep]:
        """Get list of skipped steps."""
        return [s for s in self.steps if s.is_skipped]

    def get_pending_steps(self) -> List[TestStep]:
        """Get list of pending steps."""
        return [s for s in self.steps if not s.is_completed and not s.is_skipped]

    def evaluate_overall_compliance(self) -> None:
        """Evaluate overall test sequence compliance."""
        completed_results = [s.result for s in self.steps if s.result]

        if not completed_results:
            self.overall_compliance = ComplianceStatus.PENDING
            return

        # Check if any test failed
        failed_results = [
            r for r in completed_results
            if r.compliance_status == ComplianceStatus.FAIL
        ]

        if failed_results:
            self.overall_compliance = ComplianceStatus.FAIL
        else:
            # Check if all required tests passed
            pending_required = [
                s for s in self.steps
                if not s.is_completed and not s.is_skipped
            ]

            if pending_required:
                self.overall_compliance = ComplianceStatus.PENDING
            else:
                self.overall_compliance = ComplianceStatus.PASS

    def get_progress(self) -> Dict[str, Any]:
        """Get sequence progress information."""
        total_steps = len(self.steps)
        completed = len(self.get_completed_steps())
        skipped = len(self.get_skipped_steps())
        pending = len(self.get_pending_steps())

        return {
            "total_steps": total_steps,
            "completed": completed,
            "skipped": skipped,
            "pending": pending,
            "progress_percent": (completed / total_steps * 100) if total_steps > 0 else 0,
        }

    def get_duration(self) -> Optional[float]:
        """Get total sequence duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert sequence to dictionary."""
        return {
            "sequence_id": self.sequence_id,
            "sequence_name": self.sequence_name,
            "protocol_name": self.protocol_name,
            "protocol_version": self.protocol_version,
            "module": self.module.to_dict(),
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.get_duration(),
            "overall_compliance": self.overall_compliance.value,
            "progress": self.get_progress(),
            "steps": [
                {
                    "step_id": s.step_id,
                    "test_name": s.test_name,
                    "is_completed": s.is_completed,
                    "is_skipped": s.is_skipped,
                    "compliance_status": s.result.compliance_status.value if s.result else "pending",
                }
                for s in self.steps
            ],
            "laboratory_name": self.laboratory_name,
            "test_report_number": self.test_report_number,
            "test_engineer": self.test_engineer,
            "reviewer": self.reviewer,
            "notes": self.notes,
        }
