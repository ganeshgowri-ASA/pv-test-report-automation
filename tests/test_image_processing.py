"""Unit tests for image processing modules"""

import unittest
import numpy as np
import cv2
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from image_processing.models import (
    ImageType,
    DefectType,
    DefectSeverity,
    ProcessingConfig,
)
from image_processing.quality_validator import QualityValidator
from image_processing.defect_detector import DefectDetector
from image_processing.metadata_extractor import MetadataExtractor
from image_processing.processor import ImageProcessor


class TestQualityValidator(unittest.TestCase):
    """Tests for QualityValidator"""

    def setUp(self):
        self.validator = QualityValidator()

    def test_blur_detection_sharp(self):
        """Test blur detection on sharp image"""
        # Create sharp test image
        image = np.random.randint(0, 255, (500, 500), dtype=np.uint8)
        # Add sharp edges
        cv2.rectangle(image, (100, 100), (400, 400), 255, 2)

        blur_score = self.validator._calculate_blur_score(image)
        self.assertGreater(blur_score, 100, "Sharp image should have high blur score")

    def test_blur_detection_blurry(self):
        """Test blur detection on blurry image"""
        # Create sharp image first
        image = np.zeros((500, 500), dtype=np.uint8)
        cv2.rectangle(image, (100, 100), (400, 400), 255, -1)

        # Apply strong blur
        blurry = cv2.GaussianBlur(image, (51, 51), 0)

        blur_score = self.validator._calculate_blur_score(blurry)
        self.assertLess(blur_score, 100, "Blurry image should have low blur score")

    def test_exposure_assessment(self):
        """Test exposure quality assessment"""
        # Normal exposure
        normal = np.random.randint(50, 200, (500, 500), dtype=np.uint8)
        exposure = self.validator._assess_exposure(normal)
        self.assertEqual(exposure, "normal")

        # Underexposed
        dark = np.random.randint(0, 30, (500, 500), dtype=np.uint8)
        exposure = self.validator._assess_exposure(dark)
        self.assertEqual(exposure, "underexposed")

        # Overexposed
        bright = np.random.randint(220, 255, (500, 500), dtype=np.uint8)
        exposure = self.validator._assess_exposure(bright)
        self.assertEqual(exposure, "overexposed")

    def test_quality_metrics_calculation(self):
        """Test comprehensive quality metrics calculation"""
        # Create test image
        image = np.random.randint(0, 255, (640, 480), dtype=np.uint8)

        metrics = self.validator.calculate_metrics(image)

        # Check all metrics are present and valid
        self.assertGreaterEqual(metrics.blur_score, 0)
        self.assertGreaterEqual(metrics.brightness_mean, 0)
        self.assertLessEqual(metrics.brightness_mean, 255)
        self.assertGreaterEqual(metrics.contrast_std, 0)
        self.assertEqual(metrics.resolution, (640, 480))
        self.assertGreaterEqual(metrics.dynamic_range, 0)
        self.assertLessEqual(metrics.dynamic_range, 255)
        self.assertIn(metrics.exposure_quality, ["underexposed", "normal", "overexposed"])

    def test_image_enhancement(self):
        """Test image enhancement functionality"""
        # Create low-quality image
        image = np.random.randint(50, 100, (500, 500), dtype=np.uint8)

        enhanced = self.validator.enhance_image(image)

        # Enhanced image should have different characteristics
        self.assertEqual(enhanced.shape, image.shape)
        self.assertFalse(np.array_equal(image, enhanced))


class TestDefectDetector(unittest.TestCase):
    """Tests for DefectDetector"""

    def setUp(self):
        self.detector = DefectDetector()

    def test_crack_detection(self):
        """Test crack detection in synthetic image"""
        # Create image with line (simulating crack)
        image = np.ones((500, 500), dtype=np.uint8) * 200

        # Draw diagonal line (crack)
        cv2.line(image, (50, 50), (450, 450), 0, 3)

        defects = self.detector._detect_cracks(image)

        # Should detect at least one crack
        self.assertGreater(len(defects), 0)
        self.assertEqual(defects[0].defect_type, DefectType.CRACK)

    def test_dark_spot_detection(self):
        """Test dark spot detection"""
        # Create image with dark region
        image = np.ones((500, 500), dtype=np.uint8) * 200

        # Add dark circle (simulating inactive area)
        cv2.circle(image, (250, 250), 80, 50, -1)

        defects = self.detector._detect_dark_spots(image)

        # Should detect dark spot
        self.assertGreater(len(defects), 0)
        self.assertEqual(defects[0].defect_type, DefectType.DARK_SPOT)

    def test_defect_annotation(self):
        """Test defect annotation on image"""
        image = np.ones((500, 500), dtype=np.uint8) * 200

        # Create mock defects
        from image_processing.models import Defect
        defects = [
            Defect(
                defect_type=DefectType.CRACK,
                severity=DefectSeverity.HIGH,
                location=(100, 100, 50, 50),
                confidence=0.8,
                area_pixels=2500,
            )
        ]

        annotated = self.detector.annotate_defects(image, defects)

        # Annotated image should be color
        self.assertEqual(len(annotated.shape), 3)
        self.assertEqual(annotated.shape[2], 3)

    def test_thermal_hotspot_detection(self):
        """Test hotspot detection in thermal images"""
        # Create thermal image with hotspot
        image = np.random.randint(100, 150, (500, 500), dtype=np.uint8)

        # Add hotspot (bright region)
        cv2.circle(image, (250, 250), 50, 255, -1)

        defects = self.detector._detect_thermal_defects(image)

        # Should detect hotspot
        self.assertGreater(len(defects), 0)
        if defects:
            self.assertEqual(defects[0].defect_type, DefectType.HOTSPOT)


