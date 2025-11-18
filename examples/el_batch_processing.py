#!/usr/bin/env python3
"""
Electroluminescence Batch Processing Demo

This script demonstrates batch processing of multiple EL images,
including defect detection, statistics calculation, and report generation.

Usage:
    python el_batch_processing.py --input-dir ./images --output-dir ./results
"""

import argparse
import sys
from pathlib import Path
import logging
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tests.electroluminescence import (
    ELImageProcessor,
    AdvancedDefectDetector,
    ELReportGenerator,
    IEC61215Criteria
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Batch process EL images and generate defect reports'
    )

    parser.add_argument(
        '--input-dir',
        type=str,
        required=True,
        help='Directory containing EL images (TIFF, PNG, JPEG)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='./el_results',
        help='Output directory for results (default: ./el_results)'
    )

    parser.add_argument(
        '--grid-rows',
        type=int,
        default=6,
        help='Number of cell rows in module (default: 6)'
    )

    parser.add_argument(
        '--grid-cols',
        type=int,
        default=10,
        help='Number of cell columns in module (default: 10)'
    )

    parser.add_argument(
        '--min-defect-area',
        type=int,
        default=50,
        help='Minimum defect area in pixels (default: 50)'
    )

    parser.add_argument(
        '--edge-detection',
        type=str,
        choices=['canny', 'sobel', 'scharr', 'prewitt'],
        default='canny',
        help='Edge detection method (default: canny)'
    )

    parser.add_argument(
        '--power-loss-model',
        type=str,
        choices=['linear', 'exponential', 'quadratic'],
        default='linear',
        help='Power loss estimation model (default: linear)'
    )

    parser.add_argument(
        '--use-gabor',
        action='store_true',
        help='Use Gabor filters for crack detection (slower but more accurate)'
    )

    parser.add_argument(
        '--export-stats',
        action='store_true',
        help='Export detailed statistics to JSON/CSV'
    )

    return parser.parse_args()


def find_image_files(input_dir: Path):
    """Find all supported image files in directory"""
    supported_extensions = ['.tif', '.tiff', '.png', '.jpg', '.jpeg']
    image_files = []

    for ext in supported_extensions:
        image_files.extend(input_dir.glob(f'*{ext}'))
        image_files.extend(input_dir.glob(f'*{ext.upper()}'))

    return sorted(image_files)


def process_module(
    image_path: Path,
    processor: ELImageProcessor,
    detector: AdvancedDefectDetector,
    report_gen: ELReportGenerator,
    args
):
    """Process a single module"""
    module_id = image_path.stem
    logger.info(f"Processing module: {module_id}")

    try:
        # 1. Process image
        start_time = time.time()
        result = processor.process_image(str(image_path))
        processing_time = time.time() - start_time

        logger.info(f"  Image processing completed in {processing_time:.2f}s")
        logger.info(f"  Detected {len(result.defects)} defects in {result.metadata['total_cells']} cells")

        # 2. Advanced crack detection
        crack_mask, crack_features = detector.detect_cracks_ml(
            result.processed_image,
            use_gabor_filters=args.use_gabor
        )
        logger.info(f"  Detected {len(crack_features)} crack structures")

        # 3. Micro-crack detection
        micro_cracks = detector.detect_micro_cracks(result.processed_image, sensitivity=0.8)
        micro_crack_count = len(micro_cracks[micro_cracks > 0])
        logger.info(f"  Detected {micro_crack_count} micro-crack pixels")

        # 4. Calculate statistics
        statistics = detector.calculate_statistics(
            result.defects,
            result.segmented_cells,
            (args.grid_rows, args.grid_cols)
        )

        logger.info(f"  Total affected area: {statistics.total_affected_area:.2f}%")
        logger.info(f"  Critical cells: {len(statistics.critical_cells)}")
        logger.info(f"  Defect density: {statistics.defect_density:.2f} defects/cell")

        # 5. Generate defect map
        defect_map = detector.generate_defect_map(
            result.original_image,
            result.defects,
            result.cell_boundaries,
            (args.grid_rows, args.grid_cols)
        )

        # 6. Export statistics if requested
        if args.export_stats:
            output_dir = Path(args.output_dir) / module_id
            output_dir.mkdir(parents=True, exist_ok=True)

            detector.export_statistics(
                statistics,
                str(output_dir / 'statistics.json'),
                format='json'
            )
            detector.export_statistics(
                statistics,
                str(output_dir / 'statistics.csv'),
                format='csv'
            )
            detector.export_defects(
                result.defects,
                str(output_dir / 'defects.json')
            )
            logger.info(f"  Statistics exported to {output_dir}")

        # 7. Generate report
        report_path = report_gen.generate_full_report(
            module_id=module_id,
            initial_result=result,
            statistics=statistics
        )

        logger.info(f"  Report generated: {report_path}")

        return {
            'module_id': module_id,
            'success': True,
            'defect_count': len(result.defects),
            'critical_cells': len(statistics.critical_cells),
            'processing_time': processing_time,
            'report_path': report_path
        }

    except Exception as e:
        logger.error(f"  Failed to process {module_id}: {e}")
        return {
            'module_id': module_id,
            'success': False,
            'error': str(e)
        }


