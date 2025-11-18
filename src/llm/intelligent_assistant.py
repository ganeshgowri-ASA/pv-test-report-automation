"""
Intelligent AI assistant for PV testing operations.

Features:
- Answer questions about test procedures
- Suggest test sequences based on module type
- Provide standard interpretation guidance
- Equipment calibration reminders
- Troubleshooting assistance
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from src.config.settings import get_settings
from src.llm.claude_client import ClaudeClient
from src.logging.logger import get_logger
from src.models.test_report import ModuleType, StandardType


class AssistantMode(str, Enum):
    """Assistant operation modes."""

    PROCEDURE_HELP = "procedure_help"  # Test procedure guidance
    STANDARD_INTERPRETATION = "standard_interpretation"  # Standard interpretation
    TEST_PLANNING = "test_planning"  # Test sequence planning
    TROUBLESHOOTING = "troubleshooting"  # Problem diagnosis
    CALIBRATION = "calibration"  # Equipment calibration
    QUALITY_ASSURANCE = "quality_assurance"  # QA guidance
    GENERAL = "general"  # General questions


class IntelligentAssistant:
    """
    Claude AI-powered intelligent assistant for PV testing operations.

    Provides expert guidance on:
    - Testing procedures and methodologies
    - Standard requirements interpretation
    - Test sequence optimization
    - Equipment calibration schedules
    - Troubleshooting common issues
    """

    # Knowledge base of common procedures
    KNOWLEDGE_BASE = {
        "visual_inspection": """Visual inspection per IEC 61215:
1. Inspect module under natural or artificial light (minimum 500 lux)
2. Check for:
   - Cracks, chips, or scratches on cells or glass
   - Delamination or bubbles in encapsulant
   - Broken or loose solder bonds
   - Discoloration or corrosion
   - Junction box integrity
   - Frame damage or sharp edges
3. Document all defects with photographs
4. Verify manufacturer labeling is intact and legible""",
        "thermal_cycling": """Thermal Cycling Test (IEC 61215):
Temperature cycle: -40°C to +85°C
Number of cycles: 200 cycles (IEC 61215-1)
Cycle profile:
- Ramp from ambient to high temp: ≤ 100 min
- High temp dwell (+85°C): ≥ 30 min
- Ramp to low temp (-40°C): ≤ 100 min
- Low temp dwell: ≥ 30 min
- Return to ambient: ≤ 100 min
Requirements: Max power degradation ≤ 5%""",
        "damp_heat": """Damp Heat Test (IEC 61215):
Conditions: 85°C, 85% RH
Duration: 1000 hours
Chamber requirements:
- Temperature tolerance: ±2°C
- Humidity tolerance: ±5% RH
- Air circulation: Yes
Pre-test: Measure max power, Isc, Voc
Post-test: Measure within 2 hours of removal
Acceptance: Max power degradation ≤ 5%""",
    }

    # Module-specific test sequences
    TEST_SEQUENCES = {
        ModuleType.CRYSTALLINE_SILICON: [
            "Visual Inspection",
            "Electrical Performance Characterization",
            "Hot Spot Endurance Test",
            "UV Preconditioning",
            "Thermal Cycling (200 cycles)",
            "Humidity Freeze (10 cycles)",
            "Damp Heat (1000 hours)",
            "Mechanical Load Test (Static/Dynamic)",
            "Hail Impact Test",
            "Outdoor Exposure Test",
            "Final Electrical Performance",
            "Final Visual Inspection",
        ],
        ModuleType.THIN_FILM: [
            "Visual Inspection",
            "Electrical Performance Characterization",
            "Light Soaking (per IEC 61646)",
            "Hot Spot Endurance Test",
            "UV Preconditioning",
            "Thermal Cycling (200 cycles)",
            "Humidity Freeze (10 cycles)",
            "Damp Heat (1000 hours)",
            "Mechanical Load Test",
            "Final Electrical Performance",
            "Final Visual Inspection",
        ],
        ModuleType.BIFACIAL: [
            "Visual Inspection (both sides)",
            "Electrical Performance (front/rear irradiance)",
            "Bifacial Power Measurement",
            "UV Preconditioning",
            "Thermal Cycling (200 cycles)",
            "Humidity Freeze (10 cycles)",
            "Damp Heat (1000 hours)",
            "Mechanical Load Test (both sides)",
            "Bifacial Gain Verification",
            "Final Performance Verification",
        ],
    }

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        """
        Initialize intelligent assistant.

        Args:
            claude_client: Optional Claude client instance
        """
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.claude_client = claude_client or ClaudeClient()
        self.conversation_history: List[Dict[str, str]] = []

    def _build_system_prompt(self, mode: AssistantMode) -> str:
        """
        Build system prompt based on assistant mode.

        Args:
            mode: Assistant operation mode

        Returns:
            System prompt string
        """
        base_prompt = """You are an expert photovoltaic (PV) module testing assistant with comprehensive knowledge of:

