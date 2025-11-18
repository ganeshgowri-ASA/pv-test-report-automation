"""
Image Quality Validation Module

Provides comprehensive image quality validation including blur detection,
lighting uniformity, resolution requirements, and contrast/brightness validation.
"""

import cv2
import numpy as np
from typing import Tuple, List, Optional
from . import QualityMetrics, ImageQualityError


class ImageValidator:
    """Validates image quality for PV test lab requirements."""

    # Default quality thresholds
    MIN_BLUR_THRESHOLD = 100.0  # Laplacian variance threshold
    MIN_RESOLUTION_EL = (1920, 1080)  # Minimum resolution for EL images
    MIN_RESOLUTION_VISUAL = (1280, 720)  # Minimum resolution for visual inspection
    MIN_LIGHTING_UNIFORMITY = 0.7  # 0-1 scale
    MIN_CONTRAST = 20.0  # RMS contrast
    BRIGHTNESS_RANGE = (30.0, 225.0)  # Acceptable brightness range

    def __init__(
        self,
        min_blur_threshold: float = MIN_BLUR_THRESHOLD,
        min_resolution: Optional[Tuple[int, int]] = None,
        min_lighting_uniformity: float = MIN_LIGHTING_UNIFORMITY,
        min_contrast: float = MIN_CONTRAST,
        brightness_range: Tuple[float, float] = BRIGHTNESS_RANGE
    ):
        """
        Initialize image validator with custom thresholds.

        Args:
            min_blur_threshold: Minimum Laplacian variance (higher = sharper)
            min_resolution: Minimum (width, height) required
            min_lighting_uniformity: Minimum lighting uniformity score 0-1
            min_contrast: Minimum RMS contrast
            brightness_range: Acceptable (min, max) brightness range
        """
        self.min_blur_threshold = min_blur_threshold
        self.min_resolution = min_resolution or self.MIN_RESOLUTION_VISUAL
        self.min_lighting_uniformity = min_lighting_uniformity
        self.min_contrast = min_contrast
        self.brightness_range = brightness_range

    def validate_image(self, image: np.ndarray) -> QualityMetrics:
        """
        Perform comprehensive quality validation on an image.

        Args:
            image: Input image as numpy array (BGR or grayscale)

        Returns:
            QualityMetrics object with validation results

        Raises:
            ImageQualityError: If image is invalid or cannot be processed
        """
        if image is None or image.size == 0:
            raise ImageQualityError("Image is empty or invalid")

        errors: List[str] = []

        # Check blur
        is_blurry, blur_score = self._detect_blur(image)
        if is_blurry:
            errors.append(f"Image is blurry (score: {blur_score:.2f}, threshold: {self.min_blur_threshold})")

        # Check lighting uniformity
        lighting_uniformity = self._check_lighting_uniformity(image)
        if lighting_uniformity < self.min_lighting_uniformity:
            errors.append(f"Lighting uniformity too low ({lighting_uniformity:.2f}, min: {self.min_lighting_uniformity})")

        # Check contrast
        contrast = self._calculate_contrast(image)
        if contrast < self.min_contrast:
            errors.append(f"Contrast too low ({contrast:.2f}, min: {self.min_contrast})")

        # Check brightness
        brightness = self._calculate_brightness(image)
        if not (self.brightness_range[0] <= brightness <= self.brightness_range[1]):
            errors.append(f"Brightness out of range ({brightness:.2f}, range: {self.brightness_range})")

        # Check resolution
        meets_resolution = self._check_resolution(image)
        if not meets_resolution:
            errors.append(f"Resolution too low ({image.shape[1]}x{image.shape[0]}, min: {self.min_resolution[0]}x{self.min_resolution[1]})")

        quality_passed = len(errors) == 0

        return QualityMetrics(
            is_blurry=is_blurry,
            blur_score=blur_score,
            lighting_uniformity=lighting_uniformity,
            contrast=contrast,
            brightness=brightness,
            meets_resolution_requirements=meets_resolution,
            quality_passed=quality_passed,
            quality_errors=errors
        )

    def _detect_blur(self, image: np.ndarray) -> Tuple[bool, float]:
        """
        Detect if image is blurry using Laplacian variance method.

        Args:
            image: Input image

        Returns:
            Tuple of (is_blurry, blur_score)
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Calculate Laplacian variance
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        blur_score = laplacian.var()

        is_blurry = blur_score < self.min_blur_threshold

        return is_blurry, float(blur_score)

    def _check_lighting_uniformity(self, image: np.ndarray) -> float:
        """
        Check lighting uniformity across the image.

        Uses coefficient of variation of local mean intensities.

        Args:
            image: Input image

        Returns:
            Lighting uniformity score 0-1 (higher is more uniform)
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Divide image into grid and calculate mean intensity for each cell
        grid_size = 8
        h, w = gray.shape
        cell_h, cell_w = h // grid_size, w // grid_size

        means = []
        for i in range(grid_size):
            for j in range(grid_size):
                cell = gray[i*cell_h:(i+1)*cell_h, j*cell_w:(j+1)*cell_w]
                means.append(np.mean(cell))

        means = np.array(means)

        # Calculate coefficient of variation (CV)
        mean_intensity = np.mean(means)
        std_intensity = np.std(means)

        if mean_intensity == 0:
            return 0.0

        cv = std_intensity / mean_intensity

        # Convert CV to 0-1 scale (lower CV = higher uniformity)
        # CV of 0.3 or higher is considered non-uniform
        uniformity = max(0.0, min(1.0, 1.0 - (cv / 0.3)))

        return float(uniformity)

    def _calculate_contrast(self, image: np.ndarray) -> float:
        """
        Calculate RMS (Root Mean Square) contrast.

        Args:
            image: Input image

        Returns:
            RMS contrast value
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Calculate RMS contrast
        mean_intensity = np.mean(gray)
        rms_contrast = np.sqrt(np.mean((gray - mean_intensity) ** 2))

        return float(rms_contrast)

    def _calculate_brightness(self, image: np.ndarray) -> float:
        """
        Calculate mean brightness.

        Args:
            image: Input image

        Returns:
            Mean brightness value 0-255
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        return float(np.mean(gray))

    def _check_resolution(self, image: np.ndarray) -> bool:
        """
        Check if image meets minimum resolution requirements.

        Args:
            image: Input image

        Returns:
            True if resolution is adequate
        """
        h, w = image.shape[:2]
        return w >= self.min_resolution[0] and h >= self.min_resolution[1]


