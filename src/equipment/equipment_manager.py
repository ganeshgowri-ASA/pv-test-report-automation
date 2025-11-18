"""
Equipment Manager (Session 31)

Equipment registry, tracking, usage logging, maintenance scheduling,
equipment status management, and asset allocation.
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal
import json
import logging
from pathlib import Path

from .models import (
    Equipment,
    EquipmentStatus,
    EquipmentCategory,
    UsageLog
)


logger = logging.getLogger(__name__)


class EquipmentManager:
    """
    Equipment management system

    Handles equipment registry, tracking, usage logging, maintenance scheduling,
    and asset allocation for PV testing equipment.
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize equipment manager

        Args:
            storage_path: Path to store equipment data (JSON files)
        """
        self.storage_path = Path(storage_path) if storage_path else Path("./data/equipment")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.equipment_file = self.storage_path / "equipment.json"
        self.usage_log_file = self.storage_path / "usage_logs.json"

        self._equipment_registry: Dict[str, Equipment] = {}
        self._usage_logs: List[UsageLog] = []

        self._load_data()

    def _load_data(self) -> None:
        """Load equipment data from storage"""
        try:
            if self.equipment_file.exists():
                with open(self.equipment_file, 'r') as f:
                    data = json.load(f)
                    self._equipment_registry = {
                        item['equipment_id']: Equipment.from_dict(item)
                        for item in data
                    }
                logger.info(f"Loaded {len(self._equipment_registry)} equipment records")

            if self.usage_log_file.exists():
                with open(self.usage_log_file, 'r') as f:
                    data = json.load(f)
                    self._usage_logs = [UsageLog.from_dict(item) for item in data]
                logger.info(f"Loaded {len(self._usage_logs)} usage log records")

        except Exception as e:
            logger.error(f"Error loading equipment data: {e}")

    def _save_data(self) -> None:
        """Save equipment data to storage"""
        try:
            # Save equipment registry
            with open(self.equipment_file, 'w') as f:
                data = [eq.to_dict() for eq in self._equipment_registry.values()]
                json.dump(data, f, indent=2)

            # Save usage logs
            with open(self.usage_log_file, 'w') as f:
                data = [log.to_dict() for log in self._usage_logs]
                json.dump(data, f, indent=2)

            logger.info("Equipment data saved successfully")

        except Exception as e:
            logger.error(f"Error saving equipment data: {e}")
            raise

    # ==================== Equipment Registry ====================

    def register_equipment(self, equipment: Equipment) -> str:
        """
        Register new equipment

        Args:
            equipment: Equipment object to register

        Returns:
            equipment_id of registered equipment
        """
        equipment.updated_at = datetime.now()
        self._equipment_registry[equipment.equipment_id] = equipment
        self._save_data()

        logger.info(f"Registered equipment: {equipment.name} ({equipment.equipment_id})")
        return equipment.equipment_id

    def update_equipment(self, equipment_id: str, updates: Dict[str, Any]) -> Equipment:
        """
        Update equipment information

        Args:
            equipment_id: Equipment ID to update
            updates: Dictionary of fields to update

        Returns:
            Updated Equipment object

        Raises:
            ValueError: If equipment not found
        """
        if equipment_id not in self._equipment_registry:
            raise ValueError(f"Equipment not found: {equipment_id}")

        equipment = self._equipment_registry[equipment_id]

        # Update fields
        for key, value in updates.items():
            if hasattr(equipment, key):
                setattr(equipment, key, value)

        equipment.updated_at = datetime.now()
        self._save_data()

        logger.info(f"Updated equipment: {equipment_id}")
        return equipment

    def get_equipment(self, equipment_id: str) -> Optional[Equipment]:
        """
        Get equipment by ID

        Args:
            equipment_id: Equipment ID

        Returns:
            Equipment object or None if not found
        """
        return self._equipment_registry.get(equipment_id)

    def get_equipment_by_asset_number(self, asset_number: str) -> Optional[Equipment]:
        """
        Get equipment by asset number

        Args:
            asset_number: Asset tracking number

        Returns:
            Equipment object or None if not found
        """
        for equipment in self._equipment_registry.values():
            if equipment.asset_number == asset_number:
                return equipment
        return None

    def get_equipment_by_serial(self, serial_number: str) -> Optional[Equipment]:
        """
        Get equipment by serial number

        Args:
            serial_number: Serial number

        Returns:
            Equipment object or None if not found
        """
        for equipment in self._equipment_registry.values():
            if equipment.serial_number == serial_number:
                return equipment
        return None

    def list_equipment(
        self,
        status: Optional[EquipmentStatus] = None,
        category: Optional[EquipmentCategory] = None,
        location: Optional[str] = None
    ) -> List[Equipment]:
        """
        List equipment with optional filters

        Args:
            status: Filter by equipment status
            category: Filter by equipment category
            location: Filter by location

        Returns:
            List of Equipment objects matching filters
        """
        equipment_list = list(self._equipment_registry.values())

        if status:
            equipment_list = [eq for eq in equipment_list if eq.status == status]

        if category:
            equipment_list = [eq for eq in equipment_list if eq.category == category]

        if location:
            equipment_list = [eq for eq in equipment_list if eq.location == location]

        return equipment_list

    def retire_equipment(self, equipment_id: str, notes: str = "") -> Equipment:
        """
        Retire equipment from active service

        Args:
            equipment_id: Equipment ID to retire
            notes: Retirement notes

        Returns:
            Updated Equipment object
        """
        return self.update_equipment(equipment_id, {
            'status': EquipmentStatus.RETIRED,
            'notes': notes
        })

    # ==================== Equipment Status Management ====================

    def set_equipment_status(
        self,
        equipment_id: str,
        status: EquipmentStatus,
        notes: str = ""
    ) -> Equipment:
        """
        Update equipment status

        Args:
            equipment_id: Equipment ID
            status: New status
            notes: Status change notes

        Returns:
            Updated Equipment object
        """
        return self.update_equipment(equipment_id, {
            'status': status,
            'notes': notes
        })

    def reserve_equipment(
        self,
        equipment_id: str,
        reserved_by: str,
        notes: str = ""
    ) -> Equipment:
        """
        Reserve equipment for specific use

        Args:
            equipment_id: Equipment ID
            reserved_by: Person reserving the equipment
            notes: Reservation notes

        Returns:
            Updated Equipment object
        """
        return self.update_equipment(equipment_id, {
            'status': EquipmentStatus.RESERVED,
            'responsible_person': reserved_by,
            'notes': notes
        })

    def release_equipment(self, equipment_id: str) -> Equipment:
        """
        Release reserved equipment back to active status

        Args:
            equipment_id: Equipment ID

        Returns:
            Updated Equipment object
        """
        return self.update_equipment(equipment_id, {
            'status': EquipmentStatus.ACTIVE,
            'notes': "Released from reservation"
        })

    def get_available_equipment(
        self,
        category: Optional[EquipmentCategory] = None
    ) -> List[Equipment]:
        """
        Get list of available equipment (active status)

        Args:
            category: Optional category filter

        Returns:
            List of available Equipment objects
        """
        return self.list_equipment(status=EquipmentStatus.ACTIVE, category=category)

    # ==================== Usage Logging ====================

    def start_usage(
        self,
        equipment_id: str,
        operator: str,
        test_id: Optional[str] = None,
        project_id: Optional[str] = None,
        test_type: str = "",
        notes: str = ""
    ) -> str:
        """
        Start equipment usage logging

        Args:
            equipment_id: Equipment ID
            operator: Operator name
            test_id: Optional test ID
            project_id: Optional project ID
            test_type: Type of test
            notes: Usage notes

        Returns:
            log_id of created usage log
        """
        usage_log = UsageLog(
            equipment_id=equipment_id,
            operator=operator,
            test_id=test_id,
            project_id=project_id,
            test_type=test_type,
            notes=notes,
            start_time=datetime.now()
        )

        self._usage_logs.append(usage_log)

        # Update equipment last_used
        if equipment_id in self._equipment_registry:
            self._equipment_registry[equipment_id].last_used = datetime.now()

        self._save_data()

        logger.info(f"Started usage log for equipment {equipment_id} by {operator}")
        return usage_log.log_id

    def end_usage(self, log_id: str, notes: str = "") -> UsageLog:
        """
        End equipment usage logging

        Args:
            log_id: Usage log ID
            notes: Additional notes

        Returns:
            Updated UsageLog object

        Raises:
            ValueError: If log not found
        """
        usage_log = None
        for log in self._usage_logs:
            if log.log_id == log_id:
                usage_log = log
                break

        if not usage_log:
            raise ValueError(f"Usage log not found: {log_id}")

        usage_log.end_time = datetime.now()
        duration = (usage_log.end_time - usage_log.start_time).total_seconds() / 3600
        usage_log.duration_hours = Decimal(str(duration))

        if notes:
            usage_log.notes = f"{usage_log.notes}\n{notes}" if usage_log.notes else notes

        # Update equipment total usage hours
        if usage_log.equipment_id in self._equipment_registry:
            equipment = self._equipment_registry[usage_log.equipment_id]
            equipment.total_usage_hours += usage_log.duration_hours
            equipment.test_count += 1

        self._save_data()

        logger.info(f"Ended usage log {log_id}, duration: {usage_log.duration_hours:.2f} hours")
        return usage_log

    def get_usage_logs(
        self,
        equipment_id: Optional[str] = None,
        operator: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[UsageLog]:
        """
        Get usage logs with optional filters

        Args:
            equipment_id: Filter by equipment ID
            operator: Filter by operator
            start_date: Filter by start date (inclusive)
            end_date: Filter by end date (inclusive)

        Returns:
            List of UsageLog objects
        """
        logs = self._usage_logs

        if equipment_id:
            logs = [log for log in logs if log.equipment_id == equipment_id]

        if operator:
            logs = [log for log in logs if log.operator == operator]

        if start_date:
            logs = [log for log in logs if log.start_time.date() >= start_date]

        if end_date:
            logs = [log for log in logs if log.start_time.date() <= end_date]

        return logs

    # ==================== Maintenance Scheduling ====================

    def schedule_maintenance(
        self,
        equipment_id: str,
        maintenance_date: date,
        notes: str = ""
    ) -> Equipment:
        """
        Schedule equipment maintenance

        Args:
            equipment_id: Equipment ID
            maintenance_date: Scheduled maintenance date
            notes: Maintenance notes

        Returns:
            Updated Equipment object
        """
        return self.update_equipment(equipment_id, {
            'next_maintenance': maintenance_date,
            'notes': notes
        })

    def complete_maintenance(
        self,
        equipment_id: str,
        maintenance_date: Optional[date] = None,
        next_maintenance: Optional[date] = None,
        notes: str = ""
    ) -> Equipment:
        """
        Record completed maintenance

        Args:
            equipment_id: Equipment ID
            maintenance_date: Date maintenance was completed (default: today)
            next_maintenance: Next scheduled maintenance date
            notes: Maintenance notes

        Returns:
            Updated Equipment object
        """
        if maintenance_date is None:
            maintenance_date = date.today()

        updates = {
            'last_maintenance': maintenance_date,
            'status': EquipmentStatus.ACTIVE,
            'notes': notes
        }

        if next_maintenance:
            updates['next_maintenance'] = next_maintenance

        return self.update_equipment(equipment_id, updates)

    def get_maintenance_due(
        self,
        days_ahead: int = 30
    ) -> List[Equipment]:
        """
        Get equipment with maintenance due within specified days

        Args:
            days_ahead: Number of days to look ahead

        Returns:
            List of Equipment objects with maintenance due
        """
        cutoff_date = date.today() + timedelta(days=days_ahead)
        equipment_list = []

        for equipment in self._equipment_registry.values():
            if equipment.next_maintenance and equipment.next_maintenance <= cutoff_date:
                equipment_list.append(equipment)

        # Sort by due date
        equipment_list.sort(key=lambda eq: eq.next_maintenance or date.max)

        return equipment_list

    def get_overdue_maintenance(self) -> List[Equipment]:
        """
        Get equipment with overdue maintenance

        Returns:
            List of Equipment objects with overdue maintenance
        """
        today = date.today()
        equipment_list = []

        for equipment in self._equipment_registry.values():
            if equipment.next_maintenance and equipment.next_maintenance < today:
                equipment_list.append(equipment)

        # Sort by how overdue
        equipment_list.sort(key=lambda eq: eq.next_maintenance or date.max)

        return equipment_list

    # ==================== Asset Allocation ====================

    def allocate_equipment(
        self,
        category: EquipmentCategory,
        operator: str,
        test_type: str = "",
        preferred_equipment_id: Optional[str] = None
    ) -> Optional[Equipment]:
        """
        Allocate available equipment for a test

        Args:
            category: Required equipment category
            operator: Operator requesting equipment
            test_type: Type of test
            preferred_equipment_id: Preferred equipment ID if available

        Returns:
            Allocated Equipment object or None if unavailable
        """
        # Check if preferred equipment is available
        if preferred_equipment_id:
            equipment = self.get_equipment(preferred_equipment_id)
            if equipment and equipment.status == EquipmentStatus.ACTIVE:
                return equipment

        # Find available equipment in category
        available = self.get_available_equipment(category=category)

        if not available:
            logger.warning(f"No available equipment in category {category.value}")
            return None

        # Sort by usage (prefer least used)
        available.sort(key=lambda eq: eq.test_count)

        allocated = available[0]
        logger.info(f"Allocated equipment {allocated.equipment_id} to {operator}")

        return allocated

    # ==================== Reporting ====================

    def get_equipment_utilization(
        self,
        equipment_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get equipment utilization statistics

        Args:
            equipment_id: Equipment ID
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            Dictionary with utilization statistics
        """
        equipment = self.get_equipment(equipment_id)
        if not equipment:
            raise ValueError(f"Equipment not found: {equipment_id}")

        logs = self.get_usage_logs(
            equipment_id=equipment_id,
            start_date=start_date,
            end_date=end_date
        )

        total_hours = sum(log.duration_hours for log in logs if log.duration_hours)
        test_count = len(logs)

        # Calculate availability (excluding maintenance/calibration time)
        if start_date and end_date:
            total_days = (end_date - start_date).days + 1
            total_available_hours = total_days * 24
            utilization_percent = (float(total_hours) / total_available_hours * 100) if total_available_hours > 0 else 0
        else:
            total_available_hours = None
            utilization_percent = None

        return {
            'equipment_id': equipment_id,
            'equipment_name': equipment.name,
            'total_usage_hours': float(total_hours),
            'test_count': test_count,
            'total_available_hours': total_available_hours,
            'utilization_percent': utilization_percent,
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None,
        }

    def get_fleet_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for entire equipment fleet

        Returns:
            Dictionary with fleet summary
        """
        total_equipment = len(self._equipment_registry)

        status_counts = {}
        for status in EquipmentStatus:
            count = len([eq for eq in self._equipment_registry.values() if eq.status == status])
            status_counts[status.value] = count

        category_counts = {}
        for category in EquipmentCategory:
            count = len([eq for eq in self._equipment_registry.values() if eq.category == category])
            category_counts[category.value] = count

        return {
            'total_equipment': total_equipment,
            'status_counts': status_counts,
            'category_counts': category_counts,
            'total_usage_logs': len(self._usage_logs),
        }
