"""
Unit tests for IEC 61701 Salt Mist Corrosion Test Handler

Tests verify the functionality of the IEC61701Handler implementation
according to IEC 61701:2020 standard requirements.
"""

import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.protocols.base import SpecimenInfo, TestStatus
from src.protocols.iec_61701_handler import (
    IEC61701Handler,
    SeverityLevel,
    SEVERITY_CONFIGS,
    SaltMistTestConditions,
    DryingPhaseConditions
)
from src.measurements.iv_curve import IVCurveData
from src.measurements.insulation import InsulationResistanceData


def create_test_specimen() -> SpecimenInfo:
    """Create test specimen for unit tests"""
    return SpecimenInfo(
        specimen_id="TEST-001",
        manufacturer="Test Manufacturer",
        model="TEST-400W",
        serial_number="SN-TEST-001",
        rated_power=400.0,
        rated_voltage=48.0,
        rated_current=8.33,
        technology="Mono-Si",
        dimensions={'area': 2.0}
    )


def test_severity_level_configs():
    """Test that all severity levels have correct configurations"""
    assert len(SEVERITY_CONFIGS) == 6, "Should have 6 severity levels"

    # Test Level 1
    level1 = SEVERITY_CONFIGS[SeverityLevel.LEVEL_1]
    assert level1.exposure_hours == 12
    assert level1.cycles == 1

    # Test Level 6 (most severe)
    level6 = SEVERITY_CONFIGS[SeverityLevel.LEVEL_6]
    assert level6.exposure_hours == 240
    assert level6.cycles == 10

    print("✓ Severity level configurations correct")


def test_salt_mist_conditions():
    """Test salt mist test conditions match IEC 61701 requirements"""
    conditions = SaltMistTestConditions()

    assert conditions.salt_concentration == 5.0, "Salt concentration should be 5%"
    assert conditions.temperature == 35.0, "Temperature should be 35°C"
    assert conditions.humidity == 97.5, "Humidity should be 95-100%"
    assert conditions.ph_range == (6.5, 7.2), "pH should be 6.5-7.2"

    print("✓ Salt mist conditions match IEC 61701 requirements")


def test_drying_phase_conditions():
    """Test drying phase conditions"""
    drying = DryingPhaseConditions()

    assert drying.temperature == 25.0, "Drying temp should be 25°C"
    assert drying.humidity == 50.0, "Drying humidity should be 50%"
    assert drying.duration_hours == 24, "Drying duration should be 24h"

    print("✓ Drying phase conditions correct")


def test_handler_initialization():
    """Test IEC61701Handler initialization"""
    specimen = create_test_specimen()

    handler = IEC61701Handler(
        specimen_info=specimen,
        severity_level=SeverityLevel.LEVEL_4
    )

    assert handler.STANDARD_NAME == "IEC 61701"
    assert handler.STANDARD_VERSION == "2020"
    assert handler.severity_level == SeverityLevel.LEVEL_4
    assert handler.MAX_POWER_DEGRADATION_PERCENT == 5.0
    assert handler.MIN_INSULATION_RESISTANCE_OHM == 40e6

    print("✓ Handler initialization successful")


def test_test_parameters_setup():
    """Test setup of test parameters"""
    specimen = create_test_specimen()
    handler = IEC61701Handler(
        specimen_info=specimen,
        severity_level=SeverityLevel.LEVEL_3
    )

    params = handler.setup_test_parameters()

    assert len(params) > 0, "Should have test parameters"

    # Check for required parameters
    param_names = [p.name for p in params]
    assert "Severity Level" in param_names
    assert "Salt Concentration" in param_names
    assert "Exposure Duration" in param_names

    print("✓ Test parameters setup correctly")


def test_iv_curve_data():
    """Test I-V curve data structure"""
    # Create sample I-V curve
    voltages = [0, 10, 20, 30, 40, 48]
    currents = [8.5, 8.4, 8.2, 7.5, 5.0, 0]

    iv_curve = IVCurveData(
        voltage=voltages,
        current=currents,
        irradiance=1000.0,
        cell_temperature=25.0
    )

    assert iv_curve.voc == 48, "Voc should be max voltage"
    assert iv_curve.isc == 8.5, "Isc should be max current"
    assert iv_curve.pmax > 0, "Pmax should be positive"
    assert 0 < iv_curve.fill_factor < 1, "Fill factor should be 0-1"

    print("✓ I-V curve data structure working correctly")


