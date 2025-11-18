"""Base LLM provider interface"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pv_automation.models.llm_models import (
    ComplianceCheckRequest,
    ComplianceCheckResponse,
    GeminiRequest,
    GeminiResponse,
    PredictiveAnalysisRequest,
    PredictiveAnalysisResponse,
    VisionAnalysisRequest,
    VisionAnalysisResponse,
)


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    This interface defines the contract that all LLM providers must implement
    for PV test report automation tasks.
    """

    @abstractmethod
    async def generate_text(self, request: GeminiRequest) -> GeminiResponse:
        """
        Generate text based on a prompt.

        Args:
            request: Text generation request

        Returns:
            GeminiResponse: Generated text response

        Raises:
            LLMProviderError: If generation fails
        """
        pass

    @abstractmethod
    async def analyze_image(self, request: VisionAnalysisRequest) -> VisionAnalysisResponse:
        """
        Analyze a PV module image for defects.

        Args:
            request: Vision analysis request with image path and context

        Returns:
            VisionAnalysisResponse: Analysis results with detected defects

        Raises:
            LLMProviderError: If analysis fails
        """
        pass

    @abstractmethod
    async def check_compliance(
        self, request: ComplianceCheckRequest
    ) -> ComplianceCheckResponse:
        """
        Check test report data against PV standards.

        Args:
            request: Compliance check request with report data and standard

        Returns:
            ComplianceCheckResponse: Compliance status and recommendations

        Raises:
            LLMProviderError: If compliance check fails
        """
        pass

    @abstractmethod
    async def predict_failures(
        self, request: PredictiveAnalysisRequest
    ) -> PredictiveAnalysisResponse:
        """
        Perform predictive failure analysis on test data.

        Args:
            request: Predictive analysis request with historical data

        Returns:
            PredictiveAnalysisResponse: Failure predictions and risk assessment

        Raises:
            LLMProviderError: If prediction fails
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if the LLM provider is available and healthy.

        Returns:
            Dict[str, Any]: Health check results including status and metadata

        Raises:
            LLMProviderError: If health check fails
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model configuration.

        Returns:
            Dict[str, Any]: Model information including name, capabilities, limits
        """
        pass


class LLMProviderError(Exception):
    """Base exception for LLM provider errors"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class APIKeyError(LLMProviderError):
    """Raised when API key is invalid or missing"""

    pass


class RateLimitError(LLMProviderError):
    """Raised when API rate limit is exceeded"""

    pass


class SafetyFilterError(LLMProviderError):
    """Raised when content is blocked by safety filters"""

    pass


class ModelNotFoundError(LLMProviderError):
    """Raised when requested model is not available"""

    pass


class ImageProcessingError(LLMProviderError):
    """Raised when image processing fails"""

    pass


class NetworkError(LLMProviderError):
    """Raised when network communication fails"""

    pass
