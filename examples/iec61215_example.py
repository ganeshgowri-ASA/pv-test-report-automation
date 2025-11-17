"""
Example usage of IEC 61215 Protocol Engine

This example demonstrates how to:
1. Create a module under test
2. Initialize the IEC 61215 protocol
3. Execute the complete test sequence
4. Generate compliance reports
"""
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.protocols.iec61215 import IEC61215Protocol
from core.models.test_result import ModuleUnderTest
from core.models.measurement import Equipment, Uncertainty
from core.reports.generator import ReportGenerator
from core.config.settings import SystemConfig, load_config


def create_example_module() -> ModuleUnderTest:
    """Create an example PV module for testing."""
    return ModuleUnderTest(
        manufacturer="SolarTech Industries",
        model="ST-M350-72",
        serial_number="ST2024001234",
        module_type="crystalline",  # or "thin_film"

        # Nameplate ratings (STC)
        rated_power=350.0,  # W
        rated_voltage=37.2,  # V
        rated_current=9.41,  # A
        open_circuit_voltage=45.8,  # V
        short_circuit_current=10.12,  # A

        # Physical characteristics
        length=1755.0,  # mm
        width=1038.0,  # mm
        thickness=35.0,  # mm
        weight=19.5,  # kg
        area=1.82,  # m²

        # Cell information
        cell_type="Monocrystalline PERC",
        number_of_cells=72,
        cell_technology="Half-cut cells",

        # Additional info
        manufacture_date=datetime(2024, 1, 15),
        frame_type="Aluminum alloy",
        junction_box="IP67 rated",
        connector_type="MC4",
        glass_type="3.2mm tempered glass",
        backsheet_type="White TPT",
    )


def create_example_equipment() -> Equipment:
    """Create example test equipment."""
    return Equipment(
        id="IV-TRACER-001",
        name="I-V Curve Tracer",
        manufacturer="Keysight Technologies",
        model="B2900A Series",
        serial_number="MY12345678",
        calibration_date=datetime.now() - timedelta(days=60),
        calibration_due_date=datetime.now() + timedelta(days=305),
        calibration_certificate="CAL-2024-0123",
        accuracy=0.025,  # ±2.5%
    )


def run_iec61215_test_sequence():
    """Run complete IEC 61215 test sequence."""

    print("=" * 80)
    print("IEC 61215-2:2021 Test Sequence Example")
    print("=" * 80)
    print()

    # Create module under test
    print("Creating module under test...")
    module = create_example_module()
    print(f"  Manufacturer: {module.manufacturer}")
    print(f"  Model: {module.model}")
    print(f"  Serial Number: {module.serial_number}")
    print(f"  Rated Power: {module.rated_power} W")
    print()

    # Initialize protocol
    print("Initializing IEC 61215 protocol...")
    protocol = IEC61215Protocol()

    # Initialize test sequence
    sequence = protocol.initialize_sequence(
        module=module,
        laboratory_name="Advanced PV Testing Laboratory",
        laboratory_accreditation="ISO/IEC 17025:2017, NABL TC-1234",
        test_report_number=f"IEC61215-2024-{module.serial_number}",
        test_engineer="Dr. John Smith",
    )

    print(f"  Test sequence created: {sequence.sequence_id}")
    print(f"  Total test steps: {len(sequence.steps)}")
    print()

    # Display test sequence
    print("Test Sequence:")
    print("-" * 80)
    for step in sequence.steps[:10]:  # Show first 10 steps
        print(f"  {step.sequence_number:3d}. {step.test_name}")
    print(f"  ... ({len(sequence.steps) - 10} more tests)")
    print()

    # Execute test sequence (simulated)
    print("Executing test sequence (simulated)...")
    print("Note: In production, this would interface with real test equipment.")
    print()

    equipment = create_example_equipment()

    # Simulate execution of first few tests
    test_count = 0
    max_tests = 5  # Limit for example

    for step in sequence.steps:
        if test_count >= max_tests:
            print(f"  ... (skipping remaining {len(sequence.steps) - test_count} tests for example)")
            break

        can_execute, reason = step.can_execute(
            sequence.get_completed_steps(),
            module.module_type
        )

        if not can_execute:
            continue

        print(f"  Executing: {step.test_name}...")

        # Execute test with simulated data
        result = protocol.execute_test(
            step,
            equipment=equipment,
            # Simulated test parameters
            iv_data={
                "Pmax": 350.0 if test_count == 0 else 348.0,
                "Voc": 45.8,
                "Isc": 10.12,
                "Vmp": 37.2,
                "Imp": 9.41,
                "FF": 75.5,
            } if "MST02" in step.test_id else None,
        )

        step.mark_completed(result)
        test_count += 1

        print(f"    Status: {result.status.value}")
        print(f"    Compliance: {result.compliance_status.value}")
        if result.measurements:
            print(f"    Measurements: {len(result.measurements)} recorded")
        print()

    # Evaluate overall compliance
    sequence.evaluate_overall_compliance()

    print("Test Sequence Summary:")
    print("-" * 80)
    progress = sequence.get_progress()
    print(f"  Total tests: {progress['total_steps']}")
    print(f"  Completed: {progress['completed']}")
    print(f"  Skipped: {progress['skipped']}")
    print(f"  Pending: {progress['pending']}")
    print(f"  Progress: {progress['progress_percent']:.1f}%")
    print(f"  Overall compliance: {sequence.overall_compliance.value.upper()}")
    print()

    # Generate compliance report
    print("Generating compliance report...")
    report_data = protocol.generate_compliance_report()

    # Save reports
    output_dir = Path("./output")
    output_dir.mkdir(exist_ok=True)

    report_gen = ReportGenerator()

    # Generate JSON report
    json_path = report_gen.generate_iec61215_report(
        report_data,
        output_dir / f"report_{module.serial_number}",
        format="json"
    )
    print(f"  JSON report saved: {json_path}")

    # Generate HTML report
    html_path = report_gen.generate_iec61215_report(
        report_data,
        output_dir / f"report_{module.serial_number}",
        format="html"
    )
    print(f"  HTML report saved: {html_path}")

    # Generate CSV export
    csv_path = report_gen.generate_iec61215_report(
        report_data,
        output_dir / f"report_{module.serial_number}",
        format="excel"
    )
    print(f"  CSV export saved: {csv_path}")

    print()
    print("=" * 80)
    print("Example completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    run_iec61215_test_sequence()
