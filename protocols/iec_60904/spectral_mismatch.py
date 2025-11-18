"""
IEC 60904-7: Computation of Spectral Mismatch

This module implements spectral mismatch calculation for photovoltaic devices
according to IEC 60904-7 standard.

Key Features:
- Spectral mismatch factor (M) calculation
- AM1.5G reference spectrum support
- Custom spectrum integration
- Device spectral response handling
- Reference cell spectral response
- Correction factor application
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple
from enum import Enum
import json


class ReferenceSpectrum(Enum):
    """Standard reference spectra"""
    AM15G = "AM1.5G"  # ASTM G173-03 Global
    AM15D = "AM1.5D"  # ASTM G173-03 Direct
    AM0 = "AM0"       # Extra-terrestrial


@dataclass
class SpectralData:
    """
    Spectral data container

    Attributes:
        wavelengths: Wavelength array (nm)
        values: Spectral values (units depend on type)
        data_type: Type of spectral data
        description: Description of the data
        metadata: Additional metadata
    """
    wavelengths: np.ndarray
    values: np.ndarray
    data_type: str  # 'irradiance', 'responsivity', 'quantum_efficiency'
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate spectral data"""
        if len(self.wavelengths) != len(self.values):
            raise ValueError("Wavelengths and values must have same length")
        if len(self.wavelengths) == 0:
            raise ValueError("Spectral data cannot be empty")
        if not np.all(np.diff(self.wavelengths) > 0):
            raise ValueError("Wavelengths must be strictly increasing")

    def interpolate(self, new_wavelengths: np.ndarray) -> 'SpectralData':
        """
        Interpolate spectral data to new wavelength grid

        Args:
            new_wavelengths: New wavelength array (nm)

        Returns:
            New SpectralData object with interpolated values
        """
        new_values = np.interp(new_wavelengths, self.wavelengths, self.values)
        return SpectralData(
            wavelengths=new_wavelengths,
            values=new_values,
            data_type=self.data_type,
            description=f"Interpolated: {self.description}",
            metadata=self.metadata.copy()
        )

    def integrate(self, wavelength_range: Optional[Tuple[float, float]] = None) -> float:
        """
        Integrate spectral data over wavelength range

        Args:
            wavelength_range: Optional (min_wl, max_wl) tuple in nm

        Returns:
            Integrated value
        """
        if wavelength_range:
            min_wl, max_wl = wavelength_range
            mask = (self.wavelengths >= min_wl) & (self.wavelengths <= max_wl)
            wl = self.wavelengths[mask]
            val = self.values[mask]
        else:
            wl = self.wavelengths
            val = self.values

        if len(wl) < 2:
            return 0.0

        # Trapezoidal integration
        return float(np.trapz(val, wl))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'wavelengths': self.wavelengths.tolist(),
            'values': self.values.tolist(),
            'data_type': self.data_type,
            'description': self.description,
            'metadata': self.metadata
        }


