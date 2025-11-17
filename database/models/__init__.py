"""
Database Models Package

Exports all database models for the PV test report automation system.

Models:
    - Sample: PV module samples under test
    - Test: Individual test execution records
    - User: User accounts and permissions
    - Report: Test reports with workflow
    - Audit: Audit trail for compliance
    - Equipment: Test equipment and calibration tracking
"""

# Import models
from .equipment import Equipment, EquipmentStatus
from .user import User, UserRole, UserStatus
from .sample import Sample, SampleStatus, SampleType
from .test import Test, TestType, TestStatus, PassFailStatus
from .report import Report, ReportType, ReportStatus, ReportFormat
from .audit import Audit, AuditAction, AuditSeverity


# Export all models and enums
__all__ = [
    # Equipment
    "Equipment",
    "EquipmentStatus",

    # User
    "User",
    "UserRole",
    "UserStatus",

    # Sample
    "Sample",
    "SampleStatus",
    "SampleType",

    # Test
    "Test",
    "TestType",
    "TestStatus",
    "PassFailStatus",

    # Report
    "Report",
    "ReportType",
    "ReportStatus",
    "ReportFormat",

    # Audit
    "Audit",
    "AuditAction",
    "AuditSeverity",
]


# Version info
__version__ = "1.0.0"


def get_all_models():
    """
    Get list of all model classes.

    Returns:
        List of model classes
    """
    return [
        Equipment,
        User,
        Sample,
        Test,
        Report,
        Audit,
    ]


def get_model_by_name(name: str):
    """
    Get model class by name.

    Args:
        name: Model name (case-insensitive)

    Returns:
        Model class or None if not found
    """
    model_map = {
        "equipment": Equipment,
        "user": User,
        "sample": Sample,
        "test": Test,
        "report": Report,
        "audit": Audit,
    }
    return model_map.get(name.lower())
