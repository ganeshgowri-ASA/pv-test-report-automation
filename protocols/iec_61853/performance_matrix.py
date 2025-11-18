"""
Performance Matrix Testing - IEC 61853-1
=========================================

Implements the 35-point performance matrix testing requirement:
- 7 irradiance levels: 100, 200, 400, 600, 800, 1000, 1100 W/m²
- 5 temperature levels: -25, 0, 25, 50, 75 °C
- Full I-V curve sweep at each condition
- Automated test sequencing
- Data validation and quality checks

The performance matrix characterizes module behavior across operating conditions
and is used to create the Pmax(G, T) performance surface model.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
import numpy as np
from enum import Enum

from .models import (
    MatrixTestPointData,
    IVCurve,
    IVPoint,
    TestStatus,
)
from .temperature_control import ChamberController, StabilizationCriteria


# Configure logging
logger = logging.getLogger(__name__)


# ==================== Constants ====================

# IEC 61853-1 standard test conditions
STANDARD_TEMPERATURES = [-25.0, 0.0, 25.0, 50.0, 75.0]  # °C
STANDARD_IRRADIANCES = [100.0, 200.0, 400.0, 600.0, 800.0, 1000.0, 1100.0]  # W/m²

# Standard Test Conditions (STC)
STC_TEMPERATURE = 25.0  # °C
STC_IRRADIANCE = 1000.0  # W/m²
STC_SPECTRUM = "AM1.5G"


# ==================== Enumerations ====================

class TestSequenceMode(str, Enum):
    """Test sequence execution mode"""
    TEMPERATURE_FIRST = "temperature_first"  # Change temp, then sweep irradiance
    IRRADIANCE_FIRST = "irradiance_first"  # Change irradiance, then sweep temperature
    OPTIMIZED = "optimized"  # Minimize thermal cycles


# ==================== Data Classes ====================

@dataclass
class MatrixTestPoint:
    """Single point in the performance matrix"""
    temperature: float  # °C
    irradiance: float  # W/m²
    data: Optional[MatrixTestPointData] = None
    status: TestStatus = TestStatus.PENDING
    error_message: Optional[str] = None
    retry_count: int = 0


@dataclass
class MatrixTestConfig:
    """Configuration for matrix testing"""
    temperatures: List[float] = field(default_factory=lambda: STANDARD_TEMPERATURES.copy())
    irradiances: List[float] = field(default_factory=lambda: STANDARD_IRRADIANCES.copy())
    sequence_mode: TestSequenceMode = TestSequenceMode.TEMPERATURE_FIRST
    stabilization_criteria: StabilizationCriteria = field(default_factory=StabilizationCriteria)
    max_retries: int = 3
    iv_sweep_points: int = 100
    iv_sweep_rate: float = 10.0  # V/s
    validation_enabled: bool = True


@dataclass
class MatrixTestResults:
    """Results from complete matrix test"""
    test_points: List[MatrixTestPoint]
    total_points: int
    successful_points: int
    failed_points: int
    start_time: datetime
    end_time: datetime
    total_duration: float  # seconds
    config: MatrixTestConfig


# ==================== I-V Curve Acquisition ====================

class IVCurveAcquisition:
    """
    I-V curve acquisition system

    This is a placeholder for actual hardware interface.
    In production, this would interface with:
    - Source meter units (SMU)
    - Electronic loads
    - Data acquisition systems
    """

    def __init__(
        self,
        instrument_address: Optional[str] = None,
        sweep_points: int = 100,
        sweep_rate: float = 10.0  # V/s
    ):
        self.instrument_address = instrument_address
        self.sweep_points = sweep_points
        self.sweep_rate = sweep_rate
        self._connected = False

    def connect(self) -> bool:
        """Connect to I-V curve acquisition hardware"""
        logger.info("Connecting to I-V acquisition system...")
        # TODO: Implement actual hardware connection
        self._connected = True
        return True

    def disconnect(self):
        """Disconnect from hardware"""
        logger.info("Disconnecting I-V acquisition system...")
        self._connected = False

    def acquire_iv_curve(
        self,
        voc_estimate: float = 50.0,
        isc_estimate: float = 10.0
    ) -> IVCurve:
        """
        Acquire I-V curve from module

        Args:
            voc_estimate: Estimated open circuit voltage (V)
            isc_estimate: Estimated short circuit current (A)

        Returns:
            IVCurve: Complete I-V curve data
        """
        if not self._connected:
            raise RuntimeError("I-V acquisition system not connected")

        logger.info(f"Acquiring I-V curve ({self.sweep_points} points)")

        # TODO: Replace with actual hardware acquisition
        # This is a simulated curve for demonstration
        iv_points = self._simulate_iv_curve(voc_estimate, isc_estimate)

        # Extract key parameters
        voc, isc, vmp, imp, pmax, ff = self._extract_parameters(iv_points)

        return IVCurve(
            points=iv_points,
            voc=voc,
            isc=isc,
            vmp=vmp,
            imp=imp,
            pmax=pmax,
            ff=ff
        )

    def _simulate_iv_curve(
        self,
        voc: float,
        isc: float,
        ff: float = 0.75
    ) -> List[IVPoint]:
        """
        Simulate realistic I-V curve (for testing/demo)

        Uses single-diode model approximation
        """
        n_points = self.sweep_points
        voltages = np.linspace(0, voc, n_points)
        currents = []

        # Simplified single-diode model
        for v in voltages:
            # I = Isc * (1 - exp((V - Voc) / (n * Vt)))
            # Simplified for demonstration
            vt = 0.026  # Thermal voltage at 25°C
            n = 1.5  # Ideality factor
            i = isc * (1 - np.exp((v - voc) / (n * vt * 60)))  # Scaled for cells in series
            i = max(0, i)  # No negative current
            currents.append(i)

        currents = np.array(currents)
        powers = voltages * currents

        return [
            IVPoint(voltage=float(v), current=float(i), power=float(p))
            for v, i, p in zip(voltages, currents, powers)
        ]

    def _extract_parameters(self, iv_points: List[IVPoint]) -> Tuple[float, float, float, float, float, float]:
        """Extract key parameters from I-V curve"""
        voltages = np.array([p.voltage for p in iv_points])
        currents = np.array([p.current for p in iv_points])
        powers = np.array([p.power for p in iv_points])

        # Voc: voltage at zero current
        voc = float(voltages[np.argmin(np.abs(currents))])

        # Isc: current at zero voltage
        isc = float(currents[np.argmin(np.abs(voltages))])

        # Pmax and MPP
        pmax_idx = np.argmax(powers)
        pmax = float(powers[pmax_idx])
        vmp = float(voltages[pmax_idx])
        imp = float(currents[pmax_idx])

        # Fill factor
        ff = pmax / (voc * isc) if (voc > 0 and isc > 0) else 0.0

        return voc, isc, vmp, imp, pmax, ff


# ==================== Performance Matrix Test ====================

class PerformanceMatrixTest:
    """
    Performance matrix test execution engine

    Coordinates temperature chamber, irradiance source, and I-V acquisition
    to execute the full 35-point (or custom) performance matrix.
    """

    def __init__(
        self,
        chamber_controller: ChamberController,
        iv_acquisition: IVCurveAcquisition,
        config: Optional[MatrixTestConfig] = None
    ):
        self.chamber = chamber_controller
        self.iv_acq = iv_acquisition
        self.config = config or MatrixTestConfig()

        self._test_points: List[MatrixTestPoint] = []
        self._current_test: Optional[MatrixTestResults] = None
        self._start_time: Optional[datetime] = None

        logger.info("Performance matrix test initialized")

    def generate_test_sequence(self) -> List[MatrixTestPoint]:
        """
        Generate optimized test sequence

        Returns:
            List of test points in execution order
        """
        temperatures = self.config.temperatures
        irradiances = self.config.irradiances

        test_points = []

        if self.config.sequence_mode == TestSequenceMode.TEMPERATURE_FIRST:
            # For each temperature, sweep all irradiances
            for temp in temperatures:
                for irrad in irradiances:
                    test_points.append(MatrixTestPoint(
                        temperature=temp,
                        irradiance=irrad
                    ))

        elif self.config.sequence_mode == TestSequenceMode.IRRADIANCE_FIRST:
            # For each irradiance, sweep all temperatures
            for irrad in irradiances:
                for temp in temperatures:
                    test_points.append(MatrixTestPoint(
                        temperature=temp,
                        irradiance=irrad
                    ))

        elif self.config.sequence_mode == TestSequenceMode.OPTIMIZED:
            # Minimize thermal cycles by grouping nearby temperatures
            # Sort temperatures and use zig-zag pattern
            sorted_temps = sorted(temperatures)
            for i, temp in enumerate(sorted_temps):
                # Alternate irradiance order to minimize changes
                irrad_seq = irradiances if i % 2 == 0 else list(reversed(irradiances))
                for irrad in irrad_seq:
                    test_points.append(MatrixTestPoint(
                        temperature=temp,
                        irradiance=irrad
                    ))

        logger.info(
            f"Generated test sequence: {len(test_points)} points "
            f"(mode: {self.config.sequence_mode.value})"
        )
        return test_points

    def run_matrix_test(self) -> MatrixTestResults:
        """
        Execute complete performance matrix test

        Returns:
            MatrixTestResults with all test point data
        """
        self._start_time = datetime.utcnow()
        logger.info("Starting performance matrix test")

        # Generate test sequence
        self._test_points = self.generate_test_sequence()

        # Execute each test point
        for i, point in enumerate(self._test_points):
            logger.info(
                f"Test point {i+1}/{len(self._test_points)}: "
                f"T={point.temperature}°C, G={point.irradiance}W/m²"
            )

            success = self._execute_test_point(point)

            if not success and point.retry_count < self.config.max_retries:
                logger.warning(f"Retrying test point (attempt {point.retry_count + 1})")
                point.retry_count += 1
                success = self._execute_test_point(point)

            if success:
                point.status = TestStatus.COMPLETED
                logger.info(f"Test point completed: Pmax={point.data.iv_curve.pmax:.2f}W")
            else:
                point.status = TestStatus.FAILED
                logger.error(f"Test point failed: {point.error_message}")

        # Compile results
        end_time = datetime.utcnow()
        duration = (end_time - self._start_time).total_seconds()

        successful = sum(1 for p in self._test_points if p.status == TestStatus.COMPLETED)
        failed = len(self._test_points) - successful

        results = MatrixTestResults(
            test_points=self._test_points,
            total_points=len(self._test_points),
            successful_points=successful,
            failed_points=failed,
            start_time=self._start_time,
            end_time=end_time,
            total_duration=duration,
            config=self.config
        )

        logger.info(
            f"Matrix test completed: {successful}/{len(self._test_points)} successful "
            f"in {duration/3600:.2f} hours"
        )

        self._current_test = results
        return results

    def _execute_test_point(self, point: MatrixTestPoint) -> bool:
        """
        Execute single test point

        Args:
            point: Test point to execute

        Returns:
            bool: True if successful
        """
        try:
            point.status = TestStatus.IN_PROGRESS

            # Step 1: Set chamber temperature
            logger.info(f"Setting temperature to {point.temperature}°C")
            if not self.chamber.goto_temperature(
                point.temperature,
                wait_stable=True,
                criteria=self.config.stabilization_criteria
            ):
                point.error_message = "Failed to stabilize temperature"
                return False

            # Step 2: Set irradiance
            # TODO: Implement irradiance source control
            logger.info(f"Setting irradiance to {point.irradiance}W/m²")
            # self.irradiance_source.set_irradiance(point.irradiance)

            # Step 3: Wait for stabilization
            point.status = TestStatus.STABILIZING
            import time
            time.sleep(30)  # Allow system to stabilize

            # Step 4: Acquire I-V curve
            point.status = TestStatus.MEASURING
            logger.info("Acquiring I-V curve")
            iv_curve = self.iv_acq.acquire_iv_curve()

            # Step 5: Get actual conditions
            chamber_status = self.chamber.get_status()

            # Step 6: Create test point data
            point.data = MatrixTestPointData(
                temperature=point.temperature,
                irradiance=point.irradiance,
                iv_curve=iv_curve,
                timestamp=datetime.utcnow(),
                stabilization_time=30.0,  # TODO: Track actual time
                chamber_temp_actual=chamber_status['temperature'],
                chamber_temp_stability=chamber_status['stability'],
                irradiance_actual=point.irradiance,  # TODO: Measure actual
                irradiance_uniformity=98.5  # TODO: Measure actual
            )

            # Step 7: Validate data
            if self.config.validation_enabled:
                if not self._validate_test_point(point):
                    point.error_message = "Data validation failed"
                    return False

            return True

        except Exception as e:
            logger.error(f"Error executing test point: {e}", exc_info=True)
            point.error_message = str(e)
            return False

    def _validate_test_point(self, point: MatrixTestPoint) -> bool:
        """
        Validate test point data quality

        Checks:
        - Temperature stability
        - Irradiance uniformity
        - I-V curve quality
        """
        if not point.data:
            return False

        # Check temperature stability
        if point.data.chamber_temp_stability > 2.0:
            logger.warning(
                f"Temperature stability outside tolerance: "
                f"±{point.data.chamber_temp_stability}°C"
            )
            return False

        # Check irradiance uniformity
        if point.data.irradiance_uniformity < 95.0:
            logger.warning(
                f"Irradiance uniformity low: {point.data.irradiance_uniformity}%"
            )
            return False

        # Check I-V curve sanity
        iv = point.data.iv_curve
        if iv.ff < 0.5 or iv.ff > 0.9:
            logger.warning(f"Fill factor outside expected range: {iv.ff:.3f}")
            return False

        if iv.pmax <= 0:
            logger.error("Invalid Pmax: must be positive")
            return False

        return True

    def get_test_point(
        self,
        temperature: float,
        irradiance: float
    ) -> Optional[MatrixTestPoint]:
        """Get specific test point data"""
        for point in self._test_points:
            if (abs(point.temperature - temperature) < 0.1 and
                abs(point.irradiance - irradiance) < 1.0):
                return point
        return None

    def get_results(self) -> Optional[MatrixTestResults]:
        """Get current test results"""
        return self._current_test

    def export_to_dict(self) -> Dict[str, Any]:
        """Export test results to dictionary"""
        if not self._current_test:
            return {}

        return {
            "total_points": self._current_test.total_points,
            "successful_points": self._current_test.successful_points,
            "failed_points": self._current_test.failed_points,
            "start_time": self._current_test.start_time.isoformat(),
            "end_time": self._current_test.end_time.isoformat(),
            "duration_hours": self._current_test.total_duration / 3600,
            "test_points": [
                {
                    "temperature": p.temperature,
                    "irradiance": p.irradiance,
                    "status": p.status.value,
                    "voc": p.data.iv_curve.voc if p.data else None,
                    "isc": p.data.iv_curve.isc if p.data else None,
                    "pmax": p.data.iv_curve.pmax if p.data else None,
                    "ff": p.data.iv_curve.ff if p.data else None,
                }
                for p in self._current_test.test_points
            ]
        }
