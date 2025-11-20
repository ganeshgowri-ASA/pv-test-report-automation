"""
AI-Powered Compliance Checker Module

Provides compliance verification against PV testing standards using LLMs,
including requirement extraction, gap analysis, and recommendations.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

from .gpt_integration import GPTIntegration, GPTResponse, PromptTemplate
from .llm_config import get_config, LLMConfig, ModelType

logger = logging.getLogger(__name__)


class ComplianceStatus(Enum):
    """Compliance status levels."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    NOT_APPLICABLE = "not_applicable"
    INSUFFICIENT_DATA = "insufficient_data"


class SeverityLevel(Enum):
    """Severity levels for compliance gaps."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class StandardRequirement:
    """Represents a standard requirement."""
    id: str
    standard: str
    section: str
    description: str
    category: str
    mandatory: bool = True
    test_methods: List[str] = field(default_factory=list)
    acceptance_criteria: str = ""


@dataclass
class ComplianceGap:
    """Represents a compliance gap."""
    requirement_id: str
    requirement_description: str
    severity: SeverityLevel
    current_state: str
    expected_state: str
    recommendation: str
    citations: List[str] = field(default_factory=list)


@dataclass
class ComplianceResult:
    """Result of compliance check."""
    standard: str
    overall_status: ComplianceStatus
    compliance_rate: float  # Percentage
    requirements_checked: int
    compliant_count: int
    non_compliant_count: int
    partial_count: int
    gaps: List[ComplianceGap]
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'standard': self.standard,
            'overall_status': self.overall_status.value,
            'compliance_rate': self.compliance_rate,
            'requirements_checked': self.requirements_checked,
            'compliant_count': self.compliant_count,
            'non_compliant_count': self.non_compliant_count,
            'partial_count': self.partial_count,
            'gaps': [
                {
                    'requirement_id': gap.requirement_id,
                    'requirement_description': gap.requirement_description,
                    'severity': gap.severity.value,
                    'current_state': gap.current_state,
                    'expected_state': gap.expected_state,
                    'recommendation': gap.recommendation,
                    'citations': gap.citations
                }
                for gap in self.gaps
            ],
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


class StandardsDatabase:
    """Database of PV testing standards and requirements."""

    # IEC 61215: Terrestrial PV modules - Design qualification and type approval
    IEC_61215_REQUIREMENTS = [
        StandardRequirement(
            id="IEC61215-10.1",
            standard="IEC 61215",
            section="10.1",
            description="Visual Inspection",
            category="Initial Tests",
            mandatory=True,
            test_methods=["Visual inspection"],
            acceptance_criteria="No visual defects as defined in 10.1"
        ),
        StandardRequirement(
            id="IEC61215-10.2",
            standard="IEC 61215",
            section="10.2",
            description="Maximum Power Determination",
            category="Initial Tests",
            mandatory=True,
            test_methods=["STC measurement"],
            acceptance_criteria="Pmax within ±3% of rated power"
        ),
        StandardRequirement(
            id="IEC61215-10.8",
            standard="IEC 61215",
            section="10.8",
            description="Thermal Cycling",
            category="Environmental Tests",
            mandatory=True,
            test_methods=["200 thermal cycles: -40°C to +85°C"],
            acceptance_criteria="Pmax degradation ≤5%, no major visual defects"
        ),
        StandardRequirement(
            id="IEC61215-10.11",
            standard="IEC 61215",
            section="10.11",
            description="Damp Heat Test",
            category="Environmental Tests",
            mandatory=True,
            test_methods=["1000 hours at 85°C and 85% RH"],
            acceptance_criteria="Pmax degradation ≤5%, insulation resistance >40MΩ"
        ),
        StandardRequirement(
            id="IEC61215-10.13",
            standard="IEC 61215",
            section="10.13",
            description="Humidity Freeze",
            category="Environmental Tests",
            mandatory=True,
            test_methods=["10 cycles: +85°C/85%RH to -40°C"],
            acceptance_criteria="Pmax degradation ≤5%, no major visual defects"
        ),
        StandardRequirement(
            id="IEC61215-10.16",
            standard="IEC 61215",
            section="10.16",
            description="Mechanical Load Test",
            category="Mechanical Tests",
            mandatory=True,
            test_methods=["Static/dynamic mechanical loading"],
            acceptance_criteria="Pmax degradation ≤5%, no breakage"
        ),
    ]

    # IEC 61730: PV module safety qualification
    IEC_61730_REQUIREMENTS = [
        StandardRequirement(
            id="IEC61730-MST-01",
            standard="IEC 61730",
            section="MST-01",
            description="Continuity of Grounding",
            category="Safety Tests",
            mandatory=True,
            acceptance_criteria="Resistance <0.1Ω between terminals"
        ),
        StandardRequirement(
            id="IEC61730-MST-23",
            standard="IEC 61730",
            section="MST-23",
            description="Wet Leakage Current",
            category="Safety Tests",
            mandatory=True,
            acceptance_criteria="Leakage current <3.5mA"
        ),
    ]

    @classmethod
    def get_requirements(cls, standard: str) -> List[StandardRequirement]:
        """Get requirements for a standard."""
        standard_upper = standard.upper().replace(" ", "")

        if "IEC61215" in standard_upper:
            return cls.IEC_61215_REQUIREMENTS
        elif "IEC61730" in standard_upper:
            return cls.IEC_61730_REQUIREMENTS
        else:
            return []


class CompliancePrompts:
    """Specialized prompts for compliance checking."""

    @staticmethod
    def format_requirement_extraction(
        report_data: Dict[str, Any],
        requirements: List[StandardRequirement]
    ) -> str:
        """Format prompt for requirement extraction."""
        req_list = "\n".join([
            f"- {req.id}: {req.description} (Section {req.section})"
            for req in requirements
        ])

        return f"""Analyze this PV test report and determine compliance with the following requirements:

