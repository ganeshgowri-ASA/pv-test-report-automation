"""
Image Processor for PV Test Automation (Session 08)

Handles image processing for test charts, graphs, OCR for scanned reports,
and visual QC image processing.
"""

import asyncio
import base64
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from pydantic import BaseModel, Field, validator

# Optional imports for OCR and advanced processing
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False


class ImageMetadata(BaseModel):
    """Metadata extracted from images."""

    width: int
    height: int
    format: str
    mode: str
    dpi: Optional[Tuple[int, int]] = None
    file_size_bytes: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    exif_data: Dict[str, Any] = Field(default_factory=dict)
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class OCRResult(BaseModel):
    """OCR extraction result."""

    text: str
    confidence: float = Field(..., ge=0, le=100, description="OCR confidence score")
    language: str = Field(default="eng")
    bounding_boxes: List[Dict[str, Any]] = Field(default_factory=list)
    word_count: int = 0
    line_count: int = 0
    processing_time_ms: float = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("word_count", always=True)
    def count_words(cls, v, values):
        """Auto-count words if not provided."""
        if v == 0 and "text" in values:
            return len(values["text"].split())
        return v

    @validator("line_count", always=True)
    def count_lines(cls, v, values):
        """Auto-count lines if not provided."""
        if v == 0 and "text" in values:
            return len(values["text"].split("\n"))
        return v


class TestChart(BaseModel):
    """Extracted test chart/graph data."""

    chart_type: str = Field(..., description="IV_curve, efficiency, temperature, etc.")
    image_path: str
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: ImageMetadata
    quality_score: float = Field(..., ge=0, le=100)
    contains_grid: bool = False
    contains_legend: bool = False
    contains_axes: bool = False
    processing_notes: List[str] = Field(default_factory=list)


class VisualQCResult(BaseModel):
    """Visual quality control result."""

    image_path: str
    qc_passed: bool
    defects_detected: List[str] = Field(default_factory=list)
    quality_metrics: Dict[str, float] = Field(default_factory=dict)
    annotations: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ImageProcessorConfig(BaseModel):
    """Configuration for image processor."""

    ocr_language: str = Field(default="eng")
    ocr_dpi: int = Field(default=300)
    enable_preprocessing: bool = Field(default=True)
    enable_denoising: bool = Field(default=True)
    contrast_enhancement: float = Field(default=1.5, ge=0.5, le=3.0)
    sharpness_enhancement: float = Field(default=1.2, ge=0.5, le=3.0)
    auto_rotate: bool = Field(default=True)
    max_image_size: Tuple[int, int] = Field(default=(4096, 4096))
    output_format: str = Field(default="PNG")
    quality: int = Field(default=95, ge=1, le=100)


