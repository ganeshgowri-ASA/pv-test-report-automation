"""Core GPT client with error handling and retry logic."""

import time
import logging
from typing import Optional, Dict, Any, List
from openai import OpenAI, OpenAIError, RateLimitError, APIError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from ..models.gpt_models import GPTRequest, GPTResponse
from ..utils.config import Config
from ..utils.cache import CacheManager
from ..utils.rate_limiter import RateLimiter
from ..utils.cost_tracker import CostTracker


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GPTIntegration:
    """Core GPT integration with comprehensive error handling and management."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[Config] = None
    ):
        """
        Initialize GPT integration.

        Args:
            api_key: OpenAI API key (optional if using config)
            config: Configuration object (optional)
        """
        self.config = config or Config.from_env()
        self.api_key = api_key or self.config.openai_api_key

        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=self.api_key,
            organization=self.config.openai_organization
        )

        # Initialize management components
        self.cache = CacheManager(
            max_size=self.config.cache_max_size,
            ttl_seconds=self.config.cache_ttl_seconds
        ) if self.config.enable_cache else None

        self.rate_limiter = RateLimiter(
            requests_per_minute=self.config.rate_limit_requests_per_minute,
            tokens_per_minute=self.config.rate_limit_tokens_per_minute
        )

        self.cost_tracker = CostTracker(
            alert_threshold_usd=self.config.cost_alert_threshold_usd
        ) if self.config.enable_cost_tracking else None

        logger.info("GPT Integration initialized successfully")

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation: 1 token ≈ 4 chars)."""
        return len(text) // 4

    def _calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """Calculate cost for API call."""
        pricing = self.config.get_model_pricing(model)
        prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
        completion_cost = (completion_tokens / 1000) * pricing["completion"]
        return prompt_cost + completion_cost

    @retry(
        retry=retry_if_exception_type((RateLimitError, APIError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=lambda retry_state: logger.info(
            f"Retrying after error: {retry_state.outcome.exception()}"
        )
    )
    def _make_api_call(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Any:
        """Make API call with retry logic."""
        return self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

    def generate_completion(
        self,
        request: GPTRequest,
        use_cache: bool = True
    ) -> GPTResponse:
        """
        Generate GPT completion with full management.

        Args:
            request: GPT request object
            use_cache: Whether to use cache

        Returns:
            GPT response object

        Raises:
            OpenAIError: If API call fails after retries
        """
        # Check cache first
        if use_cache and self.cache:
            cached = self.cache.get(
                request.prompt,
                request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            if cached:
                logger.info("Cache hit - returning cached response")
                cached.cached = True
                return cached

        # Estimate tokens and check rate limits
        estimated_tokens = self._estimate_tokens(request.prompt) + request.max_tokens
        wait_time = self.rate_limiter.wait_if_needed(estimated_tokens)
        if wait_time > 0:
            logger.info(f"Rate limit wait: {wait_time:.2f}s")

        # Prepare messages
        messages = []
        if request.system_message:
            messages.append({
                "role": "system",
                "content": request.system_message
            })
        messages.append({
            "role": "user",
            "content": request.prompt
        })

        # Make API call with retry logic
        try:
            start_time = time.time()
            completion = self._make_api_call(
                messages=messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            elapsed_time = time.time() - start_time

            # Extract response data
            content = completion.choices[0].message.content
            prompt_tokens = completion.usage.prompt_tokens
            completion_tokens = completion.usage.completion_tokens
            total_tokens = completion.usage.total_tokens

            # Calculate cost
            cost = self._calculate_cost(
                request.model,
                prompt_tokens,
                completion_tokens
            )

            # Record usage
            self.rate_limiter.record_request(total_tokens)
            if self.cost_tracker:
                self.cost_tracker.record_cost(
                    model=request.model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    cost_usd=cost,
                    metadata={
                        "elapsed_time": elapsed_time,
                        "temperature": request.temperature
                    }
                )

            # Create response
            response = GPTResponse(
                content=content,
                model_used=request.model,
                tokens_used=total_tokens,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_usd=cost,
                cached=False
            )

            # Cache response
            if use_cache and self.cache:
                self.cache.set(
                    request.prompt,
                    request.model,
                    response,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                )

            logger.info(
                f"GPT call completed: {total_tokens} tokens, "
                f"${cost:.4f}, {elapsed_time:.2f}s"
            )

            return response

        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    def query(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Simple query interface.

        Args:
            prompt: The prompt text
            system_message: Optional system message
            model: Model to use (defaults to config)
            temperature: Temperature (defaults to config)
            max_tokens: Max tokens (defaults to config)

        Returns:
            Response content as string
        """
        request = GPTRequest(
            prompt=prompt,
            model=model or self.config.default_model,
            temperature=temperature or self.config.default_temperature,
            max_tokens=max_tokens or self.config.default_max_tokens,
            system_message=system_message
        )
        response = self.generate_completion(request)
        return response.content

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        stats = {
            "rate_limiter": self.rate_limiter.get_stats(),
        }

        if self.cache:
            stats["cache"] = self.cache.get_stats()

        if self.cost_tracker:
            stats["costs"] = self.cost_tracker.get_stats()

        return stats
