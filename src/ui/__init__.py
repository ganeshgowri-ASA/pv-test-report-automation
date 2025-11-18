"""UI Package for PV Test Report Automation System.

This package provides Streamlit-based user interface components including:
- Dashboard: Main dashboard with KPIs and system overview
- Upload Interface: Multi-file upload with validation
- Report Builder: Interactive report builder
- Review Interface: Report review workflow
- Export Interface: Export functionality
- Components: Reusable UI components (charts, tables, forms, navigation)
"""

from .dashboard import render_dashboard
from .upload_interface import render_upload_interface
from .report_builder import render_report_builder
from .review_interface import render_review_interface
from .export_interface import render_export_interface


__all__ = [
    "render_dashboard",
    "render_upload_interface",
    "render_report_builder",
    "render_review_interface",
    "render_export_interface",
]

__version__ = "0.1.0"
