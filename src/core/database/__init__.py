"""
Database Module
===============

SQLAlchemy models and database management for the PV Test Report Automation System.

This module provides:
    - ORM models for all entities (Sample, Test, User, Report, Audit, Equipment)
    - Database session management
    - Migration support via Alembic
    - Connection pooling and transaction management
    - Database utilities and helpers

Compliance:
    - ISO 17025: Data integrity and traceability requirements
    - NABL: Audit trail and record keeping standards
    - 21 CFR Part 11: Electronic records and signatures

Models:
    - Sample: PV module samples under test
    - Test: Individual test executions and results
    - User: System users with RBAC
    - Report: Generated test reports
    - Audit: Immutable audit trail records
    - Equipment: Test equipment and calibration tracking

Usage:
    >>> from src.database import get_session, Sample, Test
    >>> session = get_session()
    >>> sample = Sample(sample_id="PV-2024-001", module_type="Monocrystalline")
    >>> session.add(sample)
    >>> session.commit()
"""

from src.database.base import Base, engine, get_session, SessionLocal
from src.database.models.sample import Sample
from src.database.models.test import Test, TestResult
from src.database.models.user import User, Role, Permission
from src.database.models.report import Report, ReportSection
from src.database.models.audit import AuditLog, DataLineage
from src.database.models.equipment import Equipment, Calibration

__all__ = [
    # Database core
    "Base",
    "engine",
    "get_session",
    "SessionLocal",
    # Models
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
