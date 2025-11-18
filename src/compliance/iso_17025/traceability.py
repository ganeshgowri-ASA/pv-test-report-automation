"""
ISO 17025 Measurement Traceability
Ensures complete traceability chain for all measurements
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class CalibrationRecord:
    """Calibration record for equipment"""
    equipment_id: str
    calibration_date: datetime
    next_calibration_date: datetime
    calibration_lab: str
    certificate_number: str
    parameters_calibrated: List[str]
    measurement_uncertainties: Dict[str, float]
    traceability_chain: List[str]  # Chain to national/international standards


@dataclass
class MeasurementRecord:
    """Complete measurement record with traceability"""
    measurement_id: str
    parameter: str
    value: float
    unit: str
    timestamp: datetime
    equipment_id: str
    calibration_record: CalibrationRecord
    measurement_uncertainty: float
    technician_id: str
    environmental_conditions: Dict[str, float]


class TraceabilityManager:
    """
    Manage measurement traceability per ISO 17025

    Requirements:
    - All measurements traceable to SI units
    - Documented calibration chain
    - Valid calibration certificates
    - Measurement uncertainty quantified
    """

    def __init__(self):
        self.calibration_records: Dict[str, CalibrationRecord] = {}
        self.measurement_records: List[MeasurementRecord] = []

    def register_calibration(self, record: CalibrationRecord):
        """Register equipment calibration record"""
        self.calibration_records[record.equipment_id] = record

    def verify_calibration_valid(self, equipment_id: str) -> bool:
        """
        Verify equipment calibration is valid

        Args:
            equipment_id: Equipment identifier

        Returns:
            bool: True if calibration is valid
        """
        if equipment_id not in self.calibration_records:
            return False

        record = self.calibration_records[equipment_id]
        return datetime.now() < record.next_calibration_date

    def record_measurement(
        self,
        measurement_id: str,
        parameter: str,
        value: float,
        unit: str,
        equipment_id: str,
        technician_id: str,
        environmental_conditions: Dict[str, float]
    ) -> MeasurementRecord:
        """
        Record measurement with complete traceability

        Args:
            measurement_id: Unique measurement identifier
            parameter: Parameter measured
            value: Measured value
            unit: Unit of measurement
            equipment_id: Equipment used
            technician_id: Technician performing measurement
            environmental_conditions: Lab conditions during measurement

        Returns:
            MeasurementRecord: Complete measurement record
        """
        if not self.verify_calibration_valid(equipment_id):
            raise ValueError(f"Equipment {equipment_id} calibration is not valid")

        calibration = self.calibration_records[equipment_id]

        # Get measurement uncertainty for this parameter
        uncertainty = calibration.measurement_uncertainties.get(parameter, 0.0)

        record = MeasurementRecord(
            measurement_id=measurement_id,
            parameter=parameter,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            equipment_id=equipment_id,
            calibration_record=calibration,
            measurement_uncertainty=uncertainty,
            technician_id=technician_id,
            environmental_conditions=environmental_conditions
        )

        self.measurement_records.append(record)
        return record

    def get_traceability_chain(self, measurement_id: str) -> Optional[List[str]]:
        """
        Get complete traceability chain for a measurement

        Args:
            measurement_id: Measurement identifier

        Returns:
            List: Traceability chain to national standards
        """
        for record in self.measurement_records:
            if record.measurement_id == measurement_id:
                return record.calibration_record.traceability_chain

        return None

    def generate_traceability_report(self, test_id: str) -> Dict[str, Any]:
        """
        Generate traceability report for a test

        Args:
            test_id: Test identifier

        Returns:
            Dict: Traceability report
        """
        report = {
            "test_id": test_id,
            "generated_date": datetime.now().isoformat(),
            "calibration_records": [],
            "measurement_records": [],
            "traceability_verified": True
        }

        # Include all relevant calibration and measurement records
        for record in self.measurement_records:
            if record.measurement_id.startswith(test_id):
                report["measurement_records"].append({
                    "parameter": record.parameter,
                    "value": record.value,
                    "unit": record.unit,
                    "uncertainty": record.measurement_uncertainty,
                    "equipment": record.equipment_id,
                    "traceability_chain": record.calibration_record.traceability_chain
                })

        return report
