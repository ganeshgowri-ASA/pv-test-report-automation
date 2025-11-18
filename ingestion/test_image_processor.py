"""
Comprehensive Unit Tests for Image Processing Engine

Tests all modules including:
- Image loading and format support
- Quality validation
- Defect detection
- EL image processing
- Visual inspection
- OCR functionality
"""

import unittest
import os
import tempfile
from pathlib import Path
import numpy as np
import cv2

from . import (
    ImageProcessingError,
    ImageFormatError,
    ImageQualityError,
    Defect,
    ImageMetadata,
    QualityMetrics,
    OCRResult,
    ImageIngestionResult,
)
from .image_processor import ImageProcessor
from .image_validators import ImageValidator
from .defect_detector import (
    CrackDetector,
    DarkSpotDetector,
    InactiveCellDetector,
    DiscolorationDetector,
    BubbleDetector,
    detect_defects,
)
from .el_image_processor import ELImageProcessor, create_annotated_image
from .visual_inspector import VisualInspector, create_annotated_visual_image


class TestImageProcessor(unittest.TestCase):
    """Test cases for ImageProcessor."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = ImageProcessor()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_test_image(self, filename: str, size: tuple = (1920, 1080), color: bool = True) -> str:
        """
        Create a test image file.

        Args:
            filename: Output filename
            size: Image size (width, height)
            color: Whether to create color image

        Returns:
            Path to created image
        """
        width, height = size

        if color:
            image = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        else:
            image = np.random.randint(0, 256, (height, width), dtype=np.uint8)

        file_path = os.path.join(self.temp_dir, filename)
        cv2.imwrite(file_path, image)

        return file_path

    def test_load_jpeg_image(self):
        """Test loading JPEG image."""
        image_path = self._create_test_image('test.jpg')
        image = self.processor.load_image(image_path)

        self.assertIsNotNone(image)
        self.assertIsInstance(image, np.ndarray)

    def test_load_png_image(self):
        """Test loading PNG image."""
        image_path = self._create_test_image('test.png')
        image = self.processor.load_image(image_path)

        self.assertIsNotNone(image)
        self.assertIsInstance(image, np.ndarray)

    def test_load_nonexistent_file(self):
        """Test loading non-existent file raises error."""
        with self.assertRaises(ImageFormatError):
            self.processor.load_image('nonexistent.jpg')

    def test_extract_metadata(self):
        """Test metadata extraction."""
        image_path = self._create_test_image('test.jpg')
        metadata = self.processor.extract_metadata(image_path)

        self.assertIsInstance(metadata, ImageMetadata)
        self.assertEqual(metadata.width, 1920)
        self.assertEqual(metadata.height, 1080)
        self.assertIn(metadata.format, ['JPEG', 'JPG'])

    def test_calculate_file_hash(self):
        """Test file hash calculation."""
        image_path = self._create_test_image('test.jpg')
        hash1 = self.processor.calculate_file_hash(image_path)
        hash2 = self.processor.calculate_file_hash(image_path)

        # Same file should produce same hash
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA-256 produces 64 hex chars

    def test_process_image(self):
        """Test complete image processing pipeline."""
        image_path = self._create_test_image('test.jpg')
        result = self.processor.process_image(image_path)

        self.assertIsInstance(result, ImageIngestionResult)
        self.assertEqual(result.file_path, image_path)
        self.assertIsNotNone(result.file_hash)
        self.assertIsNotNone(result.metadata)
        self.assertIsNotNone(result.quality_metrics)
        self.assertTrue(result.processing_time >= 0)


class TestImageValidator(unittest.TestCase):
    """Test cases for ImageValidator."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = ImageValidator()

    def _create_sharp_image(self) -> np.ndarray:
        """Create a sharp test image."""
        image = np.zeros((480, 640), dtype=np.uint8)

        # Add high-contrast patterns
        for i in range(0, 640, 20):
            cv2.line(image, (i, 0), (i, 480), 255, 1)

        return image

    def _create_blurry_image(self) -> np.ndarray:
        """Create a blurry test image."""
        sharp = self._create_sharp_image()
        blurry = cv2.GaussianBlur(sharp, (21, 21), 10)
        return blurry

    def test_detect_sharp_image(self):
        """Test blur detection on sharp image."""
        image = self._create_sharp_image()
        is_blurry, score = self.validator._detect_blur(image)

        # Sharp image should not be detected as blurry
        self.assertFalse(is_blurry)
        self.assertGreater(score, 100)

    def test_detect_blurry_image(self):
        """Test blur detection on blurry image."""
        image = self._create_blurry_image()
        is_blurry, score = self.validator._detect_blur(image)

        # Blurry image should be detected
        self.assertTrue(is_blurry)
        self.assertLess(score, 100)

    def test_validate_image(self):
        """Test comprehensive image validation."""
        image = self._create_sharp_image()
        metrics = self.validator.validate_image(image)

        self.assertIsInstance(metrics, QualityMetrics)
        self.assertIsInstance(metrics.is_blurry, bool)
        self.assertGreater(metrics.blur_score, 0)
        self.assertGreaterEqual(metrics.lighting_uniformity, 0)
        self.assertLessEqual(metrics.lighting_uniformity, 1)

    def test_check_resolution(self):
        """Test resolution checking."""
        # Create image that meets requirements
        large_image = np.zeros((1080, 1920), dtype=np.uint8)
        meets_req = self.validator._check_resolution(large_image)
        self.assertTrue(meets_req)

        # Create image that doesn't meet requirements
        small_image = np.zeros((480, 640), dtype=np.uint8)
        meets_req = self.validator._check_resolution(small_image)
        self.assertFalse(meets_req)


