"""Base model classes for PV test automation system.

This module provides foundational Pydantic models with common fields
and validation logic for all test entities.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, ConfigDict


class BaseModel(PydanticBaseModel):
    """Extended Pydantic BaseModel with common fields for all entities.

    Provides standard fields for tracking creation, modification, and versioning
    of test data across the system.

    Attributes:
        id: Unique identifier for the entity
        created_at: Timestamp when the entity was created
        updated_at: Timestamp when the entity was last updated
        version: Schema version for data migration tracking
        metadata: Additional metadata as key-value pairs
    """

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "created_at": "2025-11-18T10:00:00Z",
                    "version": "1.0"
                }
            ]
        }
    )

    id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for the entity"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the entity was created"
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the entity was last updated"
    )
    version: str = Field(
        default="1.0",
        description="Schema version for data migration tracking"
    )

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current time."""
        self.updated_at = datetime.utcnow()
