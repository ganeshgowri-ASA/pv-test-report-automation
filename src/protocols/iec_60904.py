"""
IEC 60904: Photovoltaic Devices - Measurement of Current-voltage Characteristics
"""

from typing import Dict, Any
from .base import ProtocolBase, TestSequence, SampleSpecification


class IEC60904Protocol(ProtocolBase):
    """IEC 60904 - IV Characteristic Measurements"""

    def __init__(self):
        super().__init__()
        self.protocol_name = "IEC 60904"
        self.protocol_version = "2020"
        self.full_title = "Photovoltaic devices - Measurement of current-voltage characteristics"
        self.description = "Precise IV measurement methodology"

        self.test_sequences = [
            TestSequence(1, "IV Measurements", "Current-voltage characterization",
                        ["Solar Simulator Calibration", "IV Curve Tracing", "Parameter Extraction"]),
        ]

        self.required_equipment = [
            "Class AAA Solar Simulator",
            "IV Curve Tracer",
            "Reference Cell",
            "Temperature Sensors",
        ]

    def get_test_matrix(self) -> Dict[str, Any]:
        return {
            "IV-01": {"name": "STC Measurement", "irradiance": 1000, "temp": 25, "spectrum": "AM1.5G"},
            "IV-02": {"name": "Temperature Coefficient", "temps": [-40, 0, 25, 50, 75]},
            "IV-03": {"name": "Irradiance Response", "irradiances": [200, 400, 600, 800, 1000]},
        }

    def validate_sample(self, sample: SampleSpecification) -> tuple[bool, str]:
        return True, "Sample suitable for IEC 60904"

    def get_acceptance_criteria(self, test_name: str) -> Dict[str, Any]:
        return {"accuracy": "±2%", "repeatability": "±1%"}
