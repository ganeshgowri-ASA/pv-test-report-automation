"""
Electroluminescence (EL) Test Report Generation Module

Generate comprehensive EL test reports with:
- EL test report sections with images
- Defect summary tables
- Pass/fail criteria per IEC 61215 MST sequence
- Comparison charts (initial vs post-stress)

Author: PV Test Automation System
License: MIT
"""

import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import numpy as np
import cv2
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import logging

from .image_processor import ProcessingResult, Defect, DefectType, DefectSeverity
from .defect_detector import DefectStatistics, PowerLossEstimate

logger = logging.getLogger(__name__)


@dataclass
class IEC61215Criteria:
    """IEC 61215 MST sequence pass/fail criteria"""
    max_crack_length_mm: float = 50.0
    max_inactive_area_percent: float = 5.0
    max_cell_failures: int = 0
    max_power_loss_percent: float = 5.0
    max_defect_progression_percent: float = 10.0


@dataclass
class TestResult:
    """Overall test result"""
    passed: bool
    criteria: IEC61215Criteria
    failures: List[str]
    warnings: List[str]
    score: float  # 0-100


class ELReportGenerator:
    """
    Generate comprehensive electroluminescence test reports
    """

    def __init__(self,
                 output_dir: str = "./el_reports",
                 criteria: Optional[IEC61215Criteria] = None,
                 dpi: int = 150):
        """
        Initialize the report generator

        Args:
            output_dir: Directory for output reports
            criteria: IEC 61215 criteria (uses defaults if None)
            dpi: DPI for generated images
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.criteria = criteria or IEC61215Criteria()
        self.dpi = dpi

        logger.info(f"ELReportGenerator initialized with output dir: {output_dir}")

    def generate_full_report(self,
                           module_id: str,
                           initial_result: ProcessingResult,
                           post_stress_result: Optional[ProcessingResult] = None,
                           statistics: Optional[DefectStatistics] = None,
                           comparison_data: Optional[Dict] = None) -> str:
        """
        Generate complete EL test report

        Args:
            module_id: Module identifier
            initial_result: Initial EL processing result
            post_stress_result: Post-stress EL processing result (optional)
            statistics: Defect statistics (optional)
            comparison_data: Comparison data from image_processor (optional)

        Returns:
            Path to generated HTML report
        """
        logger.info(f"Generating full report for module {module_id}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = self.output_dir / f"{module_id}_{timestamp}"
        report_dir.mkdir(parents=True, exist_ok=True)

        # Generate visualizations
        images_dir = report_dir / "images"
        images_dir.mkdir(exist_ok=True)

        # Save annotated images
        initial_annotated_path = self._save_annotated_image(
            initial_result, images_dir, "initial_annotated.png"
        )

        post_stress_annotated_path = None
        if post_stress_result is not None:
            post_stress_annotated_path = self._save_annotated_image(
                post_stress_result, images_dir, "post_stress_annotated.png"
            )

        # Generate comparison charts
        comparison_chart_path = None
        if comparison_data is not None:
            comparison_chart_path = self._generate_comparison_charts(
                comparison_data, images_dir, module_id
            )

        # Generate defect distribution charts
        defect_chart_path = self._generate_defect_charts(
            initial_result.defects,
            post_stress_result.defects if post_stress_result else None,
            images_dir
        )

        # Generate power loss chart
        power_loss_chart_path = None
        if statistics is not None:
            power_loss_chart_path = self._generate_power_loss_chart(
                statistics.power_loss_estimates, images_dir
            )

        # Evaluate pass/fail criteria
        test_result = self._evaluate_criteria(
            initial_result,
            post_stress_result,
            statistics,
            comparison_data
        )

        # Generate HTML report
        html_path = report_dir / "report.html"
        self._generate_html_report(
            html_path,
            module_id,
            initial_result,
            post_stress_result,
            statistics,
            comparison_data,
            test_result,
            initial_annotated_path,
            post_stress_annotated_path,
            comparison_chart_path,
            defect_chart_path,
            power_loss_chart_path
        )

        logger.info(f"Report generated: {html_path}")
        return str(html_path)

    def _save_annotated_image(self,
                             result: ProcessingResult,
                             output_dir: Path,
                             filename: str) -> Path:
        """Save annotated image to file"""
        from .image_processor import ELImageProcessor

        processor = ELImageProcessor()
        annotated = processor.generate_annotated_image(
            result.original_image,
            result.defects,
            result.cell_boundaries
        )

        output_path = output_dir / filename
        cv2.imwrite(str(output_path), annotated)

        return output_path

    def _generate_comparison_charts(self,
                                   comparison_data: Dict,
                                   output_dir: Path,
                                   module_id: str) -> Path:
        """
        Generate before/after comparison charts

        Args:
            comparison_data: Comparison data dictionary
            output_dir: Output directory
            module_id: Module identifier

        Returns:
            Path to generated chart
        """
        fig = plt.figure(figsize=(14, 10))
        gs = GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.3)

        # Chart 1: Defect count comparison
        ax1 = fig.add_subplot(gs[0, 0])
        categories = ['Before', 'After']
        counts = [
            comparison_data['before_defect_count'],
            comparison_data['after_defect_count']
        ]
        bars = ax1.bar(categories, counts, color=['#4CAF50', '#f44336'])
        ax1.set_ylabel('Number of Defects')
        ax1.set_title('Total Defect Count Comparison')
        ax1.grid(True, alpha=0.3)

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom')

        # Chart 2: Affected area comparison
        ax2 = fig.add_subplot(gs[0, 1])
        areas = [
            comparison_data['before_affected_area'],
            comparison_data['after_affected_area']
        ]
        bars = ax2.bar(categories, areas, color=['#4CAF50', '#f44336'])
        ax2.set_ylabel('Affected Area (%)')
        ax2.set_title('Total Affected Area Comparison')
        ax2.grid(True, alpha=0.3)

        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}%',
                    ha='center', va='bottom')

        # Chart 3: Defects by type comparison
        ax3 = fig.add_subplot(gs[1, :])
        before_types = comparison_data['before_defects_by_type']
        after_types = comparison_data['after_defects_by_type']

        all_types = sorted(set(list(before_types.keys()) + list(after_types.keys())))
        before_counts = [before_types.get(t, 0) for t in all_types]
        after_counts = [after_types.get(t, 0) for t in all_types]

        x = np.arange(len(all_types))
        width = 0.35

        ax3.bar(x - width/2, before_counts, width, label='Before', color='#4CAF50')
        ax3.bar(x + width/2, after_counts, width, label='After', color='#f44336')

        ax3.set_xlabel('Defect Type')
        ax3.set_ylabel('Count')
        ax3.set_title('Defect Distribution by Type')
        ax3.set_xticks(x)
        ax3.set_xticklabels(all_types, rotation=45, ha='right')
        ax3.legend()
        ax3.grid(True, alpha=0.3, axis='y')

        # Chart 4: Image difference statistics
        ax4 = fig.add_subplot(gs[2, 0])
        metrics = ['Mean Difference', 'Max Difference', 'Area Increase (%)']
        values = [
            comparison_data['mean_difference'],
            comparison_data['max_difference'] / 2.55,  # Normalize to 0-100
            comparison_data['area_increase']
        ]
        colors = ['#2196F3', '#FF9800', '#9C27B0']
        bars = ax4.barh(metrics, values, color=colors)
        ax4.set_xlabel('Value')
        ax4.set_title('Image Difference Metrics')
        ax4.grid(True, alpha=0.3, axis='x')

        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax4.text(width, bar.get_y() + bar.get_height()/2.,
                    f'{values[i]:.2f}',
                    ha='left', va='center', fontsize=9)

        # Chart 5: Defect progression rate
        ax5 = fig.add_subplot(gs[2, 1])
        progression_rate = comparison_data['defect_increase_rate']

        # Create a gauge-style chart
        colors_gauge = ['#4CAF50', '#FFC107', '#FF5722']
        thresholds = [0, 10, 25, 100]

        if progression_rate < thresholds[1]:
            color = colors_gauge[0]
            status = 'Good'
        elif progression_rate < thresholds[2]:
            color = colors_gauge[1]
            status = 'Warning'
        else:
            color = colors_gauge[2]
            status = 'Critical'

        ax5.barh(['Progression Rate'], [progression_rate], color=color)
        ax5.set_xlim(0, 50)
        ax5.set_xlabel('Increase Rate (%)')
        ax5.set_title(f'Defect Progression Rate: {status}')
        ax5.text(progression_rate + 1, 0, f'{progression_rate:.1f}%',
                va='center', fontsize=12, fontweight='bold')
        ax5.grid(True, alpha=0.3, axis='x')

        # Add threshold markers
        for i, threshold in enumerate(thresholds[1:-1], 1):
            ax5.axvline(x=threshold, color='gray', linestyle='--', alpha=0.5)

        plt.suptitle(f'EL Test Comparison - Module {module_id}', fontsize=14, fontweight='bold')

        output_path = output_dir / "comparison_charts.png"
        plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()

        return output_path

    def _generate_defect_charts(self,
                               initial_defects: List[Defect],
                               post_stress_defects: Optional[List[Defect]],
                               output_dir: Path) -> Path:
        """Generate defect distribution charts"""

        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Defect Analysis', fontsize=14, fontweight='bold')

        # Chart 1: Defect type distribution (initial)
        ax1 = axes[0, 0]
        type_counts = {}
        for defect in initial_defects:
            type_name = defect.defect_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        if type_counts:
            colors_pie = plt.cm.Set3(range(len(type_counts)))
            ax1.pie(type_counts.values(), labels=type_counts.keys(),
                   autopct='%1.1f%%', colors=colors_pie, startangle=90)
            ax1.set_title('Initial Defect Type Distribution')
        else:
            ax1.text(0.5, 0.5, 'No defects detected',
                    ha='center', va='center', transform=ax1.transAxes)
            ax1.set_title('Initial Defect Type Distribution')

        # Chart 2: Defect severity distribution (initial)
        ax2 = axes[0, 1]
        severity_counts = {}
        for defect in initial_defects:
            severity_name = defect.severity.value
            severity_counts[severity_name] = severity_counts.get(severity_name, 0) + 1

        severity_order = ['low', 'medium', 'high', 'critical']
        severity_labels = [s.capitalize() for s in severity_order]
        severity_values = [severity_counts.get(s, 0) for s in severity_order]
        severity_colors = ['#4CAF50', '#FFC107', '#FF9800', '#f44336']

        bars = ax2.bar(severity_labels, severity_values, color=severity_colors)
        ax2.set_ylabel('Count')
        ax2.set_title('Initial Defect Severity Distribution')
        ax2.grid(True, alpha=0.3, axis='y')

        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}',
                        ha='center', va='bottom')

        # Chart 3: Defect size distribution
        ax3 = axes[1, 0]
        defect_sizes = [d.area_pixels for d in initial_defects]

        if defect_sizes:
            ax3.hist(defect_sizes, bins=20, color='#2196F3', edgecolor='black', alpha=0.7)
            ax3.set_xlabel('Defect Size (pixels)')
            ax3.set_ylabel('Frequency')
            ax3.set_title('Defect Size Distribution')
            ax3.grid(True, alpha=0.3, axis='y')
        else:
            ax3.text(0.5, 0.5, 'No defects detected',
                    ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('Defect Size Distribution')

        # Chart 4: Post-stress comparison (if available)
        ax4 = axes[1, 1]
        if post_stress_defects is not None:
            categories = ['Initial', 'Post-Stress']
            total_counts = [len(initial_defects), len(post_stress_defects)]
            bars = ax4.bar(categories, total_counts, color=['#4CAF50', '#f44336'])
            ax4.set_ylabel('Total Defect Count')
            ax4.set_title('Before/After Stress Test')
            ax4.grid(True, alpha=0.3, axis='y')

            for bar in bars:
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}',
                        ha='center', va='bottom')
        else:
            ax4.text(0.5, 0.5, 'Post-stress data not available',
                    ha='center', va='center', transform=ax4.transAxes)
            ax4.set_title('Before/After Stress Test')

        plt.tight_layout()

        output_path = output_dir / "defect_charts.png"
        plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()

        return output_path

    def _generate_power_loss_chart(self,
                                  power_estimates: List[PowerLossEstimate],
                                  output_dir: Path) -> Path:
        """Generate power loss estimation chart"""

        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        fig.suptitle('Cell Power Loss Analysis', fontsize=14, fontweight='bold')

        # Extract data
        cell_ids = [p.cell_id for p in power_estimates]
        power_losses = [p.estimated_power_loss for p in power_estimates]
        intensities = [p.normalized_intensity for p in power_estimates]

        # Chart 1: Power loss per cell
        ax1 = axes[0]
        colors = ['#f44336' if p > 5 else '#FFC107' if p > 2 else '#4CAF50'
                 for p in power_losses]

        bars = ax1.bar(cell_ids, power_losses, color=colors)
        ax1.set_xlabel('Cell ID')
        ax1.set_ylabel('Estimated Power Loss (%)')
        ax1.set_title('Power Loss by Cell')
        ax1.axhline(y=5, color='red', linestyle='--', alpha=0.5, label='5% Threshold')
        ax1.axhline(y=2, color='orange', linestyle='--', alpha=0.5, label='2% Warning')
        ax1.legend()
        ax1.grid(True, alpha=0.3, axis='y')

        # Chart 2: Normalized intensity per cell
        ax2 = axes[1]
        colors_intensity = ['#f44336' if i < 0.8 else '#FFC107' if i < 0.9 else '#4CAF50'
                          for i in intensities]

        ax2.bar(cell_ids, intensities, color=colors_intensity)
        ax2.set_xlabel('Cell ID')
        ax2.set_ylabel('Normalized Intensity')
        ax2.set_title('Cell Intensity (Normalized to Reference)')
        ax2.axhline(y=0.9, color='orange', linestyle='--', alpha=0.5, label='90% Warning')
        ax2.axhline(y=0.8, color='red', linestyle='--', alpha=0.5, label='80% Critical')
        ax2.set_ylim(0, 1.1)
        ax2.legend()
        ax2.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()

        output_path = output_dir / "power_loss_chart.png"
        plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()

        return output_path

    def _evaluate_criteria(self,
                          initial_result: ProcessingResult,
                          post_stress_result: Optional[ProcessingResult],
                          statistics: Optional[DefectStatistics],
                          comparison_data: Optional[Dict]) -> TestResult:
        """
        Evaluate pass/fail criteria per IEC 61215

        Args:
            initial_result: Initial processing result
            post_stress_result: Post-stress processing result
            statistics: Defect statistics
            comparison_data: Comparison data

        Returns:
            TestResult object
        """
        failures = []
        warnings = []
        score = 100.0

        # Check for broken cells (critical defects)
        broken_cells = [d for d in initial_result.defects
                       if d.defect_type == DefectType.BROKEN_CELL]

        if len(broken_cells) > self.criteria.max_cell_failures:
            failures.append(f"Broken cells detected: {len(broken_cells)} "
                          f"(max allowed: {self.criteria.max_cell_failures})")
            score -= 30

        # Check inactive area
        if statistics:
            if statistics.total_affected_area > self.criteria.max_inactive_area_percent:
                failures.append(f"Total affected area: {statistics.total_affected_area:.2f}% "
                              f"(max allowed: {self.criteria.max_inactive_area_percent}%)")
                score -= 20

        # Check power loss
        if statistics:
            critical_power_loss = [p for p in statistics.power_loss_estimates
                                 if p.estimated_power_loss > self.criteria.max_power_loss_percent]
            if critical_power_loss:
                failures.append(f"High power loss detected in {len(critical_power_loss)} cells "
                              f"(threshold: {self.criteria.max_power_loss_percent}%)")
                score -= 15

        # Check defect progression (if post-stress data available)
        if comparison_data:
            progression_rate = comparison_data['defect_increase_rate']
            if progression_rate > self.criteria.max_defect_progression_percent:
                failures.append(f"Defect progression rate: {progression_rate:.1f}% "
                              f"(max allowed: {self.criteria.max_defect_progression_percent}%)")
                score -= 20

        # Check for critical severity defects
        critical_defects = [d for d in initial_result.defects
                          if d.severity == DefectSeverity.CRITICAL]

        if critical_defects:
            warnings.append(f"{len(critical_defects)} critical severity defects detected")
            score -= 5

        # Check for cracks
        cracks = [d for d in initial_result.defects
                 if d.defect_type in [DefectType.CRACK, DefectType.MICRO_CRACK]]

        if len(cracks) > 5:
            warnings.append(f"Multiple cracks detected: {len(cracks)}")
            score -= 10

        # Ensure score doesn't go below 0
        score = max(0, score)

        passed = len(failures) == 0

        return TestResult(
            passed=passed,
            criteria=self.criteria,
            failures=failures,
            warnings=warnings,
            score=score
        )

    def _generate_html_report(self,
                            output_path: Path,
                            module_id: str,
                            initial_result: ProcessingResult,
                            post_stress_result: Optional[ProcessingResult],
                            statistics: Optional[DefectStatistics],
                            comparison_data: Optional[Dict],
                            test_result: TestResult,
                            initial_image_path: Path,
                            post_stress_image_path: Optional[Path],
                            comparison_chart_path: Optional[Path],
                            defect_chart_path: Path,
                            power_loss_chart_path: Optional[Path]) -> None:
        """Generate HTML report"""

        # Create relative paths for images
        def rel_path(p: Path) -> str:
            return p.relative_to(output_path.parent).as_posix()

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EL Test Report - {module_id}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #2196F3;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
            border-bottom: 2px solid #ddd;
            padding-bottom: 5px;
        }}
        h3 {{
            color: #666;
            margin-top: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            margin: -30px -30px 30px -30px;
            border-radius: 5px 5px 0 0;
        }}
        .header h1 {{
            margin: 0;
            color: white;
            border: none;
        }}
        .status-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            margin-left: 10px;
        }}
        .status-pass {{
            background-color: #4CAF50;
            color: white;
        }}
        .status-fail {{
            background-color: #f44336;
            color: white;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .info-card {{
            background-color: #f9f9f9;
            padding: 15px;
            border-left: 4px solid #2196F3;
            border-radius: 4px;
        }}
        .info-card h4 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        .info-card p {{
            margin: 5px 0;
            color: #666;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #2196F3;
            color: white;
            font-weight: bold;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .image-container {{
            margin: 20px 0;
            text-align: center;
        }}
        .image-container img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .image-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .alert {{
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        .alert-danger {{
            background-color: #ffebee;
            border-left: 4px solid #f44336;
            color: #c62828;
        }}
        .alert-warning {{
            background-color: #fff3e0;
            border-left: 4px solid #ff9800;
            color: #e65100;
        }}
        .alert-success {{
            background-color: #e8f5e9;
            border-left: 4px solid #4CAF50;
            color: #2e7d32;
        }}
        .score {{
            font-size: 48px;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
        }}
        .score-good {{ color: #4CAF50; }}
        .score-warning {{ color: #ff9800; }}
        .score-bad {{ color: #f44336; }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #999;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Electroluminescence Test Report</h1>
            <p>Module ID: {module_id}</p>
            <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <span class="status-badge {'status-pass' if test_result.passed else 'status-fail'}">
                {'PASS' if test_result.passed else 'FAIL'}
            </span>
        </div>

        <h2>Test Summary</h2>
        <div class="score {'score-good' if test_result.score >= 80 else 'score-warning' if test_result.score >= 60 else 'score-bad'}">
            Score: {test_result.score:.1f}/100
        </div>

        <div class="info-grid">
            <div class="info-card">
                <h4>Total Defects (Initial)</h4>
                <p>{len(initial_result.defects)}</p>
            </div>
            <div class="info-card">
                <h4>Total Cells Analyzed</h4>
                <p>{initial_result.metadata['total_cells']}</p>
            </div>
"""

        if statistics:
            html_content += f"""
            <div class="info-card">
                <h4>Critical Cells</h4>
                <p>{len(statistics.critical_cells)}</p>
            </div>
            <div class="info-card">
                <h4>Defect Density</h4>
                <p>{statistics.defect_density:.2f} defects/cell</p>
            </div>
"""

        if comparison_data:
            html_content += f"""
            <div class="info-card">
                <h4>Defect Progression</h4>
                <p>{comparison_data['new_defects']} new defects ({comparison_data['defect_increase_rate']:.1f}%)</p>
            </div>
"""

        html_content += """
        </div>
"""

        # Pass/Fail Criteria Results
        if test_result.failures:
            html_content += """
        <h2>Failures</h2>
"""
            for failure in test_result.failures:
                html_content += f"""
        <div class="alert alert-danger">
            <strong>FAIL:</strong> {failure}
        </div>
"""

        if test_result.warnings:
            html_content += """
        <h2>Warnings</h2>
"""
            for warning in test_result.warnings:
                html_content += f"""
        <div class="alert alert-warning">
            <strong>WARNING:</strong> {warning}
        </div>
"""

        if not test_result.failures and not test_result.warnings:
            html_content += """
        <div class="alert alert-success">
            <strong>SUCCESS:</strong> Module passed all IEC 61215 criteria with no warnings.
        </div>
"""

        # IEC 61215 Criteria
        html_content += f"""
        <h2>IEC 61215 MST Sequence Criteria</h2>
        <table>
            <tr>
                <th>Criterion</th>
                <th>Limit</th>
                <th>Actual</th>
                <th>Status</th>
            </tr>
            <tr>
                <td>Maximum Cell Failures</td>
                <td>{self.criteria.max_cell_failures}</td>
                <td>{len([d for d in initial_result.defects if d.defect_type == DefectType.BROKEN_CELL])}</td>
                <td>{'✓ PASS' if len([d for d in initial_result.defects if d.defect_type == DefectType.BROKEN_CELL]) <= self.criteria.max_cell_failures else '✗ FAIL'}</td>
            </tr>
"""

        if statistics:
            html_content += f"""
            <tr>
                <td>Maximum Inactive Area</td>
                <td>{self.criteria.max_inactive_area_percent}%</td>
                <td>{statistics.total_affected_area:.2f}%</td>
                <td>{'✓ PASS' if statistics.total_affected_area <= self.criteria.max_inactive_area_percent else '✗ FAIL'}</td>
            </tr>
            <tr>
                <td>Maximum Power Loss</td>
                <td>{self.criteria.max_power_loss_percent}%</td>
                <td>{max([p.estimated_power_loss for p in statistics.power_loss_estimates]) if statistics.power_loss_estimates else 0:.2f}%</td>
                <td>{'✓ PASS' if max([p.estimated_power_loss for p in statistics.power_loss_estimates]) if statistics.power_loss_estimates else 0 <= self.criteria.max_power_loss_percent else '✗ FAIL'}</td>
            </tr>
"""

        if comparison_data:
            html_content += f"""
            <tr>
                <td>Maximum Defect Progression</td>
                <td>{self.criteria.max_defect_progression_percent}%</td>
                <td>{comparison_data['defect_increase_rate']:.1f}%</td>
                <td>{'✓ PASS' if comparison_data['defect_increase_rate'] <= self.criteria.max_defect_progression_percent else '✗ FAIL'}</td>
            </tr>
"""

        html_content += """
        </table>
"""

        # Defect Summary Table
        html_content += """
        <h2>Defect Summary</h2>
        <table>
            <tr>
                <th>Defect Type</th>
                <th>Count</th>
                <th>Percentage</th>
            </tr>
"""

        defects_by_type = initial_result.metadata['defects_by_type']
        total_defects = len(initial_result.defects)

        for defect_type, count in sorted(defects_by_type.items()):
            percentage = (count / total_defects * 100) if total_defects > 0 else 0
            html_content += f"""
            <tr>
                <td>{defect_type.replace('_', ' ').title()}</td>
                <td>{count}</td>
                <td>{percentage:.1f}%</td>
            </tr>
"""

        html_content += """
        </table>
"""

        # Annotated Images
        html_content += """
        <h2>EL Images</h2>
        <div class="image-grid">
"""

        html_content += f"""
            <div class="image-container">
                <h3>Initial EL Image (Annotated)</h3>
                <img src="{rel_path(initial_image_path)}" alt="Initial EL Image">
            </div>
"""

        if post_stress_image_path:
            html_content += f"""
            <div class="image-container">
                <h3>Post-Stress EL Image (Annotated)</h3>
                <img src="{rel_path(post_stress_image_path)}" alt="Post-Stress EL Image">
            </div>
"""

        html_content += """
        </div>
"""

        # Comparison Charts
        if comparison_chart_path:
            html_content += f"""
        <h2>Before/After Comparison</h2>
        <div class="image-container">
            <img src="{rel_path(comparison_chart_path)}" alt="Comparison Charts">
        </div>
"""

        # Defect Charts
        html_content += f"""
        <h2>Defect Analysis</h2>
        <div class="image-container">
            <img src="{rel_path(defect_chart_path)}" alt="Defect Charts">
        </div>
"""

        # Power Loss Charts
        if power_loss_chart_path:
            html_content += f"""
        <h2>Power Loss Analysis</h2>
        <div class="image-container">
            <img src="{rel_path(power_loss_chart_path)}" alt="Power Loss Charts">
        </div>
"""

        # Footer
        html_content += """
        <div class="footer">
            <p>PV Test Report Automation System</p>
            <p>Electroluminescence Testing Module</p>
        </div>
    </div>
</body>
</html>
"""

        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"HTML report generated: {output_path}")

    def generate_summary_table(self, defects: List[Defect]) -> str:
        """
        Generate defect summary table in markdown format

        Args:
            defects: List of defects

        Returns:
            Markdown table string
        """
        # Count by type
        type_counts = {}
        for defect in defects:
            type_name = defect.defect_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        # Count by severity
        severity_counts = {}
        for defect in defects:
            severity_name = defect.severity.value
            severity_counts[severity_name] = severity_counts.get(severity_name, 0) + 1

        # Build markdown table
        table = "## Defect Summary\n\n"
        table += "### By Type\n\n"
        table += "| Defect Type | Count |\n"
        table += "|------------|-------|\n"

        for defect_type, count in sorted(type_counts.items()):
            table += f"| {defect_type.replace('_', ' ').title()} | {count} |\n"

        table += "\n### By Severity\n\n"
        table += "| Severity | Count |\n"
        table += "|----------|-------|\n"

        severity_order = ['critical', 'high', 'medium', 'low']
        for severity in severity_order:
            count = severity_counts.get(severity, 0)
            table += f"| {severity.title()} | {count} |\n"

        return table
