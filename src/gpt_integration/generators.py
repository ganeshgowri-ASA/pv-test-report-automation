"""Report generation and recommendation engines."""

import json
import logging
from typing import Dict, List, Any, Optional

from .client import GPTIntegration
from ..models.gpt_models import (
    ReportSummary,
    Language,
    ComplianceStatus,
    NaturalLanguageQuery,
    QueryResponse
)


logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate PV test reports with multi-language support."""

    def __init__(self, gpt_client: GPTIntegration):
        """
        Initialize report generator.

        Args:
            gpt_client: GPT integration client
        """
        self.gpt_client = gpt_client

        self.language_names = {
            Language.ENGLISH: "English",
            Language.SPANISH: "Spanish (Español)",
            Language.GERMAN: "German (Deutsch)",
            Language.FRENCH: "French (Français)",
            Language.CHINESE: "Chinese (中文)",
            Language.JAPANESE: "Japanese (日本語)"
        }

    def generate_executive_summary(
        self,
        test_data: Dict[str, Any],
        analysis_results: Optional[Dict[str, Any]] = None,
        language: Language = Language.ENGLISH
    ) -> ReportSummary:
        """
        Generate executive summary of test results.

        Args:
            test_data: Test data dictionary
            analysis_results: Optional analysis results
            language: Target language for the report

        Returns:
            Report summary object
        """
        lang_name = self.language_names.get(language, "English")

        system_message = f"""You are an expert technical writer specializing in PV test reports.
Generate clear, professional summaries in {lang_name}.
Focus on executive-level insights suitable for management and stakeholders."""

        analysis_str = ""
        if analysis_results:
            analysis_str = f"\n\nAnalysis Results:\n{json.dumps(analysis_results, indent=2)}"

        prompt = f"""Generate an executive summary for this PV module test in {lang_name}.

Test Data:
{json.dumps(test_data, indent=2)}
{analysis_str}

Create a comprehensive report with:
1. Executive Summary (2-3 paragraphs for non-technical stakeholders)
2. Test Overview (what was tested, methodology)
3. Key Metrics (important performance indicators)
4. Overall Compliance Status (if applicable: compliant/non_compliant/partial/unknown)
5. Top Recommendations (3-5 actionable items)

The report should be professional, clear, and suitable for executive presentation.

Format as JSON with keys: executive_summary, test_overview, key_metrics (dict),
compliance_status, recommendations (list)"""

        response = self.gpt_client.query(
            prompt=prompt,
            system_message=system_message,
            temperature=0.5
        )

        try:
            result_data = json.loads(response)

            compliance_str = result_data.get("compliance_status")
            compliance_status = None
            if compliance_str:
                try:
                    compliance_status = ComplianceStatus(compliance_str.lower())
                except ValueError:
                    compliance_status = None

            return ReportSummary(
                executive_summary=result_data.get("executive_summary", ""),
                test_overview=result_data.get("test_overview", ""),
                key_metrics=result_data.get("key_metrics", {}),
                compliance_status=compliance_status,
                recommendations=result_data.get("recommendations", []),
                language=language
            )
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse report summary: {e}")
            return ReportSummary(
                executive_summary=response,
                test_overview="",
                key_metrics={},
                recommendations=[],
                language=language
            )

    def generate_detailed_report(
        self,
        test_data: Dict[str, Any],
        language: Language = Language.ENGLISH,
        include_technical_details: bool = True,
        include_charts_suggestions: bool = True
    ) -> str:
        """
        Generate detailed technical report.

        Args:
            test_data: Test data dictionary
            language: Target language
            include_technical_details: Include detailed technical analysis
            include_charts_suggestions: Suggest charts and visualizations

        Returns:
            Formatted report text
        """
        lang_name = self.language_names.get(language, "English")

        system_message = f"""You are an expert PV testing engineer and technical writer.
Generate comprehensive, detailed technical reports in {lang_name}.
Use proper technical terminology and provide in-depth analysis."""

        detail_level = "comprehensive technical details" if include_technical_details else "high-level overview"
        charts_instruction = ""
        if include_charts_suggestions:
            charts_instruction = "\n- Suggest appropriate charts and visualizations for the data"

        prompt = f"""Generate a detailed PV test report in {lang_name}.

Test Data:
{json.dumps(test_data, indent=2)}

Create a {detail_level} report with:
- Title and metadata
- Introduction and test objectives
- Methodology and equipment used
- Detailed results and measurements
- Performance analysis
- Observations and findings
- Conclusions
- Recommendations{charts_instruction}

Format as a well-structured markdown document."""

        response = self.gpt_client.query(
            prompt=prompt,
            system_message=system_message,
            temperature=0.4,
            max_tokens=3000
        )

        return response

    def translate_report(
        self,
        report_text: str,
        source_language: Language,
        target_language: Language
    ) -> str:
        """
        Translate report to another language.

        Args:
            report_text: Original report text
            source_language: Source language
            target_language: Target language

        Returns:
            Translated report text
        """
        source_lang = self.language_names.get(source_language, "English")
        target_lang = self.language_names.get(target_language, "English")

        system_message = f"""You are an expert translator specializing in technical PV documentation.
Translate accurately while preserving technical terminology and formatting."""

        prompt = f"""Translate this PV test report from {source_lang} to {target_lang}.

