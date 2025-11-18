"""
Unit tests for Hot Spot Endurance Test - IEC 61215.

Tests cover:
- Test initialization
- Equipment setup
- Test execution
- Result generation
- Pass/fail criteria
- Multiple shading patterns
- Bypass diode detection
- Visual inspection
- ISO 17025 compliance
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from src.models.base import TestStatus
from src.test_blocks.iec_61215.hot_spot import (
    HotSpotTest,
    HotSpotTestResult,
    ShadingPattern,
    BypassDiodeStatus,
    VisualDamageType,
    ThermalImageData,
    run_hot_spot_test
)
from src.test_blocks.common.base import TestBlockError, SetupError, ExecutionError


class TestHotSpotTestInitialization:
    """Test hot spot test initialization."""

    def test_initialization_basic(self, module_id, operator_id):
        """Test basic initialization."""
        test = HotSpotTest(
            module_id=module_id,
            operator=operator_id
        )

        assert test.module_id == module_id
        assert test.operator == operator_id
        assert test.standard == "IEC 61215"
        assert test.test_name == "Hot Spot Endurance Test"
        assert test.test_id == f"IEC-61215-HS-{module_id}"

    def test_initialization_with_config(self, module_id, operator_id, equipment_config, test_parameters):
        """Test initialization with equipment config and parameters."""
        test = HotSpotTest(
            module_id=module_id,
            operator=operator_id,
            equipment_config=equipment_config,
            test_parameters=test_parameters
        )

        assert test.equipment_config == equipment_config
        assert test.test_parameters == test_parameters
        assert test.current_status == TestStatus.INCOMPLETE


class TestShadingPatterns:
    """Test shading pattern support."""

    @pytest.mark.parametrize("pattern", [
        ShadingPattern.SINGLE_CELL,
        ShadingPattern.HALF_CELL,
        ShadingPattern.TWO_CELLS,
        ShadingPattern.STRING,
        ShadingPattern.PARTIAL_MODULE,
        ShadingPattern.DIAGONAL,
        ShadingPattern.CORNER
    ])
    def test_shading_pattern_enum(self, pattern):
        """Test all shading pattern enum values."""
        assert isinstance(pattern, ShadingPattern)
        assert isinstance(pattern.value, str)

    def test_shading_pattern_from_string(self):
        """Test creating shading pattern from string."""
        pattern = ShadingPattern("single_cell")
        assert pattern == ShadingPattern.SINGLE_CELL


class TestThermalImageData:
    """Test thermal image data model."""

    def test_thermal_image_creation(self):
        """Test creating thermal image data."""
        image = ThermalImageData(
            min_temperature_c=25.0,
            max_temperature_c=78.5,
            avg_temperature_c=45.2,
            hot_spot_temperature_c=78.5,
            image_path="/data/thermal_001.jpg",
            shading_pattern=ShadingPattern.SINGLE_CELL
        )

        assert image.min_temperature_c == 25.0
        assert image.max_temperature_c == 78.5
        assert image.avg_temperature_c == 45.2
        assert image.hot_spot_temperature_c == 78.5
        assert image.shading_pattern == ShadingPattern.SINGLE_CELL
        assert isinstance(image.timestamp, datetime)

    def test_thermal_image_validation(self):
        """Test thermal image data validation."""
        with pytest.raises(Exception):  # Pydantic validation error
            ThermalImageData(
                min_temperature_c=25.0,
                max_temperature_c=78.5
                # Missing required fields
            )


class TestHotSpotTestResult:
    """Test hot spot test result model and pass/fail logic."""

    def test_result_creation_passed(self, module_id, operator_id):
        """Test creating a passing test result."""
        result = HotSpotTestResult(
            test_id=f"IEC-61215-HS-{module_id}",
            test_name="Hot Spot Endurance Test",
            standard="IEC 61215",
            module_id=module_id,
            operator=operator_id,
            status=TestStatus.IN_PROGRESS,
            shading_pattern=ShadingPattern.SINGLE_CELL,
            test_duration_hours=1.0,
            max_temperature_c=78.5,
            initial_temperature_c=25.0,
            final_temperature_c=45.0,
            bypass_diode_activated=True,
            bypass_diode_status=BypassDiodeStatus.ACTIVATED,
            visual_damage=False,
            damage_types=[VisualDamageType.NONE],
            temperature_limit_exceeded=False,
            permanent_damage=False
        )

        # Status should be automatically set to PASSED by validator
        assert result.status == TestStatus.PASSED
        assert result.max_temperature_c == 78.5
        assert result.bypass_diode_activated is True

    def test_result_creation_high_temp_no_diode(self, module_id, operator_id):
        """Test result with high temperature but no diode activation."""
        result = HotSpotTestResult(
            test_id=f"IEC-61215-HS-{module_id}",
            test_name="Hot Spot Endurance Test",
            standard="IEC 61215",
            module_id=module_id,
            operator=operator_id,
            status=TestStatus.IN_PROGRESS,
            shading_pattern=ShadingPattern.SINGLE_CELL,
            test_duration_hours=1.0,
            max_temperature_c=95.0,  # Exceeds threshold
            initial_temperature_c=25.0,
            final_temperature_c=45.0,
            bypass_diode_activated=False,  # Diode did not activate
            bypass_diode_status=BypassDiodeStatus.NOT_ACTIVATED,
            visual_damage=False,
            damage_types=[VisualDamageType.NONE],
            temperature_limit_exceeded=True,
            permanent_damage=False
        )

        # Record data for analysis
        assert result.max_temperature_c == 95.0
        assert result.bypass_diode_activated is False
        assert result.temperature_limit_exceeded is True

    def test_result_with_permanent_damage(self, module_id, operator_id):
        """Test result documenting permanent damage."""
        result = HotSpotTestResult(
            test_id=f"IEC-61215-HS-{module_id}",
            test_name="Hot Spot Endurance Test",
            standard="IEC 61215",
            module_id=module_id,
            operator=operator_id,
            status=TestStatus.IN_PROGRESS,
            shading_pattern=ShadingPattern.SINGLE_CELL,
            test_duration_hours=1.0,
            max_temperature_c=75.0,
            initial_temperature_c=25.0,
            final_temperature_c=45.0,
            bypass_diode_activated=True,
            bypass_diode_status=BypassDiodeStatus.ACTIVATED,
            visual_damage=True,
            damage_types=[VisualDamageType.CELL_CRACK, VisualDamageType.BURN_MARK],
            temperature_limit_exceeded=False,
            permanent_damage=True
        )

        # Verify damage is recorded
        assert result.permanent_damage is True
        assert VisualDamageType.CELL_CRACK in result.damage_types
        assert VisualDamageType.BURN_MARK in result.damage_types

    def test_result_passed_with_minor_damage(self, module_id, operator_id):
        """Test that minor damage (discoloration) still allows pass."""
        result = HotSpotTestResult(
            test_id=f"IEC-61215-HS-{module_id}",
            test_name="Hot Spot Endurance Test",
            standard="IEC 61215",
            module_id=module_id,
            operator=operator_id,
            status=TestStatus.IN_PROGRESS,
            shading_pattern=ShadingPattern.SINGLE_CELL,
            test_duration_hours=1.0,
            max_temperature_c=78.5,
            initial_temperature_c=25.0,
            final_temperature_c=45.0,
            bypass_diode_activated=True,
            bypass_diode_status=BypassDiodeStatus.ACTIVATED,
            visual_damage=True,
            damage_types=[VisualDamageType.DISCOLORATION],  # Minor damage OK
            temperature_limit_exceeded=False,
            permanent_damage=False
        )

        # Status should still be PASSED (minor damage acceptable)
        assert result.status == TestStatus.PASSED

    def test_result_with_thermal_images(self, module_id, operator_id):
        """Test result with thermal imaging data."""
        thermal_images = [
            ThermalImageData(
                min_temperature_c=25.0,
                max_temperature_c=78.5,
                avg_temperature_c=45.2,
                hot_spot_temperature_c=78.5,
                image_path="/data/thermal_001.jpg",
                shading_pattern=ShadingPattern.SINGLE_CELL
            ),
            ThermalImageData(
                min_temperature_c=26.0,
                max_temperature_c=80.0,
                avg_temperature_c=47.5,
                hot_spot_temperature_c=80.0,
                image_path="/data/thermal_002.jpg",
                shading_pattern=ShadingPattern.SINGLE_CELL
            )
        ]

        result = HotSpotTestResult(
            test_id=f"IEC-61215-HS-{module_id}",
            test_name="Hot Spot Endurance Test",
            standard="IEC 61215",
            module_id=module_id,
            operator=operator_id,
            status=TestStatus.IN_PROGRESS,
            shading_pattern=ShadingPattern.SINGLE_CELL,
            test_duration_hours=1.0,
            max_temperature_c=80.0,
            initial_temperature_c=25.0,
            final_temperature_c=45.0,
            bypass_diode_activated=True,
            bypass_diode_status=BypassDiodeStatus.ACTIVATED,
            visual_damage=False,
            thermal_images=thermal_images,
            temperature_limit_exceeded=False,
            permanent_damage=False
        )

        assert len(result.thermal_images) == 2
        assert result.thermal_images[0].max_temperature_c == 78.5
        assert result.thermal_images[1].max_temperature_c == 80.0


class TestHotSpotTestExecution:
    """Test hot spot test execution (integration-style tests)."""

    @pytest.mark.asyncio
    async def test_run_hot_spot_test_convenience_function(self, module_id, operator_id, equipment_config):
        """Test using the convenience function to run hot spot test."""
        result = await run_hot_spot_test(
            module_id=module_id,
            operator=operator_id,
            shading_pattern="single_cell",
            duration_hours=1.0,
            irradiance_w_m2=1000.0,
            equipment_config=equipment_config
        )

        assert isinstance(result, HotSpotTestResult)
        assert result.module_id == module_id
        assert result.operator == operator_id
        assert result.shading_pattern == ShadingPattern.SINGLE_CELL
        assert result.test_duration_hours == 1.0

    @pytest.mark.asyncio
    async def test_hot_spot_test_run_method(self, module_id, operator_id, equipment_config):
        """Test running hot spot test via run() method."""
        test = HotSpotTest(
            module_id=module_id,
            operator=operator_id,
            equipment_config=equipment_config
        )

        result = await test.run(
            shading_pattern="single_cell",
            duration_hours=1.0,
            irradiance_w_m2=1000.0
        )

        assert isinstance(result, HotSpotTestResult)
        assert result.standard == "IEC 61215"
        assert result.test_name == "Hot Spot Endurance Test"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("shading_pattern", [
        "single_cell",
        "two_cells",
        "string",
        "partial_module"
    ])
    async def test_multiple_shading_patterns(
        self,
        module_id,
        operator_id,
        equipment_config,
        shading_pattern
    ):
        """Test hot spot test with multiple shading patterns."""
        result = await run_hot_spot_test(
            module_id=module_id,
            operator=operator_id,
            shading_pattern=shading_pattern,
            equipment_config=equipment_config
        )

        assert result.shading_pattern.value == shading_pattern

    @pytest.mark.asyncio
    async def test_test_duration_tracking(self, module_id, operator_id, equipment_config):
        """Test that test duration is tracked correctly."""
        test = HotSpotTest(
            module_id=module_id,
            operator=operator_id,
            equipment_config=equipment_config
        )

        result = await test.run(shading_pattern="single_cell")

        duration = test.get_test_duration()
        assert duration is not None
        assert duration > 0  # Some time should have elapsed


class TestBypassDiodeDetection:
    """Test bypass diode activation detection."""

    def test_bypass_diode_status_enum(self):
        """Test bypass diode status enum values."""
        assert BypassDiodeStatus.ACTIVATED.value == "activated"
        assert BypassDiodeStatus.NOT_ACTIVATED.value == "not_activated"
        assert BypassDiodeStatus.FAILED.value == "failed"
        assert BypassDiodeStatus.UNKNOWN.value == "unknown"

    def test_diode_activation_in_result(self, module_id, operator_id):
        """Test bypass diode activation data in result."""
        result = HotSpotTestResult(
            test_id=f"IEC-61215-HS-{module_id}",
            test_name="Hot Spot Endurance Test",
            standard="IEC 61215",
            module_id=module_id,
            operator=operator_id,
            status=TestStatus.IN_PROGRESS,
            shading_pattern=ShadingPattern.SINGLE_CELL,
            test_duration_hours=1.0,
            max_temperature_c=88.0,
            initial_temperature_c=25.0,
            final_temperature_c=45.0,
            bypass_diode_activated=True,
            bypass_diode_status=BypassDiodeStatus.ACTIVATED,
            diode_activation_time_seconds=450.5,  # Activated at 7.5 minutes
            diode_voltage_drop_v=0.65,
            visual_damage=False,
            temperature_limit_exceeded=True,
            permanent_damage=False
        )

        assert result.bypass_diode_activated is True
        assert result.bypass_diode_status == BypassDiodeStatus.ACTIVATED
        assert result.diode_activation_time_seconds == 450.5
        assert result.diode_voltage_drop_v == 0.65
        # Should pass because diode activated even though temp exceeded
        assert result.status == TestStatus.PASSED


class TestVisualInspection:
    """Test visual inspection functionality."""

    def test_visual_damage_types_enum(self):
        """Test visual damage type enum values."""
        assert VisualDamageType.NONE.value == "none"
        assert VisualDamageType.DISCOLORATION.value == "discoloration"
        assert VisualDamageType.DELAMINATION.value == "delamination"
        assert VisualDamageType.CELL_CRACK.value == "cell_crack"
        assert VisualDamageType.BURN_MARK.value == "burn_mark"
        assert VisualDamageType.GLASS_BREAKAGE.value == "glass_breakage"

    def test_no_damage(self, module_id, operator_id):
        """Test result with no visual damage."""
        result = HotSpotTestResult(
            test_id=f"IEC-61215-HS-{module_id}",
            test_name="Hot Spot Endurance Test",
            standard="IEC 61215",
            module_id=module_id,
            operator=operator_id,
            status=TestStatus.IN_PROGRESS,
            shading_pattern=ShadingPattern.SINGLE_CELL,
            test_duration_hours=1.0,
            max_temperature_c=75.0,
            initial_temperature_c=25.0,
            final_temperature_c=45.0,
            bypass_diode_activated=True,
            bypass_diode_status=BypassDiodeStatus.ACTIVATED,
            visual_damage=False,
            damage_types=[VisualDamageType.NONE],
            temperature_limit_exceeded=False,
            permanent_damage=False
        )

        assert result.visual_damage is False
        assert VisualDamageType.NONE in result.damage_types
        assert result.status == TestStatus.PASSED


class TestISO17025Compliance:
    """Test ISO 17025 compliance features."""

    def test_result_has_traceability_fields(self, module_id, operator_id):
        """Test that result includes ISO 17025 traceability fields."""
        result = HotSpotTestResult(
            test_id=f"IEC-61215-HS-{module_id}",
            test_name="Hot Spot Endurance Test",
            standard="IEC 61215",
            module_id=module_id,
            operator=operator_id,
            reviewer="REV-67890",
            lab_id="LAB-001",
            ambient_temperature_c=23.0,
            relative_humidity_percent=45.0,
            status=TestStatus.IN_PROGRESS,
            shading_pattern=ShadingPattern.SINGLE_CELL,
            test_duration_hours=1.0,
            max_temperature_c=75.0,
            initial_temperature_c=25.0,
            final_temperature_c=45.0,
            bypass_diode_activated=True,
            bypass_diode_status=BypassDiodeStatus.ACTIVATED,
            visual_damage=False,
            temperature_limit_exceeded=False,
            permanent_damage=False
        )

        # ISO 17025 traceability fields
        assert result.operator == operator_id
        assert result.reviewer == "REV-67890"
        assert result.lab_id == "LAB-001"
        assert result.ambient_temperature_c == 23.0
        assert result.relative_humidity_percent == 45.0
        assert isinstance(result.timestamp, datetime)

    def test_result_includes_test_parameters(self, module_id, operator_id):
        """Test that result includes all test parameters."""
        result = HotSpotTestResult(
            test_id=f"IEC-61215-HS-{module_id}",
            test_name="Hot Spot Endurance Test",
            standard="IEC 61215",
            module_id=module_id,
            operator=operator_id,
            status=TestStatus.IN_PROGRESS,
            shading_pattern=ShadingPattern.SINGLE_CELL,
            test_duration_hours=1.0,
            max_temperature_c=75.0,
            initial_temperature_c=25.0,
            final_temperature_c=45.0,
            bypass_diode_activated=True,
            bypass_diode_status=BypassDiodeStatus.ACTIVATED,
            visual_damage=False,
            irradiance_w_m2=1000.0,
            bias_voltage_v=15.0,
            temperature_threshold_c=85.0,
            temperature_limit_exceeded=False,
            permanent_damage=False
        )

        assert result.irradiance_w_m2 == 1000.0
        assert result.bias_voltage_v == 15.0
        assert result.temperature_threshold_c == 85.0
