"""
Base Protocol Handler for PV Module Testing

This module provides the base class and data structures for all protocol handlers
used in automated PV module testing according to IEC standards.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class TestStatus(Enum):
    """Test status enumeration"""
    PASS = "PASS"
    FAIL = "FAIL"
    IN_PROGRESS = "IN_PROGRESS"
    NOT_STARTED = "NOT_STARTED"
    ABORTED = "ABORTED"


@dataclass
class TestParameter:
    """Represents a single test parameter with tolerance and criteria"""
    name: str
    value: Any
    unit: str
    tolerance: Optional[float] = None
    pass_criteria: Optional[Dict[str, Any]] = None
    description: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.name}: {self.value} {self.unit}"


@dataclass
class TestResult:
    """Represents a single test result with pass/fail status"""
    parameter_name: str
    measured_value: float
    unit: str
    status: TestStatus
    timestamp: datetime
    expected_value: Optional[float] = None
    tolerance: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.parameter_name}: {self.measured_value} {self.unit} [{self.status.value}]"


@dataclass
class EnvironmentalConditions:
    """Environmental conditions during test"""
    temperature: float  # Celsius
    humidity: float  # %RH
    pressure: Optional[float] = None  # kPa
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"T={self.temperature}°C, RH={self.humidity}%"


@dataclass
class SpecimenInfo:
    """Information about the test specimen"""
    specimen_id: str
    manufacturer: str
    model: str
    serial_number: str
    rated_power: float  # Watts
    rated_voltage: float  # Volts
    rated_current: float  # Amps
    technology: str  # e.g., "Mono-Si", "Poly-Si", "Thin-film"
    dimensions: Dict[str, float] = field(default_factory=dict)  # length, width, thickness
    manufacturing_date: Optional[str] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)


class ProtocolHandler(ABC):
    """
    Base class for all protocol test handlers

    This abstract base class defines the interface that all protocol handlers
    must implement for consistent test execution and reporting.
    """

    STANDARD_NAME: str = None
    STANDARD_VERSION: str = None
    STANDARD_FULL_NAME: str = None

    def __init__(self, specimen_info: SpecimenInfo, config: Optional[Dict[str, Any]] = None):
        """
        Initialize protocol handler

        Args:
            specimen_info: Information about the specimen under test
            config: Configuration dictionary for equipment and test parameters
        """
        self.specimen_info = specimen_info
        self.config = config or {}
        self.test_parameters: List[TestParameter] = []
        self.test_results: List[TestResult] = []
        self.environmental_conditions: List[EnvironmentalConditions] = []
        self.test_status = TestStatus.NOT_STARTED
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.operator: Optional[str] = self.config.get('operator', 'Unknown')
        self.test_facility: Optional[str] = self.config.get('facility', 'Unknown')

    @abstractmethod
    def initialize_equipment(self) -> bool:
        """
        Initialize all required test equipment

        Returns:
            True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    def setup_test_parameters(self) -> List[TestParameter]:
        """
        Setup test parameters based on specimen and standard requirements

        Returns:
            List of test parameters to be used in the test
        """
        pass

    @abstractmethod
    def execute_test_sequence(self) -> List[TestResult]:
        """
        Execute the complete test sequence defined by the protocol

        Returns:
            List of test results from all measurements
        """
        pass

    @abstractmethod
    def validate_results(self) -> bool:
        """
        Validate all test results against pass/fail criteria

        Returns:
            True if all results meet pass criteria, False otherwise
        """
        pass

    @abstractmethod
    def generate_report(self, output_path: str, format: str = 'pdf') -> str:
        """
        Generate test report in specified format

        Args:
            output_path: Path where report should be saved
            format: Report format ('pdf', 'json', 'xlsx')

        Returns:
            Path to generated report file
        """
        pass

    def record_environmental_conditions(self, temp: float, humidity: float,
                                       pressure: Optional[float] = None) -> None:
        """Record environmental conditions at current timestamp"""
        conditions = EnvironmentalConditions(
            temperature=temp,
            humidity=humidity,
            pressure=pressure
        )
        self.environmental_conditions.append(conditions)

    def add_test_result(self, result: TestResult) -> None:
        """Add a test result to the collection"""
        self.test_results.append(result)

    def get_overall_status(self) -> TestStatus:
        """
        Get overall test status based on all individual results

        Returns:
            Overall test status
        """
        if not self.test_results:
            return TestStatus.NOT_STARTED

        if any(r.status == TestStatus.FAIL for r in self.test_results):
            return TestStatus.FAIL

        if all(r.status == TestStatus.PASS for r in self.test_results):
            return TestStatus.PASS

        return TestStatus.IN_PROGRESS

    def cleanup(self) -> None:
        """Cleanup equipment and release resources"""
        pass

    def __enter__(self):
        """Context manager entry"""
        self.initialize_equipment()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
        return False
