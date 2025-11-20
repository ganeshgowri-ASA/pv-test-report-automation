"""
AI-Powered Report Summarizer Module

Generates executive summaries, key findings, and technical summaries
with multi-language support and custom formatting.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json

from .gpt_integration import GPTIntegration, GPTResponse
from .llm_config import get_config, LLMConfig, ModelType

logger = logging.getLogger(__name__)


class SummaryType(Enum):
    """Types of summaries that can be generated."""
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    REGULATORY = "regulatory"
    QUALITY_ASSURANCE = "quality_assurance"
    CUSTOMER_FACING = "customer_facing"


class SummaryFormat(Enum):
    """Output formats for summaries."""
    MARKDOWN = "markdown"
    HTML = "html"
    PLAIN_TEXT = "plain_text"
    JSON = "json"
    PDF = "pdf"


class Language(Enum):
    """Supported languages for summaries."""
    ENGLISH = "en"
    GERMAN = "de"
    SPANISH = "es"
    FRENCH = "fr"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"


@dataclass
class SummaryConfig:
    """Configuration for summary generation."""
    summary_type: SummaryType = SummaryType.TECHNICAL
    format: SummaryFormat = SummaryFormat.MARKDOWN
    language: Language = Language.ENGLISH
    max_words: int = 500
    include_charts: bool = True
    include_recommendations: bool = True
    include_statistics: bool = True
    tone: str = "professional"  # professional, casual, formal
    detail_level: str = "medium"  # high, medium, low


@dataclass
class KeyFinding:
    """Represents a key finding from a report."""
    category: str
    finding: str
    severity: str  # critical, important, notable, informational
    impact: str
    recommendation: Optional[str] = None
    data_reference: Optional[str] = None


@dataclass
class ReportSummary:
    """Complete report summary."""
    title: str
    summary_type: SummaryType
    language: Language
    executive_summary: str
    key_findings: List[KeyFinding]
    technical_details: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'title': self.title,
            'summary_type': self.summary_type.value,
            'language': self.language.value,
            'executive_summary': self.executive_summary,
            'key_findings': [
                {
                    'category': kf.category,
                    'finding': kf.finding,
                    'severity': kf.severity,
                    'impact': kf.impact,
                    'recommendation': kf.recommendation,
                    'data_reference': kf.data_reference
                }
                for kf in self.key_findings
            ],
            'technical_details': self.technical_details,
            'recommendations': self.recommendations,
            'statistics': self.statistics,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


class SummaryPrompts:
    """Specialized prompts for summary generation."""

    SYSTEM_PROMPTS = {
        SummaryType.EXECUTIVE: """You are an executive report writer for PV testing.
Your summaries are concise, focus on business impact, and avoid excessive technical jargon.
Highlight key results, risks, and actionable recommendations.""",

        SummaryType.TECHNICAL: """You are a technical writer for PV engineering reports.
Your summaries are detailed, technically accurate, and include relevant measurements and test results.
Use proper technical terminology and reference specific test procedures.""",

        SummaryType.REGULATORY: """You are a regulatory compliance writer for PV testing.
Your summaries focus on compliance status, standard requirements, and certification readiness.
Be precise about standards, test methods, and acceptance criteria.""",

        SummaryType.QUALITY_ASSURANCE: """You are a quality assurance report writer.
Your summaries focus on quality metrics, defects, process compliance, and improvement opportunities.
Be systematic and data-driven in your analysis.""",

        SummaryType.CUSTOMER_FACING: """You are a customer-facing technical communicator.
Your summaries are clear, reassuring, and explain technical concepts in accessible language.
Focus on what matters to the customer: performance, reliability, and value."""
    }

    @staticmethod
    def format_summary_request(
        report_data: Dict[str, Any],
        config: SummaryConfig
    ) -> str:
        """Format prompt for summary generation."""
        language_instruction = ""
        if config.language != Language.ENGLISH:
            lang_name = config.language.name.title()
            language_instruction = f"\n\nIMPORTANT: Write the entire summary in {lang_name}."

        include_sections = []
        if config.include_statistics:
            include_sections.append("- Key statistics and metrics")
        if config.include_recommendations:
            include_sections.append("- Actionable recommendations")
        if config.include_charts:
            include_sections.append("- References to important charts/graphs")

        sections_text = "\n".join(include_sections) if include_sections else ""

        return f"""Generate a {config.summary_type.value} summary of this PV test report.

