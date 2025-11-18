"""
Unit tests for base protocol functionality
"""

import pytest
import numpy as np
from datetime import datetime

from ..base_protocol import (
    BaseProtocol, ProtocolResult, Uncertainty, TestStatus, DataQuality
)


class TestProtocolImpl(BaseProtocol):
    """Test implementation of BaseProtocol"""

    def __init__(self):
        super().__init__("TEST-001", "1.0")

    def validate_data(self, data):
        return 'value' in data

    def calculate(self, data):
        result = self.create_result()
        result.add_measurement('test_value', data['value'])
        return result


class TestUncertainty:
    """Test Uncertainty class"""

    def test_uncertainty_creation(self):
        """Test creating uncertainty object"""
        unc = Uncertainty(
            value=100.0,
            standard_uncertainty=2.0,
            coverage_factor=2.0
        )

        assert unc.value == 100.0
        assert unc.standard_uncertainty == 2.0
        assert unc.expanded_uncertainty == 4.0

    def test_relative_uncertainty(self):
        """Test relative uncertainty calculation"""
        unc = Uncertainty(value=100.0, standard_uncertainty=2.0)
        assert unc.relative_uncertainty == 2.0  # 2%

    def test_uncertainty_sources(self):
        """Test uncertainty with sources"""
        sources = {
            'sensor': 1.0,
            'calibration': 0.5,
            'environment': 0.3
        }
        unc = Uncertainty(
            value=100.0,
            standard_uncertainty=1.2,
            sources=sources
        )

        assert len(unc.sources) == 3
        assert unc.sources['sensor'] == 1.0

    def test_uncertainty_to_dict(self):
        """Test uncertainty serialization"""
        unc = Uncertainty(value=100.0, standard_uncertainty=2.0)
        data = unc.to_dict()

        assert data['value'] == 100.0
        assert data['standard_uncertainty'] == 2.0
        assert 'relative_uncertainty_percent' in data


class TestProtocolResult:
    """Test ProtocolResult class"""

    def test_result_creation(self):
        """Test creating protocol result"""
        result = ProtocolResult(
            protocol_name="TEST-001",
            test_date=datetime.now(),
            status=TestStatus.PASS,
            measurements={}
        )

        assert result.protocol_name == "TEST-001"
        assert result.status == TestStatus.PASS

    def test_add_measurement(self):
        """Test adding measurements"""
        result = ProtocolResult(
            protocol_name="TEST-001",
            test_date=datetime.now(),
            status=TestStatus.PASS,
            measurements={}
        )

        result.add_measurement('power', 100.0)
        result.add_measurement('voltage', Uncertainty(50.0, 1.0))

        assert result.measurements['power'] == 100.0
        assert isinstance(result.measurements['voltage'], Uncertainty)

    def test_add_criterion(self):
        """Test adding pass/fail criteria"""
        result = ProtocolResult(
            protocol_name="TEST-001",
            test_date=datetime.now(),
            status=TestStatus.PASS,
            measurements={}
        )

        result.add_criterion('test1', True)
        result.add_criterion('test2', False)

        assert result.pass_fail_criteria['test1'] is True
        assert result.pass_fail_criteria['test2'] is False
        assert result.status == TestStatus.FAIL  # Should update to FAIL

    def test_result_to_dict(self):
        """Test result serialization"""
        result = ProtocolResult(
            protocol_name="TEST-001",
            test_date=datetime.now(),
            status=TestStatus.PASS,
            measurements={'power': 100.0}
        )

        data = result.to_dict()

        assert data['protocol_name'] == "TEST-001"
        assert data['status'] == 'PASS'
        assert 'test_date' in data


