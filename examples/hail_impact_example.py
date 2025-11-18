"""
Example usage of Hail Impact Test Block

Demonstrates how to:
1. Create and configure a hail impact test
2. Execute the test
3. Access and display results
4. Generate reports
"""

import sys
import os
import json
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.test_blocks.iec_61215.hail_impact import HailImpactTest, run_hail_impact_test
from src.core.base_models import EquipmentInfo


def example_basic_usage():
    """Example 1: Basic hail impact test with default parameters."""
    print("=" * 70)
    print("EXAMPLE 1: Basic Hail Impact Test")
    print("=" * 70)

    # Create test instance
    test = HailImpactTest(
        block_id="HAIL-TEST-001",
        operator="John Smith",
        module_id=1001
    )

    # Set environmental conditions
    test.environmental_conditions = {
        "temperature_celsius": 25.0,
        "humidity_pct": 45.0,
        "pressure_kpa": 101.3
    }

    # Execute test
    print("\nExecuting test...")
    results = test.execute()

    # Post-process
    test.post_process()

    # Display results
    print(f"\nTest Status: {test.status.value}")
    print(f"Pass/Fail: {'PASS' if test.pass_status else 'FAIL'}")
    print(f"Power Degradation: {test.power_degradation_pct:.2f}%")
    print(f"Glass Breakage: {'YES' if test.glass_breakage else 'NO'}")
    print(f"\nNumber of Results: {len(results)}")

    for i, result in enumerate(results, 1):
        print(f"\nResult {i}:")
        print(f"  Passed: {result.passed}")
        print(f"  Value: {result.measurement_value} {result.unit or ''}")
        print(f"  Comments: {result.comments}")

    print("\n" + test.notes)


def example_custom_parameters():
    """Example 2: Hail impact test with custom parameters."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Custom Parameters Test")
    print("=" * 70)

    # Create test with custom parameters
    test = HailImpactTest(
        block_id="HAIL-TEST-002",
        operator="Jane Doe",
        module_id=2001,
        ball_diameter_mm=25.0,  # Standard 25mm
        target_velocity_ms=23.0,  # Standard 23 m/s
        impact_count=11  # Standard 11 points
    )

    # Add custom sample information
    test.sample_info.update({
        "manufacturer": "SolarTech Inc.",
        "model": "ST-450-PERC",
        "serial_number": "ST2024-001001",
        "rated_power_w": 450,
        "technology": "Monocrystalline PERC",
        "dimensions_mm": "2008 x 1002 x 35",
        "weight_kg": 24.5
    })

    # Set environmental conditions
    test.environmental_conditions = {
        "temperature_celsius": 24.5,
        "humidity_pct": 50.0,
        "pressure_kpa": 101.2,
        "test_location": "Lab A - Building 3"
    }

    print("\nTest Configuration:")
    print(f"  Module: {test.sample_info.get('model')}")
    print(f"  Serial: {test.sample_info.get('serial_number')}")
    print(f"  Ball Diameter: {test.ball_diameter_mm} mm")
    print(f"  Impact Velocity: {test.target_velocity_ms} m/s")
    print(f"  Impact Count: {test.impact_count}")

    # Execute and process
    test.execute()
    test.post_process()

    # Get summary
    summary = test.get_summary()
    print("\nTest Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")


def example_convenience_function():
    """Example 3: Using the convenience function."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Using Convenience Function")
    print("=" * 70)

    # Run test using convenience function
    test = run_hail_impact_test(
        module_id=3001,
        operator="Bob Johnson",
        ball_diameter=25.0,
        velocity=23.0
    )

    print(f"\nQuick Test Results:")
    print(f"  Block ID: {test.block_id}")
    print(f"  Status: {test.status.value}")
    print(f"  Pass: {test.pass_status}")
    print(f"  Power Degradation: {test.power_degradation_pct:.2f}%")


