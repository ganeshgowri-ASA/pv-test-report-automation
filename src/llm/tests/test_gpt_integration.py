"""
Unit tests for GPT Integration Module
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import json
import tempfile
from pathlib import Path

from ..gpt_integration import (
    GPTIntegration,
    GPTResponse,
    PromptTemplate
)
from ..llm_config import LLMConfig, ModelType, LLMProvider


@pytest.fixture
def mock_config():
    """Create a mock LLM config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = LLMConfig(
            config_file=Path(tmpdir) / "config.json",
            cache_dir=Path(tmpdir) / "cache"
        )
        # Set a test API key
        config.set_api_key(LLMProvider.OPENAI, "test-api-key")
        yield config


@pytest.fixture
def mock_openai_response():
    """Create a mock OpenAI response."""
    mock_response = Mock()
    mock_response.id = "test-id-123"
    mock_response.model = "gpt-4-turbo-preview"
    mock_response.created = 1234567890
    mock_response.system_fingerprint = "test-fingerprint"

    mock_choice = Mock()
    mock_choice.finish_reason = "stop"

    mock_message = Mock()
    mock_message.content = "This is a test response"
    mock_choice.message = mock_message

    mock_response.choices = [mock_choice]

    mock_usage = Mock()
    mock_usage.prompt_tokens = 100
    mock_usage.completion_tokens = 50
    mock_response.usage = mock_usage

    return mock_response


class TestPromptTemplate:
    """Test PromptTemplate functionality."""

    def test_system_prompts_exist(self):
        """Test that system prompts are defined."""
        assert 'report_analysis' in PromptTemplate.SYSTEM_PROMPTS
        assert 'compliance_check' in PromptTemplate.SYSTEM_PROMPTS
        assert 'data_extraction' in PromptTemplate.SYSTEM_PROMPTS
        assert 'summary_generation' in PromptTemplate.SYSTEM_PROMPTS

    def test_format_report_analysis(self):
        """Test formatting report analysis prompt."""
        report_data = {
            'module_id': 'TEST-001',
            'test_results': {'power': 300}
        }

        prompt = PromptTemplate.format_report_analysis(report_data)

        assert 'TEST-001' in prompt
        assert 'power' in prompt
        assert 'Analyze' in prompt

    def test_format_compliance_check(self):
        """Test formatting compliance check prompt."""
        report_data = {'module_id': 'TEST-001'}
        standards = ['IEC 61215', 'IEC 61730']

        prompt = PromptTemplate.format_compliance_check(report_data, standards)

        assert 'IEC 61215' in prompt
        assert 'IEC 61730' in prompt
        assert 'compliance' in prompt.lower()

    def test_format_data_extraction(self):
        """Test formatting data extraction prompt."""
        text = "Test report with data"
        schema = {'power': 'float', 'efficiency': 'float'}

        prompt = PromptTemplate.format_data_extraction(text, schema)

        assert text in prompt
        assert 'power' in prompt
        assert 'JSON' in prompt

    def test_format_summary(self):
        """Test formatting summary prompt."""
        report_data = {'module_id': 'TEST-001'}

        prompt = PromptTemplate.format_summary(
            report_data,
            audience='executive',
            max_length=200
        )

        assert 'executive' in prompt
        assert '200' in prompt
        assert 'summary' in prompt.lower()


class TestGPTResponse:
    """Test GPTResponse dataclass."""

    def test_gpt_response_creation(self):
        """Test creating a GPT response."""
        response = GPTResponse(
            content="Test content",
            model="gpt-4",
            tokens_input=100,
            tokens_output=50,
            cost=0.5
        )

        assert response.content == "Test content"
        assert response.model == "gpt-4"
        assert response.tokens_input == 100
        assert response.tokens_output == 50
        assert response.cost == 0.5
        assert response.cached is False

    def test_gpt_response_with_metadata(self):
        """Test GPT response with metadata."""
        metadata = {'id': 'test-123', 'created': 1234567890}
        response = GPTResponse(
            content="Test",
            model="gpt-4",
            tokens_input=100,
            tokens_output=50,
            cost=0.5,
            metadata=metadata
        )

        assert response.metadata == metadata
        assert response.metadata['id'] == 'test-123'


@pytest.mark.skipif(
    True,  # Skip by default as it requires OpenAI API key
    reason="Requires OpenAI API key"
)
class TestGPTIntegrationReal:
    """Tests requiring real OpenAI API (skipped by default)."""

    def test_real_completion(self):
        """Test real OpenAI completion."""
        config = LLMConfig()
        if not config.get_api_key(LLMProvider.OPENAI):
            pytest.skip("OpenAI API key not configured")

        gpt = GPTIntegration(config, ModelType.GPT_35_TURBO)

        messages = [
            {"role": "user", "content": "Say 'test successful'"}
        ]

        response = gpt.complete(messages, max_tokens=10)

        assert isinstance(response, GPTResponse)
        assert len(response.content) > 0
        assert response.tokens_input > 0
        assert response.tokens_output > 0


