"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from typing import Optional
import logging

from ..models import LLMRequest, LLMResponse

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, api_key: str, model_name: str):
        """Initialize provider.

        Args:
            api_key: API key for the provider.
            model_name: Default model name.
        """
        self.api_key = api_key
        self.model_name = model_name

    @abstractmethod
    async def generate(
        self,
        request: LLMRequest,
        timeout: Optional[int] = None
    ) -> LLMResponse:
        """Generate response from LLM.

        Args:
            request: LLM request.
            timeout: Request timeout in seconds.

        Returns:
            LLM response.

        Raises:
            Exception: If generation fails.
        """
        pass

    @abstractmethod
    async def check_availability(self) -> bool:
        """Check if provider is available.

        Returns:
            True if available, False otherwise.
        """
        pass

    def _calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        input_cost_per_1k: float,
        output_cost_per_1k: float
    ) -> float:
        """Calculate cost for token usage.

        Args:
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.
            input_cost_per_1k: Cost per 1000 input tokens.
            output_cost_per_1k: Cost per 1000 output tokens.

        Returns:
            Total cost in USD.
        """
        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        return input_cost + output_cost
