"""
Defect Detection Module

Provides advanced defect detection algorithms for PV modules including
crack detection, dark spots, inactive cells, discoloration, bubbles, and burn marks.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from scipy import ndimage
from skimage import measure, morphology, filters

from . import Defect, DefectDetectionError


class DefectDetector:
    """Base class for defect detection in PV module images."""

    def __init__(self):
        """Initialize defect detector."""
        pass

    def detect_defects(self, image: np.ndarray) -> List[Defect]:
        """
        Detect all types of defects in an image.

        Args:
            image: Input image (BGR or grayscale)

        Returns:
            List of detected defects

        Raises:
            DefectDetectionError: If detection fails
        """
        raise NotImplementedError("Subclass must implement detect_defects()")

    def _calculate_confidence(self, feature_score: float, threshold: float) -> float:
        """
        Calculate confidence score based on feature strength.

        Args:
            feature_score: Measured feature value
            threshold: Detection threshold

        Returns:
            Confidence score 0-1
        """
        if feature_score <= threshold:
            return 0.0

        # Normalize to 0-1 range with sigmoid-like curve
        confidence = min(1.0, (feature_score - threshold) / threshold)
        return confidence


class CrackDetector(DefectDetector):
    """Detect cracks in EL images using edge detection and morphological operations."""

    def __init__(
        self,
        canny_threshold1: int = 50,
        canny_threshold2: int = 150,
        min_crack_length: int = 20,
        min_crack_area: float = 10.0
    ):
        """
        Initialize crack detector.

        Args:
            canny_threshold1: Lower threshold for Canny edge detection
            canny_threshold2: Upper threshold for Canny edge detection
            min_crack_length: Minimum crack length in pixels
            min_crack_area: Minimum crack area in pixels
        """
        super().__init__()
        self.canny_threshold1 = canny_threshold1
        self.canny_threshold2 = canny_threshold2
        self.min_crack_length = min_crack_length
        self.min_crack_area = min_crack_area

    def detect_defects(self, image: np.ndarray) -> List[Defect]:
        """
        Detect cracks in EL image.

        Args:
            image: EL image (grayscale or BGR)

        Returns:
            List of crack defects
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Detect edges using Canny
        edges = cv2.Canny(enhanced, self.canny_threshold1, self.canny_threshold2)

        # Morphological operations to connect crack segments
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(edges, kernel, iterations=1)

        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        defects = []

        for contour in contours:
            area = cv2.contourArea(contour)

            if area < self.min_crack_area:
                continue

            # Calculate crack length (perimeter is a good proxy)
            perimeter = cv2.arcLength(contour, False)

            if perimeter < self.min_crack_length:
                continue

            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)

            # Calculate center point
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            else:
                cx, cy = x + w // 2, y + h // 2

            # Classify crack severity based on length and area
            severity = self._classify_crack_severity(perimeter, area)

            # Calculate confidence based on edge strength
            roi = edges[y:y+h, x:x+w]
            edge_density = np.sum(roi > 0) / (w * h) if w * h > 0 else 0
            confidence = min(1.0, edge_density * 5)  # Scale to 0-1

            defects.append(Defect(
                type="crack",
                severity=severity,
                location=(cx, cy),
                area=area,
                confidence=confidence,
                bounding_box=(x, y, w, h)
            ))

        return defects

    def _classify_crack_severity(self, length: float, area: float) -> str:
        """
        Classify crack severity based on length and area.

        Args:
            length: Crack length in pixels
            area: Crack area in pixels

        Returns:
            Severity level: "minor", "moderate", "severe"
        """
        # Thresholds (adjustable based on image resolution and requirements)
        if length > 100 or area > 500:
            return "severe"
        elif length > 50 or area > 200:
            return "moderate"
        else:
            return "minor"


