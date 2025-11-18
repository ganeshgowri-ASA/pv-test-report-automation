#!/usr/bin/env python3
"""SPC control charts example.

This example demonstrates how to create X-bar and R control charts
and perform process capability analysis.
"""

import numpy as np
from equipment.spc import SPCAnalyzer


def main():
    """Run SPC control charts example."""
    print("=" * 70)
    print("Statistical Process Control - Control Charts Example")
    print("=" * 70)
    print()

    # Initialize SPC Analyzer
    spc = SPCAnalyzer()

    # Example: Solar panel voltage measurements
    # 20 subgroups, each with 5 measurements
    np.random.seed(42)
    n_subgroups = 20
    subgroup_size = 5
    target_voltage = 100.0  # Target voltage in V
    process_std = 0.5  # Process standard deviation

    # Generate process data (normally distributed)
    data = []
    for i in range(n_subgroups):
        # Add slight process shift at subgroup 15 for demonstration
        if i >= 15:
            mean = target_voltage + 0.3  # Small shift
        else:
            mean = target_voltage

        subgroup = np.random.normal(mean, process_std, subgroup_size)
        data.append(subgroup.tolist())

    print(f"Process Data: {n_subgroups} subgroups of {subgroup_size} measurements")
    print()

    # Calculate X-bar and R control limits
    xbar_limits, r_limits = spc.calculate_xbar_r_limits(data)

    print("X-BAR CHART CONTROL LIMITS")
    print("-" * 70)
    print(f"Center Line (X-double-bar): {xbar_limits.center_line:.4f} V")
    print(f"Upper Control Limit (UCL):  {xbar_limits.upper_control_limit:.4f} V")
    print(f"Lower Control Limit (LCL):  {xbar_limits.lower_control_limit:.4f} V")
    print(f"Upper Warning Limit:        {xbar_limits.upper_warning_limit:.4f} V")
    print(f"Lower Warning Limit:        {xbar_limits.lower_warning_limit:.4f} V")
    print()

    print("R CHART CONTROL LIMITS")
    print("-" * 70)
    print(f"Center Line (R-bar):        {r_limits.center_line:.4f} V")
    print(f"Upper Control Limit (UCL):  {r_limits.upper_control_limit:.4f} V")
    print(f"Lower Control Limit (LCL):  {r_limits.lower_control_limit:.4f} V")
    print()

    # Perform complete process analysis with specification limits
    usl = 102.0  # Upper Specification Limit
    lsl = 98.0   # Lower Specification Limit

    result = spc.analyze_process(
        data=data,
        usl=usl,
        lsl=lsl,
        target=target_voltage,
        use_s_chart=False,
    )

    # Display process capability indices
    print("PROCESS CAPABILITY ANALYSIS")
    print("-" * 70)
    print(f"Specification Limits: LSL = {lsl:.1f} V, USL = {usl:.1f} V")
    print(f"Target:               {target_voltage:.1f} V")
    print()

    if result.capability:
        print("Capability Indices:")
        print(f"  Cp  (Potential Capability):  {result.capability.cp:.3f}")
        print(f"  Cpk (Actual Capability):      {result.capability.cpk:.3f}")
        print(f"  Pp  (Overall Performance):    {result.capability.pp:.3f}")
        print(f"  Ppk (Overall Performance):    {result.capability.ppk:.3f}")
        print(f"  Cpm (Taguchi Index):          {result.capability.cpm:.3f}")
        print()

        # Interpret capability
        cpk = result.capability.cpk
        if cpk >= 1.33:
            status = "CAPABLE (Cpk ≥ 1.33)"
        elif cpk >= 1.00:
            status = "MARGINALLY CAPABLE (1.00 ≤ Cpk < 1.33)"
        else:
            status = "NOT CAPABLE (Cpk < 1.00)"

        print(f"Process Status: {status}")
        print()

    # Display control status
    print("CONTROL CHART ANALYSIS")
    print("-" * 70)
    if result.in_control:
        print("Status: Process is IN CONTROL ✓")
    else:
        print("Status: Process is OUT OF CONTROL ✗")
        print()
        print("Out-of-Control Points:", result.out_of_control_points)
        print()
        print("Violations:")
        for violation in result.violations:
            print(f"  - {violation}")

    print()

    # Display subgroup means for visualization reference
    print("SUBGROUP MEANS")
    print("-" * 70)
    subgroup_means = [np.mean(subgroup) for subgroup in data]
    for i, mean in enumerate(subgroup_means, 1):
        marker = ""
        if i - 1 in result.out_of_control_points:
            marker = " ← OUT OF CONTROL"
        print(f"Subgroup {i:2d}: {mean:.4f} V{marker}")

    print()


if __name__ == "__main__":
    main()