def validate_color_calibration(image: np.ndarray, reference_colors: Optional[List[Tuple[int, int, int]]] = None) -> bool:
    """
    Validate color calibration using reference color patches.

    Args:
        image: Input image in BGR format
        reference_colors: List of expected RGB values for color patches

    Returns:
        True if color calibration is acceptable
    """
    # This is a simplified implementation
    # In production, you would detect color calibration targets (e.g., ColorChecker)
    # and compare detected colors to reference values

    if reference_colors is None:
        # No reference provided, skip validation
        return True

    # Placeholder for actual color calibration logic
    # Would involve:
    # 1. Detect color calibration target in image
    # 2. Extract color patches
    # 3. Compare to reference values using Delta E color difference
    # 4. Return True if average Delta E < threshold

    return True


def detect_motion_blur(image: np.ndarray) -> Tuple[bool, float]:
    """
    Detect motion blur specifically (vs. general blur).

    Args:
        image: Input image

    Returns:
        Tuple of (has_motion_blur, directional_score)
    """
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Apply FFT to detect directional blur patterns
    f_transform = np.fft.fft2(gray)
    f_shift = np.fft.fftshift(f_transform)
    magnitude_spectrum = 20 * np.log(np.abs(f_shift) + 1)

    # Detect directional patterns in frequency domain
    # High directional score indicates motion blur
    h, w = magnitude_spectrum.shape
    center_h, center_w = h // 2, w // 2

    # Sample horizontal and vertical lines through center
    horizontal = magnitude_spectrum[center_h, :]
    vertical = magnitude_spectrum[:, center_w]

    h_var = np.var(horizontal)
    v_var = np.var(vertical)

    directional_score = abs(h_var - v_var) / (h_var + v_var + 1e-6)

    # Threshold for motion blur detection
    has_motion_blur = directional_score > 0.3

    return has_motion_blur, float(directional_score)


__all__ = [
    'ImageValidator',
    'validate_color_calibration',
    'detect_motion_blur',
]
