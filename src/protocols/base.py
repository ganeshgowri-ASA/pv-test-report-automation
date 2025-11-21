"""
Base Protocol Framework
Foundation for all IEC protocol implementations
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PassFailCriteria(Enum):
    """Test pass/fail result"""
    PASS = "pass"
    FAIL = "fail"
    CONDITIONAL_PASS = "conditional_pass"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class TestParameter:
    """Test parameter specification"""
    name: str
    unit: str
    nominal_value: Optional[float] = None
    tolerance: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    description: Optional[str] = None


@dataclass
class TestResult:
    """Individual test result"""
    test_name: str
    test_number: str
    status: TestStatus
    result: Optional[PassFailCriteria] = None
    measured_value: Optional[float] = None
    expected_value: Optional[float] = None
    unit: Optional[str] = None
    deviation: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    operator: Optional[str] = None
    equipment_id: Optional[str] = None
    raw_data: Optional[Dict] = None
    notes: Optional[str] = None
    compliance_met: bool = True

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'test_name': self.test_name,
            'test_number': self.test_number,
            'status': self.status.value,
            'result': self.result.value if self.result else None,
            'measured_value': self.measured_value,
            'expected_value': self.expected_value,
            'unit': self.unit,
            'deviation': self.deviation,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'operator': self.operator,
            'equipment_id': self.equipment_id,
            'notes': self.notes,
            'compliance_met': self.compliance_met,
        }


@dataclass
class TestSequence:
    """Test sequence definition"""
    sequence_number: int
    name: str
    description: str
    required_tests: List[str]
    optional_tests: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    estimated_duration_hours: float = 0.0


@dataclass
class SampleSpecification:
    """Sample/module specification"""
    sample_id: str
    manufacturer: str
    model: str
    serial_number: str
    module_type: str  # Mono-Si, Poly-Si, Thin-Film, etc.
    rated_power: float
    voltage_max: float
    current_max: float
    dimensions: Dict[str, float]
    weight: float
    additional_specs: Dict[str, Any] = field(default_factory=dict)


class ProtocolBase(ABC):
    """Base class for all IEC protocols"""

    def __init__(self):
        self.protocol_name: str = ""
        self.protocol_version: str = ""
        self.full_title: str = ""
        self.description: str = ""
        self.test_sequences: List[TestSequence] = []
        self.required_equipment: List[str] = []
        self.safety_requirements: List[str] = []
        self.environmental_conditions: Dict[str, Any] = {}

    @abstractmethod
    def get_test_matrix(self) -> Dict[str, Any]:
        """Get complete test matrix for this protocol"""
        pass

    @abstractmethod
    def validate_sample(self, sample: SampleSpecification) -> tuple[bool, str]:
        """Validate if sample is suitable for this protocol"""
        pass

    @abstractmethod
    def get_acceptance_criteria(self, test_name: str) -> Dict[str, Any]:
        """Get acceptance criteria for specific test"""
        pass

    def get_test_sequences(self) -> List[TestSequence]:
        """Get ordered test sequences"""
        return self.test_sequences

    def get_required_equipment(self) -> List[str]:
        """Get list of required equipment"""
        return self.required_equipment

    def estimate_total_duration(self) -> float:
        """Estimate total test duration in hours"""
        return sum(seq.estimated_duration_hours for seq in self.test_sequences)

    def generate_test_plan(self, sample: SampleSpecification) -> Dict[str, Any]:
        """Generate comprehensive test plan"""
        return {
            'protocol': self.protocol_name,
            'version': self.protocol_version,
            'sample': {
                'id': sample.sample_id,
                'manufacturer': sample.manufacturer,
                'model': sample.model,
            },
            'sequences': [
                {
                    'number': seq.sequence_number,
                    'name': seq.name,
                    'duration_hours': seq.estimated_duration_hours,
                    'tests': seq.required_tests,
                }
                for seq in self.test_sequences
            ],
            'equipment': self.required_equipment,
            'estimated_total_hours': self.estimate_total_duration(),
        }

    def evaluate_results(self, results: List[TestResult]) -> Dict[str, Any]:
        """Evaluate overall test results against protocol requirements"""
        total_tests = len(results)
        passed_tests = len([r for r in results if r.result == PassFailCriteria.PASS])
        failed_tests = len([r for r in results if r.result == PassFailCriteria.FAIL])
        conditional_tests = len([r for r in results if r.result == PassFailCriteria.CONDITIONAL_PASS])

        overall_compliance = failed_tests == 0 and all(r.compliance_met for r in results)

        return {
            'total_tests': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'conditional': conditional_tests,
            'pass_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'overall_compliance': overall_compliance,
            'protocol': self.protocol_name,
            'certification_recommended': overall_compliance,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(protocol={self.protocol_name}, version={self.protocol_version})>"
