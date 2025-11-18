"""
Electroluminescence (EL) Image Processor

Specialized processing for EL images including grayscale conversion,
normalization, defect detection, cell segmentation, and degradation analysis.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Union
from pathlib import Path
from skimage import measure, morphology, filters

from . import ELImageResult, Defect, ImageIngestionResult
from .image_processor import ImageProcessor
from .image_validators import ImageValidator
from .defect_detector import CrackDetector, DarkSpotDetector, InactiveCellDetector


class ELImageProcessor:
    """
    Specialized processor for electroluminescence (EL) images.

    Handles:
    - Grayscale conversion and normalization
    - Cell segmentation
    - Crack detection
    - Dark spot detection
    - Inactive cell identification
    - Overall health scoring
    """

    def __init__(
        self,
        base_processor: Optional[ImageProcessor] = None,
        validator: Optional[ImageValidator] = None
    ):
        """
        Initialize EL image processor.

        Args:
            base_processor: Base ImageProcessor instance
            validator: ImageValidator with EL-specific settings
        """
        # Use EL-specific resolution requirements
        if validator is None:
            validator = ImageValidator(
                min_resolution=(1920, 1080),  # Higher resolution for EL
                min_blur_threshold=120.0  # Stricter blur threshold
            )

        self.base_processor = base_processor or ImageProcessor(validator=validator)
        self.crack_detector = CrackDetector()
        self.dark_spot_detector = DarkSpotDetector()
        self.inactive_cell_detector = InactiveCellDetector()

    def process(
        self,
        file_path: Union[str, Path],
        detect_defects: bool = True,
        segment_cells: bool = True
    ) -> ELImageResult:
        """
        Complete EL image processing pipeline.

        Args:
            file_path: Path to EL image file
            detect_defects: Whether to perform defect detection
            segment_cells: Whether to perform cell segmentation

        Returns:
            ELImageResult with complete analysis
        """
        # Base ingestion and quality validation
        ingestion_result = self.base_processor.process_image(
            file_path,
            validate_quality=True
        )

        # Load and process image
        image = self.base_processor.load_image(file_path)

        # Convert to grayscale and normalize
        processed_image = self.convert_and_normalize(image)

        # Segment cells if requested
        cell_locations = []
        cell_count = 0

        if segment_cells:
            cell_locations = self.segment_cells(processed_image)
            cell_count = len(cell_locations)

        # Detect defects if requested
        cracks = []
        dark_spots = []
        inactive_cells = []
        all_defects = []

        if detect_defects:
            # Detect cracks
            cracks = self.crack_detector.detect_defects(processed_image)
            all_defects.extend(cracks)

            # Detect dark spots
            dark_spots = self.dark_spot_detector.detect_defects(processed_image)
            all_defects.extend(dark_spots)

            # Detect inactive cells (requires cell segmentation)
            if segment_cells and cell_locations:
                inactive_cell_defects = self.inactive_cell_detector.detect_defects(
                    processed_image,
                    cell_locations
                )
                all_defects.extend(inactive_cell_defects)

                # Extract inactive cell locations
                inactive_cells = [
                    defect.location for defect in inactive_cell_defects
                ]

        # Calculate overall health score
        health_score = self.calculate_health_score(
            cell_count=cell_count,
            cracks=cracks,
            dark_spots=dark_spots,
            inactive_cells=inactive_cells
        )

        # Update ingestion result with defects
        ingestion_result.defects_detected = all_defects

        return ELImageResult(
            ingestion_result=ingestion_result,
            cell_count=cell_count,
            cell_locations=cell_locations,
            cracks_detected=cracks,
            dark_spots_detected=dark_spots,
            inactive_cells=inactive_cells,
            overall_health_score=health_score
        )

    def convert_and_normalize(self, image: np.ndarray) -> np.ndarray:
        """
        Convert to grayscale and normalize EL image.

        Args:
            image: Input EL image (BGR or grayscale)

        Returns:
            Normalized grayscale image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Normalize to full dynamic range
        normalized = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)

        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(normalized)

        return enhanced

    def segment_cells(self, image: np.ndarray) -> List[Tuple[int, int]]:
        """
        Segment individual solar cells in EL image.

        Uses watershed algorithm and contour detection.

        Args:
            image: Normalized EL grayscale image

        Returns:
            List of (x, y) cell center coordinates
        """
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(image, (5, 5), 0)

        # Threshold to separate cells from background
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)

        # Sure background area
        sure_bg = cv2.dilate(opening, kernel, iterations=3)

        # Finding sure foreground area using distance transform
        dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
        _, sure_fg = cv2.threshold(dist_transform, 0.3 * dist_transform.max(), 255, 0)

        # Finding unknown region
        sure_fg = np.uint8(sure_fg)
        unknown = cv2.subtract(sure_bg, sure_fg)

        # Marker labelling
        _, markers = cv2.connectedComponents(sure_fg)

        # Add one to all labels so that sure background is not 0, but 1
        markers = markers + 1

        # Mark the region of unknown with zero
        markers[unknown == 255] = 0

        # Apply watershed
        # Need to convert to 3-channel for watershed
        image_color = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        markers = cv2.watershed(image_color, markers)

        # Extract cell centers
        cell_locations = []

        for label in range(2, markers.max() + 1):
            mask = (markers == label).astype(np.uint8) * 255

            # Calculate moments to get center
            M = cv2.moments(mask)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])

                # Verify this is a reasonable cell size
                area = M["m00"]
                if area > 1000:  # Minimum cell area
                    cell_locations.append((cx, cy))

        return cell_locations

    def classify_crack_type(
        self,
        crack_defect: Defect,
        image: np.ndarray
    ) -> str:
        """
        Classify crack type (finger interruption vs cell crack).

        Args:
            crack_defect: Detected crack defect
            image: EL image

        Returns:
            Crack type: "finger_interruption", "cell_crack", "unknown"
        """
        x, y, w, h = crack_defect.bounding_box

        # Extract crack region
        crack_roi = image[y:y+h, x:x+w]

        # Analyze orientation
        # Finger interruptions tend to be more linear/straight
        # Cell cracks tend to be more irregular

        aspect_ratio = max(w, h) / (min(w, h) + 1e-6)

        if aspect_ratio > 5:
            # Very elongated, likely finger interruption
            return "finger_interruption"
        elif aspect_ratio < 2:
            # More square-like, likely cell crack
            return "cell_crack"
        else:
            return "unknown"

    def calculate_health_score(
        self,
        cell_count: int,
        cracks: List[Defect],
        dark_spots: List[Defect],
        inactive_cells: List[Tuple[int, int]]
    ) -> float:
        """
        Calculate overall module health score (0-100).

        Args:
            cell_count: Total number of cells detected
            cracks: List of crack defects
            dark_spots: List of dark spot defects
            inactive_cells: List of inactive cell locations

        Returns:
            Health score 0-100 (100 = perfect health)
        """
        if cell_count == 0:
            # No cells detected, cannot assess health
            return 0.0

        # Start with perfect score
        score = 100.0

        # Deduct for inactive cells (most severe)
        inactive_ratio = len(inactive_cells) / cell_count
        score -= inactive_ratio * 50.0  # Up to 50 points

        # Deduct for cracks
        for crack in cracks:
            if crack.severity == "severe":
                score -= 10.0
            elif crack.severity == "moderate":
                score -= 5.0
            else:
                score -= 2.0

        # Deduct for dark spots
        for spot in dark_spots:
            if spot.severity == "severe":
                score -= 5.0
            elif spot.severity == "moderate":
                score -= 2.0
            else:
                score -= 1.0

        # Ensure score is in valid range
        score = max(0.0, min(100.0, score))

        return score

    def compare_degradation(
        self,
        before_image: Union[str, Path],
        after_image: Union[str, Path]
    ) -> dict:
        """
        Compare before/after EL images for degradation analysis.

        Args:
            before_image: Path to "before" EL image
            after_image: Path to "after" EL image

        Returns:
            Dictionary with degradation analysis
        """
        # Process both images
        before_result = self.process(before_image)
        after_result = self.process(after_image)

        # Calculate changes
        health_change = after_result.overall_health_score - before_result.overall_health_score
        new_cracks = len(after_result.cracks_detected) - len(before_result.cracks_detected)
        new_dark_spots = len(after_result.dark_spots_detected) - len(before_result.dark_spots_detected)
        new_inactive = len(after_result.inactive_cells) - len(before_result.inactive_cells)

        degradation_analysis = {
            "health_score_change": health_change,
            "before_health": before_result.overall_health_score,
            "after_health": after_result.overall_health_score,
            "new_cracks": new_cracks,
            "new_dark_spots": new_dark_spots,
            "new_inactive_cells": new_inactive,
            "degraded": health_change < -5.0,  # Significant degradation threshold
            "before_result": before_result,
            "after_result": after_result
        }

        return degradation_analysis