def example_detailed_report():
    """Example 4: Generate detailed JSON report."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Detailed Report Generation")
    print("=" * 70)

    # Create and run test
    test = HailImpactTest(
        block_id="HAIL-TEST-004",
        operator="Alice Chen",
        module_id=4001
    )

    test.environmental_conditions = {
        "temperature_celsius": 25.0,
        "humidity_pct": 45.0,
        "pressure_kpa": 101.3
    }

    test.execute()
    test.post_process()

    # Get detailed report
    report = test.get_detailed_report()

    # Save to JSON file
    report_filename = f"hail_impact_report_{test.block_id}.json"
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\nDetailed report saved to: {report_filename}")

    # Display key sections
    print("\nKey Report Sections:")
    print(f"  Block ID: {report['block_id']}")
    print(f"  Standard: {report['standard']}")
    print(f"  Operator: {report['operator']}")
    print(f"  Status: {report['status']}")

    hail_data = report['hail_impact_data']
    print(f"\nHail Impact Data:")
    print(f"  Glass Breakage: {hail_data['glass_breakage']}")
    print(f"  Power Degradation: {hail_data['power_degradation_pct']:.2f}%")
    print(f"  Pass Status: {hail_data['pass_status']}")

    print(f"\nFlash Test Before:")
    if hail_data['flash_test_before']:
        print(f"  Pmax: {hail_data['flash_test_before']['pmax_w']:.2f} W")
        print(f"  Voc: {hail_data['flash_test_before']['voc_v']:.2f} V")
        print(f"  Isc: {hail_data['flash_test_before']['isc_a']:.2f} A")
        print(f"  Fill Factor: {hail_data['flash_test_before']['fill_factor']:.3f}")

    print(f"\nFlash Test After:")
    if hail_data['flash_test_after']:
        print(f"  Pmax: {hail_data['flash_test_after']['pmax_w']:.2f} W")
        print(f"  Voc: {hail_data['flash_test_after']['voc_v']:.2f} V")
        print(f"  Isc: {hail_data['flash_test_after']['isc_a']:.2f} A")
        print(f"  Fill Factor: {hail_data['flash_test_after']['fill_factor']:.3f}")

    print(f"\nImpact Points: {len(hail_data['impact_points'])}")
    for point in hail_data['impact_points'][:3]:  # Show first 3
        print(f"  Point {point['point_number']}: {point['location']}")
        print(f"    Velocity: {point['velocity_ms']:.2f} m/s")


def example_equipment_tracking():
    """Example 5: Equipment calibration tracking."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Equipment Calibration Tracking")
    print("=" * 70)

    test = HailImpactTest(
        block_id="HAIL-TEST-005",
        operator="Carlos Rodriguez",
        module_id=5001
    )

    print("\nEquipment Used:")
    for equipment in test.equipment_used:
        print(f"\n  {equipment.name}")
        print(f"    ID: {equipment.equipment_id}")
        print(f"    Calibration Date: {equipment.calibration_date.strftime('%Y-%m-%d')}")
        print(f"    Due Date: {equipment.calibration_due_date.strftime('%Y-%m-%d')}")
        print(f"    Certificate: {equipment.calibration_certificate}")
        print(f"    Valid: {equipment.is_calibration_valid()}")
        print(f"    Uncertainty: {equipment.uncertainty}")


def example_parameter_validation():
    """Example 6: Parameter validation demonstration."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Parameter Validation")
    print("=" * 70)

    test = HailImpactTest(
        block_id="HAIL-TEST-006",
        operator="David Lee",
        module_id=6001,
        ball_diameter_mm=25.0,
        target_velocity_ms=23.0
    )

    print("\nTest Parameters:")
    for param_name, param in test.parameters.items():
        print(f"\n  {param.name}:")
        print(f"    Value: {param.value} {param.unit or ''}")
        if param.tolerance:
            print(f"    Tolerance: [{param.tolerance.get('min')}, {param.tolerance.get('max')}]")
            print(f"    Within Tolerance: {param.is_within_tolerance()}")

    # Validate all parameters
    print("\nValidating all parameters...")
    is_valid = test.validate_parameters()
    print(f"Validation Result: {'PASS' if is_valid else 'FAIL'}")

    if not is_valid:
        print("\nValidation Notes:")
        print(test.notes)


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("HAIL IMPACT TEST - EXAMPLE DEMONSTRATIONS")
    print("IEC 61215 Section 10.17")
    print("=" * 70)

    try:
        example_basic_usage()
        example_custom_parameters()
        example_convenience_function()
        example_detailed_report()
        example_equipment_tracking()
        example_parameter_validation()

        print("\n" + "=" * 70)
        print("All examples completed successfully!")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\nError running examples: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
