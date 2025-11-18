"""
Example usage of Insulation Resistance Test

Demonstrates:
- Basic usage with simulator
- Full test sequence
- Context manager usage
- Data logging and compliance
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from test_blocks.insulation import InsulationResistanceTest
from models.measurement import EnvironmentalConditions


def basic_example():
    """Basic usage example"""
    print("=" * 60)
    print("Example 1: Basic Single Measurement")
    print("=" * 60)

    # Create test instance
    test = InsulationResistanceTest(module="PV-001", operator="John Doe")

    # Initialize test
    if not test.initialize():
        print("Failed to initialize test")
        return

    # Perform measurement
    result = test.measure(voltage=1000, condition="wet", polarity="positive")

    # Display results
    print(f"\nTest Results:")
    print(f"  Module: {test.module}")
    print(f"  Test Voltage: {result.test.test_voltage}V")
    print(f"  Condition: {result.test.condition}")
    print(f"  Polarity: {result.test.polarity}")
    print(f"  Resistance: {result.test.resistance_mohm} MΩ")
    print(f"  Pass Status: {'PASS' if result.test.pass_status else 'FAIL'}")
    print(f"  Minimum Required: {test.WET_MINIMUM_RESISTANCE_MOHM} MΩ")

    # Finalize and get summary
    summary = test.finalize()
    print(f"\nTest Summary:")
    print(f"  Overall Status: {summary['overall_status']}")
    print(f"  Total Tests: {summary['total_tests']}")
    print(f"  Passed: {summary['passed']}")
    print(f"  Failed: {summary['failed']}")


def full_sequence_example():
    """Full test sequence with both polarities"""
    print("\n" + "=" * 60)
    print("Example 2: Full Test Sequence (Both Polarities)")
    print("=" * 60)

    # Create test with environmental conditions
    env_conditions = EnvironmentalConditions(
        temperature_c=25.0,
        humidity_percent=50.0,
        pressure_hpa=1013.25
    )

    test = InsulationResistanceTest(module="PV-002", operator="Jane Smith")

    if not test.initialize():
        print("Failed to initialize test")
        return

    # Run full sequence
    results = test.run_full_test_sequence(
        voltage=1000,
        condition="wet",
        test_both_polarities=True,
        environmental_conditions=env_conditions
    )

    print(f"\nCompleted {len(results)} measurements:")
    for i, result in enumerate(results, 1):
        print(f"\n  Measurement {i}:")
        print(f"    Polarity: {result.test.polarity}")
        print(f"    Resistance: {result.test.resistance_mohm} MΩ")
        print(f"    Status: {'PASS' if result.test.pass_status else 'FAIL'}")

    summary = test.finalize()
    print(f"\nFinal Status: {summary['overall_status']}")


def context_manager_example():
    """Using context manager for automatic cleanup"""
    print("\n" + "=" * 60)
    print("Example 3: Context Manager Usage")
    print("=" * 60)

    # Context manager handles initialization and finalization
    with InsulationResistanceTest(module="PV-003", operator="Bob Johnson") as test:
        # Dry condition test with 1000V
        result_dry = test.measure(voltage=1000, condition="dry")
        print(f"\nDry Condition Test:")
        print(f"  Resistance: {result_dry.test.resistance_mohm} MΩ")
        print(f"  Minimum Required: {test.DRY_MINIMUM_RESISTANCE_MOHM} MΩ")
        print(f"  Status: {'PASS' if result_dry.test.pass_status else 'FAIL'}")

    print("\nTest automatically finalized and equipment disconnected")


def wet_vs_dry_example():
    """Compare wet and dry condition tests"""
    print("\n" + "=" * 60)
    print("Example 4: Wet vs Dry Condition Comparison")
    print("=" * 60)

    test = InsulationResistanceTest(module="PV-004", operator="Alice Williams")

    if not test.initialize():
        print("Failed to initialize test")
        return

    # Wet condition test
    result_wet = test.measure(voltage=1000, condition="wet")

    # Dry condition test (simulated - in real scenario, module would be dried first)
    result_dry = test.measure(voltage=1000, condition="dry")

    print(f"\nComparison Results:")
    print(f"\n  Wet Condition:")
    print(f"    Resistance: {result_wet.test.resistance_mohm} MΩ")
    print(f"    Minimum: {test.WET_MINIMUM_RESISTANCE_MOHM} MΩ")
    print(f"    Status: {'PASS' if result_wet.test.pass_status else 'FAIL'}")

    print(f"\n  Dry Condition:")
    print(f"    Resistance: {result_dry.test.resistance_mohm} MΩ")
    print(f"    Minimum: {test.DRY_MINIMUM_RESISTANCE_MOHM} MΩ")
    print(f"    Status: {'PASS' if result_dry.test.pass_status else 'FAIL'}")

    ratio = result_dry.test.resistance_mohm / result_wet.test.resistance_mohm
    print(f"\n  Dry/Wet Ratio: {ratio:.2f}x")

    summary = test.finalize()
    print(f"\n  Overall Status: {summary['overall_status']}")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("INSULATION RESISTANCE TEST - EXAMPLES")
    print("=" * 60)

    try:
        # Run examples
        basic_example()
        full_sequence_example()
        context_manager_example()
        wet_vs_dry_example()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        print("\nGenerated files:")
        print("  - Test data: ./test_data/insulation/")
        print("  - Compliance records: ./compliance_records/insulation/")

    except Exception as e:
        print(f"\nError during examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
