"""
Data models for test results and compliance checking.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from .measurement import Measurement, MeasurementSeries


class TestStatus(Enum):
    """Test execution status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class ComplianceStatus(Enum):
    """Compliance check result."""
    PASS = "pass"
    FAIL = "fail"
    CONDITIONAL_PASS = "conditional_pass"
    NOT_APPLICABLE = "not_applicable"
    PENDING = "pending"


@dataclass
class AcceptanceCriteria:
    """Test acceptance criteria definition."""
    parameter: str
    requirement: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    target_value: Optional[float] = None
    tolerance: Optional[float] = None
    clause_reference: Optional[str] = None

    def evaluate(self, value: float) -> tuple[ComplianceStatus, str]:
        """
        Evaluate if value meets acceptance criteria.

        Returns:
            Tuple of (compliance_status, reason)
        """
        if self.min_value is not None and value < self.min_value:
            return (
                ComplianceStatus.FAIL,
                f"Value {value} below minimum {self.min_value}"
            )

        if self.max_value is not None and value > self.max_value:
            return (
                ComplianceStatus.FAIL,
                f"Value {value} above maximum {self.max_value}"
            )

        if self.target_value is not None and self.tolerance is not None:
            deviation = abs(value - self.target_value)
            if deviation > self.tolerance:
                return (
                    ComplianceStatus.FAIL,
                    f"Value {value} deviates from target {self.target_value} by {deviation} (tolerance: {self.tolerance})"
                )

        return (ComplianceStatus.PASS, "Meets acceptance criteria")


@dataclass
class TestResult:
    """Individual test result with compliance evaluation."""
    test_id: str
    test_name: str
    test_type: str
    standard_reference: str
    clause_reference: str

    # Test execution
    status: TestStatus = TestStatus.NOT_STARTED
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # Measurements
    measurements: List[Measurement] = field(default_factory=list)
    measurement_series: List[MeasurementSeries] = field(default_factory=list)

    # Compliance
    acceptance_criteria: List[AcceptanceCriteria] = field(default_factory=list)
    compliance_status: ComplianceStatus = ComplianceStatus.PENDING
    compliance_notes: Optional[str] = None

    # Test conditions
    test_conditions: Dict[str, Any] = field(default_factory=dict)
    environmental_conditions: Dict[str, Any] = field(default_factory=dict)

    # Documentation
    operator: Optional[str] = None
    reviewer: Optional[str] = None
    review_date: Optional[datetime] = None
    observations: Optional[str] = None
    photos: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)

    # Module information
    module_id: Optional[str] = None
    module_serial_number: Optional[str] = None

    def add_measurement(self, measurement: Measurement) -> None:
        """Add a measurement to test result."""
        self.measurements.append(measurement)

    def add_measurement_series(self, series: MeasurementSeries) -> None:
        """Add a measurement series to test result."""
        self.measurement_series.append(series)

    def evaluate_compliance(self) -> None:
        """Evaluate test compliance based on acceptance criteria."""
        if not self.acceptance_criteria:
            self.compliance_status = ComplianceStatus.NOT_APPLICABLE
            return

        fail_count = 0
        fail_reasons = []

        for criteria in self.acceptance_criteria:
            # Find corresponding measurement
            matching_measurements = [
                m for m in self.measurements
                if m.parameter == criteria.parameter and m.is_valid()
            ]

            if not matching_measurements:
                fail_count += 1
                fail_reasons.append(f"No valid measurement for {criteria.parameter}")
                continue

            # Use most recent measurement
            measurement = matching_measurements[-1]
            status, reason = criteria.evaluate(measurement.value)

            if status == ComplianceStatus.FAIL:
                fail_count += 1
                fail_reasons.append(reason)

        if fail_count > 0:
            self.compliance_status = ComplianceStatus.FAIL
            self.compliance_notes = "; ".join(fail_reasons)
        else:
            self.compliance_status = ComplianceStatus.PASS
            self.compliance_notes = "All acceptance criteria met"

    def get_duration(self) -> Optional[float]:
        """Get test duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert test result to dictionary."""
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "test_type": self.test_type,
            "standard_reference": self.standard_reference,
            "clause_reference": self.clause_reference,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.get_duration(),
            "compliance_status": self.compliance_status.value,
            "compliance_notes": self.compliance_notes,
            "measurements": [m.to_dict() for m in self.measurements],
            "test_conditions": self.test_conditions,
            "environmental_conditions": self.environmental_conditions,
            "operator": self.operator,
            "reviewer": self.reviewer,
            "observations": self.observations,
            "module_id": self.module_id,
        }


@dataclass
class ModuleUnderTest:
    """Information about the module being tested."""
    manufacturer: str
    model: str
    serial_number: str
    module_type: str  # "crystalline" or "thin_film"

    # Nameplate data
    rated_power: float  # Watts
    rated_voltage: float  # Volts
    rated_current: float  # Amperes
    open_circuit_voltage: float  # Volts
    short_circuit_current: float  # Amperes

    # Physical characteristics
    length: float  # mm
    width: float  # mm
    thickness: float  # mm
    weight: float  # kg
    area: float  # m²

    # Cell information
    cell_type: str
    number_of_cells: int
    cell_technology: Optional[str] = None

    # Additional information
    manufacture_date: Optional[datetime] = None
    frame_type: Optional[str] = None
    junction_box: Optional[str] = None
    connector_type: Optional[str] = None
    glass_type: Optional[str] = None
    backsheet_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert module info to dictionary."""
        return {
            "manufacturer": self.manufacturer,
            "model": self.model,
            "serial_number": self.serial_number,
            "module_type": self.module_type,
            "rated_power": self.rated_power,
            "rated_voltage": self.rated_voltage,
            "rated_current": self.rated_current,
            "open_circuit_voltage": self.open_circuit_voltage,
            "short_circuit_current": self.short_circuit_current,
            "dimensions": {
                "length": self.length,
                "width": self.width,
                "thickness": self.thickness,
            },
            "weight": self.weight,
            "area": self.area,
            "cell_type": self.cell_type,
            "number_of_cells": self.number_of_cells,
        }
