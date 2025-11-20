"""
Tests for Equipment Management Models
"""

import unittest
from datetime import date, datetime
from decimal import Decimal

from ..models import (
    Equipment,
    EquipmentStatus,
    EquipmentCategory,
    CalibrationRecord,
    CalibrationStatus,
    SPCDataPoint,
    SPCControlChart,
    UsageLog
)


class TestEquipment(unittest.TestCase):
    """Test Equipment model"""

    def test_equipment_creation(self):
        """Test equipment object creation"""
        equipment = Equipment(
            asset_number="PV-001",
            name="Keysight B2900A",
            manufacturer="Keysight",
            model="B2900A",
            serial_number="MY12345678",
            category=EquipmentCategory.IV_TRACER
        )

        self.assertEqual(equipment.asset_number, "PV-001")
        self.assertEqual(equipment.name, "Keysight B2900A")
        self.assertEqual(equipment.status, EquipmentStatus.ACTIVE)
        self.assertIsNotNone(equipment.equipment_id)

    def test_equipment_to_dict(self):
        """Test equipment serialization to dict"""
        equipment = Equipment(
            asset_number="PV-001",
            name="Test Equipment",
            manufacturer="Test Mfg",
            model="TEST-100",
            serial_number="SN123",
            category=EquipmentCategory.MULTIMETER
        )

        data = equipment.to_dict()

        self.assertEqual(data['asset_number'], "PV-001")
        self.assertEqual(data['name'], "Test Equipment")
        self.assertEqual(data['category'], "multimeter")
        self.assertEqual(data['status'], "active")

    def test_equipment_from_dict(self):
        """Test equipment deserialization from dict"""
        data = {
            'equipment_id': 'test-id-123',
            'asset_number': 'PV-002',
            'name': 'Test Equipment',
            'manufacturer': 'Test Mfg',
            'model': 'TEST-200',
            'serial_number': 'SN456',
            'category': 'pyranometer',
            'status': 'active',
            'location': 'Lab 1',
            'responsible_person': 'John Doe',
            'specifications': {'range': '0-1000 W/m2'},
            'measurement_range': {'min': 0, 'max': 1000},
            'total_usage_hours': '100.5',
            'test_count': 50,
            'created_at': '2024-01-01T12:00:00',
            'updated_at': '2024-01-02T12:00:00',
        }

        equipment = Equipment.from_dict(data)

        self.assertEqual(equipment.equipment_id, 'test-id-123')
        self.assertEqual(equipment.asset_number, 'PV-002')
        self.assertEqual(equipment.category, EquipmentCategory.PYRANOMETER)
        self.assertEqual(equipment.status, EquipmentStatus.ACTIVE)
        self.assertEqual(equipment.total_usage_hours, Decimal('100.5'))


class TestCalibrationRecord(unittest.TestCase):
    """Test CalibrationRecord model"""

    def test_calibration_record_creation(self):
        """Test calibration record creation"""
        record = CalibrationRecord(
            equipment_id="eq-123",
            calibration_date=date(2024, 1, 15),
            due_date=date(2025, 1, 15),
            laboratory_name="NABL Lab",
            certificate_number="CAL-2024-001"
        )

        self.assertEqual(record.equipment_id, "eq-123")
        self.assertEqual(record.calibration_status, CalibrationStatus.CURRENT)
        self.assertIsNotNone(record.calibration_id)

    def test_calibration_record_to_dict(self):
        """Test calibration record serialization"""
        record = CalibrationRecord(
            equipment_id="eq-123",
            calibration_date=date(2024, 1, 15),
            due_date=date(2025, 1, 15),
            laboratory_name="Test Lab",
            certificate_number="CAL-001",
            expanded_uncertainty=Decimal('0.5'),
            coverage_factor=Decimal('2.0')
        )

        data = record.to_dict()

        self.assertEqual(data['equipment_id'], "eq-123")
        self.assertEqual(data['calibration_date'], "2024-01-15")
        self.assertEqual(data['expanded_uncertainty'], "0.5")
        self.assertEqual(data['coverage_factor'], "2.0")

    def test_calibration_record_from_dict(self):
        """Test calibration record deserialization"""
        data = {
            'calibration_id': 'cal-456',
            'equipment_id': 'eq-789',
            'calibration_date': '2024-02-01',
            'due_date': '2025-02-01',
            'calibration_interval_days': 365,
            'laboratory_name': 'NABL Lab',
            'certificate_number': 'CAL-002',
            'calibration_status': 'current',
            'expanded_uncertainty': '0.3',
            'coverage_factor': '2.0',
            'passed': True,
            'created_at': '2024-02-01T10:00:00',
            'updated_at': '2024-02-01T10:00:00',
        }

        record = CalibrationRecord.from_dict(data)

        self.assertEqual(record.calibration_id, 'cal-456')
        self.assertEqual(record.equipment_id, 'eq-789')
        self.assertEqual(record.calibration_status, CalibrationStatus.CURRENT)
        self.assertEqual(record.expanded_uncertainty, Decimal('0.3'))