def main():
    """Main execution function"""
    args = parse_arguments()

    # Validate input directory
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        sys.exit(1)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find image files
    image_files = find_image_files(input_dir)
    if not image_files:
        logger.error(f"No image files found in {input_dir}")
        sys.exit(1)

    logger.info(f"Found {len(image_files)} image files to process")

    # Initialize components
    logger.info("Initializing image processor...")
    processor = ELImageProcessor(
        cell_size=(156, 156),
        grid_layout=(args.grid_rows, args.grid_cols),
        min_defect_area=args.min_defect_area
    )

    logger.info("Initializing defect detector...")
    detector = AdvancedDefectDetector(
        min_crack_length=20,
        edge_detection_method=args.edge_detection,
        power_loss_model=args.power_loss_model
    )

    logger.info("Initializing report generator...")
    criteria = IEC61215Criteria(
        max_crack_length_mm=50.0,
        max_inactive_area_percent=5.0,
        max_cell_failures=0,
        max_power_loss_percent=5.0,
        max_defect_progression_percent=10.0
    )

    report_gen = ELReportGenerator(
        output_dir=str(output_dir),
        criteria=criteria,
        dpi=150
    )

    # Process all images
    results = []
    total_start = time.time()

    for idx, image_path in enumerate(image_files, 1):
        logger.info(f"\n[{idx}/{len(image_files)}] Processing {image_path.name}")
        result = process_module(image_path, processor, detector, report_gen, args)
        results.append(result)

    total_time = time.time() - total_start

    # Print summary
    logger.info("\n" + "="*80)
    logger.info("BATCH PROCESSING SUMMARY")
    logger.info("="*80)

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    logger.info(f"Total images processed: {len(results)}")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Failed: {len(failed)}")
    logger.info(f"Total processing time: {total_time:.2f}s")

    if successful:
        avg_time = sum(r['processing_time'] for r in successful) / len(successful)
        total_defects = sum(r['defect_count'] for r in successful)
        total_critical = sum(r['critical_cells'] for r in successful)

        logger.info(f"\nAverage processing time: {avg_time:.2f}s per module")
        logger.info(f"Total defects detected: {total_defects}")
        logger.info(f"Total critical cells: {total_critical}")

        logger.info("\nPer-module results:")
        for r in successful:
            logger.info(f"  {r['module_id']}: {r['defect_count']} defects, "
                       f"{r['critical_cells']} critical cells")

    if failed:
        logger.warning(f"\nFailed modules:")
        for r in failed:
            logger.warning(f"  {r['module_id']}: {r['error']}")

    logger.info(f"\nReports saved to: {output_dir}")
    logger.info("="*80)


if __name__ == '__main__':
    main()
