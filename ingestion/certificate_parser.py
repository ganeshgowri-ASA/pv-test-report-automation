"""
Specialized parser for ISO 17025/NABL calibration certificates.
"""

import re
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from dateutil import parser as date_parser

from ingestion.exceptions import DocumentParsingError, ValidationError
from ingestion.models import (
    AccreditationBody,
    CalibrationCertificate,
    CalibrationPoint,
    TraceabilityInfo,
    UncertaintyMeasurement,
)
from ingestion.pdf_parser import PDFIngestion


class CertificateParser:
    """Parser specialized for calibration certificates."""

    # Common patterns for certificate parsing
    CERT_NUMBER_PATTERNS = [
        r"certificate\s+(?:no|number|#)[\s:]+([A-Z0-9\-/]+)",
        r"cert\.?\s+(?:no|number|#)[\s:]+([A-Z0-9\-/]+)",
        r"certificate[\s:]+([A-Z0-9\-/]+)",
    ]

    DATE_PATTERNS = [
        r"calibration\s+date[\s:]+([0-9\-/\.]+)",
        r"date\s+of\s+calibration[\s:]+([0-9\-/\.]+)",
        r"calibrated\s+on[\s:]+([0-9\-/\.]+)",
    ]

    DUE_DATE_PATTERNS = [
        r"due\s+date[\s:]+([0-9\-/\.]+)",
        r"next\s+calibration[\s:]+([0-9\-/\.]+)",
        r"valid\s+until[\s:]+([0-9\-/\.]+)",
        r"re-?calibration\s+due[\s:]+([0-9\-/\.]+)",
    ]

    EQUIPMENT_PATTERNS = [
        r"equipment[\s:]+(.+?)(?:\n|model)",
        r"instrument[\s:]+(.+?)(?:\n|model)",
        r"device[\s:]+(.+?)(?:\n|model)",
    ]

    MODEL_PATTERNS = [
        r"model[\s:]+([A-Z0-9\-/]+)",
        r"type[\s:]+([A-Z0-9\-/]+)",
    ]

    SERIAL_PATTERNS = [
        r"serial\s+(?:no|number|#)[\s:]+([A-Z0-9\-/]+)",
        r"s/?n[\s:]+([A-Z0-9\-/]+)",
    ]

    UNCERTAINTY_PATTERNS = [
        r"uncertainty[\s:]+([±]?\s*[\d.]+)\s*([a-zA-Z%°]+)",
        r"expanded\s+uncertainty[\s:]+([±]?\s*[\d.]+)\s*([a-zA-Z%°]+)",
        r"U\s*=\s*([±]?\s*[\d.]+)\s*([a-zA-Z%°]+)",
    ]

    def __init__(self, file_path: str):
        """
        Initialize certificate parser.

        Args:
            file_path: Path to calibration certificate (PDF)
        """
        self.file_path = Path(file_path)
        self.pdf_parser = PDFIngestion(str(file_path))
        self.raw_text = ""
        self.tables = []

    def extract_data(self):
        """Extract raw data from certificate."""
        result = self.pdf_parser.parse()
        self.raw_text = result.text_content.lower()  # Lowercase for pattern matching
        self.tables = result.tables

    def extract_certificate_number(self) -> Optional[str]:
        """Extract certificate number."""
        for pattern in self.CERT_NUMBER_PATTERNS:
            match = re.search(pattern, self.raw_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def extract_dates(self) -> Tuple[Optional[date], Optional[date]]:
        """
        Extract calibration date and due date.

        Returns:
            Tuple of (calibration_date, due_date)
        """
        cal_date = None
        due_date = None

        # Extract calibration date
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, self.raw_text, re.IGNORECASE)
            if match:
                date_str = match.group(1).strip()
                cal_date = self._parse_date(date_str)
                if cal_date:
                    break

        # Extract due date
        for pattern in self.DUE_DATE_PATTERNS:
            match = re.search(pattern, self.raw_text, re.IGNORECASE)
            if match:
                date_str = match.group(1).strip()
                due_date = self._parse_date(date_str)
                if due_date:
                    break

        return cal_date, due_date

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string flexibly."""
        try:
            parsed = date_parser.parse(date_str, fuzzy=True)
            return parsed.date()
        except Exception:
            return None

    def extract_equipment_info(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract equipment name, model, and serial number.

        Returns:
            Tuple of (equipment_name, model, serial_number)
        """
        equipment_name = None
        model = None
        serial_number = None

        # Extract equipment name
        for pattern in self.EQUIPMENT_PATTERNS:
            match = re.search(pattern, self.raw_text, re.IGNORECASE)
            if match:
                equipment_name = match.group(1).strip()
                break

        # Extract model
        for pattern in self.MODEL_PATTERNS:
            match = re.search(pattern, self.raw_text, re.IGNORECASE)
            if match:
                model = match.group(1).strip()
                break

        # Extract serial number
        for pattern in self.SERIAL_PATTERNS:
            match = re.search(pattern, self.raw_text, re.IGNORECASE)
            if match:
                serial_number = match.group(1).strip()
                break

        return equipment_name, model, serial_number

    def extract_uncertainty(self) -> Optional[UncertaintyMeasurement]:
        """Extract measurement uncertainty."""
        for pattern in self.UNCERTAINTY_PATTERNS:
            match = re.search(pattern, self.raw_text, re.IGNORECASE)
            if match:
                value_str = match.group(1).replace("±", "").strip()
                unit = match.group(2).strip()

                try:
                    value = float(value_str)
                    return UncertaintyMeasurement(value=value, unit=unit)
                except ValueError:
                    continue

        return None

    def extract_accreditation_body(self) -> AccreditationBody:
        """Detect accreditation body from text."""
        text_upper = self.raw_text.upper()

        if "NABL" in text_upper:
            return AccreditationBody.NABL
        elif "ILAC" in text_upper:
            return AccreditationBody.ILAC
        elif "A2LA" in text_upper:
            return AccreditationBody.A2LA
        elif "UKAS" in text_upper:
            return AccreditationBody.UKAS
        elif "DAKKS" in text_upper or "DAkkS" in self.raw_text:
            return AccreditationBody.DAkkS

        return AccreditationBody.UNKNOWN

    def extract_accreditation_number(self) -> Optional[str]:
        """Extract accreditation certificate number."""
        patterns = [
            r"accreditation\s+(?:no|number|#)[\s:]+([A-Z0-9\-/]+)",
            r"nabl\s+(?:no|number|#)[\s:]+([A-Z0-9\-/]+)",
            r"cert\.?\s+no\.?\s+([A-Z0-9\-/]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, self.raw_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def extract_laboratory_info(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract laboratory name and address.

        Returns:
            Tuple of (lab_name, lab_address)
        """
        lab_name = None
        lab_address = None

        # Look for laboratory/lab name
        patterns = [
            r"laboratory[\s:]+(.+?)(?:\n)",
            r"calibration\s+laboratory[\s:]+(.+?)(?:\n)",
            r"lab[\s:]+(.+?)(?:\n)",
        ]

        for pattern in patterns:
            match = re.search(pattern, self.raw_text, re.IGNORECASE)
            if match:
                lab_name = match.group(1).strip()
                break

        # Address extraction is complex - simplified approach
        # Look for address keywords
        if "address" in self.raw_text:
            addr_match = re.search(
                r"address[\s:]+(.{20,200})", self.raw_text, re.IGNORECASE | re.DOTALL
            )
            if addr_match:
                lab_address = addr_match.group(1).strip()[:200]  # Limit length

        return lab_name, lab_address

    def extract_personnel(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract personnel names (calibrated by, reviewed by, approved by).

        Returns:
            Tuple of (calibrated_by, reviewed_by, approved_by)
        """
        calibrated_by = None
        reviewed_by = None
        approved_by = None

        # Calibrated by
        match = re.search(
            r"calibrated\s+by[\s:]+(.+?)(?:\n|approved|reviewed)",
            self.raw_text,
            re.IGNORECASE,
        )
        if match:
            calibrated_by = match.group(1).strip()

        # Reviewed by
        match = re.search(
            r"reviewed\s+by[\s:]+(.+?)(?:\n|approved|calibrated)",
            self.raw_text,
            re.IGNORECASE,
        )
        if match:
            reviewed_by = match.group(1).strip()

        # Approved by
        match = re.search(
            r"approved\s+by[\s:]+(.+?)(?:\n|reviewed|calibrated)",
            self.raw_text,
            re.IGNORECASE,
        )
        if match:
            approved_by = match.group(1).strip()

        return calibrated_by, reviewed_by, approved_by

    def extract_environmental_conditions(self) -> Dict[str, str]:
        """Extract environmental conditions during calibration."""
        conditions = {}

        # Temperature
        temp_match = re.search(
            r"temperature[\s:]+([0-9±.\s°C]+)", self.raw_text, re.IGNORECASE
        )
        if temp_match:
            conditions["temperature"] = temp_match.group(1).strip()

        # Humidity
        humidity_match = re.search(
            r"humidity[\s:]+([0-9±.\s%RH]+)", self.raw_text, re.IGNORECASE
        )
        if humidity_match:
            conditions["humidity"] = humidity_match.group(1).strip()

        # Pressure
        pressure_match = re.search(
            r"pressure[\s:]+([0-9±.\skPa]+)", self.raw_text, re.IGNORECASE
        )
        if pressure_match:
            conditions["pressure"] = pressure_match.group(1).strip()

        return conditions

    def extract_calibration_points(self) -> List[CalibrationPoint]:
        """Extract calibration points from tables."""
        calibration_points = []

        for table in self.tables:
            df = table.to_dataframe()

            # Look for columns containing calibration data
            # Common column names: Reference, Measured, Deviation, etc.

            ref_col = None
            measured_col = None
            unit_col = None

            for col in df.columns:
                col_lower = str(col).lower()
                if "reference" in col_lower or "standard" in col_lower:
                    ref_col = col
                elif "measured" in col_lower or "uut" in col_lower or "dut" in col_lower:
                    measured_col = col
                elif "unit" in col_lower:
                    unit_col = col

            if ref_col and measured_col:
                # Extract calibration points
                for idx, row in df.iterrows():
                    try:
                        ref_val = float(str(row[ref_col]).strip())
                        meas_val = float(str(row[measured_col]).strip())

                        unit = "unit"
                        if unit_col and unit_col in row:
                            unit = str(row[unit_col]).strip()

                        deviation = meas_val - ref_val

                        cal_point = CalibrationPoint(
                            reference_value=ref_val,
                            measured_value=meas_val,
                            unit=unit,
                            deviation=deviation,
                        )
                        calibration_points.append(cal_point)

                    except (ValueError, TypeError, KeyError):
                        continue

        return calibration_points

    def extract_traceability(self) -> Optional[TraceabilityInfo]:
        """Extract traceability information."""
        ref_standard = None
        standard_id = None

        # Look for reference standard
        patterns = [
            r"reference\s+standard[\s:]+(.+?)(?:\n|cert)",
            r"traceability[\s:]+(.+?)(?:\n|cert)",
            r"standard\s+used[\s:]+(.+?)(?:\n)",
        ]

        for pattern in patterns:
            match = re.search(pattern, self.raw_text, re.IGNORECASE)
            if match:
                ref_standard = match.group(1).strip()
                break

        # Look for standard ID or certificate
        std_id_match = re.search(
            r"(?:standard|ref\.?)\s+(?:id|cert|no)[\s:]+([A-Z0-9\-/]+)",
            self.raw_text,
            re.IGNORECASE,
        )
        if std_id_match:
            standard_id = std_id_match.group(1).strip()

        if ref_standard:
            return TraceabilityInfo(reference_standard=ref_standard, standard_id=standard_id)

        return None

    def parse(self) -> CalibrationCertificate:
        """
        Parse calibration certificate.

        Returns:
            CalibrationCertificate object

        Raises:
            DocumentParsingError: If parsing fails
            ValidationError: If required fields are missing
        """
        try:
            # Extract raw data first
            self.extract_data()

            # Extract all fields
            cert_number = self.extract_certificate_number()
            cal_date, due_date = self.extract_dates()
            equipment_name, model, serial = self.extract_equipment_info()
            uncertainty = self.extract_uncertainty()
            accreditation_body = self.extract_accreditation_body()
            accreditation_number = self.extract_accreditation_number()
            lab_name, lab_address = self.extract_laboratory_info()
            calibrated_by, reviewed_by, approved_by = self.extract_personnel()
            env_conditions = self.extract_environmental_conditions()
            calibration_points = self.extract_calibration_points()
            traceability = self.extract_traceability()

            # Validate required fields
            if not cert_number:
                raise ValidationError("Certificate number not found", "certificate_number")
            if not equipment_name:
                raise ValidationError("Equipment name not found", "equipment_name")
            if not cal_date:
                raise ValidationError("Calibration date not found", "calibration_date")
            if not lab_name:
                raise ValidationError("Laboratory name not found", "laboratory_name")

            # Calculate interval if both dates available
            interval_months = None
            if cal_date and due_date:
                days_diff = (due_date - cal_date).days
                interval_months = round(days_diff / 30.0)

            certificate = CalibrationCertificate(
                certificate_number=cert_number,
                equipment_id=serial or "UNKNOWN",
                equipment_name=equipment_name,
                model=model,
                serial_number=serial,
                calibration_date=cal_date,
                due_date=due_date,
                calibration_interval_months=interval_months,
                uncertainty=uncertainty,
                calibration_points=calibration_points,
                traceability=traceability,
                accreditation_body=accreditation_body,
                accreditation_number=accreditation_number,
                laboratory_name=lab_name,
                laboratory_address=lab_address,
                calibrated_by=calibrated_by,
                reviewed_by=reviewed_by,
                approved_by=approved_by,
                environmental_conditions=env_conditions,
                raw_text=self.pdf_parser.extract_text(),  # Original case text
            )

            return certificate

        except ValidationError:
            raise
        except Exception as e:
            raise DocumentParsingError(
                f"Failed to parse calibration certificate: {str(e)}", str(self.file_path)
            )


def parse_calibration_certificate(file_path: str) -> CalibrationCertificate:
    """
    Convenience function to parse a calibration certificate.

    Args:
        file_path: Path to calibration certificate PDF

    Returns:
        CalibrationCertificate object

    Example:
        >>> cert = parse_calibration_certificate("equipment_cal.pdf")
        >>> print(f"Cal Date: {cert.calibration_date}")
        >>> print(f"Due Date: {cert.due_date}")
        >>> print(f"Valid: {cert.is_valid()}")
    """
    parser = CertificateParser(file_path)
    return parser.parse()
