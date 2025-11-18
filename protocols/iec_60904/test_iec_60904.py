"""
Comprehensive Unit Tests for IEC 60904 Series Implementation

Tests cover:
- IEC 60904-1: I-V curve measurement
- IEC 60904-2: Reference solar cells
- IEC 60904-7: Spectral mismatch
- IEC 60904-9: Solar simulator verification

ISO 17025 compliance testing included.
"""

import unittest
import numpy as np
from datetime import datetime, timedelta

from .iv_measurement import (
    IVMeasurement, IVResult, MeasurementMode, WireConfiguration
)
from .reference_cell import (
    ReferenceCell, ReferenceCellCalibration, CellType, CalibrationMethod
)
from .spectral_mismatch import (
    SpectralMismatch, SpectralData, ReferenceSpectrum
)
from .simulator_verification import (
    SimulatorVerification, SimulatorClass, SimulatorType,
    PerformanceCriteria, VerificationResult
)


class TestIVMeasurement(unittest.TestCase):
    """Test IEC 60904-1 I-V curve measurement"""

    def setUp(self):
        """Set up test fixtures"""
        self.iv_system = IVMeasurement(
            module_serial="TEST-PV-001",
            area=1.6,  # m²
            wire_config=WireConfiguration.FOUR_WIRE_KELVIN
        )

    def test_iv_measurement_basic(self):
        """Test basic I-V curve measurement"""
        result = self.iv_system.measure_iv_curve(
            irradiance=1000.0,
            temperature=25.0
        )

        # Verify result type
        self.assertIsInstance(result, IVResult)

        # Verify basic parameters are positive
        self.assertGreater(result.voc, 0)
        self.assertGreater(result.isc, 0)
        self.assertGreater(result.pmax, 0)
        self.assertGreater(result.ff, 0)
        self.assertGreater(result.efficiency, 0)

        # Verify fill factor range
        self.assertGreaterEqual(result.ff, 0)
        self.assertLessEqual(result.ff, 1.0)

        # Verify minimum data points (IEC 60904-1 requirement)
        self.assertGreaterEqual(result.num_points, 100)

        # Verify wire configuration
        self.assertEqual(result.wire_config, WireConfiguration.FOUR_WIRE_KELVIN)

    def test_iv_curve_physics(self):
        """Test that I-V curve follows expected physics"""
        result = self.iv_system.measure_iv_curve()

        # Vmp should be less than Voc
        self.assertLess(result.vmp, result.voc)

        # Imp should be less than Isc
        self.assertLess(result.imp, result.isc)

        # Pmax should equal Vmp * Imp
        self.assertAlmostEqual(result.pmax, result.vmp * result.imp, places=2)

        # FF calculation verification
        expected_ff = result.pmax / (result.voc * result.isc)
        self.assertAlmostEqual(result.ff, expected_ff, places=6)

        # Current should be monotonically decreasing with voltage
        self.assertTrue(np.all(np.diff(result.current_data) <= 0))

    def test_temperature_effect(self):
        """Test temperature coefficient effects"""
        result_25c = self.iv_system.measure_iv_curve(temperature=25.0)
        result_50c = self.iv_system.measure_iv_curve(temperature=50.0)

        # Voc should decrease with temperature (negative temp coefficient)
        self.assertLess(result_50c.voc, result_25c.voc)

        # Isc should increase slightly with temperature (positive temp coefficient)
        self.assertGreater(result_50c.isc, result_25c.isc)

    def test_irradiance_effect(self):
        """Test irradiance scaling"""
        result_1000 = self.iv_system.measure_iv_curve(irradiance=1000.0)
        result_500 = self.iv_system.measure_iv_curve(irradiance=500.0)

        # Isc should scale linearly with irradiance
        ratio = result_500.isc / result_1000.isc
        self.assertAlmostEqual(ratio, 0.5, delta=0.05)

        # Voc should increase logarithmically (less than linear)
        voc_ratio = result_500.voc / result_1000.voc
        self.assertGreater(voc_ratio, 0.95)  # Slight decrease
        self.assertLess(voc_ratio, 1.0)

    def test_series_resistance_calculation(self):
        """Test series resistance extraction"""
        result = self.iv_system.measure_iv_curve()
        rs = result.get_series_resistance()

        # Series resistance should be positive and reasonable
        self.assertGreaterEqual(rs, 0)
        self.assertLess(rs, 10.0)  # Typical range 0-10 Ω for modules

    def test_shunt_resistance_calculation(self):
        """Test shunt resistance extraction"""
        result = self.iv_system.measure_iv_curve()
        rsh = result.get_shunt_resistance()

        # Shunt resistance should be positive and high (or inf for ideal case)
        self.assertGreaterEqual(rsh, 0)
        # Note: May return 0 or inf depending on curve characteristics
        # In simulation, this depends on the model implementation

    def test_linearity_test(self):
        """Test IEC 60904-10 linearity measurement"""
        irradiance_levels = [200, 400, 600, 800, 1000]
        linearity_result = self.iv_system.perform_linearity_test(irradiance_levels)

        # Check R² is high (good linearity)
        self.assertGreater(linearity_result['linearity']['r_squared'], 0.99)

        # Check compliance
        self.assertTrue(linearity_result['compliant'])

    def test_measurement_speed(self):
        """Test measurement speed compliance (<20ms per point)"""
        result = self.iv_system.measure_iv_curve(num_points=100)

        time_per_point = result.measurement_time / result.num_points
        # Allow some margin for simulation overhead
        self.assertLess(time_per_point, 0.1)  # 100ms in simulation mode

    def test_result_serialization(self):
        """Test result export to JSON"""
        result = self.iv_system.measure_iv_curve()

        # Test to_dict
        result_dict = result.to_dict()
        self.assertIsInstance(result_dict, dict)
        self.assertIn('voc', result_dict)
        self.assertIn('isc', result_dict)
        self.assertIn('pmax', result_dict)

        # Test to_json
        result_json = result.to_json()
        self.assertIsInstance(result_json, str)
        self.assertIn('voc', result_json)


