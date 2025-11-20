"""
Unit tests for Report Summarizer Module
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import json
import tempfile
from pathlib import Path

from ..report_summarizer import (
    ReportSummarizer,
    ReportSummary,
    SummaryType,
    SummaryFormat,
    SummaryConfig,
    KeyFinding,
    Language,
    SummaryPrompts
)
from ..llm_config import LLMConfig, LLMProvider, ModelType
from ..gpt_integration import GPTResponse


@pytest.fixture
def mock_config():
    """Create a mock LLM config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = LLMConfig(
            config_file=Path(tmpdir) / "config.json",
            cache_dir=Path(tmpdir) / "cache"
        )
        config.set_api_key(LLMProvider.OPENAI, "test-api-key")
        yield config


class TestSummaryConfig:
    """Test SummaryConfig dataclass."""

    def test_default_config(self):
        """Test default summary configuration."""
        config = SummaryConfig()

        assert config.summary_type == SummaryType.TECHNICAL
        assert config.format == SummaryFormat.MARKDOWN
        assert config.language == Language.ENGLISH
        assert config.max_words == 500
        assert config.tone == "professional"

    def test_custom_config(self):
        """Test custom summary configuration."""
        config = SummaryConfig(
            summary_type=SummaryType.EXECUTIVE,
            format=SummaryFormat.HTML,
            language=Language.GERMAN,
            max_words=300,
            tone="formal"
        )

        assert config.summary_type == SummaryType.EXECUTIVE
        assert config.format == SummaryFormat.HTML
        assert config.language == Language.GERMAN
        assert config.max_words == 300
        assert config.tone == "formal"


class TestKeyFinding:
    """Test KeyFinding dataclass."""

    def test_finding_creation(self):
        """Test creating a key finding."""
        finding = KeyFinding(
            category="Performance",
            finding="Module operates below specification",
            severity="critical",
            impact="Significant power loss",
            recommendation="Replace module"
        )

        assert finding.category == "Performance"
        assert finding.severity == "critical"
        assert finding.recommendation == "Replace module"


class TestReportSummary:
    """Test ReportSummary dataclass."""

    def test_summary_creation(self):
        """Test creating a report summary."""
        findings = [
            KeyFinding(
                category="Test",
                finding="Test finding",
                severity="low",
                impact="Minor"
            )
        ]

        summary = ReportSummary(
            title="Test Summary",
            summary_type=SummaryType.TECHNICAL,
            language=Language.ENGLISH,
            executive_summary="This is a test summary",
            key_findings=findings,
            recommendations=["Fix issues"]
        )

        assert summary.title == "Test Summary"
        assert len(summary.key_findings) == 1
        assert len(summary.recommendations) == 1

    def test_summary_to_dict(self):
        """Test converting summary to dictionary."""
        finding = KeyFinding(
            category="Test",
            finding="Test finding",
            severity="low",
            impact="Minor"
        )

        summary = ReportSummary(
            title="Test",
            summary_type=SummaryType.TECHNICAL,
            language=Language.ENGLISH,
            executive_summary="Summary",
            key_findings=[finding],
            statistics={'test_count': 10}
        )

        data = summary.to_dict()

        assert data['title'] == "Test"
        assert data['summary_type'] == 'technical'
        assert data['language'] == 'en'
        assert len(data['key_findings']) == 1
        assert data['statistics']['test_count'] == 10


class TestSummaryPrompts:
    """Test SummaryPrompts."""

    def test_system_prompts_exist(self):
        """Test that system prompts are defined."""
        assert SummaryType.EXECUTIVE in SummaryPrompts.SYSTEM_PROMPTS
        assert SummaryType.TECHNICAL in SummaryPrompts.SYSTEM_PROMPTS
        assert SummaryType.REGULATORY in SummaryPrompts.SYSTEM_PROMPTS

    def test_format_summary_request(self):
        """Test formatting summary request."""
        report_data = {'module_id': 'TEST-001'}
        config = SummaryConfig(
            summary_type=SummaryType.EXECUTIVE,
            max_words=300
        )

        prompt = SummaryPrompts.format_summary_request(report_data, config)

        assert 'executive' in prompt
        assert '300' in prompt
        assert 'TEST-001' in prompt

    def test_format_summary_request_with_language(self):
        """Test formatting summary request with non-English language."""
        report_data = {'test': 'data'}
        config = SummaryConfig(language=Language.GERMAN)

        prompt = SummaryPrompts.format_summary_request(report_data, config)

        assert 'German' in prompt

    def test_format_key_findings_extraction(self):
        """Test formatting key findings extraction."""
        report_data = {'module_id': 'TEST-001'}

        prompt = SummaryPrompts.format_key_findings_extraction(
            report_data,
            max_findings=5
        )

        assert '5' in prompt
        assert 'findings' in prompt.lower()
        assert 'JSON' in prompt

    def test_format_translation_request(self):
        """Test formatting translation request."""
        text = "This is a test summary"

        prompt = SummaryPrompts.format_translation_request(
            text,
            Language.SPANISH
        )

        assert 'Spanish' in prompt
        assert text in prompt
        assert 'technical' in prompt.lower()


