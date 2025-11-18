"""Alert system for calibration due dates and compliance monitoring."""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any
from .models import CalibrationCertificate, CertificateStatus


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    URGENT = "urgent"


class AlertType(Enum):
    """Types of calibration alerts."""
    DUE_SOON = "due_soon"
    EXPIRED = "expired"
    APPROACHING_30_DAYS = "approaching_30_days"
    APPROACHING_15_DAYS = "approaching_15_days"
    APPROACHING_7_DAYS = "approaching_7_days"
    OVERDUE = "overdue"
    TRACEABILITY_ISSUE = "traceability_issue"
    UNCERTAINTY_EXCEEDS_LIMIT = "uncertainty_exceeds_limit"


@dataclass
class CalibrationAlert:
    """
    Calibration alert notification.

    Attributes:
        alert_id: Unique alert identifier
        certificate: Related calibration certificate
        alert_type: Type of alert
        severity: Alert severity level
        message: Human-readable alert message
        days_until_due: Days until calibration is due (negative if overdue)
        created_at: Alert creation timestamp
        acknowledged: Whether alert has been acknowledged
        acknowledged_by: User who acknowledged the alert
        acknowledged_at: Timestamp of acknowledgment
    """

    alert_id: Optional[int]
    certificate: CalibrationCertificate
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    days_until_due: int
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

    def acknowledge(self, user: str) -> None:
        """Mark alert as acknowledged."""
        self.acknowledged = True
        self.acknowledged_by = user
        self.acknowledged_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "certificate_id": self.certificate.cert_id,
            "cert_number": self.certificate.cert_number,
            "equipment_id": self.certificate.equipment_id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "days_until_due": self.days_until_due,
            "created_at": self.created_at.isoformat(),
            "acknowledged": self.acknowledged,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
        }


