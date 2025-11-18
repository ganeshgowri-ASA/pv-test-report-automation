"""PV Test Report Automation System

A comprehensive system for automating photovoltaic (PV) module test report
generation with AI-powered data extraction, quality assurance, and compliance
with IEC/ISO standards.

Main modules:
- config: Configuration management (settings, standards)
- models: Database models and schemas
- services: Business logic and services
- api: REST API endpoints
- utils: Utility functions and helpers
- reports: Report generation and templates
"""

__version__ = "1.0.0"
__author__ = "PV Test Report Automation Team"
__description__ = "PV Test Report Automation System"

# Package initialization
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info(f"PV Test Report Automation System v{__version__} initialized")