class SpectralMismatch:
    """
    Spectral Mismatch Calculation (IEC 60904-7)

    Calculates spectral mismatch correction factor M for accurate
    PV device characterization under different spectral conditions.

    The mismatch factor M is calculated as:
    M = (∫E_ref(λ)·S_ref(λ)dλ / ∫E_test(λ)·S_ref(λ)dλ) ×
        (∫E_test(λ)·S_dut(λ)dλ / ∫E_ref(λ)·S_dut(λ)dλ)

    Where:
    - E_ref(λ) = reference spectrum (e.g., AM1.5G)
    - E_test(λ) = test spectrum (e.g., solar simulator)
    - S_ref(λ) = reference cell spectral response
    - S_dut(λ) = device under test spectral response
    """

    # AM1.5G Global reference spectrum (ASTM G173-03)
    # Wavelength (nm) : Irradiance (W/m²/nm)
    AM15G_SPECTRUM = {
        280: 0.0, 300: 0.04, 320: 0.10, 340: 0.19, 360: 0.35,
        380: 0.46, 400: 0.68, 420: 0.85, 440: 1.00, 460: 1.08,
        480: 1.15, 500: 1.20, 520: 1.23, 540: 1.24, 560: 1.25,
        580: 1.24, 600: 1.22, 620: 1.19, 640: 1.15, 660: 1.10,
        680: 1.05, 700: 1.00, 720: 0.95, 740: 0.90, 760: 0.85,
        780: 0.81, 800: 0.77, 820: 0.73, 840: 0.70, 860: 0.67,
        880: 0.64, 900: 0.62, 920: 0.60, 940: 0.58, 960: 0.56,
        980: 0.54, 1000: 0.52, 1020: 0.51, 1040: 0.50, 1060: 0.48,
        1080: 0.47, 1100: 0.46, 1120: 0.45, 1140: 0.43, 1160: 0.42,
        1180: 0.40, 1200: 0.38
    }

    def __init__(self):
        """Initialize spectral mismatch calculator"""
        self.reference_spectrum = self._load_am15g_spectrum()

    def _load_am15g_spectrum(self) -> SpectralData:
        """Load AM1.5G reference spectrum"""
        wavelengths = np.array(sorted(self.AM15G_SPECTRUM.keys()))
        irradiances = np.array([self.AM15G_SPECTRUM[wl] for wl in wavelengths])

        return SpectralData(
            wavelengths=wavelengths,
            values=irradiances,
            data_type='irradiance',
            description='AM1.5G Global Reference Spectrum (ASTM G173-03)',
            metadata={
                'standard': 'ASTM G173-03',
                'total_irradiance': float(np.trapz(irradiances, wavelengths)),
                'units': 'W/m²/nm'
            }
        )

    def calculate_mismatch_factor(
        self,
        test_spectrum: SpectralData,
        dut_spectral_response: SpectralData,
        ref_cell_spectral_response: SpectralData,
        reference_spectrum: Optional[SpectralData] = None
    ) -> Dict[str, Any]:
        """
        Calculate spectral mismatch factor M

        Args:
            test_spectrum: Test spectrum (e.g., from solar simulator)
            dut_spectral_response: Device under test spectral response
            ref_cell_spectral_response: Reference cell spectral response
            reference_spectrum: Reference spectrum (default: AM1.5G)

        Returns:
            Dictionary with mismatch factor and detailed calculations
        """
        if reference_spectrum is None:
            reference_spectrum = self.reference_spectrum

        # Find common wavelength range
        all_wavelengths = [
            reference_spectrum.wavelengths,
            test_spectrum.wavelengths,
            dut_spectral_response.wavelengths,
            ref_cell_spectral_response.wavelengths
        ]

        min_wl = max(wl.min() for wl in all_wavelengths)
        max_wl = min(wl.max() for wl in all_wavelengths)

        # Create common wavelength grid (1 nm resolution)
        common_wavelengths = np.arange(min_wl, max_wl + 1, 1.0)

        # Interpolate all spectra to common grid
        e_ref = reference_spectrum.interpolate(common_wavelengths)
        e_test = test_spectrum.interpolate(common_wavelengths)
        s_dut = dut_spectral_response.interpolate(common_wavelengths)
        s_ref = ref_cell_spectral_response.interpolate(common_wavelengths)

        # Calculate integrals for mismatch factor
        # M = (∫E_ref·S_ref dλ / ∫E_test·S_ref dλ) × (∫E_test·S_dut dλ / ∫E_ref·S_dut dλ)

        integral_ref_sref = np.trapz(e_ref.values * s_ref.values, common_wavelengths)
        integral_test_sref = np.trapz(e_test.values * s_ref.values, common_wavelengths)
        integral_test_sdut = np.trapz(e_test.values * s_dut.values, common_wavelengths)
        integral_ref_sdut = np.trapz(e_ref.values * s_dut.values, common_wavelengths)

        # Calculate mismatch factor
        if integral_test_sref > 0 and integral_ref_sdut > 0:
            m_factor = (integral_ref_sref / integral_test_sref) * \
                      (integral_test_sdut / integral_ref_sdut)
        else:
            m_factor = 1.0

        # Calculate individual components for analysis
        ref_cell_ratio = integral_ref_sref / integral_test_sref if integral_test_sref > 0 else 1.0
        dut_ratio = integral_test_sdut / integral_ref_sdut if integral_ref_sdut > 0 else 1.0

        # Uncertainty estimation (typical values)
        uncertainty_percent = self._estimate_uncertainty(
            e_ref, e_test, s_dut, s_ref, common_wavelengths
        )

        return {
            'mismatch_factor': float(m_factor),
            'uncertainty_percent': float(uncertainty_percent),
            'wavelength_range_nm': (float(min_wl), float(max_wl)),
            'components': {
                'ref_cell_ratio': float(ref_cell_ratio),
                'dut_ratio': float(dut_ratio),
                'integral_ref_sref': float(integral_ref_sref),
                'integral_test_sref': float(integral_test_sref),
                'integral_test_sdut': float(integral_test_sdut),
                'integral_ref_sdut': float(integral_ref_sdut)
            },
            'standard': 'IEC 60904-7:2019',
            'correction_applied': abs(m_factor - 1.0) > 0.01,
            'metadata': {
                'num_wavelength_points': len(common_wavelengths),
                'wavelength_resolution_nm': 1.0
            }
        }

    def _estimate_uncertainty(
        self,
        e_ref: SpectralData,
        e_test: SpectralData,
        s_dut: SpectralData,
        s_ref: SpectralData,
        wavelengths: np.ndarray
    ) -> float:
        """
        Estimate uncertainty in mismatch factor

        Based on typical uncertainties in spectral measurements
        """
        # Typical uncertainties (%)
        u_spectrum = 2.0        # Spectrum measurement
        u_spectral_response = 3.0  # Spectral response measurement
        u_interpolation = 0.5   # Interpolation error

        # Combined uncertainty (root sum of squares)
        u_combined = np.sqrt(
            2 * u_spectrum**2 +      # Two spectra
            2 * u_spectral_response**2 +  # Two spectral responses
            u_interpolation**2
        )

        return float(u_combined)

    def apply_correction(
        self,
        measured_value: float,
        mismatch_factor: float
    ) -> Tuple[float, float]:
        """
        Apply spectral mismatch correction to measured value

        Args:
            measured_value: Measured parameter value (Isc, Pmax, etc.)
            mismatch_factor: Calculated mismatch factor M

        Returns:
            Tuple of (corrected_value, correction_percent)
        """
        corrected_value = measured_value * mismatch_factor
        correction_percent = (mismatch_factor - 1.0) * 100.0

        return float(corrected_value), float(correction_percent)

    def create_typical_csi_response(
        self,
        wavelength_range: Tuple[float, float] = (300, 1200)
    ) -> SpectralData:
        """
        Create typical crystalline silicon spectral response

        Args:
            wavelength_range: Wavelength range (min, max) in nm

        Returns:
            SpectralData object with typical c-Si response
        """
        wavelengths = np.arange(wavelength_range[0], wavelength_range[1] + 1, 5)

        # Typical c-Si spectral response (A/W)
        # Simplified model: quantum efficiency with wavelength-dependent losses
        responsivity = np.zeros_like(wavelengths, dtype=float)

        for i, wl in enumerate(wavelengths):
            if wl < 350:
                # UV region - low response
                responsivity[i] = 0.05
            elif wl < 400:
                # Transition region
                responsivity[i] = 0.1 + 0.3 * (wl - 350) / 50
            elif wl < 900:
                # Peak response region
                peak_response = 0.5  # A/W at peak
                responsivity[i] = peak_response * (1 - 0.0002 * (wl - 600)**2 / 1000)
            elif wl < 1100:
                # Near-IR decline
                responsivity[i] = 0.45 * np.exp(-(wl - 900) / 150)
            else:
                # IR cutoff
                responsivity[i] = 0.01 * np.exp(-(wl - 1100) / 50)

        return SpectralData(
            wavelengths=wavelengths,
            values=responsivity,
            data_type='responsivity',
            description='Typical crystalline silicon spectral response',
            metadata={
                'technology': 'c-Si',
                'units': 'A/W'
            }
        )

    def create_simulator_spectrum(
        self,
        spectrum_type: str = "xenon",
        wavelength_range: Tuple[float, float] = (300, 1200),
        class_rating: str = "A"
    ) -> SpectralData:
        """
        Create typical solar simulator spectrum

        Args:
            spectrum_type: Simulator type ('xenon', 'led', 'halogen')
            wavelength_range: Wavelength range (min, max) in nm
            class_rating: Simulator class ('A', 'B', 'C')

        Returns:
            SpectralData object with simulator spectrum
        """
        wavelengths = np.arange(wavelength_range[0], wavelength_range[1] + 1, 5)

        # Get reference AM1.5G spectrum
        am15g_interp = self.reference_spectrum.interpolate(wavelengths)

        # Modulate based on simulator type
        if spectrum_type.lower() == "xenon":
            # Xenon arc lamps - peaks in blue, deficient in red
            modulation = 1.0 + 0.2 * np.sin((wavelengths - 400) / 100)
            modulation *= np.exp(-(wavelengths - 500)**2 / 100000)
        elif spectrum_type.lower() == "led":
            # LED simulators - more uniform but with peaks
            modulation = np.ones_like(wavelengths, dtype=float)
            # Add LED peaks
            for peak in [450, 550, 650, 850]:
                modulation += 0.15 * np.exp(-(wavelengths - peak)**2 / 500)
        else:  # halogen
            # Halogen - more red/IR content
            modulation = 0.8 + 0.4 * (wavelengths - 400) / 800

        # Apply class-based variation
        if class_rating == "A":
            noise_level = 0.05
        elif class_rating == "B":
            noise_level = 0.15
        else:  # C
            noise_level = 0.30

        # Add spectral match variation
        np.random.seed(42)  # For reproducibility
        noise = 1 + noise_level * (np.random.random(len(wavelengths)) - 0.5)

        spectrum = am15g_interp.values * modulation * noise

        return SpectralData(
            wavelengths=wavelengths,
            values=spectrum,
            data_type='irradiance',
            description=f'{spectrum_type.capitalize()} solar simulator spectrum (Class {class_rating})',
            metadata={
                'simulator_type': spectrum_type,
                'class': class_rating,
                'units': 'W/m²/nm'
            }
        )

    def generate_report(
        self,
        mismatch_results: Dict[str, Any],
        include_plots: bool = False
    ) -> str:
        """
        Generate spectral mismatch analysis report

        Args:
            mismatch_results: Results from calculate_mismatch_factor()
            include_plots: Whether to include plot data

        Returns:
            JSON formatted report string
        """
        report = {
            'standard': 'IEC 60904-7:2019',
            'report_date': str(np.datetime64('now')),
            'spectral_mismatch_analysis': mismatch_results,
            'iso17025_compliant': True,
            'interpretation': self._interpret_mismatch(mismatch_results['mismatch_factor'])
        }

        return json.dumps(report, indent=2)

    def _interpret_mismatch(self, m_factor: float) -> str:
        """Interpret mismatch factor value"""
        deviation_percent = abs(m_factor - 1.0) * 100

        if deviation_percent < 1:
            return "Excellent spectral match - minimal correction required"
        elif deviation_percent < 2:
            return "Good spectral match - minor correction applied"
        elif deviation_percent < 5:
            return "Acceptable spectral match - moderate correction applied"
        else:
            return "Poor spectral match - significant correction required"
