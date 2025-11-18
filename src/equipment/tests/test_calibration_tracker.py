"""
Tests for Calibration Tracker
"""

import unittest
import tempfile
import shutil
from datetime import date, datetime, timedelta
from decimal import Decimal

from ..calibration_tracker import CalibrationTracker, CalibrationAlert
from ..models import (
    CalibrationRecord,
    CalibrationStatus,
    Equipment
)


class TestCalibrationTracker(unittest.TestCase):
    """Test CalibrationTracker functionality"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.tracker = CalibrationTracker(storage_path=self.test_dir)

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_add_calibration_record(self):
        """Test adding calibration record"""
        record = CalibrationRecord(
            equipment_id="eq-123",
            calibration_date=date(2024, 1, 15),
            calibration_interval_days=365,
            laboratory_name="NABL Lab",
            certificate_number="CAL-2024-001",
            passed=True
        )

        cal_id = self.tracker.add_calibration_record(record)

        self.assertIsNotNone(cal_id)
        self.assertEqual(len(self.tracker._calibration_records), 1)

        # Check due date was calculated
        retrieved = self.tracker.get_calibration_record(cal_id)
        expected_due = date(2024, 1, 15) + timedelta(days=365)
        self.assertEqual(retrieved.due_date, expected_due)

    def test_update_calibration_record(self):
        """Test updating calibration record"""
        record = CalibrationRecord(
            equipment_id="eq-456",
            calibration_date=date.today(),
            certificate_number="CAL-001"
        )

        cal_id = self.tracker.add_calibration_record(record)

        # Update record
        updated = self.tracker.update_calibration_record(cal_id, {
            'certificate_url': 'https://example.com/cert.pdf',
            'notes': 'Updated notes'
        })

        self.assertEqual(updated.certificate_url, 'https://example.com/cert.pdf')
        self.assertEqual(updated.notes, 'Updated notes')

    def test_get_latest_calibration(self):
        """Test getting latest calibration for equipment"""
        equipment_id = "eq-789"

        # Add multiple calibration records
        record1 = CalibrationRecord(
            equipment_id=equipment_id,
            calibration_date=date(2023, 1, 1),
            certificate_number="CAL-001"
        )
        record2 = CalibrationRecord(
            equipment_id=equipment_id,
            calibration_date=date(2024, 1, 1),
            certificate_number="CAL-002"
        )

        self.tracker.add_calibration_record(record1)
        self.tracker.add_calibration_record(record2)

        # Get latest
        latest = self.tracker.get_latest_calibration(equipment_id)

        self.assertIsNotNone(latest)
        self.assertEqual(latest.certificate_number, "CAL-002")

    def test_get_calibration_history(self):
        """Test getting calibration history"""
        equipment_id = "eq-abc"

        # Add calibration records
        for month in range(1, 4):
            record = CalibrationRecord(
                equipment_id=equipment_id,
                calibration_date=date(2024, month, 1),
                certificate_number=f"CAL-2024-{month:03d}"
            )
            self.tracker.add_calibration_record(record)

        # Get history
        history = self.tracker.get_calibration_history(equipment_id)

        self.assertEqual(len(history), 3)
        # Should be sorted by date descending
        self.assertEqual(history[0].calibration_date, date(2024, 3, 1))

    def test_update_calibration_status(self):
        """Test calibration status update"""
        equipment_id = "eq-status-test"

        # Add current calibration
        record = CalibrationRecord(
            equipment_id=equipment_id,
            calibration_date=date.today() - timedelta(days=30),
            due_date=date.today() + timedelta(days=335)
        )

        self.tracker.add_calibration_record(record)

        # Update status
        status = self.tracker.update_calibration_status(equipment_id)

        self.assertEqual(status, CalibrationStatus.CURRENT)

    def test_get_calibration_status_due_soon(self):
        """Test calibration status when due soon"""
        equipment_id = "eq-due-soon"

        # Add calibration due in 15 days
        record = CalibrationRecord(
            equipment_id=equipment_id,
            calibration_date=date.today() - timedelta(days=350),
            due_date=date.today() + timedelta(days=15)
        )

        self.tracker.add_calibration_record(record)

        status_info = self.tracker.get_calibration_status(equipment_id)

        self.assertEqual(status_info['status'], CalibrationStatus.DUE_SOON.value)
        self.assertTrue(status_info['is_valid'])
        self.assertEqual(status_info['days_until_due'], 15)

    def test_get_calibration_status_overdue(self):
        """Test calibration status when overdue"""
        equipment_id = "eq-overdue"

        # Add overdue calibration
        record = CalibrationRecord(
            equipment_id=equipment_id,
            calibration_date=date.today() - timedelta(days=400),
            due_date=date.today() - timedelta(days=35)
        )

        self.tracker.add_calibration_record(record)

        status_info = self.tracker.get_calibration_status(equipment_id)

        self.assertEqual(status_info['status'], CalibrationStatus.OVERDUE.value)
        self.assertFalse(status_info['is_valid'])
        self.assertEqual(status_info['days_until_due'], -35)

    def test_get_calibrations_due_soon(self):
        """Test getting calibrations due soon"""
        # Add calibrations with various due dates
        record1 = CalibrationRecord(
            equipment_id="eq-1",
            due_date=date.today() + timedelta(days=15),
            certificate_number="CAL-001"
        )
        record2 = CalibrationRecord(
            equipment_id="eq-2",
            due_date=date.today() + timedelta(days=25),
            certificate_number="CAL-002"
        )
        record3 = CalibrationRecord(
            equipment_id="eq-3",
            due_date=date.today() + timedelta(days=60),
            certificate_number="CAL-003"
        )

        self.tracker.add_calibration_record(record1)
        self.tracker.add_calibration_record(record2)
        self.tracker.add_calibration_record(record3)

        # Get due in 30 days
        due_soon = self.tracker.get_calibrations_due_soon(days_ahead=30)

        self.assertEqual(len(due_soon), 2)

    def test_get_overdue_calibrations(self):
        """Test getting overdue calibrations"""
        # Add overdue and current calibrations
        record1 = CalibrationRecord(
            equipment_id="eq-1",
            due_date=date.today() - timedelta(days=10),
            certificate_number="CAL-001"
        )
        record2 = CalibrationRecord(
            equipment_id="eq-2",
            due_date=date.today() + timedelta(days=10),
            certificate_number="CAL-002"
        )

        self.tracker.add_calibration_record(record1)
        self.tracker.add_calibration_record(record2)

        overdue = self.tracker.get_overdue_calibrations()

        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].certificate_number, "CAL-001")

    def test_generate_alerts(self):
        """Test alert generation"""
        # Create equipment dict for names
        equipment_dict = {
            "eq-1": Equipment(equipment_id="eq-1", name="IV Tracer"),
            "eq-2": Equipment(equipment_id="eq-2", name="Pyranometer")
        }

        # Add calibrations
        record1 = CalibrationRecord(
            equipment_id="eq-1",
            due_date=date.today() + timedelta(days=15),
            certificate_number="CAL-001"
        )
        record2 = CalibrationRecord(
            equipment_id="eq-2",
            due_date=date.today() - timedelta(days=5),
            certificate_number="CAL-002"
        )

        self.tracker.add_calibration_record(record1)
        self.tracker.add_calibration_record(record2)

        # Generate alerts
        alerts = self.tracker.generate_alerts(equipment_dict)

        self.assertEqual(len(alerts), 2)

        # Check alert types
        alert_types = {alert.alert_type for alert in alerts}
        self.assertIn('due_soon', alert_types)
        self.assertIn('overdue', alert_types)

    def test_alert_callback(self):
        """Test alert callback functionality"""
        alerts_received = []

        def callback(alert: CalibrationAlert):
            alerts_received.append(alert)

        tracker = CalibrationTracker(
            storage_path=self.test_dir,
            alert_callback=callback
        )

        # Add overdue calibration
        record = CalibrationRecord(
            equipment_id="eq-callback",
            due_date=date.today() - timedelta(days=10),
            certificate_number="CAL-001"
        )

        tracker.add_calibration_record(record)

        # Generate alerts
        tracker.generate_alerts()

        self.assertEqual(len(alerts_received), 1)
        self.assertEqual(alerts_received[0].equipment_id, "eq-callback")

    def test_validate_iso17025_compliance(self):
        """Test ISO 17025 compliance validation"""
        # Create complete record
        record = CalibrationRecord(
            equipment_id="eq-compliance",
            calibration_date=date.today(),
            laboratory_name="NABL Accredited Lab",
            laboratory_accreditation="NABL",
            certificate_number="CAL-2024-001",
            reference_standard="Ref Standard XYZ",
            performed_by="Tech A",
            approved_by="Manager B",
            calibration_points=[{"point": 1, "value": 10.0}]
        )

        cal_id = self.tracker.add_calibration_record(record)

        # Validate
        validation = self.tracker.validate_iso17025_compliance(cal_id)

        self.assertTrue(validation['compliant'])
        self.assertEqual(len(validation['errors']), 0)

    def test_validate_iso17025_non_compliant(self):
        """Test ISO 17025 validation with missing fields"""
        # Create incomplete record
        record = CalibrationRecord(
            equipment_id="eq-non-compliant",
            calibration_date=date.today(),
            certificate_number="CAL-001"
        )

        cal_id = self.tracker.add_calibration_record(record)

        # Validate
        validation = self.tracker.validate_iso17025_compliance(cal_id)

        self.assertFalse(validation['compliant'])
        self.assertGreater(len(validation['errors']), 0)

    def test_get_traceability_chain(self):
        """Test traceability chain retrieval"""
        record = CalibrationRecord(
            equipment_id="eq-trace",
            calibration_date=date.today(),
            certificate_number="CAL-001",
            reference_standard="Working Standard A",
            reference_certificate="WS-CERT-123",
            traceability_chain=[
                "National Standard X",
                "International Standard Y"
            ]
        )

        cal_id = self.tracker.add_calibration_record(record)

        chain = self.tracker.get_traceability_chain(cal_id)

        self.assertEqual(len(chain), 4)  # Equipment + Reference + 2 higher levels
        self.assertEqual(chain[0]['level'], 'Equipment Under Calibration')
        self.assertEqual(chain[1]['level'], 'Reference Standard')

    def test_calculate_combined_uncertainty(self):
        """Test combined uncertainty calculation"""
        uncertainty_components = {
            'repeatability': Decimal('0.02'),
            'resolution': Decimal('0.01'),
            'drift': Decimal('0.015')
        }

        result = self.tracker.calculate_combined_uncertainty(uncertainty_components)

        self.assertIn('combined_standard_uncertainty', result)
        self.assertIn('expanded_uncertainty', result)
        self.assertEqual(result['coverage_factor'], Decimal('2.0'))
        self.assertEqual(result['confidence_level'], Decimal('95.0'))

        # Verify calculation (RSS)
        expected_combined = (Decimal('0.02')**2 + Decimal('0.01')**2 + Decimal('0.015')**2).sqrt()
        self.assertAlmostEqual(
            float(result['combined_standard_uncertainty']),
            float(expected_combined),
            places=6
        )

    def test_add_uncertainty_budget(self):
        """Test adding uncertainty budget to calibration"""
        record = CalibrationRecord(
            equipment_id="eq-uncertainty",
            calibration_date=date.today(),
            certificate_number="CAL-001"
        )

        cal_id = self.tracker.add_calibration_record(record)

        # Add uncertainty budget
        uncertainty_components = {
            'repeatability': {
                'value': '0.02',
                'distribution': 'normal',
                'divisor': '1',
                'description': 'Measurement repeatability'
            },
            'resolution': {
                'value': '0.01',
                'distribution': 'rectangular',
                'divisor': '1.732',
                'description': 'Instrument resolution'
            }
        }

        updated = self.tracker.add_uncertainty_budget(cal_id, uncertainty_components)

        self.assertIsNotNone(updated.uncertainty_budget)
        self.assertIsNotNone(updated.expanded_uncertainty)
        self.assertEqual(updated.coverage_factor, Decimal('2.0'))

    def test_upload_certificate(self):
        """Test certificate upload"""
        record = CalibrationRecord(
            equipment_id="eq-cert",
            calibration_date=date.today(),
            certificate_number="CAL-001"
        )

        cal_id = self.tracker.add_calibration_record(record)

        # Upload certificate
        cert_url = "https://example.com/certificates/CAL-001.pdf"
        updated = self.tracker.upload_certificate(cal_id, cert_url)

        self.assertEqual(updated.certificate_url, cert_url)

    def test_get_certificate(self):
        """Test certificate retrieval"""
        record = CalibrationRecord(
            equipment_id="eq-get-cert",
            calibration_date=date.today(),
            certificate_number="CAL-001",
            certificate_url="https://example.com/cert.pdf"
        )

        cal_id = self.tracker.add_calibration_record(record)

        cert_url = self.tracker.get_certificate(cal_id)

        self.assertEqual(cert_url, "https://example.com/cert.pdf")

    def test_get_calibration_summary(self):
        """Test calibration summary statistics"""
        # Add various calibrations
        for i in range(3):
            record = CalibrationRecord(
                equipment_id=f"eq-{i}",
                calibration_date=date.today() - timedelta(days=i*30),
                due_date=date.today() + timedelta(days=365-i*30),
                certificate_number=f"CAL-{i}"
            )
            self.tracker.add_calibration_record(record)

        summary = self.tracker.get_calibration_summary()

        self.assertEqual(summary['total_records'], 3)
        self.assertEqual(summary['total_equipment'], 3)

    def test_export_calibration_schedule(self):
        """Test calibration schedule export"""
        # Add calibrations with different due dates
        record1 = CalibrationRecord(
            equipment_id="eq-1",
            calibration_date=date(2024, 1, 1),
            due_date=date(2025, 1, 1),
            certificate_number="CAL-001",
            laboratory_name="Lab A"
        )
        record2 = CalibrationRecord(
            equipment_id="eq-2",
            calibration_date=date(2024, 2, 1),
            due_date=date(2025, 2, 1),
            certificate_number="CAL-002",
            laboratory_name="Lab B"
        )

        self.tracker.add_calibration_record(record1)
        self.tracker.add_calibration_record(record2)

        # Export schedule
        schedule = self.tracker.export_calibration_schedule()

        self.assertEqual(len(schedule), 2)
        # Should be sorted by due date
        self.assertEqual(schedule[0]['due_date'], "2025-01-01")

    def test_persistence(self):
        """Test data persistence"""
        record = CalibrationRecord(
            equipment_id="eq-persist",
            calibration_date=date.today(),
            certificate_number="CAL-PERSIST"
        )

        cal_id = self.tracker.add_calibration_record(record)

        # Create new tracker with same storage
        tracker2 = CalibrationTracker(storage_path=self.test_dir)

        # Verify data was loaded
        retrieved = tracker2.get_calibration_record(cal_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.certificate_number, "CAL-PERSIST")


if __name__ == '__main__':
    unittest.main()