**Standards:**
- IEC 61215 (Terrestrial PV modules - Design qualification)
- IEC 61730 (PV module safety qualification)
- IEC 61853 (Performance testing and energy rating)
- IEC 62716 (Ammonia corrosion)
- IEC 61701 (Salt mist corrosion)
- IEC 62804 (Test methods for detection of potential induced degradation)
- ISO 17025 (Testing and calibration laboratory competence)
- ISO 9001 (Quality management systems)

**Expertise Areas:**
- Test procedures and methodologies
- Equipment operation and calibration
- Data analysis and interpretation
- Quality assurance and compliance
- Troubleshooting test failures
- Safety protocols"""

        mode_specific = {
            AssistantMode.PROCEDURE_HELP: """
**Current Mode: Procedure Help**
Provide step-by-step guidance on test procedures. Be specific about:
- Equipment required
- Environmental conditions
- Measurement points
- Acceptance criteria
- Safety precautions""",
            AssistantMode.STANDARD_INTERPRETATION: """
**Current Mode: Standard Interpretation**
Explain standard requirements clearly. Include:
- Exact clause references
- Intent of the requirement
- How to demonstrate compliance
- Common misinterpretations to avoid""",
            AssistantMode.TEST_PLANNING: """
**Current Mode: Test Planning**
Help plan efficient test sequences. Consider:
- Module type and technology
- Standard requirements
- Test dependencies
- Time optimization
- Resource allocation""",
            AssistantMode.TROUBLESHOOTING: """
**Current Mode: Troubleshooting**
Diagnose test issues systematically:
- Identify root causes
- Suggest corrective actions
- Prevent recurrence
- Reference similar cases""",
            AssistantMode.CALIBRATION: """
**Current Mode: Calibration**
Provide calibration guidance:
- Calibration intervals per ISO 17025
- Calibration procedures
- Traceability requirements
- Uncertainty budgets
- Record keeping""",
            AssistantMode.QUALITY_ASSURANCE: """
