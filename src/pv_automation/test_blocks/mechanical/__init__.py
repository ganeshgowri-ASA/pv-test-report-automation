"""Mechanical test blocks for PV module testing.

This package provides mechanical load testing capabilities including:
- Static load testing (front and rear)
- Dynamic load testing (cyclic loading)
- Deflection monitoring
- Power degradation analysis
"""

from .load_test import (
    DeflectionMeasurement,
    LoadSurface,
    LoadType,
    MechanicalLoadTest,
    PowerMeasurement,
)

__all__ = [
    "MechanicalLoadTest",
    "LoadType",
    "LoadSurface",
    "DeflectionMeasurement",
    "PowerMeasurement",
]