class DarkSpotDetector(DefectDetector):
    """Detect dark spots and inactive areas in EL images."""

    def __init__(
        self,
        intensity_threshold: int = 40,
        min_spot_area: float = 50.0,
        max_spot_area: float = 5000.0
    ):
        """
        Initialize dark spot detector.

        Args:
            intensity_threshold: Maximum intensity for dark regions
            min_spot_area: Minimum spot area in pixels
            max_spot_area: Maximum spot area in pixels
        """
        super().__init__()
        self.intensity_threshold = intensity_threshold
        self.min_spot_area = min_spot_area
        self.max_spot_area = max_spot_area

    def detect_defects(self, image: np.ndarray) -> List[Defect]:
        """
        Detect dark spots in EL image.

        Args:
            image: EL image (grayscale or BGR)

        Returns:
            List of dark spot defects
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Threshold to find dark regions
        _, binary = cv2.threshold(blurred, self.intensity_threshold, 255, cv2.THRESH_BINARY_INV)

        # Remove small noise with morphological opening
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        # Find contours
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        defects = []

        for contour in contours:
            area = cv2.contourArea(contour)

            if area < self.min_spot_area or area > self.max_spot_area:
                continue

            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)

            # Calculate center point
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            else:
                cx, cy = x + w // 2, y + h // 2

            # Calculate mean intensity in the spot
            mask = np.zeros_like(gray)
            cv2.drawContours(mask, [contour], -1, 255, -1)
            mean_intensity = cv2.mean(gray, mask=mask)[0]

            # Classify severity based on darkness
            severity = self._classify_spot_severity(mean_intensity, area)

            # Calculate confidence (darker = higher confidence)
            confidence = 1.0 - (mean_intensity / self.intensity_threshold)
            confidence = max(0.0, min(1.0, confidence))

            defects.append(Defect(
                type="dark_spot",
                severity=severity,
                location=(cx, cy),
                area=area,
                confidence=confidence,
                bounding_box=(x, y, w, h)
            ))

        return defects

    def _classify_spot_severity(self, intensity: float, area: float) -> str:
        """
        Classify dark spot severity.

        Args:
            intensity: Mean intensity of the spot
            area: Spot area in pixels

        Returns:
            Severity level: "minor", "moderate", "severe"
        """
        # Very dark or large spots are severe
        if intensity < 20 or area > 2000:
            return "severe"
        elif intensity < 30 or area > 500:
            return "moderate"
        else:
            return "minor"


class InactiveCellDetector(DefectDetector):
    """Detect inactive/dead cells in EL images."""

    def __init__(self, cell_intensity_threshold: int = 30):
        """
        Initialize inactive cell detector.

        Args:
            cell_intensity_threshold: Maximum mean intensity for inactive cells
        """
        super().__init__()
        self.cell_intensity_threshold = cell_intensity_threshold

    def detect_defects(self, image: np.ndarray, cell_locations: List[Tuple[int, int]]) -> List[Defect]:
        """
        Detect inactive cells based on known cell locations.

        Args:
            image: EL image (grayscale or BGR)
            cell_locations: List of (x, y) cell center coordinates

        Returns:
            List of inactive cell defects
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        defects = []

        # Estimate cell size (assuming uniform grid)
        if len(cell_locations) < 2:
            cell_size = 100  # Default
        else:
            # Calculate average distance between cells
            distances = []
            for i in range(min(10, len(cell_locations) - 1)):
                x1, y1 = cell_locations[i]
                x2, y2 = cell_locations[i + 1]
                dist = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                distances.append(dist)
            cell_size = int(np.mean(distances)) if distances else 100

        # Check each cell
        for cx, cy in cell_locations:
            # Define cell region (approximate)
            half_size = cell_size // 2
            x1 = max(0, cx - half_size)
            y1 = max(0, cy - half_size)
            x2 = min(gray.shape[1], cx + half_size)
            y2 = min(gray.shape[0], cy + half_size)

            cell_region = gray[y1:y2, x1:x2]

            if cell_region.size == 0:
                continue

            mean_intensity = np.mean(cell_region)

            # Check if cell is inactive
            if mean_intensity < self.cell_intensity_threshold:
                severity = "severe" if mean_intensity < 15 else "moderate"
                confidence = 1.0 - (mean_intensity / self.cell_intensity_threshold)

                area = (x2 - x1) * (y2 - y1)

                defects.append(Defect(
                    type="inactive_cell",
                    severity=severity,
                    location=(cx, cy),
                    area=area,
                    confidence=confidence,
                    bounding_box=(x1, y1, x2 - x1, y2 - y1)
                ))

        return defects


