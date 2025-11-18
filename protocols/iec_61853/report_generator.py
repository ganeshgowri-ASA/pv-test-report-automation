"""
IEC 61853 Report Generator
===========================

Generates comprehensive test reports with:
- Executive summary
- Performance matrix tables (7x5 grid)
- Temperature coefficient summary
- 3D performance surface plots
- Spectral response curves
- Angular response plots
- Energy rating comparison charts
- Compliance statements
- ISO 17025 traceability

Output formats:
- PDF (primary)
- HTML (interactive)
- JSON (data export)
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
import io


# Configure logging
logger = logging.getLogger(__name__)


# ==================== Report Generator ====================

class IEC61853ReportGenerator:
    """
    Comprehensive report generator for IEC 61853 test results

    Generates professional test reports with plots, tables, and analysis.
    """

    def __init__(
        self,
        test_id: str,
        module: Any,  # ModuleUnderTest
        test_lab: str,
        test_results: Any,  # TestResults
        test_engineer: Optional[str] = None
    ):
        self.test_id = test_id
        self.module = module
        self.test_lab = test_lab
        self.test_results = test_results
        self.test_engineer = test_engineer or "Auto"

        logger.info(f"Report generator initialized for test {test_id}")

    def generate_pdf_report(self, output_path: str):
        """
        Generate PDF report

        Note: Full PDF generation requires reportlab or similar.
        This implementation creates plots and data structures.
        For production, integrate with reportlab/weasyprint.
        """
        logger.info(f"Generating PDF report: {output_path}")

        # Generate all plots
        plots = self._generate_all_plots()

        # Compile report data
        report_data = self._compile_report_data()

        # For now, export as JSON with plot references
        # In production, use reportlab to create PDF
        output_json = output_path.replace('.pdf', '_data.json')

        import json
        with open(output_json, 'w') as f:
            json.dump(report_data, f, indent=2)

        logger.info(f"Report data exported to {output_json}")
        logger.info(f"Plot files generated in same directory")
        logger.info("Note: Full PDF generation requires reportlab integration")

    def generate_html_report(self, output_path: str):
        """Generate interactive HTML report"""
        logger.info(f"Generating HTML report: {output_path}")

        html_content = self._create_html_report()

        with open(output_path, 'w') as f:
            f.write(html_content)

        logger.info(f"HTML report generated: {output_path}")

    def _compile_report_data(self) -> Dict[str, Any]:
        """Compile all report data into structured format"""
        report = {
            "report_metadata": {
                "test_id": self.test_id,
                "generation_date": datetime.utcnow().isoformat(),
                "standard": "IEC 61853:2011 series",
                "test_lab": self.test_lab,
                "test_engineer": self.test_engineer,
            },
            "module_information": {
                "serial_number": self.module.serial_number,
                "manufacturer": self.module.manufacturer,
                "model": self.module.model,
                "technology": self.module.technology,
                "rated_power_w": self.module.rated_power,
            },
            "test_summary": {},
            "performance_matrix": {},
            "temperature_coefficients": {},
            "spectral_response": {},
            "energy_ratings": {},
            "quality_metrics": {},
        }

        # Add matrix results
        if self.test_results and self.test_results.matrix_results:
            mr = self.test_results.matrix_results
            report["test_summary"]["matrix"] = {
                "total_points": mr.total_points,
                "successful_points": mr.successful_points,
                "failed_points": mr.failed_points,
                "duration_hours": mr.total_duration / 3600,
                "start_time": mr.start_time.isoformat(),
                "end_time": mr.end_time.isoformat(),
            }

            # Performance matrix table
            report["performance_matrix"] = self._create_performance_matrix_table()

        # Add temperature coefficients
        if self.test_results and self.test_results.temperature_coefficients:
            tc = self.test_results.temperature_coefficients
            report["temperature_coefficients"] = {
                "alpha_isc_pct_per_c": tc.alpha_isc,
                "beta_voc_pct_per_c": tc.beta_voc,
                "gamma_pmax_pct_per_c": tc.gamma_pmax,
                "alpha_isc_abs": tc.alpha_isc_abs,
                "beta_voc_abs": tc.beta_voc_abs,
                "gamma_pmax_abs": tc.gamma_pmax_abs,
                "reference_temperature_c": tc.reference_temperature,
                "reference_irradiance_wm2": tc.reference_irradiance,
            }

        # Add spectral data
        if self.test_results and self.test_results.spectral_data:
            report["spectral_response"] = self.test_results.spectral_data

        # Add energy ratings
        if self.test_results and self.test_results.energy_ratings:
            report["energy_ratings"] = self.test_results.energy_ratings

        # Add quality metrics
        if self.test_results and self.test_results.quality_metrics:
            report["quality_metrics"] = self.test_results.quality_metrics

        return report

    def _create_performance_matrix_table(self) -> Dict[str, Any]:
        """Create 7x5 performance matrix table"""
        if not self.test_results or not self.test_results.matrix_results:
            return {}

        matrix_data = {
            "temperatures": [],
            "irradiances": [],
            "pmax_grid": [],
            "voc_grid": [],
            "isc_grid": [],
            "ff_grid": [],
        }

        # Get unique temperatures and irradiances
        test_points = self.test_results.matrix_results.test_points
        temps = sorted(set(p.temperature for p in test_points))
        irrads = sorted(set(p.irradiance for p in test_points))

        matrix_data["temperatures"] = temps
        matrix_data["irradiances"] = irrads

        # Create grids
        for param in ["pmax", "voc", "isc", "ff"]:
            grid = []
            for temp in temps:
                row = []
                for irrad in irrads:
                    # Find matching point
                    point = next(
                        (p for p in test_points
                         if abs(p.temperature - temp) < 0.1 and abs(p.irradiance - irrad) < 1),
                        None
                    )
                    if point and point.data:
                        value = getattr(point.data.iv_curve, param)
                        row.append(float(value))
                    else:
                        row.append(None)
                grid.append(row)
            matrix_data[f"{param}_grid"] = grid

        return matrix_data

    def _generate_all_plots(self) -> Dict[str, str]:
        """Generate all plots and return file paths"""
        plots = {}

        if self.test_results:
            # Performance surface plot
            if self.test_results.performance_surface:
                plot_path = self._plot_performance_surface()
                plots["performance_surface"] = plot_path

            # Temperature coefficients plot
            if self.test_results.temperature_coefficients:
                plot_path = self._plot_temperature_coefficients()
                plots["temperature_coefficients"] = plot_path

            # Performance matrix heatmap
            if self.test_results.matrix_results:
                plot_path = self._plot_performance_heatmap()
                plots["performance_heatmap"] = plot_path

            # Spectral response curve
            if self.test_results.spectral_data:
                plot_path = self._plot_spectral_response()
                plots["spectral_response"] = plot_path

            # Angular response curve
            if self.test_results.angular_data:
                plot_path = self._plot_angular_response()
                plots["angular_response"] = plot_path

            # Energy rating comparison
            if self.test_results.energy_ratings:
                plot_path = self._plot_energy_ratings()
                plots["energy_ratings"] = plot_path

        return plots

    def _plot_performance_surface(self) -> str:
        """Generate 3D performance surface plot"""
        logger.info("Generating performance surface plot")

        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')

        # Get data from performance analyzer
        from .data_analyzer import PerformanceAnalyzer

        analyzer = PerformanceAnalyzer(self.test_results.matrix_results)
        T, G, P = analyzer.generate_mesh_predictions(temp_points=30, irrad_points=30)

        # Plot surface
        surf = ax.plot_surface(G, T, P, cmap='viridis', alpha=0.8, edgecolor='none')

        # Plot actual test points
        test_points = self.test_results.matrix_results.test_points
        test_G = [p.irradiance for p in test_points if p.data]
        test_T = [p.temperature for p in test_points if p.data]
        test_P = [p.data.iv_curve.pmax for p in test_points if p.data]

        ax.scatter(test_G, test_T, test_P, c='red', marker='o', s=50, label='Test Points')

        # Labels
        ax.set_xlabel('Irradiance (W/m²)', fontsize=10)
        ax.set_ylabel('Temperature (°C)', fontsize=10)
        ax.set_zlabel('Pmax (W)', fontsize=10)
        ax.set_title('Performance Surface: Pmax(G, T)', fontsize=12, fontweight='bold')
        ax.legend()

        # Color bar
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, label='Pmax (W)')

        # Save
        output_path = f"{self.test_id}_performance_surface.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Performance surface plot saved: {output_path}")
        return output_path

    def _plot_temperature_coefficients(self) -> str:
        """Plot temperature coefficient regression lines"""
        logger.info("Generating temperature coefficients plot")

        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        # Get data at reference irradiance
        test_points = [
            p for p in self.test_results.matrix_results.test_points
            if p.data and abs(p.irradiance - 1000.0) < 50
        ]

        temps = np.array([p.temperature for p in test_points])
        isc_vals = np.array([p.data.iv_curve.isc for p in test_points])
        voc_vals = np.array([p.data.iv_curve.voc for p in test_points])
        pmax_vals = np.array([p.data.iv_curve.pmax for p in test_points])

        tc = self.test_results.temperature_coefficients

        # Plot Isc vs T
        axes[0].scatter(temps, isc_vals, c='blue', label='Data')
        axes[0].plot(temps, np.poly1d(np.polyfit(temps, isc_vals, 1))(temps), 'r--',
                     label=f'α = {tc.alpha_isc:.3f} %/°C')
        axes[0].set_xlabel('Temperature (°C)')
        axes[0].set_ylabel('Isc (A)')
        axes[0].set_title('Short Circuit Current')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # Plot Voc vs T
        axes[1].scatter(temps, voc_vals, c='green', label='Data')
        axes[1].plot(temps, np.poly1d(np.polyfit(temps, voc_vals, 1))(temps), 'r--',
                     label=f'β = {tc.beta_voc:.3f} %/°C')
        axes[1].set_xlabel('Temperature (°C)')
        axes[1].set_ylabel('Voc (V)')
        axes[1].set_title('Open Circuit Voltage')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        # Plot Pmax vs T
        axes[2].scatter(temps, pmax_vals, c='red', label='Data')
        axes[2].plot(temps, np.poly1d(np.polyfit(temps, pmax_vals, 1))(temps), 'r--',
                     label=f'γ = {tc.gamma_pmax:.3f} %/°C')
        axes[2].set_xlabel('Temperature (°C)')
        axes[2].set_ylabel('Pmax (W)')
        axes[2].set_title('Maximum Power')
        axes[2].legend()
        axes[2].grid(True, alpha=0.3)

        plt.suptitle('Temperature Coefficients (at 1000 W/m²)', fontsize=14, fontweight='bold')

        # Save
        output_path = f"{self.test_id}_temp_coefficients.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Temperature coefficients plot saved: {output_path}")
        return output_path

    def _plot_performance_heatmap(self) -> str:
        """Generate performance matrix heatmap"""
        logger.info("Generating performance heatmap")

        matrix_data = self._create_performance_matrix_table()

        fig, ax = plt.subplots(figsize=(10, 6))

        # Create heatmap for Pmax
        pmax_grid = np.array(matrix_data["pmax_grid"])
        temps = matrix_data["temperatures"]
        irrads = matrix_data["irradiances"]

        im = ax.imshow(pmax_grid, aspect='auto', cmap='YlOrRd', origin='lower')

        # Set ticks
        ax.set_xticks(np.arange(len(irrads)))
        ax.set_yticks(np.arange(len(temps)))
        ax.set_xticklabels([f"{int(g)}" for g in irrads])
        ax.set_yticklabels([f"{int(t)}" for t in temps])

        # Labels
        ax.set_xlabel('Irradiance (W/m²)', fontsize=11)
        ax.set_ylabel('Temperature (°C)', fontsize=11)
        ax.set_title('Performance Matrix: Pmax (W)', fontsize=13, fontweight='bold')

        # Add values as text
        for i in range(len(temps)):
            for j in range(len(irrads)):
                value = pmax_grid[i, j]
                if not np.isnan(value):
                    text = ax.text(j, i, f'{value:.1f}',
                                 ha="center", va="center", color="black", fontsize=8)

        # Colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Pmax (W)', fontsize=10)

        # Save
        output_path = f"{self.test_id}_performance_heatmap.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Performance heatmap saved: {output_path}")
        return output_path

    def _plot_spectral_response(self) -> str:
        """Plot spectral response curve"""
        logger.info("Generating spectral response plot")

        spectral_data = self.test_results.spectral_data.get("data")
        if not spectral_data or not hasattr(spectral_data, 'points'):
            logger.warning("No spectral data available")
            return ""

        fig, ax = plt.subplots(figsize=(10, 6))

        wavelengths = [p.wavelength for p in spectral_data.points]
        responses = [p.response for p in spectral_data.points]

        ax.plot(wavelengths, responses, 'b-', linewidth=2, label='Spectral Response')
        ax.axvline(spectral_data.peak_wavelength, color='r', linestyle='--',
                   label=f'Peak: {spectral_data.peak_wavelength:.1f} nm')

        ax.set_xlabel('Wavelength (nm)', fontsize=11)
        ax.set_ylabel('Relative Spectral Response', fontsize=11)
        ax.set_title('Spectral Response Curve', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()

        # Save
        output_path = f"{self.test_id}_spectral_response.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Spectral response plot saved: {output_path}")
        return output_path

    def _plot_angular_response(self) -> str:
        """Plot angular response curve"""
        logger.info("Generating angular response plot")

        angular_data = self.test_results.angular_data.get("data")
        if not angular_data or not hasattr(angular_data, 'points'):
            logger.warning("No angular data available")
            return ""

        fig, ax = plt.subplots(figsize=(10, 6))

        angles = [p.angle for p in angular_data.points]
        responses = [p.relative_response for p in angular_data.points]

        ax.plot(angles, responses, 'g-', linewidth=2, marker='o', label='Measured')
        ax.axhline(angular_data.iam_factor, color='r', linestyle='--',
                   label=f'IAM Factor: {angular_data.iam_factor:.3f}')

        ax.set_xlabel('Incidence Angle (degrees)', fontsize=11)
        ax.set_ylabel('Relative Response', fontsize=11)
        ax.set_title('Angular Response (IAM)', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()
        ax.set_xlim(0, max(angles))
        ax.set_ylim(0, 1.1)

        # Save
        output_path = f"{self.test_id}_angular_response.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Angular response plot saved: {output_path}")
        return output_path

    def _plot_energy_ratings(self) -> str:
        """Plot energy rating comparison chart"""
        logger.info("Generating energy ratings plot")

        energy_results = self.test_results.energy_ratings.get("location_results", {})
        if not energy_results:
            logger.warning("No energy rating data available")
            return ""

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        locations = list(energy_results.keys())
        energies = [energy_results[loc]["annual_energy_kwh"] for loc in locations]
        yields = [energy_results[loc]["specific_yield_kwh_kwp"] for loc in locations]
        classes = [energy_results[loc]["energy_class"] for loc in locations]

        # Bar chart for annual energy
        bars1 = ax1.bar(locations, energies, color='steelblue', edgecolor='black')
        ax1.set_ylabel('Annual Energy (kWh/year)', fontsize=11)
        ax1.set_title('Annual Energy Yield by Location', fontsize=12, fontweight='bold')
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3, axis='y')

        # Add energy class labels
        for i, (bar, energy_class) in enumerate(zip(bars1, classes)):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'Class {energy_class}',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')

        # Bar chart for specific yield
        bars2 = ax2.bar(locations, yields, color='coral', edgecolor='black')
        ax2.set_ylabel('Specific Yield (kWh/kWp)', fontsize=11)
        ax2.set_title('Specific Yield by Location', fontsize=12, fontweight='bold')
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, alpha=0.3, axis='y')

        # Save
        output_path = f"{self.test_id}_energy_ratings.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Energy ratings plot saved: {output_path}")
        return output_path

    def _create_html_report(self) -> str:
        """Create HTML report content"""
        report_data = self._compile_report_data()

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>IEC 61853 Test Report - {self.test_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #3498db; color: white; }}
        .summary {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; }}
        .metric {{ display: inline-block; margin: 10px 20px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #2980b9; }}
        .metric-label {{ font-size: 14px; color: #7f8c8d; }}
    </style>
</head>
<body>
    <h1>IEC 61853 PV Module Performance Test Report</h1>

    <div class="summary">
        <h2>Test Information</h2>
        <p><strong>Test ID:</strong> {self.test_id}</p>
        <p><strong>Test Lab:</strong> {self.test_lab}</p>
        <p><strong>Test Engineer:</strong> {self.test_engineer}</p>
        <p><strong>Date:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>
    </div>

    <div class="summary">
        <h2>Module Information</h2>
        <p><strong>Serial Number:</strong> {self.module.serial_number}</p>
        <p><strong>Manufacturer:</strong> {self.module.manufacturer}</p>
        <p><strong>Model:</strong> {self.module.model}</p>
        <p><strong>Technology:</strong> {self.module.technology}</p>
        <p><strong>Rated Power:</strong> {self.module.rated_power} W</p>
    </div>

    <h2>Test Results Summary</h2>
    <div class="metric">
        <div class="metric-value">{report_data['test_summary'].get('matrix', {}).get('successful_points', 'N/A')}</div>
        <div class="metric-label">Test Points Completed</div>
    </div>
    <div class="metric">
        <div class="metric-value">{report_data.get('temperature_coefficients', {}).get('gamma_pmax_pct_per_c', 'N/A')}</div>
        <div class="metric-label">γ (Pmax) %/°C</div>
    </div>

    <h2>Standard Compliance</h2>
    <p>This test was conducted in accordance with:</p>
    <ul>
        <li>IEC 61853-1:2011 - Performance at STC and varying conditions</li>
        <li>IEC 61853-2:2016 - Spectral responsivity and angle of incidence</li>
        <li>IEC 61853-3:2018 - Energy rating of PV modules</li>
        <li>ISO/IEC 17025 - General requirements for testing laboratories</li>
    </ul>

    <p style="margin-top: 50px; font-size: 12px; color: #7f8c8d;">
        Report generated automatically by IEC 61853 Test Controller<br>
        © {datetime.utcnow().year} {self.test_lab}
    </p>
</body>
</html>
"""
        return html
