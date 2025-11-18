"""
IEC 61853 - PV Module Performance Testing and Energy Rating

This module implements IEC 61853-1 (Performance testing and energy rating of terrestrial
photovoltaic modules) for comprehensive PV module characterization.

Key Test Conditions:
- Multiple irradiance levels (100-1100 W/m²)
- Multiple module temperatures (15-75°C)
- Angle of incidence effects (0-75°)
- Low irradiance behavior

Parameters Calculated:
- Temperature coefficients (α, β, γ)
- STC power rating
- Low irradiance performance
- Angle of incidence modifier
- Normal Operating Cell Temperature (NOCT)
"""

import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from scipy.optimize import curve_fit

from .base_protocol import (
    BaseProtocol, ProtocolResult, Uncertainty, TestStatus, DataQuality
)


@dataclass
class PerformanceMatrix:
    """Container for performance matrix data"""
    irradiances: List[float]  # W/m²
    temperatures: List[float]  # °C
    power_matrix: np.ndarray  # Power at each condition
    voltage_matrix: np.ndarray
    current_matrix: np.ndarray


class IEC61853(BaseProtocol):
    """
    IEC 61853-1 Performance Testing Protocol

    Implements comprehensive performance characterization including
    temperature coefficients, power rating, and environmental effects.
    """

    # Standard Test Conditions
    STC_IRRADIANCE = 1000.0  # W/m²
    STC_TEMPERATURE = 25.0    # °C

    # Standard irradiance levels for testing (W/m²)
    STANDARD_IRRADIANCES = [100, 200, 400, 600, 800, 1000, 1100]

    # Standard module temperatures for testing (°C)
    STANDARD_TEMPERATURES = [15, 25, 50, 75]

    def __init__(self):
        """Initialize IEC 61853 protocol handler"""
        super().__init__("IEC 61853-1", "2011")

        self.uncertainty_sources = {
            'power_measurement': 0.03,         # 3% typical
            'temperature_measurement': 0.5,    # ±0.5°C
            'irradiance_measurement': 0.02,    # 2%
            'spectral_effects': 0.02,         # 2%
            'non_uniformity': 0.02,           # 2%
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate performance matrix data

        Args:
            data: Dictionary containing performance test data

        Returns:
            True if valid, False otherwise
        """
        required_fields = ['irradiances', 'temperatures', 'power_matrix']

        for field in required_fields:
            if field not in data:
                print(f"Error: Missing required field '{field}'")
                return False

        irr = data['irradiances']
        temps = data['temperatures']
        power = np.array(data['power_matrix'])

        # Check matrix dimensions
        if power.shape != (len(temps), len(irr)):
            print(f"Error: Power matrix shape {power.shape} doesn't match "
                  f"expected ({len(temps)}, {len(irr)})")
            return False

        # Check for minimum data points
        if len(irr) < 3 or len(temps) < 3:
            print("Error: Need at least 3 irradiance and 3 temperature points")
            return False

        # Check ranges
        if min(irr) > 200 or max(irr) < 800:
            print("Warning: Irradiance range should cover at least 200-800 W/m²")

        if min(temps) > 20 or max(temps) < 50:
            print("Warning: Temperature range should cover at least 20-50°C")

        return True

    def calculate(self, data: Dict[str, Any]) -> ProtocolResult:
        """
        Calculate performance parameters and temperature coefficients

        Args:
            data: Dictionary with performance matrix data

        Returns:
            ProtocolResult with performance analysis
        """
        if not self.validate_data(data):
            result = self.create_result(status=TestStatus.FAIL)
            result.notes = "Data validation failed"
            return result

        result = self.create_result(status=TestStatus.PASS)

        # Extract data
        irradiances = np.array(data['irradiances'])
        temperatures = np.array(data['temperatures'])
        power_matrix = np.array(data['power_matrix'])

        # Store metadata
        result.metadata.update({
            'irradiance_levels': irradiances.tolist(),
            'temperature_levels': temperatures.tolist(),
            'test_conditions_count': power_matrix.size
        })

        # Calculate STC power rating
        p_stc = self._calculate_stc_power(irradiances, temperatures, power_matrix)
        result.add_measurement('P_STC', p_stc)

        # Calculate temperature coefficients
        temp_coeffs = self._calculate_temperature_coefficients(
            data, irradiances, temperatures, power_matrix
        )

        result.add_measurement('alpha_Isc', temp_coeffs['alpha_isc'])
        result.add_measurement('beta_Voc', temp_coeffs['beta_voc'])
        result.add_measurement('gamma_Pmp', temp_coeffs['gamma_pmp'])

        # Calculate low irradiance performance
        low_irr_perf = self._calculate_low_irradiance_performance(
            irradiances, temperatures, power_matrix, p_stc.value
        )
        result.add_measurement('low_irradiance_performance', low_irr_perf)

        # Calculate NOCT if data available
        if 'noct_data' in data:
            noct = self._calculate_noct(data['noct_data'])
            result.add_measurement('NOCT', noct)

        # Calculate angle of incidence effects if data available
        if 'aoi_data' in data:
            aoi_modifier = self._calculate_aoi_modifier(data['aoi_data'])
            result.add_measurement('AOI_modifier', aoi_modifier)

        # Calculate performance at various conditions
        perf_200 = self._calculate_performance_at_condition(
            irradiances, temperatures, power_matrix, 200, 25
        )
        result.add_measurement('P_200W_25C', perf_200)

        perf_800 = self._calculate_performance_at_condition(
            irradiances, temperatures, power_matrix, 800, 25
        )
        result.add_measurement('P_800W_25C', perf_800)

        # Assess data quality
        result.data_quality = self.assess_data_quality(p_stc)

        # Apply pass/fail criteria
        self._apply_pass_fail_criteria(result)

        return result

    def _calculate_stc_power(self, irradiances: np.ndarray, temperatures: np.ndarray,
                            power_matrix: np.ndarray) -> Uncertainty:
        """
        Calculate power at STC using interpolation/extrapolation

        Args:
            irradiances: Array of test irradiances
            temperatures: Array of test temperatures
            power_matrix: Matrix of power values

        Returns:
            Uncertainty object with STC power
        """
        from scipy.interpolate import RectBivariateSpline

        # Create interpolation function
        # Note: RectBivariateSpline expects (x, y) = (rows, cols) = (temps, irr)
        interp_func = RectBivariateSpline(temperatures, irradiances, power_matrix, kx=2, ky=2)

        # Evaluate at STC
        p_stc_value = float(interp_func(self.STC_TEMPERATURE, self.STC_IRRADIANCE)[0, 0])

        # Calculate uncertainty
        uncertainty_sources = {
            'power_meter': abs(p_stc_value) * self.uncertainty_sources['power_measurement'],
            'interpolation': abs(p_stc_value) * 0.01,  # 1% for interpolation
            'temperature': abs(p_stc_value) * 0.005,   # 0.5% for temp uncertainty
            'irradiance': abs(p_stc_value) * self.uncertainty_sources['irradiance_measurement']
        }

        std_uncertainty = self.combine_uncertainties(uncertainty_sources)

        return Uncertainty(
            value=p_stc_value,
            standard_uncertainty=std_uncertainty,
            sources=uncertainty_sources
        )

    def _calculate_temperature_coefficients(self, data: Dict[str, Any],
                                           irradiances: np.ndarray,
                                           temperatures: np.ndarray,
                                           power_matrix: np.ndarray) -> Dict[str, Uncertainty]:
        """
        Calculate temperature coefficients for Isc, Voc, and Pmp

        Args:
            data: Complete dataset including voltage and current
            irradiances: Array of test irradiances
            temperatures: Array of test temperatures
            power_matrix: Matrix of power values

        Returns:
            Dictionary of temperature coefficients with uncertainties
        """
        # Find index closest to 1000 W/m²
        idx_1000 = np.argmin(np.abs(irradiances - 1000))
        irr_actual = irradiances[idx_1000]

        # Extract power vs temperature at ~1000 W/m²
        power_vs_temp = power_matrix[:, idx_1000]

        # Perform linear regression
        regression = self.calculate_linear_regression(temperatures, power_vs_temp)

        # Calculate gamma (Pmp temperature coefficient) in %/°C
        # gamma = (dP/dT) / P_ref * 100
        p_ref = np.interp(25.0, temperatures, power_vs_temp)  # Power at 25°C
        gamma_value = (regression['slope'] / p_ref) * 100  # %/°C

        gamma_uncertainty = (regression['slope_uncertainty'] / p_ref) * 100

        gamma_pmp = Uncertainty(
            value=gamma_value,
            standard_uncertainty=gamma_uncertainty,
            sources={'regression': gamma_uncertainty}
        )

        # Calculate alpha and beta if I-V data available
        if 'current_matrix' in data and 'voltage_matrix' in data:
            current_matrix = np.array(data['current_matrix'])
            voltage_matrix = np.array(data['voltage_matrix'])

            # Extract Isc and Voc vs temperature at ~1000 W/m²
            isc_vs_temp = current_matrix[:, idx_1000]
            voc_vs_temp = voltage_matrix[:, idx_1000]

            # Regression for Isc
            isc_regression = self.calculate_linear_regression(temperatures, isc_vs_temp)
            isc_ref = np.interp(25.0, temperatures, isc_vs_temp)
            alpha_value = (isc_regression['slope'] / isc_ref) * 100  # %/°C
            alpha_uncertainty = (isc_regression['slope_uncertainty'] / isc_ref) * 100

            # Regression for Voc
            voc_regression = self.calculate_linear_regression(temperatures, voc_vs_temp)
            voc_ref = np.interp(25.0, temperatures, voc_vs_temp)
            beta_value = (voc_regression['slope'] / voc_ref) * 100  # %/°C
            beta_uncertainty = (voc_regression['slope_uncertainty'] / voc_ref) * 100

            alpha_isc = Uncertainty(
                value=alpha_value,
                standard_uncertainty=alpha_uncertainty,
                sources={'regression': alpha_uncertainty}
            )

            beta_voc = Uncertainty(
                value=beta_value,
                standard_uncertainty=beta_uncertainty,
                sources={'regression': beta_uncertainty}
            )
        else:
            # Use typical values if I-V data not available
            alpha_isc = Uncertainty(value=0.05, standard_uncertainty=0.01)  # Typical +0.05%/°C
            beta_voc = Uncertainty(value=-0.30, standard_uncertainty=0.05)  # Typical -0.30%/°C

        return {
            'alpha_isc': alpha_isc,
            'beta_voc': beta_voc,
            'gamma_pmp': gamma_pmp
        }

    def _calculate_low_irradiance_performance(self, irradiances: np.ndarray,
                                             temperatures: np.ndarray,
                                             power_matrix: np.ndarray,
                                             p_stc: float) -> Dict[str, float]:
        """
        Calculate performance at low irradiance conditions

        Args:
            irradiances: Array of test irradiances
            temperatures: Array of test temperatures
            power_matrix: Matrix of power values
            p_stc: Power at STC

        Returns:
            Dictionary of low irradiance performance metrics
        """
        from scipy.interpolate import RectBivariateSpline

        # Create interpolation function
        interp_func = RectBivariateSpline(temperatures, irradiances, power_matrix, kx=2, ky=2)

        # Calculate power at 200 W/m², 25°C
        p_200 = float(interp_func(25.0, 200.0)[0, 0])

        # Calculate relative performance
        # At 200 W/m², ideal would be 20% of STC power
        ideal_200 = p_stc * (200 / 1000)
        performance_ratio_200 = (p_200 / ideal_200) if ideal_200 > 0 else 0

        # Calculate power at 400 W/m², 25°C
        p_400 = float(interp_func(25.0, 400.0)[0, 0])
        ideal_400 = p_stc * (400 / 1000)
        performance_ratio_400 = (p_400 / ideal_400) if ideal_400 > 0 else 0

        return {
            'P_200W': p_200,
            'P_400W': p_400,
            'performance_ratio_200W': performance_ratio_200,
            'performance_ratio_400W': performance_ratio_400,
            'low_light_loss_200W_percent': (1 - performance_ratio_200) * 100,
            'low_light_loss_400W_percent': (1 - performance_ratio_400) * 100
        }

    def _calculate_performance_at_condition(self, irradiances: np.ndarray,
                                           temperatures: np.ndarray,
                                           power_matrix: np.ndarray,
                                           target_irr: float,
                                           target_temp: float) -> Uncertainty:
        """
        Calculate power at specific test condition

        Args:
            irradiances: Array of test irradiances
            temperatures: Array of test temperatures
            power_matrix: Matrix of power values
            target_irr: Target irradiance (W/m²)
            target_temp: Target temperature (°C)

        Returns:
            Uncertainty object with power at specified condition
        """
        from scipy.interpolate import RectBivariateSpline

        # Create interpolation function
        interp_func = RectBivariateSpline(temperatures, irradiances, power_matrix, kx=2, ky=2)

        # Evaluate at target condition
        power_value = float(interp_func(target_temp, target_irr)[0, 0])

        # Calculate uncertainty
        uncertainty_sources = {
            'power_meter': abs(power_value) * self.uncertainty_sources['power_measurement'],
            'interpolation': abs(power_value) * 0.015,  # 1.5% for interpolation
        }

        std_uncertainty = self.combine_uncertainties(uncertainty_sources)

        return Uncertainty(
            value=power_value,
            standard_uncertainty=std_uncertainty,
            sources=uncertainty_sources
        )

    def _calculate_noct(self, noct_data: Dict[str, Any]) -> Uncertainty:
        """
        Calculate Nominal Operating Cell Temperature

        NOCT test conditions:
        - Irradiance: 800 W/m²
        - Ambient temperature: 20°C
        - Wind speed: 1 m/s
        - Open circuit

        Args:
            noct_data: Dictionary with NOCT test measurements

        Returns:
            Uncertainty object with NOCT value (°C)
        """
        # Extract data
        cell_temp = noct_data.get('cell_temperature', 0)
        ambient_temp = noct_data.get('ambient_temperature', 20)
        irradiance = noct_data.get('irradiance', 800)
        wind_speed = noct_data.get('wind_speed', 1)

        # Correct to standard NOCT conditions if needed
        # NOCT = T_cell - T_ambient at 800 W/m² + T_ambient_ref
        delta_t = cell_temp - ambient_temp

        # Irradiance correction (linear approximation)
        if abs(irradiance - 800) > 50:
            delta_t = delta_t * (800 / irradiance)

        noct_value = delta_t + 20  # Add reference ambient temperature

        # Calculate uncertainty
        uncertainty_sources = {
            'temperature_sensor': self.uncertainty_sources['temperature_measurement'],
            'irradiance_variation': 1.0,  # ±1°C for irradiance uncertainty
            'wind_variation': 0.5,        # ±0.5°C for wind speed variation
        }

        std_uncertainty = self.combine_uncertainties(uncertainty_sources)

        return Uncertainty(
            value=noct_value,
            standard_uncertainty=std_uncertainty,
            sources=uncertainty_sources
        )

    def _calculate_aoi_modifier(self, aoi_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate angle of incidence (AOI) modifier

        The AOI modifier describes how module performance changes with
        the angle of incident light.

        Args:
            aoi_data: Dictionary with AOI test data

        Returns:
            Dictionary with AOI modifier coefficients
        """
        angles = np.array(aoi_data.get('angles', []))  # degrees
        relative_response = np.array(aoi_data.get('relative_response', []))

        if len(angles) < 5:
            return {'error': 'Insufficient AOI data points'}

        # Fit ASHRAE model: IAM = 1 - b0 * (1/cos(θ) - 1)
        # Or use simple polynomial fit
        def aoi_model(theta, b0):
            """ASHRAE IAM model"""
            theta_rad = np.radians(theta)
            return 1 - b0 * (1 / np.cos(theta_rad) - 1)

        try:
            # Fit model
            popt, pcov = curve_fit(aoi_model, angles, relative_response, p0=[0.05])
            b0 = popt[0]
            b0_std = np.sqrt(pcov[0, 0])

            # Calculate R²
            residuals = relative_response - aoi_model(angles, b0)
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((relative_response - np.mean(relative_response))**2)
            r_squared = 1 - (ss_res / ss_tot)

            return {
                'model': 'ASHRAE',
                'b0': b0,
                'b0_uncertainty': b0_std,
                'r_squared': r_squared,
                'angles_tested': angles.tolist(),
                'fitted_values': aoi_model(angles, b0).tolist()
            }

        except Exception as e:
            return {'error': f'AOI model fitting failed: {str(e)}'}

    def _apply_pass_fail_criteria(self, result: ProtocolResult):
        """
        Apply pass/fail criteria based on IEC 61853

        Args:
            result: ProtocolResult to update
        """
        # Check STC power uncertainty
        p_stc = result.measurements.get('P_STC')
        if isinstance(p_stc, Uncertainty):
            result.add_criterion('stc_power_uncertainty_acceptable',
                               p_stc.relative_uncertainty < 3.0)

        # Check temperature coefficient ranges (typical for crystalline Si)
        gamma = result.measurements.get('gamma_Pmp')
        if isinstance(gamma, Uncertainty):
            # Typical range: -0.3 to -0.5 %/°C
            result.add_criterion('gamma_in_typical_range',
                               -0.7 < gamma.value < -0.2)

        alpha = result.measurements.get('alpha_Isc')
        if isinstance(alpha, Uncertainty):
            # Typical range: +0.03 to +0.07 %/°C
            result.add_criterion('alpha_in_typical_range',
                               0.0 < alpha.value < 0.15)

        beta = result.measurements.get('beta_Voc')
        if isinstance(beta, Uncertainty):
            # Typical range: -0.25 to -0.35 %/°C
            result.add_criterion('beta_in_typical_range',
                               -0.50 < beta.value < -0.15)

        # Check low irradiance performance
        low_irr = result.measurements.get('low_irradiance_performance')
        if isinstance(low_irr, dict):
            # Good modules should have < 10% loss at 200 W/m²
            loss_200 = low_irr.get('low_light_loss_200W_percent', 100)
            result.add_criterion('low_irradiance_performance_good',
                               loss_200 < 15.0)
