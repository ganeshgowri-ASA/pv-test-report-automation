"""
OpenAI GPT Integration for PV Test Report Automation.

Provides GPT-4 capabilities for test analysis and documentation.
"""

import logging
from typing import Any, Dict, List, Optional

from openai import OpenAI
from pydantic import BaseModel, Field

from src.llm.key_vault import get_vault

logger = logging.getLogger(__name__)


class GPTRequest(BaseModel):
    """GPT API request configuration."""

    task: str
    input_data: Dict[str, Any]
    model: str = Field(default="gpt-4-turbo-preview")
    max_tokens: int = Field(default=4096)
    temperature: float = Field(default=0.3)


class GPTResponse(BaseModel):
    """GPT API response."""

    task: str
    result: str
    usage: Dict[str, int]
    model: str
    finish_reason: str


class GPTLLM:
    """OpenAI GPT integration for PV test analysis."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize GPT client."""
        if api_key is None:
            vault = get_vault()
            api_key = vault.get_key("openai")
            if api_key is None:
                raise ValueError("OpenAI API key not found")

        self.client = OpenAI(api_key=api_key)
        logger.info("GPT LLM client initialized")

    def analyze_report(self, test_report: Dict[str, Any]) -> GPTResponse:
        """Analyze test report using GPT-4."""
        logger.info("Analyzing report with GPT")

        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a PV testing expert."},
                {"role": "user", "content": f"Analyze this test report:\n\n{test_report}"},
            ],
            max_tokens=4096,
            temperature=0.3,
        )

        return GPTResponse(
            task="analyze_report",
            result=response.choices[0].message.content or "",
            usage={
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
            },
            model=response.model,
            finish_reason=response.choices[0].finish_reason or "stop",
        )
