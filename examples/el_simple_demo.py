#!/usr/bin/env python3
"""
Simple Electroluminescence Processing Demo

A simple example demonstrating basic EL image processing and report generation.

Usage:
    python el_simple_demo.py path/to/el_image.tif
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tests.electroluminescence import (
    ELImageProcessor,
    AdvancedDefectDetector,
    ELReportGenerator
)


def main():
    """Simple demo of EL processing"""

    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python el_simple_demo.py <path_to_el_image>")
        sys.exit(1)

    image_path = sys.argv[1]

    # Verify file exists
    if not Path(image_path).exists():
        print(f"Error: Image file not found: {image_path}")
        sys.exit(1)

    print("="*80)
    print("EL IMAGE PROCESSING DEMO")
    print("="*80)
    print(f"Image: {image_path}\n")

    # Step 1: Create image processor
    print("Step 1: Initializing image processor...")
    processor = ELImageProcessor(
        cell_size=(156, 156),    # Cell size in mm
        grid_layout=(6, 10),     # 6 rows x 10 columns
        min_defect_area=50       # Minimum defect size in pixels
    )

    # Step 2: Process the image
    print("Step 2: Processing EL image...")
    result = processor.process_image(image_path)

    print(f"  ✓ Image loaded: {result.metadata['image_shape']}")
    print(f"  ✓ Cells segmented: {result.metadata['total_cells']}")
    print(f"  ✓ Defects detected: {result.metadata['total_defects']}")

    # Step 3: Display defect summary
    print("\nStep 3: Defect Summary")
    print("-"*80)

    if result.defects:
        print(f"Total defects: {len(result.defects)}\n")

        print("By Type:")
        for defect_type, count in result.metadata['defects_by_type'].items():
            print(f"  • {defect_type.replace('_', ' ').title()}: {count}")

        print("\nBy Severity:")
        for severity, count in result.metadata['defects_by_severity'].items():
            print(f"  • {severity.title()}: {count}")
    else:
        print("No defects detected - module appears healthy!")

    # Step 4: Advanced defect detection
    print("\nStep 4: Running advanced defect detection...")
    detector = AdvancedDefectDetector(
        min_crack_length=20,
        edge_detection_method='canny',
        power_loss_model='linear'
    )

    # Detect cracks
    crack_mask, crack_features = detector.detect_cracks_ml(
        result.processed_image,
        use_gabor_filters=False  # Set to True for better accuracy (slower)
    )
    print(f"  ✓ Crack structures detected: {len(crack_features)}")

    # Calculate statistics
    statistics = detector.calculate_statistics(
        result.defects,
        result.segmented_cells,
        (6, 10)
    )

    print(f"  ✓ Total affected area: {statistics.total_affected_area:.2f}%")
    print(f"  ✓ Critical cells: {len(statistics.critical_cells)}")
    print(f"  ✓ Defect density: {statistics.defect_density:.2f} defects/cell")

    # Step 5: Generate report
    print("\nStep 5: Generating HTML report...")
    report_gen = ELReportGenerator(
        output_dir="./el_demo_results",
        dpi=150
    )

    module_id = Path(image_path).stem
    report_path = report_gen.generate_full_report(
        module_id=module_id,
        initial_result=result,
        statistics=statistics
    )

    print(f"  ✓ Report generated: {report_path}")

    # Step 6: Export statistics (optional)
    print("\nStep 6: Exporting statistics...")
    detector.export_statistics(
        statistics,
        f"./el_demo_results/statistics_{module_id}.json",
        format='json'
    )
    print(f"  ✓ Statistics exported to JSON")

    # Summary
    print("\n" + "="*80)
    print("PROCESSING COMPLETE")
    print("="*80)
    print(f"Module: {module_id}")
    print(f"Defects: {len(result.defects)}")
    print(f"Critical cells: {len(statistics.critical_cells)}")
    print(f"Report: {report_path}")
    print("\nOpen the HTML report in your browser to view detailed results.")
    print("="*80)


if __name__ == '__main__':
    main()
