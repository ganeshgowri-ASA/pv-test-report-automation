"""LLM Orchestrator data models."""

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"


class LLMRequest(BaseModel):
    """Request to LLM."""

    prompt: str = Field(..., description="Prompt text")
    system_prompt: Optional[str] = Field(None, description="System prompt")
    max_tokens: int = Field(4096, description="Maximum tokens to generate")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    preferred_provider: Optional[LLMProvider] = Field(None, description="Preferred provider")
    fallback_enabled: bool = Field(True, description="Enable fallback to other providers")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class LLMResponse(BaseModel):
    """Response from LLM."""

    content: str = Field(..., description="Generated content")
    provider: LLMProvider = Field(..., description="Provider that generated response")
    model: str = Field(..., description="Model name")
    tokens_used: int = Field(..., description="Total tokens used")
    cost: float = Field(..., description="Estimated cost in USD")
    latency_ms: int = Field(..., description="Response latency in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ModelConfig(BaseModel):
    """Configuration for an LLM model."""

    provider: LLMProvider
    model_name: str
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float
    max_tokens: int
    priority: int = Field(1, description="Priority for load balancing (higher = higher priority)")
    enabled: bool = True


class ProviderStatus(BaseModel):
    """Status of an LLM provider."""

    provider: LLMProvider
    available: bool
    last_check: datetime
    error_count: int = 0
    success_count: int = 0
    average_latency_ms: float = 0.0
