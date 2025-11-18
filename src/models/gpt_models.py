"""Pydantic models for GPT requests and responses."""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


class GPTModel(str, Enum):
    """Available GPT models."""
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4 = "gpt-4"
    GPT_4O = "gpt-4o"
    GPT_35_TURBO = "gpt-3.5-turbo"


class Language(str, Enum):
    """Supported languages for report generation."""
    ENGLISH = "en"
    SPANISH = "es"
    GERMAN = "de"
    FRENCH = "fr"
    CHINESE = "zh"
    JAPANESE = "ja"


class GPTRequest(BaseModel):
    """Model for GPT API requests."""

    prompt: str = Field(..., description="The prompt to send to GPT")
    model: str = Field(default="gpt-4-turbo", description="GPT model to use")
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )
    max_tokens: int = Field(
        default=2000,
        ge=1,
        le=4000,
        description="Maximum tokens in response"
    )
    system_message: Optional[str] = Field(
        None,
        description="System message to set context"
    )

    @validator("temperature")
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v


class GPTResponse(BaseModel):
    """Model for GPT API responses."""

    content: str = Field(..., description="The response content")
    model_used: str = Field(..., description="Model that generated the response")
    tokens_used: int = Field(..., description="Total tokens used")
    prompt_tokens: int = Field(default=0, description="Tokens in prompt")
    completion_tokens: int = Field(default=0, description="Tokens in completion")
    cost_usd: float = Field(..., description="Estimated cost in USD")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cached: bool = Field(default=False, description="Whether response was cached")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ComplianceStandard(str, Enum):
    """IEC/ISO standards for PV testing."""
    IEC_61215 = "IEC 61215"
    IEC_61730 = "IEC 61730"
    IEC_62804 = "IEC 62804"
    IEC_61853 = "IEC 61853"
    ISO_9001 = "ISO 9001"


class ComplianceStatus(str, Enum):
    """Compliance check status."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class ComplianceCheck(BaseModel):
    """Model for compliance checking results."""

    standard: ComplianceStandard = Field(..., description="The standard checked against")
    status: ComplianceStatus = Field(..., description="Compliance status")
    requirements_met: List[str] = Field(default_factory=list)
    requirements_failed: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in assessment"
    )
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AnomalyType(str, Enum):
    """Types of anomalies in test data."""
    OUTLIER = "outlier"
    TREND_DEVIATION = "trend_deviation"
    MISSING_DATA = "missing_data"
    INCONSISTENCY = "inconsistency"
    THRESHOLD_VIOLATION = "threshold_violation"


class Anomaly(BaseModel):
    """Model for detected anomalies."""

    type: AnomalyType
    severity: str = Field(..., description="low, medium, high")
    location: str = Field(..., description="Where anomaly was found")
    description: str
    suggested_action: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)


class AnalysisResult(BaseModel):
    """Model for test result analysis."""

    summary: str = Field(..., description="Analysis summary")
    key_findings: List[str] = Field(default_factory=list)
    anomalies: List[Anomaly] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    data_quality_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall data quality"
    )
    patterns_detected: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ReportSummary(BaseModel):
    """Model for report summarization."""

    executive_summary: str
    test_overview: str
    key_metrics: Dict[str, Any]
    compliance_status: Optional[ComplianceStatus] = None
    recommendations: List[str] = Field(default_factory=list)
    language: Language = Field(default=Language.ENGLISH)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class NaturalLanguageQuery(BaseModel):
    """Model for natural language queries on test data."""

    query: str = Field(..., description="Natural language question")
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Test data context"
    )
    include_visualizations: bool = Field(
        default=False,
        description="Whether to suggest visualizations"
    )


class QueryResponse(BaseModel):
    """Model for query responses."""

    answer: str
    relevant_data: Dict[str, Any] = Field(default_factory=dict)
    suggested_visualizations: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    sources: List[str] = Field(default_factory=list)
