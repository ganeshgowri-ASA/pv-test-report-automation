"""
Electroluminescence (EL) Defect Detection Module

Advanced defect detection using ML-based techniques:
- ML-based crack detection using OpenCV/scikit-image
- Micro-crack identification with edge detection algorithms
- Cell-level power loss estimation from EL intensity
- Defect map generation overlaid on module layout
- Export defect statistics

Author: PV Test Automation System
License: MIT
"""

import numpy as np
import cv2
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import json
from pathlib import Path
from skimage import filters, morphology, measure, feature
from skimage.morphology import skeletonize, disk
from skimage.filters import threshold_otsu, threshold_local
from scipy import ndimage
import logging

from .image_processor import Defect, DefectType, DefectSeverity

logger = logging.getLogger(__name__)


@dataclass
class CrackFeatures:
    """Features extracted from crack analysis"""
    length: float
    width: float
    orientation: float
    endpoints: List[Tuple[int, int]]
    is_branched: bool
    tortuosity: float  # Ratio of actual length to straight-line distance


@dataclass
class PowerLossEstimate:
    """Cell-level power loss estimation"""
    cell_id: int
    mean_intensity: float
    normalized_intensity: float
    estimated_power_loss: float  # Percentage
    affected_area: float
    defect_count: int


@dataclass
class DefectStatistics:
    """Comprehensive defect statistics"""
    total_defects: int
    defects_by_type: Dict[str, int]
    defects_by_severity: Dict[str, int]
    total_affected_area: float
    critical_cells: List[int]
    defect_density: float  # Defects per cell
    average_defect_size: float
    power_loss_estimates: List[PowerLossEstimate]


