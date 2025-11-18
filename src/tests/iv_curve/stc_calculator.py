"""
STC Translation Calculator per IEC 60904-1:2020
Standard Test Conditions translation procedures with uncertainty analysis

Standard Test Conditions (STC):
- Temperature: 25°C (cell temperature)
- Irradiance: 1000 W/m²
- Spectrum: AM1.5G (Air Mass 1.5 Global)

This module provides:
- IEC 60904-1 compliant translation procedures
- Temperature coefficient application (α, β, γ)
- Spectral mismatch correction
- Uncertainty budget calculation per ISO/IEC 17025
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import warnings


@dataclass
class STCConditions:
    """Standard Test Conditions definition."""
    temperature: float = 25.0  # °C
    irradiance: float = 1000.0  # W/m²
    spectrum: str = "AM1.5G"
    air_mass: float = 1.5


@dataclass
class TemperatureCoefficients:
    """
    Temperature coefficients for PV module parameters.

    Can be specified as absolute or relative (percentage) values.
    """
    alpha_isc: float = 0.0  # Temperature coefficient of Isc (A/°C or %/°C)
    beta_voc: float = 0.0  # Temperature coefficient of Voc (V/°C or %/°C)
    gamma_pmax: float = 0.0  # Temperature coefficient of Pmax (W/°C or %/°C)
    alpha_imp: Optional[float] = None  # Temperature coefficient of Imp
    beta_vmp: Optional[float] = None  # Temperature coefficient of Vmp

    # Flag indicating if coefficients are relative (percentage)
    is_relative: bool = False

    def to_absolute(self, isc: float, voc: float, pmax: float,
                   imp: Optional[float] = None, vmp: Optional[float] = None):
        """
        Convert relative coefficients to absolute values.

        Args:
            isc, voc, pmax: Reference values at STC
            imp, vmp: Optional reference values

        Returns:
            TemperatureCoefficients with absolute values
        """
        if not self.is_relative:
            return self

        return TemperatureCoefficients(
            alpha_isc=self.alpha_isc * isc / 100,
            beta_voc=self.beta_voc * voc / 100,
            gamma_pmax=self.gamma_pmax * pmax / 100,
            alpha_imp=self.alpha_imp * imp / 100 if self.alpha_imp and imp else None,
            beta_vmp=self.beta_vmp * vmp / 100 if self.beta_vmp and vmp else None,
            is_relative=False
        )


@dataclass
class UncertaintyComponents:
    """Uncertainty budget components per ISO/IEC 17025."""
    # Type A uncertainties (statistical)
    measurement_repeatability: float = 0.0
    measurement_reproducibility: float = 0.0

    # Type B uncertainties (systematic)
    voltage_measurement: float = 0.0
    current_measurement: float = 0.0
    temperature_measurement: float = 0.0
    irradiance_measurement: float = 0.0
    temperature_correction: float = 0.0
    irradiance_correction: float = 0.0
    spectral_mismatch: float = 0.0
    module_area: float = 0.0
    calibration: float = 0.0

    def combined_uncertainty(self, coverage_factor: float = 2.0) -> float:
        """
        Calculate combined standard uncertainty per GUM.

        Args:
            coverage_factor: k-factor for expanded uncertainty (k=2 for ~95% confidence)

        Returns:
            Expanded uncertainty
        """
        # Combine all uncertainty components (RSS - Root Sum Square)
        components = [
            self.measurement_repeatability,
            self.measurement_reproducibility,
            self.voltage_measurement,
            self.current_measurement,
            self.temperature_measurement,
            self.irradiance_measurement,
            self.temperature_correction,
            self.irradiance_correction,
            self.spectral_mismatch,
            self.module_area,
            self.calibration
        ]

        combined = np.sqrt(np.sum(np.array(components) ** 2))
        return combined * coverage_factor


class STCCalculator:
    """
    Translate PV measurements to Standard Test Conditions per IEC 60904-1:2020.
    """

    def __init__(self, stc: Optional[STCConditions] = None):
        """
        Initialize STC calculator.

        Args:
            stc: Standard test conditions (default: 25°C, 1000W/m², AM1.5G)
        """
        self.stc = stc or STCConditions()

    def translate_to_stc(
        self,
        measured_params: Dict[str, float],
        temp_coefficients: TemperatureCoefficients,
        measured_conditions: Dict[str, float],
        spectral_correction: float = 1.0,
        method: str = 'iec60904'
    ) -> Dict[str, float]:
        """
        Translate measured parameters to STC per IEC 60904-1.

        Args:
            measured_params: Measured I-V parameters (Isc, Voc, Pmax, Imp, Vmp, FF)
            temp_coefficients: Temperature coefficients
            measured_conditions: Temperature and irradiance during measurement
            spectral_correction: Spectral mismatch correction factor
            method: Translation method ('iec60904', 'linear', or 'advanced')

        Returns:
            Parameters translated to STC
        """
        T_meas = measured_conditions['temperature']
        G_meas = measured_conditions['irradiance']

        if method == 'iec60904':
            return self._translate_iec60904(
                measured_params, temp_coefficients,
                T_meas, G_meas, spectral_correction
            )
        elif method == 'linear':
            return self._translate_linear(
                measured_params, temp_coefficients,
                T_meas, G_meas, spectral_correction
            )
        elif method == 'advanced':
            return self._translate_advanced(
                measured_params, temp_coefficients,
                T_meas, G_meas, spectral_correction
            )
        else:
            raise ValueError(f"Unknown translation method: {method}")

    def _translate_iec60904(
        self,
        params: Dict[str, float],
        temp_coeff: TemperatureCoefficients,
        T_meas: float,
        G_meas: float,
        M: float
    ) -> Dict[str, float]:
        """
        IEC 60904-1 standard translation procedure.

        Procedure:
        1. Correct for irradiance to 1000 W/m²
        2. Correct for temperature to 25°C
        3. Apply spectral mismatch correction

        Args:
            params: Measured parameters
            temp_coeff: Temperature coefficients
            T_meas: Measured temperature (°C)
            G_meas: Measured irradiance (W/m²)
            M: Spectral mismatch correction factor

        Returns:
            Translated parameters at STC
        """
        # Convert to absolute coefficients if needed
        if temp_coeff.is_relative:
            temp_coeff = temp_coeff.to_absolute(
                params['Isc'], params['Voc'], params['Pmax'],
                params.get('Imp'), params.get('Vmp')
            )

        # Temperature differences
        delta_T = self.stc.temperature - T_meas

        # Irradiance ratio
        G_ratio = self.stc.irradiance / G_meas

        # Thermal voltage at measurement temperature (V)
        Vt_meas = self._thermal_voltage(T_meas)
        Vt_stc = self._thermal_voltage(self.stc.temperature)

        # Step 1: Irradiance correction
        # Current scales linearly with irradiance
        Isc_G = params['Isc'] * G_ratio * M

        # Voltage has logarithmic dependence
        delta_V_irr = Vt_meas * np.log(G_ratio)
        Voc_G = params['Voc'] + delta_V_irr

        # Step 2: Temperature correction
        # Apply temperature coefficients
        Isc_stc = Isc_G + temp_coeff.alpha_isc * delta_T
        Voc_stc = Voc_G + temp_coeff.beta_voc * delta_T

        # For MPP parameters, use coefficients if available, else estimate
        if temp_coeff.alpha_imp is not None:
            Imp_G = params['Imp'] * G_ratio * M
            Imp_stc = Imp_G + temp_coeff.alpha_imp * delta_T
        else:
            # Estimate: Imp changes similar to Isc
            Imp_stc = params['Imp'] * (Isc_stc / params['Isc']) if params['Isc'] > 0 else 0

        if temp_coeff.beta_vmp is not None:
            Vmp_G = params['Vmp'] + Vt_meas * np.log(G_ratio) * 0.85
            Vmp_stc = Vmp_G + temp_coeff.beta_vmp * delta_T
        else:
            # Estimate: Vmp changes similar to Voc but less sensitive
            Vmp_stc = params['Vmp'] * (Voc_stc / params['Voc']) if params['Voc'] > 0 else 0

        # Pmax from temperature coefficient or from Vmp*Imp
        if temp_coeff.gamma_pmax != 0:
            Pmax_G = params['Pmax'] * G_ratio * M
            Pmax_stc = Pmax_G + temp_coeff.gamma_pmax * delta_T
        else:
            Pmax_stc = Vmp_stc * Imp_stc

        # Recalculate fill factor
        FF_stc = Pmax_stc / (Voc_stc * Isc_stc) if (Voc_stc * Isc_stc) > 0 else 0

        return {
            'Isc_stc': float(Isc_stc),
            'Voc_stc': float(Voc_stc),
            'Imp_stc': float(Imp_stc),
            'Vmp_stc': float(Vmp_stc),
            'Pmax_stc': float(Pmax_stc),
            'FF_stc': float(FF_stc),
            'temperature': self.stc.temperature,
            'irradiance': self.stc.irradiance,
            'method': 'IEC 60904-1'
        }

    def _translate_linear(
        self,
        params: Dict[str, float],
        temp_coeff: TemperatureCoefficients,
        T_meas: float,
        G_meas: float,
        M: float
    ) -> Dict[str, float]:
        """
        Simplified linear translation (faster, less accurate).

        Args:
            params: Measured parameters
            temp_coeff: Temperature coefficients
            T_meas: Measured temperature (°C)
            G_meas: Measured irradiance (W/m²)
            M: Spectral mismatch correction factor

        Returns:
            Translated parameters at STC
        """
        if temp_coeff.is_relative:
            temp_coeff = temp_coeff.to_absolute(
                params['Isc'], params['Voc'], params['Pmax']
            )

        delta_T = self.stc.temperature - T_meas
        G_ratio = self.stc.irradiance / G_meas

        # Linear corrections
        Isc_stc = params['Isc'] * G_ratio * M + temp_coeff.alpha_isc * delta_T
        Voc_stc = params['Voc'] + temp_coeff.beta_voc * delta_T
        Pmax_stc = params['Pmax'] * G_ratio * M + temp_coeff.gamma_pmax * delta_T

        # Estimate Vmp and Imp from power and typical ratios
        Vmp_stc = Voc_stc * 0.8  # Typical Vmp/Voc ratio
        Imp_stc = Pmax_stc / Vmp_stc if Vmp_stc > 0 else 0

        FF_stc = Pmax_stc / (Voc_stc * Isc_stc) if (Voc_stc * Isc_stc) > 0 else 0

        return {
            'Isc_stc': float(Isc_stc),
            'Voc_stc': float(Voc_stc),
            'Imp_stc': float(Imp_stc),
            'Vmp_stc': float(Vmp_stc),
            'Pmax_stc': float(Pmax_stc),
            'FF_stc': float(FF_stc),
            'temperature': self.stc.temperature,
            'irradiance': self.stc.irradiance,
            'method': 'Linear'
        }

    def _translate_advanced(
        self,
        params: Dict[str, float],
        temp_coeff: TemperatureCoefficients,
        T_meas: float,
        G_meas: float,
        M: float
    ) -> Dict[str, float]:
        """
        Advanced translation with non-linear corrections.

        Includes:
        - Non-linear temperature effects
        - Series resistance temperature dependence
        - Fill factor temperature correction

        Args:
            params: Measured parameters
            temp_coeff: Temperature coefficients
            T_meas: Measured temperature (°C)
            G_meas: Measured irradiance (W/m²)
            M: Spectral mismatch correction factor

        Returns:
            Translated parameters at STC
        """
        # Start with IEC procedure
        stc_params = self._translate_iec60904(params, temp_coeff, T_meas, G_meas, M)

        # Apply non-linear corrections
        delta_T = self.stc.temperature - T_meas

        # Temperature dependence of FF (typically decreases with T)
        # ΔFF ≈ -0.001 per °C (approximate)
        delta_FF = -0.001 * delta_T
        FF_corrected = stc_params['FF_stc'] + delta_FF
        FF_corrected = max(0, min(1, FF_corrected))  # Clamp to [0, 1]

        # Recalculate Pmax with corrected FF
        Pmax_corrected = FF_corrected * stc_params['Voc_stc'] * stc_params['Isc_stc']

        # Adjust Vmp and Imp to maintain corrected Pmax
        power_ratio = Pmax_corrected / stc_params['Pmax_stc'] if stc_params['Pmax_stc'] > 0 else 1
        Vmp_corrected = stc_params['Vmp_stc'] * np.sqrt(power_ratio)
        Imp_corrected = Pmax_corrected / Vmp_corrected if Vmp_corrected > 0 else 0

        stc_params.update({
            'Vmp_stc': float(Vmp_corrected),
            'Imp_stc': float(Imp_corrected),
            'Pmax_stc': float(Pmax_corrected),
            'FF_stc': float(FF_corrected),
            'method': 'Advanced'
        })

        return stc_params

    def calculate_spectral_mismatch(
        self,
        module_spectral_response: Optional[np.ndarray] = None,
        reference_cell_response: Optional[np.ndarray] = None,
        test_spectrum: Optional[np.ndarray] = None,
        reference_spectrum: Optional[np.ndarray] = None
    ) -> float:
        """
        Calculate spectral mismatch correction factor per IEC 60904-7.

        M = (∫ E_ref(λ) × SR_test(λ) dλ / ∫ E_test(λ) × SR_test(λ) dλ) ×
            (∫ E_test(λ) × SR_ref(λ) dλ / ∫ E_ref(λ) × SR_ref(λ) dλ)

        Args:
            module_spectral_response: Test device spectral response
            reference_cell_response: Reference cell spectral response
            test_spectrum: Test light source spectrum
            reference_spectrum: Reference spectrum (AM1.5G)

        Returns:
            Spectral mismatch correction factor M
        """
        # If no data provided, return ideal case
        if any(x is None for x in [module_spectral_response, reference_cell_response,
                                   test_spectrum, reference_spectrum]):
            warnings.warn("Spectral data not provided, assuming M=1.0")
            return 1.0

        # Calculate integrals
        numerator_1 = np.trapz(reference_spectrum * module_spectral_response)
        denominator_1 = np.trapz(test_spectrum * module_spectral_response)

        numerator_2 = np.trapz(test_spectrum * reference_cell_response)
        denominator_2 = np.trapz(reference_spectrum * reference_cell_response)

        if denominator_1 == 0 or denominator_2 == 0:
            warnings.warn("Division by zero in spectral mismatch calculation")
            return 1.0

        M = (numerator_1 / denominator_1) * (numerator_2 / denominator_2)

        return float(M)

    def calculate_uncertainty(
        self,
        components: UncertaintyComponents,
        parameter: str = 'Pmax',
        sensitivity_coefficients: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Calculate measurement uncertainty budget per ISO/IEC 17025.

        Args:
            components: Uncertainty components
            parameter: Parameter being analyzed ('Pmax', 'Isc', 'Voc', etc.)
            sensitivity_coefficients: Optional sensitivity coefficients for error propagation

        Returns:
            Uncertainty analysis results
        """
        # Default sensitivity coefficients (can be refined)
        if sensitivity_coefficients is None:
            sensitivity_coefficients = {
                'voltage_measurement': 1.0,
                'current_measurement': 1.0,
                'temperature_measurement': 1.0,
                'irradiance_measurement': 1.0,
                'temperature_correction': 1.0,
                'irradiance_correction': 1.0,
                'spectral_mismatch': 1.0
            }

        # Calculate individual contributions
        contributions = {}
        total_variance = 0

        for attr_name in dir(components):
            if not attr_name.startswith('_') and attr_name != 'combined_uncertainty':
                uncertainty = getattr(components, attr_name)
                sensitivity = sensitivity_coefficients.get(attr_name, 1.0)
                contribution = (uncertainty * sensitivity) ** 2
                contributions[attr_name] = np.sqrt(contribution)
                total_variance += contribution

        # Combined standard uncertainty
        u_combined = np.sqrt(total_variance)

        # Expanded uncertainty (k=2, approximately 95% confidence)
        U_expanded = 2.0 * u_combined

        return {
            'parameter': parameter,
            'combined_standard_uncertainty': float(u_combined),
            'expanded_uncertainty_k2': float(U_expanded),
            'relative_uncertainty_percent': float(U_expanded * 100) if U_expanded > 0 else 0,
            'contributions': {k: float(v) for k, v in contributions.items()},
            'coverage_factor': 2.0,
            'confidence_level': 0.95
        }

    @staticmethod
    def _thermal_voltage(temperature_celsius: float) -> float:
        """
        Calculate thermal voltage Vt = kT/q.

        Args:
            temperature_celsius: Temperature in °C

        Returns:
            Thermal voltage in V
        """
        k_boltzmann = 1.380649e-23  # J/K
        q_electron = 1.602176634e-19  # C
        T_kelvin = temperature_celsius + 273.15

        return k_boltzmann * T_kelvin / q_electron

    def validate_translation(
        self,
        measured_params: Dict[str, float],
        translated_params: Dict[str, float],
        tolerance_percent: float = 10.0
    ) -> Tuple[bool, List[str]]:
        """
        Validate translation results for reasonableness.

        Args:
            measured_params: Original measured parameters
            translated_params: Translated STC parameters
            tolerance_percent: Maximum acceptable change (%)

        Returns:
            Tuple of (is_valid, list of warnings)
        """
        warnings_list = []

        # Check for excessive changes
        for param in ['Isc', 'Voc', 'Pmax']:
            if param in measured_params:
                meas_key = param
                stc_key = f"{param}_stc"

                if stc_key in translated_params:
                    change = abs(translated_params[stc_key] - measured_params[meas_key])
                    rel_change = (change / measured_params[meas_key] * 100
                                 if measured_params[meas_key] > 0 else 0)

                    if rel_change > tolerance_percent:
                        warnings_list.append(
                            f"{param} changed by {rel_change:.1f}% (>{tolerance_percent}%)"
                        )

        # Check FF is in valid range
        if 'FF_stc' in translated_params:
            ff = translated_params['FF_stc']
            if ff < 0.5 or ff > 0.9:
                warnings_list.append(f"Fill factor {ff:.3f} outside typical range [0.5-0.9]")

        # Check Pmax consistency
        if all(k in translated_params for k in ['Pmax_stc', 'Vmp_stc', 'Imp_stc']):
            calc_pmax = translated_params['Vmp_stc'] * translated_params['Imp_stc']
            pmax_diff = abs(calc_pmax - translated_params['Pmax_stc'])
            if pmax_diff > 0.01 * translated_params['Pmax_stc']:
                warnings_list.append(
                    f"Pmax inconsistency: {translated_params['Pmax_stc']:.2f} W "
                    f"vs calculated {calc_pmax:.2f} W"
                )

        return len(warnings_list) == 0, warnings_list


