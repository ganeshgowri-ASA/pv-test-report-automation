"""Pydantic models for LLM requests and responses"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class LLMProvider(str, Enum):
    """Supported LLM providers"""

    GEMINI = "gemini"
    CLAUDE = "claude"
    OPENAI = "openai"


class FinishReason(str, Enum):
    """Reasons for generation completion"""

    STOP = "STOP"
    MAX_TOKENS = "MAX_TOKENS"
    SAFETY = "SAFETY"
    RECITATION = "RECITATION"
    OTHER = "OTHER"


class SafetyRating(BaseModel):
    """Safety rating for generated content"""

    category: str
    probability: str
    blocked: bool = False


class GeminiRequest(BaseModel):
    """Request model for Gemini API"""

    prompt: str = Field(..., min_length=1, description="Text prompt for generation")
    model: str = Field(default="gemini-2.0-flash-exp", description="Model to use")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Generation temperature")
    max_tokens: int = Field(
        default=2048, ge=1, le=32768, description="Maximum output tokens"
    )
    top_p: float = Field(default=0.95, ge=0.0, le=1.0, description="Nucleus sampling")
    top_k: int = Field(default=40, ge=1, le=100, description="Top-k sampling")
    images: Optional[List[str]] = Field(
        default=None, description="List of image paths for vision tasks"
    )
    system_instruction: Optional[str] = Field(
        default=None, description="System instruction for the model"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Analyze this PV module test data for compliance with IEC 61215",
                "model": "gemini-2.0-flash-exp",
                "temperature": 0.7,
                "max_tokens": 2048,
            }
        }


class GeminiResponse(BaseModel):
    """Response model from Gemini API"""

    content: str = Field(..., description="Generated content")
    safety_ratings: List[SafetyRating] = Field(
        default_factory=list, description="Content safety ratings"
    )
    finish_reason: str = Field(default="STOP", description="Generation completion reason")
    prompt_token_count: Optional[int] = Field(
        default=None, description="Number of tokens in prompt"
    )
    candidates_token_count: Optional[int] = Field(
        default=None, description="Number of tokens in response"
    )
    total_token_count: Optional[int] = Field(
        default=None, description="Total tokens used"
    )
    model: str = Field(..., description="Model used for generation")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "The PV module meets IEC 61215 requirements...",
                "safety_ratings": [],
                "finish_reason": "STOP",
                "model": "gemini-2.0-flash-exp",
            }
        }


class DefectSeverity(str, Enum):
    """Defect severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NEGLIGIBLE = "negligible"


class DefectAnalysis(BaseModel):
    """Analysis result for a detected defect"""

    defect_type: str = Field(..., description="Type of defect detected")
    severity: DefectSeverity = Field(..., description="Severity level")
    location: Optional[str] = Field(default=None, description="Location of defect in module")
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence score (0-1)"
    )
    description: str = Field(..., description="Detailed description of the defect")
    impact: Optional[str] = Field(
        default=None, description="Potential impact on module performance"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Recommended actions"
    )


class VisionAnalysisRequest(BaseModel):
    """Request for vision-based image analysis"""

    image_path: str = Field(..., description="Path to the image file")
    image_type: str = Field(
        default="EL", description="Type of image (EL, thermal, visual, etc.)"
    )
    standard: str = Field(
        default="IEC 61215", description="PV standard to check against"
    )
    additional_context: Optional[str] = Field(
        default=None, description="Additional context for analysis"
    )

    @field_validator("image_path")
    @classmethod
    def validate_image_path(cls, v: str) -> str:
        """Validate that image file exists"""
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Image file not found: {v}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {v}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "image_path": "/path/to/el_image.png",
                "image_type": "EL",
                "standard": "IEC 61215",
            }
        }


class VisionAnalysisResponse(BaseModel):
    """Response from vision-based analysis"""

    defects: List[DefectAnalysis] = Field(
        default_factory=list, description="List of detected defects"
    )
    overall_assessment: str = Field(..., description="Overall assessment of the module")
    compliance_status: str = Field(
        ..., description="Compliance status (Pass/Fail/Conditional)"
    )
    confidence_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Overall confidence score"
    )
    raw_analysis: str = Field(..., description="Raw LLM analysis text")
    image_metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Image metadata"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "defects": [
                    {
                        "defect_type": "crack",
                        "severity": "high",
                        "confidence": 0.92,
                        "description": "Micro-crack detected in cell B5",
                    }
                ],
                "overall_assessment": "Module shows signs of mechanical stress",
                "compliance_status": "Conditional",
                "confidence_score": 0.88,
                "raw_analysis": "Detailed analysis...",
            }
        }


class ComplianceCheckRequest(BaseModel):
    """Request for compliance checking"""

    report_data: Dict[str, Any] = Field(..., description="Test report data to check")
    standard: str = Field(..., description="Standard to check against (e.g., IEC 61215)")
    check_missing_data: bool = Field(
        default=True, description="Flag missing required data"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "report_data": {
                    "module_id": "PV-001",
                    "power_output": 400,
                    "efficiency": 20.5,
                },
                "standard": "IEC 61215",
            }
        }


class ComplianceCheckResponse(BaseModel):
    """Response from compliance checking"""

    compliance_status: str = Field(
        ..., description="Overall compliance status (Pass/Fail/Conditional)"
    )
    violations: List[str] = Field(
        default_factory=list, description="List of requirement violations"
    )
    missing_data: List[str] = Field(
        default_factory=list, description="List of missing required data"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Recommendations for compliance"
    )
    detailed_analysis: str = Field(..., description="Detailed compliance analysis")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "compliance_status": "Pass",
                "violations": [],
                "missing_data": ["thermal_imaging_data"],
                "recommendations": ["Provide thermal imaging results"],
                "detailed_analysis": "Module meets all IEC 61215 requirements...",
            }
        }


class PredictiveAnalysisRequest(BaseModel):
    """Request for predictive failure analysis"""

    test_data: Dict[str, Any] = Field(..., description="Historical and current test data")
    module_age_years: Optional[float] = Field(
        default=None, description="Age of the module in years"
    )
    environmental_factors: Optional[Dict[str, Any]] = Field(
        default=None, description="Environmental conditions (temperature, humidity, etc.)"
    )
    warranty_period_years: int = Field(
        default=25, description="Warranty period in years"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "test_data": {
                    "initial_power": 400,
                    "current_power": 380,
                    "degradation_rate": 0.5,
                },
                "module_age_years": 5,
                "warranty_period_years": 25,
            }
        }


class PredictiveAnalysisResponse(BaseModel):
    """Response from predictive analysis"""

    failure_probability: float = Field(
        ..., ge=0.0, le=1.0, description="Probability of failure within warranty"
    )
    risk_factors: List[str] = Field(
        default_factory=list, description="Identified risk factors"
    )
    degradation_trends: List[str] = Field(
        default_factory=list, description="Observed degradation trends"
    )
    preventive_measures: List[str] = Field(
        default_factory=list, description="Recommended preventive measures"
    )
    estimated_lifespan_years: Optional[float] = Field(
        default=None, description="Estimated remaining lifespan"
    )
    detailed_analysis: str = Field(..., description="Detailed predictive analysis")
    confidence_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence in predictions"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "failure_probability": 0.15,
                "risk_factors": ["Above-average degradation rate", "Hotspot detected"],
                "degradation_trends": ["Linear degradation at 0.5%/year"],
                "preventive_measures": ["Regular thermal imaging", "Clean modules quarterly"],
                "estimated_lifespan_years": 22.5,
                "detailed_analysis": "Based on current degradation trends...",
                "confidence_score": 0.82,
            }
        }
