"""
Compliance checker using Claude AI for PV test report validation.

Analyzes test reports against IEC/ISO requirements:
- Flags missing mandatory sections
- Checks data completeness per standard clauses
- Verifies pass/fail criteria consistency
- Identifies potential compliance issues
- Generates compliance score and recommendations
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.config.settings import get_settings
from src.llm.claude_client import ClaudeClient
from src.logging.logger import get_logger
from src.models.test_report import (
    ComplianceSummary,
    PassFailStatus,
    StandardType,
    TestReport,
)
from src.utils.exceptions import ComplianceCheckException


class ComplianceChecker:
    """
    Claude AI-powered compliance checker for PV test reports.

    Validates reports against international standards including:
    - IEC 61215 (Design qualification)
    - IEC 61730 (Safety qualification)
    - IEC 61853 (Performance testing)
    - ISO 17025 (Laboratory competence)
    - ISO 9001 (Quality management)
    """

    # Standard requirements mapping
    STANDARD_REQUIREMENTS = {
        StandardType.IEC_61215: {
            "mandatory_sections": [
                "Visual Inspection",
                "Electrical Performance",
                "Thermal Cycling",
                "Humidity Freeze",
                "Damp Heat",
                "Mechanical Load Test",
                "Hail Impact Test",
                "UV Preconditioning",
            ],
            "minimum_tests": 10,
            "critical_parameters": [
                "Maximum Power",
                "Open Circuit Voltage",
                "Short Circuit Current",
                "Insulation Resistance",
            ],
        },
        StandardType.IEC_61730: {
            "mandatory_sections": [
                "Construction Requirements",
                "Electrical Safety",
                "Fire Safety",
                "Mechanical Stress Test",
            ],
            "minimum_tests": 8,
            "critical_parameters": [
                "Insulation Resistance",
                "Wet Leakage Current",
                "Fire Classification",
            ],
        },
        StandardType.IEC_61853: {
            "mandatory_sections": [
                "Irradiance and Temperature Performance",
                "Angle of Incidence",
                "Spectral Response",
            ],
            "minimum_tests": 5,
            "critical_parameters": ["Temperature Coefficients", "NMOT"],
        },
        StandardType.ISO_17025: {
            "mandatory_sections": [
                "Traceability",
                "Measurement Uncertainty",
                "Equipment Calibration",
                "Quality Control",
            ],
            "minimum_tests": 0,  # Meta-standard
            "critical_parameters": ["Calibration Certificate", "Uncertainty Budget"],
        },
    }

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        """
        Initialize compliance checker.

        Args:
            claude_client: Optional Claude client instance (creates new if not provided)
        """
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.claude_client = claude_client or ClaudeClient()

    def _build_compliance_prompt(
        self, report: TestReport, detailed: bool = True
    ) -> tuple[str, str]:
        """
        Build system and user prompts for compliance checking.

        Args:
            report: Test report to check
            detailed: Whether to request detailed analysis

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        standard = report.header.test_standard
        requirements = self.STANDARD_REQUIREMENTS.get(
            standard, {"mandatory_sections": [], "minimum_tests": 0, "critical_parameters": []}
        )

        system_prompt = f"""You are an expert PV (Photovoltaic) test standards compliance auditor with deep knowledge of:
- {standard.value} standard requirements
- IEC and ISO testing methodologies
- Laboratory quality assurance (ISO 17025)
- PV module qualification criteria

Your task is to analyze test reports for compliance with {standard.value} and identify any gaps, issues, or non-conformities.

You must be thorough, precise, and provide actionable recommendations."""

        # Prepare report summary
        report_summary = {
            "report_id": report.header.report_id,
            "standard": report.header.test_standard.value,
            "specimen": {
                "id": report.specimen.specimen_id,
                "manufacturer": report.specimen.manufacturer,
                "model": report.specimen.model,
                "type": report.specimen.module_type.value,
                "rated_power": report.specimen.rated_power,
            },
            "test_results": [
                {
                    "test_id": tr.test_id,
                    "test_name": tr.test_name,
                    "parameter": tr.parameter,
                    "specification": tr.specification,
                    "measured_value": tr.measured_value or tr.measured_value_str,
                    "unit": tr.unit,
                    "status": tr.status.value,
                    "comments": tr.comments,
                }
                for tr in report.test_results
            ],
            "total_tests": len(report.test_results),
            "tests_passed": len(report.get_failed_tests()),
        }

        user_prompt = f"""Analyze this PV test report for compliance with {standard.value}:

**Report Information:**
```json
{json.dumps(report_summary, indent=2, default=str)}
```

**Standard Requirements for {standard.value}:**
- Mandatory sections: {', '.join(requirements['mandatory_sections'])}
- Minimum tests required: {requirements['minimum_tests']}
- Critical parameters: {', '.join(requirements['critical_parameters'])}

**Analysis Required:**

1. **Missing Mandatory Sections**: Identify any required test sections that are missing
2. **Data Completeness**: Check if all critical parameters are tested and documented
3. **Pass/Fail Consistency**: Verify that pass/fail determinations are consistent with specifications
4. **Standard Compliance**: Identify any deviations from {standard.value} requirements
5. **Quality Issues**: Flag any data quality concerns (missing units, unclear specifications, etc.)

**Output Format:**
Provide your analysis as a JSON object with the following structure:
{{
  "overall_status": "PASS" | "FAIL" | "CONDITIONAL_PASS",
  "compliance_score": <0-100>,
  "critical_failures": [<list of critical non-conformities>],
  "warnings": [<list of warnings and concerns>],
  "missing_tests": [<list of required tests not performed>],
  "data_quality_issues": [<list of data quality problems>],
  "recommendations": [<list of actionable recommendations>],
  "detailed_analysis": "<comprehensive compliance analysis>"
}}

Be specific and reference exact test IDs, parameters, and standard clauses where applicable."""

        return system_prompt, user_prompt

    async def check_compliance_async(
        self, report: TestReport, user_id: str = "system"
    ) -> ComplianceSummary:
        """
        Asynchronously check report compliance using Claude AI.

        Args:
            report: Test report to check
            user_id: User requesting the check (for audit trail)

        Returns:
            ComplianceSummary with compliance analysis

        Raises:
            ComplianceCheckException: On analysis failure
        """
        try:
            self.logger.info(
                "Starting compliance check",
                report_id=report.header.report_id,
                standard=report.header.test_standard.value,
            )

            # Build prompts
            system_prompt, user_prompt = self._build_compliance_prompt(report)

            # Call Claude API
            response = await self.claude_client.create_message_async(
                messages=[{"role": "user", "content": user_prompt}],
                system=system_prompt,
                temperature=0.3,  # Lower temperature for consistent analysis
            )

            response_text = response.content[0].text

            # Parse JSON response
            # Extract JSON from markdown code blocks if present
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text

            analysis = json.loads(json_text)

            # Create ComplianceSummary
            compliance_summary = ComplianceSummary(
                overall_status=PassFailStatus[analysis["overall_status"]],
                compliance_score=float(analysis["compliance_score"]),
                total_tests=len(report.test_results),
                tests_passed=sum(1 for tr in report.test_results if tr.status == PassFailStatus.PASS),
                tests_failed=sum(1 for tr in report.test_results if tr.status == PassFailStatus.FAIL),
                critical_failures=analysis.get("critical_failures", []),
                warnings=analysis.get("warnings", []),
                missing_tests=analysis.get("missing_tests", []),
                recommendations=analysis.get("recommendations", []),
                generated_at=datetime.utcnow(),
                generated_by_llm=True,
            )

            self.logger.log_compliance_check(
                report_id=report.header.report_id,
                standard=report.header.test_standard.value,
                compliance_score=compliance_summary.compliance_score,
                issues_found=len(compliance_summary.critical_failures)
                + len(compliance_summary.warnings),
            )

            return compliance_summary

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Claude response as JSON: {e}")
            raise ComplianceCheckException(
                f"Invalid response format from Claude API: {e}",
                error_code="INVALID_RESPONSE_FORMAT",
            )
        except Exception as e:
            self.logger.error(f"Compliance check failed: {e}", exc_info=True)
            raise ComplianceCheckException(
                f"Compliance check failed: {e}", error_code="COMPLIANCE_CHECK_FAILED"
            )

    def check_compliance(self, report: TestReport, user_id: str = "system") -> ComplianceSummary:
        """
        Synchronous version of check_compliance_async.

        Args:
            report: Test report to check
            user_id: User requesting the check

        Returns:
            ComplianceSummary with compliance analysis
        """
        import asyncio

        return asyncio.run(self.check_compliance_async(report, user_id))

    def validate_standard_requirements(
        self, report: TestReport
    ) -> Dict[str, Any]:
        """
        Validate basic standard requirements without LLM.

        Performs rule-based validation before LLM analysis.

        Args:
            report: Test report to validate

        Returns:
            Validation results dictionary
        """
        standard = report.header.test_standard
        requirements = self.STANDARD_REQUIREMENTS.get(standard)

        if not requirements:
            return {
                "valid": True,
                "warnings": [f"No validation rules defined for {standard.value}"],
            }

        issues = []
        warnings = []

        # Check minimum tests
        if len(report.test_results) < requirements["minimum_tests"]:
            issues.append(
                f"Only {len(report.test_results)} tests performed, "
                f"{requirements['minimum_tests']} required by {standard.value}"
            )

        # Check for mandatory sections
        test_names = {tr.test_name for tr in report.test_results}
        missing_sections = []
        for required_section in requirements["mandatory_sections"]:
            if not any(required_section.lower() in tn.lower() for tn in test_names):
                missing_sections.append(required_section)

        if missing_sections:
            issues.append(f"Missing mandatory test sections: {', '.join(missing_sections)}")

        # Check for critical parameters
        parameters = {tr.parameter for tr in report.test_results}
        missing_parameters = []
        for critical_param in requirements["critical_parameters"]:
            if not any(critical_param.lower() in p.lower() for p in parameters):
                missing_parameters.append(critical_param)

        if missing_parameters:
            warnings.append(f"Missing critical parameters: {', '.join(missing_parameters)}")

        # Check for failed tests
        failed_tests = report.get_failed_tests()
        if failed_tests:
            warnings.append(f"{len(failed_tests)} test(s) failed")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "missing_sections": missing_sections,
            "missing_parameters": missing_parameters,
        }

    async def batch_check_compliance(
        self, reports: List[TestReport], user_id: str = "system"
    ) -> List[ComplianceSummary]:
        """
        Check compliance for multiple reports in parallel.

        Args:
            reports: List of test reports
            user_id: User requesting the checks

        Returns:
            List of ComplianceSummary objects
        """
        import asyncio

        tasks = [self.check_compliance_async(report, user_id) for report in reports]
        return await asyncio.gather(*tasks)
