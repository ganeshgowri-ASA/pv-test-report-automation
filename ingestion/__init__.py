"""
PV Test Report Automation - Image Data Ingestion & Processing Engine

This module provides comprehensive image processing capabilities for PV test lab automation,
including electroluminescence (EL) image analysis, visual inspection, OCR, and defect detection.
"""

from typing import List, Optional, Tuple
import numpy as np
from pydantic import BaseModel, Field


# Custom Exceptions
class ImageProcessingError(Exception):
    """Base exception for image processing errors."""
    pass


class ImageFormatError(ImageProcessingError):
    """Raised when image format is unsupported or corrupted."""
    pass


class ImageQualityError(ImageProcessingError):
    """Raised when image quality does not meet requirements."""
    pass


class MetadataExtractionError(ImageProcessingError):
    """Raised when EXIF/metadata extraction fails."""
    pass


class DefectDetectionError(ImageProcessingError):
    """Raised when defect detection fails."""
    pass


class OCRError(ImageProcessingError):
    """Raised when OCR processing fails."""
    pass


# Pydantic Models
class Defect(BaseModel):
    """Represents a detected defect in an image."""
    type: str = Field(..., description="Defect type: crack, dark_spot, inactive_cell, discoloration, bubble, burn_mark, etc.")
    severity: str = Field(..., description="Severity level: minor, moderate, severe")
    location: Tuple[int, int] = Field(..., description="Defect location (x, y) coordinates")
    area: float = Field(..., description="Defect area in pixels")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score 0-1")
    bounding_box: Optional[Tuple[int, int, int, int]] = Field(None, description="Bounding box (x, y, width, height)")

    class Config:
        arbitrary_types_allowed = True


class ImageMetadata(BaseModel):
    """Represents image metadata extracted from EXIF and other sources."""
    width: int
    height: int
    format: str
    color_mode: str
    dpi: Optional[Tuple[int, int]] = None
    exif_data: dict = Field(default_factory=dict)
    capture_date: Optional[str] = None
    camera_model: Optional[str] = None
    gps_coordinates: Optional[Tuple[float, float]] = None
    file_size: int

    class Config:
        arbitrary_types_allowed = True


class QualityMetrics(BaseModel):
    """Represents image quality validation metrics."""
    is_blurry: bool
    blur_score: float = Field(..., ge=0.0, description="Laplacian variance for blur detection")
    lighting_uniformity: float = Field(..., ge=0.0, le=1.0, description="Lighting uniformity score 0-1")
    contrast: float = Field(..., ge=0.0, description="RMS contrast")
    brightness: float = Field(..., ge=0.0, le=255.0, description="Mean brightness")
    meets_resolution_requirements: bool
    quality_passed: bool
    quality_errors: List[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True


class OCRResult(BaseModel):
    """Represents OCR extraction results."""
    text: str
    confidence: float = Field(..., ge=0.0, le=1.0, description="Average OCR confidence 0-1")
    bounding_boxes: List[Tuple[int, int, int, int]] = Field(default_factory=list, description="Text bounding boxes")
    extracted_values: dict = Field(default_factory=dict, description="Parsed numeric values with labels")

    class Config:
        arbitrary_types_allowed = True


class ImageIngestionResult(BaseModel):
    """Main result object for image ingestion and processing."""
    file_path: str
    file_hash: str = Field(..., description="SHA-256 hash for ISO 17025 traceability")
    metadata: ImageMetadata
    quality_metrics: QualityMetrics
    quality_passed: bool
    defects_detected: List[Defect] = Field(default_factory=list)
    ocr_result: Optional[OCRResult] = None
    processing_time: float = Field(..., description="Processing time in seconds")

    # Store processed images as separate files or references
    original_image_path: str
    processed_image_path: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


class ELImageResult(BaseModel):
    """Specialized result for electroluminescence image processing."""
    ingestion_result: ImageIngestionResult
    cell_count: int
    cell_locations: List[Tuple[int, int]] = Field(default_factory=list)
    cracks_detected: List[Defect] = Field(default_factory=list)
    dark_spots_detected: List[Defect] = Field(default_factory=list)
    inactive_cells: List[Tuple[int, int]] = Field(default_factory=list)
    overall_health_score: float = Field(..., ge=0.0, le=100.0, description="Overall module health 0-100")

    class Config:
        arbitrary_types_allowed = True


class VisualInspectionResult(BaseModel):
    """Specialized result for visual inspection processing."""
    ingestion_result: ImageIngestionResult
    discoloration_areas: List[Defect] = Field(default_factory=list)
    bubbles_detected: List[Defect] = Field(default_factory=list)
    burn_marks: List[Defect] = Field(default_factory=list)
    junction_box_damage: Optional[Defect] = None
    frame_damage: List[Defect] = Field(default_factory=list)
    color_corrected: bool

    class Config:
        arbitrary_types_allowed = True


class IVCurveData(BaseModel):
    """Represents extracted I-V curve data."""
    voc: float = Field(..., description="Open circuit voltage (V)")
    isc: float = Field(..., description="Short circuit current (A)")
    vmp: float = Field(..., description="Maximum power voltage (V)")
    imp: float = Field(..., description="Maximum power current (A)")
    pmax: float = Field(..., description="Maximum power (W)")
    fill_factor: float = Field(..., description="Fill factor")
    curve_points: List[Tuple[float, float]] = Field(default_factory=list, description="(V, I) data points")
    extraction_confidence: float = Field(..., ge=0.0, le=1.0)

    class Config:
        arbitrary_types_allowed = True


__all__ = [
    # Exceptions
    'ImageProcessingError',
    'ImageFormatError',
    'ImageQualityError',
    'MetadataExtractionError',
    'DefectDetectionError',
    'OCRError',
    # Models
    'Defect',
    'ImageMetadata',
    'QualityMetrics',
    'OCRResult',
    'ImageIngestionResult',
    'ELImageResult',
    'VisualInspectionResult',
    'IVCurveData',
]
