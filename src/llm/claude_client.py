"""
Claude API client for PV test report automation.

Provides a production-ready wrapper around the Anthropic Claude API with:
- Authentication and secure API key management
- Message handling with system prompts
- Streaming response support
- Token usage tracking and cost estimation
- Error handling and rate limit management
- Retry logic with exponential backoff
- Comprehensive audit logging
"""

import asyncio
import hashlib
import time
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from anthropic import Anthropic, AsyncAnthropic
from anthropic.types import Message, MessageStreamEvent
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.config.settings import get_settings
from src.logging.logger import get_logger
from src.models.audit_trail import AuditEntry, AuditAction, AuditStatus, LLMUsageMetrics
from src.utils.exceptions import (
    ClaudeAPIException,
    RateLimitException,
    AuthenticationException,
    TokenLimitException,
)


class TokenUsageTracker:
    """Track and analyze token usage across API calls."""

    def __init__(self) -> None:
        """Initialize token usage tracker."""
        self.usage_log: List[Dict[str, Any]] = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

    def record_usage(
        self,
        model: str,
        operation: str,
        input_tokens: int,
        output_tokens: int,
        duration: float,
    ) -> Dict[str, Any]:
        """
        Record token usage for an API call.

        Args:
            model: Model name used
            operation: Type of operation
            input_tokens: Input tokens consumed
            output_tokens: Output tokens generated
            duration: Call duration in seconds

        Returns:
            Usage record with cost estimation
        """
        # Claude 3.5 Sonnet pricing (as of Jan 2024)
        # Input: $3 per million tokens, Output: $15 per million tokens
        cost_per_input_token = 3.0 / 1_000_000
        cost_per_output_token = 15.0 / 1_000_000

        estimated_cost = (input_tokens * cost_per_input_token) + (
            output_tokens * cost_per_output_token
        )

        usage_record = {
            "timestamp": datetime.utcnow(),
            "model": model,
            "operation": operation,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "duration_seconds": duration,
            "estimated_cost": estimated_cost,
        }

        self.usage_log.append(usage_record)
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += estimated_cost

        return usage_record

    def get_summary(self) -> Dict[str, Any]:
        """Get usage summary statistics."""
        if not self.usage_log:
            return {
                "total_calls": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
            }

        return {
            "total_calls": len(self.usage_log),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost_usd": round(self.total_cost, 4),
            "average_tokens_per_call": round(
                (self.total_input_tokens + self.total_output_tokens) / len(self.usage_log), 2
            ),
            "average_cost_per_call": round(self.total_cost / len(self.usage_log), 4),
        }


