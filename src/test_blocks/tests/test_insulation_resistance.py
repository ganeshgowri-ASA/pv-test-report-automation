"""
Unit tests for Insulation Resistance Test Block
"""

import pytest
from datetime import datetime

from ..insulation_resistance import (
    InsulationResistanceTest,
    Megohmmeter,
    EnvironmentMonitor
)
from ..base_test_block import TestResult


@pytest.fixture
def megohmmeter():
    """Create a megohmmeter instance"""
    config = {'test_voltage': 1000}
    meter = Megohmmeter('MEGA-001', config)
    meter.connect()
    return meter


@pytest.fixture
def env_monitor():
    """Create an environment monitor instance"""
    config = {'sampling_rate': 60}
    monitor = EnvironmentMonitor('ENV-001', config)
    monitor.connect()
    return monitor


@pytest.fixture
def ir_test(megohmmeter, env_monitor):
    """Create an IR test instance"""
    config = {}
    test = InsulationResistanceTest(
        test_id='IR-001',
        operator='Test Engineer',
        config=config,
        megohmmeter=megohmmeter,
        env_monitor=env_monitor
    )
    return test


class TestMegohmmeter:
    """Test megohmmeter equipment"""

    def test_connect(self, megohmmeter):
        """Test connection"""
        assert megohmmeter.connected is True

    def test_measure_resistance(self, megohmmeter):
        """Test resistance measurement"""
        resistance, leakage = megohmmeter.measure_resistance(1000, 60)
        assert resistance > 0
        assert resistance > 1e6  # Should be at least 1 MOhm
        assert leakage >= 0


class TestInsulationResistanceTest:
    """Test IR test block"""

    def test_initialization(self, ir_test):
        """Test initialization"""
        assert ir_test.test_id == 'IR-001'
        assert len(ir_test.parameters) > 0

    def test_execute(self, ir_test):
        """Test execution"""
        result = ir_test.execute()
        
        assert result is not None
        assert result.result in [TestResult.PASS, TestResult.CONDITIONAL_PASS, TestResult.FAIL]
        assert len(result.measurements) > 0

    def test_analysis(self, ir_test):
        """Test analysis"""
        ir_test.start_time = datetime.now()
        ir_test._collect_data()
        analysis = ir_test._analyze_data()
        
        assert 'min_resistance' in analysis
        assert 'resistance_stats' in analysis
        assert analysis['min_resistance'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
