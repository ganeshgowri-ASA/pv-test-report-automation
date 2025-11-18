"""Certificate parsing functionality for extracting calibration data from PDFs."""

import re
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

from .models import (
    CalibrationCertificate,
    AccreditationBody,
    UncertaintyBudget,
    UncertaintyType,
    TraceabilityChain,
    CalibrationPoint,
)


@dataclass
class ParsedCertificateData:
    """Container for parsed certificate data."""
    cert_number: Optional[str] = None
    calibration_date: Optional[date] = None
    due_date: Optional[date] = None
    calibration_lab: Optional[str] = None
    accreditation_body: Optional[str] = None
    uncertainty: Optional[float] = None
    traceability_chain: Optional[str] = None
    calibration_points: List[CalibrationPoint] = None
    environmental_conditions: Dict[str, Any] = None
    technician: Optional[str] = None
    reviewer: Optional[str] = None

    def __post_init__(self):
        if self.calibration_points is None:
            self.calibration_points = []
        if self.environmental_conditions is None:
            self.environmental_conditions = {}


class CertificateParser:
    """
    Parse calibration certificates from PDF and text files.

    Supports multiple certificate formats from various accreditation bodies.
    Uses regex patterns to extract key information.
    """

    # Common date patterns
    DATE_PATTERNS = [
        r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',  # DD-MM-YYYY or DD/MM/YYYY
        r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',    # YYYY-MM-DD
        r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})',  # DD Mon YYYY
    ]

    # Certificate number patterns
    CERT_NUMBER_PATTERNS = [
        r'Certificate\s+(?:No|Number|#)[:\s]+([A-Z0-9/-]+)',
        r'Cert\s+(?:No|#)[:\s]+([A-Z0-9/-]+)',
        r'Certificate\s+ID[:\s]+([A-Z0-9/-]+)',
    ]

    # Uncertainty patterns
    UNCERTAINTY_PATTERNS = [
        r'Uncertainty[:\s]+([0-9.]+)\s*([%°µma-zA-Z]+)',
        r'U\s*=\s*([0-9.]+)\s*([%°µma-zA-Z]+)',
        r'Expanded\s+Uncertainty[:\s]+([0-9.]+)\s*([%°µma-zA-Z]+)',
    ]

    # Accreditation body patterns
    ACCREDITATION_PATTERNS = {
        'NABL': r'NABL',
        'ILAC': r'ILAC',
        'A2LA': r'A2LA',
        'UKAS': r'UKAS',
        'DAkkS': r'DAkkS',
        'CNAS': r'CNAS',
    }

    def __init__(self):
        """Initialize the parser."""
        self.text_extractors = {
            '.pdf': self._extract_text_from_pdf,
            '.txt': self._extract_text_from_txt,
        }

    def parse_certificate(
        self,
        cert_file: Path,
        equipment_id: int,
        **additional_data
    ) -> CalibrationCertificate:
        """
        Parse calibration certificate from file.

        Args:
            cert_file: Path to certificate file (PDF or TXT)
            equipment_id: Equipment ID this certificate belongs to
            additional_data: Additional fields to override or supplement parsed data

        Returns:
            CalibrationCertificate object

        Raises:
            ValueError: If file format is unsupported or required data cannot be parsed
            FileNotFoundError: If certificate file doesn't exist
        """
        if not cert_file.exists():
            raise FileNotFoundError(f"Certificate file not found: {cert_file}")

        # Extract text from certificate
        text = self._extract_text(cert_file)

        # Parse certificate data
        parsed_data = self._parse_text(text)

        # Apply additional data overrides
        for key, value in additional_data.items():
            if hasattr(parsed_data, key):
                setattr(parsed_data, key, value)

        # Validate required fields
        self._validate_parsed_data(parsed_data)

        # Create CalibrationCertificate object
        return self._create_certificate(parsed_data, cert_file, equipment_id)

    def _extract_text(self, cert_file: Path) -> str:
        """Extract text from certificate file based on file type."""
        file_ext = cert_file.suffix.lower()

        if file_ext not in self.text_extractors:
            raise ValueError(f"Unsupported file format: {file_ext}. Supported: {list(self.text_extractors.keys())}")

        return self.text_extractors[file_ext](cert_file)

    def _extract_text_from_pdf(self, pdf_file: Path) -> str:
        """
        Extract text from PDF file.

        Note: This is a placeholder. In production, use a library like PyPDF2, pdfplumber, or pypdf.
        For now, returns empty string to allow testing without PDF dependencies.
        """
        try:
            # Try to import PDF library
            import PyPDF2
            with open(pdf_file, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            # PDF library not available - return placeholder
            # In production, this should raise an error or use alternative method
            return f"[PDF extraction requires PyPDF2 library - file: {pdf_file.name}]"

    def _extract_text_from_txt(self, txt_file: Path) -> str:
        """Extract text from plain text file."""
        with open(txt_file, 'r', encoding='utf-8') as f:
            return f.read()

    def _parse_text(self, text: str) -> ParsedCertificateData:
        """Parse certificate data from extracted text."""
        data = ParsedCertificateData()

        # Parse certificate number
        data.cert_number = self._extract_cert_number(text)

        # Parse dates
        dates = self._extract_dates(text)
        if dates:
            data.calibration_date = dates.get('calibration_date')
            data.due_date = dates.get('due_date')

        # Parse calibration lab
        data.calibration_lab = self._extract_lab_name(text)

        # Parse accreditation body
        data.accreditation_body = self._extract_accreditation_body(text)

        # Parse uncertainty
        uncertainty_data = self._extract_uncertainty(text)
        if uncertainty_data:
            data.uncertainty = uncertainty_data[0]

        # Parse traceability
        data.traceability_chain = self._extract_traceability(text)

        # Parse environmental conditions
        data.environmental_conditions = self._extract_environmental_conditions(text)

        # Parse technician/reviewer
        data.technician = self._extract_field(text, r'Technician[:\s]+([^\n]+)')
        data.reviewer = self._extract_field(text, r'Reviewed\s+by[:\s]+([^\n]+)')

        return data

    def _extract_cert_number(self, text: str) -> Optional[str]:
        """Extract certificate number from text."""
        for pattern in self.CERT_NUMBER_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_dates(self, text: str) -> Dict[str, date]:
        """Extract calibration and due dates from text."""
        dates = {}

        # Look for calibration date
        cal_date_patterns = [
            r'Calibration\s+Date[:\s]+' + '|'.join(self.DATE_PATTERNS),
            r'Date\s+of\s+Calibration[:\s]+' + '|'.join(self.DATE_PATTERNS),
        ]

        for pattern in cal_date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                parsed_date = self._parse_date_string(date_str)
                if parsed_date:
                    dates['calibration_date'] = parsed_date
                    break

        # Look for due date
        due_date_patterns = [
            r'Due\s+Date[:\s]+' + '|'.join(self.DATE_PATTERNS),
            r'Next\s+Calibration[:\s]+' + '|'.join(self.DATE_PATTERNS),
            r'Valid\s+Until[:\s]+' + '|'.join(self.DATE_PATTERNS),
        ]

        for pattern in due_date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                parsed_date = self._parse_date_string(date_str)
                if parsed_date:
                    dates['due_date'] = parsed_date
                    break

        return dates

    def _parse_date_string(self, date_str: str) -> Optional[date]:
        """Parse date string into date object."""
        date_formats = [
            '%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y',
            '%Y-%m-%d', '%Y/%m/%d',
            '%d-%m-%y', '%d/%m/%y',
            '%d %b %Y', '%d %B %Y',
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue

        return None

    def _extract_lab_name(self, text: str) -> Optional[str]:
        """Extract calibration laboratory name."""
        patterns = [
            r'(?:Calibration\s+)?Laboratory[:\s]+([^\n]+)',
            r'Lab\s+Name[:\s]+([^\n]+)',
            r'Calibrated\s+by[:\s]+([^\n]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_accreditation_body(self, text: str) -> Optional[str]:
        """Extract accreditation body."""
        for body, pattern in self.ACCREDITATION_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                return body

        return 'OTHER'

    def _extract_uncertainty(self, text: str) -> Optional[Tuple[float, str]]:
        """Extract measurement uncertainty and unit."""
        for pattern in self.UNCERTAINTY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1))
                    unit = match.group(2) if len(match.groups()) > 1 else ''
                    return (value, unit)
                except ValueError:
                    continue

        return None

    def _extract_traceability(self, text: str) -> Optional[str]:
        """Extract traceability information."""
        patterns = [
            r'Traceability[:\s]+([^\n]+)',
            r'Standards?\s+Traceable\s+to[:\s]+([^\n]+)',
            r'Reference\s+Standard[:\s]+([^\n]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_environmental_conditions(self, text: str) -> Dict[str, Any]:
        """Extract environmental conditions (temperature, humidity, etc.)."""
        conditions = {}

        # Temperature
        temp_match = re.search(r'Temperature[:\s]+([0-9.]+)\s*°?C', text, re.IGNORECASE)
        if temp_match:
            conditions['temperature'] = float(temp_match.group(1))
            conditions['temperature_unit'] = '°C'

        # Humidity
        humid_match = re.search(r'Humidity[:\s]+([0-9.]+)\s*%', text, re.IGNORECASE)
        if humid_match:
            conditions['humidity'] = float(humid_match.group(1))
            conditions['humidity_unit'] = '%'

        return conditions

    def _extract_field(self, text: str, pattern: str) -> Optional[str]:
        """Generic field extraction."""
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _validate_parsed_data(self, data: ParsedCertificateData) -> None:
        """Validate that required fields were successfully parsed."""
        required_fields = ['cert_number', 'calibration_date', 'due_date', 'calibration_lab']

        missing_fields = []
        for field in required_fields:
            if getattr(data, field) is None:
                missing_fields.append(field)

        if missing_fields:
            raise ValueError(
                f"Failed to parse required fields from certificate: {', '.join(missing_fields)}. "
                f"Please provide these fields manually."
            )

    def _create_certificate(
        self,
        data: ParsedCertificateData,
        cert_file: Path,
        equipment_id: int
    ) -> CalibrationCertificate:
        """Create CalibrationCertificate object from parsed data."""

        # Parse accreditation body
        try:
            accreditation = AccreditationBody[data.accreditation_body] if data.accreditation_body else AccreditationBody.OTHER
        except KeyError:
            accreditation = AccreditationBody.OTHER

        return CalibrationCertificate(
            cert_id=None,
            equipment_id=equipment_id,
            cert_number=data.cert_number,
            calibration_date=data.calibration_date,
            due_date=data.due_date,
            calibration_lab=data.calibration_lab,
            accreditation_body=accreditation,
            uncertainty=data.uncertainty or 0.0,
            traceability_chain=data.traceability_chain or "Not specified",
            certificate_file=cert_file,
            environmental_conditions=data.environmental_conditions,
            technician=data.technician,
            reviewer=data.reviewer,
        )
