"""
Equipment Management Database Models

Defines database models for equipment registry, calibration tracking,
and Statistical Process Control (SPC) data.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Dict, Any
from decimal import Decimal
import uuid


class EquipmentStatus(Enum):
    """Equipment operational status"""
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    CALIBRATION = "calibration"
    RETIRED = "retired"
    RESERVED = "reserved"
    OUT_OF_SERVICE = "out_of_service"


class CalibrationStatus(Enum):
    """Calibration status"""
    CURRENT = "current"
    DUE_SOON = "due_soon"
    OVERDUE = "overdue"
    IN_PROGRESS = "in_progress"
    FAILED = "failed"


class EquipmentCategory(Enum):
    """Equipment categories for PV testing"""
    IV_TRACER = "iv_tracer"
    PYRANOMETER = "pyranometer"
    TEMPERATURE_SENSOR = "temperature_sensor"
    MULTIMETER = "multimeter"
    POWER_ANALYZER = "power_analyzer"
    WEATHER_STATION = "weather_station"
    OSCOPE = "oscilloscope"
    DATA_LOGGER = "data_logger"
    SPECTRORADIOMETER = "spectroradiometer"
    REFERENCE_CELL = "reference_cell"
    OTHER = "other"


@dataclass
class Equipment:
    """
    Equipment registry model

    Tracks all test equipment with full asset management capabilities.
    """
    equipment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    asset_number: str = ""  # Organization's asset tracking number
    name: str = ""
    manufacturer: str = ""
    model: str = ""
    serial_number: str = ""
    category: EquipmentCategory = EquipmentCategory.OTHER

    # Status and location
    status: EquipmentStatus = EquipmentStatus.ACTIVE
    location: str = ""
    responsible_person: str = ""

    # Dates
    purchase_date: Optional[date] = None
    installation_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    last_maintenance: Optional[date] = None
    next_maintenance: Optional[date] = None

    # Specifications
    specifications: Dict[str, Any] = field(default_factory=dict)
    measurement_range: Dict[str, Any] = field(default_factory=dict)
    accuracy: Optional[str] = None
    resolution: Optional[str] = None

    # Usage tracking
    total_usage_hours: Decimal = Decimal('0')
    test_count: int = 0
    last_used: Optional[datetime] = None

    # Documentation
    manual_url: Optional[str] = None
    calibration_procedure: Optional[str] = None
    notes: str = ""

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'equipment_id': self.equipment_id,
            'asset_number': self.asset_number,
            'name': self.name,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'serial_number': self.serial_number,
            'category': self.category.value,
            'status': self.status.value,
            'location': self.location,
            'responsible_person': self.responsible_person,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'installation_date': self.installation_date.isoformat() if self.installation_date else None,
            'warranty_expiry': self.warranty_expiry.isoformat() if self.warranty_expiry else None,
            'last_maintenance': self.last_maintenance.isoformat() if self.last_maintenance else None,
            'next_maintenance': self.next_maintenance.isoformat() if self.next_maintenance else None,
            'specifications': self.specifications,
            'measurement_range': self.measurement_range,
            'accuracy': self.accuracy,
            'resolution': self.resolution,
            'total_usage_hours': str(self.total_usage_hours),
            'test_count': self.test_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'manual_url': self.manual_url,
            'calibration_procedure': self.calibration_procedure,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Equipment':
        """Create from dictionary"""
        # Convert date strings to date objects
        for date_field in ['purchase_date', 'installation_date', 'warranty_expiry',
                          'last_maintenance', 'next_maintenance']:
            if data.get(date_field):
                data[date_field] = date.fromisoformat(data[date_field])

        # Convert datetime strings
        for dt_field in ['last_used', 'created_at', 'updated_at']:
            if data.get(dt_field):
                data[dt_field] = datetime.fromisoformat(data[dt_field])

        # Convert enums
        if 'category' in data and isinstance(data['category'], str):
            data['category'] = EquipmentCategory(data['category'])
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = EquipmentStatus(data['status'])

        # Convert Decimal
        if 'total_usage_hours' in data and isinstance(data['total_usage_hours'], str):
            data['total_usage_hours'] = Decimal(data['total_usage_hours'])

        return cls(**data)


@dataclass
class CalibrationRecord:
    """
    Calibration record model

    Tracks calibration history with full NABL/ISO 17025 compliance.
    """
    calibration_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    equipment_id: str = ""

    # Calibration details
    calibration_date: date = field(default_factory=date.today)
    due_date: date = field(default_factory=date.today)
    calibration_interval_days: int = 365

    # Calibration provider
    laboratory_name: str = ""
    laboratory_accreditation: str = ""  # e.g., "NABL", "ISO 17025"
    certificate_number: str = ""
    certificate_url: Optional[str] = None

    # Traceability
    reference_standard: str = ""  # Equipment used for calibration
    reference_certificate: str = ""  # Reference standard's certificate
    traceability_chain: List[str] = field(default_factory=list)  # Chain to national/international standards

    # Calibration results
    calibration_status: CalibrationStatus = CalibrationStatus.CURRENT
    as_found_condition: Dict[str, Any] = field(default_factory=dict)
    as_left_condition: Dict[str, Any] = field(default_factory=dict)
    adjustments_made: List[str] = field(default_factory=list)

    # Measurement uncertainty
    uncertainty_budget: Dict[str, Any] = field(default_factory=dict)
    expanded_uncertainty: Optional[Decimal] = None
    coverage_factor: Decimal = Decimal('2.0')  # k=2 for 95% confidence
    confidence_level: Decimal = Decimal('95.0')

    # Environmental conditions
    temperature: Optional[Decimal] = None
    humidity: Optional[Decimal] = None
    pressure: Optional[Decimal] = None

    # Calibration points
    calibration_points: List[Dict[str, Any]] = field(default_factory=list)

    # Personnel
    performed_by: str = ""
    reviewed_by: str = ""
    approved_by: str = ""

    # Status and notes
    passed: bool = True
    notes: str = ""
    next_calibration_reminder_sent: bool = False

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'calibration_id': self.calibration_id,
            'equipment_id': self.equipment_id,
            'calibration_date': self.calibration_date.isoformat(),
            'due_date': self.due_date.isoformat(),
            'calibration_interval_days': self.calibration_interval_days,
            'laboratory_name': self.laboratory_name,
            'laboratory_accreditation': self.laboratory_accreditation,
            'certificate_number': self.certificate_number,
            'certificate_url': self.certificate_url,
            'reference_standard': self.reference_standard,
            'reference_certificate': self.reference_certificate,
            'traceability_chain': self.traceability_chain,
            'calibration_status': self.calibration_status.value,
            'as_found_condition': self.as_found_condition,
            'as_left_condition': self.as_left_condition,
            'adjustments_made': self.adjustments_made,
            'uncertainty_budget': self.uncertainty_budget,
            'expanded_uncertainty': str(self.expanded_uncertainty) if self.expanded_uncertainty else None,
            'coverage_factor': str(self.coverage_factor),
            'confidence_level': str(self.confidence_level),
            'temperature': str(self.temperature) if self.temperature else None,
            'humidity': str(self.humidity) if self.humidity else None,
            'pressure': str(self.pressure) if self.pressure else None,
            'calibration_points': self.calibration_points,
            'performed_by': self.performed_by,
            'reviewed_by': self.reviewed_by,
            'approved_by': self.approved_by,
            'passed': self.passed,
            'notes': self.notes,
            'next_calibration_reminder_sent': self.next_calibration_reminder_sent,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CalibrationRecord':
        """Create from dictionary"""
        # Convert date strings
        for date_field in ['calibration_date', 'due_date']:
            if data.get(date_field):
                data[date_field] = date.fromisoformat(data[date_field])

        # Convert datetime strings
        for dt_field in ['created_at', 'updated_at']:
            if data.get(dt_field):
                data[dt_field] = datetime.fromisoformat(data[dt_field])

        # Convert enums
        if 'calibration_status' in data and isinstance(data['calibration_status'], str):
            data['calibration_status'] = CalibrationStatus(data['calibration_status'])

        # Convert Decimals
        for decimal_field in ['expanded_uncertainty', 'coverage_factor', 'confidence_level',
                             'temperature', 'humidity', 'pressure']:
            if data.get(decimal_field) and isinstance(data[decimal_field], str):
                data[decimal_field] = Decimal(data[decimal_field])

        return cls(**data)


@dataclass
class SPCDataPoint:
    """
    Statistical Process Control data point

    Individual measurement for SPC tracking.
    """
    data_point_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    equipment_id: str = ""

    # Measurement details
    measurement_type: str = ""  # e.g., "voltage_accuracy", "current_accuracy"
    measured_value: Decimal = Decimal('0')
    reference_value: Decimal = Decimal('0')
    error: Decimal = Decimal('0')

    # Context
    test_id: Optional[str] = None
    operator: str = ""
    environmental_conditions: Dict[str, Any] = field(default_factory=dict)

    # Timestamp
    measured_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'data_point_id': self.data_point_id,
            'equipment_id': self.equipment_id,
            'measurement_type': self.measurement_type,
            'measured_value': str(self.measured_value),
            'reference_value': str(self.reference_value),
            'error': str(self.error),
            'test_id': self.test_id,
            'operator': self.operator,
            'environmental_conditions': self.environmental_conditions,
            'measured_at': self.measured_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SPCDataPoint':
        """Create from dictionary"""
        # Convert datetime
        if 'measured_at' in data and isinstance(data['measured_at'], str):
            data['measured_at'] = datetime.fromisoformat(data['measured_at'])

        # Convert Decimals
        for decimal_field in ['measured_value', 'reference_value', 'error']:
            if data.get(decimal_field) and isinstance(data[decimal_field], str):
                data[decimal_field] = Decimal(data[decimal_field])

        return cls(**data)


@dataclass
class SPCControlChart:
    """
    SPC Control Chart configuration and limits

    Defines control chart parameters for monitoring equipment performance.
    """
    chart_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    equipment_id: str = ""
    measurement_type: str = ""

    # Chart type
    chart_type: str = "xbar_r"  # xbar_r, individuals, cusum, ewma

    # Control limits
    center_line: Optional[Decimal] = None
    upper_control_limit: Optional[Decimal] = None
    lower_control_limit: Optional[Decimal] = None
    upper_warning_limit: Optional[Decimal] = None
    lower_warning_limit: Optional[Decimal] = None

    # Specification limits
    upper_spec_limit: Optional[Decimal] = None
    lower_spec_limit: Optional[Decimal] = None
    target_value: Optional[Decimal] = None

    # Process capability
    cp: Optional[Decimal] = None  # Process capability
    cpk: Optional[Decimal] = None  # Process capability index
    pp: Optional[Decimal] = None  # Process performance
    ppk: Optional[Decimal] = None  # Process performance index

    # Chart parameters
    subgroup_size: int = 5
    data_points_for_limits: int = 25
    sigma_multiplier: Decimal = Decimal('3.0')

    # Status
    is_active: bool = True
    last_updated: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'chart_id': self.chart_id,
            'equipment_id': self.equipment_id,
            'measurement_type': self.measurement_type,
            'chart_type': self.chart_type,
            'center_line': str(self.center_line) if self.center_line else None,
            'upper_control_limit': str(self.upper_control_limit) if self.upper_control_limit else None,
            'lower_control_limit': str(self.lower_control_limit) if self.lower_control_limit else None,
            'upper_warning_limit': str(self.upper_warning_limit) if self.upper_warning_limit else None,
            'lower_warning_limit': str(self.lower_warning_limit) if self.lower_warning_limit else None,
            'upper_spec_limit': str(self.upper_spec_limit) if self.upper_spec_limit else None,
            'lower_spec_limit': str(self.lower_spec_limit) if self.lower_spec_limit else None,
            'target_value': str(self.target_value) if self.target_value else None,
            'cp': str(self.cp) if self.cp else None,
            'cpk': str(self.cpk) if self.cpk else None,
            'pp': str(self.pp) if self.pp else None,
            'ppk': str(self.ppk) if self.ppk else None,
            'subgroup_size': self.subgroup_size,
            'data_points_for_limits': self.data_points_for_limits,
            'sigma_multiplier': str(self.sigma_multiplier),
            'is_active': self.is_active,
            'last_updated': self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SPCControlChart':
        """Create from dictionary"""
        # Convert datetime
        if 'last_updated' in data and isinstance(data['last_updated'], str):
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])

        # Convert Decimals
        decimal_fields = ['center_line', 'upper_control_limit', 'lower_control_limit',
                         'upper_warning_limit', 'lower_warning_limit', 'upper_spec_limit',
                         'lower_spec_limit', 'target_value', 'cp', 'cpk', 'pp', 'ppk',
                         'sigma_multiplier']
        for field_name in decimal_fields:
            if data.get(field_name) and isinstance(data[field_name], str):
                data[field_name] = Decimal(data[field_name])

        return cls(**data)


@dataclass
class UsageLog:
    """
    Equipment usage log

    Tracks equipment usage for maintenance scheduling and lifecycle management.
    """
    log_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    equipment_id: str = ""

    # Usage details
    test_id: Optional[str] = None
    operator: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_hours: Decimal = Decimal('0')

    # Usage context
    project_id: Optional[str] = None
    test_type: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'log_id': self.log_id,
            'equipment_id': self.equipment_id,
            'test_id': self.test_id,
            'operator': self.operator,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_hours': str(self.duration_hours),
            'project_id': self.project_id,
            'test_type': self.test_type,
            'notes': self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UsageLog':
        """Create from dictionary"""
        # Convert datetime
        for dt_field in ['start_time', 'end_time']:
            if data.get(dt_field) and isinstance(data[dt_field], str):
                data[dt_field] = datetime.fromisoformat(data[dt_field])

        # Convert Decimal
        if 'duration_hours' in data and isinstance(data['duration_hours'], str):
            data['duration_hours'] = Decimal(data['duration_hours'])

        return cls(**data)
