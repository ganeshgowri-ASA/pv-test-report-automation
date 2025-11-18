"""IEC 62716 Ammonia Corrosion Testing Protocol Handler
Ammonia corrosion test per IEC 62716:2013"""
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime

@dataclass
class IEC62716Test:
    test_id: str
    duration_hours: int
    ammonia_concentration_ppm: int
    temperature_c: float
    humidity_rh: float
    pass_criteria: str

class IEC62716Handler:
    """Handler for IEC 62716 Ammonia Corrosion Testing"""

    STANDARD_TEST = IEC62716Test(
        test_id="AMM-001",
        duration_hours=192,  # 8 days
        ammonia_concentration_ppm=10,
        temperature_c=40,
        humidity_rh=85,
        pass_criteria="No corrosion, no power degradation >5%, no safety issues"
    )

    def __init__(self, config: Dict):
        self.config = config
        self.test_params = self.STANDARD_TEST

    def execute_ammonia_test(self, sample_data: Dict) -> Dict:
        """Execute IEC 62716 ammonia corrosion test"""
        results = {
            "standard": "IEC 62716:2013",
            "test_name": "Ammonia Corrosion Resistance Test",
            "sample_id": sample_data.get("sample_id"),
            "test_date": datetime.now().isoformat(),
            "test_conditions": {
                "duration_hours": self.test_params.duration_hours,
                "ammonia_ppm": self.test_params.ammonia_concentration_ppm,
                "temperature_c": self.test_params.temperature_c,
                "humidity_rh": self.test_params.humidity_rh
            },
            "measurements": {
                "initial_pmax": sample_data.get("initial_pmax", 0),
                "final_pmax": sample_data.get("final_pmax", 0),
                "power_degradation_pct": 0,
                "visual_defects": sample_data.get("visual_defects", []),
                "el_image_analysis": sample_data.get("el_analysis", {}),
                "insulation_resistance_mohm": sample_data.get("insulation_mohm", 0)
            },
            "result": "PENDING"
        }

        # Calculate power degradation
        if results["measurements"]["initial_pmax"] > 0:
            initial = results["measurements"]["initial_pmax"]
            final = results["measurements"]["final_pmax"]
            degradation = ((initial - final) / initial) * 100
            results["measurements"]["power_degradation_pct"] = round(degradation, 2)

            # Determine pass/fail
            if degradation <= 5 and not results["measurements"]["visual_defects"]:
                results["result"] = "PASS"
            else:
                results["result"] = "FAIL"
                results["failure_reasons"] = []
                if degradation > 5:
                    results["failure_reasons"].append(f"Power degradation {degradation:.2f}% exceeds 5% limit")
                if results["measurements"]["visual_defects"]:
                    results["failure_reasons"].append(f"Visual defects found: {results['measurements']['visual_defects']}")

        return results

    def generate_report_section(self, test_results: Dict) -> Dict:
        """Generate formatted report section"""
        return {
            "title": "IEC 62716 Ammonia Corrosion Resistance Test Results",
            "standard_reference": "IEC 62716:2013",
            "test_conditions": test_results["test_conditions"],
            "measurements": test_results["measurements"],
            "result": test_results["result"],
            "compliance_statement": self._generate_compliance_statement(test_results),
            "traceability": {
                "test_date": test_results["test_date"],
                "standard_version": "IEC 62716:2013"
            }
        }

    def _generate_compliance_statement(self, results: Dict) -> str:
        if results["result"] == "PASS":
            return f"Module passed ammonia corrosion resistance test per IEC 62716:2013. Power degradation: {results['measurements']['power_degradation_pct']}%"
        else:
            return f"Module FAILED ammonia corrosion test. Reasons: {', '.join(results.get('failure_reasons', []))}"