Preserve:
- All technical terms and abbreviations
- Formatting (markdown, tables, etc.)
- Numerical values and units
- Section structure

Original Report:
{report_text}

Provide the complete translated report maintaining all technical accuracy."""

        response = self.gpt_client.query(
            prompt=prompt,
            system_message=system_message,
            temperature=0.3,
            max_tokens=3500
        )

        return response


class RecommendationEngine:
    """Generate automated recommendations for PV test results."""

    def __init__(self, gpt_client: GPTIntegration):
        """
        Initialize recommendation engine.

        Args:
            gpt_client: GPT integration client
        """
        self.gpt_client = gpt_client

    def generate_recommendations(
        self,
        test_data: Dict[str, Any],
        analysis_results: Optional[Dict[str, Any]] = None,
        compliance_results: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Generate actionable recommendations.

        Args:
            test_data: Test data dictionary
            analysis_results: Optional analysis results
            compliance_results: Optional compliance check results

        Returns:
            List of recommendations
        """
        system_message = """You are an expert PV engineer specializing in quality improvement.
Provide specific, actionable recommendations based on test results.
Focus on practical steps that can be implemented."""

        analysis_str = ""
        if analysis_results:
            analysis_str = f"\n\nAnalysis Results:\n{json.dumps(analysis_results, indent=2)}"

        compliance_str = ""
        if compliance_results:
            compliance_str = f"\n\nCompliance Results:\n{json.dumps(compliance_results, indent=2)}"

        prompt = f"""Based on these PV test results, provide actionable recommendations:

Test Data:
{json.dumps(test_data, indent=2)}
{analysis_str}
{compliance_str}

Generate 5-10 specific, prioritized recommendations covering:
1. Performance improvements
2. Quality enhancements
3. Compliance requirements
4. Testing improvements
5. Risk mitigation

Each recommendation should:
- Be specific and actionable
- Include the rationale
- Indicate priority (high/medium/low)
- Suggest implementation approach

Format as JSON array of recommendation strings, each starting with [PRIORITY] prefix."""

        response = self.gpt_client.query(
            prompt=prompt,
            system_message=system_message,
            temperature=0.4
        )

        try:
            recommendations = json.loads(response)
            if isinstance(recommendations, list):
                return recommendations
            elif isinstance(recommendations, dict) and "recommendations" in recommendations:
                return recommendations["recommendations"]
            else:
                return [response]
        except json.JSONDecodeError:
            # If not JSON, split by lines and filter
            return [
                line.strip()
                for line in response.split('\n')
                if line.strip() and not line.strip().startswith('#')
            ]

    def suggest_corrective_actions(
        self,
        failures: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[str]]:
        """
        Suggest corrective actions for test failures.

        Args:
            failures: List of test failures or issues
            context: Optional context information

        Returns:
            Dictionary mapping failures to corrective actions
        """
        system_message = """You are an expert in PV manufacturing and quality control.
Provide specific corrective actions for test failures.
Focus on root cause analysis and preventive measures."""

        context_str = ""
        if context:
            context_str = f"\n\nContext:\n{json.dumps(context, indent=2)}"

        failures_str = "\n".join(f"- {f}" for f in failures)

        prompt = f"""For each test failure, suggest specific corrective actions:

Failures:
{failures_str}
{context_str}

For each failure, provide:
1. Root cause analysis
2. Immediate corrective actions
3. Long-term preventive measures
4. Testing/verification steps

Format as JSON object where keys are failure descriptions and values are arrays
of corrective action strings."""

        response = self.gpt_client.query(
            prompt=prompt,
            system_message=system_message,
            temperature=0.4
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("Failed to parse corrective actions")
            return {failure: ["Manual analysis required"] for failure in failures}

    def answer_query(
        self,
        query: NaturalLanguageQuery
    ) -> QueryResponse:
        """
        Answer natural language queries about test data.

        Args:
            query: Natural language query object

        Returns:
            Query response with answer and context
        """
        system_message = """You are an expert PV testing assistant.
Answer questions about test data clearly and accurately.
Provide specific references to the data when possible."""

        context_str = json.dumps(query.context, indent=2) if query.context else "No context provided"

        viz_instruction = ""
        if query.include_visualizations:
            viz_instruction = "\n- Suggest relevant visualizations (charts, graphs) that would help answer the question"

        prompt = f"""Answer this question about PV test data:

Question: {query.query}

Available Data:
{context_str}

Provide:
- Clear, specific answer
- Relevant data points that support the answer
- Confidence level (0.0-1.0)
- Data sources used{viz_instruction}

Format as JSON with keys: answer, relevant_data (dict), confidence, sources (list),
suggested_visualizations (list)"""

        response = self.gpt_client.query(
            prompt=prompt,
            system_message=system_message,
            temperature=0.3
        )

        try:
            result_data = json.loads(response)

            return QueryResponse(
                answer=result_data.get("answer", response),
                relevant_data=result_data.get("relevant_data", {}),
                suggested_visualizations=result_data.get("suggested_visualizations", []),
                confidence=result_data.get("confidence", 0.5),
                sources=result_data.get("sources", [])
            )
        except json.JSONDecodeError:
            return QueryResponse(
                answer=response,
                relevant_data={},
                suggested_visualizations=[],
                confidence=0.5,
                sources=[]
            )
