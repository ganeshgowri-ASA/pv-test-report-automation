"""Analyzers for test results, compliance, and anomalies."""

import json
import logging
from typing import Dict, List, Any, Optional

from .client import GPTIntegration
from ..models.gpt_models import (
    AnalysisResult,
    ComplianceCheck,
    ComplianceStandard,
    ComplianceStatus,
    Anomaly,
    AnomalyType,
    GPTRequest
)


logger = logging.getLogger(__name__)


class TestResultAnalyzer:
    """Analyze PV test results using GPT."""

    def __init__(self, gpt_client: GPTIntegration):
        """
        Initialize test result analyzer.

        Args:
            gpt_client: GPT integration client
        """
        self.gpt_client = gpt_client

    def analyze_iv_curve(self, iv_data: Dict[str, Any]) -> AnalysisResult:
        """
        Analyze I-V curve data.

        Args:
            iv_data: I-V curve data with voltage and current measurements

        Returns:
            Analysis result with findings and patterns
        """
        system_message = """You are an expert in photovoltaic (PV) testing and I-V curve analysis.
Analyze the provided I-V curve data and identify patterns, anomalies, and key findings.
Provide specific technical insights about the PV module's performance."""

        prompt = f"""Analyze this I-V curve data from a PV module test:

{json.dumps(iv_data, indent=2)}

Please provide:
1. A summary of the I-V curve characteristics
2. Key findings about module performance (Voc, Isc, Vmp, Imp, Pmax, FF)
3. Any detected patterns or trends
4. Potential anomalies or concerns
5. Data quality assessment (0.0-1.0 score)
6. Specific recommendations

Format your response as JSON with these keys:
- summary: string
- key_findings: list of strings
- patterns_detected: list of strings
- anomalies: list of objects with {{type, severity, location, description, confidence}}
- data_quality_score: float (0.0-1.0)
- recommendations: list of strings
"""

        response = self.gpt_client.query(
            prompt=prompt,
            system_message=system_message,
            temperature=0.3  # Lower temperature for technical analysis
        )

        # Parse JSON response
        try:
            result_data = json.loads(response)

            # Convert anomaly dicts to Anomaly objects
            anomalies = [
                Anomaly(
                    type=AnomalyType(a.get("type", "inconsistency")),
                    severity=a.get("severity", "medium"),
                    location=a.get("location", "unknown"),
                    description=a.get("description", ""),
                    confidence=a.get("confidence", 0.5),
                    suggested_action=a.get("suggested_action")
                )
                for a in result_data.get("anomalies", [])
            ]

            return AnalysisResult(
                summary=result_data.get("summary", ""),
                key_findings=result_data.get("key_findings", []),
                patterns_detected=result_data.get("patterns_detected", []),
                anomalies=anomalies,
                data_quality_score=result_data.get("data_quality_score", 0.0),
                recommendations=result_data.get("recommendations", []),
                metadata={"test_type": "iv_curve", "data": iv_data}
            )
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON response, creating basic result")
            return AnalysisResult(
                summary=response,
                key_findings=[],
                anomalies=[],
                recommendations=[],
                data_quality_score=0.5
            )

    def analyze_test_results(self, test_data: Dict[str, Any]) -> AnalysisResult:
        """
        Analyze general PV test results.

        Args:
            test_data: Test data dictionary

        Returns:
            Analysis result
        """
        system_message = """You are an expert in photovoltaic testing and quality assurance.
Analyze test results comprehensively and provide actionable insights."""

        prompt = f"""Analyze these PV test results:

{json.dumps(test_data, indent=2)}

Provide comprehensive analysis including:
1. Overall summary
2. Key findings
3. Performance patterns
4. Any anomalies or issues
5. Data quality score
6. Recommendations for improvement

Format as JSON with keys: summary, key_findings, patterns_detected, anomalies,
data_quality_score, recommendations"""

        response = self.gpt_client.query(
            prompt=prompt,
            system_message=system_message,
            temperature=0.3
        )

        try:
            result_data = json.loads(response)
            anomalies = [
                Anomaly(
                    type=AnomalyType(a.get("type", "inconsistency")),
                    severity=a.get("severity", "medium"),
                    location=a.get("location", "unknown"),
                    description=a.get("description", ""),
                    confidence=a.get("confidence", 0.5)
                )
                for a in result_data.get("anomalies", [])
            ]

            return AnalysisResult(
                summary=result_data.get("summary", ""),
                key_findings=result_data.get("key_findings", []),
                patterns_detected=result_data.get("patterns_detected", []),
                anomalies=anomalies,
                data_quality_score=result_data.get("data_quality_score", 0.0),
                recommendations=result_data.get("recommendations", []),
                metadata=test_data
            )
        except json.JSONDecodeError:
            return AnalysisResult(
                summary=response,
                key_findings=[],
                anomalies=[],
                recommendations=[],
                data_quality_score=0.5
            )


