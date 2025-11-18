"""Advanced usage examples for GPT integration."""

import os
import json
from dotenv import load_dotenv

from src.gpt_integration import GPTIntegration
from src.gpt_integration.analyzers import TestResultAnalyzer, ComplianceChecker, AnomalyDetector
from src.gpt_integration.generators import ReportGenerator, RecommendationEngine
from src.models.gpt_models import (
    GPTRequest,
    ComplianceStandard,
    Language,
    NaturalLanguageQuery
)
from src.utils.config import Config

load_dotenv()


def example_custom_configuration():
    """Example: Use custom configuration."""
    print("\n=== Custom Configuration Example ===")

    # Create custom config
    config = Config.from_env()

    # Override specific settings
    config.default_temperature = 0.2  # Lower for more deterministic
    config.default_max_tokens = 3000
    config.enable_cache = True
    config.rate_limit_requests_per_minute = 30

    gpt = GPTIntegration(config=config)

    response = gpt.query("Explain PID testing in PV modules.")
    print(f"Response: {response[:200]}...")


def example_advanced_request():
    """Example: Use advanced GPT request with custom parameters."""
    print("\n=== Advanced Request Example ===")

    gpt = GPTIntegration(api_key=os.getenv("OPENAI_API_KEY"))

    request = GPTRequest(
        prompt="""Analyze this failure scenario:
        A PV module failed hot-spot endurance testing with visible burn marks.
        IR imaging shows hot spots at cell edges.
        What are the likely root causes?""",
        model="gpt-4-turbo",
        temperature=0.3,  # Lower for technical accuracy
        max_tokens=1500,
        system_message="""You are an expert in PV module failure analysis
        with 20 years of experience in manufacturing quality control."""
    )

    response = gpt.generate_completion(request)

    print(f"Content: {response.content}")
    print(f"\nModel: {response.model_used}")
    print(f"Tokens: {response.tokens_used}")
    print(f"Cost: ${response.cost_usd:.4f}")
    print(f"Cached: {response.cached}")


def example_batch_analysis():
    """Example: Analyze multiple test results in batch."""
    print("\n=== Batch Analysis Example ===")

    gpt = GPTIntegration(api_key=os.getenv("OPENAI_API_KEY"))
    analyzer = TestResultAnalyzer(gpt)

    # Multiple modules to analyze
    modules = [
        {
            "module_id": "PV-001",
            "pmax_W": 305,
            "voc_V": 48.5,
            "isc_A": 9.3,
            "ff": 0.78
        },
        {
            "module_id": "PV-002",
            "pmax_W": 298,
            "voc_V": 48.2,
            "isc_A": 9.1,
            "ff": 0.76
        },
        {
            "module_id": "PV-003",
            "pmax_W": 310,
            "voc_V": 48.7,
            "isc_A": 9.4,
            "ff": 0.79
        }
    ]

    results = []
    for module in modules:
        result = analyzer.analyze_test_results(module)
        results.append({
            "module_id": module["module_id"],
            "summary": result.summary,
            "quality_score": result.data_quality_score
        })

    print("Batch Analysis Results:")
    for r in results:
        print(f"\n{r['module_id']}:")
        print(f"  Quality Score: {r['quality_score']:.2f}")
        print(f"  Summary: {r['summary'][:100]}...")


def example_multi_standard_compliance():
    """Example: Check compliance against multiple standards."""
    print("\n=== Multi-Standard Compliance Example ===")

    gpt = GPTIntegration(api_key=os.getenv("OPENAI_API_KEY"))
    checker = ComplianceChecker(gpt)

    report = "Module passed all IEC 61215 and IEC 61730 requirements."
    test_data = {
        "all_tests": "passed",
        "safety_tests": "passed"
    }

    # Check multiple standards
    standards = [
        ComplianceStandard.IEC_61215,
        ComplianceStandard.IEC_61730
    ]

    compliance_results = {}
    for standard in standards:
        result = checker.check_compliance(report, test_data, standard)
        compliance_results[standard.value] = {
            "status": result.status.value,
            "confidence": result.confidence_score
        }

    print("Multi-Standard Compliance:")
    for standard, result in compliance_results.items():
        print(f"\n{standard}:")
        print(f"  Status: {result['status'].upper()}")
        print(f"  Confidence: {result['confidence']:.2%}")


