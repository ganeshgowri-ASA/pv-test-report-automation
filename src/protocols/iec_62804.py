"""
IEC 62804: Potential Induced Degradation (PID) Testing
"""

from typing import Dict, Any
from .base import ProtocolBase, TestSequence, SampleSpecification


class IEC62804Protocol(ProtocolBase):
    """IEC 62804 - PID Testing"""

    def __init__(self):
        super().__init__()
        self.protocol_name = "IEC 62804"
        self.protocol_version = "2021"
        self.full_title = "Photovoltaic (PV) modules - Test methods for detection of potential-induced degradation"
        self.description = "Detection and quantification of PID effects"

        self.test_sequences = [
            TestSequence(1, "PID Testing", "High voltage stress testing",
                        ["Initial Measurement", "PID Stress (96h)", "Recovery Test", "Final Measurement"]),
        ]

        self.required_equipment = [
            "High Voltage Power Supply",
            "Environmental Chamber (60°C, 85%RH)",
            "Solar Simulator",
            "EL Imaging System",
        ]

    def get_test_matrix(self) -> Dict[str, Any]:
        return {
            "PID-01": {"name": "PID Stress Test", "voltage": "-1000V or -600V",
                      "duration": "96 hours", "temp": "60°C", "humidity": "85%"},
        }

    def validate_sample(self, sample: SampleSpecification) -> tuple[bool, str]:
        return True, "Sample suitable for IEC 62804"

    def get_acceptance_criteria(self, test_name: str) -> Dict[str, Any]:
        return {"max_power_degradation": 5.0, "recoverable": "partial"}
