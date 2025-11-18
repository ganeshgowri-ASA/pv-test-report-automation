"""Defect detection module for PV cell and module images

Implements defect detection algorithms for:
- Electroluminescence (EL) images
- Visual inspection images
- Thermal images

Based on:
- IEC 60904-13: Electroluminescence of photovoltaic modules
- IEC TS 62804: Test methods for detection of potential-induced degradation
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
import logging

from .models import Defect, DefectType, DefectSeverity, ImageType, ProcessingConfig

logger = logging.getLogger(__name__)


class DefectDetector:
    """Detects defects in PV module and cell images"""

    def __init__(self, config: Optional[ProcessingConfig] = None):
        """Initialize defect detector

        Args:
            config: Processing configuration
        """
        self.config = config or ProcessingConfig()

    def detect_defects(
        self,
        image: np.ndarray,
        image_type: ImageType,
        preprocessed: Optional[np.ndarray] = None
    ) -> List[Defect]:
        """Detect defects in an image based on image type

        Args:
            image: Input image
            image_type: Type of image (EL, thermal, visual, etc.)
            preprocessed: Preprocessed/enhanced version of image

        Returns:
            List of detected defects
        """
        if preprocessed is None:
            preprocessed = image

        defects = []

        if image_type == ImageType.EL:
            defects.extend(self._detect_el_defects(preprocessed))
        elif image_type == ImageType.THERMAL:
            defects.extend(self._detect_thermal_defects(preprocessed))
        elif image_type == ImageType.VISUAL:
            defects.extend(self._detect_visual_defects(preprocessed))

        logger.info(f"Detected {len(defects)} defects in {image_type.value} image")
        return defects

    def _detect_el_defects(self, image: np.ndarray) -> List[Defect]:
        """Detect defects in electroluminescence images

        EL imaging reveals:
        - Cracks (dark lines)
        - Inactive areas (dark spots)
        - Cell breakage
        - Finger interruptions
        - PID effects

        Args:
            image: EL image (grayscale or preprocessed)

        Returns:
            List of detected defects
        """
        defects = []

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Detect cracks
        defects.extend(self._detect_cracks(gray))

        # Detect dark spots (inactive areas)
        defects.extend(self._detect_dark_spots(gray))

        # Detect finger interruptions
        defects.extend(self._detect_finger_interruptions(gray))

        return defects

    def _detect_cracks(self, gray: np.ndarray) -> List[Defect]:
        """Detect cracks using edge detection and line detection

        Args:
            gray: Grayscale image

        Returns:
            List of crack defects
        """
        defects = []

        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)

        # Apply morphological operations to connect crack segments
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

        # Detect lines using Hough transform
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi/180,
            threshold=50,
            minLineLength=30,
            maxLineGap=10
        )

        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]

                # Calculate line properties
                length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                angle = np.abs(np.arctan2(y2-y1, x2-x1) * 180 / np.pi)

                # Filter based on length and angle
                # Cracks are typically long and at various angles
                if length > 50:
                    # Create bounding box
                    x_min = min(x1, x2)
                    y_min = min(y1, y2)
                    width = abs(x2 - x1) + 10
                    height = abs(y2 - y1) + 10

                    # Determine severity based on length
                    if length > 200:
                        severity = DefectSeverity.CRITICAL
                    elif length > 150:
                        severity = DefectSeverity.HIGH
                    elif length > 100:
                        severity = DefectSeverity.MEDIUM
                    else:
                        severity = DefectSeverity.LOW

                    defect = Defect(
                        defect_type=DefectType.CRACK,
                        severity=severity,
                        location=(int(x_min), int(y_min), int(width), int(height)),
                        confidence=0.7,
                        area_pixels=int(length * 2),  # Approximate area
                        description=f"Linear crack, length={length:.1f}px, angle={angle:.1f}°"
                    )
                    defects.append(defect)

        return defects

    def _detect_dark_spots(self, gray: np.ndarray) -> List[Defect]:
        """Detect dark spots (inactive cell regions)

        Args:
            gray: Grayscale image

        Returns:
            List of dark spot defects
        """
        defects = []

        # Calculate adaptive threshold based on image statistics
        mean_intensity = np.mean(gray)
        threshold_value = mean_intensity * self.config.dark_spot_threshold

        # Threshold to find dark regions
        _, binary = cv2.threshold(
            gray,
            threshold_value,
            255,
            cv2.THRESH_BINARY_INV
        )

        # Remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        # Find contours
        contours, _ = cv2.findContours(
            binary,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        for contour in contours:
            area = cv2.contourArea(contour)

            # Filter by minimum area
            if area >= self.config.min_defect_area:
                # Get bounding box
                x, y, w, h = cv2.boundingRect(contour)

                # Calculate defect properties
                mask = np.zeros_like(gray)
                cv2.drawContours(mask, [contour], -1, 255, -1)
                mean_val = cv2.mean(gray, mask=mask)[0]

                # Determine severity based on area and darkness
                darkness_ratio = 1.0 - (mean_val / mean_intensity)

                if area > 5000 or darkness_ratio > 0.7:
                    severity = DefectSeverity.CRITICAL
                elif area > 2000 or darkness_ratio > 0.5:
                    severity = DefectSeverity.HIGH
                elif area > 1000 or darkness_ratio > 0.3:
                    severity = DefectSeverity.MEDIUM
                else:
                    severity = DefectSeverity.LOW

                defect = Defect(
                    defect_type=DefectType.DARK_SPOT,
                    severity=severity,
                    location=(int(x), int(y), int(w), int(h)),
                    confidence=0.8,
                    area_pixels=int(area),
                    description=f"Inactive area, {area}px², darkness={darkness_ratio:.2%}"
                )
                defects.append(defect)

        return defects

    def _detect_finger_interruptions(self, gray: np.ndarray) -> List[Defect]:
        """Detect interruptions in cell fingers/busbars

        Args:
            gray: Grayscale image

        Returns:
            List of finger interruption defects
        """
        defects = []

        # Apply morphological operations to enhance linear structures
        kernel_vert = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 15))
        kernel_horiz = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1))

        # Detect vertical structures (fingers)
        vert = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel_vert)
        vert = cv2.morphologyEx(vert, cv2.MORPH_OPEN, kernel_vert)

        # Threshold to find breaks
        mean_val = np.mean(vert)
        _, binary = cv2.threshold(
            vert,
            mean_val * 0.5,
            255,
            cv2.THRESH_BINARY_INV
        )

        # Find contours of interruptions
        contours, _ = cv2.findContours(
            binary,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        for contour in contours:
            area = cv2.contourArea(contour)

            if area >= 50 and area <= 2000:  # Typical interruption size
                x, y, w, h = cv2.boundingRect(contour)

                # Check aspect ratio (interruptions are typically elongated)
                aspect_ratio = float(w) / h if h > 0 else 0

                if aspect_ratio < 0.5:  # Vertical structure
                    defect = Defect(
                        defect_type=DefectType.FINGER_INTERRUPTION,
                        severity=DefectSeverity.MEDIUM,
                        location=(int(x), int(y), int(w), int(h)),
                        confidence=0.6,
                        area_pixels=int(area),
                        description=f"Finger interruption, area={area}px²"
                    )
                    defects.append(defect)

        return defects

    def _detect_thermal_defects(self, image: np.ndarray) -> List[Defect]:
        """Detect hotspots in thermal images

        Args:
            image: Thermal image

        Returns:
            List of hotspot defects
        """
        defects = []

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Calculate temperature threshold (hotspots are bright in thermal images)
        mean_temp = np.mean(gray)
        std_temp = np.std(gray)
        threshold = mean_temp + 2 * std_temp  # 2 standard deviations above mean

        # Threshold to find hot regions
        _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)

        # Find contours
        contours, _ = cv2.findContours(
            binary,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        for contour in contours:
            area = cv2.contourArea(contour)

            if area >= self.config.min_defect_area:
                x, y, w, h = cv2.boundingRect(contour)

                # Calculate max temperature in region
                mask = np.zeros_like(gray)
                cv2.drawContours(mask, [contour], -1, 255, -1)
                max_temp = cv2.minMaxLoc(gray, mask=mask)[1]

                # Determine severity based on temperature
                temp_diff = max_temp - mean_temp

                if temp_diff > 3 * std_temp:
                    severity = DefectSeverity.CRITICAL
                elif temp_diff > 2.5 * std_temp:
                    severity = DefectSeverity.HIGH
                elif temp_diff > 2 * std_temp:
                    severity = DefectSeverity.MEDIUM
                else:
                    severity = DefectSeverity.LOW

                defect = Defect(
                    defect_type=DefectType.HOTSPOT,
                    severity=severity,
                    location=(int(x), int(y), int(w), int(h)),
                    confidence=0.85,
                    area_pixels=int(area),
                    description=f"Hotspot, ΔT≈{temp_diff:.1f} units above mean"
                )
                defects.append(defect)

        return defects

    def _detect_visual_defects(self, image: np.ndarray) -> List[Defect]:
        """Detect defects in visual inspection images

        Args:
            image: Visual inspection image

        Returns:
            List of visual defects (discoloration, corrosion, delamination)
        """
        defects = []

        # Convert to appropriate color space
        if len(image.shape) == 3:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            return defects  # Need color image for visual defects

        # Detect discoloration (brownish/yellowish areas)
        lower_brown = np.array([10, 50, 50])
        upper_brown = np.array([30, 255, 200])
        mask_brown = cv2.inRange(hsv, lower_brown, upper_brown)

        contours, _ = cv2.findContours(
            mask_brown,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        for contour in contours:
            area = cv2.contourArea(contour)

            if area >= self.config.min_defect_area:
                x, y, w, h = cv2.boundingRect(contour)

                defect = Defect(
                    defect_type=DefectType.DISCOLORATION,
                    severity=DefectSeverity.MEDIUM,
                    location=(int(x), int(y), int(w), int(h)),
                    confidence=0.7,
                    area_pixels=int(area),
                    description=f"Discoloration detected, area={area}px²"
                )
                defects.append(defect)

        return defects

    def annotate_defects(
        self,
        image: np.ndarray,
        defects: List[Defect]
    ) -> np.ndarray:
        """Create annotated image with defect markers

        Args:
            image: Original image
            defects: List of detected defects

        Returns:
            Annotated image
        """
        annotated = image.copy()

        # Convert to color if grayscale
        if len(annotated.shape) == 2:
            annotated = cv2.cvtColor(annotated, cv2.COLOR_GRAY2BGR)

        # Color mapping for severity
        severity_colors = {
            DefectSeverity.LOW: (0, 255, 0),  # Green
            DefectSeverity.MEDIUM: (0, 255, 255),  # Yellow
            DefectSeverity.HIGH: (0, 165, 255),  # Orange
            DefectSeverity.CRITICAL: (0, 0, 255),  # Red
        }

        for idx, defect in enumerate(defects, 1):
            x, y, w, h = defect.location
            color = severity_colors.get(defect.severity, (255, 255, 255))

            # Draw bounding box
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)

            # Add label
            label = f"{idx}: {defect.defect_type.value}"
            cv2.putText(
                annotated,
                label,
                (x, y - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
                cv2.LINE_AA
            )

        # Add legend
        legend_y = 30
        for severity, color in severity_colors.items():
            text = f"{severity.value.upper()}"
            cv2.putText(
                annotated,
                text,
                (10, legend_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
                cv2.LINE_AA
            )
            legend_y += 25

        return annotated
