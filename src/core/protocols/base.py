"""
Base protocol class for all test protocols.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..models.test_sequence import TestSequence, TestStep
from ..models.test_result import TestResult, ModuleUnderTest


class BaseProtocol(ABC):
    """
    Abstract base class for test protocols.

    All protocol implementations (IEC 61215, IEC 61730, etc.) should inherit from this class.
    """

    def __init__(self):
        self.protocol_name: str = ""
        self.protocol_version: str = ""
        self.standard_reference: str = ""
        self.test_sequence: Optional[TestSequence] = None

    @abstractmethod
    def initialize_sequence(self, module: ModuleUnderTest, **kwargs) -> TestSequence:
        """
        Initialize test sequence for the given module.

        Args:
            module: Module under test
            **kwargs: Additional configuration parameters

        Returns:
            TestSequence object
        """
        pass

    @abstractmethod
    def define_test_steps(self, module_type: str) -> List[TestStep]:
        """
        Define test steps based on module type.

        Args:
            module_type: Type of module (e.g., "crystalline", "thin_film")

        Returns:
            List of TestStep objects
        """
        pass

    @abstractmethod
    def execute_test(self, test_step: TestStep, **kwargs) -> TestResult:
        """
        Execute a single test step.

        Args:
            test_step: Test step to execute
            **kwargs: Test-specific parameters

        Returns:
            TestResult object
        """
        pass

    def execute_sequence(self, **kwargs) -> TestSequence:
        """
        Execute full test sequence.

        Args:
            **kwargs: Execution parameters

        Returns:
            Completed TestSequence object
        """
        if not self.test_sequence:
            raise ValueError("Test sequence not initialized. Call initialize_sequence first.")

        self.test_sequence.start_time = datetime.now()

        while True:
            next_step = self.test_sequence.get_next_step()

            if not next_step:
                # No more steps to execute
                break

            try:
                # Execute test
                result = self.execute_test(next_step, **kwargs)
                next_step.mark_completed(result)

            except Exception as e:
                # Handle test execution error
                print(f"Error executing {next_step.test_name}: {str(e)}")
                # Could implement retry logic or error handling here
                raise

        self.test_sequence.end_time = datetime.now()
        self.test_sequence.evaluate_overall_compliance()

        return self.test_sequence

    def get_test_parameters(self, test_id: str) -> Dict[str, Any]:
        """
        Get standard test parameters for a specific test.

        Args:
            test_id: Test identifier

        Returns:
            Dictionary of test parameters
        """
        return {}

    def validate_test_conditions(self, test_id: str, conditions: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate that test conditions meet requirements.

        Args:
            test_id: Test identifier
            conditions: Test conditions to validate

        Returns:
            Tuple of (is_valid, message)
        """
        return True, "Conditions valid"

    def calculate_degradation(
        self,
        initial_power: float,
        final_power: float,
        test_type: str = "general"
    ) -> Dict[str, float]:
        """
        Calculate power degradation.

        Args:
            initial_power: Initial maximum power (W)
            final_power: Final maximum power (W)
            test_type: Type of test for degradation limits

        Returns:
            Dictionary with degradation percentage and pass/fail
        """
        degradation_percent = ((initial_power - final_power) / initial_power) * 100

        # Standard degradation limits (can be overridden in subclasses)
        limits = {
            "general": 5.0,  # 5% max degradation
            "thermal_cycling": 5.0,
            "humidity_freeze": 5.0,
            "damp_heat": 5.0,
            "initial_stabilization": 2.0,
        }

        limit = limits.get(test_type, 5.0)
        passes = degradation_percent <= limit

        return {
            "degradation_percent": degradation_percent,
            "limit_percent": limit,
            "passes": passes,
            "initial_power": initial_power,
            "final_power": final_power,
        }

    def generate_report_section(self, test_result: TestResult) -> Dict[str, Any]:
        """
        Generate report section for a test result.

        Args:
            test_result: Test result to report

        Returns:
            Dictionary with report data
        """
        return test_result.to_dict()

    def get_protocol_info(self) -> Dict[str, Any]:
        """Get protocol information."""
        return {
            "name": self.protocol_name,
            "version": self.protocol_version,
            "standard_reference": self.standard_reference,
        }
