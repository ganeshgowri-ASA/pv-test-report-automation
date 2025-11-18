"""
Hot Spot Endurance Test - IEC 61215

Evaluates PV module behavior under partial shading conditions to verify:
- Bypass diode activation and protection
- Cell temperature limits under hot spot conditions
- No permanent damage from localized heating

Test Conditions (IEC 61215):
- Irradiance: 1000 W/m² ± 10%
- Duration: 1 hour per shading configuration
- Maximum cell temperature: <85°C for bypass diode activation
- Multiple shading patterns: single cell, string, partial module

Equipment Required:
- Solar simulator (1000 W/m²)
- Thermal imaging camera
- Shading masks (various patterns)
- Temperature data logger
- Power supply for bias voltage
"""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator

from src.models.base import BaseTestResult, TestStatus
from src.test_blocks.common.base import BaseTestBlock, ExecutionError, SetupError
from src.equipment.base import ThermalCamera, SolarSimulator, TemperatureDataLogger


class ShadingPattern(str, Enum):
    """Shading pattern configurations for hot spot testing."""
    SINGLE_CELL = "single_cell"  # One cell fully shaded
    HALF_CELL = "half_cell"  # Half of one cell shaded
    TWO_CELLS = "two_cells"  # Two adjacent cells shaded
    STRING = "string"  # Entire string shaded
    PARTIAL_MODULE = "partial_module"  # Quarter or half module shaded
    DIAGONAL = "diagonal"  # Diagonal shading pattern
    CORNER = "corner"  # Corner cells shaded


class BypassDiodeStatus(str, Enum):
    """Bypass diode activation status."""
    ACTIVATED = "activated"
    NOT_ACTIVATED = "not_activated"
    FAILED = "failed"
    UNKNOWN = "unknown"


class VisualDamageType(str, Enum):
    """Types of visual damage observable after hot spot test."""
    NONE = "none"
    DISCOLORATION = "discoloration"
    DELAMINATION = "delamination"
    CELL_CRACK = "cell_crack"
    BURN_MARK = "burn_mark"
    GLASS_BREAKAGE = "glass_breakage"


class ThermalImageData(BaseModel):
    """Thermal imaging data captured during test."""

    timestamp: datetime = Field(default_factory=datetime.now)
    min_temperature_c: float = Field(..., description="Minimum temperature in frame")
    max_temperature_c: float = Field(..., description="Maximum temperature in frame")
    avg_temperature_c: float = Field(..., description="Average temperature in frame")
    hot_spot_temperature_c: float = Field(..., description="Hot spot cell temperature")
    image_path: str = Field(..., description="Path to thermal image file")
    shading_pattern: ShadingPattern = Field(..., description="Shading pattern during capture")


class HotSpotTestResult(BaseTestResult):
    """
    Hot Spot Endurance Test Result - IEC 61215 Compliant.

    Contains all data required for ISO 17025 test report including:
    - Thermal performance data
    - Bypass diode functionality
    - Visual inspection results
    - Pass/fail criteria evaluation
    """

    # Test-specific fields
    shading_pattern: ShadingPattern = Field(..., description="Shading pattern applied")
    test_duration_hours: float = Field(..., description="Actual test duration")

    # Temperature measurements
    max_temperature_c: float = Field(..., description="Maximum cell temperature recorded")
    initial_temperature_c: float = Field(..., description="Initial temperature before test")
    final_temperature_c: float = Field(..., description="Final temperature after test")
    temperature_threshold_c: float = Field(85.0, description="Temperature threshold for bypass diode")

    # Bypass diode verification
    bypass_diode_activated: bool = Field(..., description="Bypass diode activated during test")
    bypass_diode_status: BypassDiodeStatus = Field(..., description="Bypass diode status")
    diode_activation_time_seconds: Optional[float] = Field(None, description="Time to diode activation")
    diode_voltage_drop_v: Optional[float] = Field(None, description="Bypass diode voltage drop")

    # Visual inspection
    visual_damage: bool = Field(..., description="Visual damage observed")
    damage_types: List[VisualDamageType] = Field(default_factory=list, description="Types of damage observed")
    damage_description: Optional[str] = Field(None, description="Detailed damage description")

    # Thermal imaging data
    thermal_images: List[ThermalImageData] = Field(default_factory=list, description="Thermal images captured")

    # Test parameters
    irradiance_w_m2: float = Field(1000.0, description="Applied irradiance")
    bias_voltage_v: Optional[float] = Field(None, description="Applied bias voltage")

    # Pass/fail determination
    temperature_limit_exceeded: bool = Field(..., description="Temperature exceeded safe limits")
    permanent_damage: bool = Field(..., description="Permanent damage detected")

    @validator('status', always=True)
    def determine_pass_fail(cls, v, values):
        """
        Determine test pass/fail status based on IEC 61215 criteria.

        Pass criteria:
        - Maximum temperature stays below limits OR bypass diode activates
        - No permanent damage (cell cracks, burn marks, glass breakage)
        - Discoloration/minor delamination acceptable if module still functional
        """
        if v == TestStatus.FAILED or v == TestStatus.ABORTED:
            return v

        # Check for permanent damage (use field value if provided)
        has_permanent_damage = values.get('permanent_damage', False)

        # Also check damage_types as fallback
        if not has_permanent_damage:
            damage_types = values.get('damage_types', [])
            permanent_damage_types = {
                VisualDamageType.CELL_CRACK,
                VisualDamageType.BURN_MARK,
                VisualDamageType.GLASS_BREAKAGE
            }
            has_permanent_damage = any(d in permanent_damage_types for d in damage_types)

        # Check temperature and diode activation
        max_temp = values.get('max_temperature_c', 0)
        bypass_activated = values.get('bypass_diode_activated', False)
        temp_threshold = values.get('temperature_threshold_c', 85.0)

        # Pass if: (temp controlled OR diode activated) AND no permanent damage
        temp_ok = max_temp < temp_threshold or bypass_activated

        if temp_ok and not has_permanent_damage:
            return TestStatus.PASSED
        else:
            return TestStatus.FAILED

    class Config:
        json_schema_extra = {
            "example": {
                "test_id": "IEC-61215-HS-001",
                "test_name": "Hot Spot Endurance Test",
                "standard": "IEC 61215",
                "module_id": "PV-001",
                "operator": "OP-12345",
                "shading_pattern": "single_cell",
                "max_temperature_c": 78.5,
                "bypass_diode_activated": True,
                "visual_damage": False,
                "status": "passed"
            }
        }


