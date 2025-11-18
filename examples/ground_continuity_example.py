"""
Example usage of Ground Continuity Test Block.

This example demonstrates how to use the GroundContinuityTest class
for testing PV modules per IEC 61730 standards.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from test_blocks.ground_continuity import (
    GroundContinuityTest,
    MeasurementPoint,
    WireConfiguration,
)
from test_blocks.base import EnvironmentalConditions


def example_basic_test():
    """Basic ground continuity test example."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Ground Continuity Test")
    print("="*70 + "\n")

    # Create test instance
    test = GroundContinuityTest(
        test_id="GC-001",
        module_id="PV-MODULE-12345",
        operator="John Doe",
    )

    # Run test with simulated measurements
    report = test.run_test(simulated=True)

    # Print summary
    print("\nTest Summary:")
    print(f"  Module: {report['test_information']['module_id']}")
    print(f"  Status: {report['result']['overall_status']}")
    print(f"  Points measured: {report['statistics']['total_points_measured']}")
    print(f"  Average resistance: {report['statistics']['average_resistance_ohm']:.4f} Ω")


def example_custom_parameters():
    """Example with custom test parameters."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Custom Test Parameters")
    print("="*70 + "\n")

    # Create test with custom parameters
    test = GroundContinuityTest(
        test_id="GC-002",
        module_id="PV-MODULE-67890",
        operator="Jane Smith",
        test_current=30.0,  # Higher test current
        test_duration=90.0,  # Longer duration
        max_resistance_ohm=0.08,  # Stricter threshold
        measurement_points=[
            MeasurementPoint.FRAME_TO_GROUND.value,
            MeasurementPoint.MOUNTING_HOLE_1.value,
            MeasurementPoint.MOUNTING_HOLE_2.value,
            MeasurementPoint.MOUNTING_HOLE_3.value,
            MeasurementPoint.MOUNTING_HOLE_4.value,
        ],
    )

    # Run test
    report = test.run_test(simulated=True)

    # Print detailed results
    print("\nDetailed Results:")
    for measurement in report['measurements']:
        print(f"\n  {measurement['point']}:")
        print(f"    Resistance: {measurement['resistance_ohm']:.4f} ± {measurement['uncertainty_ohm']:.4f} Ω")
        print(f"    Voltage drop: {measurement['voltage_drop_mv']:.2f} mV")
        print(f"    Temperature rise: {measurement['temperature_rise_celsius']:.1f} °C")
        print(f"    Status: {measurement['status']}")


def example_with_environmental_conditions():
    """Example including environmental conditions."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Test with Environmental Monitoring")
    print("="*70 + "\n")

    # Create environmental conditions
    env_conditions = EnvironmentalConditions(
        temperature_celsius=23.5,
        humidity_percent=45.0,
        pressure_kpa=101.3,
    )

    # Create test
    test = GroundContinuityTest(
        test_id="GC-003",
        module_id="PV-MODULE-11111",
        operator="Mike Johnson",
        environmental_conditions=env_conditions,
    )

    # Run test
    report = test.run_test(simulated=True)

    # Print environmental data
    if report['environmental_conditions']:
        print("\nEnvironmental Conditions:")
        print(f"  Temperature: {report['environmental_conditions']['temperature_celsius']} °C")
        print(f"  Humidity: {report['environmental_conditions']['humidity_percent']} %")
        print(f"  Pressure: {report['environmental_conditions']['pressure_kpa']} kPa")


def example_simulate_failure():
    """Example demonstrating a failed test."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Simulated Test Failure")
    print("="*70 + "\n")

    # Create test
    test = GroundContinuityTest(
        test_id="GC-004",
        module_id="PV-MODULE-99999",
        operator="Sarah Wilson",
        max_resistance_ohm=0.1,
    )

    # Run test with high simulated resistance (will fail)
    report = test.run_test(simulated=True, simulated_resistance=0.25)

    print("\nFailure Analysis:")
    print(f"  Expected: ≤ {test.max_resistance_ohm} Ω")
    print(f"  Measured: {report['statistics']['max_resistance_ohm']:.4f} Ω")
    print(f"  Result: {report['result']['overall_status']}")


def example_export_report():
    """Example of exporting test report to JSON."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Export Report to JSON")
    print("="*70 + "\n")

    # Create and run test
    test = GroundContinuityTest(
        test_id="GC-005",
        module_id="PV-MODULE-55555",
        operator="Test Operator",
    )

    report = test.run_test(simulated=True)

    # Export to JSON
    output_file = Path(__file__).parent / "ground_continuity_report.json"
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\nReport exported to: {output_file}")
    print(f"File size: {output_file.stat().st_size} bytes")


def example_all_measurement_points():
    """Example testing all standard measurement points."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Comprehensive Measurement (All Points)")
    print("="*70 + "\n")

    # Get all measurement points
    all_points = [point.value for point in MeasurementPoint]

    # Create test
    test = GroundContinuityTest(
        test_id="GC-006",
        module_id="PV-MODULE-COMPREHENSIVE",
        operator="Lab Technician",
        measurement_points=all_points,
    )

    # Run test
    report = test.run_test(simulated=True)

    print(f"\nMeasurement Points Coverage: {len(all_points)} points")
    print("\nResults Summary:")
    for point in all_points:
        matching = [m for m in report['measurements'] if m['point'] == point]
        if matching:
            m = matching[0]
            status_symbol = "✓" if m['status'] == 'passed' else "✗"
            print(f"  {status_symbol} {point}: {m['resistance_ohm']:.4f} Ω")


if __name__ == "__main__":
    """Run all examples."""
    examples = [
        example_basic_test,
        example_custom_parameters,
        example_with_environmental_conditions,
        example_simulate_failure,
        example_export_report,
        example_all_measurement_points,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\nError in {example.__name__}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*70)
    print("All examples completed!")
    print("="*70 + "\n")
