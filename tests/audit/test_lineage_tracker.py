"""
Tests for DataLineageTracker.
"""
import pytest
from uuid import uuid4

from src.audit.lineage_tracker import (
    DataLineageTracker,
    DataNode,
    DataNodeType,
    LineageRelationship,
    RelationshipType,
)


class TestDataLineageTracker:
    """Test suite for DataLineageTracker"""

    def test_create_single_node(self, lineage_tracker):
        """Test creating a single data node."""
        node = DataNode(
            node_type=DataNodeType.RAW_EQUIPMENT_OUTPUT,
            name="IV Curve Raw Data",
            created_by="user123",
            source_system="Keysight B1500A",
            data_value={"voltage": [0.1, 0.2], "current": [1.0, 2.0]}
        )

        node_id = lineage_tracker.create_node(node)

        assert node_id is not None
        assert node_id == node.id

        # Retrieve and verify
        retrieved = lineage_tracker.get_node(node_id)
        assert retrieved is not None
        assert retrieved.name == "IV Curve Raw Data"
        assert retrieved.source_system == "Keysight B1500A"

    def test_data_hash_computation(self, lineage_tracker):
        """Test automatic data hash computation."""
        data = {"temperature": 25.5, "humidity": 60}

        node = DataNode(
            node_type=DataNodeType.PARSED_DATA,
            name="Environmental Data",
            created_by="user123",
            data_value=data
        )

        node_id = lineage_tracker.create_node(node)
        retrieved = lineage_tracker.get_node(node_id)

        assert retrieved.data_hash is not None
        assert len(retrieved.data_hash) == 64  # SHA-256

    def test_create_relationship(self, lineage_tracker):
        """Test creating relationships between nodes."""
        # Create parent node
        parent = DataNode(
            node_type=DataNodeType.RAW_EQUIPMENT_OUTPUT,
            name="Raw Data",
            created_by="user123",
            data_value={"raw": [1, 2, 3]}
        )
        parent_id = lineage_tracker.create_node(parent)

        # Create child node
        child = DataNode(
            node_type=DataNodeType.PARSED_DATA,
            name="Parsed Data",
            created_by="user123",
            data_value={"parsed": [10, 20, 30]}
        )
        child_id = lineage_tracker.create_node(child)

        # Create relationship
        rel_id = lineage_tracker.create_relationship(
            parent_id=parent_id,
            child_id=child_id,
            relationship_type=RelationshipType.DERIVED_FROM,
            created_by="user123",
            transformation_function="parse_raw_data",
            description="Parsed raw equipment output"
        )

        assert rel_id is not None

    def test_trace_lineage_backward(self, lineage_tracker):
        """Test tracing lineage backward to source."""
        # Create a chain: Raw -> Parsed -> Calculated
        raw = DataNode(
            node_type=DataNodeType.RAW_EQUIPMENT_OUTPUT,
            name="Raw Data",
            created_by="user123",
            data_value={"raw": [1, 2, 3]}
        )
        raw_id = lineage_tracker.create_node(raw)

        parsed = DataNode(
            node_type=DataNodeType.PARSED_DATA,
            name="Parsed Data",
            created_by="user123",
            data_value={"parsed": [10, 20, 30]}
        )
        parsed_id = lineage_tracker.create_node(parsed)

        calculated = DataNode(
            node_type=DataNodeType.CALCULATED_VALUE,
            name="Efficiency",
            created_by="user123",
            data_value={"efficiency": 18.5}
        )
        calc_id = lineage_tracker.create_node(calculated)

        # Create relationships
        lineage_tracker.create_relationship(
            parent_id=raw_id,
            child_id=parsed_id,
            relationship_type=RelationshipType.DERIVED_FROM,
            created_by="user123"
        )

        lineage_tracker.create_relationship(
            parent_id=parsed_id,
            child_id=calc_id,
            relationship_type=RelationshipType.CALCULATED_FROM,
            created_by="user123",
            transformation_function="calculate_efficiency"
        )

        # Trace backward from calculated to source
        lineage = lineage_tracker.trace_lineage(calc_id, direction="backward")

        assert lineage["root_node"] == str(calc_id)
        assert len(lineage["nodes"]) == 3
        assert len(lineage["relationships"]) == 2

    def test_trace_lineage_forward(self, lineage_tracker):
        """Test tracing lineage forward to derived data."""
        # Create source node
        source = DataNode(
            node_type=DataNodeType.RAW_EQUIPMENT_OUTPUT,
            name="Source Data",
            created_by="user123",
            data_value={"data": [1, 2, 3]}
        )
        source_id = lineage_tracker.create_node(source)

        # Create multiple derived nodes
        derived_ids = []
        for i in range(3):
            derived = DataNode(
                node_type=DataNodeType.CALCULATED_VALUE,
                name=f"Derived {i}",
                created_by="user123",
                data_value={"value": i * 10}
            )
            derived_id = lineage_tracker.create_node(derived)
            derived_ids.append(derived_id)

            lineage_tracker.create_relationship(
                parent_id=source_id,
                child_id=derived_id,
                relationship_type=RelationshipType.CALCULATED_FROM,
                created_by="user123"
            )

        # Trace forward
        lineage = lineage_tracker.trace_lineage(source_id, direction="forward")

        assert lineage["root_node"] == str(source_id)
        assert len(lineage["nodes"]) == 4  # 1 source + 3 derived
        assert len(lineage["relationships"]) == 3

    def test_get_source_nodes(self, lineage_tracker):
        """Test getting ultimate source nodes."""
        # Create lineage chain
        source = DataNode(
            node_type=DataNodeType.RAW_EQUIPMENT_OUTPUT,
            name="Source",
            created_by="user123"
        )
        source_id = lineage_tracker.create_node(source)

        intermediate = DataNode(
            node_type=DataNodeType.PARSED_DATA,
            name="Intermediate",
            created_by="user123"
        )
        inter_id = lineage_tracker.create_node(intermediate)

        final = DataNode(
            node_type=DataNodeType.REPORT_SECTION,
            name="Final Report",
            created_by="user123"
        )
        final_id = lineage_tracker.create_node(final)

        lineage_tracker.create_relationship(
            parent_id=source_id,
            child_id=inter_id,
            relationship_type=RelationshipType.DERIVED_FROM,
            created_by="user123"
        )

        lineage_tracker.create_relationship(
            parent_id=inter_id,
            child_id=final_id,
            relationship_type=RelationshipType.DERIVED_FROM,
            created_by="user123"
        )

        # Get source nodes from final
        sources = lineage_tracker.get_source_nodes(final_id)

        assert len(sources) == 1
        assert sources[0].id == source_id
        assert sources[0].node_type == DataNodeType.RAW_EQUIPMENT_OUTPUT

    def test_impact_analysis(self, lineage_tracker):
        """Test impact analysis for node changes."""
        # Create a node with multiple dependents
        base = DataNode(
            node_type=DataNodeType.PARSED_DATA,
            name="Base Data",
            created_by="user123"
        )
        base_id = lineage_tracker.create_node(base)

        # Create dependent nodes
        dependent_ids = []
        for i in range(3):
            dep = DataNode(
                node_type=DataNodeType.CALCULATED_VALUE,
                name=f"Dependent {i}",
                created_by="user123"
            )
            dep_id = lineage_tracker.create_node(dep)
            dependent_ids.append(dep_id)

            lineage_tracker.create_relationship(
                parent_id=base_id,
                child_id=dep_id,
                relationship_type=RelationshipType.CALCULATED_FROM,
                created_by="user123"
            )

        # Analyze impact
        impact = lineage_tracker.get_impact_analysis(base_id)

        assert impact["source_node_id"] == str(base_id)
        assert impact["total_impacted"] == 3
        assert len(impact["impacted_nodes"]) == 3

    def test_node_versioning(self, lineage_tracker):
        """Test creating new versions of nodes."""
        # Create original node
        original = DataNode(
            node_type=DataNodeType.PARSED_DATA,
            name="Test Data",
            created_by="user123",
            data_value={"version": 1}
        )
        original_id = lineage_tracker.create_node(original)

        # Create new version
        new_version_id = lineage_tracker.create_node_version(
            original_node_id=original_id,
            updated_data={"version": 2},
            updated_by="user456"
        )

        # Verify versioning
        original_node = lineage_tracker.get_node(original_id)
        new_node = lineage_tracker.get_node(new_version_id)

        assert original_node.version == 1
        assert new_node.version == 2
        assert original_node.version_group_id == new_node.version_group_id
        assert original_node.is_latest_version is False
        assert new_node.is_latest_version is True
        assert new_node.updated_by == "user456"

    def test_entity_lineage(self, lineage_tracker):
        """Test getting all lineage for a specific entity."""
        entity_type = "Report"
        entity_id = "RPT-001"

        # Create multiple nodes for same entity
        for i in range(5):
            node = DataNode(
                node_type=DataNodeType.REPORT_SECTION,
                name=f"Section {i}",
                created_by="user123",
                entity_type=entity_type,
                entity_id=entity_id
            )
            lineage_tracker.create_node(node)

        # Create node for different entity
        other_node = DataNode(
            node_type=DataNodeType.REPORT_SECTION,
            name="Other Section",
            created_by="user123",
            entity_type=entity_type,
            entity_id="RPT-002"
        )
        lineage_tracker.create_node(other_node)

        # Get entity lineage
        entity_nodes = lineage_tracker.get_entity_lineage(entity_type, entity_id)

        assert len(entity_nodes) == 5
        for node in entity_nodes:
            assert node.entity_type == entity_type
            assert node.entity_id == entity_id

    def test_complex_lineage_graph(self, lineage_tracker):
        """Test complex lineage graph with multiple paths."""
        # Create a diamond-shaped graph:
        #       A (source)
        #      / \
        #     B   C
        #      \ /
        #       D (final)

        node_a = DataNode(
            node_type=DataNodeType.RAW_EQUIPMENT_OUTPUT,
            name="Node A",
            created_by="user123"
        )
        id_a = lineage_tracker.create_node(node_a)

        node_b = DataNode(
            node_type=DataNodeType.PARSED_DATA,
            name="Node B",
            created_by="user123"
        )
        id_b = lineage_tracker.create_node(node_b)

        node_c = DataNode(
            node_type=DataNodeType.PARSED_DATA,
            name="Node C",
            created_by="user123"
        )
        id_c = lineage_tracker.create_node(node_c)

        node_d = DataNode(
            node_type=DataNodeType.CALCULATED_VALUE,
            name="Node D",
            created_by="user123"
        )
        id_d = lineage_tracker.create_node(node_d)

        # Create relationships
        lineage_tracker.create_relationship(
            parent_id=id_a, child_id=id_b,
            relationship_type=RelationshipType.DERIVED_FROM,
            created_by="user123"
        )
        lineage_tracker.create_relationship(
            parent_id=id_a, child_id=id_c,
            relationship_type=RelationshipType.DERIVED_FROM,
            created_by="user123"
        )
        lineage_tracker.create_relationship(
            parent_id=id_b, child_id=id_d,
            relationship_type=RelationshipType.CALCULATED_FROM,
            created_by="user123"
        )
        lineage_tracker.create_relationship(
            parent_id=id_c, child_id=id_d,
            relationship_type=RelationshipType.CALCULATED_FROM,
            created_by="user123"
        )

        # Trace backward from D
        lineage = lineage_tracker.trace_lineage(id_d, direction="backward")

        assert len(lineage["nodes"]) == 4  # A, B, C, D
        assert len(lineage["relationships"]) == 4

        # Get source nodes
        sources = lineage_tracker.get_source_nodes(id_d)
        assert len(sources) == 1
        assert sources[0].id == id_a