class TestSPCDataPoint(unittest.TestCase):
    """Test SPCDataPoint model"""

    def test_spc_data_point_creation(self):
        """Test SPC data point creation"""
        point = SPCDataPoint(
            equipment_id="eq-123",
            measurement_type="voltage_accuracy",
            measured_value=Decimal('10.05'),
            reference_value=Decimal('10.00'),
            error=Decimal('0.05')
        )

        self.assertEqual(point.equipment_id, "eq-123")
        self.assertEqual(point.error, Decimal('0.05'))
        self.assertIsNotNone(point.data_point_id)

    def test_spc_data_point_to_dict(self):
        """Test SPC data point serialization"""
        point = SPCDataPoint(
            equipment_id="eq-123",
            measurement_type="current_accuracy",
            measured_value=Decimal('5.02'),
            reference_value=Decimal('5.00'),
            error=Decimal('0.02')
        )

        data = point.to_dict()

        self.assertEqual(data['equipment_id'], "eq-123")
        self.assertEqual(data['measurement_type'], "current_accuracy")
        self.assertEqual(data['error'], "0.02")


class TestSPCControlChart(unittest.TestCase):
    """Test SPCControlChart model"""

    def test_control_chart_creation(self):
        """Test control chart creation"""
        chart = SPCControlChart(
            equipment_id="eq-123",
            measurement_type="voltage_accuracy",
            chart_type="xbar_r"
        )

        self.assertEqual(chart.equipment_id, "eq-123")
        self.assertEqual(chart.chart_type, "xbar_r")
        self.assertTrue(chart.is_active)
        self.assertIsNotNone(chart.chart_id)

    def test_control_chart_with_limits(self):
        """Test control chart with limits"""
        chart = SPCControlChart(
            equipment_id="eq-123",
            measurement_type="current_accuracy",
            center_line=Decimal('0.0'),
            upper_control_limit=Decimal('0.15'),
            lower_control_limit=Decimal('-0.15'),
            upper_spec_limit=Decimal('0.2'),
            lower_spec_limit=Decimal('-0.2')
        )

        self.assertEqual(chart.center_line, Decimal('0.0'))
        self.assertEqual(chart.upper_control_limit, Decimal('0.15'))


class TestUsageLog(unittest.TestCase):
    """Test UsageLog model"""

    def test_usage_log_creation(self):
        """Test usage log creation"""
        log = UsageLog(
            equipment_id="eq-123",
            operator="John Doe",
            test_id="test-456",
            test_type="IV curve"
        )

        self.assertEqual(log.equipment_id, "eq-123")
        self.assertEqual(log.operator, "John Doe")
        self.assertIsNotNone(log.log_id)
        self.assertIsNotNone(log.start_time)


if __name__ == '__main__':
    unittest.main()
