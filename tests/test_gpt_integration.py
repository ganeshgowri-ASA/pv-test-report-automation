"""Tests for core GPT integration."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.gpt_integration.client import GPTIntegration
from src.models.gpt_models import GPTRequest, GPTResponse
from src.utils.config import Config


class TestGPTIntegration(unittest.TestCase):
    """Test cases for GPT integration."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock config to avoid loading .env
        self.mock_config = Mock(spec=Config)
        self.mock_config.openai_api_key = "test-api-key"
        self.mock_config.openai_organization = None
        self.mock_config.default_model = "gpt-4-turbo"
        self.mock_config.default_temperature = 0.7
        self.mock_config.default_max_tokens = 2000
        self.mock_config.enable_cache = True
        self.mock_config.cache_max_size = 100
        self.mock_config.cache_ttl_seconds = 3600
        self.mock_config.rate_limit_requests_per_minute = 60
        self.mock_config.rate_limit_tokens_per_minute = 90000
        self.mock_config.enable_cost_tracking = True
        self.mock_config.cost_alert_threshold_usd = 100.0

        # Mock pricing
        self.mock_config.get_model_pricing = Mock(return_value={
            "prompt": 0.01,
            "completion": 0.03
        })

    @patch('src.gpt_integration.client.OpenAI')
    def test_initialization(self, mock_openai):
        """Test GPT integration initialization."""
        client = GPTIntegration(
            api_key="test-key",
            config=self.mock_config
        )

        self.assertIsNotNone(client.client)
        self.assertIsNotNone(client.cache)
        self.assertIsNotNone(client.rate_limiter)
        self.assertIsNotNone(client.cost_tracker)

    @patch('src.gpt_integration.client.OpenAI')
    def test_estimate_tokens(self, mock_openai):
        """Test token estimation."""
        client = GPTIntegration(
            api_key="test-key",
            config=self.mock_config
        )

        text = "This is a test" * 100
        estimated = client._estimate_tokens(text)

        self.assertGreater(estimated, 0)
        self.assertEqual(estimated, len(text) // 4)

    @patch('src.gpt_integration.client.OpenAI')
    def test_calculate_cost(self, mock_openai):
        """Test cost calculation."""
        client = GPTIntegration(
            api_key="test-key",
            config=self.mock_config
        )

        cost = client._calculate_cost(
            model="gpt-4-turbo",
            prompt_tokens=1000,
            completion_tokens=500
        )

        expected_cost = (1000 / 1000 * 0.01) + (500 / 1000 * 0.03)
        self.assertAlmostEqual(cost, expected_cost, places=4)

    @patch('src.gpt_integration.client.OpenAI')
    def test_generate_completion_with_cache(self, mock_openai):
        """Test completion generation with caching."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test response"))]
        mock_response.usage = Mock(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )

        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client_instance

        client = GPTIntegration(
            api_key="test-key",
            config=self.mock_config
        )

        request = GPTRequest(
            prompt="Test prompt",
            model="gpt-4-turbo",
            temperature=0.7,
            max_tokens=100
        )

        # First call - should hit API
        response1 = client.generate_completion(request, use_cache=True)
        self.assertIsInstance(response1, GPTResponse)
        self.assertEqual(response1.content, "Test response")
        self.assertFalse(response1.cached)

        # Second call - should hit cache
        response2 = client.generate_completion(request, use_cache=True)
        self.assertTrue(response2.cached)

    @patch('src.gpt_integration.client.OpenAI')
    def test_query_simple_interface(self, mock_openai):
        """Test simple query interface."""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Answer"))]
        mock_response.usage = Mock(
            prompt_tokens=50,
            completion_tokens=25,
            total_tokens=75
        )

        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client_instance

        client = GPTIntegration(
            api_key="test-key",
            config=self.mock_config
        )

        response = client.query("What is 2+2?")
        self.assertEqual(response, "Answer")

    @patch('src.gpt_integration.client.OpenAI')
    def test_get_stats(self, mock_openai):
        """Test statistics retrieval."""
        client = GPTIntegration(
            api_key="test-key",
            config=self.mock_config
        )

        stats = client.get_stats()

        self.assertIn("rate_limiter", stats)
        self.assertIn("cache", stats)
        self.assertIn("costs", stats)


class TestGPTRequest(unittest.TestCase):
    """Test cases for GPT request model."""

    def test_valid_request(self):
        """Test creating valid request."""
        request = GPTRequest(
            prompt="Test prompt",
            model="gpt-4-turbo",
            temperature=0.7,
            max_tokens=1000
        )

        self.assertEqual(request.prompt, "Test prompt")
        self.assertEqual(request.model, "gpt-4-turbo")
        self.assertEqual(request.temperature, 0.7)
        self.assertEqual(request.max_tokens, 1000)

    def test_default_values(self):
        """Test default values."""
        request = GPTRequest(prompt="Test")

        self.assertEqual(request.model, "gpt-4-turbo")
        self.assertEqual(request.temperature, 0.7)
        self.assertEqual(request.max_tokens, 2000)

    def test_temperature_validation(self):
        """Test temperature validation."""
        # Valid temperature
        request = GPTRequest(prompt="Test", temperature=0.5)
        self.assertEqual(request.temperature, 0.5)

        # Test boundary values
        request = GPTRequest(prompt="Test", temperature=0.0)
        self.assertEqual(request.temperature, 0.0)

        request = GPTRequest(prompt="Test", temperature=2.0)
        self.assertEqual(request.temperature, 2.0)


class TestGPTResponse(unittest.TestCase):
    """Test cases for GPT response model."""

    def test_response_creation(self):
        """Test creating response."""
        response = GPTResponse(
            content="Test content",
            model_used="gpt-4-turbo",
            tokens_used=150,
            prompt_tokens=100,
            completion_tokens=50,
            cost_usd=0.025
        )

        self.assertEqual(response.content, "Test content")
        self.assertEqual(response.tokens_used, 150)
        self.assertFalse(response.cached)
        self.assertIsInstance(response.timestamp, datetime)


if __name__ == '__main__':
    unittest.main()
