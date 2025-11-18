"""
IEC 62804 PID Testing Protocol - Database Models

This module defines SQLAlchemy ORM models and Pydantic schemas for
IEC 62804 Potential Induced Degradation (PID) testing.
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, validator

Base = declarative_base()


class TestMethod(str, Enum):
    """IEC 62804-1 Test Methods"""
    METHOD_A = "A"  # Outdoor exposure with voltage bias
    METHOD_B = "B"  # Climate chamber with humidity (60°C, 85% RH)
    METHOD_C = "C"  # Climate chamber dry (85°C)


class TestStatus(str, Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class TestResult(str, Enum):
    """Test pass/fail result"""
    PASS = "pass"  # < 5% degradation
    MARGINAL = "marginal"  # 5-10% degradation
    FAIL = "fail"  # > 10% degradation
    PENDING = "pending"


class ModuleType(str, Enum):
    """PV module types"""
    MONOFACIAL = "monofacial"
    BIFACIAL = "bifacial"


# ============================================================================
# SQLAlchemy ORM Models
# ============================================================================

class IEC62804TestORM(Base):
    """IEC 62804 PID Test main record"""
    __tablename__ = "iec62804_tests"

    test_id = Column(Integer, primary_key=True, autoincrement=True)
    module_serial = Column(String(100), nullable=False, index=True)
    module_type = Column(String(20), default="monofacial")
    manufacturer = Column(String(100))
    model = Column(String(100))

    # Test configuration
    test_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    test_method = Column(String(1), nullable=False)  # A, B, or C
    voltage = Column(Float, nullable=False)  # Typically -1000V
    duration_hours = Column(Integer, nullable=False, default=96)

    # Environmental conditions
    temperature = Column(Float, nullable=False)  # °C
    humidity = Column(Float)  # %RH (None for Method C)

    # Test status
    status = Column(String(20), nullable=False, default="pending")
    result = Column(String(20), default="pending")

    # Timestamps
    start_time = Column(DateTime)
    end_time = Column(DateTime)

    # Results summary
    initial_pmax = Column(Float)  # W
    final_pmax = Column(Float)  # W
    degradation_pct = Column(Float)  # %
    degradation_rate = Column(Float)  # %/hour

    # Recovery testing
    recovery_enabled = Column(Boolean, default=False)
    recovery_pct = Column(Float)  # % of power recovered
    reversible_pid = Column(Boolean)  # True if >80% recovery

    # Safety and monitoring
    max_leakage_current = Column(Float)  # mA
    emergency_stop_triggered = Column(Boolean, default=False)

    # Notes and observations
    notes = Column(Text)
    operator = Column(String(100))

    # Relationships
    flash_tests = relationship("FlashTestResultORM", back_populates="test", cascade="all, delete-orphan")
    leakage_logs = relationship("LeakageCurrentLogORM", back_populates="test", cascade="all, delete-orphan")
    chamber_logs = relationship("ChamberLogORM", back_populates="test", cascade="all, delete-orphan")


class FlashTestResultORM(Base):
    """Flash test (I-V curve) measurement results"""
    __tablename__ = "flash_test_results"

    result_id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(Integer, ForeignKey("iec62804_tests.test_id"), nullable=False)

    # Timing
    elapsed_hours = Column(Float, nullable=False)  # Hours since test start
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # I-V curve parameters
    pmax = Column(Float, nullable=False)  # W
    voc = Column(Float, nullable=False)  # V
    isc = Column(Float, nullable=False)  # A
    vmp = Column(Float)  # V at max power
    imp = Column(Float)  # A at max power
    ff = Column(Float)  # Fill factor

    # Degradation tracking
    degradation_pct = Column(Float)  # % from initial
    degradation_from_previous = Column(Float)  # % from previous measurement

    # I-V curve data (stored as JSON or separate table)
    iv_curve_data = Column(Text)  # JSON string of voltage/current pairs

    # Test conditions at measurement
    module_temperature = Column(Float)  # °C
    irradiance = Column(Float)  # W/m²

    # Relationship
    test = relationship("IEC62804TestORM", back_populates="flash_tests")


class LeakageCurrentLogORM(Base):
    """Continuous leakage current monitoring"""
    __tablename__ = "leakage_current_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(Integer, ForeignKey("iec62804_tests.test_id"), nullable=False)

    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    elapsed_hours = Column(Float)  # Hours since test start

    # Current monitoring
    current_ma = Column(Float, nullable=False)  # mA
    voltage = Column(Float, nullable=False)  # V

    # Safety flags
    over_threshold = Column(Boolean, default=False)
    alarm_triggered = Column(Boolean, default=False)

    # Relationship
    test = relationship("IEC62804TestORM", back_populates="leakage_logs")


class ChamberLogORM(Base):
    """Climate chamber environmental monitoring"""
    __tablename__ = "chamber_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(Integer, ForeignKey("iec62804_tests.test_id"), nullable=False)

    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    elapsed_hours = Column(Float)  # Hours since test start

    # Environmental measurements
    temperature = Column(Float, nullable=False)  # °C
    humidity = Column(Float)  # %RH

    # Setpoints
    temperature_setpoint = Column(Float)  # °C
    humidity_setpoint = Column(Float)  # %RH

    # Status flags
    temperature_in_range = Column(Boolean, default=True)
    humidity_in_range = Column(Boolean, default=True)
    chamber_alarm = Column(Boolean, default=False)

    # Relationship
    test = relationship("IEC62804TestORM", back_populates="chamber_logs")


# ============================================================================
# Pydantic Schemas for API/Validation
# ============================================================================

class IEC62804TestCreate(BaseModel):
    """Schema for creating a new IEC 62804 test"""
    module_serial: str = Field(..., description="Module serial number")
    module_type: ModuleType = Field(default=ModuleType.MONOFACIAL)
    manufacturer: Optional[str] = None
    model: Optional[str] = None

    test_method: TestMethod = Field(..., description="Test method A, B, or C")
    voltage: float = Field(default=-1000.0, description="Applied voltage (V)")
    duration_hours: int = Field(default=96, description="Test duration (hours)")

    temperature: float = Field(..., description="Test temperature (°C)")
    humidity: Optional[float] = Field(None, description="Relative humidity (%)")

    recovery_enabled: bool = Field(default=False)
    operator: Optional[str] = None
    notes: Optional[str] = None

    @validator('humidity')
    def validate_humidity(cls, v, values):
        """Ensure humidity is provided for Method B"""
        if 'test_method' in values and values['test_method'] == TestMethod.METHOD_B:
            if v is None:
                raise ValueError("Humidity required for Test Method B")
        return v

    @validator('temperature')
    def validate_temperature(cls, v, values):
        """Validate temperature ranges for different methods"""
        if 'test_method' in values:
            method = values['test_method']
            if method == TestMethod.METHOD_B and not (55 <= v <= 65):
                raise ValueError("Method B temperature should be 60°C ± 5°C")
            elif method == TestMethod.METHOD_C and not (80 <= v <= 90):
                raise ValueError("Method C temperature should be 85°C ± 5°C")
        return v

    class Config:
        use_enum_values = True


class IEC62804Test(BaseModel):
    """Schema for IEC 62804 test response"""
    test_id: int
    module_serial: str
    module_type: str
    manufacturer: Optional[str]
    model: Optional[str]

    test_date: datetime
    test_method: str
    voltage: float
    duration_hours: int

    temperature: float
    humidity: Optional[float]

    status: str
    result: Optional[str]

    start_time: Optional[datetime]
    end_time: Optional[datetime]

    initial_pmax: Optional[float]
    final_pmax: Optional[float]
    degradation_pct: Optional[float]
    degradation_rate: Optional[float]

    recovery_enabled: bool
    recovery_pct: Optional[float]
    reversible_pid: Optional[bool]

    max_leakage_current: Optional[float]
    emergency_stop_triggered: bool

    notes: Optional[str]
    operator: Optional[str]

    class Config:
        from_attributes = True


class FlashTestResult(BaseModel):
    """Schema for flash test result"""
    result_id: Optional[int] = None
    test_id: int
    elapsed_hours: float
    timestamp: datetime

    pmax: float
    voc: float
    isc: float
    vmp: Optional[float]
    imp: Optional[float]
    ff: Optional[float]

    degradation_pct: Optional[float]
    degradation_from_previous: Optional[float]

    module_temperature: Optional[float]
    irradiance: Optional[float]

    class Config:
        from_attributes = True


class FlashTestResultCreate(BaseModel):
    """Schema for creating flash test result"""
    test_id: int
    elapsed_hours: float

    pmax: float
    voc: float
    isc: float
    vmp: Optional[float] = None
    imp: Optional[float] = None
    ff: Optional[float] = None

    module_temperature: Optional[float] = None
    irradiance: Optional[float] = 1000.0  # STC default

    iv_curve_data: Optional[str] = None


class LeakageCurrentLog(BaseModel):
    """Schema for leakage current log entry"""
    log_id: Optional[int] = None
    test_id: int
    timestamp: datetime
    elapsed_hours: Optional[float]

    current_ma: float
    voltage: float

    over_threshold: bool = False
    alarm_triggered: bool = False

    class Config:
        from_attributes = True


class ChamberLog(BaseModel):
    """Schema for chamber environmental log"""
    log_id: Optional[int] = None
    test_id: int
    timestamp: datetime
    elapsed_hours: Optional[float]

    temperature: float
    humidity: Optional[float]

    temperature_setpoint: Optional[float]
    humidity_setpoint: Optional[float]

    temperature_in_range: bool = True
    humidity_in_range: bool = True
    chamber_alarm: bool = False

    class Config:
        from_attributes = True


class TestStatus(BaseModel):
    """Current test status summary"""
    test_id: int
    status: str
    elapsed_hours: float
    remaining_hours: float
    progress_pct: float

    current_temperature: Optional[float]
    current_humidity: Optional[float]
    current_leakage_ma: Optional[float]

    latest_pmax: Optional[float]
    current_degradation_pct: Optional[float]

    estimated_result: Optional[str]  # Based on current degradation


class SafetyStatus(BaseModel):
    """Safety monitoring status"""
    test_id: int
    safe_to_operate: bool

    leakage_current_ok: bool
    chamber_conditions_ok: bool
    voltage_ok: bool

    active_alarms: List[str] = []
    warnings: List[str] = []

    last_check: datetime