class AlertManager:
    """Manages calibration alerts and notifications."""

    def __init__(self):
        """Initialize alert manager."""
        self.alerts: List[CalibrationAlert] = []
        self._alert_id_counter = 1

    def generate_alerts(self, certificates: List[CalibrationCertificate]) -> List[CalibrationAlert]:
        """
        Generate alerts for certificates based on due dates and status.

        Args:
            certificates: List of calibration certificates to check

        Returns:
            List of generated alerts
        """
        new_alerts = []

        for cert in certificates:
            cert.update_status()
            days_until_due = cert.days_until_due()

            # Generate alerts based on days until due
            alert = self._create_alert_for_certificate(cert, days_until_due)
            if alert:
                alert.alert_id = self._alert_id_counter
                self._alert_id_counter += 1
                new_alerts.append(alert)
                self.alerts.append(alert)

        return new_alerts

    def _create_alert_for_certificate(
        self, cert: CalibrationCertificate, days_until_due: int
    ) -> Optional[CalibrationAlert]:
        """Create appropriate alert for a certificate based on its status."""

        # Expired/Overdue (Critical)
        if days_until_due < 0:
            return CalibrationAlert(
                alert_id=None,
                certificate=cert,
                alert_type=AlertType.OVERDUE,
                severity=AlertSeverity.CRITICAL,
                message=f"OVERDUE: Certificate {cert.cert_number} for equipment {cert.equipment_id} "
                        f"expired {abs(days_until_due)} days ago on {cert.due_date}",
                days_until_due=days_until_due,
            )

        # Due today or tomorrow (Urgent)
        if 0 <= days_until_due <= 1:
            return CalibrationAlert(
                alert_id=None,
                certificate=cert,
                alert_type=AlertType.APPROACHING_7_DAYS,
                severity=AlertSeverity.URGENT,
                message=f"URGENT: Certificate {cert.cert_number} for equipment {cert.equipment_id} "
                        f"due in {days_until_due} day(s) on {cert.due_date}",
                days_until_due=days_until_due,
            )

        # Due within 7 days (Critical)
        if 2 <= days_until_due <= 7:
            return CalibrationAlert(
                alert_id=None,
                certificate=cert,
                alert_type=AlertType.APPROACHING_7_DAYS,
                severity=AlertSeverity.CRITICAL,
                message=f"CRITICAL: Certificate {cert.cert_number} for equipment {cert.equipment_id} "
                        f"due in {days_until_due} days on {cert.due_date}",
                days_until_due=days_until_due,
            )

        # Due within 15 days (Warning)
        if 8 <= days_until_due <= 15:
            return CalibrationAlert(
                alert_id=None,
                certificate=cert,
                alert_type=AlertType.APPROACHING_15_DAYS,
                severity=AlertSeverity.WARNING,
                message=f"WARNING: Certificate {cert.cert_number} for equipment {cert.equipment_id} "
                        f"due in {days_until_due} days on {cert.due_date}",
                days_until_due=days_until_due,
            )

        # Due within 30 days (Info)
        if 16 <= days_until_due <= 30:
            return CalibrationAlert(
                alert_id=None,
                certificate=cert,
                alert_type=AlertType.APPROACHING_30_DAYS,
                severity=AlertSeverity.INFO,
                message=f"INFO: Certificate {cert.cert_number} for equipment {cert.equipment_id} "
                        f"due in {days_until_due} days on {cert.due_date}",
                days_until_due=days_until_due,
            )

        return None

    def get_critical_alerts(self) -> List[CalibrationAlert]:
        """Get all critical and urgent alerts."""
        return [
            alert for alert in self.alerts
            if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.URGENT]
            and not alert.acknowledged
        ]

    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[CalibrationAlert]:
        """Get alerts filtered by severity level."""
        return [alert for alert in self.alerts if alert.severity == severity and not alert.acknowledged]

    def get_unacknowledged_alerts(self) -> List[CalibrationAlert]:
        """Get all unacknowledged alerts."""
        return [alert for alert in self.alerts if not alert.acknowledged]

    def get_alerts_for_equipment(self, equipment_id: int) -> List[CalibrationAlert]:
        """Get all alerts for specific equipment."""
        return [
            alert for alert in self.alerts
            if alert.certificate.equipment_id == equipment_id
        ]

    def acknowledge_alert(self, alert_id: int, user: str) -> bool:
        """
        Acknowledge an alert.

        Args:
            alert_id: ID of alert to acknowledge
            user: Username acknowledging the alert

        Returns:
            True if alert was found and acknowledged, False otherwise
        """
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledge(user)
                return True
        return False

    def clear_acknowledged_alerts(self) -> int:
        """
        Remove acknowledged alerts from the list.

        Returns:
            Number of alerts removed
        """
        initial_count = len(self.alerts)
        self.alerts = [alert for alert in self.alerts if not alert.acknowledged]
        return initial_count - len(self.alerts)

    def get_alert_summary(self) -> Dict[str, int]:
        """
        Get summary of alerts by severity.

        Returns:
            Dictionary with counts for each severity level
        """
        summary = {
            "total": len(self.alerts),
            "unacknowledged": len(self.get_unacknowledged_alerts()),
            "critical": len([a for a in self.alerts if a.severity == AlertSeverity.CRITICAL and not a.acknowledged]),
            "urgent": len([a for a in self.alerts if a.severity == AlertSeverity.URGENT and not a.acknowledged]),
            "warning": len([a for a in self.alerts if a.severity == AlertSeverity.WARNING and not a.acknowledged]),
            "info": len([a for a in self.alerts if a.severity == AlertSeverity.INFO and not a.acknowledged]),
        }
        return summary

    def generate_email_report(self, include_acknowledged: bool = False) -> str:
        """
        Generate email-formatted alert report.

        Args:
            include_acknowledged: Whether to include acknowledged alerts

        Returns:
            Formatted text report for email
        """
        alerts_to_report = self.alerts if include_acknowledged else self.get_unacknowledged_alerts()

        if not alerts_to_report:
            return "No calibration alerts at this time."

        # Group alerts by severity
        critical = [a for a in alerts_to_report if a.severity == AlertSeverity.CRITICAL]
        urgent = [a for a in alerts_to_report if a.severity == AlertSeverity.URGENT]
        warning = [a for a in alerts_to_report if a.severity == AlertSeverity.WARNING]
        info = [a for a in alerts_to_report if a.severity == AlertSeverity.INFO]

        report = ["CALIBRATION ALERT REPORT", "=" * 50, ""]

        if critical:
            report.append(f"CRITICAL ALERTS ({len(critical)}):")
            report.append("-" * 50)
            for alert in sorted(critical, key=lambda a: a.days_until_due):
                report.append(f"  {alert.message}")
            report.append("")

        if urgent:
            report.append(f"URGENT ALERTS ({len(urgent)}):")
            report.append("-" * 50)
            for alert in sorted(urgent, key=lambda a: a.days_until_due):
                report.append(f"  {alert.message}")
            report.append("")

        if warning:
            report.append(f"WARNINGS ({len(warning)}):")
            report.append("-" * 50)
            for alert in sorted(warning, key=lambda a: a.days_until_due):
                report.append(f"  {alert.message}")
            report.append("")

        if info:
            report.append(f"INFORMATION ({len(info)}):")
            report.append("-" * 50)
            for alert in sorted(info, key=lambda a: a.days_until_due):
                report.append(f"  {alert.message}")
            report.append("")

        summary = self.get_alert_summary()
        report.append("SUMMARY:")
        report.append(f"  Total alerts: {summary['total']}")
        report.append(f"  Unacknowledged: {summary['unacknowledged']}")
        report.append(f"  Critical: {summary['critical']}")
        report.append(f"  Urgent: {summary['urgent']}")
        report.append(f"  Warning: {summary['warning']}")
        report.append(f"  Info: {summary['info']}")

        return "\n".join(report)
