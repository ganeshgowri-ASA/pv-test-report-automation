"""
IEC 62804 PID Testing Protocol - Main Test Controller

This module provides the main controller for automated IEC 62804 PID testing.
Orchestrates chamber control, voltage application, flash testing, and monitoring.
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
from dataclasses import dataclass

from .models import TestMethod, TestStatus as DBTestStatus, TestResult as DBTestResult
from .chamber_control import (
    ChamberControllerBase, ChamberSetpoint, create_chamber_controller
)
from .voltage_control import (
    VoltageSupplyBase, VoltageSupplyConfig, create_voltage_supply,
    InterlockType
)
from .flash_tester import FlashTesterBase, create_flash_tester, FlashTestScheduler
from .leakage_monitor import LeakageCurrentMonitor
from .degradation_analyzer import DegradationAnalyzer, TestResult
from .recovery_test import PIDRecoveryTest, RecoveryMethod

logger = logging.getLogger(__name__)


class TestPhase(Enum):
    """Test execution phases"""
    INITIALIZATION = "initialization"
    INITIAL_FLASH = "initial_flash"
    CHAMBER_STABILIZATION = "chamber_stabilization"
    VOLTAGE_APPLICATION = "voltage_application"
    PID_STRESS = "pid_stress"
    INTERIM_FLASH = "interim_flash"
    FINAL_FLASH = "final_flash"
    RECOVERY = "recovery"
    SHUTDOWN = "shutdown"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


@dataclass
class TestConfiguration:
    """IEC 62804 test configuration"""
    # Module information
    module_serial: str
    module_type: str = "monofacial"
    manufacturer: Optional[str] = None
    model: Optional[str] = None

    # Test parameters
    test_method: TestMethod = TestMethod.METHOD_B
    voltage: float = -1000.0  # V
    duration_hours: int = 96  # hours
    temperature: float = 60.0  # °C
    humidity: Optional[float] = 85.0  # %RH

    # Flash test schedule (hours from start)
    flash_intervals: List[float] = None

    # Recovery testing
    recovery_enabled: bool = False
    recovery_duration_hours: int = 24
    recovery_method: RecoveryMethod = RecoveryMethod.PASSIVE

    # Safety limits
    leakage_threshold_ma: float = 50.0
    critical_leakage_ma: float = 100.0

    # Operator
    operator: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self):
        """Set default flash intervals if not specified"""
        if self.flash_intervals is None:
            self.flash_intervals = [0, 24, 48, 72, 96]  # Standard IEC 62804 schedule


class IEC62804TestController:
    """
    Main controller for IEC 62804 PID testing.

    Provides complete automation of PID testing including:
    - Chamber environmental control
    - High voltage application
    - Automated flash testing
    - Leakage current monitoring
    - Degradation analysis
    - Safety monitoring and emergency shutdown
    - Optional recovery testing
    """

    def __init__(
        self,
        config: TestConfiguration,
        chamber: ChamberControllerBase,
        voltage_supply: VoltageSupplyBase,
        flash_tester: FlashTesterBase,
        state_callback: Optional[Callable] = None
    ):
        """
        Initialize test controller.

        Args:
            config: Test configuration
            chamber: Climate chamber controller
            voltage_supply: High voltage supply controller
            flash_tester: Flash tester / I-V tracer
            state_callback: Function to call on state changes
        """
        self.config = config
        self.chamber = chamber
        self.voltage_supply = voltage_supply
        self.flash_tester = flash_tester
        self.state_callback = state_callback

        # Test state
        self.test_id: Optional[int] = None
        self.phase = TestPhase.INITIALIZATION
        self.status = DBTestStatus.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

        # Components
        self.leakage_monitor: Optional[LeakageCurrentMonitor] = None
        self.degradation_analyzer: Optional[DegradationAnalyzer] = None
        self.flash_scheduler: Optional[FlashTestScheduler] = None
        self.recovery_test: Optional[PIDRecoveryTest] = None

        # Data storage
        self.flash_results: List[Dict[str, Any]] = []
        self.chamber_logs: List[Dict[str, Any]] = []

        # Control flags
        self._running = False
        self._abort_requested = False
        self._emergency_stop = False
        self._test_thread: Optional[threading.Thread] = None

        # Results
        self.initial_pmax: Optional[float] = None
        self.final_pmax: Optional[float] = None
        self.test_result: Optional[TestResult] = None

    def initialize(self) -> bool:
        """
        Initialize test equipment and connections.

        Returns:
            True if initialization successful
        """
        logger.info("Initializing IEC 62804 test equipment")
        self._set_phase(TestPhase.INITIALIZATION)

        try:
            # Connect to chamber
            if not self.chamber.connect():
                logger.error("Failed to connect to chamber")
                return False

            # Connect to voltage supply
            if not self.voltage_supply.connect():
                logger.error("Failed to connect to voltage supply")
                return False

            # Connect to flash tester
            if not self.flash_tester.connect():
                logger.error("Failed to connect to flash tester")
                return False

            # Initialize leakage current monitor
            self.leakage_monitor = LeakageCurrentMonitor(
                voltage_supply=self.voltage_supply,
                threshold_ma=self.config.leakage_threshold_ma,
                critical_threshold_ma=self.config.critical_leakage_ma,
                sample_interval=60.0,  # 1 minute
                alarm_callback=self._leakage_alarm_callback,
                emergency_callback=self._emergency_shutdown_callback
            )

            # Set safety interlocks
            self.voltage_supply.set_interlock(InterlockType.DOOR, True)

            logger.info("Initialization complete")
            return True

        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            return False

    def run_test(self) -> bool:
        """
        Run complete IEC 62804 test sequence.

        Returns:
            True if test completed successfully
        """
        if self._running:
            logger.warning("Test already running")
            return False

        self._running = True
        self._abort_requested = False
        self._emergency_stop = False

        # Run test in background thread
        self._test_thread = threading.Thread(
            target=self._test_sequence,
            daemon=False,
            name="IEC62804TestController"
        )
        self._test_thread.start()

        return True

    def _test_sequence(self):
        """Main test sequence (runs in background thread)"""
        try:
            self.start_time = datetime.utcnow()
            self.status = DBTestStatus.RUNNING

            # Step 1: Initial flash test
            if not self._perform_initial_flash():
                self._fail_test("Initial flash test failed")
                return

            if self._check_abort():
                return

            # Step 2: Setup chamber
            if not self._setup_chamber():
                self._fail_test("Chamber setup failed")
                return

            if self._check_abort():
                return

            # Step 3: Wait for chamber stabilization
            if not self._wait_chamber_stabilization():
                self._fail_test("Chamber stabilization failed")
                return

            if self._check_abort():
                return

            # Step 4: Apply voltage
            if not self._apply_voltage():
                self._fail_test("Voltage application failed")
                return

            # Step 5: Start monitoring
            self._start_monitoring()

            # Step 6: PID stress with interim flash tests
            if not self._run_pid_stress():
                self._fail_test("PID stress test failed")
                return

            # Step 7: Final flash test
            if not self._perform_final_flash():
                self._fail_test("Final flash test failed")
                return

            # Step 8: Optional recovery test
            if self.config.recovery_enabled:
                if not self._run_recovery_test():
                    logger.warning("Recovery test failed")

            # Step 9: Shutdown
            self._shutdown()

            # Mark test complete
            self._complete_test()

        except Exception as e:
            logger.error(f"Test sequence error: {e}", exc_info=True)
            self._fail_test(f"Exception: {e}")

        finally:
            self._running = False

    def _perform_initial_flash(self) -> bool:
        """Perform initial flash test"""
        logger.info("Performing initial flash test")
        self._set_phase(TestPhase.INITIAL_FLASH)

        try:
            iv_data = self.flash_tester.measure_iv_curve()
            self.initial_pmax = iv_data.pmax

            # Initialize degradation analyzer
            self.degradation_analyzer = DegradationAnalyzer(self.initial_pmax)

            # Initialize flash scheduler
            self.flash_scheduler = FlashTestScheduler(
                tester=self.flash_tester,
                test_start_time=self.start_time,
                test_intervals=self.config.flash_intervals
            )

            # Record flash result
            self.flash_results.append({
                "elapsed_hours": 0.0,
                "timestamp": iv_data.timestamp,
                "pmax": iv_data.pmax,
                "voc": iv_data.voc,
                "isc": iv_data.isc,
                "ff": iv_data.ff,
                "degradation_pct": 0.0
            })

            # Add to degradation analyzer
            self.degradation_analyzer.add_measurement(
                timestamp=iv_data.timestamp,
                elapsed_hours=0.0,
                pmax=iv_data.pmax,
                voc=iv_data.voc,
                isc=iv_data.isc,
                ff=iv_data.ff
            )

            logger.info(f"Initial Pmax: {self.initial_pmax:.2f}W")
            return True

        except Exception as e:
            logger.error(f"Initial flash test failed: {e}", exc_info=True)
            return False

    def _setup_chamber(self) -> bool:
        """Setup chamber conditions"""
        logger.info(f"Setting up chamber for Method {self.config.test_method.value}")
        self._set_phase(TestPhase.CHAMBER_STABILIZATION)

        try:
            # Create setpoint
            setpoint = ChamberSetpoint(
                temperature=self.config.temperature,
                humidity=self.config.humidity if self.config.test_method != TestMethod.METHOD_C else None
            )

            # Set chamber setpoint
            if not self.chamber.set_setpoint(setpoint):
                logger.error("Failed to set chamber setpoint")
                return False

            # Start chamber
            if not self.chamber.start():
                logger.error("Failed to start chamber")
                return False

            return True

        except Exception as e:
            logger.error(f"Chamber setup failed: {e}", exc_info=True)
            return False

    def _wait_chamber_stabilization(self, timeout: float = 7200) -> bool:
        """Wait for chamber to stabilize"""
        logger.info("Waiting for chamber stabilization")

        return self.chamber.wait_for_setpoint(timeout=timeout, check_interval=30)

    def _apply_voltage(self) -> bool:
        """Apply high voltage"""
        logger.info(f"Applying voltage: {self.config.voltage}V")
        self._set_phase(TestPhase.VOLTAGE_APPLICATION)

        try:
            # Set current limit
            if not self.voltage_supply.set_current_limit(self.config.critical_leakage_ma / 1000.0):
                logger.error("Failed to set current limit")
                return False

            # Ramp to voltage
            if not self.voltage_supply.ramp_to_voltage(self.config.voltage, timeout=60.0):
                logger.error("Failed to ramp voltage")
                return False

            logger.info("Voltage applied successfully")
            return True

        except Exception as e:
            logger.error(f"Voltage application failed: {e}", exc_info=True)
            return False

    def _start_monitoring(self):
        """Start continuous monitoring"""
        logger.info("Starting leakage current monitoring")

        if self.leakage_monitor:
            self.leakage_monitor.start_monitoring()

    def _run_pid_stress(self) -> bool:
        """Run PID stress test with interim flash tests"""
        logger.info(f"Starting PID stress test ({self.config.duration_hours}h)")
        self._set_phase(TestPhase.PID_STRESS)

        test_end_time = self.start_time + timedelta(hours=self.config.duration_hours)

        while datetime.utcnow() < test_end_time:
            if self._check_abort():
                return False

            if self._emergency_stop:
                logger.critical("Emergency stop triggered")
                return False

            # Check if flash test is due
            elapsed = (datetime.utcnow() - self.start_time).total_seconds() / 3600.0

            if self.flash_scheduler.is_test_due(datetime.utcnow()):
                interval = self.flash_scheduler.get_current_interval(datetime.utcnow())
                if interval is not None:
                    self._perform_interim_flash(interval)
                    self.flash_scheduler.mark_completed(interval)

            # Monitor chamber and log
            self._log_chamber_conditions()

            # Sleep for a bit
            time.sleep(60)  # Check every minute

        return True

    def _perform_interim_flash(self, elapsed_hours: float) -> bool:
        """Perform interim flash test"""
        logger.info(f"Performing interim flash test at {elapsed_hours}h")
        self._set_phase(TestPhase.INTERIM_FLASH)

        try:
            # Disable voltage temporarily
            self.voltage_supply.disable_output()
            time.sleep(5)  # Wait for discharge

            # Measure I-V curve
            iv_data = self.flash_tester.measure_iv_curve()

            # Record result
            degradation_pct = self.degradation_analyzer.calculate_degradation(iv_data.pmax)

            self.flash_results.append({
                "elapsed_hours": elapsed_hours,
                "timestamp": iv_data.timestamp,
                "pmax": iv_data.pmax,
                "voc": iv_data.voc,
                "isc": iv_data.isc,
                "ff": iv_data.ff,
                "degradation_pct": degradation_pct
            })

            # Add to degradation analyzer
            self.degradation_analyzer.add_measurement(
                timestamp=iv_data.timestamp,
                elapsed_hours=elapsed_hours,
                pmax=iv_data.pmax,
                voc=iv_data.voc,
                isc=iv_data.isc,
                ff=iv_data.ff
            )

            logger.info(
                f"Interim flash at {elapsed_hours}h: "
                f"{iv_data.pmax:.2f}W ({degradation_pct:.2f}% degradation)"
            )

            # Re-enable voltage
            time.sleep(5)
            self.voltage_supply.enable_output()

            # Return to PID stress phase
            self._set_phase(TestPhase.PID_STRESS)

            return True

        except Exception as e:
            logger.error(f"Interim flash test failed: {e}", exc_info=True)
            return False

    def _perform_final_flash(self) -> bool:
        """Perform final flash test"""
        logger.info("Performing final flash test")
        self._set_phase(TestPhase.FINAL_FLASH)

        try:
            # Disable voltage
            self.voltage_supply.disable_output()
            time.sleep(10)  # Wait for discharge

            # Measure I-V curve
            iv_data = self.flash_tester.measure_iv_curve()
            self.final_pmax = iv_data.pmax

            # Calculate final degradation
            degradation_pct = self.degradation_analyzer.calculate_degradation(self.final_pmax)

            elapsed_hours = (datetime.utcnow() - self.start_time).total_seconds() / 3600.0

            self.flash_results.append({
                "elapsed_hours": elapsed_hours,
                "timestamp": iv_data.timestamp,
                "pmax": iv_data.pmax,
                "voc": iv_data.voc,
                "isc": iv_data.isc,
                "ff": iv_data.ff,
                "degradation_pct": degradation_pct
            })

            # Add to degradation analyzer
            self.degradation_analyzer.add_measurement(
                timestamp=iv_data.timestamp,
                elapsed_hours=elapsed_hours,
                pmax=iv_data.pmax,
                voc=iv_data.voc,
                isc=iv_data.isc,
                ff=iv_data.ff
            )

            # Determine test result
            analysis = self.degradation_analyzer.analyze(test_complete=True)
            self.test_result = analysis.test_result

            logger.info(
                f"Final Pmax: {self.final_pmax:.2f}W "
                f"({degradation_pct:.2f}% degradation) - "
                f"Result: {self.test_result.value.upper()}"
            )

            return True

        except Exception as e:
            logger.error(f"Final flash test failed: {e}", exc_info=True)
            return False

    def _run_recovery_test(self) -> bool:
        """Run PID recovery test"""
        logger.info("Starting PID recovery test")
        self._set_phase(TestPhase.RECOVERY)

        try:
            # Initialize recovery test
            self.recovery_test = PIDRecoveryTest(
                flash_tester=self.flash_tester,
                initial_pmax=self.initial_pmax,
                degraded_pmax=self.final_pmax,
                recovery_method=self.config.recovery_method
            )

            self.recovery_test.start_recovery()

            # Recovery intervals (0, 1h, 2h, 4h, 8h, 24h)
            recovery_intervals = [0, 1, 2, 4, 8, 24]

            recovery_end = datetime.utcnow() + timedelta(hours=self.config.recovery_duration_hours)

            for interval in recovery_intervals:
                wait_until = datetime.utcnow() + timedelta(hours=interval)

                # Wait for interval
                while datetime.utcnow() < wait_until and datetime.utcnow() < recovery_end:
                    if self._check_abort():
                        return False
                    time.sleep(60)

                if datetime.utcnow() >= recovery_end:
                    break

                # Measure recovery
                iv_data = self.flash_tester.measure_iv_curve()
                self.recovery_test.add_measurement(iv_data.pmax)

                recovery_pct = self.recovery_test.get_current_recovery()
                logger.info(f"Recovery at {interval}h: {iv_data.pmax:.2f}W ({recovery_pct:.1f}%)")

            # Analyze recovery
            recovery_result = self.recovery_test.analyze()
            logger.info(
                f"Recovery complete: {recovery_result.recovery_pct:.1f}% "
                f"({recovery_result.classification.value})"
            )

            return True

        except Exception as e:
            logger.error(f"Recovery test failed: {e}", exc_info=True)
            return False

    def _shutdown(self):
        """Shutdown test equipment"""
        logger.info("Shutting down test equipment")
        self._set_phase(TestPhase.SHUTDOWN)

        try:
            # Stop leakage monitoring
            if self.leakage_monitor:
                self.leakage_monitor.stop_monitoring()

            # Disable voltage
            self.voltage_supply.safe_shutdown()

            # Stop chamber
            self.chamber.stop()

        except Exception as e:
            logger.error(f"Shutdown error: {e}", exc_info=True)

    def _complete_test(self):
        """Mark test as completed"""
        self.end_time = datetime.utcnow()
        self.status = DBTestStatus.COMPLETED
        self._set_phase(TestPhase.COMPLETED)

        logger.info("Test completed successfully")

    def _fail_test(self, reason: str):
        """Mark test as failed"""
        logger.error(f"Test failed: {reason}")
        self.end_time = datetime.utcnow()
        self.status = DBTestStatus.FAILED
        self._set_phase(TestPhase.FAILED)

        # Attempt shutdown
        try:
            self._shutdown()
        except:
            pass

    def abort_test(self):
        """Request test abort"""
        logger.warning("Test abort requested")
        self._abort_requested = True

    def _check_abort(self) -> bool:
        """Check if abort requested"""
        if self._abort_requested:
            logger.warning("Aborting test")
            self.end_time = datetime.utcnow()
            self.status = DBTestStatus.ABORTED
            self._set_phase(TestPhase.ABORTED)
            self._shutdown()
            return True
        return False

    def _leakage_alarm_callback(self, reading, issues):
        """Handle leakage current alarm"""
        logger.warning(f"Leakage current alarm: {reading.current_ma}mA")

    def _emergency_shutdown_callback(self, reading):
        """Handle emergency shutdown"""
        logger.critical(f"EMERGENCY SHUTDOWN: Leakage current {reading.current_ma}mA")
        self._emergency_stop = True
        self._shutdown()

    def _log_chamber_conditions(self):
        """Log chamber conditions"""
        reading = self.chamber.get_reading()
        elapsed = (datetime.utcnow() - self.start_time).total_seconds() / 3600.0

        self.chamber_logs.append({
            "timestamp": reading.timestamp,
            "elapsed_hours": elapsed,
            "temperature": reading.temperature,
            "humidity": reading.humidity
        })

    def _set_phase(self, phase: TestPhase):
        """Set test phase"""
        self.phase = phase
        logger.info(f"Test phase: {phase.value}")

        if self.state_callback:
            try:
                self.state_callback(phase, self.status)
            except Exception as e:
                logger.error(f"State callback error: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current test status"""
        elapsed = 0.0
        if self.start_time:
            elapsed = (datetime.utcnow() - self.start_time).total_seconds() / 3600.0

        current_degradation = 0.0
        if self.degradation_analyzer:
            current_degradation = self.degradation_analyzer.get_current_degradation()

        return {
            "status": self.status.value,
            "phase": self.phase.value,
            "elapsed_hours": elapsed,
            "remaining_hours": max(0, self.config.duration_hours - elapsed),
            "progress_pct": min(100, (elapsed / self.config.duration_hours) * 100),
            "initial_pmax": self.initial_pmax,
            "current_degradation_pct": current_degradation,
            "test_result": self.test_result.value if self.test_result else "pending",
            "emergency_stop": self._emergency_stop
        }
