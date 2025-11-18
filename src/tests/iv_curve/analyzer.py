"""
I-V Curve Analysis Module per IEC 60904-1:2020
Photovoltaic devices - Part 1: Measurement of photovoltaic current-voltage characteristics

This module provides comprehensive I-V curve analysis including:
- Parameter extraction (Voc, Isc, Vmp, Imp, Pmax, FF)
- Temperature and irradiance corrections to STC
- Series and shunt resistance calculation
- Curve fitting and smoothing
- Visualization and comparison plotting
"""

import numpy as np
from scipy import interpolate, optimize
from scipy.signal import savgol_filter
from typing import Dict, List, Tuple, Optional, Union
import matplotlib.pyplot as plt
import warnings


class IVCurveData:
    """Container for I-V curve measurement data."""

    def __init__(
        self,
        voltage: np.ndarray,
        current: np.ndarray,
        temperature: float,
        irradiance: float,
        measurement_conditions: Optional[Dict] = None
    ):
        """
        Initialize I-V curve data.

        Args:
            voltage: Voltage measurements in V
            current: Current measurements in A
            temperature: Cell temperature in °C
            irradiance: Irradiance in W/m²
            measurement_conditions: Additional measurement metadata
        """
        if len(voltage) != len(current):
            raise ValueError("Voltage and current arrays must have the same length")

        if len(voltage) < 3:
            raise ValueError("At least 3 data points required for analysis")

        # Sort by voltage for consistent processing
        sort_idx = np.argsort(voltage)
        self.voltage = np.array(voltage)[sort_idx]
        self.current = np.array(current)[sort_idx]
        self.temperature = temperature
        self.irradiance = irradiance
        self.measurement_conditions = measurement_conditions or {}

        # Calculate power
        self.power = self.voltage * self.current

    def __repr__(self):
        return (f"IVCurveData(points={len(self.voltage)}, "
                f"T={self.temperature}°C, G={self.irradiance}W/m²)")


