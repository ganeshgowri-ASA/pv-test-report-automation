"""Data models for image processing and ingestion"""

from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel, Field, validator


class ImageType(str, Enum):
    """Types of images processed in PV testing"""
    EL = "el"  # Electroluminescence
    VISUAL = "visual"  # Visual inspection
    THERMAL = "thermal"  # Thermal imaging
    IV_CHART = "iv_chart"  # I-V curve charts


class DefectType(str, Enum):
    """Types of defects that can be detected"""
    CRACK = "crack"  # Physical cracks in cells
    DARK_SPOT = "dark_spot"  # Dark areas indicating inactive regions
    HOTSPOT = "hotspot"  # Thermal hotspots
    FINGER_INTERRUPTION = "finger_interruption"  # Broken fingers/busbars
    CELL_BREAKAGE = "cell_breakage"  # Cell breakage
    CORROSION = "corrosion"  # Corrosion marks
    DISCOLORATION = "discoloration"  # Color changes
    DELAMINATION = "delamination"  # Layer separation
    SNAIL_TRAIL = "snail_trail"  # Snail trail patterns
    PID = "pid"  # Potential Induced Degradation


class DefectSeverity(str, Enum):
    """Severity levels for detected defects"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Defect(BaseModel):
    """Model for a detected defect in an image"""
    defect_type: DefectType
    severity: DefectSeverity
    location: Tuple[int, int, int, int] = Field(
        ..., description="Bounding box (x, y, width, height)"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    area_pixels: int = Field(..., description="Defect area in pixels")
    description: Optional[str] = Field(None, description="Additional details")
    cell_id: Optional[str] = Field(None, description="Cell identifier if applicable")

    class Config:
        use_enum_values = True


class QualityMetrics(BaseModel):
    """Quality metrics for image validation"""
    blur_score: float = Field(..., ge=0.0, description="Laplacian variance for blur")
    brightness_mean: float = Field(..., ge=0.0, le=255.0)
    contrast_std: float = Field(..., ge=0.0)
    resolution: Tuple[int, int] = Field(..., description="Image resolution (width, height)")
    dynamic_range: float = Field(..., ge=0.0, le=255.0)
    noise_level: float = Field(..., ge=0.0)
    sharpness_score: float = Field(..., ge=0.0)
    uniformity_score: float = Field(..., ge=0.0, le=1.0)
    exposure_quality: str = Field(..., description="underexposed|normal|overexposed")

    class Config:
        use_enum_values = True


class ImageIngestionResult(BaseModel):
    """Result of image ingestion and processing

    Compliant with ISO/IEC 17025:2017 requirements for:
    - Data integrity and traceability
    - Quality assurance
    - Measurement uncertainty
    - Equipment validation
    """
    file_path: str = Field(..., description="Path to the image file")
    image_type: ImageType = Field(..., description="Type of image")
    defects_detected: List[Defect] = Field(default_factory=list)
    quality_passed: bool = Field(..., description="Whether image passes quality checks")
    quality_metrics: QualityMetrics = Field(..., description="Detailed quality metrics")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="EXIF and other metadata")
    file_hash: str = Field(..., description="SHA-256 hash for integrity verification")

    # ISO 17025 compliance fields
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow)
    processor_version: str = Field(default="1.0.0")
    calibration_date: Optional[datetime] = Field(None, description="Equipment calibration date")
    operator_id: Optional[str] = Field(None, description="Operator identification")
    equipment_id: Optional[str] = Field(None, description="Equipment identification")
    uncertainty_estimate: Optional[float] = Field(None, description="Measurement uncertainty")

    # OCR results
    ocr_text: Optional[str] = Field(None, description="Extracted text from displays")
    ocr_data: Optional[Dict[str, Any]] = Field(None, description="Structured OCR data")

    # I-V curve specific
    iv_curve_data: Optional[Dict[str, Any]] = Field(
        None, description="Extracted I-V curve parameters"
    )

    # Validation and review
    validated: bool = Field(default=False, description="Technical validation status")
    reviewer_notes: Optional[str] = Field(None, description="Reviewer comments")
    validation_timestamp: Optional[datetime] = Field(None)

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

    @validator('file_hash')
    def validate_hash_format(cls, v):
        """Ensure hash is valid SHA-256 format"""
        if len(v) != 64 or not all(c in '0123456789abcdef' for c in v.lower()):
            raise ValueError('file_hash must be a valid SHA-256 hash')
        return v.lower()


class ProcessingConfig(BaseModel):
    """Configuration for image processing pipeline"""

    # Quality thresholds
    min_blur_score: float = Field(100.0, description="Minimum Laplacian variance")
    min_brightness: float = Field(20.0, description="Minimum brightness")
    max_brightness: float = Field(235.0, description="Maximum brightness")
    min_contrast: float = Field(30.0, description="Minimum contrast std dev")
    min_resolution: Tuple[int, int] = Field((640, 480), description="Minimum resolution")
    max_noise_level: float = Field(50.0, description="Maximum acceptable noise")
    min_sharpness: float = Field(50.0, description="Minimum sharpness score")

    # Defect detection parameters
    crack_detection_sensitivity: float = Field(0.7, ge=0.0, le=1.0)
    dark_spot_threshold: float = Field(0.3, ge=0.0, le=1.0)
    min_defect_area: int = Field(100, description="Minimum defect area in pixels")

    # OCR settings
    ocr_enabled: bool = Field(True)
    ocr_language: str = Field("eng", description="Tesseract language code")
    ocr_confidence_threshold: float = Field(60.0, description="Min OCR confidence")

    # Processing options
    apply_preprocessing: bool = Field(True, description="Apply image enhancement")
    generate_annotations: bool = Field(True, description="Generate annotated images")
    save_intermediate: bool = Field(False, description="Save intermediate processing steps")

    class Config:
        use_enum_values = True
