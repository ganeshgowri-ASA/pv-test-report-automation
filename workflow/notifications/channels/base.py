"""
Base Channel Interface

Defines the interface that all notification channels must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..models import Notification, NotificationConfig


class BaseChannel(ABC):
    """
    Abstract base class for notification delivery channels
    """

    def __init__(self, config: NotificationConfig):
        """
        Initialize the channel with configuration

        Args:
            config: NotificationConfig instance
        """
        self.config = config

    @abstractmethod
    async def send(self, notification: Notification, recipient: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Send a notification through this channel

        Args:
            notification: Notification instance to send
            recipient: Dictionary containing recipient information
                      (e.g., email, phone_number, user_id)

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate that the channel is properly configured

        Returns:
            True if configuration is valid, False otherwise
        """
        pass

    def get_channel_name(self) -> str:
        """Get the name of this channel"""
        return self.__class__.__name__
