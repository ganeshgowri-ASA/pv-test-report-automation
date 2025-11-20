"""
OpenAI GPT Integration Module

Provides async integration with OpenAI's GPT models for report analysis,
including prompt templates, response parsing, and error handling.
"""

import asyncio
import hashlib
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import time

try:
    from openai import AsyncOpenAI, OpenAI
    from openai.types.chat import ChatCompletion
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI library not installed. Install with: pip install openai")

from .llm_config import (
    get_config, LLMConfig, ModelType, LLMProvider, RateLimitConfig
)

logger = logging.getLogger(__name__)


@dataclass
class GPTResponse:
    """Structured response from GPT."""
    content: str
    model: str
    tokens_input: int
    tokens_output: int
    cost: float
    cached: bool = False
    finish_reason: str = "stop"
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PromptTemplate:
    """Prompt template manager."""

    SYSTEM_PROMPTS = {
        'report_analysis': """You are an expert PV (Photovoltaic) test report analyst.
Your role is to analyze solar panel test reports, extract key information, identify issues,
and provide technical insights. Focus on accuracy, technical correctness, and actionable findings.""",

        'compliance_check': """You are a compliance specialist for PV testing standards.
Your role is to verify test reports against international standards (IEC 61215, IEC 61730, etc.),
identify gaps, and provide detailed compliance assessments.""",

        'data_extraction': """You are a precise data extraction specialist.
Extract structured data from PV test reports accurately, maintaining data types and units.
When uncertain, indicate the uncertainty level.""",

        'summary_generation': """You are a technical writer specializing in PV systems.
Create clear, concise summaries of test reports for different audiences (technical, executive, regulatory)."""
    }

    @staticmethod
    def format_report_analysis(report_data: Dict[str, Any]) -> str:
        """Format prompt for report analysis."""
        return f"""Analyze the following PV test report and provide:
1. Key findings and test results
2. Any anomalies or issues detected
3. Performance assessment
4. Recommendations

Report Data:
{json.dumps(report_data, indent=2)}

Provide a structured analysis."""

    @staticmethod
    def format_compliance_check(
        report_data: Dict[str, Any],
        standards: List[str]
    ) -> str:
        """Format prompt for compliance checking."""
        standards_list = "\n".join(f"- {std}" for std in standards)
        return f"""Check the following PV test report for compliance with these standards:
{standards_list}

Report Data:
{json.dumps(report_data, indent=2)}

For each standard, indicate:
1. Compliance status (compliant/non-compliant/partial)
2. Specific requirements met or missed
3. Required corrections if any"""

    @staticmethod
    def format_data_extraction(
        text: str,
        schema: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format prompt for data extraction."""
        schema_info = ""
        if schema:
            schema_info = f"\n\nExpected schema:\n{json.dumps(schema, indent=2)}"

        return f"""Extract structured data from the following PV test report text.
Return data as valid JSON matching the expected schema.{schema_info}

Text:
{text}

Extracted Data (JSON):"""

    @staticmethod
    def format_summary(
        report_data: Dict[str, Any],
        audience: str = "technical",
        max_length: int = 500
    ) -> str:
        """Format prompt for summary generation."""
        return f"""Create a {audience} summary (max {max_length} words) of this PV test report:

{json.dumps(report_data, indent=2)}

The summary should be appropriate for a {audience} audience."""


class GPTIntegration:
    """OpenAI GPT integration for PV report analysis."""

    def __init__(
        self,
        config: Optional[LLMConfig] = None,
        model_type: ModelType = ModelType.GPT_4_TURBO,
        enable_cache: bool = True
    ):
        """
        Initialize GPT integration.

        Args:
            config: LLM configuration instance
            model_type: Model to use (GPT-4 Turbo, GPT-4, or GPT-3.5)
            enable_cache: Enable response caching
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed")

        self.config = config or get_config()
        self.model_type = model_type
        self.model_config = self.config.get_model_config(model_type)
        self.enable_cache = enable_cache

        # Get API key
        api_key = self.config.get_api_key(LLMProvider.OPENAI)
        if not api_key:
            raise ValueError("OpenAI API key not configured")

        # Initialize clients
        self.client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)

        # Rate limiter
        self.rate_limiter = self.config.rate_limiters[LLMProvider.OPENAI]

        # Cache
        self.cache_dir = self.config.cache_dir / "gpt"
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_key(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate cache key for a request."""
        cache_data = {
            'model': self.model_config.name,
            'messages': messages,
            **kwargs
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()

    def _get_cached_response(self, cache_key: str) -> Optional[GPTResponse]:
        """Get cached response if available and not expired."""
        if not self.enable_cache:
            return None

        cache_file = self.cache_dir / f"{cache_key}.json"
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)

            # Check expiration
            cached_time = datetime.fromisoformat(cached_data['timestamp'])
            if datetime.now() - cached_time > self.config.cache_ttl:
                cache_file.unlink()  # Delete expired cache
                return None

            # Reconstruct response
            response = GPTResponse(
                content=cached_data['content'],
                model=cached_data['model'],
                tokens_input=cached_data['tokens_input'],
                tokens_output=cached_data['tokens_output'],
                cost=cached_data['cost'],
                cached=True,
                finish_reason=cached_data.get('finish_reason', 'stop'),
                metadata=cached_data.get('metadata', {})
            )

            logger.info(f"Cache hit for key {cache_key[:8]}...")
            return response

        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return None

    def _save_to_cache(self, cache_key: str, response: GPTResponse):
        """Save response to cache."""
        if not self.enable_cache:
            return

        cache_file = self.cache_dir / f"{cache_key}.json"
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'content': response.content,
            'model': response.model,
            'tokens_input': response.tokens_input,
            'tokens_output': response.tokens_output,
            'cost': response.cost,
            'finish_reason': response.finish_reason,
            'metadata': response.metadata
        }

        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for token usage."""
        input_cost = (input_tokens / 1000) * self.model_config.cost_per_1k_input
        output_cost = (output_tokens / 1000) * self.model_config.cost_per_1k_output
        return input_cost + output_cost

    def _wait_for_rate_limit(self, estimated_tokens: int = 0):
        """Wait if rate limit is reached."""
        allowed, wait_time = self.rate_limiter.check_rate_limit(estimated_tokens)
        if not allowed and wait_time:
            logger.info(f"Rate limit reached, waiting {wait_time:.1f}s...")
            time.sleep(wait_time)

    async def _wait_for_rate_limit_async(self, estimated_tokens: int = 0):
        """Async version of rate limit wait."""
        allowed, wait_time = self.rate_limiter.check_rate_limit(estimated_tokens)
        if not allowed and wait_time:
            logger.info(f"Rate limit reached, waiting {wait_time:.1f}s...")
            await asyncio.sleep(wait_time)

    def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> GPTResponse:
        """
        Synchronous completion request.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional OpenAI API parameters

        Returns:
            GPTResponse object
        """
        # Check cache
        cache_key = self._get_cache_key(messages, temperature=temperature, **kwargs)
        if cached := self._get_cached_response(cache_key):
            self.config.track_usage(
                self.model_config.name,
                cached.tokens_input,
                cached.tokens_output,
                cached.cost,
                cache_hit=True
            )
            return cached

        # Wait for rate limit
        self._wait_for_rate_limit()

        # Make request
        try:
            completion = self.client.chat.completions.create(
                model=self.model_config.name,
                messages=messages,
                temperature=temperature or self.model_config.temperature_default,
                max_tokens=max_tokens or self.model_config.max_tokens,
                **kwargs
            )

            # Parse response
            response = self._parse_completion(completion)

            # Track usage
            self.config.track_usage(
                self.model_config.name,
                response.tokens_input,
                response.tokens_output,
                response.cost,
                cache_hit=False
            )

            # Record rate limit
            total_tokens = response.tokens_input + response.tokens_output
            self.rate_limiter.record_request(total_tokens)

            # Cache response
            self._save_to_cache(cache_key, response)

            return response

        except Exception as e:
            logger.error(f"GPT completion failed: {e}")
            self.config.track_usage(
                self.model_config.name, 0, 0, 0, error=True
            )
            raise

    async def complete_async(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> GPTResponse:
        """
        Async completion request.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional OpenAI API parameters

        Returns:
            GPTResponse object
        """
        # Check cache
        cache_key = self._get_cache_key(messages, temperature=temperature, **kwargs)
        if cached := self._get_cached_response(cache_key):
            self.config.track_usage(
                self.model_config.name,
                cached.tokens_input,
                cached.tokens_output,
                cached.cost,
                cache_hit=True
            )
            return cached

        # Wait for rate limit
        await self._wait_for_rate_limit_async()

        # Make request with retries
        max_retries = self.rate_limiter.config.max_retries
        retry_delay = self.rate_limiter.config.retry_delay

        for attempt in range(max_retries):
            try:
                completion = await self.async_client.chat.completions.create(
                    model=self.model_config.name,
                    messages=messages,
                    temperature=temperature or self.model_config.temperature_default,
                    max_tokens=max_tokens or self.model_config.max_tokens,
                    **kwargs
                )

                # Parse response
                response = self._parse_completion(completion)

                # Track usage
                self.config.track_usage(
                    self.model_config.name,
                    response.tokens_input,
                    response.tokens_output,
                    response.cost,
                    cache_hit=False
                )

                # Record rate limit
                total_tokens = response.tokens_input + response.tokens_output
                self.rate_limiter.record_request(total_tokens)

                # Cache response
                self._save_to_cache(cache_key, response)

                return response

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt) if self.rate_limiter.config.exponential_backoff else retry_delay
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All retry attempts failed: {e}")
                    self.config.track_usage(
                        self.model_config.name, 0, 0, 0, error=True
                    )
                    raise

    def _parse_completion(self, completion: 'ChatCompletion') -> GPTResponse:
        """Parse OpenAI completion response."""
        message = completion.choices[0].message
        usage = completion.usage

        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens
        cost = self._calculate_cost(input_tokens, output_tokens)

        return GPTResponse(
            content=message.content,
            model=completion.model,
            tokens_input=input_tokens,
            tokens_output=output_tokens,
            cost=cost,
            finish_reason=completion.choices[0].finish_reason,
            metadata={
                'id': completion.id,
                'created': completion.created,
                'system_fingerprint': getattr(completion, 'system_fingerprint', None)
            }
        )

    def analyze_report(
        self,
        report_data: Dict[str, Any],
        system_prompt: Optional[str] = None
    ) -> GPTResponse:
        """
        Analyze a PV test report.

        Args:
            report_data: Report data dictionary
            system_prompt: Custom system prompt (optional)

        Returns:
            GPTResponse with analysis
        """
        messages = [
            {
                "role": "system",
                "content": system_prompt or PromptTemplate.SYSTEM_PROMPTS['report_analysis']
            },
            {
                "role": "user",
                "content": PromptTemplate.format_report_analysis(report_data)
            }
        ]

        return self.complete(messages)

    async def analyze_report_async(
        self,
        report_data: Dict[str, Any],
        system_prompt: Optional[str] = None
    ) -> GPTResponse:
        """Async version of analyze_report."""
        messages = [
            {
                "role": "system",
                "content": system_prompt or PromptTemplate.SYSTEM_PROMPTS['report_analysis']
            },
            {
                "role": "user",
                "content": PromptTemplate.format_report_analysis(report_data)
            }
        ]

        return await self.complete_async(messages)

    def extract_data(
        self,
        text: str,
        schema: Optional[Dict[str, Any]] = None,
        response_format: str = "json_object"
    ) -> GPTResponse:
        """
        Extract structured data from text.

        Args:
            text: Input text
            schema: Expected data schema
            response_format: Response format (json_object or text)

        Returns:
            GPTResponse with extracted data
        """
        messages = [
            {
                "role": "system",
                "content": PromptTemplate.SYSTEM_PROMPTS['data_extraction']
            },
            {
                "role": "user",
                "content": PromptTemplate.format_data_extraction(text, schema)
            }
        ]

        kwargs = {}
        if response_format == "json_object":
            kwargs["response_format"] = {"type": "json_object"}

        return self.complete(messages, **kwargs)

    async def extract_data_async(
        self,
        text: str,
        schema: Optional[Dict[str, Any]] = None,
        response_format: str = "json_object"
    ) -> GPTResponse:
        """Async version of extract_data."""
        messages = [
            {
                "role": "system",
                "content": PromptTemplate.SYSTEM_PROMPTS['data_extraction']
            },
            {
                "role": "user",
                "content": PromptTemplate.format_data_extraction(text, schema)
            }
        ]

        kwargs = {}
        if response_format == "json_object":
            kwargs["response_format"] = {"type": "json_object"}

        return await self.complete_async(messages, **kwargs)

    async def batch_analyze(
        self,
        reports: List[Dict[str, Any]],
        system_prompt: Optional[str] = None
    ) -> List[GPTResponse]:
        """
        Analyze multiple reports concurrently.

        Args:
            reports: List of report data dictionaries
            system_prompt: Custom system prompt

        Returns:
            List of GPTResponse objects
        """
        tasks = [
            self.analyze_report_async(report, system_prompt)
            for report in reports
        ]
        return await asyncio.gather(*tasks)