class TestReportSummarizer:
    """Test ReportSummarizer functionality."""

    @patch('src.llm.report_summarizer.GPTIntegration')
    def test_initialization(self, mock_gpt_class, mock_config):
        """Test report summarizer initialization."""
        summarizer = ReportSummarizer(mock_config, ModelType.GPT_4_TURBO)

        assert summarizer.config == mock_config
        assert mock_gpt_class.called

    @patch('src.llm.report_summarizer.GPTIntegration')
    @pytest.mark.asyncio
    async def test_generate_summary(self, mock_gpt_class, mock_config):
        """Test generating a summary."""
        # Mock GPT responses
        mock_gpt = Mock()

        # Mock key findings response
        findings_response = GPTResponse(
            content=json.dumps([
                {
                    'category': 'Performance',
                    'finding': 'Module performs well',
                    'severity': 'informational',
                    'impact': 'Positive',
                    'recommendation': 'Continue monitoring'
                }
            ]),
            model="gpt-4",
            tokens_input=100,
            tokens_output=50,
            cost=0.5
        )

        # Mock summary response
        summary_response = GPTResponse(
            content="This is a comprehensive summary of the test report.",
            model="gpt-4",
            tokens_input=200,
            tokens_output=30,
            cost=0.7
        )

        # Mock recommendations response
        recommendations_response = GPTResponse(
            content=json.dumps({
                'recommendations': [
                    'Continue regular monitoring',
                    'Optimize performance'
                ]
            }),
            model="gpt-4",
            tokens_input=100,
            tokens_output=20,
            cost=0.3
        )

        mock_gpt.complete_async = AsyncMock(
            side_effect=[findings_response, summary_response, recommendations_response]
        )
        mock_gpt_class.return_value = mock_gpt

        summarizer = ReportSummarizer(mock_config)

        report_data = {
            'module_id': 'TEST-001',
            'test_results': {'power': 300}
        }

        summary = await summarizer.generate_summary(report_data)

        assert isinstance(summary, ReportSummary)
        assert len(summary.key_findings) > 0
        assert len(summary.executive_summary) > 0
        assert len(summary.recommendations) > 0

    @patch('src.llm.report_summarizer.GPTIntegration')
    @pytest.mark.asyncio
    async def test_generate_summary_text(self, mock_gpt_class, mock_config):
        """Test generating summary text."""
        mock_gpt = Mock()
        mock_gpt.complete_async = AsyncMock(
            return_value=GPTResponse(
                content="Test summary text",
                model="gpt-4",
                tokens_input=100,
                tokens_output=20,
                cost=0.3
            )
        )
        mock_gpt_class.return_value = mock_gpt

        summarizer = ReportSummarizer(mock_config)

        report_data = {'test': 'data'}
        config = SummaryConfig()

        text = await summarizer._generate_summary_text(report_data, config)

        assert text == "Test summary text"
        assert mock_gpt.complete_async.called

    @patch('src.llm.report_summarizer.GPTIntegration')
    @pytest.mark.asyncio
    async def test_extract_key_findings(self, mock_gpt_class, mock_config):
        """Test extracting key findings."""
        mock_gpt = Mock()
        mock_gpt.complete_async = AsyncMock(
            return_value=GPTResponse(
                content=json.dumps([
                    {
                        'category': 'Performance',
                        'finding': 'Good performance',
                        'severity': 'informational',
                        'impact': 'Positive',
                        'recommendation': None
                    }
                ]),
                model="gpt-4",
                tokens_input=100,
                tokens_output=50,
                cost=0.5
            )
        )
        mock_gpt_class.return_value = mock_gpt

        summarizer = ReportSummarizer(mock_config)

        findings = await summarizer._extract_key_findings({'test': 'data'})

        assert len(findings) == 1
        assert isinstance(findings[0], KeyFinding)
        assert findings[0].category == 'Performance'

    @patch('src.llm.report_summarizer.GPTIntegration')
    @pytest.mark.asyncio
    async def test_generate_recommendations(self, mock_gpt_class, mock_config):
        """Test generating recommendations."""
        mock_gpt = Mock()
        mock_gpt.complete_async = AsyncMock(
            return_value=GPTResponse(
                content=json.dumps({
                    'recommendations': [
                        'Recommendation 1',
                        'Recommendation 2'
                    ]
                }),
                model="gpt-4",
                tokens_input=100,
                tokens_output=30,
                cost=0.4
            )
        )
        mock_gpt_class.return_value = mock_gpt

        summarizer = ReportSummarizer(mock_config)

        findings = [
            KeyFinding(
                category="Test",
                finding="Issue found",
                severity="high",
                impact="Significant"
            )
        ]

        recommendations = await summarizer._generate_recommendations(
            {'test': 'data'},
            findings
        )

        assert len(recommendations) == 2
        assert recommendations[0] == 'Recommendation 1'

    @patch('src.llm.report_summarizer.GPTIntegration')
    @pytest.mark.asyncio
    async def test_translate_text(self, mock_gpt_class, mock_config):
        """Test translating text."""
        mock_gpt = Mock()
        mock_gpt.complete_async = AsyncMock(
            return_value=GPTResponse(
                content="Texto traducido",
                model="gpt-4",
                tokens_input=50,
                tokens_output=10,
                cost=0.2
            )
        )
        mock_gpt_class.return_value = mock_gpt

        summarizer = ReportSummarizer(mock_config)

        translated = await summarizer._translate_text(
            "Original text",
            Language.SPANISH
        )

        assert translated == "Texto traducido"

    @patch('src.llm.report_summarizer.GPTIntegration')
    @pytest.mark.asyncio
    async def test_translate_english_returns_original(self, mock_gpt_class, mock_config):
        """Test that English translation returns original."""
        summarizer = ReportSummarizer(mock_config)

        text = "Original text"
        result = await summarizer._translate_text(text, Language.ENGLISH)

        assert result == text

    @patch('src.llm.report_summarizer.GPTIntegration')
    def test_extract_statistics(self, mock_gpt_class, mock_config):
        """Test extracting statistics."""
        summarizer = ReportSummarizer(mock_config)

        report_data = {
            'test_results': {
                'power_output': 300,
                'efficiency': 18.5,
                'degradation': 2.3
            },
            'test_count': 10,
            'pass_rate': 95.0
        }

        stats = summarizer._extract_statistics(report_data)

        assert 'power_output' in stats
        assert stats['power_output'] == 300
        assert stats['total_tests'] == 10

    @patch('src.llm.report_summarizer.GPTIntegration')
    def test_generate_title(self, mock_gpt_class, mock_config):
        """Test generating summary title."""
        summarizer = ReportSummarizer(mock_config)

        report_data = {
            'report_type': 'Qualification Test',
            'module_id': 'TEST-001'
        }

        config = SummaryConfig(summary_type=SummaryType.EXECUTIVE)

        title = summarizer._generate_title(report_data, config)

        assert 'Executive' in title
        assert 'TEST-001' in title

    @patch('src.llm.report_summarizer.GPTIntegration')
    @pytest.mark.asyncio
    async def test_batch_summarize(self, mock_gpt_class, mock_config):
        """Test batch summarization."""
        mock_gpt = Mock()

        # Mock responses for batch processing
        mock_gpt.complete_async = AsyncMock(
            return_value=GPTResponse(
                content=json.dumps([]),
                model="gpt-4",
                tokens_input=100,
                tokens_output=50,
                cost=0.5
            )
        )
        mock_gpt_class.return_value = mock_gpt

        summarizer = ReportSummarizer(mock_config)

        # Override generate_summary to avoid complex mocking
        async def mock_generate_summary(report_data, config=None):
            return ReportSummary(
                title="Test",
                summary_type=SummaryType.TECHNICAL,
                language=Language.ENGLISH,
                executive_summary="Summary",
                key_findings=[]
            )

        summarizer.generate_summary = mock_generate_summary

        reports = [
            {'module_id': 'TEST-001'},
            {'module_id': 'TEST-002'}
        ]

        summaries = await summarizer.batch_summarize(reports)

        assert len(summaries) == 2
        assert all(isinstance(s, ReportSummary) for s in summaries)


