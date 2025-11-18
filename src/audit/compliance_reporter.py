"""
Compliance Reporter
Generate audit reports for ISO 17025 assessments and regulatory compliance.

Features:
- Export audit logs in multiple formats (CSV, JSON, PDF)
- Advanced search and filtering
- Compliance dashboard with statistics
- Detect unauthorized access attempts
- Generate reports for auditors
"""

import csv
import json
from datetime import datetime, timedelta, timezone
from io import StringIO, BytesIO
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import pandas as pd
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, select, func, and_, or_, desc
from sqlalchemy.orm import Session

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from .trail_logger import AuditEventModel, AuditEventType, AuditEvent


class AuditStatistics(BaseModel):
    """Statistics for compliance dashboard"""

    total_events: int = 0
    events_by_type: Dict[str, int] = Field(default_factory=dict)
    events_by_user: Dict[str, int] = Field(default_factory=dict)
    events_by_day: Dict[str, int] = Field(default_factory=dict)

    unique_users: int = 0
    unique_sessions: int = 0
    unique_entities: int = 0

    security_events: int = 0
    failed_logins: int = 0
    unauthorized_access_attempts: int = 0

    crud_operations: Dict[str, int] = Field(default_factory=dict)

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class AuditReport(BaseModel):
    """Audit report for compliance purposes"""

    report_id: UUID
    title: str
    description: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    generated_by: str

    period_start: datetime
    period_end: datetime

    statistics: AuditStatistics
    events: List[Dict[str, Any]] = Field(default_factory=list)

    findings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

    compliance_standards: List[str] = Field(default_factory=lambda: ["ISO 17025", "21 CFR Part 11"])


