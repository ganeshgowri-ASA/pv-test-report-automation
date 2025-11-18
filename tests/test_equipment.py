"""
Comprehensive tests for Equipment Management System
"""
import pytest
import tempfile
import os
from datetime import date, datetime, timedelta

from equipment import (
    Equipment,
    EquipmentStatus,
    EquipmentCategory,
    UsageLog,
    MaintenanceLog,
    MaintenanceType,
    CalibrationRecord,
    EquipmentReservation,
    EquipmentDB
)


@pytest.fixture
def db():
    """Create temporary database for testing"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    database = EquipmentDB(db_path=path)
    yield database

    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def sample_equipment():
    """Create sample equipment for testing"""
    return Equipment(
        name="IV Tracer Pro 3000",
        manufacturer="PV Test Systems",
        model="IVT-3000",
        serial_number="IVT3000-2024-001",
        category=EquipmentCategory.IV_TRACER,
        location="Lab A - Bench 1",
        status=EquipmentStatus.AVAILABLE,
        calibration_due_date=date.today() + timedelta(days=180),
        calibration_interval_days=365,
        last_calibration_date=date.today() - timedelta(days=185),
        calibration_certificate_number="CAL-2024-001",
        specifications={
            "voltage_range": "0-1500V",
            "current_range": "0-20A",
            "accuracy": "±0.5%"
        },
        accuracy="±0.5%",
        measurement_range="0-1500V, 0-20A",
        purchase_date=date(2024, 1, 15),
        purchase_cost=25000.00,
        responsible_person="John Smith",
        asset_tag="AST-001"
    )


class TestEquipmentCRUD:
    """Test equipment CRUD operations"""

    def test_add_equipment(self, db, sample_equipment):
        """Test adding equipment to database"""
        equipment_id = db.add_equipment(sample_equipment)
        assert equipment_id > 0

        # Verify retrieval
        retrieved = db.get_equipment(equipment_id)
        assert retrieved is not None
        assert retrieved.name == sample_equipment.name
        assert retrieved.serial_number == sample_equipment.serial_number
        assert retrieved.category == EquipmentCategory.IV_TRACER

    def test_update_equipment(self, db, sample_equipment):
        """Test updating equipment"""
        equipment_id = db.add_equipment(sample_equipment)

        # Update location
        success = db.update_equipment(equipment_id, location="Lab B - Bench 2")
        assert success

        retrieved = db.get_equipment(equipment_id)
        assert retrieved.location == "Lab B - Bench 2"

    def test_delete_equipment(self, db, sample_equipment):
        """Test deleting (retiring) equipment"""
        equipment_id = db.add_equipment(sample_equipment)

        success = db.delete_equipment(equipment_id)
        assert success

        retrieved = db.get_equipment(equipment_id)
        assert retrieved.status == EquipmentStatus.RETIRED

    def test_list_equipment(self, db, sample_equipment):
        """Test listing equipment with filters"""
        # Add multiple equipment
        equipment_id1 = db.add_equipment(sample_equipment)

        sample_equipment.serial_number = "IVT3000-2024-002"
        sample_equipment.category = EquipmentCategory.CLIMATE_CHAMBER
        equipment_id2 = db.add_equipment(sample_equipment)

        # List all
        all_equipment = db.list_equipment()
        assert len(all_equipment) == 2

        # Filter by category
        iv_tracers = db.list_equipment(category=EquipmentCategory.IV_TRACER)
        assert len(iv_tracers) == 1

        chambers = db.list_equipment(category=EquipmentCategory.CLIMATE_CHAMBER)
        assert len(chambers) == 1

    def test_get_available(self, db, sample_equipment):
        """Test getting available equipment"""
        equipment_id1 = db.add_equipment(sample_equipment)

        sample_equipment.serial_number = "IVT3000-2024-002"
        sample_equipment.status = EquipmentStatus.IN_USE
        equipment_id2 = db.add_equipment(sample_equipment)

        available = db.get_available()
        assert len(available) == 1
        assert available[0].equipment_id == equipment_id1

        # Test category filter
        available_iv = db.get_available(category=EquipmentCategory.IV_TRACER)
        assert len(available_iv) == 1


class TestUsageTracking:
    """Test usage tracking functionality"""

    def test_checkout_checkin(self, db, sample_equipment):
        """Test basic checkout/checkin flow"""
        equipment_id = db.add_equipment(sample_equipment)

        # Checkout
        log_id = db.checkout(
            equipment_id=equipment_id,
            user_name="Jane Doe",
            test_id=123,
            purpose="PV module testing"
        )
        assert log_id > 0

        # Verify equipment status changed
        equipment = db.get_equipment(equipment_id)
        assert equipment.status == EquipmentStatus.IN_USE

        # Checkin
        success = db.checkin(equipment_id, condition="good")
        assert success

        # Verify equipment status changed back
        equipment = db.get_equipment(equipment_id)
        assert equipment.status == EquipmentStatus.AVAILABLE

    def test_checkout_unavailable_equipment(self, db, sample_equipment):
        """Test checkout fails for unavailable equipment"""
        sample_equipment.status = EquipmentStatus.MAINTENANCE
        equipment_id = db.add_equipment(sample_equipment)

        with pytest.raises(ValueError, match="not available"):
            db.checkout(equipment_id, user_name="Jane Doe")

    def test_checkout_calibration_overdue(self, db, sample_equipment):
        """Test checkout fails for equipment with overdue calibration"""
        sample_equipment.calibration_due_date = date.today() - timedelta(days=1)
        equipment_id = db.add_equipment(sample_equipment)

        with pytest.raises(ValueError, match="calibration is overdue"):
            db.checkout(equipment_id, user_name="Jane Doe")

    def test_checkin_with_issues(self, db, sample_equipment):
        """Test checkin with reported issues"""
        equipment_id = db.add_equipment(sample_equipment)

        db.checkout(equipment_id, user_name="Jane Doe")
        db.checkin(
            equipment_id,
            condition="damaged",
            issues_reported="Display screen cracked"
        )

        # Equipment should be marked for maintenance
        equipment = db.get_equipment(equipment_id)
        assert equipment.status == EquipmentStatus.MAINTENANCE

    def test_usage_history(self, db, sample_equipment):
        """Test usage history retrieval"""
        equipment_id = db.add_equipment(sample_equipment)

        # Multiple checkout/checkin cycles
        for i in range(3):
            db.checkout(equipment_id, user_name=f"User {i}")
            db.checkin(equipment_id)

        history = db.get_usage_history(equipment_id=equipment_id)
        assert len(history) == 3

        # Test date filtering
        today = date.today()
        history_today = db.get_usage_history(
            equipment_id=equipment_id,
            start_date=today,
            end_date=today
        )
        assert len(history_today) == 3


class TestCalibrationManagement:
    """Test calibration management"""

    def test_add_calibration_record(self, db, sample_equipment):
        """Test adding calibration record"""
        equipment_id = db.add_equipment(sample_equipment)

        record = CalibrationRecord(
            equipment_id=equipment_id,
            calibration_date=date.today(),
            next_calibration_due=date.today() + timedelta(days=365),
            calibration_lab="NIST Traceable Lab",
            lab_accreditation="ISO/IEC 17025:2017",
            certificate_number="CAL-2024-NEW-001",
            traceability="NIST",
            calibration_results={
                "voltage_accuracy": "±0.48%",
                "current_accuracy": "±0.49%"
            },
            pass_fail=True,
            temperature=23.5,
            humidity=45.0,
            performed_by="Calibration Technician"
        )

        record_id = db.add_calibration_record(record)
        assert record_id > 0

        # Verify equipment calibration info was updated
        equipment = db.get_equipment(equipment_id)
        assert equipment.last_calibration_date == date.today()
        assert equipment.calibration_certificate_number == "CAL-2024-NEW-001"

    def test_calibration_history(self, db, sample_equipment):
        """Test calibration history retrieval"""
        equipment_id = db.add_equipment(sample_equipment)

        # Add multiple calibration records
        for i in range(3):
            record = CalibrationRecord(
                equipment_id=equipment_id,
                calibration_date=date.today() - timedelta(days=365 * i),
                next_calibration_due=date.today() + timedelta(days=365 * (1 - i)),
                calibration_lab="Test Lab",
                lab_accreditation="ISO/IEC 17025:2017",
                certificate_number=f"CAL-2024-{i}",
                traceability="NIST",
                calibration_results={},
                pass_fail=True,
                performed_by="Tech"
            )
            db.add_calibration_record(record)

        history = db.get_calibration_history(equipment_id)
        assert len(history) == 3
        # Should be sorted by date descending
        assert history[0].calibration_date >= history[1].calibration_date

    def test_get_calibration_due(self, db, sample_equipment):
        """Test getting equipment with calibration due"""
        # Equipment with calibration due soon
        sample_equipment.calibration_due_date = date.today() + timedelta(days=10)
        equipment_id1 = db.add_equipment(sample_equipment)

        # Equipment with calibration due later
        sample_equipment.serial_number = "IVT3000-2024-002"
        sample_equipment.calibration_due_date = date.today() + timedelta(days=200)
        equipment_id2 = db.add_equipment(sample_equipment)

        # Get equipment due in 30 days
        due_soon = db.get_calibration_due(days_ahead=30)
        assert len(due_soon) == 1
        assert due_soon[0].equipment_id == equipment_id1


class TestMaintenanceManagement:
    """Test maintenance management"""

    def test_add_maintenance_log(self, db, sample_equipment):
        """Test adding maintenance log"""
        equipment_id = db.add_equipment(sample_equipment)

        log = MaintenanceLog(
            equipment_id=equipment_id,
            maintenance_type=MaintenanceType.PREVENTIVE,
            scheduled_date=date.today(),
            completed_date=date.today(),
            performed_by="Maintenance Team",
            description="Annual preventive maintenance",
            parts_replaced=["Filter", "Fuse"],
            cost=150.00,
            verification_performed=True,
            verification_results="All tests passed",
            next_maintenance_due=date.today() + timedelta(days=180)
        )

        log_id = db.add_maintenance_log(log)
        assert log_id > 0

        # Verify equipment maintenance info was updated
        equipment = db.get_equipment(equipment_id)
        assert equipment.last_maintenance == date.today()
        assert equipment.next_maintenance_due == date.today() + timedelta(days=180)

    def test_maintenance_history(self, db, sample_equipment):
        """Test maintenance history retrieval"""
        equipment_id = db.add_equipment(sample_equipment)

        # Add multiple maintenance logs
        for i in range(3):
            log = MaintenanceLog(
                equipment_id=equipment_id,
                maintenance_type=MaintenanceType.PREVENTIVE,
                scheduled_date=date.today() - timedelta(days=30 * i),
                performed_by="Team",
                description=f"Maintenance {i}"
            )
            db.add_maintenance_log(log)

        history = db.get_maintenance_history(equipment_id)
        assert len(history) == 3


class TestReservationScheduling:
    """Test equipment reservation and scheduling"""

    def test_add_reservation(self, db, sample_equipment):
        """Test adding equipment reservation"""
        equipment_id = db.add_equipment(sample_equipment)

        reservation = EquipmentReservation(
            equipment_id=equipment_id,
            reserved_by="Jane Doe",
            start_time=datetime.now() + timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=3),
            purpose="Module testing"
        )

        reservation_id = db.add_reservation(reservation)
        assert reservation_id > 0

    def test_reservation_conflict(self, db, sample_equipment):
        """Test reservation conflict detection"""
        equipment_id = db.add_equipment(sample_equipment)

        # First reservation
        reservation1 = EquipmentReservation(
            equipment_id=equipment_id,
            reserved_by="User 1",
            start_time=datetime.now() + timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=3)
        )
        db.add_reservation(reservation1)

        # Overlapping reservation should fail
        reservation2 = EquipmentReservation(
            equipment_id=equipment_id,
            reserved_by="User 2",
            start_time=datetime.now() + timedelta(hours=2),
            end_time=datetime.now() + timedelta(hours=4)
        )

        with pytest.raises(ValueError, match="not available"):
            db.add_reservation(reservation2)

    def test_check_availability(self, db, sample_equipment):
        """Test availability checking"""
        equipment_id = db.add_equipment(sample_equipment)

        start = datetime.now() + timedelta(hours=1)
        end = datetime.now() + timedelta(hours=3)

        # Should be available initially
        conflicts = db.check_availability(equipment_id, start, end)
        assert len(conflicts) == 0

        # Add reservation
        reservation = EquipmentReservation(
            equipment_id=equipment_id,
            reserved_by="User",
            start_time=start,
            end_time=end
        )
        db.add_reservation(reservation)

        # Should have conflict now
        conflicts = db.check_availability(equipment_id, start, end)
        assert len(conflicts) == 1


class TestReporting:
    """Test reporting and analytics"""

    def test_equipment_utilization(self, db, sample_equipment):
        """Test equipment utilization calculation"""
        equipment_id = db.add_equipment(sample_equipment)

        # Simulate some usage
        for _ in range(3):
            db.checkout(equipment_id, user_name="Test User")
            db.checkin(equipment_id)

        start_date = date.today()
        end_date = date.today()

        stats = db.get_equipment_utilization(equipment_id, start_date, end_date)

        assert stats['equipment_id'] == equipment_id
        assert stats['total_uses'] == 3
        assert 'utilization_percentage' in stats
        assert 'average_use_duration' in stats


class TestISOCompliance:
    """Test ISO 17025 compliance features"""

    def test_calibration_traceability(self, db, sample_equipment):
        """Test calibration traceability requirements"""
        equipment_id = db.add_equipment(sample_equipment)

        # ISO 17025 requires traceability to national standards
        record = CalibrationRecord(
            equipment_id=equipment_id,
            calibration_date=date.today(),
            next_calibration_due=date.today() + timedelta(days=365),
            calibration_lab="Accredited Lab",
            lab_accreditation="ISO/IEC 17025:2017",
            certificate_number="CAL-TRACE-001",
            standard_used="NIST Reference Standard XYZ",
            traceability="NIST",
            calibration_results={"test": "passed"},
            pass_fail=True,
            performed_by="Technician"
        )

        record_id = db.add_calibration_record(record)
        assert record_id > 0

        # Verify traceability information is stored
        history = db.get_calibration_history(equipment_id)
        assert history[0].traceability == "NIST"
        assert history[0].lab_accreditation == "ISO/IEC 17025:2017"

    def test_maintenance_verification(self, db, sample_equipment):
        """Test maintenance verification requirements"""
        equipment_id = db.add_equipment(sample_equipment)

        # ISO 17025 requires verification after maintenance
        log = MaintenanceLog(
            equipment_id=equipment_id,
            maintenance_type=MaintenanceType.CORRECTIVE,
            scheduled_date=date.today(),
            completed_date=date.today(),
            performed_by="Technician",
            description="Replaced sensor",
            verification_performed=True,
            verification_results="Verification tests passed within specifications"
        )

        log_id = db.add_maintenance_log(log)
        history = db.get_maintenance_history(equipment_id)

        assert history[0].verification_performed is True
        assert history[0].verification_results is not None

    def test_equipment_status_compliance(self, db, sample_equipment):
        """Test that equipment with issues cannot be used"""
        # Equipment past calibration
        sample_equipment.calibration_due_date = date.today() - timedelta(days=1)
        equipment_id = db.add_equipment(sample_equipment)

        # Should not be able to checkout equipment with overdue calibration
        with pytest.raises(ValueError, match="calibration is overdue"):
            db.checkout(equipment_id, user_name="Test User")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