def create_annotated_image(
    image: np.ndarray,
    result: ELImageResult,
    show_cells: bool = True,
    show_defects: bool = True
) -> np.ndarray:
    """
    Create annotated version of EL image with defects and cells marked.

    Args:
        image: Original EL image
        result: ELImageResult from processing
        show_cells: Whether to show cell locations
        show_defects: Whether to show defect annotations

    Returns:
        Annotated image (BGR format)
    """
    # Convert to color if grayscale
    if len(image.shape) == 2:
        annotated = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    else:
        annotated = image.copy()

    # Draw cell centers
    if show_cells:
        for cx, cy in result.cell_locations:
            cv2.circle(annotated, (cx, cy), 5, (0, 255, 0), 2)

    # Draw defects
    if show_defects:
        # Cracks in red
        for crack in result.cracks_detected:
            x, y, w, h = crack.bounding_box
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(annotated, "CRACK", (x, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        # Dark spots in yellow
        for spot in result.dark_spots_detected:
            x, y, w, h = spot.bounding_box
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 255), 2)
            cv2.putText(annotated, "DARK", (x, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # Inactive cells in blue
        for cx, cy in result.inactive_cells:
            cv2.circle(annotated, (cx, cy), 15, (255, 0, 0), 3)
            cv2.putText(annotated, "INACTIVE", (cx - 30, cy - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

    # Add health score
    health_text = f"Health Score: {result.overall_health_score:.1f}/100"
    cv2.putText(annotated, health_text, (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    return annotated


__all__ = [
    'ELImageProcessor',
    'create_annotated_image',
]
