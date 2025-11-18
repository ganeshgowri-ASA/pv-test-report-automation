"""
I-V Curve Analysis Module per IEC 60904-1:2020

This module provides comprehensive I-V curve analysis tools including:
- I-V curve parameter extraction and analysis
- Translation to Standard Test Conditions (STC)
- NOCT (Nominal Operating Cell Temperature) calculations
- Thermal performance analysis
- Compliance with IEC 60904-1:2020 and IEC 61215

Main Components:
- analyzer: I-V curve parsing, parameter calculation, plotting
- stc_calculator: STC translation with uncertainty analysis
- noct_calculator: NOCT testing and thermal performance
"""

from .analyzer import (
    IVCurveData,
    IVCurveAnalyzer,
    validate_iv_data
)

from .stc_calculator import (
    STCCalculator,
    STCConditions,
    TemperatureCoefficients,
    UncertaintyComponents,
    estimate_temperature_coefficients
)

from .noct_calculator import (
    NOCTCalculator,
    NOCTConditions,
    ThermalParameters,
    calculate_inoct_power,
    calculate_module_efficiency_at_noct
)

__version__ = "1.0.0"

__all__ = [
    # Analyzer
    'IVCurveData',
    'IVCurveAnalyzer',
    'validate_iv_data',

    # STC Calculator
    'STCCalculator',
    'STCConditions',
    'TemperatureCoefficients',
    'UncertaintyComponents',
    'estimate_temperature_coefficients',

    # NOCT Calculator
    'NOCTCalculator',
    'NOCTConditions',
    'ThermalParameters',
    'calculate_inoct_power',
    'calculate_module_efficiency_at_noct',
]


def get_version():
    """Return the version of the I-V curve analysis module."""
    return __version__


def get_supported_standards():
    """Return list of supported IEC standards."""
    return [
        'IEC 60904-1:2020 - Measurement of photovoltaic current-voltage characteristics',
        'IEC 60904-7 - Computation of spectral mismatch error',
        'IEC 61215-2:2021 - Terrestrial photovoltaic modules - Design qualification',
        'ISO/IEC 17025 - General requirements for testing and calibration laboratories'
    ]


# Module-level convenience functions

def quick_analyze(voltage, current, temperature, irradiance, **kwargs):
    """
    Quick analysis of I-V curve data.

    Args:
        voltage: Voltage measurements (V)
        current: Current measurements (A)
        temperature: Cell temperature (°C)
        irradiance: Irradiance (W/m²)
        **kwargs: Additional arguments for IVCurveAnalyzer

    Returns:
        Dictionary of calculated parameters

    Example:
        >>> import numpy as np
        >>> from src.tests.iv_curve import quick_analyze
        >>>
        >>> V = np.linspace(0, 40, 50)
        >>> I = 8.5 * (1 - np.exp((V - 40) / 5))
        >>>
        >>> params = quick_analyze(V, I, temperature=25, irradiance=1000)
        >>> print(f"Pmax: {params['Pmax']:.2f} W")
    """
    analyzer = IVCurveAnalyzer(**kwargs)
    iv_data = IVCurveData(voltage, current, temperature, irradiance)
    return analyzer.calculate_parameters(iv_data)


def translate_to_stc(measured_params, temp_coefficients, measured_conditions, **kwargs):
    """
    Quick translation of parameters to STC.

    Args:
        measured_params: Measured I-V parameters
        temp_coefficients: TemperatureCoefficients object or dict
        measured_conditions: Dict with 'temperature' and 'irradiance'
        **kwargs: Additional arguments for STCCalculator

    Returns:
        Parameters translated to STC

    Example:
        >>> from src.tests.iv_curve import translate_to_stc, TemperatureCoefficients
        >>>
        >>> measured = {'Isc': 8.2, 'Voc': 36.5, 'Pmax': 219, 'Imp': 7.5, 'Vmp': 29.2, 'FF': 0.731}
        >>> temp_coeff = TemperatureCoefficients(alpha_isc=0.05, beta_voc=-0.35,
        ...                                       gamma_pmax=-0.45, is_relative=True)
        >>> conditions = {'temperature': 45.0, 'irradiance': 800.0}
        >>>
        >>> stc_params = translate_to_stc(measured, temp_coeff, conditions)
        >>> print(f"Pmax at STC: {stc_params['Pmax_stc']:.2f} W")
    """
    calculator = STCCalculator(**kwargs)

    # Convert dict to TemperatureCoefficients if needed
    if isinstance(temp_coefficients, dict):
        temp_coefficients = TemperatureCoefficients(**temp_coefficients)

    return calculator.translate_to_stc(
        measured_params,
        temp_coefficients,
        measured_conditions
    )


def calculate_operating_temp(noct, ambient_temp, irradiance, **kwargs):
    """
    Quick calculation of operating temperature from NOCT.

    Args:
        noct: Nominal Operating Cell Temperature (°C)
        ambient_temp: Ambient temperature (°C)
        irradiance: Irradiance (W/m²)
        **kwargs: Additional arguments (wind_speed, mounting_correction)

    Returns:
        Estimated cell operating temperature (°C)

    Example:
        >>> from src.tests.iv_curve import calculate_operating_temp
        >>>
        >>> T_cell = calculate_operating_temp(noct=45, ambient_temp=35, irradiance=1000)
        >>> print(f"Operating temperature: {T_cell:.1f}°C")
    """
    calculator = NOCTCalculator()
    thermal_params = ThermalParameters(noct=noct)

    return calculator.calculate_operating_temperature(
        thermal_params,
        ambient_temp,
        irradiance,
        wind_speed=kwargs.get('wind_speed', 1.0),
        mounting_correction=kwargs.get('mounting_correction', 1.0)
    )


# Print module information when imported
def _print_module_info():
    """Print module information (for debugging)."""
    import sys
    if hasattr(sys, 'ps1'):  # Interactive mode
        print(f"I-V Curve Analysis Module v{__version__}")
        print("Supported standards:")
        for standard in get_supported_standards():
            print(f"  - {standard}")


# Uncomment to enable module info on import
# _print_module_info()
