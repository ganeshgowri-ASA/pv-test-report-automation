"""Unit tests for Gemini provider"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from PIL import Image
import io

from pv_automation.services.llm.gemini_provider import GeminiProvider
from pv_automation.services.llm.base import (
    APIKeyError,
    LLMProviderError,
    ImageProcessingError,
    SafetyFilterError,
)
from pv_automation.models.llm_models import (
    GeminiRequest,
    VisionAnalysisRequest,
    ComplianceCheckRequest,
    PredictiveAnalysisRequest,
    DefectSeverity,
)
from pv_automation.config.settings import Settings, LLMConfig


@pytest.fixture
def mock_settings():
    """Create mock settings"""
    settings = Settings()
    settings.llm = LLMConfig(
        provider="gemini",
        api_key="test_api_key",
        model="gemini-2.0-flash-exp",
        vision_model="gemini-2.0-flash-exp",
        temperature=0.7,
        max_tokens=2048,
        enable_safety_filters=False,
    )
    return settings


@pytest.fixture
def mock_genai():
    """Mock google.generativeai module"""
    with patch("pv_automation.services.llm.gemini_provider.genai") as mock:
        # Mock configure
        mock.configure = MagicMock()

        # Mock GenerativeModel
        mock_model = MagicMock()
        mock.GenerativeModel = MagicMock(return_value=mock_model)

        yield mock


@pytest.fixture
def gemini_provider(mock_settings, mock_genai):
    """Create Gemini provider instance"""
    return GeminiProvider(api_key="test_api_key", settings=mock_settings)


class TestGeminiProviderInitialization:
    """Test Gemini provider initialization"""

    def test_init_with_api_key(self, mock_settings, mock_genai):
        """Test initialization with API key"""
        provider = GeminiProvider(api_key="test_key", settings=mock_settings)
        assert provider.api_key == "test_key"
        assert provider.model_name == "gemini-2.0-flash-exp"
        mock_genai.configure.assert_called_once_with(api_key="test_key")

    def test_init_without_api_key_raises_error(self, mock_settings, mock_genai):
        """Test initialization without API key raises error"""
        mock_settings.llm.api_key = None
        with pytest.raises(APIKeyError) as exc_info:
            GeminiProvider(settings=mock_settings)
        assert "API key not provided" in str(exc_info.value)

    def test_init_custom_models(self, mock_settings, mock_genai):
        """Test initialization with custom models"""
        provider = GeminiProvider(
            api_key="test_key",
            model="custom-model",
            vision_model="custom-vision-model",
            settings=mock_settings,
        )
        assert provider.model_name == "custom-model"
        assert provider.vision_model_name == "custom-vision-model"

    def test_get_model_info(self, gemini_provider):
        """Test get_model_info returns correct information"""
        info = gemini_provider.get_model_info()
        assert info["provider"] == "gemini"
        assert info["text_model"] == "gemini-2.0-flash-exp"
        assert info["vision_model"] == "gemini-2.0-flash-exp"
        assert "text_generation" in info["capabilities"]
        assert "vision_analysis" in info["capabilities"]


class TestTextGeneration:
    """Test text generation functionality"""

    @pytest.mark.asyncio
    async def test_generate_text_success(self, gemini_provider):
        """Test successful text generation"""
        # Mock response
        mock_response = MagicMock()
        mock_response.text = "This is a test response"
        mock_response.candidates = [
            MagicMock(
                finish_reason=MagicMock(name="STOP"),
                safety_ratings=[],
            )
        ]
        mock_response.usage_metadata = MagicMock(
            prompt_token_count=10,
            candidates_token_count=5,
            total_token_count=15,
        )

        gemini_provider.text_model.generate_content = MagicMock(return_value=mock_response)

        request = GeminiRequest(
            prompt="Test prompt",
            model="gemini-2.0-flash-exp",
            temperature=0.7,
        )

        response = await gemini_provider.generate_text(request)

        assert response.content == "This is a test response"
        assert response.finish_reason == "STOP"
        assert response.prompt_token_count == 10
        assert response.total_token_count == 15

    @pytest.mark.asyncio
    async def test_generate_text_empty_response_raises_error(self, gemini_provider):
        """Test empty response raises error"""
        mock_response = MagicMock()
        mock_response.text = ""
        mock_response.candidates = []

        gemini_provider.text_model.generate_content = MagicMock(return_value=mock_response)

        request = GeminiRequest(prompt="Test prompt")

        with pytest.raises(LLMProviderError) as exc_info:
            await gemini_provider.generate_text(request)
        assert "Empty response" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_text_with_safety_ratings(self, gemini_provider):
        """Test text generation with safety ratings"""
        # Mock safety rating
        mock_rating = MagicMock()
        mock_rating.category.name = "HARM_CATEGORY_HARASSMENT"
        mock_rating.probability.name = "LOW"
        mock_rating.blocked = False

        mock_candidate = MagicMock()
        mock_candidate.finish_reason.name = "STOP"
        mock_candidate.safety_ratings = [mock_rating]

        mock_response = MagicMock()
        mock_response.text = "Safe response"
        mock_response.candidates = [mock_candidate]
        mock_response.usage_metadata = MagicMock(
            prompt_token_count=10, candidates_token_count=5, total_token_count=15
        )

        gemini_provider.text_model.generate_content = MagicMock(return_value=mock_response)

        request = GeminiRequest(prompt="Test prompt")
        response = await gemini_provider.generate_text(request)

        assert len(response.safety_ratings) == 1
        assert response.safety_ratings[0].category == "HARM_CATEGORY_HARASSMENT"
        assert response.safety_ratings[0].probability == "LOW"


class TestVisionAnalysis:
    """Test vision analysis functionality"""

    @pytest.fixture
    def temp_image(self, tmp_path):
        """Create a temporary test image"""
        image_path = tmp_path / "test_image.png"
        # Create a small test image
        img = Image.new("RGB", (100, 100), color="red")
        img.save(image_path)
        return str(image_path)

    @pytest.mark.asyncio
    async def test_analyze_image_success(self, gemini_provider, temp_image):
        """Test successful image analysis"""
        mock_response = MagicMock()
        mock_response.text = """
        **Defect Identification:**
        1. Crack detected in cell B5 - High severity - 92% confidence
        2. Hotspot in cell C3 - Medium severity - 85% confidence

        **Overall Assessment:** Module shows signs of mechanical stress
        **Compliance Status:** Conditional Pass
        """

        gemini_provider.vision_model.generate_content = MagicMock(return_value=mock_response)

        request = VisionAnalysisRequest(
            image_path=temp_image,
            image_type="EL",
            standard="IEC 61215",
        )

        response = await gemini_provider.analyze_image(request)

        assert response.overall_assessment is not None
        assert response.compliance_status in ["Pass", "Fail", "Conditional"]
        assert response.raw_analysis == mock_response.text
        assert response.image_metadata is not None
        assert "format" in response.image_metadata

    @pytest.mark.asyncio
    async def test_analyze_image_file_not_found(self, gemini_provider):
        """Test image analysis with non-existent file"""
        request = VisionAnalysisRequest(
            image_path="/nonexistent/image.png",
            image_type="EL",
        )

        # The validator should catch this, but if it doesn't:
        with pytest.raises((ImageProcessingError, ValueError)):
            await gemini_provider.analyze_image(request)

    @pytest.mark.asyncio
    async def test_analyze_image_too_large(self, gemini_provider, tmp_path, mock_settings):
        """Test image analysis with oversized image"""
        # Create a large dummy file
        large_image_path = tmp_path / "large_image.png"

        # Create a small image first
        img = Image.new("RGB", (100, 100), color="blue")
        img.save(large_image_path)

        # Override file size check by mocking
        original_max_size = mock_settings.file_upload.max_image_size_mb
        mock_settings.file_upload.max_image_size_mb = 0.000001  # Very small limit

        request = VisionAnalysisRequest(
            image_path=str(large_image_path),
            image_type="EL",
        )

        with pytest.raises(ImageProcessingError) as exc_info:
            await gemini_provider.analyze_image(request)
        assert "exceeds maximum" in str(exc_info.value).lower()

        # Restore
        mock_settings.file_upload.max_image_size_mb = original_max_size


class TestComplianceChecking:
    """Test compliance checking functionality"""

    @pytest.mark.asyncio
    async def test_check_compliance_success(self, gemini_provider):
        """Test successful compliance check"""
        mock_response = MagicMock()
        mock_response.text = """
        **Overall Compliance Status: Pass**

        All IEC 61215 requirements have been met.

        **Missing Data:**
        - Thermal imaging data

        **Recommendations:**
        - Provide thermal imaging results for complete assessment
        """
        mock_response.candidates = [MagicMock(finish_reason=MagicMock(name="STOP"))]
        mock_response.usage_metadata = MagicMock(
            prompt_token_count=100, candidates_token_count=50, total_token_count=150
        )

        gemini_provider.text_model.generate_content = MagicMock(return_value=mock_response)

        request = ComplianceCheckRequest(
            report_data={"module_id": "PV-001", "power_output": 400},
            standard="IEC 61215",
        )

        response = await gemini_provider.check_compliance(request)

        assert response.compliance_status == "Pass"
        assert response.detailed_analysis is not None
        assert isinstance(response.violations, list)
        assert isinstance(response.missing_data, list)
        assert isinstance(response.recommendations, list)


class TestPredictiveAnalysis:
    """Test predictive analysis functionality"""

    @pytest.mark.asyncio
    async def test_predict_failures_success(self, gemini_provider):
        """Test successful predictive analysis"""
        mock_response = MagicMock()
        mock_response.text = """
        **Failure Probability:** 15%

        **Risk Factors:**
        - Above-average degradation rate
        - Hotspot detected in thermal imaging

        **Degradation Trends:**
        - Linear degradation at 0.5%/year

        **Preventive Measures:**
        - Regular thermal imaging
        - Clean modules quarterly

        **Estimated Lifespan:** 22.5 years
        """
        mock_response.candidates = [MagicMock(finish_reason=MagicMock(name="STOP"))]
        mock_response.usage_metadata = MagicMock(
            prompt_token_count=100, candidates_token_count=50, total_token_count=150
        )

        gemini_provider.text_model.generate_content = MagicMock(return_value=mock_response)

        request = PredictiveAnalysisRequest(
            test_data={"initial_power": 400, "current_power": 380},
            module_age_years=5.0,
            warranty_period_years=25,
        )

        response = await gemini_provider.predict_failures(request)

        assert 0 <= response.failure_probability <= 1
        assert isinstance(response.risk_factors, list)
        assert isinstance(response.degradation_trends, list)
        assert isinstance(response.preventive_measures, list)
        assert response.detailed_analysis is not None


class TestBatchProcessing:
    """Test batch processing functionality"""

    @pytest.fixture
    def temp_images(self, tmp_path):
        """Create multiple temporary test images"""
        images = []
        for i in range(3):
            image_path = tmp_path / f"test_image_{i}.png"
            img = Image.new("RGB", (100, 100), color="red")
            img.save(image_path)
            images.append(str(image_path))
        return images

    @pytest.mark.asyncio
    async def test_batch_analyze_images_success(self, gemini_provider, temp_images):
        """Test successful batch image analysis"""
        mock_response = MagicMock()
        mock_response.text = "Analysis result"

        gemini_provider.vision_model.generate_content = MagicMock(return_value=mock_response)

        requests = [
            VisionAnalysisRequest(image_path=img, image_type="EL")
            for img in temp_images
        ]

        responses = await gemini_provider.batch_analyze_images(requests)

        assert len(responses) == 3
        for response in responses:
            assert response.raw_analysis is not None

    @pytest.mark.asyncio
    async def test_batch_analyze_with_failures(self, gemini_provider, temp_images):
        """Test batch analysis with some failures"""
        # Make one analysis fail
        def mock_generate(*args, **kwargs):
            # Fail on every other call
            if not hasattr(mock_generate, "call_count"):
                mock_generate.call_count = 0
            mock_generate.call_count += 1

            if mock_generate.call_count % 2 == 0:
                raise Exception("Test error")

            mock_response = MagicMock()
            mock_response.text = "Success"
            return mock_response

        gemini_provider.vision_model.generate_content = MagicMock(side_effect=mock_generate)

        requests = [
            VisionAnalysisRequest(image_path=img, image_type="EL")
            for img in temp_images
        ]

        responses = await gemini_provider.batch_analyze_images(requests)

        # All requests should return a response (some with errors)
        assert len(responses) == 3


class TestHealthCheck:
    """Test health check functionality"""

    @pytest.mark.asyncio
    async def test_health_check_success(self, gemini_provider):
        """Test successful health check"""
        mock_response = MagicMock()
        mock_response.text = "OK"
        mock_response.candidates = [MagicMock(finish_reason=MagicMock(name="STOP"))]
        mock_response.usage_metadata = MagicMock(
            prompt_token_count=5, candidates_token_count=2, total_token_count=7
        )

        gemini_provider.text_model.generate_content = MagicMock(return_value=mock_response)

        health = await gemini_provider.health_check()

        assert health["status"] == "healthy"
        assert health["provider"] == "gemini"
        assert health["model"] == "gemini-2.0-flash-exp"
        assert health["response_received"] is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, gemini_provider):
        """Test health check failure"""
        gemini_provider.text_model.generate_content = MagicMock(
            side_effect=Exception("Connection failed")
        )

        health = await gemini_provider.health_check()

        assert health["status"] == "unhealthy"
        assert health["provider"] == "gemini"
        assert "error" in health


class TestErrorHandling:
    """Test error handling"""

    def test_handle_api_key_error(self, gemini_provider):
        """Test API key error handling"""
        error = Exception("Invalid API key")
        result = gemini_provider._handle_error(error)
        assert isinstance(result, APIKeyError)

    def test_handle_rate_limit_error(self, gemini_provider):
        """Test rate limit error handling"""
        error = Exception("Rate limit exceeded")
        result = gemini_provider._handle_error(error)
        assert isinstance(result, LLMProviderError)

    def test_handle_network_error(self, gemini_provider):
        """Test network error handling"""
        error = Exception("Network connection failed")
        result = gemini_provider._handle_error(error)
        assert isinstance(result, LLMProviderError)
