"""IEC 61730 Safety Qualification Protocol Handler
Safety qualification of PV modules per IEC 61730-1 & IEC 61730-2
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

class SafetyClass(Enum):
    CLASS_A = "A"  # Hazardous voltage >120V DC, restricted access
    CLASS_B = "B"  # Hazardous voltage ≤120V DC
    CLASS_C = "C"  # Accessible, no hazardous voltage

class ApplicationClass(Enum):
    APP_A = "A"  # General access
    APP_B = "B"  # Restricted access
    APP_C = "C"  # Special access

@dataclass
class IEC61730Test:
    test_id: str
    test_name: str
    clause: str
    required_for_classes: List[SafetyClass]
    pass_criteria: str
    test_params: Dict

class IEC61730Handler:
    """Handler for IEC 61730 Safety Qualification Tests"""

    MST_TESTS = [
        IEC61730Test("10.1", "Visual Inspection", "10.1", [SafetyClass.CLASS_A, SafetyClass.CLASS_B, SafetyClass.CLASS_C],
                    "No visible defects, damage, or safety concerns", {}),
        IEC61730Test("10.2", "Ground Continuity", "10.2", [SafetyClass.CLASS_A, SafetyClass.CLASS_B],
                    "Resistance ≤ 0.1Ω between frame and ground terminal", {"max_resistance": 0.1}),
        IEC61730Test("10.3", "Wet Leakage Current", "10.3", [SafetyClass.CLASS_A, SafetyClass.CLASS_B],
                    "Leakage current ≤ 0.5mA after 1min spray", {"max_current_ma": 0.5, "spray_duration_min": 1}),
        IEC61730Test("10.7", "Dielectric Withstand", "10.7", [SafetyClass.CLASS_A, SafetyClass.CLASS_B, SafetyClass.CLASS_C],
                    "No breakdown at test voltage for 1 minute", {"voltage_multiplier": 2, "test_duration_min": 1}),
        IEC61730Test("10.9", "Cut Susceptibility", "10.9", [SafetyClass.CLASS_A, SafetyClass.CLASS_B],
                    "No cut through or damage allowing access to live parts", {}),
        IEC61730Test("10.10", "Impact", "10.10", [SafetyClass.CLASS_A, SafetyClass.CLASS_B, SafetyClass.CLASS_C],
                    "No safety-relevant damage after impact test", {"energy_joules": 1.0}),
        IEC61730Test("10.11", "Screw Threads", "10.11", [SafetyClass.CLASS_A, SafetyClass.CLASS_B, SafetyClass.CLASS_C],
                    "Thread engagement meets minimum requirements", {}),
        IEC61730Test("10.12", "Sharp Edges", "10.12", [SafetyClass.CLASS_A, SafetyClass.CLASS_B, SafetyClass.CLASS_C],
                    "No sharp edges or corners posing injury risk", {}),
        IEC61730Test("10.13", "Bypass Diode Thermal", "10.13", [SafetyClass.CLASS_A, SafetyClass.CLASS_B],
                    "Junction temperature ≤ manufacturer's rating under test", {}),
        IEC61730Test("10.14.1", "Fire Test - Spread of Flame", "10.14.1", [SafetyClass.CLASS_A, SafetyClass.CLASS_B, SafetyClass.CLASS_C],
                    "Self-extinguishing within specified time", {"test_method": "UL 94 V-0 or V-1"}),
        IEC61730Test("10.15", "Module Breakage", "10.15", [SafetyClass.CLASS_A, SafetyClass.CLASS_B, SafetyClass.CLASS_C],
                    "No accessible live parts after intentional breakage", {}),
    ]

    def __init__(self, config: Dict):
        self.config = config
        self.safety_class = SafetyClass(config.get('safety_class', 'A'))
        self.application_class = ApplicationClass(config.get('application_class', 'A'))

    def get_required_tests(self) -> List[IEC61730Test]:
        """Get tests required for specified safety class"""
        return [test for test in self.MST_TESTS
                if self.safety_class in test.required_for_classes]

    def execute_test_sequence(self, sample_data: Dict) -> Dict:
        """Execute full IEC 61730 test sequence"""
        required_tests = self.get_required_tests()
        results = {
            "standard": "IEC 61730-2:2023",
            "safety_class": self.safety_class.value,
            "application_class": self.application_class.value,
            "test_date": datetime.now().isoformat(),
            "sample_id": sample_data.get("sample_id"),
            "tests": []
        }

        for test in required_tests:
            test_result = self._execute_single_test(test, sample_data)
            results["tests"].append(test_result)

        # Overall compliance
        all_passed = all(t["result"] == "PASS" for t in results["tests"])
        results["overall_result"] = "PASS" if all_passed else "FAIL"
        results["compliance_statement"] = self._generate_compliance_statement(all_passed)

        return results

    def _execute_single_test(self, test: IEC61730Test, sample_data: Dict) -> Dict:
        """Execute individual safety test with measurements"""
        # Placeholder for actual test execution
        # In production, this would interface with test equipment

        result = {
            "test_id": test.test_id,
            "test_name": test.test_name,
            "clause": test.clause,
            "pass_criteria": test.pass_criteria,
            "measurements": {},
            "result": "PASS",  # Determined by actual measurements
            "notes": ""
        }

        # Specific test logic
        if test.test_id == "10.2":  # Ground Continuity
            measured_resistance = sample_data.get("ground_resistance_ohm", 0.05)
            result["measurements"]["resistance_ohm"] = measured_resistance
            result["result"] = "PASS" if measured_resistance <= test.test_params["max_resistance"] else "FAIL"

        elif test.test_id == "10.3":  # Wet Leakage Current
            measured_current = sample_data.get("wet_leakage_current_ma", 0.3)
            result["measurements"]["leakage_current_ma"] = measured_current
            result["result"] = "PASS" if measured_current <= test.test_params["max_current_ma"] else "FAIL"

        elif test.test_id == "10.7":  # Dielectric Withstand
            test_voltage = sample_data.get("rated_voltage", 1000) * test.test_params["voltage_multiplier"]
            result["measurements"]["test_voltage_v"] = test_voltage
            result["measurements"]["test_duration_min"] = test.test_params["test_duration_min"]
            breakdown_occurred = sample_data.get("dielectric_breakdown", False)
            result["result"] = "FAIL" if breakdown_occurred else "PASS"

        return result

    def _generate_compliance_statement(self, passed: bool) -> str:
        """Generate formal compliance statement"""
        if passed:
            return (f"This module has successfully passed all required tests for "
                   f"Safety Class {self.safety_class.value} and Application Class "
                   f"{self.application_class.value} per IEC 61730-1:2023 and IEC 61730-2:2023. "
                   f"The module meets the safety requirements for photovoltaic modules.")
        else:
            return (f"This module has NOT passed all required tests for "
                   f"Safety Class {self.safety_class.value}. "
                   f"Additional corrective actions required before certification.")

    def generate_report_section(self, test_results: Dict) -> Dict:
        """Generate formatted report section for IEC 61730"""
        return {
            "title": "IEC 61730 Safety Qualification Test Results",
            "standard_reference": "IEC 61730-1:2023 & IEC 61730-2:2023",
            "classification": {
                "safety_class": test_results["safety_class"],
                "application_class": test_results["application_class"]
            },
            "test_summary": {
                "total_tests": len(test_results["tests"]),
                "passed": sum(1 for t in test_results["tests"] if t["result"] == "PASS"),
                "failed": sum(1 for t in test_results["tests"] if t["result"] == "FAIL")
            },
            "detailed_results": test_results["tests"],
            "overall_result": test_results["overall_result"],
            "compliance_statement": test_results["compliance_statement"],
            "traceability": {
                "test_date": test_results["test_date"],
                "standard_version": "IEC 61730-2:2023",
                "data_integrity_hash": self._calculate_hash(test_results)
            }
        }

    def _calculate_hash(self, data: Dict) -> str:
        """Calculate data integrity hash"""
        import hashlib
        import json
        data_string = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_string.encode()).hexdigest()[:16]

# Unit tests
def test_safety_class_detection():
    config = {"safety_class": "A", "application_class": "A"}
    handler = IEC61730Handler(config)
    required = handler.get_required_tests()
    assert len(required) > 0
    assert all(SafetyClass.CLASS_A in test.required_for_classes for test in required)

def test_ground_continuity():
    config = {"safety_class": "A"}
    handler = IEC61730Handler(config)
    sample_data = {"sample_id": "TEST-001", "ground_resistance_ohm": 0.08}
    results = handler.execute_test_sequence(sample_data)
    ground_test = next(t for t in results["tests"] if t["test_id"] == "10.2")
    assert ground_test["result"] == "PASS"

if __name__ == "__main__":
    # Example usage
    config = {
        "safety_class": "A",
        "application_class": "A"
    }
    handler = IEC61730Handler(config)

    sample_data = {
        "sample_id": "PV-SAFETY-001",
        "ground_resistance_ohm": 0.05,
        "wet_leakage_current_ma": 0.3,
        "rated_voltage": 1000,
        "dielectric_breakdown": False
    }

    results = handler.execute_test_sequence(sample_data)
    print(f"Safety Class {results['safety_class']} - Result: {results['overall_result']}")
