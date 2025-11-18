"""
IEC 62804 PID Testing Protocol

Comprehensive implementation of IEC 62804 Potential Induced Degradation (PID)
testing protocol for photovoltaic modules.

This package provides:
- Automated climate chamber control
- High voltage application and monitoring
- Flash testing (I-V curve measurement)
- Leakage current monitoring with safety features
- Power degradation analysis
- PID recovery testing
- Comprehensive reporting (text, HTML, JSON)
- ISO 17025 compliance features

Example Usage:
    >>> from protocols.iec_62804 import (
    ...     IEC62804TestController,
    ...     TestConfiguration,
    ...     create_chamber_controller,
    ...     create_voltage_supply,
    ...     create_flash_tester
    ... )
    >>>
    >>> # Create test configuration
    >>> config = TestConfiguration(
    ...     module_serial="PV-2025-001234",
    ...     test_method=TestMethod.METHOD_B,
    ...     voltage=-1000,
    ...     duration_hours=96,
    ...     temperature=60.0,
    ...     humidity=85.0
    ... )
    >>>
    >>> # Initialize equipment
    >>> chamber = create_chamber_controller("simulated", "CHAMBER-01")
    >>> voltage_supply = create_voltage_supply("simulated", "SUPPLY-01")
    >>> flash_tester = create_flash_tester("simulated", "TESTER-01")
    >>>
    >>> # Create test controller
    >>> controller = IEC62804TestController(
    ...     config=config,
    ...     chamber=chamber,
    ...     voltage_supply=voltage_supply,
    ...     flash_tester=flash_tester
    ... )
    >>>
    >>> # Initialize and run test
    >>> controller.initialize()
    >>> controller.run_test()
    >>>
    >>> # Monitor progress
    >>> status = controller.get_status()
    >>> print(f"Degradation: {status['current_degradation_pct']:.2f}%")

Standards Compliance:
- IEC 62804-1: PID testing methods
- IEC 62804-1-1: Crystalline silicon modules
- ISO 17025: Testing laboratory requirements

Author: IEC 62804 Protocol Development Team
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "IEC 62804 Protocol Development Team"

# Database models
from .models import (
    # Enums
    TestMethod,
    TestStatus,
    TestResult,
    ModuleType,
    # ORM Models
    Base,
    IEC62804TestORM,
    FlashTestResultORM,
    LeakageCurrentLogORM,
    ChamberLogORM,
    # Pydantic Schemas
    IEC62804TestCreate,
    IEC62804Test,
    FlashTestResult,
    FlashTestResultCreate,
    LeakageCurrentLog,
    ChamberLog,
    SafetyStatus,
)

# Chamber control
from .chamber_control import (
    ChamberControllerBase,
    SimulatedChamberController,
    ChamberSetpoint,
    ChamberReading,
    ChamberMonitor,
    ChamberAlarmType,
    create_chamber_controller,
)

# Voltage control
from .voltage_control import (
    VoltageSupplyBase,
    SimulatedVoltageSupply,
    VoltageSupplyConfig,
    VoltageReading,
    VoltageSupplyStatus,
    VoltageMonitor,
    InterlockType,
    create_voltage_supply,
)

# Flash testing
from .flash_tester import (
    FlashTesterBase,
    SimulatedFlashTester,
    IVCurveData,
    IVCurvePoint,
    FlashTestScheduler,
    create_flash_tester,
    correct_to_stc,
)

# Leakage current monitoring
from .leakage_monitor import (
    LeakageCurrentMonitor,
    LeakageCurrentReading,
    LeakageStatistics,
    LeakageCurrentAnalyzer,
)

# Degradation analysis
from .degradation_analyzer import (
    DegradationAnalyzer,
    DegradationResult,
    DegradationForecast,
    DegradationLevel,
    PowerMeasurement,
    DegradationComparator,
)

# Recovery testing
from .recovery_test import (
    PIDRecoveryTest,
    RecoveryResult,
    RecoveryMeasurement,
    RecoveryMethod,
    RecoveryClassification,
    RecoveryProtocol,
    calculate_recovery_kinetics,
)

# Main test controller
from .test_controller import (
    IEC62804TestController,
    TestConfiguration,
    TestPhase,
)

# Report generation
from .report_generator import (
    IEC62804ReportGenerator,
    create_test_report,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",

    # Models - Enums
    "TestMethod",
    "TestStatus",
    "TestResult",
    "ModuleType",

    # Models - ORM
    "Base",
    "IEC62804TestORM",
    "FlashTestResultORM",
    "LeakageCurrentLogORM",
    "ChamberLogORM",

    # Models - Pydantic
    "IEC62804TestCreate",
    "IEC62804Test",
    "FlashTestResult",
    "FlashTestResultCreate",
    "LeakageCurrentLog",
    "ChamberLog",
    "SafetyStatus",

    # Chamber control
    "ChamberControllerBase",
    "SimulatedChamberController",
    "ChamberSetpoint",
    "ChamberReading",
    "ChamberMonitor",
    "ChamberAlarmType",
    "create_chamber_controller",

    # Voltage control
    "VoltageSupplyBase",
    "SimulatedVoltageSupply",
    "VoltageSupplyConfig",
    "VoltageReading",
    "VoltageSupplyStatus",
    "VoltageMonitor",
    "InterlockType",
    "create_voltage_supply",

    # Flash testing
    "FlashTesterBase",
    "SimulatedFlashTester",
    "IVCurveData",
    "IVCurvePoint",
    "FlashTestScheduler",
    "create_flash_tester",
    "correct_to_stc",

    # Leakage monitoring
    "LeakageCurrentMonitor",
    "LeakageCurrentReading",
    "LeakageStatistics",
    "LeakageCurrentAnalyzer",

    # Degradation analysis
    "DegradationAnalyzer",
    "DegradationResult",
    "DegradationForecast",
    "DegradationLevel",
    "PowerMeasurement",
    "DegradationComparator",

    # Recovery testing
    "PIDRecoveryTest",
    "RecoveryResult",
    "RecoveryMeasurement",
    "RecoveryMethod",
    "RecoveryClassification",
    "RecoveryProtocol",
    "calculate_recovery_kinetics",

    # Main controller
    "IEC62804TestController",
    "TestConfiguration",
    "TestPhase",

    # Reporting
    "IEC62804ReportGenerator",
    "create_test_report",
]


# Package metadata
PACKAGE_INFO = {
    "name": "iec_62804",
    "version": __version__,
    "description": "IEC 62804 PID Testing Protocol Implementation",
    "standards": [
        "IEC 62804-1: Photovoltaic (PV) modules - Test methods for the detection of potential-induced degradation",
        "IEC 62804-1-1: Crystalline silicon",
        "ISO/IEC 17025: General requirements for the competence of testing and calibration laboratories"
    ],
    "features": [
        "Full IEC 62804-1 Methods A, B, C implementation",
        "Automated climate chamber control",
        "High voltage application with safety interlocks",
        "Continuous leakage current monitoring",
        "Automated flash testing at intervals",
        "Real-time degradation analysis",
        "PID recovery testing",
        "Emergency shutdown on safety violations",
        "Comprehensive reporting (text, HTML, JSON)",
        "ISO 17025 compliance features",
        "Extensive unit test coverage"
    ],
    "test_methods": {
        "A": "Outdoor exposure with voltage bias",
        "B": "Climate chamber with humidity (60°C, 85% RH)",
        "C": "Climate chamber dry (85°C)"
    },
    "pass_criteria": {
        "pass": "< 5% power degradation after 96 hours",
        "marginal": "5-10% power degradation after 96 hours",
        "fail": "> 10% power degradation after 96 hours"
    }
}


def get_package_info() -> dict:
    """
    Get package information.

    Returns:
        Dictionary with package metadata
    """
    return PACKAGE_INFO.copy()


def print_package_info():
    """Print package information"""
    info = get_package_info()

    print("=" * 80)
    print(f"{info['name']} v{info['version']}")
    print("=" * 80)
    print(f"\n{info['description']}\n")

    print("Standards Compliance:")
    for standard in info['standards']:
        print(f"  - {standard}")

    print("\nTest Methods:")
    for method, description in info['test_methods'].items():
        print(f"  Method {method}: {description}")

    print("\nPass/Fail Criteria:")
    for level, criteria in info['pass_criteria'].items():
        print(f"  {level.upper()}: {criteria}")

    print("\nKey Features:")
    for feature in info['features'][:5]:
        print(f"  ✓ {feature}")

    print("\n" + "=" * 80)