class TestBaseProtocol:
    """Test BaseProtocol functionality"""

    def test_protocol_initialization(self):
        """Test protocol initialization"""
        protocol = TestProtocolImpl()

        assert protocol.protocol_name == "TEST-001"
        assert protocol.protocol_version == "1.0"

    def test_combine_uncertainties(self):
        """Test uncertainty combination (RSS)"""
        protocol = TestProtocolImpl()

        sources = {
            'source1': 3.0,
            'source2': 4.0
        }

        combined = protocol.combine_uncertainties(sources)
        assert np.isclose(combined, 5.0)  # sqrt(3² + 4²) = 5

    def test_type_a_uncertainty(self):
        """Test Type A uncertainty calculation"""
        protocol = TestProtocolImpl()

        measurements = np.array([100, 102, 98, 101, 99])
        type_a = protocol.calculate_type_a_uncertainty(measurements)

        assert type_a > 0
        assert type_a < 1  # Should be small for this data

    def test_type_b_uncertainty(self):
        """Test Type B uncertainty calculation"""
        protocol = TestProtocolImpl()

        # Normal distribution (k=2)
        type_b = protocol.calculate_type_b_uncertainty(2.0, 'normal')
        assert np.isclose(type_b, 1.0)

        # Uniform distribution
        type_b = protocol.calculate_type_b_uncertainty(1.0, 'uniform')
        assert np.isclose(type_b, 1.0 / np.sqrt(3))

    def test_assess_data_quality(self):
        """Test data quality assessment"""
        protocol = TestProtocolImpl()

        # Excellent quality (< 1%)
        unc1 = Uncertainty(100.0, 0.5)
        assert protocol.assess_data_quality(unc1) == DataQuality.EXCELLENT

        # Good quality (1-2%)
        unc2 = Uncertainty(100.0, 1.5)
        assert protocol.assess_data_quality(unc2) == DataQuality.GOOD

        # Acceptable quality (2-5%)
        unc3 = Uncertainty(100.0, 3.0)
        assert protocol.assess_data_quality(unc3) == DataQuality.ACCEPTABLE

        # Poor quality (> 5%)
        unc4 = Uncertainty(100.0, 6.0)
        assert protocol.assess_data_quality(unc4) == DataQuality.POOR

    def test_temperature_correction(self):
        """Test temperature correction"""
        protocol = TestProtocolImpl()

        # Correct from 50°C to 25°C with -0.4%/°C coefficient
        corrected = protocol.correct_temperature(
            value=100.0,
            measured_temp=50.0,
            reference_temp=25.0,
            temp_coefficient=-0.4
        )

        # Expected: 100 / (1 + (-0.4/100) * 25) = 100 / 0.9 = 111.11
        assert np.isclose(corrected, 111.11, atol=0.01)

    def test_irradiance_correction(self):
        """Test irradiance correction"""
        protocol = TestProtocolImpl()

        # Correct from 800 W/m² to 1000 W/m²
        corrected = protocol.correct_irradiance(
            value=80.0,
            measured_irr=800.0,
            reference_irr=1000.0
        )

        # Expected: 80 * (1000/800) = 100
        assert np.isclose(corrected, 100.0)

    def test_linear_regression(self):
        """Test linear regression"""
        protocol = TestProtocolImpl()

        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])

        result = protocol.calculate_linear_regression(x, y)

        assert np.isclose(result['slope'], 2.0)
        assert np.isclose(result['intercept'], 0.0)
        assert np.isclose(result['r_squared'], 1.0)

    def test_interpolate_value(self):
        """Test value interpolation"""
        protocol = TestProtocolImpl()

        x_data = np.array([0, 10, 20, 30])
        y_data = np.array([0, 100, 200, 300])

        # Linear interpolation
        y_interp = protocol.interpolate_value(x_data, y_data, 15.0, 'linear')
        assert np.isclose(y_interp, 150.0)

    def test_check_data_range(self):
        """Test data range checking"""
        protocol = TestProtocolImpl()

        assert protocol.check_data_range(50, 0, 100, "Test") is True
        assert protocol.check_data_range(150, 0, 100, "Test") is False

    def test_create_result(self):
        """Test result creation"""
        protocol = TestProtocolImpl()

        result = protocol.create_result(
            status=TestStatus.PASS,
            metadata={'test_key': 'test_value'}
        )

        assert result.protocol_name == "TEST-001"
        assert result.status == TestStatus.PASS
        assert result.metadata['test_key'] == 'test_value'
        assert result.metadata['protocol_version'] == "1.0"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
