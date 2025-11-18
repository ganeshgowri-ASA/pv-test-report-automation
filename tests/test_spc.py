"""Tests for SPC and Uncertainty Analysis."""

import pytest
import numpy as np
from equipment.spc import SPCAnalyzer
from equipment.models import (
    UncertaintyType,
    DistributionType,
    UncertaintySource,
    UncertaintyBudget,
)


class TestSPCAnalyzer:
    """Test suite for SPCAnalyzer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.spc = SPCAnalyzer()

    def test_xbar_r_limits_basic(self):
        """Test X-bar and R chart calculation with known data."""
        # Example data: 5 subgroups of 4 measurements each
        data = [
            [20.1, 20.3, 20.0, 20.2],
            [20.2, 20.4, 20.1, 20.3],
            [19.9, 20.1, 19.8, 20.0],
            [20.3, 20.5, 20.2, 20.4],
            [20.0, 20.2, 19.9, 20.1],
        ]

        xbar_limits, r_limits = self.spc.calculate_xbar_r_limits(data)

        # Verify structure
        assert xbar_limits.center_line > 0
        assert xbar_limits.upper_control_limit > xbar_limits.center_line
        assert xbar_limits.lower_control_limit < xbar_limits.center_line

        assert r_limits.center_line > 0
        assert r_limits.upper_control_limit > r_limits.center_line
        assert r_limits.lower_control_limit >= 0

    def test_xbar_s_limits_basic(self):
        """Test X-bar and S chart calculation."""
        data = [
            [100.0, 100.2, 99.8, 100.1],
            [99.9, 100.1, 100.0, 99.8],
            [100.2, 100.0, 100.1, 99.9],
        ]

        xbar_limits, s_limits = self.spc.calculate_xbar_s_limits(data)

        assert xbar_limits.center_line > 0
        assert s_limits.center_line > 0
        assert xbar_limits.upper_control_limit > xbar_limits.lower_control_limit

    def test_capability_indices(self):
        """Test process capability calculation."""
        # Normally distributed data around 100
        np.random.seed(42)
        data = np.random.normal(100, 1, 100)

        capability = self.spc.calculate_capability_indices(
            data=data,
            usl=103,
            lsl=97,
            target=100,
        )

        # With 6-sigma tolerance and sigma=1, Cp should be around 1.0
        assert capability.cp is not None
        assert 0.8 < capability.cp < 1.2

        assert capability.cpk is not None
        assert capability.pp is not None
        assert capability.ppk is not None
        assert capability.cpm is not None

    def test_capability_no_limits(self):
        """Test capability calculation without specification limits."""
        data = [100, 101, 99, 100, 102]

        capability = self.spc.calculate_capability_indices(data)

        assert capability.cp is None
        assert capability.cpk is None

    def test_type_a_uncertainty(self):
        """Test Type A uncertainty calculation."""
        measurements = [100.1, 100.2, 100.0, 99.9, 100.1]

        source = self.spc.calculate_type_a_uncertainty(measurements)

        assert source.uncertainty_type == UncertaintyType.TYPE_A
        assert source.value > 0
        assert source.degrees_of_freedom == 4  # n - 1
        assert source.distribution == DistributionType.NORMAL

    def test_type_a_insufficient_data(self):
        """Test Type A uncertainty with insufficient data."""
        with pytest.raises(ValueError, match="At least 2 measurements"):
            self.spc.calculate_type_a_uncertainty([100.0])

    def test_type_b_uncertainty_rectangular(self):
        """Test Type B uncertainty with rectangular distribution."""
        # ±0.5 tolerance with rectangular distribution
        source = self.spc.calculate_type_b_uncertainty(
            half_width=0.5,
            distribution=DistributionType.RECTANGULAR,
            name="Calibration tolerance",
        )

        assert source.uncertainty_type == UncertaintyType.TYPE_B
        assert source.distribution == DistributionType.RECTANGULAR
        # For rectangular: u = a/sqrt(3)
        expected = 0.5 / np.sqrt(3)
        assert abs(source.value - expected) < 1e-6

    def test_type_b_uncertainty_normal(self):
        """Test Type B uncertainty with normal distribution."""
        source = self.spc.calculate_type_b_uncertainty(
            half_width=2.0,  # ±2 at k=2
            distribution=DistributionType.NORMAL,
            name="Temperature effect",
        )

        # For normal at k=2: u = a/2
        expected = 2.0 / 2.0
        assert abs(source.value - expected) < 1e-6

    def test_type_b_uncertainty_triangular(self):
        """Test Type B uncertainty with triangular distribution."""
        source = self.spc.calculate_type_b_uncertainty(
            half_width=1.0,
            distribution=DistributionType.TRIANGULAR,
        )

        # For triangular: u = a/sqrt(6)
        expected = 1.0 / np.sqrt(6)
        assert abs(source.value - expected) < 1e-6

    def test_combined_uncertainty(self):
        """Test combined uncertainty calculation."""
        sources = [
            UncertaintySource(
                name="Source 1",
                value=0.1,
                uncertainty_type=UncertaintyType.TYPE_A,
                sensitivity_coefficient=1.0,
            ),
            UncertaintySource(
                name="Source 2",
                value=0.2,
                uncertainty_type=UncertaintyType.TYPE_B,
                distribution=DistributionType.RECTANGULAR,
                sensitivity_coefficient=1.0,
            ),
            UncertaintySource(
                name="Source 3",
                value=0.15,
                uncertainty_type=UncertaintyType.TYPE_B,
                distribution=DistributionType.NORMAL,
                sensitivity_coefficient=2.0,
            ),
        ]

        combined = self.spc.calculate_combined_uncertainty(sources)

        # u_c = sqrt((1*0.1)^2 + (1*0.2)^2 + (2*0.15)^2)
        expected = np.sqrt(0.1**2 + 0.2**2 + (2*0.15)**2)
        assert abs(combined - expected) < 1e-6

    def test_combined_uncertainty_empty(self):
        """Test combined uncertainty with no sources."""
        combined = self.spc.calculate_combined_uncertainty([])
        assert combined == 0.0

    def test_calculate_uncertainty_full(self):
        """Test complete uncertainty budget calculation."""
        measurements = [100.1, 100.2, 100.0, 99.9, 100.1]

        additional_sources = [
            self.spc.calculate_type_b_uncertainty(
                half_width=0.5,
                distribution=DistributionType.RECTANGULAR,
                name="Calibration",
            ),
            self.spc.calculate_type_b_uncertainty(
                half_width=0.1,
                distribution=DistributionType.NORMAL,
                name="Temperature",
            ),
        ]

        budget = self.spc.calculate_uncertainty(
            measurements=measurements,
            additional_sources=additional_sources,
            measurement_id=1,
            confidence_level=95.0,
        )

        assert budget.measurement_id == 1
        assert len(budget.sources) == 3  # 1 Type A + 2 Type B
        assert budget.combined_uncertainty > 0
        assert budget.expanded_uncertainty > budget.combined_uncertainty
        assert budget.coverage_factor > 0
        assert budget.confidence_level == 95.0

        # Verify expanded uncertainty relationship
        expected_expanded = budget.combined_uncertainty * budget.coverage_factor
        assert abs(budget.expanded_uncertainty - expected_expanded) < 1e-9

    def test_calculate_uncertainty_type_a_only(self):
        """Test uncertainty calculation with Type A only."""
        measurements = [100.1, 100.2, 100.0]

        budget = self.spc.calculate_uncertainty(
            measurements=measurements,
            measurement_id=2,
        )

        assert len(budget.sources) == 1
        assert budget.sources[0].uncertainty_type == UncertaintyType.TYPE_A

    def test_calculate_uncertainty_type_b_only(self):
        """Test uncertainty calculation with Type B only."""
        sources = [
            self.spc.calculate_type_b_uncertainty(
                half_width=1.0,
                distribution=DistributionType.RECTANGULAR,
                name="Resolution",
            ),
        ]

        budget = self.spc.calculate_uncertainty(
            additional_sources=sources,
            measurement_id=3,
        )

        assert len(budget.sources) == 1
        assert budget.sources[0].uncertainty_type == UncertaintyType.TYPE_B

    def test_calculate_uncertainty_custom_coverage_factor(self):
        """Test uncertainty with custom coverage factor."""
        measurements = [100.0, 100.1, 99.9]

        budget = self.spc.calculate_uncertainty(
            measurements=measurements,
            coverage_factor=3.0,  # 3-sigma instead of 2
        )

        assert budget.coverage_factor == 3.0
        expected_expanded = budget.combined_uncertainty * 3.0
        assert abs(budget.expanded_uncertainty - expected_expanded) < 1e-9

    def test_calculate_uncertainty_no_sources(self):
        """Test uncertainty calculation with no sources raises error."""
        with pytest.raises(ValueError, match="No uncertainty sources"):
            self.spc.calculate_uncertainty()

    def test_effective_dof_calculation(self):
        """Test Welch-Satterthwaite effective degrees of freedom."""
        sources = [
            UncertaintySource(
                name="Source 1",
                value=0.1,
                uncertainty_type=UncertaintyType.TYPE_A,
                sensitivity_coefficient=1.0,
                degrees_of_freedom=9.0,
            ),
            UncertaintySource(
                name="Source 2",
                value=0.2,
                uncertainty_type=UncertaintyType.TYPE_B,
                distribution=DistributionType.RECTANGULAR,
                sensitivity_coefficient=1.0,
                degrees_of_freedom=50.0,
            ),
        ]

        combined = self.spc.calculate_combined_uncertainty(sources)
        eff_dof = self.spc.calculate_effective_dof(combined, sources)

        assert eff_dof is not None
        assert eff_dof > 0

    def test_effective_dof_infinite(self):
        """Test effective DoF with infinite DoF sources."""
        sources = [
            UncertaintySource(
                name="Source 1",
                value=0.1,
                uncertainty_type=UncertaintyType.TYPE_B,
                distribution=DistributionType.RECTANGULAR,
                sensitivity_coefficient=1.0,
                # No DoF specified = infinite
            ),
        ]

        combined = self.spc.calculate_combined_uncertainty(sources)
        eff_dof = self.spc.calculate_effective_dof(combined, sources)

        assert eff_dof is None  # Infinite

    def test_coverage_factor_normal(self):
        """Test coverage factor for normal distribution (infinite DoF)."""
        k = self.spc.calculate_coverage_factor(confidence_level=95.0)

        # For 95% and normal distribution, k ≈ 1.96
        assert abs(k - 1.96) < 0.01

    def test_coverage_factor_t_distribution(self):
        """Test coverage factor for t-distribution (finite DoF)."""
        k = self.spc.calculate_coverage_factor(
            confidence_level=95.0,
            degrees_of_freedom=10.0,
        )

        # For 95% and 10 DoF, k ≈ 2.23
        assert k > 2.0
        assert k < 2.5

    def test_check_control_rules_in_control(self):
        """Test control rules with in-control process."""
        # Generate data near center line
        values = np.array([100.0, 100.1, 99.9, 100.0, 100.2, 99.8])

        from equipment.models import ControlLimits
        limits = ControlLimits(
            center_line=100.0,
            upper_control_limit=103.0,
            lower_control_limit=97.0,
        )

        in_control, ooc_points, violations = self.spc.check_control_rules(values, limits)

        assert in_control is True
        assert len(ooc_points) == 0
        assert len(violations) == 0

    def test_check_control_rules_beyond_limits(self):
        """Test control rules with points beyond limits."""
        values = np.array([100.0, 105.0, 99.0, 100.0])  # 105.0 beyond UCL

        from equipment.models import ControlLimits
        limits = ControlLimits(
            center_line=100.0,
            upper_control_limit=103.0,
            lower_control_limit=97.0,
        )

        in_control, ooc_points, violations = self.spc.check_control_rules(values, limits)

        assert in_control is False
        assert 1 in ooc_points  # Index of 105.0
        assert len(violations) > 0
        assert any("Rule 1" in v for v in violations)

    def test_analyze_process_complete(self):
        """Test complete process analysis."""
        # Generate controlled process data
        np.random.seed(42)
        data = []
        for _ in range(10):
            subgroup = np.random.normal(100, 0.5, 5)
            data.append(subgroup.tolist())

        result = self.spc.analyze_process(
            data=data,
            usl=102,
            lsl=98,
            target=100,
            use_s_chart=False,
        )

        assert result.xbar_limits is not None
        assert result.r_limits is not None
        assert result.s_limits is None  # Using R chart
        assert result.capability is not None
        assert isinstance(result.in_control, bool)
        assert result.metadata["chart_type"] == "X-bar & R"
        assert result.metadata["n_subgroups"] == 10
        assert result.metadata["subgroup_size"] == 5

    def test_analyze_process_with_s_chart(self):
        """Test process analysis with S chart."""
        data = [
            [100.0, 100.2, 99.8, 100.1],
            [99.9, 100.1, 100.0, 99.8],
            [100.2, 100.0, 100.1, 99.9],
        ]

        result = self.spc.analyze_process(
            data=data,
            use_s_chart=True,
        )

        assert result.xbar_limits is not None
        assert result.r_limits is None  # Using S chart
        assert result.s_limits is not None
        assert result.metadata["chart_type"] == "X-bar & S"

    def test_invalid_subgroup_size(self):
        """Test error handling for invalid subgroup size."""
        # Subgroup size of 1 (too small)
        data = [[100.0], [100.1], [99.9]]

        with pytest.raises(ValueError, match="between 2 and 25"):
            self.spc.calculate_xbar_r_limits(data)

    def test_invalid_data_shape(self):
        """Test error handling for invalid data shape."""
        # 1D data instead of 2D
        data = [100.0, 100.1, 99.9]

        with pytest.raises(ValueError, match="2-dimensional"):
            self.spc.calculate_xbar_r_limits(data)


class TestUncertaintyBudgetValidation:
    """Test validation of uncertainty budget models."""

    def test_uncertainty_source_validation(self):
        """Test UncertaintySource validation."""
        with pytest.raises(ValueError):
            # Negative uncertainty value
            UncertaintySource(
                name="Test",
                value=-0.1,
                uncertainty_type=UncertaintyType.TYPE_A,
            )

    def test_uncertainty_budget_validation(self):
        """Test UncertaintyBudget validation."""
        source = UncertaintySource(
            name="Test",
            value=0.1,
            uncertainty_type=UncertaintyType.TYPE_A,
        )

        # Valid budget
        budget = UncertaintyBudget(
            measurement_id=1,
            sources=[source],
            combined_uncertainty=0.1,
            expanded_uncertainty=0.2,
            coverage_factor=2.0,
        )

        assert budget.combined_uncertainty == 0.1
        assert budget.expanded_uncertainty == 0.2

    def test_uncertainty_budget_invalid_expanded(self):
        """Test validation of expanded uncertainty calculation."""
        source = UncertaintySource(
            name="Test",
            value=0.1,
            uncertainty_type=UncertaintyType.TYPE_A,
        )

        with pytest.raises(ValueError, match="does not match"):
            # Expanded uncertainty doesn't match combined * k
            UncertaintyBudget(
                measurement_id=1,
                sources=[source],
                combined_uncertainty=0.1,
                expanded_uncertainty=0.5,  # Should be 0.2
                coverage_factor=2.0,
            )


class TestExampleFromSpec:
    """Test the specific example from the specification."""

    def test_example_usage(self):
        """Test the example from the specification."""
        spc = SPCAnalyzer()
        result = spc.calculate_uncertainty(
            measurements=[100.1, 100.2, 100.0],
            coverage_factor=2.0,  # Explicitly set k=2
        )

        print(f"U (k=2): {result.expanded_uncertainty}")

        assert result.expanded_uncertainty > 0
        assert result.coverage_factor == 2.0
        assert len(result.sources) == 1
        assert result.sources[0].uncertainty_type == UncertaintyType.TYPE_A
