"""B21: Data Intelligence, BI, Pipelines, Quality, Lineage, Data Sources & Governance Hardening

Revision ID: 032_b21_data_intelligence_hardening
Revises: 031_b20_strategic_intelligence_hardening
Create Date: 2026-11-23 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '032_b21_data_intelligence_hardening'
down_revision = '031_b20_strategic_intelligence_hardening'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. Update analytics_datasets
    if 'analytics_datasets' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('analytics_datasets')}
        with op.batch_alter_table('analytics_datasets') as batch_op:
            if 'organization_id' not in cols:
                batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))
            if 'classification' not in cols:
                batch_op.add_column(sa.Column('classification', sa.String(length=32), server_default='INTERNAL', nullable=False))
            if 'source_type' not in cols:
                batch_op.add_column(sa.Column('source_type', sa.String(length=64), server_default='DATABASE', nullable=False))

    # 2. Update analytics_data_pipelines
    if 'analytics_data_pipelines' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('analytics_data_pipelines')}
        with op.batch_alter_table('analytics_data_pipelines') as batch_op:
            if 'organization_id' not in cols:
                batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))
            if 'pipeline_config_json' not in cols:
                batch_op.add_column(sa.Column('pipeline_config_json', sa.Text(), server_default='{}', nullable=False))

    # 3. Update analytics_pipeline_executions
    if 'analytics_pipeline_executions' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('analytics_pipeline_executions')}
        with op.batch_alter_table('analytics_pipeline_executions') as batch_op:
            if 'logs_json' not in cols:
                batch_op.add_column(sa.Column('logs_json', sa.Text(), server_default='[]', nullable=False))

    # 4. Update analytics_dashboards
    if 'analytics_dashboards' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('analytics_dashboards')}
        with op.batch_alter_table('analytics_dashboards') as batch_op:
            if 'organization_id' not in cols:
                batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))

    # 5. Update analytics_custom_reports
    if 'analytics_custom_reports' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('analytics_custom_reports')}
        with op.batch_alter_table('analytics_custom_reports') as batch_op:
            if 'organization_id' not in cols:
                batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))

    # 6. Update data_quality_rules
    if 'data_quality_rules' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('data_quality_rules')}
        with op.batch_alter_table('data_quality_rules') as batch_op:
            if 'organization_id' not in cols:
                batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))

    # 7. Update data_quality_issues
    if 'data_quality_issues' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('data_quality_issues')}
        with op.batch_alter_table('data_quality_issues') as batch_op:
            if 'organization_id' not in cols:
                batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))

    # 8. Update analytics_metric_definitions
    if 'analytics_metric_definitions' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('analytics_metric_definitions')}
        with op.batch_alter_table('analytics_metric_definitions') as batch_op:
            if 'organization_id' not in cols:
                batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))

    # 9. Create data_sources table if not exists
    if 'data_sources' not in existing_tables:
        op.create_table(
            'data_sources',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('organization_id', sa.Integer(), nullable=True),
            sa.Column('workspace_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(length=150), nullable=False),
            sa.Column('source_type', sa.String(length=50), server_default='INTERNAL_DB', nullable=False),
            sa.Column('connection_status', sa.String(length=30), server_default='CONNECTED', nullable=False),
            sa.Column('config_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('last_sync_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        with op.batch_alter_table('data_sources') as batch_op:
            batch_op.create_index('ix_data_sources_org', ['organization_id'], unique=False)
            batch_op.create_index('ix_data_sources_ws', ['workspace_id'], unique=False)
            batch_op.create_index('ix_data_sources_type', ['source_type'], unique=False)

    # 10. Create data_lineage_nodes table if not exists
    if 'data_lineage_nodes' not in existing_tables:
        op.create_table(
            'data_lineage_nodes',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('organization_id', sa.Integer(), nullable=True),
            sa.Column('workspace_id', sa.Integer(), nullable=True),
            sa.Column('source_asset_id', sa.String(length=64), nullable=False),
            sa.Column('target_asset_id', sa.String(length=64), nullable=False),
            sa.Column('lineage_type', sa.String(length=50), server_default='SOURCE_TO_DATASET', nullable=False),
            sa.Column('transformation_details', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        with op.batch_alter_table('data_lineage_nodes') as batch_op:
            batch_op.create_index('ix_data_lineage_source', ['source_asset_id'], unique=False)
            batch_op.create_index('ix_data_lineage_target', ['target_asset_id'], unique=False)

    # 11. Create data_insights table if not exists
    if 'data_insights' not in existing_tables:
        op.create_table(
            'data_insights',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('organization_id', sa.Integer(), nullable=True),
            sa.Column('workspace_id', sa.Integer(), nullable=True),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('insight_type', sa.String(length=50), server_default='TREND', nullable=False),
            sa.Column('severity', sa.String(length=30), server_default='INFO', nullable=False),
            sa.Column('confidence_score', sa.Float(), server_default='0.9', nullable=False),
            sa.Column('supporting_data_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('status', sa.String(length=30), server_default='ACTIVE', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        with op.batch_alter_table('data_insights') as batch_op:
            batch_op.create_index('ix_data_insights_org', ['organization_id'], unique=False)
            batch_op.create_index('ix_data_insights_type', ['insight_type'], unique=False)

def downgrade() -> None:
    pass
