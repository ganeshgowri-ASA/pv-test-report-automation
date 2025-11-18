"""Example usage of the Mechanical Load Test Block.

This script demonstrates how to use the MechanicalLoadTest class to perform
IEC 61215 compliant mechanical load testing with deflection monitoring and
power degradation analysis.
"""

from datetime import datetime

from pv_automation.test_blocks.mechanical import (
    DeflectionMeasurement,
    LoadType,
    MechanicalLoadTest,
    PowerMeasurement,
)


def example_static_load_test():
    """Example: Static front load test at 2400 Pa."""
    print("=" * 70)
    print("Example 1: Static Front Load Test (IEC 61215)")
    print("=" * 70)

    # Create test instance
    test = MechanicalLoadTest(
        module_id="PV-001",
        load_type=LoadType.STATIC_FRONT,
        load_pa=2400.0,
        operator_name="John Smith",
        equipment_ids=["PRESS-CHAMBER-001", "LVDT-SENSOR-001", "IV-TRACER-001"],
        environmental_conditions={
            "temperature_c": 23.5,
            "humidity_pct": 45.0,
            "atmospheric_pressure_kpa": 101.3
        }
    )

    # Pre-test flash measurement
    pre_test_power = PowerMeasurement(
        pmax_w=450.0,
        voc_v=48.5,
        isc_a=11.2,
        vmp_v=40.2,
        imp_a=11.19,
        fill_factor=0.827,
        irradiance_wm2=1000.0,
        temperature_c=25.0
    )
    test.set_pre_test_power(pre_test_power)
    print(f"Pre-test Pmax: {pre_test_power.pmax_w} W")

    # Simulate deflection measurements during static load
    print("\nApplying static load and monitoring deflection...")
    test.add_deflection_measurement(load_pa=0, deflection_mm=0, position="center")
    test.add_deflection_measurement(load_pa=600, deflection_mm=5.2, position="center")
    test.add_deflection_measurement(load_pa=1200, deflection_mm=10.8, position="center")
    test.add_deflection_measurement(load_pa=1800, deflection_mm=16.5, position="center")
    test.add_deflection_measurement(load_pa=2400, deflection_mm=22.3, position="center")

    print(f"Max deflection: {test.max_deflection_mm} mm")

    # Post-test flash measurement (slight degradation)
    post_test_power = PowerMeasurement(
        pmax_w=448.5,
        voc_v=48.4,
        isc_a=11.18,
        vmp_v=40.1,
        imp_a=11.18,
        fill_factor=0.826,
        irradiance_wm2=1000.0,
        temperature_c=25.0
    )
    test.set_post_test_power(post_test_power)
    print(f"Post-test Pmax: {post_test_power.pmax_w} W")

    # Execute test
    result = test.execute()

    print(f"\n{'Test Result':.<50} {'PASSED' if result else 'FAILED'}")
    print(f"Power Degradation: {test.power_degradation_pct:.2f}%")
    print(f"Max Deflection: {test.max_deflection_mm:.2f} mm")
    print(f"Duration: {test.duration_seconds:.1f} seconds")

    # Generate report
    report = test.generate_report()
    print(f"\nTest ID: {report['test_id']}")
    print(f"Status: {report['status']}")
    print(f"Pass Status: {report['pass_status']}")

    return test


