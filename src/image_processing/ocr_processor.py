"""OCR processing module for equipment displays and text extraction

Extracts text from:
- Equipment displays
- Test equipment readings
- Module labels and serial numbers
- Measurement instruments
"""

import re
import cv2
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
import logging

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    pytesseract = None

from .models import ProcessingConfig

logger = logging.getLogger(__name__)


class OCRProcessor:
    """Processes images to extract text using OCR"""

    def __init__(self, config: Optional[ProcessingConfig] = None):
        """Initialize OCR processor

        Args:
            config: Processing configuration
        """
        self.config = config or ProcessingConfig()

        if not TESSERACT_AVAILABLE:
            logger.warning("Tesseract OCR not available. OCR functionality will be disabled.")

    def extract_text(
        self,
        image: np.ndarray,
        preprocess: bool = True
    ) -> Tuple[str, Dict[str, Any]]:
        """Extract text from image using OCR

        Args:
            image: Input image
            preprocess: Whether to apply preprocessing

        Returns:
            Tuple of (extracted_text, ocr_data)
        """
        if not TESSERACT_AVAILABLE or not self.config.ocr_enabled:
            return "", {}

        # Preprocess image for better OCR
        if preprocess:
            processed = self._preprocess_for_ocr(image)
        else:
            processed = image

        try:
            # Extract text
            text = pytesseract.image_to_string(
                processed,
                lang=self.config.ocr_language,
                config='--psm 6'  # Assume uniform block of text
            )

            # Get detailed OCR data
            ocr_data = pytesseract.image_to_data(
                processed,
                lang=self.config.ocr_language,
                output_type=pytesseract.Output.DICT
            )

            # Filter by confidence
            filtered_data = self._filter_by_confidence(ocr_data)

            # Parse structured data
            structured_data = self._parse_structured_data(text)

            result_data = {
                'raw_text': text.strip(),
                'word_count': len(text.split()),
                'confidence_mean': np.mean([c for c in ocr_data['conf'] if c > 0]) if ocr_data['conf'] else 0,
                'structured_data': structured_data,
                'filtered_words': filtered_data,
            }

            logger.info(f"OCR extracted {result_data['word_count']} words with {result_data['confidence_mean']:.1f}% avg confidence")

            return text.strip(), result_data

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return "", {}

    def _preprocess_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image to improve OCR accuracy

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

        # Resize if too small (OCR works better on larger images)
        height, width = gray.shape
        if height < 300 or width < 300:
            scale = max(300 / height, 300 / width)
            gray = cv2.resize(
                gray,
                None,
                fx=scale,
                fy=scale,
                interpolation=cv2.INTER_CUBIC
            )

        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, h=10)

        # Increase contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        # Binarization using adaptive thresholding
        binary = cv2.adaptiveThreshold(
            enhanced,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )

        # Morphological operations to clean up
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        return cleaned

    def _filter_by_confidence(
        self,
        ocr_data: Dict[str, List]
    ) -> List[Dict[str, Any]]:
        """Filter OCR results by confidence threshold

        Args:
            ocr_data: OCR data from Tesseract

        Returns:
            List of filtered word data
        """
        filtered = []

        n_boxes = len(ocr_data['text'])
        for i in range(n_boxes):
            conf = float(ocr_data['conf'][i])
            text = ocr_data['text'][i].strip()

            if conf >= self.config.ocr_confidence_threshold and text:
                filtered.append({
                    'text': text,
                    'confidence': conf,
                    'bbox': (
                        int(ocr_data['left'][i]),
                        int(ocr_data['top'][i]),
                        int(ocr_data['width'][i]),
                        int(ocr_data['height'][i])
                    )
                })

        return filtered

    def _parse_structured_data(self, text: str) -> Dict[str, Any]:
        """Parse structured data from OCR text

        Extracts common patterns:
        - Numerical measurements (voltage, current, power)
        - Serial numbers
        - Date/time stamps
        - Model numbers

        Args:
            text: OCR extracted text

        Returns:
            Dictionary with parsed structured data
        """
        structured = {}

        # Extract voltage measurements (e.g., "12.5V", "12.5 V")
        voltage_pattern = r'(\d+\.?\d*)\s*V(?:olt)?s?'
        voltages = re.findall(voltage_pattern, text, re.IGNORECASE)
        if voltages:
            structured['voltages'] = [float(v) for v in voltages]

        # Extract current measurements (e.g., "5.2A", "5.2 A")
        current_pattern = r'(\d+\.?\d*)\s*A(?:mp)?s?'
        currents = re.findall(current_pattern, text, re.IGNORECASE)
        if currents:
            structured['currents'] = [float(c) for c in currents]

        # Extract power measurements (e.g., "250W", "250 W")
        power_pattern = r'(\d+\.?\d*)\s*W(?:att)?s?'
        powers = re.findall(power_pattern, text, re.IGNORECASE)
        if powers:
            structured['powers'] = [float(p) for p in powers]

        # Extract temperature (e.g., "25°C", "25 C")
        temp_pattern = r'(\d+\.?\d*)\s*°?C'
        temperatures = re.findall(temp_pattern, text, re.IGNORECASE)
        if temperatures:
            structured['temperatures'] = [float(t) for t in temperatures]

        # Extract efficiency (e.g., "18.5%", "18.5 %")
        efficiency_pattern = r'(\d+\.?\d*)\s*%'
        efficiencies = re.findall(efficiency_pattern, text)
        if efficiencies:
            structured['percentages'] = [float(e) for e in efficiencies]

        # Extract serial numbers (various formats)
        serial_pattern = r'(?:S/?N|Serial|SN)[:\s]*([A-Z0-9-]+)'
        serials = re.findall(serial_pattern, text, re.IGNORECASE)
        if serials:
            structured['serial_numbers'] = serials

        # Extract model numbers
        model_pattern = r'(?:Model|M/?N)[:\s]*([A-Z0-9-]+)'
        models = re.findall(model_pattern, text, re.IGNORECASE)
        if models:
            structured['model_numbers'] = models

        # Extract dates (various formats)
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY or MM/DD/YYYY
            r'\d{2}\.\d{2}\.\d{4}',  # DD.MM.YYYY
        ]
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text))
        if dates:
            structured['dates'] = dates

        return structured

    def extract_display_readings(
        self,
        image: np.ndarray,
        display_region: Optional[Tuple[int, int, int, int]] = None
    ) -> Dict[str, Any]:
        """Extract readings from equipment display

        Args:
            image: Input image
            display_region: Optional ROI for display (x, y, w, h)

        Returns:
            Dictionary with extracted display readings
        """
        # Crop to display region if specified
        if display_region:
            x, y, w, h = display_region
            roi = image[y:y+h, x:x+w]
        else:
            roi = image

        # Extract text
        text, ocr_data = self.extract_text(roi, preprocess=True)

        # Parse display-specific patterns
        readings = {
            'raw_text': text,
            'measurements': {},
        }

        # Extract common display patterns
        structured = ocr_data.get('structured_data', {})

        if 'voltages' in structured and structured['voltages']:
            readings['measurements']['voltage'] = structured['voltages'][0]

        if 'currents' in structured and structured['currents']:
            readings['measurements']['current'] = structured['currents'][0]

        if 'powers' in structured and structured['powers']:
            readings['measurements']['power'] = structured['powers'][0]

        if 'temperatures' in structured and structured['temperatures']:
            readings['measurements']['temperature'] = structured['temperatures'][0]

        return readings

    def detect_text_regions(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect regions containing text in an image

        Args:
            image: Input image

        Returns:
            List of bounding boxes (x, y, w, h) for text regions
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Apply morphological gradient
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        gradient = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, kernel)

        # Threshold
        _, binary = cv2.threshold(gradient, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Dilate to connect text regions
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
        dilated = cv2.dilate(binary, kernel, iterations=3)

        # Find contours
        contours, _ = cv2.findContours(
            dilated,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # Filter and return bounding boxes
        text_regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            # Filter by size (typical text regions)
            if w > 20 and h > 10 and w < gray.shape[1] * 0.9:
                text_regions.append((x, y, w, h))

        return text_regions
