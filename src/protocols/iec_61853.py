"""
IEC 61853: PV Module Performance Testing and Energy Rating
"""

from typing import Dict, Any
from .base import ProtocolBase, TestSequence, SampleSpecification


class IEC61853Protocol(ProtocolBase):
    """IEC 61853 - PV Module Performance Testing"""

    def __init__(self):
        super().__init__()
        self.protocol_name = "IEC 61853"
        self.protocol_version = "2024"
        self.full_title = "Photovoltaic (PV) module performance testing and energy rating"
        self.description = "Performance characterization at various conditions"

        self.test_sequences = [
            TestSequence(1, "IV Characteristics", "Current-voltage curves at multiple conditions",
                        ["IV at STC", "IV at NOCT", "IV at Low Irradiance", "IV at High Temperature"]),
            TestSequence(2, "Spectral Response", "Module response to different wavelengths",
                        ["Spectral Response Measurement"]),
            TestSequence(3, "Incidence Angle", "Performance at various angles",
                        ["Angle of Incidence Testing"]),
        ]

        self.required_equipment = [
            "Multi-Temperature Solar Simulator",
            "Spectral Response System",
            "Angle-Variable Test Fixture",
        ]

    def get_test_matrix(self) -> Dict[str, Any]:
        return {
            "PTC-01": {"name": "IV at STC", "irradiance": 1000, "temp": 25},
            "PTC-02": {"name": "IV at NOCT", "irradiance": 800, "temp": "NOCT"},
            "PTC-03": {"name": "Low Irradiance", "irradiance": 200, "temp": 25},
            "PTC-04": {"name": "High Temperature", "irradiance": 1000, "temp": 75},
        }

    def validate_sample(self, sample: SampleSpecification) -> tuple[bool, str]:
        return True, "Sample suitable for IEC 61853"

    def get_acceptance_criteria(self, test_name: str) -> Dict[str, Any]:
        return {"criteria": "Performance within datasheet specs"}
