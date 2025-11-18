"""
Equipment Database Manager
ISO 17025 compliant equipment tracking and management system
"""
import sqlite3
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path
import json
from contextlib import contextmanager

from .models import (
    Equipment,
    EquipmentStatus,
    EquipmentCategory,
    UsageLog,
    MaintenanceLog,
    CalibrationRecord,
    EquipmentReservation,
    MaintenanceType
)


class EquipmentDB:
    """
    Equipment Database Manager

    Provides complete equipment lifecycle management including:
    - Equipment registry and CRUD operations
    - Usage tracking (checkout/checkin)
    - Calibration management (ISO 17025)
    - Maintenance tracking
    - Availability scheduling
    - Service history
    """

    def __init__(self, db_path: str = "equipment.db"):
        """
        Initialize equipment database

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _init_database(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Equipment table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS equipment (
                    equipment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    manufacturer TEXT NOT NULL,
                    model TEXT NOT NULL,
                    serial_number TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL,
                    location TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'available',

                    calibration_due_date TEXT NOT NULL,
                    calibration_interval_days INTEGER DEFAULT 365,
                    last_calibration_date TEXT,
                    calibration_certificate_number TEXT,

                    last_maintenance TEXT,
                    next_maintenance_due TEXT,

                    specifications TEXT,
                    accuracy TEXT,
                    measurement_range TEXT,

                    purchase_date TEXT,
                    purchase_cost REAL,
                    warranty_expiry TEXT,
                    responsible_person TEXT,

                    asset_tag TEXT,
                    notes TEXT,

                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Usage log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage_log (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id INTEGER NOT NULL,
                    test_id INTEGER,
                    user_name TEXT NOT NULL,

                    checkout_time TEXT NOT NULL,
                    checkin_time TEXT,

                    purpose TEXT,
                    location_used TEXT,

                    condition_at_checkout TEXT DEFAULT 'good',
                    condition_at_checkin TEXT,
                    issues_reported TEXT,

                    created_at TEXT NOT NULL,

                    FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id)
                )
            """)

            # Maintenance log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS maintenance_log (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id INTEGER NOT NULL,
                    maintenance_type TEXT NOT NULL,

                    scheduled_date TEXT NOT NULL,
                    completed_date TEXT,

                    performed_by TEXT NOT NULL,
                    description TEXT NOT NULL,

                    parts_replaced TEXT,
                    cost REAL,

                    verification_performed INTEGER DEFAULT 0,
                    verification_results TEXT,

                    next_maintenance_due TEXT,
                    attachments TEXT,
                    notes TEXT,

                    created_at TEXT NOT NULL,

                    FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id)
                )
            """)

            # Calibration records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS calibration_record (
                    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id INTEGER NOT NULL,

                    calibration_date TEXT NOT NULL,
                    next_calibration_due TEXT NOT NULL,

                    calibration_lab TEXT NOT NULL,
                    lab_accreditation TEXT NOT NULL,
                    certificate_number TEXT NOT NULL UNIQUE,

                    standard_used TEXT,
                    traceability TEXT NOT NULL,

                    calibration_results TEXT NOT NULL,
                    measurement_uncertainty TEXT,
                    pass_fail INTEGER NOT NULL,

                    temperature REAL,
                    humidity REAL,

                    certificate_path TEXT,
                    performed_by TEXT NOT NULL,
                    verified_by TEXT,

                    notes TEXT,
                    created_at TEXT NOT NULL,

                    FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id)
                )
            """)

            # Reservations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reservations (
                    reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id INTEGER NOT NULL,

                    reserved_by TEXT NOT NULL,
                    test_id INTEGER,

                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,

                    purpose TEXT,
                    status TEXT DEFAULT 'confirmed',

                    created_at TEXT NOT NULL,

                    FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id)
                )
            """)

            # Create indexes for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_equipment_status
                ON equipment(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_equipment_category
                ON equipment(category)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_equipment_calibration_due
                ON equipment(calibration_due_date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_usage_log_equipment
                ON usage_log(equipment_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_usage_log_active
                ON usage_log(checkin_time)
            """)

    # ==================== Equipment CRUD Operations ====================

    def add_equipment(self, equipment: Equipment) -> int:
        """
        Add new equipment to database

        Args:
            equipment: Equipment object

        Returns:
            equipment_id: ID of newly created equipment
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO equipment (
                    name, manufacturer, model, serial_number, category, location, status,
                    calibration_due_date, calibration_interval_days, last_calibration_date,
                    calibration_certificate_number, last_maintenance, next_maintenance_due,
                    specifications, accuracy, measurement_range,
                    purchase_date, purchase_cost, warranty_expiry, responsible_person,
                    asset_tag, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                equipment.name,
                equipment.manufacturer,
                equipment.model,
                equipment.serial_number,
                equipment.category,
                equipment.location,
                equipment.status,
                equipment.calibration_due_date.isoformat(),
                equipment.calibration_interval_days,
                equipment.last_calibration_date.isoformat() if equipment.last_calibration_date else None,
                equipment.calibration_certificate_number,
                equipment.last_maintenance.isoformat() if equipment.last_maintenance else None,
                equipment.next_maintenance_due.isoformat() if equipment.next_maintenance_due else None,
                json.dumps(equipment.specifications) if equipment.specifications else None,
                equipment.accuracy,
                equipment.measurement_range,
                equipment.purchase_date.isoformat() if equipment.purchase_date else None,
                equipment.purchase_cost,
                equipment.warranty_expiry.isoformat() if equipment.warranty_expiry else None,
                equipment.responsible_person,
                equipment.asset_tag,
                equipment.notes,
                equipment.created_at.isoformat(),
                equipment.updated_at.isoformat()
            ))

            return cursor.lastrowid

    def get_equipment(self, equipment_id: int) -> Optional[Equipment]:
        """
        Get equipment by ID

        Args:
            equipment_id: Equipment ID

        Returns:
            Equipment object or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM equipment WHERE equipment_id = ?", (equipment_id,))
            row = cursor.fetchone()

            if row:
                return self._row_to_equipment(row)
            return None

    def update_equipment(self, equipment_id: int, **kwargs) -> bool:
        """
        Update equipment fields

        Args:
            equipment_id: Equipment ID
            **kwargs: Fields to update

        Returns:
            True if updated successfully
        """
        if not kwargs:
            return False

        # Add updated_at timestamp
        kwargs['updated_at'] = datetime.now().isoformat()

        # Handle special types
        for key, value in kwargs.items():
            if isinstance(value, (date, datetime)):
                kwargs[key] = value.isoformat()
            elif isinstance(value, dict):
                kwargs[key] = json.dumps(value)

        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [equipment_id]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE equipment SET {set_clause} WHERE equipment_id = ?",
                values
            )
            return cursor.rowcount > 0

    def delete_equipment(self, equipment_id: int) -> bool:
        """
        Delete equipment (soft delete by setting status to retired)

        Args:
            equipment_id: Equipment ID

        Returns:
            True if deleted successfully
        """
        return self.update_equipment(
            equipment_id,
            status=EquipmentStatus.RETIRED
        )

    def list_equipment(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        location: Optional[str] = None
    ) -> List[Equipment]:
        """
        List equipment with optional filters

        Args:
            category: Filter by category
            status: Filter by status
            location: Filter by location

        Returns:
            List of Equipment objects
        """
        query = "SELECT * FROM equipment WHERE 1=1"
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)

        if status:
            query += " AND status = ?"
            params.append(status)

        if location:
            query += " AND location = ?"
            params.append(location)

        query += " ORDER BY name"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_equipment(row) for row in rows]

    def get_available(
        self,
        category: Optional[str] = None,
        location: Optional[str] = None
    ) -> List[Equipment]:
        """
        Get available equipment

        Args:
            category: Filter by category (e.g., "iv_tracer")
            location: Filter by location

        Returns:
            List of available Equipment objects
        """
        return self.list_equipment(
            category=category,
            status=EquipmentStatus.AVAILABLE,
            location=location
        )

    # ==================== Usage Tracking ====================

    def checkout(
        self,
        equipment_id: int,
        user_name: str,
        test_id: Optional[int] = None,
        purpose: Optional[str] = None,
        location_used: Optional[str] = None
    ) -> int:
        """
        Check out equipment for use

        Args:
            equipment_id: Equipment ID
            user_name: User checking out equipment
            test_id: Optional test ID
            purpose: Purpose of use
            location_used: Location where equipment will be used

        Returns:
            log_id: Usage log ID

        Raises:
            ValueError: If equipment is not available
        """
        # Check equipment availability
        equipment = self.get_equipment(equipment_id)
        if not equipment:
            raise ValueError(f"Equipment {equipment_id} not found")

        if equipment.status != EquipmentStatus.AVAILABLE:
            raise ValueError(
                f"Equipment {equipment_id} is not available (status: {equipment.status})"
            )

        # Check for calibration due
        if equipment.calibration_due_date < date.today():
            raise ValueError(
                f"Equipment {equipment_id} calibration is overdue. "
                f"Due date: {equipment.calibration_due_date}"
            )

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create usage log
            usage_log = UsageLog(
                equipment_id=equipment_id,
                test_id=test_id,
                user_name=user_name,
                purpose=purpose,
                location_used=location_used
            )

            cursor.execute("""
                INSERT INTO usage_log (
                    equipment_id, test_id, user_name, checkout_time,
                    purpose, location_used, condition_at_checkout, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                usage_log.equipment_id,
                usage_log.test_id,
                usage_log.user_name,
                usage_log.checkout_time.isoformat(),
                usage_log.purpose,
                usage_log.location_used,
                usage_log.condition_at_checkout,
                usage_log.created_at.isoformat()
            ))

            log_id = cursor.lastrowid

            # Update equipment status
            cursor.execute("""
                UPDATE equipment
                SET status = ?, updated_at = ?
                WHERE equipment_id = ?
            """, (EquipmentStatus.IN_USE, datetime.now().isoformat(), equipment_id))

            return log_id

    def checkin(
        self,
        equipment_id: int,
        condition: str = "good",
        issues_reported: Optional[str] = None
    ) -> bool:
        """
        Check in equipment after use

        Args:
            equipment_id: Equipment ID
            condition: Equipment condition at checkin
            issues_reported: Any issues to report

        Returns:
            True if checked in successfully

        Raises:
            ValueError: If equipment is not checked out
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Find active usage log
            cursor.execute("""
                SELECT log_id FROM usage_log
                WHERE equipment_id = ? AND checkin_time IS NULL
                ORDER BY checkout_time DESC
                LIMIT 1
            """, (equipment_id,))

            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Equipment {equipment_id} is not checked out")

            log_id = row[0]

            # Update usage log
            cursor.execute("""
                UPDATE usage_log
                SET checkin_time = ?,
                    condition_at_checkin = ?,
                    issues_reported = ?
                WHERE log_id = ?
            """, (
                datetime.now().isoformat(),
                condition,
                issues_reported,
                log_id
            ))

            # Update equipment status
            new_status = EquipmentStatus.AVAILABLE
            if issues_reported:
                new_status = EquipmentStatus.MAINTENANCE

            cursor.execute("""
                UPDATE equipment
                SET status = ?, updated_at = ?
                WHERE equipment_id = ?
            """, (new_status, datetime.now().isoformat(), equipment_id))

            return True

    def get_usage_history(
        self,
        equipment_id: Optional[int] = None,
        user_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[UsageLog]:
        """
        Get equipment usage history

        Args:
            equipment_id: Filter by equipment ID
            user_name: Filter by user
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            List of UsageLog objects
        """
        query = "SELECT * FROM usage_log WHERE 1=1"
        params = []

        if equipment_id:
            query += " AND equipment_id = ?"
            params.append(equipment_id)

        if user_name:
            query += " AND user_name = ?"
            params.append(user_name)

        if start_date:
            query += " AND date(checkout_time) >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND date(checkout_time) <= ?"
            params.append(end_date.isoformat())

        query += " ORDER BY checkout_time DESC"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_usage_log(row) for row in rows]

    # ==================== Calibration Management ====================

    def add_calibration_record(self, record: CalibrationRecord) -> int:
        """
        Add calibration record

        Args:
            record: CalibrationRecord object

        Returns:
            record_id: Calibration record ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO calibration_record (
                    equipment_id, calibration_date, next_calibration_due,
                    calibration_lab, lab_accreditation, certificate_number,
                    standard_used, traceability,
                    calibration_results, measurement_uncertainty, pass_fail,
                    temperature, humidity,
                    certificate_path, performed_by, verified_by,
                    notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.equipment_id,
                record.calibration_date.isoformat(),
                record.next_calibration_due.isoformat(),
                record.calibration_lab,
                record.lab_accreditation,
                record.certificate_number,
                record.standard_used,
                record.traceability,
                json.dumps(record.calibration_results),
                json.dumps(record.measurement_uncertainty) if record.measurement_uncertainty else None,
                int(record.pass_fail),
                record.temperature,
                record.humidity,
                record.certificate_path,
                record.performed_by,
                record.verified_by,
                record.notes,
                record.created_at.isoformat()
            ))

            record_id = cursor.lastrowid

            # Update equipment calibration info
            cursor.execute("""
                UPDATE equipment
                SET last_calibration_date = ?,
                    calibration_due_date = ?,
                    calibration_certificate_number = ?,
                    updated_at = ?
                WHERE equipment_id = ?
            """, (
                record.calibration_date.isoformat(),
                record.next_calibration_due.isoformat(),
                record.certificate_number,
                datetime.now().isoformat(),
                record.equipment_id
            ))

            return record_id

    def get_calibration_history(self, equipment_id: int) -> List[CalibrationRecord]:
        """
        Get calibration history for equipment

        Args:
            equipment_id: Equipment ID

        Returns:
            List of CalibrationRecord objects
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM calibration_record
                WHERE equipment_id = ?
                ORDER BY calibration_date DESC
            """, (equipment_id,))

            rows = cursor.fetchall()
            return [self._row_to_calibration_record(row) for row in rows]

    def get_calibration_due(self, days_ahead: int = 30) -> List[Equipment]:
        """
        Get equipment with calibration due within specified days

        Args:
            days_ahead: Number of days to look ahead

        Returns:
            List of Equipment objects
        """
        due_date = (date.today() + timedelta(days=days_ahead)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM equipment
                WHERE calibration_due_date <= ?
                AND status != 'retired'
                ORDER BY calibration_due_date
            """, (due_date,))

            rows = cursor.fetchall()
            return [self._row_to_equipment(row) for row in rows]

    # ==================== Maintenance Management ====================

    def add_maintenance_log(self, log: MaintenanceLog) -> int:
        """
        Add maintenance log entry

        Args:
            log: MaintenanceLog object

        Returns:
            log_id: Maintenance log ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO maintenance_log (
                    equipment_id, maintenance_type, scheduled_date, completed_date,
                    performed_by, description,
                    parts_replaced, cost,
                    verification_performed, verification_results,
                    next_maintenance_due, attachments, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log.equipment_id,
                log.maintenance_type,
                log.scheduled_date.isoformat(),
                log.completed_date.isoformat() if log.completed_date else None,
                log.performed_by,
                log.description,
                json.dumps(log.parts_replaced) if log.parts_replaced else None,
                log.cost,
                int(log.verification_performed),
                log.verification_results,
                log.next_maintenance_due.isoformat() if log.next_maintenance_due else None,
                json.dumps(log.attachments) if log.attachments else None,
                log.notes,
                log.created_at.isoformat()
            ))

            log_id = cursor.lastrowid

            # Update equipment maintenance info if completed
            if log.completed_date:
                cursor.execute("""
                    UPDATE equipment
                    SET last_maintenance = ?,
                        next_maintenance_due = ?,
                        updated_at = ?
                    WHERE equipment_id = ?
                """, (
                    log.completed_date.isoformat(),
                    log.next_maintenance_due.isoformat() if log.next_maintenance_due else None,
                    datetime.now().isoformat(),
                    log.equipment_id
                ))

            return log_id

    def get_maintenance_history(self, equipment_id: int) -> List[MaintenanceLog]:
        """
        Get maintenance history for equipment

        Args:
            equipment_id: Equipment ID

        Returns:
            List of MaintenanceLog objects
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM maintenance_log
                WHERE equipment_id = ?
                ORDER BY scheduled_date DESC
            """, (equipment_id,))

            rows = cursor.fetchall()
            return [self._row_to_maintenance_log(row) for row in rows]

    # ==================== Availability & Scheduling ====================

    def add_reservation(self, reservation: EquipmentReservation) -> int:
        """
        Add equipment reservation

        Args:
            reservation: EquipmentReservation object

        Returns:
            reservation_id: Reservation ID

        Raises:
            ValueError: If equipment is not available for the time slot
        """
        # Check for conflicts
        conflicts = self.check_availability(
            reservation.equipment_id,
            reservation.start_time,
            reservation.end_time
        )

        if conflicts:
            raise ValueError(
                f"Equipment {reservation.equipment_id} is not available "
                f"from {reservation.start_time} to {reservation.end_time}"
            )

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO reservations (
                    equipment_id, reserved_by, test_id,
                    start_time, end_time, purpose, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                reservation.equipment_id,
                reservation.reserved_by,
                reservation.test_id,
                reservation.start_time.isoformat(),
                reservation.end_time.isoformat(),
                reservation.purpose,
                reservation.status,
                reservation.created_at.isoformat()
            ))

            return cursor.lastrowid

    def check_availability(
        self,
        equipment_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> List[EquipmentReservation]:
        """
        Check equipment availability for time period

        Args:
            equipment_id: Equipment ID
            start_time: Start time
            end_time: End time

        Returns:
            List of conflicting reservations
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM reservations
                WHERE equipment_id = ?
                AND status = 'confirmed'
                AND (
                    (start_time <= ? AND end_time > ?)
                    OR (start_time < ? AND end_time >= ?)
                    OR (start_time >= ? AND end_time <= ?)
                )
            """, (
                equipment_id,
                start_time.isoformat(), start_time.isoformat(),
                end_time.isoformat(), end_time.isoformat(),
                start_time.isoformat(), end_time.isoformat()
            ))

            rows = cursor.fetchall()
            return [self._row_to_reservation(row) for row in rows]

    def get_reservations(
        self,
        equipment_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[EquipmentReservation]:
        """
        Get equipment reservations

        Args:
            equipment_id: Filter by equipment ID
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            List of EquipmentReservation objects
        """
        query = "SELECT * FROM reservations WHERE status = 'confirmed'"
        params = []

        if equipment_id:
            query += " AND equipment_id = ?"
            params.append(equipment_id)

        if start_date:
            query += " AND date(start_time) >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND date(end_time) <= ?"
            params.append(end_date.isoformat())

        query += " ORDER BY start_time"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_reservation(row) for row in rows]

    # ==================== Status Management ====================

    def update_status(self, equipment_id: int, status: EquipmentStatus) -> bool:
        """
        Update equipment status

        Args:
            equipment_id: Equipment ID
            status: New status

        Returns:
            True if updated successfully
        """
        return self.update_equipment(equipment_id, status=status)

    def get_equipment_by_status(self, status: EquipmentStatus) -> List[Equipment]:
        """
        Get all equipment with specified status

        Args:
            status: Equipment status

        Returns:
            List of Equipment objects
        """
        return self.list_equipment(status=status)

    # ==================== Reporting & Analytics ====================

    def get_equipment_utilization(
        self,
        equipment_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Calculate equipment utilization statistics

        Args:
            equipment_id: Equipment ID
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary with utilization statistics
        """
        usage_logs = self.get_usage_history(
            equipment_id=equipment_id,
            start_date=start_date,
            end_date=end_date
        )

        total_hours = 0
        total_uses = len(usage_logs)

        for log in usage_logs:
            if log.usage_duration:
                total_hours += log.usage_duration

        period_days = (end_date - start_date).days + 1
        available_hours = period_days * 24

        return {
            "equipment_id": equipment_id,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_uses": total_uses,
            "total_hours": round(total_hours, 2),
            "available_hours": available_hours,
            "utilization_percentage": round((total_hours / available_hours) * 100, 2) if available_hours > 0 else 0,
            "average_use_duration": round(total_hours / total_uses, 2) if total_uses > 0 else 0
        }

    # ==================== Helper Methods ====================

    def _row_to_equipment(self, row: sqlite3.Row) -> Equipment:
        """Convert database row to Equipment object"""
        return Equipment(
            equipment_id=row['equipment_id'],
            name=row['name'],
            manufacturer=row['manufacturer'],
            model=row['model'],
            serial_number=row['serial_number'],
            category=row['category'],
            location=row['location'],
            status=row['status'],
            calibration_due_date=date.fromisoformat(row['calibration_due_date']),
            calibration_interval_days=row['calibration_interval_days'],
            last_calibration_date=date.fromisoformat(row['last_calibration_date']) if row['last_calibration_date'] else None,
            calibration_certificate_number=row['calibration_certificate_number'],
            last_maintenance=date.fromisoformat(row['last_maintenance']) if row['last_maintenance'] else None,
            next_maintenance_due=date.fromisoformat(row['next_maintenance_due']) if row['next_maintenance_due'] else None,
            specifications=json.loads(row['specifications']) if row['specifications'] else {},
            accuracy=row['accuracy'],
            measurement_range=row['measurement_range'],
            purchase_date=date.fromisoformat(row['purchase_date']) if row['purchase_date'] else None,
            purchase_cost=row['purchase_cost'],
            warranty_expiry=date.fromisoformat(row['warranty_expiry']) if row['warranty_expiry'] else None,
            responsible_person=row['responsible_person'],
            asset_tag=row['asset_tag'],
            notes=row['notes'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )

    def _row_to_usage_log(self, row: sqlite3.Row) -> UsageLog:
        """Convert database row to UsageLog object"""
        return UsageLog(
            log_id=row['log_id'],
            equipment_id=row['equipment_id'],
            test_id=row['test_id'],
            user_name=row['user_name'],
            checkout_time=datetime.fromisoformat(row['checkout_time']),
            checkin_time=datetime.fromisoformat(row['checkin_time']) if row['checkin_time'] else None,
            purpose=row['purpose'],
            location_used=row['location_used'],
            condition_at_checkout=row['condition_at_checkout'],
            condition_at_checkin=row['condition_at_checkin'],
            issues_reported=row['issues_reported'],
            created_at=datetime.fromisoformat(row['created_at'])
        )

    def _row_to_maintenance_log(self, row: sqlite3.Row) -> MaintenanceLog:
        """Convert database row to MaintenanceLog object"""
        return MaintenanceLog(
            log_id=row['log_id'],
            equipment_id=row['equipment_id'],
            maintenance_type=row['maintenance_type'],
            scheduled_date=date.fromisoformat(row['scheduled_date']),
            completed_date=date.fromisoformat(row['completed_date']) if row['completed_date'] else None,
            performed_by=row['performed_by'],
            description=row['description'],
            parts_replaced=json.loads(row['parts_replaced']) if row['parts_replaced'] else [],
            cost=row['cost'],
            verification_performed=bool(row['verification_performed']),
            verification_results=row['verification_results'],
            next_maintenance_due=date.fromisoformat(row['next_maintenance_due']) if row['next_maintenance_due'] else None,
            attachments=json.loads(row['attachments']) if row['attachments'] else [],
            notes=row['notes'],
            created_at=datetime.fromisoformat(row['created_at'])
        )

    def _row_to_calibration_record(self, row: sqlite3.Row) -> CalibrationRecord:
        """Convert database row to CalibrationRecord object"""
        return CalibrationRecord(
            record_id=row['record_id'],
            equipment_id=row['equipment_id'],
            calibration_date=date.fromisoformat(row['calibration_date']),
            next_calibration_due=date.fromisoformat(row['next_calibration_due']),
            calibration_lab=row['calibration_lab'],
            lab_accreditation=row['lab_accreditation'],
            certificate_number=row['certificate_number'],
            standard_used=row['standard_used'],
            traceability=row['traceability'],
            calibration_results=json.loads(row['calibration_results']),
            measurement_uncertainty=json.loads(row['measurement_uncertainty']) if row['measurement_uncertainty'] else None,
            pass_fail=bool(row['pass_fail']),
            temperature=row['temperature'],
            humidity=row['humidity'],
            certificate_path=row['certificate_path'],
            performed_by=row['performed_by'],
            verified_by=row['verified_by'],
            notes=row['notes'],
            created_at=datetime.fromisoformat(row['created_at'])
        )

    def _row_to_reservation(self, row: sqlite3.Row) -> EquipmentReservation:
        """Convert database row to EquipmentReservation object"""
        return EquipmentReservation(
            reservation_id=row['reservation_id'],
            equipment_id=row['equipment_id'],
            reserved_by=row['reserved_by'],
            test_id=row['test_id'],
            start_time=datetime.fromisoformat(row['start_time']),
            end_time=datetime.fromisoformat(row['end_time']),
            purpose=row['purpose'],
            status=row['status'],
            created_at=datetime.fromisoformat(row['created_at'])
        )