{req_list}

Report Data:
{json.dumps(report_data, indent=2)}

For each requirement, provide:
1. Compliance status (compliant/non_compliant/partial/not_applicable/insufficient_data)
2. Evidence found in the report
3. Specific values or findings that support the determination
4. Any gaps or missing information

Return your analysis as a JSON array with this structure:
[
  {{
    "requirement_id": "...",
    "status": "...",
    "evidence": "...",
    "findings": "...",
    "gaps": ["..."]
  }}
]"""

    @staticmethod
    def format_gap_analysis(
        requirement: StandardRequirement,
        current_state: str
    ) -> str:
        """Format prompt for gap analysis."""
        return f"""Analyze the compliance gap for this requirement:

Requirement: {requirement.id} - {requirement.description}
Standard: {requirement.standard}, Section {requirement.section}
Acceptance Criteria: {requirement.acceptance_criteria}

Current State from Report:
{current_state}

Provide:
1. Severity level (critical/high/medium/low/info)
2. Detailed description of the gap
3. Specific recommendations to achieve compliance
4. Relevant standard citations

Return as JSON:
{{
  "severity": "...",
  "gap_description": "...",
  "recommendations": ["..."],
  "citations": ["..."]
}}"""

    @staticmethod
    def format_compliance_summary(
        results: List[Dict[str, Any]],
        standard: str
    ) -> str:
        """Format prompt for compliance summary."""
        return f"""Summarize the overall compliance status for {standard} based on these requirement checks:

{json.dumps(results, indent=2)}

Provide:
1. Overall compliance assessment
2. Key compliance achievements
3. Critical gaps that need immediate attention
4. Recommendations for achieving full compliance
5. Estimated effort for remediation

