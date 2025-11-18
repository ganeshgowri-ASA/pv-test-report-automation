"""
Test Blocks Module

Production-ready test block implementations for PV module testing.
Covers all standard test types according to IEC 61215, 61730, and related standards.
"""

from .base_test_block import (
    BaseTestBlock,
    EquipmentInterface,
    MeasurementData,
    TestBlockResult,
    TestParameter,
    TestResult,
    TestSeverity
)

from .vi_curve_test import VICurveTest, SolarSimulator, SourceMeter
from .insulation_resistance import InsulationResistanceTest, Megohmmeter, EnvironmentMonitor
from .climate_chamber import ClimateChamberTest, ClimateChamber, TestType, DataLogger
from .outdoor_exposure import OutdoorExposureTest, WeatherStation, PowerMeter
from .dielectric_test import DielectricTest, HipotTester
from .wet_leakage import WetLeakageTest, LeakageCurrentMeter, WaterSpraySystem, HighVoltageSource
from .ground_continuity import GroundContinuityTest, GroundContinuityTester

__all__ = [
    # Base classes
    'BaseTestBlock',
    'EquipmentInterface',
    'MeasurementData',
    'TestBlockResult',
    'TestParameter',
    'TestResult',
    'TestSeverity',
    
    # Test implementations
    'VICurveTest',
    'InsulationResistanceTest',
    'ClimateChamberTest',
    'OutdoorExposureTest',
    'DielectricTest',
    'WetLeakageTest',
    'GroundContinuityTest',
    
    # Equipment interfaces
    'SolarSimulator',
    'SourceMeter',
    'Megohmmeter',
    'EnvironmentMonitor',
    'ClimateChamber',
    'DataLogger',
    'WeatherStation',
    'PowerMeter',
    'HipotTester',
    'LeakageCurrentMeter',
    'WaterSpraySystem',
    'HighVoltageSource',
    'GroundContinuityTester',
    
    # Enums and types
    'TestType',
]

__version__ = "1.0.0"
