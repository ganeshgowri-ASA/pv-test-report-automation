"""
Base protocol class for all test protocols
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
import logging

from src.utils.constants import TestStatus, PassFailStatus


@dataclass
class TestResult:
    """Standard test result structure"""
    test_id: Optional[int] = None
    protocol: str = ""
    module_id: str = ""
    status: TestStatus = TestStatus.PENDING
    pass_fail: PassFailStatus = PassFailStatus.NOT_TESTED
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    test_data: Dict[str, Any] = field(default_factory=dict)
    measurements: Dict[str, Any] = field(default_factory=dict)
    compliance_data: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'test_id': self.test_id,
            'protocol': self.protocol,
            'module_id': self.module_id,
            'status': self.status.value if isinstance(self.status, TestStatus) else self.status,
            'pass_fail': self.pass_fail.value if isinstance(self.pass_fail, PassFailStatus) else self.pass_fail,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'test_data': self.test_data,
            'measurements': self.measurements,
            'compliance_data': self.compliance_data,
            'notes': self.notes
        }


class BaseProtocol(ABC):
    """
    Base class for all test protocols

    All protocol implementations must inherit from this class and implement
    the required abstract methods for ISO 17025 compliance.
    """

    def __init__(self, module_id: str, test_id: Optional[int] = None):
        self.module_id = module_id
        self.test_id = test_id
        self.logger = logging.getLogger(self.__class__.__name__)
        self.result = TestResult(
            test_id=test_id,
            protocol=self.get_protocol_name(),
            module_id=module_id
        )

    @property
    @abstractmethod
    def protocol_name(self) -> str:
        """Protocol name (e.g., 'IEC 62759')"""
        pass

    @property
    @abstractmethod
    def protocol_version(self) -> str:
        """Protocol version (e.g., '1.0:2021')"""
        pass

    def get_protocol_name(self) -> str:
        """Get full protocol name with version"""
        return f"{self.protocol_name} {self.protocol_version}"

    @abstractmethod
    def validate_inputs(self, **kwargs) -> bool:
        """
        Validate input parameters against protocol requirements

        Returns:
            bool: True if valid, raises ValidationError otherwise
        """
        pass

    @abstractmethod
    def run_test_sequence(self, **kwargs) -> TestResult:
        """
        Execute the complete test sequence

        Returns:
            TestResult: Complete test results
        """
        pass

    @abstractmethod
    def calculate_pass_fail(self) -> PassFailStatus:
        """
        Calculate pass/fail status based on test results

        Returns:
            PassFailStatus: Final pass/fail determination
        """
        pass

    @abstractmethod
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate test report with all required data

        Returns:
            Dict: Report data structure
        """
        pass

    def verify_iso17025_compliance(self) -> bool:
        """
        Verify ISO 17025 compliance requirements

        Returns:
            bool: True if compliant
        """
        required_fields = [
            'technician_id',
            'equipment_ids',
            'calibration_dates',
            'environmental_conditions',
            'measurement_uncertainty'
        ]

        for field in required_fields:
            if field not in self.result.compliance_data:
                self.logger.warning(f"Missing ISO 17025 field: {field}")
                return False

        return True

    def log_test_event(self, event: str, data: Optional[Dict] = None):
        """Log test event with optional data"""
        timestamp = datetime.now().isoformat()
        event_log = {
            'timestamp': timestamp,
            'event': event,
            'data': data or {}
        }

        if 'event_log' not in self.result.test_data:
            self.result.test_data['event_log'] = []

        self.result.test_data['event_log'].append(event_log)
        self.logger.info(f"{event}: {data}")
