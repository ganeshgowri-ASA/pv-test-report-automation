"""
Compliance Checker Module

Provides comprehensive compliance checking for ISO 17025, NABL, and IEC standards.
Ensures test data and procedures meet international quality and testing standards.

Standards covered:
- ISO/IEC 17025: General requirements for competence of testing and calibration labs
- NABL: National Accreditation Board for Testing and Calibration Laboratories
- IEC 61215: Terrestrial photovoltaic (PV) modules - Design qualification
- IEC 61853: Photovoltaic (PV) module performance testing
- IEC 60904: Photovoltaic devices - Measurement procedures
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .schema_validators import (
    TestDataSchema,
    ValidationResultSchema,
    ValidationSeverityEnum,
    ErrorDetailSchema,
)

logger = logging.getLogger(__name__)


class ComplianceStandard(str, Enum):
    """Compliance standards."""
    ISO_17025 = "ISO/IEC 17025:2017"
    NABL_162 = "NABL 162"
    IEC_61215 = "IEC 61215"
    IEC_61853 = "IEC 61853"
    IEC_60904 = "IEC 60904"
    IEC_62804 = "IEC 62804"


class ComplianceLevel(str, Enum):
    """Compliance achievement levels."""
    FULL = "full"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class ComplianceRequirement:
    """Represents a single compliance requirement."""
    requirement_id: str
    standard: ComplianceStandard
    description: str
    is_mandatory: bool = True
    check_function: Optional[callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceCheckResult:
    """Result of a single compliance check."""
    requirement: ComplianceRequirement
    is_compliant: bool
    level: ComplianceLevel
    findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "requirement_id": self.requirement.requirement_id,
            "standard": self.requirement.standard.value,
            "description": self.requirement.description,
            "is_mandatory": self.requirement.is_mandatory,
            "is_compliant": self.is_compliant,
            "level": self.level.value,
            "findings": self.findings,
            "recommendations": self.recommendations,
            "evidence": self.evidence,
        }


@dataclass
class ComplianceReport:
    """Comprehensive compliance report."""
    overall_compliant: bool
    standard: ComplianceStandard
    check_results: List[ComplianceCheckResult] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate summary statistics."""
        if not self.summary:
            self.summary = {
                "total_checks": len(self.check_results),
                "passed": sum(1 for r in self.check_results if r.is_compliant),
                "failed": sum(1 for r in self.check_results if not r.is_compliant),
                "mandatory_failed": sum(
                    1 for r in self.check_results
                    if not r.is_compliant and r.requirement.is_mandatory
                ),
            }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "overall_compliant": self.overall_compliant,
            "standard": self.standard.value,
            "check_results": [r.to_dict() for r in self.check_results],
            "summary": self.summary,
            "generated_at": self.generated_at.isoformat(),
            "metadata": self.metadata,
        }

    def get_failed_requirements(self) -> List[ComplianceCheckResult]:
        """Get list of failed compliance requirements."""
        return [r for r in self.check_results if not r.is_compliant]

    def get_summary_text(self) -> str:
        """Get human-readable summary."""
        status = "COMPLIANT" if self.overall_compliant else "NON-COMPLIANT"
        return (
            f"{self.standard.value} Compliance: {status}\n"
            f"Checks: {self.summary['passed']}/{self.summary['total_checks']} passed\n"
            f"Mandatory failures: {self.summary['mandatory_failed']}"
        )


