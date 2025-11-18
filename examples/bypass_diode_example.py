"""
Example usage of Bypass Diode Test Block

Demonstrates IEC 61215 compliant bypass diode testing
for photovoltaic modules
"""

from test_blocks.bypass_diode import BypassDiodeTest
from datetime import datetime


def main():
    """Run bypass diode test example"""

    print("Bypass Diode Test Example")
    print("=" * 60)

    # Create test instance
    test = BypassDiodeTest(
        module="PV-001",
        test_id=1001,
        diode_count=3,
        operator="John Smith"
    )

    # Set environmental conditions (ISO 17025 requirement)
    test.set_environmental_conditions(
        temperature=25.0,  # °C
        humidity=45.0,     # %
        pressure=1013.25   # hPa
    )

    # Set equipment information (ISO 17025 requirement)
    test.set_equipment(
        equipment_id="SMU-2450-001",
        calibration_date=datetime(2025, 10, 15)
    )

    # Run comprehensive test on all diodes
    result = test.test_all_diodes()

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Module ID: {result.module_id}")
    print(f"Diodes tested: {len(result.forward_voltage)}")
    print(f"Overall Pass: {result.pass_status}")
    print(f"All activated: {result.activation_verified}")
    print(f"Test duration: {result.test_duration_seconds:.2f}s")

    # Individual diode results
    print("\nIndividual Diode Results:")
    print("-" * 60)
    for i, char in enumerate(result.diode_characteristics):
        print(f"\nDiode {i + 1}:")
        print(f"  Forward voltage @ 8A: {result.forward_voltage[i]:.3f}V")
        print(f"  Reverse leakage: {char.reverse_leakage_current_ua:.2f}µA")
        print(f"  Operating temp: {char.thermal_temperature_c:.1f}°C")
        print(f"  Activation voltage: {char.activation_voltage:.3f}V")
        print(f"  Activation verified: {char.activation_verified}")
        print(f"  Status: {'PASS' if char.overall_pass else 'FAIL'}")

    # Export results
    print("\n" + "=" * 60)
    print("EXPORT OPTIONS")
    print("=" * 60)

    # JSON export
    json_output = test.export_results(result, format='json')
    print("\nJSON Export (first 500 chars):")
    print(json_output[:500] + "...")

    # CSV export
    csv_output = test.export_results(result, format='csv')
    print("\nCSV Export:")
    print(csv_output)

    # Access V-I curve data
    print("\n" + "=" * 60)
    print("V-I CURVE DATA")
    print("=" * 60)
    for diode_idx, vi_points in result.vi_curve_data.items():
        print(f"\nDiode {diode_idx + 1}:")
        print("  Current (A) | Voltage (V)")
        print("  " + "-" * 25)
        for current, voltage in vi_points[:3]:  # Show first 3 points
            print(f"  {current:>10.1f} | {voltage:>10.3f}")
        print(f"  ... ({len(vi_points)} total points)")

    return result


if __name__ == "__main__":
    result = main()
