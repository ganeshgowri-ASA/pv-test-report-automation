"""
IEC 62804 PID Testing Protocol - Power Degradation Analysis

This module provides analysis of power degradation over time during PID testing,
including trend analysis, pass/fail determination, and degradation rate calculation.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class DegradationLevel(Enum):
    """IEC 62804 degradation classification"""
    NONE = "none"  # < 1%
    MINIMAL = "minimal"  # 1-3%
    MODERATE = "moderate"  # 3-5%
    SIGNIFICANT = "significant"  # 5-10%
    SEVERE = "severe"  # > 10%


class TestResult(Enum):
    """IEC 62804 test result"""
    PASS = "pass"  # < 5% at 96h
    MARGINAL = "marginal"  # 5-10% at 96h
    FAIL = "fail"  # > 10% at 96h
    PENDING = "pending"  # Test not complete


@dataclass
class PowerMeasurement:
    """Power measurement at specific time"""
    timestamp: datetime
    elapsed_hours: float
    pmax: float  # W
    voc: float  # V
    isc: float  # A
    ff: float  # Fill factor


@dataclass
class DegradationResult:
    """Degradation analysis result"""
    initial_pmax: float  # W
    current_pmax: float  # W
    final_pmax: Optional[float]  # W (if test complete)

    degradation_pct: float  # %
    degradation_absolute: float  # W

    degradation_rate: float  # %/hour
    degradation_rate_absolute: float  # W/hour

    test_duration: float  # hours
    test_complete: bool

    degradation_level: DegradationLevel
    test_result: TestResult

    measurements: List[PowerMeasurement]


@dataclass
class DegradationForecast:
    """Forecast of degradation based on current trend"""
    current_degradation_pct: float
    forecast_96h_pct: float
    predicted_result: TestResult
    confidence: float  # 0-1
    time_to_5pct: Optional[float]  # hours until 5% (or None if already past)
    time_to_10pct: Optional[float]  # hours until 10%


class DegradationAnalyzer:
    """
    Analyze power degradation patterns in PID testing.

    Provides comprehensive analysis of degradation trends, rates, and forecasts.
    """

    # IEC 62804 thresholds
    PASS_THRESHOLD = 5.0  # %
    MARGINAL_THRESHOLD = 10.0  # %

    def __init__(self, initial_pmax: float):
        """
        Initialize analyzer.

        Args:
            initial_pmax: Initial maximum power in W
        """
        self.initial_pmax = initial_pmax
        self._measurements: List[PowerMeasurement] = []

    def add_measurement(
        self,
        timestamp: datetime,
        elapsed_hours: float,
        pmax: float,
        voc: float,
        isc: float,
        ff: float
    ):
        """
        Add a power measurement.

        Args:
            timestamp: Measurement time
            elapsed_hours: Hours from test start
            pmax: Maximum power (W)
            voc: Open circuit voltage (V)
            isc: Short circuit current (A)
            ff: Fill factor
        """
        measurement = PowerMeasurement(
            timestamp=timestamp,
            elapsed_hours=elapsed_hours,
            pmax=pmax,
            voc=voc,
            isc=isc,
            ff=ff
        )
        self._measurements.append(measurement)
        logger.debug(f"Added measurement at {elapsed_hours}h: {pmax}W ({self.calculate_degradation(pmax):.2f}%)")

    def calculate_degradation(self, current_pmax: float) -> float:
        """
        Calculate degradation percentage.

        Args:
            current_pmax: Current maximum power (W)

        Returns:
            Degradation percentage
        """
        if self.initial_pmax <= 0:
            return 0.0

        degradation = ((self.initial_pmax - current_pmax) / self.initial_pmax) * 100.0
        return max(0.0, degradation)  # Don't report negative degradation

    def get_current_degradation(self) -> float:
        """
        Get current degradation percentage.

        Returns:
            Current degradation %
        """
        if not self._measurements:
            return 0.0

        latest = self._measurements[-1]
        return self.calculate_degradation(latest.pmax)

    def calculate_degradation_rate(
        self,
        window_hours: Optional[float] = None
    ) -> float:
        """
        Calculate degradation rate.

        Args:
            window_hours: Time window for calculation (None = use all data)

        Returns:
            Degradation rate in %/hour
        """
        if len(self._measurements) < 2:
            return 0.0

        # Filter measurements by window
        measurements = self._measurements
        if window_hours is not None:
            cutoff_time = self._measurements[-1].timestamp - timedelta(hours=window_hours)
            measurements = [m for m in measurements if m.timestamp >= cutoff_time]

        if len(measurements) < 2:
            return 0.0

        # Calculate linear fit
        times = np.array([m.elapsed_hours for m in measurements])
        powers = np.array([m.pmax for m in measurements])

        # Convert to degradation percentages
        degradations = ((self.initial_pmax - powers) / self.initial_pmax) * 100.0

        # Linear regression
        if len(times) > 1:
            coeffs = np.polyfit(times, degradations, 1)
            rate = coeffs[0]  # Slope in %/hour
            return float(rate)

        return 0.0

    def classify_degradation(self, degradation_pct: float) -> DegradationLevel:
        """
        Classify degradation level.

        Args:
            degradation_pct: Degradation percentage

        Returns:
            Degradation level classification
        """
        if degradation_pct < 1.0:
            return DegradationLevel.NONE
        elif degradation_pct < 3.0:
            return DegradationLevel.MINIMAL
        elif degradation_pct < 5.0:
            return DegradationLevel.MODERATE
        elif degradation_pct < 10.0:
            return DegradationLevel.SIGNIFICANT
        else:
            return DegradationLevel.SEVERE

    def determine_test_result(
        self,
        degradation_pct: float,
        elapsed_hours: float
    ) -> TestResult:
        """
        Determine test pass/fail result.

        Args:
            degradation_pct: Degradation percentage
            elapsed_hours: Test duration

        Returns:
            Test result classification
        """
        # Test must run for at least 96 hours per IEC 62804
        if elapsed_hours < 96.0:
            return TestResult.PENDING

        if degradation_pct < self.PASS_THRESHOLD:
            return TestResult.PASS
        elif degradation_pct < self.MARGINAL_THRESHOLD:
            return TestResult.MARGINAL
        else:
            return TestResult.FAIL

    def analyze(self, test_complete: bool = False) -> DegradationResult:
        """
        Perform comprehensive degradation analysis.

        Args:
            test_complete: Whether test is complete (96h+)

        Returns:
            Complete degradation analysis
        """
        if not self._measurements:
            # No data yet
            return DegradationResult(
                initial_pmax=self.initial_pmax,
                current_pmax=self.initial_pmax,
                final_pmax=None,
                degradation_pct=0.0,
                degradation_absolute=0.0,
                degradation_rate=0.0,
                degradation_rate_absolute=0.0,
                test_duration=0.0,
                test_complete=False,
                degradation_level=DegradationLevel.NONE,
                test_result=TestResult.PENDING,
                measurements=[]
            )

        latest = self._measurements[-1]
        current_pmax = latest.pmax
        elapsed_hours = latest.elapsed_hours

        # Calculate degradation
        degradation_pct = self.calculate_degradation(current_pmax)
        degradation_absolute = self.initial_pmax - current_pmax

        # Calculate rate
        degradation_rate = self.calculate_degradation_rate()
        degradation_rate_absolute = degradation_rate * self.initial_pmax / 100.0

        # Classify
        degradation_level = self.classify_degradation(degradation_pct)
        test_result = self.determine_test_result(degradation_pct, elapsed_hours)

        return DegradationResult(
            initial_pmax=self.initial_pmax,
            current_pmax=current_pmax,
            final_pmax=current_pmax if test_complete else None,
            degradation_pct=degradation_pct,
            degradation_absolute=degradation_absolute,
            degradation_rate=degradation_rate,
            degradation_rate_absolute=degradation_rate_absolute,
            test_duration=elapsed_hours,
            test_complete=test_complete,
            degradation_level=degradation_level,
            test_result=test_result,
            measurements=self._measurements.copy()
        )

    def forecast_degradation(self) -> Optional[DegradationForecast]:
        """
        Forecast degradation at 96 hours based on current trend.

        Returns:
            Degradation forecast or None if insufficient data
        """
        if len(self._measurements) < 3:
            return None

        current_degradation = self.get_current_degradation()
        current_hours = self._measurements[-1].elapsed_hours

        if current_hours >= 96.0:
            # Test already at or past 96h
            return DegradationForecast(
                current_degradation_pct=current_degradation,
                forecast_96h_pct=current_degradation,
                predicted_result=self.determine_test_result(current_degradation, current_hours),
                confidence=1.0,
                time_to_5pct=None,
                time_to_10pct=None
            )

        # Calculate trend
        rate = self.calculate_degradation_rate()

        # Forecast to 96h
        hours_remaining = 96.0 - current_hours
        forecast_96h = current_degradation + (rate * hours_remaining)
        forecast_96h = max(0.0, forecast_96h)  # No negative degradation

        # Predict result
        predicted_result = self.determine_test_result(forecast_96h, 96.0)

        # Calculate confidence (based on R² of linear fit)
        times = np.array([m.elapsed_hours for m in self._measurements])
        powers = np.array([m.pmax for m in self._measurements])
        degradations = ((self.initial_pmax - powers) / self.initial_pmax) * 100.0

        if len(times) > 2:
            coeffs = np.polyfit(times, degradations, 1)
            fit_values = np.polyval(coeffs, times)
            residuals = degradations - fit_values
            ss_res = np.sum(residuals ** 2)
            ss_tot = np.sum((degradations - np.mean(degradations)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            confidence = max(0.0, min(1.0, r_squared))
        else:
            confidence = 0.5

        # Calculate time to thresholds
        time_to_5pct = None
        time_to_10pct = None

        if rate > 0:
            if current_degradation < 5.0:
                time_to_5pct = (5.0 - current_degradation) / rate
            if current_degradation < 10.0:
                time_to_10pct = (10.0 - current_degradation) / rate

        return DegradationForecast(
            current_degradation_pct=current_degradation,
            forecast_96h_pct=forecast_96h,
            predicted_result=predicted_result,
            confidence=confidence,
            time_to_5pct=time_to_5pct,
            time_to_10pct=time_to_10pct
        )

    def get_measurements(self) -> List[PowerMeasurement]:
        """Get all measurements"""
        return self._measurements.copy()

    def export_data(self) -> List[Dict[str, Any]]:
        """
        Export measurements as dictionaries.

        Returns:
            List of measurement dictionaries
        """
        return [
            {
                "timestamp": m.timestamp.isoformat(),
                "elapsed_hours": m.elapsed_hours,
                "pmax": m.pmax,
                "voc": m.voc,
                "isc": m.isc,
                "ff": m.ff,
                "degradation_pct": self.calculate_degradation(m.pmax)
            }
            for m in self._measurements
        ]


class DegradationComparator:
    """
    Compare degradation between multiple modules or tests.
    """

    @staticmethod
    def compare_modules(
        results: List[Tuple[str, DegradationResult]]
    ) -> Dict[str, Any]:
        """
        Compare degradation across multiple modules.

        Args:
            results: List of (module_id, degradation_result) tuples

        Returns:
            Comparison summary
        """
        if not results:
            return {}

        degradations = [r[1].degradation_pct for r in results]

        return {
            "num_modules": len(results),
            "mean_degradation": float(np.mean(degradations)),
            "std_degradation": float(np.std(degradations)),
            "min_degradation": float(np.min(degradations)),
            "max_degradation": float(np.max(degradations)),
            "pass_count": sum(1 for r in results if r[1].test_result == TestResult.PASS),
            "marginal_count": sum(1 for r in results if r[1].test_result == TestResult.MARGINAL),
            "fail_count": sum(1 for r in results if r[1].test_result == TestResult.FAIL),
            "modules": [
                {
                    "module_id": r[0],
                    "degradation_pct": r[1].degradation_pct,
                    "result": r[1].test_result.value
                }
                for r in results
            ]
        }

    @staticmethod
    def rank_by_degradation(
        results: List[Tuple[str, DegradationResult]]
    ) -> List[Tuple[str, float]]:
        """
        Rank modules by degradation (worst first).

        Args:
            results: List of (module_id, degradation_result) tuples

        Returns:
            List of (module_id, degradation_pct) sorted by degradation
        """
        ranked = [(r[0], r[1].degradation_pct) for r in results]
        return sorted(ranked, key=lambda x: x[1], reverse=True)

    @staticmethod
    def identify_outliers(
        results: List[Tuple[str, DegradationResult]],
        threshold_std: float = 2.0
    ) -> List[str]:
        """
        Identify modules with outlier degradation.

        Args:
            results: List of (module_id, degradation_result) tuples
            threshold_std: Number of standard deviations for outlier

        Returns:
            List of module IDs with outlier degradation
        """
        if len(results) < 3:
            return []

        degradations = np.array([r[1].degradation_pct for r in results])
        mean = np.mean(degradations)
        std = np.std(degradations)

        outliers = []
        for module_id, result in results:
            z_score = abs(result.degradation_pct - mean) / std if std > 0 else 0
            if z_score > threshold_std:
                outliers.append(module_id)

        return outliers
