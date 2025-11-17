"""
Basic Usage Example

Demonstrates how to use the database models for the PV test report automation system.
"""

from datetime import date, datetime, timedelta
from database import init_db, get_session
from database.models import (
    Equipment, EquipmentStatus,
    User, UserRole, UserStatus,
    Sample, SampleStatus, SampleType,
    Test, TestType, TestStatus, PassFailStatus,
    Report, ReportType, ReportStatus,
    Audit, AuditAction, AuditSeverity
)


def create_sample_data():
    """Create sample data to demonstrate the database models."""

    # Initialize database
    print("Initializing database...")
    db_config = init_db(database_url="sqlite:///./pv_test_lab_demo.db", echo=True)

    with next(db_config.get_session()) as session:
        # 1. Create Equipment
        print("\n1. Creating test equipment...")
        solar_simulator = Equipment(
            name="Solar Simulator AAA Class",
            model_number="SS-1000X",
            serial_number="SS1000-2024-001",
            manufacturer="Newport Corporation",
            calibration_date=date(2024, 1, 15),
            calibration_due_date=date(2025, 1, 15),
            calibration_interval_days=365,
            calibration_certificate_number="CAL-2024-001",
            uncertainty=2.0,
            uncertainty_unit="%",
            uncertainty_description="±2% at standard test conditions",
            status=EquipmentStatus.ACTIVE,
            location="Testing Lab A"
        )
        session.add(solar_simulator)

        multimeter = Equipment(
            name="High Precision Multimeter",
            model_number="DMM-7510",
            serial_number="DMM7510-2024-001",
            manufacturer="Keithley Instruments",
            calibration_date=date(2024, 2, 1),
            calibration_due_date=date(2025, 2, 1),
            calibration_interval_days=365,
            uncertainty=0.015,
            uncertainty_unit="%",
            status=EquipmentStatus.ACTIVE,
            location="Testing Lab A"
        )
        session.add(multimeter)

        # 2. Create Users
        print("\n2. Creating users...")
        admin_user = User(
            username="admin",
            email="admin@pvlab.com",
            full_name="Admin User",
            employee_id="EMP001",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            reviewer_flag=True,
            approver_flag=True,
            password_hash="hashed_password_here",  # In production, use proper password hashing
            contact={
                "phone": "+1-555-0100",
                "extension": "1000"
            },
            department="Management"
        )
        session.add(admin_user)

        test_engineer = User(
            username="jsmith",
            email="jsmith@pvlab.com",
            full_name="John Smith",
            employee_id="EMP002",
            role=UserRole.TEST_ENGINEER,
            status=UserStatus.ACTIVE,
            reviewer_flag=True,
            approver_flag=False,
            password_hash="hashed_password_here",
            contact={
                "phone": "+1-555-0101",
                "extension": "1001"
            },
            department="Testing Lab",
            qualifications=[
                {
                    "name": "IEC 61215 Certified Technician",
                    "issuer": "TÜV Rheinland",
                    "date": "2023-06-15"
                }
            ]
        )
        session.add(test_engineer)

        # 3. Create Sample
        print("\n3. Creating PV module sample...")
        sample = Sample(
            sample_number="S-2024-001",
            sample_type=SampleType.MODULE,
            protocol="IEC 61215-2:2021",
            scope="Full type approval testing per IEC 61215-2:2021 including all MQT tests",
            customer_name="Solar Tech Industries",
            customer_po_number="PO-2024-1234",
            customer_contact={
                "name": "Jane Doe",
                "email": "jane.doe@solartech.com",
                "phone": "+1-555-2000"
            },
            manufacturer="High Efficiency Solar Co.",
            model_number="HES-400W-MONO",
            serial_numbers=["HES400-001", "HES400-002", "HES400-003"],
            quantity=3,
            received_date=date(2024, 1, 15),
            expected_completion_date=date(2024, 3, 15),
            status=SampleStatus.IN_PROGRESS,
            nameplate_ratings={
                "pmax": 400,
                "pmax_tolerance": "+5/-0",
                "voc": 49.5,
                "isc": 10.5,
                "vmp": 41.2,
                "imp": 9.71,
                "efficiency": 20.5
            },
            physical_dimensions={
                "length_mm": 1722,
                "width_mm": 1134,
                "thickness_mm": 35,
                "weight_kg": 22.5,
                "cells": "120 half-cut monocrystalline"
            },
            bom={
                "cells": "M10 monocrystalline PERC",
                "glass_front": "3.2mm tempered AR coated",
                "glass_back": "2.0mm tempered",
                "encapsulant": "POE",
                "frame": "Anodized aluminum",
                "junction_box": "IP68 rated with bypass diodes"
            },
            storage_location="Rack A-12"
        )
        session.add(sample)
        session.flush()  # Get sample.id

        # 4. Create Tests
        print("\n4. Creating test records...")

        # Visual Inspection
        visual_test = Test(
            sample_id=sample.id,
            test_number="T-2024-001-001",
            type=TestType.VISUAL_INSPECTION,
            test_standard_reference="IEC 61215-2:2021 MQT 01",
            description="Visual inspection for defects, workmanship, and compliance",
            test_date=date(2024, 1, 16),
            start_time=datetime(2024, 1, 16, 9, 0),
            end_time=datetime(2024, 1, 16, 10, 30),
            performed_by_user_id=test_engineer.id,
            status=TestStatus.COMPLETED,
            pass_fail=PassFailStatus.PASS,
            results_summary={
                "overall": "Pass",
                "defects_found": 0,
                "observations": "No visible defects, good workmanship"
            },
            notes="Module construction and labeling meet requirements"
        )
        session.add(visual_test)

        # Electrical Performance Test
        performance_test = Test(
            sample_id=sample.id,
            equipment_id=solar_simulator.id,
            test_number="T-2024-001-002",
            type=TestType.ELECTRICAL_PERFORMANCE,
            test_standard_reference="IEC 61215-2:2021 MQT 01",
            description="Electrical performance at STC (1000 W/m², 25°C, AM1.5)",
            test_date=date(2024, 1, 17),
            start_time=datetime(2024, 1, 17, 10, 0),
            end_time=datetime(2024, 1, 17, 11, 30),
            performed_by_user_id=test_engineer.id,
            reviewed_by_user_id=admin_user.id,
            calibration_valid=True,
            readings=[
                {
                    "module": "HES400-001",
                    "voc": 49.52,
                    "isc": 10.48,
                    "pmax": 402.5,
                    "vmp": 41.18,
                    "imp": 9.77,
                    "ff": 77.5
                },
                {
                    "module": "HES400-002",
                    "voc": 49.48,
                    "isc": 10.51,
                    "pmax": 403.2,
                    "vmp": 41.15,
                    "imp": 9.80,
                    "ff": 77.4
                },
                {
                    "module": "HES400-003",
                    "voc": 49.55,
                    "isc": 10.46,
                    "pmax": 401.8,
                    "vmp": 41.22,
                    "imp": 9.75,
                    "ff": 77.6
                }
            ],
            test_conditions={
                "irradiance": 1000,
                "spectrum": "AM 1.5G",
                "module_temperature": 25,
                "ambient_temperature": 23,
                "humidity": 45
            },
            uncertainty={
                "pmax": "±2.5%",
                "voltage": "±0.5%",
                "current": "±0.5%"
            },
            acceptance_criteria={
                "pmax_min": 380,  # -5% of 400W
                "tolerance_met": True
            },
            status=TestStatus.COMPLETED,
            pass_fail=PassFailStatus.PASS,
            reviewed=True,
            review_date=datetime(2024, 1, 17, 14, 0),
            results_summary={
                "average_pmax": 402.5,
                "min_pmax": 401.8,
                "max_pmax": 403.2,
                "within_tolerance": True
            }
        )
        session.add(performance_test)

        # Insulation Test
        insulation_test = Test(
            sample_id=sample.id,
            equipment_id=multimeter.id,
            test_number="T-2024-001-003",
            type=TestType.INSULATION_TEST,
            test_standard_reference="IEC 61215-2:2021 MQT 02",
            description="Wet leakage current test",
            test_date=date(2024, 1, 18),
            performed_by_user_id=test_engineer.id,
            calibration_valid=True,
            status=TestStatus.COMPLETED,
            pass_fail=PassFailStatus.PASS,
            test_conditions={
                "test_voltage": 1000,
                "duration_hours": 2,
                "water_resistivity": "< 5000 Ω·cm"
            },
            readings=[
                {
                    "module": "HES400-001",
                    "leakage_current_ma": 0.15
                },
                {
                    "module": "HES400-002",
                    "leakage_current_ma": 0.12
                },
                {
                    "module": "HES400-003",
                    "leakage_current_ma": 0.14
                }
            ],
            acceptance_criteria={
                "max_leakage_current_ma": 2.0
            },
            results_summary={
                "max_leakage": 0.15,
                "all_pass": True
            }
        )
        session.add(insulation_test)

        session.flush()  # Get test IDs

        # 5. Create Report
        print("\n5. Creating test report...")
        report = Report(
            report_number="RPT-2024-001",
            revision=0,
            type=ReportType.TYPE_APPROVAL,
            protocol="IEC 61215-2:2021",
            additional_standards=["IEC 61730-1:2016", "IEC 61730-2:2016"],
            sample_id=sample.id,
            customer={
                "name": "Solar Tech Industries",
                "address": "123 Solar Street, Tech City, TC 12345",
                "contact": "Jane Doe",
                "email": "jane.doe@solartech.com",
                "po_number": "PO-2024-1234"
            },
            title="Type Approval Test Report - High Efficiency Solar Co. HES-400W-MONO",
            summary="This report presents the results of type approval testing performed on "
                   "High Efficiency Solar Co. HES-400W-MONO photovoltaic modules according to "
                   "IEC 61215-2:2021.",
            sections=[
                {
                    "order": 1,
                    "heading": "1. Introduction",
                    "content": "Type approval testing per IEC 61215-2:2021"
                },
                {
                    "order": 2,
                    "heading": "2. Sample Description",
                    "content": "Monocrystalline silicon PV modules, 400W rated power"
                },
                {
                    "order": 3,
                    "heading": "3. Test Results",
                    "content": "Summary of test results"
                },
                {
                    "order": 4,
                    "heading": "4. Conclusion",
                    "content": "All tests passed"
                }
            ],
            tables=[
                {
                    "name": "Electrical Performance Results",
                    "headers": ["Module", "Voc (V)", "Isc (A)", "Pmax (W)", "Vmp (V)", "Imp (A)", "FF (%)"],
                    "rows": [
                        ["HES400-001", "49.52", "10.48", "402.5", "41.18", "9.77", "77.5"],
                        ["HES400-002", "49.48", "10.51", "403.2", "41.15", "9.80", "77.4"],
                        ["HES400-003", "49.55", "10.46", "401.8", "41.22", "9.75", "77.6"]
                    ]
                }
            ],
            test_ids=[visual_test.id, performance_test.id, insulation_test.id],
            prepared_by_user_id=test_engineer.id,
            prepared_date=datetime(2024, 1, 19, 10, 0),
            status=ReportStatus.DRAFT,
            export_formats=["pdf", "docx"],
            template_used="IEC_61215_Type_Approval_v1.0",
            metadata={
                "lab_name": "PV Testing Laboratory",
                "lab_accreditation": "ISO/IEC 17025:2017",
                "accreditation_number": "LAB-2024-001",
                "test_facility": "Testing Lab A"
            }
        )
        session.add(report)

        # 6. Create Audit Logs
        print("\n6. Creating audit trail...")

        # Log sample creation
        audit_sample = Audit.log_action(
            user_id=admin_user.id,
            action=AuditAction.CREATE_SAMPLE,
            entity_type="sample",
            entity_id=sample.id,
            description=f"Created new sample {sample.sample_number}",
            post_snapshot={
                "sample_number": sample.sample_number,
                "customer": sample.customer_name,
                "status": sample.status.value
            },
            severity=AuditSeverity.INFO
        )
        session.add(audit_sample)

        # Log test completion
        audit_test = Audit.log_action(
            user_id=test_engineer.id,
            action=AuditAction.COMPLETE_TEST,
            entity_type="test",
            entity_id=performance_test.id,
            description=f"Completed electrical performance test {performance_test.test_number}",
            post_snapshot={
                "test_number": performance_test.test_number,
                "pass_fail": performance_test.pass_fail.value,
                "status": performance_test.status.value
            },
            severity=AuditSeverity.INFO
        )
        session.add(audit_test)

        # Log report creation
        audit_report = Audit.log_action(
            user_id=test_engineer.id,
            action=AuditAction.CREATE_REPORT,
            entity_type="report",
            entity_id=report.id,
            description=f"Created test report {report.report_number}",
            post_snapshot={
                "report_number": report.report_number,
                "type": report.type.value,
                "status": report.status.value
            },
            severity=AuditSeverity.INFO
        )
        session.add(audit_report)

        # Commit all changes
        print("\n7. Committing to database...")
        session.commit()

        print("\n✓ Sample data created successfully!")
        print(f"  - Equipment: {solar_simulator.name}, {multimeter.name}")
        print(f"  - Users: {admin_user.full_name}, {test_engineer.full_name}")
        print(f"  - Sample: {sample.sample_number}")
        print(f"  - Tests: {len([visual_test, performance_test, insulation_test])} tests")
        print(f"  - Report: {report.report_number}")
        print(f"  - Audit logs: 3 entries")


