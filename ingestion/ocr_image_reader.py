"""
OCR Image Reader Module

Provides OCR functionality for extracting text from equipment displays,
multimeters, chamber displays, and data logger screen captures.
"""

import cv2
import numpy as np
import re
from typing import Optional, Dict, List, Tuple, Union
from pathlib import Path

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

from . import OCRResult, OCRError


class OCRImageReader:
    """
    OCR reader for equipment displays and measurement screenshots.

    Supports:
    - Digital display reading
    - Multimeter screenshots
    - Chamber displays (temperature, humidity)
    - Data logger screen captures
    - Confidence scoring
    """

    def __init__(
        self,
        tesseract_cmd: Optional[str] = None,
        preprocess: bool = True
    ):
        """
        Initialize OCR reader.

        Args:
            tesseract_cmd: Path to tesseract executable (optional)
            preprocess: Whether to apply preprocessing for better OCR

        Raises:
            OCRError: If pytesseract is not available
        """
        if not TESSERACT_AVAILABLE:
            raise OCRError(
                "pytesseract is not installed. Install with: pip install pytesseract\n"
                "Also ensure tesseract-ocr is installed on your system."
            )

        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        self.preprocess = preprocess

    def read_text(
        self,
        image: np.ndarray,
        region: Optional[Tuple[int, int, int, int]] = None,
        config: str = '--oem 3 --psm 6'
    ) -> OCRResult:
        """
        Extract text from image using OCR.

        Args:
            image: Input image (BGR or grayscale)
            region: Optional region of interest (x, y, w, h)
            config: Tesseract configuration string

        Returns:
            OCRResult with extracted text and confidence

        Raises:
            OCRError: If OCR processing fails
        """
        try:
            # Extract region if specified
            if region:
                x, y, w, h = region
                image = image[y:y+h, x:x+w]

            # Preprocess image
            if self.preprocess:
                processed = self._preprocess_image(image)
            else:
                processed = image

            # Perform OCR
            data = pytesseract.image_to_data(
                processed,
                output_type=pytesseract.Output.DICT,
                config=config
            )

            # Extract text and confidence
            text_parts = []
            confidences = []
            bounding_boxes = []

            n_boxes = len(data['text'])
            for i in range(n_boxes):
                conf = int(data['conf'][i])
                text = data['text'][i].strip()

                if conf > 0 and text:
                    text_parts.append(text)
                    confidences.append(conf / 100.0)

                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    bounding_boxes.append((x, y, w, h))

            # Combine text
            full_text = ' '.join(text_parts)

            # Calculate average confidence
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            # Extract numeric values
            extracted_values = self._extract_numeric_values(full_text)

            return OCRResult(
                text=full_text,
                confidence=avg_confidence,
                bounding_boxes=bounding_boxes,
                extracted_values=extracted_values
            )

        except Exception as e:
            raise OCRError(f"OCR processing failed: {str(e)}")

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR accuracy.

        Args:
            image: Input image

        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Increase contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Denoise
        denoised = cv2.fastNlMeansDenoising(enhanced)

        # Threshold to binary
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Morphological operations to clean up
        kernel = np.ones((1, 1), np.uint8)
        morphed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        return morphed

    def _extract_numeric_values(self, text: str) -> Dict[str, float]:
        """
        Extract numeric values from OCR text.

        Args:
            text: OCR text

        Returns:
            Dictionary of extracted values with labels
        """
        values = {}

        # Common patterns for equipment readings
        patterns = {
            'voltage': r'(\d+\.?\d*)\s*[Vv](?:olts?)?',
            'current': r'(\d+\.?\d*)\s*[Aa](?:mps?|mperes?)?',
            'temperature': r'(\d+\.?\d*)\s*[°]?[CcFf]',
            'humidity': r'(\d+\.?\d*)\s*%\s*(?:RH|rh)?',
            'power': r'(\d+\.?\d*)\s*[Ww](?:atts?)?',
            'resistance': r'(\d+\.?\d*)\s*[Ωω]|(?:ohms?)',
        }

        for key, pattern in patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                try:
                    # Take the first match
                    values[key] = float(matches[0])
                except ValueError:
                    continue

        return values

    def read_multimeter(self, image: np.ndarray) -> OCRResult:
        """
        Specialized OCR for multimeter displays.

        Args:
            image: Multimeter screenshot

        Returns:
            OCRResult with extracted measurement
        """
        # Multimeters typically show large digits
        config = '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.-'

        return self.read_text(image, config=config)

    def read_chamber_display(
        self,
        image: np.ndarray,
        extract_temp: bool = True,
        extract_humidity: bool = True
    ) -> OCRResult:
        """
        Specialized OCR for environmental chamber displays.

        Args:
            image: Chamber display screenshot
            extract_temp: Extract temperature value
            extract_humidity: Extract humidity value

        Returns:
            OCRResult with extracted values
        """
        # Standard OCR
        result = self.read_text(image)

        # Parse specific values
        parsed_values = {}

        if extract_temp and 'temperature' in result.extracted_values:
            parsed_values['temperature'] = result.extracted_values['temperature']

        if extract_humidity and 'humidity' in result.extracted_values:
            parsed_values['humidity'] = result.extracted_values['humidity']

        # Update extracted values
        result.extracted_values.update(parsed_values)

        return result

    def read_seven_segment_display(self, image: np.ndarray) -> OCRResult:
        """
        Specialized OCR for seven-segment LED displays.

        Uses template matching for better accuracy.

        Args:
            image: Seven-segment display image

        Returns:
            OCRResult with extracted digits
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Threshold to get bright segments
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Invert if necessary (segments should be white)
        if np.mean(binary) > 127:
            binary = cv2.bitwise_not(binary)

        # Use specialized config for digits
        config = '--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789.-'

        try:
            text = pytesseract.image_to_string(binary, config=config).strip()

            # Try to extract numeric value
            numbers = re.findall(r'-?\d+\.?\d*', text)
            if numbers:
                extracted_value = float(numbers[0])
            else:
                extracted_value = None

            return OCRResult(
                text=text,
                confidence=0.8,  # Estimated confidence
                bounding_boxes=[],
                extracted_values={'value': extracted_value} if extracted_value is not None else {}
            )

        except Exception as e:
            raise OCRError(f"Seven-segment OCR failed: {str(e)}")

    def read_data_logger_screen(self, image: np.ndarray) -> OCRResult:
        """
        Extract readings from data logger screen captures.

        Args:
            image: Data logger screenshot

        Returns:
            OCRResult with extracted data
        """
        # Data loggers often have tabular data
        config = '--oem 3 --psm 6'

        result = self.read_text(image, config=config)

        # Try to extract timestamp if present
        timestamp_pattern = r'\d{2}[:/]\d{2}[:/]\d{2,4}'
        timestamps = re.findall(timestamp_pattern, result.text)

        if timestamps:
            result.extracted_values['timestamp'] = timestamps[0]

        return result

    def detect_display_region(self, image: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        Automatically detect display region in image.

        Useful when the display is only a small part of the image.

        Args:
            image: Input image

        Returns:
            Bounding box (x, y, w, h) of display region or None
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Detect edges
        edges = cv2.Canny(gray, 50, 150)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None

        # Find largest rectangular contour
        max_area = 0
        best_rect = None

        for contour in contours:
            area = cv2.contourArea(contour)

            if area < 1000:  # Minimum display area
                continue

            # Approximate to polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            # Check if roughly rectangular (4 corners)
            if len(approx) >= 4 and area > max_area:
                x, y, w, h = cv2.boundingRect(contour)

                # Check aspect ratio (displays are usually wider than tall)
                aspect_ratio = w / h if h > 0 else 0

                if 1.5 < aspect_ratio < 5.0:
                    max_area = area
                    best_rect = (x, y, w, h)

        return best_rect


class BatchOCRProcessor:
    """Process multiple images with OCR in batch."""

    def __init__(self, reader: Optional[OCRImageReader] = None):
        """
        Initialize batch processor.

        Args:
            reader: OCRImageReader instance
        """
        self.reader = reader or OCRImageReader()

    def process_batch(
        self,
        image_paths: List[Union[str, Path]],
        display_type: str = 'auto'
    ) -> List[OCRResult]:
        """
        Process multiple images with OCR.

        Args:
            image_paths: List of image file paths
            display_type: Type of display ('auto', 'multimeter', 'chamber', 'seven_segment')

        Returns:
            List of OCRResults
        """
        results = []

        for image_path in image_paths:
            try:
                # Load image
                image = cv2.imread(str(image_path))

                if image is None:
                    results.append(OCRResult(
                        text="",
                        confidence=0.0,
                        bounding_boxes=[],
                        extracted_values={'error': 'Failed to load image'}
                    ))
                    continue

                # Process based on display type
                if display_type == 'multimeter':
                    result = self.reader.read_multimeter(image)
                elif display_type == 'chamber':
                    result = self.reader.read_chamber_display(image)
                elif display_type == 'seven_segment':
                    result = self.reader.read_seven_segment_display(image)
                else:  # auto
                    result = self.reader.read_text(image)

                results.append(result)

            except Exception as e:
                results.append(OCRResult(
                    text="",
                    confidence=0.0,
                    bounding_boxes=[],
                    extracted_values={'error': str(e)}
                ))

        return results


__all__ = [
    'OCRImageReader',
    'BatchOCRProcessor',
]
