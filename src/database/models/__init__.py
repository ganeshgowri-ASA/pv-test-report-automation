"""
Database Models Package
========================

SQLAlchemy ORM models for the PV Test Report Automation System.

Models:
    - Sample: PV module samples under test
    - Test: Test executions and configurations
    - TestResult: Individual test results and measurements
    - User: System users with authentication
    - Role: User roles for RBAC
    - Permission: Granular permissions
    - Report: Generated test reports
    - ReportSection: Report sections and content
    - AuditLog: Immutable audit trail
    - DataLineage: Data provenance tracking
    - Equipment: Test equipment inventory
    - Calibration: Equipment calibration records

All models inherit from the declarative Base and include:
    - Timestamps (created_at, updated_at)
    - Soft delete support (deleted_at)
    - UUID primary keys
    - Audit trail integration
    - JSON fields for flexible data storage
"""

__all__ = [
    "Sample",
    "Test",
    "TestResult",
    "User",
    "Role",
    "Permission",
    "Report",
    "ReportSection",
    "AuditLog",
    "DataLineage",
    "Equipment",
    "Calibration",
]
