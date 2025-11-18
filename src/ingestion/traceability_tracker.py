"""
Traceability Tracker for PV Test Automation (Session 10)

Implements data lineage tracking, audit trails, change history,
and ISO 17025 compliance traceability.
"""

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field, validator


class ActionType(str, Enum):
    """Types of trackable actions."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    READ = "read"
    EXPORT = "export"
    IMPORT = "import"
    APPROVE = "approve"
    REJECT = "reject"
    ARCHIVE = "archive"
    RESTORE = "restore"


class EntityType(str, Enum):
    """Types of trackable entities."""

    TEST_DATA = "test_data"
    REPORT = "report"
    DOCUMENT = "document"
    IMAGE = "image"
    BLOB = "blob"
    CONFIGURATION = "configuration"
    USER = "user"


class ComplianceStandard(str, Enum):
    """Compliance standards."""

    ISO_17025 = "ISO 17025"
    ISO_9001 = "ISO 9001"
    IEC_61215 = "IEC 61215"
    IEC_61730 = "IEC 61730"
    NABL = "NABL"
    ILAC = "ILAC"
    BIS = "BIS"


class AuditLog(BaseModel):
    """Comprehensive audit log entry."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Action details
    action: ActionType
    entity_type: EntityType
    entity_id: str
    entity_name: Optional[str] = None

    # User and session
    user_id: str
    user_name: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Change tracking
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    changes: Dict[str, Any] = Field(default_factory=dict)
    change_summary: Optional[str] = None

    # Compliance
    compliance_standards: List[ComplianceStandard] = Field(default_factory=list)
    traceability_chain: List[str] = Field(default_factory=list)
    requires_approval: bool = False
    approved_by: Optional[str] = None
    approval_timestamp: Optional[datetime] = None

    # Context
    reason: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

    # Data integrity
    checksum: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ActionType: lambda v: v.value,
            EntityType: lambda v: v.value,
            ComplianceStandard: lambda v: v.value,
        }

    def calculate_checksum(self) -> str:
        """Calculate checksum for audit log integrity."""
        data = {
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "entity_type": self.entity_type.value,
            "entity_id": self.entity_id,
            "user_id": self.user_id,
            "changes": self.changes,
        }
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def verify_checksum(self) -> bool:
        """Verify audit log checksum integrity."""
        if not self.checksum:
            return False
        return self.checksum == self.calculate_checksum()


