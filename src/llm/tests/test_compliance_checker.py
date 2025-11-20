"""
Unit tests for Compliance Checker Module
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import json
import tempfile
from pathlib import Path

from ..compliance_checker import (
    ComplianceChecker,
    ComplianceResult,
    ComplianceStatus,
    ComplianceGap,
    SeverityLevel,
    StandardRequirement,
    StandardsDatabase,
    CompliancePrompts
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


class TestStandardRequirement:
    """Test StandardRequirement dataclass."""

    def test_requirement_creation(self):
        """Test creating a standard requirement."""
        req = StandardRequirement(
            id="IEC61215-10.1",
            standard="IEC 61215",
            section="10.1",
            description="Visual Inspection",
            category="Initial Tests"
        )

        assert req.id == "IEC61215-10.1"
        assert req.standard == "IEC 61215"
        assert req.mandatory is True
        assert isinstance(req.test_methods, list)


class TestComplianceGap:
    """Test ComplianceGap dataclass."""

    def test_gap_creation(self):
        """Test creating a compliance gap."""
        gap = ComplianceGap(
            requirement_id="IEC61215-10.1",
            requirement_description="Visual Inspection",
            severity=SeverityLevel.HIGH,
            current_state="Not performed",
            expected_state="Visual inspection required",
            recommendation="Perform visual inspection"
        )

        assert gap.severity == SeverityLevel.HIGH
        assert isinstance(gap.citations, list)


class TestComplianceResult:
    """Test ComplianceResult dataclass."""

    def test_result_creation(self):
        """Test creating a compliance result."""
        result = ComplianceResult(
            standard="IEC 61215",
            overall_status=ComplianceStatus.COMPLIANT,
            compliance_rate=95.0,
            requirements_checked=10,
            compliant_count=9,
            non_compliant_count=1,
            partial_count=0,
            gaps=[]
        )

        assert result.standard == "IEC 61215"
        assert result.overall_status == ComplianceStatus.COMPLIANT
        assert result.compliance_rate == 95.0

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        gap = ComplianceGap(
            requirement_id="TEST-1",
            requirement_description="Test",
            severity=SeverityLevel.LOW,
            current_state="Current",
            expected_state="Expected",
            recommendation="Fix it"
        )

        result = ComplianceResult(
            standard="IEC 61215",
            overall_status=ComplianceStatus.PARTIAL,
            compliance_rate=75.0,
            requirements_checked=4,
            compliant_count=3,
            non_compliant_count=1,
            partial_count=0,
            gaps=[gap]
        )

        data = result.to_dict()

        assert data['standard'] == "IEC 61215"
        assert data['overall_status'] == "partial"
        assert data['compliance_rate'] == 75.0
        assert len(data['gaps']) == 1
        assert data['gaps'][0]['severity'] == 'low'


class TestStandardsDatabase:
    """Test StandardsDatabase."""

    def test_get_iec_61215_requirements(self):
        """Test getting IEC 61215 requirements."""
        requirements = StandardsDatabase.get_requirements("IEC 61215")

        assert len(requirements) > 0
        assert all(isinstance(req, StandardRequirement) for req in requirements)
        assert all(req.standard == "IEC 61215" for req in requirements)

    def test_get_iec_61730_requirements(self):
        """Test getting IEC 61730 requirements."""
        requirements = StandardsDatabase.get_requirements("IEC 61730")

        assert len(requirements) > 0
        assert all(req.standard == "IEC 61730" for req in requirements)

    def test_get_unknown_standard(self):
        """Test getting requirements for unknown standard."""
        requirements = StandardsDatabase.get_requirements("UNKNOWN-STD")

        assert len(requirements) == 0

    def test_requirement_structure(self):
        """Test that requirements have proper structure."""
        requirements = StandardsDatabase.get_requirements("IEC 61215")

        for req in requirements:
            assert req.id
            assert req.standard
            assert req.section
            assert req.description
            assert req.category
            assert isinstance(req.mandatory, bool)


class TestCompliancePrompts:
    """Test CompliancePrompts."""

    def test_format_requirement_extraction(self):
        """Test formatting requirement extraction prompt."""
        report_data = {'module_id': 'TEST-001'}
        requirements = [
            StandardRequirement(
                id="TEST-1",
                standard="TEST",
                section="1",
                description="Test requirement",
                category="Test"
            )
        ]

        prompt = CompliancePrompts.format_requirement_extraction(
            report_data,
            requirements
        )

        assert 'TEST-1' in prompt
        assert 'Test requirement' in prompt
        assert 'compliance' in prompt.lower()
        assert 'JSON' in prompt

    def test_format_gap_analysis(self):
        """Test formatting gap analysis prompt."""
        req = StandardRequirement(
            id="TEST-1",
            standard="TEST",
            section="1",
            description="Test requirement",
            category="Test",
            acceptance_criteria="Must pass"
        )

        current_state = "Failed test"

        prompt = CompliancePrompts.format_gap_analysis(req, current_state)

        assert 'TEST-1' in prompt
        assert current_state in prompt
        assert 'severity' in prompt.lower()
        assert 'JSON' in prompt

    def test_format_compliance_summary(self):
        """Test formatting compliance summary prompt."""
        results = [
            {
                'requirement_id': 'TEST-1',
                'status': 'compliant'
            }
        ]

        prompt = CompliancePrompts.format_compliance_summary(
            results,
            "IEC 61215"
        )

        assert 'IEC 61215' in prompt
        assert 'TEST-1' in prompt
        assert 'compliance' in prompt.lower()


class TestComplianceChecker:
    """Test ComplianceChecker functionality."""

    @patch('src.llm.compliance_checker.GPTIntegration')
    def test_initialization(self, mock_gpt_class, mock_config):
        """Test compliance checker initialization."""
        checker = ComplianceChecker(mock_config, ModelType.GPT_4_TURBO)

        assert checker.config == mock_config
        assert mock_gpt_class.called

    @patch('src.llm.compliance_checker.GPTIntegration')
    @pytest.mark.asyncio
    async def test_check_compliance_no_requirements(self, mock_gpt_class, mock_config):
        """Test compliance check with no requirements."""
        checker = ComplianceChecker(mock_config)

        report_data = {'module_id': 'TEST-001'}

        result = await checker.check_compliance(
            report_data,
            "UNKNOWN-STANDARD"
        )

        assert result.overall_status == ComplianceStatus.INSUFFICIENT_DATA
        assert result.requirements_checked == 0

    @patch('src.llm.compliance_checker.GPTIntegration')
    @pytest.mark.asyncio
    async def test_check_compliance_with_requirements(self, mock_gpt_class, mock_config):
        """Test compliance check with requirements."""
        # Mock GPT responses
        mock_gpt = Mock()

        # Mock requirement extraction response
        extraction_response = GPTResponse(
            content=json.dumps([
                {
                    'requirement_id': 'IEC61215-10.1',
                    'status': 'compliant',
                    'evidence': 'Visual inspection passed',
                    'findings': 'No defects found',
                    'gaps': []
                },
                {
                    'requirement_id': 'IEC61215-10.2',
                    'status': 'non_compliant',
                    'evidence': 'Power measurement failed',
                    'findings': 'Below spec',
                    'gaps': ['Power output too low']
                }
            ]),
            model="gpt-4",
            tokens_input=100,
            tokens_output=50,
            cost=0.5
        )

        # Mock gap analysis response
        gap_response = GPTResponse(
            content=json.dumps({
                'severity': 'high',
                'gap_description': 'Power output below specification',
                'recommendations': ['Investigate module performance'],
                'citations': ['IEC 61215-10.2']
            }),
            model="gpt-4",
            tokens_input=50,
            tokens_output=30,
            cost=0.3
        )

        mock_gpt.complete_async = AsyncMock(
            side_effect=[extraction_response, gap_response]
        )
        mock_gpt_class.return_value = mock_gpt

        checker = ComplianceChecker(mock_config)

        report_data = {'module_id': 'TEST-001'}

        result = await checker.check_compliance(
            report_data,
            "IEC 61215"
        )

        assert isinstance(result, ComplianceResult)
        assert result.standard == "IEC 61215"
        assert result.requirements_checked > 0
        assert result.overall_status == ComplianceStatus.NON_COMPLIANT

    @patch('src.llm.compliance_checker.GPTIntegration')
    @pytest.mark.asyncio
    async def test_extract_requirement_compliance(self, mock_gpt_class, mock_config):
        """Test requirement compliance extraction."""
        mock_gpt = Mock()
        mock_gpt.complete_async = AsyncMock(
            return_value=GPTResponse(
                content=json.dumps([
                    {
                        'requirement_id': 'TEST-1',
                        'status': 'compliant',
                        'evidence': 'Test passed',
                        'findings': 'OK',
                        'gaps': []
                    }
                ]),
                model="gpt-4",
                tokens_input=100,
                tokens_output=50,
                cost=0.5
            )
        )
        mock_gpt_class.return_value = mock_gpt

        checker = ComplianceChecker(mock_config)

        requirements = [
            StandardRequirement(
                id="TEST-1",
                standard="TEST",
                section="1",
                description="Test",
                category="Test"
            )
        ]

        results = await checker._extract_requirement_compliance(
            {'test': 'data'},
            requirements
        )

        assert len(results) == 1
        assert results[0]['requirement_id'] == 'TEST-1'
        assert results[0]['status'] == 'compliant'

    @patch('src.llm.compliance_checker.GPTIntegration')
    @pytest.mark.asyncio
    async def test_analyze_single_gap(self, mock_gpt_class, mock_config):
        """Test analyzing a single gap."""
        mock_gpt = Mock()
        mock_gpt.complete_async = AsyncMock(
            return_value=GPTResponse(
                content=json.dumps({
                    'severity': 'critical',
                    'gap_description': 'Critical failure',
                    'recommendations': ['Fix immediately'],
                    'citations': ['TEST-1']
                }),
                model="gpt-4",
                tokens_input=50,
                tokens_output=30,
                cost=0.3
            )
        )
        mock_gpt_class.return_value = mock_gpt

        checker = ComplianceChecker(mock_config)

        result = {
            'requirement_id': 'TEST-1',
            'status': 'non_compliant',
            'evidence': 'Failed',
            'findings': 'Test failed',
            'gaps': ['Major issue']
        }

        requirement = StandardRequirement(
            id="TEST-1",
            standard="TEST",
            section="1",
            description="Test",
            category="Test",
            acceptance_criteria="Must pass"
        )

        gap = await checker._analyze_single_gap(result, requirement)

        assert isinstance(gap, ComplianceGap)
        assert gap.severity == SeverityLevel.CRITICAL
        assert gap.requirement_id == 'TEST-1'

    @patch('src.llm.compliance_checker.GPTIntegration')
    @pytest.mark.asyncio
    async def test_generate_compliance_report(self, mock_gpt_class, mock_config):
        """Test generating comprehensive compliance report."""
        checker = ComplianceChecker(mock_config)

        results = [
            ComplianceResult(
                standard="IEC 61215",
                overall_status=ComplianceStatus.PARTIAL,
                compliance_rate=80.0,
                requirements_checked=10,
                compliant_count=8,
                non_compliant_count=2,
                partial_count=0,
                gaps=[
                    ComplianceGap(
                        requirement_id="TEST-1",
                        requirement_description="Test",
                        severity=SeverityLevel.CRITICAL,
                        current_state="Failed",
                        expected_state="Pass",
                        recommendation="Fix"
                    )
                ]
            )
        ]

        report = await checker.generate_compliance_report(results)

        assert 'timestamp' in report
        assert 'IEC 61215' in report['standards_checked']
        assert 'IEC 61215' in report['standards']
        assert len(report['critical_gaps']) == 1
        assert report['overall_compliance']['total_requirements'] == 10

    @patch('src.llm.compliance_checker.GPTIntegration')
    def test_export_compliance_report(self, mock_gpt_class, mock_config):
        """Test exporting compliance report."""
        checker = ComplianceChecker(mock_config)

        report = {
            'timestamp': '2024-01-01T00:00:00',
            'standards_checked': ['IEC 61215'],
            'overall_compliance': {'rate': 85.0}
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "compliance_report.json"

            checker.export_compliance_report(report, str(output_path), format='json')

            assert output_path.exists()

            with open(output_path, 'r') as f:
                loaded = json.load(f)
                assert loaded['overall_compliance']['rate'] == 85.0


class TestComplianceCalculations:
    """Test compliance calculation logic."""

    def test_compliance_rate_calculation(self):
        """Test compliance rate calculation."""
        # 80% compliant (8 out of 10)
        result = ComplianceResult(
            standard="TEST",
            overall_status=ComplianceStatus.PARTIAL,
            compliance_rate=80.0,
            requirements_checked=10,
            compliant_count=8,
            non_compliant_count=2,
            partial_count=0,
            gaps=[]
        )

        assert result.compliance_rate == 80.0

    def test_overall_status_logic(self):
        """Test overall status determination."""
        # Should be NON_COMPLIANT if any non-compliant
        assert ComplianceStatus.NON_COMPLIANT.value == "non_compliant"

        # Should be PARTIAL if any partial and no non-compliant
        assert ComplianceStatus.PARTIAL.value == "partial"

        # Should be COMPLIANT if all compliant
        assert ComplianceStatus.COMPLIANT.value == "compliant"


@pytest.mark.asyncio
class TestComplianceAsyncOperations:
    """Test async compliance operations."""

    @patch('src.llm.compliance_checker.GPTIntegration')
    async def test_concurrent_gap_analysis(self, mock_gpt_class, mock_config):
        """Test analyzing multiple gaps concurrently."""
        mock_gpt = Mock()
        mock_gpt.complete_async = AsyncMock(
            return_value=GPTResponse(
                content=json.dumps({
                    'severity': 'medium',
                    'gap_description': 'Issue found',
                    'recommendations': ['Fix it'],
                    'citations': []
                }),
                model="gpt-4",
                tokens_input=50,
                tokens_output=30,
                cost=0.3
            )
        )
        mock_gpt_class.return_value = mock_gpt

        checker = ComplianceChecker(mock_config)

        extraction_results = [
            {
                'requirement_id': f'TEST-{i}',
                'status': 'non_compliant',
                'evidence': 'Failed',
                'findings': 'Issue',
                'gaps': ['Gap']
            }
            for i in range(3)
        ]

        requirements = [
            StandardRequirement(
                id=f"TEST-{i}",
                standard="TEST",
                section=str(i),
                description=f"Test {i}",
                category="Test"
            )
            for i in range(3)
        ]

        gaps = await checker._analyze_gaps(extraction_results, requirements)

        assert len(gaps) == 3
        assert all(isinstance(gap, ComplianceGap) for gap in gaps)
