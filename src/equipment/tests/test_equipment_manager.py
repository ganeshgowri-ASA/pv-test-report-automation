"""
Tests for Equipment Manager
"""

import unittest
import tempfile
import shutil
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from ..equipment_manager import EquipmentManager
from ..models import (
    Equipment,
    EquipmentStatus,
    EquipmentCategory
)


class TestEquipmentManager(unittest.TestCase):
    """Test EquipmentManager functionality"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.manager = EquipmentManager(storage_path=self.test_dir)

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_register_equipment(self):
        """Test equipment registration"""
        equipment = Equipment(
            asset_number="PV-001",
            name="Test IV Tracer",
            manufacturer="Keysight",
            model="B2900A",
            serial_number="SN12345",
            category=EquipmentCategory.IV_TRACER
        )

        equipment_id = self.manager.register_equipment(equipment)

        self.assertIsNotNone(equipment_id)
        self.assertEqual(len(self.manager._equipment_registry), 1)

        # Verify retrieval
        retrieved = self.manager.get_equipment(equipment_id)
        self.assertEqual(retrieved.asset_number, "PV-001")

    def test_update_equipment(self):
        """Test equipment update"""
        equipment = Equipment(
            asset_number="PV-002",
            name="Test Equipment",
            location="Lab 1"
        )

        equipment_id = self.manager.register_equipment(equipment)

        # Update location
        updated = self.manager.update_equipment(equipment_id, {
            'location': 'Lab 2',
            'responsible_person': 'Jane Doe'
        })

        self.assertEqual(updated.location, 'Lab 2')
        self.assertEqual(updated.responsible_person, 'Jane Doe')

    def test_get_equipment_by_asset_number(self):
        """Test retrieving equipment by asset number"""
        equipment = Equipment(
            asset_number="PV-003",
            name="Pyranometer",
            category=EquipmentCategory.PYRANOMETER
        )

        self.manager.register_equipment(equipment)

        retrieved = self.manager.get_equipment_by_asset_number("PV-003")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Pyranometer")

    def test_get_equipment_by_serial(self):
        """Test retrieving equipment by serial number"""
        equipment = Equipment(
            asset_number="PV-004",
            serial_number="ABC123",
            name="Temperature Sensor"
        )

        self.manager.register_equipment(equipment)

        retrieved = self.manager.get_equipment_by_serial("ABC123")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.asset_number, "PV-004")

    def test_list_equipment_with_filters(self):
        """Test listing equipment with filters"""
        # Create multiple equipment items
        eq1 = Equipment(
            asset_number="PV-005",
            category=EquipmentCategory.IV_TRACER,
            status=EquipmentStatus.ACTIVE,
            location="Lab 1"
        )
        eq2 = Equipment(
            asset_number="PV-006",
            category=EquipmentCategory.PYRANOMETER,
            status=EquipmentStatus.ACTIVE,
            location="Lab 1"
        )
        eq3 = Equipment(
            asset_number="PV-007",
            category=EquipmentCategory.IV_TRACER,
            status=EquipmentStatus.MAINTENANCE,
            location="Lab 2"
        )

        self.manager.register_equipment(eq1)
        self.manager.register_equipment(eq2)
        self.manager.register_equipment(eq3)

        # Filter by category
        iv_tracers = self.manager.list_equipment(category=EquipmentCategory.IV_TRACER)
        self.assertEqual(len(iv_tracers), 2)

        # Filter by status
        active = self.manager.list_equipment(status=EquipmentStatus.ACTIVE)
        self.assertEqual(len(active), 2)

        # Filter by location
        lab1 = self.manager.list_equipment(location="Lab 1")
        self.assertEqual(len(lab1), 2)

        # Multiple filters
        active_iv = self.manager.list_equipment(
            category=EquipmentCategory.IV_TRACER,
            status=EquipmentStatus.ACTIVE
        )
        self.assertEqual(len(active_iv), 1)

    def test_retire_equipment(self):
        """Test equipment retirement"""
        equipment = Equipment(asset_number="PV-008", name="Old Equipment")
        equipment_id = self.manager.register_equipment(equipment)

        retired = self.manager.retire_equipment(equipment_id, "End of life")

        self.assertEqual(retired.status, EquipmentStatus.RETIRED)
        self.assertIn("End of life", retired.notes)

    def test_reserve_and_release_equipment(self):
        """Test equipment reservation and release"""
        equipment = Equipment(asset_number="PV-009", name="Shared Equipment")
        equipment_id = self.manager.register_equipment(equipment)

        # Reserve equipment
        reserved = self.manager.reserve_equipment(
            equipment_id,
            reserved_by="John Doe",
            notes="For experiment X"
        )

        self.assertEqual(reserved.status, EquipmentStatus.RESERVED)
        self.assertEqual(reserved.responsible_person, "John Doe")

        # Release equipment
        released = self.manager.release_equipment(equipment_id)
        self.assertEqual(released.status, EquipmentStatus.ACTIVE)

    def test_usage_logging(self):
        """Test equipment usage logging"""
        equipment = Equipment(asset_number="PV-010", name="Test Equipment")
        equipment_id = self.manager.register_equipment(equipment)

        # Start usage
        log_id = self.manager.start_usage(
            equipment_id=equipment_id,
            operator="Jane Doe",
            test_id="test-123",
            test_type="IV curve"
        )

        self.assertIsNotNone(log_id)
        self.assertEqual(len(self.manager._usage_logs), 1)

        # End usage
        ended_log = self.manager.end_usage(log_id, notes="Test completed")

        self.assertIsNotNone(ended_log.end_time)
        self.assertGreater(ended_log.duration_hours, Decimal('0'))

        # Check equipment usage updated
        updated_eq = self.manager.get_equipment(equipment_id)
        self.assertGreater(updated_eq.total_usage_hours, Decimal('0'))
        self.assertEqual(updated_eq.test_count, 1)

    def test_get_usage_logs_with_filters(self):
        """Test retrieving usage logs with filters"""
        eq1_id = self.manager.register_equipment(Equipment(asset_number="PV-011"))
        eq2_id = self.manager.register_equipment(Equipment(asset_number="PV-012"))

        # Create multiple logs
        log1_id = self.manager.start_usage(eq1_id, "Alice", test_type="IV")
        log2_id = self.manager.start_usage(eq2_id, "Bob", test_type="Performance")
        log3_id = self.manager.start_usage(eq1_id, "Alice", test_type="IV")

        self.manager.end_usage(log1_id)
        self.manager.end_usage(log2_id)
        self.manager.end_usage(log3_id)

        # Filter by equipment
        eq1_logs = self.manager.get_usage_logs(equipment_id=eq1_id)
        self.assertEqual(len(eq1_logs), 2)

        # Filter by operator
        alice_logs = self.manager.get_usage_logs(operator="Alice")
        self.assertEqual(len(alice_logs), 2)

    def test_maintenance_scheduling(self):
        """Test maintenance scheduling"""
        equipment = Equipment(asset_number="PV-013", name="Test Equipment")
        equipment_id = self.manager.register_equipment(equipment)

        # Schedule maintenance
        next_month = date.today() + timedelta(days=30)
        scheduled = self.manager.schedule_maintenance(
            equipment_id,
            maintenance_date=next_month,
            notes="Annual maintenance"
        )

        self.assertEqual(scheduled.next_maintenance, next_month)

        # Complete maintenance
        completed = self.manager.complete_maintenance(
            equipment_id,
            next_maintenance=date.today() + timedelta(days=365)
        )

        self.assertEqual(completed.last_maintenance, date.today())
        self.assertEqual(completed.status, EquipmentStatus.ACTIVE)

    def test_get_maintenance_due(self):
        """Test getting equipment with maintenance due"""
        # Create equipment with various maintenance dates
        eq1 = Equipment(asset_number="PV-014", next_maintenance=date.today() + timedelta(days=5))
        eq2 = Equipment(asset_number="PV-015", next_maintenance=date.today() + timedelta(days=20))
        eq3 = Equipment(asset_number="PV-016", next_maintenance=date.today() + timedelta(days=60))

        self.manager.register_equipment(eq1)
        self.manager.register_equipment(eq2)
        self.manager.register_equipment(eq3)

        # Get maintenance due in 30 days
        due_soon = self.manager.get_maintenance_due(days_ahead=30)
        self.assertEqual(len(due_soon), 2)

    def test_get_overdue_maintenance(self):
        """Test getting overdue maintenance"""
        # Create equipment with overdue maintenance
        eq1 = Equipment(
            asset_number="PV-017",
            next_maintenance=date.today() - timedelta(days=10)
        )
        eq2 = Equipment(
            asset_number="PV-018",
            next_maintenance=date.today() + timedelta(days=10)
        )

        self.manager.register_equipment(eq1)
        self.manager.register_equipment(eq2)

        overdue = self.manager.get_overdue_maintenance()
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].asset_number, "PV-017")

    def test_equipment_allocation(self):
        """Test equipment allocation"""
        # Create available equipment
        eq1 = Equipment(
            asset_number="PV-019",
            category=EquipmentCategory.IV_TRACER,
            status=EquipmentStatus.ACTIVE,
            test_count=10
        )
        eq2 = Equipment(
            asset_number="PV-020",
            category=EquipmentCategory.IV_TRACER,
            status=EquipmentStatus.ACTIVE,
            test_count=5
        )
        eq3 = Equipment(
            asset_number="PV-021",
            category=EquipmentCategory.IV_TRACER,
            status=EquipmentStatus.RESERVED
        )

        self.manager.register_equipment(eq1)
        self.manager.register_equipment(eq2)
        self.manager.register_equipment(eq3)

        # Allocate equipment (should get least used)
        allocated = self.manager.allocate_equipment(
            category=EquipmentCategory.IV_TRACER,
            operator="Test User",
            test_type="IV curve"
        )

        self.assertIsNotNone(allocated)
        self.assertEqual(allocated.asset_number, "PV-020")  # Least used

    def test_equipment_utilization(self):
        """Test equipment utilization statistics"""
        equipment = Equipment(asset_number="PV-022", name="Test Equipment")
        equipment_id = self.manager.register_equipment(equipment)

        # Create some usage logs
        log1_id = self.manager.start_usage(equipment_id, "User1")
        self.manager.end_usage(log1_id)

        log2_id = self.manager.start_usage(equipment_id, "User2")
        self.manager.end_usage(log2_id)

        # Get utilization
        stats = self.manager.get_equipment_utilization(equipment_id)

        self.assertEqual(stats['equipment_id'], equipment_id)
        self.assertGreater(stats['total_usage_hours'], 0)
        self.assertEqual(stats['test_count'], 2)

    def test_fleet_summary(self):
        """Test fleet summary statistics"""
        # Create various equipment
        self.manager.register_equipment(Equipment(
            asset_number="PV-023",
            category=EquipmentCategory.IV_TRACER,
            status=EquipmentStatus.ACTIVE
        ))
        self.manager.register_equipment(Equipment(
            asset_number="PV-024",
            category=EquipmentCategory.PYRANOMETER,
            status=EquipmentStatus.ACTIVE
        ))
        self.manager.register_equipment(Equipment(
            asset_number="PV-025",
            category=EquipmentCategory.IV_TRACER,
            status=EquipmentStatus.MAINTENANCE
        ))

        summary = self.manager.get_fleet_summary()

        self.assertEqual(summary['total_equipment'], 3)
        self.assertEqual(summary['status_counts']['active'], 2)
        self.assertEqual(summary['category_counts']['iv_tracer'], 2)

    def test_persistence(self):
        """Test data persistence across manager instances"""
        # Create equipment
        equipment = Equipment(
            asset_number="PV-026",
            name="Persistent Equipment"
        )
        equipment_id = self.manager.register_equipment(equipment)

        # Create new manager instance with same storage
        manager2 = EquipmentManager(storage_path=self.test_dir)

        # Verify data was loaded
        retrieved = manager2.get_equipment(equipment_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.asset_number, "PV-026")


if __name__ == '__main__':
    unittest.main()
