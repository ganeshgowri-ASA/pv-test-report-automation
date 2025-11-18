"""
PV Test Report Automation - Test Blocks Module

Test blocks for IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759
ISO 17025, ISO 9001, NABL, ILAC, BIS standards compliance
"""

from .base import BaseTestModel, TestResult
from .bypass_diode import BypassDiodeTest, BypassDiodeResult

__all__ = [
    'BaseTestModel',
    'TestResult',
    'BypassDiodeTest',
    'BypassDiodeResult',
]

__version__ = '1.0.0'