**Current Mode: Quality Assurance**
Ensure quality and compliance:
- QC checkpoints
- Documentation requirements
- Audit readiness
- Non-conformance handling""",
        }

        return base_prompt + mode_specific.get(mode, "")

    async def ask_async(
        self,
        question: str,
        mode: AssistantMode = AssistantMode.GENERAL,
        context: Optional[Dict[str, Any]] = None,
        use_history: bool = True,
    ) -> str:
        """
        Ask the intelligent assistant a question.

        Args:
            question: User's question
            mode: Assistant mode for specialized responses
            context: Optional context (module type, standard, etc.)
            use_history: Whether to use conversation history

        Returns:
            Assistant's response
        """
        try:
            self.logger.info(
                "Processing assistant query", question_preview=question[:100], mode=mode.value
            )

            # Build system prompt
            system_prompt = self._build_system_prompt(mode)

            # Add context if provided
            context_str = ""
            if context:
                context_str = "\n\n**Context:**\n"
                for key, value in context.items():
                    context_str += f"- {key}: {value}\n"

            # Build user message
            user_message = f"{question}{context_str}"

            # Build messages list
            if use_history and self.conversation_history:
                messages = self.conversation_history + [{"role": "user", "content": user_message}]
            else:
                messages = [{"role": "user", "content": user_message}]

            # Call Claude API
            response = await self.claude_client.create_message_async(
                messages=messages, system=system_prompt, temperature=0.4  # Balanced creativity
            )

            answer = response.content[0].text

            # Update conversation history
            if use_history:
                self.conversation_history.append({"role": "user", "content": user_message})
                self.conversation_history.append({"role": "assistant", "content": answer})

                # Limit history to last 10 exchanges
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]

            self.logger.info("Assistant query completed", response_length=len(answer))

            return answer

        except Exception as e:
            self.logger.error(f"Assistant query failed: {e}", exc_info=True)
            raise

    def ask(
        self,
        question: str,
        mode: AssistantMode = AssistantMode.GENERAL,
        context: Optional[Dict[str, Any]] = None,
        use_history: bool = True,
    ) -> str:
        """
        Synchronous version of ask_async.

        Args:
            question: User's question
            mode: Assistant mode
            context: Optional context
            use_history: Use conversation history

        Returns:
            Assistant's response
        """
        import asyncio

        return asyncio.run(self.ask_async(question, mode, context, use_history))

    def suggest_test_sequence(
        self, module_type: ModuleType, standard: StandardType = StandardType.IEC_61215
    ) -> List[str]:
        """
        Suggest optimal test sequence for a module type.

        Args:
            module_type: Type of PV module
            standard: Testing standard to follow

        Returns:
            List of tests in recommended order
        """
        self.logger.info(
            "Generating test sequence", module_type=module_type.value, standard=standard.value
        )

        # Get base sequence
        sequence = self.TEST_SEQUENCES.get(
            module_type, self.TEST_SEQUENCES[ModuleType.CRYSTALLINE_SILICON]
        )

        return sequence.copy()

    async def get_procedure_guidance_async(self, test_name: str) -> str:
        """
        Get detailed procedure guidance for a test.

        Args:
            test_name: Name of test procedure

        Returns:
            Detailed procedure guidance
        """
        # Check knowledge base first
        test_key = test_name.lower().replace(" ", "_")
        if test_key in self.KNOWLEDGE_BASE:
            kb_info = self.KNOWLEDGE_BASE[test_key]
            question = f"Provide detailed guidance for {test_name}. Here is basic info:\n{kb_info}\n\nExpand on this with additional details, tips, and best practices."
        else:
            question = f"Provide detailed step-by-step guidance for the PV module test: {test_name}"

        return await self.ask_async(question, mode=AssistantMode.PROCEDURE_HELP)

    def get_procedure_guidance(self, test_name: str) -> str:
        """
        Synchronous version of get_procedure_guidance_async.

        Args:
            test_name: Name of test

        Returns:
            Procedure guidance
        """
        import asyncio

        return asyncio.run(self.get_procedure_guidance_async(test_name))

    async def interpret_standard_clause_async(
        self, standard: StandardType, clause: str
    ) -> str:
        """
        Interpret a specific standard clause.

        Args:
            standard: Testing standard
            clause: Clause number or description

        Returns:
            Interpretation and guidance
        """
        question = f"Explain {standard.value}, clause {clause}. Include:\n1. What the requirement means\n2. How to demonstrate compliance\n3. Common mistakes to avoid\n4. Practical tips"

        return await self.ask_async(question, mode=AssistantMode.STANDARD_INTERPRETATION)

    def interpret_standard_clause(self, standard: StandardType, clause: str) -> str:
        """
        Synchronous version of interpret_standard_clause_async.

        Args:
            standard: Testing standard
            clause: Clause reference

        Returns:
            Interpretation
        """
        import asyncio

        return asyncio.run(self.interpret_standard_clause_async(standard, clause))

    async def troubleshoot_async(self, problem_description: str, test_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Get troubleshooting help for a test issue.

        Args:
            problem_description: Description of the problem
            test_context: Optional context about the test

        Returns:
            Troubleshooting guidance
        """
        question = f"Help troubleshoot this issue:\n\n{problem_description}\n\nProvide:\n1. Possible root causes\n2. Diagnostic steps\n3. Solutions\n4. Prevention measures"

        return await self.ask_async(
            question, mode=AssistantMode.TROUBLESHOOTING, context=test_context
        )

    def troubleshoot(self, problem_description: str, test_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Synchronous version of troubleshoot_async.

        Args:
            problem_description: Problem description
            test_context: Optional context

        Returns:
            Troubleshooting guidance
        """
        import asyncio

        return asyncio.run(self.troubleshoot_async(problem_description, test_context))

    def get_calibration_reminder(self, equipment_type: str, last_calibration_date: datetime) -> Dict[str, Any]:
        """
        Check calibration status and get reminder.

        Args:
            equipment_type: Type of equipment
            last_calibration_date: Date of last calibration

        Returns:
            Calibration status and recommendations
        """
        # Standard calibration intervals (ISO 17025)
        calibration_intervals = {
            "solar_simulator": 365,  # 1 year
            "reference_cell": 365,  # 1 year
            "multimeter": 365,  # 1 year
            "temperature_chamber": 365,  # 1 year
            "humidity_sensor": 180,  # 6 months
            "irradiance_meter": 365,  # 1 year
        }

        interval_days = calibration_intervals.get(equipment_type.lower(), 365)
        days_since_calibration = (datetime.utcnow() - last_calibration_date).days
        days_until_due = interval_days - days_since_calibration

        status = "OK"
        if days_until_due < 0:
            status = "OVERDUE"
        elif days_until_due < 30:
            status = "DUE_SOON"

        return {
            "equipment_type": equipment_type,
            "last_calibration": last_calibration_date.isoformat(),
            "calibration_interval_days": interval_days,
            "days_since_calibration": days_since_calibration,
            "days_until_due": days_until_due,
            "status": status,
            "recommendation": f"Calibration {'is overdue' if status == 'OVERDUE' else 'due soon' if status == 'DUE_SOON' else 'is current'}",
        }

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history.clear()
        self.logger.debug("Conversation history cleared")
