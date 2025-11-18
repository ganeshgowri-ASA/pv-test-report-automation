"""Database operations for calibration certificate management."""

import sqlite3
import json
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from .models import CalibrationCertificate, AccreditationBody, CertificateStatus


class CalibrationDatabase:
    """SQLite database for calibration certificate storage and retrieval."""

    def __init__(self, db_path: str = "calibration.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_database(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create certificates table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS calibration_certificates (
                    cert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id INTEGER NOT NULL,
                    cert_number TEXT NOT NULL UNIQUE,
                    calibration_date DATE NOT NULL,
                    due_date DATE NOT NULL,
                    calibration_lab TEXT NOT NULL,
                    accreditation_body TEXT NOT NULL,
                    uncertainty REAL NOT NULL,
                    traceability_chain TEXT NOT NULL,
                    certificate_file TEXT,
                    status TEXT NOT NULL,
                    uncertainty_budget TEXT,
                    calibration_points TEXT,
                    environmental_conditions TEXT,
                    calibration_procedure TEXT,
                    technician TEXT,
                    reviewer TEXT,
                    notes TEXT,
                    traceability_chain_obj TEXT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id)
                )
            ''')

            # Create equipment table (simplified)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS equipment (
                    equipment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT,
                    serial_number TEXT,
                    manufacturer TEXT,
                    model TEXT
                )
            ''')

            # Create calibration history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS calibration_history (
                    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id INTEGER NOT NULL,
                    cert_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    action_date TIMESTAMP NOT NULL,
                    performed_by TEXT,
                    notes TEXT,
                    FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id),
                    FOREIGN KEY (cert_id) REFERENCES calibration_certificates(cert_id)
                )
            ''')

            # Create indexes for better query performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_equipment_id
                ON calibration_certificates(equipment_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_due_date
                ON calibration_certificates(due_date)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_status
                ON calibration_certificates(status)
            ''')

            conn.commit()

    def add_certificate(self, certificate: CalibrationCertificate) -> int:
        """
        Add a new calibration certificate to the database.

        Args:
            certificate: CalibrationCertificate object to add

        Returns:
            The cert_id of the inserted certificate
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO calibration_certificates (
                    equipment_id, cert_number, calibration_date, due_date,
                    calibration_lab, accreditation_body, uncertainty,
                    traceability_chain, certificate_file, status,
                    uncertainty_budget, calibration_points, environmental_conditions,
                    calibration_procedure, technician, reviewer, notes,
                    traceability_chain_obj, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                certificate.equipment_id,
                certificate.cert_number,
                certificate.calibration_date.isoformat(),
                certificate.due_date.isoformat(),
                certificate.calibration_lab,
                certificate.accreditation_body.value,
                certificate.uncertainty,
                certificate.traceability_chain,
                str(certificate.certificate_file) if certificate.certificate_file else None,
                certificate.status.value,
                json.dumps(certificate.uncertainty_budget.to_dict()) if certificate.uncertainty_budget else None,
                json.dumps([p.to_dict() for p in certificate.calibration_points]),
                json.dumps(certificate.environmental_conditions),
                certificate.calibration_procedure,
                certificate.technician,
                certificate.reviewer,
                certificate.notes,
                json.dumps(certificate.traceability_chain_obj.to_dict()) if certificate.traceability_chain_obj else None,
                certificate.created_at.isoformat(),
                certificate.updated_at.isoformat(),
            ))

            conn.commit()
            cert_id = cursor.lastrowid

            # Add to history
            self._add_history_entry(
                conn, certificate.equipment_id, cert_id,
                "CERTIFICATE_ADDED", "system", "Certificate added to database"
            )

            return cert_id

    def update_certificate(self, certificate: CalibrationCertificate) -> bool:
        """
        Update an existing calibration certificate.

        Args:
            certificate: CalibrationCertificate object with updated data

        Returns:
            True if update was successful, False otherwise
        """
        if certificate.cert_id is None:
            raise ValueError("Certificate must have a cert_id to be updated")

        certificate.updated_at = datetime.now()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE calibration_certificates SET
                    equipment_id = ?, cert_number = ?, calibration_date = ?,
                    due_date = ?, calibration_lab = ?, accreditation_body = ?,
                    uncertainty = ?, traceability_chain = ?, certificate_file = ?,
                    status = ?, uncertainty_budget = ?, calibration_points = ?,
                    environmental_conditions = ?, calibration_procedure = ?,
                    technician = ?, reviewer = ?, notes = ?,
                    traceability_chain_obj = ?, updated_at = ?
                WHERE cert_id = ?
            ''', (
                certificate.equipment_id,
                certificate.cert_number,
                certificate.calibration_date.isoformat(),
                certificate.due_date.isoformat(),
                certificate.calibration_lab,
                certificate.accreditation_body.value,
                certificate.uncertainty,
                certificate.traceability_chain,
                str(certificate.certificate_file) if certificate.certificate_file else None,
                certificate.status.value,
                json.dumps(certificate.uncertainty_budget.to_dict()) if certificate.uncertainty_budget else None,
                json.dumps([p.to_dict() for p in certificate.calibration_points]),
                json.dumps(certificate.environmental_conditions),
                certificate.calibration_procedure,
                certificate.technician,
                certificate.reviewer,
                certificate.notes,
                json.dumps(certificate.traceability_chain_obj.to_dict()) if certificate.traceability_chain_obj else None,
                certificate.updated_at.isoformat(),
                certificate.cert_id,
            ))

            conn.commit()

            self._add_history_entry(
                conn, certificate.equipment_id, certificate.cert_id,
                "CERTIFICATE_UPDATED", "system", "Certificate updated"
            )

            return cursor.rowcount > 0

    def get_certificate(self, cert_id: int) -> Optional[CalibrationCertificate]:
        """
        Retrieve a certificate by ID.

        Args:
            cert_id: Certificate ID

        Returns:
            CalibrationCertificate object or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM calibration_certificates WHERE cert_id = ?',
                (cert_id,)
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_certificate(row)
            return None

    def get_certificates_by_equipment(self, equipment_id: int) -> List[CalibrationCertificate]:
        """
        Get all certificates for a specific equipment.

        Args:
            equipment_id: Equipment ID

        Returns:
            List of CalibrationCertificate objects
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM calibration_certificates WHERE equipment_id = ? ORDER BY calibration_date DESC',
                (equipment_id,)
            )
            rows = cursor.fetchall()

            return [self._row_to_certificate(row) for row in rows]

    def get_all_certificates(self) -> List[CalibrationCertificate]:
        """
        Get all certificates in the database.

        Returns:
            List of all CalibrationCertificate objects
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM calibration_certificates ORDER BY due_date ASC')
            rows = cursor.fetchall()

            return [self._row_to_certificate(row) for row in rows]

    def get_certificates_by_status(self, status: CertificateStatus) -> List[CalibrationCertificate]:
        """
        Get certificates filtered by status.

        Args:
            status: Certificate status to filter by

        Returns:
            List of CalibrationCertificate objects with the specified status
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM calibration_certificates WHERE status = ? ORDER BY due_date ASC',
                (status.value,)
            )
            rows = cursor.fetchall()

            return [self._row_to_certificate(row) for row in rows]

    def get_certificates_due_soon(self, days: int = 30) -> List[CalibrationCertificate]:
        """
        Get certificates due within specified days.

        Args:
            days: Number of days to look ahead

        Returns:
            List of CalibrationCertificate objects due within specified days
        """
        from datetime import timedelta
        cutoff_date = date.today() + timedelta(days=days)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT * FROM calibration_certificates
                   WHERE due_date <= ? AND due_date >= ?
                   ORDER BY due_date ASC''',
                (cutoff_date.isoformat(), date.today().isoformat())
            )
            rows = cursor.fetchall()

            return [self._row_to_certificate(row) for row in rows]

    def get_expired_certificates(self) -> List[CalibrationCertificate]:
        """
        Get all expired certificates.

        Returns:
            List of expired CalibrationCertificate objects
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM calibration_certificates WHERE due_date < ? ORDER BY due_date DESC',
                (date.today().isoformat(),)
            )
            rows = cursor.fetchall()

            return [self._row_to_certificate(row) for row in rows]

    def delete_certificate(self, cert_id: int) -> bool:
        """
        Delete a certificate from the database.

        Args:
            cert_id: Certificate ID to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get certificate info before deleting
            cert = self.get_certificate(cert_id)
            if cert:
                self._add_history_entry(
                    conn, cert.equipment_id, cert_id,
                    "CERTIFICATE_DELETED", "system", f"Certificate {cert.cert_number} deleted"
                )

            cursor.execute('DELETE FROM calibration_certificates WHERE cert_id = ?', (cert_id,))
            conn.commit()

            return cursor.rowcount > 0

    def get_calibration_history(self, equipment_id: int) -> List[Dict[str, Any]]:
        """
        Get calibration history for equipment.

        Args:
            equipment_id: Equipment ID

        Returns:
            List of history entries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT * FROM calibration_history
                   WHERE equipment_id = ?
                   ORDER BY action_date DESC''',
                (equipment_id,)
            )
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def _add_history_entry(
        self,
        conn: sqlite3.Connection,
        equipment_id: int,
        cert_id: int,
        action: str,
        performed_by: str,
        notes: str = None
    ) -> None:
        """Add entry to calibration history."""
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO calibration_history
            (equipment_id, cert_id, action, action_date, performed_by, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (equipment_id, cert_id, action, datetime.now().isoformat(), performed_by, notes))
        conn.commit()

    def _row_to_certificate(self, row: sqlite3.Row) -> CalibrationCertificate:
        """Convert database row to CalibrationCertificate object."""
        data = dict(row)

        # Parse JSON fields
        if data.get('uncertainty_budget'):
            data['uncertainty_budget'] = json.loads(data['uncertainty_budget'])
        if data.get('calibration_points'):
            data['calibration_points'] = json.loads(data['calibration_points'])
        if data.get('environmental_conditions'):
            data['environmental_conditions'] = json.loads(data['environmental_conditions'])
        if data.get('traceability_chain_obj'):
            data['traceability_chain_obj'] = json.loads(data['traceability_chain_obj'])

        return CalibrationCertificate.from_dict(data)

    def update_all_statuses(self) -> int:
        """
        Update status for all certificates based on current date.

        Returns:
            Number of certificates updated
        """
        certificates = self.get_all_certificates()
        updated_count = 0

        for cert in certificates:
            old_status = cert.status
            cert.update_status()

            if old_status != cert.status:
                self.update_certificate(cert)
                updated_count += 1

        return updated_count
