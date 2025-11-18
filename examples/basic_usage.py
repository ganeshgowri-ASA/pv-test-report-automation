"""Basic usage examples for GPT integration."""

import os
from dotenv import load_dotenv

from src.gpt_integration import GPTIntegration
from src.gpt_integration.analyzers import TestResultAnalyzer, ComplianceChecker, AnomalyDetector
from src.gpt_integration.generators import ReportGenerator, RecommendationEngine
from src.models.gpt_models import ComplianceStandard, Language

# Load environment variables
load_dotenv()


def example_simple_query():
    """Example: Simple query to GPT."""
    print("\n=== Simple Query Example ===")

    gpt = GPTIntegration(api_key=os.getenv("OPENAI_API_KEY"))

    response = gpt.query(
        "What are the key parameters to measure in PV module I-V curve testing?"
    )

    print(f"Response: {response}")

    # Get statistics
    stats = gpt.get_stats()
    print(f"\nStatistics: {stats}")


def example_iv_curve_analysis():
    """Example: Analyze I-V curve data."""
    print("\n=== I-V Curve Analysis Example ===")

    gpt = GPTIntegration(api_key=os.getenv("OPENAI_API_KEY"))
    analyzer = TestResultAnalyzer(gpt)

    # Sample I-V curve data
    iv_data = {
        "module_id": "PV-2024-001",
        "test_date": "2024-01-15",
        "irradiance": 1000,  # W/m²
        "temperature": 25,  # °C
        "voltage_V": [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 48],
        "current_A": [9.2, 9.1, 9.0, 8.8, 8.5, 8.0, 7.0, 5.5, 3.0, 0.5, 0],
        "power_W": [0, 45.5, 90, 132, 170, 200, 210, 192.5, 120, 22.5, 0]
    }

    result = analyzer.analyze_iv_curve(iv_data)

    print(f"Summary: {result.summary}")
    print(f"\nKey Findings:")
    for finding in result.key_findings:
        print(f"  - {finding}")

    print(f"\nData Quality Score: {result.data_quality_score:.2f}")

    if result.anomalies:
        print(f"\nAnomalies Detected:")
        for anomaly in result.anomalies:
            print(f"  - [{anomaly.severity.upper()}] {anomaly.description}")

    print(f"\nRecommendations:")
    for rec in result.recommendations:
        print(f"  - {rec}")


def example_compliance_check():
    """Example: Check compliance with IEC 61215."""
    print("\n=== Compliance Check Example ===")

    gpt = GPTIntegration(api_key=os.getenv("OPENAI_API_KEY"))
    checker = ComplianceChecker(gpt)

    test_report = """
    PV Module Test Report

    Module: 300W Monocrystalline Silicon

    Tests Completed:
    - Thermal Cycling: 200 cycles (-40°C to +85°C) - PASSED
    - Humidity Freeze: 10 cycles - PASSED
    - Damp Heat: 1000 hours at 85°C/85%RH - PASSED
    - UV Preconditioning: 15 kWh/m² - PASSED
    - Hot-spot Endurance: PASSED
    - Mechanical Load: 2400 Pa - PASSED

    Power degradation: 2.5% (within 5% limit)
    """

    test_data = {
        "thermal_cycling": {"cycles": 200, "result": "PASS"},
        "humidity_freeze": {"cycles": 10, "result": "PASS"},
        "damp_heat": {"hours": 1000, "result": "PASS"},
        "uv_preconditioning": {"kwh_per_m2": 15, "result": "PASS"},
        "hot_spot": {"result": "PASS"},
        "mechanical_load": {"pressure_pa": 2400, "result": "PASS"},
        "power_degradation_pct": 2.5
    }

    result = checker.check_compliance(
        report=test_report,
        test_data=test_data,
        standard=ComplianceStandard.IEC_61215
    )

    print(f"Standard: {result.standard.value}")
    print(f"Status: {result.status.value.upper()}")
    print(f"Confidence: {result.confidence_score:.2%}")

    print(f"\nRequirements Met ({len(result.requirements_met)}):")
    for req in result.requirements_met:
        print(f"  ✓ {req}")

    if result.requirements_failed:
        print(f"\nRequirements Failed ({len(result.requirements_failed)}):")
        for req in result.requirements_failed:
            print(f"  ✗ {req}")

    print(f"\nRecommendations:")
    for rec in result.recommendations:
        print(f"  - {rec}")