def example_data_quality_analysis():
    """Example: Comprehensive data quality analysis."""
    print("\n=== Data Quality Analysis Example ===")

    gpt = GPTIntegration(api_key=os.getenv("OPENAI_API_KEY"))
    detector = AnomalyDetector(gpt)

    test_data = {
        "module_id": "PV-2024-005",
        "measurements": {
            "power_W": [305, 307, None, 308, 306],  # Missing value
            "voltage_V": [48.5, 48.6, 48.4, 48.5, 48.5],
            "current_A": [9.2, 9.3, 9.1, 9.2, 9.2],
            "temperature_C": [25, 25, 25, 45, 25]  # Temperature spike
        },
        "timestamp": ["10:00", "10:05", "10:10", "10:15", "10:20"]
    }

    quality_report = detector.check_data_quality(test_data)

    print("Data Quality Report:")
    print(f"  Overall Score: {quality_report['overall_score']:.2f}")
    print(f"  Completeness: {quality_report.get('completeness_score', 'N/A')}")
    print(f"  Accuracy: {quality_report.get('accuracy_score', 'N/A')}")
    print(f"  Consistency: {quality_report.get('consistency_score', 'N/A')}")

    if quality_report.get('issues'):
        print("\nIssues Found:")
        for issue in quality_report['issues']:
            print(f"  - {issue}")

    if quality_report.get('recommendations'):
        print("\nRecommendations:")
        for rec in quality_report['recommendations']:
            print(f"  - {rec}")


def example_natural_language_queries():
    """Example: Answer natural language queries about test data."""
    print("\n=== Natural Language Queries Example ===")

    gpt = GPTIntegration(api_key=os.getenv("OPENAI_API_KEY"))
    engine = RecommendationEngine(gpt)

    # Test context
    context = {
        "module_type": "300W Monocrystalline",
        "test_results": {
            "pmax_W": 305,
            "efficiency_pct": 19.2,
            "degradation_pct": 2.1
        },
        "environmental_tests": {
            "thermal_cycling": "PASS",
            "humidity_freeze": "PASS",
            "damp_heat": "PASS"
        }
    }

    # Various queries
    queries = [
        "What is the power output of this module?",
        "Did the module pass environmental testing?",
        "How does the efficiency compare to industry standards?",
        "What is the degradation percentage?"
    ]

    print("Natural Language Query Results:\n")
    for query_text in queries:
        query = NaturalLanguageQuery(
            query=query_text,
            context=context,
            include_visualizations=True
        )

        response = engine.answer_query(query)

        print(f"Q: {query_text}")
        print(f"A: {response.answer}")
        print(f"   Confidence: {response.confidence:.2%}\n")


def example_multilingual_reports():
    """Example: Generate reports in multiple languages."""
    print("\n=== Multilingual Reports Example ===")

    gpt = GPTIntegration(api_key=os.getenv("OPENAI_API_KEY"))
    generator = ReportGenerator(gpt)

    test_data = {
        "module": "300W Solar Panel",
        "result": "All tests passed",
        "efficiency": 19.2
    }

    languages = [
        (Language.ENGLISH, "English"),
        (Language.SPANISH, "Spanish"),
        (Language.GERMAN, "German")
    ]

    for lang, name in languages:
        report = generator.generate_executive_summary(
            test_data=test_data,
            language=lang
        )
        print(f"\n{name} Summary:")
        print(report.executive_summary[:150] + "...")


def example_corrective_actions():
    """Example: Get corrective actions for failures."""
    print("\n=== Corrective Actions Example ===")

    gpt = GPTIntegration(api_key=os.getenv("OPENAI_API_KEY"))
    engine = RecommendationEngine(gpt)

    failures = [
        "Hot-spot endurance test failed - visible burn marks",
        "Mechanical load test failed - glass cracking at 2400 Pa",
        "Damp heat test - 6% power degradation (exceeds 5% limit)"
    ]

    context = {
        "module_type": "Polycrystalline",
        "manufacturing_date": "2024-01",
        "production_line": "Line B"
    }

    actions = engine.suggest_corrective_actions(failures, context)

    print("Corrective Actions:\n")
    for failure, action_list in actions.items():
        print(f"Failure: {failure}")
        for action in action_list:
            print(f"  → {action}")
        print()


def example_performance_optimization():
    """Example: Optimize performance with caching."""
    print("\n=== Performance Optimization Example ===")

    gpt = GPTIntegration(api_key=os.getenv("OPENAI_API_KEY"))

    # Same query multiple times
    query = "What is the fill factor in PV modules?"

    print("Making same query 3 times...\n")

    for i in range(3):
        response = gpt.generate_completion(
            GPTRequest(prompt=query),
            use_cache=True
        )
        status = "CACHED" if response.cached else "API CALL"
        print(f"Call {i+1}: {status} - Cost: ${response.cost_usd:.4f}")

    # Check cache statistics
    stats = gpt.get_stats()
    print(f"\nCache Hit Rate: {stats['cache']['hit_rate']:.2%}")
    print(f"Cache Size: {stats['cache']['size']}")


if __name__ == "__main__":
    print("=" * 60)
    print("Advanced GPT Integration Examples")
    print("=" * 60)

    try:
        example_custom_configuration()
        example_advanced_request()
        example_batch_analysis()
        example_multi_standard_compliance()
        example_data_quality_analysis()
        example_natural_language_queries()
        example_multilingual_reports()
        example_corrective_actions()
        example_performance_optimization()

    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure OPENAI_API_KEY is set in .env file")