def query_examples():
    """Demonstrate various database queries."""

    print("\n" + "="*80)
    print("DATABASE QUERY EXAMPLES")
    print("="*80)

    db_config = init_db(database_url="sqlite:///./pv_test_lab_demo.db", echo=False)

    with next(db_config.get_session()) as session:
        # Query 1: Get all active equipment
        print("\n1. Active Equipment:")
        equipment = session.query(Equipment).filter(
            Equipment.status == EquipmentStatus.ACTIVE
        ).all()
        for eq in equipment:
            print(f"  - {eq.name} (S/N: {eq.serial_number})")
            print(f"    Calibration due: {eq.calibration_due_date}")
            print(f"    Days until due: {eq.days_until_calibration_due()}")

        # Query 2: Get all samples in progress
        print("\n2. Samples In Progress:")
        samples = session.query(Sample).filter(
            Sample.status == SampleStatus.IN_PROGRESS
        ).all()
        for sample in samples:
            print(f"  - {sample.sample_number}: {sample.manufacturer} {sample.model_number}")
            print(f"    Customer: {sample.customer_name}")
            print(f"    Days in lab: {sample.days_in_lab()}")

        # Query 3: Get all completed tests
        print("\n3. Completed Tests:")
        tests = session.query(Test).filter(
            Test.status == TestStatus.COMPLETED
        ).all()
        for test in tests:
            print(f"  - {test.test_number}: {test.type.value}")
            print(f"    Result: {test.pass_fail.value}")
            print(f"    Date: {test.test_date}")

        # Query 4: Get report with customer info
        print("\n4. Reports:")
        reports = session.query(Report).all()
        for report in reports:
            print(f"  - {report.get_full_report_number()}")
            print(f"    Type: {report.type.value}")
            print(f"    Status: {report.status.value}")
            print(f"    Tests included: {len(report.test_ids)}")

        # Query 5: Get recent audit logs
        print("\n5. Recent Audit Logs:")
        audits = session.query(Audit).order_by(Audit.timestamp.desc()).limit(5).all()
        for audit in audits:
            print(f"  - {audit.timestamp}: {audit.action.value}")
            print(f"    Description: {audit.description}")


if __name__ == "__main__":
    print("="*80)
    print("PV Test Report Automation - Database Models Demo")
    print("="*80)

    # Create sample data
    create_sample_data()

    # Run query examples
    query_examples()

    print("\n" + "="*80)
    print("Demo completed! Database: pv_test_lab_demo.db")
    print("="*80)
