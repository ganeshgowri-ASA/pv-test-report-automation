"""
ISO 17025 Personnel Competence Tracking
Ensures only qualified personnel perform tests
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


class CompetenceLevel(Enum):
    """Personnel competence levels"""
    TRAINEE = "trainee"
    QUALIFIED = "qualified"
    LEAD = "lead"
    SUPERVISOR = "supervisor"


@dataclass
class PersonnelQualification:
    """Personnel qualification record"""
    technician_id: str
    name: str
    protocol_code: str  # e.g., "IEC 62759"
    competence_level: CompetenceLevel
    certification_date: datetime
    expiry_date: datetime
    authorized_activities: List[str]
    training_records: List[str]
    authorized: bool


class CompetenceManager:
    """
    Manage personnel competence per ISO 17025

    Requirements:
    - Document personnel competence
    - Track training and authorization
    - Verify qualifications before test
    - Maintain competence records
    """

    def __init__(self):
        self.qualifications: Dict[str, List[PersonnelQualification]] = {}

    def register_qualification(self, qualification: PersonnelQualification):
        """Register personnel qualification"""
        if qualification.technician_id not in self.qualifications:
            self.qualifications[qualification.technician_id] = []

        self.qualifications[qualification.technician_id].append(qualification)

    def verify_competence(
        self,
        technician_id: str,
        protocol_code: str,
        activity: str
    ) -> bool:
        """
        Verify technician is competent for specific activity

        Args:
            technician_id: Technician identifier
            protocol_code: Protocol code (e.g., "IEC 62759")
            activity: Activity to perform

        Returns:
            bool: True if qualified
        """
        if technician_id not in self.qualifications:
            return False

        for qual in self.qualifications[technician_id]:
            # Check protocol match
            if qual.protocol_code != protocol_code:
                continue

            # Check authorization
            if not qual.authorized:
                continue

            # Check expiry
            if datetime.now() > qual.expiry_date:
                continue

            # Check activity authorization
            if activity in qual.authorized_activities:
                return True

        return False

    def get_qualified_technicians(
        self,
        protocol_code: str,
        min_level: CompetenceLevel = CompetenceLevel.QUALIFIED
    ) -> List[str]:
        """
        Get list of qualified technicians for a protocol

        Args:
            protocol_code: Protocol code
            min_level: Minimum competence level required

        Returns:
            List: Technician IDs
        """
        qualified = []

        for tech_id, quals in self.qualifications.items():
            for qual in quals:
                if (qual.protocol_code == protocol_code and
                    qual.authorized and
                    datetime.now() < qual.expiry_date):

                    # Check competence level
                    level_order = [
                        CompetenceLevel.TRAINEE,
                        CompetenceLevel.QUALIFIED,
                        CompetenceLevel.LEAD,
                        CompetenceLevel.SUPERVISOR
                    ]

                    if level_order.index(qual.competence_level) >= level_order.index(min_level):
                        qualified.append(tech_id)
                        break

        return qualified

    def schedule_requalification(
        self,
        technician_id: str,
        protocol_code: str,
        days_before_expiry: int = 30
    ) -> Optional[datetime]:
        """
        Get requalification due date

        Args:
            technician_id: Technician identifier
            protocol_code: Protocol code
            days_before_expiry: Days before expiry to schedule

        Returns:
            datetime: Requalification date or None
        """
        if technician_id not in self.qualifications:
            return None

        for qual in self.qualifications[technician_id]:
            if qual.protocol_code == protocol_code:
                return qual.expiry_date - timedelta(days=days_before_expiry)

        return None
