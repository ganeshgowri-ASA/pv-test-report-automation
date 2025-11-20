"""
Base Protocol Class for IEC Standards Implementation

This module provides the abstract base class and common structures for all
IEC protocol implementations in the PV testing framework.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import numpy as np


class TestStatus(Enum):
    """Test result status enumeration"""
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    NOT_TESTED = "NOT_TESTED"
    IN_PROGRESS = "IN_PROGRESS"


class DataQuality(Enum):
    """Data quality classification"""
    EXCELLENT = "EXCELLENT"  # < 1% uncertainty
    GOOD = "GOOD"           # 1-2% uncertainty
    ACCEPTABLE = "ACCEPTABLE"  # 2-5% uncertainty
    POOR = "POOR"           # > 5% uncertainty
    INVALID = "INVALID"     # Data fails validation


@dataclass
class Uncertainty:
    """
    Measurement uncertainty representation following GUM (Guide to Uncertainty in Measurement)

    Attributes:
        value: The measured or calculated value
        standard_uncertainty: Standard uncertainty (k=1)
        expanded_uncertainty: Expanded uncertainty (typically k=2 for 95% confidence)
        coverage_factor: Coverage factor (k)
        degrees_of_freedom: Effective degrees of freedom
        sources: Dictionary of uncertainty sources and their contributions
    """
    value: float
    standard_uncertainty: float
    expanded_uncertainty: Optional[float] = None
    coverage_factor: float = 2.0
    degrees_of_freedom: Optional[float] = None
    sources: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate expanded uncertainty if not provided"""
        if self.expanded_uncertainty is None:
            self.expanded_uncertainty = self.coverage_factor * self.standard_uncertainty

    @property
    def relative_uncertainty(self) -> float:
        """Calculate relative uncertainty as percentage"""
        if self.value == 0:
            return float('inf')
        return (self.standard_uncertainty / abs(self.value)) * 100

    @property
    def relative_expanded_uncertainty(self) -> float:
        """Calculate relative expanded uncertainty as percentage"""
        if self.value == 0:
            return float('inf')
        return (self.expanded_uncertainty / abs(self.value)) * 100

    def __str__(self) -> str:
        """String representation with uncertainty"""
        return f"{self.value:.4f} ± {self.expanded_uncertainty:.4f}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'value': self.value,
            'standard_uncertainty': self.standard_uncertainty,
            'expanded_uncertainty': self.expanded_uncertainty,
            'coverage_factor': self.coverage_factor,
            'degrees_of_freedom': self.degrees_of_freedom,
            'relative_uncertainty_percent': self.relative_uncertainty,
            'sources': self.sources
        }


