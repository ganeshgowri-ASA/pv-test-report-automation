"""
AI-powered report summarization for PV test reports.

Features:
- Auto-generate executive summaries
- Extract key findings and results
- Identify critical failures or deviations
- Multi-language summary support
- Customizable summary length/detail level
"""

import json
from enum import Enum
from typing import Any, Dict, List, Optional

from src.config.settings import get_settings
from src.llm.claude_client import ClaudeClient
from src.logging.logger import get_logger
from src.models.test_report import TestReport, PassFailStatus
from src.utils.exceptions import ReportGenerationException


class SummaryType(str, Enum):
    """Types of summaries that can be generated."""

    EXECUTIVE = "executive"  # High-level summary for executives
    TECHNICAL = "technical"  # Detailed technical summary
    COMPLIANCE = "compliance"  # Compliance-focused summary
    FINDINGS = "findings"  # Key findings and issues only
    QUICK = "quick"  # Brief overview


class SummaryLength(str, Enum):
    """Summary length options."""

    BRIEF = "brief"  # 1-2 paragraphs
    STANDARD = "standard"  # 3-5 paragraphs
    DETAILED = "detailed"  # Comprehensive summary


class ReportSummarizer:
    """
    Claude AI-powered report summarizer for PV test reports.

    Generates intelligent summaries with:
    - Automatic key finding extraction
    - Critical failure highlighting
    - Multi-language support
    - Customizable detail levels
    """

    # Language prompts
    LANGUAGE_INSTRUCTIONS = {
        "en": "Generate the summary in English.",
        "es": "Genera el resumen en español.",
        "fr": "Générez le résumé en français.",
        "de": "Erstellen Sie die Zusammenfassung auf Deutsch.",
        "zh": "用中文生成摘要。",
        "ja": "日本語で要約を生成してください。",
        "hi": "सारांश हिंदी में उत्पन्न करें।",
    }

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        """
        Initialize report summarizer.

        Args:
            claude_client: Optional Claude client instance
        """
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.claude_client = claude_client or ClaudeClient()

    def _build_summarization_prompt(
        self,
        report: TestReport,
        summary_type: SummaryType,
        length: SummaryLength,
        language: str,
        include_recommendations: bool,
    ) -> tuple[str, str]:
        """
        Build prompts for report summarization.

        Args:
            report: Test report to summarize
            summary_type: Type of summary to generate
            length: Desired length
            language: Target language
            include_recommendations: Whether to include recommendations

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # System prompt based on summary type
        system_prompts = {
            SummaryType.EXECUTIVE: """You are an expert technical writer specializing in executive summaries for photovoltaic testing reports.
Your summaries are clear, concise, and focused on business-critical information for decision-makers.""",
            SummaryType.TECHNICAL: """You are a senior PV test engineer creating detailed technical summaries.
Your summaries include precise technical details, test methodologies, and measurement results.""",
            SummaryType.COMPLIANCE: """You are a compliance auditor summarizing test reports for regulatory purposes.
Your summaries focus on standard compliance, deviations, and certification implications.""",
            SummaryType.FINDINGS: """You are a quality assurance analyst extracting key findings from test reports.
Your summaries highlight critical issues, failures, and noteworthy observations.""",
            SummaryType.QUICK: """You are creating quick overviews of test reports for rapid assessment.
