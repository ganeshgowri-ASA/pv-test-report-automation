"""Example usage of the PV data ingestion module."""

from datetime import datetime
from pathlib import Path

from src.ingestion.csv_parser import CSVParser
from src.ingestion.json_parser import JSONParser
from src.ingestion.timeseries_handler import TimeSeriesHandler
from src.ingestion.equipment_handler import EquipmentDataHandler
from src.ingestion.batch_handler import BatchTestHandler
from src.ingestion.validators import ISO17025Validator
from src.models.ingestion_models import ISO17025Metadata, EquipmentType


def example_csv_parsing():
    """Example: Parse CSV file with auto-detection."""
    print("=" * 60)
    print("CSV PARSING EXAMPLE")
    print("=" * 60)

    parser = CSVParser()

    # Create sample CSV data
    csv_data = """Module_ID,Voltage,Current,Power,Temperature
MODULE-001,30.5,8.2,250.1,25.0
MODULE-002,30.8,8.3,255.6,25.1
MODULE-003,30.2,8.1,244.6,24.9
"""

    result = parser.parse_from_string(csv_data)

    print(f"✓ Parsed {result.row_count} rows, {result.column_count} columns")
    print(f"✓ Delimiter detected: '{result.delimiter_detected}'")
    print(f"✓ Encoding: {result.encoding_detected}")
    print(f"✓ File hash: {result.file_hash[:16]}...")
    print(f"\nData preview:\n{result.dataframe.head()}")
    print()


def example_json_parsing():
    """Example: Parse JSON and JSONL files."""
    print("=" * 60)
    print("JSON PARSING EXAMPLE")
    print("=" * 60)

    parser = JSONParser()

    # JSON array
    json_data = """[
        {"module_id": "M-001", "pmax": 250.5, "voc": 38.2, "isc": 8.5},
        {"module_id": "M-002", "pmax": 252.1, "voc": 38.4, "isc": 8.6},
        {"module_id": "M-003", "pmax": 249.8, "voc": 38.1, "isc": 8.4}
    ]"""

    result = parser.parse_from_string(json_data, to_dataframe=True)

    print(f"✓ Parsed {result.record_count} records")
    print(f"✓ Is JSONL: {result.is_jsonl}")
    print(f"✓ Schema valid: {result.schema_valid}")
    print(f"\nData as DataFrame:\n{result.dataframe}")
    print()


def example_iv_curve_analysis():
    """Example: Parse and analyze I-V curve data."""
    print("=" * 60)
    print("I-V CURVE ANALYSIS EXAMPLE")
    print("=" * 60)

    handler = TimeSeriesHandler()
    parser = CSVParser()

    # Sample I-V curve data
    iv_csv = """Voltage,Current
0.0,8.65
5.0,8.63
10.0,8.61
15.0,8.58
20.0,8.54
25.0,8.48
30.0,8.38
31.0,8.31
32.0,8.20
33.0,7.98
34.0,7.65
35.0,7.10
36.0,6.20
37.0,4.50
37.5,3.00
38.0,1.20
38.5,0.00
"""

    # Parse CSV first
    csv_result = parser.parse_from_string(iv_csv)

    # Create I-V curve from parsed data
    voltage = csv_result.dataframe["Voltage"].tolist()
    current = csv_result.dataframe["Current"].tolist()
    power = [v * i for v, i in zip(voltage, current)]

    from src.models.ingestion_models import IVCurveData

    iv_data = IVCurveData(
        voltage=voltage,
        current=current,
        power=power,
        timestamp=datetime.now(),
        irradiance=1000.0,
        temperature=25.0,
        voc=max(voltage),
        isc=max(current),
        vmp=voltage[power.index(max(power))],
        imp=current[power.index(max(power))],
        pmax=max(power),
        fill_factor=max(power) / (max(voltage) * max(current)),
        module_id="EXAMPLE-MODULE-001",
        test_standard="IEC 60904-1",
        equipment_type=EquipmentType.IV_TRACER,
    )

    print(f"✓ Module: {iv_data.module_id}")
    print(f"✓ Test conditions: {iv_data.irradiance} W/m², {iv_data.temperature} °C")
    print(f"✓ Voc: {iv_data.voc:.2f} V")
    print(f"✓ Isc: {iv_data.isc:.2f} A")
    print(f"✓ Vmp: {iv_data.vmp:.2f} V")
    print(f"✓ Imp: {iv_data.imp:.2f} A")
    print(f"✓ Pmax: {iv_data.pmax:.2f} W")
    print(f"✓ Fill Factor: {iv_data.fill_factor:.4f}")
    print()