def estimate_temperature_coefficients(
    params_cold: Dict[str, float],
    params_hot: Dict[str, float],
    temp_cold: float,
    temp_hot: float
) -> TemperatureCoefficients:
    """
    Estimate temperature coefficients from two measurements at different temperatures.

    Args:
        params_cold: Parameters at lower temperature
        params_hot: Parameters at higher temperature
        temp_cold: Lower temperature (°C)
        temp_hot: Higher temperature (°C)

    Returns:
        Estimated temperature coefficients
    """
    if temp_hot <= temp_cold:
        raise ValueError("temp_hot must be greater than temp_cold")

    delta_T = temp_hot - temp_cold

    alpha_isc = (params_hot['Isc'] - params_cold['Isc']) / delta_T
    beta_voc = (params_hot['Voc'] - params_cold['Voc']) / delta_T
    gamma_pmax = (params_hot['Pmax'] - params_cold['Pmax']) / delta_T

    # Optional MPP coefficients
    alpha_imp = ((params_hot.get('Imp', 0) - params_cold.get('Imp', 0)) / delta_T
                if 'Imp' in params_hot and 'Imp' in params_cold else None)
    beta_vmp = ((params_hot.get('Vmp', 0) - params_cold.get('Vmp', 0)) / delta_T
               if 'Vmp' in params_hot and 'Vmp' in params_cold else None)

    return TemperatureCoefficients(
        alpha_isc=alpha_isc,
        beta_voc=beta_voc,
        gamma_pmax=gamma_pmax,
        alpha_imp=alpha_imp,
        beta_vmp=beta_vmp,
        is_relative=False
    )


