"""
Unit tests for IEC 60904 I-V Characteristics Protocol
"""

import pytest
import numpy as np

from ..iec_60904 import IEC60904
from ..base_protocol import TestStatus, Uncertainty


class TestIEC60904:
    """Test IEC 60904 protocol implementation"""

    @pytest.fixture
    def protocol(self):
        """Create protocol instance"""
        return IEC60904()

    @pytest.fixture
    def sample_iv_data(self):
        """Create sample I-V curve data"""
        # Simulate typical crystalline silicon module
        voltage = np.linspace(0, 45, 50)
        # Simplified I-V curve: I = Isc * (1 - V/Voc)^0.5
        isc = 9.5
        voc = 45.0
        current = isc * (1 - voltage / voc) ** 0.5

        return {
            'voltage': voltage.tolist(),
            'current': current.tolist(),
            'irradiance': 1000.0,
            'temperature': 25.0,
            'area': 1.95,
            'spectrum': 'AM1.5G'
        }

    def test_protocol_initialization(self, protocol):
        """Test protocol initialization"""
        assert protocol.protocol_name == "IEC 60904-1"
        assert protocol.STC_IRRADIANCE == 1000.0
        assert protocol.STC_TEMPERATURE == 25.0

    def test_data_validation_valid(self, protocol, sample_iv_data):
        """Test validation with valid data"""
        assert protocol.validate_data(sample_iv_data) is True

    def test_data_validation_missing_field(self, protocol):
        """Test validation with missing required field"""
        data = {
            'voltage': [0, 10, 20],
            'current': [10, 8, 6]
            # Missing other required fields
        }
        assert protocol.validate_data(data) is False

    def test_data_validation_length_mismatch(self, protocol):
        """Test validation with mismatched array lengths"""
        data = {
            'voltage': [0, 10, 20, 30],
            'current': [10, 8, 6],  # Different length
            'irradiance': 1000,
            'temperature': 25,
            'area': 2.0
        }
        assert protocol.validate_data(data) is False

    def test_isc_calculation(self, protocol, sample_iv_data):
        """Test short-circuit current calculation"""
        result = protocol.calculate(sample_iv_data)

        isc = result.measurements['Isc']
        assert isinstance(isc, Uncertainty)
        assert isc.value > 9.0  # Should be close to 9.5A
        assert isc.value < 10.0

    def test_voc_calculation(self, protocol, sample_iv_data):
        """Test open-circuit voltage calculation"""
        result = protocol.calculate(sample_iv_data)

        voc = result.measurements['Voc']
        assert isinstance(voc, Uncertainty)
        assert voc.value > 44.0  # Should be close to 45V
        assert voc.value < 46.0

    def test_mpp_calculation(self, protocol, sample_iv_data):
        """Test maximum power point calculation"""
        result = protocol.calculate(sample_iv_data)

        pmp = result.measurements['Pmp']
        vmp = result.measurements['Vmp']
        imp = result.measurements['Imp']

        assert isinstance(pmp, Uncertainty)
        assert isinstance(vmp, Uncertainty)
        assert isinstance(imp, Uncertainty)

        # Pmp should be positive
        assert pmp.value > 0

        # Vmp should be between 0 and Voc
        assert 0 < vmp.value < result.measurements['Voc'].value

        # Imp should be between 0 and Isc
        assert 0 < imp.value < result.measurements['Isc'].value

        # Verify P = V × I at MPP
        assert np.isclose(pmp.value, vmp.value * imp.value, rtol=0.01)

    def test_fill_factor_calculation(self, protocol, sample_iv_data):
        """Test fill factor calculation"""
        result = protocol.calculate(sample_iv_data)

        ff = result.measurements['FF']
        assert isinstance(ff, Uncertainty)

        # Fill factor should be between 0 and 1
        assert 0 < ff.value < 1

        # For good crystalline silicon: 0.7 < FF < 0.85
        assert 0.6 < ff.value < 0.9

    def test_efficiency_calculation(self, protocol, sample_iv_data):
        """Test efficiency calculation"""
        result = protocol.calculate(sample_iv_data)

        efficiency = result.measurements['Efficiency']
        assert isinstance(efficiency, Uncertainty)

        # Efficiency should be positive and reasonable (10-25% for Si)
        assert 0 < efficiency.value < 30

    def test_series_resistance(self, protocol, sample_iv_data):
        """Test series resistance calculation"""
        result = protocol.calculate(sample_iv_data)

        rs = result.measurements['Rs']
        assert isinstance(rs, Uncertainty)

        # Series resistance should be positive and small
        assert rs.value >= 0
        assert rs.value < 20  # Typically < 5Ω for good modules

    def test_shunt_resistance(self, protocol, sample_iv_data):
        """Test shunt resistance calculation"""
        result = protocol.calculate(sample_iv_data)

        rsh = result.measurements['Rsh']
        assert isinstance(rsh, Uncertainty)

        # Shunt resistance should be positive and large
        assert rsh.value > 0

    def test_stc_correction(self, protocol):
        """Test STC correction for non-STC conditions"""
        # Data at different conditions
        voltage = np.linspace(0, 42, 50)
        current = 9.8 * (1 - voltage / 42) ** 0.5

        data = {
            'voltage': voltage.tolist(),
            'current': current.tolist(),
            'irradiance': 800.0,  # Non-STC
            'temperature': 40.0,   # Non-STC
            'area': 1.95,
            'temp_coefficients': {
                'alpha_isc': 0.05,
                'beta_voc': -0.30,
                'gamma_pmp': -0.40
            }
        }

        result = protocol.calculate(data)

        # Should include STC correction
        assert 'STC_corrected' in result.measurements

        stc_params = result.measurements['STC_corrected']
        assert 'Isc_STC' in stc_params
        assert 'Voc_STC' in stc_params
        assert 'Pmp_STC' in stc_params

    def test_pass_fail_criteria(self, protocol, sample_iv_data):
        """Test pass/fail criteria application"""
        result = protocol.calculate(sample_iv_data)

        # Check that criteria are present
        assert 'data_quality_acceptable' in result.pass_fail_criteria
        assert 'fill_factor_acceptable' in result.pass_fail_criteria
        assert 'series_resistance_acceptable' in result.pass_fail_criteria
        assert 'shunt_resistance_acceptable' in result.pass_fail_criteria

    def test_result_status(self, protocol, sample_iv_data):
        """Test overall result status"""
        result = protocol.calculate(sample_iv_data)

        # With good data, should pass
        assert result.status == TestStatus.PASS

    def test_low_quality_data(self, protocol):
        """Test with noisy/low quality data"""
        # Add noise to simulate poor measurement
        voltage = np.linspace(0, 45, 20)  # Fewer points
        current = 9.5 * (1 - voltage / 45) ** 0.5
        current += np.random.normal(0, 0.5, len(current))  # Add noise

        data = {
            'voltage': voltage.tolist(),
            'current': current.tolist(),
            'irradiance': 1000.0,
            'temperature': 25.0,
            'area': 1.95
        }

        result = protocol.calculate(data)

        # Should still complete but may have warnings
        assert result is not None
        assert 'Pmp' in result.measurements

    def test_calculation_example(self, protocol, sample_iv_data):
        """Test complete calculation with example data"""
        result = protocol.calculate(sample_iv_data)

        # Verify all expected measurements are present
        expected_measurements = [
            'Isc', 'Voc', 'Pmp', 'Vmp', 'Imp',
            'FF', 'Efficiency', 'Rs', 'Rsh'
        ]

        for measurement in expected_measurements:
            assert measurement in result.measurements

        # Print example results (for documentation)
        print("\n--- IEC 60904 Calculation Example ---")
        print(f"Isc: {result.measurements['Isc']}")
        print(f"Voc: {result.measurements['Voc']}")
        print(f"Pmp: {result.measurements['Pmp']}")
        print(f"FF: {result.measurements['FF'].value:.3f}")
        print(f"Efficiency: {result.measurements['Efficiency'].value:.2f}%")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
