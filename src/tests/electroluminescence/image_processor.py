"""
Electroluminescence (EL) Image Processing Module

This module provides comprehensive EL image processing capabilities for PV modules:
- Image loading (TIFF, PNG, JPEG formats)
- Preprocessing (noise reduction, contrast enhancement)
- Cell segmentation and boundary detection
- Defect classification and quantification
- Before/after comparison analysis
- Defect progression metrics

Author: PV Test Automation System
License: MIT
"""

import os
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import cv2
from PIL import Image
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DefectType(Enum):
    """Enumeration of PV module defect types"""
    CRACK = "crack"
    BROKEN_CELL = "broken_cell"
    INACTIVE_AREA = "inactive_area"
    FINGER_INTERRUPTION = "finger_interruption"
    MICRO_CRACK = "micro_crack"
    DARK_SPOT = "dark_spot"
    HOTSPOT = "hotspot"
    UNKNOWN = "unknown"


class DefectSeverity(Enum):
    """Enumeration of defect severity levels"""
    CRITICAL = "critical"  # > 10% cell area affected
    HIGH = "high"          # 5-10% cell area affected
    MEDIUM = "medium"      # 2-5% cell area affected
    LOW = "low"            # < 2% cell area affected


@dataclass
class Defect:
    """Data class representing a detected defect"""
    defect_type: DefectType
    severity: DefectSeverity
    area_pixels: float
    area_percentage: float
    centroid: Tuple[int, int]
    bounding_box: Tuple[int, int, int, int]  # (x, y, width, height)
    cell_id: Optional[int] = None
    confidence: float = 1.0
    metadata: Dict = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """Data class for image processing results"""
    original_image: np.ndarray
    processed_image: np.ndarray
    segmented_cells: List[np.ndarray]
    defects: List[Defect]
    cell_boundaries: List[np.ndarray]
    metadata: Dict = field(default_factory=dict)


