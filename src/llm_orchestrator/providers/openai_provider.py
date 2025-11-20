"""OpenAI GPT provider."""

import logging
import time
from typing import Optional

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .base_provider import BaseLLMProvider
from ..models import LLMRequest, LLMResponse, LLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider implementation."""

    # Pricing (as of 2024) - Update as needed
    PRICING = {
        "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    }

    def __init__(self, api_key: str, model_name: str = "gpt-4o"):
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key.
            model_name: Model name.
        """
        if not OPENAI_AVAILABLE:
            raise RuntimeError("openai package not installed. Install with: pip install openai")

        super().__init__(api_key, model_name)
        self.client = openai.OpenAI(api_key=api_key)
        logger.info(f"OpenAIProvider initialized with model: {model_name}")

    async def generate(
        self,
        request: LLMRequest,
        timeout: Optional[int] = None
    ) -> LLMResponse:
        """Generate response from GPT.

        Args:
            request: LLM request.
            timeout: Request timeout in seconds.

        Returns:
            LLM response.
        """
        start_time = time.time()

        try:
            messages = []

            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})

            messages.append({"role": "user", "content": request.prompt})

            kwargs = {
                "model": self.model_name,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "messages": messages,
            }

            if timeout:
                kwargs["timeout"] = timeout

            response = self.client.chat.completions.create(**kwargs)

            latency_ms = int((time.time() - start_time) * 1000)

            # Extract usage information
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens

            # Calculate cost
            pricing = self.PRICING.get(self.model_name, {"input": 0.005, "output": 0.015})
            cost = self._calculate_cost(
                input_tokens,
                output_tokens,
                pricing["input"],
                pricing["output"]
            )

            # Extract content
            content = response.choices[0].message.content if response.choices else ""

            return LLMResponse(
                content=content,
                provider=LLMProvider.OPENAI,
                model=self.model_name,
                tokens_used=total_tokens,
                cost=cost,
                latency_ms=latency_ms,
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "finish_reason": response.choices[0].finish_reason if response.choices else None,
                }
            )

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise

    async def check_availability(self) -> bool:
        """Check if OpenAI API is available.

        Returns:
            True if available, False otherwise.
        """
        try:
            # Make a minimal request to check availability
            self.client.chat.completions.create(
                model=self.model_name,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception as e:
            logger.warning(f"OpenAI availability check failed: {e}")
            return False