Configuration:
- Maximum length: {config.max_words} words
- Detail level: {config.detail_level}
- Tone: {config.tone}
- Format: {config.format.value}

Include:{sections_text}

Report Data:
{json.dumps(report_data, indent=2)}{language_instruction}

Provide a well-structured summary that is appropriate for the {config.summary_type.value} audience."""

    @staticmethod
    def format_key_findings_extraction(
        report_data: Dict[str, Any],
        max_findings: int = 10
    ) -> str:
        """Format prompt for key findings extraction."""
        return f"""Extract the {max_findings} most important findings from this PV test report.

Report Data:
{json.dumps(report_data, indent=2)}

For each finding, provide:
1. Category (e.g., Performance, Safety, Quality, Compliance)
2. Finding description
3. Severity (critical/important/notable/informational)
4. Impact on the overall assessment
5. Recommendation (if applicable)
6. Reference to specific data point

Return as JSON array:
[
  {{
    "category": "...",
    "finding": "...",
    "severity": "...",
    "impact": "...",
    "recommendation": "...",
    "data_reference": "..."
  }}
]"""

    @staticmethod
    def format_translation_request(
        text: str,
        target_language: Language,
        preserve_technical_terms: bool = True
    ) -> str:
        """Format prompt for text translation."""
        lang_name = target_language.name.title()
        technical_note = ""

        if preserve_technical_terms:
            technical_note = "\nPreserve technical terms, units, and measurements in their original form."

        return f"""Translate the following PV test report summary to {lang_name}.

Maintain:
- Professional tone
- Technical accuracy
- Document structure{technical_note}

Original text:
{text}

Translated text in {lang_name}:"""


class ReportSummarizer:
    """AI-powered report summarizer."""

    def __init__(
        self,
        config: Optional[LLMConfig] = None,
        model_type: ModelType = ModelType.GPT_4_TURBO
    ):
        """
        Initialize report summarizer.

        Args:
            config: LLM configuration
            model_type: Model to use for summarization
        """
        self.config = config or get_config()
        self.gpt = GPTIntegration(config, model_type)

    async def generate_summary(
        self,
        report_data: Dict[str, Any],
        config: Optional[SummaryConfig] = None
    ) -> ReportSummary:
        """
        Generate comprehensive report summary.

        Args:
            report_data: Report data dictionary
            config: Summary configuration

        Returns:
            ReportSummary object
        """
        config = config or SummaryConfig()

        # Extract key findings
        key_findings = await self._extract_key_findings(report_data)

        # Generate main summary
        summary_text = await self._generate_summary_text(report_data, config)

        # Translate if needed
        if config.language != Language.ENGLISH:
            summary_text = await self._translate_text(
                summary_text,
                config.language
            )

        # Generate recommendations if requested
        recommendations = []
        if config.include_recommendations:
            recommendations = await self._generate_recommendations(
                report_data,
                key_findings
            )

        # Extract statistics if requested
        statistics = {}
        if config.include_statistics:
            statistics = self._extract_statistics(report_data)

        # Generate technical details if technical summary
        technical_details = None
        if config.summary_type == SummaryType.TECHNICAL:
            technical_details = await self._generate_technical_details(report_data)

        # Create title
        title = self._generate_title(report_data, config)

        return ReportSummary(
            title=title,
            summary_type=config.summary_type,
            language=config.language,
            executive_summary=summary_text,
            key_findings=key_findings,
            technical_details=technical_details,
            recommendations=recommendations,
            statistics=statistics,
            metadata={
                'word_count': len(summary_text.split()),
                'format': config.format.value,
                'detail_level': config.detail_level
            }
        )

    async def _generate_summary_text(
        self,
        report_data: Dict[str, Any],
        config: SummaryConfig
    ) -> str:
        """Generate the main summary text."""
        prompt = SummaryPrompts.format_summary_request(report_data, config)

        system_prompt = SummaryPrompts.SYSTEM_PROMPTS.get(
            config.summary_type,
            SummaryPrompts.SYSTEM_PROMPTS[SummaryType.TECHNICAL]
        )

        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        response = await self.gpt.complete_async(
            messages,
            temperature=0.7
        )

        return response.content

    async def _extract_key_findings(
        self,
        report_data: Dict[str, Any],
        max_findings: int = 10
    ) -> List[KeyFinding]:
        """Extract key findings from report."""
        prompt = SummaryPrompts.format_key_findings_extraction(
            report_data,
            max_findings
        )

        messages = [
            {
                "role": "system",
                "content": "You are an expert at identifying key findings in PV test reports."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        response = await self.gpt.complete_async(
            messages,
            temperature=0.5,
            response_format={"type": "json_object"}
        )

        try:
            content = response.content
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]

            result = json.loads(content)

            # Handle both array and object with array
            findings_data = result if isinstance(result, list) else result.get('findings', [])

            return [
                KeyFinding(
                    category=f.get('category', 'General'),
                    finding=f.get('finding', ''),
                    severity=f.get('severity', 'informational'),
                    impact=f.get('impact', ''),
                    recommendation=f.get('recommendation'),
                    data_reference=f.get('data_reference')
                )
                for f in findings_data
            ]

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse key findings: {e}")
            return []

    async def _generate_recommendations(
        self,
        report_data: Dict[str, Any],
        key_findings: List[KeyFinding]
    ) -> List[str]:
        """Generate actionable recommendations."""
        findings_summary = "\n".join([
            f"- {kf.category}: {kf.finding} (Severity: {kf.severity})"
            for kf in key_findings
        ])

        prompt = f"""Based on this PV test report and key findings, generate 5-10 actionable recommendations.

