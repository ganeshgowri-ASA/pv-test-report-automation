"""
IEC 62759 Transportation Testing Database Models
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime

from src.models.base import BaseModel


class IEC62759Test(BaseModel):
    """
    IEC 62759 Transportation Testing - Main Test Record

    Covers the complete test sequence:
    1. Initial Flash Test
    2. Edge Loading (Static load)
    3. Dynamic Mechanical Loading
    4. Thermal Cycling
    5. Final Flash Test
    6. Visual Inspection
    """
    __tablename__ = 'iec_62759_tests'

    # Test identification
    test_id = Column(Integer, unique=True, nullable=False)
    module_id = Column(String(100), nullable=False)
    test_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Initial measurements
    initial_pmax = Column(Float, nullable=False, comment="Initial maximum power (W)")
    initial_voc = Column(Float, comment="Initial open circuit voltage (V)")
    initial_isc = Column(Float, comment="Initial short circuit current (A)")
    initial_vmp = Column(Float, comment="Initial voltage at max power (V)")
    initial_imp = Column(Float, comment="Initial current at max power (A)")
    initial_fill_factor = Column(Float, comment="Initial fill factor")

    # Final measurements
    final_pmax = Column(Float, nullable=False, comment="Final maximum power (W)")
    final_voc = Column(Float, comment="Final open circuit voltage (V)")
    final_isc = Column(Float, comment="Final short circuit current (A)")
    final_vmp = Column(Float, comment="Final voltage at max power (V)")
    final_imp = Column(Float, comment="Final current at max power (A)")
    final_fill_factor = Column(Float, comment="Final fill factor")

    # Power degradation
    power_degradation_pct = Column(Float, comment="Power degradation percentage")
    power_degradation_w = Column(Float, comment="Power degradation in watts")

    # Edge loading test results
    edge_load_result = Column(String(50), nullable=False, comment="pass/fail/conditional")
    edge_load_duration_hours = Column(Float, default=1.0, comment="Edge load duration")
    edge_load_pa = Column(Float, default=600, comment="Edge load pressure (Pa)")
    edge_deflection_mm = Column(Float, comment="Maximum deflection during edge load (mm)")
    edge_load_notes = Column(String(500), comment="Edge loading observations")

    # Dynamic mechanical loading results
    dynamic_cycles = Column(Integer, default=1000, comment="Number of dynamic load cycles")
    dynamic_load_pa = Column(Float, default=1000, comment="Dynamic load pressure (Pa)")
    dynamic_frequency_hz = Column(Float, comment="Dynamic load frequency (Hz)")
    dynamic_load_result = Column(String(50), comment="pass/fail/conditional")
    dynamic_load_notes = Column(String(500), comment="Dynamic loading observations")

    # Thermal cycling results
    thermal_cycles = Column(Integer, default=50, comment="Number of thermal cycles")
    thermal_low_temp = Column(Float, default=-40, comment="Low temperature (°C)")
    thermal_high_temp = Column(Float, default=85, comment="High temperature (°C)")
    thermal_ramp_rate = Column(Float, default=100, comment="Ramp rate (°C/hour)")
    thermal_hold_time_min = Column(Float, comment="Hold time at extremes (minutes)")
    thermal_result = Column(String(50), comment="pass/fail/conditional")
    thermal_notes = Column(String(500), comment="Thermal cycling observations")

    # Visual inspection
    visual_inspection_result = Column(String(50), comment="pass/fail/conditional")
    visual_defects = Column(JSON, comment="List of visual defects found")
    visual_notes = Column(String(1000), comment="Visual inspection notes")

    # Overall test status
    pass_status = Column(Boolean, nullable=False, comment="Overall pass/fail")
    test_status = Column(String(50), default="pending", comment="Test execution status")

    # ISO 17025 Compliance fields
    technician_id = Column(String(100), nullable=False, comment="Technician performing test")
    reviewer_id = Column(String(100), comment="Reviewer who approved results")
    lab_temperature = Column(Float, comment="Lab temperature during test (°C)")
    lab_humidity = Column(Float, comment="Lab humidity during test (%RH)")
    equipment_ids = Column(JSON, comment="List of equipment IDs used")
    calibration_dates = Column(JSON, comment="Calibration dates for equipment")
    measurement_uncertainty = Column(JSON, comment="Measurement uncertainty budget")

    # Additional data
    test_sequence_log = Column(JSON, comment="Complete test sequence event log")
    raw_data_path = Column(String(500), comment="Path to raw measurement data files")
    certificate_number = Column(String(100), comment="Test certificate number")

    # Relationships
    compliance_records = relationship("IEC62759Compliance", back_populates="test")

    def calculate_degradation(self):
        """Calculate power degradation"""
        if self.initial_pmax and self.final_pmax:
            self.power_degradation_w = self.initial_pmax - self.final_pmax
            self.power_degradation_pct = (self.power_degradation_w / self.initial_pmax) * 100

    def determine_pass_fail(self):
        """Determine overall pass/fail status"""
        # Pass criteria:
        # 1. No breakage (visual inspection pass)
        # 2. Power degradation < 5%
        # 3. All individual tests pass

        criteria = [
            self.visual_inspection_result == "pass",
            self.edge_load_result == "pass",
            self.dynamic_load_result == "pass",
            self.thermal_result == "pass",
            self.power_degradation_pct is not None and self.power_degradation_pct < 5.0
        ]

        self.pass_status = all(criteria)
        return self.pass_status


class IEC62759Compliance(BaseModel):
    """
    ISO 17025 Compliance tracking for IEC 62759 tests
    """
    __tablename__ = 'iec_62759_compliance'

    test_id = Column(Integer, ForeignKey('iec_62759_tests.id'), nullable=False)
    compliance_check = Column(String(200), nullable=False, comment="Compliance item checked")
    status = Column(String(50), nullable=False, comment="pass/fail/na")
    evidence = Column(String(500), comment="Evidence of compliance")
    checked_by = Column(String(100), nullable=False, comment="Person who verified")
    check_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    test = relationship("IEC62759Test", back_populates="compliance_records")


class IEC62759Equipment(BaseModel):
    """
    Equipment tracking for IEC 62759 tests
    """
    __tablename__ = 'iec_62759_equipment'

    equipment_id = Column(String(100), unique=True, nullable=False)
    equipment_name = Column(String(200), nullable=False)
    equipment_type = Column(String(100), nullable=False, comment="solar_simulator/load_frame/thermal_chamber")
    manufacturer = Column(String(200))
    model = Column(String(200))
    serial_number = Column(String(200))

    # Calibration tracking
    last_calibration_date = Column(DateTime, nullable=False)
    next_calibration_date = Column(DateTime, nullable=False)
    calibration_certificate = Column(String(200), comment="Certificate number")
    calibration_lab = Column(String(200), comment="Calibration laboratory")

    # Measurement uncertainty
    measurement_uncertainty = Column(JSON, comment="Uncertainty budget for this equipment")

    # Status
    status = Column(String(50), default="active", comment="active/calibration/maintenance/retired")
    notes = Column(String(1000))


class IEC62759Module(BaseModel):
    """
    PV Module information for testing
    """
    __tablename__ = 'iec_62759_modules'

    module_id = Column(String(100), unique=True, nullable=False)
    manufacturer = Column(String(200), nullable=False)
    model = Column(String(200), nullable=False)
    serial_number = Column(String(200), unique=True)
    manufacturing_date = Column(DateTime)

    # Module specifications
    rated_power_w = Column(Float, nullable=False, comment="Rated power at STC (W)")
    rated_voltage = Column(Float, comment="Rated voltage (V)")
    rated_current = Column(Float, comment="Rated current (A)")
    module_area_m2 = Column(Float, comment="Module area (m²)")
    cell_technology = Column(String(100), comment="mono-Si/poly-Si/thin-film/etc")

    # Physical dimensions
    length_mm = Column(Float)
    width_mm = Column(Float)
    thickness_mm = Column(Float)
    weight_kg = Column(Float)

    # Customer information
    customer_name = Column(String(200))
    purchase_order = Column(String(100))
    sample_type = Column(String(100), comment="production/prototype/certification")

    notes = Column(String(1000))
