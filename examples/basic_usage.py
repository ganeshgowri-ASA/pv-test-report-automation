"""Basic usage examples for PV image processing

This script demonstrates how to use the image processing module
for various PV testing scenarios.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from image_processing import ImageProcessor, ImageType, ProcessingConfig


def example_1_process_el_image():
    """Example 1: Process a single EL image"""
    print("=" * 80)
    print("Example 1: Process EL Image")
    print("=" * 80)

    # Initialize processor with operator and equipment IDs
    processor = ImageProcessor(
        operator_id="OP-001",
        equipment_id="EL-CAM-001"
    )

    # Process EL image
    result = processor.process_image(
        file_path="path/to/el_image.jpg",
        image_type=ImageType.EL,
        save_annotated=True,
        output_dir="output/annotated"
    )

    # Print results
    print(f"\nFile: {result.file_path}")
    print(f"Quality Passed: {result.quality_passed}")
    print(f"Defects Detected: {len(result.defects_detected)}")

    for i, defect in enumerate(result.defects_detected, 1):
        print(f"\n  Defect {i}:")
        print(f"    Type: {defect.defect_type.value}")
        print(f"    Severity: {defect.severity.value}")
        print(f"    Location: {defect.location}")
        print(f"    Confidence: {defect.confidence:.2%}")
        print(f"    Description: {defect.description}")

    print(f"\nQuality Metrics:")
    print(f"  Blur Score: {result.quality_metrics.blur_score:.2f}")
    print(f"  Brightness: {result.quality_metrics.brightness_mean:.2f}")
    print(f"  Contrast: {result.quality_metrics.contrast_std:.2f}")
    print(f"  Exposure: {result.quality_metrics.exposure_quality}")

    # Export to JSON for archival
    import json
    with open("output/result.json", "w") as f:
        json.dump(result.dict(), f, indent=2, default=str)

    print("\nResult saved to output/result.json")


def example_2_batch_processing():
    """Example 2: Batch process multiple images"""
    print("\n" + "=" * 80)
    print("Example 2: Batch Processing")
    print("=" * 80)

    processor = ImageProcessor(
        operator_id="OP-001",
        equipment_id="EL-CAM-001"
    )

    # Define batch of images
    image_files = [
        "path/to/el_image_1.jpg",
        "path/to/el_image_2.jpg",
        "path/to/el_image_3.jpg",
    ]
    image_types = [ImageType.EL] * 3

    # Process batch
    results = processor.process_batch(
        file_paths=image_files,
        image_types=image_types,
        save_annotated=True,
        output_dir="output/batch"
    )

    # Generate summary report
    processor.generate_report(results, "output/batch_report.txt")

    print(f"\nProcessed {len(results)} images")
    print(f"Report saved to output/batch_report.txt")


def example_3_custom_configuration():
    """Example 3: Custom processing configuration"""
    print("\n" + "=" * 80)
    print("Example 3: Custom Configuration")
    print("=" * 80)

    # Create custom configuration
    config = ProcessingConfig(
        # Quality thresholds
        min_blur_score=150.0,  # Stricter blur requirement
        min_brightness=30.0,
        max_brightness=225.0,
        min_contrast=40.0,
        min_resolution=(1024, 768),  # Higher resolution requirement

        # Defect detection
        crack_detection_sensitivity=0.8,  # More sensitive
        dark_spot_threshold=0.25,
        min_defect_area=50,  # Detect smaller defects

        # OCR settings
        ocr_enabled=True,
        ocr_language="eng",
        ocr_confidence_threshold=70.0,

        # Processing options
        apply_preprocessing=True,
        generate_annotations=True,
        save_intermediate=True  # Save intermediate processing steps
    )

    # Initialize processor with custom config
    processor = ImageProcessor(
        config=config,
        operator_id="OP-002",
        equipment_id="HIGHRES-CAM-001"
    )

    # Process with custom settings
    result = processor.process_image(
        "path/to/high_res_image.jpg",
        ImageType.EL,
        save_annotated=True,
        output_dir="output/custom"
    )

    print(f"\nProcessed with custom configuration")
    print(f"Quality Passed: {result.quality_passed}")


def example_4_thermal_imaging():
    """Example 4: Process thermal images"""
    print("\n" + "=" * 80)
    print("Example 4: Thermal Image Processing")
    print("=" * 80)

    processor = ImageProcessor(
        operator_id="OP-001",
        equipment_id="THERMAL-CAM-001"
    )

    # Process thermal image
    result = processor.process_image(
        "path/to/thermal_image.jpg",
        ImageType.THERMAL,
        save_annotated=True,
        output_dir="output/thermal"
    )

    print(f"\nThermal Image Analysis:")
    print(f"Hotspots Detected: {len([d for d in result.defects_detected if d.defect_type.value == 'hotspot'])}")

    for defect in result.defects_detected:
        if defect.defect_type.value == "hotspot":
            print(f"\n  Hotspot:")
            print(f"    Severity: {defect.severity.value}")
            print(f"    Area: {defect.area_pixels} pixels")
            print(f"    {defect.description}")


def example_5_iv_curve_extraction():
    """Example 5: Extract I-V curve from chart"""
    print("\n" + "=" * 80)
    print("Example 5: I-V Curve Extraction")
    print("=" * 80)

    processor = ImageProcessor(
        operator_id="OP-001",
        equipment_id="SCANNER-001"
    )

    # Process I-V curve chart
    result = processor.process_image(
        "path/to/iv_curve_chart.jpg",
        ImageType.IV_CHART,
        save_annotated=True,
        output_dir="output/iv_curves"
    )

    if result.iv_curve_data and result.iv_curve_data.get('parameters'):
        params = result.iv_curve_data['parameters']
        print(f"\nI-V Curve Parameters:")
        print(f"  Voc (Open Circuit Voltage): {params.get('Voc', 0):.2f} V")
        print(f"  Isc (Short Circuit Current): {params.get('Isc', 0):.2f} A")
        print(f"  Pmax (Maximum Power): {params.get('Pmax', 0):.2f} W")
        print(f"  Vmpp (Voltage at MPP): {params.get('Vmpp', 0):.2f} V")
        print(f"  Impp (Current at MPP): {params.get('Impp', 0):.2f} A")
        print(f"  Fill Factor: {params.get('FF', 0):.3f}")


def example_6_result_validation():
    """Example 6: Two-person validation workflow"""
    print("\n" + "=" * 80)
    print("Example 6: Result Validation Workflow")
    print("=" * 80)

    # Step 1: Operator processes image
    processor = ImageProcessor(
        operator_id="OP-001",
        equipment_id="EL-CAM-001"
    )

    result = processor.process_image(
        "path/to/el_image.jpg",
        ImageType.EL
    )

    print(f"Step 1: Image processed by {result.operator_id}")
    print(f"        Validated: {result.validated}")

    # Step 2: Technical reviewer validates
    validated_result = processor.validate_result(
        result,
        reviewer_id="REVIEWER-001",
        notes="Reviewed defect classifications. All confirmed via visual inspection."
    )

    print(f"\nStep 2: Result validated by REVIEWER-001")
    print(f"        Validated: {validated_result.validated}")
    print(f"        Validation Time: {validated_result.validation_timestamp}")
    print(f"        Notes: {validated_result.reviewer_notes}")


def example_7_ocr_extraction():
    """Example 7: OCR text extraction from equipment displays"""
    print("\n" + "=" * 80)
    print("Example 7: OCR Text Extraction")
    print("=" * 80)

    processor = ImageProcessor(
        operator_id="OP-001",
        equipment_id="CAMERA-001"
    )

    # Process image with equipment display
    result = processor.process_image(
        "path/to/equipment_display.jpg",
        ImageType.VISUAL
    )

    if result.ocr_text:
        print(f"\nExtracted Text:")
        print(result.ocr_text)

    if result.ocr_data and result.ocr_data.get('structured_data'):
        structured = result.ocr_data['structured_data']

        print(f"\nStructured Data:")
        if 'voltages' in structured:
            print(f"  Voltages: {structured['voltages']}")
        if 'currents' in structured:
            print(f"  Currents: {structured['currents']}")
        if 'temperatures' in structured:
            print(f"  Temperatures: {structured['temperatures']}")
        if 'serial_numbers' in structured:
            print(f"  Serial Numbers: {structured['serial_numbers']}")


def example_8_quality_only():
    """Example 8: Quality assessment only (no defect detection)"""
    print("\n" + "=" * 80)
    print("Example 8: Quality Assessment Only")
    print("=" * 80)

    from image_processing import QualityValidator
    import cv2

    validator = QualityValidator()

    # Load image
    image = cv2.imread("path/to/image.jpg")

    # Validate quality
    passed, metrics = validator.validate_image(image)

    print(f"\nQuality Assessment:")
    print(f"  Overall: {'PASS' if passed else 'FAIL'}")
    print(f"\nMetrics:")
    print(f"  Blur Score: {metrics.blur_score:.2f} (min: 100)")
    print(f"  Brightness: {metrics.brightness_mean:.2f} (range: 20-235)")
    print(f"  Contrast: {metrics.contrast_std:.2f} (min: 30)")
    print(f"  Sharpness: {metrics.sharpness_score:.2f} (min: 50)")
    print(f"  Noise Level: {metrics.noise_level:.2f} (max: 50)")
    print(f"  Uniformity: {metrics.uniformity_score:.2f}")
    print(f"  Exposure: {metrics.exposure_quality}")

    # Enhance if needed
    if not passed:
        print("\n  Applying enhancement...")
        enhanced = validator.enhance_image(image)
        passed_enhanced, metrics_enhanced = validator.validate_image(enhanced)
        print(f"  Enhanced Quality: {'PASS' if passed_enhanced else 'FAIL'}")


def main():
    """Run all examples (demonstrative only - paths need to be updated)"""
    print("\n")
    print("=" * 80)
    print("PV Image Processing - Usage Examples")
    print("=" * 80)
    print("\nNOTE: Update file paths before running these examples")
    print("\nAvailable examples:")
    print("  1. Process single EL image")
    print("  2. Batch processing")
    print("  3. Custom configuration")
    print("  4. Thermal imaging")
    print("  5. I-V curve extraction")
    print("  6. Result validation workflow")
    print("  7. OCR text extraction")
    print("  8. Quality assessment only")
    print("\nUncomment the desired example in the code to run it.")


if __name__ == "__main__":
    main()

    # Uncomment to run specific examples:
    # example_1_process_el_image()
    # example_2_batch_processing()
    # example_3_custom_configuration()
    # example_4_thermal_imaging()
    # example_5_iv_curve_extraction()
    # example_6_result_validation()
    # example_7_ocr_extraction()
    # example_8_quality_only()
