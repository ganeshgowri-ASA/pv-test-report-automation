"""
Main Image Processor Module

Provides comprehensive image format support, metadata extraction,
and base image processing functionality.
"""

import os
import hashlib
import time
from pathlib import Path
from typing import Optional, Union, Dict, Any, Tuple
from datetime import datetime

import cv2
import numpy as np
from PIL import Image, ExifTags
from PIL.TiffImagePlugin import TiffImageFile

from . import (
    ImageProcessingError,
    ImageFormatError,
    MetadataExtractionError,
    ImageMetadata,
    ImageIngestionResult,
)
from .image_validators import ImageValidator


class ImageProcessor:
    """
    Main image processor for PV test lab automation.

    Supports: JPEG, PNG, BMP, TIFF, GIF, and RAW camera formats (CR2, NEF, ARW).
    """

    SUPPORTED_FORMATS = {
        '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif',
        '.cr2', '.nef', '.arw', '.dng'  # RAW formats
    }

    def __init__(self, validator: Optional[ImageValidator] = None):
        """
        Initialize image processor.

        Args:
            validator: Optional custom ImageValidator instance
        """
        self.validator = validator or ImageValidator()

    def load_image(self, file_path: Union[str, Path]) -> np.ndarray:
        """
        Load image from file supporting multiple formats.

        Args:
            file_path: Path to image file

        Returns:
            Image as numpy array in BGR format

        Raises:
            ImageFormatError: If format is unsupported or file is corrupted
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise ImageFormatError(f"File not found: {file_path}")

        ext = file_path.suffix.lower()
        if ext not in self.SUPPORTED_FORMATS:
            raise ImageFormatError(f"Unsupported format: {ext}")

        try:
            # Try OpenCV first (fastest for most formats)
            image = cv2.imread(str(file_path), cv2.IMREAD_UNCHANGED)

            if image is None:
                # Fall back to PIL for formats OpenCV doesn't support well
                image = self._load_with_pil(file_path)

            if image is None or image.size == 0:
                raise ImageFormatError(f"Failed to load image: {file_path}")

            return image

        except Exception as e:
            raise ImageFormatError(f"Error loading image {file_path}: {str(e)}")

    def _load_with_pil(self, file_path: Path) -> np.ndarray:
        """
        Load image using PIL/Pillow (for formats OpenCV doesn't support).

        Args:
            file_path: Path to image file

        Returns:
            Image as numpy array in BGR format
        """
        try:
            pil_image = Image.open(file_path)

            # Convert to RGB if necessary
            if pil_image.mode == 'P':  # Palette mode
                pil_image = pil_image.convert('RGB')
            elif pil_image.mode == 'RGBA':
                # Create white background and composite
                background = Image.new('RGB', pil_image.size, (255, 255, 255))
                background.paste(pil_image, mask=pil_image.split()[3])
                pil_image = background
            elif pil_image.mode != 'RGB' and pil_image.mode != 'L':
                pil_image = pil_image.convert('RGB')

            # Convert PIL to numpy
            image_array = np.array(pil_image)

            # Convert RGB to BGR for OpenCV compatibility
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

            return image_array

        except Exception as e:
            raise ImageFormatError(f"PIL failed to load image: {str(e)}")

    def extract_metadata(self, file_path: Union[str, Path]) -> ImageMetadata:
        """
        Extract comprehensive metadata including EXIF data.

        Args:
            file_path: Path to image file

        Returns:
            ImageMetadata object

        Raises:
            MetadataExtractionError: If metadata extraction fails
        """
        file_path = Path(file_path)

        try:
            pil_image = Image.open(file_path)

            # Basic metadata
            width, height = pil_image.size
            img_format = pil_image.format or file_path.suffix[1:].upper()
            color_mode = pil_image.mode
            dpi = pil_image.info.get('dpi', None)
            file_size = file_path.stat().st_size

            # Extract EXIF data
            exif_data = {}
            capture_date = None
            camera_model = None
            gps_coordinates = None

            if hasattr(pil_image, '_getexif') and pil_image._getexif():
                exif = pil_image._getexif()
                if exif:
                    exif_data = self._parse_exif(exif)
                    capture_date = exif_data.get('DateTime', None)
                    camera_model = exif_data.get('Model', None)
                    gps_coordinates = self._extract_gps(exif_data)

            return ImageMetadata(
                width=width,
                height=height,
                format=img_format,
                color_mode=color_mode,
                dpi=dpi,
                exif_data=exif_data,
                capture_date=capture_date,
                camera_model=camera_model,
                gps_coordinates=gps_coordinates,
                file_size=file_size
            )

        except Exception as e:
            raise MetadataExtractionError(f"Failed to extract metadata: {str(e)}")

    def _parse_exif(self, exif: Dict[int, Any]) -> Dict[str, Any]:
        """
        Parse EXIF data from PIL format to readable dictionary.

        Args:
            exif: Raw EXIF data from PIL

        Returns:
            Dictionary with readable EXIF tags
        """
        parsed = {}

        for tag_id, value in exif.items():
            tag_name = ExifTags.TAGS.get(tag_id, tag_id)

            # Handle nested EXIF data
            if isinstance(value, bytes):
                try:
                    value = value.decode('utf-8', errors='ignore')
                except:
                    value = str(value)

            parsed[tag_name] = value

        return parsed

    def _extract_gps(self, exif_data: Dict[str, Any]) -> Optional[Tuple[float, float]]:
        """
        Extract GPS coordinates from EXIF data.

        Args:
            exif_data: Parsed EXIF data

        Returns:
            Tuple of (latitude, longitude) or None
        """
        try:
            gps_info = exif_data.get('GPSInfo', {})
            if not gps_info:
                return None

            # This is a simplified version
            # Full implementation would parse GPS IFD properly
            lat = gps_info.get('GPSLatitude')
            lon = gps_info.get('GPSLongitude')

            if lat and lon:
                # Convert from degrees/minutes/seconds to decimal
                lat_decimal = self._convert_to_degrees(lat)
                lon_decimal = self._convert_to_degrees(lon)

                return (lat_decimal, lon_decimal)

        except Exception:
            return None

        return None

    def _convert_to_degrees(self, value) -> float:
        """
        Convert GPS coordinates to decimal degrees.

        Args:
            value: GPS coordinate in degrees/minutes/seconds

        Returns:
            Decimal degree value
        """
        # Simplified conversion
        # Actual implementation depends on GPS data format
        if isinstance(value, (list, tuple)) and len(value) >= 3:
            d, m, s = value[0], value[1], value[2]
            return float(d) + float(m) / 60.0 + float(s) / 3600.0
        return float(value)

    def calculate_file_hash(self, file_path: Union[str, Path]) -> str:
        """
        Calculate SHA-256 hash for ISO 17025 traceability.

        Args:
            file_path: Path to image file

        Returns:
            SHA-256 hash string
        """
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Read in 64kb chunks for efficiency
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def process_image(
        self,
        file_path: Union[str, Path],
        validate_quality: bool = True,
        save_processed: bool = False,
        output_dir: Optional[Union[str, Path]] = None
    ) -> ImageIngestionResult:
        """
        Complete image ingestion and processing pipeline.

        Args:
            file_path: Path to image file
            validate_quality: Whether to perform quality validation
            save_processed: Whether to save processed image
            output_dir: Directory for saving processed images

        Returns:
            ImageIngestionResult object

        Raises:
            ImageProcessingError: If processing fails
        """
        start_time = time.time()
        file_path = Path(file_path)

        try:
            # Load image
            image = self.load_image(file_path)

            # Extract metadata
            metadata = self.extract_metadata(file_path)

            # Calculate file hash
            file_hash = self.calculate_file_hash(file_path)

            # Validate quality
            quality_metrics = None
            quality_passed = True

            if validate_quality:
                quality_metrics = self.validator.validate_image(image)
                quality_passed = quality_metrics.quality_passed

            # Save processed image if requested
            processed_image_path = None
            if save_processed and output_dir:
                processed_image_path = self._save_processed_image(
                    image, file_path, output_dir
                )

            processing_time = time.time() - start_time

            return ImageIngestionResult(
                file_path=str(file_path),
                file_hash=file_hash,
                metadata=metadata,
                quality_metrics=quality_metrics,
                quality_passed=quality_passed,
                processing_time=processing_time,
                original_image_path=str(file_path),
                processed_image_path=processed_image_path
            )

        except Exception as e:
            raise ImageProcessingError(f"Image processing failed: {str(e)}")

    def _save_processed_image(
        self,
        image: np.ndarray,
        original_path: Path,
        output_dir: Union[str, Path]
    ) -> str:
        """
        Save processed image to output directory.

        Args:
            image: Processed image array
            original_path: Original file path
            output_dir: Output directory

        Returns:
            Path to saved image
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{original_path.stem}_processed_{timestamp}{original_path.suffix}"
        output_path = output_dir / output_filename

        cv2.imwrite(str(output_path), image)

        return str(output_path)

    def load_multipage_tiff(self, file_path: Union[str, Path]) -> list[np.ndarray]:
        """
        Load all pages from a multi-page TIFF file.

        Args:
            file_path: Path to TIFF file

        Returns:
            List of images (one per page)

        Raises:
            ImageFormatError: If not a valid TIFF or loading fails
        """
        file_path = Path(file_path)

        try:
            pil_image = Image.open(file_path)

            if not isinstance(pil_image, TiffImageFile):
                raise ImageFormatError("Not a TIFF file")

            images = []
            page = 0

            while True:
                try:
                    pil_image.seek(page)
                    image_array = np.array(pil_image)

                    # Convert to BGR if needed
                    if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                        image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

                    images.append(image_array)
                    page += 1

                except EOFError:
                    break

            return images

        except Exception as e:
            raise ImageFormatError(f"Failed to load multi-page TIFF: {str(e)}")


__all__ = ['ImageProcessor']