def example_batch_testing():
    """Example: Process batch test results."""
    print("=" * 60)
    print("BATCH TEST RESULTS EXAMPLE")
    print("=" * 60)

    handler = BatchTestHandler()

    # Sample batch test data
    batch_csv = """Module_ID,Pmax,Voc,Isc,Fill_Factor,Result
M-001,250.5,38.2,8.5,0.772,PASS
M-002,252.1,38.4,8.6,0.765,PASS
M-003,249.8,38.1,8.4,0.779,PASS
M-004,245.2,37.9,8.3,0.778,PASS
M-005,230.5,37.5,8.1,0.758,FAIL
M-006,251.8,38.3,8.5,0.774,PASS
"""

    parser = CSVParser()
    csv_result = parser.parse_from_string(batch_csv)

    from src.models.ingestion_models import BatchTestResult

    # Count pass/fail
    results = csv_result.dataframe["Result"].str.upper()
    pass_count = (results == "PASS").sum()
    fail_count = (results == "FAIL").sum()

    batch_result = BatchTestResult(
        batch_id="BATCH-2024-001",
        test_date=datetime.now(),
        module_ids=csv_result.dataframe["Module_ID"].tolist(),
        test_results=csv_result.dataframe,
        pass_count=int(pass_count),
        fail_count=int(fail_count),
        total_count=len(csv_result.dataframe),
        test_standard="IEC 61215-2",
        test_parameters={
            "irradiance": 1000.0,
            "temperature": 25.0,
            "test_voltage": 600.0,
        },
        summary_statistics={
            "pmax_mean": csv_result.dataframe["Pmax"].mean(),
            "pmax_std": csv_result.dataframe["Pmax"].std(),
            "voc_mean": csv_result.dataframe["Voc"].mean(),
            "isc_mean": csv_result.dataframe["Isc"].mean(),
        },
    )

    print(f"✓ Batch ID: {batch_result.batch_id}")
    print(f"✓ Test standard: {batch_result.test_standard}")
    print(f"✓ Total modules: {batch_result.total_count}")
    print(f"✓ Passed: {batch_result.pass_count}")
    print(f"✓ Failed: {batch_result.fail_count}")
    print(f"✓ Pass rate: {batch_result.pass_count / batch_result.total_count * 100:.1f}%")
    print(f"\n✓ Average Pmax: {batch_result.summary_statistics['pmax_mean']:.2f} W")
    print(f"✓ Std Dev Pmax: {batch_result.summary_statistics['pmax_std']:.2f} W")
    print()


def example_iso17025_compliance():
    """Example: ISO 17025 compliance validation."""
    print("=" * 60)
    print("ISO 17025 COMPLIANCE EXAMPLE")
    print("=" * 60)

    # Create compliant metadata
    metadata = ISO17025Metadata(
        lab_name="National PV Testing Laboratory",
        lab_accreditation_number="ISO17025-NABL-2024-12345",
        test_method="IEC 61215-1:2021",
        test_date=datetime(2024, 11, 18),
        operator_id="OPERATOR-SMITH-001",
        equipment_id="IV-TRACER-KEYSIGHT-001",
        calibration_due_date=datetime(2025, 6, 1),
        environmental_conditions={
            "temperature": 23.0,  # °C
            "humidity": 45.0,  # %RH
            "pressure": 101325,  # Pa
        },
        uncertainty_budget={
            "calibration_uncertainty": 0.5,  # %
            "repeatability": 0.3,  # %
            "resolution": 0.1,  # %
            "temperature_effect": 0.2,  # %
            "drift": 0.15,  # %
        },
        traceability_chain=[
            "Working Standard WS-IV-001 (Cal Cert: 2024-WS-001, Valid: 2024-06-01)",
            "Reference Standard RS-IV-REF (NIST-Traceable, Cal Cert: NIST-2024-001)",
            "NIST Primary Standard (National Institute of Standards and Technology)",
        ],
    )

    # Validate compliance
    is_compliant, error_dict = ISO17025Validator.validate_full_compliance(
        metadata,
        calibration_date=datetime(2024, 6, 1),
        calibration_due_date=datetime(2025, 6, 1),
    )

    if is_compliant:
        print("✓ FULLY ISO 17025 COMPLIANT")
        print(f"\n✓ Lab: {metadata.lab_name}")
        print(f"✓ Accreditation: {metadata.lab_accreditation_number}")
        print(f"✓ Test method: {metadata.test_method}")
        print(f"✓ Operator: {metadata.operator_id}")
        print(f"✓ Equipment: {metadata.equipment_id}")
        print(f"✓ Calibration valid until: {metadata.calibration_due_date.date()}")
        print(f"\n✓ Environmental conditions:")
        for param, value in metadata.environmental_conditions.items():
            print(f"   - {param}: {value}")
        print(f"\n✓ Traceability chain: {len(metadata.traceability_chain)} levels")
        print(f"✓ Uncertainty components: {len(metadata.uncertainty_budget)}")
    else:
        print("✗ COMPLIANCE ISSUES FOUND:")
        for category, errors in error_dict.items():
            print(f"\n{category.upper()}:")
            for error in errors:
                print(f"  ✗ {error}")
    print()


def example_streaming():
    """Example: Streaming large files."""
    print("=" * 60)
    print("STREAMING EXAMPLE")
    print("=" * 60)

    # Simulate large JSONL file
    large_jsonl = "\n".join(
        [f'{{"id": {i}, "value": {i * 10.5}, "status": "OK"}}' for i in range(1000)]
    )

    parser = JSONParser()

    # Stream in batches
    total_processed = 0
    batch_count = 0

    # Note: In real usage, you'd stream from a file
    # For demo, we'll parse the full data and show the concept
    result = parser.parse_from_string(f"[{large_jsonl.replace(chr(10), ',')}]")

    # Simulate batch processing
    batch_size = 100
    for i in range(0, len(result.data), batch_size):
        batch = result.data[i : i + batch_size]
        batch_count += 1
        total_processed += len(batch)
        print(f"✓ Processed batch {batch_count}: {len(batch)} records")

    print(f"\n✓ Total records processed: {total_processed}")
    print(f"✓ Total batches: {batch_count}")
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("PV DATA INGESTION - EXAMPLE USAGE")
    print("=" * 60 + "\n")

    example_csv_parsing()
    example_json_parsing()
    example_iv_curve_analysis()
    example_batch_testing()
    example_iso17025_compliance()
    example_streaming()

    print("=" * 60)
    print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
