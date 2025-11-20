"""
Unit tests for V-I Curve Test Block
"""

import pytest
import numpy as np
from datetime import datetime

from ..vi_curve_test import (
    VICurveTest,
    SolarSimulator,
    SourceMeter,
    VICurveParameters
)
from ..base_test_block import TestResult


@pytest.fixture
def solar_simulator():
    """Create a solar simulator instance"""
    config = {'irradiance': 1000, 'spectrum': 'AM1.5G'}
    sim = SolarSimulator('SIM-001', config)
    sim.connect()
    return sim


@pytest.fixture
def source_meter():
    """Create a source meter instance"""
    config = {'compliance_current': 15, 'compliance_voltage': 60}
    meter = SourceMeter('SMU-001', config)
    meter.connect()
    return meter


@pytest.fixture
def vi_curve_test(solar_simulator, source_meter):
    """Create a VI curve test instance"""
    config = {'module_area': 2.0}
    test = VICurveTest(
        test_id='VI-001',
        operator='Test Engineer',
        config=config,
        simulator=solar_simulator,
        source_meter=source_meter
    )
    return test


class TestSolarSimulator:
    """Test solar simulator equipment"""

    def test_connect(self, solar_simulator):
        """Test connection to simulator"""
        assert solar_simulator.connected is True

    def test_initialize(self, solar_simulator):
        """Test simulator initialization"""
        assert solar_simulator.initialize() is True

    def test_measure_irradiance(self, solar_simulator):
        """Test irradiance measurement"""
        measurement = solar_simulator.measure('irradiance')
        assert measurement.value > 0
        assert measurement.unit == 'W/m²'
        assert abs(measurement.value - 1000) < 50  # Within 50 W/m² of target

    def test_set_irradiance(self, solar_simulator):
        """Test setting irradiance level"""
        assert solar_simulator.set_irradiance(800) is True


class TestSourceMeter:
    """Test source meter equipment"""

    def test_connect(self, source_meter):
        """Test connection to source meter"""
        assert source_meter.connected is True

    def test_voltage_sweep(self, source_meter):
        """Test voltage sweep"""
        sweep_data = source_meter.sweep_voltage(0, 50, 100)
        assert len(sweep_data) == 100
        
        voltages, currents = zip(*sweep_data)
        assert min(voltages) >= 0
        assert max(voltages) <= 50
        assert all(c >= 0 for c in currents)  # Current should be non-negative


class TestVICurveTest:
    """Test VI curve test block"""

    def test_initialization(self, vi_curve_test):
        """Test test block initialization"""
        assert vi_curve_test.test_id == 'VI-001'
        assert vi_curve_test.operator == 'Test Engineer'
        assert len(vi_curve_test.parameters) > 0

    def test_parameters(self, vi_curve_test):
        """Test parameter initialization"""
        params = vi_curve_test.parameters
        assert 'irradiance' in params
        assert 'sweep_points' in params
        assert 'min_fill_factor' in params
        assert params['irradiance'].value == 1000

    def test_execute(self, vi_curve_test):
        """Test full test execution"""
        result = vi_curve_test.execute()
        
        assert result is not None
        assert result.test_name == 'VICurveTest'
        assert result.result in [TestResult.PASS, TestResult.CONDITIONAL_PASS, TestResult.FAIL]
        assert len(result.measurements) > 0
        assert result.start_time is not None
        assert result.end_time is not None

    def test_data_collection(self, vi_curve_test):
        """Test data collection"""
        vi_curve_test.start_time = datetime.now()
        measurements = vi_curve_test._collect_data()
        
        assert len(measurements) > 0
        assert len(vi_curve_test.curve_points) > 0

    def test_analysis(self, vi_curve_test):
        """Test data analysis"""
        # First collect data
        vi_curve_test.start_time = datetime.now()
        vi_curve_test._collect_data()
        
        # Then analyze
        analysis = vi_curve_test._analyze_data()
        
        assert 'voc' in analysis
        assert 'isc' in analysis
        assert 'pmax' in analysis
        assert 'fill_factor' in analysis
        assert analysis['pmax'] > 0
        assert 0 < analysis['fill_factor'] < 100

    def test_parameter_extraction(self, vi_curve_test):
        """Test VI curve parameter extraction"""
        vi_curve_test.start_time = datetime.now()
        vi_curve_test._collect_data()
        vi_curve_test._analyze_data()
        
        params = vi_curve_test.extracted_params
        assert params is not None
        assert params.voc > 0
        assert params.isc > 0
        assert params.pmax > 0
        assert params.fill_factor > 0

    def test_pass_fail_determination(self, vi_curve_test):
        """Test pass/fail determination"""
        vi_curve_test.start_time = datetime.now()
        vi_curve_test._collect_data()
        vi_curve_test._analyze_data()
        
        result, criteria = vi_curve_test._determine_pass_fail()
        
        assert result in [TestResult.PASS, TestResult.CONDITIONAL_PASS, TestResult.FAIL]
        assert isinstance(criteria, dict)
        assert 'fill_factor' in criteria
        assert 'power_output' in criteria


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