class ImageProcessor:
    """
    Production-ready image processor for PV test automation.

    Supports:
    - Test chart/graph extraction
    - OCR for scanned reports
    - Image preprocessing and enhancement
    - Metadata extraction
    - Visual QC processing
    - Batch processing with async support
    - Progress tracking
    """

    def __init__(self, config: Optional[ImageProcessorConfig] = None):
        """Initialize image processor."""
        self.config = config or ImageProcessorConfig()
        self._progress_callback = None

        if not TESSERACT_AVAILABLE:
            print("Warning: pytesseract not available. OCR functionality disabled.")

        if not OPENCV_AVAILABLE:
            print("Warning: OpenCV not available. Advanced processing limited.")

    def set_progress_callback(self, callback):
        """Set callback for progress tracking."""
        self._progress_callback = callback

    def _report_progress(self, current: int, total: int, message: str = ""):
        """Report progress if callback is set."""
        if self._progress_callback:
            self._progress_callback(current, total, message)

    def load_image(self, file_path: Union[str, Path]) -> Image.Image:
        """
        Load image from file.

        Args:
            file_path: Path to image file

        Returns:
            PIL Image object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not a valid image
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Image file not found: {file_path}")

        try:
            img = Image.open(file_path)
            return img
        except Exception as e:
            raise ValueError(f"Failed to load image: {e}") from e

    def extract_metadata(self, image: Union[Image.Image, str, Path]) -> ImageMetadata:
        """
        Extract metadata from image.

        Args:
            image: PIL Image or path to image file

        Returns:
            ImageMetadata object
        """
        if isinstance(image, (str, Path)):
            file_path = Path(image)
            file_size = file_path.stat().st_size
            image = self.load_image(file_path)
        else:
            file_size = 0

        # Extract EXIF data
        exif_data = {}
        if hasattr(image, "_getexif") and image._getexif():
            exif_data = {k: v for k, v in image._getexif().items()}

        # Get DPI
        dpi = image.info.get("dpi")

        return ImageMetadata(
            width=image.width,
            height=image.height,
            format=image.format or "Unknown",
            mode=image.mode,
            dpi=dpi,
            file_size_bytes=file_size,
            exif_data=exif_data,
        )

    def preprocess_image(
        self, image: Image.Image, enhance: bool = True
    ) -> Image.Image:
        """
        Preprocess image for better OCR/analysis results.

        Args:
            image: PIL Image
            enhance: Whether to apply enhancement

        Returns:
            Preprocessed PIL Image
        """
        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Resize if too large
        if (
            image.width > self.config.max_image_size[0]
            or image.height > self.config.max_image_size[1]
        ):
            image.thumbnail(self.config.max_image_size, Image.Resampling.LANCZOS)

        if not enhance or not self.config.enable_preprocessing:
            return image

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(self.config.contrast_enhancement)

        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(self.config.sharpness_enhancement)

        # Denoise if enabled
        if self.config.enable_denoising:
            image = image.filter(ImageFilter.MedianFilter(size=3))

        return image

    def perform_ocr(
        self,
        image: Union[Image.Image, str, Path],
        preprocess: bool = True,
        language: Optional[str] = None,
    ) -> OCRResult:
        """
        Perform OCR on image.

        Args:
            image: PIL Image or path to image file
            preprocess: Whether to preprocess image
            language: OCR language (default from config)

        Returns:
            OCRResult object

        Raises:
            RuntimeError: If Tesseract is not available
        """
        if not TESSERACT_AVAILABLE:
            raise RuntimeError(
                "pytesseract not available. Install with: pip install pytesseract"
            )

        start_time = datetime.utcnow()

        # Load image if path provided
        if isinstance(image, (str, Path)):
            image = self.load_image(image)

        # Preprocess
        if preprocess:
            image = self.preprocess_image(image)

        # Perform OCR
        lang = language or self.config.ocr_language

        try:
            # Get detailed data
            ocr_data = pytesseract.image_to_data(
                image, lang=lang, output_type=pytesseract.Output.DICT
            )

            # Extract text
            text = pytesseract.image_to_string(image, lang=lang)

            # Calculate average confidence
            confidences = [
                float(conf) for conf in ocr_data["conf"] if conf != "-1"
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            # Extract bounding boxes
            bounding_boxes = []
            n_boxes = len(ocr_data["text"])
            for i in range(n_boxes):
                if int(ocr_data["conf"][i]) > 0:
                    bounding_boxes.append(
                        {
                            "text": ocr_data["text"][i],
                            "left": ocr_data["left"][i],
                            "top": ocr_data["top"][i],
                            "width": ocr_data["width"][i],
                            "height": ocr_data["height"][i],
                            "confidence": float(ocr_data["conf"][i]),
                        }
                    )

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return OCRResult(
                text=text.strip(),
                confidence=avg_confidence,
                language=lang,
                bounding_boxes=bounding_boxes,
                processing_time_ms=processing_time,
            )

        except Exception as e:
            raise RuntimeError(f"OCR failed: {e}") from e

    def extract_test_chart(
        self,
        file_path: Union[str, Path],
        chart_type: str = "unknown",
    ) -> TestChart:
        """
        Extract test chart/graph from image.

        Args:
            file_path: Path to chart image
            chart_type: Type of chart (IV_curve, efficiency, etc.)

        Returns:
            TestChart object
        """
        file_path = Path(file_path)
        image = self.load_image(file_path)

        # Extract metadata
        metadata = self.extract_metadata(image)

        # Analyze chart quality
        quality_score = self._assess_image_quality(image)

        # Detect chart elements
        contains_grid = self._detect_grid(image)
        contains_legend = self._detect_legend(image)
        contains_axes = self._detect_axes(image)

        # Extract data based on chart type
        extracted_data = {}
        processing_notes = []

        if chart_type.lower() == "iv_curve":
            extracted_data = self._extract_iv_curve_data(image)
            processing_notes.append("IV curve data extraction attempted")

        return TestChart(
            chart_type=chart_type,
            image_path=str(file_path),
            extracted_data=extracted_data,
            metadata=metadata,
            quality_score=quality_score,
            contains_grid=contains_grid,
            contains_legend=contains_legend,
            contains_axes=contains_axes,
            processing_notes=processing_notes,
        )

    def _assess_image_quality(self, image: Image.Image) -> float:
        """
        Assess image quality.

        Returns:
            Quality score (0-100)
        """
        # Convert to grayscale
        gray = image.convert("L")
        img_array = np.array(gray)

        # Calculate sharpness (using Laplacian variance)
        if OPENCV_AVAILABLE:
            laplacian_var = cv2.Laplacian(img_array, cv2.CV_64F).var()
            sharpness = min(100, (laplacian_var / 100) * 100)
        else:
            # Fallback: use edge detection with PIL
            edges = gray.filter(ImageFilter.FIND_EDGES)
            edge_array = np.array(edges)
            sharpness = min(100, (edge_array.std() / 50) * 100)

        # Calculate contrast
        contrast = img_array.std() / 128 * 100

        # Overall quality (weighted average)
        quality = (sharpness * 0.6 + contrast * 0.4)

        return min(100, max(0, quality))

    def _detect_grid(self, image: Image.Image) -> bool:
        """Detect if image contains a grid."""
        if not OPENCV_AVAILABLE:
            return False

        # Convert to grayscale
        gray = image.convert("L")
        img_array = np.array(gray)

        # Detect lines using Hough transform
        edges = cv2.Canny(img_array, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 100)

        # If many lines detected, likely has grid
        return lines is not None and len(lines) > 10

    def _detect_legend(self, image: Image.Image) -> bool:
        """Detect if image contains a legend."""
        # Simplified detection: OCR on image regions
        # In production, would use ML-based detection
        if not TESSERACT_AVAILABLE:
            return False

        try:
            text = pytesseract.image_to_string(image)
            # Common legend indicators
            legend_keywords = ["legend", "series", "data", "curve", "line"]
            return any(kw in text.lower() for kw in legend_keywords)
        except Exception:
            return False

    def _detect_axes(self, image: Image.Image) -> bool:
        """Detect if image contains axes."""
        if not OPENCV_AVAILABLE:
            return False

        # Convert to grayscale
        gray = image.convert("L")
        img_array = np.array(gray)

        # Detect lines
        edges = cv2.Canny(img_array, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10
        )

        if lines is None:
            return False

        # Check for horizontal and vertical lines
        h_lines = 0
        v_lines = 0

        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi

            if abs(angle) < 10 or abs(angle - 180) < 10:
                h_lines += 1
            elif abs(angle - 90) < 10 or abs(angle + 90) < 10:
                v_lines += 1

        # Has axes if both horizontal and vertical lines present
        return h_lines > 0 and v_lines > 0

    def _extract_iv_curve_data(self, image: Image.Image) -> Dict[str, Any]:
        """
        Extract I-V curve data from chart image.

        Note: This is a placeholder for advanced curve extraction.
        In production, would use ML-based curve detection and digitization.
        """
        data = {
            "extraction_method": "basic",
            "status": "not_implemented",
            "note": "Advanced curve extraction requires ML-based digitization",
        }

        # Could implement using techniques like:
        # - Color-based curve detection
        # - Edge detection and tracing
        # - ML model for curve digitization
        # - Template matching

        return data

    def perform_visual_qc(
        self,
        image_path: Union[str, Path],
        defect_threshold: float = 0.8,
    ) -> VisualQCResult:
        """
        Perform visual quality control on image.

        Args:
            image_path: Path to image
            defect_threshold: Threshold for defect detection (0-1)

        Returns:
            VisualQCResult object
        """
        image_path = Path(image_path)
        image = self.load_image(image_path)

        defects_detected = []
        quality_metrics = {}

        # Check image quality
        quality_score = self._assess_image_quality(image)
        quality_metrics["quality_score"] = quality_score

        if quality_score < 50:
            defects_detected.append("Low image quality")

        # Check brightness
        gray = image.convert("L")
        brightness = np.array(gray).mean()
        quality_metrics["brightness"] = float(brightness)

        if brightness < 50:
            defects_detected.append("Image too dark")
        elif brightness > 200:
            defects_detected.append("Image too bright")

        # Check contrast
        contrast = np.array(gray).std()
        quality_metrics["contrast"] = float(contrast)

        if contrast < 20:
            defects_detected.append("Low contrast")

        # Check for blur
        if OPENCV_AVAILABLE:
            img_array = np.array(gray)
            laplacian_var = cv2.Laplacian(img_array, cv2.CV_64F).var()
            quality_metrics["sharpness"] = float(laplacian_var)

            if laplacian_var < 100:
                defects_detected.append("Image appears blurry")

        # QC passed if no defects or quality above threshold
        qc_passed = len(defects_detected) == 0 or quality_score >= (
            defect_threshold * 100
        )

        return VisualQCResult(
            image_path=str(image_path),
            qc_passed=qc_passed,
            defects_detected=defects_detected,
            quality_metrics=quality_metrics,
        )

    def save_image(
        self,
        image: Image.Image,
        output_path: Union[str, Path],
        format: Optional[str] = None,
        quality: Optional[int] = None,
    ):
        """
        Save image to file.

        Args:
            image: PIL Image
            output_path: Output file path
            format: Image format (PNG, JPEG, etc.)
            quality: Quality setting (1-100)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fmt = format or self.config.output_format
        qual = quality or self.config.quality

        save_kwargs = {}
        if fmt.upper() in ["JPEG", "JPG"]:
            save_kwargs["quality"] = qual
            save_kwargs["optimize"] = True

        image.save(output_path, format=fmt, **save_kwargs)

    def image_to_base64(self, image: Image.Image, format: str = "PNG") -> str:
        """
        Convert image to base64 string.

        Args:
            image: PIL Image
            format: Image format

        Returns:
            Base64 encoded string
        """
        buffer = BytesIO()
        image.save(buffer, format=format)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode("utf-8")

    async def process_batch_async(
        self,
        file_paths: List[Union[str, Path]],
        operation: str = "ocr",
        **kwargs,
    ) -> List[Any]:
        """
        Process multiple images asynchronously.

        Args:
            file_paths: List of image file paths
            operation: Operation to perform (ocr, extract_chart, visual_qc)
            **kwargs: Additional arguments for the operation

        Returns:
            List of results
        """
        tasks = []
        for file_path in file_paths:
            if operation == "ocr":
                task = asyncio.to_thread(self.perform_ocr, file_path, **kwargs)
            elif operation == "extract_chart":
                task = asyncio.to_thread(self.extract_test_chart, file_path, **kwargs)
            elif operation == "visual_qc":
                task = asyncio.to_thread(self.perform_visual_qc, file_path, **kwargs)
            else:
                raise ValueError(f"Unknown operation: {operation}")

            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error processing {file_paths[idx]}: {result}")
            else:
                valid_results.append(result)

        return valid_results

    def rotate_image(self, image: Image.Image, angle: float) -> Image.Image:
        """Rotate image by specified angle."""
        return image.rotate(angle, expand=True, fillcolor="white")

    def crop_image(
        self, image: Image.Image, bbox: Tuple[int, int, int, int]
    ) -> Image.Image:
        """
        Crop image to bounding box.

        Args:
            image: PIL Image
            bbox: Bounding box (left, top, right, bottom)

        Returns:
            Cropped image
        """
        return image.crop(bbox)
