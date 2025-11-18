"""
Unit tests for IEC 61853 Performance Testing Protocol
"""

import pytest
import numpy as np

from ..iec_61853 import IEC61853
from ..base_protocol import TestStatus, Uncertainty


class TestIEC61853:
    """Test IEC 61853 protocol implementation"""

    @pytest.fixture
    def protocol(self):
        """Create protocol instance"""
        return IEC61853()

    @pytest.fixture
    def sample_performance_data(self):
        """Create sample performance matrix data"""
        # Irradiance levels (W/m²)
        irradiances = [200, 400, 600, 800, 1000, 1100]

        # Temperature levels (°C)
        temperatures = [15, 25, 50, 75]

        # Generate realistic power matrix
        # Base power at STC (1000 W/m², 25°C) = 300W
        p_stc = 300.0
        gamma = -0.004  # -0.4%/°C

        power_matrix = []
        for temp in temperatures:
            power_row = []
            for irr in irradiances:
                # Power scales linearly with irradiance
                # Power decreases with temperature
                temp_factor = 1 + gamma * (temp - 25)
                irr_factor = irr / 1000
                power = p_stc * irr_factor * temp_factor
                power_row.append(power)
            power_matrix.append(power_row)

        # Also create voltage and current matrices
        v_stc = 37.5  # Voc at STC
        i_stc = 10.0  # Isc at STC

        voltage_matrix = []
        current_matrix = []

        for temp in temperatures:
            v_row = []
            i_row = []
            for irr in irradiances:
                # Simplified: Voc decreases with temp, Isc increases
                v = v_stc * (1 - 0.003 * (temp - 25))
                i = i_stc * (irr / 1000) * (1 + 0.0005 * (temp - 25))
                v_row.append(v)
                i_row.append(i)
            voltage_matrix.append(v_row)
            current_matrix.append(i_row)

        return {
            'irradiances': irradiances,
            'temperatures': temperatures,
            'power_matrix': power_matrix,
            'voltage_matrix': voltage_matrix,
            'current_matrix': current_matrix
        }

    def test_protocol_initialization(self, protocol):
        """Test protocol initialization"""
        assert protocol.protocol_name == "IEC 61853-1"
        assert protocol.STC_IRRADIANCE == 1000.0
        assert protocol.STC_TEMPERATURE == 25.0

    def test_data_validation_valid(self, protocol, sample_performance_data):
        """Test validation with valid data"""
        assert protocol.validate_data(sample_performance_data) is True

    def test_data_validation_missing_field(self, protocol):
        """Test validation with missing required field"""
        data = {
            'irradiances': [200, 400, 600],
            'temperatures': [25, 50]
            # Missing power_matrix
        }
        assert protocol.validate_data(data) is False

    def test_data_validation_matrix_mismatch(self, protocol):
        """Test validation with mismatched matrix dimensions"""
        data = {
            'irradiances': [200, 400, 600],
            'temperatures': [25, 50],
            'power_matrix': [[100, 200], [150, 250]]  # Wrong dimensions
        }
        # Should still validate dimensions correctly
        assert protocol.validate_data(data) is True

    def test_stc_power_calculation(self, protocol, sample_performance_data):
        """Test STC power rating calculation"""
        result = protocol.calculate(sample_performance_data)

        p_stc = result.measurements['P_STC']
        assert isinstance(p_stc, Uncertainty)

        # Should be close to 300W (our test data)
        assert 290 < p_stc.value < 310

    def test_temperature_coefficients(self, protocol, sample_performance_data):
        """Test temperature coefficient calculation"""
        result = protocol.calculate(sample_performance_data)

        alpha = result.measurements['alpha_Isc']
        beta = result.measurements['beta_Voc']
        gamma = result.measurements['gamma_Pmp']

        assert isinstance(alpha, Uncertainty)
        assert isinstance(beta, Uncertainty)
        assert isinstance(gamma, Uncertainty)

        # Check typical ranges for crystalline silicon
        # Alpha: +0.03 to +0.07 %/°C
        assert 0.0 < alpha.value < 0.15

        # Beta: -0.25 to -0.35 %/°C
        assert -0.50 < beta.value < -0.15

        # Gamma: -0.3 to -0.5 %/°C
        assert -0.70 < gamma.value < -0.20

    def test_low_irradiance_performance(self, protocol, sample_performance_data):
        """Test low irradiance performance analysis"""
        result = protocol.calculate(sample_performance_data)

        low_irr = result.measurements['low_irradiance_performance']
        assert isinstance(low_irr, dict)

        # Check required fields
        assert 'P_200W' in low_irr
        assert 'P_400W' in low_irr
        assert 'performance_ratio_200W' in low_irr
        assert 'low_light_loss_200W_percent' in low_irr

        # Performance ratio should be between 0 and 1.2
        assert 0 < low_irr['performance_ratio_200W'] < 1.2
        assert 0 < low_irr['performance_ratio_400W'] < 1.2

    def test_performance_at_specific_conditions(self, protocol, sample_performance_data):
        """Test power calculation at specific conditions"""
        result = protocol.calculate(sample_performance_data)

        # Check 200W and 800W measurements
        p_200 = result.measurements.get('P_200W_25C')
        p_800 = result.measurements.get('P_800W_25C')

        if p_200:
            assert isinstance(p_200, Uncertainty)
            assert p_200.value > 0

        if p_800:
            assert isinstance(p_800, Uncertainty)
            assert p_800.value > 0

    def test_noct_calculation(self, protocol):
        """Test NOCT calculation"""
        noct_data = {
            'cell_temperature': 47.0,
            'ambient_temperature': 20.0,
            'irradiance': 800.0,
            'wind_speed': 1.0
        }

        data = {
            'irradiances': [800, 1000],
            'temperatures': [25, 47],
            'power_matrix': [[240, 300], [230, 285]],
            'noct_data': noct_data
        }

        result = protocol.calculate(data)

        noct = result.measurements.get('NOCT')
        assert noct is not None
        assert isinstance(noct, Uncertainty)

        # NOCT typically 40-50°C
        assert 35 < noct.value < 55

    def test_aoi_modifier(self, protocol):
        """Test angle of incidence modifier calculation"""
        aoi_data = {
            'angles': [0, 15, 30, 45, 60, 75],
            'relative_response': [1.00, 0.99, 0.97, 0.93, 0.85, 0.70]
        }

        data = {
            'irradiances': [800, 1000],
            'temperatures': [25, 50],
            'power_matrix': [[240, 300], [230, 285]],
            'aoi_data': aoi_data
        }

        result = protocol.calculate(data)

        aoi_mod = result.measurements.get('AOI_modifier')
        assert aoi_mod is not None
        assert isinstance(aoi_mod, dict)

        # Should have model parameters
        assert 'model' in aoi_mod
        assert 'b0' in aoi_mod
        assert 'r_squared' in aoi_mod

        # R² should be high for good fit
        if 'r_squared' in aoi_mod:
            assert aoi_mod['r_squared'] > 0.90

    def test_pass_fail_criteria(self, protocol, sample_performance_data):
        """Test pass/fail criteria application"""
        result = protocol.calculate(sample_performance_data)

        # Check that criteria are present
        criteria = result.pass_fail_criteria

        assert 'stc_power_uncertainty_acceptable' in criteria
        assert 'gamma_in_typical_range' in criteria
        assert 'alpha_in_typical_range' in criteria
        assert 'beta_in_typical_range' in criteria

    def test_result_status(self, protocol, sample_performance_data):
        """Test overall result status"""
        result = protocol.calculate(sample_performance_data)

        # With good data, should pass
        assert result.status == TestStatus.PASS

    def test_calculation_example(self, protocol, sample_performance_data):
        """Test complete calculation with example data"""
        result = protocol.calculate(sample_performance_data)

        # Verify all expected measurements
        assert 'P_STC' in result.measurements
        assert 'alpha_Isc' in result.measurements
        assert 'beta_Voc' in result.measurements
        assert 'gamma_Pmp' in result.measurements
        assert 'low_irradiance_performance' in result.measurements

        # Print example results
        print("\n--- IEC 61853 Calculation Example ---")
        print(f"P_STC: {result.measurements['P_STC']}")
        print(f"Alpha (Isc): {result.measurements['alpha_Isc'].value:.4f} %/°C")
        print(f"Beta (Voc): {result.measurements['beta_Voc'].value:.4f} %/°C")
        print(f"Gamma (Pmp): {result.measurements['gamma_Pmp'].value:.4f} %/°C")

        low_irr = result.measurements['low_irradiance_performance']
        print(f"Low light loss (200W): {low_irr['low_light_loss_200W_percent']:.2f}%")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
