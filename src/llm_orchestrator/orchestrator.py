"""Main LLM Orchestrator - Unified interface for multi-model LLM management."""

import logging
from typing import Optional, List
import asyncio

from .models import LLMProvider, LLMRequest, LLMResponse, ModelConfig
from .router import LLMRouter
from .cost_tracker import CostTracker
from .providers import AnthropicProvider, OpenAIProvider, GoogleProvider
from .providers.base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)


class LLMOrchestrator:
    """Unified LLM orchestrator with intelligent routing and fallback.

    Features:
    - Multi-provider support (Anthropic, OpenAI, Google)
    - Intelligent routing and load balancing
    - Automatic fallback on failures
    - Cost tracking and optimization
    - Response aggregation
    - ISO 17025 audit logging
    """

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        google_api_key: Optional[str] = None,
        monthly_budget: Optional[float] = None,
        enable_fallback: bool = True,
        max_retries: int = 3,
        timeout: int = 30
    ):
        """Initialize LLM orchestrator.

        Args:
            anthropic_api_key: Anthropic API key.
            openai_api_key: OpenAI API key.
            google_api_key: Google API key.
            monthly_budget: Monthly budget in USD.
            enable_fallback: Enable automatic fallback.
            max_retries: Maximum number of retries per provider.
            timeout: Request timeout in seconds.
        """
        self.providers: dict[LLMProvider, BaseLLMProvider] = {}
        self.router = LLMRouter()
        self.cost_tracker = CostTracker(monthly_budget)
        self.enable_fallback = enable_fallback
        self.max_retries = max_retries
        self.timeout = timeout

        # Initialize providers
        if anthropic_api_key:
            self._init_anthropic(anthropic_api_key)

        if openai_api_key:
            self._init_openai(openai_api_key)

        if google_api_key:
            self._init_google(google_api_key)

        if not self.providers:
            logger.warning("No LLM providers initialized - at least one API key is required")

        logger.info(
            f"LLMOrchestrator initialized with {len(self.providers)} providers, "
            f"fallback={'enabled' if enable_fallback else 'disabled'}"
        )

    def _init_anthropic(self, api_key: str) -> None:
        """Initialize Anthropic provider."""
        try:
            provider = AnthropicProvider(api_key)
            self.providers[LLMProvider.ANTHROPIC] = provider

            config = ModelConfig(
                provider=LLMProvider.ANTHROPIC,
                model_name="claude-3-5-sonnet-20241022",
                cost_per_1k_input_tokens=0.003,
                cost_per_1k_output_tokens=0.015,
                max_tokens=8192,
                priority=3  # High priority
            )
            self.router.register_model(config)

            logger.info("Anthropic provider initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic provider: {e}")

    def _init_openai(self, api_key: str) -> None:
        """Initialize OpenAI provider."""
        try:
            provider = OpenAIProvider(api_key)
            self.providers[LLMProvider.OPENAI] = provider

            config = ModelConfig(
                provider=LLMProvider.OPENAI,
                model_name="gpt-4o",
                cost_per_1k_input_tokens=0.005,
                cost_per_1k_output_tokens=0.015,
                max_tokens=4096,
                priority=2  # Medium priority
            )
            self.router.register_model(config)

            logger.info("OpenAI provider initialized")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI provider: {e}")

    def _init_google(self, api_key: str) -> None:
        """Initialize Google provider."""
        try:
            provider = GoogleProvider(api_key)
            self.providers[LLMProvider.GOOGLE] = provider

            config = ModelConfig(
                provider=LLMProvider.GOOGLE,
                model_name="gemini-1.5-pro",
                cost_per_1k_input_tokens=0.00125,
                cost_per_1k_output_tokens=0.005,
                max_tokens=8192,
                priority=1  # Lower priority
            )
            self.router.register_model(config)

            logger.info("Google provider initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google provider: {e}")

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response with intelligent routing and fallback.

        Args:
            request: LLM request.

        Returns:
            LLM response.

        Raises:
            RuntimeError: If all providers fail.
        """
        # Select primary provider
        primary_provider = self.router.select_provider(request.preferred_provider)

        if not primary_provider:
            raise RuntimeError("No available providers")

        # Build provider chain (primary + fallbacks)
        provider_chain = [primary_provider]

        if self.enable_fallback and request.fallback_enabled:
            fallbacks = self.router.get_fallback_chain(primary_provider)
            provider_chain.extend(fallbacks)

        # Try providers in order
        last_error = None
        for provider in provider_chain:
            if provider not in self.providers:
                continue

            try:
                response = await self._generate_with_retries(
                    self.providers[provider],
                    request
                )

                # Track response
                self.cost_tracker.track_response(response)
                self.router.update_provider_status(
                    provider,
                    success=True,
                    latency_ms=response.latency_ms
                )

                logger.info(
                    f"Successfully generated response using {provider} "
                    f"(${response.cost:.4f}, {response.tokens_used} tokens, "
                    f"{response.latency_ms}ms)"
                )

                return response

            except Exception as e:
                last_error = e
                self.router.update_provider_status(provider, success=False)
                logger.warning(f"Provider {provider} failed: {e}")
                continue

        # All providers failed
        raise RuntimeError(f"All providers failed. Last error: {last_error}")

    async def _generate_with_retries(
        self,
        provider: BaseLLMProvider,
        request: LLMRequest
    ) -> LLMResponse:
        """Generate with retries for a single provider.

        Args:
            provider: Provider to use.
            request: LLM request.

        Returns:
            LLM response.

        Raises:
            Exception: If all retries fail.
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = await provider.generate(request, timeout=self.timeout)
                return response

            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.debug(f"Retry attempt {attempt + 1}, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)

        raise last_error or RuntimeError("Generation failed")

    async def generate_batch(
        self,
        requests: List[LLMRequest],
        max_concurrent: int = 5
    ) -> List[LLMResponse]:
        """Generate multiple responses concurrently.

        Args:
            requests: List of LLM requests.
            max_concurrent: Maximum concurrent requests.

        Returns:
            List of LLM responses.
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _generate_with_semaphore(req: LLMRequest) -> LLMResponse:
            async with semaphore:
                return await self.generate(req)

        responses = await asyncio.gather(
            *[_generate_with_semaphore(req) for req in requests],
            return_exceptions=True
        )

        # Filter out exceptions and log them
        valid_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                logger.error(f"Batch request {i} failed: {response}")
            else:
                valid_responses.append(response)

        return valid_responses

    def get_cost_summary(self) -> dict:
        """Get cost summary.

        Returns:
            Cost summary dictionary.
        """
        stats = self.cost_tracker.get_stats()
        return {
            "total_cost": stats.total_cost,
            "total_requests": stats.total_requests,
            "total_tokens": stats.total_tokens,
            "average_cost_per_request": stats.total_cost / stats.total_requests if stats.total_requests > 0 else 0,
            "cost_by_provider": stats.by_provider,
            "monthly_budget": self.cost_tracker.monthly_budget,
            "monthly_cost": self.cost_tracker.get_monthly_cost(),
            "recommendations": self.cost_tracker.get_optimization_recommendations(),
        }

    def get_provider_status(self) -> dict:
        """Get provider status summary.

        Returns:
            Provider status dictionary.
        """
        return {
            provider.value: {
                "available": status.available,
                "success_count": status.success_count,
                "error_count": status.error_count,
                "average_latency_ms": status.average_latency_ms,
                "last_check": status.last_check.isoformat(),
            }
            for provider, status in self.router.provider_status.items()
        }