Your summaries are brief and highlight only the most essential information.""",
        }

        system_prompt = system_prompts[summary_type]

        # Add language instruction
        if language in self.LANGUAGE_INSTRUCTIONS:
            system_prompt += f"\n\n{self.LANGUAGE_INSTRUCTIONS[language]}"

        # Prepare report data
        report_data = {
            "report_id": report.header.report_id,
            "report_number": report.header.report_number,
            "standard": report.header.test_standard.value,
            "specimen": {
                "manufacturer": report.specimen.manufacturer,
                "model": report.specimen.model,
                "type": report.specimen.module_type.value,
                "rated_power": f"{report.specimen.rated_power}W",
            },
            "test_period": {
                "start": report.header.test_start_date,
                "end": report.header.test_end_date,
            },
            "client": report.header.client_name,
            "total_tests": len(report.test_results),
            "passed": sum(1 for tr in report.test_results if tr.status == PassFailStatus.PASS),
            "failed": sum(1 for tr in report.test_results if tr.status == PassFailStatus.FAIL),
            "pass_rate": f"{report.calculate_pass_rate():.1f}%",
        }

        # Add test results
        test_results_summary = []
        for tr in report.test_results:
            test_results_summary.append(
                {
                    "test": tr.test_name,
                    "parameter": tr.parameter,
                    "result": tr.measured_value or tr.measured_value_str,
                    "unit": tr.unit,
                    "status": tr.status.value,
                    "spec": tr.specification,
                }
            )

        # Length guidelines
        length_guidelines = {
            SummaryLength.BRIEF: "Keep the summary to 1-2 short paragraphs (100-150 words).",
            SummaryLength.STANDARD: "Provide a standard summary of 3-5 paragraphs (250-400 words).",
            SummaryLength.DETAILED: "Create a comprehensive summary with multiple sections (500-800 words).",
        }

        # Build user prompt based on summary type
        if summary_type == SummaryType.EXECUTIVE:
            focus_areas = """
**Focus on:**
- Overall test outcome and certification readiness
- Critical findings that impact product quality or safety
- Key performance metrics vs. specifications
- Business implications (pass/fail, certification status)
- Risk factors or concerns
"""
        elif summary_type == SummaryType.TECHNICAL:
            focus_areas = """
**Focus on:**
- Test methodology and procedures followed
- Detailed test results with measurements
- Technical deviations and their significance
- Environmental conditions during testing
- Equipment and measurement uncertainty
"""
        elif summary_type == SummaryType.COMPLIANCE:
            focus_areas = """
**Focus on:**
- Compliance with standard requirements
- Mandatory vs. optional tests performed
- Non-conformities and deviations
- Certification implications
- Required corrective actions
"""
        elif summary_type == SummaryType.FINDINGS:
            focus_areas = """
**Focus on:**
- Critical failures and their root causes
- Borderline results near specification limits
- Unusual observations or anomalies
- Quality concerns
- Items requiring attention
"""
        else:  # QUICK
            focus_areas = """
**Focus on:**
- Pass/Fail status
- Critical failures only
- Overall assessment
"""

        user_prompt = f"""Summarize this PV module test report:

**Report Information:**
```json
{json.dumps(report_data, indent=2, default=str)}
```

**Test Results:**
```json
{json.dumps(test_results_summary, indent=2, default=str)}
```

{focus_areas}

**Summary Requirements:**
- {length_guidelines[length]}
- Use clear, professional language
- Highlight the most important information first
- Be specific with data and measurements
{"- Include actionable recommendations" if include_recommendations else "- Do not include recommendations"}
{"- Identify critical failures and their implications" if summary_type != SummaryType.QUICK else ""}

