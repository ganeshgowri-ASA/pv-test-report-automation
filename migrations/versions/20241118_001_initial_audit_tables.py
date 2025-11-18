"""Initial audit trail and lineage tables with PostgreSQL triggers

Revision ID: 001_initial_audit
Revises:
Create Date: 2024-11-18

This migration creates:
1. Audit events table with hash chaining
2. Data lineage tables (nodes and relationships)
3. PostgreSQL triggers for immutability enforcement
4. Indexes for performance
5. Functions for audit trail protection
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_audit'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create audit trail and lineage tables with triggers"""

    # ========================================
    # 1. AUDIT EVENTS TABLE
    # ========================================
    op.create_table(
        'audit_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.String(length=100), nullable=True),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('user_name', sa.String(length=255), nullable=False),
        sa.Column('user_role', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('old_values', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('new_values', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('previous_hash', sa.String(length=64), nullable=True),
        sa.Column('event_hash', sa.String(length=64), nullable=False),
        sa.Column('retention_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_anonymized', sa.String(length=10), nullable=True, server_default='false'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sequence_number'),
        sa.UniqueConstraint('event_hash')
    )

    # Create indexes for audit_events
    op.create_index('idx_audit_timestamp_user', 'audit_events', ['timestamp', 'user_id'])
    op.create_index('idx_audit_entity', 'audit_events', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_event_type', 'audit_events', ['event_type', 'timestamp'])
    op.create_index('idx_audit_session', 'audit_events', ['session_id', 'timestamp'])
    op.create_index(op.f('ix_audit_events_entity_id'), 'audit_events', ['entity_id'])
    op.create_index(op.f('ix_audit_events_event_type'), 'audit_events', ['event_type'])
    op.create_index(op.f('ix_audit_events_sequence_number'), 'audit_events', ['sequence_number'])
    op.create_index(op.f('ix_audit_events_timestamp'), 'audit_events', ['timestamp'])
    op.create_index(op.f('ix_audit_events_user_id'), 'audit_events', ['user_id'])
    op.create_index(op.f('ix_audit_events_event_hash'), 'audit_events', ['event_hash'])

    # ========================================
    # 2. LINEAGE NODES TABLE
    # ========================================
    op.create_table(
        'lineage_nodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('node_type', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('version_group_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_latest_version', sa.String(length=10), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', sa.String(length=100), nullable=True),
        sa.Column('data_value', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('data_schema', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('data_hash', sa.String(length=64), nullable=True),
        sa.Column('source_system', sa.String(length=100), nullable=True),
        sa.Column('source_file', sa.String(length=500), nullable=True),
        sa.Column('source_location', sa.String(length=500), nullable=True),
        sa.Column('quality_score', sa.Integer(), nullable=True),
        sa.Column('validation_status', sa.String(length=20), nullable=True),
        sa.Column('validation_errors', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('entity_type', sa.String(length=100), nullable=True),
        sa.Column('entity_id', sa.String(length=100), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for lineage_nodes
    op.create_index('idx_lineage_node_entity', 'lineage_nodes', ['entity_type', 'entity_id'])
    op.create_index('idx_lineage_node_version', 'lineage_nodes', ['version_group_id', 'version'])
    op.create_index('idx_lineage_node_type_created', 'lineage_nodes', ['node_type', 'created_at'])
    op.create_index(op.f('ix_lineage_nodes_created_at'), 'lineage_nodes', ['created_at'])
    op.create_index(op.f('ix_lineage_nodes_data_hash'), 'lineage_nodes', ['data_hash'])
    op.create_index(op.f('ix_lineage_nodes_entity_id'), 'lineage_nodes', ['entity_id'])
    op.create_index(op.f('ix_lineage_nodes_is_latest_version'), 'lineage_nodes', ['is_latest_version'])
    op.create_index(op.f('ix_lineage_nodes_node_type'), 'lineage_nodes', ['node_type'])
    op.create_index(op.f('ix_lineage_nodes_version_group_id'), 'lineage_nodes', ['version_group_id'])

    # ========================================
    # 3. LINEAGE RELATIONSHIPS TABLE
    # ========================================
    op.create_table(
        'lineage_relationships',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('relationship_type', sa.String(length=50), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('child_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transformation_type', sa.String(length=100), nullable=True),
        sa.Column('transformation_function', sa.String(length=255), nullable=True),
        sa.Column('transformation_params', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['child_id'], ['lineage_nodes.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['lineage_nodes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for lineage_relationships
    op.create_index('idx_lineage_rel_parent', 'lineage_relationships', ['parent_id', 'relationship_type'])
    op.create_index('idx_lineage_rel_child', 'lineage_relationships', ['child_id', 'relationship_type'])
    op.create_index('idx_lineage_rel_both', 'lineage_relationships', ['parent_id', 'child_id'])
    op.create_index(op.f('ix_lineage_relationships_child_id'), 'lineage_relationships', ['child_id'])
    op.create_index(op.f('ix_lineage_relationships_parent_id'), 'lineage_relationships', ['parent_id'])
    op.create_index(op.f('ix_lineage_relationships_relationship_type'), 'lineage_relationships', ['relationship_type'])

    # ========================================
    # 4. PostgreSQL TRIGGERS for Immutability
    # ========================================

    # Create function to prevent audit event modifications
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_audit_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Audit events are immutable - no updates or deletes allowed
            IF TG_OP = 'UPDATE' THEN
                RAISE EXCEPTION 'Audit events are immutable and cannot be modified. Event ID: %', OLD.id
                    USING ERRCODE = '23502';  -- not_null_violation
            ELSIF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'Audit events are immutable and cannot be deleted. Event ID: %', OLD.id
                    USING ERRCODE = '23502';
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger to prevent modifications
    op.execute("""
        CREATE TRIGGER audit_events_immutable
        BEFORE UPDATE OR DELETE ON audit_events
        FOR EACH ROW
        EXECUTE FUNCTION prevent_audit_modification();
    """)

    # Create function to validate hash chain on insert
    op.execute("""
        CREATE OR REPLACE FUNCTION validate_audit_hash_chain()
        RETURNS TRIGGER AS $$
        DECLARE
            last_event_hash VARCHAR(64);
        BEGIN
            -- Get the hash of the most recent event
            SELECT event_hash INTO last_event_hash
            FROM audit_events
            ORDER BY sequence_number DESC
            LIMIT 1;

            -- If this is not the first event, validate the chain
            IF last_event_hash IS NOT NULL THEN
                IF NEW.previous_hash != last_event_hash THEN
                    RAISE EXCEPTION 'Hash chain broken: previous_hash does not match last event hash'
                        USING ERRCODE = '23000';  -- integrity_constraint_violation
                END IF;
            ELSE
                -- First event must have genesis hash
                IF NEW.previous_hash != '0000000000000000000000000000000000000000000000000000000000000000' THEN
                    RAISE WARNING 'First audit event should have genesis hash (all zeros)';
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger to validate hash chain
    op.execute("""
        CREATE TRIGGER audit_events_validate_chain
        BEFORE INSERT ON audit_events
        FOR EACH ROW
        EXECUTE FUNCTION validate_audit_hash_chain();
    """)

    # Create function to auto-log lineage changes to audit trail
    op.execute("""
        CREATE OR REPLACE FUNCTION log_lineage_change()
        RETURNS TRIGGER AS $$
        BEGIN
            -- This function can be extended to automatically create
            -- audit events when lineage data changes
            -- For now, it's a placeholder for future enhancement
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger for lineage changes
    op.execute("""
        CREATE TRIGGER lineage_nodes_change_trigger
        AFTER INSERT OR UPDATE ON lineage_nodes
        FOR EACH ROW
        EXECUTE FUNCTION log_lineage_change();
    """)

    # ========================================
    # 5. GDPR Compliance Functions
    # ========================================

    # Function to anonymize audit events (for GDPR compliance)
    op.execute("""
        CREATE OR REPLACE FUNCTION anonymize_audit_event(event_uuid UUID)
        RETURNS VOID AS $$
        BEGIN
            -- Note: Since audit events are immutable, we can only mark them as anonymized
            -- The actual user data should be removed from a separate users table
            -- This is a marker function for compliance tracking
            RAISE NOTICE 'Audit event % marked for anonymization. User data should be removed separately.', event_uuid;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # ========================================
    # 6. Helper Functions
    # ========================================

    # Function to get lineage trace
    op.execute("""
        CREATE OR REPLACE FUNCTION get_lineage_ancestors(node_uuid UUID, max_depth INT DEFAULT 100)
        RETURNS TABLE (
            node_id UUID,
            node_name VARCHAR,
            node_type VARCHAR,
            depth INT,
            path TEXT
        ) AS $$
        WITH RECURSIVE lineage_tree AS (
            -- Base case: start with the given node
            SELECT
                id,
                name,
                node_type,
                0 as depth,
                name::TEXT as path
            FROM lineage_nodes
            WHERE id = node_uuid

            UNION ALL

            -- Recursive case: get parents
            SELECT
                n.id,
                n.name,
                n.node_type,
                lt.depth + 1,
                n.name || ' -> ' || lt.path
            FROM lineage_nodes n
            INNER JOIN lineage_relationships r ON n.id = r.parent_id
            INNER JOIN lineage_tree lt ON r.child_id = lt.node_id
            WHERE lt.depth < max_depth
        )
        SELECT * FROM lineage_tree ORDER BY depth;
        $$ LANGUAGE SQL;
    """)


def downgrade() -> None:
    """Drop all audit trail and lineage tables"""

    # Drop triggers first
    op.execute('DROP TRIGGER IF EXISTS lineage_nodes_change_trigger ON lineage_nodes')
    op.execute('DROP TRIGGER IF EXISTS audit_events_validate_chain ON audit_events')
    op.execute('DROP TRIGGER IF EXISTS audit_events_immutable ON audit_events')

    # Drop functions
    op.execute('DROP FUNCTION IF EXISTS get_lineage_ancestors(UUID, INT)')
    op.execute('DROP FUNCTION IF EXISTS anonymize_audit_event(UUID)')
    op.execute('DROP FUNCTION IF EXISTS log_lineage_change()')
    op.execute('DROP FUNCTION IF EXISTS validate_audit_hash_chain()')
    op.execute('DROP FUNCTION IF EXISTS prevent_audit_modification()')

    # Drop tables (in reverse order due to foreign keys)
    op.drop_table('lineage_relationships')
    op.drop_table('lineage_nodes')
    op.drop_table('audit_events')
