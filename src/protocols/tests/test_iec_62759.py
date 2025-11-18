"""
Unit tests for IEC 62759 Transportation Testing Protocol
"""

import pytest
import numpy as np

from ..iec_62759 import IEC62759, DefectSeverity, TransportationMode
from ..base_protocol import TestStatus, Uncertainty


class TestIEC62759:
    """Test IEC 62759 protocol implementation"""

    @pytest.fixture
    def protocol(self):
        """Create protocol instance"""
        return IEC62759()

    @pytest.fixture
    def sample_transport_data_pass(self):
        """Create sample transportation test data - passing"""
        return {
            'initial_power': 300.0,
            'final_power': 296.5,  # 1.2% degradation (< 5%)
            'transportation_mode': 'SEA',
            'mechanical_tests': [
                {
                    'type': 'static_front',
                    'load': 2400,
                    'passed': True,
                    'defects_found': [],
                    'duration': '30min'
                },
                {
                    'type': 'static_back',
                    'load': 2400,
                    'passed': True,
                    'defects_found': [],
                    'duration': '30min'
                },
                {
                    'type': 'vibration',
                    'load': 1.5,  # g's
                    'passed': True,
                    'defects_found': [],
                    'duration': '3hours'
                }
            ],
            'visual_inspections': [
                {
                    'time': 'before',
                    'defects': [],
                    'overall_condition': 'excellent'
                },
                {
                    'time': 'after',
                    'defects': [
                        {
                            'type': 'minor_scratch',
                            'severity': 'MINOR',
                            'location': 'frame'
                        }
                    ],
                    'overall_condition': 'good'
                }
            ],
            'insulation_resistance': {
                'value': 150.0  # MΩ
            }
        }

    @pytest.fixture
    def sample_transport_data_fail(self):
        """Create sample transportation test data - failing"""
        return {
            'initial_power': 300.0,
            'final_power': 270.0,  # 10% degradation (> 5%)
            'transportation_mode': 'ROAD',
            'mechanical_tests': [
                {
                    'type': 'static_front',
                    'load': 2400,
                    'passed': False,
                    'defects_found': ['cell_crack'],
                    'duration': '30min'
                }
            ],
            'visual_inspections': [
                {
                    'time': 'before',
                    'defects': [],
                    'overall_condition': 'excellent'
                },
                {
                    'time': 'after',
                    'defects': [
                        {
                            'type': 'cell_crack',
                            'severity': 'MAJOR',
                            'location': 'center'
                        }
                    ],
                    'overall_condition': 'poor'
                }
            ]
        }

    def test_protocol_initialization(self, protocol):
        """Test protocol initialization"""
        assert protocol.protocol_name == "IEC 62759-1"
        assert protocol.STATIC_LOAD_FRONT == 2400
        assert protocol.MAX_POWER_DEGRADATION == 5.0

    def test_data_validation_valid(self, protocol, sample_transport_data_pass):
        """Test validation with valid data"""
        assert protocol.validate_data(sample_transport_data_pass) is True

    def test_data_validation_missing_field(self, protocol):
        """Test validation with missing required field"""
        data = {
            'initial_power': 300.0,
            'final_power': 295.0
            # Missing other required fields
        }
        assert protocol.validate_data(data) is False

    def test_power_degradation_calculation(self, protocol, sample_transport_data_pass):
        """Test power degradation calculation"""
        result = protocol.calculate(sample_transport_data_pass)

        degradation = result.measurements['power_degradation']
        assert isinstance(degradation, Uncertainty)

        # Should be around 1.2%
        assert 0.5 < degradation.value < 2.0

    def test_mechanical_tests_analysis(self, protocol, sample_transport_data_pass):
        """Test mechanical test analysis"""
        result = protocol.calculate(sample_transport_data_pass)

        mech_analysis = result.measurements['mechanical_test_results']
        assert isinstance(mech_analysis, dict)

        assert 'total_tests' in mech_analysis
        assert 'tests_passed' in mech_analysis
        assert 'tests_failed' in mech_analysis
        assert 'pass_rate_percent' in mech_analysis

        # All tests should pass
        assert mech_analysis['tests_passed'] == 3
        assert mech_analysis['tests_failed'] == 0
        assert mech_analysis['pass_rate_percent'] == 100.0

    def test_visual_inspection_analysis(self, protocol, sample_transport_data_pass):
        """Test visual inspection analysis"""
        result = protocol.calculate(sample_transport_data_pass)

        visual_analysis = result.measurements['visual_inspection_results']
        assert isinstance(visual_analysis, dict)

        assert 'total_inspections' in visual_analysis
        assert 'defects_summary' in visual_analysis
        assert 'worst_severity' in visual_analysis

        # Should have minor defect
        assert visual_analysis['worst_severity'] == 'MINOR'

    def test_insulation_resistance_analysis(self, protocol, sample_transport_data_pass):
        """Test insulation resistance analysis"""
        result = protocol.calculate(sample_transport_data_pass)

        insulation = result.measurements['insulation_resistance']
        assert isinstance(insulation, Uncertainty)

        # Should be 150 MΩ
        assert 140 < insulation.value < 160

    def test_environmental_tests_analysis(self, protocol):
        """Test environmental test analysis"""
        data = {
            'initial_power': 300.0,
            'final_power': 295.0,
            'mechanical_tests': [],
            'visual_inspections': [
                {'time': 'before', 'defects': [], 'overall_condition': 'good'},
                {'time': 'after', 'defects': [], 'overall_condition': 'good'}
            ],
            'environmental_tests': [
                {
                    'type': 'thermal_cycle',
                    'temperature': 85,
                    'humidity': 85,
                    'duration_hours': 48
                },
                {
                    'type': 'cold_exposure',
                    'temperature': -40,
                    'duration_hours': 24
                }
            ]
        }

        result = protocol.calculate(data)

        env_analysis = result.measurements['environmental_test_results']
        assert isinstance(env_analysis, dict)

        assert 'total_tests' in env_analysis
        assert 'test_types' in env_analysis

    def test_vibration_analysis(self, protocol):
        """Test vibration response analysis"""
        # Simulate vibration sweep
        frequencies = np.linspace(1, 200, 100)
        # Add resonance peaks at 15Hz and 80Hz
        accelerations = 0.5 + 0.3 * np.exp(-((frequencies - 15)**2) / 20)
        accelerations += 0.2 * np.exp(-((frequencies - 80)**2) / 50)

        data = {
            'initial_power': 300.0,
            'final_power': 295.0,
            'mechanical_tests': [],
            'visual_inspections': [
                {'time': 'before', 'defects': [], 'overall_condition': 'good'},
                {'time': 'after', 'defects': [], 'overall_condition': 'good'}
            ],
            'vibration_data': {
                'frequencies': frequencies.tolist(),
                'accelerations': accelerations.tolist(),
                'axes': ['x', 'y', 'z'],
                'duration': 1.0
            }
        }

        result = protocol.calculate(data)

        vib_analysis = result.measurements['vibration_analysis']
        assert isinstance(vib_analysis, dict)

        assert 'frequency_range_Hz' in vib_analysis
        assert 'max_acceleration_g' in vib_analysis
        assert 'resonance_peaks' in vib_analysis

        # Should detect resonance peaks
        assert 'resonance_peaks_count' in vib_analysis

    def test_durability_score_excellent(self, protocol, sample_transport_data_pass):
        """Test durability score calculation - excellent performance"""
        result = protocol.calculate(sample_transport_data_pass)

        durability = result.measurements['durability_score']
        assert isinstance(durability, dict)

        assert 'score' in durability
        assert 'rating' in durability

        # Should have high score (>90)
        assert durability['score'] > 90
        assert durability['rating'] in ['Excellent', 'Good']

    def test_durability_score_fail(self, protocol, sample_transport_data_fail):
        """Test durability score calculation - poor performance"""
        result = protocol.calculate(sample_transport_data_fail)

        durability = result.measurements['durability_score']
        assert isinstance(durability, dict)

        # Should have lower score due to major defects
        assert durability['score'] < 80

    def test_pass_criteria_passing(self, protocol, sample_transport_data_pass):
        """Test pass/fail criteria - passing case"""
        result = protocol.calculate(sample_transport_data_pass)

        criteria = result.pass_fail_criteria

        assert 'power_degradation_acceptable' in criteria
        assert 'no_critical_defects' in criteria
        assert 'no_major_defects' in criteria
        assert 'insulation_resistance_adequate' in criteria

        # Should pass all criteria
        assert criteria['power_degradation_acceptable'] is True
        assert criteria['no_critical_defects'] is True
        assert criteria['no_major_defects'] is True

        assert result.status == TestStatus.PASS

    def test_pass_criteria_failing(self, protocol, sample_transport_data_fail):
        """Test pass/fail criteria - failing case"""
        result = protocol.calculate(sample_transport_data_fail)

        criteria = result.pass_fail_criteria

        # Should fail due to major defects and high degradation
        assert result.status in [TestStatus.FAIL, TestStatus.WARNING]

    def test_critical_defect_failure(self, protocol):
        """Test that critical defects cause failure"""
        data = {
            'initial_power': 300.0,
            'final_power': 295.0,  # Good power
            'mechanical_tests': [],
            'visual_inspections': [
                {
                    'time': 'before',
                    'defects': [],
                    'overall_condition': 'excellent'
                },
                {
                    'time': 'after',
                    'defects': [
                        {
                            'type': 'junction_box_detached',
                            'severity': 'CRITICAL',
                            'location': 'back'
                        }
                    ],
                    'overall_condition': 'critical'
                }
            ]
        }

        result = protocol.calculate(data)

        # Should fail due to critical defect
        assert result.status == TestStatus.FAIL
        assert 'Critical visual defects detected' in result.notes

    def test_low_insulation_resistance_failure(self, protocol):
        """Test that low insulation resistance causes failure"""
        data = {
            'initial_power': 300.0,
            'final_power': 295.0,
            'mechanical_tests': [],
            'visual_inspections': [
                {'time': 'before', 'defects': [], 'overall_condition': 'good'},
                {'time': 'after', 'defects': [], 'overall_condition': 'good'}
            ],
            'insulation_resistance': {
                'value': 25.0  # Below minimum of 40 MΩ
            }
        }

        result = protocol.calculate(data)

        # Should fail due to low insulation resistance
        assert result.status == TestStatus.FAIL
        assert 'Insulation resistance' in result.notes

    def test_calculation_example(self, protocol, sample_transport_data_pass):
        """Test complete calculation with example data"""
        result = protocol.calculate(sample_transport_data_pass)

        # Verify all expected measurements
        assert 'power_degradation' in result.measurements
        assert 'mechanical_test_results' in result.measurements
        assert 'visual_inspection_results' in result.measurements
        assert 'insulation_resistance' in result.measurements
        assert 'durability_score' in result.measurements

        # Print example results
        print("\n--- IEC 62759 Calculation Example ---")
        print(f"Power degradation: {result.measurements['power_degradation']}")

        mech = result.measurements['mechanical_test_results']
        print(f"Mechanical tests: {mech['tests_passed']}/{mech['total_tests']} passed")

        visual = result.measurements['visual_inspection_results']
        print(f"Visual inspection: {visual['worst_severity']} defects")

        durability = result.measurements['durability_score']
        print(f"Durability score: {durability['score']:.0f}/100 ({durability['rating']})")
        print(f"Test status: {result.status.value}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
