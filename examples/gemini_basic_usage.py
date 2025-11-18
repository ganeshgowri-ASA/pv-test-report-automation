"""
Basic usage examples for Gemini integration in PV test automation.

This script demonstrates how to use the GeminiProvider for various
PV testing and analysis tasks.
"""

import asyncio
import os
from pathlib import Path

from pv_automation.services.llm import GeminiProvider
from pv_automation.models.llm_models import (
    GeminiRequest,
    VisionAnalysisRequest,
    ComplianceCheckRequest,
    PredictiveAnalysisRequest,
)


async def example_text_generation():
    """Example: Basic text generation with Gemini"""
    print("\n" + "=" * 60)
    print("Example 1: Basic Text Generation")
    print("=" * 60)

    # Initialize provider (API key from environment)
    provider = GeminiProvider(api_key=os.getenv("GEMINI_API_KEY"))

    # Create request
    request = GeminiRequest(
        prompt="Explain the importance of electroluminescence (EL) imaging in PV module testing.",
        temperature=0.7,
        max_tokens=500,
    )

    # Generate response
    response = await provider.generate_text(request)

    print(f"\nPrompt: {request.prompt}")
    print(f"\nResponse:\n{response.content}")
    print(f"\nTokens used: {response.total_token_count}")
    print(f"Finish reason: {response.finish_reason}")


async def example_image_analysis():
    """Example: Analyze EL image for defects"""
    print("\n" + "=" * 60)
    print("Example 2: EL Image Defect Analysis")
    print("=" * 60)

    provider = GeminiProvider(api_key=os.getenv("GEMINI_API_KEY"))

    # Prepare request (replace with actual image path)
    request = VisionAnalysisRequest(
        image_path="path/to/el_image.png",
        image_type="EL",
        standard="IEC 61215",
        additional_context="Module is 5 years old, showing degradation symptoms",
    )

    try:
        # Analyze image
        response = await provider.analyze_image(request)

        print(f"\nImage analyzed: {request.image_path}")
        print(f"Image type: {request.image_type}")
        print(f"\nOverall Assessment:")
        print(response.overall_assessment)
        print(f"\nCompliance Status: {response.compliance_status}")
        print(f"Confidence Score: {response.confidence_score:.2%}")

        print(f"\nDetected Defects ({len(response.defects)}):")
        for i, defect in enumerate(response.defects, 1):
            print(f"\n  {i}. {defect.defect_type.upper()}")
            print(f"     Severity: {defect.severity}")
            print(f"     Confidence: {defect.confidence:.2%}")
            print(f"     Description: {defect.description}")
            if defect.recommendations:
                print(f"     Recommendations: {', '.join(defect.recommendations)}")

    except FileNotFoundError:
        print("\n⚠ Image file not found. Please provide a valid image path.")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


async def example_compliance_check():
    """Example: Check test report compliance"""
    print("\n" + "=" * 60)
    print("Example 3: Compliance Checking")
    print("=" * 60)

    provider = GeminiProvider(api_key=os.getenv("GEMINI_API_KEY"))

    # Sample test data
    test_report = {
        "module_id": "PV-TEST-001",
        "manufacturer": "Solar Tech Inc.",
        "model": "ST-400W-PERC",
        "rated_power": 400,
        "measured_power": 402.5,
        "efficiency": 20.5,
        "voc": 48.2,
        "isc": 10.5,
        "vmpp": 40.1,
        "impp": 10.0,
        "fill_factor": 0.795,
        "temperature_coefficient_pmax": -0.37,
        "tests_completed": [
            "Visual Inspection",
            "Performance at STC",
            "Low Irradiance Performance",
            "Outdoor Exposure",
            "Hot-Spot Endurance",
            "UV Preconditioning",
            "Thermal Cycling",
            "Humidity-Freeze",
            "Damp Heat",
            "Mechanical Load",
        ],
    }

    request = ComplianceCheckRequest(
        report_data=test_report,
        standard="IEC 61215",
        check_missing_data=True,
    )

    # Check compliance
    response = await provider.check_compliance(request)

    print(f"\nStandard: {request.standard}")
    print(f"Compliance Status: {response.compliance_status}")

    if response.violations:
        print(f"\n⚠ Violations Found ({len(response.violations)}):")
        for violation in response.violations:
            print(f"  - {violation}")
    else:
        print("\n✓ No violations found")

    if response.missing_data:
        print(f"\nMissing Data ({len(response.missing_data)}):")
        for missing in response.missing_data:
            print(f"  - {missing}")

    if response.recommendations:
        print(f"\nRecommendations:")
        for rec in response.recommendations:
            print(f"  • {rec}")


