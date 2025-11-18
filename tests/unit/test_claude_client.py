"""
Unit tests for Claude API client.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.llm.claude_client import ClaudeClient, TokenUsageTracker
from src.utils.exceptions import (
    ClaudeAPIException,
    RateLimitException,
    AuthenticationException,
)


class TestTokenUsageTracker:
    """Test token usage tracking."""

    def test_record_usage(self):
        """Test recording token usage."""
        tracker = TokenUsageTracker()

        usage = tracker.record_usage(
            model="claude-3-5-sonnet-20241022",
            operation="test",
            input_tokens=100,
            output_tokens=50,
            duration=1.5,
        )

        assert usage["input_tokens"] == 100
        assert usage["output_tokens"] == 50
        assert usage["total_tokens"] == 150
        assert usage["estimated_cost"] > 0
        assert len(tracker.usage_log) == 1

    def test_get_summary(self):
        """Test getting usage summary."""
        tracker = TokenUsageTracker()

        tracker.record_usage("model1", "op1", 100, 50, 1.0)
        tracker.record_usage("model1", "op2", 200, 100, 2.0)

        summary = tracker.get_summary()

        assert summary["total_calls"] == 2
        assert summary["total_input_tokens"] == 300
        assert summary["total_output_tokens"] == 150
        assert summary["total_tokens"] == 450
        assert summary["total_cost_usd"] > 0


class TestClaudeClient:
    """Test Claude API client."""

    @patch("src.llm.claude_client.Anthropic")
    def test_initialization_with_api_key(self, mock_anthropic):
        """Test client initialization with API key."""
        client = ClaudeClient(api_key="test-key")

        assert client.api_key == "test-key"
        assert client.model == "claude-3-5-sonnet-20241022"
        assert client.token_tracker is not None

    @patch("src.llm.claude_client.Anthropic")
    def test_initialization_without_api_key_raises_error(self, mock_anthropic):
        """Test initialization without API key raises error."""
        with patch("src.config.settings.get_settings") as mock_settings:
            mock_settings.return_value.CLAUDE_API_KEY = ""

            with pytest.raises(AuthenticationException):
                ClaudeClient()

    @patch("src.llm.claude_client.Anthropic")
    def test_hash_prompt(self, mock_anthropic):
        """Test prompt hashing."""
        hash1 = ClaudeClient._hash_prompt("test prompt")
        hash2 = ClaudeClient._hash_prompt("test prompt")
        hash3 = ClaudeClient._hash_prompt("different prompt")

        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 16

    @pytest.mark.asyncio
    @patch("src.llm.claude_client.AsyncAnthropic")
    async def test_simple_prompt_async(self, mock_async_anthropic):
        """Test async simple prompt."""
        # Mock response
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response")]
        mock_response.usage = Mock(input_tokens=10, output_tokens=20)

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("src.llm.claude_client.AsyncAnthropic", return_value=mock_client):
            client = ClaudeClient(api_key="test-key")
            result = await client.simple_prompt_async("Test question")

            assert result == "Test response"
            mock_client.messages.create.assert_called_once()

    @patch("src.llm.claude_client.Anthropic")
    def test_get_usage_summary(self, mock_anthropic):
        """Test getting usage summary from client."""
        client = ClaudeClient(api_key="test-key")
        client.token_tracker.record_usage("model", "op", 100, 50, 1.0)

        summary = client.get_usage_summary()

        assert summary["total_calls"] == 1
        assert summary["total_tokens"] == 150


@pytest.mark.integration
class TestClaudeClientIntegration:
    """Integration tests requiring actual API key (marked for skipping)."""

    @pytest.mark.llm
    @pytest.mark.skip(reason="Requires actual Claude API key")
    async def test_real_api_call(self):
        """Test real API call (requires API key)."""
        client = ClaudeClient()
        response = await client.simple_prompt_async("What is 2+2?")

        assert len(response) > 0
        assert "4" in response