if __name__ == "__main__":
    print("STC Calculator - IEC 60904-1:2020")
    print("=" * 50)

    # Example usage
    calculator = STCCalculator()

    # Measured parameters (example at 45°C, 800 W/m²)
    measured = {
        'Isc': 8.2,
        'Voc': 36.5,
        'Imp': 7.5,
        'Vmp': 29.2,
        'Pmax': 219.0,
        'FF': 0.731
    }

    # Temperature coefficients (typical crystalline silicon)
    temp_coeff = TemperatureCoefficients(
        alpha_isc=0.05,  # %/°C
        beta_voc=-0.35,  # %/°C
        gamma_pmax=-0.45,  # %/°C
        is_relative=True
    )

    # Measurement conditions
    conditions = {
        'temperature': 45.0,
        'irradiance': 800.0
    }

    # Translate to STC
    stc_params = calculator.translate_to_stc(
        measured,
        temp_coeff,
        conditions,
        spectral_correction=1.0,
        method='iec60904'
    )

    print("\nMeasured Parameters (45°C, 800 W/m²):")
    for key, value in measured.items():
        print(f"  {key}: {value:.3f}")

    print("\nTranslated to STC (25°C, 1000 W/m²):")
    for key, value in stc_params.items():
        if isinstance(value, (int, float)):
            print(f"  {key}: {value:.3f}")
        else:
            print(f"  {key}: {value}")

    # Validate translation
    is_valid, warnings_list = calculator.validate_translation(measured, stc_params)
    print(f"\nValidation: {'PASS' if is_valid else 'WARNINGS'}")
    for warning in warnings_list:
        print(f"  ⚠ {warning}")

    # Calculate uncertainty
    uncertainty_components = UncertaintyComponents(
        measurement_repeatability=0.5,
        voltage_measurement=0.3,
        current_measurement=0.5,
        temperature_measurement=0.2,
        irradiance_measurement=1.0,
        temperature_correction=0.5,
        irradiance_correction=0.8,
        spectral_mismatch=0.5
    )

    uncertainty = calculator.calculate_uncertainty(uncertainty_components, 'Pmax')
    print("\nUncertainty Budget (Pmax):")
    print(f"  Combined uncertainty: ±{uncertainty['combined_standard_uncertainty']:.2f}%")
    print(f"  Expanded uncertainty (k=2): ±{uncertainty['expanded_uncertainty_k2']:.2f}%")

    print("\n" + "=" * 50)
    print("Module ready for production use")
