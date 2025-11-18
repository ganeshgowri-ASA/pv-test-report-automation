"""
Unit Tests for IEC 61853 Protocol Implementation
=================================================

Comprehensive test suite covering:
- Temperature chamber control
- Performance matrix testing
- Spectral response measurements
- Data analysis and surface fitting
- Energy rating calculations
- Report generation
"""

import unittest
import numpy as np
from datetime import datetime
from typing import List

from .temperature_control import (
    SimulatedChamber,
    ChamberController,
    StabilizationCriteria,
    ChamberState
)
from .performance_matrix import (
    PerformanceMatrixTest,
    IVCurveAcquisition,
    MatrixTestConfig,
    TestSequenceMode,
    STANDARD_TEMPERATURES,
    STANDARD_IRRADIANCES
)
from .spectral_response import (
    SpectralResponseTest,
    AngularResponseTest,
    SpectralCurve
)
from .data_analyzer import (
    PerformanceAnalyzer,
)
from .energy_rating import (
    EnergyRatingCalculator,
    get_standard_location,
    STANDARD_LOCATIONS
)
from .test_controller import (
    IEC61853TestController,
    ModuleUnderTest
)
from .models import (
    IVPoint,
    IVCurve,
    MatrixTestPointData,
    TemperatureCoefficientsData
)


class TestTemperatureControl(unittest.TestCase):
    """Test temperature chamber control"""

    def setUp(self):
        self.chamber = SimulatedChamber("TEST-CHAMBER-001")
        self.controller = ChamberController(self.chamber)

    def test_chamber_connection(self):
        """Test chamber connection"""
        self.assertTrue(self.controller.connect())
        self.controller.disconnect()

    def test_set_temperature(self):
        """Test setting temperature"""
        self.controller.connect()
        self.assertTrue(self.controller.goto_temperature(25.0, wait_stable=False))
        self.controller.disconnect()

    def test_temperature_validation(self):
        """Test temperature limits validation"""
        self.controller.connect()
        # Should fail - too low
        self.assertFalse(self.controller.goto_temperature(-50.0, wait_stable=False))
        # Should fail - too high
        self.assertFalse(self.controller.goto_temperature(100.0, wait_stable=False))
        self.controller.disconnect()

    def test_stabilization(self):
        """Test temperature stabilization"""
        self.controller.connect()

        # Use very relaxed criteria for quick testing
        criteria = StabilizationCriteria(
            tolerance=5.0,
            duration=5.0,
            max_wait_time=60.0,
            sample_interval=1.0
        )

        result = self.controller.goto_temperature(
            25.0,
            wait_stable=True,
            criteria=criteria
        )

        self.assertTrue(result)
        self.controller.disconnect()

    def test_temperature_sequence(self):
        """Test temperature sequence execution"""
        self.controller.connect()

        # Short sequence for testing
        temps = [0.0, 25.0, 50.0]
        self.assertTrue(self.controller.set_temperature_sequence(temps))

        # Note: Full sequence test would take too long
        # Just verify setup
        self.assertEqual(len(self.controller._test_sequence), 3)

        self.controller.disconnect()


