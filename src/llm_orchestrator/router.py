"""LLM Router - Intelligent routing and load balancing."""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
import random

from .models import LLMProvider, ModelConfig, ProviderStatus

logger = logging.getLogger(__name__)


class LLMRouter:
    """Intelligent router for LLM requests.

    Features:
    - Load balancing across providers
    - Priority-based routing
    - Health checking
    - Fallback selection
    """

    def __init__(self):
        """Initialize LLM router."""
        self.model_configs: List[ModelConfig] = []
        self.provider_status: dict[LLMProvider, ProviderStatus] = {}
        logger.info("LLMRouter initialized")

    def register_model(self, config: ModelConfig) -> None:
        """Register a model configuration.

        Args:
            config: Model configuration.
        """
        self.model_configs.append(config)
        logger.info(f"Registered model: {config.provider} - {config.model_name}")

    def select_provider(
        self,
        preferred_provider: Optional[LLMProvider] = None,
        exclude_providers: Optional[List[LLMProvider]] = None
    ) -> Optional[LLMProvider]:
        """Select best provider for request.

        Args:
            preferred_provider: Preferred provider (if available).
            exclude_providers: Providers to exclude from selection.

        Returns:
            Selected provider or None if none available.
        """
        exclude_providers = exclude_providers or []

        # Try preferred provider first
        if preferred_provider and preferred_provider not in exclude_providers:
            if self._is_provider_available(preferred_provider):
                return preferred_provider

        # Get available providers
        available_configs = [
            config for config in self.model_configs
            if config.enabled
            and config.provider not in exclude_providers
            and self._is_provider_available(config.provider)
        ]

        if not available_configs:
            logger.warning("No available providers")
            return None

        # Sort by priority (higher priority first) and average latency
        available_configs.sort(
            key=lambda c: (
                -c.priority,  # Higher priority first
                self.provider_status.get(c.provider, ProviderStatus(
                    provider=c.provider,
                    available=True,
                    last_check=datetime.utcnow()
                )).average_latency_ms
            )
        )

        # Weighted random selection from top candidates
        # This provides load balancing while preferring higher priority providers
        top_candidates = available_configs[:3]  # Top 3 candidates
        weights = [c.priority for c in top_candidates]
        selected_config = random.choices(top_candidates, weights=weights)[0]

        logger.info(f"Selected provider: {selected_config.provider} (priority: {selected_config.priority})")
        return selected_config.provider

    def get_fallback_chain(
        self,
        primary_provider: LLMProvider,
        max_fallbacks: int = 2
    ) -> List[LLMProvider]:
        """Get fallback chain for a provider.

        Args:
            primary_provider: Primary provider.
            max_fallbacks: Maximum number of fallbacks.

        Returns:
            List of fallback providers in order of preference.
        """
        fallbacks = []
        exclude = [primary_provider]

        for _ in range(max_fallbacks):
            next_provider = self.select_provider(exclude_providers=exclude)
            if next_provider:
                fallbacks.append(next_provider)
                exclude.append(next_provider)
            else:
                break

        return fallbacks

    def update_provider_status(
        self,
        provider: LLMProvider,
        success: bool,
        latency_ms: Optional[int] = None
    ) -> None:
        """Update provider status after request.

        Args:
            provider: Provider that was used.
            success: Whether request was successful.
            latency_ms: Request latency in milliseconds.
        """
        if provider not in self.provider_status:
            self.provider_status[provider] = ProviderStatus(
                provider=provider,
                available=True,
                last_check=datetime.utcnow()
            )

        status = self.provider_status[provider]
        status.last_check = datetime.utcnow()

        if success:
            status.success_count += 1
            if latency_ms is not None:
                # Update rolling average latency
                total_requests = status.success_count + status.error_count
                status.average_latency_ms = (
                    (status.average_latency_ms * (total_requests - 1) + latency_ms) / total_requests
                )
        else:
            status.error_count += 1

        # Mark as unavailable if too many consecutive errors
        total_requests = status.success_count + status.error_count
        if total_requests >= 5:
            error_rate = status.error_count / total_requests
            status.available = error_rate < 0.5  # Mark unavailable if >50% error rate

        logger.debug(
            f"Updated {provider} status: "
            f"success={status.success_count}, "
            f"errors={status.error_count}, "
            f"avg_latency={status.average_latency_ms:.0f}ms"
        )

    def _is_provider_available(self, provider: LLMProvider) -> bool:
        """Check if provider is available.

        Args:
            provider: Provider to check.

        Returns:
            True if available, False otherwise.
        """
        if provider not in self.provider_status:
            return True  # Assume available if no status yet

        status = self.provider_status[provider]

        # Check if status is stale (> 5 minutes)
        if datetime.utcnow() - status.last_check > timedelta(minutes=5):
            return True  # Reset availability after 5 minutes

        return status.available

    def get_model_config(self, provider: LLMProvider) -> Optional[ModelConfig]:
        """Get model configuration for provider.

        Args:
            provider: Provider.

        Returns:
            Model configuration or None if not found.
        """
        for config in self.model_configs:
            if config.provider == provider and config.enabled:
                return config
        return None