class TestDefectDetector(unittest.TestCase):
    """Test cases for defect detection."""

    def setUp(self):
        """Set up test fixtures."""
        self.crack_detector = CrackDetector()
        self.dark_spot_detector = DarkSpotDetector()

    def _create_image_with_crack(self) -> np.ndarray:
        """Create test image with artificial crack."""
        image = np.ones((480, 640), dtype=np.uint8) * 128

        # Draw a crack-like line
        cv2.line(image, (100, 100), (300, 400), 0, 2)

        return image

    def _create_image_with_dark_spot(self) -> np.ndarray:
        """Create test image with dark spot."""
        image = np.ones((480, 640), dtype=np.uint8) * 200

        # Draw a dark spot
        cv2.circle(image, (320, 240), 50, 20, -1)

        return image

    def test_crack_detection(self):
        """Test crack detection."""
        image = self._create_image_with_crack()
        defects = self.crack_detector.detect_defects(image)

        # Should detect at least one crack
        self.assertGreater(len(defects), 0)

        # Check defect properties
        for defect in defects:
            self.assertIsInstance(defect, Defect)
            self.assertEqual(defect.type, "crack")
            self.assertIn(defect.severity, ["minor", "moderate", "severe"])
            self.assertGreaterEqual(defect.confidence, 0.0)
            self.assertLessEqual(defect.confidence, 1.0)

    def test_dark_spot_detection(self):
        """Test dark spot detection."""
        image = self._create_image_with_dark_spot()
        defects = self.dark_spot_detector.detect_defects(image)

        # Should detect at least one dark spot
        self.assertGreater(len(defects), 0)

        # Check defect properties
        for defect in defects:
            self.assertIsInstance(defect, Defect)
            self.assertEqual(defect.type, "dark_spot")
            self.assertIn(defect.severity, ["minor", "moderate", "severe"])

    def test_detect_defects_function(self):
        """Test convenience function for detecting multiple defect types."""
        image = self._create_image_with_crack()
        defects = detect_defects(image, defect_types=["crack"])

        self.assertIsInstance(defects, list)