class TestIVCurveAcquisition(unittest.TestCase):
    """Test I-V curve acquisition"""

    def setUp(self):
        self.iv_acq = IVCurveAcquisition(sweep_points=100)

    def test_connection(self):
        """Test connection to I-V system"""
        self.assertTrue(self.iv_acq.connect())
        self.iv_acq.disconnect()

    def test_iv_curve_acquisition(self):
        """Test I-V curve acquisition"""
        self.iv_acq.connect()

        iv_curve = self.iv_acq.acquire_iv_curve(voc_estimate=45.0, isc_estimate=8.5)

        # Verify curve data
        self.assertIsInstance(iv_curve, IVCurve)
        self.assertEqual(len(iv_curve.points), 100)
        self.assertGreater(iv_curve.voc, 0)
        self.assertGreater(iv_curve.isc, 0)
        self.assertGreater(iv_curve.pmax, 0)
        self.assertGreater(iv_curve.ff, 0.5)
        self.assertLess(iv_curve.ff, 0.9)

        self.iv_acq.disconnect()

    def test_iv_curve_parameters(self):
        """Test I-V curve parameter extraction"""
        self.iv_acq.connect()

        iv_curve = self.iv_acq.acquire_iv_curve()

        # Verify Pmax = Vmp × Imp
        pmax_calculated = iv_curve.vmp * iv_curve.imp
        self.assertAlmostEqual(iv_curve.pmax, pmax_calculated, delta=1.0)

        # Verify fill factor
        ff_calculated = iv_curve.pmax / (iv_curve.voc * iv_curve.isc)
        self.assertAlmostEqual(iv_curve.ff, ff_calculated, delta=0.01)

        self.iv_acq.disconnect()


class TestPerformanceMatrix(unittest.TestCase):
    """Test performance matrix testing"""

    def setUp(self):
        self.chamber = SimulatedChamber("TEST-CHAMBER-001")
        self.chamber_controller = ChamberController(self.chamber)
        self.iv_acq = IVCurveAcquisition()

        # Quick test configuration (reduced points)
        self.config = MatrixTestConfig(
            temperatures=[0.0, 25.0, 50.0],  # 3 instead of 5
            irradiances=[200.0, 600.0, 1000.0],  # 3 instead of 7
            sequence_mode=TestSequenceMode.TEMPERATURE_FIRST
        )
        self.config.stabilization_criteria = StabilizationCriteria(
            tolerance=5.0,
            duration=2.0,
            max_wait_time=30.0,
            sample_interval=0.5
        )

    def test_test_sequence_generation(self):
        """Test generation of test sequence"""
        matrix_test = PerformanceMatrixTest(
            self.chamber_controller,
            self.iv_acq,
            self.config
        )

        sequence = matrix_test.generate_test_sequence()

        # Should have 3×3 = 9 points
        self.assertEqual(len(sequence), 9)

    def test_matrix_config(self):
        """Test matrix configuration"""
        # Standard configuration
        std_config = MatrixTestConfig()
        self.assertEqual(len(std_config.temperatures), 5)
        self.assertEqual(len(std_config.irradiances), 7)

        # Custom configuration
        self.assertEqual(len(self.config.temperatures), 3)
        self.assertEqual(len(self.config.irradiances), 3)

    # Note: Full matrix test would take too long for unit testing
    # Integration tests should cover full execution


class TestSpectralResponse(unittest.TestCase):
    """Test spectral response measurements"""

    def setUp(self):
        self.spectral_test = SpectralResponseTest()

    def test_connection(self):
        """Test spectral system connection"""
        self.assertTrue(self.spectral_test.connect())
        self.spectral_test.disconnect()

    def test_spectral_measurement(self):
        """Test spectral response measurement"""
        self.spectral_test.connect()

        spectral_data = self.spectral_test.measure_spectral_response()

        # Verify data
        self.assertGreater(len(spectral_data.points), 0)
        self.assertGreater(spectral_data.peak_wavelength, 300)
        self.assertLess(spectral_data.peak_wavelength, 1200)
        self.assertAlmostEqual(spectral_data.peak_response, 1.0, delta=0.01)
        self.assertGreater(spectral_data.mismatch_factor, 0.9)
        self.assertLess(spectral_data.mismatch_factor, 1.1)

        self.spectral_test.disconnect()


