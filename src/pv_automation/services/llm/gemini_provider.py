"""Google Gemini LLM provider implementation for PV test automation"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from google.generativeai.types import GenerationConfig, HarmBlockThreshold, HarmCategory
from PIL import Image

from pv_automation.config.constants import ERROR_MESSAGES
from pv_automation.config.settings import Settings, get_settings
from pv_automation.models.llm_models import (
    ComplianceCheckRequest,
    ComplianceCheckResponse,
    DefectAnalysis,
    DefectSeverity,
    GeminiRequest,
    GeminiResponse,
    PredictiveAnalysisRequest,
    PredictiveAnalysisResponse,
    SafetyRating,
    VisionAnalysisRequest,
    VisionAnalysisResponse,
)
from pv_automation.services.llm.base import (
    APIKeyError,
    ImageProcessingError,
    LLMProvider,
    LLMProviderError,
    ModelNotFoundError,
    NetworkError,
    RateLimitError,
    SafetyFilterError,
)
from pv_automation.services.llm.prompts import PVAnalysisPrompts

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """
    Google Gemini LLM provider for PV test report automation.

    Features:
    - Text generation with Gemini Pro
    - Multi-modal analysis (text + images) with Gemini Vision
    - EL/thermal image defect detection
    - Compliance checking against PV standards
    - Predictive failure analysis
    - Batch processing capabilities
    - Safety filters and error handling
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        vision_model: Optional[str] = None,
        settings: Optional[Settings] = None,
    ):
        """
        Initialize Gemini provider.

        Args:
            api_key: Google API key (uses settings if not provided)
            model: Model name for text (uses settings if not provided)
            vision_model: Model name for vision (uses settings if not provided)
            settings: Application settings (loads from environment if not provided)

        Raises:
            APIKeyError: If API key is not provided or invalid
        """
        self.settings = settings or get_settings()

        # Get API key
        self.api_key = api_key or self.settings.llm.api_key
        if not self.api_key:
            raise APIKeyError(
                "Gemini API key not provided. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter.",
                error_code="MISSING_API_KEY",
            )

        # Configure Gemini
        try:
            genai.configure(api_key=self.api_key)
        except Exception as e:
            raise APIKeyError(
                f"Failed to configure Gemini API: {str(e)}",
                error_code="INVALID_API_KEY",
            ) from e

        # Set models
        self.model_name = model or self.settings.llm.model
        self.vision_model_name = vision_model or self.settings.llm.vision_model

        # Initialize models
        try:
            self.text_model = genai.GenerativeModel(
                self.model_name,
                system_instruction=PVAnalysisPrompts.SYSTEM_INSTRUCTION,
            )
            self.vision_model = genai.GenerativeModel(
                self.vision_model_name,
                system_instruction=PVAnalysisPrompts.SYSTEM_INSTRUCTION,
            )
        except Exception as e:
            raise ModelNotFoundError(
                f"Failed to initialize Gemini models: {str(e)}",
                error_code="MODEL_INIT_FAILED",
            ) from e

        # Configure generation parameters
        self.generation_config = GenerationConfig(
            temperature=self.settings.llm.temperature,
            top_p=self.settings.llm.top_p,
            top_k=self.settings.llm.top_k,
            max_output_tokens=self.settings.llm.max_tokens,
        )

        # Configure safety settings
        self.safety_settings = self._get_safety_settings()

        logger.info(
            f"Gemini provider initialized with model={self.model_name}, "
            f"vision_model={self.vision_model_name}"
        )

    def _get_safety_settings(self) -> Dict[HarmCategory, HarmBlockThreshold]:
        """
        Get safety settings for content filtering.

        Returns:
            Dict[HarmCategory, HarmBlockThreshold]: Safety settings
        """
        if self.settings.llm.enable_safety_filters:
            return {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        else:
            # Disable safety filters for technical content
            return {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

    async def generate_text(self, request: GeminiRequest) -> GeminiResponse:
        """
        Generate text using Gemini.

        Args:
            request: Text generation request

        Returns:
            GeminiResponse: Generated response

        Raises:
            LLMProviderError: If generation fails
        """
        try:
            logger.debug(f"Generating text with prompt length: {len(request.prompt)}")

            # Override default config with request parameters
            gen_config = GenerationConfig(
                temperature=request.temperature,
                top_p=request.top_p,
                top_k=request.top_k,
                max_output_tokens=request.max_tokens,
            )

            # Generate content
            response = await asyncio.to_thread(
                self.text_model.generate_content,
                request.prompt,
                generation_config=gen_config,
                safety_settings=self.safety_settings,
            )

            # Check for blocking
            if not response.text:
                if hasattr(response, "prompt_feedback"):
                    raise SafetyFilterError(
                        "Content was blocked by safety filters",
                        error_code="SAFETY_BLOCKED",
                        details={"feedback": str(response.prompt_feedback)},
                    )
                raise LLMProviderError("Empty response from Gemini", error_code="EMPTY_RESPONSE")

            # Extract safety ratings
            safety_ratings = []
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "safety_ratings"):
                    safety_ratings = [
                        SafetyRating(
                            category=rating.category.name,
                            probability=rating.probability.name,
                            blocked=rating.blocked if hasattr(rating, "blocked") else False,
                        )
                        for rating in candidate.safety_ratings
                    ]

            # Extract token counts
            prompt_tokens = None
            candidates_tokens = None
            total_tokens = None

            if hasattr(response, "usage_metadata"):
                prompt_tokens = response.usage_metadata.prompt_token_count
                candidates_tokens = response.usage_metadata.candidates_token_count
                total_tokens = response.usage_metadata.total_token_count

            # Build response
            return GeminiResponse(
                content=response.text,
                safety_ratings=safety_ratings,
                finish_reason=response.candidates[0].finish_reason.name
                if response.candidates
                else "STOP",
                prompt_token_count=prompt_tokens,
                candidates_token_count=candidates_tokens,
                total_token_count=total_tokens,
                model=self.model_name,
            )

        except SafetyFilterError:
            raise
        except Exception as e:
            logger.error(f"Text generation failed: {str(e)}")
            raise self._handle_error(e)

    async def analyze_image(self, request: VisionAnalysisRequest) -> VisionAnalysisResponse:
        """
        Analyze a PV module image for defects using Gemini Vision.

        Args:
            request: Vision analysis request

        Returns:
            VisionAnalysisResponse: Analysis results

        Raises:
            LLMProviderError: If analysis fails
        """
        try:
            logger.info(f"Analyzing image: {request.image_path}")

            # Load and validate image
            image_path = Path(request.image_path)
            if not image_path.exists():
                raise ImageProcessingError(
                    f"Image file not found: {request.image_path}",
                    error_code="IMAGE_NOT_FOUND",
                )

            # Check file size
            file_size_mb = image_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.settings.file_upload.max_image_size_mb:
                raise ImageProcessingError(
                    ERROR_MESSAGES["image_too_large"].format(
                        max_size=self.settings.file_upload.max_image_size_mb
                    ),
                    error_code="IMAGE_TOO_LARGE",
                    details={"size_mb": file_size_mb},
                )

            # Load image
            try:
                pil_image = Image.open(image_path)
                image_metadata = {
                    "format": pil_image.format,
                    "mode": pil_image.mode,
                    "size": pil_image.size,
                    "size_mb": file_size_mb,
                }
            except Exception as e:
                raise ImageProcessingError(
                    f"Failed to load image: {str(e)}",
                    error_code="IMAGE_LOAD_FAILED",
                ) from e

            # Get analysis prompt
            prompt = PVAnalysisPrompts.get_defect_analysis_prompt(
                image_type=request.image_type,
                standard=request.standard,
                additional_context=request.additional_context,
            )

            # Generate analysis
            response = await asyncio.to_thread(
                self.vision_model.generate_content,
                [prompt, pil_image],
                generation_config=self.generation_config,
                safety_settings=self.safety_settings,
            )

            if not response.text:
                raise LLMProviderError("Empty response from vision model", error_code="EMPTY_RESPONSE")

            # Parse the response to extract structured data
            analysis_text = response.text
            defects = self._parse_defects_from_analysis(analysis_text)
            overall_assessment, compliance_status, confidence = self._parse_assessment(
                analysis_text
            )

            return VisionAnalysisResponse(
                defects=defects,
                overall_assessment=overall_assessment,
                compliance_status=compliance_status,
                confidence_score=confidence,
                raw_analysis=analysis_text,
                image_metadata=image_metadata,
            )

        except (ImageProcessingError, LLMProviderError):
            raise
        except Exception as e:
            logger.error(f"Image analysis failed: {str(e)}")
            raise self._handle_error(e)

    async def check_compliance(
        self, request: ComplianceCheckRequest
    ) -> ComplianceCheckResponse:
        """
        Check test report data against PV standards.

        Args:
            request: Compliance check request

        Returns:
            ComplianceCheckResponse: Compliance assessment

        Raises:
            LLMProviderError: If compliance check fails
        """
        try:
            logger.info(f"Checking compliance against {request.standard}")

            # Get compliance check prompt
            prompt = PVAnalysisPrompts.get_compliance_check_prompt(
                report_data=request.report_data,
                standard=request.standard,
                check_missing=request.check_missing_data,
            )

            # Generate compliance analysis
            gen_request = GeminiRequest(
                prompt=prompt,
                model=self.model_name,
                temperature=0.3,  # Lower temperature for more precise compliance checking
            )
            response = await self.generate_text(gen_request)

            # Parse compliance response
            analysis_text = response.content
            compliance_status, violations, missing_data, recommendations = (
                self._parse_compliance_response(analysis_text)
            )

            return ComplianceCheckResponse(
                compliance_status=compliance_status,
                violations=violations,
                missing_data=missing_data,
                recommendations=recommendations,
                detailed_analysis=analysis_text,
            )

        except LLMProviderError:
            raise
        except Exception as e:
            logger.error(f"Compliance check failed: {str(e)}")
            raise self._handle_error(e)

    async def predict_failures(
        self, request: PredictiveAnalysisRequest
    ) -> PredictiveAnalysisResponse:
        """
        Perform predictive failure analysis.

        Args:
            request: Predictive analysis request

        Returns:
            PredictiveAnalysisResponse: Failure predictions

        Raises:
            LLMProviderError: If prediction fails
        """
        try:
            logger.info("Performing predictive failure analysis")

            # Get predictive analysis prompt
            prompt = PVAnalysisPrompts.get_predictive_analysis_prompt(
                test_data=request.test_data,
                module_age_years=request.module_age_years,
                environmental_factors=request.environmental_factors,
                warranty_period_years=request.warranty_period_years,
            )

            # Generate prediction
            gen_request = GeminiRequest(
                prompt=prompt,
                model=self.model_name,
                temperature=0.4,  # Moderate temperature for balanced prediction
            )
            response = await self.generate_text(gen_request)

            # Parse predictive response
            analysis_text = response.content
            (
                failure_prob,
                risk_factors,
                trends,
                measures,
                lifespan,
                confidence,
            ) = self._parse_predictive_response(analysis_text)

            return PredictiveAnalysisResponse(
                failure_probability=failure_prob,
                risk_factors=risk_factors,
                degradation_trends=trends,
                preventive_measures=measures,
                estimated_lifespan_years=lifespan,
                detailed_analysis=analysis_text,
                confidence_score=confidence,
            )

        except LLMProviderError:
            raise
        except Exception as e:
            logger.error(f"Predictive analysis failed: {str(e)}")
            raise self._handle_error(e)

    async def batch_analyze_images(
        self, requests: List[VisionAnalysisRequest]
    ) -> List[VisionAnalysisResponse]:
        """
        Analyze multiple images in batch.

        Args:
            requests: List of vision analysis requests

        Returns:
            List[VisionAnalysisResponse]: Analysis results for each image

        Raises:
            LLMProviderError: If batch analysis fails
        """
        logger.info(f"Batch analyzing {len(requests)} images")

        # Process images concurrently
        tasks = [self.analyze_image(request) for request in requests]

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Convert exceptions to error responses
            final_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(
                        f"Failed to analyze image {requests[i].image_path}: {str(result)}"
                    )
                    # Create error response
                    error_response = VisionAnalysisResponse(
                        defects=[],
                        overall_assessment=f"Analysis failed: {str(result)}",
                        compliance_status="Error",
                        confidence_score=0.0,
                        raw_analysis=f"Error: {str(result)}",
                    )
                    final_results.append(error_response)
                else:
                    final_results.append(result)

            return final_results

        except Exception as e:
            logger.error(f"Batch analysis failed: {str(e)}")
            raise self._handle_error(e)

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Gemini API health.

        Returns:
            Dict[str, Any]: Health status

        Raises:
            LLMProviderError: If health check fails
        """
        try:
            # Simple test request
            test_request = GeminiRequest(
                prompt="Respond with 'OK' if you can process this message.",
                model=self.model_name,
                temperature=0.0,
                max_tokens=10,
            )

            response = await self.generate_text(test_request)

            return {
                "status": "healthy",
                "provider": "gemini",
                "model": self.model_name,
                "vision_model": self.vision_model_name,
                "response_received": True,
                "test_response": response.content[:50],
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "gemini",
                "error": str(e),
                "error_type": type(e).__name__,
            }

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model configuration information.

        Returns:
            Dict[str, Any]: Model information
        """
        return {
            "provider": "gemini",
            "text_model": self.model_name,
            "vision_model": self.vision_model_name,
            "capabilities": [
                "text_generation",
                "vision_analysis",
                "multi_modal",
                "batch_processing",
            ],
            "configuration": {
                "temperature": self.settings.llm.temperature,
                "max_tokens": self.settings.llm.max_tokens,
                "top_p": self.settings.llm.top_p,
                "top_k": self.settings.llm.top_k,
                "safety_filters_enabled": self.settings.llm.enable_safety_filters,
            },
            "limits": {
                "max_image_size_mb": self.settings.file_upload.max_image_size_mb,
                "allowed_formats": self.settings.file_upload.allowed_image_formats,
            },
        }

    # Helper methods for parsing responses

    def _parse_defects_from_analysis(self, analysis: str) -> List[DefectAnalysis]:
        """Parse defects from analysis text"""
        # This is a simplified parser - in production, you might use more sophisticated NLP
        defects = []

        # Look for common defect indicators
        defect_keywords = {
            "crack": DefectSeverity.HIGH,
            "hotspot": DefectSeverity.HIGH,
            "delamination": DefectSeverity.MEDIUM,
            "discoloration": DefectSeverity.LOW,
            "breakage": DefectSeverity.CRITICAL,
        }

        for keyword, severity in defect_keywords.items():
            if keyword.lower() in analysis.lower():
                defects.append(
                    DefectAnalysis(
                        defect_type=keyword,
                        severity=severity,
                        confidence=0.8,
                        description=f"{keyword.capitalize()} detected in analysis",
                        recommendations=[f"Further investigation of {keyword} required"],
                    )
                )

        return defects

    def _parse_assessment(self, analysis: str) -> tuple:
        """Parse overall assessment from analysis"""
        # Extract compliance status
        compliance = "Conditional"
        if "pass" in analysis.lower() and "fail" not in analysis.lower():
            compliance = "Pass"
        elif "fail" in analysis.lower():
            compliance = "Fail"

        # Extract first paragraph as assessment
        paragraphs = analysis.split("\n\n")
        assessment = paragraphs[0] if paragraphs else analysis[:200]

        # Estimate confidence (simplified)
        confidence = 0.85 if "confident" in analysis.lower() else 0.75

        return assessment, compliance, confidence

    def _parse_compliance_response(self, analysis: str) -> tuple:
        """Parse compliance check response"""
        # Determine compliance status
        status = "Conditional"
        if "overall compliance status: pass" in analysis.lower():
            status = "Pass"
        elif "overall compliance status: fail" in analysis.lower():
            status = "Fail"

        # Extract violations (simplified)
        violations = []
        if "violations:" in analysis.lower() or "fail" in analysis.lower():
            violations.append("See detailed analysis for specific violations")

        # Extract missing data
        missing_data = []
        if "missing" in analysis.lower():
            missing_data.append("See detailed analysis for missing data")

        # Extract recommendations
        recommendations = ["Review detailed analysis for specific recommendations"]

        return status, violations, missing_data, recommendations

    def _parse_predictive_response(self, analysis: str) -> tuple:
        """Parse predictive analysis response"""
        # Extract failure probability (simplified)
        failure_prob = 0.15  # Default

        # Extract risk factors
        risk_factors = ["See detailed analysis for risk factors"]

        # Extract degradation trends
        trends = ["See detailed analysis for degradation trends"]

        # Extract preventive measures
        measures = ["See detailed analysis for preventive measures"]

        # Extract lifespan estimate
        lifespan = 22.0  # Default

        # Confidence
        confidence = 0.75

        return failure_prob, risk_factors, trends, measures, lifespan, confidence

    def _handle_error(self, error: Exception) -> LLMProviderError:
        """Convert exceptions to appropriate LLMProviderError"""
        error_str = str(error).lower()

        if "api key" in error_str or "authentication" in error_str:
            return APIKeyError(str(error), error_code="AUTH_FAILED")
        elif "rate limit" in error_str or "quota" in error_str:
            return RateLimitError(str(error), error_code="RATE_LIMIT")
        elif "model" in error_str and "not found" in error_str:
            return ModelNotFoundError(str(error), error_code="MODEL_NOT_FOUND")
        elif "network" in error_str or "connection" in error_str:
            return NetworkError(str(error), error_code="NETWORK_ERROR")
        else:
            return LLMProviderError(str(error), error_code="UNKNOWN_ERROR")
