"""
Claude LLM Integration for PV Test Report Automation.

Provides Claude AI capabilities for:
- Compliance checking against IEC/ISO standards
- Test report summarization
- Defect analysis and recommendations
- Quality assurance review
- Technical documentation generation

Uses Anthropic Claude API.
"""

import logging
from typing import Any, Dict, List, Optional

from anthropic import Anthropic
from pydantic import BaseModel, Field

from src.llm.key_vault import get_vault

logger = logging.getLogger(__name__)


class ClaudeRequest(BaseModel):
    """Claude API request configuration."""

    task: str = Field(..., description="Task type: compliance_check, summarize, analyze, qa_review")
    input_data: Dict[str, Any]
    model: str = Field(default="claude-3-5-sonnet-20241022")
    max_tokens: int = Field(default=4096, ge=1, le=200000)
    temperature: float = Field(default=0.3, ge=0, le=1)
    system_prompt: Optional[str] = None


class ClaudeResponse(BaseModel):
    """Claude API response."""

    task: str
    result: str
    usage: Dict[str, int]
    model: str
    finish_reason: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ClaudeLLM:
    """
    Claude LLM integration for PV test analysis.

    Provides AI-powered analysis and compliance checking.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude LLM client.

        Args:
            api_key: Anthropic API key (retrieved from vault if not provided)
        """
        if api_key is None:
            vault = get_vault()
            api_key = vault.get_key("claude")
            if api_key is None:
                raise ValueError("Claude API key not found in vault or environment")

        self.client = Anthropic(api_key=api_key)
        logger.info("Claude LLM client initialized")

    def compliance_check(
        self,
        test_report: Dict[str, Any],
        standards: List[str],
        model: str = "claude-3-5-sonnet-20241022",
    ) -> ClaudeResponse:
        """
        Check test report compliance against IEC/ISO standards.

        Args:
            test_report: Test report data
            standards: List of standards to check against
            model: Claude model to use

        Returns:
            Compliance check results
        """
        logger.info(f"Running compliance check against standards: {standards}")

        system_prompt = """You are an expert in photovoltaic (PV) testing standards including IEC 61215,
IEC 61730, IEC 61853, IEC 61701, ISO 17025, and NABL requirements. Analyze test reports for
compliance with these standards and identify any deviations or missing requirements."""

        user_message = f"""Analyze the following PV test report for compliance with these standards: {', '.join(standards)}

Test Report Data:
{self._format_report_data(test_report)}

Please provide:
1. Compliance status for each standard
2. Any deviations or non-conformances found
3. Missing data or test results
4. Recommendations for achieving full compliance
5. Overall compliance rating (0-100%)

Format your response as structured JSON with sections for each standard."""

        response = self.client.messages.create(
            model=model,
            max_tokens=4096,
            temperature=0.3,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        result = ClaudeResponse(
            task="compliance_check",
            result=response.content[0].text,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            model=response.model,
            finish_reason=response.stop_reason or "complete",
            metadata={"standards": standards},
        )

        logger.info(f"Compliance check completed, tokens used: {response.usage.input_tokens + response.usage.output_tokens}")
        return result

    def summarize_report(
        self,
        test_report: Dict[str, Any],
        summary_type: str = "executive",
    ) -> ClaudeResponse:
        """
        Generate report summary.

        Args:
            test_report: Test report data
            summary_type: Type of summary (executive, technical, detailed)

        Returns:
            Generated summary
        """
        logger.info(f"Generating {summary_type} summary")

        summary_prompts = {
            "executive": "Create a concise executive summary (2-3 paragraphs) suitable for management.",
            "technical": "Create a detailed technical summary including key test results and findings.",
            "detailed": "Create a comprehensive summary covering all test procedures, results, and conclusions.",
        }

        system_prompt = """You are a technical writer specializing in PV module testing and certification.
Generate clear, professional summaries of test reports."""

        user_message = f"""Generate a {summary_type} summary of the following PV test report.

{summary_prompts.get(summary_type, summary_prompts["technical"])}

Test Report Data:
{self._format_report_data(test_report)}

Include:
- Test type and standards
- Sample information
- Key findings
- Pass/fail status
- Significant defects or issues (if any)
- Overall assessment"""

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            temperature=0.5,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        result = ClaudeResponse(
            task="summarize_report",
            result=response.content[0].text,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            model=response.model,
            finish_reason=response.stop_reason or "complete",
            metadata={"summary_type": summary_type},
        )

        logger.info(f"Summary generated, tokens used: {response.usage.input_tokens + response.usage.output_tokens}")
        return result

    def analyze_defects(
        self,
        defects: List[Dict[str, Any]],
        test_type: str,
    ) -> ClaudeResponse:
        """
        Analyze detected defects and provide recommendations.

        Args:
            defects: List of detected defects
            test_type: Type of test performed

        Returns:
            Defect analysis and recommendations
        """
        logger.info(f"Analyzing {len(defects)} defects from {test_type}")

        system_prompt = """You are a PV module quality assurance expert. Analyze defects found
in PV modules and provide actionable recommendations for quality improvement and failure prevention."""

        user_message = f"""Analyze the following defects detected during {test_type}:

Defects:
{self._format_defects(defects)}

Provide:
1. Severity assessment for each defect type
2. Root cause analysis
3. Impact on module performance and reliability
4. Recommendations for manufacturing process improvements
5. Recommended corrective actions
6. Long-term quality improvement strategies"""

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=3072,
            temperature=0.4,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        result = ClaudeResponse(
            task="analyze_defects",
            result=response.content[0].text,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            model=response.model,
            finish_reason=response.stop_reason or "complete",
            metadata={"defect_count": len(defects), "test_type": test_type},
        )

        logger.info(f"Defect analysis completed")
        return result

    def qa_review(
        self,
        test_report: Dict[str, Any],
    ) -> ClaudeResponse:
        """
        Perform QA review of test report.

        Args:
            test_report: Test report data

        Returns:
            QA review findings
        """
        logger.info("Performing QA review")

        system_prompt = """You are a quality assurance reviewer for an ISO 17025 and NABL accredited
testing laboratory. Review test reports for completeness, accuracy, and compliance."""

        user_message = f"""Perform a comprehensive QA review of this test report:

{self._format_report_data(test_report)}

Check for:
1. Data completeness and consistency
2. Calibration records and traceability
3. Test procedure adherence
4. Calculation accuracy
5. Units and formatting
6. Compliance with ISO 17025 and NABL requirements
7. Missing information or signatures
8. Data quality issues

Provide a structured review with:
- Issues found (categorized by severity)
- Recommendations for correction
- Overall QA assessment (pass/fail/revision required)"""

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            temperature=0.2,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        result = ClaudeResponse(
            task="qa_review",
            result=response.content[0].text,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            model=response.model,
            finish_reason=response.stop_reason or "complete",
        )

        logger.info("QA review completed")
        return result

    def _format_report_data(self, report: Dict[str, Any]) -> str:
        """Format report data for LLM input."""
        import json
        return json.dumps(report, indent=2, default=str)

    def _format_defects(self, defects: List[Dict[str, Any]]) -> str:
        """Format defects list for LLM input."""
        import json
        return json.dumps(defects, indent=2, default=str)