class AdvancedDefectDetector:
    """
    Advanced defect detection using ML and computer vision techniques
    """

    def __init__(self,
                 min_crack_length: int = 20,
                 max_crack_width: int = 5,
                 edge_detection_method: str = 'canny',
                 power_loss_model: str = 'linear'):
        """
        Initialize the advanced defect detector

        Args:
            min_crack_length: Minimum crack length in pixels
            max_crack_width: Maximum crack width in pixels
            edge_detection_method: 'canny', 'sobel', 'scharr', 'prewitt'
            power_loss_model: 'linear', 'exponential', or 'quadratic'
        """
        self.min_crack_length = min_crack_length
        self.max_crack_width = max_crack_width
        self.edge_detection_method = edge_detection_method
        self.power_loss_model = power_loss_model

        logger.info("AdvancedDefectDetector initialized")

    def detect_cracks_ml(self, image: np.ndarray,
                        use_gabor_filters: bool = True) -> Tuple[np.ndarray, List[CrackFeatures]]:
        """
        ML-based crack detection using advanced filtering techniques

        Args:
            image: Input grayscale image
            use_gabor_filters: Use Gabor filters for orientation-sensitive detection

        Returns:
            Tuple of (crack_mask, crack_features_list)
        """
        logger.info("Starting ML-based crack detection")

        # Preprocessing
        denoised = cv2.fastNlMeansDenoising(image, h=10)

        if use_gabor_filters:
            # Apply Gabor filter bank for multi-orientation crack detection
            crack_response = self._apply_gabor_filter_bank(denoised)
        else:
            # Use standard edge detection
            crack_response = self._apply_edge_detection(denoised)

        # Morphological operations to enhance crack structures
        crack_mask = self._enhance_crack_structures(crack_response)

        # Extract crack features
        crack_features = self._extract_crack_features(crack_mask)

        logger.info(f"Detected {len(crack_features)} crack structures")
        return crack_mask, crack_features

    def _apply_gabor_filter_bank(self, image: np.ndarray,
                                 num_orientations: int = 8,
                                 frequencies: List[float] = None) -> np.ndarray:
        """
        Apply Gabor filter bank for orientation-sensitive crack detection

        Args:
            image: Input image
            num_orientations: Number of orientations to test
            frequencies: List of frequencies to test

        Returns:
            Maximum response across all filters
        """
        if frequencies is None:
            frequencies = [0.1, 0.2, 0.3]

        height, width = image.shape
        max_response = np.zeros((height, width))

        # Test multiple orientations and frequencies
        for freq in frequencies:
            for i in range(num_orientations):
                theta = i * np.pi / num_orientations

                # Create Gabor kernel
                kernel = cv2.getGaborKernel(
                    ksize=(21, 21),
                    sigma=3.0,
                    theta=theta,
                    lambd=1.0/freq,
                    gamma=0.5,
                    psi=0
                )

                # Apply filter
                filtered = cv2.filter2D(image, cv2.CV_32F, kernel)
                filtered = np.abs(filtered)

                # Keep maximum response
                max_response = np.maximum(max_response, filtered)

        # Normalize to 0-255 range
        max_response = cv2.normalize(max_response, None, 0, 255, cv2.NORM_MINMAX)
        return max_response.astype(np.uint8)

    def _apply_edge_detection(self, image: np.ndarray) -> np.ndarray:
        """
        Apply edge detection based on configured method

        Args:
            image: Input image

        Returns:
            Edge detected image
        """
        if self.edge_detection_method == 'canny':
            edges = cv2.Canny(image, 50, 150)

        elif self.edge_detection_method == 'sobel':
            sobelx = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
            edges = np.sqrt(sobelx**2 + sobely**2)
            edges = cv2.normalize(edges, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        elif self.edge_detection_method == 'scharr':
            scharrx = cv2.Scharr(image, cv2.CV_64F, 1, 0)
            scharry = cv2.Scharr(image, cv2.CV_64F, 0, 1)
            edges = np.sqrt(scharrx**2 + scharry**2)
            edges = cv2.normalize(edges, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        elif self.edge_detection_method == 'prewitt':
            # Prewitt operator using scikit-image
            edges_x = filters.prewitt_h(image)
            edges_y = filters.prewitt_v(image)
            edges = np.sqrt(edges_x**2 + edges_y**2)
            edges = cv2.normalize(edges, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        else:
            # Default to Canny
            edges = cv2.Canny(image, 50, 150)

        return edges

    def _enhance_crack_structures(self, edge_image: np.ndarray) -> np.ndarray:
        """
        Enhance crack structures using morphological operations

        Args:
            edge_image: Edge detected image

        Returns:
            Enhanced crack mask
        """
        # Threshold to binary
        _, binary = cv2.threshold(edge_image, 0, 255,
                                 cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Morphological closing to connect nearby edges
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        # Remove small noise
        opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel)

        # Skeletonize to get thin crack lines
        skeleton = skeletonize(opened // 255)
        skeleton = (skeleton * 255).astype(np.uint8)

        return skeleton

    def _extract_crack_features(self, crack_mask: np.ndarray) -> List[CrackFeatures]:
        """
        Extract features from detected cracks

        Args:
            crack_mask: Binary crack mask

        Returns:
            List of crack features
        """
        crack_features = []

        # Label connected components
        labeled = measure.label(crack_mask)
        regions = measure.regionprops(labeled)

        for region in regions:
            # Filter by minimum crack length
            if region.major_axis_length < self.min_crack_length:
                continue

            # Calculate crack orientation
            orientation = region.orientation

            # Get endpoints (approximate)
            coords = region.coords
            if len(coords) < 2:
                continue

            # Find points furthest apart (approximation of endpoints)
            distances = np.sqrt(((coords[:, None] - coords) ** 2).sum(axis=2))
            i, j = np.unravel_index(distances.argmax(), distances.shape)
            endpoint1 = tuple(coords[i])
            endpoint2 = tuple(coords[j])

            # Calculate straight-line distance
            straight_distance = np.linalg.norm(coords[i] - coords[j])

            # Calculate actual path length (tortuosity)
            actual_length = region.major_axis_length
            tortuosity = actual_length / straight_distance if straight_distance > 0 else 1.0

            # Detect branching (simplified)
            is_branched = region.euler_number < 1

            features = CrackFeatures(
                length=float(region.major_axis_length),
                width=float(region.minor_axis_length),
                orientation=float(orientation),
                endpoints=[endpoint1, endpoint2],
                is_branched=is_branched,
                tortuosity=float(tortuosity)
            )

            crack_features.append(features)

        return crack_features

    def detect_micro_cracks(self, image: np.ndarray,
                           sensitivity: float = 0.8) -> np.ndarray:
        """
        Detect micro-cracks using enhanced edge detection

        Args:
            image: Input grayscale image
            sensitivity: Detection sensitivity (0.0 - 1.0)

        Returns:
            Micro-crack mask
        """
        logger.info("Detecting micro-cracks with enhanced algorithms")

        # Apply local adaptive thresholding
        block_size = 35
        adaptive_thresh = threshold_local(image, block_size, offset=10)
        binary = image < adaptive_thresh

        # Enhance using morphological operations
        selem = disk(1)
        eroded = morphology.erosion(binary, selem)
        dilated = morphology.dilation(eroded, selem)

        # Detect edges in the processed image
        edges = feature.canny(image, sigma=sensitivity)

        # Combine with binary threshold
        micro_cracks = np.logical_and(edges, dilated)

        # Remove very small components
        cleaned = morphology.remove_small_objects(micro_cracks, min_size=10)

        return cleaned.astype(np.uint8) * 255

    def estimate_power_loss(self, cell_image: np.ndarray,
                           defects: List[Defect],
                           cell_id: int,
                           reference_intensity: Optional[float] = None) -> PowerLossEstimate:
        """
        Estimate cell-level power loss from EL intensity

        Args:
            cell_image: Cell image
            defects: List of defects in the cell
            cell_id: Cell identifier
            reference_intensity: Reference intensity for healthy cell

        Returns:
            PowerLossEstimate object
        """
        # Calculate mean intensity
        mean_intensity = np.mean(cell_image)

        # Use provided reference or assume 200 as typical healthy cell intensity
        if reference_intensity is None:
            reference_intensity = 200.0

        # Normalize intensity
        normalized_intensity = mean_intensity / reference_intensity

        # Calculate affected area
        total_affected_area = sum(d.area_percentage for d in defects)

        # Estimate power loss based on model
        if self.power_loss_model == 'linear':
            # Simple linear model: power loss proportional to intensity reduction
            base_loss = (1 - normalized_intensity) * 100
            defect_loss = total_affected_area * 0.5  # Each % area contributes 0.5% loss
            estimated_power_loss = min(base_loss + defect_loss, 100.0)

        elif self.power_loss_model == 'exponential':
            # Exponential model for severe degradation
            base_loss = (1 - np.exp(-2 * (1 - normalized_intensity))) * 100
            defect_loss = total_affected_area * 0.7
            estimated_power_loss = min(base_loss + defect_loss, 100.0)

        elif self.power_loss_model == 'quadratic':
            # Quadratic model
            base_loss = ((1 - normalized_intensity) ** 2) * 150
            defect_loss = total_affected_area * 0.6
            estimated_power_loss = min(base_loss + defect_loss, 100.0)

        else:
            # Default to linear
            estimated_power_loss = (1 - normalized_intensity) * 100

        return PowerLossEstimate(
            cell_id=cell_id,
            mean_intensity=float(mean_intensity),
            normalized_intensity=float(normalized_intensity),
            estimated_power_loss=float(estimated_power_loss),
            affected_area=float(total_affected_area),
            defect_count=len(defects)
        )

    def generate_defect_map(self, image: np.ndarray,
                           defects: List[Defect],
                           cell_boundaries: List[np.ndarray],
                           grid_layout: Tuple[int, int]) -> np.ndarray:
        """
        Generate defect map overlaid on module layout

        Args:
            image: Original EL image
            defects: List of all defects
            cell_boundaries: Cell boundary coordinates
            grid_layout: Module grid layout (rows, cols)

        Returns:
            Defect map visualization
        """
        # Create colored overlay
        overlay = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        # Draw grid
        rows, cols = grid_layout
        height, width = image.shape
        cell_height = height // rows
        cell_width = width // cols

        # Draw grid lines
        for i in range(1, rows):
            y = i * cell_height
            cv2.line(overlay, (0, y), (width, y), (100, 100, 100), 1)

        for j in range(1, cols):
            x = j * cell_width
            cv2.line(overlay, (x, 0), (x, height), (100, 100, 100), 1)

        # Create heat map based on defect density
        heatmap = np.zeros((rows, cols))

        for defect in defects:
            if defect.cell_id is not None:
                row = defect.cell_id // cols
                col = defect.cell_id % cols
                if row < rows and col < cols:
                    # Weight by severity
                    weight = {
                        DefectSeverity.CRITICAL: 4,
                        DefectSeverity.HIGH: 3,
                        DefectSeverity.MEDIUM: 2,
                        DefectSeverity.LOW: 1
                    }.get(defect.severity, 1)
                    heatmap[row, col] += weight

        # Normalize heatmap
        if heatmap.max() > 0:
            heatmap = heatmap / heatmap.max()

        # Apply heatmap overlay
        for i in range(rows):
            for j in range(cols):
                if heatmap[i, j] > 0:
                    y1 = i * cell_height
                    y2 = (i + 1) * cell_height
                    x1 = j * cell_width
                    x2 = (j + 1) * cell_width

                    # Create color based on defect density (green to red)
                    intensity = int(heatmap[i, j] * 255)
                    color_overlay = np.zeros((y2-y1, x2-x1, 3), dtype=np.uint8)
                    color_overlay[:, :, 2] = intensity  # Red channel
                    color_overlay[:, :, 1] = 255 - intensity  # Green channel

                    # Blend with original
                    alpha = 0.3
                    overlay[y1:y2, x1:x2] = cv2.addWeighted(
                        overlay[y1:y2, x1:x2], 1-alpha,
                        color_overlay, alpha, 0
                    )

        # Mark individual defects
        for defect in defects:
            # Only mark critical and high severity defects
            if defect.severity in [DefectSeverity.CRITICAL, DefectSeverity.HIGH]:
                x, y, w, h = defect.bounding_box
                color = (0, 0, 255) if defect.severity == DefectSeverity.CRITICAL else (0, 165, 255)
                cv2.rectangle(overlay, (x, y), (x+w, y+h), color, 2)

        logger.info("Generated defect map with heatmap overlay")
        return overlay

    def calculate_statistics(self, defects: List[Defect],
                            cell_images: List[np.ndarray],
                            grid_layout: Tuple[int, int]) -> DefectStatistics:
        """
        Calculate comprehensive defect statistics

        Args:
            defects: List of all defects
            cell_images: List of cell images
            grid_layout: Module grid layout

        Returns:
            DefectStatistics object
        """
        # Count defects by type
        defects_by_type = {}
        for defect in defects:
            type_name = defect.defect_type.value
            defects_by_type[type_name] = defects_by_type.get(type_name, 0) + 1

        # Count defects by severity
        defects_by_severity = {}
        for defect in defects:
            severity_name = defect.severity.value
            defects_by_severity[severity_name] = defects_by_severity.get(severity_name, 0) + 1

        # Calculate total affected area
        total_affected_area = sum(d.area_percentage for d in defects)

        # Identify critical cells
        cell_defect_counts = {}
        for defect in defects:
            if defect.cell_id is not None:
                cell_defect_counts[defect.cell_id] = cell_defect_counts.get(defect.cell_id, 0) + 1

        # Critical cells: cells with >3 defects or any critical severity defect
        critical_cells = []
        for cell_id, count in cell_defect_counts.items():
            if count > 3:
                critical_cells.append(cell_id)
            else:
                # Check for critical severity defects
                for defect in defects:
                    if defect.cell_id == cell_id and defect.severity == DefectSeverity.CRITICAL:
                        if cell_id not in critical_cells:
                            critical_cells.append(cell_id)

        # Calculate defect density
        total_cells = grid_layout[0] * grid_layout[1]
        defect_density = len(defects) / total_cells if total_cells > 0 else 0

        # Calculate average defect size
        average_defect_size = np.mean([d.area_pixels for d in defects]) if defects else 0

        # Estimate power loss for each cell
        power_loss_estimates = []
        for cell_id, cell_image in enumerate(cell_images):
            cell_defects = [d for d in defects if d.cell_id == cell_id]
            power_loss = self.estimate_power_loss(cell_image, cell_defects, cell_id)
            power_loss_estimates.append(power_loss)

        statistics = DefectStatistics(
            total_defects=len(defects),
            defects_by_type=defects_by_type,
            defects_by_severity=defects_by_severity,
            total_affected_area=float(total_affected_area),
            critical_cells=critical_cells,
            defect_density=float(defect_density),
            average_defect_size=float(average_defect_size),
            power_loss_estimates=power_loss_estimates
        )

        logger.info(f"Calculated statistics: {len(defects)} total defects, "
                   f"{len(critical_cells)} critical cells")
        return statistics

    def export_statistics(self, statistics: DefectStatistics,
                         output_path: str,
                         format: str = 'json') -> None:
        """
        Export defect statistics to file

        Args:
            statistics: DefectStatistics object
            output_path: Output file path
            format: Output format ('json' or 'csv')
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == 'json':
            # Convert to dictionary
            stats_dict = {
                'total_defects': statistics.total_defects,
                'defects_by_type': statistics.defects_by_type,
                'defects_by_severity': statistics.defects_by_severity,
                'total_affected_area': statistics.total_affected_area,
                'critical_cells': statistics.critical_cells,
                'defect_density': statistics.defect_density,
                'average_defect_size': statistics.average_defect_size,
                'power_loss_estimates': [asdict(p) for p in statistics.power_loss_estimates]
            }

            with open(output_path, 'w') as f:
                json.dump(stats_dict, f, indent=2)

            logger.info(f"Statistics exported to {output_path} (JSON format)")

        elif format == 'csv':
            import csv

            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)

                # Write summary statistics
                writer.writerow(['Metric', 'Value'])
                writer.writerow(['Total Defects', statistics.total_defects])
                writer.writerow(['Total Affected Area (%)', statistics.total_affected_area])
                writer.writerow(['Defect Density (defects/cell)', statistics.defect_density])
                writer.writerow(['Average Defect Size (pixels)', statistics.average_defect_size])
                writer.writerow(['Critical Cells', len(statistics.critical_cells)])
                writer.writerow([])

                # Write defects by type
                writer.writerow(['Defect Type', 'Count'])
                for defect_type, count in statistics.defects_by_type.items():
                    writer.writerow([defect_type, count])
                writer.writerow([])

                # Write defects by severity
                writer.writerow(['Severity', 'Count'])
                for severity, count in statistics.defects_by_severity.items():
                    writer.writerow([severity, count])
                writer.writerow([])

                # Write power loss estimates
                writer.writerow(['Cell ID', 'Mean Intensity', 'Normalized Intensity',
                               'Estimated Power Loss (%)', 'Affected Area (%)', 'Defect Count'])
                for pwr in statistics.power_loss_estimates:
                    writer.writerow([pwr.cell_id, f'{pwr.mean_intensity:.2f}',
                                   f'{pwr.normalized_intensity:.3f}',
                                   f'{pwr.estimated_power_loss:.2f}',
                                   f'{pwr.affected_area:.2f}', pwr.defect_count])

            logger.info(f"Statistics exported to {output_path} (CSV format)")

        else:
            raise ValueError(f"Unsupported format: {format}")

    def export_defects(self, defects: List[Defect], output_path: str) -> None:
        """
        Export detailed defect information to JSON

        Args:
            defects: List of defects
            output_path: Output file path
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        defects_dict = []
        for defect in defects:
            defect_dict = {
                'type': defect.defect_type.value,
                'severity': defect.severity.value,
                'area_pixels': defect.area_pixels,
                'area_percentage': defect.area_percentage,
                'centroid': defect.centroid,
                'bounding_box': defect.bounding_box,
                'cell_id': defect.cell_id,
                'confidence': defect.confidence,
                'metadata': defect.metadata
            }
            defects_dict.append(defect_dict)

        with open(output_path, 'w') as f:
            json.dump(defects_dict, f, indent=2)

        logger.info(f"Exported {len(defects)} defects to {output_path}")
