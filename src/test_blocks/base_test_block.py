"""
Base Test Block Module

Provides abstract base class and common functionality for all PV test block implementations.
Includes equipment integration framework, data collection, analysis, and reporting.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import logging
import numpy as np
from scipy import stats


class TestResult(Enum):
    """Test result enumeration"""
    PASS = "PASS"
    FAIL = "FAIL"
    CONDITIONAL_PASS = "CONDITIONAL_PASS"
    NOT_TESTED = "NOT_TESTED"
    IN_PROGRESS = "IN_PROGRESS"
    ERROR = "ERROR"


class TestSeverity(Enum):
    """Test failure severity levels"""
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    INFORMATIONAL = "INFORMATIONAL"


@dataclass
class TestParameter:
    """Test parameter configuration"""
    name: str
    value: Any
    unit: str
    tolerance: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    description: str = ""


@dataclass
class MeasurementData:
    """Single measurement data point"""
    timestamp: datetime
    value: float
    unit: str
    parameter_name: str
    equipment_id: Optional[str] = None
    uncertainty: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestBlockResult:
    """Test block execution result"""
    test_name: str
    test_id: str
    result: TestResult
    start_time: datetime
    end_time: Optional[datetime]
    measurements: List[MeasurementData]
    parameters: Dict[str, TestParameter]
    analysis_results: Dict[str, Any]
    pass_fail_criteria: Dict[str, bool]
    anomalies: List[str]
    severity: TestSeverity
    operator: str
    equipment_used: List[str]
    comments: str = ""
    error_message: Optional[str] = None


class EquipmentInterface(ABC):
    """Abstract interface for test equipment"""

    def __init__(self, equipment_id: str, config: Dict[str, Any]):
        self.equipment_id = equipment_id
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{equipment_id}")
        self.connected = False
        self.last_calibration_date: Optional[datetime] = None
        self.calibration_due_date: Optional[datetime] = None

    @abstractmethod
    def connect(self) -> bool:
        """Connect to equipment"""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from equipment"""
        pass

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize equipment for testing"""
        pass

    @abstractmethod
    def measure(self, parameter: str) -> MeasurementData:
        """Take a measurement"""
        pass

    @abstractmethod
    def configure(self, settings: Dict[str, Any]) -> bool:
        """Configure equipment settings"""
        pass

    def verify_calibration(self) -> bool:
        """Verify equipment calibration status"""
        if self.calibration_due_date:
            return datetime.now() < self.calibration_due_date
        return True

    def get_uncertainty(self, parameter: str, value: float) -> float:
        """Calculate measurement uncertainty for given parameter and value"""
        # Default implementation - override in specific equipment classes
        return 0.01 * abs(value)  # 1% default uncertainty


class BaseTestBlock(ABC):
    """
    Abstract base class for all test block implementations.

    Provides common functionality for:
    - Equipment management
    - Data collection
    - Statistical analysis
    - Pass/fail determination
    - Result reporting
    """

    def __init__(
        self,
        test_id: str,
        operator: str,
        config: Dict[str, Any],
        equipment: Optional[List[EquipmentInterface]] = None
    ):
        self.test_id = test_id
        self.operator = operator
        self.config = config
        self.equipment = equipment or []
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        self.measurements: List[MeasurementData] = []
        self.parameters: Dict[str, TestParameter] = {}
        self.analysis_results: Dict[str, Any] = {}
        self.anomalies: List[str] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

        self._initialize_parameters()

    @abstractmethod
    def _initialize_parameters(self) -> None:
        """Initialize test-specific parameters"""
        pass

    @abstractmethod
    def execute(self) -> TestBlockResult:
        """Execute the test block"""
        pass

    @abstractmethod
    def _collect_data(self) -> List[MeasurementData]:
        """Collect test data"""
        pass

    @abstractmethod
    def _analyze_data(self) -> Dict[str, Any]:
        """Analyze collected data"""
        pass

    @abstractmethod
    def _determine_pass_fail(self) -> Tuple[TestResult, Dict[str, bool]]:
        """Determine pass/fail status"""
        pass

    def add_measurement(
        self,
        parameter_name: str,
        value: float,
        unit: str,
        equipment_id: Optional[str] = None,
        uncertainty: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a measurement data point"""
        measurement = MeasurementData(
            timestamp=datetime.now(),
            value=value,
            unit=unit,
            parameter_name=parameter_name,
            equipment_id=equipment_id,
            uncertainty=uncertainty,
            metadata=metadata or {}
        )
        self.measurements.append(measurement)

    def get_measurements(self, parameter_name: str) -> List[MeasurementData]:
        """Get all measurements for a specific parameter"""
        return [m for m in self.measurements if m.parameter_name == parameter_name]

    def calculate_statistics(self, parameter_name: str) -> Dict[str, float]:
        """Calculate statistical measures for a parameter"""
        measurements = self.get_measurements(parameter_name)
        if not measurements:
            return {}

        values = np.array([m.value for m in measurements])

        return {
            'mean': float(np.mean(values)),
            'median': float(np.median(values)),
            'std': float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
            'min': float(np.min(values)),
            'max': float(np.max(values)),
            'range': float(np.ptp(values)),
            'count': len(values),
            'cv': float(np.std(values, ddof=1) / np.mean(values) * 100) if np.mean(values) != 0 and len(values) > 1 else 0.0
        }

    def detect_outliers(
        self,
        parameter_name: str,
        method: str = 'iqr',
        threshold: float = 1.5
    ) -> List[int]:
        """
        Detect outliers in measurement data

        Args:
            parameter_name: Name of parameter to analyze
            method: Detection method ('iqr', 'zscore', 'modified_zscore')
            threshold: Threshold for outlier detection

        Returns:
            List of indices of outlier measurements
        """
        measurements = self.get_measurements(parameter_name)
        if len(measurements) < 4:
            return []

        values = np.array([m.value for m in measurements])
        outlier_indices = []

        if method == 'iqr':
            q1 = np.percentile(values, 25)
            q3 = np.percentile(values, 75)
            iqr = q3 - q1
            lower = q1 - threshold * iqr
            upper = q3 + threshold * iqr
            outlier_indices = [i for i, v in enumerate(values) if v < lower or v > upper]

        elif method == 'zscore':
            z_scores = np.abs(stats.zscore(values))
            outlier_indices = [i for i, z in enumerate(z_scores) if z > threshold]

        elif method == 'modified_zscore':
            median = np.median(values)
            mad = np.median(np.abs(values - median))
            modified_z_scores = 0.6745 * (values - median) / mad if mad != 0 else np.zeros_like(values)
            outlier_indices = [i for i, z in enumerate(modified_z_scores) if abs(z) > threshold]

        return outlier_indices

    def check_trend(
        self,
        parameter_name: str,
        method: str = 'linear'
    ) -> Dict[str, Any]:
        """
        Analyze trend in measurement data

        Args:
            parameter_name: Name of parameter to analyze
            method: Trend analysis method ('linear', 'polynomial')

        Returns:
            Dictionary with trend analysis results
        """
        measurements = self.get_measurements(parameter_name)
        if len(measurements) < 2:
            return {'trend': 'insufficient_data'}

        values = np.array([m.value for m in measurements])
        x = np.arange(len(values))

        if method == 'linear':
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)

            return {
                'trend': 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable',
                'slope': float(slope),
                'intercept': float(intercept),
                'r_squared': float(r_value ** 2),
                'p_value': float(p_value),
                'std_error': float(std_err),
                'significant': p_value < 0.05
            }

        return {'trend': 'unknown'}

    def validate_equipment(self) -> List[str]:
        """Validate all equipment calibration and readiness"""
        issues = []

        for equip in self.equipment:
            if not equip.verify_calibration():
                issues.append(f"Equipment {equip.equipment_id} calibration expired")

            if not equip.connected:
                issues.append(f"Equipment {equip.equipment_id} not connected")

        return issues

    def generate_result(self) -> TestBlockResult:
        """Generate test block result"""
        result, criteria = self._determine_pass_fail()

        # Determine severity based on result
        severity_map = {
            TestResult.FAIL: TestSeverity.CRITICAL,
            TestResult.CONDITIONAL_PASS: TestSeverity.MAJOR,
            TestResult.ERROR: TestSeverity.CRITICAL,
            TestResult.PASS: TestSeverity.INFORMATIONAL
        }

        return TestBlockResult(
            test_name=self.__class__.__name__,
            test_id=self.test_id,
            result=result,
            start_time=self.start_time or datetime.now(),
            end_time=self.end_time or datetime.now(),
            measurements=self.measurements,
            parameters=self.parameters,
            analysis_results=self.analysis_results,
            pass_fail_criteria=criteria,
            anomalies=self.anomalies,
            severity=severity_map.get(result, TestSeverity.INFORMATIONAL),
            operator=self.operator,
            equipment_used=[e.equipment_id for e in self.equipment]
        )

    def log_anomaly(self, description: str) -> None:
        """Log an anomaly detected during testing"""
        self.anomalies.append(f"{datetime.now().isoformat()}: {description}")
        self.logger.warning(f"Anomaly detected: {description}")

    def cleanup(self) -> None:
        """Cleanup resources after test execution"""
        for equip in self.equipment:
            try:
                if equip.connected:
                    equip.disconnect()
            except Exception as e:
                self.logger.error(f"Error disconnecting {equip.equipment_id}: {e}")
