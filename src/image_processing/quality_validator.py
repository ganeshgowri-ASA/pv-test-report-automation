"""Image quality validation module

Implements quality checks for PV test images according to:
- IEC 60904-13: Electroluminescence imaging
- ISO/IEC 17025:2017: Testing and calibration laboratories
"""

import cv2
import numpy as np
from typing import Tuple, Optional
import logging

from .models import QualityMetrics, ProcessingConfig

logger = logging.getLogger(__name__)


class QualityValidator:
    """Validates image quality for PV testing compliance"""

    def __init__(self, config: Optional[ProcessingConfig] = None):
        """Initialize quality validator

        Args:
            config: Processing configuration with quality thresholds
        """
        self.config = config or ProcessingConfig()

    def validate_image(self, image: np.ndarray) -> Tuple[bool, QualityMetrics]:
        """Validate image quality against defined thresholds

        Args:
            image: Input image as numpy array

        Returns:
            Tuple of (passed: bool, metrics: QualityMetrics)
        """
        metrics = self.calculate_metrics(image)
        passed = self._check_thresholds(metrics)

        logger.info(
            f"Image quality validation: {'PASSED' if passed else 'FAILED'} "
            f"(blur={metrics.blur_score:.2f}, brightness={metrics.brightness_mean:.2f})"
        )

        return passed, metrics

    def calculate_metrics(self, image: np.ndarray) -> QualityMetrics:
        """Calculate comprehensive quality metrics for an image

        Args:
            image: Input image (color or grayscale)

        Returns:
            QualityMetrics object with all calculated metrics
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Calculate blur score (Laplacian variance)
        blur_score = self._calculate_blur_score(gray)

        # Calculate brightness
        brightness_mean = float(np.mean(gray))

        # Calculate contrast
        contrast_std = float(np.std(gray))

        # Get resolution
        height, width = gray.shape[:2]
        resolution = (width, height)

        # Calculate dynamic range
        dynamic_range = float(np.max(gray) - np.min(gray))

        # Calculate noise level
        noise_level = self._estimate_noise(gray)

        # Calculate sharpness
        sharpness_score = self._calculate_sharpness(gray)

        # Calculate uniformity
        uniformity_score = self._calculate_uniformity(gray)

        # Assess exposure quality
        exposure_quality = self._assess_exposure(gray)

        return QualityMetrics(
            blur_score=blur_score,
            brightness_mean=brightness_mean,
            contrast_std=contrast_std,
            resolution=resolution,
            dynamic_range=dynamic_range,
            noise_level=noise_level,
            sharpness_score=sharpness_score,
            uniformity_score=uniformity_score,
            exposure_quality=exposure_quality,
        )

    def _calculate_blur_score(self, gray: np.ndarray) -> float:
        """Calculate blur score using Laplacian variance method

        Higher values indicate sharper images. Typical thresholds:
        - < 100: Blurry
        - 100-500: Acceptable
        - > 500: Sharp

        Args:
            gray: Grayscale image

        Returns:
            Laplacian variance score
        """
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        return float(variance)

    def _estimate_noise(self, gray: np.ndarray) -> float:
        """Estimate noise level using median absolute deviation

        Args:
            gray: Grayscale image

        Returns:
            Estimated noise level
        """
        # Use high-pass filter to estimate noise
        kernel = np.array([[-1, -1, -1],
                          [-1, 8, -1],
                          [-1, -1, -1]])
        high_pass = cv2.filter2D(gray.astype(np.float32), -1, kernel)
        noise = np.median(np.abs(high_pass))
        return float(noise)

    def _calculate_sharpness(self, gray: np.ndarray) -> float:
        """Calculate image sharpness using gradient magnitude

        Args:
            gray: Grayscale image

        Returns:
            Sharpness score
        """
        # Calculate gradients
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

        # Calculate gradient magnitude
        gradient_magnitude = np.sqrt(sobelx**2 + sobely**2)
        sharpness = np.mean(gradient_magnitude)

        return float(sharpness)

    def _calculate_uniformity(self, gray: np.ndarray) -> float:
        """Calculate illumination uniformity score

        Based on IEC 60904-13 requirements for EL imaging

        Args:
            gray: Grayscale image

        Returns:
            Uniformity score (0-1, higher is more uniform)
        """
        # Divide image into blocks
        block_size = 64
        h, w = gray.shape

        blocks = []
        for i in range(0, h - block_size, block_size):
            for j in range(0, w - block_size, block_size):
                block = gray[i:i+block_size, j:j+block_size]
                blocks.append(np.mean(block))

        if not blocks:
            return 0.0

        # Calculate coefficient of variation
        mean_intensity = np.mean(blocks)
        std_intensity = np.std(blocks)

        if mean_intensity > 0:
            cv = std_intensity / mean_intensity
            # Convert to 0-1 score (lower CV = higher uniformity)
            uniformity = max(0.0, 1.0 - cv)
        else:
            uniformity = 0.0

        return float(uniformity)

    def _assess_exposure(self, gray: np.ndarray) -> str:
        """Assess exposure quality

        Args:
            gray: Grayscale image

        Returns:
            Exposure assessment: 'underexposed', 'normal', or 'overexposed'
        """
        mean = np.mean(gray)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])

        # Check for underexposure
        if mean < 50 or np.sum(hist[:50]) > 0.6 * gray.size:
            return "underexposed"

        # Check for overexposure
        if mean > 200 or np.sum(hist[200:]) > 0.6 * gray.size:
            return "overexposed"

        return "normal"

    def _check_thresholds(self, metrics: QualityMetrics) -> bool:
        """Check if metrics meet quality thresholds

        Args:
            metrics: Calculated quality metrics

        Returns:
            True if all thresholds are met
        """
        checks = [
            metrics.blur_score >= self.config.min_blur_score,
            metrics.brightness_mean >= self.config.min_brightness,
            metrics.brightness_mean <= self.config.max_brightness,
            metrics.contrast_std >= self.config.min_contrast,
            metrics.resolution[0] >= self.config.min_resolution[0],
            metrics.resolution[1] >= self.config.min_resolution[1],
            metrics.noise_level <= self.config.max_noise_level,
            metrics.sharpness_score >= self.config.min_sharpness,
            metrics.exposure_quality == "normal",
        ]

        return all(checks)

    def enhance_image(self, image: np.ndarray) -> np.ndarray:
        """Apply enhancement to improve image quality

        Args:
            image: Input image

        Returns:
            Enhanced image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Denoise
        enhanced = cv2.fastNlMeansDenoising(enhanced, h=10)

        # Sharpen
        kernel = np.array([[-1, -1, -1],
                          [-1, 9, -1],
                          [-1, -1, -1]]) / 9.0
        enhanced = cv2.filter2D(enhanced, -1, kernel)

        return enhanced
