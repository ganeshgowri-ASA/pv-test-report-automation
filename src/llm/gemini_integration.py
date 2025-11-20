"""
Google Gemini Integration Module

Provides async integration with Google's Gemini models for multi-modal analysis,
including text, images, and chart interpretation.
"""

import asyncio
import hashlib
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import base64
import time

try:
    import google.generativeai as genai
    from google.generativeai.types import GenerateContentResponse
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Google GenerativeAI library not installed. Install with: pip install google-generativeai")

from .llm_config import (
    get_config, LLMConfig, ModelType, LLMProvider
)

logger = logging.getLogger(__name__)


@dataclass
class GeminiResponse:
    """Structured response from Gemini."""
    content: str
    model: str
    tokens_input: int
    tokens_output: int
    cost: float
    cached: bool = False
    safety_ratings: List[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.safety_ratings is None:
            self.safety_ratings = []
        if self.metadata is None:
            self.metadata = {}


class ImageData:
    """Wrapper for image data."""

    def __init__(self, data: Union[bytes, str, Path], mime_type: str = "image/png"):
        """
        Initialize image data.

        Args:
            data: Image data (bytes, base64 string, or file path)
            mime_type: MIME type of the image
        """
        self.mime_type = mime_type

        if isinstance(data, Path):
            with open(data, 'rb') as f:
                self.data = f.read()
        elif isinstance(data, str):
            # Assume base64 encoded
            self.data = base64.b64decode(data)
        else:
            self.data = data

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Gemini API format."""
        return {
            'mime_type': self.mime_type,
            'data': base64.b64encode(self.data).decode('utf-8')
        }


class GeminiPromptTemplate:
    """Prompt templates for Gemini."""

    @staticmethod
    def format_chart_analysis(chart_description: str = "") -> str:
        """Format prompt for chart analysis."""
        return f"""Analyze the provided chart/graph from a PV test report.

{chart_description}

Provide:
1. Type of chart and what it represents
2. Key data points and trends
3. Notable patterns or anomalies
4. Technical interpretation
5. Any concerns or recommendations

Be specific with numerical values where visible."""

    @staticmethod
    def format_image_text_extraction() -> str:
        """Format prompt for text extraction from images."""
        return """Extract all visible text from this image, including:
- Tables and their data
- Labels and legends
- Numerical values
- Any annotations

Preserve the structure and formatting as much as possible.
Return as structured data (JSON format)."""

    @staticmethod
    def format_comparative_analysis(
        num_items: int,
        analysis_type: str = "reports"
    ) -> str:
        """Format prompt for comparative analysis."""
        return f"""Compare the {num_items} {analysis_type} provided.

For each comparison:
1. Identify similarities and differences
2. Highlight performance variations
3. Note any outliers or unusual patterns
4. Provide recommendations based on the comparison

Present findings in a structured format."""

    @staticmethod
    def format_multimodal_analysis() -> str:
        """Format prompt for multi-modal analysis (text + images)."""
        return """Analyze both the text data and images provided from this PV test report.

Provide a comprehensive analysis that:
1. Correlates information from text and images
2. Identifies discrepancies between visual and textual data
3. Extracts all relevant technical parameters
4. Provides quality assessment
5. Highlights any concerns

Ensure all findings are backed by specific references to the data."""


class GeminiIntegration:
    """Google Gemini integration for multi-modal PV report analysis."""

    def __init__(
        self,
        config: Optional[LLMConfig] = None,
        model_type: ModelType = ModelType.GEMINI_15_PRO,
        enable_cache: bool = True
    ):
        """
        Initialize Gemini integration.

        Args:
            config: LLM configuration instance
            model_type: Model to use (Gemini Pro or Gemini Pro Vision)
            enable_cache: Enable response caching
        """
        if not GEMINI_AVAILABLE:
            raise ImportError("Google GenerativeAI library not installed")

        self.config = config or get_config()
        self.model_type = model_type
        self.model_config = self.config.get_model_config(model_type)
        self.enable_cache = enable_cache

        # Get API key
        api_key = self.config.get_api_key(LLMProvider.GEMINI)
        if not api_key:
            raise ValueError("Google API key not configured")

        # Configure Gemini
        genai.configure(api_key=api_key)

        # Initialize model
        self.model = genai.GenerativeModel(self.model_config.name)

        # Rate limiter
        self.rate_limiter = self.config.rate_limiters[LLMProvider.GEMINI]

        # Cache
        self.cache_dir = self.config.cache_dir / "gemini"
        self.cache_dir.mkdir(exist_ok=True)

        # Safety settings (permissive for technical content)
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            },
        ]

    def _get_cache_key(
        self,
        prompt: str,
        images: Optional[List[ImageData]] = None,
        **kwargs
    ) -> str:
        """Generate cache key for a request."""
        cache_data = {
            'model': self.model_config.name,
            'prompt': prompt,
            **kwargs
        }

        # Include image hashes if present
        if images:
            image_hashes = [
                hashlib.md5(img.data).hexdigest()
                for img in images
            ]
            cache_data['images'] = image_hashes

        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()

    def _get_cached_response(self, cache_key: str) -> Optional[GeminiResponse]:
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
                cache_file.unlink()
                return None

            response = GeminiResponse(
                content=cached_data['content'],
                model=cached_data['model'],
                tokens_input=cached_data['tokens_input'],
                tokens_output=cached_data['tokens_output'],
                cost=cached_data['cost'],
                cached=True,
                safety_ratings=cached_data.get('safety_ratings', []),
                metadata=cached_data.get('metadata', {})
            )

            logger.info(f"Cache hit for key {cache_key[:8]}...")
            return response

        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return None

    def _save_to_cache(self, cache_key: str, response: GeminiResponse):
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
            'safety_ratings': response.safety_ratings,
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

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        # Rough estimation: ~4 characters per token
        return len(text) // 4

    async def _wait_for_rate_limit_async(self, estimated_tokens: int = 0):
        """Wait if rate limit is reached."""
        allowed, wait_time = self.rate_limiter.check_rate_limit(estimated_tokens)
        if not allowed and wait_time:
            logger.info(f"Rate limit reached, waiting {wait_time:.1f}s...")
            await asyncio.sleep(wait_time)

    def generate(
        self,
        prompt: str,
        images: Optional[List[Union[ImageData, Path]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> GeminiResponse:
        """
        Synchronous content generation.

        Args:
            prompt: Text prompt
            images: Optional list of images
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional generation parameters

        Returns:
            GeminiResponse object
        """
        # Convert image paths to ImageData
        if images:
            images = [
                img if isinstance(img, ImageData) else ImageData(img)
                for img in images
            ]

        # Check cache
        cache_key = self._get_cache_key(prompt, images, temperature=temperature)
        if cached := self._get_cached_response(cache_key):
            self.config.track_usage(
                self.model_config.name,
                cached.tokens_input,
                cached.tokens_output,
                cached.cost,
                cache_hit=True
            )
            return cached

        # Prepare content
        content = [prompt]
        if images:
            for img in images:
                content.append(img.to_dict())

        # Generate
        try:
            generation_config = {
                'temperature': temperature,
                'max_output_tokens': max_tokens or self.model_config.max_tokens,
                **kwargs
            }

            response = self.model.generate_content(
                content,
                generation_config=generation_config,
                safety_settings=self.safety_settings
            )

            # Parse response
            parsed_response = self._parse_response(response, prompt, images)

            # Track usage
            self.config.track_usage(
                self.model_config.name,
                parsed_response.tokens_input,
                parsed_response.tokens_output,
                parsed_response.cost,
                cache_hit=False
            )

            # Record rate limit
            total_tokens = parsed_response.tokens_input + parsed_response.tokens_output
            self.rate_limiter.record_request(total_tokens)

            # Cache response
            self._save_to_cache(cache_key, parsed_response)

            return parsed_response

        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            self.config.track_usage(
                self.model_config.name, 0, 0, 0, error=True
            )
            raise

    async def generate_async(
        self,
        prompt: str,
        images: Optional[List[Union[ImageData, Path]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> GeminiResponse:
        """
        Async content generation.

        Args:
            prompt: Text prompt
            images: Optional list of images
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional generation parameters

        Returns:
            GeminiResponse object
        """
        # Convert image paths to ImageData
        if images:
            images = [
                img if isinstance(img, ImageData) else ImageData(img)
                for img in images
            ]

        # Check cache
        cache_key = self._get_cache_key(prompt, images, temperature=temperature)
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
        estimated_tokens = self._estimate_tokens(prompt)
        await self._wait_for_rate_limit_async(estimated_tokens)

        # Prepare content
        content = [prompt]
        if images:
            for img in images:
                content.append(img.to_dict())

        # Generate with retries
        max_retries = self.rate_limiter.config.max_retries
        retry_delay = self.rate_limiter.config.retry_delay

        for attempt in range(max_retries):
            try:
                generation_config = {
                    'temperature': temperature,
                    'max_output_tokens': max_tokens or self.model_config.max_tokens,
                    **kwargs
                }

                response = await asyncio.to_thread(
                    self.model.generate_content,
                    content,
                    generation_config=generation_config,
                    safety_settings=self.safety_settings
                )

                # Parse response
                parsed_response = self._parse_response(response, prompt, images)

                # Track usage
                self.config.track_usage(
                    self.model_config.name,
                    parsed_response.tokens_input,
                    parsed_response.tokens_output,
                    parsed_response.cost,
                    cache_hit=False
                )

                # Record rate limit
                total_tokens = parsed_response.tokens_input + parsed_response.tokens_output
                self.rate_limiter.record_request(total_tokens)

                # Cache response
                self._save_to_cache(cache_key, parsed_response)

                return parsed_response

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

    def _parse_response(
        self,
        response: GenerateContentResponse,
        prompt: str,
        images: Optional[List[ImageData]] = None
    ) -> GeminiResponse:
        """Parse Gemini response."""
        # Extract text
        text = response.text if hasattr(response, 'text') else ""

        # Estimate tokens (Gemini doesn't always return token counts)
        input_tokens = self._estimate_tokens(prompt)
        if images:
            # Estimate ~258 tokens per image
            input_tokens += len(images) * 258

        output_tokens = self._estimate_tokens(text)

        # Calculate cost
        cost = self._calculate_cost(input_tokens, output_tokens)

        # Extract safety ratings
        safety_ratings = []
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'safety_ratings'):
                safety_ratings = [
                    {
                        'category': rating.category.name,
                        'probability': rating.probability.name
                    }
                    for rating in candidate.safety_ratings
                ]

        return GeminiResponse(
            content=text,
            model=self.model_config.name,
            tokens_input=input_tokens,
            tokens_output=output_tokens,
            cost=cost,
            safety_ratings=safety_ratings,
            metadata={
                'prompt_feedback': getattr(response, 'prompt_feedback', None)
            }
        )

    async def analyze_chart(
        self,
        chart_image: Union[ImageData, Path],
        context: str = ""
    ) -> GeminiResponse:
        """
        Analyze a chart/graph from a test report.

        Args:
            chart_image: Chart image data or path
            context: Additional context about the chart

        Returns:
            GeminiResponse with chart analysis
        """
        prompt = GeminiPromptTemplate.format_chart_analysis(context)
        return await self.generate_async(prompt, images=[chart_image])

    async def extract_image_text(
        self,
        image: Union[ImageData, Path]
    ) -> GeminiResponse:
        """
        Extract text from an image.

        Args:
            image: Image data or path

        Returns:
            GeminiResponse with extracted text
        """
        prompt = GeminiPromptTemplate.format_image_text_extraction()
        return await self.generate_async(prompt, images=[image])

    async def multimodal_analysis(
        self,
        text_data: str,
        images: List[Union[ImageData, Path]],
        custom_prompt: Optional[str] = None
    ) -> GeminiResponse:
        """
        Perform multi-modal analysis on text and images.

        Args:
            text_data: Text data from report
            images: List of images from report
            custom_prompt: Custom analysis prompt

        Returns:
            GeminiResponse with comprehensive analysis
        """
        base_prompt = custom_prompt or GeminiPromptTemplate.format_multimodal_analysis()
        full_prompt = f"{base_prompt}\n\nText Data:\n{text_data}"

        return await self.generate_async(full_prompt, images=images)

    async def comparative_analysis(
        self,
        items: List[Dict[str, Any]],
        analysis_type: str = "reports"
    ) -> GeminiResponse:
        """
        Compare multiple items (reports, charts, etc.).

        Args:
            items: List of items to compare (each can have text and images)
            analysis_type: Type of items being compared

        Returns:
            GeminiResponse with comparative analysis
        """
        prompt = GeminiPromptTemplate.format_comparative_analysis(
            len(items),
            analysis_type
        )

        # Combine all text and images
        combined_text = prompt + "\n\n"
        all_images = []

        for i, item in enumerate(items, 1):
            combined_text += f"\n## Item {i}:\n"
            if 'text' in item:
                combined_text += item['text'] + "\n"
            if 'images' in item:
                all_images.extend(item['images'])

        return await self.generate_async(combined_text, images=all_images if all_images else None)

    async def batch_analyze_charts(
        self,
        charts: List[Union[ImageData, Path]],
        contexts: Optional[List[str]] = None
    ) -> List[GeminiResponse]:
        """
        Analyze multiple charts concurrently.

        Args:
            charts: List of chart images
            contexts: Optional list of contexts for each chart

        Returns:
            List of GeminiResponse objects
        """
        if contexts is None:
            contexts = [""] * len(charts)

        tasks = [
            self.analyze_chart(chart, context)
            for chart, context in zip(charts, contexts)
        ]
        return await asyncio.gather(*tasks)