class IVCurveAnalyzer:
    """
    Comprehensive I-V curve analyzer implementing IEC 60904-1:2020 standards.
    """

    # Standard Test Conditions (STC)
    STC_TEMPERATURE = 25.0  # °C
    STC_IRRADIANCE = 1000.0  # W/m²
    STC_SPECTRUM = "AM1.5G"

    def __init__(self, smoothing: bool = True, smoothing_window: int = 5):
        """
        Initialize I-V curve analyzer.

        Args:
            smoothing: Apply Savitzky-Golay smoothing to data
            smoothing_window: Window size for smoothing (must be odd)
        """
        self.smoothing = smoothing
        self.smoothing_window = smoothing_window if smoothing_window % 2 == 1 else smoothing_window + 1

    def parse_iv_data(
        self,
        data: Union[np.ndarray, List, Dict],
        temperature: float,
        irradiance: float,
        format_type: str = 'array'
    ) -> IVCurveData:
        """
        Parse I-V curve data from various formats.

        Args:
            data: Input data (array, list of tuples, or dict)
            temperature: Cell temperature in °C
            irradiance: Irradiance in W/m²
            format_type: 'array' (Nx2), 'dict' (keys: 'V', 'I'), or 'tuples'

        Returns:
            IVCurveData object
        """
        if format_type == 'array':
            if isinstance(data, (list, tuple)):
                data = np.array(data)
            if data.shape[1] != 2:
                raise ValueError("Array format requires Nx2 shape (voltage, current)")
            voltage = data[:, 0]
            current = data[:, 1]

        elif format_type == 'dict':
            voltage = np.array(data.get('V', data.get('voltage', [])))
            current = np.array(data.get('I', data.get('current', [])))

        elif format_type == 'tuples':
            voltage = np.array([v for v, _ in data])
            current = np.array([i for _, i in data])

        else:
            raise ValueError(f"Unknown format type: {format_type}")

        return IVCurveData(voltage, current, temperature, irradiance)

    def smooth_curve(self, iv_data: IVCurveData) -> IVCurveData:
        """
        Apply Savitzky-Golay smoothing to reduce measurement noise.

        Args:
            iv_data: Raw I-V curve data

        Returns:
            Smoothed I-V curve data
        """
        if len(iv_data.voltage) < self.smoothing_window:
            warnings.warn("Too few points for smoothing, returning original data")
            return iv_data

        try:
            smoothed_current = savgol_filter(
                iv_data.current,
                self.smoothing_window,
                polyorder=2
            )

            return IVCurveData(
                iv_data.voltage,
                smoothed_current,
                iv_data.temperature,
                iv_data.irradiance,
                iv_data.measurement_conditions
            )
        except Exception as e:
            warnings.warn(f"Smoothing failed: {e}, returning original data")
            return iv_data

    def calculate_parameters(self, iv_data: IVCurveData) -> Dict[str, float]:
        """
        Calculate key I-V curve parameters per IEC 60904-1.

        Parameters extracted:
        - Voc: Open-circuit voltage
        - Isc: Short-circuit current
        - Vmp: Voltage at maximum power point
        - Imp: Current at maximum power point
        - Pmax: Maximum power
        - FF: Fill factor

        Args:
            iv_data: I-V curve data

        Returns:
            Dictionary of parameters
        """
        # Apply smoothing if enabled
        if self.smoothing:
            iv_data = self.smooth_curve(iv_data)

        # Short-circuit current (Isc) - current when V=0
        isc = self._calculate_isc(iv_data)

        # Open-circuit voltage (Voc) - voltage when I=0
        voc = self._calculate_voc(iv_data)

        # Maximum power point
        pmax_idx = np.argmax(iv_data.power)
        pmax = iv_data.power[pmax_idx]
        vmp = iv_data.voltage[pmax_idx]
        imp = iv_data.current[pmax_idx]

        # Fill factor
        ff = pmax / (voc * isc) if (voc * isc) > 0 else 0.0

        # Efficiency (requires module area - placeholder)
        # eta = pmax / (irradiance * area) * 100

        return {
            'Voc': float(voc),
            'Isc': float(isc),
            'Vmp': float(vmp),
            'Imp': float(imp),
            'Pmax': float(pmax),
            'FF': float(ff),
            'temperature': iv_data.temperature,
            'irradiance': iv_data.irradiance
        }

    def _calculate_isc(self, iv_data: IVCurveData) -> float:
        """Calculate short-circuit current by interpolation at V=0."""
        if 0 in iv_data.voltage:
            return float(iv_data.current[iv_data.voltage == 0][0])

        # Interpolate to find Isc at V=0
        f = interpolate.interp1d(
            iv_data.voltage,
            iv_data.current,
            kind='linear',
            fill_value='extrapolate'
        )
        return float(f(0))

    def _calculate_voc(self, iv_data: IVCurveData) -> float:
        """Calculate open-circuit voltage by interpolation at I=0."""
        if 0 in iv_data.current:
            return float(iv_data.voltage[iv_data.current == 0][0])

        # Interpolate to find Voc at I=0
        f = interpolate.interp1d(
            iv_data.current[::-1],
            iv_data.voltage[::-1],
            kind='linear',
            fill_value='extrapolate'
        )
        return float(f(0))

    def calculate_series_resistance(
        self,
        iv_data: IVCurveData,
        method: str = 'slope'
    ) -> float:
        """
        Calculate series resistance (Rs) from I-V curve.

        Methods:
        - 'slope': From slope near Voc
        - 'derivative': From dV/dI at I=0

        Args:
            iv_data: I-V curve data
            method: Calculation method

        Returns:
            Series resistance in Ω
        """
        if method == 'slope':
            # Use points near Voc (last 10% of current range)
            n_points = max(3, len(iv_data.current) // 10)
            v_near_voc = iv_data.voltage[-n_points:]
            i_near_voc = iv_data.current[-n_points:]

            # Linear fit: V = Voc - Rs*I
            coeffs = np.polyfit(i_near_voc, v_near_voc, 1)
            rs = -coeffs[0]  # Negative slope

        elif method == 'derivative':
            # Calculate numerical derivative dV/dI
            dv_di = np.gradient(iv_data.voltage, iv_data.current)
            # Rs is dV/dI near I=0 (at Voc)
            rs = abs(dv_di[-1])

        else:
            raise ValueError(f"Unknown method: {method}")

        return float(max(0, rs))  # Rs should be positive

    def calculate_shunt_resistance(
        self,
        iv_data: IVCurveData,
        method: str = 'slope'
    ) -> float:
        """
        Calculate shunt resistance (Rsh) from I-V curve.

        Methods:
        - 'slope': From slope near Isc
        - 'derivative': From dV/dI at V=0

        Args:
            iv_data: I-V curve data
            method: Calculation method

        Returns:
            Shunt resistance in Ω
        """
        if method == 'slope':
            # Use points near Isc (first 10% of voltage range)
            n_points = max(3, len(iv_data.voltage) // 10)
            v_near_isc = iv_data.voltage[:n_points]
            i_near_isc = iv_data.current[:n_points]

            # Linear fit: I = Isc - V/Rsh
            coeffs = np.polyfit(v_near_isc, i_near_isc, 1)
            rsh = -1.0 / coeffs[0] if coeffs[0] != 0 else np.inf

        elif method == 'derivative':
            # Calculate numerical derivative dV/dI
            dv_di = np.gradient(iv_data.voltage, iv_data.current)
            # Rsh is dV/dI near V=0 (at Isc)
            rsh = abs(dv_di[0])

        else:
            raise ValueError(f"Unknown method: {method}")

        return float(max(0, rsh))  # Rsh should be positive

    def correct_temperature_to_stc(
        self,
        params: Dict[str, float],
        temp_coefficients: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Correct I-V parameters to STC temperature (25°C) per IEC 60904-1.

        Temperature coefficients:
        - alpha (α): Temperature coefficient of Isc in A/°C or %/°C
        - beta (β): Temperature coefficient of Voc in V/°C or %/°C
        - gamma (γ): Temperature coefficient of Pmax in W/°C or %/°C

        Args:
            params: Measured parameters at test conditions
            temp_coefficients: Temperature coefficients (alpha, beta, gamma)

        Returns:
            Corrected parameters at STC
        """
        delta_t = self.STC_TEMPERATURE - params['temperature']

        alpha = temp_coefficients.get('alpha', 0.0)
        beta = temp_coefficients.get('beta', 0.0)
        gamma = temp_coefficients.get('gamma', 0.0)

        # Determine if coefficients are absolute or relative
        alpha_abs = alpha if abs(alpha) > 0.01 else alpha * params['Isc'] / 100
        beta_abs = beta if abs(beta) > 0.01 else beta * params['Voc'] / 100
        gamma_abs = gamma if abs(gamma) > 0.01 else gamma * params['Pmax'] / 100

        corrected = params.copy()

        # Apply temperature corrections
        corrected['Isc_stc'] = params['Isc'] + alpha_abs * delta_t
        corrected['Voc_stc'] = params['Voc'] + beta_abs * delta_t
        corrected['Pmax_stc'] = params['Pmax'] + gamma_abs * delta_t

        # Recalculate Vmp and Imp maintaining approximate ratio
        # This is a simplified approach; more sophisticated methods exist
        power_ratio = corrected['Pmax_stc'] / params['Pmax'] if params['Pmax'] > 0 else 1.0
        voltage_ratio = corrected['Voc_stc'] / params['Voc'] if params['Voc'] > 0 else 1.0

        corrected['Vmp_stc'] = params['Vmp'] * voltage_ratio
        corrected['Imp_stc'] = corrected['Pmax_stc'] / corrected['Vmp_stc'] if corrected['Vmp_stc'] > 0 else 0

        # Recalculate fill factor
        corrected['FF_stc'] = (corrected['Pmax_stc'] /
                               (corrected['Voc_stc'] * corrected['Isc_stc'])
                               if (corrected['Voc_stc'] * corrected['Isc_stc']) > 0 else 0)

        corrected['temperature'] = self.STC_TEMPERATURE

        return corrected

    def correct_irradiance_to_stc(
        self,
        params: Dict[str, float],
        linearity_factor: float = 1.0
    ) -> Dict[str, float]:
        """
        Correct I-V parameters to STC irradiance (1000 W/m²) per IEC 60904-1.

        Corrections assume linear relationship with irradiance for current,
        and logarithmic relationship for voltage.

        Args:
            params: Measured parameters at test conditions
            linearity_factor: Deviation from linear response (typically 0.98-1.02)

        Returns:
            Corrected parameters at STC irradiance
        """
        g_ratio = self.STC_IRRADIANCE / params['irradiance']

        corrected = params.copy()

        # Current scales linearly with irradiance
        corrected['Isc_stc'] = params['Isc'] * g_ratio * linearity_factor
        corrected['Imp_stc'] = params['Imp'] * g_ratio * linearity_factor

        # Voltage has logarithmic dependence (small correction)
        # ΔV ≈ n*k*T/q * ln(G2/G1) where n≈1, kT/q≈0.026V at 25°C
        thermal_voltage = 0.026 * (params['temperature'] + 273.15) / 298.15
        delta_v = thermal_voltage * np.log(g_ratio)

        corrected['Voc_stc'] = params['Voc'] + delta_v
        corrected['Vmp_stc'] = params['Vmp'] + delta_v * 0.85  # Vmp changes less than Voc

        # Recalculate power and fill factor
        corrected['Pmax_stc'] = corrected['Vmp_stc'] * corrected['Imp_stc']
        corrected['FF_stc'] = (corrected['Pmax_stc'] /
                               (corrected['Voc_stc'] * corrected['Isc_stc'])
                               if (corrected['Voc_stc'] * corrected['Isc_stc']) > 0 else 0)

        corrected['irradiance'] = self.STC_IRRADIANCE

        return corrected

    def fit_single_diode_model(
        self,
        iv_data: IVCurveData,
        initial_guess: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        Fit single-diode equivalent circuit model to I-V data.

        Model: I = IL - I0*(exp((V+I*Rs)/(n*Vt)) - 1) - (V+I*Rs)/Rsh

        Parameters:
        - IL: Light-generated current
        - I0: Diode saturation current
        - Rs: Series resistance
        - Rsh: Shunt resistance
        - n: Diode ideality factor

        Args:
            iv_data: I-V curve data
            initial_guess: Initial parameter values

        Returns:
            Fitted model parameters
        """
        # Thermal voltage Vt = kT/q
        k_boltzmann = 1.380649e-23
        q_electron = 1.602176634e-19
        T_kelvin = iv_data.temperature + 273.15
        Vt = k_boltzmann * T_kelvin / q_electron

        # Initial guess for parameters
        if initial_guess is None:
            params_basic = self.calculate_parameters(iv_data)
            rs_init = self.calculate_series_resistance(iv_data)
            rsh_init = self.calculate_shunt_resistance(iv_data)

            initial_guess = {
                'IL': params_basic['Isc'] * 1.01,
                'I0': 1e-9,
                'Rs': rs_init,
                'Rsh': rsh_init,
                'n': 1.2
            }

        def diode_model(V, IL, I0, Rs, Rsh, n):
            """Single diode model equation."""
            # Use Lambert W function for accurate solution
            # Simplified iterative approach
            I = np.zeros_like(V)
            for i, v in enumerate(V):
                # Initial guess
                I_guess = IL
                for _ in range(50):
                    exp_term = np.exp((v + I_guess * Rs) / (n * Vt))
                    f = IL - I0 * (exp_term - 1) - (v + I_guess * Rs) / Rsh - I_guess
                    df = -I0 * Rs / (n * Vt) * exp_term - Rs / Rsh - 1
                    I_new = I_guess - f / df
                    if abs(I_new - I_guess) < 1e-6:
                        I_guess = I_new
                        break
                    I_guess = I_new
                I[i] = I_guess
            return I

        try:
            # Fit the model
            popt, _ = optimize.curve_fit(
                diode_model,
                iv_data.voltage,
                iv_data.current,
                p0=[initial_guess['IL'], initial_guess['I0'],
                    initial_guess['Rs'], initial_guess['Rsh'], initial_guess['n']],
                bounds=([0, 0, 0, 0, 0.5],
                        [np.inf, 1e-3, 50, 1e6, 5]),
                maxfev=10000
            )

            return {
                'IL': float(popt[0]),
                'I0': float(popt[1]),
                'Rs': float(popt[2]),
                'Rsh': float(popt[3]),
                'n': float(popt[4])
            }
        except Exception as e:
            warnings.warn(f"Model fitting failed: {e}")
            return initial_guess

    def plot_iv_curve(
        self,
        iv_data: IVCurveData,
        params: Optional[Dict] = None,
        title: str = "I-V Characteristic Curve",
        save_path: Optional[str] = None,
        show_mpp: bool = True
    ) -> plt.Figure:
        """
        Plot I-V and P-V curves with key parameters marked.

        Args:
            iv_data: I-V curve data
            params: Calculated parameters (if None, will calculate)
            title: Plot title
            save_path: Path to save figure (optional)
            show_mpp: Mark maximum power point

        Returns:
            Matplotlib figure object
        """
        if params is None:
            params = self.calculate_parameters(iv_data)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

        # I-V curve
        ax1.plot(iv_data.voltage, iv_data.current, 'b-', linewidth=2, label='I-V Curve')
        ax1.axhline(y=0, color='k', linestyle='--', alpha=0.3)
        ax1.axvline(x=0, color='k', linestyle='--', alpha=0.3)

        # Mark key points
        ax1.plot(0, params['Isc'], 'ro', markersize=10, label=f"Isc = {params['Isc']:.3f} A")
        ax1.plot(params['Voc'], 0, 'go', markersize=10, label=f"Voc = {params['Voc']:.3f} V")

        if show_mpp:
            ax1.plot(params['Vmp'], params['Imp'], 'rs', markersize=12,
                    label=f"MPP: ({params['Vmp']:.3f} V, {params['Imp']:.3f} A)")

        ax1.set_xlabel('Voltage (V)', fontsize=12)
        ax1.set_ylabel('Current (A)', fontsize=12)
        ax1.set_title(f"{title}\nT={iv_data.temperature}°C, G={iv_data.irradiance}W/m²",
                     fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='best')

        # P-V curve
        ax2.plot(iv_data.voltage, iv_data.power, 'r-', linewidth=2, label='P-V Curve')
        ax2.axhline(y=0, color='k', linestyle='--', alpha=0.3)

        if show_mpp:
            ax2.plot(params['Vmp'], params['Pmax'], 'rs', markersize=12,
                    label=f"Pmax = {params['Pmax']:.3f} W\nFF = {params['FF']:.4f}")
            ax2.axvline(x=params['Vmp'], color='r', linestyle=':', alpha=0.5)
            ax2.axhline(y=params['Pmax'], color='r', linestyle=':', alpha=0.5)

        ax2.set_xlabel('Voltage (V)', fontsize=12)
        ax2.set_ylabel('Power (W)', fontsize=12)
        ax2.set_title('Power-Voltage Characteristic', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='best')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return fig

    def plot_comparison(
        self,
        iv_data_before: IVCurveData,
        iv_data_after: IVCurveData,
        labels: Tuple[str, str] = ("Before", "After"),
        title: str = "I-V Curve Comparison",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot comparison of two I-V curves (e.g., before/after stress test).

        Args:
            iv_data_before: Initial I-V curve data
            iv_data_after: Final I-V curve data
            labels: Labels for the two curves
            title: Plot title
            save_path: Path to save figure (optional)

        Returns:
            Matplotlib figure object
        """
        params_before = self.calculate_parameters(iv_data_before)
        params_after = self.calculate_parameters(iv_data_after)

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))

        # I-V comparison
        ax1.plot(iv_data_before.voltage, iv_data_before.current,
                'b-', linewidth=2, label=labels[0])
        ax1.plot(iv_data_after.voltage, iv_data_after.current,
                'r--', linewidth=2, label=labels[1])
        ax1.set_xlabel('Voltage (V)', fontsize=11)
        ax1.set_ylabel('Current (A)', fontsize=11)
        ax1.set_title('I-V Curves Comparison', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # P-V comparison
        ax2.plot(iv_data_before.voltage, iv_data_before.power,
                'b-', linewidth=2, label=labels[0])
        ax2.plot(iv_data_after.voltage, iv_data_after.power,
                'r--', linewidth=2, label=labels[1])
        ax2.set_xlabel('Voltage (V)', fontsize=11)
        ax2.set_ylabel('Power (W)', fontsize=11)
        ax2.set_title('P-V Curves Comparison', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend()

        # Parameter comparison bar chart
        param_names = ['Pmax', 'Voc', 'Isc', 'FF']
        before_values = [params_before['Pmax'], params_before['Voc'],
                        params_before['Isc'], params_before['FF']]
        after_values = [params_after['Pmax'], params_after['Voc'],
                       params_after['Isc'], params_after['FF']]

        x = np.arange(len(param_names))
        width = 0.35

        # Normalize for visualization (FF is already 0-1)
        norm_before = [before_values[0]/max(before_values[0], after_values[0]),
                      before_values[1]/max(before_values[1], after_values[1]),
                      before_values[2]/max(before_values[2], after_values[2]),
                      before_values[3]]
        norm_after = [after_values[0]/max(before_values[0], after_values[0]),
                     after_values[1]/max(before_values[1], after_values[1]),
                     after_values[2]/max(before_values[2], after_values[2]),
                     after_values[3]]

        bars1 = ax3.bar(x - width/2, norm_before, width, label=labels[0], color='blue', alpha=0.7)
        bars2 = ax3.bar(x + width/2, norm_after, width, label=labels[1], color='red', alpha=0.7)

        ax3.set_ylabel('Normalized Value', fontsize=11)
        ax3.set_title('Parameter Comparison (Normalized)', fontsize=12, fontweight='bold')
        ax3.set_xticks(x)
        ax3.set_xticklabels(param_names)
        ax3.legend()
        ax3.grid(True, alpha=0.3, axis='y')

        # Degradation percentages
        degradation = {
            'Pmax': ((params_before['Pmax'] - params_after['Pmax']) /
                    params_before['Pmax'] * 100),
            'Voc': ((params_before['Voc'] - params_after['Voc']) /
                   params_before['Voc'] * 100),
            'Isc': ((params_before['Isc'] - params_after['Isc']) /
                   params_before['Isc'] * 100),
            'FF': ((params_before['FF'] - params_after['FF']) /
                  params_before['FF'] * 100)
        }

        colors = ['green' if d < 0 else 'red' for d in degradation.values()]
        ax4.barh(list(degradation.keys()), list(degradation.values()), color=colors, alpha=0.7)
        ax4.axvline(x=0, color='k', linestyle='-', linewidth=0.8)
        ax4.set_xlabel('Change (%)', fontsize=11)
        ax4.set_title('Parameter Degradation', fontsize=12, fontweight='bold')
        ax4.grid(True, alpha=0.3, axis='x')

        # Add percentage labels
        for i, (param, value) in enumerate(degradation.items()):
            ax4.text(value, i, f' {value:+.2f}%', va='center',
                    ha='left' if value >= 0 else 'right')

        fig.suptitle(title, fontsize=14, fontweight='bold', y=0.995)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return fig


def validate_iv_data(
    iv_data: IVCurveData,
    min_points: int = 10,
    max_noise_ratio: float = 0.1
) -> Tuple[bool, List[str]]:
    """
    Validate I-V curve data quality per IEC 60904-1.

    Args:
        iv_data: I-V curve data to validate
        min_points: Minimum number of data points required
        max_noise_ratio: Maximum acceptable noise-to-signal ratio

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    # Check minimum points
    if len(iv_data.voltage) < min_points:
        errors.append(f"Insufficient data points: {len(iv_data.voltage)} < {min_points}")

    # Check for monotonicity
    if not np.all(np.diff(iv_data.voltage) >= 0):
        errors.append("Voltage values are not monotonically increasing")

    # Check current decreases with voltage (typical for PV)
    if not np.all(np.diff(iv_data.current) <= 0):
        # Allow small violations due to noise
        violations = np.sum(np.diff(iv_data.current) > 0)
        if violations > len(iv_data.current) * 0.1:
            errors.append("Current should generally decrease with voltage")

    # Check for negative power at MPP region
    if np.max(iv_data.power) < 0:
        errors.append("Maximum power is negative - check current polarity")

    # Check measurement conditions
    if iv_data.temperature < -40 or iv_data.temperature > 100:
        errors.append(f"Temperature out of range: {iv_data.temperature}°C")

    if iv_data.irradiance < 0 or iv_data.irradiance > 1500:
        errors.append(f"Irradiance out of range: {iv_data.irradiance}W/m²")

    # Check for excessive noise
    current_smoothed = savgol_filter(iv_data.current, min(11, len(iv_data.current)//2*2+1), 2)
    noise = np.std(iv_data.current - current_smoothed)
    signal = np.std(iv_data.current)
    if signal > 0 and noise / signal > max_noise_ratio:
        errors.append(f"Excessive noise detected: SNR = {signal/noise:.1f}")

    return len(errors) == 0, errors


if __name__ == "__main__":
    # Example usage and testing
    print("I-V Curve Analyzer - IEC 60904-1:2020")
    print("=" * 50)

    # Generate sample I-V curve data
    voltage_sample = np.linspace(0, 40, 50)
    # Simplified diode equation for demo
    current_sample = 8.5 * (1 - np.exp((voltage_sample - 40) / 5)) - voltage_sample / 1000

    analyzer = IVCurveAnalyzer(smoothing=True)
    iv_data = analyzer.parse_iv_data(
        np.column_stack([voltage_sample, current_sample]),
        temperature=25.0,
        irradiance=1000.0
    )

    # Validate data
    is_valid, errors = validate_iv_data(iv_data)
    print(f"\nData validation: {'PASS' if is_valid else 'FAIL'}")
    if errors:
        for error in errors:
            print(f"  - {error}")

    # Calculate parameters
    params = analyzer.calculate_parameters(iv_data)
    print("\nCalculated Parameters:")
    for key, value in params.items():
        print(f"  {key}: {value:.4f}")

    # Calculate resistances
    rs = analyzer.calculate_series_resistance(iv_data)
    rsh = analyzer.calculate_shunt_resistance(iv_data)
    print(f"\nSeries Resistance: {rs:.4f} Ω")
    print(f"Shunt Resistance: {rsh:.4f} Ω")

    print("\n" + "=" * 50)
    print("Module ready for production use")