def example_anomaly_detection():
    """Example: Detect anomalies in test data."""
    print("\n=== Anomaly Detection Example ===")

    gpt = GPTIntegration(api_key=os.getenv("OPENAI_API_KEY"))
    detector = AnomalyDetector(gpt)

    # Test data with some anomalies
    test_data = {
        "module_id": "PV-2024-002",
        "measurements": {
            "voc_V": [48.2, 48.1, 48.3, 35.0, 48.2],  # One outlier
            "isc_A": [9.1, 9.2, 9.1, 9.2, 9.1],
            "pmax_W": [310, 312, 311, None, 310],  # Missing data
            "fill_factor": [0.78, 0.79, 0.78, 0.55, 0.79],  # One outlier
        },
        "temperature_C": [25, 25, 25, 25, 25]
    }

    anomalies = detector.detect_anomalies(test_data)

    print(f"Detected {len(anomalies)} anomalies:")
    for i, anomaly in enumerate(anomalies, 1):
        print(f"\n{i}. {anomaly.type.value.upper()} - {anomaly.severity.upper()}")
        print(f"   Location: {anomaly.location}")
        print(f"   Description: {anomaly.description}")
        print(f"   Confidence: {anomaly.confidence:.2%}")
        if anomaly.suggested_action:
            print(f"   Suggested Action: {anomaly.suggested_action}")


def example_report_generation():
    """Example: Generate executive summary report."""
    print("\n=== Report Generation Example ===")

    gpt = GPTIntegration(api_key=os.getenv("OPENAI_API_KEY"))
    generator = ReportGenerator(gpt)

    test_data = {
        "module_info": {
            "model": "SolarMax 300W",
            "serial": "SM300-2024-001",
            "technology": "Monocrystalline Silicon"
        },
        "test_results": {
            "power_output_W": 305,
            "efficiency_pct": 19.2,
            "voc_V": 48.5,
            "isc_A": 9.3,
            "fill_factor": 0.78,
            "temperature_coefficient_pct_per_C": -0.35
        },
        "quality_tests": {
            "visual_inspection": "PASS",
            "electrical_tests": "PASS",
            "mechanical_tests": "PASS",
            "environmental_tests": "PASS"
        }
    }

    # Generate in English
    report_en = generator.generate_executive_summary(
        test_data=test_data,
        language=Language.ENGLISH
    )

    print("=== Executive Summary (English) ===")
    print(report_en.executive_summary)

    print("\n=== Key Metrics ===")
    for metric, value in report_en.key_metrics.items():
        print(f"  {metric}: {value}")

    # Generate in Spanish
    report_es = generator.generate_executive_summary(
        test_data=test_data,
        language=Language.SPANISH
    )

    print("\n=== Executive Summary (Spanish) ===")
    print(report_es.executive_summary)


def example_recommendations():
    """Example: Generate recommendations."""
    print("\n=== Recommendations Example ===")

    gpt = GPTIntegration(api_key=os.getenv("OPENAI_API_KEY"))
    engine = RecommendationEngine(gpt)

    test_data = {
        "power_output_W": 285,  # Below rated 300W
        "efficiency_pct": 17.8,  # Below expected
        "degradation_after_damp_heat_pct": 4.2
    }

    analysis_results = {
        "summary": "Module underperforming in power output",
        "key_findings": [
            "Power output 5% below rated",
            "Efficiency lower than expected",
            "Degradation within acceptable limits"
        ]
    }

    recommendations = engine.generate_recommendations(
        test_data=test_data,
        analysis_results=analysis_results
    )

    print("Recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")


def example_cost_tracking():
    """Example: Monitor costs and usage."""
    print("\n=== Cost Tracking Example ===")

    gpt = GPTIntegration(api_key=os.getenv("OPENAI_API_KEY"))

    # Make a few queries
    gpt.query("What is the purpose of thermal cycling tests?")
    gpt.query("Explain fill factor in PV modules.")

    # Get statistics
    stats = gpt.get_stats()

    print("Cost Statistics:")
    print(f"  Total Cost: ${stats['costs']['total_cost_usd']:.4f}")
    print(f"  Total Requests: {stats['costs']['total_requests']}")
    print(f"  Total Tokens: {stats['costs']['total_tokens']}")
    print(f"  Avg Cost/Request: ${stats['costs']['average_cost_per_request']:.4f}")

    print("\nCache Statistics:")
    print(f"  Cache Size: {stats['cache']['size']}/{stats['cache']['max_size']}")
    print(f"  Hit Rate: {stats['cache']['hit_rate']:.2%}")

    print("\nRate Limiter Statistics:")
    print(f"  Requests This Minute: {stats['rate_limiter']['requests_this_minute']}")
    print(f"  Tokens This Minute: {stats['rate_limiter']['tokens_this_minute']}")


if __name__ == "__main__":
    # Run all examples
    print("=" * 60)
    print("PV Test Report Automation - GPT Integration Examples")
    print("=" * 60)

    try:
        example_simple_query()
        example_iv_curve_analysis()
        example_compliance_check()
        example_anomaly_detection()
        example_report_generation()
        example_recommendations()
        example_cost_tracking()

    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure you have:")
        print("1. Created a .env file with your OPENAI_API_KEY")
        print("2. Installed all dependencies: pip install -r requirements.txt")
