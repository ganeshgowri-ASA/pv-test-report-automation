"""
Database Models for IEC 61853 Testing
======================================

Pydantic and SQLAlchemy models for storing and validating IEC 61853 test data.

Models:
- IEC61853Test: Main test record
- PerformanceMatrixPoint: Individual test point in 35-point matrix
- IVCurveData: I-V curve measurements
- SpectralResponseData: Spectral response measurements
- AngularResponseData: Angular dependency data
- EnergyRating: Energy yield calculations
- TemperatureCoefficients: Temperature coefficients (α, β, γ)
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator, confloat, conint
from sqlalchemy import (
    Column, Integer, Float, String, DateTime, JSON,
    ForeignKey, Boolean, Text, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


# ==================== Enumerations ====================

class TestStatus(str, Enum):
    """Test execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    STABILIZING = "stabilizing"
    MEASURING = "measuring"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class IEC61853Part(int, Enum):
    """IEC 61853 standard parts"""
    PART_1 = 1  # Performance at STC and varying conditions
    PART_2 = 2  # Spectral responsivity and angle of incidence
    PART_3 = 3  # Energy rating
    PART_4 = 4  # Standard reference climatic profiles


class ClimateType(str, Enum):
    """Climate classifications for energy rating"""
    TROPICAL = "tropical"
    SUBTROPICAL_DESERT = "subtropical_desert"
    TEMPERATE = "temperate"
    TEMPERATE_DESERT = "temperate_desert"
    COLD = "cold"


# ==================== Pydantic Models ====================

class IVPoint(BaseModel):
    """Single point on I-V curve"""
    voltage: confloat(ge=0.0) = Field(..., description="Voltage (V)")
    current: confloat(ge=0.0) = Field(..., description="Current (A)")
    power: confloat(ge=0.0) = Field(..., description="Power (W)")


class IVCurve(BaseModel):
    """Complete I-V curve data"""
    points: List[IVPoint] = Field(..., min_items=50, description="I-V curve points")
    voc: confloat(ge=0.0) = Field(..., description="Open circuit voltage (V)")
    isc: confloat(ge=0.0) = Field(..., description="Short circuit current (A)")
    vmp: confloat(ge=0.0) = Field(..., description="Voltage at maximum power (V)")
    imp: confloat(ge=0.0) = Field(..., description="Current at maximum power (A)")
    pmax: confloat(ge=0.0) = Field(..., description="Maximum power (W)")
    ff: confloat(ge=0.0, le=1.0) = Field(..., description="Fill factor")

    @validator('ff', pre=True, always=True)
    def calculate_fill_factor(cls, v, values):
        """Calculate fill factor if not provided"""
        if v is None and 'voc' in values and 'isc' in values and 'pmax' in values:
            voc, isc, pmax = values['voc'], values['isc'], values['pmax']
            if voc > 0 and isc > 0:
                return pmax / (voc * isc)
        return v