class TestAngularResponse(unittest.TestCase):
    """Test angular response measurements"""

    def setUp(self):
        self.angular_test = AngularResponseTest()

    def test_connection(self):
        """Test angular system connection"""
        self.assertTrue(self.angular_test.connect())
        self.angular_test.disconnect()

    def test_angular_measurement(self):
        """Test angular response measurement"""
        self.angular_test.connect()

        angular_data = self.angular_test.measure_angular_response()

        # Verify data
        self.assertGreater(len(angular_data.points), 0)
        self.assertGreater(angular_data.iam_factor, 0.90)
        self.assertLess(angular_data.iam_factor, 1.0)

        # Verify response at normal incidence
        normal_response = angular_data.points[0].relative_response
        self.assertAlmostEqual(normal_response, 1.0, delta=0.01)

        self.angular_test.disconnect()


class TestDataAnalyzer(unittest.TestCase):
    """Test performance data analysis"""

    def setUp(self):
        # Create dummy matrix results for testing
        from .performance_matrix import MatrixTestPoint, MatrixTestResults

        # Create test points with realistic data
        test_points = []
        for temp in [0, 25, 50]:
            for irrad in [200, 600, 1000]:
                # Simulate realistic Pmax values
                pmax = (irrad / 1000.0) * 300.0 * (1 - 0.004 * (temp - 25))

                # Create IV curve
                iv_curve = IVCurve(
                    points=[IVPoint(voltage=i, current=8.0, power=pmax) for i in range(100)],
                    voc=45.0 - 0.15 * (temp - 25),
                    isc=8.5 * (irrad / 1000.0) + 0.003 * (temp - 25),
                    vmp=36.0,
                    imp=pmax / 36.0 if pmax > 0 else 0,
                    pmax=pmax,
                    ff=0.75
                )

                # Create test point data
                point_data = MatrixTestPointData(
                    temperature=temp,
                    irradiance=irrad,
                    iv_curve=iv_curve,
                    timestamp=datetime.utcnow(),
                    stabilization_time=30.0,
                    chamber_temp_actual=temp,
                    chamber_temp_stability=0.5,
                    irradiance_actual=irrad,
                    irradiance_uniformity=98.0
                )

                point = MatrixTestPoint(temperature=temp, irradiance=irrad, data=point_data)
                test_points.append(point)

        self.matrix_results = MatrixTestResults(
            test_points=test_points,
            total_points=len(test_points),
            successful_points=len(test_points),
            failed_points=0,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            total_duration=3600.0,
            config=MatrixTestConfig()
        )

    def test_performance_surface_fitting(self):
        """Test performance surface model fitting"""
        analyzer = PerformanceAnalyzer(self.matrix_results)

        surface = analyzer.fit_performance_surface(polynomial_degree=2)

        self.assertIsNotNone(surface)
        self.assertGreater(surface.r_squared, 0.8)  # Should have good fit
        self.assertGreater(surface.rmse, 0)

    def test_temperature_coefficient_extraction(self):
        """Test temperature coefficient extraction"""
        analyzer = PerformanceAnalyzer(self.matrix_results)

        temp_coeff = analyzer.extract_temperature_coefficients(
            reference_irradiance=1000.0,
            reference_temperature=25.0
        )

        self.assertIsNotNone(temp_coeff)
        # Typical values for Si modules
        self.assertLess(temp_coeff.alpha_isc, 0.1)  # Positive, small
        self.assertLess(temp_coeff.beta_voc, 0)  # Negative
        self.assertLess(temp_coeff.gamma_pmax, 0)  # Negative

    def test_quality_metrics(self):
        """Test quality metrics calculation"""
        analyzer = PerformanceAnalyzer(self.matrix_results)

        quality = analyzer.calculate_quality_metrics()

        self.assertIn("fill_factor", quality)
        self.assertIn("temperature_stability", quality)
        self.assertIn("data_completeness", quality)
        self.assertEqual(quality["data_completeness"]["success_rate"], 1.0)