class ClaudeClient:
    """
    Production-ready Claude API client with comprehensive features.

    Features:
    - Synchronous and asynchronous API calls
    - Streaming and non-streaming responses
    - Automatic retry with exponential backoff
    - Rate limiting and error handling
    - Token usage tracking and cost estimation
    - Audit trail integration
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout: Optional[int] = None,
    ):
        """
        Initialize Claude API client.

        Args:
            api_key: Anthropic API key (defaults to settings)
            model: Model to use (defaults to settings)
            max_tokens: Maximum tokens for responses (defaults to settings)
            temperature: Sampling temperature (defaults to settings)
            timeout: Request timeout in seconds (defaults to settings)
        """
        self.settings = get_settings()
        self.logger = get_logger(__name__)

        # Configuration
        self.api_key = api_key or self.settings.CLAUDE_API_KEY
        if not self.api_key:
            raise AuthenticationException("Claude API key not configured")

        self.model = model or self.settings.CLAUDE_MODEL
        self.max_tokens = max_tokens or self.settings.CLAUDE_MAX_TOKENS
        self.temperature = temperature or self.settings.CLAUDE_TEMPERATURE
        self.timeout = timeout or self.settings.CLAUDE_TIMEOUT

        # Initialize clients
        self.client = Anthropic(api_key=self.api_key, timeout=self.timeout)
        self.async_client = AsyncAnthropic(api_key=self.api_key, timeout=self.timeout)

        # Usage tracking
        self.token_tracker = TokenUsageTracker()

        self.logger.info(
            "Claude API client initialized",
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

    @staticmethod
    def _hash_prompt(prompt: str) -> str:
        """Create hash of prompt for tracking."""
        return hashlib.sha256(prompt.encode()).hexdigest()[:16]

    def _create_audit_entry(
        self,
        operation: str,
        user_id: str,
        resource_id: str,
        status: AuditStatus,
        llm_usage: Optional[LLMUsageMetrics] = None,
        prompt: Optional[str] = None,
        response: Optional[str] = None,
        error: Optional[str] = None,
    ) -> AuditEntry:
        """Create audit entry for LLM interaction."""
        audit_id = f"AUD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        return AuditEntry(
            audit_id=audit_id,
            timestamp=datetime.utcnow(),
            action=AuditAction.LLM_ANALYSIS,
            resource_type="LLMInteraction",
            resource_id=resource_id,
            user_id=user_id,
            status=status,
            llm_usage=llm_usage,
            llm_prompt=prompt if self.settings.AUDIT_LOG_LLM_PROMPTS else None,
            llm_response=response if self.settings.AUDIT_LOG_LLM_PROMPTS else None,
            error_message=error,
            metadata={"operation": operation},
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=16),
        retry=retry_if_exception_type(RateLimitException),
        reraise=True,
    )
    def create_message(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> Message:
        """
        Create a message using Claude API with retry logic.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system: Optional system prompt
            model: Model to use (overrides default)
            max_tokens: Max tokens (overrides default)
            temperature: Temperature (overrides default)
            **kwargs: Additional API parameters

        Returns:
            Claude API Message response

        Raises:
            ClaudeAPIException: On API errors
            RateLimitException: On rate limiting
            TokenLimitException: On token limit exceeded
        """
        start_time = time.time()

        try:
            request_params = {
                "model": model or self.model,
                "max_tokens": max_tokens or self.max_tokens,
                "messages": messages,
                **kwargs,
            }

            if temperature is not None:
                request_params["temperature"] = temperature
            elif self.temperature is not None:
                request_params["temperature"] = self.temperature

            if system:
                request_params["system"] = system

            self.logger.debug(
                "Creating Claude message",
                model=request_params["model"],
                message_count=len(messages),
                system_prompt_provided=bool(system),
            )

            response = self.client.messages.create(**request_params)

            duration = time.time() - start_time

            # Track usage
            usage_record = self.token_tracker.record_usage(
                model=request_params["model"],
                operation="create_message",
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                duration=duration,
            )

            self.logger.log_llm_call(
                model=request_params["model"],
                operation="create_message",
                tokens_used={
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                },
                duration=duration,
                success=True,
            )

            return response

        except Exception as e:
            duration = time.time() - start_time
            error_message = str(e)

            self.logger.error(
                f"Claude API error: {error_message}",
                model=model or self.model,
                duration=duration,
            )

            # Handle specific error types
            if "rate_limit" in error_message.lower():
                raise RateLimitException(error_message)
            elif "authentication" in error_message.lower() or "api_key" in error_message.lower():
                raise AuthenticationException(error_message)
            elif "token" in error_message.lower() and "limit" in error_message.lower():
                raise TokenLimitException(error_message)
            else:
                raise ClaudeAPIException(error_message)

    async def create_message_async(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> Message:
        """
        Async version of create_message.

        Args:
            messages: List of message dictionaries
            system: Optional system prompt
            model: Model to use
            max_tokens: Max tokens
            temperature: Temperature
            **kwargs: Additional parameters

        Returns:
            Claude API Message response
        """
        start_time = time.time()

        try:
            request_params = {
                "model": model or self.model,
                "max_tokens": max_tokens or self.max_tokens,
                "messages": messages,
                **kwargs,
            }

            if temperature is not None:
                request_params["temperature"] = temperature
            elif self.temperature is not None:
                request_params["temperature"] = self.temperature

            if system:
                request_params["system"] = system

            response = await self.async_client.messages.create(**request_params)

            duration = time.time() - start_time

            # Track usage
            self.token_tracker.record_usage(
                model=request_params["model"],
                operation="create_message_async",
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                duration=duration,
            )

            self.logger.log_llm_call(
                model=request_params["model"],
                operation="create_message_async",
                tokens_used={
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                },
                duration=duration,
                success=True,
            )

            return response

        except Exception as e:
            duration = time.time() - start_time
            error_message = str(e)

            self.logger.error(
                f"Claude API async error: {error_message}",
                model=model or self.model,
                duration=duration,
            )

            if "rate_limit" in error_message.lower():
                raise RateLimitException(error_message)
            elif "authentication" in error_message.lower():
                raise AuthenticationException(error_message)
            elif "token" in error_message.lower() and "limit" in error_message.lower():
                raise TokenLimitException(error_message)
            else:
                raise ClaudeAPIException(error_message)

    def create_message_stream(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Create a streaming message response.

        Args:
            messages: List of message dictionaries
            system: Optional system prompt
            model: Model to use
            max_tokens: Max tokens
            temperature: Temperature
            **kwargs: Additional parameters

        Returns:
            Stream of message events

        Usage:
            with client.create_message_stream(...) as stream:
                for event in stream:
                    if event.type == "content_block_delta":
                        print(event.delta.text, end="", flush=True)
        """
        request_params = {
            "model": model or self.model,
            "max_tokens": max_tokens or self.max_tokens,
            "messages": messages,
            **kwargs,
        }

        if temperature is not None:
            request_params["temperature"] = temperature
        elif self.temperature is not None:
            request_params["temperature"] = self.temperature

        if system:
            request_params["system"] = system

        self.logger.debug("Creating streaming message", model=request_params["model"])

        return self.client.messages.stream(**request_params)

    async def create_message_stream_async(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> AsyncIterator[MessageStreamEvent]:
        """
        Create an async streaming message response.

        Args:
            messages: List of message dictionaries
            system: Optional system prompt
            model: Model to use
            max_tokens: Max tokens
            temperature: Temperature
            **kwargs: Additional parameters

        Returns:
            Async iterator of message events
        """
        request_params = {
            "model": model or self.model,
            "max_tokens": max_tokens or self.max_tokens,
            "messages": messages,
            **kwargs,
        }

        if temperature is not None:
            request_params["temperature"] = temperature
        elif self.temperature is not None:
            request_params["temperature"] = self.temperature

        if system:
            request_params["system"] = system

        async with self.async_client.messages.stream(**request_params) as stream:
            async for event in stream:
                yield event

    def simple_prompt(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Simple helper to send a single prompt and get text response.

        Args:
            prompt: User prompt
            system: Optional system prompt
            **kwargs: Additional parameters

        Returns:
            Response text
        """
        messages = [{"role": "user", "content": prompt}]
        response = self.create_message(messages, system=system, **kwargs)
        return response.content[0].text

    async def simple_prompt_async(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Async version of simple_prompt.

        Args:
            prompt: User prompt
            system: Optional system prompt
            **kwargs: Additional parameters

        Returns:
            Response text
        """
        messages = [{"role": "user", "content": prompt}]
        response = await self.create_message_async(messages, system=system, **kwargs)
        return response.content[0].text

    def get_usage_summary(self) -> Dict[str, Any]:
        """
        Get token usage summary.

        Returns:
            Usage statistics dictionary
        """
        return self.token_tracker.get_summary()

    def check_cost_threshold(self) -> bool:
        """
        Check if cost has exceeded alert threshold.

        Returns:
            True if threshold exceeded
        """
        if self.settings.ENABLE_COST_TRACKING:
            summary = self.get_usage_summary()
            if summary["total_cost_usd"] >= self.settings.COST_ALERT_THRESHOLD:
                self.logger.warning(
                    "Cost threshold exceeded",
                    total_cost=summary["total_cost_usd"],
                    threshold=self.settings.COST_ALERT_THRESHOLD,
                )
                return True
        return False
