"""
Electroluminescence (EL) Image Processing for PV Module Defect Detection.

Advanced computer vision analysis for detecting defects in PV modules using
electroluminescence imaging:
- Micro-cracks in cells
- Cell interconnect failures
- Hot spots and degraded areas
- Busbar defects
- Inactive cell areas
- Shunt defects

Uses OpenCV and scikit-image for image processing with ISO 17025 compliance.
"""

import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from pydantic import BaseModel, Field
from skimage import filters, measure, morphology
from skimage.feature import canny

logger = logging.getLogger(__name__)


class DefectType(str, Enum):
    """Types of defects detected in EL images."""

    MICROCRACK = "microcrack"
    CELL_CRACK = "cell_crack"
    BUSBAR_DEFECT = "busbar_defect"
    INTERCONNECT_FAILURE = "interconnect_failure"
    INACTIVE_AREA = "inactive_area"
    HOT_SPOT = "hot_spot"
    SHUNT = "shunt"
    DEGRADED_CELL = "degraded_cell"
    EDGE_DEFECT = "edge_defect"


class DefectSeverity(str, Enum):
    """Severity classification for defects."""

    CRITICAL = "critical"  # Immediate failure risk
    MAJOR = "major"  # Significant performance impact
    MINOR = "minor"  # Limited performance impact
    NEGLIGIBLE = "negligible"  # Minimal impact


class ELImageConfig(BaseModel):
    """EL image processing configuration."""

    image_resolution_dpi: int = Field(default=300, description="Image resolution DPI")
    contrast_threshold: float = Field(default=0.3, description="Contrast threshold for defects")
    min_defect_area_px: int = Field(default=50, description="Minimum defect area (pixels)")
    max_defect_area_px: int = Field(default=10000, description="Maximum defect area (pixels)")
    edge_detection_sigma: float = Field(default=2.0, description="Canny edge detection sigma")
    morphology_kernel_size: int = Field(default=5, description="Morphological operation kernel")
    brightness_normalization: bool = Field(default=True, description="Normalize brightness")
    denoise: bool = Field(default=True, description="Apply denoising")
    enhance_contrast: bool = Field(default=True, description="Enhance contrast")


class DetectedDefect(BaseModel):
    """Individual defect detection result."""

    defect_id: str
    defect_type: DefectType
    severity: DefectSeverity
    location_x: int = Field(..., description="X coordinate (pixels)")
    location_y: int = Field(..., description="Y coordinate (pixels)")
    area_px: int = Field(..., description="Defect area (pixels)")
    area_mm2: Optional[float] = Field(None, description="Defect area (mm²)")
    bounding_box: Tuple[int, int, int, int] = Field(
        ..., description="Bounding box (x, y, width, height)"
    )
    intensity_mean: float = Field(..., description="Mean intensity in defect region")
    intensity_std: float = Field(..., description="Std deviation of intensity")
    perimeter_px: float = Field(..., description="Defect perimeter (pixels)")
    circularity: float = Field(..., description="Circularity measure (0-1)")
    notes: Optional[str] = None


class ELAnalysisResult(BaseModel):
    """Complete EL image analysis result."""

    image_path: str
    image_size: Tuple[int, int]
    total_defects: int
    defects_by_type: Dict[str, int]
    defects_by_severity: Dict[str, int]
    detected_defects: List[DetectedDefect]
    overall_quality_score: float = Field(..., description="Quality score 0-100")
    pass_fail: bool
    pass_criteria: str
    processing_time_seconds: float
    annotated_image_path: Optional[str] = None
    notes: Optional[str] = None


