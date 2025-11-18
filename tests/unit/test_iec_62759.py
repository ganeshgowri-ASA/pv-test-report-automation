"""
Unit tests for IEC 62759 Transportation Testing
"""

import pytest
from datetime import datetime

from src.protocols.iec.iec_62759 import IEC62759Controller
from src.utils.constants import PassFailStatus, TestStatus
from src.equipment.solar_simulator import SolarSimulator, FlashTestResult
from src.equipment.load_frame import LoadFrame
from src.equipment.thermal_chamber import ThermalChamber


class TestIEC62759Controller:
    """Test IEC 62759 Controller functionality"""

    def test_controller_initialization(self):
        """Test controller can be initialized"""
        controller = IEC62759Controller(module_id="TEST-001")

        assert controller.module_id == "TEST-001"
        assert controller.protocol_name == "IEC 62759"
        assert controller.protocol_version == "1.0:2015"

    def test_equipment_connection(self):
        """Test equipment connection"""
        controller = IEC62759Controller(module_id="TEST-001")
        success = controller.connect_equipment()

        assert success is True

    def test_initial_flash_test(self):
        """Test initial flash test execution"""
        controller = IEC62759Controller(module_id="TEST-001")
        controller.connect_equipment()

        result = controller.step1_initial_flash_test()

        assert isinstance(result, FlashTestResult)
        assert result.pmax > 0
        assert result.voc > 0
        assert result.isc > 0
        assert controller.initial_flash is not None

    def test_edge_loading(self):
        """Test edge loading execution"""
        controller = IEC62759Controller(module_id="TEST-001")
        controller.connect_equipment()

        result = controller.step2_edge_loading()

        assert result.load_pa == 600
        assert result.duration_hours == 1.0
        assert result.breakage_detected is False

    def test_dynamic_loading(self):
        """Test dynamic mechanical loading"""
        controller = IEC62759Controller(module_id="TEST-001")
        controller.connect_equipment()

        results = controller.step3_dynamic_mechanical_loading()

        assert 'front' in results
        assert 'rear' in results
        assert results['front'].cycles == 1000
        assert results['rear'].cycles == 1000

    def test_thermal_cycling(self):
        """Test thermal cycling"""
        controller = IEC62759Controller(module_id="TEST-001")
        controller.connect_equipment()

        result = controller.step4_thermal_cycling()

        assert result.cycles_completed == 50
        assert result.actual_low_temp == -40
        assert result.actual_high_temp == 85

    def test_power_degradation_calculation(self):
        """Test power degradation calculation"""
        controller = IEC62759Controller(module_id="TEST-001")
        controller.connect_equipment()

        # Set test data
        controller.initial_flash = FlashTestResult(
            pmax=300.0,
            voc=45.0,
            isc=9.0,
            vmp=37.5,
            imp=8.0,
            fill_factor=0.74
        )

        controller.final_flash = FlashTestResult(
            pmax=290.0,
            voc=44.8,
            isc=8.95,
            vmp=37.2,
            imp=7.8,
            fill_factor=0.72
        )

        controller.calculate_power_degradation()

        degradation_pct = controller.degradation_pct
        assert degradation_pct is not None
        assert degradation_pct > 0
        assert degradation_pct < 5.0  # Should pass

    def test_pass_fail_determination(self):
        """Test pass/fail determination"""
        controller = IEC62759Controller(module_id="TEST-001")
        controller.connect_equipment()

        # Set all tests to pass
        controller.result.test_data['edge_load_pass'] = True
        controller.result.test_data['dynamic_load_pass'] = True
        controller.result.test_data['thermal_pass'] = True
        controller.result.test_data['degradation_pass'] = True
        controller.result.test_data['visual_pass'] = True

        result = controller.calculate_pass_fail()

        assert result == PassFailStatus.PASS

    def test_pass_fail_with_failure(self):
        """Test pass/fail with one failing test"""
        controller = IEC62759Controller(module_id="TEST-001")
        controller.connect_equipment()

        # Set one test to fail
        controller.result.test_data['edge_load_pass'] = True
        controller.result.test_data['dynamic_load_pass'] = False  # FAIL
        controller.result.test_data['thermal_pass'] = True
        controller.result.test_data['degradation_pass'] = True
        controller.result.test_data['visual_pass'] = True

        result = controller.calculate_pass_fail()

        assert result == PassFailStatus.FAIL

    def test_report_generation(self):
        """Test report generation"""
        controller = IEC62759Controller(module_id="TEST-001")
        controller.connect_equipment()
        controller.step1_initial_flash_test()

        report = controller.generate_report()

        assert 'test_info' in report
        assert 'initial_measurements' in report
        assert 'iso_17025_compliance' in report
        assert report['test_info']['module_id'] == "TEST-001"


class TestEquipment:
    """Test equipment interfaces"""

    def test_solar_simulator(self):
        """Test solar simulator"""
        sim = SolarSimulator()
        sim.connect()

        assert sim.get_status() == "ready"

        result = sim.measure_iv_curve("TEST-001")
        assert result.pmax > 0

    def test_load_frame(self):
        """Test load frame"""
        load = LoadFrame()
        load.connect()

        assert load.get_status() == "ready"

        result = load.apply_static_edge_load(600, 1.0)
        assert result.load_pa == 600

    def test_thermal_chamber(self):
        """Test thermal chamber"""
        chamber = ThermalChamber()
        chamber.connect()

        assert chamber.get_status() == "idle"

        result = chamber.run_iec62759_thermal_cycling(cycles=50)
        assert result.cycles_completed == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
