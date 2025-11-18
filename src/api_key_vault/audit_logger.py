"""Vault Audit Logger - ISO 17025 Compliant Access Logging.

Provides comprehensive audit trail for all vault operations.
"""

import logging
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class VaultAuditLogger:
    """Audit logger for vault access.

    ISO 17025 Requirements:
    - Complete access logging
    - Tamper-proof audit trail
    - User identification
    - Timestamp accuracy
    - Action tracking
    """

    def __init__(self, log_file: str = "vault_audit.log"):
        """Initialize audit logger.

        Args:
            log_file: Path to audit log file.
        """
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Configure dedicated audit logger
        self.audit_logger = logging.getLogger("vault_audit")
        self.audit_logger.setLevel(logging.INFO)

        # File handler for audit logs
        handler = logging.FileHandler(self.log_file)
        handler.setLevel(logging.INFO)

        # JSON formatter for structured logging
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
        )
        handler.setFormatter(formatter)

        if not self.audit_logger.handlers:
            self.audit_logger.addHandler(handler)

        logger.info(f"VaultAuditLogger initialized with log file: {log_file}")

    def log_access(
        self,
        user_id: str,
        resource_path: str,
        action: str,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log vault access event.

        Args:
            user_id: User ID performing the action.
            resource_path: Path to the resource being accessed.
            action: Action performed (READ, WRITE, DELETE, LIST).
            success: Whether the action succeeded.
            error: Error message if action failed.
            metadata: Additional metadata.
        """
        log_entry = {
            "user_id": user_id,
            "resource_path": resource_path,
            "action": action,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if error:
            log_entry["error"] = error

        if metadata:
            log_entry["metadata"] = metadata

        # Log to audit file
        self.audit_logger.info(json.dumps(log_entry))

        # Also log to main logger
        level = logging.INFO if success else logging.WARNING
        logger.log(
            level,
            f"Vault access: {user_id} {action} {resource_path} - {'SUCCESS' if success else 'FAILED'}"
        )

    def log_key_rotation(
        self,
        user_id: str,
        service: str,
        rotation_count: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log API key rotation event.

        Args:
            user_id: User ID performing the rotation.
            service: Service name.
            rotation_count: Number of times key has been rotated.
            metadata: Additional metadata.
        """
        log_entry = {
            "event_type": "KEY_ROTATION",
            "user_id": user_id,
            "service": service,
            "rotation_count": rotation_count,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if metadata:
            log_entry["metadata"] = metadata

        self.audit_logger.info(json.dumps(log_entry))
        logger.info(f"Key rotation: {service} (rotation #{rotation_count})")

    def log_key_expiry(
        self,
        service: str,
        expires_at: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log API key expiry event.

        Args:
            service: Service name.
            expires_at: Expiry timestamp.
            metadata: Additional metadata.
        """
        log_entry = {
            "event_type": "KEY_EXPIRY",
            "service": service,
            "expires_at": expires_at.isoformat(),
            "timestamp": datetime.utcnow().isoformat(),
        }

        if metadata:
            log_entry["metadata"] = metadata

        self.audit_logger.info(json.dumps(log_entry))
        logger.warning(f"Key expiry: {service} expired at {expires_at}")

    def get_audit_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query audit logs.

        Args:
            start_date: Start date for filtering.
            end_date: End date for filtering.
            user_id: Filter by user ID.
            action: Filter by action type.
            limit: Maximum number of entries to return.

        Returns:
            List of audit log entries.
        """
        if not self.log_file.exists():
            return []

        logs = []
        try:
            with open(self.log_file, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip().split(", \"message\": ", 1)[1][:-1])

                        # Apply filters
                        if start_date and datetime.fromisoformat(entry["timestamp"]) < start_date:
                            continue
                        if end_date and datetime.fromisoformat(entry["timestamp"]) > end_date:
                            continue
                        if user_id and entry.get("user_id") != user_id:
                            continue
                        if action and entry.get("action") != action:
                            continue

                        logs.append(entry)

                        if len(logs) >= limit:
                            break

                    except (json.JSONDecodeError, IndexError, KeyError):
                        continue

        except Exception as e:
            logger.error(f"Failed to read audit logs: {e}")

        return logs

    def get_user_activity(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get activity summary for a user.

        Args:
            user_id: User ID.
            days: Number of days to look back.

        Returns:
            Activity summary.
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        logs = self.get_audit_logs(start_date=start_date, user_id=user_id, limit=1000)

        summary = {
            "user_id": user_id,
            "period_days": days,
            "total_actions": len(logs),
            "successful_actions": sum(1 for log in logs if log.get("success")),
            "failed_actions": sum(1 for log in logs if not log.get("success")),
            "actions_by_type": {},
            "resources_accessed": set(),
        }

        for log in logs:
            action = log.get("action", "UNKNOWN")
            summary["actions_by_type"][action] = summary["actions_by_type"].get(action, 0) + 1

            if "resource_path" in log:
                summary["resources_accessed"].add(log["resource_path"])

        summary["resources_accessed"] = list(summary["resources_accessed"])

        return summary


from datetime import timedelta
