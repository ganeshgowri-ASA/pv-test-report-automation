"""
Visual Inspection Analyzer

Specialized processing for visual inspection images including color correction,
discoloration detection, bubble detection, burn marks, and junction box/frame damage.
"""

import cv2
import numpy as np
from typing import List, Optional, Union, Tuple
from pathlib import Path

from . import VisualInspectionResult, Defect, ImageIngestionResult
from .image_processor import ImageProcessor
from .image_validators import ImageValidator
from .defect_detector import DiscolorationDetector, BubbleDetector


class VisualInspector:
    """
    Specialized analyzer for visual inspection images.

    Handles:
    - Color correction and enhancement
    - Discoloration detection (browning, yellowing)
    - Bubble/delamination detection
    - Burn mark identification
    - Junction box damage detection
    - Frame/edge damage assessment
    """

    def __init__(
        self,
        base_processor: Optional[ImageProcessor] = None,
        validator: Optional[ImageValidator] = None
    ):
        """
        Initialize visual inspector.

        Args:
            base_processor: Base ImageProcessor instance
            validator: ImageValidator with visual inspection settings
        """
        # Use visual inspection resolution requirements
        if validator is None:
            validator = ImageValidator(
                min_resolution=(1280, 720),
                min_blur_threshold=80.0
            )

        self.base_processor = base_processor or ImageProcessor(validator=validator)
        self.discoloration_detector = DiscolorationDetector()
        self.bubble_detector = BubbleDetector()

    def process(
        self,
        file_path: Union[str, Path],
        detect_defects: bool = True,
        apply_color_correction: bool = True
    ) -> VisualInspectionResult:
        """
        Complete visual inspection processing pipeline.

        Args:
            file_path: Path to visual inspection image
            detect_defects: Whether to perform defect detection
            apply_color_correction: Whether to apply color correction

        Returns:
            VisualInspectionResult with complete analysis
        """
        # Base ingestion and quality validation
        ingestion_result = self.base_processor.process_image(
            file_path,
            validate_quality=True
        )

        # Load image
        image = self.base_processor.load_image(file_path)

        # Apply color correction if requested
        color_corrected = False
        if apply_color_correction and len(image.shape) == 3:
            image = self.color_correct(image)
            color_corrected = True

        # Detect defects
        discoloration_areas = []
        bubbles = []
        burn_marks = []
        junction_box_damage = None
        frame_damage = []
        all_defects = []

        if detect_defects:
            # Detect discoloration
            if len(image.shape) == 3:
                discoloration_areas = self.discoloration_detector.detect_defects(image)
                all_defects.extend(discoloration_areas)

            # Detect bubbles
            bubbles = self.bubble_detector.detect_defects(image)
            all_defects.extend(bubbles)

            # Detect burn marks
            burn_marks = self.detect_burn_marks(image)
            all_defects.extend(burn_marks)

            # Detect junction box damage
            junction_box_damage = self.detect_junction_box_damage(image)
            if junction_box_damage:
                all_defects.append(junction_box_damage)

            # Detect frame damage
            frame_damage = self.detect_frame_damage(image)
            all_defects.extend(frame_damage)

        # Update ingestion result with defects
        ingestion_result.defects_detected = all_defects

        return VisualInspectionResult(
            ingestion_result=ingestion_result,
            discoloration_areas=discoloration_areas,
            bubbles_detected=bubbles,
            burn_marks=burn_marks,
            junction_box_damage=junction_box_damage,
            frame_damage=frame_damage,
            color_corrected=color_corrected
        )

    def color_correct(self, image: np.ndarray) -> np.ndarray:
        """
        Apply automatic color correction and white balance.

        Args:
            image: Input BGR image

        Returns:
            Color-corrected BGR image
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

        # Split channels
        l, a, b = cv2.split(lab)

        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)

        # Merge channels
        lab = cv2.merge([l, a, b])

        # Convert back to BGR
        corrected = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        # Apply simple white balance (gray world assumption)
        corrected = self._white_balance(corrected)

        return corrected

    def _white_balance(self, image: np.ndarray) -> np.ndarray:
        """
        Apply white balance using gray world algorithm.

        Args:
            image: Input BGR image

        Returns:
            White-balanced BGR image
        """
        result = image.copy()

        # Calculate average for each channel
        avg_b = np.mean(result[:, :, 0])
        avg_g = np.mean(result[:, :, 1])
        avg_r = np.mean(result[:, :, 2])

        # Calculate global average
        avg_gray = (avg_b + avg_g + avg_r) / 3.0

        # Calculate scaling factors
        if avg_b > 0:
            scale_b = avg_gray / avg_b
        else:
            scale_b = 1.0

        if avg_g > 0:
            scale_g = avg_gray / avg_g
        else:
            scale_g = 1.0

        if avg_r > 0:
            scale_r = avg_gray / avg_r
        else:
            scale_r = 1.0

        # Apply scaling
        result[:, :, 0] = np.clip(result[:, :, 0] * scale_b, 0, 255)
        result[:, :, 1] = np.clip(result[:, :, 1] * scale_g, 0, 255)
        result[:, :, 2] = np.clip(result[:, :, 2] * scale_r, 0, 255)

        return result.astype(np.uint8)

    def detect_burn_marks(self, image: np.ndarray) -> List[Defect]:
        """
        Detect burn marks in visual inspection image.

        Burn marks typically appear as very dark spots with high contrast.

        Args:
            image: Visual inspection image (BGR or grayscale)

        Returns:
            List of burn mark defects
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Threshold for very dark regions
        _, binary = cv2.threshold(gray, 40, 255, cv2.THRESH_BINARY_INV)

        # Remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        # Find contours
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        defects = []

        for contour in contours:
            area = cv2.contourArea(contour)

            if area < 50:  # Minimum burn mark area
                continue

            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)

            # Calculate center
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            else:
                cx, cy = x + w // 2, y + h // 2

            # Check if it's really dark (burn marks are very dark)
            mask = np.zeros_like(gray)
            cv2.drawContours(mask, [contour], -1, 255, -1)
            mean_intensity = cv2.mean(gray, mask=mask)[0]

            if mean_intensity > 30:  # Not dark enough to be a burn mark
                continue

            # All burn marks are considered severe
            severity = "severe"

            # Calculate confidence based on darkness
            confidence = 1.0 - (mean_intensity / 30.0)

            defects.append(Defect(
                type="burn_mark",
                severity=severity,
                location=(cx, cy),
                area=area,
                confidence=confidence,
                bounding_box=(x, y, w, h)
            ))

        return defects

    def detect_junction_box_damage(self, image: np.ndarray) -> Optional[Defect]:
        """
        Detect junction box damage in visual inspection image.

        This is a simplified implementation that looks for damage in the
        typical junction box location (center-back of module).

        Args:
            image: Visual inspection image (BGR or grayscale)

        Returns:
            Junction box damage defect or None
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        h, w = gray.shape

        # Typical junction box location (center, can be adjusted)
        box_x = w // 2 - w // 8
        box_y = h // 2 - h // 8
        box_w = w // 4
        box_h = h // 4

        # Extract junction box region
        roi = gray[box_y:box_y+box_h, box_x:box_x+box_w]

        if roi.size == 0:
            return None

        # Look for anomalies in junction box area
        # Check for very dark regions (potential damage)
        _, binary = cv2.threshold(roi, 50, 255, cv2.THRESH_BINARY_INV)

        damage_pixels = np.sum(binary > 0)
        total_pixels = box_w * box_h

        damage_ratio = damage_pixels / total_pixels if total_pixels > 0 else 0

        # If more than 10% of junction box area is dark, consider it damaged
        if damage_ratio > 0.10:
            severity = "severe" if damage_ratio > 0.3 else "moderate"
            confidence = min(1.0, damage_ratio * 2)

            return Defect(
                type="junction_box_damage",
                severity=severity,
                location=(box_x + box_w // 2, box_y + box_h // 2),
                area=float(damage_pixels),
                confidence=confidence,
                bounding_box=(box_x, box_y, box_w, box_h)
            )

        return None

    def detect_frame_damage(self, image: np.ndarray) -> List[Defect]:
        """
        Detect frame/edge damage in visual inspection image.

        Args:
            image: Visual inspection image (BGR or grayscale)

        Returns:
            List of frame damage defects
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        h, w = gray.shape

        # Define edge regions (top, bottom, left, right)
        edge_width = min(50, w // 10)
        edge_height = min(50, h // 10)

        edges = {
            'top': gray[0:edge_height, :],
            'bottom': gray[h-edge_height:h, :],
            'left': gray[:, 0:edge_width],
            'right': gray[:, w-edge_width:w]
        }

        defects = []

        for edge_name, edge_roi in edges.items():
            if edge_roi.size == 0:
                continue

            # Detect edges using Canny
            edge_detected = cv2.Canny(edge_roi, 50, 150)

            # Count edge pixels
            edge_pixels = np.sum(edge_detected > 0)
            total_pixels = edge_roi.shape[0] * edge_roi.shape[1]

            edge_ratio = edge_pixels / total_pixels if total_pixels > 0 else 0

            # High edge density might indicate damage/deformation
            if edge_ratio > 0.15:
                # Determine location based on edge name
                if edge_name == 'top':
                    location = (w // 2, edge_height // 2)
                    bbox = (0, 0, w, edge_height)
                elif edge_name == 'bottom':
                    location = (w // 2, h - edge_height // 2)
                    bbox = (0, h - edge_height, w, edge_height)
                elif edge_name == 'left':
                    location = (edge_width // 2, h // 2)
                    bbox = (0, 0, edge_width, h)
                else:  # right
                    location = (w - edge_width // 2, h // 2)
                    bbox = (w - edge_width, 0, edge_width, h)

                severity = "moderate" if edge_ratio > 0.25 else "minor"
                confidence = min(1.0, edge_ratio * 3)

                defects.append(Defect(
                    type="frame_damage",
                    severity=severity,
                    location=location,
                    area=float(edge_pixels),
                    confidence=confidence,
                    bounding_box=bbox
                ))

        return defects

    def enhance_image(self, image: np.ndarray) -> np.ndarray:
        """
        Apply general image enhancement for better visibility.

        Args:
            image: Input image (BGR or grayscale)

        Returns:
            Enhanced image
        """
        if len(image.shape) == 3:
            # Color image enhancement
            enhanced = self.color_correct(image)

            # Sharpen
            kernel = np.array([[-1, -1, -1],
                             [-1,  9, -1],
                             [-1, -1, -1]])
            enhanced = cv2.filter2D(enhanced, -1, kernel)

        else:
            # Grayscale enhancement
            # Apply CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(image)

            # Sharpen
            kernel = np.array([[-1, -1, -1],
                             [-1,  9, -1],
                             [-1, -1, -1]])
            enhanced = cv2.filter2D(enhanced, -1, kernel)

        return enhanced


def create_annotated_visual_image(
    image: np.ndarray,
    result: VisualInspectionResult,
    show_defects: bool = True
) -> np.ndarray:
    """
    Create annotated version of visual inspection image with defects marked.

    Args:
        image: Original visual inspection image
        result: VisualInspectionResult from processing
        show_defects: Whether to show defect annotations

    Returns:
        Annotated image (BGR format)
    """
    # Convert to color if grayscale
    if len(image.shape) == 2:
        annotated = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    else:
        annotated = image.copy()

    if not show_defects:
        return annotated

    # Draw discoloration areas in orange
    for defect in result.discoloration_areas:
        x, y, w, h = defect.bounding_box
        cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 165, 255), 2)
        cv2.putText(annotated, "DISCOLOR", (x, y - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1)

    # Draw bubbles in cyan
    for defect in result.bubbles_detected:
        x, y, w, h = defect.bounding_box
        cv2.rectangle(annotated, (x, y), (x + w, y + h), (255, 255, 0), 2)
        cv2.putText(annotated, "BUBBLE", (x, y - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

    # Draw burn marks in red
    for defect in result.burn_marks:
        x, y, w, h = defect.bounding_box
        cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 0, 255), 3)
        cv2.putText(annotated, "BURN", (x, y - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    # Draw junction box damage in magenta
    if result.junction_box_damage:
        x, y, w, h = result.junction_box_damage.bounding_box
        cv2.rectangle(annotated, (x, y), (x + w, y + h), (255, 0, 255), 3)
        cv2.putText(annotated, "J-BOX DAMAGE", (x, y - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)

    # Draw frame damage in blue
    for defect in result.frame_damage:
        x, y, w, h = defect.bounding_box
        cv2.rectangle(annotated, (x, y), (x + w, y + h), (255, 0, 0), 2)
        cv2.putText(annotated, "FRAME", (x, y - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

    # Add summary
    total_defects = len(result.ingestion_result.defects_detected)
    summary_text = f"Total Defects: {total_defects}"
    cv2.putText(annotated, summary_text, (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    return annotated


__all__ = [
    'VisualInspector',
    'create_annotated_visual_image',
]