def example_dynamic_load_test():
    """Example: Dynamic load test at ±1000 Pa for 1000 cycles."""
    print("\n" + "=" * 70)
    print("Example 2: Dynamic Load Test (IEC 61215)")
    print("=" * 70)

    # Create test instance
    test = MechanicalLoadTest(
        module_id="PV-002",
        load_type=LoadType.DYNAMIC,
        load_pa=1000.0,
        cycles=1000,
        operator_name="Jane Doe",
        equipment_ids=["CYCLIC-LOADER-001", "LVDT-SENSOR-002", "IV-TRACER-001"],
        environmental_conditions={
            "temperature_c": 24.0,
            "humidity_pct": 50.0,
            "atmospheric_pressure_kpa": 101.2
        }
    )

    # Pre-test flash measurement
    pre_test_power = PowerMeasurement(
        pmax_w=500.0,
        voc_v=49.0,
        isc_a=12.3,
        vmp_v=40.5,
        imp_a=12.35,
        fill_factor=0.829,
        irradiance_wm2=1000.0,
        temperature_c=25.0
    )
    test.set_pre_test_power(pre_test_power)
    print(f"Pre-test Pmax: {pre_test_power.pmax_w} W")

    # Simulate deflection measurements during dynamic load (sample cycles)
    print(f"\nRunning {test.cycles} dynamic load cycles...")
    sample_cycles = [1, 100, 250, 500, 750, 1000]

    for cycle in sample_cycles:
        # Positive load
        test.add_deflection_measurement(
            load_pa=1000,
            deflection_mm=12.5 + (cycle * 0.002),  # Slight increase over cycles
            position="center",
            cycle_number=cycle
        )
        # Negative load
        test.add_deflection_measurement(
            load_pa=-1000,
            deflection_mm=-12.3 - (cycle * 0.002),
            position="center",
            cycle_number=cycle
        )
        if cycle in [1, 500, 1000]:
            print(f"  Cycle {cycle:4d}: deflection = ±{12.5 + (cycle * 0.002):.2f} mm")

    print(f"Max deflection: {test.max_deflection_mm:.2f} mm")

    # Post-test flash measurement (acceptable degradation)
    post_test_power = PowerMeasurement(
        pmax_w=478.0,
        voc_v=48.8,
        isc_a=12.25,
        vmp_v=40.3,
        imp_a=11.86,
        fill_factor=0.825,
        irradiance_wm2=1000.0,
        temperature_c=25.0
    )
    test.set_post_test_power(post_test_power)
    print(f"Post-test Pmax: {post_test_power.pmax_w} W")

    # Execute test
    result = test.execute()

    print(f"\n{'Test Result':.<50} {'PASSED' if result else 'FAILED'}")
    print(f"Power Degradation: {test.power_degradation_pct:.2f}%")
    print(f"Max Deflection: {test.max_deflection_mm:.2f} mm")
    print(f"Cycles Completed: {test.cycles}")
    print(f"Duration: {test.duration_seconds:.1f} seconds")

    # Display statistics
    stats = test.calculate_statistics()
    print("\nDeflection Statistics:")
    print(f"  Mean: {stats['mean_deflection_mm']:.2f} mm")
    print(f"  Std Dev: {stats['std_deflection_mm']:.2f} mm")
    print(f"  Measurements: {stats['measurement_count']}")

    return test


def example_failed_test():
    """Example: Test that fails due to excessive power degradation."""
    print("\n" + "=" * 70)
    print("Example 3: Failed Test (Excessive Power Degradation)")
    print("=" * 70)

    # Create test instance
    test = MechanicalLoadTest(
        module_id="PV-003-DEFECTIVE",
        load_type=LoadType.STATIC_FRONT,
        load_pa=2400.0,
        operator_name="John Smith",
        equipment_ids=["PRESS-CHAMBER-001", "LVDT-SENSOR-001", "IV-TRACER-001"]
    )

    # Pre-test flash measurement
    pre_test_power = PowerMeasurement(
        pmax_w=450.0,
        voc_v=48.5,
        isc_a=11.2,
        vmp_v=40.2,
        imp_a=11.19,
        fill_factor=0.827
    )
    test.set_pre_test_power(pre_test_power)

    # Simulate excessive deflection
    test.add_deflection_measurement(load_pa=2400, deflection_mm=38.5, position="center")

    # Post-test flash measurement (significant degradation - module damaged)
    post_test_power = PowerMeasurement(
        pmax_w=420.0,  # > 5% degradation
        voc_v=48.0,
        isc_a=10.8,
        vmp_v=39.5,
        imp_a=10.63,
        fill_factor=0.811
    )
    test.set_post_test_power(post_test_power)

    # Execute test
    result = test.execute()

    print(f"\n{'Test Result':.<50} {'PASSED' if result else 'FAILED'}")
    print(f"Power Degradation: {test.power_degradation_pct:.2f}% (limit: 5.0%)")
    print(f"Max Deflection: {test.max_deflection_mm:.2f} mm")

    if test.error_messages:
        print("\nErrors:")
        for error in test.error_messages:
            print(f"  - {error}")

    return test


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("PV Module Mechanical Load Test Examples")
    print("IEC 61215 Compliance")
    print("=" * 70)

    # Run examples
    test1 = example_static_load_test()
    test2 = example_dynamic_load_test()
    test3 = example_failed_test()

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    tests = [test1, test2, test3]
    passed = sum(1 for t in tests if t.pass_status)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {len(tests) - passed}")
