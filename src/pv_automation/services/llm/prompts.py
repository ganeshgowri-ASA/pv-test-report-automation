"""Prompt templates for PV test analysis"""

from enum import Enum
from typing import Any, Dict, Optional


class PromptType(str, Enum):
    """Types of prompts for different analysis tasks"""

    DEFECT_ANALYSIS = "defect_analysis"
    COMPLIANCE_CHECK = "compliance_check"
    PREDICTIVE_ANALYSIS = "predictive_analysis"
    REPORT_SUMMARY = "report_summary"
    TEST_OPTIMIZATION = "test_optimization"


class PromptTemplate:
    """Base class for prompt templates"""

    def __init__(self, template: str):
        self.template = template

    def format(self, **kwargs: Any) -> str:
        """
        Format the template with provided variables.

        Args:
            **kwargs: Variables to substitute in template

        Returns:
            str: Formatted prompt
        """
        return self.template.format(**kwargs)


class PVAnalysisPrompts:
    """Collection of prompt templates for PV analysis tasks"""

    # System instructions
    SYSTEM_INSTRUCTION = """You are an expert in photovoltaic (PV) module testing and quality assurance.
You have deep knowledge of international standards including IEC 61215, IEC 61730, IEC 61853,
and other relevant PV testing standards. You analyze test data, images, and reports with technical
precision and provide actionable recommendations."""

    # Defect analysis prompts
    DEFECT_ANALYSIS_EL_IMAGE = PromptTemplate(
        """Analyze this Electroluminescence (EL) image of a photovoltaic module and identify any defects or anomalies.

**Image Type:** {image_type}
**Testing Standard:** {standard}
{additional_context}

**Focus on detecting:**
1. **Cell-level defects:**
   - Micro-cracks (single or multiple)
   - Cell breakage or fractures
   - Inactive cell areas (dead cells)
   - Cell interconnection failures

2. **String-level issues:**
   - Broken or disconnected cell strings
   - Reverse polarity
   - Shunts

3. **Module-level defects:**
   - Delamination patterns
   - Encapsulant degradation
   - Bypass diode issues
   - Edge defects

**Provide a structured analysis including:**
1. **Defect Identification:** List each defect with:
   - Type of defect
   - Location (cell position, e.g., "Row 3, Column 5" or "B5")
   - Severity level (Critical/High/Medium/Low/Negligible)
   - Confidence score (0-100%)

2. **Performance Impact:** Estimate the impact on:
   - Power output (percentage loss)
   - Module reliability
   - Long-term degradation risk

3. **Compliance Assessment:** Evaluate against {standard} requirements:
   - Pass/Fail/Conditional status
   - Specific requirements violated (if any)

4. **Recommendations:**
   - Immediate actions required
   - Further testing needed
   - Module disposition (Accept/Reject/Conditional Accept)

**Output Format:**
Provide your analysis in a clear, structured format. Be specific about locations and technical details.
Use engineering terminology appropriate for PV testing professionals."""
    )

    DEFECT_ANALYSIS_THERMAL_IMAGE = PromptTemplate(
        """Analyze this thermal (infrared) image of a photovoltaic module for thermal anomalies and hotspots.

**Image Type:** Thermal/IR
**Testing Standard:** {standard}
{additional_context}

**Focus on detecting:**
1. **Hotspots:**
   - Bypass diode activation
   - Cell-level hotspots
   - Junction box heating
   - Localized heating from shading/soiling

2. **Temperature anomalies:**
   - Abnormal temperature gradients
   - Cold spots (inactive cells)
   - Uniform vs. non-uniform heating

3. **Potential causes:**
   - Series resistance issues
   - Shunt resistance problems
   - Manufacturing defects
   - Installation issues

**Provide analysis including:**
1. **Hotspot Identification:**
   - Location and extent
   - Temperature differential (ΔT)
   - Severity classification
   - Probable cause

2. **Safety Assessment:**
   - Fire risk evaluation
   - Electrical hazard assessment
   - Compliance with IEC 61730 safety requirements

3. **Performance Impact:**
   - Power loss estimation
   - Accelerated degradation risk
   - System-level implications

4. **Recommendations:**
   - Remediation actions
   - Further diagnostic testing
   - Monitoring requirements

Be specific about temperature values if visible in the image."""
    )

    # Compliance checking prompt
    COMPLIANCE_CHECK = PromptTemplate(
        """Review the following PV module test report data against **{standard}** standard requirements.

**Test Report Data:**
{report_data}

**Missing Data Check:** {check_missing}

**Your Task:**
Perform a comprehensive compliance assessment against {standard} requirements.

**Analysis Steps:**
1. **Requirement Mapping:**
   - List all applicable requirements from {standard}
   - Match test data to each requirement
   - Identify gaps in test coverage

2. **Compliance Evaluation:**
   For each requirement, determine:
   - ✓ Pass: Meets requirement
   - ✗ Fail: Does not meet requirement
   - ⚠ Conditional: Meets with conditions/caveats
   - ? Insufficient Data: Cannot determine

3. **Data Completeness:**
   - Identify missing required test data
   - Highlight incomplete or ambiguous results
   - Note any inconsistencies in reported values

4. **Critical Findings:**
   - Flag any safety-critical violations
   - Identify performance requirement failures
   - Note durability/reliability concerns

**Output Requirements:**
Provide:
1. **Overall Compliance Status:** Pass/Fail/Conditional
2. **Specific Violations:** List each requirement not met with:
   - Requirement reference (e.g., "IEC 61215:2016, Section 10.1")
   - Test result vs. required value
   - Severity of violation

3. **Missing Data:** List all required but missing test data

4. **Recommendations:**
   - Additional testing needed
   - Documentation improvements
   - Corrective actions for non-compliance

5. **Certification Readiness:** Assessment of readiness for certification

Be precise with requirement references and technical specifications."""
    )

    # Predictive analysis prompt
    PREDICTIVE_FAILURE_ANALYSIS = PromptTemplate(
        """Perform a predictive failure analysis on this PV module based on test data and degradation patterns.

**Test Data:**
{test_data}

**Module Information:**
- Age: {module_age_years} years
- Warranty Period: {warranty_period_years} years
- Environmental Factors: {environmental_factors}

**Analysis Requirements:**

1. **Degradation Assessment:**
   - Calculate current degradation rate (%/year)
   - Compare to expected/typical rates (0.5-0.8%/year for standard modules)
   - Identify accelerated degradation indicators
   - Analyze degradation linearity vs. non-linear patterns

2. **Failure Probability:**
   Estimate probability of:
   - Power output falling below warranty threshold (typically 80% at 25 years)
   - Critical component failures (bypass diodes, junction box, etc.)
   - Safety-related failures (insulation, grounding)
   - Catastrophic failures (fire, electrical hazard)

3. **Risk Factors:**
   Identify and rank risk factors:
   - Defects found (cracks, hotspots, delamination, etc.)
   - Environmental stress (temperature cycling, humidity, UV exposure)
   - Operational stress (high current, reverse bias, soiling)
   - Manufacturing quality indicators

4. **Degradation Mechanisms:**
   Identify active degradation mechanisms:
   - Potential-Induced Degradation (PID)
   - Light-Induced Degradation (LID)
   - UV degradation
   - Mechanical fatigue
   - Corrosion
   - Delamination progression

5. **Lifespan Estimation:**
   - Expected remaining useful life
   - Probability of meeting warranty guarantees
   - Expected end-of-life power output
   - Confidence intervals for predictions

6. **Preventive Measures:**
   Recommend specific actions to:
   - Slow degradation progression
   - Mitigate identified risks
   - Extend module lifespan
   - Maintain warranty compliance

**Output Format:**
Provide quantitative estimates where possible (e.g., "15% probability of failure within warranty period").
Include confidence scores for predictions and clearly state assumptions made.
Base recommendations on industry best practices and published research."""
    )

    # Report summary prompt
    REPORT_SUMMARY = PromptTemplate(
        """Generate an executive summary for this PV module test report.

**Full Report Data:**
{report_data}

**Target Audience:** {audience}

**Summary Requirements:**

1. **Overview (2-3 sentences):**
   - Module identification
   - Testing scope and standards applied
   - Overall result (Pass/Fail/Conditional)

2. **Key Findings (bullet points):**
   - Critical defects or issues
   - Performance metrics (power, efficiency, etc.)
   - Compliance status
   - Notable strengths or weaknesses

3. **Test Results Summary:**
   Brief summary of each major test category:
   - Visual inspection
   - Electrical performance
   - Mechanical tests
   - Environmental durability
   - Safety tests

4. **Recommendations:**
   - Certification readiness
   - Required follow-up actions
   - Quality improvement suggestions

5. **Risk Assessment:**
   - Identified risks
   - Mitigation status

**Tone:** Professional and technical, but accessible to non-experts
**Length:** Concise summary suitable for management review
**Format:** Well-structured with clear sections and bullet points"""
    )

    # Test optimization prompt
    TEST_OPTIMIZATION = PromptTemplate(
        """Analyze this PV testing data and provide recommendations for test parameter optimization.

**Current Test Configuration:**
{current_config}

**Test Results:**
{test_results}

**Optimization Goals:**
{optimization_goals}

**Analysis Focus:**

1. **Test Coverage:**
   - Identify gaps in current testing
   - Suggest additional tests for better defect detection
   - Recommend optimal test sequence

2. **Parameter Optimization:**
   For each test:
   - Evaluate current parameters (voltage, current, duration, cycles, etc.)
   - Suggest optimizations for:
     * Improved defect sensitivity
     * Reduced testing time
     * Better repeatability
     * Cost effectiveness

3. **Testing Efficiency:**
   - Identify redundant or low-value tests
   - Suggest parallelization opportunities
   - Recommend automation potential

4. **Quality Improvements:**
   - Enhanced measurement accuracy
   - Better environmental controls
   - Improved documentation
   - Data analysis enhancements

5. **Standards Alignment:**
   - Ensure compliance with latest standard revisions
   - Adopt best practices from industry leaders
   - Consider emerging requirements (e.g., bifacial modules, half-cut cells)

**Deliverables:**
1. Prioritized list of optimization recommendations
2. Expected impact of each recommendation (time, cost, quality)
3. Implementation difficulty (Easy/Medium/Hard)
4. ROI estimation for major changes

Be specific with parameter values and provide technical justification."""
    )

    @staticmethod
    def get_defect_analysis_prompt(
        image_type: str,
        standard: str = "IEC 61215",
        additional_context: Optional[str] = None,
    ) -> str:
        """
        Get defect analysis prompt for image analysis.

        Args:
            image_type: Type of image (EL, thermal, visual)
            standard: Testing standard to reference
            additional_context: Additional context for analysis

        Returns:
            str: Formatted prompt
        """
        context_str = (
            f"\n**Additional Context:** {additional_context}" if additional_context else ""
        )

        if image_type.upper() in ["EL", "ELECTROLUMINESCENCE"]:
            return PVAnalysisPrompts.DEFECT_ANALYSIS_EL_IMAGE.format(
                image_type=image_type,
                standard=standard,
                additional_context=context_str,
            )
        elif image_type.upper() in ["THERMAL", "IR", "INFRARED"]:
            return PVAnalysisPrompts.DEFECT_ANALYSIS_THERMAL_IMAGE.format(
                standard=standard,
                additional_context=context_str,
            )
        else:
            # Generic visual inspection prompt
            return PVAnalysisPrompts.DEFECT_ANALYSIS_EL_IMAGE.format(
                image_type=image_type,
                standard=standard,
                additional_context=context_str,
            )

    @staticmethod
    def get_compliance_check_prompt(
        report_data: Dict[str, Any],
        standard: str,
        check_missing: bool = True,
    ) -> str:
        """
        Get compliance checking prompt.

        Args:
            report_data: Test report data dictionary
            standard: Standard to check against
            check_missing: Whether to check for missing data

        Returns:
            str: Formatted prompt
        """
        import json

        report_json = json.dumps(report_data, indent=2)
        return PVAnalysisPrompts.COMPLIANCE_CHECK.format(
            standard=standard,
            report_data=report_json,
            check_missing="Enabled" if check_missing else "Disabled",
        )

    @staticmethod
    def get_predictive_analysis_prompt(
        test_data: Dict[str, Any],
        module_age_years: Optional[float] = None,
        environmental_factors: Optional[Dict[str, Any]] = None,
        warranty_period_years: int = 25,
    ) -> str:
        """
        Get predictive failure analysis prompt.

        Args:
            test_data: Historical and current test data
            module_age_years: Age of module in years
            environmental_factors: Environmental conditions
            warranty_period_years: Warranty period

        Returns:
            str: Formatted prompt
        """
        import json

        test_json = json.dumps(test_data, indent=2)
        env_json = json.dumps(environmental_factors or {}, indent=2)
        age_str = f"{module_age_years}" if module_age_years is not None else "Unknown"

        return PVAnalysisPrompts.PREDICTIVE_FAILURE_ANALYSIS.format(
            test_data=test_json,
            module_age_years=age_str,
            environmental_factors=env_json,
            warranty_period_years=warranty_period_years,
        )

    @staticmethod
    def get_report_summary_prompt(
        report_data: Dict[str, Any],
        audience: str = "technical management",
    ) -> str:
        """
        Get report summary generation prompt.

        Args:
            report_data: Complete report data
            audience: Target audience for summary

        Returns:
            str: Formatted prompt
        """
        import json

        report_json = json.dumps(report_data, indent=2)
        return PVAnalysisPrompts.REPORT_SUMMARY.format(
            report_data=report_json,
            audience=audience,
        )

    @staticmethod
    def get_test_optimization_prompt(
        current_config: Dict[str, Any],
        test_results: Dict[str, Any],
        optimization_goals: str = "Improve defect detection while reducing test time",
    ) -> str:
        """
        Get test optimization prompt.

        Args:
            current_config: Current test configuration
            test_results: Recent test results
            optimization_goals: Optimization objectives

        Returns:
            str: Formatted prompt
        """
        import json

        config_json = json.dumps(current_config, indent=2)
        results_json = json.dumps(test_results, indent=2)

        return PVAnalysisPrompts.TEST_OPTIMIZATION.format(
            current_config=config_json,
            test_results=results_json,
            optimization_goals=optimization_goals,
        )
