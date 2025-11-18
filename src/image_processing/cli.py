"""Command-line interface for image processing

Simple CLI tool for processing PV test images.
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Optional

from .processor import ImageProcessor
from .models import ImageType, ProcessingConfig


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="PV Test Image Processing CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single EL image
  python -m image_processing.cli process image.jpg --type el --output results/

  # Batch process with custom config
  python -m image_processing.cli batch images/*.jpg --type el --output batch/

  # Quality check only
  python -m image_processing.cli quality image.jpg

  # Extract I-V curve
  python -m image_processing.cli process chart.jpg --type iv_chart
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Process command
    process_parser = subparsers.add_parser("process", help="Process a single image")
    process_parser.add_argument("image", help="Path to image file")
    process_parser.add_argument(
        "--type",
        choices=["el", "thermal", "visual", "iv_chart"],
        required=True,
        help="Image type"
    )
    process_parser.add_argument(
        "--output",
        help="Output directory for annotated images"
    )
    process_parser.add_argument(
        "--operator-id",
        help="Operator identification"
    )
    process_parser.add_argument(
        "--equipment-id",
        help="Equipment identification"
    )
    process_parser.add_argument(
        "--save-json",
        action="store_true",
        help="Save result as JSON"
    )

    # Quality command
    quality_parser = subparsers.add_parser("quality", help="Check image quality")
    quality_parser.add_argument("image", help="Path to image file")

    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Process multiple images")
    batch_parser.add_argument("images", nargs="+", help="Image file paths")
    batch_parser.add_argument(
        "--type",
        choices=["el", "thermal", "visual", "iv_chart"],
        required=True,
        help="Image type (same for all)"
    )
    batch_parser.add_argument(
        "--output",
        help="Output directory"
    )
    batch_parser.add_argument(
        "--operator-id",
        help="Operator identification"
    )
    batch_parser.add_argument(
        "--equipment-id",
        help="Equipment identification"
    )
    batch_parser.add_argument(
        "--report",
        help="Generate report at this path"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    if args.command == "process":
        return process_image(args)
    elif args.command == "quality":
        return check_quality(args)
    elif args.command == "batch":
        return process_batch(args)

    return 0


def process_image(args):
    """Process a single image"""
    import cv2

    # Load image
    image_path = Path(args.image)
    if not image_path.exists():
        print(f"Error: Image not found: {image_path}")
        return 1

    # Initialize processor
    processor = ImageProcessor(
        operator_id=args.operator_id,
        equipment_id=args.equipment_id
    )

    # Map image type
    image_type = ImageType(args.type)

    # Process
    print(f"Processing {image_type.value} image: {image_path}")

    try:
        result = processor.process_image(
            str(image_path),
            image_type,
            save_annotated=bool(args.output),
            output_dir=args.output
        )

        # Print summary
        print(f"\n{'='*60}")
        print(f"Processing Complete")
        print(f"{'='*60}")
        print(f"File: {result.file_path}")
        print(f"Hash: {result.file_hash}")
        print(f"Quality: {'PASS' if result.quality_passed else 'FAIL'}")
        print(f"Defects: {len(result.defects_detected)}")

        if result.defects_detected:
            print(f"\nDetected Defects:")
            for i, defect in enumerate(result.defects_detected, 1):
                print(f"  {i}. {defect.defect_type.value} ({defect.severity.value})")
                print(f"     Location: {defect.location}")
                print(f"     Confidence: {defect.confidence:.1%}")

        print(f"\nQuality Metrics:")
        print(f"  Blur Score: {result.quality_metrics.blur_score:.2f}")
        print(f"  Brightness: {result.quality_metrics.brightness_mean:.2f}")
        print(f"  Exposure: {result.quality_metrics.exposure_quality}")

        if result.iv_curve_data and result.iv_curve_data.get('parameters'):
            params = result.iv_curve_data['parameters']
            print(f"\nI-V Curve Parameters:")
            print(f"  Voc: {params.get('Voc', 0):.2f} V")
            print(f"  Isc: {params.get('Isc', 0):.2f} A")
            print(f"  Pmax: {params.get('Pmax', 0):.2f} W")
            print(f"  FF: {params.get('FF', 0):.3f}")

        # Save JSON if requested
        if args.save_json:
            json_path = image_path.with_suffix('.json')
            with open(json_path, 'w') as f:
                json.dump(result.dict(), f, indent=2, default=str)
            print(f"\nResult saved to: {json_path}")

        return 0

    except Exception as e:
        print(f"Error processing image: {e}")
        import traceback
        traceback.print_exc()
        return 1


def check_quality(args):
    """Check image quality only"""
    import cv2
    from .quality_validator import QualityValidator

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"Error: Image not found: {image_path}")
        return 1

    # Load image
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"Error: Failed to read image: {image_path}")
        return 1

    # Validate
    validator = QualityValidator()
    passed, metrics = validator.validate_image(image)

    # Print results
    print(f"\n{'='*60}")
    print(f"Quality Assessment: {image_path.name}")
    print(f"{'='*60}")
    print(f"Overall: {'PASS' if passed else 'FAIL'}")
    print(f"\nMetrics:")
    print(f"  Blur Score: {metrics.blur_score:.2f} (min: 100)")
    print(f"  Brightness: {metrics.brightness_mean:.2f} (range: 20-235)")
    print(f"  Contrast: {metrics.contrast_std:.2f} (min: 30)")
    print(f"  Sharpness: {metrics.sharpness_score:.2f} (min: 50)")
    print(f"  Noise: {metrics.noise_level:.2f} (max: 50)")
    print(f"  Uniformity: {metrics.uniformity_score:.2f}")
    print(f"  Exposure: {metrics.exposure_quality}")
    print(f"  Resolution: {metrics.resolution[0]}×{metrics.resolution[1]}")

    return 0 if passed else 1


def process_batch(args):
    """Process multiple images"""
    from pathlib import Path

    # Validate images
    image_paths = [Path(p) for p in args.images]
    missing = [p for p in image_paths if not p.exists()]
    if missing:
        print(f"Error: Images not found: {', '.join(str(p) for p in missing)}")
        return 1

    # Initialize processor
    processor = ImageProcessor(
        operator_id=args.operator_id,
        equipment_id=args.equipment_id
    )

    # Map image type
    image_type = ImageType(args.type)
    image_types = [image_type] * len(image_paths)

    # Process batch
    print(f"Processing {len(image_paths)} images...")

    try:
        results = processor.process_batch(
            file_paths=[str(p) for p in image_paths],
            image_types=image_types,
            save_annotated=bool(args.output),
            output_dir=args.output
        )

        # Print summary
        print(f"\n{'='*60}")
        print(f"Batch Processing Complete")
        print(f"{'='*60}")
        print(f"Total Images: {len(results)}")
        print(f"Quality Passed: {sum(1 for r in results if r.quality_passed)}")
        print(f"Total Defects: {sum(len(r.defects_detected) for r in results)}")

        # Generate report if requested
        if args.report:
            processor.generate_report(results, args.report)
            print(f"\nReport saved to: {args.report}")

        return 0

    except Exception as e:
        print(f"Error in batch processing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