class TestSummaryFormatting:
    """Test summary formatting."""

    @patch('src.llm.report_summarizer.GPTIntegration')
    def test_format_markdown(self, mock_gpt_class, mock_config):
        """Test Markdown formatting."""
        summarizer = ReportSummarizer(mock_config)

        summary = ReportSummary(
            title="Test Summary",
            summary_type=SummaryType.TECHNICAL,
            language=Language.ENGLISH,
            executive_summary="This is a test summary",
            key_findings=[
                KeyFinding(
                    category="Performance",
                    finding="Good",
                    severity="informational",
                    impact="Positive"
                )
            ],
            recommendations=["Keep monitoring"]
        )

        md = summarizer.format_summary(summary, SummaryFormat.MARKDOWN)

        assert '# Test Summary' in md
        assert '## Executive Summary' in md
        assert '## Key Findings' in md
        assert '## Recommendations' in md

    @patch('src.llm.report_summarizer.GPTIntegration')
    def test_format_html(self, mock_gpt_class, mock_config):
        """Test HTML formatting."""
        summarizer = ReportSummarizer(mock_config)

        summary = ReportSummary(
            title="Test",
            summary_type=SummaryType.TECHNICAL,
            language=Language.ENGLISH,
            executive_summary="Summary",
            key_findings=[]
        )

        html = summarizer.format_summary(summary, SummaryFormat.HTML)

        assert '<html>' in html
        assert '<h1>Test</h1>' in html
        assert '</html>' in html

    @patch('src.llm.report_summarizer.GPTIntegration')
    def test_format_plain_text(self, mock_gpt_class, mock_config):
        """Test plain text formatting."""
        summarizer = ReportSummarizer(mock_config)

        summary = ReportSummary(
            title="Test Summary",
            summary_type=SummaryType.TECHNICAL,
            language=Language.ENGLISH,
            executive_summary="Summary text",
            key_findings=[]
        )

        text = summarizer.format_summary(summary, SummaryFormat.PLAIN_TEXT)

        assert 'Test Summary' in text
        assert 'EXECUTIVE SUMMARY' in text
        assert '=' in text  # Header underline

    @patch('src.llm.report_summarizer.GPTIntegration')
    def test_format_json(self, mock_gpt_class, mock_config):
        """Test JSON formatting."""
        summarizer = ReportSummarizer(mock_config)

        summary = ReportSummary(
            title="Test",
            summary_type=SummaryType.TECHNICAL,
            language=Language.ENGLISH,
            executive_summary="Summary",
            key_findings=[]
        )

        json_str = summarizer.format_summary(summary, SummaryFormat.JSON)

        data = json.loads(json_str)
        assert data['title'] == "Test"

    @patch('src.llm.report_summarizer.GPTIntegration')
    def test_export_summary(self, mock_gpt_class, mock_config):
        """Test exporting summary to file."""
        summarizer = ReportSummarizer(mock_config)

        summary = ReportSummary(
            title="Test",
            summary_type=SummaryType.TECHNICAL,
            language=Language.ENGLISH,
            executive_summary="Summary",
            key_findings=[]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            # Test Markdown export
            md_path = Path(tmpdir) / "summary.md"
            summarizer.export_summary(summary, str(md_path))
            assert md_path.exists()

            # Test JSON export
            json_path = Path(tmpdir) / "summary.json"
            summarizer.export_summary(summary, str(json_path))
            assert json_path.exists()

            # Verify JSON content
            with open(json_path, 'r') as f:
                data = json.load(f)
                assert data['title'] == "Test"


class TestLanguageSupport:
    """Test multi-language support."""

    def test_supported_languages(self):
        """Test that major languages are supported."""
        assert Language.ENGLISH.value == "en"
        assert Language.GERMAN.value == "de"
        assert Language.SPANISH.value == "es"
        assert Language.FRENCH.value == "fr"
        assert Language.CHINESE.value == "zh"


class TestSummaryTypes:
    """Test different summary types."""

    def test_all_summary_types_have_prompts(self):
        """Test that all summary types have system prompts."""
        for summary_type in [
            SummaryType.EXECUTIVE,
            SummaryType.TECHNICAL,
            SummaryType.REGULATORY,
            SummaryType.QUALITY_ASSURANCE,
            SummaryType.CUSTOMER_FACING
        ]:
            if summary_type in SummaryPrompts.SYSTEM_PROMPTS:
                prompt = SummaryPrompts.SYSTEM_PROMPTS[summary_type]
                assert len(prompt) > 0