async def example_predictive_analysis():
    """Example: Predictive failure analysis"""
    print("\n" + "=" * 60)
    print("Example 4: Predictive Failure Analysis")
    print("=" * 60)

    provider = GeminiProvider(api_key=os.getenv("GEMINI_API_KEY"))

    # Historical test data
    test_data = {
        "installation_date": "2018-01-15",
        "initial_measurements": {
            "power_output": 400.0,
            "efficiency": 20.8,
            "degradation_rate": 0.0,
        },
        "year_1_measurements": {
            "power_output": 398.0,
            "efficiency": 20.7,
            "degradation_rate": 0.5,
        },
        "year_3_measurements": {
            "power_output": 394.0,
            "efficiency": 20.5,
            "degradation_rate": 0.5,
        },
        "current_measurements": {
            "power_output": 388.0,
            "efficiency": 20.2,
            "degradation_rate": 0.61,
        },
        "defects_observed": ["minor_hotspot_cell_B7", "micro_crack_cell_C5"],
        "el_imaging_score": 8.5,
    }

    environmental_data = {
        "location": "Desert climate",
        "avg_temperature_celsius": 35,
        "humidity_percent": 15,
        "annual_rainfall_mm": 50,
        "uv_exposure": "high",
        "soiling_frequency": "moderate",
    }

    request = PredictiveAnalysisRequest(
        test_data=test_data,
        module_age_years=5.5,
        environmental_factors=environmental_data,
        warranty_period_years=25,
    )

    # Perform predictive analysis
    response = await provider.predict_failures(request)

    print(f"\nModule Age: {request.module_age_years} years")
    print(f"Warranty Period: {request.warranty_period_years} years")
    print(f"\n📊 Analysis Results:")
    print(f"   Failure Probability: {response.failure_probability:.1%}")
    print(f"   Confidence: {response.confidence_score:.1%}")

    if response.estimated_lifespan_years:
        print(f"   Estimated Remaining Life: {response.estimated_lifespan_years:.1f} years")

    print(f"\n⚠ Risk Factors:")
    for risk in response.risk_factors:
        print(f"   • {risk}")

    print(f"\n📈 Degradation Trends:")
    for trend in response.degradation_trends:
        print(f"   • {trend}")

    print(f"\n🛡️ Preventive Measures:")
    for measure in response.preventive_measures:
        print(f"   • {measure}")


async def example_batch_analysis():
    """Example: Batch analyze multiple images"""
    print("\n" + "=" * 60)
    print("Example 5: Batch Image Analysis")
    print("=" * 60)

    provider = GeminiProvider(api_key=os.getenv("GEMINI_API_KEY"))

    # Multiple images to analyze
    image_paths = [
        "path/to/module_1_el.png",
        "path/to/module_2_el.png",
        "path/to/module_3_thermal.png",
    ]

    requests = [
        VisionAnalysisRequest(
            image_path=img,
            image_type="EL" if "el" in img else "Thermal",
            standard="IEC 61215",
        )
        for img in image_paths
    ]

    print(f"\nAnalyzing {len(requests)} images in batch...")

    try:
        # Batch analyze
        responses = await provider.batch_analyze_images(requests)

        print(f"\n✓ Analysis complete!\n")

        for i, (req, resp) in enumerate(zip(requests, responses), 1):
            print(f"Image {i}: {Path(req.image_path).name}")
            print(f"  Status: {resp.compliance_status}")
            print(f"  Defects: {len(resp.defects)}")
            print(f"  Confidence: {resp.confidence_score:.2%}")
            print()

    except FileNotFoundError:
        print("\n⚠ One or more image files not found. Please provide valid paths.")


async def example_health_check():
    """Example: Check Gemini API health"""
    print("\n" + "=" * 60)
    print("Example 6: API Health Check")
    print("=" * 60)

    provider = GeminiProvider(api_key=os.getenv("GEMINI_API_KEY"))

    health = await provider.health_check()

    print(f"\nHealth Status: {health['status'].upper()}")
    print(f"Provider: {health['provider']}")
    print(f"Model: {health.get('model', 'N/A')}")
    print(f"Vision Model: {health.get('vision_model', 'N/A')}")

    if health["status"] == "healthy":
        print("\n✓ All systems operational")
    else:
        print(f"\n❌ Error: {health.get('error', 'Unknown error')}")


def example_model_info():
    """Example: Get model configuration information"""
    print("\n" + "=" * 60)
    print("Example 7: Model Information")
    print("=" * 60)

    provider = GeminiProvider(api_key=os.getenv("GEMINI_API_KEY"))

    info = provider.get_model_info()

    print(f"\nProvider: {info['provider']}")
    print(f"Text Model: {info['text_model']}")
    print(f"Vision Model: {info['vision_model']}")

    print(f"\nCapabilities:")
    for cap in info['capabilities']:
        print(f"  ✓ {cap.replace('_', ' ').title()}")

    print(f"\nConfiguration:")
    for key, value in info['configuration'].items():
        print(f"  {key}: {value}")

    print(f"\nLimits:")
    for key, value in info['limits'].items():
        print(f"  {key}: {value}")


async def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("GEMINI INTEGRATION EXAMPLES")
    print("PV Test Report Automation")
    print("=" * 60)

    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        print("\n❌ Error: GEMINI_API_KEY environment variable not set")
        print("Please set your API key:")
        print("  export GEMINI_API_KEY='your_api_key_here'")
        return

    try:
        # Run examples
        await example_text_generation()
        await example_image_analysis()
        await example_compliance_check()
        await example_predictive_analysis()
        await example_batch_analysis()
        await example_health_check()
        example_model_info()

        print("\n" + "=" * 60)
        print("Examples completed successfully!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Error running examples: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
