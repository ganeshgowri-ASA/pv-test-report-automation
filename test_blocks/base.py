"""
Base models and classes for PV test blocks
ISO 17025 compliant test framework
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class Standard(Enum):
    """Applicable test standards"""
    IEC_61215 = "IEC 61215"
    IEC_61730 = "IEC 61730"
    IEC_61853 = "IEC 61853"
    IEC_62716 = "IEC 62716"
    IEC_61701 = "IEC 61701"
    IEC_62804 = "IEC 62804"
    IEC_60904 = "IEC 60904"
    IEC_62759 = "IEC 62759"
    ISO_17025 = "ISO 17025"
    ISO_9001 = "ISO 9001"


@dataclass
class TestMetadata:
    """ISO 17025 compliant test metadata"""
    test_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    operator: Optional[str] = None
    reviewer: Optional[str] = None
    equipment_id: Optional[str] = None
    calibration_date: Optional[datetime] = None
    environmental_conditions: Dict[str, Any] = field(default_factory=dict)
    standards: List[Standard] = field(default_factory=list)
    traceability_id: Optional[str] = None


@dataclass
class TestResult:
    """Base test result model"""
    test_id: int
    module_id: str
    test_name: str
    status: TestStatus
    pass_status: bool
    metadata: TestMetadata
    measurements: Dict[str, Any] = field(default_factory=dict)
    notes: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization"""
        return {
            'test_id': self.test_id,
            'module_id': self.module_id,
            'test_name': self.test_name,
            'status': self.status.value,
            'pass_status': self.pass_status,
            'metadata': {
                'test_id': self.metadata.test_id,
                'timestamp': self.metadata.timestamp.isoformat(),
                'operator': self.metadata.operator,
                'reviewer': self.metadata.reviewer,
                'equipment_id': self.metadata.equipment_id,
                'calibration_date': self.metadata.calibration_date.isoformat() if self.metadata.calibration_date else None,
                'environmental_conditions': self.metadata.environmental_conditions,
                'standards': [s.value for s in self.metadata.standards],
                'traceability_id': self.metadata.traceability_id,
            },
            'measurements': self.measurements,
            'notes': self.notes,
            'error_message': self.error_message,
        }


class BaseTestModel:
    """Base class for all test models"""

    def __init__(self, module_id: str, test_id: int, operator: Optional[str] = None):
        """
        Initialize base test model

        Args:
            module_id: Unique module identifier
            test_id: Unique test identifier
            operator: Test operator name
        """
        self.module_id = module_id
        self.test_id = test_id
        self.metadata = TestMetadata(
            test_id=f"{module_id}-{test_id}",
            operator=operator,
            standards=[Standard.ISO_17025]
        )

    def validate_measurement(self, value: float, min_val: float, max_val: float,
                           name: str = "measurement") -> bool:
        """
        Validate measurement against limits

        Args:
            value: Measured value
            min_val: Minimum acceptable value
            max_val: Maximum acceptable value
            name: Measurement name for logging

        Returns:
            True if within limits, False otherwise
        """
        if value < min_val or value > max_val:
            print(f"WARNING: {name} = {value} is outside limits [{min_val}, {max_val}]")
            return False
        return True

    def set_environmental_conditions(self, temperature: float, humidity: float,
                                    pressure: Optional[float] = None) -> None:
        """
        Set environmental test conditions

        Args:
            temperature: Ambient temperature (°C)
            humidity: Relative humidity (%)
            pressure: Atmospheric pressure (hPa), optional
        """
        self.metadata.environmental_conditions = {
            'temperature_c': temperature,
            'humidity_percent': humidity,
        }
        if pressure is not None:
            self.metadata.environmental_conditions['pressure_hpa'] = pressure

    def set_equipment(self, equipment_id: str, calibration_date: datetime) -> None:
        """
        Set test equipment information

        Args:
            equipment_id: Unique equipment identifier
            calibration_date: Last calibration date
        """
        self.metadata.equipment_id = equipment_id
        self.metadata.calibration_date = calibration_date