class ComplianceChecker:
    """
    Comprehensive compliance checker for PV test data.

    Validates test data and procedures against ISO 17025, NABL, and IEC standards.
    """

    # ISO 17025 Requirements
    ISO_17025_REQUIREMENTS = [
        ComplianceRequirement(
            requirement_id="ISO17025-4.1",
            standard=ComplianceStandard.ISO_17025,
            description="Equipment calibration within valid period",
            is_mandatory=True,
        ),
        ComplianceRequirement(
            requirement_id="ISO17025-4.2",
            standard=ComplianceStandard.ISO_17025,
            description="Calibration certificate documented",
            is_mandatory=True,
        ),
        ComplianceRequirement(
            requirement_id="ISO17025-5.1",
            standard=ComplianceStandard.ISO_17025,
            description="Test procedures documented with standard references",
            is_mandatory=True,
        ),
        ComplianceRequirement(
            requirement_id="ISO17025-5.2",
            standard=ComplianceStandard.ISO_17025,
            description="Measurement uncertainty evaluated",
            is_mandatory=True,
        ),
        ComplianceRequirement(
            requirement_id="ISO17025-6.1",
            standard=ComplianceStandard.ISO_17025,
            description="Test personnel identified",
            is_mandatory=True,
        ),
        ComplianceRequirement(
            requirement_id="ISO17025-7.1",
            standard=ComplianceStandard.ISO_17025,
            description="Test facility documented",
            is_mandatory=True,
        ),
        ComplianceRequirement(
            requirement_id="ISO17025-8.1",
            standard=ComplianceStandard.ISO_17025,
            description="Quality assurance procedures followed",
            is_mandatory=True,
        ),
    ]

    # NABL Requirements
    NABL_REQUIREMENTS = [
        ComplianceRequirement(
            requirement_id="NABL-162-1",
            standard=ComplianceStandard.NABL_162,
            description="Traceability to national/international standards",
            is_mandatory=True,
        ),
        ComplianceRequirement(
            requirement_id="NABL-162-2",
            standard=ComplianceStandard.NABL_162,
            description="Environmental conditions monitored and recorded",
            is_mandatory=True,
        ),
        ComplianceRequirement(
            requirement_id="NABL-162-3",
            standard=ComplianceStandard.NABL_162,
            description="Test reports contain all required information",
            is_mandatory=True,
        ),
        ComplianceRequirement(
            requirement_id="NABL-162-4",
            standard=ComplianceStandard.NABL_162,
            description="Data integrity and authenticity maintained",
            is_mandatory=True,
        ),
    ]

    # IEC Standards Requirements
    IEC_REQUIREMENTS = [
        ComplianceRequirement(
            requirement_id="IEC60904-1",
            standard=ComplianceStandard.IEC_60904,
            description="Current-voltage measurements per IEC 60904-1",
            is_mandatory=True,
        ),
        ComplianceRequirement(
            requirement_id="IEC61215-1",
            standard=ComplianceStandard.IEC_61215,
            description="Module specifications documented per IEC 61215",
            is_mandatory=True,
        ),
        ComplianceRequirement(
            requirement_id="IEC61853-1",
            standard=ComplianceStandard.IEC_61853,
            description="Environmental conditions within IEC 61853 ranges",
            is_mandatory=True,
        ),
    ]

    def __init__(self):
        """Initialize compliance checker."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def check_iso17025_compliance(
        self,
        test_data: TestDataSchema
    ) -> ComplianceReport:
        """
        Check ISO/IEC 17025:2017 compliance.

        Args:
            test_data: Test data to validate

        Returns:
            ComplianceReport with detailed findings
        """
        report = ComplianceReport(
            overall_compliant=True,
            standard=ComplianceStandard.ISO_17025,
        )

        for requirement in self.ISO_17025_REQUIREMENTS:
            result = self._check_iso17025_requirement(requirement, test_data)
            report.check_results.append(result)

            if not result.is_compliant and requirement.is_mandatory:
                report.overall_compliant = False

        report.__post_init__()  # Update summary
        return report

    def _check_iso17025_requirement(
        self,
        requirement: ComplianceRequirement,
        test_data: TestDataSchema
    ) -> ComplianceCheckResult:
        """Check individual ISO 17025 requirement."""
        findings = []
        recommendations = []
        evidence = {}
        is_compliant = True
        level = ComplianceLevel.FULL

        if requirement.requirement_id == "ISO17025-4.1":
            # Equipment calibration validity
            if test_data.calibration_date is None:
                is_compliant = False
                level = ComplianceLevel.NON_COMPLIANT
                findings.append("Calibration date not documented")
                recommendations.append("Record equipment calibration date")
            else:
                days_since_cal = (test_data.test_date - test_data.calibration_date).days
                evidence["calibration_age_days"] = days_since_cal
                evidence["calibration_date"] = test_data.calibration_date.isoformat()

                if days_since_cal > 365:
                    is_compliant = False
                    level = ComplianceLevel.NON_COMPLIANT
                    findings.append(f"Calibration expired ({days_since_cal} days old)")
                    recommendations.append("Recalibrate equipment (max 365 days)")
                elif days_since_cal > 335:
                    level = ComplianceLevel.PARTIAL
                    findings.append(f"Calibration due soon ({days_since_cal} days old)")
                    recommendations.append("Schedule calibration within 30 days")

        elif requirement.requirement_id == "ISO17025-4.2":
            # Calibration certificate
            if not test_data.calibration_certificate:
                is_compliant = False
                level = ComplianceLevel.NON_COMPLIANT
                findings.append("Calibration certificate number not documented")
                recommendations.append("Record calibration certificate number")
            else:
                evidence["calibration_certificate"] = test_data.calibration_certificate

        elif requirement.requirement_id == "ISO17025-5.1":
            # Standard references
            if not test_data.standard_reference:
                is_compliant = False
                level = ComplianceLevel.NON_COMPLIANT
                findings.append("No standard references documented")
                recommendations.append("Document applicable IEC/ISO standards")
            else:
                evidence["standards"] = test_data.standard_reference
                required_standards = {"IEC 60904", "IEC 61215"}
                documented_standards = set(test_data.standard_reference)

                missing = required_standards - documented_standards
                if missing:
                    level = ComplianceLevel.PARTIAL
                    findings.append(f"Missing standard references: {', '.join(missing)}")
                    recommendations.append(f"Add references to: {', '.join(missing)}")

        elif requirement.requirement_id == "ISO17025-5.2":
            # Measurement uncertainty
            has_uncertainty = False
            for measurement in test_data.measurements[:5]:  # Check first 5
                if measurement.measurement_uncertainty:
                    has_uncertainty = True
                    break

            if not has_uncertainty:
                is_compliant = False
                level = ComplianceLevel.NON_COMPLIANT
                findings.append("Measurement uncertainty not evaluated")
                recommendations.append("Include measurement uncertainty for all parameters")
            else:
                evidence["uncertainty_documented"] = True

        elif requirement.requirement_id == "ISO17025-6.1":
            # Test personnel
            if not test_data.operator or not test_data.operator.strip():
                is_compliant = False
                level = ComplianceLevel.NON_COMPLIANT
                findings.append("Test operator not identified")
                recommendations.append("Document test operator name/ID")
            else:
                evidence["operator"] = test_data.operator

        elif requirement.requirement_id == "ISO17025-7.1":
            # Test facility
            if not test_data.test_facility or not test_data.test_facility.strip():
                is_compliant = False
                level = ComplianceLevel.NON_COMPLIANT
                findings.append("Test facility not documented")
                recommendations.append("Document test facility name and location")
            else:
                evidence["test_facility"] = test_data.test_facility

        elif requirement.requirement_id == "ISO17025-8.1":
            # Quality assurance
            if not test_data.quality_assurance_passed:
                level = ComplianceLevel.PARTIAL
                findings.append("Quality assurance not marked as passed")
                recommendations.append("Complete quality assurance checks")
            else:
                evidence["qa_passed"] = True

        return ComplianceCheckResult(
            requirement=requirement,
            is_compliant=is_compliant,
            level=level,
            findings=findings,
            recommendations=recommendations,
            evidence=evidence,
        )

    def check_nabl_compliance(
        self,
        test_data: TestDataSchema
    ) -> ComplianceReport:
        """
        Check NABL compliance.

        Args:
            test_data: Test data to validate

        Returns:
            ComplianceReport with detailed findings
        """
        report = ComplianceReport(
            overall_compliant=True,
            standard=ComplianceStandard.NABL_162,
        )

        for requirement in self.NABL_REQUIREMENTS:
            result = self._check_nabl_requirement(requirement, test_data)
            report.check_results.append(result)

            if not result.is_compliant and requirement.is_mandatory:
                report.overall_compliant = False

        report.__post_init__()  # Update summary
        return report

    def _check_nabl_requirement(
        self,
        requirement: ComplianceRequirement,
        test_data: TestDataSchema
    ) -> ComplianceCheckResult:
        """Check individual NABL requirement."""
        findings = []
        recommendations = []
        evidence = {}
        is_compliant = True
        level = ComplianceLevel.FULL

        if requirement.requirement_id == "NABL-162-1":
            # Traceability to standards
            if not test_data.standard_reference:
                is_compliant = False
                level = ComplianceLevel.NON_COMPLIANT
                findings.append("No traceability to national/international standards")
                recommendations.append("Reference applicable IEC/ISO standards")
            else:
                evidence["standards"] = test_data.standard_reference

            if not test_data.calibration_certificate:
                level = ComplianceLevel.PARTIAL
                findings.append("Calibration certificate not documented for traceability")
                recommendations.append("Document calibration certificate from accredited lab")

        elif requirement.requirement_id == "NABL-162-2":
            # Environmental conditions
            if test_data.conditions:
                evidence["conditions_recorded"] = True

                # Check completeness
                missing_params = []
                if test_data.conditions.irradiance is None:
                    missing_params.append("irradiance")
                if test_data.conditions.module_temperature is None:
                    missing_params.append("module_temperature")
                if test_data.conditions.ambient_temperature is None:
                    missing_params.append("ambient_temperature")

                if missing_params:
                    level = ComplianceLevel.PARTIAL
                    findings.append(f"Missing environmental parameters: {', '.join(missing_params)}")
                    recommendations.append("Record all relevant environmental conditions")
            else:
                is_compliant = False
                level = ComplianceLevel.NON_COMPLIANT
                findings.append("Environmental conditions not recorded")
                recommendations.append("Monitor and record all environmental conditions")

        elif requirement.requirement_id == "NABL-162-3":
            # Test report completeness
            required_fields = {
                "test_id": test_data.test_id,
                "test_date": test_data.test_date,
                "test_facility": test_data.test_facility,
                "operator": test_data.operator,
                "equipment_id": test_data.equipment_id,
            }

            missing = [k for k, v in required_fields.items() if not v]
            if missing:
                is_compliant = False
                level = ComplianceLevel.NON_COMPLIANT
                findings.append(f"Missing required fields: {', '.join(missing)}")
                recommendations.append("Complete all mandatory test report fields")
            else:
                evidence["required_fields_complete"] = True

        elif requirement.requirement_id == "NABL-162-4":
            # Data integrity
            if not test_data.measurements:
                is_compliant = False
                level = ComplianceLevel.NON_COMPLIANT
                findings.append("No measurement data available")
                recommendations.append("Include all measurement data")
            else:
                evidence["measurement_count"] = len(test_data.measurements)

                # Check for data quality flags
                flagged_count = sum(
                    1 for m in test_data.measurements
                    if m.quality_flag and m.quality_flag != "good"
                )

                if flagged_count > 0:
                    evidence["flagged_measurements"] = flagged_count
                    if flagged_count / len(test_data.measurements) > 0.1:  # >10% flagged
                        level = ComplianceLevel.PARTIAL
                        findings.append(f"{flagged_count} measurements flagged for quality issues")
                        recommendations.append("Review and address data quality issues")

        return ComplianceCheckResult(
            requirement=requirement,
            is_compliant=is_compliant,
            level=level,
            findings=findings,
            recommendations=recommendations,
            evidence=evidence,
        )

    def check_iec_conformance(
        self,
        test_data: TestDataSchema
    ) -> ComplianceReport:
        """
        Check IEC standards conformance.

        Args:
            test_data: Test data to validate

        Returns:
            ComplianceReport with detailed findings
        """
        report = ComplianceReport(
            overall_compliant=True,
            standard=ComplianceStandard.IEC_60904,
        )

        for requirement in self.IEC_REQUIREMENTS:
            result = self._check_iec_requirement(requirement, test_data)
            report.check_results.append(result)

            if not result.is_compliant and requirement.is_mandatory:
                report.overall_compliant = False

        report.__post_init__()  # Update summary
        return report

    def _check_iec_requirement(
        self,
        requirement: ComplianceRequirement,
        test_data: TestDataSchema
    ) -> ComplianceCheckResult:
        """Check individual IEC requirement."""
        findings = []
        recommendations = []
        evidence = {}
        is_compliant = True
        level = ComplianceLevel.FULL

        if requirement.requirement_id == "IEC60904-1":
            # I-V measurements
            if not test_data.measurements:
                is_compliant = False
                level = ComplianceLevel.NON_COMPLIANT
                findings.append("No I-V measurements available")
                recommendations.append("Perform I-V curve measurements per IEC 60904-1")
            else:
                evidence["measurement_count"] = len(test_data.measurements)

                # Check for complete I-V curve (should have points from Voc to Isc)
                voltages = [m.voltage for m in test_data.measurements]
                currents = [m.current for m in test_data.measurements]

                if len(voltages) < 10:
                    level = ComplianceLevel.PARTIAL
                    findings.append(f"Insufficient measurement points ({len(voltages)})")
                    recommendations.append("IEC 60904-1 recommends at least 10-20 points")

                evidence["voltage_range"] = (min(voltages), max(voltages))
                evidence["current_range"] = (min(currents), max(currents))

        elif requirement.requirement_id == "IEC61215-1":
            # Module specifications
            if not test_data.module_spec:
                is_compliant = False
                level = ComplianceLevel.NON_COMPLIANT
                findings.append("Module specifications not documented")
                recommendations.append("Document module specs per IEC 61215")
            else:
                # Check for required specifications
                spec = test_data.module_spec
                evidence["module"] = {
                    "manufacturer": spec.manufacturer,
                    "model": spec.model,
                    "technology": spec.technology.value,
                }

                if not spec.certification:
                    level = ComplianceLevel.PARTIAL
                    findings.append("Module certification not documented")
                    recommendations.append("Include IEC 61215 certification if available")

        elif requirement.requirement_id == "IEC61853-1":
            # Environmental conditions ranges
            if not test_data.conditions:
                is_compliant = False
                level = ComplianceLevel.NON_COMPLIANT
                findings.append("Environmental conditions not documented")
                recommendations.append("Document conditions per IEC 61853")
            else:
                conditions = test_data.conditions

                # Check ranges per IEC 61853
                issues = []
                if conditions.irradiance < 0 or conditions.irradiance > 1500:
                    issues.append(f"irradiance ({conditions.irradiance} W/m²)")
                if conditions.module_temperature < -40 or conditions.module_temperature > 85:
                    issues.append(f"module temperature ({conditions.module_temperature}°C)")

                if issues:
                    is_compliant = False
                    level = ComplianceLevel.NON_COMPLIANT
                    findings.append(f"Conditions outside IEC 61853 ranges: {', '.join(issues)}")
                    recommendations.append("Ensure test conditions within IEC 61853 specifications")
                else:
                    evidence["conditions_valid"] = True

        return ComplianceCheckResult(
            requirement=requirement,
            is_compliant=is_compliant,
            level=level,
            findings=findings,
            recommendations=recommendations,
            evidence=evidence,
        )

    def check_data_completeness(
        self,
        test_data: TestDataSchema
    ) -> ValidationResultSchema:
        """
        Check overall data completeness.

        Args:
            test_data: Test data to validate

        Returns:
            ValidationResultSchema with completeness check results
        """
        result = ValidationResultSchema(is_valid=True)

        # Check essential fields
        essential_fields = {
            "test_id": test_data.test_id,
            "test_date": test_data.test_date,
            "test_facility": test_data.test_facility,
            "operator": test_data.operator,
            "equipment_id": test_data.equipment_id,
            "module_spec": test_data.module_spec,
            "conditions": test_data.conditions,
            "measurements": test_data.measurements,
        }

        for field_name, field_value in essential_fields.items():
            if field_value is None or (isinstance(field_value, (list, str)) and not field_value):
                result.add_error(
                    f"Essential field '{field_name}' is missing or empty",
                    field=field_name,
                    severity=ValidationSeverityEnum.ERROR
                )

        # Check measurement data completeness
        if test_data.measurements:
            total = len(test_data.measurements)
            complete = sum(
                1 for m in test_data.measurements
                if m.voltage is not None and m.current is not None
            )

            completeness_ratio = complete / total if total > 0 else 0
            result.metadata["measurement_completeness"] = f"{completeness_ratio:.1%}"

            if completeness_ratio < 0.9:  # Less than 90% complete
                result.add_error(
                    f"Only {completeness_ratio:.1%} of measurements are complete",
                    field="measurements",
                    severity=ValidationSeverityEnum.WARNING,
                    expected="At least 90% complete measurements"
                )

        # Check calibration documentation
        if not test_data.calibration_date:
            result.add_error(
                "Equipment calibration date not documented",
                field="calibration_date",
                severity=ValidationSeverityEnum.ERROR
            )

        if not test_data.calibration_certificate:
            result.add_error(
                "Calibration certificate not documented",
                field="calibration_certificate",
                severity=ValidationSeverityEnum.WARNING
            )

        # Check standard references
        if not test_data.standard_reference:
            result.add_error(
                "No standard references documented",
                field="standard_reference",
                severity=ValidationSeverityEnum.ERROR
            )

        return result


# Convenience functions for direct use

def check_iso17025_compliance(test_data: TestDataSchema) -> ComplianceReport:
    """Check ISO 17025 compliance."""
    checker = ComplianceChecker()
    return checker.check_iso17025_compliance(test_data)


def check_nabl_compliance(test_data: TestDataSchema) -> ComplianceReport:
    """Check NABL compliance."""
    checker = ComplianceChecker()
    return checker.check_nabl_compliance(test_data)


def check_iec_conformance(test_data: TestDataSchema) -> ComplianceReport:
    """Check IEC standards conformance."""
    checker = ComplianceChecker()
    return checker.check_iec_conformance(test_data)


def check_data_completeness(test_data: TestDataSchema) -> ValidationResultSchema:
    """Check data completeness."""
    checker = ComplianceChecker()
    return checker.check_data_completeness(test_data)