class TestGPTIntegrationMocked:
    """Tests with mocked OpenAI API."""

    @patch('src.llm.gpt_integration.OpenAI')
    @patch('src.llm.gpt_integration.AsyncOpenAI')
    def test_initialization(self, mock_async_openai, mock_openai, mock_config):
        """Test GPT integration initialization."""
        gpt = GPTIntegration(mock_config, ModelType.GPT_4_TURBO)

        assert gpt.model_type == ModelType.GPT_4_TURBO
        assert gpt.enable_cache is True
        assert mock_openai.called
        assert mock_async_openai.called

    @patch('src.llm.gpt_integration.OpenAI')
    @patch('src.llm.gpt_integration.AsyncOpenAI')
    def test_initialization_without_api_key(self, mock_async_openai, mock_openai):
        """Test initialization fails without API key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LLMConfig(config_file=Path(tmpdir) / "config.json")
            # Don't set API key

            with pytest.raises(ValueError, match="API key not configured"):
                GPTIntegration(config)

    @patch('src.llm.gpt_integration.OpenAI')
    @patch('src.llm.gpt_integration.AsyncOpenAI')
    def test_cache_key_generation(self, mock_async_openai, mock_openai, mock_config):
        """Test cache key generation."""
        gpt = GPTIntegration(mock_config)

        messages = [{"role": "user", "content": "test"}]

        key1 = gpt._get_cache_key(messages)
        key2 = gpt._get_cache_key(messages)

        # Same messages should produce same key
        assert key1 == key2

        # Different messages should produce different key
        messages2 = [{"role": "user", "content": "different"}]
        key3 = gpt._get_cache_key(messages2)
        assert key1 != key3

    @patch('src.llm.gpt_integration.OpenAI')
    @patch('src.llm.gpt_integration.AsyncOpenAI')
    def test_calculate_cost(self, mock_async_openai, mock_openai, mock_config):
        """Test cost calculation."""
        gpt = GPTIntegration(mock_config, ModelType.GPT_4_TURBO)

        # GPT-4 Turbo: $0.01 per 1K input, $0.03 per 1K output
        cost = gpt._calculate_cost(1000, 1000)
        expected_cost = 0.01 + 0.03  # $0.04
        assert abs(cost - expected_cost) < 0.001

        cost = gpt._calculate_cost(500, 500)
        expected_cost = 0.005 + 0.015  # $0.02
        assert abs(cost - expected_cost) < 0.001

    @patch('src.llm.gpt_integration.OpenAI')
    @patch('src.llm.gpt_integration.AsyncOpenAI')
    def test_parse_completion(self, mock_async_openai, mock_openai, mock_config, mock_openai_response):
        """Test parsing OpenAI completion."""
        gpt = GPTIntegration(mock_config)

        response = gpt._parse_completion(mock_openai_response)

        assert isinstance(response, GPTResponse)
        assert response.content == "This is a test response"
        assert response.model == "gpt-4-turbo-preview"
        assert response.tokens_input == 100
        assert response.tokens_output == 50
        assert response.finish_reason == "stop"
        assert 'id' in response.metadata

    @patch('src.llm.gpt_integration.OpenAI')
    @patch('src.llm.gpt_integration.AsyncOpenAI')
    def test_complete_with_cache_hit(self, mock_async_openai, mock_openai, mock_config, mock_openai_response):
        """Test completion with cache hit."""
        gpt = GPTIntegration(mock_config)

        # Mock the OpenAI client
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        gpt.client = mock_client

        messages = [{"role": "user", "content": "test"}]

        # First call - should hit API
        response1 = gpt.complete(messages)
        assert mock_client.chat.completions.create.called
        assert response1.cached is False

        # Second call - should hit cache
        mock_client.chat.completions.create.reset_mock()
        response2 = gpt.complete(messages)
        assert not mock_client.chat.completions.create.called
        assert response2.cached is True
        assert response1.content == response2.content

    @patch('src.llm.gpt_integration.OpenAI')
    @patch('src.llm.gpt_integration.AsyncOpenAI')
    @pytest.mark.asyncio
    async def test_complete_async(self, mock_async_openai, mock_openai, mock_config, mock_openai_response):
        """Test async completion."""
        gpt = GPTIntegration(mock_config)

        # Mock the async client
        mock_async_client = Mock()
        mock_async_client.chat.completions.create = AsyncMock(return_value=mock_openai_response)
        gpt.async_client = mock_async_client

        messages = [{"role": "user", "content": "test"}]

        response = await gpt.complete_async(messages)

        assert isinstance(response, GPTResponse)
        assert response.content == "This is a test response"
        assert mock_async_client.chat.completions.create.called

    @patch('src.llm.gpt_integration.OpenAI')
    @patch('src.llm.gpt_integration.AsyncOpenAI')
    @pytest.mark.asyncio
    async def test_complete_async_with_retry(self, mock_async_openai, mock_openai, mock_config, mock_openai_response):
        """Test async completion with retry on failure."""
        gpt = GPTIntegration(mock_config)

        # Mock the async client to fail first, then succeed
        mock_async_client = Mock()
        mock_async_client.chat.completions.create = AsyncMock(
            side_effect=[Exception("API Error"), mock_openai_response]
        )
        gpt.async_client = mock_async_client

        messages = [{"role": "user", "content": "test"}]

        response = await gpt.complete_async(messages)

        assert isinstance(response, GPTResponse)
        assert mock_async_client.chat.completions.create.call_count == 2

    @patch('src.llm.gpt_integration.OpenAI')
    @patch('src.llm.gpt_integration.AsyncOpenAI')
    def test_analyze_report(self, mock_async_openai, mock_openai, mock_config, mock_openai_response):
        """Test analyze_report method."""
        gpt = GPTIntegration(mock_config)

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        gpt.client = mock_client

        report_data = {
            'module_id': 'TEST-001',
            'test_results': {'power': 300}
        }

        response = gpt.analyze_report(report_data)

        assert isinstance(response, GPTResponse)
        # Verify the system prompt was used
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        assert messages[0]['role'] == 'system'
        assert 'PV' in messages[0]['content']

    @patch('src.llm.gpt_integration.OpenAI')
    @patch('src.llm.gpt_integration.AsyncOpenAI')
    def test_extract_data(self, mock_async_openai, mock_openai, mock_config, mock_openai_response):
        """Test extract_data method."""
        gpt = GPTIntegration(mock_config)

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        gpt.client = mock_client

        text = "Power output: 300W, Efficiency: 18%"
        schema = {'power': 'float', 'efficiency': 'float'}

        response = gpt.extract_data(text, schema, response_format="json_object")

        assert isinstance(response, GPTResponse)
        # Verify JSON format was requested
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1].get('response_format') == {"type": "json_object"}

    @patch('src.llm.gpt_integration.OpenAI')
    @patch('src.llm.gpt_integration.AsyncOpenAI')
    @pytest.mark.asyncio
    async def test_batch_analyze(self, mock_async_openai, mock_openai, mock_config, mock_openai_response):
        """Test batch analysis."""
        gpt = GPTIntegration(mock_config)

        mock_async_client = Mock()
        mock_async_client.chat.completions.create = AsyncMock(return_value=mock_openai_response)
        gpt.async_client = mock_async_client

        reports = [
            {'module_id': 'TEST-001'},
            {'module_id': 'TEST-002'},
            {'module_id': 'TEST-003'}
        ]

        responses = await gpt.batch_analyze(reports)

        assert len(responses) == 3
        assert all(isinstance(r, GPTResponse) for r in responses)
        assert mock_async_client.chat.completions.create.call_count == 3

    @patch('src.llm.gpt_integration.OpenAI')
    @patch('src.llm.gpt_integration.AsyncOpenAI')
    def test_cache_disabled(self, mock_async_openai, mock_openai, mock_config, mock_openai_response):
        """Test with cache disabled."""
        gpt = GPTIntegration(mock_config, enable_cache=False)

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        gpt.client = mock_client

        messages = [{"role": "user", "content": "test"}]

        # Two identical calls
        response1 = gpt.complete(messages)
        response2 = gpt.complete(messages)

        # Both should hit API (no caching)
        assert mock_client.chat.completions.create.call_count == 2
        assert response1.cached is False
        assert response2.cached is False


@pytest.mark.asyncio
class TestGPTAsyncOperations:
    """Test async-specific operations."""

    @patch('src.llm.gpt_integration.OpenAI')
    @patch('src.llm.gpt_integration.AsyncOpenAI')
    async def test_concurrent_requests(self, mock_async_openai, mock_openai, mock_config, mock_openai_response):
        """Test handling multiple concurrent requests."""
        gpt = GPTIntegration(mock_config)

        mock_async_client = Mock()
        mock_async_client.chat.completions.create = AsyncMock(return_value=mock_openai_response)
        gpt.async_client = mock_async_client

        messages_list = [
            [{"role": "user", "content": f"test {i}"}]
            for i in range(5)
        ]

        tasks = [gpt.complete_async(messages) for messages in messages_list]
        responses = await asyncio.gather(*tasks)

        assert len(responses) == 5
        assert all(isinstance(r, GPTResponse) for r in responses)
