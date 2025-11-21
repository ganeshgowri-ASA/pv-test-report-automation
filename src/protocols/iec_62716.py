"""
IEC 62716: Ammonia Corrosion Testing
"""

from typing import Dict, Any
from .base import ProtocolBase, TestSequence, SampleSpecification


class IEC62716Protocol(ProtocolBase):
    """IEC 62716 - Ammonia (NH3) Corrosion Testing"""

    def __init__(self):
        super().__init__()
        self.protocol_name = "IEC 62716"
        self.protocol_version = "2013"
        self.full_title = "Ammonia corrosion testing of photovoltaic (PV) modules"
        self.description = "Testing resistance to ammonia exposure"

        self.test_sequences = [
            TestSequence(1, "Ammonia Exposure", "Exposure to NH3 environment",
                        ["Initial Measurement", "NH3 Exposure (4 weeks)", "Final Measurement"]),
        ]

        self.required_equipment = [
            "Ammonia Exposure Chamber",
            "Environmental Control System",
            "Solar Simulator",
        ]

    def get_test_matrix(self) -> Dict[str, Any]:
        return {
            "NH3-01": {"name": "Ammonia Exposure", "concentration": "100 ppm",
                      "duration": "672 hours", "temp": "50°C", "humidity": "85%"},
        }

    def validate_sample(self, sample: SampleSpecification) -> tuple[bool, str]:
        return True, "Sample suitable for IEC 62716"

    def get_acceptance_criteria(self, test_name: str) -> Dict[str, Any]:
        return {"max_power_degradation": 5.0, "no_corrosion": True}