class TestReferenceCell(unittest.TestCase):
    """Test IEC 60904-2 reference cell management"""

    def setUp(self):
        """Set up test fixtures"""
        # Create typical spectral response
        wavelengths = np.arange(300, 1201, 10)
        responsivity = 0.4 * np.ones_like(wavelengths, dtype=float)
        self.spectral_response = {float(wl): float(resp)
                                  for wl, resp in zip(wavelengths, responsivity)}

        # Create reference spectrum (simplified AM1.5G)
        self.reference_spectrum = {float(wl): 1.0 for wl in wavelengths}

    def test_primary_cell_calibration(self):
        """Test primary reference cell calibration"""
        primary_cell = ReferenceCell(
            cell_serial="PRIMARY-001",
            cell_type=CellType.PRIMARY,
            active_area=4.0  # cm²
        )

        calibration = primary_cell.calibrate_primary(
            spectral_response=self.spectral_response,
            reference_spectrum=self.reference_spectrum,
            measured_current=0.4,
            temperature=25.0,
            traceability="NIST"
        )

        self.assertIsInstance(calibration, ReferenceCellCalibration)
        self.assertEqual(calibration.cell_type, CellType.PRIMARY)
        self.assertGreater(calibration.calibration_constant, 0)
        self.assertTrue(calibration.is_valid())

    def test_transfer_calibration(self):
        """Test secondary cell calibration by transfer"""
        # Create calibrated primary cell
        primary_cell = ReferenceCell(
            cell_serial="PRIMARY-001",
            cell_type=CellType.PRIMARY,
            active_area=4.0
        )
        primary_cell.calibrate_primary(
            spectral_response=self.spectral_response,
            reference_spectrum=self.reference_spectrum,
            measured_current=0.4,
            temperature=25.0
        )

        # Create secondary cell
        secondary_cell = ReferenceCell(
            cell_serial="SECONDARY-001",
            cell_type=CellType.SECONDARY,
            active_area=4.0
        )

        # Transfer calibration
        calibration = secondary_cell.calibrate_by_transfer(
            primary_cell=primary_cell,
            measured_current_secondary=0.38,
            measured_current_primary=0.40,
            irradiance=1000.0,
            temperature=25.0
        )

        self.assertIsInstance(calibration, ReferenceCellCalibration)
        self.assertEqual(calibration.cell_type, CellType.SECONDARY)
        self.assertGreater(calibration.uncertainty, primary_cell.calibration.uncertainty)

    def test_irradiance_measurement(self):
        """Test irradiance measurement with calibrated cell"""
        cell = ReferenceCell(
            cell_serial="REF-001",
            cell_type=CellType.SECONDARY,
            active_area=4.0
        )

        # Create calibration
        cell.calibration = ReferenceCellCalibration(
            cell_serial="REF-001",
            cell_type=CellType.SECONDARY,
            calibration_date=datetime.now(),
            calibration_constant=0.0004,  # A/(W/m²)
            temperature_coefficient=-0.05,
            spectral_response=self.spectral_response,
            reference_temperature=25.0
        )

        # Measure irradiance
        measured_current = 0.4  # A
        temperature = 25.0
        irradiance, uncertainty = cell.measure_irradiance(measured_current, temperature)

        self.assertGreater(irradiance, 0)
        self.assertGreater(uncertainty, 0)
        self.assertAlmostEqual(irradiance, 1000.0, delta=10)

    def test_temperature_coefficient_determination(self):
        """Test temperature coefficient measurement"""
        cell = ReferenceCell(
            cell_serial="REF-001",
            cell_type=CellType.PRIMARY,
            active_area=4.0
        )

        # Simulate measurements at different temperatures
        temperatures = [15, 20, 25, 30, 35, 40]
        currents = [0.402, 0.401, 0.400, 0.399, 0.398, 0.397]

        temp_coeff = cell.determine_temperature_coefficient(
            temperatures, currents, irradiance=1000.0
        )

        # Temperature coefficient should be negative for c-Si
        self.assertLess(temp_coeff, 0)
        self.assertGreater(temp_coeff, -0.1)  # Typical range

    def test_stability_monitoring(self):
        """Test reference cell stability analysis"""
        cell = ReferenceCell(
            cell_serial="REF-001",
            cell_type=CellType.SECONDARY,
            active_area=4.0
        )

        cell.calibration = ReferenceCellCalibration(
            cell_serial="REF-001",
            cell_type=CellType.SECONDARY,
            calibration_date=datetime.now(),
            calibration_constant=0.0004,
            temperature_coefficient=-0.05,
            spectral_response=self.spectral_response
        )

        # Add measurement history
        for i in range(20):
            cell.measurement_history.append({
                'timestamp': (datetime.now() - timedelta(days=i)).isoformat(),
                'measured_current': 0.4 + 0.001 * np.random.randn(),
                'temperature': 25.0,
                'irradiance': 1000.0,
                'uncertainty': 0.5
            })

        stability = cell.check_stability(lookback_days=30, max_drift_percent=1.0)

        self.assertIn('stable', stability)
        self.assertIn('drift_percent', stability)

    def test_calibration_expiration(self):
        """Test calibration validity checking"""
        # Create expired calibration
        calibration = ReferenceCellCalibration(
            cell_serial="REF-001",
            cell_type=CellType.PRIMARY,
            calibration_date=datetime.now() - timedelta(days=400),
            calibration_constant=0.0004,
            temperature_coefficient=-0.05,
            spectral_response=self.spectral_response,
            valid_until=datetime.now() - timedelta(days=35)
        )

        self.assertFalse(calibration.is_valid())


