"""
IEC 61701: Salt Mist Corrosion Testing
"""

from typing import Dict, Any
from .base import ProtocolBase, TestSequence, SampleSpecification


class IEC61701Protocol(ProtocolBase):
    """IEC 61701 - Salt Mist Corrosion Testing"""

    def __init__(self):
        super().__init__()
        self.protocol_name = "IEC 61701"
        self.protocol_version = "2020"
        self.full_title = "Photovoltaic (PV) modules - Salt mist corrosion testing"
        self.description = "Salt fog corrosion resistance testing"

        self.test_sequences = [
            TestSequence(1, "Salt Mist Exposure", "Exposure to salt spray environment",
                        ["Initial Test", "Salt Mist (Severity 6)", "Final Test"]),
        ]

        self.required_equipment = [
            "Salt Spray Chamber",
            "NaCl Solution Preparation System",
            "Solar Simulator",
        ]

    def get_test_matrix(self) -> Dict[str, Any]:
        return {
            "SM-01": {"name": "Salt Mist Severity 6", "solution": "5% NaCl",
                     "duration": "240 hours", "temp": "35°C"},
        }

    def validate_sample(self, sample: SampleSpecification) -> tuple[bool, str]:
        return True, "Sample suitable for IEC 61701"

    def get_acceptance_criteria(self, test_name: str) -> Dict[str, Any]:
        return {"max_power_degradation": 5.0, "no_visible_corrosion": True}