class DiscolorationDetector(DefectDetector):
    """Detect discoloration (browning, yellowing) in visual inspection images."""

    def __init__(self):
        """Initialize discoloration detector."""
        super().__init__()

    def detect_defects(self, image: np.ndarray) -> List[Defect]:
        """
        Detect discoloration in visual inspection image.

        Args:
            image: Visual inspection image (BGR)

        Returns:
            List of discoloration defects
        """
        if len(image.shape) != 3:
            raise DefectDetectionError("Discoloration detection requires color image")

        # Convert to HSV for better color analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Define color ranges for browning/yellowing
        # Yellow-brown range in HSV
        lower_brown = np.array([10, 50, 50])
        upper_brown = np.array([30, 255, 200])

        # Create mask for discolored areas
        mask = cv2.inRange(hsv, lower_brown, upper_brown)

        # Remove small noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        defects = []

        for contour in contours:
            area = cv2.contourArea(contour)

            if area < 100:  # Minimum area
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

            # Classify severity based on area and color intensity
            severity = "severe" if area > 5000 else "moderate" if area > 1000 else "minor"

            # Calculate confidence based on color saturation
            roi_hsv = hsv[y:y+h, x:x+w]
            mean_saturation = np.mean(roi_hsv[:, :, 1])
            confidence = min(1.0, mean_saturation / 128.0)

            defects.append(Defect(
                type="discoloration",
                severity=severity,
                location=(cx, cy),
                area=area,
                confidence=confidence,
                bounding_box=(x, y, w, h)
            ))

        return defects


class BubbleDetector(DefectDetector):
    """Detect bubbles and delamination in visual inspection images."""

    def __init__(self, min_bubble_area: float = 50.0):
        """
        Initialize bubble detector.

        Args:
            min_bubble_area: Minimum bubble area in pixels
        """
        super().__init__()
        self.min_bubble_area = min_bubble_area

    def detect_defects(self, image: np.ndarray) -> List[Defect]:
        """
        Detect bubbles/delamination in visual inspection image.

        Args:
            image: Visual inspection image (BGR or grayscale)

        Returns:
            List of bubble defects
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)

        # Detect circles using Hough Circle Transform
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=20,
            param1=50,
            param2=30,
            minRadius=5,
            maxRadius=100
        )

        defects = []

        if circles is not None:
            circles = np.uint16(np.around(circles))

            for circle in circles[0, :]:
                cx, cy, radius = circle
                area = np.pi * radius * radius

                if area < self.min_bubble_area:
                    continue

                # Classify severity based on size
                severity = "severe" if radius > 50 else "moderate" if radius > 20 else "minor"

                # Calculate confidence based on circularity
                confidence = 0.8  # Hough circles are fairly reliable

                defects.append(Defect(
                    type="bubble",
                    severity=severity,
                    location=(int(cx), int(cy)),
                    area=area,
                    confidence=confidence,
                    bounding_box=(int(cx - radius), int(cy - radius), int(2 * radius), int(2 * radius))
                ))

        return defects


def detect_defects(
    image: np.ndarray,
    defect_types: Optional[List[str]] = None,
    cell_locations: Optional[List[Tuple[int, int]]] = None
) -> List[Defect]:
    """
    Convenience function to detect multiple defect types.

    Args:
        image: Input image
        defect_types: List of defect types to detect (None = all)
        cell_locations: Cell locations for inactive cell detection

    Returns:
        Combined list of all detected defects
    """
    all_defects = []

    if defect_types is None:
        defect_types = ["crack", "dark_spot", "discoloration", "bubble"]

    if "crack" in defect_types:
        detector = CrackDetector()
        all_defects.extend(detector.detect_defects(image))

    if "dark_spot" in defect_types:
        detector = DarkSpotDetector()
        all_defects.extend(detector.detect_defects(image))

    if "inactive_cell" in defect_types and cell_locations:
        detector = InactiveCellDetector()
        all_defects.extend(detector.detect_defects(image, cell_locations))

    if "discoloration" in defect_types and len(image.shape) == 3:
        detector = DiscolorationDetector()
        all_defects.extend(detector.detect_defects(image))

    if "bubble" in defect_types:
        detector = BubbleDetector()
        all_defects.extend(detector.detect_defects(image))

    return all_defects


__all__ = [
    'DefectDetector',
    'CrackDetector',
    'DarkSpotDetector',
    'InactiveCellDetector',
    'DiscolorationDetector',
    'BubbleDetector',
    'detect_defects',
]
