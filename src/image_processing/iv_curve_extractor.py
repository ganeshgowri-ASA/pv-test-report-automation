"""I-V curve chart extraction and digitization module

Extracts I-V curve data from chart images for:
- IEC 60904-1: I-V measurement procedures
- Performance characterization
- Power output analysis
- Fill factor calculation
"""

import cv2
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
import logging

from .ocr_processor import OCRProcessor
from .models import ProcessingConfig

logger = logging.getLogger(__name__)


class IVCurveExtractor:
    """Extracts I-V curve data from chart images"""

    def __init__(self, config: Optional[ProcessingConfig] = None):
        """Initialize I-V curve extractor

        Args:
            config: Processing configuration
        """
        self.config = config or ProcessingConfig()
        self.ocr = OCRProcessor(config)

    def extract_iv_curve(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract I-V curve data from chart image

        Args:
            image: Chart image containing I-V curve

        Returns:
            Dictionary with extracted curve data and parameters
        """
        result = {
            'curve_detected': False,
            'parameters': {},
            'digitized_points': [],
            'chart_bounds': None,
        }

        # Detect chart area
        chart_region = self._detect_chart_region(image)
        if chart_region is None:
            logger.warning("Could not detect chart region")
            return result

        result['chart_bounds'] = chart_region

        # Extract curve points
        points = self._extract_curve_points(image, chart_region)
        if points:
            result['curve_detected'] = True
            result['digitized_points'] = points

        # Extract axis labels and values using OCR
        axis_info = self._extract_axis_info(image, chart_region)
        result.update(axis_info)

        # Calculate I-V parameters if we have enough data
        if len(points) > 10:
            parameters = self._calculate_iv_parameters(points, axis_info)
            result['parameters'] = parameters

        return result

    def _detect_chart_region(
        self,
        image: np.ndarray
    ) -> Optional[Tuple[int, int, int, int]]:
        """Detect the chart region in the image

        Args:
            image: Input image

        Returns:
            Bounding box (x, y, w, h) of chart or None
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Detect edges
        edges = cv2.Canny(gray, 50, 150)

        # Find horizontal and vertical lines (axes)
        # Horizontal lines
        kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        horizontal = cv2.morphologyEx(edges, cv2.MORPH_OPEN, kernel_h)

        # Vertical lines
        kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        vertical = cv2.morphologyEx(edges, cv2.MORPH_OPEN, kernel_v)

        # Combine axes
        axes = cv2.bitwise_or(horizontal, vertical)

        # Find contours
        contours, _ = cv2.findContours(
            axes,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # Find largest rectangular region (likely the chart)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)

            # Validate aspect ratio (charts are typically wider than tall)
            aspect_ratio = w / h if h > 0 else 0
            if 0.5 < aspect_ratio < 3.0 and w > 100 and h > 100:
                return (x, y, w, h)

        return None

    def _extract_curve_points(
        self,
        image: np.ndarray,
        chart_region: Tuple[int, int, int, int]
    ) -> List[Tuple[float, float]]:
        """Extract curve points from chart

        Args:
            image: Input image
            chart_region: Chart bounding box (x, y, w, h)

        Returns:
            List of (x, y) curve points normalized to 0-1 range
        """
        x, y, w, h = chart_region

        # Extract chart region
        chart_roi = image[y:y+h, x:x+w]

        # Convert to grayscale
        if len(chart_roi.shape) == 3:
            gray = cv2.cvtColor(chart_roi, cv2.COLOR_BGR2GRAY)
        else:
            gray = chart_roi.copy()

        # Threshold to isolate curve
        # Assuming dark curve on light background
        _, binary = cv2.threshold(
            gray,
            0,
            255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )

        # Remove axes by masking edges
        mask = np.ones_like(binary) * 255
        border = 20
        mask[:border, :] = 0
        mask[-border:, :] = 0
        mask[:, :border] = 0
        mask[:, -border:] = 0

        curve_binary = cv2.bitwise_and(binary, mask)

        # Thin the curve to get skeleton
        kernel = np.ones((3, 3), np.uint8)
        curve_binary = cv2.morphologyEx(curve_binary, cv2.MORPH_CLOSE, kernel)

        # Extract points
        points_px = np.where(curve_binary > 0)

        if len(points_px[0]) == 0:
            return []

        # Convert to (x, y) coordinates and normalize
        points = []
        for i in range(len(points_px[0])):
            px_y = points_px[0][i]
            px_x = points_px[1][i]

            # Normalize to 0-1 range
            norm_x = px_x / w
            norm_y = 1.0 - (px_y / h)  # Flip y-axis (image coords are top-down)

            points.append((norm_x, norm_y))

        # Sort by x coordinate
        points.sort(key=lambda p: p[0])

        # Downsample if too many points
        if len(points) > 200:
            step = len(points) // 200
            points = points[::step]

        return points

    def _extract_axis_info(
        self,
        image: np.ndarray,
        chart_region: Tuple[int, int, int, int]
    ) -> Dict[str, Any]:
        """Extract axis labels and tick values using OCR

        Args:
            image: Input image
            chart_region: Chart bounding box

        Returns:
            Dictionary with axis information
        """
        x, y, w, h = chart_region

        axis_info = {
            'x_axis_label': None,
            'y_axis_label': None,
            'x_min': 0.0,
            'x_max': None,
            'y_min': 0.0,
            'y_max': None,
        }

        # Extract text from regions around the chart
        # X-axis label (below chart)
        if y + h + 50 < image.shape[0]:
            x_label_roi = image[y+h:y+h+50, x:x+w]
            x_text, _ = self.ocr.extract_text(x_label_roi)
            if 'voltage' in x_text.lower() or 'v' in x_text.lower():
                axis_info['x_axis_label'] = 'Voltage (V)'

        # Y-axis label (left of chart)
        if x > 50:
            y_label_roi = image[y:y+h, max(0, x-50):x]
            y_text, _ = self.ocr.extract_text(y_label_roi)
            if 'current' in y_text.lower() or 'a' in y_text.lower():
                axis_info['y_axis_label'] = 'Current (A)'

        # Try to extract tick values
        # This is complex and would require sophisticated OCR + parsing
        # For now, we'll use heuristics based on typical I-V curves

        # Extract numbers from chart vicinity
        if self.ocr.config.ocr_enabled:
            margin = 30
            roi_with_labels = image[
                max(0, y-margin):min(image.shape[0], y+h+margin),
                max(0, x-margin):min(image.shape[1], x+w+margin)
            ]
            text, ocr_data = self.ocr.extract_text(roi_with_labels)

            # Extract numerical values
            if 'structured_data' in ocr_data:
                structured = ocr_data['structured_data']

                # X-axis is typically voltage (0-50V range)
                if 'voltages' in structured and structured['voltages']:
                    voltages = sorted(structured['voltages'])
                    if voltages:
                        axis_info['x_max'] = max(voltages)
                        axis_info['x_min'] = min(voltages) if min(voltages) >= 0 else 0.0

                # Y-axis is typically current (0-10A range)
                if 'currents' in structured and structured['currents']:
                    currents = sorted(structured['currents'])
                    if currents:
                        axis_info['y_max'] = max(currents)
                        axis_info['y_min'] = min(currents) if min(currents) >= 0 else 0.0

        return axis_info

    def _calculate_iv_parameters(
        self,
        points: List[Tuple[float, float]],
        axis_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate I-V curve parameters

        Args:
            points: Normalized curve points
            axis_info: Axis scaling information

        Returns:
            Dictionary with I-V parameters
        """
        parameters = {}

        if not points:
            return parameters

        # Get scaling factors
        v_max = axis_info.get('x_max', 1.0) or 1.0
        i_max = axis_info.get('y_max', 1.0) or 1.0

        # Convert normalized points to actual values
        voltages = [p[0] * v_max for p in points]
        currents = [p[1] * i_max for p in points]

        # Find key points
        # Voc: voltage at zero current (rightmost point)
        voc_idx = np.argmax(voltages)
        parameters['Voc'] = voltages[voc_idx]

        # Isc: current at zero voltage (topmost point at x=0)
        isc_idx = np.argmax(currents)
        parameters['Isc'] = currents[isc_idx]

        # Calculate power at each point
        powers = [v * i for v, i in zip(voltages, currents)]

        # Pmax: maximum power point
        pmax_idx = np.argmax(powers)
        parameters['Pmax'] = powers[pmax_idx]
        parameters['Vmpp'] = voltages[pmax_idx]
        parameters['Impp'] = currents[pmax_idx]

        # Fill Factor: FF = (Vmpp * Impp) / (Voc * Isc)
        if parameters['Voc'] > 0 and parameters['Isc'] > 0:
            ff = parameters['Pmax'] / (parameters['Voc'] * parameters['Isc'])
            parameters['FF'] = ff
        else:
            parameters['FF'] = 0.0

        # Add units
        parameters['units'] = {
            'voltage': 'V',
            'current': 'A',
            'power': 'W',
            'FF': 'dimensionless'
        }

        logger.info(
            f"I-V Parameters: Voc={parameters['Voc']:.2f}V, "
            f"Isc={parameters['Isc']:.2f}A, "
            f"Pmax={parameters['Pmax']:.2f}W, "
            f"FF={parameters['FF']:.3f}"
        )

        return parameters

    def visualize_extraction(
        self,
        image: np.ndarray,
        extraction_result: Dict[str, Any]
    ) -> np.ndarray:
        """Create visualization of the I-V curve extraction

        Args:
            image: Original image
            extraction_result: Result from extract_iv_curve

        Returns:
            Annotated image
        """
        annotated = image.copy()

        # Convert to color if grayscale
        if len(annotated.shape) == 2:
            annotated = cv2.cvtColor(annotated, cv2.COLOR_GRAY2BGR)

        # Draw chart region
        if extraction_result['chart_bounds']:
            x, y, w, h = extraction_result['chart_bounds']
            cv2.rectangle(annotated, (x, y), (x+w, y+h), (0, 255, 0), 2)

            # Draw extracted points
            if extraction_result['digitized_points']:
                for px, py in extraction_result['digitized_points']:
                    # Convert normalized coords back to pixels
                    img_x = int(x + px * w)
                    img_y = int(y + (1 - py) * h)
                    cv2.circle(annotated, (img_x, img_y), 2, (255, 0, 0), -1)

        # Add parameters text
        if extraction_result['parameters']:
            params = extraction_result['parameters']
            y_offset = 30
            texts = [
                f"Voc: {params.get('Voc', 0):.2f} V",
                f"Isc: {params.get('Isc', 0):.2f} A",
                f"Pmax: {params.get('Pmax', 0):.2f} W",
                f"FF: {params.get('FF', 0):.3f}",
            ]

            for text in texts:
                cv2.putText(
                    annotated,
                    text,
                    (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA
                )
                y_offset += 30

        return annotated