class DataLineage(BaseModel):
    """Data lineage tracking for full traceability."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    entity_id: str
    entity_type: EntityType

    # Lineage chain
    source_entities: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of source entities (type, id, name)",
    )
    derived_entities: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of derived entities (type, id, name)",
    )

    # Processing information
    processing_steps: List[Dict[str, Any]] = Field(default_factory=list)
    transformations: List[Dict[str, Any]] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Quality and validation
    validation_status: str = "pending"  # pending, validated, failed
    quality_checks: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            EntityType: lambda v: v.value,
        }

    def add_source(self, entity_type: EntityType, entity_id: str, entity_name: str):
        """Add source entity to lineage."""
        self.source_entities.append(
            {
                "type": entity_type.value,
                "id": entity_id,
                "name": entity_name,
            }
        )
        self.updated_at = datetime.utcnow()

    def add_derived(self, entity_type: EntityType, entity_id: str, entity_name: str):
        """Add derived entity to lineage."""
        self.derived_entities.append(
            {
                "type": entity_type.value,
                "id": entity_id,
                "name": entity_name,
            }
        )
        self.updated_at = datetime.utcnow()

    def add_processing_step(
        self, step_name: str, description: str, metadata: Optional[Dict] = None
    ):
        """Add processing step to lineage."""
        self.processing_steps.append(
            {
                "step": step_name,
                "description": description,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
            }
        )
        self.updated_at = datetime.utcnow()


class ChangeHistory(BaseModel):
    """Change history for entity modifications."""

    entity_id: str
    entity_type: EntityType
    version: int
    changes: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            EntityType: lambda v: v.value,
        }


class ISO17025Traceability(BaseModel):
    """ISO 17025 specific traceability requirements."""

    test_id: str
    report_id: str

    # Equipment traceability
    equipment_used: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Equipment ID, calibration date, certificate number",
    )

    # Standard traceability
    measurement_standards: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Standard used, traceability to national/international standard",
    )

    # Environmental conditions
    environmental_conditions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Temperature, humidity, etc. during test",
    )

    # Personnel
    performed_by: str
    reviewed_by: Optional[str] = None
    approved_by: Optional[str] = None

    # Uncertainty
    measurement_uncertainty: Optional[Dict[str, float]] = None

    # Calibration chain
    calibration_chain: List[Dict[str, Any]] = Field(default_factory=list)

    # Documentation
    referenced_documents: List[str] = Field(default_factory=list)
    test_procedure: str
    test_method: str

    # Timestamps
    test_date: datetime
    review_date: Optional[datetime] = None
    approval_date: Optional[datetime] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class TraceabilityTracker:
    """
    Production-ready traceability tracker for PV test automation.

    Supports:
    - Comprehensive audit logging
    - Data lineage tracking
    - Change history management
    - ISO 17025 compliance
    - Checksum verification
    - Query and reporting capabilities
    """

    def __init__(self, storage_backend=None):
        """
        Initialize traceability tracker.

        Args:
            storage_backend: Optional storage backend (database, file, etc.)
        """
        self.storage_backend = storage_backend
        self._audit_logs: List[AuditLog] = []
        self._lineage_records: Dict[str, DataLineage] = {}
        self._change_history: Dict[str, List[ChangeHistory]] = {}
        self._iso17025_records: Dict[str, ISO17025Traceability] = {}

    # ========================================================================
    # Audit Logging
    # ========================================================================

    def log_action(
        self,
        action: ActionType,
        entity_type: EntityType,
        entity_id: str,
        user_id: str,
        old_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
        reason: Optional[str] = None,
        compliance_standards: Optional[List[ComplianceStandard]] = None,
        **kwargs,
    ) -> AuditLog:
        """
        Log an action for audit trail.

        Args:
            action: Type of action
            entity_type: Type of entity
            entity_id: Entity ID
            user_id: User performing action
            old_value: Previous value (for updates)
            new_value: New value
            reason: Reason for action
            compliance_standards: Applicable compliance standards
            **kwargs: Additional metadata

        Returns:
            AuditLog object
        """
        # Calculate changes
        changes = {}
        if old_value and new_value:
            changes = self._calculate_changes(old_value, new_value)

        # Create audit log
        audit_log = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            old_value=old_value,
            new_value=new_value,
            changes=changes,
            reason=reason,
            compliance_standards=compliance_standards or [],
            **kwargs,
        )

        # Calculate checksum for integrity
        audit_log.checksum = audit_log.calculate_checksum()

        # Store audit log
        self._audit_logs.append(audit_log)

        if self.storage_backend:
            self.storage_backend.save_audit_log(audit_log)

        return audit_log

    def _calculate_changes(
        self, old_value: Dict[str, Any], new_value: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate detailed changes between old and new values."""
        changes = {}

        all_keys = set(old_value.keys()) | set(new_value.keys())

        for key in all_keys:
            old = old_value.get(key)
            new = new_value.get(key)

            if old != new:
                changes[key] = {
                    "old": old,
                    "new": new,
                }

        return changes

    def get_audit_logs(
        self,
        entity_id: Optional[str] = None,
        entity_type: Optional[EntityType] = None,
        action: Optional[ActionType] = None,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AuditLog]:
        """
        Query audit logs with filters.

        Args:
            entity_id: Filter by entity ID
            entity_type: Filter by entity type
            action: Filter by action type
            user_id: Filter by user
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            List of matching AuditLog objects
        """
        results = self._audit_logs.copy()

        if entity_id:
            results = [log for log in results if log.entity_id == entity_id]

        if entity_type:
            results = [log for log in results if log.entity_type == entity_type]

        if action:
            results = [log for log in results if log.action == action]

        if user_id:
            results = [log for log in results if log.user_id == user_id]

        if start_date:
            results = [log for log in results if log.timestamp >= start_date]

        if end_date:
            results = [log for log in results if log.timestamp <= end_date]

        return sorted(results, key=lambda x: x.timestamp, reverse=True)

    # ========================================================================
    # Data Lineage
    # ========================================================================

    def create_lineage(
        self, entity_id: str, entity_type: EntityType, metadata: Optional[Dict] = None
    ) -> DataLineage:
        """
        Create data lineage record.

        Args:
            entity_id: Entity ID
            entity_type: Entity type
            metadata: Optional metadata

        Returns:
            DataLineage object
        """
        lineage = DataLineage(
            entity_id=entity_id,
            entity_type=entity_type,
            metadata=metadata or {},
        )

        self._lineage_records[entity_id] = lineage

        if self.storage_backend:
            self.storage_backend.save_lineage(lineage)

        return lineage

    def get_lineage(self, entity_id: str) -> Optional[DataLineage]:
        """Get data lineage for entity."""
        return self._lineage_records.get(entity_id)

    def trace_lineage_upstream(
        self, entity_id: str, max_depth: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Trace lineage upstream to source entities.

        Args:
            entity_id: Starting entity ID
            max_depth: Maximum depth to trace

        Returns:
            List of upstream entities with lineage info
        """
        result = []
        visited = set()
        queue = [(entity_id, 0)]

        while queue:
            current_id, depth = queue.pop(0)

            if depth >= max_depth or current_id in visited:
                continue

            visited.add(current_id)

            lineage = self.get_lineage(current_id)
            if lineage:
                result.append(
                    {
                        "entity_id": current_id,
                        "entity_type": lineage.entity_type.value,
                        "depth": depth,
                        "sources": lineage.source_entities,
                        "processing_steps": lineage.processing_steps,
                    }
                )

                # Add source entities to queue
                for source in lineage.source_entities:
                    queue.append((source["id"], depth + 1))

        return result

    def trace_lineage_downstream(
        self, entity_id: str, max_depth: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Trace lineage downstream to derived entities.

        Args:
            entity_id: Starting entity ID
            max_depth: Maximum depth to trace

        Returns:
            List of downstream entities with lineage info
        """
        result = []
        visited = set()
        queue = [(entity_id, 0)]

        while queue:
            current_id, depth = queue.pop(0)

            if depth >= max_depth or current_id in visited:
                continue

            visited.add(current_id)

            lineage = self.get_lineage(current_id)
            if lineage:
                result.append(
                    {
                        "entity_id": current_id,
                        "entity_type": lineage.entity_type.value,
                        "depth": depth,
                        "derived": lineage.derived_entities,
                        "transformations": lineage.transformations,
                    }
                )

                # Add derived entities to queue
                for derived in lineage.derived_entities:
                    queue.append((derived["id"], depth + 1))

        return result

    # ========================================================================
    # Change History
    # ========================================================================

    def record_change(
        self,
        entity_id: str,
        entity_type: EntityType,
        changes: Dict[str, Any],
        user_id: str,
    ) -> ChangeHistory:
        """
        Record change to entity.

        Args:
            entity_id: Entity ID
            entity_type: Entity type
            changes: Dictionary of changes
            user_id: User making change

        Returns:
            ChangeHistory object
        """
        # Get current version
        history_list = self._change_history.get(entity_id, [])
        version = len(history_list) + 1

        # Create change history
        change_history = ChangeHistory(
            entity_id=entity_id,
            entity_type=entity_type,
            version=version,
            changes=[
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "user_id": user_id,
                    "changes": changes,
                }
            ],
        )

        # Store
        if entity_id not in self._change_history:
            self._change_history[entity_id] = []

        self._change_history[entity_id].append(change_history)

        if self.storage_backend:
            self.storage_backend.save_change_history(change_history)

        return change_history

    def get_change_history(
        self, entity_id: str
    ) -> List[ChangeHistory]:
        """Get full change history for entity."""
        return self._change_history.get(entity_id, [])

    # ========================================================================
    # ISO 17025 Traceability
    # ========================================================================

    def create_iso17025_record(
        self,
        test_id: str,
        report_id: str,
        performed_by: str,
        test_date: datetime,
        test_procedure: str,
        test_method: str,
        **kwargs,
    ) -> ISO17025Traceability:
        """
        Create ISO 17025 traceability record.

        Args:
            test_id: Test ID
            report_id: Report ID
            performed_by: Personnel who performed test
            test_date: Date of test
            test_procedure: Test procedure reference
            test_method: Test method used
            **kwargs: Additional ISO 17025 fields

        Returns:
            ISO17025Traceability object
        """
        record = ISO17025Traceability(
            test_id=test_id,
            report_id=report_id,
            performed_by=performed_by,
            test_date=test_date,
            test_procedure=test_procedure,
            test_method=test_method,
            **kwargs,
        )

        self._iso17025_records[test_id] = record

        if self.storage_backend:
            self.storage_backend.save_iso17025_record(record)

        return record

    def get_iso17025_record(self, test_id: str) -> Optional[ISO17025Traceability]:
        """Get ISO 17025 traceability record."""
        return self._iso17025_records.get(test_id)

    def validate_iso17025_compliance(
        self, test_id: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate ISO 17025 compliance for test.

        Returns:
            Tuple of (is_compliant, list_of_issues)
        """
        record = self.get_iso17025_record(test_id)
        if not record:
            return False, ["No ISO 17025 record found"]

        issues = []

        # Check required fields
        if not record.equipment_used:
            issues.append("Equipment information missing")

        if not record.measurement_standards:
            issues.append("Measurement standards not documented")

        if not record.reviewed_by:
            issues.append("Test results not reviewed")

        if not record.approved_by:
            issues.append("Test results not approved")

        if not record.measurement_uncertainty:
            issues.append("Measurement uncertainty not documented")

        if not record.calibration_chain:
            issues.append("Calibration chain not documented")

        return len(issues) == 0, issues

    # ========================================================================
    # Reporting
    # ========================================================================

    def generate_audit_report(
        self,
        start_date: datetime,
        end_date: datetime,
        entity_type: Optional[EntityType] = None,
    ) -> Dict[str, Any]:
        """
        Generate audit report for date range.

        Args:
            start_date: Report start date
            end_date: Report end date
            entity_type: Optional entity type filter

        Returns:
            Dictionary with audit statistics and details
        """
        logs = self.get_audit_logs(
            entity_type=entity_type, start_date=start_date, end_date=end_date
        )

        # Calculate statistics
        action_counts = {}
        user_counts = {}
        entity_counts = {}

        for log in logs:
            action_counts[log.action.value] = action_counts.get(log.action.value, 0) + 1
            user_counts[log.user_id] = user_counts.get(log.user_id, 0) + 1
            entity_counts[log.entity_type.value] = (
                entity_counts.get(log.entity_type.value, 0) + 1
            )

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "total_actions": len(logs),
            "action_breakdown": action_counts,
            "user_activity": user_counts,
            "entity_breakdown": entity_counts,
            "logs": [log.dict() for log in logs],
        }

    def generate_lineage_report(self, entity_id: str) -> Dict[str, Any]:
        """
        Generate comprehensive lineage report.

        Args:
            entity_id: Entity ID

        Returns:
            Dictionary with complete lineage information
        """
        lineage = self.get_lineage(entity_id)
        if not lineage:
            return {"error": "No lineage found for entity"}

        upstream = self.trace_lineage_upstream(entity_id)
        downstream = self.trace_lineage_downstream(entity_id)

        return {
            "entity_id": entity_id,
            "entity_type": lineage.entity_type.value,
            "created_at": lineage.created_at.isoformat(),
            "updated_at": lineage.updated_at.isoformat(),
            "validation_status": lineage.validation_status,
            "source_entities": lineage.source_entities,
            "derived_entities": lineage.derived_entities,
            "processing_steps": lineage.processing_steps,
            "transformations": lineage.transformations,
            "upstream_lineage": upstream,
            "downstream_lineage": downstream,
        }

    def verify_audit_integrity(self) -> Tuple[bool, List[str]]:
        """
        Verify integrity of all audit logs.

        Returns:
            Tuple of (all_valid, list_of_invalid_log_ids)
        """
        invalid_logs = []

        for log in self._audit_logs:
            if not log.verify_checksum():
                invalid_logs.append(log.id)

        return len(invalid_logs) == 0, invalid_logs
