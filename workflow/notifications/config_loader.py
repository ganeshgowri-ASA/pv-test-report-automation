"""
Configuration Loader

Loads notification configuration from environment variables or config files.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional

from .models import NotificationConfig, DeliveryChannel

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Loads notification configuration from various sources
    """

    @staticmethod
    def from_env() -> NotificationConfig:
        """
        Load configuration from environment variables

        Environment Variables:
            # Email (SMTP)
            SMTP_HOST: SMTP server host
            SMTP_PORT: SMTP server port (default: 587)
            SMTP_USERNAME: SMTP username
            SMTP_PASSWORD: SMTP password
            SMTP_FROM_EMAIL: From email address
            SMTP_USE_TLS: Use TLS (default: true)

            # SMS (Twilio)
            TWILIO_ACCOUNT_SID: Twilio account SID
            TWILIO_AUTH_TOKEN: Twilio auth token
            TWILIO_FROM_NUMBER: Twilio phone number

            # Slack
            SLACK_WEBHOOK_URL: Slack webhook URL
            SLACK_BOT_TOKEN: Slack bot token
            SLACK_DEFAULT_CHANNEL: Default Slack channel (default: #general)

            # Microsoft Teams
            TEAMS_WEBHOOK_URL: Teams webhook URL

            # Retry Configuration
            NOTIFICATION_MAX_RETRIES: Maximum retry attempts (default: 3)
            NOTIFICATION_RETRY_DELAY: Retry delay in seconds (default: 60)

        Returns:
            NotificationConfig instance
        """
        config = NotificationConfig(
            # Email configuration
            smtp_host=os.getenv('SMTP_HOST'),
            smtp_port=int(os.getenv('SMTP_PORT', '587')),
            smtp_username=os.getenv('SMTP_USERNAME'),
            smtp_password=os.getenv('SMTP_PASSWORD'),
            smtp_from_email=os.getenv('SMTP_FROM_EMAIL'),
            smtp_use_tls=os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',

            # Twilio configuration
            twilio_account_sid=os.getenv('TWILIO_ACCOUNT_SID'),
            twilio_auth_token=os.getenv('TWILIO_AUTH_TOKEN'),
            twilio_from_number=os.getenv('TWILIO_FROM_NUMBER'),

            # Slack configuration
            slack_webhook_url=os.getenv('SLACK_WEBHOOK_URL'),
            slack_bot_token=os.getenv('SLACK_BOT_TOKEN'),
            slack_default_channel=os.getenv('SLACK_DEFAULT_CHANNEL', '#general'),

            # Teams configuration
            teams_webhook_url=os.getenv('TEAMS_WEBHOOK_URL'),

            # Retry configuration
            max_retries=int(os.getenv('NOTIFICATION_MAX_RETRIES', '3')),
            retry_delay_seconds=int(os.getenv('NOTIFICATION_RETRY_DELAY', '60'))
        )

        logger.info("Configuration loaded from environment variables")
        return config

    @staticmethod
    def from_file(file_path: str) -> NotificationConfig:
        """
        Load configuration from a JSON file

        Args:
            file_path: Path to JSON configuration file

        Returns:
            NotificationConfig instance

        Example JSON structure:
        {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_username": "user@example.com",
            "smtp_password": "password",
            "smtp_from_email": "noreply@example.com",
            "twilio_account_sid": "AC...",
            "twilio_auth_token": "...",
            "twilio_from_number": "+1234567890",
            "slack_webhook_url": "https://hooks.slack.com/...",
            "teams_webhook_url": "https://outlook.office.com/webhook/..."
        }
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(path, 'r') as f:
            data = json.load(f)

        config = NotificationConfig(**data)
        logger.info(f"Configuration loaded from file: {file_path}")
        return config

    @staticmethod
    def from_dict(config_dict: dict) -> NotificationConfig:
        """
        Load configuration from a dictionary

        Args:
            config_dict: Dictionary with configuration values

        Returns:
            NotificationConfig instance
        """
        config = NotificationConfig(**config_dict)
        logger.info("Configuration loaded from dictionary")
        return config

    @staticmethod
    def get_default_config() -> NotificationConfig:
        """
        Get default configuration

        Returns:
            NotificationConfig with default values
        """
        return NotificationConfig()


def load_config(
    config_file: Optional[str] = None,
    use_env: bool = True
) -> NotificationConfig:
    """
    Load notification configuration

    Priority order:
    1. Config file (if provided)
    2. Environment variables (if use_env=True)
    3. Default configuration

    Args:
        config_file: Optional path to JSON config file
        use_env: Whether to load from environment variables

    Returns:
        NotificationConfig instance
    """
    if config_file:
        try:
            return ConfigLoader.from_file(config_file)
        except Exception as e:
            logger.error(f"Failed to load config from file: {e}")
            logger.info("Falling back to environment variables")

    if use_env:
        return ConfigLoader.from_env()

    logger.info("Using default configuration")
    return ConfigLoader.get_default_config()
