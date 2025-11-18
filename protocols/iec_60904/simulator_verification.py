"""
IEC 60904-9: Solar Simulator Performance Requirements

This module implements solar simulator performance verification and classification
according to IEC 60904-9 standard.

Key Features:
- Class A/B/C classification
- Spectral match verification (0.75-0.25, 1.25-0.4, 2.0-0.6 for A/B/C)
- Non-uniformity measurement (<2%, <5%, <10% for A/B/C)
- Temporal instability check (<2%, <5%, <10% for A/B/C)
- Flash duration monitoring
- Performance certification
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
import json


class SimulatorClass(Enum):
    """Solar simulator classification per IEC 60904-9"""
    CLASS_A = "A"
    CLASS_B = "B"
    CLASS_C = "C"
    NOT_CLASSIFIED = "Not Classified"


class SimulatorType(Enum):
    """Solar simulator types"""
    CONTINUOUS = "continuous"
    PULSED_SINGLE_FLASH = "pulsed_single_flash"
    PULSED_MULTI_FLASH = "pulsed_multi_flash"


@dataclass
class PerformanceCriteria:
    """
    Performance criteria for simulator classification

    Per IEC 60904-9, three criteria must be met:
    1. Spectral match
    2. Non-uniformity of irradiance
    3. Temporal instability of irradiance
    """
    spectral_match_range: Tuple[float, float]  # (min, max) for each band
    non_uniformity_max_percent: float
    temporal_instability_max_percent: float

    @staticmethod
    def get_class_a_criteria() -> 'PerformanceCriteria':
        """Class A performance criteria"""
        return PerformanceCriteria(
            spectral_match_range=(0.75, 1.25),
            non_uniformity_max_percent=2.0,
            temporal_instability_max_percent=2.0
        )

    @staticmethod
    def get_class_b_criteria() -> 'PerformanceCriteria':
        """Class B performance criteria"""
        return PerformanceCriteria(
            spectral_match_range=(0.6, 1.4),
            non_uniformity_max_percent=5.0,
            temporal_instability_max_percent=5.0
        )

    @staticmethod
    def get_class_c_criteria() -> 'PerformanceCriteria':
        """Class C performance criteria"""
        return PerformanceCriteria(
            spectral_match_range=(0.4, 2.0),
            non_uniformity_max_percent=10.0,
            temporal_instability_max_percent=10.0
        )


@dataclass
class VerificationResult:
    """
    Solar simulator verification result

    Attributes:
        simulator_id: Simulator identification
        verification_date: Date of verification
        simulator_type: Type of simulator
        classification: Achieved classification
        spectral_match: Spectral match results
        non_uniformity: Non-uniformity results
        temporal_instability: Temporal instability results
        compliant: Overall compliance status
        recommendations: Recommendations for improvement
        metadata: Additional verification metadata
    """
    simulator_id: str
    verification_date: datetime
    simulator_type: SimulatorType
    classification: SimulatorClass
    spectral_match: Dict[str, Any]
    non_uniformity: Dict[str, Any]
    temporal_instability: Dict[str, Any]
    compliant: bool
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'simulator_id': self.simulator_id,
            'verification_date': self.verification_date.isoformat(),
            'simulator_type': self.simulator_type.value,
            'classification': self.classification.value,
            'spectral_match': self.spectral_match,
            'non_uniformity': self.non_uniformity,
            'temporal_instability': self.temporal_instability,
            'compliant': self.compliant,
            'recommendations': self.recommendations,
            'metadata': self.metadata,
            'standard': 'IEC 60904-9:2020'
        }

    def to_json(self) -> str:
        """Export as JSON"""
        return json.dumps(self.to_dict(), indent=2)


class SimulatorVerification:
    """
    Solar Simulator Performance Verification (IEC 60904-9)

    Verifies and classifies solar simulators according to three criteria:
    1. Spectral match to reference (AM1.5G)
    2. Spatial non-uniformity of irradiance
    3. Temporal instability of irradiance
    """

    # IEC 60904-9 wavelength bands for spectral match
    WAVELENGTH_BANDS = [
        (400, 500, "400-500nm"),
        (500, 600, "500-600nm"),
        (600, 700, "600-700nm"),
        (700, 800, "700-800nm"),
        (800, 900, "800-900nm"),
        (900, 1100, "900-1100nm")
    ]

    def __init__(self, simulator_id: str, simulator_type: SimulatorType):
        """
        Initialize simulator verification

        Args:
            simulator_id: Simulator identification
            simulator_type: Type of simulator
        """
        self.simulator_id = simulator_id
        self.simulator_type = simulator_type

    def verify_spectral_match(
        self,
        measured_spectrum: Dict[float, float],  # wavelength (nm) -> irradiance
        reference_spectrum: Dict[float, float]
    ) -> Dict[str, Any]:
        """
        Verify spectral match in defined wavelength bands

        The spectral match is calculated as the ratio of measured to reference
        irradiance integrated over each wavelength band.

        Args:
            measured_spectrum: Measured spectrum (wavelength nm -> W/m²/nm)
            reference_spectrum: Reference spectrum (AM1.5G)

        Returns:
            Dictionary with spectral match results for each band
        """
        band_results = []

        for wl_min, wl_max, band_name in self.WAVELENGTH_BANDS:
            # Integrate measured spectrum over band
            measured_integral = self._integrate_spectrum(
                measured_spectrum, wl_min, wl_max
            )

            # Integrate reference spectrum over band
            reference_integral = self._integrate_spectrum(
                reference_spectrum, wl_min, wl_max
            )

            # Calculate ratio
            if reference_integral > 0:
                ratio = measured_integral / reference_integral
            else:
                ratio = 0.0

            band_results.append({
                'band': band_name,
                'wavelength_range_nm': (wl_min, wl_max),
                'measured_integral': float(measured_integral),
                'reference_integral': float(reference_integral),
                'ratio': float(ratio)
            })

        # Extract ratios for classification
        ratios = [r['ratio'] for r in band_results]
        min_ratio = min(ratios)
        max_ratio = max(ratios)

        # Determine classification based on spectral match
        spectral_class = self._classify_spectral_match(min_ratio, max_ratio)

        return {
            'band_results': band_results,
            'min_ratio': float(min_ratio),
            'max_ratio': float(max_ratio),
            'spectral_classification': spectral_class.value,
            'standard': 'IEC 60904-9:2020'
        }

    def verify_non_uniformity(
        self,
        irradiance_grid: np.ndarray,
        test_plane_area_cm2: float
    ) -> Dict[str, Any]:
        """
        Verify spatial non-uniformity of irradiance

        Non-uniformity is calculated as:
        NU = (E_max - E_min) / (E_max + E_min) × 100%

        Measurements should cover the test plane area.

        Args:
            irradiance_grid: 2D array of irradiance measurements (W/m²)
            test_plane_area_cm2: Test plane area in cm²

        Returns:
            Dictionary with non-uniformity results
        """
        if irradiance_grid.size == 0:
            raise ValueError("Irradiance grid cannot be empty")

        # Calculate statistics
        e_max = np.max(irradiance_grid)
        e_min = np.min(irradiance_grid)
        e_mean = np.mean(irradiance_grid)
        e_std = np.std(irradiance_grid)

        # Calculate non-uniformity per IEC 60904-9
        if (e_max + e_min) > 0:
            non_uniformity_percent = ((e_max - e_min) / (e_max + e_min)) * 100.0
        else:
            non_uniformity_percent = 0.0

        # Alternative metric: coefficient of variation
        cv_percent = (e_std / e_mean) * 100.0 if e_mean > 0 else 0.0

        # Determine classification
        uniformity_class = self._classify_non_uniformity(non_uniformity_percent)

        # Create spatial map summary
        grid_shape = irradiance_grid.shape
        measurement_points = irradiance_grid.size

        return {
            'non_uniformity_percent': float(non_uniformity_percent),
            'e_max': float(e_max),
            'e_min': float(e_min),
            'e_mean': float(e_mean),
            'e_std': float(e_std),
            'cv_percent': float(cv_percent),
            'uniformity_classification': uniformity_class.value,
            'measurement_points': int(measurement_points),
            'grid_shape': grid_shape,
            'test_plane_area_cm2': float(test_plane_area_cm2),
            'standard': 'IEC 60904-9:2020'
        }

    def verify_temporal_instability(
        self,
        irradiance_time_series: np.ndarray,
        sampling_rate_hz: float,
        measurement_duration_s: float
    ) -> Dict[str, Any]:
        """
        Verify temporal instability of irradiance

        Temporal instability depends on simulator type:
        - Continuous: measured over long-term stability (LTS) and short-term stability (STS)
        - Pulsed: measured during flash duration

        Instability = (E_max - E_min) / (E_max + E_min) × 100%

        Args:
            irradiance_time_series: Array of irradiance vs time measurements
            sampling_rate_hz: Sampling rate in Hz
            measurement_duration_s: Total measurement duration in seconds

        Returns:
            Dictionary with temporal instability results
        """
        if len(irradiance_time_series) == 0:
            raise ValueError("Time series cannot be empty")

        # Calculate statistics
        e_max = np.max(irradiance_time_series)
        e_min = np.min(irradiance_time_series)
        e_mean = np.mean(irradiance_time_series)
        e_std = np.std(irradiance_time_series)

        # Calculate temporal instability per IEC 60904-9
        if (e_max + e_min) > 0:
            instability_percent = ((e_max - e_min) / (e_max + e_min)) * 100.0
        else:
            instability_percent = 0.0

        # Calculate drift (linear trend)
        time_array = np.arange(len(irradiance_time_series)) / sampling_rate_hz
        coeffs = np.polyfit(time_array, irradiance_time_series, 1)
        drift_slope = coeffs[0]
        drift_percent = (drift_slope * measurement_duration_s / e_mean) * 100.0 if e_mean > 0 else 0.0

        # Determine classification
        stability_class = self._classify_temporal_instability(instability_percent)

        # Specific metrics for pulsed simulators
        if self.simulator_type != SimulatorType.CONTINUOUS:
            flash_duration = self._calculate_flash_duration(
                irradiance_time_series, sampling_rate_hz, e_mean
            )
        else:
            flash_duration = None

        return {
            'temporal_instability_percent': float(instability_percent),
            'e_max': float(e_max),
            'e_min': float(e_min),
            'e_mean': float(e_mean),
            'e_std': float(e_std),
            'drift_percent': float(drift_percent),
            'stability_classification': stability_class.value,
            'measurement_duration_s': float(measurement_duration_s),
            'sampling_rate_hz': float(sampling_rate_hz),
            'flash_duration_ms': float(flash_duration * 1000) if flash_duration else None,
            'simulator_type': self.simulator_type.value,
            'standard': 'IEC 60904-9:2020'
        }

    def perform_full_verification(
        self,
        measured_spectrum: Dict[float, float],
        reference_spectrum: Dict[float, float],
        irradiance_grid: np.ndarray,
        test_plane_area_cm2: float,
        irradiance_time_series: np.ndarray,
        sampling_rate_hz: float,
        measurement_duration_s: float
    ) -> VerificationResult:
        """
        Perform complete simulator verification

        Args:
            measured_spectrum: Measured spectrum
            reference_spectrum: Reference spectrum (AM1.5G)
            irradiance_grid: Spatial irradiance measurements
            test_plane_area_cm2: Test plane area
            irradiance_time_series: Temporal irradiance measurements
            sampling_rate_hz: Sampling rate
            measurement_duration_s: Measurement duration

        Returns:
            VerificationResult object
        """
        # Perform individual verifications
        spectral_match = self.verify_spectral_match(measured_spectrum, reference_spectrum)
        non_uniformity = self.verify_non_uniformity(irradiance_grid, test_plane_area_cm2)
        temporal_instability = self.verify_temporal_instability(
            irradiance_time_series, sampling_rate_hz, measurement_duration_s
        )

        # Determine overall classification (most restrictive)
        spectral_class = SimulatorClass(spectral_match['spectral_classification'])
        uniformity_class = SimulatorClass(non_uniformity['uniformity_classification'])
        stability_class = SimulatorClass(temporal_instability['stability_classification'])

        overall_class = self._determine_overall_classification(
            spectral_class, uniformity_class, stability_class
        )

        # Check compliance
        compliant = overall_class != SimulatorClass.NOT_CLASSIFIED

        # Generate recommendations
        recommendations = self._generate_recommendations(
            spectral_match, non_uniformity, temporal_instability, overall_class
        )

        result = VerificationResult(
            simulator_id=self.simulator_id,
            verification_date=datetime.now(),
            simulator_type=self.simulator_type,
            classification=overall_class,
            spectral_match=spectral_match,
            non_uniformity=non_uniformity,
            temporal_instability=temporal_instability,
            compliant=compliant,
            recommendations=recommendations,
            metadata={
                'test_plane_area_cm2': test_plane_area_cm2,
                'measurement_duration_s': measurement_duration_s,
                'iso17025_compliant': True
            }
        )

        return result

    def _integrate_spectrum(
        self,
        spectrum: Dict[float, float],
        wl_min: float,
        wl_max: float
    ) -> float:
        """Integrate spectrum over wavelength range"""
        # Filter wavelengths in range
        wavelengths = sorted([wl for wl in spectrum.keys() if wl_min <= wl <= wl_max])

        if len(wavelengths) < 2:
            return 0.0

        values = np.array([spectrum[wl] for wl in wavelengths])
        wavelengths = np.array(wavelengths)

        # Trapezoidal integration
        return float(np.trapz(values, wavelengths))

    def _classify_spectral_match(self, min_ratio: float, max_ratio: float) -> SimulatorClass:
        """Classify based on spectral match criteria"""
        # Class A: 0.75 ≤ ratio ≤ 1.25
        if 0.75 <= min_ratio and max_ratio <= 1.25:
            return SimulatorClass.CLASS_A
        # Class B: 0.6 ≤ ratio ≤ 1.4
        elif 0.6 <= min_ratio and max_ratio <= 1.4:
            return SimulatorClass.CLASS_B
        # Class C: 0.4 ≤ ratio ≤ 2.0
        elif 0.4 <= min_ratio and max_ratio <= 2.0:
            return SimulatorClass.CLASS_C
        else:
            return SimulatorClass.NOT_CLASSIFIED

    def _classify_non_uniformity(self, non_uniformity_percent: float) -> SimulatorClass:
        """Classify based on non-uniformity criteria"""
        if non_uniformity_percent <= 2.0:
            return SimulatorClass.CLASS_A
        elif non_uniformity_percent <= 5.0:
            return SimulatorClass.CLASS_B
        elif non_uniformity_percent <= 10.0:
            return SimulatorClass.CLASS_C
        else:
            return SimulatorClass.NOT_CLASSIFIED

    def _classify_temporal_instability(self, instability_percent: float) -> SimulatorClass:
        """Classify based on temporal instability criteria"""
        if instability_percent <= 2.0:
            return SimulatorClass.CLASS_A
        elif instability_percent <= 5.0:
            return SimulatorClass.CLASS_B
        elif instability_percent <= 10.0:
            return SimulatorClass.CLASS_C
        else:
            return SimulatorClass.NOT_CLASSIFIED

    def _determine_overall_classification(
        self,
        spectral_class: SimulatorClass,
        uniformity_class: SimulatorClass,
        stability_class: SimulatorClass
    ) -> SimulatorClass:
        """Determine overall classification (most restrictive)"""
        classes = [spectral_class, uniformity_class, stability_class]

        # If any is not classified, overall is not classified
        if SimulatorClass.NOT_CLASSIFIED in classes:
            return SimulatorClass.NOT_CLASSIFIED

        # Otherwise, take most restrictive (highest letter)
        class_order = {
            SimulatorClass.CLASS_A: 1,
            SimulatorClass.CLASS_B: 2,
            SimulatorClass.CLASS_C: 3
        }

        most_restrictive = max(classes, key=lambda c: class_order.get(c, 999))
        return most_restrictive

    def _calculate_flash_duration(
        self,
        irradiance_time_series: np.ndarray,
        sampling_rate_hz: float,
        mean_irradiance: float
    ) -> float:
        """
        Calculate flash duration for pulsed simulators

        Flash duration is defined as the time during which irradiance
        exceeds 50% of peak irradiance.
        """
        threshold = 0.5 * np.max(irradiance_time_series)
        above_threshold = irradiance_time_series >= threshold
        flash_samples = np.sum(above_threshold)
        flash_duration_s = flash_samples / sampling_rate_hz
        return float(flash_duration_s)

    def _generate_recommendations(
        self,
        spectral_match: Dict[str, Any],
        non_uniformity: Dict[str, Any],
        temporal_instability: Dict[str, Any],
        overall_class: SimulatorClass
    ) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []

        # Spectral match recommendations
        if SimulatorClass(spectral_match['spectral_classification']) != SimulatorClass.CLASS_A:
            recommendations.append(
                f"Spectral match: {spectral_match['spectral_classification']} - "
                "Consider spectral correction filters or lamp replacement"
            )

        # Non-uniformity recommendations
        if SimulatorClass(non_uniformity['uniformity_classification']) != SimulatorClass.CLASS_A:
            recommendations.append(
                f"Non-uniformity: {non_uniformity['non_uniformity_percent']:.1f}% - "
                "Check collimation optics and lamp positioning"
            )

        # Temporal instability recommendations
        if SimulatorClass(temporal_instability['stability_classification']) != SimulatorClass.CLASS_A:
            recommendations.append(
                f"Temporal instability: {temporal_instability['temporal_instability_percent']:.1f}% - "
                "Verify power supply stability and thermal management"
            )

        if overall_class == SimulatorClass.CLASS_A:
            recommendations.append("Excellent performance - maintain regular calibration schedule")
        elif overall_class == SimulatorClass.NOT_CLASSIFIED:
            recommendations.append("CRITICAL: Simulator does not meet minimum IEC 60904-9 requirements")

        return recommendations