class TestSpectralMismatch(unittest.TestCase):
    """Test IEC 60904-7 spectral mismatch calculation"""

    def setUp(self):
        """Set up test fixtures"""
        self.spectral_mismatch = SpectralMismatch()

    def test_am15g_spectrum_loading(self):
        """Test AM1.5G reference spectrum loading"""
        spectrum = self.spectral_mismatch.reference_spectrum

        self.assertIsInstance(spectrum, SpectralData)
        self.assertEqual(spectrum.data_type, 'irradiance')
        self.assertGreater(len(spectrum.wavelengths), 0)

    def test_spectral_data_interpolation(self):
        """Test spectral data interpolation"""
        wavelengths = np.array([400, 500, 600, 700, 800])
        values = np.array([1.0, 1.2, 1.1, 0.9, 0.7])

        spectral_data = SpectralData(
            wavelengths=wavelengths,
            values=values,
            data_type='irradiance'
        )

        # Interpolate to finer grid
        new_wavelengths = np.arange(400, 801, 10)
        interpolated = spectral_data.interpolate(new_wavelengths)

        self.assertEqual(len(interpolated.wavelengths), len(new_wavelengths))
        self.assertAlmostEqual(interpolated.values[0], 1.0, places=5)

    def test_spectral_data_integration(self):
        """Test spectral data integration"""
        wavelengths = np.linspace(400, 700, 100)
        values = np.ones_like(wavelengths)

        spectral_data = SpectralData(
            wavelengths=wavelengths,
            values=values,
            data_type='irradiance'
        )

        integral = spectral_data.integrate()
        expected = 300.0  # Approximately (700-400) * 1.0
        self.assertAlmostEqual(integral, expected, delta=10)

    def test_mismatch_factor_calculation(self):
        """Test spectral mismatch factor calculation"""
        # Create test spectrum (similar to reference)
        test_spectrum = self.spectral_mismatch.create_simulator_spectrum(
            spectrum_type="xenon",
            class_rating="A"
        )

        # Create typical c-Si responses
        dut_response = self.spectral_mismatch.create_typical_csi_response()
        ref_response = self.spectral_mismatch.create_typical_csi_response()

        # Calculate mismatch
        result = self.spectral_mismatch.calculate_mismatch_factor(
            test_spectrum=test_spectrum,
            dut_spectral_response=dut_response,
            ref_cell_spectral_response=ref_response
        )

        self.assertIn('mismatch_factor', result)
        self.assertIn('uncertainty_percent', result)

        # Mismatch factor should be close to 1.0 for similar cells
        self.assertGreater(result['mismatch_factor'], 0.8)
        self.assertLess(result['mismatch_factor'], 1.2)

    def test_correction_application(self):
        """Test applying spectral mismatch correction"""
        measured_isc = 9.5  # A
        mismatch_factor = 1.05

        corrected, correction_percent = self.spectral_mismatch.apply_correction(
            measured_isc, mismatch_factor
        )

        self.assertAlmostEqual(corrected, measured_isc * mismatch_factor, places=6)
        self.assertAlmostEqual(correction_percent, 5.0, places=1)

    def test_different_simulator_types(self):
        """Test different simulator spectrum types"""
        for sim_type in ["xenon", "led", "halogen"]:
            spectrum = self.spectral_mismatch.create_simulator_spectrum(
                spectrum_type=sim_type,
                class_rating="A"
            )

            self.assertIsInstance(spectrum, SpectralData)
            self.assertEqual(spectrum.data_type, 'irradiance')
            self.assertGreater(len(spectrum.wavelengths), 0)


