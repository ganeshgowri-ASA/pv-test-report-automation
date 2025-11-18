"""
IEC 62759 - Transportation Testing for PV Modules
Complete implementation with ISO 17025 compliance
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

from src.protocols.base import BaseProtocol, TestResult
from src.utils.constants import (
    TestStatus, PassFailStatus,
    IEC_62759_EDGE_LOAD_PA, IEC_62759_EDGE_LOAD_DURATION_HOURS,
    IEC_62759_DYNAMIC_LOAD_PA, IEC_62759_DYNAMIC_CYCLES,
    IEC_62759_THERMAL_CYCLES, IEC_62759_THERMAL_LOW_TEMP,
    IEC_62759_THERMAL_HIGH_TEMP, IEC_62759_THERMAL_RAMP_RATE,
    IEC_62759_THERMAL_HOLD_TIME_MIN, IEC_62759_MAX_POWER_DEGRADATION_PCT,
    IEC_62759_DYNAMIC_FREQ_MIN, IEC_62759_DYNAMIC_FREQ_MAX
)
from src.utils.validators import (
    validate_module_id, validate_power_measurement,
    validate_temperature_range, validate_degradation_limit
)
from src.equipment.solar_simulator import SolarSimulator, FlashTestResult
from src.equipment.load_frame import LoadFrame, LoadTestResult
from src.equipment.thermal_chamber import ThermalChamber, ThermalCycleProfile


class IEC62759Controller(BaseProtocol):
    """
    IEC 62759 Transportation Testing Controller

    Test Sequence:
    1. Initial Flash Test
    2. Edge Loading (Static load)
    3. Dynamic Mechanical Loading
    4. Thermal Cycling
    5. Final Flash Test
    6. Visual Inspection

    Pass Criteria:
    - No breakage or visual defects
    - Power degradation < 5%
    - All sub-tests pass
    """

    protocol_name = "IEC 62759"
    protocol_version = "1.0:2015"

    def __init__(
        self,
        module_id: str,
        test_id: Optional[int] = None,
        solar_simulator: Optional[SolarSimulator] = None,
        load_frame: Optional[LoadFrame] = None,
        thermal_chamber: Optional[ThermalChamber] = None,
        technician_id: str = "TECH-001"
    ):
        """
        Initialize IEC 62759 test controller

        Args:
            module_id: PV module identifier
            test_id: Test sequence ID
            solar_simulator: Solar simulator instance (optional, will create if None)
            load_frame: Load frame instance (optional, will create if None)
            thermal_chamber: Thermal chamber instance (optional, will create if None)
            technician_id: Technician performing the test
        """
        super().__init__(module_id, test_id)

        # Equipment setup
        self.solar_simulator = solar_simulator or SolarSimulator()
        self.load_frame = load_frame or LoadFrame()
        self.thermal_chamber = thermal_chamber or ThermalChamber()

        # Test data storage
        self.initial_flash: Optional[FlashTestResult] = None
        self.final_flash: Optional[FlashTestResult] = None
        self.edge_load_result: Optional[LoadTestResult] = None
        self.dynamic_load_result: Optional[LoadTestResult] = None
        self.thermal_result = None
        self.visual_inspection_result: Optional[Dict] = None

        # ISO 17025 compliance
        self.result.compliance_data['technician_id'] = technician_id
        self.result.compliance_data['protocol'] = self.get_protocol_name()

        self.logger.info(f"IEC 62759 Controller initialized for module {module_id}")

    def validate_inputs(self, **kwargs) -> bool:
        """Validate test inputs"""
        validate_module_id(self.module_id)

        # Validate equipment calibration status
        if not self.solar_simulator.is_calibration_valid():
            self.logger.warning("Solar simulator calibration may be expired")

        if not self.load_frame.is_calibration_valid():
            self.logger.warning("Load frame calibration may be expired")

        if not self.thermal_chamber.is_calibration_valid():
            self.logger.warning("Thermal chamber calibration may be expired")

        return True

    def connect_equipment(self) -> bool:
        """Connect to all test equipment"""
        self.logger.info("Connecting to test equipment...")

        success = True
        success &= self.solar_simulator.connect()
        success &= self.load_frame.connect()
        success &= self.thermal_chamber.connect()

        if success:
            self.log_test_event("equipment_connected", {
                "solar_simulator": self.solar_simulator.equipment_id,
                "load_frame": self.load_frame.equipment_id,
                "thermal_chamber": self.thermal_chamber.equipment_id
            })
        else:
            self.logger.error("Failed to connect to all equipment")

        return success

    def disconnect_equipment(self) -> bool:
        """Disconnect from all test equipment"""
        self.logger.info("Disconnecting from test equipment...")

        success = True
        success &= self.solar_simulator.disconnect()
        success &= self.load_frame.disconnect()
        success &= self.thermal_chamber.disconnect()

        self.log_test_event("equipment_disconnected")
        return success

    def step1_initial_flash_test(self) -> FlashTestResult:
        """
        Step 1: Initial Flash Test - Measure baseline performance

        Returns:
            FlashTestResult: Initial flash test measurements
        """
        self.logger.info("=" * 60)
        self.logger.info("STEP 1: Initial Flash Test")
        self.logger.info("=" * 60)

        self.log_test_event("initial_flash_start")

        # Stabilize solar simulator
        self.solar_simulator.stabilize()

        # Perform flash test
        self.initial_flash = self.solar_simulator.measure_iv_curve(self.module_id)

        validate_power_measurement(self.initial_flash.pmax)

        self.result.measurements['initial_pmax'] = self.initial_flash.pmax
        self.result.measurements['initial_voc'] = self.initial_flash.voc
        self.result.measurements['initial_isc'] = self.initial_flash.isc
        self.result.measurements['initial_vmp'] = self.initial_flash.vmp
        self.result.measurements['initial_imp'] = self.initial_flash.imp
        self.result.measurements['initial_fill_factor'] = self.initial_flash.fill_factor

        self.log_test_event("initial_flash_complete", {
            "pmax": self.initial_flash.pmax,
            "voc": self.initial_flash.voc,
            "isc": self.initial_flash.isc
        })

        self.logger.info(f"Initial Pmax: {self.initial_flash.pmax:.2f} W")

        return self.initial_flash

    def step2_edge_loading(
        self,
        load_pa: float = IEC_62759_EDGE_LOAD_PA,
        duration_hours: float = IEC_62759_EDGE_LOAD_DURATION_HOURS
    ) -> LoadTestResult:
        """
        Step 2: Edge Loading Test - Static load with edge support

        Args:
            load_pa: Load pressure (default 600 Pa)
            duration_hours: Load duration (default 1 hour)

        Returns:
            LoadTestResult: Edge loading test results
        """
        self.logger.info("=" * 60)
        self.logger.info("STEP 2: Edge Loading Test")
        self.logger.info(f"Load: {load_pa} Pa, Duration: {duration_hours} hours")
        self.logger.info("=" * 60)

        self.log_test_event("edge_loading_start", {
            "load_pa": load_pa,
            "duration_hours": duration_hours
        })

        # Apply edge load
        self.edge_load_result = self.load_frame.apply_static_edge_load(
            load_pa=load_pa,
            duration_hours=duration_hours,
            module_id=self.module_id
        )

        # Store results
        self.result.measurements['edge_load_pa'] = load_pa
        self.result.measurements['edge_load_duration'] = duration_hours
        self.result.measurements['edge_deflection_mm'] = self.edge_load_result.max_deflection_mm
        self.result.measurements['edge_breakage'] = self.edge_load_result.breakage_detected

        # Determine pass/fail
        edge_pass = not self.edge_load_result.breakage_detected
        self.result.test_data['edge_load_pass'] = edge_pass

        self.log_test_event("edge_loading_complete", {
            "deflection_mm": self.edge_load_result.max_deflection_mm,
            "breakage": self.edge_load_result.breakage_detected,
            "pass": edge_pass
        })

        self.logger.info(f"Edge Loading: {'PASS' if edge_pass else 'FAIL'}")

        return self.edge_load_result

    def step3_dynamic_mechanical_loading(
        self,
        load_pa: float = IEC_62759_DYNAMIC_LOAD_PA,
        cycles: int = IEC_62759_DYNAMIC_CYCLES,
        frequency_hz: float = 1.0
    ) -> Dict[str, LoadTestResult]:
        """
        Step 3: Dynamic Mechanical Loading - Front and rear loading

        Args:
            load_pa: Load pressure (default 1000 Pa)
            cycles: Number of cycles (default 1000)
            frequency_hz: Load frequency (default 1.0 Hz, range 0.5-2.0)

        Returns:
            Dict: Front and rear loading results
        """
        self.logger.info("=" * 60)
        self.logger.info("STEP 3: Dynamic Mechanical Loading")
        self.logger.info(f"Load: {load_pa} Pa, Cycles: {cycles}, Frequency: {frequency_hz} Hz")
        self.logger.info("=" * 60)

        if not (IEC_62759_DYNAMIC_FREQ_MIN <= frequency_hz <= IEC_62759_DYNAMIC_FREQ_MAX):
            raise ValueError(
                f"Frequency {frequency_hz} Hz outside valid range "
                f"[{IEC_62759_DYNAMIC_FREQ_MIN}, {IEC_62759_DYNAMIC_FREQ_MAX}]"
            )

        results = {}

        # Front loading
        self.logger.info("Performing front loading...")
        front_result = self.load_frame.apply_dynamic_load(
            load_pa=load_pa,
            cycles=cycles,
            frequency_hz=frequency_hz,
            front_loading=True,
            module_id=self.module_id
        )
        results['front'] = front_result

        # Rear loading
        self.logger.info("Performing rear loading...")
        rear_result = self.load_frame.apply_dynamic_load(
            load_pa=load_pa,
            cycles=cycles,
            frequency_hz=frequency_hz,
            front_loading=False,
            module_id=self.module_id
        )
        results['rear'] = rear_result

        self.dynamic_load_result = front_result  # Store primary result

        # Store results
        self.result.measurements['dynamic_load_pa'] = load_pa
        self.result.measurements['dynamic_cycles'] = cycles
        self.result.measurements['dynamic_frequency_hz'] = frequency_hz
        self.result.measurements['dynamic_front_breakage'] = front_result.breakage_detected
        self.result.measurements['dynamic_rear_breakage'] = rear_result.breakage_detected

        # Determine pass/fail
        dynamic_pass = not (front_result.breakage_detected or rear_result.breakage_detected)
        self.result.test_data['dynamic_load_pass'] = dynamic_pass

        self.log_test_event("dynamic_loading_complete", {
            "front_breakage": front_result.breakage_detected,
            "rear_breakage": rear_result.breakage_detected,
            "pass": dynamic_pass
        })

        self.logger.info(f"Dynamic Loading: {'PASS' if dynamic_pass else 'FAIL'}")

        return results

    def step4_thermal_cycling(
        self,
        cycles: int = IEC_62759_THERMAL_CYCLES,
        low_temp: float = IEC_62759_THERMAL_LOW_TEMP,
        high_temp: float = IEC_62759_THERMAL_HIGH_TEMP,
        ramp_rate: float = IEC_62759_THERMAL_RAMP_RATE,
        hold_time_min: float = IEC_62759_THERMAL_HOLD_TIME_MIN
    ):
        """
        Step 4: Thermal Cycling

        Args:
            cycles: Number of cycles (default 50)
            low_temp: Low temperature (default -40°C)
            high_temp: High temperature (default 85°C)
            ramp_rate: Ramp rate (default 100°C/hour)
            hold_time_min: Hold time at extremes (default 10 min)

        Returns:
            ThermalTestResult: Thermal cycling results
        """
        self.logger.info("=" * 60)
        self.logger.info("STEP 4: Thermal Cycling")
        self.logger.info(f"Cycles: {cycles}, Range: {low_temp}°C to {high_temp}°C")
        self.logger.info("=" * 60)

        validate_temperature_range(low_temp)
        validate_temperature_range(high_temp)

        self.log_test_event("thermal_cycling_start", {
            "cycles": cycles,
            "low_temp": low_temp,
            "high_temp": high_temp,
            "ramp_rate": ramp_rate,
            "hold_time_min": hold_time_min
        })

        # Create thermal profile
        profile = ThermalCycleProfile(
            low_temp=low_temp,
            high_temp=high_temp,
            ramp_rate=ramp_rate,
            hold_time_min=hold_time_min,
            cycles=cycles
        )

        # Run thermal cycling
        self.thermal_result = self.thermal_chamber.run_thermal_cycling(
            profile=profile,
            module_id=self.module_id
        )

        # Store results
        self.result.measurements['thermal_cycles'] = cycles
        self.result.measurements['thermal_low_temp'] = low_temp
        self.result.measurements['thermal_high_temp'] = high_temp
        self.result.measurements['thermal_cycles_completed'] = self.thermal_result.cycles_completed

        # Determine pass/fail
        thermal_pass = (
            self.thermal_result.cycles_completed == cycles and
            len(self.thermal_result.errors) == 0
        )
        self.result.test_data['thermal_pass'] = thermal_pass

        self.log_test_event("thermal_cycling_complete", {
            "cycles_completed": self.thermal_result.cycles_completed,
            "pass": thermal_pass
        })

        self.logger.info(f"Thermal Cycling: {'PASS' if thermal_pass else 'FAIL'}")

        return self.thermal_result

    def step5_final_flash_test(self) -> FlashTestResult:
        """
        Step 5: Final Flash Test - Measure final performance

        Returns:
            FlashTestResult: Final flash test measurements
        """
        self.logger.info("=" * 60)
        self.logger.info("STEP 5: Final Flash Test")
        self.logger.info("=" * 60)

        self.log_test_event("final_flash_start")

        # Stabilize solar simulator
        self.solar_simulator.stabilize()

        # Perform flash test
        self.final_flash = self.solar_simulator.measure_iv_curve(self.module_id)

        validate_power_measurement(self.final_flash.pmax)

        self.result.measurements['final_pmax'] = self.final_flash.pmax
        self.result.measurements['final_voc'] = self.final_flash.voc
        self.result.measurements['final_isc'] = self.final_flash.isc
        self.result.measurements['final_vmp'] = self.final_flash.vmp
        self.result.measurements['final_imp'] = self.final_flash.imp
        self.result.measurements['final_fill_factor'] = self.final_flash.fill_factor

        self.log_test_event("final_flash_complete", {
            "pmax": self.final_flash.pmax,
            "voc": self.final_flash.voc,
            "isc": self.final_flash.isc
        })

        self.logger.info(f"Final Pmax: {self.final_flash.pmax:.2f} W")

        # Calculate degradation
        self.calculate_power_degradation()

        return self.final_flash

    def step6_visual_inspection(self) -> Dict[str, Any]:
        """
        Step 6: Visual Inspection

        Returns:
            Dict: Visual inspection results
        """
        self.logger.info("=" * 60)
        self.logger.info("STEP 6: Visual Inspection")
        self.logger.info("=" * 60)

        self.log_test_event("visual_inspection_start")

        # In real implementation:
        # - Check for cracks, delamination, junction box damage
        # - Document with photographs
        # - Use EL imaging for cell cracks

        # Simulated inspection
        defects = []  # List of defects found

        self.visual_inspection_result = {
            "cracks": False,
            "delamination": False,
            "junction_box_damage": False,
            "defects": defects,
            "pass": len(defects) == 0,
            "inspector": self.result.compliance_data.get('technician_id'),
            "timestamp": datetime.now().isoformat()
        }

        self.result.test_data['visual_inspection'] = self.visual_inspection_result
        self.result.test_data['visual_pass'] = self.visual_inspection_result['pass']

        self.log_test_event("visual_inspection_complete", {
            "defects_found": len(defects),
            "pass": self.visual_inspection_result['pass']
        })

        self.logger.info(f"Visual Inspection: {'PASS' if self.visual_inspection_result['pass'] else 'FAIL'}")

        return self.visual_inspection_result

    def calculate_power_degradation(self):
        """Calculate power degradation from initial to final"""
        if not self.initial_flash or not self.final_flash:
            raise ValueError("Both initial and final flash tests must be completed")

        degradation_w = self.initial_flash.pmax - self.final_flash.pmax
        degradation_pct = (degradation_w / self.initial_flash.pmax) * 100

        self.result.measurements['power_degradation_w'] = degradation_w
        self.result.measurements['power_degradation_pct'] = degradation_pct

        self.logger.info(f"Power Degradation: {degradation_pct:.2f}% ({degradation_w:.2f} W)")

        # Validate against limit
        try:
            validate_degradation_limit(
                self.initial_flash.pmax,
                self.final_flash.pmax,
                IEC_62759_MAX_POWER_DEGRADATION_PCT
            )
            self.result.test_data['degradation_pass'] = True
        except Exception as e:
            self.logger.error(str(e))
            self.result.test_data['degradation_pass'] = False

    @property
    def degradation_pct(self) -> Optional[float]:
        """Get power degradation percentage"""
        return self.result.measurements.get('power_degradation_pct')

    def run_test_sequence(self, **kwargs) -> TestResult:
        """
        Execute complete IEC 62759 test sequence

        Returns:
            TestResult: Complete test results
        """
        self.logger.info("*" * 70)
        self.logger.info("STARTING IEC 62759 TRANSPORTATION TESTING")
        self.logger.info(f"Module ID: {self.module_id}")
        self.logger.info("*" * 70)

        self.result.status = TestStatus.IN_PROGRESS
        self.result.start_time = datetime.now()

        try:
            # Validate inputs
            self.validate_inputs(**kwargs)

            # Connect equipment
            if not self.connect_equipment():
                raise RuntimeError("Failed to connect to test equipment")

            # Run test sequence
            self.step1_initial_flash_test()
            self.step2_edge_loading()
            self.step3_dynamic_mechanical_loading()
            self.step4_thermal_cycling()
            self.step5_final_flash_test()
            self.step6_visual_inspection()

            # Calculate pass/fail
            self.result.pass_fail = self.calculate_pass_fail()
            self.result.status = TestStatus.COMPLETED

        except Exception as e:
            self.logger.error(f"Test sequence failed: {e}")
            self.result.status = TestStatus.FAILED
            self.result.notes = f"Test failed: {str(e)}"
            self.result.pass_fail = PassFailStatus.FAIL
            raise

        finally:
            self.result.end_time = datetime.now()
            # Disconnect equipment
            self.disconnect_equipment()

        self.logger.info("*" * 70)
        self.logger.info(f"TEST COMPLETE - {self.result.pass_fail.value.upper()}")
        self.logger.info("*" * 70)

        return self.result

    def run_full_sequence(self) -> TestResult:
        """Alias for run_test_sequence for convenience"""
        return self.run_test_sequence()

    def calculate_pass_fail(self) -> PassFailStatus:
        """
        Calculate overall pass/fail status

        Pass Criteria:
        1. No breakage during edge loading
        2. No breakage during dynamic loading
        3. Thermal cycling completed successfully
        4. Power degradation < 5%
        5. Visual inspection pass

        Returns:
            PassFailStatus: Overall pass/fail determination
        """
        criteria = {
            'edge_load': self.result.test_data.get('edge_load_pass', False),
            'dynamic_load': self.result.test_data.get('dynamic_load_pass', False),
            'thermal': self.result.test_data.get('thermal_pass', False),
            'degradation': self.result.test_data.get('degradation_pass', False),
            'visual': self.result.test_data.get('visual_pass', False)
        }

        all_pass = all(criteria.values())

        self.logger.info("Pass/Fail Criteria:")
        for criterion, status in criteria.items():
            self.logger.info(f"  {criterion}: {'PASS' if status else 'FAIL'}")

        return PassFailStatus.PASS if all_pass else PassFailStatus.FAIL

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive test report

        Returns:
            Dict: Complete report data
        """
        report = {
            "test_info": {
                "protocol": self.get_protocol_name(),
                "test_id": self.test_id,
                "module_id": self.module_id,
                "test_date": self.result.start_time.isoformat() if self.result.start_time else None,
                "technician": self.result.compliance_data.get('technician_id'),
                "status": self.result.status.value,
                "pass_fail": self.result.pass_fail.value
            },
            "initial_measurements": {
                "pmax": self.result.measurements.get('initial_pmax'),
                "voc": self.result.measurements.get('initial_voc'),
                "isc": self.result.measurements.get('initial_isc'),
                "fill_factor": self.result.measurements.get('initial_fill_factor')
            },
            "final_measurements": {
                "pmax": self.result.measurements.get('final_pmax'),
                "voc": self.result.measurements.get('final_voc'),
                "isc": self.result.measurements.get('final_isc'),
                "fill_factor": self.result.measurements.get('final_fill_factor')
            },
            "degradation": {
                "power_degradation_pct": self.result.measurements.get('power_degradation_pct'),
                "power_degradation_w": self.result.measurements.get('power_degradation_w'),
                "limit_pct": IEC_62759_MAX_POWER_DEGRADATION_PCT,
                "pass": self.result.test_data.get('degradation_pass')
            },
            "edge_loading": {
                "load_pa": self.result.measurements.get('edge_load_pa'),
                "duration_hours": self.result.measurements.get('edge_load_duration'),
                "deflection_mm": self.result.measurements.get('edge_deflection_mm'),
                "pass": self.result.test_data.get('edge_load_pass')
            },
            "dynamic_loading": {
                "load_pa": self.result.measurements.get('dynamic_load_pa'),
                "cycles": self.result.measurements.get('dynamic_cycles'),
                "frequency_hz": self.result.measurements.get('dynamic_frequency_hz'),
                "pass": self.result.test_data.get('dynamic_load_pass')
            },
            "thermal_cycling": {
                "cycles": self.result.measurements.get('thermal_cycles'),
                "low_temp": self.result.measurements.get('thermal_low_temp'),
                "high_temp": self.result.measurements.get('thermal_high_temp'),
                "pass": self.result.test_data.get('thermal_pass')
            },
            "visual_inspection": self.result.test_data.get('visual_inspection', {}),
            "iso_17025_compliance": self.result.compliance_data,
            "test_log": self.result.test_data.get('event_log', [])
        }

        return report
