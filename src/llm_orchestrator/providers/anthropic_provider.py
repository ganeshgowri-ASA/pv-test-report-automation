"""Anthropic Claude provider."""

import logging
import time
from typing import Optional

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .base_provider import BaseLLMProvider
from ..models import LLMRequest, LLMResponse, LLMProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider implementation."""

    # Pricing (as of 2024) - Update as needed
    PRICING = {
        "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
        "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
        "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
    }

    def __init__(self, api_key: str, model_name: str = "claude-3-5-sonnet-20241022"):
        """Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key.
            model_name: Model name.
        """
        if not ANTHROPIC_AVAILABLE:
            raise RuntimeError("anthropic package not installed. Install with: pip install anthropic")

        super().__init__(api_key, model_name)
        self.client = anthropic.Anthropic(api_key=api_key)
        logger.info(f"AnthropicProvider initialized with model: {model_name}")

    async def generate(
        self,
        request: LLMRequest,
        timeout: Optional[int] = None
    ) -> LLMResponse:
        """Generate response from Claude.

        Args:
            request: LLM request.
            timeout: Request timeout in seconds.

        Returns:
            LLM response.
        """
        start_time = time.time()

        try:
            messages = [{"role": "user", "content": request.prompt}]

            kwargs = {
                "model": self.model_name,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "messages": messages,
            }

            if request.system_prompt:
                kwargs["system"] = request.system_prompt

            if timeout:
                kwargs["timeout"] = timeout

            response = self.client.messages.create(**kwargs)

            latency_ms = int((time.time() - start_time) * 1000)

            # Extract usage information
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            total_tokens = input_tokens + output_tokens

            # Calculate cost
            pricing = self.PRICING.get(self.model_name, {"input": 0.003, "output": 0.015})
            cost = self._calculate_cost(
                input_tokens,
                output_tokens,
                pricing["input"],
                pricing["output"]
            )

            # Extract content
            content = response.content[0].text if response.content else ""

            return LLMResponse(
                content=content,
                provider=LLMProvider.ANTHROPIC,
                model=self.model_name,
                tokens_used=total_tokens,
                cost=cost,
                latency_ms=latency_ms,
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "stop_reason": response.stop_reason,
                }
            )

        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            raise

    async def check_availability(self) -> bool:
        """Check if Anthropic API is available.

        Returns:
            True if available, False otherwise.
        """
        try:
            # Make a minimal request to check availability
            self.client.messages.create(
                model=self.model_name,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception as e:
            logger.warning(f"Anthropic availability check failed: {e}")
            return False
