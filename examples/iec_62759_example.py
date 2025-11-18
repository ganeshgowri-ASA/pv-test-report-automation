"""
IEC 62759 Transportation Testing - Example Usage

This example demonstrates the complete IEC 62759 test sequence
for PV module transportation testing with ISO 17025 compliance.
"""

import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from src.protocols.iec.iec_62759 import IEC62759Controller
from src.equipment.solar_simulator import SolarSimulator
from src.equipment.load_frame import LoadFrame
from src.equipment.thermal_chamber import ThermalChamber


def example_basic_usage():
    """
    Basic usage example - minimal setup
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Basic IEC 62759 Test")
    print("=" * 70)

    # Create test controller
    test = IEC62759Controller(
        module_id="PV-001",
        technician_id="TECH-001"
    )

    # Run full test sequence
    result = test.run_full_sequence()

    # Print results
    print(f"\nTest Status: {result.status.value}")
    print(f"Pass/Fail: {result.pass_fail.value}")
    print(f"Power Degradation: {test.degradation_pct:.2f}%")

    # Generate report
    report = test.generate_report()
    print(f"\nTest Report Generated:")
    print(f"  Initial Pmax: {report['initial_measurements']['pmax']:.2f} W")
    print(f"  Final Pmax: {report['final_measurements']['pmax']:.2f} W")
    print(f"  Degradation: {report['degradation']['power_degradation_pct']:.2f}%")


def example_with_custom_parameters():
    """
    Example with custom test parameters
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Custom Test Parameters")
    print("=" * 70)

    # Create test controller with specific test ID
    test = IEC62759Controller(
        module_id="PV-002",
        test_id=12345,
        technician_id="TECH-002"
    )

    # Connect equipment
    test.connect_equipment()

    # Run individual test steps with custom parameters
    print("\n1. Initial Flash Test...")
    test.step1_initial_flash_test()

    print("\n2. Edge Loading with custom load...")
    test.step2_edge_loading(
        load_pa=750,  # Custom load (instead of default 600 Pa)
        duration_hours=2.0  # Custom duration (instead of default 1 hour)
    )

    print("\n3. Dynamic Loading with custom frequency...")
    test.step3_dynamic_mechanical_loading(
        load_pa=1000,
        cycles=1000,
        frequency_hz=1.5  # Custom frequency
    )

    print("\n4. Thermal Cycling...")
    test.step4_thermal_cycling(
        cycles=50,
        low_temp=-40,
        high_temp=85
    )

    print("\n5. Final Flash Test...")
    test.step5_final_flash_test()

    print("\n6. Visual Inspection...")
    test.step6_visual_inspection()

    # Calculate results
    pass_fail = test.calculate_pass_fail()
    print(f"\nOverall Result: {pass_fail.value}")

    # Disconnect equipment
    test.disconnect_equipment()


def example_with_equipment_instances():
    """
    Example with pre-configured equipment instances
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Using Pre-configured Equipment")
    print("=" * 70)

    # Create and configure equipment
    solar_sim = SolarSimulator(equipment_id="SIM-001")
    solar_sim.set_irradiance(1000.0)  # 1000 W/m²
    solar_sim.set_temperature(25.0)  # 25°C

    load_frame = LoadFrame(equipment_id="LOAD-001")

    thermal_chamber = ThermalChamber(equipment_id="THERMAL-001")

    # Set calibration info for ISO 17025 compliance
    solar_sim.set_calibration_info(
        calibration_date=datetime(2024, 1, 15),
        uncertainty={
            'pmax': 0.02,  # ±2%
            'voc': 0.01,   # ±1%
            'isc': 0.02    # ±2%
        }
    )

    # Create test controller with equipment
    test = IEC62759Controller(
        module_id="PV-003",
        test_id=12346,
        solar_simulator=solar_sim,
        load_frame=load_frame,
        thermal_chamber=thermal_chamber,
        technician_id="TECH-003"
    )

    # Add ISO 17025 compliance data
    test.result.compliance_data.update({
        'equipment_ids': ['SIM-001', 'LOAD-001', 'THERMAL-001'],
        'calibration_dates': {
            'SIM-001': '2024-01-15',
            'LOAD-001': '2024-02-01',
            'THERMAL-001': '2024-01-20'
        },
        'environmental_conditions': {
            'lab_temperature': 23.5,
            'lab_humidity': 45.0,
            'atmospheric_pressure': 101.3
        },
        'measurement_uncertainty': {
            'pmax': '±2%',
            'temperature': '±0.5°C',
            'load': '±5 Pa'
        }
    })

    # Run test
    result = test.run_full_sequence()

    # Generate comprehensive report
    report = test.generate_report()

    print("\nTest Report Summary:")
    print(f"  Test ID: {report['test_info']['test_id']}")
    print(f"  Module: {report['test_info']['module_id']}")
    print(f"  Status: {report['test_info']['status']}")
    print(f"  Result: {report['test_info']['pass_fail']}")
    print(f"\nISO 17025 Compliance:")
    print(f"  Technician: {report['iso_17025_compliance']['technician_id']}")
    print(f"  Equipment: {report['iso_17025_compliance'].get('equipment_ids', [])}")
    print(f"  Lab Conditions: {report['iso_17025_compliance'].get('environmental_conditions', {})}")


def example_database_integration():
    """
    Example showing database integration
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Database Integration")
    print("=" * 70)

    from src.models.base import get_db_session
    from src.models.iec_62759 import IEC62759Test, IEC62759Module

    # Get database session
    session = get_db_session()

    # Create module record
    module = IEC62759Module(
        module_id="PV-004",
        manufacturer="SolarTech Inc.",
        model="ST-300P",
        serial_number="SN-2024-001",
        rated_power_w=300.0,
        rated_voltage=45.0,
        rated_current=8.9,
        cell_technology="mono-Si",
        created_by="admin",
        updated_by="admin"
    )
    session.add(module)
    session.commit()

    print(f"Module registered: {module.module_id}")

    # Run test
    test = IEC62759Controller(
        module_id="PV-004",
        test_id=12347,
        technician_id="TECH-004"
    )
    result = test.run_full_sequence()

    # Create test record
    test_record = IEC62759Test(
        test_id=12347,
        module_id="PV-004",
        test_date=datetime.now(),
        initial_pmax=result.measurements['initial_pmax'],
        final_pmax=result.measurements['final_pmax'],
        power_degradation_pct=result.measurements.get('power_degradation_pct'),
        edge_load_result="pass" if result.test_data['edge_load_pass'] else "fail",
        dynamic_load_result="pass" if result.test_data['dynamic_load_pass'] else "fail",
        thermal_result="pass" if result.test_data['thermal_pass'] else "fail",
        visual_inspection_result="pass" if result.test_data['visual_pass'] else "fail",
        pass_status=result.pass_fail.value == "pass",
        test_status=result.status.value,
        technician_id="TECH-004",
        created_by="TECH-004",
        updated_by="TECH-004"
    )

    # Calculate degradation
    test_record.calculate_degradation()

    session.add(test_record)
    session.commit()

    print(f"Test record saved: ID {test_record.id}")
    print(f"Pass Status: {test_record.pass_status}")

    session.close()


if __name__ == "__main__":
    print("\n" + "#" * 70)
    print("IEC 62759 TRANSPORTATION TESTING - EXAMPLE USAGE")
    print("#" * 70)

    # Run examples
    example_basic_usage()
    example_with_custom_parameters()
    example_with_equipment_instances()
    example_database_integration()

    print("\n" + "#" * 70)
    print("ALL EXAMPLES COMPLETED")
    print("#" * 70 + "\n")
