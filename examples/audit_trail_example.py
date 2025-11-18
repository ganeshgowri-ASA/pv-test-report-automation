"""
Complete Example: Audit Trail & Data Lineage System

This example demonstrates a complete workflow for a PV module test,
including audit logging and data lineage tracking from raw measurements
to final test report.
"""

import os
from datetime import datetime, timezone
from uuid import uuid4

from src.audit import (
    AuditTrailLogger,
    AuditEvent,
    AuditEventType,
    DataLineageTracker,
    DataNode,
    DataNodeType,
    RelationshipType,
    ComplianceReporter,
    IntegrityChecker,
)


def main():
    """Run complete audit trail example."""

    # Configuration
    db_url = os.getenv("DATABASE_URL", "sqlite:///example_audit.db")

    print("=" * 80)
    print("PV Test Report Automation - Audit Trail Example")
    print("ISO 17025 & 21 CFR Part 11 Compliant")
    print("=" * 80)
    print()

    # ========================================
    # 1. Initialize Components
    # ========================================
    print("1. Initializing audit trail system...")
    audit_logger = AuditTrailLogger(db_url=db_url)
    lineage_tracker = DataLineageTracker(db_url=db_url)
    compliance_reporter = ComplianceReporter(db_url=db_url)
    integrity_checker = IntegrityChecker(db_url=db_url)
    print("   ✓ All components initialized")
    print()

    # ========================================
    # 2. User Authentication
    # ========================================
    print("2. Logging user authentication...")
    audit_logger.log_auth(
        event_type=AuditEventType.LOGIN,
        user_id="tech001",
        user_name="Alice Johnson",
        success=True,
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        session_id=str(uuid4())
    )
    print("   ✓ User login recorded")
    print()

    # ========================================
    # 3. Create Test Report
    # ========================================
    print("3. Creating new test report...")
    report_id = "RPT-2024-001"

    audit_logger.log_crud(
        operation="CREATE",
        entity_type="Report",
        entity_id=report_id,
        user_id="tech001",
        user_name="Alice Johnson",
        new_values={
            "title": "PV Module IEC 61215 Performance Test",
            "module_id": "MOD-XYZ-12345",
            "standard": "IEC 61215-1:2021",
            "status": "in_progress",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        reason="Customer order #12345 - Performance verification"
    )
    print(f"   ✓ Report {report_id} created")
    print()

    # ========================================
    # 4. Import Raw Equipment Data
    # ========================================
    print("4. Importing raw measurement data...")

    # Simulate raw IV curve data from Keysight B1500A
    raw_iv_data = {
        "voltage_V": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.54, 0.58, 0.62, 0.65],
        "current_A": [9.2, 9.18, 9.15, 9.10, 9.00, 8.80, 8.50, 7.20, 3.50, 0.0],
        "temperature_C": 25.0,
        "irradiance_W_m2": 1000.0,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    raw_node = DataNode(
        node_type=DataNodeType.RAW_EQUIPMENT_OUTPUT,
        name="IV Curve Raw Measurement",
        description="Raw I-V curve data from Keysight B1500A",
        created_by="tech001",
        source_system="Keysight B1500A",
        source_file="/measurements/2024/01/15/iv_curve_001.csv",
        data_value=raw_iv_data,
        entity_type="Report",
        entity_id=report_id,
        quality_score=95,
        validation_status="VALID"
    )
    raw_node_id = lineage_tracker.create_node(raw_node)

    audit_logger.log(AuditEvent(
        event_type=AuditEventType.DATA_IMPORT,
        entity_type="Measurement",
        entity_id=str(raw_node_id),
        user_id="tech001",
        user_name="Alice Johnson",
        action="Imported IV curve data from Keysight B1500A",
        description=f"Raw measurement data for report {report_id}",
        metadata={
            "source_system": "Keysight B1500A",
            "measurement_type": "IV_CURVE",
            "data_points": len(raw_iv_data["voltage_V"])
        }
    ))
    print("   ✓ Raw measurement data imported")
    print(f"   ✓ Data lineage node created: {raw_node_id}")
    print()

    # ========================================
    # 5. Parse and Validate Data
    # ========================================
    print("5. Parsing and validating measurement data...")

    # Extract key parameters from IV curve
    parsed_data = {
        "voc": 0.65,      # Open circuit voltage
        "isc": 9.2,       # Short circuit current
        "vmp": 0.54,      # Voltage at max power
        "imp": 8.50,      # Current at max power
        "pmax": 4.59,     # Maximum power (vmp * imp)
        "fill_factor": 0.767,  # (vmp * imp) / (voc * isc)
        "temperature_C": 25.0,
        "irradiance_W_m2": 1000.0
    }

    parsed_node = DataNode(
        node_type=DataNodeType.PARSED_DATA,
        name="IV Curve Parameters",
        description="Extracted parameters from IV curve",
        created_by="tech001",
        data_value=parsed_data,
        entity_type="Report",
        entity_id=report_id,
        quality_score=98,
        validation_status="VALID"
    )
    parsed_node_id = lineage_tracker.create_node(parsed_node)

    # Create lineage relationship
    lineage_tracker.create_relationship(
        parent_id=raw_node_id,
        child_id=parsed_node_id,
        relationship_type=RelationshipType.DERIVED_FROM,
        created_by="tech001",
        transformation_function="extract_iv_parameters",
        transformation_params={
            "method": "polynomial_fit",
            "degree": 5,
            "smoothing": "savitzky_golay"
        },
        description="Extracted IV curve parameters using polynomial fitting"
    )

    audit_logger.log(AuditEvent(
        event_type=AuditEventType.DATA_TRANSFORM,
        entity_type="Measurement",
        entity_id=str(parsed_node_id),
        user_id="tech001",
        user_name="Alice Johnson",
        action="Parsed IV curve parameters",
        description="Extracted Voc, Isc, Vmp, Imp, Pmax, FF from raw data",
        metadata={
            "transformation": "extract_iv_parameters",
            "parent_node": str(raw_node_id)
        }
    ))
    print("   ✓ IV parameters extracted")
    print(f"   ✓ Lineage relationship created")
    print()

    # ========================================
    # 6. Calculate Performance Metrics
    # ========================================
    print("6. Calculating module efficiency...")

    # Calculate efficiency
    module_area_cm2 = 15625  # 125cm x 125cm
    irradiance_W_m2 = 1000
    efficiency_pct = (parsed_data["pmax"] / (irradiance_W_m2 * (module_area_cm2 / 10000))) * 100

    efficiency_data = {
        "efficiency_percent": round(efficiency_pct, 2),
        "pmax_W": parsed_data["pmax"],
        "area_cm2": module_area_cm2,
        "area_m2": module_area_cm2 / 10000,
        "irradiance_W_m2": irradiance_W_m2,
        "calculation_method": "pmax / (irradiance * area)"
    }

    efficiency_node = DataNode(
        node_type=DataNodeType.CALCULATED_VALUE,
        name="Module Efficiency",
        description="Calculated module conversion efficiency",
        created_by="tech001",
        data_value=efficiency_data,
        entity_type="Report",
        entity_id=report_id,
        quality_score=100,
        validation_status="VALID"
    )
    efficiency_node_id = lineage_tracker.create_node(efficiency_node)

    lineage_tracker.create_relationship(
        parent_id=parsed_node_id,
        child_id=efficiency_node_id,
        relationship_type=RelationshipType.CALCULATED_FROM,
        created_by="tech001",
        transformation_function="calculate_efficiency",
        transformation_params={
            "area_cm2": module_area_cm2,
            "standard": "IEC 61215"
        },
        description="Calculated efficiency per IEC 61215 standard"
    )

    audit_logger.log(AuditEvent(
        event_type=AuditEventType.DATA_TRANSFORM,
        entity_type="Calculation",
        entity_id=str(efficiency_node_id),
        user_id="tech001",
        user_name="Alice Johnson",
        action="Calculated module efficiency",
        description=f"Efficiency: {efficiency_pct:.2f}%",
        metadata={
            "calculation": "calculate_efficiency",
            "efficiency": efficiency_pct,
            "standard": "IEC 61215"
        }
    ))
    print(f"   ✓ Efficiency calculated: {efficiency_pct:.2f}%")
    print()

    # ========================================
    # 7. Create Report Section
    # ========================================
    print("7. Adding results to report...")

    report_section_data = {
        "section": "IV Curve Performance",
        "measurements": parsed_data,
        "efficiency": efficiency_data,
        "pass_fail": "PASS" if efficiency_pct >= 18.0 else "FAIL",
        "standard_requirement": "≥18.0%",
        "actual_value": f"{efficiency_pct:.2f}%"
    }

    report_section_node = DataNode(
        node_type=DataNodeType.REPORT_SECTION,
        name="Performance Test Results",
        description="IV curve performance test results section",
        created_by="tech001",
        data_value=report_section_data,
        entity_type="Report",
        entity_id=report_id
    )
    report_section_id = lineage_tracker.create_node(report_section_node)

    # Link to efficiency calculation
    lineage_tracker.create_relationship(
        parent_id=efficiency_node_id,
        child_id=report_section_id,
        relationship_type=RelationshipType.COMPOSED_OF,
        created_by="tech001",
        description="Report section includes efficiency calculation"
    )

    audit_logger.log_crud(
        operation="UPDATE",
        entity_type="Report",
        entity_id=report_id,
        user_id="tech001",
        user_name="Alice Johnson",
        old_values={"status": "in_progress", "sections": []},
        new_values={"status": "in_progress", "sections": ["Performance Test Results"]},
        reason="Added IV curve performance test results"
    )
    print("   ✓ Report section added")
    print()

    # ========================================
    # 8. Trace Complete Lineage
    # ========================================
    print("8. Tracing data lineage...")

    # Trace backward from report section to source
    lineage = lineage_tracker.trace_lineage(report_section_id, direction="backward")
    print(f"   ✓ Complete lineage traced:")
    print(f"     - Total nodes: {len(lineage['nodes'])}")
    print(f"     - Relationships: {len(lineage['relationships'])}")

    # Get source nodes
    sources = lineage_tracker.get_source_nodes(report_section_id)
    print(f"   ✓ Original source:")
    for source in sources:
        print(f"     - {source.name} ({source.source_system})")
    print()

    # ========================================
    # 9. Report Review and Approval
    # ========================================
    print("9. Report review process...")

    # Technical review
    audit_logger.log(AuditEvent(
        event_type=AuditEventType.REPORT_UPDATE,
        entity_type="Report",
        entity_id=report_id,
        user_id="reviewer001",
        user_name="Bob Smith",
        action="Reviewed test report",
        description="Technical review completed - all calculations verified",
        reason="Quality assurance check",
        metadata={"review_type": "technical", "reviewer_role": "Senior Engineer"}
    ))

    # Approval
    audit_logger.log(AuditEvent(
        event_type=AuditEventType.REPORT_APPROVE,
        entity_type="Report",
        entity_id=report_id,
        user_id="manager001",
        user_name="Carol Davis",
        action="Approved test report",
        reason="All requirements met per IEC 61215",
        metadata={"approval_level": "manager"}
    ))

    # Digital signature
    audit_logger.log(AuditEvent(
        event_type=AuditEventType.SIGNATURE_APPLY,
        entity_type="Report",
        entity_id=report_id,
        user_id="manager001",
        user_name="Carol Davis",
        action="Applied digital signature",
        description="Report signed with digital certificate",
        metadata={
            "signature_type": "digital_certificate",
            "certificate_serial": "ABC123456"
        }
    ))

    print("   ✓ Technical review completed")
    print("   ✓ Report approved")
    print("   ✓ Digital signature applied")
    print()

    # ========================================
    # 10. Verify Integrity
    # ========================================
    print("10. Verifying audit trail integrity...")

    # Verify hash chain
    hash_result = integrity_checker.verify_hash_chain()
    print(f"   ✓ Hash chain: {'PASS' if hash_result.passed else 'FAIL'}")
    print(f"     - Records checked: {hash_result.total_records_checked}")
    print(f"     - Issues found: {hash_result.issues_found}")

    # Verify sequence
    seq_result = integrity_checker.verify_sequence_integrity()
    print(f"   ✓ Sequence: {'PASS' if seq_result.passed else 'FAIL'}")

    # Get integrity score
    score = integrity_checker.get_integrity_score()
    print(f"   ✓ Integrity score: {score}/100")
    print()

    # ========================================
    # 11. Generate Compliance Report
    # ========================================
    print("11. Generating compliance report...")

    from datetime import timedelta
    report = compliance_reporter.generate_audit_report(
        period_start=datetime.now(timezone.utc) - timedelta(days=1),
        period_end=datetime.now(timezone.utc),
        title="PV Module Test - Audit Report",
        generated_by="system",
        description="Audit trail for report " + report_id
    )

    print(f"   ✓ Audit report generated")
    print(f"     - Total events: {report.statistics.total_events}")
    print(f"     - Unique users: {report.statistics.unique_users}")
    print(f"     - Findings: {len(report.findings)}")
    print(f"     - Recommendations: {len(report.recommendations)}")
    print()

    # Get statistics
    stats = compliance_reporter.get_statistics()
    print("   📊 Audit Statistics:")
    print(f"     - Total events: {stats.total_events}")
    print(f"     - Security events: {stats.security_events}")
    print(f"     - Failed logins: {stats.failed_logins}")
    print()

    # ========================================
    # 12. Export Audit Trail
    # ========================================
    print("12. Exporting audit trail...")

    # Get all events
    events = audit_logger.get_events(entity_id=report_id, limit=100)

    # Export to CSV
    csv_data = compliance_reporter.export_csv(events)
    with open("audit_trail_export.csv", "w") as f:
        f.write(csv_data)
    print(f"   ✓ CSV export: audit_trail_export.csv ({len(events)} events)")

    # Export to JSON
    json_data = compliance_reporter.export_json(events)
    with open("audit_trail_export.json", "w") as f:
        f.write(json_data)
    print(f"   ✓ JSON export: audit_trail_export.json")
    print()

    # ========================================
    # Summary
    # ========================================
    print("=" * 80)
    print("✅ AUDIT TRAIL EXAMPLE COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  • Report ID: {report_id}")
    print(f"  • Module Efficiency: {efficiency_pct:.2f}%")
    print(f"  • Audit Events: {stats.total_events}")
    print(f"  • Lineage Nodes: 4 (Raw → Parsed → Calculated → Report)")
    print(f"  • Integrity Score: {score}/100")
    print()
    print("This demonstrates:")
    print("  ✓ Complete audit trail from measurement to report")
    print("  ✓ Full data lineage tracking")
    print("  ✓ User authentication and authorization logging")
    print("  ✓ Review and approval workflow")
    print("  ✓ Integrity verification")
    print("  ✓ Compliance reporting")
    print("  ✓ ISO 17025 & 21 CFR Part 11 compliance")
    print()


if __name__ == "__main__":
    main()
