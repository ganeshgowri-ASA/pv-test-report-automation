#!/usr/bin/env python3
"""ISO 17025 Measurement Uncertainty Example.

This example demonstrates a complete measurement uncertainty analysis
for a calibration laboratory following ISO/IEC 17025:2017 requirements.

Scenario: Calibration of a PV module voltage measurement system
"""

from equipment.spc import SPCAnalyzer
from equipment.models import DistributionType
import numpy as np


def main():
    """Run ISO 17025 compliant uncertainty analysis."""
    print("=" * 80)
    print("ISO/IEC 17025:2017 - Measurement Uncertainty Analysis")
    print("PV Module Voltage Calibration Example")
    print("=" * 80)
    print()

    spc = SPCAnalyzer()

    # Measurement scenario
    print("MEASUREMENT SCENARIO")
    print("-" * 80)
    print("Item Under Test:     PV Module Voltage Measurement System")
    print("Measurand:           DC Voltage")
    print("Nominal Value:       100.0 V")
    print("Test Method:         Direct comparison with calibrated reference")
    print("Reference Standard:  Precision DC voltage calibrator")
    print()

    # Step 1: Collect repeated measurements (Type A uncertainty)
    print("STEP 1: REPEATED MEASUREMENTS")
    print("-" * 80)

    # Simulate 10 repeated measurements
    np.random.seed(42)
    measurements = [
        100.15, 100.12, 100.18, 100.10, 100.14,
        100.16, 100.11, 100.13, 100.17, 100.12
    ]

    print("Repeated measurements (n=10):")
    for i, m in enumerate(measurements, 1):
        print(f"  {i:2d}. {m:.2f} V")

    mean = np.mean(measurements)
    std = np.std(measurements, ddof=1)
    print(f"\nMean:              {mean:.4f} V")
    print(f"Std. Deviation:    {std:.4f} V")
    print()

    # Step 2: Identify and quantify Type B uncertainty sources
    print("STEP 2: TYPE B UNCERTAINTY SOURCES")
    print("-" * 80)

    type_b_sources = []

    # Source 1: Reference standard calibration uncertainty
    print("1. Reference Standard Calibration")
    print("   Uncertainty from calibration certificate: ±0.15 V (k=2)")
    print("   Distribution: Normal")
    u_ref = spc.calculate_type_b_uncertainty(
        half_width=0.15,
        distribution=DistributionType.NORMAL,  # k=2 normal
        name="Reference Standard Calibration",
        sensitivity_coefficient=1.0,
    )
    type_b_sources.append(u_ref)
    print(f"   Standard uncertainty: {u_ref.value:.6f} V")
    print()

    # Source 2: Reference standard drift
    print("2. Reference Standard Drift")
    print("   Maximum drift since last calibration: ±0.05 V")
    print("   Distribution: Rectangular (uniform)")
    u_drift = spc.calculate_type_b_uncertainty(
        half_width=0.05,
        distribution=DistributionType.RECTANGULAR,
        name="Reference Standard Drift",
        sensitivity_coefficient=1.0,
    )
    type_b_sources.append(u_drift)
    print(f"   Standard uncertainty: {u_drift.value:.6f} V")
    print()

    # Source 3: Resolution of measurement system
    print("3. Digital Multimeter Resolution")
    print("   Resolution: 0.01 V")
    print("   Half-width: ±0.005 V")
    print("   Distribution: Rectangular")
    u_resolution = spc.calculate_type_b_uncertainty(
        half_width=0.005,
        distribution=DistributionType.RECTANGULAR,
        name="DMM Resolution",
        sensitivity_coefficient=1.0,
    )
    type_b_sources.append(u_resolution)
    print(f"   Standard uncertainty: {u_resolution.value:.6f} V")
    print()

    # Source 4: Temperature effect
    print("4. Temperature Effect")
    print("   Temperature variation: ±2°C")
    print("   Temperature coefficient: 0.01 V/°C")
    print("   Maximum variation: ±0.02 V")
    print("   Distribution: Rectangular")
    u_temp = spc.calculate_type_b_uncertainty(
        half_width=0.02,
        distribution=DistributionType.RECTANGULAR,
        name="Temperature Effect",
        sensitivity_coefficient=1.0,
    )
    type_b_sources.append(u_temp)
    print(f"   Standard uncertainty: {u_temp.value:.6f} V")
    print()

    # Source 5: Loading effect
    print("5. Loading Effect")
    print("   Estimated maximum effect: ±0.03 V")
    print("   Distribution: Triangular (most likely zero)")
    u_loading = spc.calculate_type_b_uncertainty(
        half_width=0.03,
        distribution=DistributionType.TRIANGULAR,
        name="Loading Effect",
        sensitivity_coefficient=1.0,
    )
    type_b_sources.append(u_loading)
    print(f"   Standard uncertainty: {u_loading.value:.6f} V")
    print()

    # Step 3: Calculate combined uncertainty budget
    print("STEP 3: UNCERTAINTY BUDGET")
    print("-" * 80)

    budget = spc.calculate_uncertainty(
        measurements=measurements,
        additional_sources=type_b_sources,
        measurement_id=1,
        confidence_level=95.45,  # k≈2 for ~95%
    )

    # Display detailed uncertainty budget table
    print(f"{'Source':<35} {'Type':<8} {'u(x_i)':<12} {'ν_i':<8} {'u_i(y)':<12} {'u_i²(y)':<12}")
    print("-" * 80)

    total_variance = 0.0
    for source in budget.sources:
        contrib = source.contribution
        variance_contrib = source.variance_contribution
        total_variance += variance_contrib

        dof_str = f"{source.degrees_of_freedom:.0f}" if source.degrees_of_freedom else "∞"

        print(
            f"{source.name:<35} "
            f"{source.uncertainty_type.value:<8} "
            f"{source.value:<12.6f} "
            f"{dof_str:<8} "
            f"{contrib:<12.6f} "
            f"{variance_contrib:<12.6f}"
        )

    print("-" * 80)
    print(f"{'Combined Standard Uncertainty u_c(y):':<59} {budget.combined_uncertainty:.6f}")
    print()

    # Step 4: Effective degrees of freedom
    print("STEP 4: EFFECTIVE DEGREES OF FREEDOM")
    print("-" * 80)
    print("Welch-Satterthwaite formula:")

    if budget.effective_degrees_of_freedom:
        print(f"ν_eff = {budget.effective_degrees_of_freedom:.1f}")
    else:
        print("ν_eff = ∞ (infinite)")
    print()

    # Step 5: Coverage factor and expanded uncertainty
    print("STEP 5: EXPANDED UNCERTAINTY")
    print("-" * 80)
    print(f"Confidence Level:       {budget.confidence_level:.2f}%")
    print(f"Coverage Factor k:      {budget.coverage_factor:.2f}")
    print(f"Expanded Uncertainty U: {budget.expanded_uncertainty:.6f} V")
    print()

    # Step 6: Report the result
    print("STEP 6: REPORTED RESULT")
    print("-" * 80)
    print(f"Measured Voltage: {mean:.2f} V ± {budget.expanded_uncertainty:.2f} V")
    print(f"Coverage Factor:  k = {budget.coverage_factor:.0f}")
    print(f"Confidence Level: ~{budget.confidence_level:.0f}%")
    print()
    print("The reported expanded uncertainty is based on a combined standard")
    print("uncertainty multiplied by a coverage factor k=2, providing a level")
    print("of confidence of approximately 95%.")
    print()

    # Additional analysis: Identify dominant sources
    print("UNCERTAINTY CONTRIBUTION ANALYSIS")
    print("-" * 80)
    print(f"{'Source':<35} {'Contribution %':<15}")
    print("-" * 80)

    total_variance = sum(s.variance_contribution for s in budget.sources)
    contributions = []
    for source in budget.sources:
        percentage = (source.variance_contribution / total_variance) * 100
        contributions.append((source.name, percentage))

    # Sort by contribution (descending)
    contributions.sort(key=lambda x: x[1], reverse=True)

    for name, percentage in contributions:
        bar = "█" * int(percentage / 2)
        print(f"{name:<35} {percentage:>6.2f}% {bar}")

    print()


if __name__ == "__main__":
    main()
