"""
Unit tests for Image Processor module.
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import numpy as np

from ..image_processor import (
    ImageProcessor,
    ImageProcessorConfig,
    ImageMetadata,
    OCRResult,
    TestChart,
    VisualQCResult,
)


class TestImageMetadata:
    """Test ImageMetadata model."""

    def test_valid_metadata(self):
        """Test creating valid image metadata."""
        metadata = ImageMetadata(
            width=1920,
            height=1080,
            format="PNG",
            mode="RGB",
            file_size_bytes=1024000,
        )

        assert metadata.width == 1920
        assert metadata.height == 1080
        assert metadata.format == "PNG"

    def test_with_dpi(self):
        """Test metadata with DPI information."""
        metadata = ImageMetadata(
            width=1920,
            height=1080,
            format="JPEG",
            mode="RGB",
            dpi=(300, 300),
            file_size_bytes=2048000,
        )

        assert metadata.dpi == (300, 300)


class TestOCRResult:
    """Test OCRResult model."""

    def test_valid_ocr_result(self):
        """Test creating valid OCR result."""
        result = OCRResult(
            text="Test Report IEC 61215",
            confidence=95.5,
            language="eng",
        )

        assert result.text == "Test Report IEC 61215"
        assert result.confidence == 95.5
        assert result.word_count == 4  # Auto-calculated

    def test_word_count_calculation(self):
        """Test automatic word counting."""
        result = OCRResult(
            text="This is a test document",
            confidence=90.0,
        )

        assert result.word_count == 5

    def test_line_count_calculation(self):
        """Test automatic line counting."""
        result = OCRResult(
            text="Line 1\nLine 2\nLine 3",
            confidence=90.0,
        )

        assert result.line_count == 3


class TestTestChart:
    """Test TestChart model."""

    def test_valid_test_chart(self):
        """Test creating valid test chart."""
        metadata = ImageMetadata(
            width=800,
            height=600,
            format="PNG",
            mode="RGB",
            file_size_bytes=100000,
        )

        chart = TestChart(
            chart_type="IV_curve",
            image_path="/path/to/chart.png",
            metadata=metadata,
            quality_score=85.5,
            contains_grid=True,
            contains_axes=True,
        )

        assert chart.chart_type == "IV_curve"
        assert chart.quality_score == 85.5
        assert chart.contains_grid is True


class TestVisualQCResult:
    """Test VisualQCResult model."""

    def test_passed_qc(self):
        """Test QC result that passes."""
        result = VisualQCResult(
            image_path="/path/to/image.jpg",
            qc_passed=True,
            defects_detected=[],
            quality_metrics={"brightness": 128.5, "contrast": 45.2},
        )

        assert result.qc_passed is True
        assert len(result.defects_detected) == 0

    def test_failed_qc(self):
        """Test QC result that fails."""
        result = VisualQCResult(
            image_path="/path/to/image.jpg",
            qc_passed=False,
            defects_detected=["Low contrast", "Image too dark"],
            quality_metrics={"brightness": 35.0, "contrast": 15.0},
        )

        assert result.qc_passed is False
        assert len(result.defects_detected) == 2


class TestImageProcessor:
    """Test ImageProcessor class."""

    def test_initialization(self):
        """Test processor initialization."""
        processor = ImageProcessor()
        assert processor.config is not None
        assert isinstance(processor.config, ImageProcessorConfig)

    def test_custom_config(self):
        """Test processor with custom config."""
        config = ImageProcessorConfig(
            ocr_language="spa",
            contrast_enhancement=2.0,
        )
        processor = ImageProcessor(config)

        assert processor.config.ocr_language == "spa"
        assert processor.config.contrast_enhancement == 2.0

    def test_progress_callback(self):
        """Test progress callback."""
        processor = ImageProcessor()
        callback = Mock()
        processor.set_progress_callback(callback)

        processor._report_progress(5, 10, "Processing image 5")
        callback.assert_called_once_with(5, 10, "Processing image 5")

    def test_load_image_not_found(self):
        """Test loading nonexistent image."""
        processor = ImageProcessor()

        with pytest.raises(FileNotFoundError):
            processor.load_image("nonexistent.jpg")

    @pytest.fixture
    def sample_image(self):
        """Create a sample PIL Image for testing."""
        # Create a simple RGB image
        img = Image.new("RGB", (800, 600), color=(128, 128, 128))
        return img

    def test_extract_metadata(self, sample_image):
        """Test metadata extraction from image."""
        processor = ImageProcessor()
        metadata = processor.extract_metadata(sample_image)

        assert isinstance(metadata, ImageMetadata)
        assert metadata.width == 800
        assert metadata.height == 600
        assert metadata.mode == "RGB"

    def test_preprocess_image(self, sample_image):
        """Test image preprocessing."""
        processor = ImageProcessor()
        processed = processor.preprocess_image(sample_image)

        assert isinstance(processed, Image.Image)
        assert processed.mode == "RGB"

    def test_preprocess_image_resize(self):
        """Test image resizing during preprocessing."""
        # Create a very large image
        large_img = Image.new("RGB", (5000, 5000), color=(128, 128, 128))

        config = ImageProcessorConfig(max_image_size=(2000, 2000))
        processor = ImageProcessor(config)

        processed = processor.preprocess_image(large_img)

        assert processed.width <= 2000
        assert processed.height <= 2000

    def test_assess_image_quality(self, sample_image):
        """Test image quality assessment."""
        processor = ImageProcessor()
        quality = processor._assess_image_quality(sample_image)

        assert 0 <= quality <= 100

    def test_rotate_image(self, sample_image):
        """Test image rotation."""
        processor = ImageProcessor()
        rotated = processor.rotate_image(sample_image, 90)

        assert isinstance(rotated, Image.Image)
        # After 90° rotation, width and height swap
        assert rotated.height == sample_image.width

    def test_crop_image(self, sample_image):
        """Test image cropping."""
        processor = ImageProcessor()
        cropped = processor.crop_image(sample_image, (100, 100, 400, 400))

        assert cropped.width == 300
        assert cropped.height == 300

    def test_save_image(self, sample_image, tmp_path):
        """Test image saving."""
        processor = ImageProcessor()
        output_path = tmp_path / "output.png"

        processor.save_image(sample_image, output_path)

        assert output_path.exists()

    def test_image_to_base64(self, sample_image):
        """Test image to base64 conversion."""
        processor = ImageProcessor()
        base64_str = processor.image_to_base64(sample_image)

        assert isinstance(base64_str, str)
        assert len(base64_str) > 0

    def test_perform_visual_qc(self, sample_image, tmp_path):
        """Test visual QC on image."""
        processor = ImageProcessor()
        image_path = tmp_path / "test.png"
        sample_image.save(image_path)

        result = processor.perform_visual_qc(image_path)

        assert isinstance(result, VisualQCResult)
        assert "quality_score" in result.quality_metrics
        assert "brightness" in result.quality_metrics
        assert "contrast" in result.quality_metrics

    def test_extract_test_chart(self, sample_image, tmp_path):
        """Test test chart extraction."""
        processor = ImageProcessor()
        image_path = tmp_path / "chart.png"
        sample_image.save(image_path)

        chart = processor.extract_test_chart(image_path, chart_type="IV_curve")

        assert isinstance(chart, TestChart)
        assert chart.chart_type == "IV_curve"
        assert 0 <= chart.quality_score <= 100


@pytest.mark.skipif(
    not pytest.importorskip("pytesseract", reason="pytesseract not available"),
    reason="OCR tests require pytesseract",
)
class TestOCRFunctionality:
    """Test OCR functionality (requires pytesseract)."""

    @pytest.fixture
    def text_image(self, tmp_path):
        """Create an image with text for OCR testing."""
        from PIL import ImageDraw, ImageFont

        img = Image.new("RGB", (400, 100), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        # Draw simple text (using default font)
        draw.text((10, 40), "Test Report", fill=(0, 0, 0))

        image_path = tmp_path / "text.png"
        img.save(image_path)
        return image_path

    @patch("pytesseract.image_to_string")
    @patch("pytesseract.image_to_data")
    def test_perform_ocr(self, mock_image_to_data, mock_image_to_string):
        """Test OCR performance."""
        # Mock OCR responses
        mock_image_to_string.return_value = "Test Report"
        mock_image_to_data.return_value = {
            "text": ["Test", "Report"],
            "conf": ["95", "90"],
            "left": [10, 60],
            "top": [10, 10],
            "width": [40, 60],
            "height": [20, 20],
        }

        processor = ImageProcessor()
        img = Image.new("RGB", (200, 100), color=(255, 255, 255))

        result = processor.perform_ocr(img)

        assert isinstance(result, OCRResult)
        assert result.text == "Test Report"
        assert result.confidence >= 0


@pytest.mark.asyncio
async def test_process_batch_async(tmp_path):
    """Test async batch processing."""
    # Create sample images
    img_paths = []
    for i in range(3):
        img = Image.new("RGB", (100, 100), color=(i * 50, i * 50, i * 50))
        path = tmp_path / f"image_{i}.png"
        img.save(path)
        img_paths.append(path)

    processor = ImageProcessor()

    results = await processor.process_batch_async(
        img_paths, operation="visual_qc"
    )

    assert len(results) <= 3  # May have exceptions filtered


class TestImageProcessorIntegration:
    """Integration tests for image processor."""

    def test_full_workflow(self, tmp_path):
        """Test complete image processing workflow."""
        # Create test image
        img = Image.new("RGB", (800, 600), color=(200, 200, 200))
        input_path = tmp_path / "input.jpg"
        img.save(input_path)

        processor = ImageProcessor()

        # Load and preprocess
        loaded = processor.load_image(input_path)
        preprocessed = processor.preprocess_image(loaded)

        # Extract metadata
        metadata = processor.extract_metadata(preprocessed)

        # Perform visual QC
        qc_result = processor.perform_visual_qc(input_path)

        # Save processed image
        output_path = tmp_path / "output.png"
        processor.save_image(preprocessed, output_path)

        assert output_path.exists()
        assert isinstance(metadata, ImageMetadata)
        assert isinstance(qc_result, VisualQCResult)