Keep the summary concise and actionable."""


class ComplianceChecker:
    """AI-powered compliance checker for PV test reports."""

    def __init__(
        self,
        config: Optional[LLMConfig] = None,
        model_type: ModelType = ModelType.GPT_4_TURBO
    ):
        """
        Initialize compliance checker.

        Args:
            config: LLM configuration
            model_type: Model to use for compliance checking
        """
        self.config = config or get_config()
        self.gpt = GPTIntegration(config, model_type)
        self.standards_db = StandardsDatabase()

    async def check_compliance(
        self,
        report_data: Dict[str, Any],
        standard: str,
        custom_requirements: Optional[List[StandardRequirement]] = None
    ) -> ComplianceResult:
        """
        Check report compliance against a standard.

        Args:
            report_data: Report data dictionary
            standard: Standard name (e.g., "IEC 61215")
            custom_requirements: Optional custom requirements

        Returns:
            ComplianceResult object
        """
        # Get requirements
        requirements = custom_requirements or self.standards_db.get_requirements(standard)

        if not requirements:
            logger.warning(f"No requirements found for standard: {standard}")
            return ComplianceResult(
                standard=standard,
                overall_status=ComplianceStatus.INSUFFICIENT_DATA,
                compliance_rate=0.0,
                requirements_checked=0,
                compliant_count=0,
                non_compliant_count=0,
                partial_count=0,
                gaps=[]
            )

        # Extract requirement compliance
        extraction_results = await self._extract_requirement_compliance(
            report_data,
            requirements
        )

        # Analyze gaps for non-compliant items
        gaps = await self._analyze_gaps(extraction_results, requirements)

        # Calculate compliance metrics
        status_counts = {
            ComplianceStatus.COMPLIANT: 0,
            ComplianceStatus.NON_COMPLIANT: 0,
            ComplianceStatus.PARTIAL: 0,
            ComplianceStatus.NOT_APPLICABLE: 0,
            ComplianceStatus.INSUFFICIENT_DATA: 0
        }

        for result in extraction_results:
            status = ComplianceStatus(result['status'])
            status_counts[status] += 1

        # Calculate compliance rate (excluding N/A and insufficient data)
        checkable = (
            status_counts[ComplianceStatus.COMPLIANT] +
            status_counts[ComplianceStatus.NON_COMPLIANT] +
            status_counts[ComplianceStatus.PARTIAL]
        )

        if checkable > 0:
            compliance_rate = (
                (status_counts[ComplianceStatus.COMPLIANT] +
                 0.5 * status_counts[ComplianceStatus.PARTIAL]) /
                checkable * 100
            )
        else:
            compliance_rate = 0.0

        # Determine overall status
        if status_counts[ComplianceStatus.NON_COMPLIANT] > 0:
            overall_status = ComplianceStatus.NON_COMPLIANT
        elif status_counts[ComplianceStatus.PARTIAL] > 0:
            overall_status = ComplianceStatus.PARTIAL
        elif status_counts[ComplianceStatus.COMPLIANT] > 0:
            overall_status = ComplianceStatus.COMPLIANT
        else:
            overall_status = ComplianceStatus.INSUFFICIENT_DATA

        return ComplianceResult(
            standard=standard,
            overall_status=overall_status,
            compliance_rate=compliance_rate,
            requirements_checked=len(requirements),
            compliant_count=status_counts[ComplianceStatus.COMPLIANT],
            non_compliant_count=status_counts[ComplianceStatus.NON_COMPLIANT],
            partial_count=status_counts[ComplianceStatus.PARTIAL],
            gaps=gaps,
            metadata={
                'not_applicable': status_counts[ComplianceStatus.NOT_APPLICABLE],
                'insufficient_data': status_counts[ComplianceStatus.INSUFFICIENT_DATA]
            }
        )

    async def _extract_requirement_compliance(
        self,
        report_data: Dict[str, Any],
        requirements: List[StandardRequirement]
    ) -> List[Dict[str, Any]]:
        """Extract compliance status for each requirement."""
        prompt = CompliancePrompts.format_requirement_extraction(
            report_data,
            requirements
        )

        messages = [
            {
                "role": "system",
                "content": PromptTemplate.SYSTEM_PROMPTS['compliance_check']
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        response = await self.gpt.complete_async(
            messages,
            temperature=0.3,  # Lower temperature for more consistent results
            response_format={"type": "json_object"}
        )

        try:
            # Parse JSON response
            content = response.content
            # Handle if wrapped in markdown code block
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]

            result = json.loads(content)

            # Handle both array and object with array
            if isinstance(result, dict) and 'requirements' in result:
                return result['requirements']
            elif isinstance(result, list):
                return result
            else:
                logger.error(f"Unexpected response format: {result}")
                return []

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse compliance extraction: {e}")
            logger.error(f"Response: {response.content}")
            return []

    async def _analyze_gaps(
        self,
        extraction_results: List[Dict[str, Any]],
        requirements: List[StandardRequirement]
    ) -> List[ComplianceGap]:
        """Analyze gaps for non-compliant requirements."""
        gaps = []
        req_map = {req.id: req for req in requirements}

        # Identify non-compliant and partial items
        gap_items = [
            result for result in extraction_results
            if result['status'] in ['non_compliant', 'partial']
        ]

        # Analyze each gap
        gap_tasks = [
            self._analyze_single_gap(item, req_map[item['requirement_id']])
            for item in gap_items
            if item['requirement_id'] in req_map
        ]

        if gap_tasks:
            gaps = await asyncio.gather(*gap_tasks)

        return [g for g in gaps if g is not None]

    async def _analyze_single_gap(
        self,
        result: Dict[str, Any],
        requirement: StandardRequirement
    ) -> Optional[ComplianceGap]:
        """Analyze a single compliance gap."""
        current_state = f"""