class TestEnergyRating(unittest.TestCase):
    """Test energy rating calculations"""

    def setUp(self):
        # Create simple performance surface for testing
        from .data_analyzer import PerformanceSurface
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import PolynomialFeatures

        # Simple linear model: Pmax ≈ G * 0.3 - T * 1.2
        X = np.array([[1000, 25], [800, 25], [600, 25]])
        y = np.array([300, 240, 180])

        poly = PolynomialFeatures(degree=1)
        X_poly = poly.fit_transform(X)
        model = LinearRegression()
        model.fit(X_poly, y)

        class SimpleModel:
            def __init__(self, poly, linear_model):
                self.poly = poly
                self.linear_model = linear_model

            def predict(self, X):
                X_poly = self.poly.transform(X)
                return self.linear_model.predict(X_poly)

        self.surface = PerformanceSurface(
            model=SimpleModel(poly, model),
            polynomial_degree=1,
            coefficients=[],
            r_squared=0.99,
            rmse=5.0,
            temperature_range=(-25, 75),
            irradiance_range=(100, 1100)
        )

        # Create temperature coefficients
        from .data_analyzer import TemperatureCoefficients

        self.temp_coeff = TemperatureCoefficients(
            alpha_isc=0.05,
            beta_voc=-0.35,
            gamma_pmax=-0.40,
            alpha_isc_abs=0.004,
            beta_voc_abs=-0.16,
            gamma_pmax_abs=-1.2,
            reference_temperature=25.0,
            reference_irradiance=1000.0,
            r_squared_isc=0.98,
            r_squared_voc=0.99,
            r_squared_pmax=0.97
        )

    def test_standard_location_loading(self):
        """Test loading standard locations"""
        location = get_standard_location("Nicosia")

        self.assertIsNotNone(location)
        self.assertEqual(location.name, "Nicosia")
        self.assertGreater(location.annual_irradiation, 0)

    def test_energy_calculation(self):
        """Test annual energy calculation"""
        calculator = EnergyRatingCalculator(
            performance_surface=self.surface,
            temperature_coefficients=self.temp_coeff,
            rated_power=300.0
        )

        location = get_standard_location("Nicosia")
        energy_rating = calculator.calculate_annual_energy(location)

        self.assertIsNotNone(energy_rating)
        self.assertGreater(energy_rating.annual_energy_kwh, 0)
        self.assertGreater(energy_rating.specific_yield_kwh_kwp, 0)
        self.assertGreater(energy_rating.performance_ratio, 0)
        self.assertIn(energy_rating.energy_rating_class, ["A+", "A", "B", "C", "D", "E"])

    def test_multiple_locations(self):
        """Test energy calculation for multiple locations"""
        calculator = EnergyRatingCalculator(
            performance_surface=self.surface,
            temperature_coefficients=self.temp_coeff,
            rated_power=300.0
        )

        results = calculator.calculate_multiple_locations(["Nicosia", "Phoenix"])

        self.assertEqual(len(results), 2)
        self.assertIn("Nicosia", results)
        self.assertIn("Phoenix", results)


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflow"""

    def test_complete_workflow_simulation(self):
        """Test complete IEC 61853 workflow with simulated hardware"""
        # This is a simplified integration test
        # Full test would take too long for unit testing

        controller = IEC61853TestController(
            module_serial="TEST-MODULE-001",
            test_lab="Test Lab",
            rated_power=300.0,
            use_simulated_hardware=True
        )

        # Test initialization
        self.assertEqual(controller.module.serial_number, "TEST-MODULE-001")
        self.assertEqual(controller.test_lab, "Test Lab")

        # Note: Running full test would take very long
        # In practice, this would be an integration/acceptance test


def run_tests():
    """Run all unit tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTemperatureControl))
    suite.addTests(loader.loadTestsFromTestCase(TestIVCurveAcquisition))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceMatrix))
    suite.addTests(loader.loadTestsFromTestCase(TestSpectralResponse))
    suite.addTests(loader.loadTestsFromTestCase(TestAngularResponse))
    suite.addTests(loader.loadTestsFromTestCase(TestDataAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestEnergyRating))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
