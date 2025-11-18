"""Calibration Manager - Main interface for calibration certificate management."""

from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any

from .models import (
    CalibrationCertificate,
    AccreditationBody,
    CertificateStatus,
    TraceabilityChain,
    UncertaintyBudget,
)
from .database import CalibrationDatabase
from .parser import CertificateParser
from .alerts import AlertManager, CalibrationAlert, AlertSeverity


class CalibrationManager:
    """
    Main interface for calibration certificate management per ISO 17025.

    Provides high-level methods for:
    - Adding and managing certificates
    - Parsing certificates from PDF files
    - Tracking due dates and generating alerts
    - Maintaining traceability chains
    - Managing uncertainty budgets
    - Generating compliance reports

    Example:
        >>> cm = CalibrationManager()
        >>> cm.add_certificate(equipment_id=123, cert_file="cert.pdf")
        >>> alerts = cm.get_due_soon(days=30)
        >>> cm.export_alerts_report("alerts.txt")
    """

    def __init__(self, db_path: str = "calibration.db"):
        """
        Initialize the Calibration Manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db = CalibrationDatabase(db_path)
        self.parser = CertificateParser()
        self.alert_manager = AlertManager()

    def add_certificate(
        self,
        equipment_id: int,
        cert_file: Optional[Path] = None,
        **certificate_data
    ) -> CalibrationCertificate:
        """
        Add a calibration certificate.

        Can either parse from a file or accept certificate data directly.

        Args:
            equipment_id: ID of equipment being calibrated
            cert_file: Optional path to certificate PDF/TXT file to parse
            **certificate_data: Certificate fields (cert_number, calibration_date, etc.)

        Returns:
            Created CalibrationCertificate object

        Example:
            >>> # From file
            >>> cm.add_certificate(equipment_id=123, cert_file=Path("cert.pdf"))
            >>>
            >>> # Manual entry
            >>> cm.add_certificate(
            ...     equipment_id=123,
            ...     cert_number="CAL-2025-001",
            ...     calibration_date=date(2025, 1, 1),
            ...     due_date=date(2026, 1, 1),
            ...     calibration_lab="ABC Calibration Lab",
            ...     accreditation_body=AccreditationBody.NABL,
            ...     uncertainty=0.05,
            ...     traceability_chain="NIST"
            ... )
        """
        if cert_file:
            # Parse certificate from file
            certificate = self.parser.parse_certificate(
                cert_file, equipment_id, **certificate_data
            )
        else:
            # Create certificate from provided data
            if not all(k in certificate_data for k in [
                'cert_number', 'calibration_date', 'due_date',
                'calibration_lab', 'accreditation_body', 'uncertainty', 'traceability_chain'
            ]):
                raise ValueError(
                    "When not parsing from file, must provide: cert_number, calibration_date, "
                    "due_date, calibration_lab, accreditation_body, uncertainty, traceability_chain"
                )

            certificate = CalibrationCertificate(
                cert_id=None,
                equipment_id=equipment_id,
                **certificate_data
            )

        # Save to database
        cert_id = self.db.add_certificate(certificate)
        certificate.cert_id = cert_id

        # Generate alerts if needed
        self.alert_manager.generate_alerts([certificate])

        return certificate

    def update_certificate(self, certificate: CalibrationCertificate) -> bool:
        """
        Update an existing certificate.

        Args:
            certificate: CalibrationCertificate object with updated data

        Returns:
            True if update successful
        """
        success = self.db.update_certificate(certificate)

        if success:
            # Regenerate alerts for this certificate
            self.alert_manager.generate_alerts([certificate])

        return success

    def get_certificate(self, cert_id: int) -> Optional[CalibrationCertificate]:
        """
        Get certificate by ID.

        Args:
            cert_id: Certificate ID

        Returns:
            CalibrationCertificate or None
        """
        return self.db.get_certificate(cert_id)

    def get_certificates_for_equipment(self, equipment_id: int) -> List[CalibrationCertificate]:
        """
        Get all certificates for specific equipment.

        Args:
            equipment_id: Equipment ID

        Returns:
            List of certificates for the equipment
        """
        return self.db.get_certificates_by_equipment(equipment_id)

    def get_current_certificate(self, equipment_id: int) -> Optional[CalibrationCertificate]:
        """
        Get the most recent valid certificate for equipment.

        Args:
            equipment_id: Equipment ID

        Returns:
            Most recent valid certificate or None
        """
        certificates = self.get_certificates_for_equipment(equipment_id)

        # Filter for valid certificates and sort by calibration date
        valid_certs = [
            cert for cert in certificates
            if cert.is_valid()
        ]

        if valid_certs:
            return max(valid_certs, key=lambda c: c.calibration_date)

        return None

    def get_due_soon(self, days: int = 30) -> List[CalibrationCertificate]:
        """
        Get certificates due within specified days.

        Args:
            days: Number of days to look ahead (default: 30)

        Returns:
            List of certificates due within specified period
        """
        return self.db.get_certificates_due_soon(days)

    def get_expired_certificates(self) -> List[CalibrationCertificate]:
        """
        Get all expired certificates.

        Returns:
            List of expired certificates
        """
        return self.db.get_expired_certificates()

    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        unacknowledged_only: bool = True
    ) -> List[CalibrationAlert]:
        """
        Get calibration alerts.

        Args:
            severity: Optional filter by severity level
            unacknowledged_only: Only return unacknowledged alerts (default: True)

        Returns:
            List of alerts matching criteria
        """
        # Refresh alerts based on current certificates
        self.refresh_alerts()

        if unacknowledged_only:
            alerts = self.alert_manager.get_unacknowledged_alerts()
        else:
            alerts = self.alert_manager.alerts

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        return alerts

    def get_critical_alerts(self) -> List[CalibrationAlert]:
        """
        Get critical and urgent alerts.

        Returns:
            List of critical/urgent alerts
        """
        self.refresh_alerts()
        return self.alert_manager.get_critical_alerts()

    def refresh_alerts(self) -> List[CalibrationAlert]:
        """
        Refresh all alerts based on current certificates.

        Returns:
            List of newly generated alerts
        """
        # Update all certificate statuses
        self.db.update_all_statuses()

        # Get all certificates
        certificates = self.db.get_all_certificates()

        # Clear old alerts and regenerate
        self.alert_manager.alerts = []
        return self.alert_manager.generate_alerts(certificates)

    def acknowledge_alert(self, alert_id: int, user: str) -> bool:
        """
        Acknowledge an alert.

        Args:
            alert_id: Alert ID
            user: Username acknowledging the alert

        Returns:
            True if successful
        """
        return self.alert_manager.acknowledge_alert(alert_id, user)

    def get_calibration_history(self, equipment_id: int) -> List[Dict[str, Any]]:
        """
        Get calibration history for equipment.

        Args:
            equipment_id: Equipment ID

        Returns:
            List of historical calibration records
        """
        return self.db.get_calibration_history(equipment_id)

    def flag_expired_certificates(self) -> List[CalibrationCertificate]:
        """
        Auto-flag all expired certificates.

        Updates certificate status to EXPIRED for certificates past due date.

        Returns:
            List of certificates that were flagged as expired
        """
        expired = self.get_expired_certificates()

        for cert in expired:
            if cert.status != CertificateStatus.EXPIRED:
                cert.update_status()
                self.db.update_certificate(cert)

        return expired

    def validate_traceability(self, cert_id: int) -> Dict[str, Any]:
        """
        Validate traceability chain for a certificate.

        Args:
            cert_id: Certificate ID

        Returns:
            Validation results with status and details
        """
        cert = self.get_certificate(cert_id)

        if not cert:
            return {
                "valid": False,
                "error": "Certificate not found"
            }

        if not cert.traceability_chain_obj:
            return {
                "valid": False,
                "error": "No traceability chain object defined",
                "traceability_string": cert.traceability_chain
            }

        is_valid = cert.traceability_chain_obj.validate()

        return {
            "valid": is_valid,
            "primary_standard": cert.traceability_chain_obj.primary_standard,
            "intermediate_standards": cert.traceability_chain_obj.intermediate_standards,
            "chain_length": len(cert.traceability_chain_obj.intermediate_standards) + 1,
            "uncertainty_propagation": cert.traceability_chain_obj.uncertainty_propagation,
        }

    def generate_compliance_report(self) -> str:
        """
        Generate ISO 17025 compliance report.

        Returns:
            Formatted text report
        """
        all_certs = self.db.get_all_certificates()
        valid_certs = [c for c in all_certs if c.is_valid()]
        expired_certs = [c for c in all_certs if c.is_expired()]
        due_soon = self.get_due_soon(30)

        report_lines = [
            "=" * 80,
            "CALIBRATION COMPLIANCE REPORT - ISO 17025",
            "=" * 80,
            f"Report Date: {date.today().isoformat()}",
            "",
            "SUMMARY:",
            "-" * 80,
            f"Total Certificates: {len(all_certs)}",
            f"Valid Certificates: {len(valid_certs)}",
            f"Expired Certificates: {len(expired_certs)}",
            f"Due within 30 days: {len(due_soon)}",
            "",
        ]

        # Accreditation breakdown
        accreditation_counts = {}
        for cert in all_certs:
            body = cert.accreditation_body.value
            accreditation_counts[body] = accreditation_counts.get(body, 0) + 1

        report_lines.extend([
            "ACCREDITATION BREAKDOWN:",
            "-" * 80,
        ])
        for body, count in sorted(accreditation_counts.items()):
            report_lines.append(f"  {body}: {count}")

        report_lines.append("")

        # Alerts summary
        alert_summary = self.alert_manager.get_alert_summary()
        report_lines.extend([
            "ALERTS:",
            "-" * 80,
            f"  Total alerts: {alert_summary['total']}",
            f"  Unacknowledged: {alert_summary['unacknowledged']}",
            f"  Critical: {alert_summary['critical']}",
            f"  Urgent: {alert_summary['urgent']}",
            f"  Warning: {alert_summary['warning']}",
            f"  Info: {alert_summary['info']}",
            "",
        ])

        # Expired certificates detail
        if expired_certs:
            report_lines.extend([
                "EXPIRED CERTIFICATES:",
                "-" * 80,
            ])
            for cert in sorted(expired_certs, key=lambda c: c.due_date):
                days_overdue = abs(cert.days_until_due())
                report_lines.append(
                    f"  {cert.cert_number} | Equipment: {cert.equipment_id} | "
                    f"Expired: {cert.due_date} ({days_overdue} days overdue)"
                )
            report_lines.append("")

        # Due soon detail
        if due_soon:
            report_lines.extend([
                "CERTIFICATES DUE SOON (Next 30 days):",
                "-" * 80,
            ])
            for cert in sorted(due_soon, key=lambda c: c.due_date):
                days_remaining = cert.days_until_due()
                report_lines.append(
                    f"  {cert.cert_number} | Equipment: {cert.equipment_id} | "
                    f"Due: {cert.due_date} ({days_remaining} days)"
                )
            report_lines.append("")

        report_lines.append("=" * 80)

        return "\n".join(report_lines)

    def export_alerts_report(self, output_file: str) -> None:
        """
        Export alerts to a text file.

        Args:
            output_file: Path to output file
        """
        report = self.alert_manager.generate_email_report(include_acknowledged=False)

        with open(output_file, 'w') as f:
            f.write(report)

    def export_compliance_report(self, output_file: str) -> None:
        """
        Export compliance report to a text file.

        Args:
            output_file: Path to output file
        """
        report = self.generate_compliance_report()

        with open(output_file, 'w') as f:
            f.write(report)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get calibration statistics.

        Returns:
            Dictionary with various statistics
        """
        all_certs = self.db.get_all_certificates()

        if not all_certs:
            return {
                "total_certificates": 0,
                "valid": 0,
                "expired": 0,
                "due_soon_30": 0,
                "due_soon_15": 0,
                "due_soon_7": 0,
            }

        valid_certs = [c for c in all_certs if c.is_valid()]
        expired_certs = [c for c in all_certs if c.is_expired()]

        return {
            "total_certificates": len(all_certs),
            "valid": len(valid_certs),
            "expired": len(expired_certs),
            "due_soon_30": len(self.get_due_soon(30)),
            "due_soon_15": len(self.get_due_soon(15)),
            "due_soon_7": len(self.get_due_soon(7)),
            "unique_equipment": len(set(c.equipment_id for c in all_certs)),
            "accreditation_bodies": len(set(c.accreditation_body for c in all_certs)),
            "avg_uncertainty": sum(c.uncertainty for c in all_certs) / len(all_certs),
        }
