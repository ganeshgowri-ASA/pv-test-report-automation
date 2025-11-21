"""
IEC 62759: Transportation Testing for PV Modules
"""

from typing import Dict, Any
from .base import ProtocolBase, TestSequence, SampleSpecification


class IEC62759Protocol(ProtocolBase):
    """IEC 62759 - Transportation Testing"""

    def __init__(self):
        super().__init__()
        self.protocol_name = "IEC 62759"
        self.protocol_version = "2019"
        self.full_title = "Transportation testing of photovoltaic (PV) modules"
        self.description = "Testing for transportation durability"

        self.test_sequences = [
            TestSequence(1, "Vibration Testing", "Simulated transportation vibration",
                        ["Initial Test", "Vibration Exposure", "Final Test"]),
            TestSequence(2, "Shock Testing", "Impact and shock resistance",
                        ["Drop Test", "Impact Test"]),
        ]

        self.required_equipment = [
            "Vibration Test Table",
            "Shock Test Equipment",
            "Packaging Test System",
        ]

    def get_test_matrix(self) -> Dict[str, Any]:
        return {
            "TRN-01": {"name": "Vibration Test", "frequency": "2-200 Hz",
                      "amplitude": "per ASTM D4169", "duration": "3 hours"},
            "TRN-02": {"name": "Drop Test", "height": "1.0 meter", "drops": 5},
        }

    def validate_sample(self, sample: SampleSpecification) -> tuple[bool, str]:
        return True, "Sample suitable for IEC 62759"

    def get_acceptance_criteria(self, test_name: str) -> Dict[str, Any]:
        return {"max_power_degradation": 5.0, "no_physical_damage": True}
