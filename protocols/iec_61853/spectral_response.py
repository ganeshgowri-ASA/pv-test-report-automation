"""
Spectral Response and Angular Dependence Testing - IEC 61853-2
===============================================================

Implements spectral responsivity and angle of incidence measurements:

Spectral Response:
- Wavelength range: 300-1200 nm (covers UV to near-IR)
- Measures quantum efficiency vs wavelength
- Spectral mismatch factor calculation
- Comparison to AM1.5G reference spectrum

Angular Response:
- Incidence angles: 0° to 75° (or up to 85°)
- Measures response vs angle of incidence
- Incidence angle modifier (IAM) calculation
- Critical for energy rating calculations

Applications:
- Spectral corrections for different light sources
- Performance modeling under real-world conditions
- Energy yield calculations with spectral variations
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
import numpy as np
from scipy import interpolate, integrate

from .models import (
    SpectralPoint,
    SpectralCurveData,
    AngularPoint,
    AngularResponseData,
)


# Configure logging
logger = logging.getLogger(__name__)


# ==================== Constants ====================

# Standard wavelength range for PV spectral response
MIN_WAVELENGTH = 300.0  # nm
MAX_WAVELENGTH = 1200.0  # nm

# AM1.5G reference spectrum (simplified, wavelength in nm, irradiance in W/m²/nm)
AM15G_SPECTRUM = {
    300: 0.0, 350: 0.35, 400: 0.85, 450: 1.45, 500: 1.80,
    550: 1.85, 600: 1.75, 650: 1.65, 700: 1.50, 750: 1.35,
    800: 1.20, 850: 1.05, 900: 0.90, 950: 0.75, 1000: 0.60,
    1050: 0.45, 1100: 0.30, 1150: 0.15, 1200: 0.05
}


# ==================== Data Classes ====================

@dataclass
class SpectralTestConfig:
    """Configuration for spectral response testing"""
    wavelength_min: float = MIN_WAVELENGTH  # nm
    wavelength_max: float = MAX_WAVELENGTH  # nm
    wavelength_step: float = 10.0  # nm
    measurement_bandwidth: float = 10.0  # nm
    integration_time: float = 0.1  # seconds
    averaging_count: int = 5


@dataclass
class AngularTestConfig:
    """Configuration for angular response testing"""
    angle_min: float = 0.0  # degrees
    angle_max: float = 75.0  # degrees
    angle_step: float = 5.0  # degrees
    measurement_averaging: int = 10
    rotation_settle_time: float = 2.0  # seconds


# ==================== Spectral Response ====================

class SpectralResponseTest:
    """
    Spectral response measurement system

    Measures quantum efficiency (QE) or spectral response (SR) of PV modules
    across the wavelength range of interest.
    """

    def __init__(
        self,
        monochromator_address: Optional[str] = None,
        config: Optional[SpectralTestConfig] = None
    ):
        self.monochromator_address = monochromator_address
        self.config = config or SpectralTestConfig()
        self._connected = False

    def connect(self) -> bool:
        """Connect to spectral measurement system"""
        logger.info("Connecting to spectral measurement system...")
        # TODO: Implement actual hardware connection
        self._connected = True
        return True

    def disconnect(self):
        """Disconnect from measurement system"""
        logger.info("Disconnecting spectral measurement system...")
        self._connected = False

    def measure_spectral_response(self) -> SpectralCurveData:
        """
        Measure complete spectral response curve

        Returns:
            SpectralCurveData with response vs wavelength
        """
        if not self._connected:
            raise RuntimeError("Spectral measurement system not connected")

        logger.info(
            f"Measuring spectral response from {self.config.wavelength_min}nm "
            f"to {self.config.wavelength_max}nm"
        )

        # Generate wavelength points
        wavelengths = np.arange(
            self.config.wavelength_min,
            self.config.wavelength_max + self.config.wavelength_step,
            self.config.wavelength_step
        )

        spectral_points = []

        for wavelength in wavelengths:
            # Measure response at this wavelength
            response = self._measure_at_wavelength(wavelength)

            spectral_points.append(SpectralPoint(
                wavelength=float(wavelength),
                response=float(response)
            ))

            logger.debug(f"λ={wavelength:.1f}nm, SR={response:.4f}")

        # Normalize to peak response
        responses = np.array([p.response for p in spectral_points])
        peak_response = np.max(responses)
        peak_idx = np.argmax(responses)
        peak_wavelength = spectral_points[peak_idx].wavelength

        # Normalize
        for point in spectral_points:
            point.response /= peak_response

        # Calculate spectral mismatch factor
        mismatch_factor = self._calculate_mismatch_factor(spectral_points)

        logger.info(
            f"Spectral response measured: peak at {peak_wavelength:.1f}nm, "
            f"mismatch factor: {mismatch_factor:.4f}"
        )

        return SpectralCurveData(
            points=spectral_points,
            peak_wavelength=peak_wavelength,
            peak_response=1.0,  # Normalized
            mismatch_factor=mismatch_factor
        )

    def _measure_at_wavelength(self, wavelength: float) -> float:
        """
        Measure response at specific wavelength

        Args:
            wavelength: Wavelength in nm

        Returns:
            Spectral response (relative)
        """
        # TODO: Replace with actual hardware measurement
        # This simulates a typical crystalline silicon response

        # Simulate c-Si spectral response (approximate)
        # Peak around 800-900nm, drops off in UV and IR
        if wavelength < 400:
            # UV cutoff
            response = np.exp(-(400 - wavelength) / 50)
        elif wavelength < 900:
            # Increasing response towards IR
            response = 0.6 + 0.4 * (wavelength - 400) / 500
        else:
            # IR cutoff
            response = np.exp(-(wavelength - 900) / 100)

        # Add some noise
        response *= (1 + np.random.normal(0, 0.02))
        response = max(0.0, min(1.0, response))

        return response

    def _calculate_mismatch_factor(
        self,
        spectral_points: List[SpectralPoint]
    ) -> float:
        """
        Calculate spectral mismatch factor

        The mismatch factor accounts for differences between test source
        spectrum and reference AM1.5G spectrum.

        M = (∫ Eref(λ) SR(λ) dλ) / (∫ Etest(λ) SR(λ) dλ)

        For simplicity, assuming test source is close to AM1.5G.
        """
        wavelengths = np.array([p.wavelength for p in spectral_points])
        responses = np.array([p.response for p in spectral_points])

        # Interpolate AM1.5G spectrum to our wavelength points
        am15g_wavelengths = np.array(list(AM15G_SPECTRUM.keys()))
        am15g_irradiances = np.array(list(AM15G_SPECTRUM.values()))

        am15g_interp = interpolate.interp1d(
            am15g_wavelengths,
            am15g_irradiances,
            kind='linear',
            fill_value='extrapolate'
        )

        reference_spectrum = am15g_interp(wavelengths)

        # Calculate weighted integrals
        integral_ref = integrate.trapezoid(reference_spectrum * responses, wavelengths)
        integral_test = integrate.trapezoid(reference_spectrum * responses, wavelengths)

        # For real testing, would compare test source to reference
        # Here we assume perfect match
        mismatch_factor = integral_ref / integral_test if integral_test > 0 else 1.0

        # Typical mismatch factors are 0.95-1.05
        mismatch_factor = np.clip(mismatch_factor, 0.90, 1.10)

        return float(mismatch_factor)


# ==================== Angular Response ====================

class AngularResponseTest:
    """
    Angular response (incidence angle modifier) measurement

    Measures how module output varies with angle of incidence.
    Critical for energy rating calculations.
    """

    def __init__(
        self,
        rotation_stage_address: Optional[str] = None,
        config: Optional[AngularTestConfig] = None
    ):
        self.rotation_stage_address = rotation_stage_address
        self.config = config or AngularTestConfig()
        self._connected = False

    def connect(self) -> bool:
        """Connect to rotation stage"""
        logger.info("Connecting to angular measurement system...")
        # TODO: Implement actual hardware connection
        self._connected = True
        return True

    def disconnect(self):
        """Disconnect from rotation stage"""
        logger.info("Disconnecting angular measurement system...")
        self._connected = False

    def measure_angular_response(self) -> AngularResponseData:
        """
        Measure angular response curve

        Returns:
            AngularResponseData with response vs angle
        """
        if not self._connected:
            raise RuntimeError("Angular measurement system not connected")

        logger.info(
            f"Measuring angular response from {self.config.angle_min}° "
            f"to {self.config.angle_max}°"
        )

        # Generate angle points
        angles = np.arange(
            self.config.angle_min,
            self.config.angle_max + self.config.angle_step,
            self.config.angle_step
        )

        angular_points = []

        for angle in angles:
            # Measure response at this angle
            response = self._measure_at_angle(angle)

            angular_points.append(AngularPoint(
                angle=float(angle),
                relative_response=float(response)
            ))

            logger.debug(f"Angle={angle:.1f}°, Response={response:.4f}")

        # Normalize to normal incidence (0°)
        normal_response = angular_points[0].relative_response
        for point in angular_points:
            point.relative_response /= normal_response

        # Calculate IAM factor (average over typical operating range)
        iam_factor = self._calculate_iam_factor(angular_points)

        logger.info(f"Angular response measured: IAM factor = {iam_factor:.4f}")

        return AngularResponseData(
            points=angular_points,
            iam_factor=iam_factor
        )

    def _measure_at_angle(self, angle: float) -> float:
        """
        Measure response at specific incidence angle

        Args:
            angle: Incidence angle in degrees

        Returns:
            Relative response (0-1)
        """
        # TODO: Replace with actual hardware measurement
        # This simulates typical angular response

        # Fresnel reflection + light trapping effects
        # Cosine law with corrections
        angle_rad = np.radians(angle)

        # Base cosine response
        response = np.cos(angle_rad)

        # Fresnel reflection increases with angle
        # Simplified model
        if angle > 50:
            fresnel_loss = (angle - 50) / 40  # Increases linearly
            response *= (1 - fresnel_loss * 0.2)

        # Add some noise
        response *= (1 + np.random.normal(0, 0.01))
        response = max(0.0, min(1.0, response))

        return response

    def _calculate_iam_factor(
        self,
        angular_points: List[AngularPoint]
    ) -> float:
        """
        Calculate incidence angle modifier (IAM) factor

        IAM represents average optical loss over typical operating angles.
        Weighted average based on typical solar angles throughout the day.

        Returns:
            IAM factor (typically 0.95-0.99)
        """
        # Weight angles by typical solar exposure
        # More weight to lower angles (typical morning/evening)
        angles = np.array([p.angle for p in angular_points])
        responses = np.array([p.relative_response for p in angular_points])

        # Weighting function: more exposure at moderate angles
        weights = np.cos(np.radians(angles)) ** 0.5

        # Weighted average
        iam_factor = np.average(responses, weights=weights)

        return float(iam_factor)


# ==================== Combined Spectral & Angular Test ====================

class SpectralCurve:
    """
    Complete spectral and angular characterization

    Combines spectral response and angular response for comprehensive
    optical characterization.
    """

    def __init__(
        self,
        spectral_test: SpectralResponseTest,
        angular_test: AngularResponseTest
    ):
        self.spectral_test = spectral_test
        self.angular_test = angular_test

    def run_complete_characterization(self) -> Dict[str, Any]:
        """
        Run complete spectral and angular characterization

        Returns:
            Dictionary with both spectral and angular data
        """
        logger.info("Starting complete optical characterization")

        # Connect to systems
        self.spectral_test.connect()
        self.angular_test.connect()

        try:
            # Measure spectral response
            logger.info("Measuring spectral response...")
            spectral_data = self.spectral_test.measure_spectral_response()

            # Measure angular response
            logger.info("Measuring angular response...")
            angular_data = self.angular_test.measure_angular_response()

            # Combine results
            results = {
                "spectral_response": {
                    "peak_wavelength": spectral_data.peak_wavelength,
                    "mismatch_factor": spectral_data.mismatch_factor,
                    "curve_points": len(spectral_data.points),
                    "data": spectral_data
                },
                "angular_response": {
                    "iam_factor": angular_data.iam_factor,
                    "curve_points": len(angular_data.points),
                    "data": angular_data
                },
                "timestamp": datetime.utcnow().isoformat(),
                "standard": "IEC 61853-2"
            }

            logger.info("Optical characterization completed successfully")
            return results

        finally:
            # Disconnect
            self.spectral_test.disconnect()
            self.angular_test.disconnect()

    def calculate_effective_irradiance(
        self,
        spectral_data: SpectralCurveData,
        actual_spectrum: Dict[float, float]
    ) -> float:
        """
        Calculate effective irradiance accounting for spectral mismatch

        Args:
            spectral_data: Module spectral response
            actual_spectrum: Actual spectrum {wavelength: irradiance}

        Returns:
            Effective irradiance (W/m²)
        """
        # This is a simplified calculation
        # Real implementation would integrate over full spectrum

        total_effective = 0.0
        wavelengths = [p.wavelength for p in spectral_data.points]

        for wavelength in actual_spectrum:
            if wavelength in wavelengths:
                idx = wavelengths.index(wavelength)
                response = spectral_data.points[idx].response
                irradiance = actual_spectrum[wavelength]
                total_effective += response * irradiance

        return total_effective

    def export_spectral_data(
        self,
        spectral_data: SpectralCurveData,
        filename: str
    ):
        """Export spectral response data to CSV"""
        import csv

        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Wavelength (nm)', 'Spectral Response'])

            for point in spectral_data.points:
                writer.writerow([point.wavelength, point.response])

        logger.info(f"Spectral data exported to {filename}")

    def export_angular_data(
        self,
        angular_data: AngularResponseData,
        filename: str
    ):
        """Export angular response data to CSV"""
        import csv

        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Angle (degrees)', 'Relative Response'])

            for point in angular_data.points:
                writer.writerow([point.angle, point.relative_response])

        logger.info(f"Angular data exported to {filename}")