class ComplianceReporter:
    """
    Generate compliance reports and audit analytics.

    Provides:
    - ISO 17025 assessment reports
    - Audit log exports (CSV, JSON, PDF)
    - Advanced search and filtering
    - Unauthorized access detection
    - Compliance dashboard statistics

    Example:
        reporter = ComplianceReporter(db_url="postgresql://...")

        # Generate monthly audit report
        report = reporter.generate_audit_report(
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
            title="January 2024 Audit Report",
            generated_by="auditor@company.com"
        )

        # Export to PDF
        pdf_data = reporter.export_report_pdf(report)

        # Get compliance dashboard
        stats = reporter.get_compliance_dashboard(days=30)

        # Detect security issues
        issues = reporter.detect_security_issues(days=7)
    """

    def __init__(self, db_url: str):
        """Initialize compliance reporter"""
        self.engine = create_engine(db_url, echo=False)

    def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        entity_type: Optional[str] = None
    ) -> AuditStatistics:
        """
        Calculate audit statistics for a given period.

        Args:
            start_date: Start of period (default: 30 days ago)
            end_date: End of period (default: now)
            user_id: Filter by specific user
            entity_type: Filter by entity type

        Returns:
            AuditStatistics with aggregated data
        """
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        with Session(self.engine) as session:
            # Build base query
            stmt = select(AuditEventModel)
            conditions = [
                AuditEventModel.timestamp >= start_date,
                AuditEventModel.timestamp <= end_date
            ]
            if user_id:
                conditions.append(AuditEventModel.user_id == user_id)
            if entity_type:
                conditions.append(AuditEventModel.entity_type == entity_type)

            stmt = stmt.where(and_(*conditions))

            # Get all events
            events = session.execute(stmt).scalars().all()

            stats = AuditStatistics(
                start_date=start_date,
                end_date=end_date
            )

            stats.total_events = len(events)

            # Count by type
            for event in events:
                event_type = event.event_type
                stats.events_by_type[event_type] = stats.events_by_type.get(event_type, 0) + 1

                # Count by user
                stats.events_by_user[event.user_name] = stats.events_by_user.get(event.user_name, 0) + 1

                # Count by day
                day_str = event.timestamp.strftime("%Y-%m-%d")
                stats.events_by_day[day_str] = stats.events_by_day.get(day_str, 0) + 1

            # Unique counts
            stats.unique_users = len(set(e.user_id for e in events))
            stats.unique_sessions = len(set(e.session_id for e in events if e.session_id))
            stats.unique_entities = len(set(f"{e.entity_type}:{e.entity_id}" for e in events if e.entity_id))

            # Security metrics
            security_event_types = {
                AuditEventType.UNAUTHORIZED_ACCESS.value,
                AuditEventType.PRIVILEGE_ESCALATION.value,
                AuditEventType.DATA_BREACH_ATTEMPT.value
            }
            stats.security_events = sum(
                1 for e in events if e.event_type in security_event_types
            )
            stats.failed_logins = sum(
                1 for e in events if e.event_type == AuditEventType.LOGIN_FAILED.value
            )
            stats.unauthorized_access_attempts = sum(
                1 for e in events if e.event_type == AuditEventType.UNAUTHORIZED_ACCESS.value
            )

            # CRUD operations
            crud_types = {"CREATE", "READ", "UPDATE", "DELETE"}
            for event in events:
                if event.event_type in crud_types:
                    stats.crud_operations[event.event_type] = \
                        stats.crud_operations.get(event.event_type, 0) + 1

            return stats

    def search_events(
        self,
        query: Optional[str] = None,
        event_types: Optional[List[str]] = None,
        user_ids: Optional[List[str]] = None,
        entity_types: Optional[List[str]] = None,
        entity_ids: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> Tuple[List[AuditEvent], int]:
        """
        Advanced search of audit events with multiple filters.

        Args:
            query: Text search in action, description, reason
            event_types: Filter by event types
            user_ids: Filter by user IDs
            entity_types: Filter by entity types
            entity_ids: Filter by entity IDs
            start_date: Events after this date
            end_date: Events before this date
            ip_address: Filter by IP address
            session_id: Filter by session ID
            limit: Maximum results to return
            offset: Number of results to skip

        Returns:
            Tuple of (events, total_count)
        """
        with Session(self.engine) as session:
            # Build query
            stmt = select(AuditEventModel)
            conditions = []

            # Text search
            if query:
                text_conditions = [
                    AuditEventModel.action.ilike(f"%{query}%"),
                    AuditEventModel.description.ilike(f"%{query}%"),
                    AuditEventModel.reason.ilike(f"%{query}%"),
                ]
                conditions.append(or_(*text_conditions))

            # Filter conditions
            if event_types:
                conditions.append(AuditEventModel.event_type.in_(event_types))
            if user_ids:
                conditions.append(AuditEventModel.user_id.in_(user_ids))
            if entity_types:
                conditions.append(AuditEventModel.entity_type.in_(entity_types))
            if entity_ids:
                conditions.append(AuditEventModel.entity_id.in_(entity_ids))
            if start_date:
                conditions.append(AuditEventModel.timestamp >= start_date)
            if end_date:
                conditions.append(AuditEventModel.timestamp <= end_date)
            if ip_address:
                conditions.append(AuditEventModel.ip_address == ip_address)
            if session_id:
                conditions.append(AuditEventModel.session_id == session_id)

            if conditions:
                stmt = stmt.where(and_(*conditions))

            # Get total count
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total_count = session.execute(count_stmt).scalar()

            # Apply ordering, limit, offset
            stmt = stmt.order_by(desc(AuditEventModel.timestamp))
            stmt = stmt.limit(limit).offset(offset)

            # Execute query
            db_events = session.execute(stmt).scalars().all()

            # Convert to Pydantic models
            events = []
            for db_event in db_events:
                event = AuditEvent(
                    id=db_event.id,
                    sequence_number=db_event.sequence_number,
                    timestamp=db_event.timestamp,
                    event_type=AuditEventType(db_event.event_type),
                    entity_type=db_event.entity_type,
                    entity_id=db_event.entity_id,
                    user_id=db_event.user_id,
                    user_name=db_event.user_name,
                    user_role=db_event.user_role,
                    ip_address=db_event.ip_address,
                    user_agent=db_event.user_agent,
                    session_id=db_event.session_id,
                    action=db_event.action,
                    description=db_event.description,
                    reason=db_event.reason,
                    old_values=db_event.old_values,
                    new_values=db_event.new_values,
                    metadata=db_event.metadata,
                    previous_hash=db_event.previous_hash,
                    event_hash=db_event.event_hash,
                    retention_until=db_event.retention_until,
                    is_anonymized=db_event.is_anonymized == "true",
                )
                events.append(event)

            return events, total_count

    def generate_audit_report(
        self,
        period_start: datetime,
        period_end: datetime,
        title: str,
        generated_by: str,
        description: Optional[str] = None,
        include_events: bool = True,
        event_limit: int = 10000
    ) -> AuditReport:
        """
        Generate a comprehensive audit report for a period.

        Args:
            period_start: Start of reporting period
            period_end: End of reporting period
            title: Report title
            generated_by: User generating the report
            description: Report description
            include_events: Whether to include full event list
            event_limit: Maximum events to include

        Returns:
            AuditReport object
        """
        from uuid import uuid4

        # Get statistics
        stats = self.get_statistics(
            start_date=period_start,
            end_date=period_end
        )

        # Get events if requested
        events_data = []
        if include_events:
            events, _ = self.search_events(
                start_date=period_start,
                end_date=period_end,
                limit=event_limit
            )
            events_data = [e.model_dump(mode="json") for e in events]

        # Generate findings
        findings = self._analyze_findings(stats)

        # Generate recommendations
        recommendations = self._generate_recommendations(stats)

        report = AuditReport(
            report_id=uuid4(),
            title=title,
            description=description or f"Audit report for period {period_start.date()} to {period_end.date()}",
            generated_by=generated_by,
            period_start=period_start,
            period_end=period_end,
            statistics=stats,
            events=events_data,
            findings=findings,
            recommendations=recommendations
        )

        return report

    def _analyze_findings(self, stats: AuditStatistics) -> List[str]:
        """Analyze statistics and generate findings"""
        findings = []

        # Check for security issues
        if stats.security_events > 0:
            findings.append(
                f"CRITICAL: {stats.security_events} security event(s) detected "
                f"(unauthorized access, privilege escalation, or breach attempts)"
            )

        if stats.failed_logins > 10:
            findings.append(
                f"WARNING: {stats.failed_logins} failed login attempts detected. "
                f"Consider reviewing authentication security."
            )

        if stats.unauthorized_access_attempts > 0:
            findings.append(
                f"WARNING: {stats.unauthorized_access_attempts} unauthorized access attempt(s) detected"
            )

        # Activity analysis
        if stats.total_events == 0:
            findings.append("INFO: No audit events recorded in this period")
        else:
            findings.append(
                f"INFO: {stats.total_events} total events from {stats.unique_users} unique user(s)"
            )

        # CRUD analysis
        if stats.crud_operations:
            crud_summary = ", ".join(
                f"{op}: {count}" for op, count in stats.crud_operations.items()
            )
            findings.append(f"INFO: CRUD operations - {crud_summary}")

        return findings

    def _generate_recommendations(self, stats: AuditStatistics) -> List[str]:
        """Generate recommendations based on statistics"""
        recommendations = []

        if stats.security_events > 0:
            recommendations.append(
                "Investigate all security events immediately and take corrective action"
            )

        if stats.failed_logins > 10:
            recommendations.append(
                "Review failed login patterns and consider implementing rate limiting or account lockout"
            )

        if stats.total_events > 100000:
            recommendations.append(
                "Consider implementing audit log archival and retention policies (high volume detected)"
            )

        if stats.unique_users < 2:
            recommendations.append(
                "Ensure multiple personnel are trained on system usage for redundancy"
            )

        recommendations.append(
            "Maintain regular audit reviews per ISO 17025 requirements"
        )

        return recommendations

    def export_csv(
        self,
        events: List[AuditEvent],
        include_columns: Optional[List[str]] = None
    ) -> str:
        """
        Export events to CSV format.

        Args:
            events: List of events to export
            include_columns: Specific columns to include (default: all)

        Returns:
            CSV string
        """
        if not events:
            return ""

        # Default columns
        if include_columns is None:
            include_columns = [
                "timestamp", "event_type", "user_name", "action",
                "entity_type", "entity_id", "description", "reason"
            ]

        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=include_columns)
        writer.writeheader()

        for event in events:
            event_dict = event.model_dump()
            row = {col: event_dict.get(col, "") for col in include_columns}
            # Convert datetime to ISO format
            if "timestamp" in row and row["timestamp"]:
                row["timestamp"] = row["timestamp"].isoformat() if hasattr(row["timestamp"], "isoformat") else str(row["timestamp"])
            writer.writerow(row)

        return output.getvalue()

    def export_json(self, events: List[AuditEvent]) -> str:
        """Export events to JSON format"""
        events_data = [e.model_dump(mode="json") for e in events]
        return json.dumps(events_data, indent=2, default=str)

    def export_report_pdf(self, report: AuditReport) -> bytes:
        """
        Export audit report to PDF format.

        Args:
            report: AuditReport to export

        Returns:
            PDF bytes

        Raises:
            ImportError: If reportlab is not installed
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab is required for PDF export. Install with: pip install reportlab")

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        elements.append(Paragraph(report.title, title_style))
        elements.append(Spacer(1, 0.2 * inch))

        # Metadata
        elements.append(Paragraph(f"<b>Report ID:</b> {report.report_id}", styles['Normal']))
        elements.append(Paragraph(f"<b>Generated:</b> {report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}", styles['Normal']))
        elements.append(Paragraph(f"<b>Generated By:</b> {report.generated_by}", styles['Normal']))
        elements.append(Paragraph(
            f"<b>Period:</b> {report.period_start.strftime('%Y-%m-%d')} to {report.period_end.strftime('%Y-%m-%d')}",
            styles['Normal']
        ))
        elements.append(Spacer(1, 0.3 * inch))

        # Description
        if report.description:
            elements.append(Paragraph(report.description, styles['Normal']))
            elements.append(Spacer(1, 0.2 * inch))

        # Statistics
        elements.append(Paragraph("<b>Audit Statistics</b>", styles['Heading2']))
        stats = report.statistics

        stats_data = [
            ["Metric", "Value"],
            ["Total Events", str(stats.total_events)],
            ["Unique Users", str(stats.unique_users)],
            ["Unique Sessions", str(stats.unique_sessions)],
            ["Security Events", str(stats.security_events)],
            ["Failed Logins", str(stats.failed_logins)],
            ["Unauthorized Access", str(stats.unauthorized_access_attempts)],
        ]

        stats_table = Table(stats_data, colWidths=[3 * inch, 2 * inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(stats_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Findings
        if report.findings:
            elements.append(Paragraph("<b>Findings</b>", styles['Heading2']))
            for finding in report.findings:
                elements.append(Paragraph(f"• {finding}", styles['Normal']))
            elements.append(Spacer(1, 0.2 * inch))

        # Recommendations
        if report.recommendations:
            elements.append(Paragraph("<b>Recommendations</b>", styles['Heading2']))
            for rec in report.recommendations:
                elements.append(Paragraph(f"• {rec}", styles['Normal']))

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.read()

    def get_compliance_dashboard(self, days: int = 30) -> Dict[str, Any]:
        """
        Get compliance dashboard data for the last N days.

        Args:
            days: Number of days to analyze

        Returns:
            Dashboard data dictionary
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        stats = self.get_statistics(start_date=start_date, end_date=end_date)

        # Detect security issues
        security_issues = self.detect_security_issues(days=days)

        dashboard = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "statistics": stats.model_dump(),
            "security_issues": security_issues,
            "compliance_status": self._assess_compliance_status(stats),
            "trending": {
                "daily_events": stats.events_by_day,
                "top_users": dict(sorted(
                    stats.events_by_user.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]),
                "event_type_distribution": stats.events_by_type
            }
        }

        return dashboard

    def detect_security_issues(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Detect potential security issues in recent audit logs.

        Args:
            days: Number of days to analyze

        Returns:
            List of security issues found
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        issues = []

        # Search for security events
        security_event_types = [
            AuditEventType.UNAUTHORIZED_ACCESS.value,
            AuditEventType.PRIVILEGE_ESCALATION.value,
            AuditEventType.DATA_BREACH_ATTEMPT.value,
        ]

        events, count = self.search_events(
            event_types=security_event_types,
            start_date=start_date,
            end_date=end_date,
            limit=1000
        )

        for event in events:
            issues.append({
                "type": "security_event",
                "severity": "CRITICAL",
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "user": event.user_name,
                "description": event.description or event.action,
                "ip_address": event.ip_address
            })

        # Detect multiple failed logins
        failed_logins, _ = self.search_events(
            event_types=[AuditEventType.LOGIN_FAILED.value],
            start_date=start_date,
            end_date=end_date,
            limit=1000
        )

        # Group by user
        failed_by_user: Dict[str, int] = {}
        for event in failed_logins:
            failed_by_user[event.user_id] = failed_by_user.get(event.user_id, 0) + 1

        for user_id, count in failed_by_user.items():
            if count >= 5:  # Threshold
                issues.append({
                    "type": "excessive_failed_logins",
                    "severity": "HIGH",
                    "user_id": user_id,
                    "count": count,
                    "description": f"{count} failed login attempts for user {user_id}"
                })

        return issues

    def _assess_compliance_status(self, stats: AuditStatistics) -> str:
        """Assess overall compliance status"""
        if stats.security_events > 0:
            return "NON_COMPLIANT"
        elif stats.failed_logins > 20:
            return "AT_RISK"
        elif stats.total_events == 0:
            return "UNKNOWN"
        else:
            return "COMPLIANT"
