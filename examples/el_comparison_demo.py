#!/usr/bin/env python3
"""
Electroluminescence Before/After Comparison Demo

This script demonstrates comparing EL images before and after stress testing
to track defect progression and module degradation.

Usage:
    python el_comparison_demo.py --before initial.tif --after post_stress.tif --module-id MODULE-001
"""

import argparse
import sys
from pathlib import Path
import logging

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
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Compare EL images before and after stress testing'
    )

    parser.add_argument(
        '--before',
        type=str,
        required=True,
        help='Path to initial/before EL image'
    )

    parser.add_argument(
        '--after',
        type=str,
        required=True,
        help='Path to post-stress/after EL image'
    )

    parser.add_argument(
        '--module-id',
        type=str,
        required=True,
        help='Module identifier'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='./el_comparison_results',
        help='Output directory (default: ./el_comparison_results)'
    )

    parser.add_argument(
        '--grid-rows',
        type=int,
        default=6,
        help='Number of cell rows (default: 6)'
    )

    parser.add_argument(
        '--grid-cols',
        type=int,
        default=10,
        help='Number of cell columns (default: 10)'
    )

    return parser.parse_args()


def main():
    """Main execution function"""
    args = parse_arguments()

    # Validate input files
    before_path = Path(args.before)
    after_path = Path(args.after)

    if not before_path.exists():
        logger.error(f"Before image not found: {before_path}")
        sys.exit(1)

    if not after_path.exists():
        logger.error(f"After image not found: {after_path}")
        sys.exit(1)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("="*80)
    logger.info("EL IMAGE COMPARISON ANALYSIS")
    logger.info("="*80)
    logger.info(f"Module ID: {args.module_id}")
    logger.info(f"Before image: {before_path}")
    logger.info(f"After image: {after_path}")
    logger.info(f"Output directory: {output_dir}")
    logger.info("="*80)

    # Initialize components
    logger.info("\nInitializing image processor...")
    processor = ELImageProcessor(
        cell_size=(156, 156),
        grid_layout=(args.grid_rows, args.grid_cols),
        min_defect_area=50
    )

    logger.info("Initializing defect detector...")
    detector = AdvancedDefectDetector(
        min_crack_length=20,
        edge_detection_method='canny',
        power_loss_model='linear'
    )

    # Process before image
    logger.info("\n" + "-"*80)
    logger.info("PROCESSING INITIAL (BEFORE) IMAGE")
    logger.info("-"*80)

    initial_result = processor.process_image(str(before_path))

    logger.info(f"Detected {len(initial_result.defects)} defects")
    logger.info(f"Defects by type: {initial_result.metadata['defects_by_type']}")
    logger.info(f"Defects by severity: {initial_result.metadata['defects_by_severity']}")

    # Calculate initial statistics
    initial_stats = detector.calculate_statistics(
        initial_result.defects,
        initial_result.segmented_cells,
        (args.grid_rows, args.grid_cols)
    )

    logger.info(f"Total affected area: {initial_stats.total_affected_area:.2f}%")
    logger.info(f"Critical cells: {len(initial_stats.critical_cells)}")
    logger.info(f"Defect density: {initial_stats.defect_density:.2f} defects/cell")

    # Process after image
    logger.info("\n" + "-"*80)
    logger.info("PROCESSING POST-STRESS (AFTER) IMAGE")
    logger.info("-"*80)

    post_stress_result = processor.process_image(str(after_path))

    logger.info(f"Detected {len(post_stress_result.defects)} defects")
    logger.info(f"Defects by type: {post_stress_result.metadata['defects_by_type']}")
    logger.info(f"Defects by severity: {post_stress_result.metadata['defects_by_severity']}")

    # Calculate post-stress statistics
    post_stress_stats = detector.calculate_statistics(
        post_stress_result.defects,
        post_stress_result.segmented_cells,
        (args.grid_rows, args.grid_cols)
    )

    logger.info(f"Total affected area: {post_stress_stats.total_affected_area:.2f}%")
    logger.info(f"Critical cells: {len(post_stress_stats.critical_cells)}")
    logger.info(f"Defect density: {post_stress_stats.defect_density:.2f} defects/cell")

    # Compare images
    logger.info("\n" + "-"*80)
    logger.info("COMPARISON ANALYSIS")
    logger.info("-"*80)

    comparison_data = processor.compare_images(
        initial_result.original_image,
        post_stress_result.original_image,
        initial_result.defects,
        post_stress_result.defects
    )

    logger.info(f"New defects detected: {comparison_data['new_defects']}")
    logger.info(f"Defect increase rate: {comparison_data['defect_increase_rate']:.1f}%")
    logger.info(f"Mean image difference: {comparison_data['mean_difference']:.2f}")
    logger.info(f"Affected area increase: {comparison_data['area_increase']:.2f}%")

    # Calculate progression metrics
    progression = processor.calculate_defect_progression(
        initial_result.defects,
        post_stress_result.defects
    )

    logger.info(f"\nDefect progression by type:")
    for defect_type, change in progression['type_progression'].items():
        if change != 0:
            sign = "+" if change > 0 else ""
            logger.info(f"  {defect_type}: {sign}{change}")

    logger.info(f"\nCritical defects increase: {progression['critical_defects_increase']}")
    logger.info(f"High severity defects increase: {progression['high_severity_increase']}")

    # Power loss analysis
    logger.info("\n" + "-"*80)
    logger.info("POWER LOSS ANALYSIS")
    logger.info("-"*80)

    # Find cells with significant power loss increase
    initial_power_loss = {p.cell_id: p.estimated_power_loss
                         for p in initial_stats.power_loss_estimates}
    post_stress_power_loss = {p.cell_id: p.estimated_power_loss
                             for p in post_stress_stats.power_loss_estimates}

    logger.info("\nCells with significant power loss increase (>2%):")
    significant_changes = []

    for cell_id in initial_power_loss.keys():
        initial_loss = initial_power_loss.get(cell_id, 0)
        post_loss = post_stress_power_loss.get(cell_id, 0)
        difference = post_loss - initial_loss

        if difference > 2.0:
            significant_changes.append((cell_id, initial_loss, post_loss, difference))

    if significant_changes:
        for cell_id, initial_loss, post_loss, difference in sorted(
            significant_changes, key=lambda x: x[3], reverse=True
        ):
            logger.info(f"  Cell {cell_id}: {initial_loss:.2f}% → {post_loss:.2f}% "
                       f"(+{difference:.2f}%)")
    else:
        logger.info("  No significant power loss increases detected")

    # IEC 61215 compliance check
    logger.info("\n" + "-"*80)
    logger.info("IEC 61215 COMPLIANCE CHECK")
    logger.info("-"*80)

    criteria = IEC61215Criteria()

    # Check defect progression
    progression_pass = comparison_data['defect_increase_rate'] <= criteria.max_defect_progression_percent
    logger.info(f"Defect progression: {comparison_data['defect_increase_rate']:.1f}% "
               f"(limit: {criteria.max_defect_progression_percent}%) "
               f"{'✓ PASS' if progression_pass else '✗ FAIL'}")

    # Check inactive area
    area_pass = post_stress_stats.total_affected_area <= criteria.max_inactive_area_percent
    logger.info(f"Inactive area: {post_stress_stats.total_affected_area:.2f}% "
               f"(limit: {criteria.max_inactive_area_percent}%) "
               f"{'✓ PASS' if area_pass else '✗ FAIL'}")

    # Check maximum power loss
    max_power_loss = max([p.estimated_power_loss for p in post_stress_stats.power_loss_estimates])
    power_loss_pass = max_power_loss <= criteria.max_power_loss_percent
    logger.info(f"Maximum power loss: {max_power_loss:.2f}% "
               f"(limit: {criteria.max_power_loss_percent}%) "
               f"{'✓ PASS' if power_loss_pass else '✗ FAIL'}")

    overall_pass = progression_pass and area_pass and power_loss_pass
    logger.info(f"\nOverall result: {'✓ PASS' if overall_pass else '✗ FAIL'}")

    # Generate comprehensive report
    logger.info("\n" + "-"*80)
    logger.info("GENERATING COMPREHENSIVE REPORT")
    logger.info("-"*80)

    report_gen = ELReportGenerator(
        output_dir=str(output_dir),
        criteria=criteria,
        dpi=150
    )

    report_path = report_gen.generate_full_report(
        module_id=args.module_id,
        initial_result=initial_result,
        post_stress_result=post_stress_result,
        statistics=post_stress_stats,
        comparison_data=comparison_data
    )

    logger.info(f"Report generated: {report_path}")

    # Export detailed statistics
    stats_dir = output_dir / f"{args.module_id}_{detector.__class__.__name__}"
    stats_dir.mkdir(parents=True, exist_ok=True)

    detector.export_statistics(
        initial_stats,
        str(stats_dir / 'initial_statistics.json'),
        format='json'
    )

    detector.export_statistics(
        post_stress_stats,
        str(stats_dir / 'post_stress_statistics.json'),
        format='json'
    )

    logger.info(f"Statistics exported to: {stats_dir}")

    # Summary
    logger.info("\n" + "="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    logger.info(f"Initial defects: {len(initial_result.defects)}")
    logger.info(f"Post-stress defects: {len(post_stress_result.defects)}")
    logger.info(f"New defects: {comparison_data['new_defects']} "
               f"({comparison_data['defect_increase_rate']:.1f}% increase)")
    logger.info(f"Compliance status: {'PASS' if overall_pass else 'FAIL'}")
    logger.info(f"\nAll results saved to: {output_dir}")
    logger.info("="*80)


if __name__ == '__main__':
    main()