class TestMetadataExtractor(unittest.TestCase):
    """Tests for MetadataExtractor"""

    def setUp(self):
        self.extractor = MetadataExtractor()

    def test_file_info_extraction(self):
        """Test basic file information extraction"""
        # Create temporary test file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            test_file = f.name
            # Write some data
            image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            cv2.imwrite(test_file, image)

        try:
            file_info = self.extractor._get_file_info(test_file)

            # Check required fields
            self.assertIn('filename', file_info)
            self.assertIn('file_size_bytes', file_info)
            self.assertIn('file_extension', file_info)
            self.assertIn('created_timestamp', file_info)
            self.assertIn('modified_timestamp', file_info)

            self.assertEqual(file_info['file_extension'], '.jpg')
            self.assertGreater(file_info['file_size_bytes'], 0)

        finally:
            os.unlink(test_file)

    def test_equipment_info_extraction(self):
        """Test equipment information extraction"""
        metadata = {
            'exif': {
                'camera': {
                    'make': 'TestCam',
                    'model': 'TC-1000'
                },
                'SerialNumber': '12345'
            }
        }

        equipment_info = self.extractor.get_equipment_info(metadata)

        self.assertEqual(equipment_info['manufacturer'], 'TestCam')
        self.assertEqual(equipment_info['model'], 'TC-1000')
        self.assertEqual(equipment_info['serial_number'], '12345')


class TestImageProcessor(unittest.TestCase):
    """Tests for main ImageProcessor"""

    def setUp(self):
        self.processor = ImageProcessor(
            operator_id="TEST_OP",
            equipment_id="TEST_EQ"
        )
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Clean up temp directory
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_process_image_el(self):
        """Test processing EL image"""
        # Create test image
        image = np.random.randint(0, 255, (640, 480), dtype=np.uint8)
        # Add some features
        cv2.rectangle(image, (100, 100), (300, 300), 150, -1)

        test_file = os.path.join(self.temp_dir, 'test_el.jpg')
        cv2.imwrite(test_file, image)

        result = self.processor.process_image(test_file, ImageType.EL)

        # Verify result
        self.assertEqual(result.file_path, test_file)
        self.assertEqual(result.image_type, ImageType.EL)
        self.assertIsNotNone(result.file_hash)
        self.assertIsNotNone(result.quality_metrics)
        self.assertEqual(result.operator_id, "TEST_OP")
        self.assertEqual(result.equipment_id, "TEST_EQ")

    def test_file_hash_calculation(self):
        """Test file hash calculation"""
        # Create test file
        test_file = os.path.join(self.temp_dir, 'test.jpg')
        image = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        cv2.imwrite(test_file, image)

        hash1 = self.processor._calculate_file_hash(test_file)

        # Hash should be 64 characters (SHA-256)
        self.assertEqual(len(hash1), 64)

        # Same file should produce same hash
        hash2 = self.processor._calculate_file_hash(test_file)
        self.assertEqual(hash1, hash2)

    def test_batch_processing(self):
        """Test batch image processing"""
        # Create multiple test images
        test_files = []
        image_types = []

        for i in range(3):
            image = np.random.randint(0, 255, (500, 500), dtype=np.uint8)
            test_file = os.path.join(self.temp_dir, f'test_{i}.jpg')
            cv2.imwrite(test_file, image)
            test_files.append(test_file)
            image_types.append(ImageType.EL)

        results = self.processor.process_batch(test_files, image_types)

        # Should have results for all images
        self.assertEqual(len(results), 3)

        for result in results:
            self.assertIsNotNone(result.file_hash)
            self.assertEqual(result.image_type, ImageType.EL)

    def test_result_validation(self):
        """Test result validation"""
        # Create test image and process
        image = np.random.randint(0, 255, (500, 500), dtype=np.uint8)
        test_file = os.path.join(self.temp_dir, 'test.jpg')
        cv2.imwrite(test_file, image)

        result = self.processor.process_image(test_file, ImageType.VISUAL)

        # Initially not validated
        self.assertFalse(result.validated)

        # Validate
        validated = self.processor.validate_result(
            result,
            reviewer_id="REVIEWER_1",
            notes="Looks good"
        )

        self.assertTrue(validated.validated)
        self.assertEqual(validated.reviewer_notes, "Looks good")
        self.assertIsNotNone(validated.validation_timestamp)


class TestProcessingConfig(unittest.TestCase):
    """Tests for ProcessingConfig"""

    def test_default_config(self):
        """Test default configuration values"""
        config = ProcessingConfig()

        # Check some defaults
        self.assertEqual(config.min_blur_score, 100.0)
        self.assertEqual(config.min_resolution, (640, 480))
        self.assertTrue(config.ocr_enabled)
        self.assertTrue(config.apply_preprocessing)

    def test_custom_config(self):
        """Test custom configuration"""
        config = ProcessingConfig(
            min_blur_score=200.0,
            ocr_enabled=False,
            min_resolution=(1024, 768)
        )

        self.assertEqual(config.min_blur_score, 200.0)
        self.assertFalse(config.ocr_enabled)
        self.assertEqual(config.min_resolution, (1024, 768))


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    unittest.main()
