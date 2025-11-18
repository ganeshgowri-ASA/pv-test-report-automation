"""
Comprehensive tests for calibration certificate management system.

Tests cover:
- Certificate model validation
- Database operations
- Alert generation
- Certificate parsing
- Traceability validation
- ISO 17025 compliance
"""

import unittest
import tempfile
import os
from datetime import date, datetime, timedelta
from pathlib import Path

from equipment.calibration import (
    CalibrationCertificate,
    CalibrationManager,
    AccreditationBody,
    AlertSeverity,
)
from equipment.calibration.models import (
    CertificateStatus,
    UncertaintyBudget,
    UncertaintyType,
    TraceabilityChain,
    CalibrationPoint,
)
from equipment.calibration.database import CalibrationDatabase
from equipment.calibration.alerts import AlertManager, AlertType
from equipment.calibration.parser import CertificateParser


class TestCalibrationCertificate(unittest.TestCase):
    """Test CalibrationCertificate model."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_cert_data = {
            "cert_id": None,
            "equipment_id": 123,
            "cert_number": "CAL-2025-001",
            "calibration_date": date(2025, 1, 1),
            "due_date": date(2026, 1, 1),
            "calibration_lab": "Test Lab",
            "accreditation_body": AccreditationBody.NABL,
            "uncertainty": 0.05,
            "traceability_chain": "NIST",
        }

    def test_create_valid_certificate(self):
        """Test creating a valid certificate."""
        cert = CalibrationCertificate(**self.valid_cert_data)
        self.assertEqual(cert.cert_number, "CAL-2025-001")
        self.assertEqual(cert.equipment_id, 123)
        self.assertTrue(cert.is_valid())

    def test_certificate_validation_future_date(self):
        """Test that future calibration dates raise error."""
        data = self.valid_cert_data.copy()
        data["calibration_date"] = date.today() + timedelta(days=10)

        with self.assertRaises(ValueError):
            CalibrationCertificate(**data)

    def test_certificate_validation_due_before_calibration(self):
        """Test that due date before calibration date raises error."""
        data = self.valid_cert_data.copy()
        data["due_date"] = data["calibration_date"] - timedelta(days=1)

        with self.assertRaises(ValueError):
            CalibrationCertificate(**data)

    def test_certificate_validation_negative_uncertainty(self):
        """Test that negative uncertainty raises error."""
        data = self.valid_cert_data.copy()
        data["uncertainty"] = -0.5

        with self.assertRaises(ValueError):
            CalibrationCertificate(**data)

    def test_certificate_status_valid(self):
        """Test valid certificate status."""
        data = self.valid_cert_data.copy()
        data["calibration_date"] = date.today() - timedelta(days=30)
        data["due_date"] = date.today() + timedelta(days=60)

        cert = CalibrationCertificate(**data)
        cert.update_status()
        self.assertEqual(cert.status, CertificateStatus.VALID)

    def test_certificate_status_due_soon(self):
        """Test due soon certificate status."""
        data = self.valid_cert_data.copy()
        data["calibration_date"] = date.today() - timedelta(days=300)
        data["due_date"] = date.today() + timedelta(days=20)

        cert = CalibrationCertificate(**data)
        cert.update_status()
        self.assertEqual(cert.status, CertificateStatus.DUE_SOON)

    def test_certificate_status_expired(self):
        """Test expired certificate status."""
        data = self.valid_cert_data.copy()
        data["calibration_date"] = date.today() - timedelta(days=400)
        data["due_date"] = date.today() - timedelta(days=10)

        cert = CalibrationCertificate(**data)
        cert.update_status()
        self.assertEqual(cert.status, CertificateStatus.EXPIRED)
        self.assertTrue(cert.is_expired())

    def test_days_until_due(self):
        """Test days until due calculation."""
        data = self.valid_cert_data.copy()
        data["due_date"] = date.today() + timedelta(days=15)

        cert = CalibrationCertificate(**data)
        self.assertEqual(cert.days_until_due(), 15)

    def test_certificate_to_dict(self):
        """Test certificate serialization to dict."""
        cert = CalibrationCertificate(**self.valid_cert_data)
        cert_dict = cert.to_dict()

        self.assertEqual(cert_dict["cert_number"], "CAL-2025-001")
        self.assertEqual(cert_dict["equipment_id"], 123)
        self.assertEqual(cert_dict["accreditation_body"], "NABL")

    def test_certificate_from_dict(self):
        """Test certificate deserialization from dict."""
        cert = CalibrationCertificate(**self.valid_cert_data)
        cert_dict = cert.to_dict()

        restored_cert = CalibrationCertificate.from_dict(cert_dict)
        self.assertEqual(restored_cert.cert_number, cert.cert_number)
        self.assertEqual(restored_cert.equipment_id, cert.equipment_id)


class TestUncertaintyBudget(unittest.TestCase):
    """Test UncertaintyBudget model."""

    def test_create_uncertainty_budget(self):
        """Test creating uncertainty budget."""
        budget = UncertaintyBudget(
            value=0.05,
            unit="V",
            uncertainty_type=UncertaintyType.EXPANDED,
            coverage_factor=2.0,
            confidence_level=0.95,
            components={"type_a": 0.03, "type_b": 0.04}
        )

        self.assertEqual(budget.value, 0.05)
        self.assertEqual(budget.unit, "V")
        self.assertEqual(len(budget.components), 2)

    def test_uncertainty_validation(self):
        """Test uncertainty budget validation."""
        with self.assertRaises(ValueError):
            UncertaintyBudget(
                value=-0.05,  # Negative value
                unit="V",
                uncertainty_type=UncertaintyType.EXPANDED
            )


class TestTraceabilityChain(unittest.TestCase):
    """Test TraceabilityChain model."""

    def test_create_traceability_chain(self):
        """Test creating traceability chain."""
        chain = TraceabilityChain(
            primary_standard="NIST",
            intermediate_standards=["Lab A", "Lab B"],
            reference_certificate="REF-123",
            uncertainty_propagation=[0.01, 0.02, 0.03]
        )

        self.assertEqual(chain.primary_standard, "NIST")
        self.assertEqual(len(chain.intermediate_standards), 2)

    def test_traceability_validation(self):
        """Test traceability chain validation."""
        chain = TraceabilityChain(
            primary_standard="NIST",
            intermediate_standards=["Lab A"],
            uncertainty_propagation=[0.01, 0.02]  # Should match chain length
        )

        self.assertTrue(chain.validate())


class TestCalibrationDatabase(unittest.TestCase):
    """Test CalibrationDatabase operations."""

    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db = CalibrationDatabase(self.temp_db.name)

        self.test_cert = CalibrationCertificate(
            cert_id=None,
            equipment_id=123,
            cert_number="TEST-001",
            calibration_date=date.today() - timedelta(days=30),
            due_date=date.today() + timedelta(days=335),
            calibration_lab="Test Lab",
            accreditation_body=AccreditationBody.NABL,
            uncertainty=0.05,
            traceability_chain="NIST",
        )

    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.temp_db.name)

    def test_add_certificate(self):
        """Test adding certificate to database."""
        cert_id = self.db.add_certificate(self.test_cert)
        self.assertIsNotNone(cert_id)
        self.assertGreater(cert_id, 0)

    def test_get_certificate(self):
        """Test retrieving certificate from database."""
        cert_id = self.db.add_certificate(self.test_cert)
        retrieved = self.db.get_certificate(cert_id)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.cert_number, "TEST-001")
        self.assertEqual(retrieved.equipment_id, 123)

    def test_update_certificate(self):
        """Test updating certificate."""
        cert_id = self.db.add_certificate(self.test_cert)
        self.test_cert.cert_id = cert_id
        self.test_cert.notes = "Updated notes"

        success = self.db.update_certificate(self.test_cert)
        self.assertTrue(success)

        retrieved = self.db.get_certificate(cert_id)
        self.assertEqual(retrieved.notes, "Updated notes")

    def test_get_certificates_by_equipment(self):
        """Test retrieving certificates by equipment ID."""
        self.db.add_certificate(self.test_cert)

        certs = self.db.get_certificates_by_equipment(123)
        self.assertEqual(len(certs), 1)
        self.assertEqual(certs[0].cert_number, "TEST-001")

    def test_get_due_soon(self):
        """Test getting certificates due soon."""
        # Create certificate due in 20 days
        cert = CalibrationCertificate(
            cert_id=None,
            equipment_id=124,
            cert_number="TEST-002",
            calibration_date=date.today() - timedelta(days=345),
            due_date=date.today() + timedelta(days=20),
            calibration_lab="Test Lab",
            accreditation_body=AccreditationBody.NABL,
            uncertainty=0.05,
            traceability_chain="NIST",
        )

        self.db.add_certificate(cert)
        due_soon = self.db.get_certificates_due_soon(30)

        self.assertEqual(len(due_soon), 1)

    def test_get_expired_certificates(self):
        """Test getting expired certificates."""
        expired_cert = CalibrationCertificate(
            cert_id=None,
            equipment_id=125,
            cert_number="TEST-EXPIRED",
            calibration_date=date.today() - timedelta(days=400),
            due_date=date.today() - timedelta(days=10),
            calibration_lab="Test Lab",
            accreditation_body=AccreditationBody.NABL,
            uncertainty=0.05,
            traceability_chain="NIST",
        )

        self.db.add_certificate(expired_cert)
        expired = self.db.get_expired_certificates()

        self.assertEqual(len(expired), 1)
        self.assertEqual(expired[0].cert_number, "TEST-EXPIRED")

    def test_delete_certificate(self):
        """Test deleting certificate."""
        cert_id = self.db.add_certificate(self.test_cert)
        success = self.db.delete_certificate(cert_id)

        self.assertTrue(success)
        retrieved = self.db.get_certificate(cert_id)
        self.assertIsNone(retrieved)


class TestAlertManager(unittest.TestCase):
    """Test AlertManager functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.alert_manager = AlertManager()

    def test_generate_alerts_expired(self):
        """Test generating alerts for expired certificates."""
        expired_cert = CalibrationCertificate(
            cert_id=1,
            equipment_id=123,
            cert_number="EXPIRED-001",
            calibration_date=date.today() - timedelta(days=400),
            due_date=date.today() - timedelta(days=10),
            calibration_lab="Test Lab",
            accreditation_body=AccreditationBody.NABL,
            uncertainty=0.05,
            traceability_chain="NIST",
        )

        alerts = self.alert_manager.generate_alerts([expired_cert])
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].severity, AlertSeverity.CRITICAL)
        self.assertEqual(alerts[0].alert_type, AlertType.OVERDUE)

    def test_generate_alerts_due_soon(self):
        """Test generating alerts for certificates due soon."""
        due_soon_cert = CalibrationCertificate(
            cert_id=2,
            equipment_id=124,
            cert_number="DUE-SOON-001",
            calibration_date=date.today() - timedelta(days=335),
            due_date=date.today() + timedelta(days=15),
            calibration_lab="Test Lab",
            accreditation_body=AccreditationBody.NABL,
            uncertainty=0.05,
            traceability_chain="NIST",
        )

        alerts = self.alert_manager.generate_alerts([due_soon_cert])
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].severity, AlertSeverity.WARNING)

    def test_acknowledge_alert(self):
        """Test acknowledging an alert."""
        cert = CalibrationCertificate(
            cert_id=1,
            equipment_id=123,
            cert_number="TEST-001",
            calibration_date=date.today() - timedelta(days=335),
            due_date=date.today() + timedelta(days=5),
            calibration_lab="Test Lab",
            accreditation_body=AccreditationBody.NABL,
            uncertainty=0.05,
            traceability_chain="NIST",
        )

        alerts = self.alert_manager.generate_alerts([cert])
        alert_id = alerts[0].alert_id

        success = self.alert_manager.acknowledge_alert(alert_id, "test_user")
        self.assertTrue(success)
        self.assertTrue(alerts[0].acknowledged)
        self.assertEqual(alerts[0].acknowledged_by, "test_user")

    def test_get_alert_summary(self):
        """Test getting alert summary."""
        certs = [
            CalibrationCertificate(
                cert_id=i,
                equipment_id=100 + i,
                cert_number=f"CERT-{i:03d}",
                calibration_date=date.today() - timedelta(days=335),
                due_date=date.today() + timedelta(days=days_until),
                calibration_lab="Test Lab",
                accreditation_body=AccreditationBody.NABL,
                uncertainty=0.05,
                traceability_chain="NIST",
            )
            for i, days_until in enumerate([5, 10, 25, -5])  # Mix of due dates
        ]

        self.alert_manager.generate_alerts(certs)
        summary = self.alert_manager.get_alert_summary()

        self.assertEqual(summary['total'], 4)
        self.assertGreater(summary['critical'], 0)


