"""
IEC 62804 PID Testing Protocol - Leakage Current Monitoring

This module provides continuous monitoring of leakage current during PID testing
with automatic safety shutdown and data logging.
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, List, Callable, Dict, Any
from dataclasses import dataclass
from collections import deque
import numpy as np

from .voltage_control import VoltageSupplyBase, VoltageReading

logger = logging.getLogger(__name__)


@dataclass
class LeakageCurrentReading:
    """Leakage current measurement"""
    timestamp: datetime
    elapsed_hours: float
    current_ma: float
    voltage: float
    over_threshold: bool = False


@dataclass
class LeakageStatistics:
    """Statistical summary of leakage current"""
    mean_current_ma: float
    max_current_ma: float
    min_current_ma: float
    std_current_ma: float
    num_readings: int
    time_over_threshold: float  # seconds
    threshold_violations: int


class LeakageCurrentMonitor:
    """
    Continuous monitoring of leakage current with safety features.

    Monitors leakage current from voltage supply and triggers alarms/shutdowns
    when thresholds are exceeded.
    """

    def __init__(
        self,
        voltage_supply: VoltageSupplyBase,
        threshold_ma: float = 50.0,
        critical_threshold_ma: float = 100.0,
        sample_interval: float = 60.0,  # seconds
        alarm_callback: Optional[Callable] = None,
        emergency_callback: Optional[Callable] = None
    ):
        """
        Initialize leakage current monitor.

        Args:
            voltage_supply: Voltage supply instance to monitor
            threshold_ma: Warning threshold in mA
            critical_threshold_ma: Critical threshold for auto-shutdown in mA
            sample_interval: Time between samples in seconds
            alarm_callback: Function to call on threshold violation
            emergency_callback: Function to call on critical threshold
        """
        self.voltage_supply = voltage_supply
        self.threshold_ma = threshold_ma
        self.critical_threshold_ma = critical_threshold_ma
        self.sample_interval = sample_interval
        self.alarm_callback = alarm_callback
        self.emergency_callback = emergency_callback

        # Monitoring state
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._start_time: Optional[datetime] = None

        # Data storage
        self._readings: deque = deque(maxlen=10000)  # Keep last 10k readings
        self._alarm_count = 0
        self._shutdown_triggered = False

    def start_monitoring(self):
        """Start continuous monitoring in background thread"""
        if self._monitoring:
            logger.warning("Monitoring already started")
            return

        self._monitoring = True
        self._start_time = datetime.utcnow()
        self._shutdown_triggered = False

        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="LeakageCurrentMonitor"
        )
        self._monitor_thread.start()
        logger.info(f"Leakage current monitoring started (interval: {self.sample_interval}s)")

    def stop_monitoring(self):
        """Stop continuous monitoring"""
        if not self._monitoring:
            return

        logger.info("Stopping leakage current monitoring")
        self._monitoring = False

        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)

    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                # Get current reading from voltage supply
                voltage_reading = self.voltage_supply.get_reading()
                current_ma = voltage_reading.current * 1000.0  # Convert A to mA

                # Calculate elapsed time
                elapsed = (datetime.utcnow() - self._start_time).total_seconds() / 3600.0

                # Create reading
                reading = LeakageCurrentReading(
                    timestamp=datetime.utcnow(),
                    elapsed_hours=elapsed,
                    current_ma=current_ma,
                    voltage=voltage_reading.voltage,
                    over_threshold=(current_ma > self.threshold_ma)
                )

                # Store reading
                self._readings.append(reading)

                # Check thresholds
                if current_ma > self.critical_threshold_ma:
                    logger.critical(
                        f"CRITICAL: Leakage current {current_ma:.1f}mA exceeds "
                        f"critical threshold {self.critical_threshold_ma}mA"
                    )
                    self._handle_critical_threshold(reading)

                elif current_ma > self.threshold_ma:
                    logger.warning(
                        f"Leakage current {current_ma:.1f}mA exceeds "
                        f"threshold {self.threshold_ma}mA"
                    )
                    self._handle_alarm(reading)

                # Wait for next sample
                time.sleep(self.sample_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                time.sleep(self.sample_interval)

    def _handle_alarm(self, reading: LeakageCurrentReading):
        """Handle threshold alarm"""
        self._alarm_count += 1

        if self.alarm_callback:
            try:
                self.alarm_callback(reading)
            except Exception as e:
                logger.error(f"Error in alarm callback: {e}")

    def _handle_critical_threshold(self, reading: LeakageCurrentReading):
        """Handle critical threshold - trigger emergency shutdown"""
        if self._shutdown_triggered:
            return  # Already handled

        self._shutdown_triggered = True
        logger.critical("Triggering emergency shutdown due to excessive leakage current")

        # Trigger emergency stop on voltage supply
        try:
            self.voltage_supply.emergency_stop()
        except Exception as e:
            logger.error(f"Error triggering emergency stop: {e}")

        # Call emergency callback
        if self.emergency_callback:
            try:
                self.emergency_callback(reading)
            except Exception as e:
                logger.error(f"Error in emergency callback: {e}")

    def get_current_reading(self) -> Optional[LeakageCurrentReading]:
        """
        Get most recent leakage current reading.

        Returns:
            Latest reading or None if no data
        """
        if not self._readings:
            return None
        return self._readings[-1]

    def get_readings(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[LeakageCurrentReading]:
        """
        Get historical readings within time range.

        Args:
            start_time: Start of time range (inclusive)
            end_time: End of time range (inclusive)

        Returns:
            List of readings
        """
        readings = list(self._readings)

        if start_time:
            readings = [r for r in readings if r.timestamp >= start_time]

        if end_time:
            readings = [r for r in readings if r.timestamp <= end_time]

        return readings

    def get_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Optional[LeakageStatistics]:
        """
        Calculate statistics for leakage current.

        Args:
            start_time: Start of time range
            end_time: End of time range

        Returns:
            Statistical summary or None if no data
        """
        readings = self.get_readings(start_time, end_time)

        if not readings:
            return None

        currents = [r.current_ma for r in readings]

        # Calculate time over threshold
        time_over_threshold = 0.0
        threshold_violations = 0

        for r in readings:
            if r.over_threshold:
                time_over_threshold += self.sample_interval
                threshold_violations += 1

        return LeakageStatistics(
            mean_current_ma=float(np.mean(currents)),
            max_current_ma=float(np.max(currents)),
            min_current_ma=float(np.min(currents)),
            std_current_ma=float(np.std(currents)),
            num_readings=len(readings),
            time_over_threshold=time_over_threshold,
            threshold_violations=threshold_violations
        )

    def get_trend(self, window_hours: float = 1.0) -> Optional[float]:
        """
        Calculate leakage current trend (slope).

        Args:
            window_hours: Time window for trend calculation

        Returns:
            Trend in mA/hour, or None if insufficient data
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=window_hours)
        readings = self.get_readings(start_time=cutoff_time)

        if len(readings) < 2:
            return None

        # Convert to arrays
        times = np.array([(r.timestamp - readings[0].timestamp).total_seconds() / 3600
                          for r in readings])
        currents = np.array([r.current_ma for r in readings])

        # Calculate linear fit
        if len(times) > 1:
            coeffs = np.polyfit(times, currents, 1)
            trend = coeffs[0]  # Slope in mA/hour
            return float(trend)

        return None

    def is_monitoring(self) -> bool:
        """Check if monitoring is active"""
        return self._monitoring

    def get_status(self) -> Dict[str, Any]:
        """
        Get monitor status.

        Returns:
            Status information
        """
        current_reading = self.get_current_reading()
        stats = self.get_statistics()

        return {
            "monitoring": self._monitoring,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "sample_interval": self.sample_interval,
            "threshold_ma": self.threshold_ma,
            "critical_threshold_ma": self.critical_threshold_ma,
            "current_reading": {
                "timestamp": current_reading.timestamp.isoformat(),
                "current_ma": current_reading.current_ma,
                "voltage": current_reading.voltage,
                "over_threshold": current_reading.over_threshold
            } if current_reading else None,
            "statistics": {
                "mean_ma": stats.mean_current_ma,
                "max_ma": stats.max_current_ma,
                "min_ma": stats.min_current_ma,
                "std_ma": stats.std_current_ma,
                "num_readings": stats.num_readings,
                "alarm_count": self._alarm_count,
                "threshold_violations": stats.threshold_violations
            } if stats else None,
            "shutdown_triggered": self._shutdown_triggered
        }

    def export_data(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Export readings as list of dictionaries.

        Args:
            start_time: Start of time range
            end_time: End of time range

        Returns:
            List of reading dictionaries
        """
        readings = self.get_readings(start_time, end_time)

        return [
            {
                "timestamp": r.timestamp.isoformat(),
                "elapsed_hours": r.elapsed_hours,
                "current_ma": r.current_ma,
                "voltage": r.voltage,
                "over_threshold": r.over_threshold
            }
            for r in readings
        ]


class LeakageCurrentAnalyzer:
    """
    Analyze leakage current patterns and detect anomalies.
    """

    @staticmethod
    def detect_anomalies(
        readings: List[LeakageCurrentReading],
        threshold_std: float = 3.0
    ) -> List[LeakageCurrentReading]:
        """
        Detect anomalous readings using statistical methods.

        Args:
            readings: List of readings to analyze
            threshold_std: Number of standard deviations for anomaly

        Returns:
            List of anomalous readings
        """
        if len(readings) < 10:
            return []

        currents = np.array([r.current_ma for r in readings])
        mean = np.mean(currents)
        std = np.std(currents)

        anomalies = []
        for reading in readings:
            z_score = abs(reading.current_ma - mean) / std if std > 0 else 0
            if z_score > threshold_std:
                anomalies.append(reading)

        return anomalies

    @staticmethod
    def calculate_stability(
        readings: List[LeakageCurrentReading]
    ) -> float:
        """
        Calculate stability metric (coefficient of variation).

        Args:
            readings: List of readings

        Returns:
            Coefficient of variation (std/mean)
        """
        if not readings:
            return 0.0

        currents = [r.current_ma for r in readings]
        mean = np.mean(currents)
        std = np.std(currents)

        return (std / mean) if mean > 0 else 0.0

    @staticmethod
    def predict_time_to_threshold(
        readings: List[LeakageCurrentReading],
        threshold_ma: float
    ) -> Optional[float]:
        """
        Predict time until threshold is reached based on trend.

        Args:
            readings: List of readings
            threshold_ma: Threshold in mA

        Returns:
            Predicted hours until threshold, or None if not trending up
        """
        if len(readings) < 10:
            return None

        # Calculate trend
        times = np.array([(r.timestamp - readings[0].timestamp).total_seconds() / 3600
                          for r in readings])
        currents = np.array([r.current_ma for r in readings])

        # Linear fit
        coeffs = np.polyfit(times, currents, 1)
        slope = coeffs[0]
        intercept = coeffs[1]

        # If trending down or flat, no prediction
        if slope <= 0:
            return None

        # Calculate time to threshold
        current_current = currents[-1]
        hours_to_threshold = (threshold_ma - current_current) / slope

        return float(hours_to_threshold) if hours_to_threshold > 0 else None