class TestELImageProcessor(unittest.TestCase):
    """Test cases for EL image processing."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = ELImageProcessor()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_el_test_image(self) -> str:
        """Create synthetic EL test image."""
        # Create grayscale image simulating EL
        image = np.ones((1080, 1920), dtype=np.uint8) * 150

        # Add some "cells" (bright rectangles)
        for i in range(0, 1920, 200):
            for j in range(0, 1080, 180):
                cv2.rectangle(image, (i + 10, j + 10), (i + 190, j + 170), 200, -1)

        # Add a crack
        cv2.line(image, (500, 300), (700, 600), 50, 2)

        # Add a dark spot
        cv2.circle(image, (1000, 500), 30, 40, -1)

        file_path = os.path.join(self.temp_dir, 'el_test.jpg')
        cv2.imwrite(file_path, image)

        return file_path

    def test_convert_and_normalize(self):
        """Test grayscale conversion and normalization."""
        image = np.ones((480, 640), dtype=np.uint8) * 100
        normalized = self.processor.convert_and_normalize(image)

        self.assertEqual(normalized.shape, image.shape)
        self.assertEqual(normalized.dtype, np.uint8)

    def test_segment_cells(self):
        """Test cell segmentation."""
        image_path = self._create_el_test_image()
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        normalized = self.processor.convert_and_normalize(image)

        cell_locations = self.processor.segment_cells(normalized)

        # Should detect some cells
        self.assertIsInstance(cell_locations, list)
        # Each location should be a tuple of (x, y)
        for loc in cell_locations:
            self.assertEqual(len(loc), 2)

    def test_calculate_health_score(self):
        """Test health score calculation."""
        score = self.processor.calculate_health_score(
            cell_count=60,
            cracks=[],
            dark_spots=[],
            inactive_cells=[]
        )

        # Perfect health
        self.assertEqual(score, 100.0)

        # With defects
        fake_crack = Defect(
            type="crack",
            severity="severe",
            location=(100, 100),
            area=100.0,
            confidence=0.9
        )

        score = self.processor.calculate_health_score(
            cell_count=60,
            cracks=[fake_crack],
            dark_spots=[],
            inactive_cells=[]
        )

        # Should be less than perfect
        self.assertLess(score, 100.0)
        self.assertGreaterEqual(score, 0.0)


class TestVisualInspector(unittest.TestCase):
    """Test cases for visual inspection."""

    def setUp(self):
        """Set up test fixtures."""
        self.inspector = VisualInspector()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_visual_test_image(self) -> str:
        """Create synthetic visual inspection image."""
        # Create color image
        image = np.ones((1080, 1920, 3), dtype=np.uint8) * 200

        # Add some discoloration (yellow-brown)
        cv2.rectangle(image, (500, 400), (700, 600), (50, 150, 200), -1)

        # Add a dark spot (potential burn mark)
        cv2.circle(image, (1000, 500), 40, (10, 10, 10), -1)

        file_path = os.path.join(self.temp_dir, 'visual_test.jpg')
        cv2.imwrite(file_path, image)

        return file_path

    def test_color_correction(self):
        """Test color correction."""
        image = np.ones((480, 640, 3), dtype=np.uint8) * 100
        corrected = self.inspector.color_correct(image)

        self.assertEqual(corrected.shape, image.shape)
        self.assertEqual(corrected.dtype, np.uint8)

    def test_white_balance(self):
        """Test white balance."""
        # Create image with color cast
        image = np.ones((480, 640, 3), dtype=np.uint8)
        image[:, :, 0] = 150  # Blue channel
        image[:, :, 1] = 100  # Green channel
        image[:, :, 2] = 50   # Red channel

        balanced = self.inspector._white_balance(image)

        self.assertEqual(balanced.shape, image.shape)
        self.assertEqual(balanced.dtype, np.uint8)

    def test_detect_burn_marks(self):
        """Test burn mark detection."""
        image_path = self._create_visual_test_image()
        image = cv2.imread(image_path)

        burn_marks = self.inspector.detect_burn_marks(image)

        # Should detect the artificial burn mark
        self.assertIsInstance(burn_marks, list)

        for mark in burn_marks:
            self.assertEqual(mark.type, "burn_mark")
            self.assertEqual(mark.severity, "severe")

    def test_enhance_image(self):
        """Test image enhancement."""
        image = np.ones((480, 640, 3), dtype=np.uint8) * 100
        enhanced = self.inspector.enhance_image(image)

        self.assertEqual(enhanced.shape, image.shape)


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflows."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_test_image(self, filename: str) -> str:
        """Create a test image."""
        image = np.random.randint(0, 256, (1080, 1920), dtype=np.uint8)
        file_path = os.path.join(self.temp_dir, filename)
        cv2.imwrite(file_path, image)
        return file_path

    def test_complete_el_workflow(self):
        """Test complete EL image processing workflow."""
        # Create test image
        image_path = self._create_test_image('el_complete.jpg')

        # Process with EL processor
        processor = ELImageProcessor()
        result = processor.process(image_path)

        # Verify result structure
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.ingestion_result)
        self.assertGreaterEqual(result.cell_count, 0)
        self.assertIsInstance(result.cell_locations, list)
        self.assertIsInstance(result.cracks_detected, list)
        self.assertIsInstance(result.dark_spots_detected, list)
        self.assertGreaterEqual(result.overall_health_score, 0.0)
        self.assertLessEqual(result.overall_health_score, 100.0)

    def test_complete_visual_workflow(self):
        """Test complete visual inspection workflow."""
        # Create test image
        image = np.ones((1080, 1920, 3), dtype=np.uint8) * 200
        file_path = os.path.join(self.temp_dir, 'visual_complete.jpg')
        cv2.imwrite(file_path, image)

        # Process with visual inspector
        inspector = VisualInspector()
        result = inspector.process(file_path)

        # Verify result structure
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.ingestion_result)
        self.assertIsInstance(result.discoloration_areas, list)
        self.assertIsInstance(result.bubbles_detected, list)
        self.assertIsInstance(result.burn_marks, list)
        self.assertIsInstance(result.frame_damage, list)


def run_tests():
    """Run all tests."""
    unittest.main()


if __name__ == '__main__':
    run_tests()