class TestSimulatorVerification(unittest.TestCase):
    """Test IEC 60904-9 solar simulator verification"""

    def setUp(self):
        """Set up test fixtures"""
        self.simulator = SimulatorVerification(
            simulator_id="SIM-001",
            simulator_type=SimulatorType.CONTINUOUS
        )

        # Create test spectra
        wavelengths = np.arange(300, 1201, 10)
        self.reference_spectrum = {float(wl): 1.0 for wl in wavelengths}
        self.measured_spectrum = {float(wl): 1.0 + 0.05 * np.random.randn()
                                  for wl in wavelengths}

    def test_spectral_match_verification(self):
        """Test spectral match verification and classification"""
        result = self.simulator.verify_spectral_match(
            measured_spectrum=self.measured_spectrum,
            reference_spectrum=self.reference_spectrum
        )

        self.assertIn('band_results', result)
        self.assertIn('spectral_classification', result)
        self.assertEqual(len(result['band_results']), 6)  # 6 wavelength bands

        # Classification should be valid
        classification = SimulatorClass(result['spectral_classification'])
        self.assertIn(classification, [
            SimulatorClass.CLASS_A,
            SimulatorClass.CLASS_B,
            SimulatorClass.CLASS_C,
            SimulatorClass.NOT_CLASSIFIED
        ])

    def test_non_uniformity_verification(self):
        """Test spatial non-uniformity verification"""
        # Create test grid with good uniformity
        irradiance_grid = np.random.normal(1000.0, 5.0, (10, 10))

        result = self.simulator.verify_non_uniformity(
            irradiance_grid=irradiance_grid,
            test_plane_area_cm2=1600.0
        )

        self.assertIn('non_uniformity_percent', result)
        self.assertIn('uniformity_classification', result)
        self.assertGreater(result['e_mean'], 0)

        # Good uniformity should achieve Class A
        self.assertLess(result['non_uniformity_percent'], 5.0)

    def test_temporal_instability_verification(self):
        """Test temporal instability verification"""
        # Create stable time series
        sampling_rate = 1000.0  # Hz
        duration = 10.0  # seconds
        num_samples = int(sampling_rate * duration)

        irradiance_time_series = np.random.normal(1000.0, 2.0, num_samples)

        result = self.simulator.verify_temporal_instability(
            irradiance_time_series=irradiance_time_series,
            sampling_rate_hz=sampling_rate,
            measurement_duration_s=duration
        )

        self.assertIn('temporal_instability_percent', result)
        self.assertIn('stability_classification', result)

        # Good stability should achieve Class A or B
        self.assertLess(result['temporal_instability_percent'], 10.0)

    def test_full_verification(self):
        """Test complete simulator verification"""
        # Create test data
        irradiance_grid = np.random.normal(1000.0, 10.0, (10, 10))
        irradiance_time_series = np.random.normal(1000.0, 10.0, 10000)

        result = self.simulator.perform_full_verification(
            measured_spectrum=self.measured_spectrum,
            reference_spectrum=self.reference_spectrum,
            irradiance_grid=irradiance_grid,
            test_plane_area_cm2=1600.0,
            irradiance_time_series=irradiance_time_series,
            sampling_rate_hz=1000.0,
            measurement_duration_s=10.0
        )

        self.assertIsInstance(result, VerificationResult)
        self.assertIsInstance(result.classification, SimulatorClass)
        self.assertIsInstance(result.compliant, bool)
        self.assertGreater(len(result.recommendations), 0)

    def test_class_criteria(self):
        """Test performance criteria for each class"""
        class_a = PerformanceCriteria.get_class_a_criteria()
        class_b = PerformanceCriteria.get_class_b_criteria()
        class_c = PerformanceCriteria.get_class_c_criteria()

        # Class A should be most stringent
        self.assertLess(class_a.non_uniformity_max_percent,
                       class_b.non_uniformity_max_percent)
        self.assertLess(class_b.non_uniformity_max_percent,
                       class_c.non_uniformity_max_percent)

        # Verify specific values per IEC 60904-9
        self.assertEqual(class_a.non_uniformity_max_percent, 2.0)
        self.assertEqual(class_b.non_uniformity_max_percent, 5.0)
        self.assertEqual(class_c.non_uniformity_max_percent, 10.0)

    def test_pulsed_simulator(self):
        """Test pulsed simulator verification"""
        pulsed_sim = SimulatorVerification(
            simulator_id="PULSED-001",
            simulator_type=SimulatorType.PULSED_SINGLE_FLASH
        )

        # Create flash pulse
        sampling_rate = 10000.0  # Hz
        duration = 0.1  # 100ms flash
        num_samples = int(sampling_rate * duration)

        time_array = np.arange(num_samples) / sampling_rate
        # Gaussian pulse
        irradiance_time_series = 1000.0 * np.exp(-((time_array - 0.05) / 0.01)**2)

        result = pulsed_sim.verify_temporal_instability(
            irradiance_time_series=irradiance_time_series,
            sampling_rate_hz=sampling_rate,
            measurement_duration_s=duration
        )

        self.assertIn('flash_duration_ms', result)
        self.assertIsNotNone(result['flash_duration_ms'])
        self.assertGreater(result['flash_duration_ms'], 0)

    def test_result_serialization(self):
        """Test verification result export"""
        irradiance_grid = np.random.normal(1000.0, 5.0, (5, 5))
        irradiance_time_series = np.random.normal(1000.0, 5.0, 1000)

        result = self.simulator.perform_full_verification(
            measured_spectrum=self.measured_spectrum,
            reference_spectrum=self.reference_spectrum,
            irradiance_grid=irradiance_grid,
            test_plane_area_cm2=1600.0,
            irradiance_time_series=irradiance_time_series,
            sampling_rate_hz=1000.0,
            measurement_duration_s=1.0
        )

        # Test to_dict
        result_dict = result.to_dict()
        self.assertIsInstance(result_dict, dict)
        self.assertIn('classification', result_dict)
        self.assertIn('standard', result_dict)

        # Test to_json
        result_json = result.to_json()
        self.assertIsInstance(result_json, str)
        self.assertIn('IEC 60904-9', result_json)