class ELImageProcessor:
    """
    Electroluminescence image processor for PV module defect detection.

    Uses advanced computer vision techniques for automated defect detection.
    """

    def __init__(self, config: ELImageConfig = ELImageConfig()):
        """
        Initialize EL image processor.

        Args:
            config: Image processing configuration
        """
        self.config = config

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess EL image for defect detection.

        Args:
            image: Input EL image (grayscale or BGR)

        Returns:
            Preprocessed grayscale image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Denoise
        if self.config.denoise:
            gray = cv2.fastNlMeansDenoising(gray, h=10)

        # Normalize brightness
        if self.config.brightness_normalization:
            gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)

        # Enhance contrast
        if self.config.enhance_contrast:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)

        return gray

    def detect_microcracks(self, image: np.ndarray) -> List[DetectedDefect]:
        """
        Detect micro-cracks using edge detection and morphological operations.

        Args:
            image: Preprocessed EL image

        Returns:
            List of detected micro-crack defects
        """
        defects = []

        # Edge detection
        edges = canny(
            image,
            sigma=self.config.edge_detection_sigma,
            low_threshold=0.1,
            high_threshold=0.3,
        )

        # Morphological closing to connect nearby edges
        kernel = morphology.square(3)
        closed = morphology.closing(edges, kernel)

        # Label connected components
        labeled = measure.label(closed)
        regions = measure.regionprops(labeled)

        for idx, region in enumerate(regions):
            area = region.area
            if self.config.min_defect_area_px < area < self.config.max_defect_area_px:
                # Check if it's likely a crack (elongated shape)
                if region.eccentricity > 0.9:  # Very elongated
                    y, x = region.centroid
                    bbox = region.bbox  # (min_row, min_col, max_row, max_col)

                    # Calculate circularity
                    perimeter = region.perimeter
                    circularity = (
                        (4 * np.pi * area) / (perimeter**2) if perimeter > 0 else 0
                    )

                    # Determine severity based on crack length
                    severity = self._classify_crack_severity(area, region.major_axis_length)

                    defect = DetectedDefect(
                        defect_id=f"CRACK_{idx:04d}",
                        defect_type=DefectType.MICROCRACK,
                        severity=severity,
                        location_x=int(x),
                        location_y=int(y),
                        area_px=int(area),
                        bounding_box=(bbox[1], bbox[0], bbox[3] - bbox[1], bbox[2] - bbox[0]),
                        intensity_mean=float(image[region.coords[:, 0], region.coords[:, 1]].mean()),
                        intensity_std=float(image[region.coords[:, 0], region.coords[:, 1]].std()),
                        perimeter_px=float(perimeter),
                        circularity=float(circularity),
                    )
                    defects.append(defect)

        logger.info(f"Detected {len(defects)} micro-cracks")
        return defects

    def detect_inactive_areas(self, image: np.ndarray) -> List[DetectedDefect]:
        """
        Detect inactive (dark) cell areas.

        Args:
            image: Preprocessed EL image

        Returns:
            List of detected inactive area defects
        """
        defects = []

        # Threshold for dark areas (inactive cells)
        mean_intensity = image.mean()
        threshold_value = mean_intensity * (1 - self.config.contrast_threshold)

        # Binary threshold
        _, binary = cv2.threshold(
            image, threshold_value, 255, cv2.THRESH_BINARY_INV
        )

        # Remove noise
        kernel = np.ones((self.config.morphology_kernel_size, self.config.morphology_kernel_size), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for idx, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if self.config.min_defect_area_px < area < self.config.max_defect_area_px:
                M = cv2.moments(contour)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])

                    x, y, w, h = cv2.boundingRect(contour)
                    perimeter = cv2.arcLength(contour, True)
                    circularity = (4 * np.pi * area) / (perimeter**2) if perimeter > 0 else 0

                    # Create mask for this region
                    mask = np.zeros_like(image)
                    cv2.drawContours(mask, [contour], -1, 255, -1)
                    region_pixels = image[mask == 255]

                    severity = self._classify_inactive_area_severity(area, region_pixels.mean())

                    defect = DetectedDefect(
                        defect_id=f"INACTIVE_{idx:04d}",
                        defect_type=DefectType.INACTIVE_AREA,
                        severity=severity,
                        location_x=cx,
                        location_y=cy,
                        area_px=int(area),
                        bounding_box=(x, y, w, h),
                        intensity_mean=float(region_pixels.mean()),
                        intensity_std=float(region_pixels.std()),
                        perimeter_px=float(perimeter),
                        circularity=float(circularity),
                    )
                    defects.append(defect)

        logger.info(f"Detected {len(defects)} inactive areas")
        return defects

    def detect_hotspots(self, image: np.ndarray) -> List[DetectedDefect]:
        """
        Detect hot spots (bright areas indicating localized heating).

        Args:
            image: Preprocessed EL image

        Returns:
            List of detected hot spot defects
        """
        defects = []

        # Threshold for bright areas (hot spots)
        mean_intensity = image.mean()
        threshold_value = mean_intensity * (1 + self.config.contrast_threshold)

        # Binary threshold
        _, binary = cv2.threshold(image, threshold_value, 255, cv2.THRESH_BINARY)

        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for idx, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if area > self.config.min_defect_area_px:
                M = cv2.moments(contour)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])

                    x, y, w, h = cv2.boundingRect(contour)
                    perimeter = cv2.arcLength(contour, True)
                    circularity = (4 * np.pi * area) / (perimeter**2) if perimeter > 0 else 0

                    # Create mask
                    mask = np.zeros_like(image)
                    cv2.drawContours(mask, [contour], -1, 255, -1)
                    region_pixels = image[mask == 255]

                    severity = DefectSeverity.CRITICAL  # Hot spots are always critical

                    defect = DetectedDefect(
                        defect_id=f"HOTSPOT_{idx:04d}",
                        defect_type=DefectType.HOT_SPOT,
                        severity=severity,
                        location_x=cx,
                        location_y=cy,
                        area_px=int(area),
                        bounding_box=(x, y, w, h),
                        intensity_mean=float(region_pixels.mean()),
                        intensity_std=float(region_pixels.std()),
                        perimeter_px=float(perimeter),
                        circularity=float(circularity),
                    )
                    defects.append(defect)

        logger.info(f"Detected {len(defects)} hot spots")
        return defects

    def _classify_crack_severity(
        self, area: float, length: float
    ) -> DefectSeverity:
        """Classify crack severity based on area and length."""
        if length > 500:  # pixels
            return DefectSeverity.CRITICAL
        elif length > 200:
            return DefectSeverity.MAJOR
        elif length > 100:
            return DefectSeverity.MINOR
        else:
            return DefectSeverity.NEGLIGIBLE

    def _classify_inactive_area_severity(
        self, area: float, mean_intensity: float
    ) -> DefectSeverity:
        """Classify inactive area severity."""
        if area > 5000 and mean_intensity < 30:
            return DefectSeverity.CRITICAL
        elif area > 2000 or mean_intensity < 50:
            return DefectSeverity.MAJOR
        elif area > 500:
            return DefectSeverity.MINOR
        else:
            return DefectSeverity.NEGLIGIBLE

    def analyze_image(
        self,
        image_path: str,
        output_dir: Optional[str] = None,
    ) -> ELAnalysisResult:
        """
        Perform complete EL image analysis.

        Args:
            image_path: Path to EL image file
            output_dir: Optional directory for annotated images

        Returns:
            Complete analysis result with all detected defects
        """
        start_time = datetime.utcnow()
        logger.info(f"Starting EL image analysis: {image_path}")

        # Load image
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")

        # Preprocess
        processed = self.preprocess_image(image)

        # Detect all defect types
        all_defects = []
        all_defects.extend(self.detect_microcracks(processed))
        all_defects.extend(self.detect_inactive_areas(processed))
        all_defects.extend(self.detect_hotspots(processed))

        # Aggregate statistics
        defects_by_type = {}
        defects_by_severity = {}

        for defect in all_defects:
            defects_by_type[defect.defect_type.value] = (
                defects_by_type.get(defect.defect_type.value, 0) + 1
            )
            defects_by_severity[defect.severity.value] = (
                defects_by_severity.get(defect.severity.value, 0) + 1
            )

        # Calculate quality score (0-100)
        quality_score = self._calculate_quality_score(all_defects, image.size)

        # Determine pass/fail (< 80 fails)
        pass_fail = quality_score >= 80

        # Generate annotated image
        annotated_path = None
        if output_dir:
            annotated_path = self._create_annotated_image(
                image, all_defects, output_dir, Path(image_path).stem
            )

        processing_time = (datetime.utcnow() - start_time).total_seconds()

        result = ELAnalysisResult(
            image_path=image_path,
            image_size=(image.shape[1], image.shape[0]),
            total_defects=len(all_defects),
            defects_by_type=defects_by_type,
            defects_by_severity=defects_by_severity,
            detected_defects=all_defects,
            overall_quality_score=round(quality_score, 2),
            pass_fail=pass_fail,
            pass_criteria="Quality score >= 80, no critical defects",
            processing_time_seconds=round(processing_time, 2),
            annotated_image_path=annotated_path,
        )

        logger.info(
            f"EL analysis completed: {len(all_defects)} defects, "
            f"Quality: {quality_score:.1f}, {'PASS' if pass_fail else 'FAIL'}"
        )

        return result

    def _calculate_quality_score(
        self, defects: List[DetectedDefect], image_size: int
    ) -> float:
        """Calculate overall quality score (0-100)."""
        # Start with perfect score
        score = 100.0

        # Deduct points based on defect severity
        severity_weights = {
            DefectSeverity.CRITICAL: 20,
            DefectSeverity.MAJOR: 10,
            DefectSeverity.MINOR: 3,
            DefectSeverity.NEGLIGIBLE: 1,
        }

        for defect in defects:
            score -= severity_weights[defect.severity]

        return max(0.0, score)

    def _create_annotated_image(
        self,
        image: np.ndarray,
        defects: List[DetectedDefect],
        output_dir: str,
        filename: str,
    ) -> str:
        """Create annotated image with defect overlays."""
        # Convert to BGR for color annotations
        annotated = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        # Color coding by severity
        severity_colors = {
            DefectSeverity.CRITICAL: (0, 0, 255),  # Red
            DefectSeverity.MAJOR: (0, 165, 255),  # Orange
            DefectSeverity.MINOR: (0, 255, 255),  # Yellow
            DefectSeverity.NEGLIGIBLE: (0, 255, 0),  # Green
        }

        for defect in defects:
            color = severity_colors[defect.severity]
            x, y, w, h = defect.bounding_box

            # Draw bounding box
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)

            # Add label
            label = f"{defect.defect_type.value[:4].upper()}"
            cv2.putText(
                annotated,
                label,
                (x, y - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
            )

        # Save annotated image
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_path = str(Path(output_dir) / f"{filename}_annotated.png")
        cv2.imwrite(output_path, annotated)

        return output_path
