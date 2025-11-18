"""Equipment module for PV Test Report Automation.

This module provides Statistical Process Control (SPC) and
Measurement Uncertainty analysis following GUM and ISO 17025 standards.
"""

from equipment.models import (
    BaseModel,
    UncertaintySource,
    UncertaintyBudget,
    SPCResult,
    CapabilityIndices,
)
from equipment.spc import SPCAnalyzer

__version__ = "0.1.0"
__all__ = [
    "BaseModel",
    "UncertaintySource",
    "UncertaintyBudget",
    "SPCResult",
    "CapabilityIndices",
    "SPCAnalyzer",
]
