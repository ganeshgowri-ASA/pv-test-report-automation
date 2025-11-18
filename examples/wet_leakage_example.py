"""
Example usage of Wet Leakage Current Test Block.

Demonstrates:
- Basic test execution
- Custom voltage calculation
- ISO 17025 compliant data recording
- Safety interlock verification
"""

import logging
from datetime import datetime, timedelta

from test_blocks.wet_leakage import WetLeakageTest, WetLeakageTestResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_basic_test():
    """Basic wet leakage test with default parameters."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Wet Leakage Test")
    print("="*70)

    # Initialize test
    test = WetLeakageTest(module="PV-001")

    # Execute measurement with default 1000V
    result = test.measure(
        voltage=1200,
        operator_id="TECH-001",
        equipment_id="HV-SOURCE-001"
    )

    # Display results
    print(f"\nModule: PV-001")
    print(f"Applied Voltage: {result.applied_voltage}V")
    print(f"Leakage Current: {result.leakage_current_ua}μA")
    print(f"Duration: {result.duration_sec}s")
    print(f"Status: {result.status.value.upper()}")
    print(f"Result: {'PASS' if result.pass_status else 'FAIL'}")


def example_auto_voltage():
    """Test with automatic voltage calculation based on Voc."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Automatic Voltage Calculation (1000V + 1.2×Voc)")
    print("="*70)

    # Initialize test with module Voc
    module_voc = 45.6  # Typical 72-cell module
    test = WetLeakageTest(
        module="PV-002",
        module_voc=module_voc,
        test_id=2002,
        module_id=2002
    )

    # Measure with auto-calculated voltage
    result = test.measure(
        operator_id="TECH-002",
        equipment_id="HV-SOURCE-001",
        ambient_temp_c=25.0,
        humidity_percent=50.0
    )

    # Display results
    print(f"\nModule: PV-002")
    print(f"Module Voc: {module_voc}V")
    print(f"Calculated Test Voltage: {result.applied_voltage}V")
    print(f"  (1000V + 1.2×{module_voc}V = {1000 + 1.2*module_voc}V)")
    print(f"Leakage Current: {result.leakage_current_ua}μA")
    print(f"Duration: {result.duration_sec}s")
    print(f"Status: {result.status.value.upper()}")
    print(f"Result: {'PASS' if result.pass_status else 'FAIL'}")


def example_full_iso17025():
    """Complete test with full ISO 17025 traceability."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Full ISO 17025 Compliant Test")
    print("="*70)

    # Initialize test
    test = WetLeakageTest(
        module="PV-003",
        module_voc=48.2,
        test_id=3003,
        module_id=3003
    )

    # Equipment calibration (valid for 1 year)
    calibration_date = datetime.now() - timedelta(days=180)  # 6 months ago

    # Execute measurement with full traceability
    result = test.measure(
        voltage=1100,
        duration_sec=150,  # 2.5 minutes
        operator_id="TECH-003",
        equipment_id="HV-SOURCE-002",
        calibration_date=calibration_date,
        ambient_temp_c=23.5,
        humidity_percent=45.0,
        water_temp_c=20.0,
        water_resistivity_ohm_cm=1000.0,
        immersion_duration_hours=24.0,
        notes="Standard wet leakage test per IEC 61215-2:2016"
    )

    # Display comprehensive results
    print(f"\nTest Information:")
    print(f"  Test ID: {result.test_id}")
    print(f"  Module ID: {result.module_id}")
    print(f"  Test Date: {result.test_date}")
    print(f"  Operator: {result.operator_id}")
    print(f"  Equipment: {result.equipment_id}")
    print(f"  Calibration Date: {result.calibration_date}")

    print(f"\nTest Parameters:")
    print(f"  Applied Voltage: {result.applied_voltage}V")
    print(f"  Module Voc: {result.module_voc}V")
    print(f"  Immersion Duration: {result.immersion_duration_hours}h")
    print(f"  Measurement Duration: {result.duration_sec}s")

    print(f"\nEnvironmental Conditions:")
    print(f"  Ambient Temperature: {result.ambient_temp_c}°C")
    print(f"  Humidity: {result.humidity_percent}%")
    print(f"  Water Temperature: {result.water_temp_c}°C")
    print(f"  Water Resistivity: {result.water_resistivity_ohm_cm}Ω·cm")

    print(f"\nResults:")
    print(f"  Leakage Current: {result.leakage_current_ua}μA")
    print(f"  Limit: <{result.max_leakage_ua}μA")
    print(f"  Status: {result.status.value.upper()}")
    print(f"  Result: {'PASS' if result.pass_status else 'FAIL'}")

    print(f"\nNotes:")
    print(f"  {result.notes}")

    # Export to dict (for database storage or JSON export)
    print("\n" + "-"*70)
    print("Data export (JSON-compatible):")
    print("-"*70)
    import json
    print(json.dumps(result.model_dump(), indent=2, default=str))


def example_batch_testing():
    """Batch testing of multiple modules."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Batch Testing Multiple Modules")
    print("="*70)

    modules = [
        {"name": "PV-101", "voc": 45.6},
        {"name": "PV-102", "voc": 46.1},
        {"name": "PV-103", "voc": 45.8},
        {"name": "PV-104", "voc": 46.3},
        {"name": "PV-105", "voc": 45.9},
    ]

    results = []

    for idx, module_info in enumerate(modules):
        test = WetLeakageTest(
            module=module_info["name"],
            module_voc=module_info["voc"],
            test_id=4000 + idx,
            module_id=4000 + idx
        )

        result = test.measure(
            operator_id="TECH-004",
            equipment_id="HV-SOURCE-001",
            ambient_temp_c=24.0,
            humidity_percent=48.0
        )

        results.append(result)

    # Summary report
    print("\nBatch Test Summary:")
    print("-"*70)
    print(f"{'Module':<10} {'Voc (V)':<10} {'Test V (V)':<12} {'Leakage (μA)':<15} {'Result':<10}")
    print("-"*70)

    passed = 0
    failed = 0

    for module_info, result in zip(modules, results):
        status = "PASS" if result.pass_status else "FAIL"
        print(
            f"{module_info['name']:<10} "
            f"{module_info['voc']:<10.1f} "
            f"{result.applied_voltage:<12.1f} "
            f"{result.leakage_current_ua:<15.2f} "
            f"{status:<10}"
        )

        if result.pass_status:
            passed += 1
        else:
            failed += 1

    print("-"*70)
    print(f"Total: {len(results)} modules | Passed: {passed} | Failed: {failed}")
    print(f"Yield: {100*passed/len(results):.1f}%")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("WET LEAKAGE CURRENT TEST - EXAMPLES")
    print("Per IEC 61215-2:2016 and IEC 61730-2:2016")
    print("="*70)

    # Run all examples
    example_basic_test()
    example_auto_voltage()
    example_full_iso17025()
    example_batch_testing()

    print("\n" + "="*70)
    print("All examples completed successfully!")
    print("="*70 + "\n")