Status: {result['status']}
Evidence: {result.get('evidence', 'None')}
Findings: {result.get('findings', 'None')}
Gaps: {', '.join(result.get('gaps', []))}
"""

        prompt = CompliancePrompts.format_gap_analysis(requirement, current_state)

        messages = [
            {
                "role": "system",
                "content": "You are a compliance gap analysis specialist."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        try:
            response = await self.gpt.complete_async(
                messages,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            gap_data = json.loads(response.content)

            return ComplianceGap(
                requirement_id=requirement.id,
                requirement_description=requirement.description,
                severity=SeverityLevel(gap_data['severity']),
                current_state=current_state.strip(),
                expected_state=requirement.acceptance_criteria,
                recommendation=gap_data.get('gap_description', ''),
                citations=gap_data.get('citations', [])
            )

        except Exception as e:
            logger.error(f"Failed to analyze gap for {requirement.id}: {e}")
            return None

    async def generate_compliance_report(
        self,
        compliance_results: List[ComplianceResult]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive compliance report.

        Args:
            compliance_results: List of compliance results for different standards

        Returns:
            Comprehensive report dictionary
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'standards_checked': [r.standard for r in compliance_results],
            'overall_compliance': {},
            'standards': {},
            'critical_gaps': [],
            'recommendations': []
        }

        # Process each standard
        for result in compliance_results:
            report['standards'][result.standard] = result.to_dict()

            # Collect critical gaps
            critical_gaps = [
                gap for gap in result.gaps
                if gap.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]
            ]
            report['critical_gaps'].extend([
                {
                    'standard': result.standard,
                    **gap.__dict__
                }
                for gap in critical_gaps
            ])

        # Calculate overall metrics
        total_requirements = sum(r.requirements_checked for r in compliance_results)
        total_compliant = sum(r.compliant_count for r in compliance_results)

        if total_requirements > 0:
            overall_rate = (total_compliant / total_requirements) * 100
            report['overall_compliance'] = {
                'rate': overall_rate,
                'total_requirements': total_requirements,
                'total_compliant': total_compliant,
                'total_gaps': len(report['critical_gaps'])
            }

        return report

    def export_compliance_report(
        self,
        report: Dict[str, Any],
        output_path: str,
        format: str = 'json'
    ):
        """
        Export compliance report to file.

        Args:
            report: Compliance report dictionary
            output_path: Output file path
            format: Output format (json, html, pdf)
        """
        from pathlib import Path
        output_path = Path(output_path)

        if format == 'json':
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Compliance report exported to {output_path}")

        else:
            logger.warning(f"Format {format} not yet implemented")
