"""Data models for SPC and Measurement Uncertainty Analysis.

This module defines the core data structures for statistical process control
and uncertainty analysis following GUM (Guide to the Expression of Uncertainty
in Measurement) and ISO 17025 standards.
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel as PydanticBaseModel, Field, field_validator, model_validator, ConfigDict


class UncertaintyType(str, Enum):
    """Types of uncertainty evaluation per GUM."""
    TYPE_A = "type_a"  # Statistical evaluation
    TYPE_B = "type_b"  # Non-statistical evaluation


class DistributionType(str, Enum):
    """Probability distributions for Type B uncertainty."""
    NORMAL = "normal"
    RECTANGULAR = "rectangular"
    TRIANGULAR = "triangular"
    U_SHAPED = "u_shaped"


class BaseModel(PydanticBaseModel):
    """Base model with common configuration."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "examples": []
        }
    )


class UncertaintySource(BaseModel):
    """Individual uncertainty source in the uncertainty budget.

    Attributes:
        name: Name/description of the uncertainty source
        value: Standard uncertainty value (1 sigma)
        uncertainty_type: Type A (statistical) or Type B (other)
        distribution: Probability distribution for Type B
        sensitivity_coefficient: Sensitivity coefficient (default 1.0)
        degrees_of_freedom: Degrees of freedom for this source
        notes: Additional notes or references
    """

    name: str = Field(..., description="Name of uncertainty source")
    value: float = Field(..., gt=0, description="Standard uncertainty (1 sigma)")
    uncertainty_type: UncertaintyType = Field(..., description="Type A or Type B")
    distribution: DistributionType = Field(
        default=DistributionType.NORMAL,
        description="Probability distribution"
    )
    sensitivity_coefficient: float = Field(
        default=1.0,
        description="Sensitivity coefficient c_i"
    )
    degrees_of_freedom: Optional[float] = Field(
        default=None,
        ge=1,
        description="Degrees of freedom"
    )
    notes: Optional[str] = Field(default=None, description="Additional notes")

    @property
    def contribution(self) -> float:
        """Calculate contribution to combined uncertainty: c_i * u_i."""
        return abs(self.sensitivity_coefficient) * self.value

    @property
    def variance_contribution(self) -> float:
        """Calculate contribution to combined variance: (c_i * u_i)^2."""
        return self.contribution ** 2


class UncertaintyBudget(BaseModel):
    """Complete uncertainty budget for a measurement per GUM.

    Attributes:
        measurement_id: Unique identifier for the measurement
        sources: List of individual uncertainty sources
        combined_uncertainty: Combined standard uncertainty u_c
        expanded_uncertainty: Expanded uncertainty U (typically k=2)
        coverage_factor: Coverage factor k (default 2.0 for ~95% confidence)
        effective_degrees_of_freedom: Welch-Satterthwaite effective DoF
        confidence_level: Confidence level as percentage (e.g., 95.0)
    """

    measurement_id: int = Field(..., description="Measurement identifier")
    sources: List[UncertaintySource] = Field(
        default_factory=list,
        description="Individual uncertainty sources"
    )
    combined_uncertainty: float = Field(..., ge=0, description="Combined standard uncertainty u_c")
    expanded_uncertainty: float = Field(..., ge=0, description="Expanded uncertainty U")
    coverage_factor: float = Field(default=2.0, gt=0, description="Coverage factor k")
    effective_degrees_of_freedom: Optional[float] = Field(
        default=None,
        ge=1,
        description="Effective degrees of freedom (Welch-Satterthwaite)"
    )
    confidence_level: float = Field(
        default=95.0,
        ge=0,
        le=100,
        description="Confidence level (%)"
    )

    @model_validator(mode='after')
    def validate_expanded(self) -> 'UncertaintyBudget':
        """Validate that expanded uncertainty is calculated correctly."""
        expected = self.combined_uncertainty * self.coverage_factor
        if abs(self.expanded_uncertainty - expected) > 1e-9:
            raise ValueError(
                f"Expanded uncertainty {self.expanded_uncertainty} does not match "
                f"combined_uncertainty * coverage_factor = {expected}"
            )
        return self


class ControlLimits(BaseModel):
    """Control limits for SPC charts.

    Attributes:
        center_line: Center line (mean or median)
        upper_control_limit: Upper control limit (UCL)
        lower_control_limit: Lower control limit (LCL)
        upper_warning_limit: Upper warning limit (2 sigma)
        lower_warning_limit: Lower warning limit (2 sigma)
    """

    center_line: float = Field(..., description="Center line (CL)")
    upper_control_limit: float = Field(..., description="Upper control limit (UCL)")
    lower_control_limit: float = Field(..., description="Lower control limit (LCL)")
    upper_warning_limit: Optional[float] = Field(
        default=None,
        description="Upper warning limit (2σ)"
    )
    lower_warning_limit: Optional[float] = Field(
        default=None,
        description="Lower warning limit (2σ)"
    )


class CapabilityIndices(BaseModel):
    """Process capability indices.

    Attributes:
        cp: Process capability index Cp
        cpk: Process capability index Cpk
        pp: Process performance index Pp
        ppk: Process performance index Ppk
        cpm: Taguchi capability index Cpm
    """

    cp: Optional[float] = Field(default=None, ge=0, description="Capability index Cp")
    cpk: Optional[float] = Field(default=None, ge=0, description="Capability index Cpk")
    pp: Optional[float] = Field(default=None, ge=0, description="Performance index Pp")
    ppk: Optional[float] = Field(default=None, ge=0, description="Performance index Ppk")
    cpm: Optional[float] = Field(default=None, ge=0, description="Taguchi index Cpm")


class SPCResult(BaseModel):
    """Results from SPC analysis.

    Attributes:
        xbar_limits: Control limits for X-bar chart
        r_limits: Control limits for R chart
        s_limits: Control limits for S chart
        capability: Process capability indices
        in_control: Whether process is in statistical control
        out_of_control_points: Indices of out-of-control points
        violations: Description of control rule violations
    """

    xbar_limits: Optional[ControlLimits] = Field(
        default=None,
        description="X-bar chart control limits"
    )
    r_limits: Optional[ControlLimits] = Field(
        default=None,
        description="R chart control limits"
    )
    s_limits: Optional[ControlLimits] = Field(
        default=None,
        description="S chart control limits"
    )
    capability: Optional[CapabilityIndices] = Field(
        default=None,
        description="Process capability indices"
    )
    in_control: bool = Field(default=True, description="Process in control status")
    out_of_control_points: List[int] = Field(
        default_factory=list,
        description="Indices of out-of-control points"
    )
    violations: List[str] = Field(
        default_factory=list,
        description="Control rule violations"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