class TestCalibrationManager(unittest.TestCase):
    """Test CalibrationManager integration."""

    def setUp(self):
        """Set up test manager with temporary database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.manager = CalibrationManager(self.temp_db.name)

    def tearDown(self):
        """Clean up."""
        os.unlink(self.temp_db.name)

    def test_add_certificate_manual(self):
        """Test adding certificate manually."""
        cert = self.manager.add_certificate(
            equipment_id=123,
            cert_number="MAN-001",
            calibration_date=date.today() - timedelta(days=30),
            due_date=date.today() + timedelta(days=335),
            calibration_lab="Manual Lab",
            accreditation_body=AccreditationBody.NABL,
            uncertainty=0.05,
            traceability_chain="NIST"
        )

        self.assertIsNotNone(cert)
        self.assertIsNotNone(cert.cert_id)

    def test_get_due_soon(self):
        """Test getting certificates due soon."""
        self.manager.add_certificate(
            equipment_id=123,
            cert_number="DUE-001",
            calibration_date=date.today() - timedelta(days=335),
            due_date=date.today() + timedelta(days=20),
            calibration_lab="Test Lab",
            accreditation_body=AccreditationBody.NABL,
            uncertainty=0.05,
            traceability_chain="NIST"
        )

        due_soon = self.manager.get_due_soon(30)
        self.assertEqual(len(due_soon), 1)

    def test_flag_expired_certificates(self):
        """Test auto-flagging expired certificates."""
        self.manager.add_certificate(
            equipment_id=123,
            cert_number="EXP-001",
            calibration_date=date.today() - timedelta(days=400),
            due_date=date.today() - timedelta(days=10),
            calibration_lab="Test Lab",
            accreditation_body=AccreditationBody.NABL,
            uncertainty=0.05,
            traceability_chain="NIST"
        )

        expired = self.manager.flag_expired_certificates()
        self.assertEqual(len(expired), 1)
        self.assertTrue(expired[0].is_expired())

    def test_generate_compliance_report(self):
        """Test generating compliance report."""
        self.manager.add_certificate(
            equipment_id=123,
            cert_number="COMP-001",
            calibration_date=date.today() - timedelta(days=30),
            due_date=date.today() + timedelta(days=335),
            calibration_lab="Test Lab",
            accreditation_body=AccreditationBody.NABL,
            uncertainty=0.05,
            traceability_chain="NIST"
        )

        report = self.manager.generate_compliance_report()
        self.assertIn("CALIBRATION COMPLIANCE REPORT", report)
        self.assertIn("ISO 17025", report)
        self.assertIn("NABL", report)

    def test_get_statistics(self):
        """Test getting calibration statistics."""
        # Add some certificates
        for i in range(3):
            self.manager.add_certificate(
                equipment_id=100 + i,
                cert_number=f"STAT-{i:03d}",
                calibration_date=date.today() - timedelta(days=30),
                due_date=date.today() + timedelta(days=335),
                calibration_lab="Test Lab",
                accreditation_body=AccreditationBody.NABL,
                uncertainty=0.05,
                traceability_chain="NIST"
            )

        stats = self.manager.get_statistics()
        self.assertEqual(stats['total_certificates'], 3)
        self.assertEqual(stats['valid'], 3)
        self.assertEqual(stats['expired'], 0)


class TestCertificateParser(unittest.TestCase):
    """Test CertificateParser functionality."""

    def setUp(self):
        """Set up parser."""
        self.parser = CertificateParser()

    def test_parse_date_string(self):
        """Test date string parsing."""
        date_str = "15-01-2025"
        parsed = self.parser._parse_date_string(date_str)
        self.assertEqual(parsed, date(2025, 1, 15))

    def test_extract_cert_number(self):
        """Test extracting certificate number."""
        text = "Certificate No: CAL-2025-001\nOther text..."
        cert_num = self.parser._extract_cert_number(text)
        self.assertEqual(cert_num, "CAL-2025-001")

    def test_extract_accreditation_body(self):
        """Test extracting accreditation body."""
        text = "This lab is accredited by NABL"
        body = self.parser._extract_accreditation_body(text)
        self.assertEqual(body, "NABL")


if __name__ == '__main__':
    unittest.main()
