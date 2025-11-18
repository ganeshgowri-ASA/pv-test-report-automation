"""Statistical Process Control and Measurement Uncertainty Analysis.

This module implements SPC control charts, capability indices, and
measurement uncertainty calculations following GUM and ISO 17025 standards.
"""

from typing import List, Optional, Tuple, Union
import numpy as np
from scipy import stats
from equipment.models import (
    UncertaintySource,
    UncertaintyBudget,
    UncertaintyType,
    DistributionType,
    ControlLimits,
    CapabilityIndices,
    SPCResult,
)


class SPCAnalyzer:
    """Statistical Process Control and Uncertainty Analyzer.

    This class provides methods for:
    - Control charts (X-bar, R, S charts)
    - Process capability indices (Cp, Cpk, Pp, Ppk)
    - Measurement uncertainty per GUM
    - Type A and Type B uncertainty evaluation
    - Combined and expanded uncertainty
    """

    # Control chart constants for different sample sizes
    # Source: Montgomery, D. C. (2009). Statistical Quality Control
    CONTROL_CHART_CONSTANTS = {
        # n: (A2, D3, D4, A3, B3, B4, d2, c4)
        2: (1.880, 0.000, 3.267, 2.659, 0.000, 3.267, 1.128, 0.7979),
        3: (1.023, 0.000, 2.574, 1.954, 0.000, 2.568, 1.693, 0.8862),
        4: (0.729, 0.000, 2.282, 1.628, 0.000, 2.266, 2.059, 0.9213),
        5: (0.577, 0.000, 2.114, 1.427, 0.000, 2.089, 2.326, 0.9400),
        6: (0.483, 0.000, 2.004, 1.287, 0.030, 1.970, 2.534, 0.9515),
        7: (0.419, 0.076, 1.924, 1.182, 0.118, 1.882, 2.704, 0.9594),
        8: (0.373, 0.136, 1.864, 1.099, 0.185, 1.815, 2.847, 0.9650),
        9: (0.337, 0.184, 1.816, 1.032, 0.239, 1.761, 2.970, 0.9693),
        10: (0.308, 0.223, 1.777, 0.975, 0.284, 1.716, 3.078, 0.9727),
        11: (0.285, 0.256, 1.744, 0.927, 0.321, 1.679, 3.173, 0.9754),
        12: (0.266, 0.283, 1.717, 0.886, 0.354, 1.646, 3.258, 0.9776),
        13: (0.249, 0.307, 1.693, 0.850, 0.382, 1.618, 3.336, 0.9794),
        14: (0.235, 0.328, 1.672, 0.817, 0.406, 1.594, 3.407, 0.9810),
        15: (0.223, 0.347, 1.653, 0.789, 0.428, 1.572, 3.472, 0.9823),
        16: (0.212, 0.363, 1.637, 0.763, 0.448, 1.552, 3.532, 0.9835),
        17: (0.203, 0.378, 1.622, 0.739, 0.466, 1.534, 3.588, 0.9845),
        18: (0.194, 0.391, 1.608, 0.718, 0.482, 1.518, 3.640, 0.9854),
        19: (0.187, 0.403, 1.597, 0.698, 0.497, 1.503, 3.689, 0.9862),
        20: (0.180, 0.415, 1.585, 0.680, 0.510, 1.490, 3.735, 0.9869),
        21: (0.173, 0.425, 1.575, 0.663, 0.523, 1.477, 3.778, 0.9876),
        22: (0.167, 0.434, 1.566, 0.647, 0.534, 1.466, 3.819, 0.9882),
        23: (0.162, 0.443, 1.557, 0.633, 0.545, 1.455, 3.858, 0.9887),
        24: (0.157, 0.451, 1.548, 0.619, 0.555, 1.445, 3.895, 0.9892),
        25: (0.153, 0.459, 1.541, 0.606, 0.565, 1.435, 3.931, 0.9896),
    }

    def __init__(self, alpha: float = 0.0027) -> None:
        """Initialize SPC Analyzer.

        Args:
            alpha: Significance level for control limits (default 0.0027 for 3-sigma)
        """
        self.alpha = alpha

    def calculate_xbar_r_limits(
        self,
        data: Union[np.ndarray, List[List[float]]],
    ) -> Tuple[ControlLimits, ControlLimits]:
        """Calculate X-bar and R chart control limits.

        Args:
            data: 2D array where each row is a subgroup of measurements

        Returns:
            Tuple of (xbar_limits, r_limits)
        """
        data_array = np.array(data)
        if data_array.ndim != 2:
            raise ValueError("Data must be 2-dimensional (subgroups x measurements)")

        n_subgroups, subgroup_size = data_array.shape

        if subgroup_size < 2 or subgroup_size > 25:
            raise ValueError("Subgroup size must be between 2 and 25")

        # Get control chart constants
        A2, D3, D4, _, _, _, d2, _ = self.CONTROL_CHART_CONSTANTS[subgroup_size]

        # Calculate subgroup means and ranges
        xbar = np.mean(data_array, axis=1)
        r = np.ptp(data_array, axis=1)  # Range = max - min

        # Grand mean and average range
        xbar_bar = np.mean(xbar)
        r_bar = np.mean(r)

        # X-bar chart limits
        xbar_ucl = xbar_bar + A2 * r_bar
        xbar_lcl = xbar_bar - A2 * r_bar
        xbar_uwl = xbar_bar + (2/3) * A2 * r_bar
        xbar_lwl = xbar_bar - (2/3) * A2 * r_bar

        xbar_limits = ControlLimits(
            center_line=xbar_bar,
            upper_control_limit=xbar_ucl,
            lower_control_limit=xbar_lcl,
            upper_warning_limit=xbar_uwl,
            lower_warning_limit=xbar_lwl,
        )

        # R chart limits
        r_ucl = D4 * r_bar
        r_lcl = D3 * r_bar
        r_uwl = r_bar + (2/3) * (D4 - 1) * r_bar
        r_lwl = max(0, r_bar - (2/3) * (1 - D3) * r_bar)

        r_limits = ControlLimits(
            center_line=r_bar,
            upper_control_limit=r_ucl,
            lower_control_limit=r_lcl,
            upper_warning_limit=r_uwl,
            lower_warning_limit=r_lwl,
        )

        return xbar_limits, r_limits

    def calculate_xbar_s_limits(
        self,
        data: Union[np.ndarray, List[List[float]]],
    ) -> Tuple[ControlLimits, ControlLimits]:
        """Calculate X-bar and S (standard deviation) chart control limits.

        Args:
            data: 2D array where each row is a subgroup of measurements

        Returns:
            Tuple of (xbar_limits, s_limits)
        """
        data_array = np.array(data)
        if data_array.ndim != 2:
            raise ValueError("Data must be 2-dimensional (subgroups x measurements)")

        n_subgroups, subgroup_size = data_array.shape

        if subgroup_size < 2 or subgroup_size > 25:
            raise ValueError("Subgroup size must be between 2 and 25")

        # Get control chart constants
        _, _, _, A3, B3, B4, _, c4 = self.CONTROL_CHART_CONSTANTS[subgroup_size]

        # Calculate subgroup means and standard deviations
        xbar = np.mean(data_array, axis=1)
        s = np.std(data_array, axis=1, ddof=1)

        # Grand mean and average standard deviation
        xbar_bar = np.mean(xbar)
        s_bar = np.mean(s)

        # X-bar chart limits
        xbar_ucl = xbar_bar + A3 * s_bar
        xbar_lcl = xbar_bar - A3 * s_bar
        xbar_uwl = xbar_bar + (2/3) * A3 * s_bar
        xbar_lwl = xbar_bar - (2/3) * A3 * s_bar

        xbar_limits = ControlLimits(
            center_line=xbar_bar,
            upper_control_limit=xbar_ucl,
            lower_control_limit=xbar_lcl,
            upper_warning_limit=xbar_uwl,
            lower_warning_limit=xbar_lwl,
        )

        # S chart limits
        s_ucl = B4 * s_bar
        s_lcl = B3 * s_bar
        s_uwl = s_bar + (2/3) * (B4 - 1) * s_bar
        s_lwl = max(0, s_bar - (2/3) * (1 - B3) * s_bar)

        s_limits = ControlLimits(
            center_line=s_bar,
            upper_control_limit=s_ucl,
            lower_control_limit=s_lcl,
            upper_warning_limit=s_uwl,
            lower_warning_limit=s_lwl,
        )

        return xbar_limits, s_limits

    def calculate_capability_indices(
        self,
        data: Union[np.ndarray, List[float]],
        usl: Optional[float] = None,
        lsl: Optional[float] = None,
        target: Optional[float] = None,
        use_overall_std: bool = False,
    ) -> CapabilityIndices:
        """Calculate process capability indices.

        Args:
            data: Process measurements (1D array or list)
            usl: Upper specification limit
            lsl: Lower specification limit
            target: Target value (default is midpoint of USL and LSL)
            use_overall_std: Use overall std for Pp/Ppk instead of within-subgroup

        Returns:
            CapabilityIndices object with Cp, Cpk, Pp, Ppk, Cpm
        """
        data_array = np.array(data).flatten()
        mean = np.mean(data_array)
        std_overall = np.std(data_array, ddof=1)

        # Within-subgroup standard deviation estimate
        # Using moving range for individual measurements
        if len(data_array) > 1:
            moving_ranges = np.abs(np.diff(data_array))
            std_within = np.mean(moving_ranges) / 1.128  # d2 for n=2
        else:
            std_within = std_overall

        cp = None
        cpk = None
        pp = None
        ppk = None
        cpm = None

        # Calculate Cp and Cpk (short-term capability using within-subgroup variation)
        if usl is not None and lsl is not None and std_within > 0:
            cp = (usl - lsl) / (6 * std_within)

            cpu = (usl - mean) / (3 * std_within)
            cpl = (mean - lsl) / (3 * std_within)
            cpk = min(cpu, cpl)

        # Calculate Pp and Ppk (overall performance using overall variation)
        if usl is not None and lsl is not None and std_overall > 0:
            pp = (usl - lsl) / (6 * std_overall)

            ppu = (usl - mean) / (3 * std_overall)
            ppl = (mean - lsl) / (3 * std_overall)
            ppk = min(ppu, ppl)

        # Calculate Cpm (Taguchi index)
        if usl is not None and lsl is not None and std_overall > 0:
            if target is None:
                target = (usl + lsl) / 2

            tau_squared = std_overall**2 + (mean - target)**2
            cpm = (usl - lsl) / (6 * np.sqrt(tau_squared))

        return CapabilityIndices(
            cp=cp,
            cpk=cpk,
            pp=pp,
            ppk=ppk,
            cpm=cpm,
        )

    def check_control_rules(
        self,
        values: np.ndarray,
        limits: ControlLimits,
    ) -> Tuple[bool, List[int], List[str]]:
        """Check Western Electric control rules.

        Args:
            values: Data points to check
            limits: Control limits

        Returns:
            Tuple of (in_control, out_of_control_indices, violations)
        """
        in_control = True
        out_of_control_points = []
        violations = []

        cl = limits.center_line
        ucl = limits.upper_control_limit
        lcl = limits.lower_control_limit
        uwl = limits.upper_warning_limit if limits.upper_warning_limit else cl + (2/3) * (ucl - cl)
        lwl = limits.lower_warning_limit if limits.lower_warning_limit else cl - (2/3) * (cl - lcl)

        # Rule 1: Any point beyond control limits
        beyond_limits = np.where((values > ucl) | (values < lcl))[0]
        if len(beyond_limits) > 0:
            in_control = False
            out_of_control_points.extend(beyond_limits.tolist())
            violations.append(f"Rule 1: {len(beyond_limits)} point(s) beyond control limits")

        # Rule 2: 2 out of 3 consecutive points beyond 2-sigma (warning limits)
        for i in range(len(values) - 2):
            window = values[i:i+3]
            beyond_2sigma = np.sum((window > uwl) | (window < lwl))
            if beyond_2sigma >= 2:
                in_control = False
                out_of_control_points.extend(range(i, i+3))
                violations.append(f"Rule 2: 2 out of 3 points beyond 2-sigma at index {i}")

        # Rule 3: 4 out of 5 consecutive points beyond 1-sigma
        one_sigma_upper = cl + (ucl - cl) / 3
        one_sigma_lower = cl - (cl - lcl) / 3
        for i in range(len(values) - 4):
            window = values[i:i+5]
            beyond_1sigma = np.sum((window > one_sigma_upper) | (window < one_sigma_lower))
            if beyond_1sigma >= 4:
                in_control = False
                out_of_control_points.extend(range(i, i+5))
                violations.append(f"Rule 3: 4 out of 5 points beyond 1-sigma at index {i}")

        # Rule 4: 8 consecutive points on one side of center line
        for i in range(len(values) - 7):
            window = values[i:i+8]
            all_above = np.all(window > cl)
            all_below = np.all(window < cl)
            if all_above or all_below:
                in_control = False
                out_of_control_points.extend(range(i, i+8))
                violations.append(f"Rule 4: 8 consecutive points on one side at index {i}")

        # Remove duplicates
        out_of_control_points = sorted(list(set(out_of_control_points)))

        return in_control, out_of_control_points, violations

    def calculate_type_a_uncertainty(
        self,
        measurements: Union[np.ndarray, List[float]],
        name: str = "Repeatability (Type A)",
    ) -> UncertaintySource:
        """Calculate Type A (statistical) uncertainty.

        Args:
            measurements: Repeated measurements
            name: Name of the uncertainty source

        Returns:
            UncertaintySource with Type A uncertainty
        """
        data = np.array(measurements)
        n = len(data)

        if n < 2:
            raise ValueError("At least 2 measurements required for Type A uncertainty")

        # Standard uncertainty is standard error of the mean
        std = np.std(data, ddof=1)
        standard_uncertainty = std / np.sqrt(n)

        # Degrees of freedom
        dof = n - 1

        return UncertaintySource(
            name=name,
            value=standard_uncertainty,
            uncertainty_type=UncertaintyType.TYPE_A,
            distribution=DistributionType.NORMAL,
            sensitivity_coefficient=1.0,
            degrees_of_freedom=float(dof),
            notes=f"Based on {n} measurements, std={std:.6f}",
        )

    def calculate_type_b_uncertainty(
        self,
        half_width: float,
        distribution: DistributionType = DistributionType.RECTANGULAR,
        name: str = "Type B uncertainty",
        sensitivity_coefficient: float = 1.0,
        dof: Optional[float] = None,
    ) -> UncertaintySource:
        """Calculate Type B (non-statistical) uncertainty.

        Args:
            half_width: Half-width of the uncertainty interval (e.g., tolerance/2)
            distribution: Assumed probability distribution
            name: Name of the uncertainty source
            sensitivity_coefficient: Sensitivity coefficient
            dof: Degrees of freedom (infinite for Type B if not specified)

        Returns:
            UncertaintySource with Type B uncertainty
        """
        # Convert half-width to standard uncertainty based on distribution
        divisors = {
            DistributionType.NORMAL: 2.0,  # For k=2 coverage
            DistributionType.RECTANGULAR: np.sqrt(3),
            DistributionType.TRIANGULAR: np.sqrt(6),
            DistributionType.U_SHAPED: np.sqrt(2),
        }

        divisor = divisors.get(distribution, np.sqrt(3))
        standard_uncertainty = half_width / divisor

        # Type B uncertainties typically have infinite DoF unless otherwise specified
        if dof is None:
            dof = float('inf')

        return UncertaintySource(
            name=name,
            value=standard_uncertainty,
            uncertainty_type=UncertaintyType.TYPE_B,
            distribution=distribution,
            sensitivity_coefficient=sensitivity_coefficient,
            degrees_of_freedom=dof if np.isfinite(dof) else None,
            notes=f"Half-width={half_width}, distribution={distribution.value}",
        )

    def calculate_combined_uncertainty(
        self,
        sources: List[UncertaintySource],
    ) -> float:
        """Calculate combined standard uncertainty per GUM.

        Uses root-sum-of-squares (RSS) method assuming independent sources.

        Args:
            sources: List of uncertainty sources

        Returns:
            Combined standard uncertainty u_c
        """
        if not sources:
            return 0.0

        # Sum of variance contributions: u_c^2 = sum((c_i * u_i)^2)
        variance = sum(source.variance_contribution for source in sources)
        return np.sqrt(variance)

    def calculate_effective_dof(
        self,
        combined_uncertainty: float,
        sources: List[UncertaintySource],
    ) -> Optional[float]:
        """Calculate effective degrees of freedom using Welch-Satterthwaite formula.

        Args:
            combined_uncertainty: Combined standard uncertainty
            sources: List of uncertainty sources

        Returns:
            Effective degrees of freedom, or None if infinite
        """
        if combined_uncertainty == 0:
            return None

        numerator = combined_uncertainty ** 4
        denominator = 0.0

        for source in sources:
            if source.degrees_of_freedom is not None and np.isfinite(source.degrees_of_freedom):
                contribution = source.contribution ** 4
                denominator += contribution / source.degrees_of_freedom

        if denominator == 0:
            return None  # Infinite DoF

        eff_dof = numerator / denominator
        return eff_dof

    def calculate_coverage_factor(
        self,
        confidence_level: float = 95.0,
        degrees_of_freedom: Optional[float] = None,
    ) -> float:
        """Calculate coverage factor for expanded uncertainty.

        Args:
            confidence_level: Desired confidence level (%)
            degrees_of_freedom: Effective degrees of freedom

        Returns:
            Coverage factor k
        """
        alpha = 1 - (confidence_level / 100)

        # For infinite or very large DoF, use normal distribution
        if degrees_of_freedom is None or degrees_of_freedom > 1000:
            k = stats.norm.ppf(1 - alpha/2)
        else:
            # Use t-distribution for finite DoF
            k = stats.t.ppf(1 - alpha/2, df=degrees_of_freedom)

        return k

    def calculate_uncertainty(
        self,
        measurements: Optional[List[float]] = None,
        additional_sources: Optional[List[UncertaintySource]] = None,
        measurement_id: int = 1,
        coverage_factor: Optional[float] = None,
        confidence_level: float = 95.0,
    ) -> UncertaintyBudget:
        """Calculate complete uncertainty budget per GUM.

        Args:
            measurements: Repeated measurements for Type A uncertainty
            additional_sources: Additional Type B uncertainty sources
            measurement_id: Measurement identifier
            coverage_factor: Coverage factor k (if None, calculated from confidence level)
            confidence_level: Confidence level in percent (default 95%)

        Returns:
            Complete uncertainty budget
        """
        sources = []

        # Add Type A uncertainty from measurements
        if measurements and len(measurements) >= 2:
            type_a = self.calculate_type_a_uncertainty(measurements)
            sources.append(type_a)

        # Add additional Type B sources
        if additional_sources:
            sources.extend(additional_sources)

        if not sources:
            raise ValueError("No uncertainty sources provided")

        # Calculate combined uncertainty
        combined_uncertainty = self.calculate_combined_uncertainty(sources)

        # Calculate effective degrees of freedom
        eff_dof = self.calculate_effective_dof(combined_uncertainty, sources)

        # Calculate or use provided coverage factor
        if coverage_factor is None:
            coverage_factor = self.calculate_coverage_factor(confidence_level, eff_dof)

        # Calculate expanded uncertainty
        expanded_uncertainty = combined_uncertainty * coverage_factor

        return UncertaintyBudget(
            measurement_id=measurement_id,
            sources=sources,
            combined_uncertainty=combined_uncertainty,
            expanded_uncertainty=expanded_uncertainty,
            coverage_factor=coverage_factor,
            effective_degrees_of_freedom=eff_dof,
            confidence_level=confidence_level,
        )

    def analyze_process(
        self,
        data: Union[np.ndarray, List[List[float]]],
        usl: Optional[float] = None,
        lsl: Optional[float] = None,
        target: Optional[float] = None,
        use_s_chart: bool = False,
    ) -> SPCResult:
        """Perform complete SPC analysis on process data.

        Args:
            data: 2D array where each row is a subgroup
            usl: Upper specification limit
            lsl: Lower specification limit
            target: Target value
            use_s_chart: Use S chart instead of R chart

        Returns:
            Complete SPC analysis results
        """
        data_array = np.array(data)

        # Calculate control limits
        if use_s_chart:
            xbar_limits, s_limits = self.calculate_xbar_s_limits(data_array)
            r_limits = None
        else:
            xbar_limits, r_limits = self.calculate_xbar_r_limits(data_array)
            s_limits = None

        # Check control rules on subgroup means
        xbar_values = np.mean(data_array, axis=1)
        in_control, ooc_points, violations = self.check_control_rules(xbar_values, xbar_limits)

        # Calculate capability indices if specification limits provided
        capability = None
        if usl is not None or lsl is not None:
            all_data = data_array.flatten()
            capability = self.calculate_capability_indices(all_data, usl, lsl, target)

        return SPCResult(
            xbar_limits=xbar_limits,
            r_limits=r_limits,
            s_limits=s_limits,
            capability=capability,
            in_control=in_control,
            out_of_control_points=ooc_points,
            violations=violations,
            metadata={
                "n_subgroups": data_array.shape[0],
                "subgroup_size": data_array.shape[1],
                "chart_type": "X-bar & S" if use_s_chart else "X-bar & R",
            }
        )