class ComplianceChecker:
    """Check compliance with IEC/ISO standards."""

    def __init__(self, gpt_client: GPTIntegration):
        """
        Initialize compliance checker.

        Args:
            gpt_client: GPT integration client
        """
        self.gpt_client = gpt_client

        # Standard requirements knowledge base
        self.standard_info = {
            ComplianceStandard.IEC_61215: """IEC 61215: Terrestrial PV modules - Design qualification and type approval.
Key requirements: thermal cycling, humidity freeze, damp heat, UV preconditioning,
outdoor exposure, hot-spot endurance, mechanical load, hail impact.""",

            ComplianceStandard.IEC_61730: """IEC 61730: PV module safety qualification.
Key requirements: electrical safety, fire safety, mechanical safety,
construction requirements, testing procedures.""",

            ComplianceStandard.IEC_62804: """IEC 62804: Test methods for detection of potential-induced degradation.
Key requirements: PID testing at 85°C/85%RH, voltage stress testing,
degradation measurement.""",

            ComplianceStandard.IEC_61853: """IEC 61853: PV module performance testing and energy rating.
Key requirements: performance at different irradiances and temperatures,
angle of incidence effects."""
        }

    def check_compliance(
        self,
        report: str,
        test_data: Dict[str, Any],
        standard: ComplianceStandard
    ) -> ComplianceCheck:
        """
        Check compliance against specified standard.

        Args:
            report: Test report text
            test_data: Test data dictionary
            standard: Compliance standard to check against

        Returns:
            Compliance check result
        """
        standard_requirements = self.standard_info.get(
            standard,
            f"General requirements for {standard.value}"
        )

        system_message = f"""You are an expert in PV module compliance and certification.
You specialize in {standard.value} compliance verification."""

        prompt = f"""Check compliance with {standard.value} for this PV module test.

Standard Requirements:
{standard_requirements}

Test Report:
{report}

Test Data:
{json.dumps(test_data, indent=2)}

Evaluate compliance and provide:
1. Overall compliance status (compliant/non_compliant/partial/unknown)
2. List of requirements met
3. List of requirements failed
4. Specific recommendations for achieving full compliance
5. Confidence score (0.0-1.0) in this assessment
6. Detailed explanation

Format as JSON with keys: status, requirements_met, requirements_failed,
recommendations, confidence_score, details"""

        response = self.gpt_client.query(
            prompt=prompt,
            system_message=system_message,
            temperature=0.2  # Very low temperature for compliance checking
        )

        try:
            result_data = json.loads(response)

            return ComplianceCheck(
                standard=standard,
                status=ComplianceStatus(result_data.get("status", "unknown")),
                requirements_met=result_data.get("requirements_met", []),
                requirements_failed=result_data.get("requirements_failed", []),
                recommendations=result_data.get("recommendations", []),
                confidence_score=result_data.get("confidence_score", 0.0),
                details=result_data.get("details")
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse compliance response: {e}")
            return ComplianceCheck(
                standard=standard,
                status=ComplianceStatus.UNKNOWN,
                requirements_met=[],
                requirements_failed=[],
                recommendations=["Manual review required"],
                confidence_score=0.0,
                details=response
            )


class AnomalyDetector:
    """Detect anomalies in PV test data."""

    def __init__(self, gpt_client: GPTIntegration):
        """
        Initialize anomaly detector.

        Args:
            gpt_client: GPT integration client
        """
        self.gpt_client = gpt_client

    def detect_anomalies(
        self,
        test_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Anomaly]:
        """
        Detect anomalies in test data.

        Args:
            test_data: Test data to analyze
            context: Optional context (historical data, expected ranges, etc.)

        Returns:
            List of detected anomalies
        """
        system_message = """You are an expert in PV testing anomaly detection.
Identify unusual patterns, outliers, inconsistencies, and potential issues in test data.
Be specific about the type, location, and severity of anomalies."""

        context_str = ""
        if context:
            context_str = f"\nContext (expected ranges, historical data):\n{json.dumps(context, indent=2)}"

        prompt = f"""Detect anomalies in this PV test data:

{json.dumps(test_data, indent=2)}
{context_str}

Identify:
1. Outliers in measurements
2. Trend deviations
3. Missing or incomplete data
4. Inconsistencies between related measurements
5. Threshold violations

For each anomaly provide:
- type: outlier, trend_deviation, missing_data, inconsistency, or threshold_violation
- severity: low, medium, or high
- location: where in the data the anomaly occurs
- description: detailed explanation
- confidence: 0.0-1.0 confidence score
- suggested_action: what should be done

Format as JSON array of anomaly objects."""

        response = self.gpt_client.query(
            prompt=prompt,
            system_message=system_message,
            temperature=0.3
        )

        try:
            anomalies_data = json.loads(response)

            return [
                Anomaly(
                    type=AnomalyType(a.get("type", "inconsistency")),
                    severity=a.get("severity", "medium"),
                    location=a.get("location", "unknown"),
                    description=a.get("description", ""),
                    confidence=a.get("confidence", 0.5),
                    suggested_action=a.get("suggested_action")
                )
                for a in anomalies_data
                if isinstance(a, dict)
            ]
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse anomalies: {e}")
            return []

    def check_data_quality(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check data quality comprehensively.

        Args:
            test_data: Test data to check

        Returns:
            Data quality report
        """
        system_message = """You are a data quality expert for PV testing.
Assess data completeness, accuracy, consistency, and validity."""

        prompt = f"""Assess the quality of this PV test data:

{json.dumps(test_data, indent=2)}

Evaluate:
1. Completeness: Are all required fields present?
2. Accuracy: Are values within reasonable ranges?
3. Consistency: Are related values consistent?
4. Validity: Does the data follow expected formats?
5. Overall quality score (0.0-1.0)

Identify specific issues and provide recommendations.

Format as JSON with keys: completeness_score, accuracy_score, consistency_score,
validity_score, overall_score, issues, recommendations"""

        response = self.gpt_client.query(
            prompt=prompt,
            system_message=system_message,
            temperature=0.2
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "overall_score": 0.5,
                "issues": ["Failed to parse quality assessment"],
                "recommendations": ["Manual review required"]
            }
