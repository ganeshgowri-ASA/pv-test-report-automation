"""
PV Test Report Automation System
==================================

A comprehensive photovoltaic testing and reporting automation platform
compliant with IEC 61215-2021, IEC 61730-2023, ISO 17025, and NABL standards.

Modules:
    - database: SQLAlchemy models and database operations
    - config: Configuration management system
    - security: Authentication, encryption, and RBAC
    - audit: Audit trail and data lineage tracking
    - validation: Data validation and completeness checks
    - protocols: IEC/ISO protocol implementations
    - tests: Test execution engines
    - workflow: Review and approval workflows
    - equipment: Equipment and calibration management
    - llm: LLM integration for compliance and summarization
    - export: Report generation and export engines
    - ui: Streamlit-based user interface

Author: PV Test Automation Team
License: Proprietary
"""

__version__ = "0.1.0"
__author__ = "PV Test Automation Team"
__license__ = "Proprietary"

# Package metadata
__all__ = [
    "database",
    "config",
    "security",
    "audit",
    "validation",
    "protocols",
    "tests",
    "workflow",
    "equipment",
    "llm",
    "export",
    "ui",
]
