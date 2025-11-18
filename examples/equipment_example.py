"""
Equipment Management System - Usage Example
Demonstrates complete workflow for managing test lab equipment
"""

from datetime import date, datetime, timedelta
from equipment import (
    EquipmentDB,
    Equipment,
    EquipmentCategory,
    EquipmentStatus,
    CalibrationRecord,
    MaintenanceLog,
    MaintenanceType,
    EquipmentReservation
)


def main():
    """Demonstrate equipment management system usage"""

    print("=" * 60)
    print("Equipment Management System - Demo")
    print("=" * 60)

    # Initialize database
    db = EquipmentDB("demo_equipment.db")
    print("\n✓ Database initialized")

    # ==================== Add Equipment ====================
    print("\n" + "=" * 60)
    print("1. Adding Equipment to Registry")
    print("=" * 60)

    equipment = Equipment(
        name="IV Tracer Pro 3000",
        manufacturer="PV Test Systems",
        model="IVT-3000",
        serial_number="IVT3000-2024-001",
        category=EquipmentCategory.IV_TRACER,
        location="Lab A - Bench 1",
        status=EquipmentStatus.AVAILABLE,
        calibration_due_date=date.today() + timedelta(days=180),
        calibration_interval_days=365,
        last_calibration_date=date.today() - timedelta(days=185),
        calibration_certificate_number="CAL-2023-001",
        specifications={
            "voltage_range": "0-1500V",
            "current_range": "0-20A",
            "accuracy": "±0.5%",
            "power_rating": "30kW"
        },
        accuracy="±0.5%",
        measurement_range="0-1500V, 0-20A",
        purchase_date=date(2024, 1, 15),
        purchase_cost=25000.00,
        responsible_person="Dr. John Smith",
        asset_tag="AST-IVT-001"
    )

    equipment_id = db.add_equipment(equipment)
    print(f"✓ Added equipment: {equipment.name}")
    print(f"  ID: {equipment_id}")
    print(f"  Serial: {equipment.serial_number}")
    print(f"  Location: {equipment.location}")

    # ==================== View Available Equipment ====================
    print("\n" + "=" * 60)
    print("2. Viewing Available Equipment")
    print("=" * 60)

    available = db.get_available(category=EquipmentCategory.IV_TRACER)
    print(f"\nAvailable IV Tracers: {len(available)}")
    for equip in available:
        print(f"  - {equip.name} ({equip.serial_number})")
        print(f"    Location: {equip.location}")
        print(f"    Status: {equip.status}")

    # ==================== Equipment Checkout ====================
    print("\n" + "=" * 60)
    print("3. Checking Out Equipment")
    print("=" * 60)

    log_id = db.checkout(
        equipment_id=equipment_id,
        user_name="Jane Doe",
        test_id=12345,
        purpose="PV module performance testing - Project Alpha",
        location_used="Outdoor Test Field A"
    )

    print(f"✓ Equipment checked out")
    print(f"  Log ID: {log_id}")
    print(f"  User: Jane Doe")
    print(f"  Purpose: PV module performance testing")

    # Verify status changed
    equip = db.get_equipment(equipment_id)
    print(f"  Current status: {equip.status}")

    # ==================== Equipment Checkin ====================
    print("\n" + "=" * 60)
    print("4. Checking In Equipment")
    print("=" * 60)

    db.checkin(
        equipment_id=equipment_id,
        condition="good",
        issues_reported=None
    )

    print(f"✓ Equipment checked in")
    equip = db.get_equipment(equipment_id)
    print(f"  Status: {equip.status}")

    # ==================== Usage History ====================
    print("\n" + "=" * 60)
    print("5. Viewing Usage History")
    print("=" * 60)

    history = db.get_usage_history(equipment_id=equipment_id)
    print(f"\nUsage history: {len(history)} record(s)")
    for log in history:
        print(f"\n  Checkout: {log.checkout_time}")
        print(f"  User: {log.user_name}")
        print(f"  Test ID: {log.test_id}")
        if log.checkin_time:
            print(f"  Checkin: {log.checkin_time}")
            if log.usage_duration:
                print(f"  Duration: {log.usage_duration:.2f} hours")

    # ==================== Add Calibration Record ====================
    print("\n" + "=" * 60)
    print("6. Recording Calibration (ISO 17025)")
    print("=" * 60)

    calibration = CalibrationRecord(
        equipment_id=equipment_id,
        calibration_date=date.today(),
        next_calibration_due=date.today() + timedelta(days=365),

        # ISO 17025 Requirements
        calibration_lab="NIST Traceable Calibration Laboratory",
        lab_accreditation="ISO/IEC 17025:2017 #A2LA-12345",
        certificate_number="CAL-2024-IVT-001",
        traceability="NIST",
        standard_used="NIST Reference Standard RS-IV-2024",

        # Results
        calibration_results={
            "voltage_accuracy": "±0.48%",
            "current_accuracy": "±0.49%",
            "measurement_points": 10,
            "all_within_specification": True
        },
        measurement_uncertainty={
            "voltage": "±0.1%",
            "current": "±0.1%"
        },
        pass_fail=True,

        # Environmental Conditions
        temperature=23.5,
        humidity=45.0,

        # Personnel
        performed_by="John Smith, Senior Calibration Technician",
        verified_by="Dr. Sarah Johnson",

        certificate_path="/docs/calibrations/CAL-2024-IVT-001.pdf",
        notes="Annual calibration performed per procedure CAL-PRO-001"
    )

    cal_id = db.add_calibration_record(calibration)
    print(f"✓ Calibration record added")
    print(f"  Record ID: {cal_id}")
    print(f"  Certificate: {calibration.certificate_number}")
    print(f"  Lab: {calibration.calibration_lab}")
    print(f"  Result: {'PASS' if calibration.pass_fail else 'FAIL'}")
    print(f"  Next due: {calibration.next_calibration_due}")

    # ==================== Add Maintenance Log ====================
    print("\n" + "=" * 60)
    print("7. Recording Maintenance")
    print("=" * 60)

    maintenance = MaintenanceLog(
        equipment_id=equipment_id,
        maintenance_type=MaintenanceType.PREVENTIVE,
        scheduled_date=date.today(),
        completed_date=date.today(),
        performed_by="ABC Maintenance Services",
        description="Annual preventive maintenance: cleaning, lubrication, functional testing",
        parts_replaced=["Air filter", "Cooling fan"],
        cost=350.00,
        verification_performed=True,
        verification_results="All functional tests passed. Performance within specifications.",
        next_maintenance_due=date.today() + timedelta(days=180),
        notes="Cooling fan replaced preventively due to bearing noise"
    )

    maint_id = db.add_maintenance_log(maintenance)
    print(f"✓ Maintenance record added")
    print(f"  Log ID: {maint_id}")
    print(f"  Type: {maintenance.maintenance_type}")
    print(f"  Performed by: {maintenance.performed_by}")
    print(f"  Cost: ${maintenance.cost:.2f}")
    print(f"  Next due: {maintenance.next_maintenance_due}")

    # ==================== Equipment Reservation ====================
    print("\n" + "=" * 60)
    print("8. Making Equipment Reservation")
    print("=" * 60)

    reservation = EquipmentReservation(
        equipment_id=equipment_id,
        reserved_by="Dr. Mike Johnson",
        test_id=67890,
        start_time=datetime.now() + timedelta(days=2, hours=9),
        end_time=datetime.now() + timedelta(days=2, hours=17),
        purpose="Long-term stability testing - Project Beta"
    )

    try:
        res_id = db.add_reservation(reservation)
        print(f"✓ Reservation created")
        print(f"  Reservation ID: {res_id}")
        print(f"  Reserved by: {reservation.reserved_by}")
        print(f"  Start: {reservation.start_time}")
        print(f"  End: {reservation.end_time}")
    except ValueError as e:
        print(f"✗ Reservation failed: {e}")

    # ==================== Check Calibration Due ====================
    print("\n" + "=" * 60)
    print("9. Checking Calibration Status")
    print("=" * 60)

    due_soon = db.get_calibration_due(days_ahead=365)
    print(f"\nEquipment requiring calibration in next 365 days: {len(due_soon)}")
    for equip in due_soon:
        days_until = (equip.calibration_due_date - date.today()).days
        status_icon = "✓" if days_until > 30 else "⚠️"
        print(f"  {status_icon} {equip.name}")
        print(f"     Serial: {equip.serial_number}")
        print(f"     Due: {equip.calibration_due_date} ({days_until} days)")

    # ==================== Equipment Utilization ====================
    print("\n" + "=" * 60)
    print("10. Equipment Utilization Report")
    print("=" * 60)

    # Add more usage for demonstration
    for i in range(5):
        db.checkout(equipment_id, user_name=f"User {i}", purpose="Testing")
        db.checkin(equipment_id)

    start_date = date.today() - timedelta(days=7)
    end_date = date.today()

    stats = db.get_equipment_utilization(equipment_id, start_date, end_date)

    print(f"\nUtilization Report")
    print(f"  Period: {stats['period_start']} to {stats['period_end']}")
    print(f"  Total uses: {stats['total_uses']}")
    print(f"  Total hours: {stats['total_hours']:.2f}")
    print(f"  Available hours: {stats['available_hours']}")
    print(f"  Utilization: {stats['utilization_percentage']:.1f}%")
    print(f"  Avg use duration: {stats['average_use_duration']:.2f} hours")

    # ==================== Summary ====================
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)

    all_equipment = db.list_equipment()
    print(f"\nTotal equipment in database: {len(all_equipment)}")
    print(f"Database file: demo_equipment.db")
    print("\nThe database has been created and populated with sample data.")
    print("You can now explore the data using the EquipmentDB class.")


if __name__ == "__main__":
    main()
