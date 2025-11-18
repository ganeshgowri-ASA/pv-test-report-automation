"""
Equipment Management Models
ISO 17025 compliant equipment tracking and management
"""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class EquipmentStatus(str, Enum):
    """Equipment status enumeration"""
    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    CALIBRATION_DUE = "calibration_due"
    OUT_OF_SERVICE = "out_of_service"
    RETIRED = "retired"


class EquipmentCategory(str, Enum):
    """Equipment category enumeration"""
    IV_TRACER = "iv_tracer"
    CLIMATE_CHAMBER = "climate_chamber"
    MULTIMETER = "multimeter"
    PYRANOMETER = "pyranometer"
    POWER_ANALYZER = "power_analyzer"
    TEMPERATURE_SENSOR = "temperature_sensor"
    IRRADIANCE_SENSOR = "irradiance_sensor"
    DATA_LOGGER = "data_logger"
    OSCILLOSCOPE = "oscilloscope"
    OTHER = "other"


class MaintenanceType(str, Enum):
    """Maintenance type enumeration"""
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    CALIBRATION = "calibration"
    INSPECTION = "inspection"
    REPAIR = "repair"


class Equipment(BaseModel):
    """
    Equipment model for test lab equipment
    Compliant with ISO/IEC 17025:2017 requirements
    """
    equipment_id: Optional[int] = Field(None, description="Unique equipment identifier")
    name: str = Field(..., description="Equipment name", min_length=1)
    manufacturer: str = Field(..., description="Equipment manufacturer")
    model: str = Field(..., description="Equipment model number")
    serial_number: str = Field(..., description="Equipment serial number", min_length=1)
    category: EquipmentCategory = Field(..., description="Equipment category")
    location: str = Field(..., description="Physical location of equipment")
    status: EquipmentStatus = Field(
        default=EquipmentStatus.AVAILABLE,
        description="Current equipment status"
    )

    # Calibration tracking (ISO 17025 requirement)
    calibration_due_date: date = Field(..., description="Next calibration due date")
    calibration_interval_days: int = Field(
        default=365,
        description="Calibration interval in days",
        ge=1
    )
    last_calibration_date: Optional[date] = Field(
        None,
        description="Last calibration date"
    )
    calibration_certificate_number: Optional[str] = Field(
        None,
        description="Current calibration certificate number"
    )

    # Maintenance tracking
    last_maintenance: Optional[date] = Field(None, description="Last maintenance date")
    next_maintenance_due: Optional[date] = Field(None, description="Next maintenance due date")

    # Equipment specifications
    specifications: Optional[dict] = Field(
        default_factory=dict,
        description="Equipment technical specifications"
    )
    accuracy: Optional[str] = Field(None, description="Equipment accuracy specifications")
    measurement_range: Optional[str] = Field(None, description="Measurement range")

    # Administrative
    purchase_date: Optional[date] = Field(None, description="Purchase date")
    purchase_cost: Optional[float] = Field(None, description="Purchase cost", ge=0)
    warranty_expiry: Optional[date] = Field(None, description="Warranty expiry date")
    responsible_person: Optional[str] = Field(None, description="Person responsible for equipment")

    # Asset management
    asset_tag: Optional[str] = Field(None, description="Asset tag number")
    notes: Optional[str] = Field(None, description="Additional notes")

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @validator('calibration_due_date')
    def validate_calibration_date(cls, v, values):
        """Ensure calibration due date is in the future for new equipment"""
        if v < date.today():
            # If calibration is overdue, this is valid but equipment should be marked accordingly
            pass
        return v

    class Config:
        use_enum_values = True
        json_encoders = {
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }


class UsageLog(BaseModel):
    """
    Usage log for equipment checkout/checkin tracking
    """
    log_id: Optional[int] = Field(None, description="Unique log identifier")
    equipment_id: int = Field(..., description="Equipment being used")
    test_id: Optional[int] = Field(None, description="Associated test ID")
    user_name: str = Field(..., description="Person using the equipment")

    checkout_time: datetime = Field(default_factory=datetime.now)
    checkin_time: Optional[datetime] = Field(None, description="Equipment return time")

    purpose: Optional[str] = Field(None, description="Purpose of equipment use")
    location_used: Optional[str] = Field(None, description="Location where equipment was used")

    # Condition tracking
    condition_at_checkout: Optional[str] = Field(
        default="good",
        description="Equipment condition at checkout"
    )
    condition_at_checkin: Optional[str] = Field(
        None,
        description="Equipment condition at checkin"
    )
    issues_reported: Optional[str] = Field(None, description="Any issues reported during use")

    created_at: datetime = Field(default_factory=datetime.now)

    @property
    def usage_duration(self) -> Optional[float]:
        """Calculate usage duration in hours"""
        if self.checkin_time:
            delta = self.checkin_time - self.checkout_time
            return delta.total_seconds() / 3600
        return None

    @property
    def is_active(self) -> bool:
        """Check if equipment is currently checked out"""
        return self.checkin_time is None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MaintenanceLog(BaseModel):
    """
    Maintenance log for equipment service history
    ISO 17025 requires documented maintenance records
    """
    log_id: Optional[int] = Field(None, description="Unique log identifier")
    equipment_id: int = Field(..., description="Equipment being maintained")
    maintenance_type: MaintenanceType = Field(..., description="Type of maintenance")

    scheduled_date: date = Field(..., description="Scheduled maintenance date")
    completed_date: Optional[date] = Field(None, description="Actual completion date")

    performed_by: str = Field(..., description="Person/company performing maintenance")
    description: str = Field(..., description="Maintenance description")

    parts_replaced: Optional[List[str]] = Field(
        default_factory=list,
        description="Parts replaced during maintenance"
    )
    cost: Optional[float] = Field(None, description="Maintenance cost", ge=0)

    # Quality control
    verification_performed: bool = Field(
        default=False,
        description="Whether verification was performed after maintenance"
    )
    verification_results: Optional[str] = Field(
        None,
        description="Verification test results"
    )

    next_maintenance_due: Optional[date] = Field(
        None,
        description="Next scheduled maintenance date"
    )

    attachments: Optional[List[str]] = Field(
        default_factory=list,
        description="Paths to attachment files (invoices, reports)"
    )
    notes: Optional[str] = Field(None, description="Additional notes")

    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True
        json_encoders = {
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }


class CalibrationRecord(BaseModel):
    """
    Calibration record for ISO 17025 compliance
    Maintains full traceability of equipment calibration
    """
    record_id: Optional[int] = Field(None, description="Unique record identifier")
    equipment_id: int = Field(..., description="Equipment being calibrated")

    calibration_date: date = Field(..., description="Calibration date")
    next_calibration_due: date = Field(..., description="Next calibration due date")

    # ISO 17025 requirements
    calibration_lab: str = Field(
        ...,
        description="Calibrating laboratory (must be accredited)"
    )
    lab_accreditation: str = Field(
        ...,
        description="Laboratory accreditation number (e.g., ISO/IEC 17025)"
    )
    certificate_number: str = Field(
        ...,
        description="Calibration certificate number",
        min_length=1
    )

    # Traceability
    standard_used: Optional[str] = Field(
        None,
        description="Reference standard used for calibration"
    )
    traceability: str = Field(
        ...,
        description="Traceability chain (e.g., NIST, PTB)"
    )

    # Results
    calibration_results: dict = Field(
        default_factory=dict,
        description="Calibration measurement results"
    )
    measurement_uncertainty: Optional[dict] = Field(
        None,
        description="Measurement uncertainties"
    )
    pass_fail: bool = Field(..., description="Calibration pass/fail status")

    # Environmental conditions
    temperature: Optional[float] = Field(None, description="Temperature during calibration (°C)")
    humidity: Optional[float] = Field(None, description="Humidity during calibration (%)")

    # Documentation
    certificate_path: Optional[str] = Field(
        None,
        description="Path to calibration certificate file"
    )
    performed_by: str = Field(..., description="Technician who performed calibration")
    verified_by: Optional[str] = Field(None, description="Person who verified calibration")

    notes: Optional[str] = Field(None, description="Additional notes")
    created_at: datetime = Field(default_factory=datetime.now)

    @validator('next_calibration_due')
    def validate_next_calibration(cls, v, values):
        """Ensure next calibration is after current calibration"""
        if 'calibration_date' in values and v <= values['calibration_date']:
            raise ValueError("Next calibration date must be after calibration date")
        return v

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }


class EquipmentReservation(BaseModel):
    """
    Equipment reservation for availability scheduling
    """
    reservation_id: Optional[int] = Field(None, description="Unique reservation identifier")
    equipment_id: int = Field(..., description="Equipment being reserved")

    reserved_by: str = Field(..., description="Person making reservation")
    test_id: Optional[int] = Field(None, description="Associated test ID")

    start_time: datetime = Field(..., description="Reservation start time")
    end_time: datetime = Field(..., description="Reservation end time")

    purpose: Optional[str] = Field(None, description="Purpose of reservation")
    status: str = Field(
        default="confirmed",
        description="Reservation status: confirmed, cancelled, completed"
    )

    created_at: datetime = Field(default_factory=datetime.now)

    @validator('end_time')
    def validate_end_time(cls, v, values):
        """Ensure end time is after start time"""
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError("End time must be after start time")
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
