"""Google Gemini provider."""

import logging
import time
from typing import Optional

try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

from .base_provider import BaseLLMProvider
from ..models import LLMRequest, LLMResponse, LLMProvider

logger = logging.getLogger(__name__)


class GoogleProvider(BaseLLMProvider):
    """Google Gemini provider implementation."""

    # Pricing (as of 2024) - Update as needed
    PRICING = {
        "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
        "gemini-1.5-flash": {"input": 0.000125, "output": 0.0005},
        "gemini-pro": {"input": 0.00025, "output": 0.001},
    }

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-pro"):
        """Initialize Google provider.

        Args:
            api_key: Google API key.
            model_name: Model name.
        """
        if not GOOGLE_AVAILABLE:
            raise RuntimeError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )

        super().__init__(api_key, model_name)
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        logger.info(f"GoogleProvider initialized with model: {model_name}")

    async def generate(
        self,
        request: LLMRequest,
        timeout: Optional[int] = None
    ) -> LLMResponse:
        """Generate response from Gemini.

        Args:
            request: LLM request.
            timeout: Request timeout in seconds.

        Returns:
            LLM response.
        """
        start_time = time.time()

        try:
            # Combine system prompt and user prompt if system prompt exists
            full_prompt = request.prompt
            if request.system_prompt:
                full_prompt = f"{request.system_prompt}\n\n{request.prompt}"

            generation_config = genai.types.GenerationConfig(
                max_output_tokens=request.max_tokens,
                temperature=request.temperature,
            )

            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config,
            )

            latency_ms = int((time.time() - start_time) * 1000)

            # Extract content
            content = response.text if response.text else ""

            # Estimate token usage (Gemini doesn't always provide exact counts)
            # Rough estimation: ~4 characters per token
            input_tokens = len(full_prompt) // 4
            output_tokens = len(content) // 4
            total_tokens = input_tokens + output_tokens

            # Calculate cost
            pricing = self.PRICING.get(self.model_name, {"input": 0.00125, "output": 0.005})
            cost = self._calculate_cost(
                input_tokens,
                output_tokens,
                pricing["input"],
                pricing["output"]
            )

            return LLMResponse(
                content=content,
                provider=LLMProvider.GOOGLE,
                model=self.model_name,
                tokens_used=total_tokens,
                cost=cost,
                latency_ms=latency_ms,
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "finish_reason": response.candidates[0].finish_reason if response.candidates else None,
                }
            )

        except Exception as e:
            logger.error(f"Google generation failed: {e}")
            raise

    async def check_availability(self) -> bool:
        """Check if Google API is available.

        Returns:
            True if available, False otherwise.
        """
        try:
            # Make a minimal request to check availability
            self.model.generate_content("test")
            return True
        except Exception as e:
            logger.warning(f"Google availability check failed: {e}")
            return False