class ELImageProcessor:
    """
    Main class for processing electroluminescence images of PV modules
    """

    def __init__(self,
                 cell_size: Tuple[int, int] = (156, 156),
                 grid_layout: Tuple[int, int] = (6, 10),
                 min_defect_area: int = 50,
                 enable_adaptive_processing: bool = True):
        """
        Initialize the EL image processor

        Args:
            cell_size: Expected cell size in mm (width, height)
            grid_layout: Grid layout (rows, cols) of cells in module
            min_defect_area: Minimum defect area in pixels to detect
            enable_adaptive_processing: Enable adaptive thresholding
        """
        self.cell_size = cell_size
        self.grid_layout = grid_layout
        self.min_defect_area = min_defect_area
        self.enable_adaptive_processing = enable_adaptive_processing

        # Processing parameters
        self.gaussian_kernel_size = (5, 5)
        self.bilateral_d = 9
        self.bilateral_sigma_color = 75
        self.bilateral_sigma_space = 75
        self.clahe_clip_limit = 2.0
        self.clahe_tile_grid_size = (8, 8)

        logger.info("ELImageProcessor initialized")

    def load_image(self, image_path: str) -> np.ndarray:
        """
        Load an EL image from file (supports TIFF, PNG, JPEG)

        Args:
            image_path: Path to the image file

        Returns:
            Loaded image as numpy array (grayscale)

        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If image cannot be loaded
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Try loading with OpenCV first
        try:
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if image is not None:
                logger.info(f"Loaded image {image_path} with OpenCV - Shape: {image.shape}")
                return image
        except Exception as e:
            logger.warning(f"OpenCV failed to load image: {e}")

        # Try loading with PIL for TIFF support
        try:
            pil_image = Image.open(image_path)
            # Convert to grayscale if not already
            if pil_image.mode != 'L':
                pil_image = pil_image.convert('L')
            image = np.array(pil_image)
            logger.info(f"Loaded image {image_path} with PIL - Shape: {image.shape}")
            return image
        except Exception as e:
            raise ValueError(f"Failed to load image {image_path}: {e}")

    def preprocess_image(self, image: np.ndarray,
                        denoise: bool = True,
                        enhance_contrast: bool = True) -> np.ndarray:
        """
        Preprocess EL image with noise reduction and contrast enhancement

        Args:
            image: Input grayscale image
            denoise: Apply denoising filters
            enhance_contrast: Apply contrast enhancement

        Returns:
            Preprocessed image
        """
        processed = image.copy()

        # Noise reduction
        if denoise:
            # Apply Gaussian blur for initial smoothing
            processed = cv2.GaussianBlur(processed, self.gaussian_kernel_size, 0)

            # Apply bilateral filter to preserve edges while reducing noise
            processed = cv2.bilateralFilter(processed,
                                           self.bilateral_d,
                                           self.bilateral_sigma_color,
                                           self.bilateral_sigma_space)
            logger.debug("Applied noise reduction filters")

        # Contrast enhancement using CLAHE (Contrast Limited Adaptive Histogram Equalization)
        if enhance_contrast:
            clahe = cv2.createCLAHE(clipLimit=self.clahe_clip_limit,
                                   tileGridSize=self.clahe_tile_grid_size)
            processed = clahe.apply(processed)
            logger.debug("Applied CLAHE contrast enhancement")

        return processed

    def segment_cells(self, image: np.ndarray) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """
        Segment individual cells and detect cell boundaries

        Args:
            image: Preprocessed EL image

        Returns:
            Tuple of (segmented_cells, cell_boundaries)
        """
        height, width = image.shape
        rows, cols = self.grid_layout

        # Calculate expected cell dimensions
        cell_height = height // rows
        cell_width = width // cols

        segmented_cells = []
        cell_boundaries = []

        # Grid-based segmentation
        for i in range(rows):
            for j in range(cols):
                y1 = i * cell_height
                y2 = (i + 1) * cell_height if i < rows - 1 else height
                x1 = j * cell_width
                x2 = (j + 1) * cell_width if j < cols - 1 else width

                # Extract cell region
                cell = image[y1:y2, x1:x2]
                segmented_cells.append(cell)

                # Create boundary coordinates
                boundary = np.array([
                    [x1, y1],
                    [x2, y1],
                    [x2, y2],
                    [x1, y2]
                ])
                cell_boundaries.append(boundary)

        logger.info(f"Segmented {len(segmented_cells)} cells from {rows}x{cols} grid")

        # Refine boundaries using edge detection
        cell_boundaries = self._refine_cell_boundaries(image, cell_boundaries)

        return segmented_cells, cell_boundaries

    def _refine_cell_boundaries(self, image: np.ndarray,
                               initial_boundaries: List[np.ndarray]) -> List[np.ndarray]:
        """
        Refine cell boundaries using edge detection

        Args:
            image: Input image
            initial_boundaries: Initial boundary estimates

        Returns:
            Refined boundaries
        """
        # Apply Canny edge detection
        edges = cv2.Canny(image, 50, 150)

        # For production, we would use the edge information to adjust boundaries
        # For now, return initial boundaries (can be enhanced with contour detection)

        return initial_boundaries

    def classify_defects(self, cell: np.ndarray, cell_id: int) -> List[Defect]:
        """
        Classify defects in a single cell

        Args:
            cell: Cell image
            cell_id: Cell identifier

        Returns:
            List of detected defects
        """
        defects = []
        cell_area = cell.shape[0] * cell.shape[1]

        # Apply adaptive thresholding to identify dark regions (potential defects)
        if self.enable_adaptive_processing:
            binary = cv2.adaptiveThreshold(cell, 255,
                                          cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                          cv2.THRESH_BINARY_INV,
                                          11, 2)
        else:
            # Use Otsu's method for automatic threshold determination
            _, binary = cv2.threshold(cell, 0, 255,
                                     cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Find contours of potential defects
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)

            # Filter out noise (small areas)
            if area < self.min_defect_area:
                continue

            # Calculate defect properties
            M = cv2.moments(contour)
            if M['m00'] == 0:
                continue

            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])

            x, y, w, h = cv2.boundingRect(contour)
            area_percentage = (area / cell_area) * 100

            # Classify defect type based on characteristics
            defect_type = self._classify_defect_type(contour, area, w, h)

            # Determine severity based on area percentage
            severity = self._determine_severity(area_percentage)

            defect = Defect(
                defect_type=defect_type,
                severity=severity,
                area_pixels=area,
                area_percentage=area_percentage,
                centroid=(cx, cy),
                bounding_box=(x, y, w, h),
                cell_id=cell_id,
                confidence=0.85,  # Can be enhanced with ML confidence scores
                metadata={'aspect_ratio': w/h if h > 0 else 0}
            )

            defects.append(defect)

        return defects

    def _classify_defect_type(self, contour: np.ndarray,
                             area: float,
                             width: int,
                             height: int) -> DefectType:
        """
        Classify defect type based on geometric features

        Args:
            contour: Defect contour
            area: Defect area
            width: Bounding box width
            height: Bounding box height

        Returns:
            Classified defect type
        """
        aspect_ratio = width / height if height > 0 else 0
        perimeter = cv2.arcLength(contour, True)
        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0

        # Classification rules based on geometric features
        if aspect_ratio > 5 or aspect_ratio < 0.2:
            # Linear defects likely cracks or finger interruptions
            if width > height:
                return DefectType.FINGER_INTERRUPTION
            else:
                return DefectType.CRACK

        elif area > 5000 and circularity > 0.5:
            # Large circular defects
            return DefectType.INACTIVE_AREA

        elif area < 200 and circularity < 0.3:
            # Small irregular defects
            return DefectType.MICRO_CRACK

        elif area > 10000:
            # Very large defects
            return DefectType.BROKEN_CELL

        else:
            # Dark spots or unknown defects
            return DefectType.DARK_SPOT

    def _determine_severity(self, area_percentage: float) -> DefectSeverity:
        """
        Determine defect severity based on area percentage

        Args:
            area_percentage: Percentage of cell area affected

        Returns:
            Defect severity level
        """
        if area_percentage > 10:
            return DefectSeverity.CRITICAL
        elif area_percentage > 5:
            return DefectSeverity.HIGH
        elif area_percentage > 2:
            return DefectSeverity.MEDIUM
        else:
            return DefectSeverity.LOW

    def generate_annotated_image(self, image: np.ndarray,
                                defects: List[Defect],
                                cell_boundaries: List[np.ndarray]) -> np.ndarray:
        """
        Generate annotated image with defect highlights

        Args:
            image: Original image
            defects: List of detected defects
            cell_boundaries: Cell boundary coordinates

        Returns:
            Annotated image (color)
        """
        # Convert to color image for annotations
        if len(image.shape) == 2:
            annotated = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            annotated = image.copy()

        # Draw cell boundaries
        for boundary in cell_boundaries:
            cv2.polylines(annotated, [boundary], True, (0, 255, 0), 1)

        # Define colors for different defect types
        defect_colors = {
            DefectType.CRACK: (0, 0, 255),              # Red
            DefectType.BROKEN_CELL: (255, 0, 255),      # Magenta
            DefectType.INACTIVE_AREA: (255, 165, 0),    # Orange
            DefectType.FINGER_INTERRUPTION: (255, 255, 0),  # Yellow
            DefectType.MICRO_CRACK: (0, 165, 255),      # Light Red
            DefectType.DARK_SPOT: (128, 0, 128),        # Purple
            DefectType.HOTSPOT: (0, 0, 128),            # Dark Red
            DefectType.UNKNOWN: (128, 128, 128)         # Gray
        }

        # Draw defect annotations
        for defect in defects:
            color = defect_colors.get(defect.defect_type, (128, 128, 128))
            x, y, w, h = defect.bounding_box

            # Draw bounding box with thickness based on severity
            thickness = 3 if defect.severity == DefectSeverity.CRITICAL else 2
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, thickness)

            # Draw centroid
            cv2.circle(annotated, defect.centroid, 5, color, -1)

            # Add label
            label = f"{defect.defect_type.value[:4]}"
            cv2.putText(annotated, label, (x, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        logger.info(f"Generated annotated image with {len(defects)} defects marked")
        return annotated

    def compare_images(self, before_image: np.ndarray,
                      after_image: np.ndarray,
                      before_defects: List[Defect],
                      after_defects: List[Defect]) -> Dict:
        """
        Compare before and after stress test EL images

        Args:
            before_image: EL image before stress test
            after_image: EL image after stress test
            before_defects: Defects detected in before image
            after_defects: Defects detected in after image

        Returns:
            Dictionary containing comparison metrics
        """
        # Calculate image difference
        if before_image.shape != after_image.shape:
            # Resize to match dimensions
            after_image = cv2.resize(after_image,
                                    (before_image.shape[1], before_image.shape[0]))

        # Compute absolute difference
        diff_image = cv2.absdiff(before_image, after_image)

        # Calculate mean difference
        mean_diff = np.mean(diff_image)
        max_diff = np.max(diff_image)

        # Count defects by type
        before_counts = self._count_defects_by_type(before_defects)
        after_counts = self._count_defects_by_type(after_defects)

        # Calculate progression metrics
        new_defects = len(after_defects) - len(before_defects)
        defect_increase_rate = (new_defects / len(before_defects) * 100
                               if len(before_defects) > 0 else 0)

        # Calculate total affected area
        before_area = sum(d.area_percentage for d in before_defects)
        after_area = sum(d.area_percentage for d in after_defects)
        area_increase = after_area - before_area

        comparison_result = {
            'mean_difference': float(mean_diff),
            'max_difference': float(max_diff),
            'before_defect_count': len(before_defects),
            'after_defect_count': len(after_defects),
            'new_defects': new_defects,
            'defect_increase_rate': defect_increase_rate,
            'before_affected_area': before_area,
            'after_affected_area': after_area,
            'area_increase': area_increase,
            'before_defects_by_type': before_counts,
            'after_defects_by_type': after_counts,
            'difference_image': diff_image
        }

        logger.info(f"Comparison complete: {new_defects} new defects detected")
        return comparison_result

    def _count_defects_by_type(self, defects: List[Defect]) -> Dict[str, int]:
        """
        Count defects by type

        Args:
            defects: List of defects

        Returns:
            Dictionary mapping defect type to count
        """
        counts = {}
        for defect in defects:
            type_name = defect.defect_type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts

    def calculate_defect_progression(self, before_defects: List[Defect],
                                    after_defects: List[Defect]) -> Dict:
        """
        Calculate detailed defect progression metrics

        Args:
            before_defects: Defects before stress test
            after_defects: Defects after stress test

        Returns:
            Dictionary of progression metrics
        """
        metrics = {
            'total_progression': len(after_defects) - len(before_defects),
            'severity_distribution_before': self._count_by_severity(before_defects),
            'severity_distribution_after': self._count_by_severity(after_defects),
            'type_progression': {},
            'critical_defects_increase': 0,
            'high_severity_increase': 0
        }

        # Calculate progression by defect type
        before_by_type = self._count_defects_by_type(before_defects)
        after_by_type = self._count_defects_by_type(after_defects)

        all_types = set(list(before_by_type.keys()) + list(after_by_type.keys()))
        for defect_type in all_types:
            before_count = before_by_type.get(defect_type, 0)
            after_count = after_by_type.get(defect_type, 0)
            metrics['type_progression'][defect_type] = after_count - before_count

        # Count critical and high severity increases
        before_critical = len([d for d in before_defects
                              if d.severity == DefectSeverity.CRITICAL])
        after_critical = len([d for d in after_defects
                             if d.severity == DefectSeverity.CRITICAL])
        metrics['critical_defects_increase'] = after_critical - before_critical

        before_high = len([d for d in before_defects
                          if d.severity == DefectSeverity.HIGH])
        after_high = len([d for d in after_defects
                         if d.severity == DefectSeverity.HIGH])
        metrics['high_severity_increase'] = after_high - before_high

        return metrics

    def _count_by_severity(self, defects: List[Defect]) -> Dict[str, int]:
        """
        Count defects by severity level

        Args:
            defects: List of defects

        Returns:
            Dictionary mapping severity to count
        """
        counts = {}
        for defect in defects:
            severity_name = defect.severity.value
            counts[severity_name] = counts.get(severity_name, 0) + 1
        return counts

    def process_image(self, image_path: str) -> ProcessingResult:
        """
        Complete processing pipeline for a single EL image

        Args:
            image_path: Path to EL image file

        Returns:
            ProcessingResult containing all analysis results
        """
        logger.info(f"Starting processing pipeline for {image_path}")

        # Load image
        original_image = self.load_image(image_path)

        # Preprocess
        processed_image = self.preprocess_image(original_image)

        # Segment cells
        segmented_cells, cell_boundaries = self.segment_cells(processed_image)

        # Detect and classify defects in each cell
        all_defects = []
        for cell_id, cell in enumerate(segmented_cells):
            cell_defects = self.classify_defects(cell, cell_id)
            all_defects.extend(cell_defects)

        # Generate metadata
        metadata = {
            'image_path': image_path,
            'image_shape': original_image.shape,
            'total_cells': len(segmented_cells),
            'total_defects': len(all_defects),
            'defects_by_type': self._count_defects_by_type(all_defects),
            'defects_by_severity': self._count_by_severity(all_defects)
        }

        result = ProcessingResult(
            original_image=original_image,
            processed_image=processed_image,
            segmented_cells=segmented_cells,
            defects=all_defects,
            cell_boundaries=cell_boundaries,
            metadata=metadata
        )

        logger.info(f"Processing complete: {len(all_defects)} defects detected in {len(segmented_cells)} cells")
        return result

    def batch_process(self, image_paths: List[str]) -> List[ProcessingResult]:
        """
        Process multiple EL images in batch

        Args:
            image_paths: List of image file paths

        Returns:
            List of ProcessingResult objects
        """
        results = []
        total = len(image_paths)

        logger.info(f"Starting batch processing of {total} images")

        for idx, image_path in enumerate(image_paths, 1):
            try:
                logger.info(f"Processing image {idx}/{total}: {image_path}")
                result = self.process_image(image_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {image_path}: {e}")
                continue

        logger.info(f"Batch processing complete: {len(results)}/{total} successful")
        return results
