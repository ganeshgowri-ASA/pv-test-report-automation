"""
IEC 61853 Test Controller
==========================

Main orchestration controller for complete IEC 61853 test series.

Coordinates:
- Temperature chamber control
- Performance matrix testing (IEC 61853-1)
- Spectral response testing (IEC 61853-2)
- Energy rating calculations (IEC 61853-3)
- Data analysis and reporting
- Database persistence

Workflow:
1. Initialize test session
2. Run performance matrix (35 points)
3. Analyze performance surface
4. Run spectral/angular response tests
5. Calculate energy ratings
6. Generate comprehensive report
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import json

from .temperature_control import (
    TemperatureChamber,
    ChamberController,
    SimulatedChamber,
    StabilizationCriteria
)
from .performance_matrix import (
    PerformanceMatrixTest,
    IVCurveAcquisition,
    MatrixTestConfig,
    MatrixTestResults,
    STANDARD_TEMPERATURES,
    STANDARD_IRRADIANCES
)
from .spectral_response import (
    SpectralResponseTest,
    AngularResponseTest,
    SpectralCurve,
    SpectralTestConfig,
    AngularTestConfig
)
from .data_analyzer import (
    PerformanceAnalyzer,
    PerformanceSurface,
    TemperatureCoefficients
)
from .energy_rating import (
    EnergyRatingCalculator,
    LocationProfile,
    get_standard_location,
    STANDARD_LOCATIONS
)
from .models import IEC61853Part, TestStatus


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== Data Classes ====================

@dataclass
class ModuleUnderTest:
    """Module being tested"""
    serial_number: str
    manufacturer: str
    model: str
    technology: str  # "mono-Si", "poly-Si", "CdTe", etc.
    rated_power: float  # W
    rated_voc: float  # V
    rated_isc: float  # A
    rated_vmp: Optional[float] = None  # V
    rated_imp: Optional[float] = None  # A
    noct: Optional[float] = None  # °C


@dataclass
class TestConfiguration:
    """Complete test configuration"""
    test_id: str
    module: ModuleUnderTest
    test_lab: str
    test_engineer: str
    test_parts: List[IEC61853Part]

    # Test configurations
    matrix_config: MatrixTestConfig
    spectral_config: Optional[SpectralTestConfig] = None
    angular_config: Optional[AngularTestConfig] = None

    # Energy rating locations
    energy_rating_locations: List[str] = None

    def __post_init__(self):
        if self.energy_rating_locations is None:
            self.energy_rating_locations = ["Nicosia", "Phoenix", "Aachen", "Mumbai"]


@dataclass
class TestResults:
    """Complete test results"""
    test_id: str
    module_serial: str
    test_date: datetime
    status: TestStatus

    # Performance matrix results
    matrix_results: Optional[MatrixTestResults] = None

    # Analysis results
    performance_surface: Optional[PerformanceSurface] = None
    temperature_coefficients: Optional[TemperatureCoefficients] = None

    # Spectral/angular results
    spectral_data: Optional[Dict[str, Any]] = None
    angular_data: Optional[Dict[str, Any]] = None

    # Energy ratings
    energy_ratings: Optional[Dict[str, Any]] = None

    # Quality metrics
    quality_metrics: Optional[Dict[str, Any]] = None


# ==================== Main Test Controller ====================

class IEC61853TestController:
    """
    Main controller for IEC 61853 test series

    Example usage:
    >>> test = IEC61853TestController(
    ...     module_serial="PV-2025-001234",
    ...     test_lab="NABL Lab XYZ"
    ... )
    >>> test.run_performance_matrix()
    >>> results = test.analyze_performance()
    >>> test.generate_report("iec61853_report.pdf")
    """

    def __init__(
        self,
        module_serial: str,
        test_lab: str,
        module_manufacturer: str = "Unknown",
        module_model: str = "Unknown",
        module_technology: str = "mono-Si",
        rated_power: float = 300.0,
        test_engineer: Optional[str] = None,
        use_simulated_hardware: bool = True
    ):
        """
        Initialize test controller

        Args:
            module_serial: Module serial number
            test_lab: Test laboratory name
            module_manufacturer: Module manufacturer
            module_model: Module model
            module_technology: PV technology type
            rated_power: Rated power in watts
            test_engineer: Test engineer name
            use_simulated_hardware: Use simulated hardware (for testing)
        """
        # Generate test ID
        self.test_id = f"IEC61853-{module_serial}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Module under test
        self.module = ModuleUnderTest(
            serial_number=module_serial,
            manufacturer=module_manufacturer,
            model=module_model,
            technology=module_technology,
            rated_power=rated_power,
            rated_voc=45.0,  # Placeholder
            rated_isc=8.5,   # Placeholder
        )

        self.test_lab = test_lab
        self.test_engineer = test_engineer or "Auto"

        # Initialize hardware interfaces
        if use_simulated_hardware:
            logger.info("Using simulated hardware for testing")
            self.chamber = SimulatedChamber("SIM-CHAMBER-001")
            self.iv_acquisition = IVCurveAcquisition()
            self.spectral_test = SpectralResponseTest()
            self.angular_test = AngularResponseTest()
        else:
            logger.warning("Real hardware not implemented yet, using simulated")
            self.chamber = SimulatedChamber("SIM-CHAMBER-001")
            self.iv_acquisition = IVCurveAcquisition()
            self.spectral_test = SpectralResponseTest()
            self.angular_test = AngularResponseTest()

        # Initialize controllers
        self.chamber_controller = ChamberController(self.chamber)
        self.matrix_test: Optional[PerformanceMatrixTest] = None
        self.analyzer: Optional[PerformanceAnalyzer] = None
        self.energy_calculator: Optional[EnergyRatingCalculator] = None

        # Results storage
        self.test_results: Optional[TestResults] = None

        logger.info(
            f"IEC 61853 test controller initialized\n"
            f"  Test ID: {self.test_id}\n"
            f"  Module: {module_serial}\n"
            f"  Lab: {test_lab}"
        )

    def run_performance_matrix(
        self,
        temperatures: Optional[List[float]] = None,
        irradiances: Optional[List[float]] = None,
        config: Optional[MatrixTestConfig] = None
    ) -> MatrixTestResults:
        """
        Run complete performance matrix test (IEC 61853-1)

        Args:
            temperatures: Temperature points (default: standard 5 points)
            irradiances: Irradiance points (default: standard 7 points)
            config: Custom matrix test configuration

        Returns:
            MatrixTestResults
        """
        logger.info("=" * 70)
        logger.info("Starting IEC 61853-1 Performance Matrix Test")
        logger.info("=" * 70)

        # Setup configuration
        if config is None:
            config = MatrixTestConfig()
            if temperatures:
                config.temperatures = temperatures
            if irradiances:
                config.irradiances = irradiances

        # Connect hardware
        logger.info("Connecting to test equipment...")
        self.chamber_controller.connect()
        self.iv_acquisition.connect()

        # Initialize matrix test
        self.matrix_test = PerformanceMatrixTest(
            chamber_controller=self.chamber_controller,
            iv_acquisition=self.iv_acquisition,
            config=config
        )

        # Run test
        logger.info(
            f"Running performance matrix: "
            f"{len(config.temperatures)} temps × {len(config.irradiances)} irradiances = "
            f"{len(config.temperatures) * len(config.irradiances)} points"
        )

        matrix_results = self.matrix_test.run_matrix_test()

        # Store results
        if self.test_results is None:
            self.test_results = TestResults(
                test_id=self.test_id,
                module_serial=self.module.serial_number,
                test_date=datetime.utcnow(),
                status=TestStatus.IN_PROGRESS
            )

        self.test_results.matrix_results = matrix_results

        logger.info(
            f"Performance matrix completed: "
            f"{matrix_results.successful_points}/{matrix_results.total_points} successful"
        )

        return matrix_results

    def analyze_performance(self) -> Dict[str, Any]:
        """
        Analyze performance matrix data

        Extracts:
        - Performance surface model
        - Temperature coefficients
        - Quality metrics

        Returns:
            Analysis results dictionary
        """
        logger.info("=" * 70)
        logger.info("Analyzing Performance Data")
        logger.info("=" * 70)

        if self.test_results is None or self.test_results.matrix_results is None:
            raise RuntimeError("No matrix test results available. Run performance matrix first.")

        # Initialize analyzer
        self.analyzer = PerformanceAnalyzer(self.test_results.matrix_results)

        # Run complete analysis
        analysis_results = self.analyzer.analyze_all()

        # Store results
        self.test_results.performance_surface = self.analyzer.get_performance_surface()
        self.test_results.temperature_coefficients = self.analyzer.get_temperature_coefficients()
        self.test_results.quality_metrics = analysis_results["quality_metrics"]

        logger.info("Performance analysis completed")
        logger.info(f"  Temperature coefficients:")
        logger.info(f"    α (Isc): {analysis_results['temperature_coefficients']['alpha_isc']:.3f} %/°C")
        logger.info(f"    β (Voc): {analysis_results['temperature_coefficients']['beta_voc']:.3f} %/°C")
        logger.info(f"    γ (Pmax): {analysis_results['temperature_coefficients']['gamma_pmax']:.3f} %/°C")
        logger.info(f"  Performance surface R²: {analysis_results['performance_surface']['r_squared']:.4f}")

        return analysis_results

    def run_spectral_angular_tests(self) -> Dict[str, Any]:
        """
        Run spectral and angular response tests (IEC 61853-2)

        Returns:
            Combined spectral and angular test results
        """
        logger.info("=" * 70)
        logger.info("Starting IEC 61853-2 Spectral & Angular Tests")
        logger.info("=" * 70)

        # Create combined test
        spectral_curve = SpectralCurve(
            spectral_test=self.spectral_test,
            angular_test=self.angular_test
        )

        # Run characterization
        results = spectral_curve.run_complete_characterization()

        # Store results
        if self.test_results:
            self.test_results.spectral_data = results["spectral_response"]
            self.test_results.angular_data = results["angular_response"]

        logger.info("Spectral & angular testing completed")
        logger.info(f"  Peak wavelength: {results['spectral_response']['peak_wavelength']:.1f} nm")
        logger.info(f"  Spectral mismatch: {results['spectral_response']['mismatch_factor']:.4f}")
        logger.info(f"  IAM factor: {results['angular_response']['iam_factor']:.4f}")

        return results

    def calculate_energy_ratings(
        self,
        locations: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calculate energy ratings for multiple locations (IEC 61853-3)

        Args:
            locations: List of location names (default: standard 4 locations)

        Returns:
            Energy rating results for all locations
        """
        logger.info("=" * 70)
        logger.info("Calculating IEC 61853-3 Energy Ratings")
        logger.info("=" * 70)

        if self.test_results is None or self.test_results.performance_surface is None:
            raise RuntimeError("Performance analysis required. Run analyze_performance() first.")

        # Get spectral and angular factors
        spectral_mismatch = 1.0
        iam_factor = 0.97

        if self.test_results.spectral_data:
            spectral_mismatch = self.test_results.spectral_data.get("mismatch_factor", 1.0)

        if self.test_results.angular_data:
            iam_factor = self.test_results.angular_data.get("iam_factor", 0.97)

        # Initialize energy calculator
        self.energy_calculator = EnergyRatingCalculator(
            performance_surface=self.test_results.performance_surface,
            temperature_coefficients=self.test_results.temperature_coefficients,
            rated_power=self.module.rated_power,
            spectral_mismatch_factor=spectral_mismatch,
            iam_factor=iam_factor
        )

        # Calculate for all locations
        energy_results = self.energy_calculator.generate_energy_rating_report(locations)

        # Store results
        self.test_results.energy_ratings = energy_results

        logger.info("Energy ratings calculated")
        for loc_name, loc_results in energy_results["location_results"].items():
            logger.info(
                f"  {loc_name}: {loc_results['annual_energy_kwh']:.1f} kWh/year, "
                f"Class {loc_results['energy_class']}"
            )

        return energy_results

    def run_complete_test_series(
        self,
        include_spectral: bool = True,
        include_energy_rating: bool = True
    ) -> TestResults:
        """
        Run complete IEC 61853 test series

        Args:
            include_spectral: Include IEC 61853-2 tests
            include_energy_rating: Include IEC 61853-3 calculations

        Returns:
            Complete test results
        """
        logger.info("#" * 70)
        logger.info("# IEC 61853 COMPLETE TEST SERIES")
        logger.info(f"# Module: {self.module.serial_number}")
        logger.info(f"# Lab: {self.test_lab}")
        logger.info("#" * 70)

        try:
            # Part 1: Performance matrix
            logger.info("\n[1/4] IEC 61853-1: Performance Matrix")
            self.run_performance_matrix()

            # Analyze performance
            logger.info("\n[2/4] Performance Analysis")
            self.analyze_performance()

            # Part 2: Spectral/angular (optional)
            if include_spectral:
                logger.info("\n[3/4] IEC 61853-2: Spectral & Angular Response")
                self.run_spectral_angular_tests()
            else:
                logger.info("\n[3/4] Skipping spectral/angular tests")

            # Part 3: Energy rating (optional)
            if include_energy_rating:
                logger.info("\n[4/4] IEC 61853-3: Energy Rating")
                self.calculate_energy_ratings()
            else:
                logger.info("\n[4/4] Skipping energy rating calculations")

            # Mark test as completed
            if self.test_results:
                self.test_results.status = TestStatus.COMPLETED

            logger.info("\n" + "#" * 70)
            logger.info("# TEST SERIES COMPLETED SUCCESSFULLY")
            logger.info("#" * 70)

        except Exception as e:
            logger.error(f"Test series failed: {e}", exc_info=True)
            if self.test_results:
                self.test_results.status = TestStatus.FAILED
            raise

        finally:
            # Cleanup
            self.disconnect_all()

        return self.test_results

    def disconnect_all(self):
        """Disconnect from all hardware"""
        logger.info("Disconnecting from test equipment...")
        try:
            self.chamber_controller.disconnect()
            self.iv_acquisition.disconnect()
            if hasattr(self.spectral_test, 'disconnect'):
                self.spectral_test.disconnect()
            if hasattr(self.angular_test, 'disconnect'):
                self.angular_test.disconnect()
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    def export_results(self, output_dir: str = "."):
        """
        Export all test results to files

        Args:
            output_dir: Output directory for results
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Export matrix data
        if self.matrix_test:
            matrix_file = output_path / f"{self.test_id}_matrix.json"
            with open(matrix_file, 'w') as f:
                json.dump(self.matrix_test.export_to_dict(), f, indent=2)
            logger.info(f"Matrix data exported to {matrix_file}")

        # Export analysis results
        if self.analyzer:
            analysis_file = output_path / f"{self.test_id}_analysis.json"
            self.analyzer.export_analysis_report(str(analysis_file))
            logger.info(f"Analysis exported to {analysis_file}")

        # Export energy ratings
        if self.energy_calculator:
            energy_file = output_path / f"{self.test_id}_energy.json"
            self.energy_calculator.export_to_json(str(energy_file))
            logger.info(f"Energy ratings exported to {energy_file}")

    def generate_report(self, output_path: str = "iec61853_report.pdf"):
        """
        Generate comprehensive test report

        Args:
            output_path: Path for output report (PDF)
        """
        logger.info(f"Generating comprehensive report: {output_path}")

        # Import report generator
        from .report_generator import IEC61853ReportGenerator

        # Create report generator
        report_gen = IEC61853ReportGenerator(
            test_id=self.test_id,
            module=self.module,
            test_lab=self.test_lab,
            test_results=self.test_results
        )

        # Generate report
        report_gen.generate_pdf_report(output_path)

        logger.info(f"Report generated: {output_path}")

    def get_summary(self) -> Dict[str, Any]:
        """Get test summary"""
        if not self.test_results:
            return {"status": "No test results available"}

        summary = {
            "test_id": self.test_id,
            "module": self.module.serial_number,
            "status": self.test_results.status.value,
            "test_date": self.test_results.test_date.isoformat(),
        }

        if self.test_results.matrix_results:
            summary["matrix"] = {
                "total_points": self.test_results.matrix_results.total_points,
                "successful": self.test_results.matrix_results.successful_points,
                "duration_hours": self.test_results.matrix_results.total_duration / 3600
            }

        if self.test_results.temperature_coefficients:
            tc = self.test_results.temperature_coefficients
            summary["temperature_coefficients"] = {
                "alpha_isc": tc.alpha_isc,
                "beta_voc": tc.beta_voc,
                "gamma_pmax": tc.gamma_pmax,
            }

        if self.test_results.energy_ratings:
            summary["energy_ratings"] = self.test_results.energy_ratings.get("summary", {})

        return summary
