"""
Audit trail data models for PV test report automation.

Provides comprehensive audit logging for all system operations,
especially LLM-assisted decisions and data modifications.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AuditAction(str, Enum):
    """Audit action types."""

    # CRUD Operations
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

    # Workflow Actions
    SUBMIT = "SUBMIT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REVIEW = "REVIEW"

    # LLM Operations
    LLM_ANALYSIS = "LLM_ANALYSIS"
    LLM_SUMMARY = "LLM_SUMMARY"
    LLM_COMPLIANCE_CHECK = "LLM_COMPLIANCE_CHECK"
    LLM_ASSISTANT_QUERY = "LLM_ASSISTANT_QUERY"

    # Report Operations
    REPORT_GENERATE = "REPORT_GENERATE"
    REPORT_EXPORT = "REPORT_EXPORT"
    REPORT_IMPORT = "REPORT_IMPORT"

    # Authentication & Authorization
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    PERMISSION_GRANT = "PERMISSION_GRANT"
    PERMISSION_REVOKE = "PERMISSION_REVOKE"

    # System Operations
    CONFIG_CHANGE = "CONFIG_CHANGE"
    BACKUP = "BACKUP"
    RESTORE = "RESTORE"


class ResourceType(str, Enum):
    """Types of resources that can be audited."""

    TEST_REPORT = "TestReport"
    TEST_RESULT = "TestResult"
    SPECIMEN = "Specimen"
    USER = "User"
    REVIEWER_FEEDBACK = "ReviewerFeedback"
    CONFIGURATION = "Configuration"
    LLM_INTERACTION = "LLMInteraction"
    EXPORT = "Export"
    IMPORT = "Import"


class AuditStatus(str, Enum):
    """Audit event status."""

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PARTIAL = "PARTIAL"
    PENDING = "PENDING"


class LLMUsageMetrics(BaseModel):
    """Metrics for LLM API usage in audit trail."""

    model_name: str = Field(..., description="LLM model used")
    operation_type: str = Field(..., description="Type of LLM operation")
    input_tokens: int = Field(..., ge=0, description="Input tokens used")
    output_tokens: int = Field(..., ge=0, description="Output tokens used")
    total_tokens: int = Field(..., ge=0, description="Total tokens used")
    duration_seconds: float = Field(..., ge=0.0, description="Operation duration in seconds")
    estimated_cost: Optional[float] = Field(None, ge=0.0, description="Estimated cost in USD")
    prompt_hash: Optional[str] = Field(
        None, description="Hash of prompt for deduplication tracking"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "model_name": "claude-3-5-sonnet-20241022",
                "operation_type": "compliance_check",
                "input_tokens": 1500,
                "output_tokens": 800,
                "total_tokens": 2300,
                "duration_seconds": 3.5,
                "estimated_cost": 0.023,
            }
        }


class AuditEntry(BaseModel):
    """Single audit trail entry."""

    audit_id: str = Field(..., description="Unique audit entry identifier")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Event timestamp (UTC)"
    )
    action: AuditAction = Field(..., description="Action performed")
    resource_type: ResourceType = Field(..., description="Type of resource affected")
    resource_id: str = Field(..., description="ID of the resource")
    resource_name: Optional[str] = Field(None, description="Human-readable resource name")

    # User Information
    user_id: str = Field(..., description="User who performed the action")
    user_name: Optional[str] = Field(None, description="User's display name")
    user_role: Optional[str] = Field(None, description="User's role")

    # Request Metadata
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    request_id: Optional[str] = Field(None, description="Request ID for correlation")
    session_id: Optional[str] = Field(None, description="Session ID")

    # Event Details
    status: AuditStatus = Field(..., description="Event status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    error_code: Optional[str] = Field(None, description="Error code if failed")

    # Change Tracking
    changes: Optional[Dict[str, Any]] = Field(
        None,
        description="Changed fields with before/after values",
    )
    previous_values: Optional[Dict[str, Any]] = Field(
        None, description="Previous values before change"
    )
    new_values: Optional[Dict[str, Any]] = Field(None, description="New values after change")

    # LLM-Specific Information
    llm_usage: Optional[LLMUsageMetrics] = Field(
        None, description="LLM usage metrics if applicable"
    )
    llm_prompt: Optional[str] = Field(None, description="LLM prompt used")
    llm_response: Optional[str] = Field(None, description="LLM response received")
    llm_confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="LLM confidence score"
    )

    # Additional Context
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional contextual information"
    )
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")

    # Compliance & Regulatory
    regulatory_context: Optional[str] = Field(
        None, description="Regulatory context (ISO 17025, etc.)"
    )
    signature: Optional[str] = Field(None, description="Digital signature of entry")

    class Config:
        json_schema_extra = {
            "example": {
                "audit_id": "AUD-2024-001",
                "timestamp": "2024-01-15T10:30:00Z",
                "action": "LLM_COMPLIANCE_CHECK",
                "resource_type": "TestReport",
                "resource_id": "RPT-2024-001",
                "user_id": "USR-123",
                "status": "SUCCESS",
                "llm_usage": {
                    "model_name": "claude-3-5-sonnet-20241022",
                    "operation_type": "compliance_check",
                    "input_tokens": 1500,
                    "output_tokens": 800,
                    "total_tokens": 2300,
                    "duration_seconds": 3.5,
                },
            }
        }


class AuditTrail(BaseModel):
    """Complete audit trail for a resource."""

    resource_id: str = Field(..., description="Resource being tracked")
    resource_type: ResourceType = Field(..., description="Type of resource")
    entries: List[AuditEntry] = Field(
        default_factory=list, description="Chronological list of audit entries"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When audit trail was created"
    )
    last_modified: datetime = Field(
        default_factory=datetime.utcnow, description="Last modification timestamp"
    )
    modification_count: int = Field(default=0, description="Total number of modifications")
    llm_interaction_count: int = Field(
        default=0, description="Number of LLM interactions for this resource"
    )
    total_cost: Optional[float] = Field(
        None, ge=0.0, description="Total estimated cost of LLM operations"
    )

    def add_entry(self, entry: AuditEntry) -> None:
        """Add an audit entry and update trail metadata."""
        self.entries.append(entry)
        self.last_modified = datetime.utcnow()
        self.modification_count += 1

        # Track LLM interactions
        if entry.llm_usage:
            self.llm_interaction_count += 1
            if entry.llm_usage.estimated_cost:
                if self.total_cost is None:
                    self.total_cost = 0.0
                self.total_cost += entry.llm_usage.estimated_cost

    def get_entries_by_action(self, action: AuditAction) -> List[AuditEntry]:
        """Get all entries for a specific action."""
        return [e for e in self.entries if e.action == action]

    def get_llm_entries(self) -> List[AuditEntry]:
        """Get all LLM-related entries."""
        llm_actions = [
            AuditAction.LLM_ANALYSIS,
            AuditAction.LLM_SUMMARY,
            AuditAction.LLM_COMPLIANCE_CHECK,
            AuditAction.LLM_ASSISTANT_QUERY,
        ]
        return [e for e in self.entries if e.action in llm_actions]

    def get_recent_entries(self, limit: int = 10) -> List[AuditEntry]:
        """Get most recent audit entries."""
        return sorted(self.entries, key=lambda e: e.timestamp, reverse=True)[:limit]


class CostTracker(BaseModel):
    """Track LLM usage costs over time."""

    tracker_id: str = Field(..., description="Unique tracker identifier")
    period_start: datetime = Field(..., description="Start of tracking period")
    period_end: datetime = Field(..., description="End of tracking period")
    total_requests: int = Field(default=0, description="Total API requests")
    total_input_tokens: int = Field(default=0, description="Total input tokens")
    total_output_tokens: int = Field(default=0, description="Total output tokens")
    total_cost: float = Field(default=0.0, ge=0.0, description="Total cost in USD")
    cost_by_model: Dict[str, float] = Field(
        default_factory=dict, description="Cost breakdown by model"
    )
    cost_by_operation: Dict[str, float] = Field(
        default_factory=dict, description="Cost breakdown by operation type"
    )
    requests_by_user: Dict[str, int] = Field(
        default_factory=dict, description="Request count by user"
    )
    average_response_time: float = Field(
        default=0.0, ge=0.0, description="Average response time in seconds"
    )

    def add_usage(
        self,
        model: str,
        operation: str,
        user_id: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        duration: float,
    ) -> None:
        """Add a usage record to the tracker."""
        self.total_requests += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += cost

        # Update breakdowns
        self.cost_by_model[model] = self.cost_by_model.get(model, 0.0) + cost
        self.cost_by_operation[operation] = self.cost_by_operation.get(operation, 0.0) + cost
        self.requests_by_user[user_id] = self.requests_by_user.get(user_id, 0) + 1

        # Update average response time
        total_time = self.average_response_time * (self.total_requests - 1) + duration
        self.average_response_time = total_time / self.total_requests

    def get_summary(self) -> Dict[str, Any]:
        """Get cost tracking summary."""
        return {
            "period": {
                "start": self.period_start.isoformat(),
                "end": self.period_end.isoformat(),
            },
            "totals": {
                "requests": self.total_requests,
                "input_tokens": self.total_input_tokens,
                "output_tokens": self.total_output_tokens,
                "cost_usd": round(self.total_cost, 4),
            },
            "breakdown": {
                "by_model": self.cost_by_model,
                "by_operation": self.cost_by_operation,
            },
            "performance": {
                "average_response_time": round(self.average_response_time, 3),
            },
            "top_users": sorted(
                self.requests_by_user.items(), key=lambda x: x[1], reverse=True
            )[:5],
        }
