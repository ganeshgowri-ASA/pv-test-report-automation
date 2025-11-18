"""
Unit tests for IEC 62804 PID Testing Protocol
"""

import pytest
import numpy as np

from ..iec_62804 import IEC62804, PIDClass
from ..base_protocol import TestStatus, Uncertainty


class TestIEC62804:
    """Test IEC 62804 protocol implementation"""

    @pytest.fixture
    def protocol(self):
        """Create protocol instance"""
        return IEC62804()

    @pytest.fixture
    def sample_pid_data_class_a(self):
        """Create sample PID test data - Class A (< 5% degradation)"""
        return {
            'initial_power': 300.0,
            'post_stress_power': 287.0,  # 4.3% degradation
            'stress_voltage': -1000,
            'stress_duration_hours': 96,
            'stress_temperature': 85,
            'stress_humidity': 85
        }

    @pytest.fixture
    def sample_pid_data_fail(self):
        """Create sample PID test data - Failed (> 20% degradation)"""
        return {
            'initial_power': 300.0,
            'post_stress_power': 230.0,  # 23.3% degradation
            'stress_voltage': -1000,
            'stress_duration_hours': 96,
            'stress_temperature': 85,
            'stress_humidity': 85
        }

    def test_protocol_initialization(self, protocol):
        """Test protocol initialization"""
        assert protocol.protocol_name == "IEC 62804-1"
        assert protocol.STRESS_VOLTAGE == 1000
        assert protocol.STRESS_DURATION == 96
        assert protocol.CLASS_A_THRESHOLD == 5.0
        assert protocol.CLASS_B_THRESHOLD == 20.0

    def test_data_validation_valid(self, protocol, sample_pid_data_class_a):
        """Test validation with valid data"""
        assert protocol.validate_data(sample_pid_data_class_a) is True

    def test_data_validation_missing_field(self, protocol):
        """Test validation with missing required field"""
        data = {
            'initial_power': 300.0,
            'post_stress_power': 285.0
            # Missing other required fields
        }
        assert protocol.validate_data(data) is False

    def test_degradation_calculation_class_a(self, protocol, sample_pid_data_class_a):
        """Test degradation calculation for Class A result"""
        result = protocol.calculate(sample_pid_data_class_a)

        degradation = result.measurements['power_degradation']
        assert isinstance(degradation, Uncertainty)

        # Should be around 4.3%
        assert 4.0 < degradation.value < 5.0

    def test_pid_classification_class_a(self, protocol, sample_pid_data_class_a):
        """Test PID classification - Class A"""
        result = protocol.calculate(sample_pid_data_class_a)

        pid_class = result.measurements['PID_classification']
        assert pid_class == PIDClass.CLASS_A

        # Should pass
        assert result.status == TestStatus.PASS

    def test_pid_classification_class_b(self, protocol):
        """Test PID classification - Class B"""
        data = {
            'initial_power': 300.0,
            'post_stress_power': 255.0,  # 15% degradation
            'stress_voltage': -1000,
            'stress_duration_hours': 96,
            'stress_temperature': 85,
            'stress_humidity': 85
        }

        result = protocol.calculate(data)

        pid_class = result.measurements['PID_classification']
        assert pid_class == PIDClass.CLASS_B

    def test_pid_classification_fail(self, protocol, sample_pid_data_fail):
        """Test PID classification - Fail"""
        result = protocol.calculate(sample_pid_data_fail)

        pid_class = result.measurements['PID_classification']
        assert pid_class == PIDClass.FAIL

        # Should fail
        assert result.status == TestStatus.FAIL

    def test_degradation_rate(self, protocol, sample_pid_data_class_a):
        """Test degradation rate calculation"""
        result = protocol.calculate(sample_pid_data_class_a)

        deg_rate = result.measurements['degradation_rate_per_hour']
        assert isinstance(deg_rate, Uncertainty)

        # For 4.3% over 96 hours = ~0.045%/hour
        assert 0.03 < deg_rate.value < 0.06

    def test_time_series_analysis(self, protocol):
        """Test time-series degradation analysis"""
        # Simulate degradation over time
        hours = np.linspace(0, 96, 25)
        initial_power = 300.0
        degradation_rate = -0.05  # %/hour

        # Power decreases linearly
        powers = initial_power * (1 + degradation_rate * hours / 100)

        data = {
            'initial_power': 300.0,
            'post_stress_power': powers[-1],
            'stress_voltage': -1000,
            'stress_duration_hours': 96,
            'stress_temperature': 85,
            'stress_humidity': 85,
            'time_series': {
                'hours': hours.tolist(),
                'powers': powers.tolist()
            }
        }

        result = protocol.calculate(data)

        time_analysis = result.measurements['time_series_analysis']
        assert isinstance(time_analysis, dict)

        # Should have calculated degradation rate
        assert 'linear_degradation_rate_pct_per_hour' in time_analysis
        assert 'r_squared' in time_analysis
        assert 'time_to_5pct_degradation_hours' in time_analysis

        # Should have good linear fit
        assert time_analysis['r_squared'] > 0.90

    def test_leakage_current_analysis(self, protocol):
        """Test leakage current analysis"""
        data = {
            'initial_power': 300.0,
            'post_stress_power': 285.0,
            'stress_voltage': -1000,
            'stress_duration_hours': 96,
            'stress_temperature': 85,
            'stress_humidity': 85,
            'leakage_current': {
                'hours': [0, 24, 48, 72, 96],
                'current_mA': [2.5, 2.6, 2.7, 2.6, 2.5]
            }
        }

        result = protocol.calculate(data)

        leakage = result.measurements['leakage_current_analysis']
        assert isinstance(leakage, dict)

        assert 'initial_leakage_mA' in leakage
        assert 'max_leakage_mA' in leakage
        assert 'mean_leakage_mA' in leakage
        assert 'leakage_stable' in leakage

    def test_recovery_analysis(self, protocol):
        """Test PID recovery analysis"""
        data = {
            'initial_power': 300.0,
            'post_stress_power': 270.0,  # 10% degradation
            'stress_voltage': -1000,
            'stress_duration_hours': 96,
            'stress_temperature': 85,
            'stress_humidity': 85,
            'recovery_data': {
                'final_power': 298.0,  # Nearly full recovery
                'duration_hours': 96
            }
        }

        result = protocol.calculate(data)

        recovery = result.measurements['recovery_analysis']
        assert isinstance(recovery, dict)

        assert 'recovered_power_W' in recovery
        assert 'recovery_percentage' in recovery
        assert 'residual_degradation_pct' in recovery
        assert 'full_recovery' in recovery

        # Should show good recovery
        assert recovery['recovery_percentage'] > 80
        assert recovery['residual_degradation_pct'] < 2

    def test_reference_comparison(self, protocol):
        """Test comparison with reference module"""
        data = {
            'initial_power': 300.0,
            'post_stress_power': 285.0,
            'stress_voltage': -1000,
            'stress_duration_hours': 96,
            'stress_temperature': 85,
            'stress_humidity': 85,
            'reference_module_power': {
                'initial': 300.0,
                'final': 240.0  # Reference degraded more (20%)
            }
        }

        result = protocol.calculate(data)

        comparison = result.measurements['reference_comparison']
        assert isinstance(comparison, dict)

        assert 'reference_degradation_pct' in comparison
        assert 'test_degradation_pct' in comparison
        assert 'better_than_reference' in comparison

        # Test module should perform better than reference
        assert comparison['better_than_reference'] is True

    def test_pass_fail_criteria(self, protocol, sample_pid_data_class_a):
        """Test pass/fail criteria application"""
        result = protocol.calculate(sample_pid_data_class_a)

        criteria = result.pass_fail_criteria

        assert 'passes_class_A' in criteria
        assert 'passes_class_B' in criteria

        # Class A data should pass both
        assert criteria['passes_class_A'] is True
        assert criteria['passes_class_B'] is True

    def test_calculation_example(self, protocol, sample_pid_data_class_a):
        """Test complete calculation with example data"""
        result = protocol.calculate(sample_pid_data_class_a)

        # Verify all expected measurements
        assert 'power_degradation' in result.measurements
        assert 'PID_classification' in result.measurements
        assert 'degradation_rate_per_hour' in result.measurements

        # Print example results
        print("\n--- IEC 62804 Calculation Example ---")
        print(f"Power degradation: {result.measurements['power_degradation']}")
        print(f"PID Classification: {result.measurements['PID_classification']}")
        print(f"Degradation rate: {result.measurements['degradation_rate_per_hour'].value:.4f} %/hour")
        print(f"Test status: {result.status.value}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