@dataclass
class ProtocolResult:
    """
    Standard result structure for protocol measurements

    Attributes:
        protocol_name: Name of the protocol/standard
        test_date: Date and time of the test
        status: Overall test status
        measurements: Dictionary of measurement results
        pass_fail_criteria: Dictionary of criteria and their results
        data_quality: Overall data quality assessment
        metadata: Additional metadata (equipment, conditions, etc.)
        notes: Optional notes or comments
        raw_data: Optional raw data storage
    """
    protocol_name: str
    test_date: datetime
    status: TestStatus
    measurements: Dict[str, Union[float, Uncertainty, Dict[str, Any]]]
    pass_fail_criteria: Dict[str, bool] = field(default_factory=dict)
    data_quality: DataQuality = DataQuality.ACCEPTABLE
    metadata: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    raw_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization"""
        measurements_dict = {}
        for key, value in self.measurements.items():
            if isinstance(value, Uncertainty):
                measurements_dict[key] = value.to_dict()
            else:
                measurements_dict[key] = value

        return {
            'protocol_name': self.protocol_name,
            'test_date': self.test_date.isoformat(),
            'status': self.status.value,
            'measurements': measurements_dict,
            'pass_fail_criteria': self.pass_fail_criteria,
            'data_quality': self.data_quality.value,
            'metadata': self.metadata,
            'notes': self.notes,
            'raw_data': self.raw_data
        }

    def add_measurement(self, name: str, value: Union[float, Uncertainty, Dict[str, Any]]):
        """Add a measurement to the results"""
        self.measurements[name] = value

    def add_criterion(self, name: str, passed: bool):
        """Add a pass/fail criterion result"""
        self.pass_fail_criteria[name] = passed

        # Update overall status if any criterion fails
        if not passed and self.status == TestStatus.PASS:
            self.status = TestStatus.FAIL


class BaseProtocol(ABC):
    """
    Abstract base class for all IEC protocol implementations

    This class provides common functionality including:
    - Uncertainty calculation methods
    - Data quality assessment
    - Temperature corrections
    - Irradiance corrections
    - Result reporting
    """

    def __init__(self, protocol_name: str, protocol_version: str):
        """
        Initialize protocol handler

        Args:
            protocol_name: Name of the IEC standard (e.g., "IEC 61853-1")
            protocol_version: Version of the standard
        """
        self.protocol_name = protocol_name
        self.protocol_version = protocol_version
        self.results: Optional[ProtocolResult] = None

    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate input data meets protocol requirements

        Args:
            data: Input data dictionary

        Returns:
            True if data is valid, False otherwise
        """
        pass

    @abstractmethod
    def calculate(self, data: Dict[str, Any]) -> ProtocolResult:
        """
        Perform protocol-specific calculations

        Args:
            data: Input data dictionary

        Returns:
            ProtocolResult containing all measurements and analysis
        """
        pass

    def combine_uncertainties(self, sources: Dict[str, float]) -> float:
        """
        Combine multiple uncertainty sources using root sum of squares

        Args:
            sources: Dictionary of uncertainty source names and values

        Returns:
            Combined standard uncertainty
        """
        return np.sqrt(sum(u**2 for u in sources.values()))

    def calculate_type_a_uncertainty(self, measurements: np.ndarray) -> float:
        """
        Calculate Type A uncertainty (statistical) from repeated measurements

        Args:
            measurements: Array of measurement values

        Returns:
            Standard uncertainty (standard error of the mean)
        """
        if len(measurements) < 2:
            raise ValueError("At least 2 measurements required for Type A uncertainty")

        return np.std(measurements, ddof=1) / np.sqrt(len(measurements))

    def calculate_type_b_uncertainty(self, instrument_uncertainty: float,
                                    distribution: str = 'normal') -> float:
        """
        Calculate Type B uncertainty from instrument specifications

        Args:
            instrument_uncertainty: Stated instrument uncertainty
            distribution: Assumed probability distribution ('normal', 'uniform', 'triangular')

        Returns:
            Standard uncertainty
        """
        divisors = {
            'normal': 2.0,      # k=2 for 95% confidence
            'uniform': np.sqrt(3),
            'triangular': np.sqrt(6)
        }

        divisor = divisors.get(distribution, 2.0)
        return instrument_uncertainty / divisor

    def assess_data_quality(self, uncertainty: Uncertainty) -> DataQuality:
        """
        Assess data quality based on relative uncertainty

        Args:
            uncertainty: Uncertainty object

        Returns:
            DataQuality classification
        """
        rel_unc = uncertainty.relative_uncertainty

        if rel_unc < 1.0:
            return DataQuality.EXCELLENT
        elif rel_unc < 2.0:
            return DataQuality.GOOD
        elif rel_unc < 5.0:
            return DataQuality.ACCEPTABLE
        else:
            return DataQuality.POOR

    def correct_temperature(self, value: float, measured_temp: float,
                          reference_temp: float, temp_coefficient: float) -> float:
        """
        Apply temperature correction to a measured value

        Args:
            value: Measured value at measured_temp
            measured_temp: Temperature during measurement (°C)
            reference_temp: Reference temperature (°C)
            temp_coefficient: Temperature coefficient (%/°C)

        Returns:
            Temperature-corrected value
        """
        delta_temp = measured_temp - reference_temp
        correction_factor = 1 + (temp_coefficient / 100) * delta_temp
        return value / correction_factor

    def correct_irradiance(self, value: float, measured_irr: float,
                          reference_irr: float, power_law_exp: float = 1.0) -> float:
        """
        Apply irradiance correction to a measured value

        Args:
            value: Measured value at measured_irr
            measured_irr: Irradiance during measurement (W/m²)
            reference_irr: Reference irradiance (W/m²)
            power_law_exp: Power law exponent (default 1.0 for linear)

        Returns:
            Irradiance-corrected value
        """
        return value * (reference_irr / measured_irr) ** power_law_exp

    def calculate_spectral_mismatch(self, reference_spectrum: np.ndarray,
                                   test_spectrum: np.ndarray,
                                   spectral_response: np.ndarray) -> float:
        """
        Calculate spectral mismatch factor

        Args:
            reference_spectrum: Reference spectral irradiance (W/m²/nm)
            test_spectrum: Test spectral irradiance (W/m²/nm)
            spectral_response: Device spectral response (A/W)

        Returns:
            Spectral mismatch factor M
        """
        # Ensure arrays are same length
        min_len = min(len(reference_spectrum), len(test_spectrum), len(spectral_response))
        ref = reference_spectrum[:min_len]
        test = test_spectrum[:min_len]
        sr = spectral_response[:min_len]

        # Calculate integrals
        numerator = np.trapz(ref * sr) * np.trapz(test)
        denominator = np.trapz(test * sr) * np.trapz(ref)

        if denominator == 0:
            raise ValueError("Spectral mismatch calculation resulted in division by zero")

        return numerator / denominator

    def check_data_range(self, value: float, min_val: float, max_val: float,
                        param_name: str = "Parameter") -> bool:
        """
        Check if a value is within acceptable range

        Args:
            value: Value to check
            min_val: Minimum acceptable value
            max_val: Maximum acceptable value
            param_name: Parameter name for error messages

        Returns:
            True if within range, False otherwise
        """
        if not (min_val <= value <= max_val):
            print(f"Warning: {param_name} = {value} is outside acceptable range "
                  f"[{min_val}, {max_val}]")
            return False
        return True

    def calculate_linear_regression(self, x: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        Perform linear regression and return coefficients with uncertainties

        Args:
            x: Independent variable array
            y: Dependent variable array

        Returns:
            Dictionary with slope, intercept, R², and their uncertainties
        """
        if len(x) != len(y) or len(x) < 3:
            raise ValueError("Arrays must have same length and at least 3 points")

        n = len(x)

        # Calculate regression coefficients
        x_mean = np.mean(x)
        y_mean = np.mean(y)

        ss_xx = np.sum((x - x_mean)**2)
        ss_xy = np.sum((x - x_mean) * (y - y_mean))
        ss_yy = np.sum((y - y_mean)**2)

        slope = ss_xy / ss_xx
        intercept = y_mean - slope * x_mean

        # Calculate R²
        ss_res = np.sum((y - (slope * x + intercept))**2)
        r_squared = 1 - (ss_res / ss_yy)

        # Calculate standard errors
        s_yx = np.sqrt(ss_res / (n - 2))  # Residual standard deviation
        slope_std_error = s_yx / np.sqrt(ss_xx)
        intercept_std_error = s_yx * np.sqrt(1/n + x_mean**2/ss_xx)

        return {
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_squared,
            'slope_uncertainty': slope_std_error,
            'intercept_uncertainty': intercept_std_error,
            'residual_std_dev': s_yx
        }

    def interpolate_value(self, x_data: np.ndarray, y_data: np.ndarray,
                         x_target: float, method: str = 'linear') -> float:
        """
        Interpolate value at target x using specified method

        Args:
            x_data: Known x values
            y_data: Known y values
            x_target: Target x value for interpolation
            method: Interpolation method ('linear', 'cubic')

        Returns:
            Interpolated y value
        """
        if len(x_data) != len(y_data):
            raise ValueError("x_data and y_data must have same length")

        if method == 'linear':
            return np.interp(x_target, x_data, y_data)
        elif method == 'cubic' and len(x_data) >= 4:
            from scipy.interpolate import CubicSpline
            cs = CubicSpline(x_data, y_data)
            return float(cs(x_target))
        else:
            # Fall back to linear if cubic not possible
            return np.interp(x_target, x_data, y_data)

    def create_result(self, status: TestStatus = TestStatus.PASS,
                     metadata: Optional[Dict[str, Any]] = None) -> ProtocolResult:
        """
        Create a new ProtocolResult object

        Args:
            status: Initial test status
            metadata: Optional metadata dictionary

        Returns:
            New ProtocolResult object
        """
        result = ProtocolResult(
            protocol_name=self.protocol_name,
            test_date=datetime.now(),
            status=status,
            measurements={},
            metadata=metadata or {}
        )

        # Add protocol version to metadata
        result.metadata['protocol_version'] = self.protocol_version

        self.results = result
        return result
