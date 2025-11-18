"""
IEC 62804 PID Testing Protocol - PID Recovery Testing

This module provides testing for PID recovery (reversibility).
Tests whether power loss is reversible by removing voltage stress.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np

from .flash_tester import FlashTesterBase, IVCurveData

logger = logging.getLogger(__name__)


class RecoveryMethod(Enum):
    """PID recovery methods"""
    PASSIVE = "passive"  # Natural recovery (no external stimulation)
    ACTIVE_DARK = "active_dark"  # Reverse bias in dark
    ACTIVE_LIGHT = "active_light"  # Illumination with reverse bias
    THERMAL = "thermal"  # Elevated temperature recovery


class RecoveryClassification(Enum):
    """PID reversibility classification"""
    REVERSIBLE = "reversible"  # > 80% recovery
    PARTIALLY_REVERSIBLE = "partially_reversible"  # 20-80% recovery
    IRREVERSIBLE = "irreversible"  # < 20% recovery


@dataclass
class RecoveryMeasurement:
    """Recovery measurement at specific time"""
    timestamp: datetime
    elapsed_hours: float  # Hours since recovery started
    pmax: float  # W
    recovery_pct: float  # % of lost power recovered


@dataclass
class RecoveryResult:
    """PID recovery test result"""
    initial_pmax: float  # W (before PID stress)
    degraded_pmax: float  # W (after PID stress)
    final_pmax: float  # W (after recovery)

    power_loss: float  # W (degraded - initial)
    power_recovered: float  # W (final - degraded)

    degradation_pct: float  # % power loss
    recovery_pct: float  # % of lost power recovered
    final_degradation_pct: float  # % remaining degradation

    recovery_time: float  # hours
    recovery_rate: float  # %/hour

    classification: RecoveryClassification
    measurements: List[RecoveryMeasurement]


class PIDRecoveryTest:
    """
    Test PID recovery (reversibility).

    Monitors power recovery after removing PID stress conditions.
    """

    # IEC 62804 recovery thresholds
    REVERSIBLE_THRESHOLD = 80.0  # % recovery
    PARTIALLY_REVERSIBLE_THRESHOLD = 20.0  # % recovery

    def __init__(
        self,
        flash_tester: FlashTesterBase,
        initial_pmax: float,
        degraded_pmax: float,
        recovery_method: RecoveryMethod = RecoveryMethod.PASSIVE
    ):
        """
        Initialize recovery test.

        Args:
            flash_tester: Flash tester instance
            initial_pmax: Initial power before PID stress (W)
            degraded_pmax: Degraded power after PID stress (W)
            recovery_method: Recovery method to use
        """
        self.flash_tester = flash_tester
        self.initial_pmax = initial_pmax
        self.degraded_pmax = degraded_pmax
        self.recovery_method = recovery_method

        self.power_loss = initial_pmax - degraded_pmax
        self.degradation_pct = (self.power_loss / initial_pmax) * 100.0

        self._measurements: List[RecoveryMeasurement] = []
        self._start_time: Optional[datetime] = None

    def start_recovery(self):
        """Start recovery test"""
        self._start_time = datetime.utcnow()
        logger.info(
            f"Starting PID recovery test - "
            f"Initial: {self.initial_pmax}W, "
            f"Degraded: {self.degraded_pmax}W ({self.degradation_pct:.1f}% loss)"
        )

    def add_measurement(self, pmax: float, timestamp: Optional[datetime] = None):
        """
        Add recovery measurement.

        Args:
            pmax: Measured power (W)
            timestamp: Measurement time (default: now)
        """
        if self._start_time is None:
            raise RuntimeError("Recovery test not started")

        timestamp = timestamp or datetime.utcnow()
        elapsed = (timestamp - self._start_time).total_seconds() / 3600.0

        # Calculate recovery
        power_recovered = pmax - self.degraded_pmax
        recovery_pct = (power_recovered / self.power_loss) * 100.0 if self.power_loss > 0 else 0.0
        recovery_pct = max(0.0, min(100.0, recovery_pct))  # Clamp to 0-100%

        measurement = RecoveryMeasurement(
            timestamp=timestamp,
            elapsed_hours=elapsed,
            pmax=pmax,
            recovery_pct=recovery_pct
        )

        self._measurements.append(measurement)
        logger.info(
            f"Recovery measurement at {elapsed:.1f}h: "
            f"{pmax}W ({recovery_pct:.1f}% recovered)"
        )

    def get_current_recovery(self) -> float:
        """
        Get current recovery percentage.

        Returns:
            Recovery percentage (0-100)
        """
        if not self._measurements:
            return 0.0

        return self._measurements[-1].recovery_pct

    def calculate_recovery_rate(
        self,
        window_hours: Optional[float] = None
    ) -> float:
        """
        Calculate recovery rate.

        Args:
            window_hours: Time window (None = use all data)

        Returns:
            Recovery rate in %/hour
        """
        if len(self._measurements) < 2:
            return 0.0

        measurements = self._measurements
        if window_hours is not None:
            cutoff = self._measurements[-1].timestamp - timedelta(hours=window_hours)
            measurements = [m for m in measurements if m.timestamp >= cutoff]

        if len(measurements) < 2:
            return 0.0

        # Linear fit
        times = np.array([m.elapsed_hours for m in measurements])
        recoveries = np.array([m.recovery_pct for m in measurements])

        if len(times) > 1:
            coeffs = np.polyfit(times, recoveries, 1)
            rate = coeffs[0]  # %/hour
            return float(rate)

        return 0.0

    def classify_recovery(self, recovery_pct: float) -> RecoveryClassification:
        """
        Classify recovery as reversible/irreversible.

        Args:
            recovery_pct: Recovery percentage

        Returns:
            Recovery classification
        """
        if recovery_pct >= self.REVERSIBLE_THRESHOLD:
            return RecoveryClassification.REVERSIBLE
        elif recovery_pct >= self.PARTIALLY_REVERSIBLE_THRESHOLD:
            return RecoveryClassification.PARTIALLY_REVERSIBLE
        else:
            return RecoveryClassification.IRREVERSIBLE

    def analyze(self) -> RecoveryResult:
        """
        Analyze recovery test results.

        Returns:
            Complete recovery analysis
        """
        if not self._measurements:
            # No measurements yet
            return RecoveryResult(
                initial_pmax=self.initial_pmax,
                degraded_pmax=self.degraded_pmax,
                final_pmax=self.degraded_pmax,
                power_loss=self.power_loss,
                power_recovered=0.0,
                degradation_pct=self.degradation_pct,
                recovery_pct=0.0,
                final_degradation_pct=self.degradation_pct,
                recovery_time=0.0,
                recovery_rate=0.0,
                classification=RecoveryClassification.IRREVERSIBLE,
                measurements=[]
            )

        latest = self._measurements[-1]
        final_pmax = latest.pmax
        power_recovered = final_pmax - self.degraded_pmax
        recovery_pct = latest.recovery_pct

        # Calculate final degradation from initial
        final_degradation_pct = ((self.initial_pmax - final_pmax) / self.initial_pmax) * 100.0

        # Calculate recovery rate
        recovery_rate = self.calculate_recovery_rate()

        # Classify
        classification = self.classify_recovery(recovery_pct)

        return RecoveryResult(
            initial_pmax=self.initial_pmax,
            degraded_pmax=self.degraded_pmax,
            final_pmax=final_pmax,
            power_loss=self.power_loss,
            power_recovered=power_recovered,
            degradation_pct=self.degradation_pct,
            recovery_pct=recovery_pct,
            final_degradation_pct=final_degradation_pct,
            recovery_time=latest.elapsed_hours,
            recovery_rate=recovery_rate,
            classification=classification,
            measurements=self._measurements.copy()
        )

    def predict_recovery_time(
        self,
        target_recovery_pct: float = 80.0
    ) -> Optional[float]:
        """
        Predict time to reach target recovery.

        Args:
            target_recovery_pct: Target recovery percentage

        Returns:
            Predicted hours to target, or None if trend insufficient
        """
        if len(self._measurements) < 3:
            return None

        current_recovery = self.get_current_recovery()

        if current_recovery >= target_recovery_pct:
            return 0.0  # Already reached

        rate = self.calculate_recovery_rate()

        if rate <= 0:
            return None  # Not recovering or degrading further

        hours_to_target = (target_recovery_pct - current_recovery) / rate
        return float(hours_to_target)

    def is_recovery_complete(
        self,
        stability_threshold: float = 0.1,  # %/hour
        min_duration_hours: float = 24.0
    ) -> bool:
        """
        Check if recovery has stabilized.

        Args:
            stability_threshold: Max rate for stability (%/hour)
            min_duration_hours: Minimum test duration

        Returns:
            True if recovery appears complete
        """
        if not self._measurements:
            return False

        # Check minimum duration
        elapsed = self._measurements[-1].elapsed_hours
        if elapsed < min_duration_hours:
            return False

        # Check if rate has stabilized (near zero)
        rate = self.calculate_recovery_rate(window_hours=6.0)  # Last 6 hours
        return abs(rate) < stability_threshold

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
                "recovery_pct": m.recovery_pct
            }
            for m in self._measurements
        ]


class RecoveryProtocol:
    """
    Automated recovery test protocol.

    Manages recovery test with scheduled measurements.
    """

    def __init__(
        self,
        recovery_test: PIDRecoveryTest,
        measurement_intervals: List[float],  # Hours from start
        target_recovery: float = 80.0
    ):
        """
        Initialize recovery protocol.

        Args:
            recovery_test: Recovery test instance
            measurement_intervals: Hours from start for measurements
            target_recovery: Target recovery percentage
        """
        self.recovery_test = recovery_test
        self.measurement_intervals = sorted(measurement_intervals)
        self.target_recovery = target_recovery
        self._completed_intervals: List[float] = []

    def get_next_measurement_time(self) -> Optional[float]:
        """
        Get next scheduled measurement time.

        Returns:
            Hours from start, or None if all complete
        """
        for interval in self.measurement_intervals:
            if interval not in self._completed_intervals:
                return interval
        return None

    def is_measurement_due(
        self,
        current_hours: float,
        tolerance: float = 0.5
    ) -> bool:
        """
        Check if measurement is due.

        Args:
            current_hours: Current elapsed hours
            tolerance: Tolerance in hours

        Returns:
            True if measurement should be taken
        """
        next_interval = self.get_next_measurement_time()
        if next_interval is None:
            return False

        return abs(current_hours - next_interval) <= tolerance

    def mark_completed(self, interval: float):
        """Mark interval as completed"""
        if interval not in self._completed_intervals:
            self._completed_intervals.append(interval)

    def is_target_reached(self) -> bool:
        """Check if target recovery reached"""
        return self.recovery_test.get_current_recovery() >= self.target_recovery

    def get_progress(self) -> Dict[str, Any]:
        """
        Get protocol progress.

        Returns:
            Progress information
        """
        return {
            "total_measurements": len(self.measurement_intervals),
            "completed_measurements": len(self._completed_intervals),
            "current_recovery_pct": self.recovery_test.get_current_recovery(),
            "target_recovery_pct": self.target_recovery,
            "target_reached": self.is_target_reached(),
            "recovery_complete": self.recovery_test.is_recovery_complete()
        }


def calculate_recovery_kinetics(
    measurements: List[RecoveryMeasurement]
) -> Dict[str, float]:
    """
    Calculate recovery kinetics (exponential fit).

    Recovery often follows exponential: R(t) = R_max * (1 - exp(-t/tau))

    Args:
        measurements: List of recovery measurements

    Returns:
        Kinetics parameters (r_max, tau, r_squared)
    """
    if len(measurements) < 4:
        return {
            "r_max": 0.0,
            "tau": 0.0,
            "r_squared": 0.0
        }

    times = np.array([m.elapsed_hours for m in measurements])
    recoveries = np.array([m.recovery_pct for m in measurements])

    # Initial parameter estimates
    r_max_est = np.max(recoveries) * 1.2  # 120% of max observed
    tau_est = times[len(times) // 2]  # Half-time estimate

    try:
        from scipy.optimize import curve_fit

        def exponential_recovery(t, r_max, tau):
            return r_max * (1 - np.exp(-t / tau))

        # Fit exponential
        params, _ = curve_fit(
            exponential_recovery,
            times,
            recoveries,
            p0=[r_max_est, tau_est],
            maxfev=1000
        )

        r_max, tau = params

        # Calculate R²
        fit_values = exponential_recovery(times, r_max, tau)
        residuals = recoveries - fit_values
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((recoveries - np.mean(recoveries)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        return {
            "r_max": float(r_max),
            "tau": float(tau),
            "r_squared": float(r_squared)
        }

    except (ImportError, RuntimeError):
        # scipy not available or fit failed, use linear approximation
        logger.warning("Exponential fit failed, using linear approximation")
        return {
            "r_max": float(np.max(recoveries)),
            "tau": 0.0,
            "r_squared": 0.0
        }
