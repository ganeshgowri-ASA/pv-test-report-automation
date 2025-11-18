"""
IEC 61853 - Photovoltaic Module Performance Testing and Energy Rating
======================================================================

Comprehensive implementation of IEC 61853 test series for PV module characterization:

- IEC 61853-1: Performance at STC and varying irradiance/temperature conditions
- IEC 61853-2: Spectral responsivity, angle of incidence, and operating temperature
- IEC 61853-3: Energy rating of PV modules
- IEC 61853-4: Standard reference climatic profiles

Key Features:
-------------
- Automated 35-point performance matrix testing (7 irradiance × 5 temperature)
- Real-time temperature chamber control and monitoring
- I-V curve acquisition and analysis at each test point
- Performance surface modeling: Pmax(G, T)
- Temperature coefficient extraction (α, β, γ)
- Spectral response and angular dependency testing
- Location-specific annual energy yield calculations
- ISO 17025 compliant data management and reporting

Usage Example:
--------------
>>> from protocols.iec_61853 import IEC61853TestController
>>>
>>> test = IEC61853TestController(
...     module_serial="PV-2025-001234",
...     test_lab="NABL Lab XYZ"
... )
>>>
>>> # Run full performance matrix
>>> test.run_performance_matrix(
...     temperatures=[-25, 0, 25, 50, 75],
...     irradiances=[100, 200, 400, 600, 800, 1000, 1100]
... )
>>>
>>> # Analyze and generate report
>>> results = test.analyze_performance()
>>> test.generate_report(output_path="iec61853_report.pdf")

Author: PV Test Automation Team
Standard: IEC 61853:2011 series
"""

from .test_controller import IEC61853TestController
from .performance_matrix import PerformanceMatrixTest, MatrixTestPoint
from .spectral_response import SpectralResponseTest, SpectralCurve
from .energy_rating import EnergyRatingCalculator, LocationProfile
from .temperature_control import TemperatureChamber, ChamberController
from .data_analyzer import PerformanceAnalyzer, PerformanceSurface
from .report_generator import IEC61853ReportGenerator

__all__ = [
    "IEC61853TestController",
    "PerformanceMatrixTest",
    "MatrixTestPoint",
    "SpectralResponseTest",
    "SpectralCurve",
    "EnergyRatingCalculator",
    "LocationProfile",
    "TemperatureChamber",
    "ChamberController",
    "PerformanceAnalyzer",
    "PerformanceSurface",
    "IEC61853ReportGenerator",
]

__version__ = "1.0.0"
__standard__ = "IEC 61853:2011"
