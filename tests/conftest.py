"""
Pytest configuration and fixtures for audit trail tests.
"""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.audit.trail_logger import Base as AuditBase, AuditTrailLogger
from src.audit.lineage_tracker import Base as LineageBase, DataLineageTracker
from src.audit.compliance_reporter import ComplianceReporter
from src.audit.integrity_checker import IntegrityChecker


@pytest.fixture(scope="session")
def db_url():
    """Database URL for testing. Uses in-memory SQLite by default."""
    # Use environment variable if set, otherwise use SQLite in-memory
    return os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture(scope="function")
def db_engine(db_url):
    """Create a fresh database engine for each test."""
    engine = create_engine(db_url, echo=False)

    # Create all tables
    AuditBase.metadata.create_all(engine)
    LineageBase.metadata.create_all(engine)

    yield engine

    # Drop all tables after test
    AuditBase.metadata.drop_all(engine)
    LineageBase.metadata.drop_all(engine)

    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Provide a database session for tests."""
    session = Session(db_engine)
    yield session
    session.close()


@pytest.fixture(scope="function")
def audit_logger(db_url):
    """Provide an AuditTrailLogger instance."""
    logger = AuditTrailLogger(db_url=db_url, auto_create_tables=True)
    yield logger
    # Cleanup handled by db_engine fixture


@pytest.fixture(scope="function")
def lineage_tracker(db_url):
    """Provide a DataLineageTracker instance."""
    tracker = DataLineageTracker(db_url=db_url, auto_create_tables=True)
    yield tracker


@pytest.fixture(scope="function")
def compliance_reporter(db_url):
    """Provide a ComplianceReporter instance."""
    return ComplianceReporter(db_url=db_url)


@pytest.fixture(scope="function")
def integrity_checker(db_url):
    """Provide an IntegrityChecker instance."""
    return IntegrityChecker(db_url=db_url)
