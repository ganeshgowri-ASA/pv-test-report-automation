#!/usr/bin/env python3
"""
Example usage of the Calibration Certificate Management System.

This script demonstrates all major features of the calibration management system.
"""

from datetime import date, timedelta
from pathlib import Path

from equipment.calibration import (
    CalibrationManager,
    CalibrationCertificate,
    AccreditationBody,
    AlertSeverity,
)
from equipment.calibration.models import (
    UncertaintyBudget,
    UncertaintyType,
    TraceabilityChain,
    CalibrationPoint,
)


def main():
    """Run calibration management examples."""
    print("=" * 80)
    print("Calibration Certificate Management System - Example Usage")
    print("=" * 80)
    print()

    # Initialize the manager
    print("1. Initializing Calibration Manager...")
    cm = CalibrationManager(db_path="example_calibration.db")
    print("   ✓ Manager initialized")
    print()

    # Example 1: Add certificate manually
    print("2. Adding Calibration Certificate (Manual Entry)...")
    cert1 = cm.add_certificate(
        equipment_id=101,
        cert_number="CAL-2025-001",
        calibration_date=date.today() - timedelta(days=30),
        due_date=date.today() + timedelta(days=335),
        calibration_lab="National Calibration Laboratory",
        accreditation_body=AccreditationBody.NABL,
        uncertainty=0.05,
        traceability_chain="NIST through NPL India",
        technician="John Smith",
        reviewer="Dr. Jane Doe",
        notes="Annual calibration completed successfully"
    )
    print(f"   ✓ Certificate added: {cert1.cert_number}")
    print(f"   - Equipment ID: {cert1.equipment_id}")
    print(f"   - Due Date: {cert1.due_date}")
    print(f"   - Days until due: {cert1.days_until_due()}")
    print()

    # Example 2: Add certificate with uncertainty budget
    print("3. Adding Certificate with Detailed Uncertainty Budget...")

    uncertainty_budget = UncertaintyBudget(
        value=0.08,
        unit="V",
        uncertainty_type=UncertaintyType.EXPANDED,
        coverage_factor=2.0,
        confidence_level=0.95,
        components={
            "type_a_repeatability": 0.03,
            "type_b_resolution": 0.02,
            "type_b_stability": 0.025,
            "type_b_reference_standard": 0.04,
        }
    )

    traceability_chain = TraceabilityChain(
        primary_standard="NIST",
        intermediate_standards=["NPL India", "NABL Accredited Lab"],
        reference_certificate="NIST-REF-2024-567",
        uncertainty_propagation=[0.01, 0.03, 0.08]
    )

    cert2 = cm.add_certificate(
        equipment_id=102,
        cert_number="CAL-2025-002",
        calibration_date=date.today() - timedelta(days=15),
        due_date=date.today() + timedelta(days=350),
        calibration_lab="Precision Calibration Services",
        accreditation_body=AccreditationBody.ILAC,
        uncertainty=0.08,
        traceability_chain="NIST → NPL India → NABL Lab",
        uncertainty_budget=uncertainty_budget,
        traceability_chain_obj=traceability_chain,
        environmental_conditions={
            "temperature": 23.5,
            "temperature_unit": "°C",
            "humidity": 45.2,
            "humidity_unit": "%"
        }
    )
    print(f"   ✓ Certificate added: {cert2.cert_number}")
    print(f"   - Uncertainty: {cert2.uncertainty} {uncertainty_budget.unit}")
    print(f"   - Coverage factor: k={uncertainty_budget.coverage_factor}")
    print(f"   - Confidence level: {uncertainty_budget.confidence_level*100}%")
    print()

    # Example 3: Add certificate due soon (for alert testing)
    print("4. Adding Certificate Due Soon (for Alert Testing)...")
    cert3 = cm.add_certificate(
        equipment_id=103,
        cert_number="CAL-2024-999",
        calibration_date=date.today() - timedelta(days=350),
        due_date=date.today() + timedelta(days=10),
        calibration_lab="Quick Cal Lab",
        accreditation_body=AccreditationBody.A2LA,
        uncertainty=0.1,
        traceability_chain="NIST"
    )
    print(f"   ✓ Certificate added: {cert3.cert_number}")
    print(f"   - Status: {cert3.status.value}")
    print(f"   - Days until due: {cert3.days_until_due()}")
    print()

    # Example 4: Add expired certificate
    print("5. Adding Expired Certificate (for Testing)...")
    cert4 = cm.add_certificate(
        equipment_id=104,
        cert_number="CAL-2023-100",
        calibration_date=date.today() - timedelta(days=400),
        due_date=date.today() - timedelta(days=15),
        calibration_lab="Expired Cal Services",
        accreditation_body=AccreditationBody.NABL,
        uncertainty=0.12,
        traceability_chain="NIST"
    )
    print(f"   ✓ Certificate added: {cert4.cert_number}")
    print(f"   - Status: {cert4.status.value}")
    print(f"   - Days overdue: {abs(cert4.days_until_due())}")
    print()

    # Example 5: Get certificates due soon
    print("6. Checking Certificates Due Soon (30 days)...")
    due_soon = cm.get_due_soon(days=30)
    print(f"   ✓ Found {len(due_soon)} certificate(s) due within 30 days:")
    for cert in due_soon:
        print(f"   - {cert.cert_number}: Due {cert.due_date} ({cert.days_until_due()} days)")
    print()

    # Example 6: Get expired certificates
    print("7. Checking Expired Certificates...")
    expired = cm.get_expired_certificates()
    print(f"   ✓ Found {len(expired)} expired certificate(s):")
    for cert in expired:
        print(f"   - {cert.cert_number}: Expired {cert.due_date} ({abs(cert.days_until_due())} days ago)")
    print()

    # Example 7: Auto-flag expired certificates
    print("8. Auto-Flagging Expired Certificates...")
    flagged = cm.flag_expired_certificates()
    print(f"   ✓ Flagged {len(flagged)} expired certificate(s)")
    print()

    # Example 8: Get alerts
    print("9. Checking Calibration Alerts...")
    cm.refresh_alerts()

    critical = cm.get_critical_alerts()
    print(f"   ✓ Critical/Urgent alerts: {len(critical)}")
    for alert in critical[:3]:  # Show first 3
        print(f"   - [{alert.severity.value.upper()}] {alert.message}")

    all_alerts = cm.get_alerts(unacknowledged_only=True)
    print(f"   ✓ Total unacknowledged alerts: {len(all_alerts)}")
    print()

    # Example 9: Get alert summary
    print("10. Alert Summary...")
    summary = cm.alert_manager.get_alert_summary()
    print(f"   ✓ Total alerts: {summary['total']}")
    print(f"   - Unacknowledged: {summary['unacknowledged']}")
    print(f"   - Critical: {summary['critical']}")
    print(f"   - Urgent: {summary['urgent']}")
    print(f"   - Warning: {summary['warning']}")
    print(f"   - Info: {summary['info']}")
    print()

    # Example 10: Validate traceability
    print("11. Validating Traceability Chain...")
    traceability_result = cm.validate_traceability(cert2.cert_id)
    print(f"   ✓ Traceability validation:")
    print(f"   - Valid: {traceability_result['valid']}")
    print(f"   - Primary standard: {traceability_result['primary_standard']}")
    print(f"   - Chain length: {traceability_result['chain_length']}")
    print()

    # Example 11: Get calibration history
    print("12. Retrieving Calibration History...")
    history = cm.get_calibration_history(equipment_id=101)
    print(f"   ✓ Found {len(history)} history record(s) for equipment 101:")
    for entry in history[:3]:  # Show first 3
        print(f"   - {entry['action_date'][:10]}: {entry['action']}")
    print()

    # Example 12: Get statistics
    print("13. Calibration Statistics...")
    stats = cm.get_statistics()
    print(f"   ✓ Total certificates: {stats['total_certificates']}")
    print(f"   - Valid: {stats['valid']}")
    print(f"   - Expired: {stats['expired']}")
    print(f"   - Due in 30 days: {stats['due_soon_30']}")
    print(f"   - Due in 15 days: {stats['due_soon_15']}")
    print(f"   - Due in 7 days: {stats['due_soon_7']}")
    print(f"   - Unique equipment: {stats['unique_equipment']}")
    print(f"   - Avg uncertainty: {stats['avg_uncertainty']:.4f}")
    print()

    # Example 13: Generate compliance report
    print("14. Generating ISO 17025 Compliance Report...")
    report = cm.generate_compliance_report()
    print("   ✓ Report generated")
    print()
    print(report)
    print()

    # Example 14: Export reports
    print("15. Exporting Reports to Files...")
    cm.export_compliance_report("compliance_report.txt")
    print("   ✓ Compliance report exported to: compliance_report.txt")

    cm.export_alerts_report("alerts_report.txt")
    print("   ✓ Alerts report exported to: alerts_report.txt")
    print()

    # Example 15: Get current certificate for equipment
    print("16. Getting Current Certificate for Equipment...")
    current = cm.get_current_certificate(equipment_id=101)
    if current:
        print(f"   ✓ Current certificate: {current.cert_number}")
        print(f"   - Calibration date: {current.calibration_date}")
        print(f"   - Valid until: {current.due_date}")
    print()

    print("=" * 80)
    print("Example completed successfully!")
    print("=" * 80)
    print()
    print("Database file: example_calibration.db")
    print("Reports generated:")
    print("  - compliance_report.txt")
    print("  - alerts_report.txt")
    print()


if __name__ == "__main__":
    main()
