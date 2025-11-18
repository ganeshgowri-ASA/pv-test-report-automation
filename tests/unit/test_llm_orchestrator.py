"""Unit tests for LLM Orchestrator."""
import pytest
from src.llm_orchestrator import LLMRouter, CostTracker
from src.llm_orchestrator.models import LLMProvider, ModelConfig


class TestLLMRouter:
    """Test LLM router."""
    
    def test_register_model(self):
        """Test model registration."""
        router = LLMRouter()
        config = ModelConfig(
            provider=LLMProvider.ANTHROPIC,
            model_name="claude-3-sonnet",
            cost_per_1k_input_tokens=0.003,
            cost_per_1k_output_tokens=0.015,
            max_tokens=4096,
            priority=1
        )
        router.register_model(config)
        assert len(router.model_configs) == 1


class TestCostTracker:
    """Test cost tracker."""
    
    def test_cost_tracking(self):
        """Test cost tracking."""
        tracker = CostTracker(monthly_budget=100.0)
        assert tracker.monthly_budget == 100.0
        assert tracker.get_total_cost() == 0.0
