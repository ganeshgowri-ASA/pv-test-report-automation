"""
Example usage of IEC 61701 Salt Mist Corrosion Test Handler

This script demonstrates how to use the IEC61701Handler to test
PV modules for corrosion resistance in marine and coastal environments.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime
from src.protocols.base import SpecimenInfo
from src.protocols.iec_61701_handler import (
    IEC61701Handler,
    SeverityLevel,
    SEVERITY_CONFIGS
)


def create_example_specimen() -> SpecimenInfo:
    """Create example specimen information"""
    return SpecimenInfo(
        specimen_id="PV-2024-001",
        manufacturer="Example Solar Inc.",
        model="ES-400M-72",
        serial_number="SN20240115-001",
        rated_power=400.0,  # 400W
        rated_voltage=48.0,  # 48V
        rated_current=8.33,  # 8.33A
        technology="Mono-Si PERC",
        dimensions={
            'length': 2.008,  # meters
            'width': 1.002,   # meters
            'thickness': 0.040,  # meters
            'area': 2.012  # m²
        },
        manufacturing_date="2024-01-15",
        additional_info={
            'frame_material': 'Anodized Aluminum',
            'glass_type': 'Tempered low-iron',
            'backsheet': 'Multi-layer polymer',
            'junction_box': 'IP68 rated'
        }
    )


def run_severity_level_test(severity_level: SeverityLevel):
    """
    Run IEC 61701 test for a specific severity level

    Args:
        severity_level: Severity level to test (1-6)
    """
    print(f"\n{'='*80}")
    print(f"IEC 61701:2020 Salt Mist Corrosion Test")
    print(f"Severity Level {severity_level.value}")
    print(f"{'='*80}\n")

    # Get severity configuration
    config = SEVERITY_CONFIGS[severity_level]
    print(f"Test Configuration:")
    print(f"  Level: {config.level.value} - {config.description}")
    print(f"  Environment: {config.typical_environment}")
    print(f"  Distance from coast: {config.distance_from_coast}")
    print(f"  Exposure duration: {config.exposure_hours} hours ({config.exposure_duration_days:.1f} days)")
    print(f"  Number of cycles: {config.cycles}")

    # Create specimen
    specimen = create_example_specimen()

    # Configure test
    test_config = {
        'operator': 'Jane Smith',
        'facility': 'Example Test Laboratory',
        'equipment': {
            'salt_chamber': 'ASTM-B117-Chamber-01',
            'iv_tracer': 'IVT-1000-Pro',
            'megohmmeter': 'FLUKE-1550C'
        }
    }

    # Create test handler
    handler = IEC61701Handler(
        specimen_info=specimen,
        severity_level=severity_level,
        config=test_config
    )

    # Initialize equipment
    print(f"\n{'-'*80}")
    print("Initializing Test Equipment")
    print(f"{'-'*80}")
    handler.initialize_equipment()

    # Setup test parameters
    print(f"\n{'-'*80}")
    print("Test Parameters")
    print(f"{'-'*80}")
    params = handler.setup_test_parameters()
    for param in params:
        tolerance_str = f" ± {param.tolerance}" if param.tolerance else ""
        print(f"  {param.name}: {param.value}{tolerance_str} {param.unit}")
        if param.description:
            print(f"    ({param.description})")

    # Execute test sequence
    print(f"\n{'-'*80}")
    print("Executing Test Sequence")
    print(f"{'-'*80}")
    results = handler.execute_test_sequence()

    # Validate results
    print(f"\n{'-'*80}")
    print("Validating Results")
    print(f"{'-'*80}")
    is_valid = handler.validate_results()

    # Print summary
    handler.print_summary()

    # Generate report
    print(f"{'-'*80}")
    print("Generating Report")
    print(f"{'-'*80}")
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
    os.makedirs(output_dir, exist_ok=True)

    report_path = handler.generate_report(output_dir, format='json')
    print(f"Report generated: {report_path}")

    return handler


def demonstrate_all_severity_levels():
    """Demonstrate test execution for all severity levels"""
    print("\n" + "="*80)
    print("IEC 61701:2020 - All Severity Levels Overview")
    print("="*80 + "\n")

    print("Severity Level Specifications:\n")
    for level, config in SEVERITY_CONFIGS.items():
        print(f"Level {level.value}: {config.description}")
        print(f"  Environment: {config.typical_environment}")
        print(f"  Distance from coast: {config.distance_from_coast}")
        print(f"  Exposure: {config.exposure_hours}h ({config.exposure_duration_days:.1f} days)")
        print(f"  Cycles: {config.cycles}")
        print()

    print(f"\n{'='*80}")
    print("NOTE: This is a demonstration script.")
    print("In production, each test would take hours to days to complete.")
    print("="*80 + "\n")


def main():
    """Main demonstration function"""
    # Show overview of all severity levels
    demonstrate_all_severity_levels()

    # Run example test for Severity Level 4 (Coastal Zone)
    # This is the most common level for coastal installations
    print("\n" + "="*80)
    print("DEMONSTRATION: Running Severity Level 4 Test")
    print("(Coastal Zone - High Corrosivity)")
    print("="*80 + "\n")

    handler = run_severity_level_test(SeverityLevel.LEVEL_4)

    print("\n" + "="*80)
    print("Demonstration Complete")
    print("="*80)
    print("\nTo test other severity levels, use:")
    print("  - SeverityLevel.LEVEL_1 for far inland installations")
    print("  - SeverityLevel.LEVEL_2 for inland areas")
    print("  - SeverityLevel.LEVEL_3 for near-coast installations")
    print("  - SeverityLevel.LEVEL_4 for coastal zone (demonstrated above)")
    print("  - SeverityLevel.LEVEL_5 for marine/offshore")
    print("  - SeverityLevel.LEVEL_6 for extreme marine/splash zone")
    print()


if __name__ == "__main__":
    main()
