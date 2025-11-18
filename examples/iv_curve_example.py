#!/usr/bin/env python3
"""
Complete Example: I-V Curve Analysis Workflow
Demonstrates all major features of the I-V curve analysis system
"""

import numpy as np
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tests.iv_curve import (
    IVCurveAnalyzer,
    IVCurveData,
    STCCalculator,
    TemperatureCoefficients,
    NOCTCalculator,
    ThermalParameters,
    UncertaintyComponents,
    validate_iv_data
)


def generate_sample_iv_curve(
    isc=8.5,
    voc=40.0,
    temperature=25.0,
    irradiance=1000.0,
    num_points=50,
    add_noise=False
):
    """Generate realistic I-V curve data for demonstration."""
    # Voltage points from 0 to Voc
    voltage = np.linspace(0, voc, num_points)

    # Simplified single-diode model for realistic curve
    # I = IL - I0*(exp((V+I*Rs)/(n*Vt)) - 1) - (V+I*Rs)/Rsh
    # Simplified: I ≈ Isc * (1 - exp((V - Voc)/n*Vt))

    n = 1.2  # Ideality factor
    Vt = 0.026 * (temperature + 273.15) / 298.15  # Thermal voltage

    # Current calculation (simplified)
    current = isc * (1 - np.exp((voltage - voc) / (n * Vt)))

    # Add series resistance effect (voltage drop at high current)
    Rs = 0.3  # Series resistance
    current = current - voltage / 1000  # Shunt resistance effect

    # Ensure current doesn't go negative
    current = np.maximum(current, 0)

    # Add measurement noise if requested
    if add_noise:
        noise = np.random.normal(0, 0.02 * isc, num_points)
        current = current + noise
        current = np.maximum(current, 0)

    return IVCurveData(voltage, current, temperature, irradiance)


def example_1_basic_analysis():
    """Example 1: Basic I-V curve analysis."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Basic I-V Curve Analysis")
    print("=" * 70)

    # Generate sample data
    iv_data = generate_sample_iv_curve(
        isc=8.5,
        voc=40.0,
        temperature=25.0,
        irradiance=1000.0
    )

    # Create analyzer
    analyzer = IVCurveAnalyzer(smoothing=True)

    # Validate data
    is_valid, errors = validate_iv_data(iv_data)
    print(f"\nData Validation: {'✓ PASS' if is_valid else '✗ FAIL'}")
    if errors:
        for error in errors:
            print(f"  ⚠ {error}")

    # Calculate parameters
    params = analyzer.calculate_parameters(iv_data)

    print("\nCalculated I-V Parameters:")
    print(f"  Open-circuit voltage (Voc): {params['Voc']:.3f} V")
    print(f"  Short-circuit current (Isc): {params['Isc']:.3f} A")
    print(f"  Maximum power (Pmax):        {params['Pmax']:.3f} W")
    print(f"  Voltage at MPP (Vmp):        {params['Vmp']:.3f} V")
    print(f"  Current at MPP (Imp):        {params['Imp']:.3f} A")
    print(f"  Fill Factor (FF):            {params['FF']:.4f}")

    # Calculate resistances
    rs = analyzer.calculate_series_resistance(iv_data)
    rsh = analyzer.calculate_shunt_resistance(iv_data)

    print("\nParasitic Resistances:")
    print(f"  Series resistance (Rs):   {rs:.4f} Ω")
    print(f"  Shunt resistance (Rsh):   {rsh:.2f} Ω")

    return iv_data, params


def example_2_stc_translation():
    """Example 2: Translate measurements to STC."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Translation to Standard Test Conditions")
    print("=" * 70)

    # Measurement at non-STC conditions
    iv_data = generate_sample_iv_curve(
        isc=8.2,
        voc=36.5,
        temperature=45.0,
        irradiance=800.0
    )

    analyzer = IVCurveAnalyzer()
    measured_params = analyzer.calculate_parameters(iv_data)

    print(f"\nMeasured Conditions: T={iv_data.temperature}°C, G={iv_data.irradiance}W/m²")
    print(f"  Pmax: {measured_params['Pmax']:.2f} W")
    print(f"  Voc:  {measured_params['Voc']:.2f} V")
    print(f"  Isc:  {measured_params['Isc']:.2f} A")

    # Temperature coefficients (typical crystalline silicon)
    temp_coeff = TemperatureCoefficients(
        alpha_isc=0.05,     # %/°C
        beta_voc=-0.35,     # %/°C
        gamma_pmax=-0.45,   # %/°C
        is_relative=True
    )

    # Translate to STC
    calculator = STCCalculator()
    stc_params = calculator.translate_to_stc(
        measured_params,
        temp_coeff,
        {
            'temperature': iv_data.temperature,
            'irradiance': iv_data.irradiance
        },
        method='iec60904'
    )

    print(f"\nTranslated to STC (25°C, 1000W/m²):")
    print(f"  Pmax: {stc_params['Pmax_stc']:.2f} W")
    print(f"  Voc:  {stc_params['Voc_stc']:.2f} V")
    print(f"  Isc:  {stc_params['Isc_stc']:.2f} A")
    print(f"  FF:   {stc_params['FF_stc']:.4f}")

    # Validate translation
    is_valid, warnings = calculator.validate_translation(measured_params, stc_params)
    print(f"\nTranslation Validation: {'✓ PASS' if is_valid else '⚠ WARNINGS'}")
    for warning in warnings:
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

    print(f"\nUncertainty Budget (Pmax):")
    print(f"  Combined standard uncertainty: ±{uncertainty['combined_standard_uncertainty']:.2f}%")
    print(f"  Expanded uncertainty (k=2):    ±{uncertainty['expanded_uncertainty_k2']:.2f}%")
    print(f"  Confidence level:              {uncertainty['confidence_level']*100:.0f}%")


