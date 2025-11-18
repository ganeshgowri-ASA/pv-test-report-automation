"""
Google Gemini Integration for PV Test Report Automation.

Provides Gemini Pro capabilities for test analysis.
"""

import logging
from typing import Any, Dict, Optional

import google.generativeai as genai
from pydantic import BaseModel, Field

from src.llm.key_vault import get_vault

logger = logging.getLogger(__name__)


class GeminiRequest(BaseModel):
    """Gemini API request configuration."""

    task: str
    input_data: Dict[str, Any]
    model: str = Field(default="gemini-1.5-pro")
    max_tokens: int = Field(default=4096)
    temperature: float = Field(default=0.3)


class GeminiResponse(BaseModel):
    """Gemini API response."""

    task: str
    result: str
    model: str
    finish_reason: str


class GeminiLLM:
    """Google Gemini integration for PV test analysis."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini client."""
        if api_key is None:
            vault = get_vault()
            api_key = vault.get_key("gemini")
            if api_key is None:
                raise ValueError("Gemini API key not found")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-pro")
        logger.info("Gemini LLM client initialized")

    def analyze_report(self, test_report: Dict[str, Any]) -> GeminiResponse:
        """Analyze test report using Gemini."""
        logger.info("Analyzing report with Gemini")

        prompt = f"Analyze this PV test report:\n\n{test_report}"
        response = self.model.generate_content(prompt)

        return GeminiResponse(
            task="analyze_report",
            result=response.text,
            model="gemini-1.5-pro",
            finish_reason="stop",
        )
