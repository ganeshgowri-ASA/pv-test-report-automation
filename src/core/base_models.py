"""
Base models for PV test report automation system.
Provides foundational classes for all test blocks.

Compliant with:
- ISO 17025 (Testing and calibration laboratory competence)
- ISO 9001 (Quality management systems)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


class TestBlockStatus(Enum):
    """Test block lifecycle states for tracking execution progress."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class TestParameter:
    """
    Represents a single test parameter with validation capabilities.

    Attributes:
        name: Parameter name
        value: Parameter value
        unit: Unit of measurement (optional)
        tolerance: Dictionary with 'min' and 'max' tolerance bounds
        metadata: Additional parameter metadata
    """
    name: str
    value: Any
    unit: Optional[str] = None
    tolerance: Optional[Dict[str, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_within_tolerance(self) -> bool:
        """Check if value is within specified tolerance range."""
        if not self.tolerance or not isinstance(self.value, (int, float)):
            return True
        min_val = self.tolerance.get("min", float("-inf"))
        max_val = self.tolerance.get("max", float("inf"))
        return min_val <= self.value <= max_val


@dataclass
class TestResult:
    """
    Represents a test measurement result with compliance checking.

    Attributes:
        passed: Whether the test passed specification limits
        measurement_value: The measured value
        specification_limit_min: Minimum acceptable value (optional)
        specification_limit_max: Maximum acceptable value (optional)
        unit: Unit of measurement
        comments: Additional notes or observations
        timestamp: When the measurement was taken
        raw_data: Dictionary containing raw measurement data
    """
    passed: bool
    measurement_value: float
    specification_limit_min: Optional[float] = None
    specification_limit_max: Optional[float] = None
    unit: Optional[str] = None
    comments: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    raw_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "passed": self.passed,
            "measurement_value": self.measurement_value,
            "specification_limit_min": self.specification_limit_min,
            "specification_limit_max": self.specification_limit_max,
            "unit": self.unit,
            "comments": self.comments,
            "timestamp": self.timestamp.isoformat(),
            "raw_data": self.raw_data
        }


@dataclass
class EquipmentInfo:
    """
    Equipment tracking for ISO 17025 traceability requirements.

    Attributes:
        equipment_id: Unique equipment identifier
        name: Equipment name/description
        calibration_date: Last calibration date
        calibration_due_date: Next calibration due date
        calibration_certificate: Certificate number
        uncertainty: Measurement uncertainty
    """
    equipment_id: str
    name: str
    calibration_date: datetime
    calibration_due_date: datetime
    calibration_certificate: str = ""
    uncertainty: Optional[str] = None

    def is_calibration_valid(self) -> bool:
        """Check if equipment calibration is still valid."""
        return datetime.now() <= self.calibration_due_date


class BaseTestBlock(ABC):
    """
    Abstract base class for all test blocks.

    Provides common functionality for:
    - Parameter validation
    - Result tracking
    - Equipment traceability
    - ISO 17025 compliance
    - Execution lifecycle management
    """

    def __init__(
        self,
        block_id: str,
        standard: str,
        description: str,
        operator: str,
        sample_info: Dict[str, Any]
    ):
        """
        Initialize base test block.

        Args:
            block_id: Unique identifier for this test block instance
            standard: Standard being followed (e.g., "IEC 61215")
            description: Test block description
            operator: Name of test operator
            sample_info: Dictionary containing sample/module information
        """
        self.block_id = block_id
        self.standard = standard
        self.description = description
        self.operator = operator
        self.sample_info = sample_info
        self.status = TestBlockStatus.NOT_STARTED
        self.results: List[TestResult] = []
        self.parameters: Dict[str, TestParameter] = {}
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.equipment_used: List[EquipmentInfo] = []
        self.notes: str = ""
        self.environmental_conditions: Dict[str, Any] = {}

    @abstractmethod
    def validate_parameters(self) -> bool:
        """
        Validate test parameters before execution.

        Returns:
            True if all parameters are valid, False otherwise
        """
        pass

    @abstractmethod
    def execute(self) -> List[TestResult]:
        """
        Execute the test block.

        Returns:
            List of test results
        """
        pass

    @abstractmethod
    def post_process(self) -> None:
        """Post-process results and generate reports."""
        pass

    def get_summary(self) -> Dict[str, Any]:
        """
        Get test block summary.

        Returns:
            Dictionary containing test summary information
        """
        return {
            "block_id": self.block_id,
            "standard": self.standard,
            "description": self.description,
            "status": self.status.value,
            "operator": self.operator,
            "total_results": len(self.results),
            "passed": sum(1 for r in self.results if r.passed),
            "failed": sum(1 for r in self.results if not r.passed),
            "duration_seconds": self._calculate_duration(),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None
        }

    def _calculate_duration(self) -> Optional[float]:
        """Calculate test duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def validate_equipment_calibration(self) -> bool:
        """
        Validate all equipment calibrations are current.

        Returns:
            True if all equipment is properly calibrated, False otherwise
        """
        for equipment in self.equipment_used:
            if not equipment.is_calibration_valid():
                self.notes += f"Equipment {equipment.equipment_id} calibration expired\n"
                return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert test block to dictionary for serialization.

        Returns:
            Dictionary containing all test block data
        """
        return {
            "block_id": self.block_id,
            "standard": self.standard,
            "description": self.description,
            "operator": self.operator,
            "sample_info": self.sample_info,
            "status": self.status.value,
            "results": [r.to_dict() for r in self.results],
            "parameters": {
                k: {
                    "name": v.name,
                    "value": v.value,
                    "unit": v.unit,
                    "tolerance": v.tolerance,
                    "metadata": v.metadata
                }
                for k, v in self.parameters.items()
            },
            "equipment_used": [
                {
                    "equipment_id": eq.equipment_id,
                    "name": eq.name,
                    "calibration_date": eq.calibration_date.isoformat(),
                    "calibration_due_date": eq.calibration_due_date.isoformat(),
                    "calibration_certificate": eq.calibration_certificate,
                    "uncertainty": eq.uncertainty
                }
                for eq in self.equipment_used
            ],
            "notes": self.notes,
            "environmental_conditions": self.environmental_conditions,
            "summary": self.get_summary()
        }
