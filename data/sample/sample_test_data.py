"""
Sample test data for demonstrating the LaTeX report generation system.

Creates realistic IEC 61215 test data for a crystalline silicon PV module.
"""

from datetime import datetime, timedelta
from src.models.test_data import (
    TestReport, ReportMetadata, LabInformation, ModuleUnderTest,
    TestSequence, Measurement, ChartData, BrandingConfig,
    TestResult, AccreditationBody
)


def create_sample_report() -> TestReport:
    """
    Create a complete sample test report with realistic data.

    Returns:
        TestReport instance with sample data
    """

    # Report metadata
    metadata = ReportMetadata(
        report_number="TR-2025-PV-001",
        report_date=datetime.now(),
        report_version="1.0",
        is_draft=True,
        prepared_by="Dr. Rajesh Kumar",
        reviewed_by="Dr. Priya Sharma",
        approved_by="Dr. Anil Gupta",
        review_date=datetime.now() + timedelta(days=1),
        approval_date=datetime.now() + timedelta(days=2),
        customer_name="SolarTech Industries Pvt. Ltd.",
        customer_reference="PO-2025-ST-456"
    )

    # Laboratory information
    lab_info = LabInformation(
        lab_name="National Solar Testing Laboratory",
        lab_address="Technology Park, IISER Campus, Pune - 411008, Maharashtra, India",
        accreditation_number="TC-1234",
        accreditation_body=AccreditationBody.NABL,
        iso17025_certified=True,
        contact_email="info@nstl.in",
        contact_phone="+91-20-1234-5678",
        website="www.nstl.in"
    )

    # Module under test
    module_info = ModuleUnderTest(
        manufacturer="SolarTech Industries",
        model="ST-550M-PERC",
        serial_number="ST2025Q1-123456",
        rated_power=550.0,
        rated_voltage=41.2,
        rated_current=13.35,
        module_type="Crystalline Silicon",
        cell_technology="Monocrystalline PERC",
        dimensions="2278 mm × 1134 mm × 35 mm",
        weight=28.5,
        manufacturing_date=datetime(2025, 1, 15)
    )

    # Test sequences
    test_sequences = []

    # MST-01: Visual Inspection
    test_sequences.append(TestSequence(
        sequence_id="MST-01",
        sequence_name="Visual Inspection",
        standard_reference="IEC 61215-2:2021 Clause 10.1",
        test_date=datetime.now() - timedelta(days=30),
        operator="Amit Patel",
        measurements=[
            Measurement(
                parameter="Surface defects",
                value=0,
                unit="count",
                specification="No visible defects",
                result=TestResult.PASS
            ),
            Measurement(
                parameter="Label legibility",
                value=100,
                unit="%",
                specification="All labels legible",
                result=TestResult.PASS
            ),
        ],
        overall_result=TestResult.PASS,
        test_conditions={
            "Temperature": "25°C ± 2°C",
            "Humidity": "45% ± 5%",
        },
        remarks="Module in excellent condition with no visible defects."
    ))

    # MST-02: Maximum Power Determination
    test_sequences.append(TestSequence(
        sequence_id="MST-02",
        sequence_name="Maximum Power Determination",
        standard_reference="IEC 61215-2:2021 Clause 10.2",
        test_date=datetime.now() - timedelta(days=28),
        operator="Sneha Reddy",
        measurements=[
            Measurement(
                parameter="Maximum Power (Pmax)",
                value=552.3,
                unit="W",
                uncertainty=2.5,
                specification="≥ 545 W (-1%)",
                result=TestResult.PASS
            ),
            Measurement(
                parameter="Voltage at Pmax (Vmp)",
                value=41.45,
                unit="V",
                uncertainty=0.15,
                specification="41.2 V ± 3%",
                result=TestResult.PASS
            ),
            Measurement(
                parameter="Current at Pmax (Imp)",
                value=13.32,
                unit="A",
                uncertainty=0.08,
                specification="13.35 A ± 3%",
                result=TestResult.PASS
            ),
            Measurement(
                parameter="Open Circuit Voltage (Voc)",
                value=49.68,
                unit="V",
                uncertainty=0.18,
                specification="> 48 V",
                result=TestResult.PASS
            ),
            Measurement(
                parameter="Short Circuit Current (Isc)",
                value=14.21,
                unit="A",
                uncertainty=0.09,
                specification="> 13 A",
                result=TestResult.PASS
            ),
        ],
        overall_result=TestResult.PASS,
        test_conditions={
            "Irradiance": "1000 W/m²",
            "Spectrum": "AM 1.5G",
            "Cell Temperature": "25°C ± 2°C",
        },
        remarks="Module performance meets rated specifications with excellent efficiency."
    ))

    # MST-03: Insulation Test
    test_sequences.append(TestSequence(
        sequence_id="MST-03",
        sequence_name="Insulation Test",
        standard_reference="IEC 61215-2:2021 Clause 10.3",
        test_date=datetime.now() - timedelta(days=26),
        operator="Vikram Singh",
        measurements=[
            Measurement(
                parameter="Wet Insulation Resistance",
                value=850.5,
                unit="MΩ",
                uncertainty=10.2,
                specification="> 400 MΩ",
                result=TestResult.PASS
            ),
            Measurement(
                parameter="Dry Insulation Resistance",
                value=1250.8,
                unit="MΩ",
                uncertainty=15.5,
                specification="> 400 MΩ",
                result=TestResult.PASS
            ),
        ],
        overall_result=TestResult.PASS,
        test_conditions={
            "Test Voltage": "500 V DC",
            "Duration": "60 seconds",
            "Temperature": "25°C",
        }
    ))

    # MST-04: Temperature Coefficients
    test_sequences.append(TestSequence(
        sequence_id="MST-04",
        sequence_name="Temperature Coefficients",
        standard_reference="IEC 61215-2:2021 Clause 10.4",
        test_date=datetime.now() - timedelta(days=24),
        operator="Kavya Iyer",
        measurements=[
            Measurement(
                parameter="Pmax Temperature Coefficient",
                value=-0.35,
                unit="%/°C",
                uncertainty=0.02,
                specification="-0.40 to -0.30 %/°C",
                result=TestResult.PASS
            ),
            Measurement(
                parameter="Voc Temperature Coefficient",
                value=-0.28,
                unit="%/°C",
                uncertainty=0.015,
                specification="-0.32 to -0.25 %/°C",
                result=TestResult.PASS
            ),
            Measurement(
                parameter="Isc Temperature Coefficient",
                value=0.048,
                unit="%/°C",
                uncertainty=0.003,
                specification="0.04 to 0.06 %/°C",
                result=TestResult.PASS
            ),
        ],
        overall_result=TestResult.PASS,
        test_conditions={
            "Temperature Range": "15°C to 75°C",
            "Irradiance": "1000 W/m²",
            "Spectrum": "AM 1.5G",
        }
    ))

    # MST-05: Hot-Spot Endurance Test
    test_sequences.append(TestSequence(
        sequence_id="MST-05",
        sequence_name="Hot-Spot Endurance Test",
        standard_reference="IEC 61215-2:2021 Clause 10.9",
        test_date=datetime.now() - timedelta(days=20),
        operator="Rohit Desai",
        measurements=[
            Measurement(
                parameter="Maximum Hot-Spot Temperature",
                value=85.3,
                unit="°C",
                uncertainty=1.5,
                specification="< 100°C",
                result=TestResult.PASS
            ),
            Measurement(
                parameter="Post-test Pmax Degradation",
                value=-1.2,
                unit="%",
                specification="< 5%",
                result=TestResult.PASS
            ),
        ],
        overall_result=TestResult.PASS,
        test_conditions={
            "Duration": "1 hour",
            "Shading Configuration": "Single cell",
            "Current": "1.25 × Isc",
        }
    ))

    # Charts for performance visualization
    charts = [
        ChartData(
            chart_type="line",
            title="I-V Characteristic Curve",
            x_label="Voltage (V)",
            y_label="Current (A)",
            x_data=[0, 10, 20, 30, 35, 40, 41.45, 45, 49.68],
            y_data=[14.21, 14.15, 14.08, 13.95, 13.75, 13.48, 13.32, 10.5, 0],
            series_label="Measured I-V Curve"
        ),
        ChartData(
            chart_type="line",
            title="Power vs Voltage Curve",
            x_label="Voltage (V)",
            y_label="Power (W)",
            x_data=[0, 10, 20, 30, 35, 40, 41.45, 45, 49.68],
            y_data=[0, 141.5, 281.6, 418.5, 481.25, 539.2, 552.3, 472.5, 0],
            series_label="P-V Curve"
        ),
        ChartData(
            chart_type="bar",
            title="Test Sequence Results Summary",
            x_label="Test Sequence",
            y_label="Result (1=Pass, 0=Fail)",
            x_data=[1, 2, 3, 4, 5],
            y_data=[1, 1, 1, 1, 1],
            series_label="Pass/Fail Status"
        ),
    ]

    # Create complete report
    report = TestReport(
        metadata=metadata,
        lab_info=lab_info,
        module_info=module_info,
        test_sequences=test_sequences,
        charts=charts,
        summary=(
            "The SolarTech ST-550M-PERC photovoltaic module has successfully completed "
            "the IEC 61215-2:2021 Module Sequence Testing (MST) requirements. "
            "All test sequences from MST-01 to MST-05 were performed and passed. "
            "The module demonstrates excellent electrical performance with maximum power "
            "output of 552.3 W, exceeding the rated specification."
        ),
        conclusions=(
            "Based on the comprehensive testing performed, the module meets all requirements "
            "of IEC 61215-2:2021 for crystalline silicon terrestrial photovoltaic modules. "
            "The module is recommended for type approval and is suitable for deployment "
            "in terrestrial photovoltaic power systems."
        ),
        attachments=[
            "Calibration certificates for test equipment",
            "Raw measurement data files",
            "High-resolution thermal images",
        ]
    )

    return report


def create_sample_branding() -> BrandingConfig:
    """
    Create sample branding configuration.

    Returns:
        BrandingConfig instance
    """
    return BrandingConfig(
        primary_color="#1f77b4",
        secondary_color="#ff7f0e",
        watermark_text="DRAFT - FOR REVIEW ONLY",
        watermark_opacity=0.1,
        font_family="Arial",
        company_tagline="Excellence in Solar Testing"
    )


if __name__ == "__main__":
    # Generate and display sample report
    report = create_sample_report()

    print("Sample Test Report Created")
    print("=" * 50)
    print(f"Report Number: {report.metadata.report_number}")
    print(f"Module: {report.module_info.manufacturer} {report.module_info.model}")
    print(f"Test Sequences: {len(report.test_sequences)}")
    print(f"Overall Result: {report.get_overall_result()}")
    print(f"Statistics: {report.get_test_statistics()}")