class MatrixTestPointData(BaseModel):
    """Single test point in performance matrix"""
    temperature: confloat(ge=-40.0, le=85.0) = Field(..., description="Temperature (°C)")
    irradiance: confloat(ge=0.0, le=1400.0) = Field(..., description="Irradiance (W/m²)")
    iv_curve: IVCurve = Field(..., description="I-V curve data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    stabilization_time: confloat(ge=0.0) = Field(..., description="Stabilization time (s)")
    chamber_temp_actual: float = Field(..., description="Actual chamber temperature (°C)")
    chamber_temp_stability: confloat(ge=0.0) = Field(..., description="Temperature stability (±°C)")
    irradiance_actual: float = Field(..., description="Actual irradiance (W/m²)")
    irradiance_uniformity: confloat(ge=0.0, le=100.0) = Field(..., description="Irradiance uniformity (%)")
    notes: Optional[str] = None


class TemperatureCoefficientsData(BaseModel):
    """Temperature coefficients from performance matrix"""
    alpha_isc: float = Field(..., description="Isc temperature coefficient (%/°C)")
    beta_voc: float = Field(..., description="Voc temperature coefficient (%/°C)")
    gamma_pmax: float = Field(..., description="Pmax temperature coefficient (%/°C)")
    reference_temperature: float = Field(default=25.0, description="Reference temperature (°C)")
    reference_irradiance: float = Field(default=1000.0, description="Reference irradiance (W/m²)")
    r_squared: confloat(ge=0.0, le=1.0) = Field(..., description="Coefficient of determination")


class SpectralPoint(BaseModel):
    """Single point in spectral response curve"""
    wavelength: confloat(ge=250.0, le=1300.0) = Field(..., description="Wavelength (nm)")
    response: confloat(ge=0.0, le=1.0) = Field(..., description="Relative spectral response")


class SpectralCurveData(BaseModel):
    """Spectral response curve"""
    points: List[SpectralPoint] = Field(..., min_items=20)
    peak_wavelength: float = Field(..., description="Peak response wavelength (nm)")
    peak_response: float = Field(..., description="Peak response value")
    mismatch_factor: confloat(ge=0.9, le=1.1) = Field(..., description="Spectral mismatch factor")


class AngularPoint(BaseModel):
    """Single point in angular response curve"""
    angle: confloat(ge=0.0, le=90.0) = Field(..., description="Incidence angle (degrees)")
    relative_response: confloat(ge=0.0, le=1.0) = Field(..., description="Relative response")


class AngularResponseData(BaseModel):
    """Angular response curve"""
    points: List[AngularPoint] = Field(..., min_items=10)
    iam_factor: confloat(ge=0.0, le=1.0) = Field(..., description="Incidence angle modifier")


class LocationProfileData(BaseModel):
    """Location profile for energy rating"""
    name: str = Field(..., description="Location name")
    latitude: confloat(ge=-90.0, le=90.0) = Field(..., description="Latitude (degrees)")
    longitude: confloat(ge=-180.0, le=180.0) = Field(..., description="Longitude (degrees)")
    climate_type: ClimateType
    annual_irradiation: confloat(ge=0.0) = Field(..., description="Annual irradiation (kWh/m²/year)")
    average_temperature: float = Field(..., description="Average temperature (°C)")
    altitude: float = Field(default=0.0, description="Altitude (m)")


class EnergyRatingData(BaseModel):
    """Energy rating calculation results"""
    location_profile: LocationProfileData
    annual_energy_kwh: confloat(ge=0.0) = Field(..., description="Annual energy yield (kWh)")
    specific_yield_kwh_kwp: confloat(ge=0.0) = Field(..., description="Specific yield (kWh/kWp)")
    performance_ratio: confloat(ge=0.0, le=1.0) = Field(..., description="Performance ratio")
    energy_rating_class: str = Field(..., description="Energy rating class (A+ to E)")
    comparison_to_stc: float = Field(..., description="Comparison to STC rating (%)")


class PerformanceSurfaceData(BaseModel):
    """Performance surface model Pmax(G, T)"""
    polynomial_coefficients: List[float] = Field(..., description="Polynomial coefficients")
    polynomial_degree: conint(ge=1, le=5) = Field(default=2, description="Polynomial degree")
    r_squared: confloat(ge=0.0, le=1.0) = Field(..., description="Model fit quality")
    rmse: confloat(ge=0.0) = Field(..., description="Root mean square error (W)")
    temperature_range: tuple = Field(..., description="Temperature range (°C)")
    irradiance_range: tuple = Field(..., description="Irradiance range (W/m²)")


# ==================== SQLAlchemy Models ====================

class IEC61853TestORM(Base):
    """Main IEC 61853 test record (SQLAlchemy ORM)"""
    __tablename__ = "iec61853_tests"

    test_id = Column(Integer, primary_key=True, autoincrement=True)
    module_id = Column(String(100), nullable=False, index=True)
    module_serial = Column(String(100), nullable=False, unique=True)
    manufacturer = Column(String(200))
    model = Column(String(200))
    technology = Column(String(50))  # mono-Si, poly-Si, CdTe, CIGS, etc.

    test_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    test_lab = Column(String(200), nullable=False)
    test_engineer = Column(String(100))

    standard_reference = Column(String(50), default="IEC 61853", nullable=False)
    test_part = Column(SQLEnum(IEC61853Part), nullable=False)
    status = Column(SQLEnum(TestStatus), default=TestStatus.PENDING, nullable=False)

    # Rated parameters (from nameplate)
    rated_pmax = Column(Float)  # W
    rated_voc = Column(Float)  # V
    rated_isc = Column(Float)  # A
    rated_vmp = Column(Float)  # V
    rated_imp = Column(Float)  # A
    noct = Column(Float)  # °C

    # Test configuration
    test_config = Column(JSON)  # Test parameters and settings

    # Relationships
    matrix_points = relationship("PerformanceMatrixPointORM", back_populates="test", cascade="all, delete-orphan")
    spectral_data = relationship("SpectralResponseORM", back_populates="test", cascade="all, delete-orphan")
    energy_ratings = relationship("EnergyRatingORM", back_populates="test", cascade="all, delete-orphan")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    notes = Column(Text)


class PerformanceMatrixPointORM(Base):
    """Performance matrix test point (SQLAlchemy ORM)"""
    __tablename__ = "performance_matrix_points"

    point_id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(Integer, ForeignKey("iec61853_tests.test_id"), nullable=False, index=True)

    # Test conditions
    temperature = Column(Float, nullable=False)  # °C
    irradiance = Column(Float, nullable=False)  # W/m²

    # I-V curve results
    voc = Column(Float, nullable=False)  # V
    isc = Column(Float, nullable=False)  # A
    vmp = Column(Float, nullable=False)  # V
    imp = Column(Float, nullable=False)  # A
    pmax = Column(Float, nullable=False)  # W
    ff = Column(Float, nullable=False)  # Fill factor

    # Full I-V curve data
    iv_curve_data = Column(JSON, nullable=False)  # List of {v, i, p} points

    # Measurement metadata
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    stabilization_time = Column(Float)  # seconds
    chamber_temp_actual = Column(Float)  # °C
    chamber_temp_stability = Column(Float)  # ±°C
    irradiance_actual = Column(Float)  # W/m²
    irradiance_uniformity = Column(Float)  # %

    # Relationship
    test = relationship("IEC61853TestORM", back_populates="matrix_points")

    notes = Column(Text)


class SpectralResponseORM(Base):
    """Spectral response test data (SQLAlchemy ORM)"""
    __tablename__ = "spectral_response_data"

    spectral_id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(Integer, ForeignKey("iec61853_tests.test_id"), nullable=False, index=True)

    # Spectral curve
    spectral_curve = Column(JSON, nullable=False)  # List of {wavelength, response}
    peak_wavelength = Column(Float)  # nm
    peak_response = Column(Float)
    mismatch_factor = Column(Float)

    # Angular response
    angular_curve = Column(JSON)  # List of {angle, response}
    iam_factor = Column(Float)  # Incidence angle modifier

    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    test = relationship("IEC61853TestORM", back_populates="spectral_data")
    notes = Column(Text)


class EnergyRatingORM(Base):
    """Energy rating calculation (SQLAlchemy ORM)"""
    __tablename__ = "energy_ratings"

    rating_id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(Integer, ForeignKey("iec61853_tests.test_id"), nullable=False, index=True)

    # Location
    location_name = Column(String(200), nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    climate_type = Column(SQLEnum(ClimateType))
    annual_irradiation = Column(Float)  # kWh/m²/year
    average_temperature = Column(Float)  # °C

    # Energy yield results
    annual_energy_kwh = Column(Float, nullable=False)
    specific_yield_kwh_kwp = Column(Float)
    performance_ratio = Column(Float)
    energy_rating_class = Column(String(10))
    comparison_to_stc = Column(Float)  # %

    # Detailed results
    monthly_energy = Column(JSON)  # Monthly breakdown
    loss_analysis = Column(JSON)  # Temperature, spectral, angular losses

    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    test = relationship("IEC61853TestORM", back_populates="energy_ratings")


class TemperatureCoefficientsORM(Base):
    """Temperature coefficients (SQLAlchemy ORM)"""
    __tablename__ = "temperature_coefficients"

    coeff_id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(Integer, ForeignKey("iec61853_tests.test_id"), nullable=False, index=True)

    # Coefficients
    alpha_isc = Column(Float, nullable=False)  # %/°C
    beta_voc = Column(Float, nullable=False)  # %/°C
    gamma_pmax = Column(Float, nullable=False)  # %/°C

    # Reference conditions
    reference_temperature = Column(Float, default=25.0)  # °C
    reference_irradiance = Column(Float, default=1000.0)  # W/m²

    # Statistical quality
    r_squared = Column(Float)
    standard_error = Column(Float)

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


# ==================== Helper Functions ====================

def create_database_tables(engine):
    """Create all database tables"""
    Base.metadata.create_all(engine)


def drop_database_tables(engine):
    """Drop all database tables (use with caution!)"""
    Base.metadata.drop_all(engine)
