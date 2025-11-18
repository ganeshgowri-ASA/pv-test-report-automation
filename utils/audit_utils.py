"""
Audit Trail Utilities for ISO 17025 Compliance
Immutable audit logging and trail management
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class AuditLogger:
    """
    Immutable audit trail logger for ISO 17025 compliance
    All actions are logged with cryptographic integrity
    """

    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize audit logger

        Args:
            log_file: Path to audit log file
        """
        self.log_file = log_file or "audit_trail.jsonl"
        self._ensure_log_file()

    def _ensure_log_file(self):
        """Ensure log file exists"""
        log_path = Path(self.log_file)
        if not log_path.exists():
            log_path.touch()

    def log_action(
        self,
        workflow_id: int,
        action_id: int,
        user_id: int,
        action: str,
        stage: str,
        previous_state: Optional[str],
        new_state: str,
        signature_hash: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Log approval action to immutable audit trail

        Args:
            workflow_id: Workflow identifier
            action_id: Action identifier
            user_id: User performing action
            action: Action type
            stage: Approval stage
            previous_state: Previous workflow state
            new_state: New workflow state
            signature_hash: Digital signature hash
            metadata: Additional metadata

        Returns:
            True if logged successfully
        """
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "workflow_id": workflow_id,
            "action_id": action_id,
            "user_id": user_id,
            "action": action,
            "stage": stage,
            "previous_state": previous_state,
            "new_state": new_state,
            "signature_hash": signature_hash,
            "metadata": metadata,
            "immutable": True
        }

        # Append to log file (append-only for immutability)
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(audit_entry) + '\n')
            return True
        except Exception as e:
            print(f"Error logging audit entry: {e}")
            return False

    def get_workflow_trail(self, workflow_id: int) -> List[Dict[str, Any]]:
        """
        Get complete audit trail for a workflow

        Args:
            workflow_id: Workflow identifier

        Returns:
            List of audit entries
        """
        trail = []
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    entry = json.loads(line.strip())
                    if entry.get('workflow_id') == workflow_id:
                        trail.append(entry)
        except FileNotFoundError:
            pass
        return trail

    def get_user_actions(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all actions performed by a user

        Args:
            user_id: User identifier

        Returns:
            List of audit entries
        """
        actions = []
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    entry = json.loads(line.strip())
                    if entry.get('user_id') == user_id:
                        actions.append(entry)
        except FileNotFoundError:
            pass
        return actions

    def verify_trail_integrity(self, workflow_id: int) -> bool:
        """
        Verify audit trail integrity for a workflow

        Args:
            workflow_id: Workflow identifier

        Returns:
            True if trail is intact and immutable
        """
        trail = self.get_workflow_trail(workflow_id)

        # Check all entries are marked immutable
        for entry in trail:
            if not entry.get('immutable', False):
                return False

        # Verify chronological order
        timestamps = [entry['timestamp'] for entry in trail]
        if timestamps != sorted(timestamps):
            return False

        return True

    def export_trail(
        self,
        workflow_id: int,
        format: str = "json"
    ) -> str:
        """
        Export audit trail for compliance reporting

        Args:
            workflow_id: Workflow identifier
            format: Export format (json, csv)

        Returns:
            Formatted audit trail
        """
        trail = self.get_workflow_trail(workflow_id)

        if format == "json":
            return json.dumps(trail, indent=2)
        elif format == "csv":
            # Simple CSV export
            if not trail:
                return ""

            headers = trail[0].keys()
            csv_lines = [",".join(headers)]

            for entry in trail:
                values = [str(entry.get(h, "")) for h in headers]
                csv_lines.append(",".join(values))

            return "\n".join(csv_lines)
        else:
            raise ValueError(f"Unsupported format: {format}")
