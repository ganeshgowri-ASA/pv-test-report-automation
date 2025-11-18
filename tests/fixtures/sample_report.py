"""
Sample test report fixtures for testing.
"""

from datetime import datetime
from src.models.test_report import (
    TestReport,
    TestReportHeader,
    SpecimenInfo,
    TestResult,
    StandardType,
    ModuleType,
    PassFailStatus,
    TestStatus,
)


def create_sample_report() -> TestReport:
    """Create a sample test report for testing."""

    header = TestReportHeader(
        report_id="RPT-2024-001",
        report_number="PV-TEST-2024-001",
        revision=1,
        date_issued=datetime.utcnow(),
        test_standard=StandardType.IEC_61215,
        lab_name="Solar Testing Laboratory",
        lab_accreditation="NABL-TC-1234",
        client_name="Solar Modules Inc.",
        client_reference="CLIENT-REF-001",
        test_duration="30 days",
        test_start_date=datetime(2024, 1, 1),
        test_end_date=datetime(2024, 1, 30),
        performed_by="John Doe",
        reviewed_by="Jane Smith",
        approved_by="Dr. Robert Johnson",
        certification_level="IEC 61215 Full Qualification",
    )

    specimen = SpecimenInfo(
        specimen_id="SPEC-001",
        manufacturer="Solar Tech Ltd",
        model="ST-300W-Mono",
        serial_number="SN123456789",
        module_type=ModuleType.CRYSTALLINE_SILICON,
        rated_power=300.0,
        dimensions="1650x992x40mm",
        weight=18.5,
        cell_technology="Monocrystalline PERC",
        manufacturing_date=datetime(2023, 12, 1),
        received_date=datetime(2023, 12, 15),
        condition_on_receipt="Good, no visible damage",
    )

    test_results = [
        TestResult(
            test_id="TC-001",
            test_name="Visual Inspection",
            parameter="Module Appearance",
            specification="No defects per IEC 61215",
            measured_value_str="Pass",
            unit="categorical",
            status=PassFailStatus.PASS,
            test_date=datetime(2024, 1, 2),
            operator_id="OP-001",
            comments="No visible defects observed",
        ),
        TestResult(
            test_id="TC-002",
            test_name="Electrical Performance",
            parameter="Maximum Power",
            specification="≥ 285W (95% of rated)",
            measured_value=295.5,
            unit="W",
            status=PassFailStatus.PASS,
            tolerance="±3%",
            equipment_used="Solar Simulator SS-1000",
            test_date=datetime(2024, 1, 5),
            operator_id="OP-002",
        ),
        TestResult(
            test_id="TC-003",
            test_name="Electrical Performance",
            parameter="Open Circuit Voltage",
            specification="38-42V",
            measured_value=40.2,
            unit="V",
            status=PassFailStatus.PASS,
            equipment_used="Multimeter DMM-6500",
            test_date=datetime(2024, 1, 5),
            operator_id="OP-002",
        ),
        TestResult(
            test_id="TC-004",
            test_name="Insulation Resistance",
            parameter="Insulation Resistance",
            specification="≥ 400 MΩ·m²",
            measured_value=850.0,
            unit="MΩ·m²",
            status=PassFailStatus.PASS,
            equipment_used="Megohmmeter",
            test_date=datetime(2024, 1, 6),
            operator_id="OP-001",
        ),
        TestResult(
            test_id="TC-005",
            test_name="Thermal Cycling",
            parameter="Power Degradation",
            specification="≤ 5%",
            measured_value=2.1,
            unit="%",
            status=PassFailStatus.PASS,
            equipment_used="Thermal Chamber TC-200",
            test_date=datetime(2024, 1, 20),
            operator_id="OP-003",
            comments="200 cycles completed",
        ),
    ]

    return TestReport(
        header=header,
        specimen=specimen,
        test_results=test_results,
        status=TestStatus.COMPLETED,
        executive_summary="Sample executive summary",
        conclusions="All tests passed successfully.",
        recommendations="Module meets IEC 61215 requirements.",
    )


def create_failed_report() -> TestReport:
    """Create a sample report with failures."""
    report = create_sample_report()

    # Add a failed test
    failed_test = TestResult(
        test_id="TC-006",
        test_name="Damp Heat",
        parameter="Power Degradation",
        specification="≤ 5%",
        measured_value=7.5,
        unit="%",
        status=PassFailStatus.FAIL,
        equipment_used="Climate Chamber CH-1000",
        test_date=datetime(2024, 1, 25),
        operator_id="OP-002",
        comments="Exceeded maximum allowed degradation",
    )

    report.test_results.append(failed_test)
    report.status = TestStatus.FAILED

    return report
