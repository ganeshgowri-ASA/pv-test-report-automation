"""
IEC 61730: PV Module Safety Qualification
Construction and testing for safety certification
"""

from typing import Dict, Any
from .base import ProtocolBase, TestSequence, SampleSpecification


class IEC61730Protocol(ProtocolBase):
    """IEC 61730 - PV Module Safety Qualification"""

    def __init__(self):
        super().__init__()
        self.protocol_name = "IEC 61730"
        self.protocol_version = "2016"
        self.full_title = "Photovoltaic (PV) module safety qualification"
        self.description = "Safety qualification for PV modules"

        self.test_sequences = [
            TestSequence(1, "Construction Requirements", "Module construction safety evaluation",
                        ["Construction Review", "Insulation Testing", "Ground Continuity"]),
            TestSequence(2, "Fire Safety", "Fire resistance testing",
                        ["Fire Test Type 1", "Fire Test Type 2"]),
            TestSequence(3, "Electrical Safety", "Electrical safety verification",
                        ["High Voltage Test", "Touch Current Test"]),
        ]

        self.required_equipment = [
            "High Voltage Tester (up to 5kV)",
            "Ground Continuity Tester",
            "Fire Test Equipment",
            "Insulation Resistance Meter",
        ]

    def get_test_matrix(self) -> Dict[str, Any]:
        return {
            "MST-01": {"name": "Construction Review", "type": "visual"},
            "MST-02": {"name": "Insulation Test", "type": "electrical", "voltage": "2×Vmax+1000V"},
            "MST-03": {"name": "Ground Continuity", "type": "safety", "max_resistance": "0.1 Ω"},
            "MST-04": {"name": "Fire Test", "type": "fire", "standard": "IEC 61730-2"},
        }

    def validate_sample(self, sample: SampleSpecification) -> tuple[bool, str]:
        return True, "Sample suitable for IEC 61730"

    def get_acceptance_criteria(self, test_name: str) -> Dict[str, Any]:
        return {"criteria": "As per IEC 61730"}