Key Findings:
{findings_summary}

Report Data:
{json.dumps(report_data, indent=2)}

Provide specific, actionable recommendations that address:
1. Critical issues that need immediate attention
2. Performance optimization opportunities
3. Quality improvements
4. Compliance requirements
5. Long-term reliability considerations

Return as a JSON array of recommendation strings."""

        messages = [
            {
                "role": "system",
                "content": "You are an expert PV consultant providing actionable recommendations."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        response = await self.gpt.complete_async(
            messages,
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        try:
            result = json.loads(response.content)
            return result.get('recommendations', [])
        except json.JSONDecodeError:
            logger.error("Failed to parse recommendations")
            return []

    async def _generate_technical_details(
        self,
        report_data: Dict[str, Any]
    ) -> str:
        """Generate detailed technical section."""
        prompt = f"""Provide detailed technical analysis of this PV test report.

Include:
1. Test methodologies used
2. Detailed test results with measurements
3. Performance characteristics
4. Technical observations
5. Comparison to specifications/standards

Report Data:
{json.dumps(report_data, indent=2)}

Provide a comprehensive technical analysis (300-500 words)."""

        messages = [
            {
                "role": "system",
                "content": SummaryPrompts.SYSTEM_PROMPTS[SummaryType.TECHNICAL]
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        response = await self.gpt.complete_async(messages, temperature=0.6)
        return response.content

    async def _translate_text(
        self,
        text: str,
        target_language: Language
    ) -> str:
        """Translate text to target language."""
        if target_language == Language.ENGLISH:
            return text

        prompt = SummaryPrompts.format_translation_request(
            text,
            target_language,
            preserve_technical_terms=True
        )

        messages = [
            {
                "role": "system",
                "content": "You are a professional translator specializing in technical documentation."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        response = await self.gpt.complete_async(messages, temperature=0.3)
        return response.content

    def _extract_statistics(
        self,
        report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract key statistics from report data."""
        stats = {}

        # Extract common statistics
        if 'test_results' in report_data:
            results = report_data['test_results']

            if 'power_output' in results:
                stats['power_output'] = results['power_output']

            if 'efficiency' in results:
                stats['efficiency'] = results['efficiency']

            if 'degradation' in results:
                stats['degradation'] = results['degradation']

        if 'test_count' in report_data:
            stats['total_tests'] = report_data['test_count']

        if 'pass_rate' in report_data:
            stats['pass_rate'] = report_data['pass_rate']

        return stats

    def _generate_title(
        self,
        report_data: Dict[str, Any],
        config: SummaryConfig
    ) -> str:
        """Generate summary title."""
        report_type = report_data.get('report_type', 'PV Test Report')
        summary_type = config.summary_type.value.replace('_', ' ').title()

        module_id = report_data.get('module_id', '')
        if module_id:
            return f"{summary_type} Summary: {report_type} - {module_id}"
        else:
            return f"{summary_type} Summary: {report_type}"

    async def batch_summarize(
        self,
        reports: List[Dict[str, Any]],
        config: Optional[SummaryConfig] = None
    ) -> List[ReportSummary]:
        """
        Generate summaries for multiple reports concurrently.

        Args:
            reports: List of report data dictionaries
            config: Summary configuration

        Returns:
            List of ReportSummary objects
        """
        tasks = [
            self.generate_summary(report, config)
            for report in reports
        ]
        return await asyncio.gather(*tasks)

    def format_summary(
        self,
        summary: ReportSummary,
        format: SummaryFormat = SummaryFormat.MARKDOWN
    ) -> str:
        """
        Format summary in specified format.

        Args:
            summary: ReportSummary object
            format: Desired output format

        Returns:
            Formatted summary string
        """
        if format == SummaryFormat.MARKDOWN:
            return self._format_markdown(summary)
        elif format == SummaryFormat.HTML:
            return self._format_html(summary)
        elif format == SummaryFormat.PLAIN_TEXT:
            return self._format_plain_text(summary)
        elif format == SummaryFormat.JSON:
            return json.dumps(summary.to_dict(), indent=2)
        else:
            return str(summary.to_dict())

    def _format_markdown(self, summary: ReportSummary) -> str:
        """Format as Markdown."""
        md = f"# {summary.title}\n\n"
        md += f"**Generated:** {summary.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md += f"## Executive Summary\n\n{summary.executive_summary}\n\n"

        if summary.key_findings:
            md += "## Key Findings\n\n"
            for i, kf in enumerate(summary.key_findings, 1):
                md += f"### {i}. {kf.category} - {kf.severity.upper()}\n\n"
                md += f"{kf.finding}\n\n"
                md += f"**Impact:** {kf.impact}\n\n"
                if kf.recommendation:
                    md += f"**Recommendation:** {kf.recommendation}\n\n"

        if summary.recommendations:
            md += "## Recommendations\n\n"
            for i, rec in enumerate(summary.recommendations, 1):
                md += f"{i}. {rec}\n"
            md += "\n"

        if summary.technical_details:
            md += f"## Technical Details\n\n{summary.technical_details}\n\n"

        if summary.statistics:
            md += "## Statistics\n\n"
            for key, value in summary.statistics.items():
                md += f"- **{key.replace('_', ' ').title()}:** {value}\n"

        return md

    def _format_html(self, summary: ReportSummary) -> str:
        """Format as HTML."""
        html = f"<html><head><title>{summary.title}</title></head><body>\n"
        html += f"<h1>{summary.title}</h1>\n"
        html += f"<p><strong>Generated:</strong> {summary.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>\n"
        html += f"<h2>Executive Summary</h2>\n<p>{summary.executive_summary}</p>\n"

        if summary.key_findings:
            html += "<h2>Key Findings</h2>\n<ul>\n"
            for kf in summary.key_findings:
                html += f"<li><strong>{kf.category}</strong> ({kf.severity}): {kf.finding}</li>\n"
            html += "</ul>\n"

        if summary.recommendations:
            html += "<h2>Recommendations</h2>\n<ol>\n"
            for rec in summary.recommendations:
                html += f"<li>{rec}</li>\n"
            html += "</ol>\n"

        html += "</body></html>"
        return html

    def _format_plain_text(self, summary: ReportSummary) -> str:
        """Format as plain text."""
        text = f"{summary.title}\n"
        text += "=" * len(summary.title) + "\n\n"
        text += f"Generated: {summary.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        text += f"EXECUTIVE SUMMARY\n{'-' * 50}\n{summary.executive_summary}\n\n"

        if summary.key_findings:
            text += f"KEY FINDINGS\n{'-' * 50}\n"
            for i, kf in enumerate(summary.key_findings, 1):
                text += f"\n{i}. {kf.category} ({kf.severity.upper()})\n"
                text += f"   {kf.finding}\n"

        return text

    def export_summary(
        self,
        summary: ReportSummary,
        output_path: str,
        format: Optional[SummaryFormat] = None
    ):
        """
        Export summary to file.

        Args:
            summary: ReportSummary object
            output_path: Output file path
            format: Output format (auto-detected from extension if not provided)
        """
        from pathlib import Path
        output_path = Path(output_path)

        # Auto-detect format from extension
        if format is None:
            ext = output_path.suffix.lower()
            format_map = {
                '.md': SummaryFormat.MARKDOWN,
                '.html': SummaryFormat.HTML,
                '.txt': SummaryFormat.PLAIN_TEXT,
                '.json': SummaryFormat.JSON
            }
            format = format_map.get(ext, SummaryFormat.MARKDOWN)

        # Format and write
        formatted = self.format_summary(summary, format)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted)

        logger.info(f"Summary exported to {output_path}")