Provide the summary as plain text."""

        return system_prompt, user_prompt

    async def generate_summary_async(
        self,
        report: TestReport,
        summary_type: SummaryType = SummaryType.EXECUTIVE,
        length: SummaryLength = SummaryLength.STANDARD,
        language: str = "en",
        include_recommendations: bool = True,
    ) -> str:
        """
        Asynchronously generate report summary.

        Args:
            report: Test report to summarize
            summary_type: Type of summary to generate
            length: Desired summary length
            language: Target language (ISO 639-1 code)
            include_recommendations: Whether to include recommendations

        Returns:
            Generated summary text

        Raises:
            ReportGenerationException: On generation failure
        """
        try:
            self.logger.info(
                "Generating report summary",
                report_id=report.header.report_id,
                summary_type=summary_type.value,
                length=length.value,
                language=language,
            )

            # Validate language
            if language not in self.settings.SUPPORTED_LANGUAGES:
                self.logger.warning(
                    f"Unsupported language '{language}', falling back to English",
                    supported_languages=self.settings.SUPPORTED_LANGUAGES,
                )
                language = "en"

            # Build prompts
            system_prompt, user_prompt = self._build_summarization_prompt(
                report, summary_type, length, language, include_recommendations
            )

            # Call Claude API
            response = await self.claude_client.create_message_async(
                messages=[{"role": "user", "content": user_prompt}],
                system=system_prompt,
                temperature=0.5,  # Moderate creativity for summaries
            )

            summary = response.content[0].text.strip()

            self.logger.info(
                "Summary generated successfully",
                report_id=report.header.report_id,
                summary_length=len(summary),
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            )

            return summary

        except Exception as e:
            self.logger.error(f"Summary generation failed: {e}", exc_info=True)
            raise ReportGenerationException(
                f"Failed to generate summary: {e}", error_code="SUMMARY_GENERATION_FAILED"
            )

    def generate_summary(
        self,
        report: TestReport,
        summary_type: SummaryType = SummaryType.EXECUTIVE,
        length: SummaryLength = SummaryLength.STANDARD,
        language: str = "en",
        include_recommendations: bool = True,
    ) -> str:
        """
        Synchronous version of generate_summary_async.

        Args:
            report: Test report to summarize
            summary_type: Type of summary
            length: Summary length
            language: Target language
            include_recommendations: Include recommendations

        Returns:
            Generated summary text
        """
        import asyncio

        return asyncio.run(
            self.generate_summary_async(
                report, summary_type, length, language, include_recommendations
            )
        )

    async def extract_key_findings_async(self, report: TestReport) -> List[str]:
        """
        Extract key findings from report.

        Args:
            report: Test report to analyze

        Returns:
            List of key findings
        """
        system_prompt = """You are an expert PV test analyst identifying key findings from test reports.
Extract the most important findings, focusing on:
- Critical failures or deviations
- Borderline results
- Unusual observations
- Safety concerns
- Performance issues"""

        # Summarize test results
        failed_tests = report.get_failed_tests()
        test_summary = []
        for tr in report.test_results[:20]:  # Limit to prevent token overflow
            test_summary.append(f"- {tr.test_name}: {tr.status.value} ({tr.parameter})")

        user_prompt = f"""Extract key findings from this test report:

**Report:** {report.header.report_number}
**Standard:** {report.header.test_standard.value}
**Module:** {report.specimen.manufacturer} {report.specimen.model}
**Pass Rate:** {report.calculate_pass_rate():.1f}%

**Test Results Summary:**
{chr(10).join(test_summary)}

**Failed Tests:** {len(failed_tests)}

Provide a JSON array of key findings (5-10 items):
["finding 1", "finding 2", ...]"""

        response = await self.claude_client.create_message_async(
            messages=[{"role": "user", "content": user_prompt}], system=system_prompt
        )

        response_text = response.content[0].text.strip()

        # Parse JSON
        try:
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                findings = json.loads(response_text[json_start:json_end].strip())
            else:
                findings = json.loads(response_text)
            return findings
        except json.JSONDecodeError:
            # Fallback: extract from text
            return response_text.split("\n")

    def extract_key_findings(self, report: TestReport) -> List[str]:
        """
        Synchronous version of extract_key_findings_async.

        Args:
            report: Test report

        Returns:
            List of key findings
        """
        import asyncio

        return asyncio.run(self.extract_key_findings_async(report))

    async def generate_multi_language_summaries(
        self, report: TestReport, languages: List[str]
    ) -> Dict[str, str]:
        """
        Generate summaries in multiple languages concurrently.

        Args:
            report: Test report
            languages: List of language codes

        Returns:
            Dictionary mapping language codes to summaries
        """
        import asyncio

        tasks = {
            lang: self.generate_summary_async(report, language=lang) for lang in languages
        }

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        summaries = {}
        for lang, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                self.logger.error(f"Failed to generate summary for {lang}: {result}")
                summaries[lang] = f"[Error generating summary: {result}]"
            else:
                summaries[lang] = result

        return summaries
