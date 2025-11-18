"""
LLM Integration Module for PV Test Report Automation

Provides production-ready integration with various LLM providers
for AI-powered report analysis, compliance checking, and summarization.
"""

from .llm_config import (
    LLMConfig,
    LLMProvider,
    ModelType,
    ModelConfig,
    RateLimitConfig,
    UsageStats,
    get_config,
    set_config
)

from .gpt_integration import (
    GPTIntegration,
    GPTResponse,
    PromptTemplate
)

from .gemini_integration import (
    GeminiIntegration,
    GeminiResponse,
    GeminiPromptTemplate,
    ImageData
)

from .compliance_checker import (
    ComplianceChecker,
    ComplianceResult,
    ComplianceStatus,
    ComplianceGap,
    SeverityLevel,
    StandardRequirement,
    StandardsDatabase
)

from .report_summarizer import (
    ReportSummarizer,
    ReportSummary,
    SummaryType,
    SummaryFormat,
    SummaryConfig,
    KeyFinding,
    Language
)

__version__ = "1.0.0"

__all__ = [
    # Configuration
    "LLMConfig",
    "LLMProvider",
    "ModelType",
    "ModelConfig",
    "RateLimitConfig",
    "UsageStats",
    "get_config",
    "set_config",

    # GPT Integration
    "GPTIntegration",
    "GPTResponse",
    "PromptTemplate",

    # Gemini Integration
    "GeminiIntegration",
    "GeminiResponse",
    "GeminiPromptTemplate",
    "ImageData",

    # Compliance Checking
    "ComplianceChecker",
    "ComplianceResult",
    "ComplianceStatus",
    "ComplianceGap",
    "SeverityLevel",
    "StandardRequirement",
    "StandardsDatabase",

    # Report Summarization
    "ReportSummarizer",
    "ReportSummary",
    "SummaryType",
    "SummaryFormat",
    "SummaryConfig",
    "KeyFinding",
    "Language",
]
