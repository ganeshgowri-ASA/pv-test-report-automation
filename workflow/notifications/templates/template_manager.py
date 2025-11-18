"""
Template Manager

Manages notification templates and rendering.
"""

from typing import Dict, Optional
import logging

from ..models import NotificationTemplate, NotificationType
from .default_templates import get_default_templates

logger = logging.getLogger(__name__)


class TemplateManager:
    """
    Manages notification templates
    """

    def __init__(self):
        """Initialize template manager with default templates"""
        self.templates: Dict[str, NotificationTemplate] = get_default_templates()

    def get_template(self, template_id: str) -> Optional[NotificationTemplate]:
        """
        Get a template by ID

        Args:
            template_id: Template identifier

        Returns:
            NotificationTemplate or None if not found
        """
        return self.templates.get(template_id)

    def get_template_by_type(self, notification_type: NotificationType) -> Optional[NotificationTemplate]:
        """
        Get the default template for a notification type

        Args:
            notification_type: NotificationType enum value

        Returns:
            NotificationTemplate or None if not found
        """
        for template in self.templates.values():
            if template.notification_type == notification_type:
                return template
        return None

    def add_template(self, template: NotificationTemplate) -> None:
        """
        Add or update a template

        Args:
            template: NotificationTemplate to add
        """
        self.templates[template.template_id] = template
        logger.info(f"Added template: {template.template_id}")

    def remove_template(self, template_id: str) -> bool:
        """
        Remove a template

        Args:
            template_id: Template ID to remove

        Returns:
            True if removed, False if not found
        """
        if template_id in self.templates:
            del self.templates[template_id]
            logger.info(f"Removed template: {template_id}")
            return True
        return False

    def render_template(self, template_id: str, **variables) -> Optional[tuple[str, str]]:
        """
        Render a template with provided variables

        Args:
            template_id: Template ID to render
            **variables: Template variables

        Returns:
            Tuple of (subject, message) or None if template not found
        """
        template = self.get_template(template_id)
        if not template:
            logger.error(f"Template not found: {template_id}")
            return None

        try:
            return template.render(**variables)
        except KeyError as e:
            logger.error(f"Missing template variable: {e}")
            raise ValueError(f"Missing required template variable: {e}")
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            raise

    def list_templates(self) -> Dict[str, NotificationTemplate]:
        """
        Get all templates

        Returns:
            Dictionary of all templates
        """
        return self.templates.copy()
