"""
Calibration Tracker (Session 32)

Calibration schedule management, certificate storage, due date tracking,
calibration history, traceability to standards, ISO 17025 compliance,
and uncertainty budgets.
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Callable
from decimal import Decimal
import json
import logging
from pathlib import Path
from dataclasses import dataclass

from .models import (
    CalibrationRecord,
    CalibrationStatus,
    Equipment,
    EquipmentStatus
)


logger = logging.getLogger(__name__)


@dataclass
class CalibrationAlert:
    """Alert for calibration due dates"""
    equipment_id: str
    equipment_name: str
    calibration_id: str
    due_date: date
    days_until_due: int
    alert_type: str  # 'due_soon', 'overdue'
    message: str


class CalibrationTracker:
    """
    Calibration tracking and management system

    Handles calibration schedule management, certificate storage,
    due date tracking, calibration history, traceability to standards,
    ISO 17025 compliance, and uncertainty budgets.
    """

    def __init__(
        self,
        storage_path: Optional[str] = None,
        alert_days_before: int = 30,
        alert_callback: Optional[Callable[[CalibrationAlert], None]] = None
    ):
        """
        Initialize calibration tracker

        Args:
            storage_path: Path to store calibration data
            alert_days_before: Days before due date to trigger alert
            alert_callback: Optional callback function for alerts
        """
        self.storage_path = Path(storage_path) if storage_path else Path("./data/calibration")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.calibration_file = self.storage_path / "calibrations.json"
        self.alert_days_before = alert_days_before
        self.alert_callback = alert_callback

        self._calibration_records: Dict[str, CalibrationRecord] = {}
        self._load_data()

    def _load_data(self) -> None:
        """Load calibration data from storage"""
        try:
            if self.calibration_file.exists():
                with open(self.calibration_file, 'r') as f:
                    data = json.load(f)
                    self._calibration_records = {
                        item['calibration_id']: CalibrationRecord.from_dict(item)
                        for item in data
                    }
                logger.info(f"Loaded {len(self._calibration_records)} calibration records")
        except Exception as e:
            logger.error(f"Error loading calibration data: {e}")

    def _save_data(self) -> None:
        """Save calibration data to storage"""
        try:
            with open(self.calibration_file, 'w') as f:
                data = [cal.to_dict() for cal in self._calibration_records.values()]
                json.dump(data, f, indent=2)
            logger.info("Calibration data saved successfully")
        except Exception as e:
            logger.error(f"Error saving calibration data: {e}")
            raise

    # ==================== Calibration Record Management ====================

    def add_calibration_record(self, record: CalibrationRecord) -> str:
        """
        Add new calibration record

        Args:
            record: CalibrationRecord object

        Returns:
            calibration_id of added record
        """
        # Calculate due date if not set
        if not record.due_date or record.due_date == date.today():
            record.due_date = record.calibration_date + timedelta(
                days=record.calibration_interval_days
            )

        # Update calibration status based on results
        if record.passed:
            record.calibration_status = CalibrationStatus.CURRENT
        else:
            record.calibration_status = CalibrationStatus.FAILED

        record.updated_at = datetime.now()
        self._calibration_records[record.calibration_id] = record
        self._save_data()

        logger.info(f"Added calibration record for equipment {record.equipment_id}")
        return record.calibration_id

    def update_calibration_record(
        self,
        calibration_id: str,
        updates: Dict[str, Any]
    ) -> CalibrationRecord:
        """
        Update calibration record

        Args:
            calibration_id: Calibration record ID
            updates: Dictionary of fields to update

        Returns:
            Updated CalibrationRecord object

        Raises:
            ValueError: If record not found
        """
        if calibration_id not in self._calibration_records:
            raise ValueError(f"Calibration record not found: {calibration_id}")

        record = self._calibration_records[calibration_id]

        for key, value in updates.items():
            if hasattr(record, key):
                setattr(record, key, value)

        record.updated_at = datetime.now()
        self._save_data()

        logger.info(f"Updated calibration record: {calibration_id}")
        return record

    def get_calibration_record(self, calibration_id: str) -> Optional[CalibrationRecord]:
        """
        Get calibration record by ID

        Args:
            calibration_id: Calibration record ID

        Returns:
            CalibrationRecord object or None
        """
        return self._calibration_records.get(calibration_id)

    def get_latest_calibration(self, equipment_id: str) -> Optional[CalibrationRecord]:
        """
        Get latest calibration record for equipment

        Args:
            equipment_id: Equipment ID

        Returns:
            Latest CalibrationRecord or None
        """
        records = self.get_calibration_history(equipment_id)
        if records:
            return records[0]  # Already sorted by date descending
        return None

    def get_calibration_history(
        self,
        equipment_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[CalibrationRecord]:
        """
        Get calibration history for equipment

        Args:
            equipment_id: Equipment ID
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of CalibrationRecord objects sorted by date descending
        """
        records = [
            rec for rec in self._calibration_records.values()
            if rec.equipment_id == equipment_id
        ]

        if start_date:
            records = [rec for rec in records if rec.calibration_date >= start_date]

        if end_date:
            records = [rec for rec in records if rec.calibration_date <= end_date]

        # Sort by calibration date, most recent first
        records.sort(key=lambda r: r.calibration_date, reverse=True)

        return records

    # ==================== Calibration Status Management ====================

    def update_calibration_status(self, equipment_id: str) -> CalibrationStatus:
        """
        Update and return current calibration status for equipment

        Args:
            equipment_id: Equipment ID

        Returns:
            Current CalibrationStatus
        """
        latest = self.get_latest_calibration(equipment_id)

        if not latest:
            return CalibrationStatus.OVERDUE

        today = date.today()
        days_until_due = (latest.due_date - today).days

        if days_until_due < 0:
            status = CalibrationStatus.OVERDUE
        elif days_until_due <= self.alert_days_before:
            status = CalibrationStatus.DUE_SOON
        else:
            status = CalibrationStatus.CURRENT

        # Update record if status changed
        if latest.calibration_status != status:
            self.update_calibration_record(latest.calibration_id, {
                'calibration_status': status
            })

        return status

    def get_calibration_status(self, equipment_id: str) -> Dict[str, Any]:
        """
        Get detailed calibration status for equipment

        Args:
            equipment_id: Equipment ID

        Returns:
            Dictionary with calibration status details
        """
        latest = self.get_latest_calibration(equipment_id)

        if not latest:
            return {
                'equipment_id': equipment_id,
                'status': CalibrationStatus.OVERDUE.value,
                'message': 'No calibration record found',
                'is_valid': False
            }

        today = date.today()
        days_until_due = (latest.due_date - today).days

        status = self.update_calibration_status(equipment_id)

        return {
            'equipment_id': equipment_id,
            'calibration_id': latest.calibration_id,
            'status': status.value,
            'calibration_date': latest.calibration_date.isoformat(),
            'due_date': latest.due_date.isoformat(),
            'days_until_due': days_until_due,
            'is_valid': days_until_due >= 0,
            'certificate_number': latest.certificate_number,
            'laboratory_name': latest.laboratory_name,
        }

    # ==================== Due Date Tracking and Alerts ====================

    def get_calibrations_due_soon(
        self,
        days_ahead: Optional[int] = None
    ) -> List[CalibrationRecord]:
        """
        Get calibrations due within specified days

        Args:
            days_ahead: Days to look ahead (default: alert_days_before)

        Returns:
            List of CalibrationRecord objects due soon
        """
        if days_ahead is None:
            days_ahead = self.alert_days_before

        cutoff_date = date.today() + timedelta(days=days_ahead)
        today = date.today()

        due_soon = []
        for record in self._calibration_records.values():
            if today <= record.due_date <= cutoff_date:
                due_soon.append(record)

        # Sort by due date
        due_soon.sort(key=lambda r: r.due_date)

        return due_soon

    def get_overdue_calibrations(self) -> List[CalibrationRecord]:
        """
        Get overdue calibrations

        Returns:
            List of overdue CalibrationRecord objects
        """
        today = date.today()

        overdue = [
            record for record in self._calibration_records.values()
            if record.due_date < today
        ]

        # Sort by how overdue (most overdue first)
        overdue.sort(key=lambda r: r.due_date)

        return overdue

    def generate_alerts(self, equipment_dict: Optional[Dict[str, Equipment]] = None) -> List[CalibrationAlert]:
        """
        Generate calibration alerts

        Args:
            equipment_dict: Optional dictionary of equipment for names

        Returns:
            List of CalibrationAlert objects
        """
        alerts = []
        today = date.today()

        # Check all latest calibrations
        equipment_ids = set(rec.equipment_id for rec in self._calibration_records.values())

        for equipment_id in equipment_ids:
            latest = self.get_latest_calibration(equipment_id)
            if not latest:
                continue

            days_until_due = (latest.due_date - today).days

            # Get equipment name
            equipment_name = equipment_id
            if equipment_dict and equipment_id in equipment_dict:
                equipment_name = equipment_dict[equipment_id].name

            alert = None

            if days_until_due < 0:
                alert = CalibrationAlert(
                    equipment_id=equipment_id,
                    equipment_name=equipment_name,
                    calibration_id=latest.calibration_id,
                    due_date=latest.due_date,
                    days_until_due=days_until_due,
                    alert_type='overdue',
                    message=f"Calibration overdue by {abs(days_until_due)} days"
                )
            elif days_until_due <= self.alert_days_before:
                alert = CalibrationAlert(
                    equipment_id=equipment_id,
                    equipment_name=equipment_name,
                    calibration_id=latest.calibration_id,
                    due_date=latest.due_date,
                    days_until_due=days_until_due,
                    alert_type='due_soon',
                    message=f"Calibration due in {days_until_due} days"
                )

            if alert:
                alerts.append(alert)

                # Call alert callback if provided
                if self.alert_callback:
                    try:
                        self.alert_callback(alert)
                    except Exception as e:
                        logger.error(f"Error in alert callback: {e}")

        return alerts

    def send_reminders(self, calibration_id: str) -> bool:
        """
        Mark reminder as sent for calibration

        Args:
            calibration_id: Calibration record ID

        Returns:
            True if successful
        """
        try:
            self.update_calibration_record(calibration_id, {
                'next_calibration_reminder_sent': True
            })
            return True
        except Exception as e:
            logger.error(f"Error sending reminder: {e}")
            return False

    # ==================== ISO 17025 Compliance ====================

    def validate_iso17025_compliance(self, calibration_id: str) -> Dict[str, Any]:
        """
        Validate ISO 17025 compliance for calibration record

        Args:
            calibration_id: Calibration record ID

        Returns:
            Dictionary with compliance status and missing requirements
        """
        record = self.get_calibration_record(calibration_id)
        if not record:
            return {
                'compliant': False,
                'errors': ['Calibration record not found']
            }

        errors = []
        warnings = []

        # Required fields for ISO 17025
        required_fields = {
            'laboratory_name': 'Calibration laboratory name',
            'laboratory_accreditation': 'Laboratory accreditation',
            'certificate_number': 'Calibration certificate number',
            'reference_standard': 'Reference standard used',
            'performed_by': 'Technician name',
            'approved_by': 'Approver name',
        }

        for field, description in required_fields.items():
            if not getattr(record, field):
                errors.append(f"Missing {description}")

        # Check traceability
        if not record.traceability_chain:
            warnings.append("No traceability chain documented")

        # Check uncertainty budget
        if not record.uncertainty_budget:
            warnings.append("No uncertainty budget provided")

        # Check environmental conditions
        if not record.temperature and not record.humidity:
            warnings.append("Environmental conditions not recorded")

        # Check calibration points
        if not record.calibration_points:
            errors.append("No calibration points recorded")

        # Check certificate
        if not record.certificate_url:
            warnings.append("Calibration certificate not uploaded")

        is_compliant = len(errors) == 0

        return {
            'compliant': is_compliant,
            'calibration_id': calibration_id,
            'errors': errors,
            'warnings': warnings,
            'certificate_number': record.certificate_number,
            'laboratory': record.laboratory_name,
            'accreditation': record.laboratory_accreditation,
        }

    def get_traceability_chain(self, calibration_id: str) -> List[Dict[str, str]]:
        """
        Get traceability chain for calibration

        Args:
            calibration_id: Calibration record ID

        Returns:
            List of traceability links
        """
        record = self.get_calibration_record(calibration_id)
        if not record:
            return []

        chain = [{
            'level': 'Equipment Under Calibration',
            'reference': calibration_id,
            'certificate': record.certificate_number
        }]

        if record.reference_standard:
            chain.append({
                'level': 'Reference Standard',
                'reference': record.reference_standard,
                'certificate': record.reference_certificate
            })

        for idx, ref in enumerate(record.traceability_chain):
            chain.append({
                'level': f'Higher Level Standard {idx + 1}',
                'reference': ref,
                'certificate': ''
            })

        return chain

    # ==================== Uncertainty Budget Management ====================

    def calculate_combined_uncertainty(
        self,
        uncertainty_components: Dict[str, Decimal]
    ) -> Dict[str, Decimal]:
        """
        Calculate combined uncertainty from components

        Args:
            uncertainty_components: Dictionary of uncertainty components

        Returns:
            Dictionary with combined uncertainty values
        """
        # Calculate RSS (Root Sum Square) of components
        sum_of_squares = sum(u ** 2 for u in uncertainty_components.values())
        combined_uncertainty = sum_of_squares.sqrt() if sum_of_squares > 0 else Decimal('0')

        # Default coverage factor k=2 for 95% confidence
        coverage_factor = Decimal('2.0')
        expanded_uncertainty = combined_uncertainty * coverage_factor

        return {
            'combined_standard_uncertainty': combined_uncertainty,
            'coverage_factor': coverage_factor,
            'expanded_uncertainty': expanded_uncertainty,
            'confidence_level': Decimal('95.0'),
        }

    def add_uncertainty_budget(
        self,
        calibration_id: str,
        uncertainty_components: Dict[str, Any]
    ) -> CalibrationRecord:
        """
        Add uncertainty budget to calibration record

        Args:
            calibration_id: Calibration record ID
            uncertainty_components: Dictionary of uncertainty components
                Format: {
                    'component_name': {
                        'value': Decimal,
                        'distribution': 'normal|rectangular|triangular',
                        'divisor': Decimal (for rectangular/triangular),
                        'description': str
                    }
                }

        Returns:
            Updated CalibrationRecord
        """
        # Convert string values to Decimal
        processed_components = {}
        for name, component in uncertainty_components.items():
            if isinstance(component.get('value'), str):
                component['value'] = Decimal(component['value'])
            if isinstance(component.get('divisor'), str):
                component['divisor'] = Decimal(component['divisor'])
            processed_components[name] = component

        # Calculate combined uncertainty
        component_uncertainties = {
            name: comp['value'] / comp.get('divisor', Decimal('1'))
            for name, comp in processed_components.items()
        }

        uncertainty_result = self.calculate_combined_uncertainty(component_uncertainties)

        # Build complete uncertainty budget (convert all Decimals to strings for JSON)
        components_for_storage = {}
        for name, comp in processed_components.items():
            comp_copy = comp.copy()
            if isinstance(comp_copy.get('value'), Decimal):
                comp_copy['value'] = str(comp_copy['value'])
            if isinstance(comp_copy.get('divisor'), Decimal):
                comp_copy['divisor'] = str(comp_copy['divisor'])
            components_for_storage[name] = comp_copy

        uncertainty_budget = {
            'components': components_for_storage,
            'combined_standard_uncertainty': str(uncertainty_result['combined_standard_uncertainty']),
            'coverage_factor': str(uncertainty_result['coverage_factor']),
            'expanded_uncertainty': str(uncertainty_result['expanded_uncertainty']),
            'confidence_level': str(uncertainty_result['confidence_level']),
        }

        # Update calibration record
        return self.update_calibration_record(calibration_id, {
            'uncertainty_budget': uncertainty_budget,
            'expanded_uncertainty': uncertainty_result['expanded_uncertainty'],
            'coverage_factor': uncertainty_result['coverage_factor'],
            'confidence_level': uncertainty_result['confidence_level'],
        })

    # ==================== Certificate Management ====================

    def upload_certificate(
        self,
        calibration_id: str,
        certificate_url: str
    ) -> CalibrationRecord:
        """
        Upload calibration certificate

        Args:
            calibration_id: Calibration record ID
            certificate_url: URL or path to certificate

        Returns:
            Updated CalibrationRecord
        """
        return self.update_calibration_record(calibration_id, {
            'certificate_url': certificate_url
        })

    def get_certificate(self, calibration_id: str) -> Optional[str]:
        """
        Get calibration certificate URL

        Args:
            calibration_id: Calibration record ID

        Returns:
            Certificate URL or None
        """
        record = self.get_calibration_record(calibration_id)
        return record.certificate_url if record else None

    # ==================== Reporting ====================

    def get_calibration_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for all calibrations

        Returns:
            Dictionary with calibration summary
        """
        total_records = len(self._calibration_records)

        # Get unique equipment count
        equipment_ids = set(rec.equipment_id for rec in self._calibration_records.values())
        total_equipment = len(equipment_ids)

        # Count by status
        status_counts = {}
        for equipment_id in equipment_ids:
            status = self.update_calibration_status(equipment_id)
            status_counts[status.value] = status_counts.get(status.value, 0) + 1

        # Count overdue
        overdue = len(self.get_overdue_calibrations())
        due_soon = len(self.get_calibrations_due_soon())

        return {
            'total_records': total_records,
            'total_equipment': total_equipment,
            'status_counts': status_counts,
            'overdue_count': overdue,
            'due_soon_count': due_soon,
        }

    def export_calibration_schedule(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Export calibration schedule

        Args:
            start_date: Start date for schedule
            end_date: End date for schedule

        Returns:
            List of calibration schedule items
        """
        schedule = []

        equipment_ids = set(rec.equipment_id for rec in self._calibration_records.values())

        for equipment_id in equipment_ids:
            latest = self.get_latest_calibration(equipment_id)
            if not latest:
                continue

            # Filter by date range
            if start_date and latest.due_date < start_date:
                continue
            if end_date and latest.due_date > end_date:
                continue

            status = self.update_calibration_status(equipment_id)

            schedule.append({
                'equipment_id': equipment_id,
                'calibration_id': latest.calibration_id,
                'last_calibration': latest.calibration_date.isoformat(),
                'due_date': latest.due_date.isoformat(),
                'status': status.value,
                'certificate_number': latest.certificate_number,
                'laboratory': latest.laboratory_name,
            })

        # Sort by due date
        schedule.sort(key=lambda x: x['due_date'])

        return schedule
