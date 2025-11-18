#!/usr/bin/env python3
"""Basic uncertainty calculation example.

This example demonstrates how to calculate measurement uncertainty
following GUM methodology with Type A and Type B uncertainty sources.
"""

from equipment.spc import SPCAnalyzer
from equipment.models import DistributionType


def main():
    """Run basic uncertainty calculation example."""
    print("=" * 70)
    print("Basic Uncertainty Calculation Example")
    print("Following GUM (Guide to the Expression of Uncertainty in Measurement)")
    print("=" * 70)
    print()

    # Initialize SPC Analyzer
    spc = SPCAnalyzer()

    # Example: Measuring a voltage with a digital multimeter
    # Multiple repeated measurements
    measurements = [100.1, 100.2, 100.0, 99.9, 100.1, 100.0, 100.2, 99.8, 100.1, 100.0]

    print("Measurements (V):", measurements)
    print()

    # Additional Type B uncertainty sources
    additional_sources = [
        # DMM calibration uncertainty (from calibration certificate)
        spc.calculate_type_b_uncertainty(
            half_width=0.5,  # ±0.5 V from certificate
            distribution=DistributionType.RECTANGULAR,
            name="DMM Calibration",
            sensitivity_coefficient=1.0,
        ),
        # Temperature effect (from manufacturer specifications)
        spc.calculate_type_b_uncertainty(
            half_width=0.1,  # ±0.1 V for temperature variation
            distribution=DistributionType.RECTANGULAR,
            name="Temperature Effect",
            sensitivity_coefficient=1.0,
        ),
        # Resolution (least significant digit)
        spc.calculate_type_b_uncertainty(
            half_width=0.05,  # ±0.05 V (half of 0.1 V resolution)
            distribution=DistributionType.RECTANGULAR,
            name="DMM Resolution",
            sensitivity_coefficient=1.0,
        ),
    ]

    # Calculate complete uncertainty budget
    budget = spc.calculate_uncertainty(
        measurements=measurements,
        additional_sources=additional_sources,
        measurement_id=1,
        confidence_level=95.0,
    )

    # Display results
    print("UNCERTAINTY BUDGET")
    print("-" * 70)
    print(f"{'Source':<30} {'Type':<10} {'u(x_i)':<12} {'c_i':<8} {'Contribution':<12}")
    print("-" * 70)

    for source in budget.sources:
        print(
            f"{source.name:<30} "
            f"{source.uncertainty_type.value:<10} "
            f"{source.value:<12.6f} "
            f"{source.sensitivity_coefficient:<8.2f} "
            f"{source.contribution:<12.6f}"
        )

    print("-" * 70)
    print(f"Combined Standard Uncertainty (u_c): {budget.combined_uncertainty:.6f} V")
    print(f"Coverage Factor (k):                 {budget.coverage_factor:.2f}")
    print(f"Effective Degrees of Freedom:        {budget.effective_degrees_of_freedom:.1f}")
    print(f"Expanded Uncertainty (U, k=2):       {budget.expanded_uncertainty:.6f} V")
    print(f"Confidence Level:                    {budget.confidence_level:.0f}%")
    print()

    # Calculate and display the final result
    mean_value = sum(measurements) / len(measurements)
    print("FINAL RESULT")
    print("-" * 70)
    print(f"Measured Value: {mean_value:.2f} V ± {budget.expanded_uncertainty:.2f} V (k={budget.coverage_factor:.0f})")
    print(f"or: ({mean_value - budget.expanded_uncertainty:.2f} to {mean_value + budget.expanded_uncertainty:.2f}) V")
    print()


if __name__ == "__main__":
    main()