def example_3_noct_analysis():
    """Example 3: NOCT calculation and thermal analysis."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: NOCT and Thermal Performance Analysis")
    print("=" * 70)

    calculator = NOCTCalculator()

    # Calculate NOCT from field measurements
    print("\n1. Calculate NOCT from Field Measurements:")
    print("-" * 70)

    measured_cell_temp = 55.0  # °C
    measured_ambient = 28.0    # °C
    measured_irradiance = 950.0  # W/m²
    measured_wind = 0.5  # m/s

    noct = calculator.calculate_noct_from_measurements(
        measured_cell_temp,
        measured_ambient,
        measured_irradiance,
        measured_wind
    )

    print(f"Field measurement conditions:")
    print(f"  Cell temperature:    {measured_cell_temp}°C")
    print(f"  Ambient temperature: {measured_ambient}°C")
    print(f"  Irradiance:          {measured_irradiance} W/m²")
    print(f"  Wind speed:          {measured_wind} m/s")
    print(f"\nCalculated NOCT: {noct:.1f}°C")

    # Validate NOCT
    is_valid, warnings = calculator.validate_noct_measurement(noct, 'crystalline_silicon')
    print(f"NOCT Validation: {'✓ PASS' if is_valid else '⚠ WARNINGS'}")
    for warning in warnings:
        print(f"  ⚠ {warning}")

    # Operating temperature prediction
    print("\n2. Predict Operating Temperature:")
    print("-" * 70)

    thermal_params = ThermalParameters(noct=45.0)

    conditions = [
        (25, 1000, 1.0, "STC-like conditions"),
        (35, 1000, 2.0, "Hot day, good wind"),
        (40, 1200, 0.5, "Very hot, low wind"),
        (15, 800, 1.5, "Cool day")
    ]

    for T_amb, G, wind, description in conditions:
        T_cell = calculator.calculate_operating_temperature(
            thermal_params, T_amb, G, wind
        )
        print(f"  {description:25s}: T_cell = {T_cell:.1f}°C "
              f"(T_amb={T_amb}°C, G={G}W/m², wind={wind}m/s)")

    # Power prediction at operating conditions
    print("\n3. Power at Operating Conditions:")
    print("-" * 70)

    rated_power = 300.0  # W at STC
    temp_coeff_power = -0.40  # %/°C

    power_results = calculator.predict_power_at_operating_conditions(
        rated_power,
        thermal_params,
        temp_coeff_power,
        {
            'ambient_temperature': 35.0,
            'irradiance': 1000.0,
            'wind_speed': 2.0
        }
    )

    print(f"Rated power (STC):      {rated_power:.1f} W")
    print(f"Operating power:        {power_results['power_operating']:.1f} W")
    print(f"Cell temperature:       {power_results['cell_temperature']:.1f}°C")
    print(f"Temperature loss:       {power_results['power_loss_temperature']:.1f}%")
    print(f"Irradiance factor:      {power_results['irradiance_factor']:.3f}")

    # Thermal characteristics
    print("\n4. Thermal Characteristics:")
    print("-" * 70)

    ross_coeff = calculator.calculate_ross_coefficient(thermal_params)
    heat_loss = calculator.calculate_heat_loss_coefficient(thermal_params)
    time_const = calculator.estimate_thermal_time_constant(thermal_params)

    print(f"Ross coefficient (k):       {ross_coeff:.4f} °C·m²/W")
    print(f"Heat loss coefficient (UL): {heat_loss:.1f} W/(m²·K)")
    print(f"Thermal time constant (τ):  {time_const:.1f} s ({time_const/60:.1f} min)")

    # Mounting corrections
    print("\n5. Mounting Type Effects:")
    print("-" * 70)

    mounting_types = ['open_rack', 'close_roof', 'integrated', 'ground']

    for mounting in mounting_types:
        factor = calculator.calculate_mounting_correction(mounting)
        T_cell = calculator.calculate_operating_temperature(
            thermal_params, 25.0, 800.0, 1.0, factor
        )
        print(f"  {mounting:15s}: correction={factor:.2f}, T_cell={T_cell:.1f}°C @ NOCT conditions")


def example_4_comparison():
    """Example 4: Before/After comparison (e.g., stress test)."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Before/After Stress Test Comparison")
    print("=" * 70)

    analyzer = IVCurveAnalyzer()

    # Initial measurement
    iv_before = generate_sample_iv_curve(
        isc=8.5,
        voc=40.0,
        temperature=25.0,
        irradiance=1000.0
    )

    # After stress test (simulated degradation)
    iv_after = generate_sample_iv_curve(
        isc=8.4,  # -1.2% Isc degradation
        voc=39.7,  # -0.75% Voc degradation
        temperature=25.0,
        irradiance=1000.0
    )

    params_before = analyzer.calculate_parameters(iv_before)
    params_after = analyzer.calculate_parameters(iv_after)

    print("\nInitial Performance:")
    print(f"  Pmax: {params_before['Pmax']:.2f} W")
    print(f"  Voc:  {params_before['Voc']:.2f} V")
    print(f"  Isc:  {params_before['Isc']:.2f} A")
    print(f"  FF:   {params_before['FF']:.4f}")

    print("\nAfter Stress Test (1000h Damp Heat):")
    print(f"  Pmax: {params_after['Pmax']:.2f} W")
    print(f"  Voc:  {params_after['Voc']:.2f} V")
    print(f"  Isc:  {params_after['Isc']:.2f} A")
    print(f"  FF:   {params_after['FF']:.4f}")

    print("\nDegradation Analysis:")
    print(f"  ΔPmax: {(params_before['Pmax'] - params_after['Pmax']):.2f} W "
          f"({(1 - params_after['Pmax']/params_before['Pmax'])*100:+.2f}%)")
    print(f"  ΔVoc:  {(params_before['Voc'] - params_after['Voc']):.2f} V "
          f"({(1 - params_after['Voc']/params_before['Voc'])*100:+.2f}%)")
    print(f"  ΔIsc:  {(params_before['Isc'] - params_after['Isc']):.2f} A "
          f"({(1 - params_after['Isc']/params_before['Isc'])*100:+.2f}%)")
    print(f"  ΔFF:   {(params_before['FF'] - params_after['FF']):.4f} "
          f"({(1 - params_after['FF']/params_before['FF'])*100:+.2f}%)")

    # IEC 61215 pass/fail criteria: <5% power degradation
    power_degradation = (1 - params_after['Pmax'] / params_before['Pmax']) * 100

    print(f"\nIEC 61215 Qualification:")
    if power_degradation < 5.0:
        print(f"  ✓ PASS - Power degradation {power_degradation:.2f}% < 5%")
    else:
        print(f"  ✗ FAIL - Power degradation {power_degradation:.2f}% ≥ 5%")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print(" I-V CURVE ANALYSIS SYSTEM - COMPREHENSIVE EXAMPLES")
    print(" IEC 60904-1:2020 Compliant Implementation")
    print("=" * 70)

    try:
        example_1_basic_analysis()
        example_2_stc_translation()
        example_3_noct_analysis()
        example_4_comparison()

        print("\n" + "=" * 70)
        print(" All examples completed successfully! ✓")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. Review the generated plots (if matplotlib is available)")
        print("  2. Check src/tests/iv_curve/README.md for detailed documentation")
        print("  3. Explore the API reference for advanced usage")
        print("  4. Run unit tests: pytest src/tests/iv_curve/")
        print("\n")

    except Exception as e:
        print(f"\n✗ Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