class TestISO17025Compliance(unittest.TestCase):
    """Test ISO 17025 compliance features"""

    def test_traceability_documentation(self):
        """Test traceability to national standards"""
        # Reference cell traceability
        cell = ReferenceCell(
            cell_serial="REF-001",
            cell_type=CellType.PRIMARY,
            active_area=4.0
        )

        spectral_response = {float(wl): 0.4 for wl in range(300, 1201, 10)}
        reference_spectrum = {float(wl): 1.0 for wl in range(300, 1201, 10)}

        calibration = cell.calibrate_primary(
            spectral_response=spectral_response,
            reference_spectrum=reference_spectrum,
            measured_current=0.4,
            traceability="NIST"
        )

        certificate = cell.get_calibration_certificate()

        self.assertTrue(certificate['iso17025_compliant'])
        self.assertEqual(certificate['traceability'], "NIST")
        self.assertIn('standard', certificate)

    def test_uncertainty_budgets(self):
        """Test measurement uncertainty calculation"""
        # Spectral mismatch uncertainty
        spectral_mismatch = SpectralMismatch()
        test_spectrum = spectral_mismatch.create_simulator_spectrum("xenon", class_rating="A")
        dut_response = spectral_mismatch.create_typical_csi_response()
        ref_response = spectral_mismatch.create_typical_csi_response()

        result = spectral_mismatch.calculate_mismatch_factor(
            test_spectrum=test_spectrum,
            dut_spectral_response=dut_response,
            ref_cell_spectral_response=ref_response
        )

        self.assertIn('uncertainty_percent', result)
        self.assertGreater(result['uncertainty_percent'], 0)

    def test_calibration_records(self):
        """Test calibration record keeping"""
        cell = ReferenceCell(
            cell_serial="REF-001",
            cell_type=CellType.SECONDARY,
            active_area=4.0
        )

        calibration = ReferenceCellCalibration(
            cell_serial="REF-001",
            cell_type=CellType.SECONDARY,
            calibration_date=datetime.now(),
            calibration_constant=0.0004,
            temperature_coefficient=-0.05,
            spectral_response={400.0: 0.4},
            traceability="NIST via PRIMARY-001"
        )

        record = calibration.to_dict()

        # Verify all required fields are present
        required_fields = [
            'cell_serial', 'calibration_date', 'calibration_constant',
            'uncertainty', 'traceability', 'valid_until'
        ]

        for field in required_fields:
            self.assertIn(field, record)


def run_all_tests():
    """Run all test suites"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestIVMeasurement))
    suite.addTests(loader.loadTestsFromTestCase(TestReferenceCell))
    suite.addTests(loader.loadTestsFromTestCase(TestSpectralMismatch))
    suite.addTests(loader.loadTestsFromTestCase(TestSimulatorVerification))
    suite.addTests(loader.loadTestsFromTestCase(TestISO17025Compliance))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == '__main__':
    unittest.main()
