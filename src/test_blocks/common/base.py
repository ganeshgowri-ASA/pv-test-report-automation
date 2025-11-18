"""
Base test block implementation for all PV test standards.

Provides common functionality for test execution with:
- Equipment management
- Test lifecycle (setup/execute/teardown)
- Result generation
- Error handling
- ISO 17025 compliance
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel

from src.models.base import BaseTestResult, TestStatus


class TestBlockError(Exception):
    """Base exception for test block errors."""
    pass


class SetupError(TestBlockError):
    """Raised when test setup fails."""
    pass


class ExecutionError(TestBlockError):
    """Raised when test execution fails."""
    pass


class BaseTestBlock(ABC):
    """
    Base class for all test blocks across different standards.

    Implements the test execution lifecycle:
    1. Setup - Configure and verify equipment
    2. Execute - Run the test procedure
    3. Teardown - Cleanup and reset equipment
    """

    def __init__(
        self,
        module_id: str,
        operator: str,
        equipment_config: Optional[Dict[str, Any]] = None,
        test_parameters: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize test block.

        Args:
            module_id: Module under test identifier
            operator: Test operator name/ID
            equipment_config: Equipment configuration
            test_parameters: Test-specific parameters
        """
        self.module_id = module_id
        self.operator = operator
        self.equipment_config = equipment_config or {}
        self.test_parameters = test_parameters or {}
        self.test_results: List[Dict[str, Any]] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.current_status = TestStatus.INCOMPLETE

    @property
    @abstractmethod
    def standard(self) -> str:
        """Return the test standard this block implements."""
        pass

    @property
    @abstractmethod
    def test_name(self) -> str:
        """Return the name of this test."""
        pass

    @property
    @abstractmethod
    def test_id(self) -> str:
        """Return the unique test identifier."""
        pass

    @abstractmethod
    async def setup(self) -> None:
        """
        Setup test equipment and verify readiness.

        Should:
        - Initialize equipment connections
        - Verify calibration status
        - Configure test parameters
        - Perform safety checks

        Raises:
            SetupError: If setup fails
        """
        pass

    @abstractmethod
    async def execute(self) -> Dict[str, Any]:
        """
        Execute the test procedure.

        Should:
        - Perform test measurements
        - Log data continuously
        - Monitor safety conditions
        - Handle errors gracefully

        Returns:
            Dictionary containing raw test data

        Raises:
            ExecutionError: If test execution fails
        """
        pass

    @abstractmethod
    async def teardown(self) -> None:
        """
        Cleanup and reset equipment to safe state.

        Should:
        - Disconnect equipment
        - Save data
        - Reset equipment states
        - Never raise exceptions (best effort)
        """
        pass

    @abstractmethod
    def create_result(self, data: Dict[str, Any]) -> BaseTestResult:
        """
        Create standardized result model from test data.

        Args:
            data: Raw test data from execute()

        Returns:
            Pydantic model containing structured test results
        """
        pass

    async def run(self, **kwargs) -> BaseTestResult:
        """
        Execute complete test lifecycle.

        Args:
            **kwargs: Additional test parameters

        Returns:
            Test result model

        Raises:
            TestBlockError: If test fails at any stage
        """
        self.start_time = datetime.now()
        self.current_status = TestStatus.IN_PROGRESS

        try:
            # Update parameters with any runtime kwargs
            self.test_parameters.update(kwargs)

            # Setup
            await self.setup()

            # Execute
            results = await self.execute()

            # Create result
            result = self.create_result(results)

            # Update status
            self.current_status = result.status
            self.end_time = datetime.now()

            return result

        except Exception as e:
            self.current_status = TestStatus.FAILED
            self.end_time = datetime.now()
            raise TestBlockError(f"Test execution failed: {str(e)}") from e

        finally:
            # Always attempt teardown
            try:
                await self.teardown()
            except Exception as e:
                # Log but don't raise - teardown is best effort
                print(f"Warning: Teardown error: {e}")

    def get_test_duration(self) -> Optional[float]:
        """
        Get test duration in seconds.

        Returns:
            Test duration or None if not complete
        """
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def add_note(self, note: str) -> None:
        """Add a note to the test record."""
        timestamp = datetime.now().isoformat()
        self.test_results.append({
            "timestamp": timestamp,
            "type": "note",
            "content": note
        })

    def add_measurement(self, measurement_type: str, value: Any, unit: str = "") -> None:
        """
        Add a measurement to the test record.

        Args:
            measurement_type: Type of measurement
            value: Measured value
            unit: Unit of measurement
        """
        self.test_results.append({
            "timestamp": datetime.now().isoformat(),
            "type": "measurement",
            "measurement_type": measurement_type,
            "value": value,
            "unit": unit
        })
