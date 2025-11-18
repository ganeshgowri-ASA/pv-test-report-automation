"""
Data Lineage Tracker
Track data transformations from raw equipment output to final report.

Implements complete traceability per ISO 17025 requirements:
- Raw equipment data → Parsed data → Calculated results → Report sections
- Parent-child relationships with version control
- Bidirectional tracing (forward and backward)
"""

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import (
    Column, String, DateTime, Integer, Text, JSON, ForeignKey,
    Index, create_engine, select, and_, or_
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, Session, relationship
from sqlalchemy.pool import NullPool

Base = declarative_base()


class DataNodeType(str, Enum):
    """Types of data nodes in the lineage graph"""

    # Source data
    RAW_EQUIPMENT_OUTPUT = "RAW_EQUIPMENT_OUTPUT"  # Direct from test equipment
    MANUAL_ENTRY = "MANUAL_ENTRY"  # Manually entered data
    IMPORTED_FILE = "IMPORTED_FILE"  # Imported CSV, Excel, etc.

    # Processed data
    PARSED_DATA = "PARSED_DATA"  # After parsing/validation
    CALCULATED_VALUE = "CALCULATED_VALUE"  # Computed from other values
    AGGREGATED_DATA = "AGGREGATED_DATA"  # Summary statistics
    TRANSFORMED_DATA = "TRANSFORMED_DATA"  # Unit conversions, etc.

    # Report elements
    REPORT_SECTION = "REPORT_SECTION"  # Report section/table
    REPORT_FIGURE = "REPORT_FIGURE"  # Charts, graphs
    REPORT_SUMMARY = "REPORT_SUMMARY"  # Summary values
    REPORT_CONCLUSION = "REPORT_CONCLUSION"  # Conclusions/recommendations

    # Intermediate
    VALIDATION_RESULT = "VALIDATION_RESULT"  # Validation checks
    QC_CHECK = "QC_CHECK"  # Quality control checks


class RelationshipType(str, Enum):
    """Types of relationships between data nodes"""

    DERIVED_FROM = "DERIVED_FROM"  # Child derived from parent
    CALCULATED_FROM = "CALCULATED_FROM"  # Calculation relationship
    AGGREGATED_FROM = "AGGREGATED_FROM"  # Aggregation relationship
    TRANSFORMED_FROM = "TRANSFORMED_FROM"  # Transformation relationship
    VALIDATED_BY = "VALIDATED_BY"  # Validation relationship
    COMPOSED_OF = "COMPOSED_OF"  # Composition relationship
    REFERENCED_BY = "REFERENCED_BY"  # Reference relationship


class DataNodeModel(Base):
    """Data node in the lineage graph"""
    __tablename__ = "lineage_nodes"

    # Identification
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    node_type = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Versioning
    version = Column(Integer, nullable=False, default=1)
    version_group_id = Column(PG_UUID(as_uuid=True), index=True)  # Links versions together
    is_latest_version = Column(String(10), default="true", index=True)

    # Temporal
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_by = Column(String(100), nullable=False)
    updated_at = Column(DateTime(timezone=True))
    updated_by = Column(String(100))

    # Data content
    data_value = Column(JSON)  # The actual data
    data_schema = Column(JSON)  # Schema/structure of the data
    data_hash = Column(String(64), index=True)  # SHA-256 of data for integrity

    # Source information
    source_system = Column(String(100))  # e.g., "Keysight B1500A"
    source_file = Column(String(500))  # Original file path
    source_location = Column(String(500))  # Location in source (line number, cell, etc.)

    # Quality metadata
    quality_score = Column(Integer)  # 0-100
    validation_status = Column(String(20))  # VALID, INVALID, PENDING
    validation_errors = Column(JSON)

    # Business context
    entity_type = Column(String(100))  # e.g., "Report", "Test"
    entity_id = Column(String(100), index=True)  # ID of related entity

    # Additional metadata
    metadata = Column(JSON)

    # Indexes
    __table_args__ = (
        Index('idx_lineage_node_entity', 'entity_type', 'entity_id'),
        Index('idx_lineage_node_version', 'version_group_id', 'version'),
        Index('idx_lineage_node_type_created', 'node_type', 'created_at'),
    )


class LineageRelationshipModel(Base):
    """Relationship between data nodes"""
    __tablename__ = "lineage_relationships"

    # Identification
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    relationship_type = Column(String(50), nullable=False, index=True)

    # Parent-child relationship
    parent_id = Column(PG_UUID(as_uuid=True), ForeignKey('lineage_nodes.id'), nullable=False, index=True)
    child_id = Column(PG_UUID(as_uuid=True), ForeignKey('lineage_nodes.id'), nullable=False, index=True)

    # Transformation details
    transformation_type = Column(String(100))  # Type of transformation
    transformation_function = Column(String(255))  # Function/formula used
    transformation_params = Column(JSON)  # Parameters used

    # Temporal
    created_at = Column(DateTime(timezone=True), nullable=False)
    created_by = Column(String(100), nullable=False)

    # Additional metadata
    description = Column(Text)
    metadata = Column(JSON)

    # Indexes
    __table_args__ = (
        Index('idx_lineage_rel_parent', 'parent_id', 'relationship_type'),
        Index('idx_lineage_rel_child', 'child_id', 'relationship_type'),
        Index('idx_lineage_rel_both', 'parent_id', 'child_id'),
    )


class DataNode(BaseModel):
    """Pydantic model for data node"""

    model_config = ConfigDict(use_enum_values=True)

    id: UUID = Field(default_factory=uuid4)
    node_type: DataNodeType
    name: str
    description: Optional[str] = None

    version: int = 1
    version_group_id: Optional[UUID] = None
    is_latest_version: bool = True

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

    data_value: Optional[Dict[str, Any]] = None
    data_schema: Optional[Dict[str, Any]] = None
    data_hash: Optional[str] = None

    source_system: Optional[str] = None
    source_file: Optional[str] = None
    source_location: Optional[str] = None

    quality_score: Optional[int] = Field(None, ge=0, le=100)
    validation_status: Optional[str] = None
    validation_errors: Optional[List[str]] = None

    entity_type: Optional[str] = None
    entity_id: Optional[str] = None

    metadata: Optional[Dict[str, Any]] = None


class LineageRelationship(BaseModel):
    """Pydantic model for lineage relationship"""

    model_config = ConfigDict(use_enum_values=True)

    id: UUID = Field(default_factory=uuid4)
    relationship_type: RelationshipType

    parent_id: UUID
    child_id: UUID

    transformation_type: Optional[str] = None
    transformation_function: Optional[str] = None
    transformation_params: Optional[Dict[str, Any]] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str

    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DataLineageTracker:
    """
    Track complete data lineage from source to report.

    Provides:
    - Complete traceability per ISO 17025
    - Version control for all data transformations
    - Bidirectional lineage (forward and backward tracking)
    - Impact analysis (what's affected by a change)
    - Audit trail integration

    Example:
        tracker = DataLineageTracker(db_url="postgresql://...")

        # Create source node
        raw_data = DataNode(
            node_type=DataNodeType.RAW_EQUIPMENT_OUTPUT,
            name="IV Curve Raw Data",
            created_by="user123",
            source_system="Keysight B1500A",
            data_value={"voltage": [...], "current": [...]}
        )
        raw_id = tracker.create_node(raw_data)

        # Create derived node
        parsed_data = DataNode(
            node_type=DataNodeType.PARSED_DATA,
            name="IV Curve Parsed",
            created_by="user123",
            data_value={"voc": 0.65, "isc": 9.2, ...}
        )
        parsed_id = tracker.create_node(parsed_data)

        # Link them
        tracker.create_relationship(
            parent_id=raw_id,
            child_id=parsed_id,
            relationship_type=RelationshipType.DERIVED_FROM,
            created_by="user123"
        )

        # Trace back from report to source
        lineage = tracker.trace_lineage(parsed_id, direction="backward")
    """

    def __init__(self, db_url: str, auto_create_tables: bool = True):
        """Initialize lineage tracker"""
        self.engine = create_engine(
            db_url,
            poolclass=NullPool,
            echo=False
        )

        if auto_create_tables:
            Base.metadata.create_all(self.engine)

    def _compute_data_hash(self, data: Any) -> str:
        """Compute SHA-256 hash of data for integrity checking"""
        import hashlib
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def create_node(self, node: DataNode) -> UUID:
        """
        Create a new data node in the lineage graph.

        Args:
            node: DataNode to create

        Returns:
            UUID of created node
        """
        with Session(self.engine) as session:
            # Compute data hash if data provided
            if node.data_value is not None and node.data_hash is None:
                node.data_hash = self._compute_data_hash(node.data_value)

            # Set version group ID if not set
            if node.version_group_id is None:
                node.version_group_id = node.id

            db_node = DataNodeModel(
                id=node.id,
                node_type=node.node_type,
                name=node.name,
                description=node.description,
                version=node.version,
                version_group_id=node.version_group_id,
                is_latest_version="true" if node.is_latest_version else "false",
                created_at=node.created_at,
                created_by=node.created_by,
                updated_at=node.updated_at,
                updated_by=node.updated_by,
                data_value=node.data_value,
                data_schema=node.data_schema,
                data_hash=node.data_hash,
                source_system=node.source_system,
                source_file=node.source_file,
                source_location=node.source_location,
                quality_score=node.quality_score,
                validation_status=node.validation_status,
                validation_errors=node.validation_errors,
                entity_type=node.entity_type,
                entity_id=node.entity_id,
                metadata=node.metadata,
            )

            session.add(db_node)
            session.commit()

            return node.id

    def create_node_version(
        self,
        original_node_id: UUID,
        updated_data: Dict[str, Any],
        updated_by: str
    ) -> UUID:
        """
        Create a new version of an existing node.

        Args:
            original_node_id: ID of the node to version
            updated_data: Updated data
            updated_by: User making the update

        Returns:
            UUID of new version
        """
        with Session(self.engine) as session:
            # Get original node
            stmt = select(DataNodeModel).where(DataNodeModel.id == original_node_id)
            original = session.execute(stmt).scalar_one()

            # Mark original as not latest
            original.is_latest_version = "false"

            # Create new version
            new_node = DataNode(
                node_type=DataNodeType(original.node_type),
                name=original.name,
                description=original.description,
                version=original.version + 1,
                version_group_id=original.version_group_id,
                is_latest_version=True,
                created_by=original.created_by,
                created_at=original.created_at,
                updated_by=updated_by,
                updated_at=datetime.now(timezone.utc),
                data_value=updated_data,
                data_schema=original.data_schema,
                source_system=original.source_system,
                source_file=original.source_file,
                source_location=original.source_location,
                entity_type=original.entity_type,
                entity_id=original.entity_id,
                metadata=original.metadata,
            )

            session.commit()

        return self.create_node(new_node)

    def create_relationship(
        self,
        parent_id: UUID,
        child_id: UUID,
        relationship_type: RelationshipType,
        created_by: str,
        transformation_type: Optional[str] = None,
        transformation_function: Optional[str] = None,
        transformation_params: Optional[Dict] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> UUID:
        """
        Create a relationship between two nodes.

        Args:
            parent_id: ID of parent (source) node
            child_id: ID of child (derived) node
            relationship_type: Type of relationship
            created_by: User creating the relationship
            transformation_type: Type of transformation applied
            transformation_function: Function/formula used
            transformation_params: Parameters for transformation
            description: Human-readable description
            metadata: Additional metadata

        Returns:
            UUID of created relationship
        """
        relationship = LineageRelationship(
            relationship_type=relationship_type,
            parent_id=parent_id,
            child_id=child_id,
            transformation_type=transformation_type,
            transformation_function=transformation_function,
            transformation_params=transformation_params,
            created_by=created_by,
            description=description,
            metadata=metadata,
        )

        with Session(self.engine) as session:
            db_rel = LineageRelationshipModel(
                id=relationship.id,
                relationship_type=relationship.relationship_type,
                parent_id=relationship.parent_id,
                child_id=relationship.child_id,
                transformation_type=relationship.transformation_type,
                transformation_function=relationship.transformation_function,
                transformation_params=relationship.transformation_params,
                created_at=relationship.created_at,
                created_by=relationship.created_by,
                description=relationship.description,
                metadata=relationship.metadata,
            )

            session.add(db_rel)
            session.commit()

            return relationship.id

    def get_node(self, node_id: UUID) -> Optional[DataNode]:
        """Get a data node by ID"""
        with Session(self.engine) as session:
            stmt = select(DataNodeModel).where(DataNodeModel.id == node_id)
            db_node = session.execute(stmt).scalar_one_or_none()

            if not db_node:
                return None

            return self._convert_db_node(db_node)

    def _convert_db_node(self, db_node: DataNodeModel) -> DataNode:
        """Convert database model to Pydantic model"""
        return DataNode(
            id=db_node.id,
            node_type=DataNodeType(db_node.node_type),
            name=db_node.name,
            description=db_node.description,
            version=db_node.version,
            version_group_id=db_node.version_group_id,
            is_latest_version=db_node.is_latest_version == "true",
            created_at=db_node.created_at,
            created_by=db_node.created_by,
            updated_at=db_node.updated_at,
            updated_by=db_node.updated_by,
            data_value=db_node.data_value,
            data_schema=db_node.data_schema,
            data_hash=db_node.data_hash,
            source_system=db_node.source_system,
            source_file=db_node.source_file,
            source_location=db_node.source_location,
            quality_score=db_node.quality_score,
            validation_status=db_node.validation_status,
            validation_errors=db_node.validation_errors,
            entity_type=db_node.entity_type,
            entity_id=db_node.entity_id,
            metadata=db_node.metadata,
        )

    def trace_lineage(
        self,
        node_id: UUID,
        direction: str = "backward",
        max_depth: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Trace complete lineage for a node.

        Args:
            node_id: Starting node ID
            direction: "backward" (to sources) or "forward" (to derived)
            max_depth: Maximum depth to trace (None = unlimited)

        Returns:
            Dictionary with lineage graph structure
        """
        visited: Set[UUID] = set()
        lineage_graph = {
            "root_node": None,
            "nodes": {},
            "relationships": []
        }

        def trace_recursive(current_id: UUID, depth: int = 0):
            if max_depth is not None and depth > max_depth:
                return
            if current_id in visited:
                return

            visited.add(current_id)

            # Get current node
            node = self.get_node(current_id)
            if not node:
                return

            lineage_graph["nodes"][str(current_id)] = node.model_dump(mode="json")

            if depth == 0:
                lineage_graph["root_node"] = str(current_id)

            # Get relationships
            with Session(self.engine) as session:
                if direction == "backward":
                    # Get parents (sources)
                    stmt = select(LineageRelationshipModel).where(
                        LineageRelationshipModel.child_id == current_id
                    )
                else:
                    # Get children (derived)
                    stmt = select(LineageRelationshipModel).where(
                        LineageRelationshipModel.parent_id == current_id
                    )

                relationships = session.execute(stmt).scalars().all()

                for rel in relationships:
                    lineage_graph["relationships"].append({
                        "id": str(rel.id),
                        "type": rel.relationship_type,
                        "parent_id": str(rel.parent_id),
                        "child_id": str(rel.child_id),
                        "transformation": rel.transformation_function,
                    })

                    # Recurse
                    next_id = rel.parent_id if direction == "backward" else rel.child_id
                    trace_recursive(next_id, depth + 1)

        trace_recursive(node_id)
        return lineage_graph

    def get_source_nodes(self, node_id: UUID) -> List[DataNode]:
        """
        Get all ultimate source nodes for a given node.

        Returns nodes with no parents (original sources).
        """
        lineage = self.trace_lineage(node_id, direction="backward")
        sources = []

        with Session(self.engine) as session:
            for node_id_str, node_data in lineage["nodes"].items():
                # Check if this node has no parents
                node_uuid = UUID(node_id_str)
                stmt = select(LineageRelationshipModel).where(
                    LineageRelationshipModel.child_id == node_uuid
                )
                has_parents = session.execute(stmt).first() is not None

                if not has_parents:
                    sources.append(self.get_node(node_uuid))

        return [s for s in sources if s is not None]

    def get_impact_analysis(self, node_id: UUID) -> Dict[str, Any]:
        """
        Analyze what would be affected if this node changes.

        Returns all downstream nodes that depend on this node.
        """
        forward_lineage = self.trace_lineage(node_id, direction="forward")

        impacted_nodes = []
        for node_id_str, node_data in forward_lineage["nodes"].items():
            if node_id_str != str(node_id):  # Exclude the root node itself
                impacted_nodes.append(node_data)

        return {
            "source_node_id": str(node_id),
            "total_impacted": len(impacted_nodes),
            "impacted_nodes": impacted_nodes,
            "relationships": forward_lineage["relationships"]
        }

    def get_entity_lineage(self, entity_type: str, entity_id: str) -> List[DataNode]:
        """
        Get all lineage nodes for a specific entity (e.g., all nodes for a report).

        Args:
            entity_type: Type of entity (e.g., "Report")
            entity_id: ID of entity

        Returns:
            List of all nodes associated with the entity
        """
        with Session(self.engine) as session:
            stmt = select(DataNodeModel).where(
                and_(
                    DataNodeModel.entity_type == entity_type,
                    DataNodeModel.entity_id == entity_id
                )
            ).order_by(DataNodeModel.created_at)

            db_nodes = session.execute(stmt).scalars().all()
            return [self._convert_db_node(node) for node in db_nodes]
