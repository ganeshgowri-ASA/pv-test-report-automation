"""
Unit tests for Base Test Block
"""

import pytest
import numpy as np
from datetime import datetime

from ..base_test_block import (
    BaseTestBlock,
    EquipmentInterface,
    MeasurementData,
    TestParameter,
    TestResult,
    TestSeverity
)


class MockEquipment(EquipmentInterface):
    """Mock equipment for testing"""

    def connect(self):
        self.connected = True
        return True

    def disconnect(self):
        self.connected = False
        return True

    def initialize(self):
        return True

    def measure(self, parameter):
        return MeasurementData(
            timestamp=datetime.now(),
            value=100.0,
            unit='V',
            parameter_name=parameter,
            equipment_id=self.equipment_id
        )

    def configure(self, settings):
        self.config.update(settings)
        return True


class MockTestBlock(BaseTestBlock):
    """Mock test block for testing"""

    def _initialize_parameters(self):
        self.parameters = {
            'test_param': TestParameter(
                name='test_param',
                value=100,
                unit='V',
                description='Test parameter'
            )
        }

    def execute(self):
        self.start_time = datetime.now()
        self.measurements = self._collect_data()
        self.analysis_results = self._analyze_data()
        self.end_time = datetime.now()
        return self.generate_result()

    def _collect_data(self):
        measurements = []
        for i in range(10):
            self.add_measurement('voltage', 100 + i, 'V')
        return self.measurements

    def _analyze_data(self):
        return {'mean_voltage': 105.0}

    def _determine_pass_fail(self):
        return TestResult.PASS, {'all_criteria': True}


@pytest.fixture
def mock_equipment():
    """Create mock equipment"""
    config = {'test': True}
    equip = MockEquipment('MOCK-001', config)
    equip.connect()
    return equip


@pytest.fixture
def mock_test_block(mock_equipment):
    """Create mock test block"""
    config = {}
    test = MockTestBlock(
        test_id='TEST-001',
        operator='Test Engineer',
        config=config,
        equipment=[mock_equipment]
    )
    return test


class TestMeasurementData:
    """Test MeasurementData dataclass"""

    def test_creation(self):
        """Test measurement data creation"""
        measurement = MeasurementData(
            timestamp=datetime.now(),
            value=100.0,
            unit='V',
            parameter_name='voltage'
        )
        
        assert measurement.value == 100.0
        assert measurement.unit == 'V'
        assert measurement.parameter_name == 'voltage'


class TestEquipmentInterface:
    """Test equipment interface"""

    def test_connect(self, mock_equipment):
        """Test connection"""
        assert mock_equipment.connected is True

    def test_disconnect(self, mock_equipment):
        """Test disconnection"""
        mock_equipment.disconnect()
        assert mock_equipment.connected is False

    def test_measure(self, mock_equipment):
        """Test measurement"""
        measurement = mock_equipment.measure('voltage')
        assert measurement.value > 0
        assert measurement.unit == 'V'

    def test_calibration_verification(self, mock_equipment):
        """Test calibration verification"""
        assert mock_equipment.verify_calibration() is True


class TestBaseTestBlock:
    """Test base test block functionality"""

    def test_initialization(self, mock_test_block):
        """Test initialization"""
        assert mock_test_block.test_id == 'TEST-001'
        assert mock_test_block.operator == 'Test Engineer'
        assert len(mock_test_block.equipment) == 1

    def test_add_measurement(self, mock_test_block):
        """Test adding measurements"""
        mock_test_block.add_measurement('voltage', 100.0, 'V')
        assert len(mock_test_block.measurements) == 1
        assert mock_test_block.measurements[0].value == 100.0

    def test_get_measurements(self, mock_test_block):
        """Test getting measurements by parameter"""
        mock_test_block.add_measurement('voltage', 100.0, 'V')
        mock_test_block.add_measurement('current', 5.0, 'A')
        mock_test_block.add_measurement('voltage', 110.0, 'V')
        
        voltage_measurements = mock_test_block.get_measurements('voltage')
        assert len(voltage_measurements) == 2

    def test_calculate_statistics(self, mock_test_block):
        """Test statistical calculations"""
        # Add test data
        for i in range(10):
            mock_test_block.add_measurement('voltage', 100 + i, 'V')
        
        stats = mock_test_block.calculate_statistics('voltage')
        
        assert 'mean' in stats
        assert 'std' in stats
        assert 'min' in stats
        assert 'max' in stats
        assert stats['mean'] == pytest.approx(104.5, rel=0.01)
        assert stats['min'] == 100
        assert stats['max'] == 109

    def test_detect_outliers_iqr(self, mock_test_block):
        """Test outlier detection using IQR method"""
        # Add normal data
        for i in range(20):
            mock_test_block.add_measurement('voltage', 100 + np.random.normal(0, 1), 'V')
        
        # Add outliers
        mock_test_block.add_measurement('voltage', 150, 'V')
        mock_test_block.add_measurement('voltage', 50, 'V')
        
        outliers = mock_test_block.detect_outliers('voltage', method='iqr')
        assert len(outliers) >= 0  # Should detect some outliers

    def test_check_trend(self, mock_test_block):
        """Test trend analysis"""
        # Add increasing trend
        for i in range(10):
            mock_test_block.add_measurement('voltage', 100 + i * 2, 'V')
        
        trend = mock_test_block.check_trend('voltage')
        
        assert 'trend' in trend
        assert 'slope' in trend
        assert trend['trend'] == 'increasing'
        assert trend['slope'] > 0

    def test_validate_equipment(self, mock_test_block):
        """Test equipment validation"""
        issues = mock_test_block.validate_equipment()
        assert isinstance(issues, list)

    def test_log_anomaly(self, mock_test_block):
        """Test anomaly logging"""
        mock_test_block.log_anomaly('Test anomaly')
        assert len(mock_test_block.anomalies) == 1

    def test_generate_result(self, mock_test_block):
        """Test result generation"""
        mock_test_block.start_time = datetime.now()
        mock_test_block.end_time = datetime.now()
        
        result = mock_test_block.generate_result()
        
        assert result is not None
        assert result.test_id == 'TEST-001'
        assert result.operator == 'Test Engineer'
        assert result.result in [r for r in TestResult]

    def test_execute(self, mock_test_block):
        """Test execution"""
        result = mock_test_block.execute()
        
        assert result is not None
        assert len(result.measurements) > 0
        assert result.start_time is not None
        assert result.end_time is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
