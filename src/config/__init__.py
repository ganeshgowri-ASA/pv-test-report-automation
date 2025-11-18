"""Configuration Module

This module provides centralized configuration management for the PV Test Report
Automation system.

Key components:
- settings: Application settings loaded from environment variables
- standards_config: IEC/ISO standards configuration loaded from YAML
- Helper functions for accessing configuration data

Usage:
    from src.config import settings, standards_config

    # Access application settings
    database_url = settings.database_url
    upload_dir = settings.upload_dir

    # Access standards configuration
    iec_61215 = standards_config['standards']['iec_61215']

    # Use helper functions
    from src.config import get_standard_info, get_test_info

    standard = get_standard_info('iec_61215', standards_config)
    test = get_test_info('iec_61215', 'MST 10', standards_config)
"""

from .settings import (
    Settings,
    settings,
    standards_config,
    load_standards_config,
    get_settings,
    get_standards_config,
    get_standard_info,
    get_test_info,
    get_upload_path,
    get_report_path,
    get_template_path,
    ensure_directories,
    validate_environment,
)

__all__ = [
    # Main instances
    "settings",
    "standards_config",

    # Classes
    "Settings",

    # Functions
    "load_standards_config",
    "get_settings",
    "get_standards_config",
    "get_standard_info",
    "get_test_info",
    "get_upload_path",
    "get_report_path",
    "get_template_path",
    "ensure_directories",
    "validate_environment",
]

__version__ = "1.0.0"
