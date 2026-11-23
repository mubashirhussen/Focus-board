"""B16: Integrations, Synchronization Jobs, and Entity Mappings

Revision ID: 027_b16_integrations_sync_and_mappings
Revises: 026_b14_knowledge_chunks_and_embeddings
Create Date: 2026-11-23 00:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '027_b16_integrations_sync_and_mappings'
down_revision = '026_b14_knowledge_chunks_and_embeddings'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. Update external_integrations table if missing new columns
    if 'external_integrations' in existing_tables:
        existing_cols = {col['name'] for col in inspector.get_columns('external_integrations')}
        if 'config_json' not in existing_cols:
            op.add_column('external_integrations', sa.Column('config_json', sa.Text(), server_default='{}', nullable=False))
        if 'health_status' not in existing_cols:
            op.add_column('external_integrations', sa.Column('health_status', sa.String(length=32), server_default='HEALTHY', nullable=False))
        if 'last_error_message' not in existing_cols:
            op.add_column('external_integrations', sa.Column('last_error_message', sa.Text(), nullable=True))

    # 2. Update oauth_connectors table if missing config_json or health_status
    if 'oauth_connectors' in existing_tables:
        existing_cols = {col['name'] for col in inspector.get_columns('oauth_connectors')}
        if 'config_json' not in existing_cols:
            op.add_column('oauth_connectors', sa.Column('config_json', sa.Text(), server_default='{}', nullable=False))
        if 'health_status' not in existing_cols:
            op.add_column('oauth_connectors', sa.Column('health_status', sa.String(length=32), server_default='HEALTHY', nullable=False))

    # 3. Create integration_entity_mappings
    if 'integration_entity_mappings' not in existing_tables:
        op.create_table(
            'integration_entity_mappings',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('integration_id', sa.Integer(), sa.ForeignKey('external_integrations.id', ondelete='CASCADE'), nullable=True),
            sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True),
            sa.Column('provider', sa.String(length=64), nullable=False),
            sa.Column('entity_type', sa.String(length=64), nullable=False),
            sa.Column('internal_id', sa.String(length=64), nullable=False),
            sa.Column('external_id', sa.String(length=255), nullable=False),
            sa.Column('external_url', sa.String(length=512), nullable=True),
            sa.Column('sync_status', sa.String(length=32), server_default='SYNCED', nullable=False),
            sa.Column('metadata_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('last_synced_at', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_iem_provider_internal', 'integration_entity_mappings', ['provider', 'internal_id'])
        op.create_index('ix_iem_provider_external', 'integration_entity_mappings', ['provider', 'external_id'])

    # 4. Create integration_sync_jobs
    if 'integration_sync_jobs' not in existing_tables:
        op.create_table(
            'integration_sync_jobs',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('integration_id', sa.Integer(), sa.ForeignKey('external_integrations.id', ondelete='CASCADE'), nullable=True),
            sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('provider', sa.String(length=64), nullable=False),
            sa.Column('sync_type', sa.String(length=32), server_default='INCREMENTAL', nullable=False),
            sa.Column('direction', sa.String(length=32), server_default='BIDIRECTIONAL', nullable=False),
            sa.Column('status', sa.String(length=32), server_default='COMPLETED', nullable=False),
            sa.Column('records_synced', sa.Integer(), server_default='0', nullable=False),
            sa.Column('records_failed', sa.Integer(), server_default='0', nullable=False),
            sa.Column('conflict_resolution', sa.String(length=32), server_default='LATEST_UPDATE_WINS', nullable=False),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('duration_ms', sa.Integer(), server_default='0', nullable=False),
            sa.Column('started_at', sa.DateTime(), nullable=False),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
        )
        op.create_index('ix_sync_jobs_provider', 'integration_sync_jobs', ['provider'])
        op.create_index('ix_sync_jobs_status', 'integration_sync_jobs', ['status'])

def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    if 'integration_sync_jobs' in existing_tables:
        op.drop_table('integration_sync_jobs')
    if 'integration_entity_mappings' in existing_tables:
        op.drop_table('integration_entity_mappings')