def test_power_degradation_calculation():
    """Test power degradation calculation"""
    # Initial curve (400W)
    initial = IVCurveData(
        voltage=[0, 24, 48],
        current=[8.33, 8.33, 0],
        irradiance=1000.0
    )

    # Final curve (380W - 5% degradation)
    final = IVCurveData(
        voltage=[0, 24, 48],
        current=[7.92, 7.92, 0],
        irradiance=1000.0
    )

    degradation = final.calculate_power_degradation(initial)

    assert 4.5 < degradation < 5.5, "Should calculate ~5% degradation"

    print("✓ Power degradation calculation correct")


def test_insulation_resistance_data():
    """Test insulation resistance data structure"""
    insulation = InsulationResistanceData(
        resistance=50e6,  # 50 MΩ
        test_voltage=1000.0,
        measurement_duration=60.0,
        temperature=25.0,
        humidity=50.0,
        timestamp=datetime.now(),
        pass_threshold=40e6  # 40 MΩ
    )

    assert insulation.resistance_megohm == 50.0, "Should convert to MΩ"
    assert insulation.passes == True, "50 MΩ should pass 40 MΩ threshold"

    # Test failing case
    insulation_fail = InsulationResistanceData(
        resistance=30e6,  # 30 MΩ
        test_voltage=1000.0,
        measurement_duration=60.0,
        temperature=25.0,
        humidity=50.0,
        timestamp=datetime.now(),
        pass_threshold=40e6
    )

    assert insulation_fail.passes == False, "30 MΩ should fail 40 MΩ threshold"

    print("✓ Insulation resistance data structure working correctly")


def test_severity_level_exposure_durations():
    """Test that exposure durations increase with severity level"""
    previous_hours = 0

    for level in [SeverityLevel.LEVEL_1, SeverityLevel.LEVEL_2,
                  SeverityLevel.LEVEL_3, SeverityLevel.LEVEL_4,
                  SeverityLevel.LEVEL_5, SeverityLevel.LEVEL_6]:
        config = SEVERITY_CONFIGS[level]
        assert config.exposure_hours > previous_hours, \
            f"Level {level.value} should have more exposure than previous level"
        previous_hours = config.exposure_hours

    print("✓ Severity levels have increasing exposure durations")


def test_report_data_structure():
    """Test that report data structure is complete"""
    from src.protocols.iec_61701_handler import IEC61701TestReport, VisualInspectionResult

    specimen = create_test_specimen()

    # Create sample data
    initial_iv = IVCurveData(
        voltage=[0, 24, 48],
        current=[8.33, 8.33, 0],
        irradiance=1000.0
    )

    final_iv = IVCurveData(
        voltage=[0, 24, 48],
        current=[8.0, 8.0, 0],
        irradiance=1000.0
    )

    visual = VisualInspectionResult(
        timestamp=datetime.now(),
        corrosion_detected=False,
        delamination_detected=False,
        bubbles_detected=False
    )

    insulation = InsulationResistanceData(
        resistance=50e6,
        test_voltage=1000.0,
        measurement_duration=60.0,
        temperature=25.0,
        humidity=50.0,
        timestamp=datetime.now(),
        pass_threshold=40e6
    )

    # Create report
    report = IEC61701TestReport(
        specimen_info=specimen,
        severity_level=SeverityLevel.LEVEL_4,
        severity_config=SEVERITY_CONFIGS[SeverityLevel.LEVEL_4],
        test_conditions=SaltMistTestConditions(),
        drying_conditions=DryingPhaseConditions(),
        initial_iv_curve=initial_iv,
        final_iv_curve=final_iv,
        power_degradation_percent=4.0,
        visual_inspection=visual,
        insulation_resistance=insulation,
        overall_status=TestStatus.PASS,
        test_start_time=datetime.now(),
        test_end_time=datetime.now(),
        operator="Test Operator",
        facility="Test Facility"
    )

    # Convert to dict and check structure
    report_dict = report.to_dict()

    assert 'standard' in report_dict
    assert 'specimen' in report_dict
    assert 'test_parameters' in report_dict
    assert 'measurements' in report_dict
    assert 'results' in report_dict
    assert 'compliance_statement' in report_dict

    print("✓ Report data structure complete")


def run_all_tests():
    """Run all unit tests"""
    print("\n" + "="*70)
    print("IEC 61701 Handler - Unit Tests")
    print("="*70 + "\n")

    tests = [
        test_severity_level_configs,
        test_salt_mist_conditions,
        test_drying_phase_conditions,
        test_handler_initialization,
        test_test_parameters_setup,
        test_iv_curve_data,
        test_power_degradation_calculation,
        test_insulation_resistance_data,
        test_severity_level_exposure_durations,
        test_report_data_structure
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            failed += 1

    print("\n" + "="*70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*70 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
