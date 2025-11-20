"""
LLM Orchestrator for Multi-Model Routing and Fallback.

Provides intelligent routing between Claude, GPT, and Gemini based on:
- Task type and complexity
- Cost optimization
- API availability and rate limits
- Performance requirements
- Fallback handling

Ensures high availability and optimal LLM selection.
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from src.llm.claude_integration import ClaudeLLM, ClaudeResponse
from src.llm.gemini_integration import GeminiLLM, GeminiResponse
from src.llm.gpt_integration import GPTLLM, GPTResponse

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """LLM provider types."""

    CLAUDE = "claude"
    GPT = "gpt"
    GEMINI = "gemini"


class TaskType(str, Enum):
    """Task type classification."""

    COMPLIANCE_CHECK = "compliance_check"
    SUMMARIZE = "summarize"
    ANALYZE_DEFECTS = "analyze_defects"
    QA_REVIEW = "qa_review"
    GENERATE_DOCS = "generate_docs"
    GENERAL = "general"


class RoutingStrategy(str, Enum):
    """LLM routing strategies."""

    COST_OPTIMIZED = "cost_optimized"
    PERFORMANCE_OPTIMIZED = "performance_optimized"
    BALANCED = "balanced"
    SPECIFIC_PROVIDER = "specific_provider"


class OrchestratorConfig(BaseModel):
    """Orchestrator configuration."""

    default_provider: LLMProvider = LLMProvider.CLAUDE
    routing_strategy: RoutingStrategy = RoutingStrategy.BALANCED
    enable_fallback: bool = True
    fallback_order: List[LLMProvider] = Field(
        default=[LLMProvider.CLAUDE, LLMProvider.GPT, LLMProvider.GEMINI]
    )
    max_retries: int = 3


class LLMOrchestrator:
    """
    Multi-LLM orchestrator with intelligent routing and fallback.

    Routes requests to optimal LLM provider based on configuration and availability.
    """

    def __init__(self, config: OrchestratorConfig = OrchestratorConfig()):
        """
        Initialize LLM orchestrator.

        Args:
            config: Orchestrator configuration
        """
        self.config = config
        self.providers: Dict[LLMProvider, Any] = {}

        # Initialize available providers
        self._initialize_providers()

        logger.info(
            f"LLM Orchestrator initialized with {len(self.providers)} providers: "
            f"{list(self.providers.keys())}"
        )

    def _initialize_providers(self) -> None:
        """Initialize LLM provider clients."""
        # Try to initialize each provider
        try:
            self.providers[LLMProvider.CLAUDE] = ClaudeLLM()
            logger.info("Claude provider initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Claude: {e}")

        try:
            self.providers[LLMProvider.GPT] = GPTLLM()
            logger.info("GPT provider initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize GPT: {e}")

        try:
            self.providers[LLMProvider.GEMINI] = GeminiLLM()
            logger.info("Gemini provider initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini: {e}")

        if not self.providers:
            raise RuntimeError("No LLM providers could be initialized")

    def _select_provider(
        self,
        task_type: TaskType,
        preferred_provider: Optional[LLMProvider] = None,
    ) -> LLMProvider:
        """
        Select optimal LLM provider based on task and strategy.

        Args:
            task_type: Type of task
            preferred_provider: Preferred provider (overrides strategy)

        Returns:
            Selected provider
        """
        if preferred_provider and preferred_provider in self.providers:
            return preferred_provider

        if self.config.routing_strategy == RoutingStrategy.SPECIFIC_PROVIDER:
            if self.config.default_provider in self.providers:
                return self.config.default_provider

        # Task-based routing
        task_provider_map = {
            TaskType.COMPLIANCE_CHECK: LLMProvider.CLAUDE,  # Claude best for compliance
            TaskType.QA_REVIEW: LLMProvider.CLAUDE,
            TaskType.SUMMARIZE: LLMProvider.GPT,  # GPT good for summaries
            TaskType.ANALYZE_DEFECTS: LLMProvider.CLAUDE,
            TaskType.GENERATE_DOCS: LLMProvider.GPT,
            TaskType.GENERAL: self.config.default_provider,
        }

        recommended = task_provider_map.get(task_type, self.config.default_provider)

        if recommended in self.providers:
            return recommended

        # Fallback to first available provider
        return next(iter(self.providers.keys()))

    def process_request(
        self,
        task_type: TaskType,
        input_data: Dict[str, Any],
        preferred_provider: Optional[LLMProvider] = None,
        **kwargs: Any,
    ) -> Union[ClaudeResponse, GPTResponse, GeminiResponse]:
        """
        Process LLM request with routing and fallback.

        Args:
            task_type: Type of task to perform
            input_data: Input data for the task
            preferred_provider: Preferred LLM provider
            **kwargs: Additional task-specific arguments

        Returns:
            LLM response

        Raises:
            RuntimeError: If all providers fail
        """
        logger.info(f"Processing {task_type.value} request")

        provider = self._select_provider(task_type, preferred_provider)
        fallback_providers = (
            [p for p in self.config.fallback_order if p in self.providers and p != provider]
            if self.config.enable_fallback
            else []
        )

        all_providers = [provider] + fallback_providers
        last_error = None

        for attempt, current_provider in enumerate(all_providers):
            try:
                logger.info(
                    f"Attempting {task_type.value} with {current_provider.value} "
                    f"(attempt {attempt + 1}/{len(all_providers)})"
                )

                response = self._execute_task(
                    current_provider, task_type, input_data, **kwargs
                )

                logger.info(
                    f"Successfully processed {task_type.value} with {current_provider.value}"
                )
                return response

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Failed to process with {current_provider.value}: {e}"
                )
                continue

        # All providers failed
        error_msg = f"All LLM providers failed for {task_type.value}. Last error: {last_error}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    def _execute_task(
        self,
        provider: LLMProvider,
        task_type: TaskType,
        input_data: Dict[str, Any],
        **kwargs: Any,
    ) -> Union[ClaudeResponse, GPTResponse, GeminiResponse]:
        """
        Execute task with specific provider.

        Args:
            provider: LLM provider to use
            task_type: Task type
            input_data: Input data
            **kwargs: Additional arguments

        Returns:
            Provider-specific response
        """
        client = self.providers[provider]

        if provider == LLMProvider.CLAUDE:
            if task_type == TaskType.COMPLIANCE_CHECK:
                return client.compliance_check(
                    test_report=input_data.get("test_report", {}),
                    standards=input_data.get("standards", []),
                )
            elif task_type == TaskType.SUMMARIZE:
                return client.summarize_report(
                    test_report=input_data.get("test_report", {}),
                    summary_type=kwargs.get("summary_type", "executive"),
                )
            elif task_type == TaskType.ANALYZE_DEFECTS:
                return client.analyze_defects(
                    defects=input_data.get("defects", []),
                    test_type=input_data.get("test_type", "unknown"),
                )
            elif task_type == TaskType.QA_REVIEW:
                return client.qa_review(test_report=input_data.get("test_report", {}))

        elif provider == LLMProvider.GPT:
            return client.analyze_report(test_report=input_data.get("test_report", {}))

        elif provider == LLMProvider.GEMINI:
            return client.analyze_report(test_report=input_data.get("test_report", {}))

        raise ValueError(f"Unsupported task type: {task_type}")

    def get_provider_status(self) -> Dict[str, bool]:
        """
        Get status of all providers.

        Returns:
            Dictionary of provider availability
        """
        return {
            provider.value: provider in self.providers
            for provider in LLMProvider
        }
