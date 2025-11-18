"""
Notification Templates

Pre-defined templates for common notification types.
"""

from .template_manager import TemplateManager
from .default_templates import get_default_templates

__all__ = ['TemplateManager', 'get_default_templates']
