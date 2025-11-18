"""Main image processor orchestrating all image processing operations

Coordinates:
- Image ingestion and validation
- Quality assessment
- Defect detection
- Metadata extraction
- OCR processing
- I-V curve extraction

Compliant with:
- IEC 60904 series (PV testing standards)
- IEC 61215 (Module qualification)
- ISO/IEC 17025:2017 (Testing laboratories)
"""

import os
import hashlib
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from .models import (
    ImageType,
    ImageIngestionResult,
    ProcessingConfig,
    QualityMetrics,
)
from .quality_validator import QualityValidator
from .defect_detector import DefectDetector
from .metadata_extractor import MetadataExtractor
from .ocr_processor import OCRProcessor
from .iv_curve_extractor import IVCurveExtractor

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Main image processor for PV test automation

    Example:
        >>> processor = ImageProcessor()
        >>> result = processor.process_image(
        ...     "path/to/el_image.jpg",
        ...     ImageType.EL
        ... )
        >>> print(f"Found {len(result.defects_detected)} defects")
        >>> print(f"Quality passed: {result.quality_passed}")
    """

    def __init__(
        self,
        config: Optional[ProcessingConfig] = None,
        operator_id: Optional[str] = None,
        equipment_id: Optional[str] = None
    ):
        """Initialize image processor

        Args:
            config: Processing configuration
            operator_id: Operator identification for ISO 17025 compliance
            equipment_id: Equipment identification
        """
        self.config = config or ProcessingConfig()
        self.operator_id = operator_id
        self.equipment_id = equipment_id

        # Initialize sub-processors
        self.quality_validator = QualityValidator(self.config)
        self.defect_detector = DefectDetector(self.config)
        self.metadata_extractor = MetadataExtractor()
        self.ocr_processor = OCRProcessor(self.config)
        self.iv_extractor = IVCurveExtractor(self.config)

        logger.info("ImageProcessor initialized")

    def process_image(
        self,
        file_path: str,
        image_type: ImageType,
        save_annotated: bool = False,
        output_dir: Optional[str] = None
    ) -> ImageIngestionResult:
        """Process an image file through the complete pipeline

        Args:
            file_path: Path to image file
            image_type: Type of image (EL, thermal, visual, IV chart)
            save_annotated: Whether to save annotated image with defects marked
            output_dir: Directory for saving annotated images

        Returns:
            ImageIngestionResult with all processing results

        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If image cannot be read
        """
        logger.info(f"Processing {image_type.value} image: {file_path}")

        # Validate file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")

        # Load image
        image = cv2.imread(file_path)
        if image is None:
            raise ValueError(f"Failed to read image: {file_path}")

        # Calculate file hash for integrity
        file_hash = self._calculate_file_hash(file_path)

        # Extract metadata
        metadata = self.metadata_extractor.extract_metadata(file_path)

        # Validate quality
        quality_passed, quality_metrics = self.quality_validator.validate_image(image)

        # Apply preprocessing if enabled and quality checks failed
        if self.config.apply_preprocessing and not quality_passed:
            logger.info("Applying image enhancement")
            preprocessed = self.quality_validator.enhance_image(image)
        else:
            preprocessed = image

        # Detect defects based on image type
        defects = []
        if image_type in [ImageType.EL, ImageType.THERMAL, ImageType.VISUAL]:
            defects = self.defect_detector.detect_defects(
                image,
                image_type,
                preprocessed
            )

        # Process OCR if enabled
        ocr_text = None
        ocr_data = None
        if self.config.ocr_enabled and image_type != ImageType.IV_CHART:
            ocr_text, ocr_data = self.ocr_processor.extract_text(image)

        # Extract I-V curve data if applicable
        iv_curve_data = None
        if image_type == ImageType.IV_CHART:
            iv_curve_data = self.iv_extractor.extract_iv_curve(image)

        # Create result
        result = ImageIngestionResult(
            file_path=file_path,
            image_type=image_type,
            defects_detected=defects,
            quality_passed=quality_passed,
            quality_metrics=quality_metrics,
            metadata=metadata,
            file_hash=file_hash,
            processing_timestamp=datetime.utcnow(),
            processor_version="1.0.0",
            operator_id=self.operator_id,
            equipment_id=self.equipment_id,
            ocr_text=ocr_text,
            ocr_data=ocr_data,
            iv_curve_data=iv_curve_data,
        )

        # Save annotated image if requested
        if save_annotated and output_dir:
            self._save_annotated_image(
                image,
                result,
                output_dir
            )

        logger.info(
            f"Processing complete: {len(defects)} defects, "
            f"quality={'PASS' if quality_passed else 'FAIL'}"
        )

        return result

    def process_batch(
        self,
        file_paths: list[str],
        image_types: list[ImageType],
        save_annotated: bool = False,
        output_dir: Optional[str] = None
    ) -> list[ImageIngestionResult]:
        """Process multiple images in batch

        Args:
            file_paths: List of image file paths
            image_types: Corresponding image types
            save_annotated: Whether to save annotated images
            output_dir: Directory for annotated images

        Returns:
            List of ImageIngestionResult objects
        """
        if len(file_paths) != len(image_types):
            raise ValueError("file_paths and image_types must have same length")

        results = []
        for file_path, image_type in zip(file_paths, image_types):
            try:
                result = self.process_image(
                    file_path,
                    image_type,
                    save_annotated,
                    output_dir
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                # Continue with other images

        logger.info(f"Batch processing complete: {len(results)}/{len(file_paths)} successful")
        return results

    def validate_result(
        self,
        result: ImageIngestionResult,
        reviewer_id: str,
        notes: Optional[str] = None
    ) -> ImageIngestionResult:
        """Validate and approve processing result

        Args:
            result: Processing result to validate
            reviewer_id: Reviewer identification
            notes: Optional reviewer notes

        Returns:
            Updated result with validation status
        """
        # Mark as validated
        result.validated = True
        result.validation_timestamp = datetime.utcnow()
        result.reviewer_notes = notes

        logger.info(f"Result validated by {reviewer_id}")
        return result

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file for integrity verification

        Args:
            file_path: Path to file

        Returns:
            Hexadecimal hash string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _save_annotated_image(
        self,
        image: np.ndarray,
        result: ImageIngestionResult,
        output_dir: str
    ):
        """Save annotated image with defects marked

        Args:
            image: Original image
            result: Processing result
            output_dir: Output directory
        """
        # Create output directory if needed
        os.makedirs(output_dir, exist_ok=True)

        # Generate output filename
        input_name = Path(result.file_path).stem
        timestamp = result.processing_timestamp.strftime("%Y%m%d_%H%M%S")
        output_name = f"{input_name}_annotated_{timestamp}.jpg"
        output_path = os.path.join(output_dir, output_name)

        # Create annotated image
        if result.defects_detected:
            annotated = self.defect_detector.annotate_defects(
                image,
                result.defects_detected
            )
        else:
            annotated = image

        # Add quality metrics overlay
        annotated = self._add_quality_overlay(annotated, result.quality_metrics)

        # Add metadata overlay
        annotated = self._add_metadata_overlay(annotated, result)

        # Save
        cv2.imwrite(output_path, annotated)
        logger.info(f"Saved annotated image: {output_path}")

    def _add_quality_overlay(
        self,
        image: np.ndarray,
        metrics: QualityMetrics
    ) -> np.ndarray:
        """Add quality metrics overlay to image

        Args:
            image: Input image
            metrics: Quality metrics

        Returns:
            Image with overlay
        """
        annotated = image.copy()

        # Convert to color if grayscale
        if len(annotated.shape) == 2:
            annotated = cv2.cvtColor(annotated, cv2.COLOR_GRAY2BGR)

        # Create semi-transparent overlay area
        overlay = annotated.copy()
        cv2.rectangle(
            overlay,
            (annotated.shape[1] - 300, 0),
            (annotated.shape[1], 200),
            (0, 0, 0),
            -1
        )
        cv2.addWeighted(overlay, 0.7, annotated, 0.3, 0, annotated)

        # Add text
        texts = [
            f"Blur: {metrics.blur_score:.1f}",
            f"Brightness: {metrics.brightness_mean:.1f}",
            f"Contrast: {metrics.contrast_std:.1f}",
            f"Sharpness: {metrics.sharpness_score:.1f}",
            f"Exposure: {metrics.exposure_quality}",
        ]

        y_offset = 25
        for text in texts:
            cv2.putText(
                annotated,
                text,
                (annotated.shape[1] - 290, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )
            y_offset += 30

        return annotated

    def _add_metadata_overlay(
        self,
        image: np.ndarray,
        result: ImageIngestionResult
    ) -> np.ndarray:
        """Add processing metadata overlay

        Args:
            image: Input image
            result: Processing result

        Returns:
            Image with overlay
        """
        annotated = image.copy()

        # Convert to color if grayscale
        if len(annotated.shape) == 2:
            annotated = cv2.cvtColor(annotated, cv2.COLOR_GRAY2BGR)

        # Add header with basic info
        header_texts = [
            f"Type: {result.image_type.value.upper()}",
            f"Defects: {len(result.defects_detected)}",
            f"Quality: {'PASS' if result.quality_passed else 'FAIL'}",
            f"Processed: {result.processing_timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        ]

        # Create semi-transparent header
        overlay = annotated.copy()
        cv2.rectangle(overlay, (0, 0), (600, 80), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, annotated, 0.3, 0, annotated)

        x_offset = 10
        for text in header_texts:
            cv2.putText(
                annotated,
                text,
                (x_offset, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )
            x_offset += 150

        return annotated

    def generate_report(
        self,
        results: list[ImageIngestionResult],
        output_path: str
    ):
        """Generate summary report for processed images

        Args:
            results: List of processing results
            output_path: Path for output report file
        """
        # This could be expanded to generate PDF/HTML reports
        # For now, we'll create a simple text summary

        with open(output_path, 'w') as f:
            f.write("PV Test Image Processing Report\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Generated: {datetime.utcnow().isoformat()}\n")
            f.write(f"Total Images: {len(results)}\n\n")

            # Summary statistics
            passed = sum(1 for r in results if r.quality_passed)
            total_defects = sum(len(r.defects_detected) for r in results)

            f.write("Summary Statistics:\n")
            f.write(f"  Quality Passed: {passed}/{len(results)} ({passed/len(results)*100:.1f}%)\n")
            f.write(f"  Total Defects: {total_defects}\n\n")

            # Per-image details
            f.write("Image Details:\n")
            f.write("-" * 80 + "\n")

            for i, result in enumerate(results, 1):
                f.write(f"\n{i}. {Path(result.file_path).name}\n")
                f.write(f"   Type: {result.image_type.value}\n")
                f.write(f"   Quality: {'PASS' if result.quality_passed else 'FAIL'}\n")
                f.write(f"   Defects: {len(result.defects_detected)}\n")

                if result.defects_detected:
                    f.write("   Detected Defects:\n")
                    for defect in result.defects_detected:
                        f.write(f"     - {defect.defect_type.value} "
                               f"({defect.severity.value}): {defect.description}\n")

                f.write(f"   Hash: {result.file_hash}\n")

        logger.info(f"Report generated: {output_path}")