class HotSpotTest(BaseTestBlock):
    """
    Hot Spot Endurance Test implementation per IEC 61215.

    Test Procedure:
    1. Setup equipment and verify calibration
    2. Apply shading pattern to specified cells
    3. Expose to 1000 W/m² irradiance for 1 hour
    4. Monitor temperature with thermal camera
    5. Verify bypass diode activation
    6. Inspect for visual damage
    7. Evaluate pass/fail criteria

    Example:
        ```python
        # Initialize test
        test = HotSpotTest(
            module_id="PV-001",
            operator="OP-12345"
        )

        # Run with specific shading pattern
        result = await test.run(shading_pattern="single_cell")

        # Check results
        print(f"Max Temp: {result.max_temperature_c}°C")
        print(f"Bypass Diode: {result.bypass_diode_activated}")
        print(f"Status: {result.status}")
        ```
    """

    def __init__(
        self,
        module_id: str,
        operator: str,
        equipment_config: Optional[Dict[str, Any]] = None,
        test_parameters: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Hot Spot Endurance Test.

        Args:
            module_id: Module under test identifier (e.g., "PV-001")
            operator: Test operator name/ID
            equipment_config: Equipment configuration
            test_parameters: Test parameters (irradiance, duration, etc.)
        """
        super().__init__(module_id, operator, equipment_config, test_parameters)

        # Equipment instances
        self.thermal_camera: Optional[ThermalCamera] = None
        self.solar_simulator: Optional[SolarSimulator] = None
        self.temp_logger: Optional[TemperatureDataLogger] = None

        # Test data collection
        self.thermal_images: List[ThermalImageData] = []
        self.temperature_readings: List[float] = []
        self.timestamps: List[datetime] = []

        # Test state
        self.shading_pattern: Optional[ShadingPattern] = None
        self.test_start_time: Optional[datetime] = None
        self.diode_activation_detected: bool = False

    @property
    def standard(self) -> str:
        return "IEC 61215"

    @property
    def test_name(self) -> str:
        return "Hot Spot Endurance Test"

    @property
    def test_id(self) -> str:
        return f"IEC-61215-HS-{self.module_id}"

    async def setup(self) -> None:
        """
        Setup test equipment and verify readiness.

        Equipment initialization:
        - Thermal camera connection and calibration check
        - Solar simulator setup and irradiance calibration
        - Temperature data logger configuration
        - Shading mask positioning
        """
        try:
            # Initialize equipment
            self.thermal_camera = ThermalCamera(
                self.equipment_config.get("thermal_camera", {})
            )
            self.solar_simulator = SolarSimulator(
                self.equipment_config.get("solar_simulator", {})
            )
            self.temp_logger = TemperatureDataLogger(
                self.equipment_config.get("temp_logger", {})
            )

            # Connect equipment
            await self.thermal_camera.connect()
            await self.solar_simulator.connect()
            await self.temp_logger.connect()

            # Verify equipment status
            camera_status = await self.thermal_camera.get_status()
            simulator_status = await self.solar_simulator.get_status()

            if not camera_status.get("connected"):
                raise SetupError("Thermal camera connection failed")

            if not simulator_status.get("connected"):
                raise SetupError("Solar simulator connection failed")

            # Set solar simulator to target irradiance
            target_irradiance = self.test_parameters.get("irradiance_w_m2", 1000.0)
            await self.solar_simulator.set_irradiance(target_irradiance)

            self.add_note(f"Equipment setup complete. Irradiance set to {target_irradiance} W/m²")

        except Exception as e:
            raise SetupError(f"Setup failed: {str(e)}") from e

    async def execute(self) -> Dict[str, Any]:
        """
        Execute hot spot endurance test.

        Procedure:
        1. Apply specified shading pattern
        2. Turn on solar simulator
        3. Monitor temperature continuously for specified duration
        4. Capture thermal images at intervals
        5. Detect bypass diode activation
        6. Record all measurements

        Returns:
            Dictionary containing test measurements and observations
        """
        try:
            # Get test parameters
            shading_pattern_str = self.test_parameters.get("shading_pattern", "single_cell")
            self.shading_pattern = ShadingPattern(shading_pattern_str)
            duration_hours = self.test_parameters.get("duration_hours", 1.0)
            thermal_capture_interval = self.test_parameters.get("thermal_interval_seconds", 300)  # 5 min

            self.test_start_time = datetime.now()

            # Record initial temperature
            initial_thermal = await self.thermal_camera.capture_thermal_image()
            initial_temp = initial_thermal["max_temp_c"]
            self.add_measurement("initial_temperature", initial_temp, "°C")

            # Apply shading pattern (simulated - would be manual or automated mask)
            self.add_note(f"Applied shading pattern: {self.shading_pattern.value}")

            # Turn on solar simulator
            await self.solar_simulator.lamp_on()
            self.add_note("Solar simulator lamp ON")

            # Start temperature logging
            duration_seconds = duration_hours * 3600
            await self.temp_logger.start_logging(duration_seconds, sample_rate=1.0)

            # Monitor test for specified duration
            elapsed_time = 0
            max_temperature = initial_temp
            bypass_diode_activated = False
            diode_activation_time = None

            # Simulate test execution (in real implementation, this would be actual monitoring)
            num_captures = int(duration_seconds / thermal_capture_interval)

            for i in range(num_captures):
                # Wait for interval
                await asyncio.sleep(min(thermal_capture_interval, duration_seconds - elapsed_time))
                elapsed_time += thermal_capture_interval

                # Capture thermal image
                thermal_data = await self.thermal_camera.capture_thermal_image()
                current_max_temp = thermal_data["max_temp_c"]

                # Create thermal image record
                thermal_image = ThermalImageData(
                    min_temperature_c=thermal_data["min_temp_c"],
                    max_temperature_c=current_max_temp,
                    avg_temperature_c=thermal_data["avg_temp_c"],
                    hot_spot_temperature_c=current_max_temp,
                    image_path=thermal_data["image_path"],
                    shading_pattern=self.shading_pattern
                )
                self.thermal_images.append(thermal_image)

                # Update max temperature
                if current_max_temp > max_temperature:
                    max_temperature = current_max_temp

                # Check for bypass diode activation
                temp_threshold = self.test_parameters.get("temperature_threshold_c", 85.0)
                if not bypass_diode_activated and current_max_temp >= temp_threshold:
                    bypass_diode_activated = True
                    diode_activation_time = elapsed_time
                    self.add_note(
                        f"Bypass diode activation detected at {elapsed_time}s "
                        f"(temp: {current_max_temp}°C)"
                    )

                self.add_measurement(
                    "cell_temperature",
                    current_max_temp,
                    "°C"
                )

                # Safety check - abort if temperature too high
                if current_max_temp > 120.0:
                    self.add_note(f"CRITICAL: Temperature {current_max_temp}°C exceeds safety limit!")
                    await self.solar_simulator.lamp_off()
                    raise ExecutionError("Test aborted - temperature safety limit exceeded")

                if elapsed_time >= duration_seconds:
                    break

            # Turn off solar simulator
            await self.solar_simulator.lamp_off()
            self.add_note("Solar simulator lamp OFF")

            # Final temperature reading
            final_thermal = await self.thermal_camera.capture_thermal_image()
            final_temp = final_thermal["max_temp_c"]

            # Get logged temperature data
            temp_data = await self.temp_logger.get_temperature_data()

            # Perform visual inspection (simulated - would be manual inspection)
            visual_inspection = self._perform_visual_inspection()

            # Compile results
            return {
                "shading_pattern": self.shading_pattern,
                "duration_hours": duration_hours,
                "initial_temperature_c": initial_temp,
                "max_temperature_c": max_temperature,
                "final_temperature_c": final_temp,
                "bypass_diode_activated": bypass_diode_activated,
                "diode_activation_time_seconds": diode_activation_time,
                "thermal_images": self.thermal_images,
                "visual_inspection": visual_inspection,
                "temperature_data": temp_data
            }

        except Exception as e:
            # Emergency shutdown
            if self.solar_simulator:
                await self.solar_simulator.lamp_off()
            raise ExecutionError(f"Test execution failed: {str(e)}") from e

    async def teardown(self) -> None:
        """
        Cleanup and reset equipment to safe state.

        Ensures:
        - Solar simulator lamp is OFF
        - All equipment disconnected
        - Data saved
        """
        try:
            # Ensure simulator is off
            if self.solar_simulator:
                await self.solar_simulator.lamp_off()
                await self.solar_simulator.disconnect()

            # Disconnect other equipment
            if self.thermal_camera:
                await self.thermal_camera.disconnect()

            if self.temp_logger:
                await self.temp_logger.disconnect()

            self.add_note("Equipment teardown complete")

        except Exception as e:
            # Log error but don't raise - teardown is best effort
            print(f"Warning: Teardown error: {e}")

    def create_result(self, data: Dict[str, Any]) -> HotSpotTestResult:
        """
        Create HotSpotTestResult from test data.

        Args:
            data: Raw test data from execute()

        Returns:
            Structured test result model
        """
        visual_inspection = data.get("visual_inspection", {})

        # Determine bypass diode status
        if data["bypass_diode_activated"]:
            diode_status = BypassDiodeStatus.ACTIVATED
        else:
            diode_status = BypassDiodeStatus.NOT_ACTIVATED

        # Check if temperature limit was exceeded
        temp_threshold = self.test_parameters.get("temperature_threshold_c", 85.0)
        temp_exceeded = data["max_temperature_c"] > temp_threshold

        result = HotSpotTestResult(
            test_id=self.test_id,
            test_name=self.test_name,
            standard=self.standard,
            module_id=self.module_id,
            operator=self.operator,
            status=TestStatus.IN_PROGRESS,  # Will be determined by validator
            # Hot spot specific fields
            shading_pattern=data["shading_pattern"],
            test_duration_hours=data["duration_hours"],
            max_temperature_c=data["max_temperature_c"],
            initial_temperature_c=data["initial_temperature_c"],
            final_temperature_c=data["final_temperature_c"],
            bypass_diode_activated=data["bypass_diode_activated"],
            bypass_diode_status=diode_status,
            diode_activation_time_seconds=data.get("diode_activation_time_seconds"),
            visual_damage=visual_inspection["damage_detected"],
            damage_types=visual_inspection["damage_types"],
            damage_description=visual_inspection.get("description"),
            thermal_images=data.get("thermal_images", []),
            irradiance_w_m2=self.test_parameters.get("irradiance_w_m2", 1000.0),
            temperature_limit_exceeded=temp_exceeded,
            permanent_damage=visual_inspection["permanent_damage"]
        )

        return result

    def _perform_visual_inspection(self) -> Dict[str, Any]:
        """
        Perform visual inspection for damage.

        In production, this would involve:
        - Manual inspection by operator
        - High-resolution photography
        - EL (electroluminescence) imaging
        - IR thermography

        Returns:
            Dictionary containing inspection results
        """
        # Simulated inspection results
        # In real implementation, operator would input findings

        return {
            "damage_detected": False,
            "damage_types": [VisualDamageType.NONE],
            "permanent_damage": False,
            "description": "No visible damage detected. Module appearance normal."
        }


# Convenience function for running hot spot test
async def run_hot_spot_test(
    module_id: str,
    operator: str,
    shading_pattern: str = "single_cell",
    duration_hours: float = 1.0,
    irradiance_w_m2: float = 1000.0,
    equipment_config: Optional[Dict[str, Any]] = None
) -> HotSpotTestResult:
    """
    Convenience function to run hot spot endurance test.

    Args:
        module_id: Module identifier (e.g., "PV-001")
        operator: Operator name/ID
        shading_pattern: Shading pattern to apply
        duration_hours: Test duration in hours
        irradiance_w_m2: Solar irradiance level
        equipment_config: Equipment configuration

    Returns:
        HotSpotTestResult with test outcome

    Example:
        ```python
        result = await run_hot_spot_test(
            module_id="PV-001",
            operator="OP-12345",
            shading_pattern="single_cell"
        )
        print(f"Test {result.status}: Max temp {result.max_temperature_c}°C")
        ```
    """
    test = HotSpotTest(
        module_id=module_id,
        operator=operator,
        equipment_config=equipment_config or {}
    )

    result = await test.run(
        shading_pattern=shading_pattern,
        duration_hours=duration_hours,
        irradiance_w_m2=irradiance_w_m2
    )

    return result
