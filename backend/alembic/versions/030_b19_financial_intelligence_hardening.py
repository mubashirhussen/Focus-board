"""B19: Financial Intelligence Hardening, Multi-Tenant Scoping, Data Sources, Imports, Insights & Scenarios

Revision ID: 030_b19_financial_intelligence_hardening
Revises: 029_b18_product_lifecycle_hardening
Create Date: 2026-11-23 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '030_b19_financial_intelligence_hardening'
down_revision = '029_b18_product_lifecycle_hardening'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. financial_transactions
    if 'financial_transactions' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('financial_transactions')}
        with op.batch_alter_table('financial_transactions') as batch_op:
            if 'organization_id' not in cols:
                batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))

    # 2. cost_records
    if 'cost_records' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('cost_records')}
        with op.batch_alter_table('cost_records') as batch_op:
            if 'organization_id' not in cols:
                batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))

    # 3. financial_budgets
    if 'financial_budgets' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('financial_budgets')}
        with op.batch_alter_table('financial_budgets') as batch_op:
            if 'organization_id' not in cols:
                batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))

    # 4. financial_forecasts
    if 'financial_forecasts' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('financial_forecasts')}
        with op.batch_alter_table('financial_forecasts') as batch_op:
            if 'organization_id' not in cols:
                batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))
            if 'tenant_id' not in cols:
                batch_op.add_column(sa.Column('tenant_id', sa.String(length=64), nullable=True))

    # 5. financial_metric_snapshots
    if 'financial_metric_snapshots' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('financial_metric_snapshots')}
        with op.batch_alter_table('financial_metric_snapshots') as batch_op:
            if 'organization_id' not in cols:
                batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))

    # 6. financial_data_sources
    if 'financial_data_sources' not in existing_tables:
        op.create_table(
            'financial_data_sources',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
            sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True),
            sa.Column('name', sa.String(length=128), nullable=False),
            sa.Column('source_type', sa.String(length=64), nullable=False),
            sa.Column('status', sa.String(length=32), server_default='CONNECTED', nullable=False),
            sa.Column('sync_status', sa.String(length=32), server_default='IDLE', nullable=False),
            sa.Column('last_synced_at', sa.DateTime(), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('config_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_fin_ds_org', 'financial_data_sources', ['organization_id'])
        op.create_index('ix_fin_ds_ws', 'financial_data_sources', ['workspace_id'])

    # 7. financial_imports
    if 'financial_imports' not in existing_tables:
        op.create_table(
            'financial_imports',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
            sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True),
            sa.Column('filename', sa.String(length=255), nullable=False),
            sa.Column('import_type', sa.String(length=32), server_default='TRANSACTIONS', nullable=False),
            sa.Column('status', sa.String(length=32), server_default='PREVIEW', nullable=False),
            sa.Column('total_rows', sa.Integer(), server_default='0', nullable=False),
            sa.Column('valid_rows', sa.Integer(), server_default='0', nullable=False),
            sa.Column('error_rows', sa.Integer(), server_default='0', nullable=False),
            sa.Column('total_amount_cents', sa.Integer(), server_default='0', nullable=False),
            sa.Column('summary_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('imported_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_fin_imp_org', 'financial_imports', ['organization_id'])
        op.create_index('ix_fin_imp_ws', 'financial_imports', ['workspace_id'])

    # 8. financial_insights
    if 'financial_insights' not in existing_tables:
        op.create_table(
            'financial_insights',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
            sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('insight_type', sa.String(length=64), nullable=False),
            sa.Column('severity', sa.String(length=32), server_default='INFO', nullable=False),
            sa.Column('supporting_metrics_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('recommended_action', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=32), server_default='OPEN', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_fin_ins_org', 'financial_insights', ['organization_id'])
        op.create_index('ix_fin_ins_ws', 'financial_insights', ['workspace_id'])

    # 9. financial_recommendations
    if 'financial_recommendations' not in existing_tables:
        op.create_table(
            'financial_recommendations',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
            sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('category', sa.String(length=64), nullable=False),
            sa.Column('potential_savings_cents', sa.Integer(), server_default='0', nullable=False),
            sa.Column('impact', sa.String(length=32), server_default='MEDIUM', nullable=False),
            sa.Column('status', sa.String(length=32), server_default='PENDING', nullable=False),
            sa.Column('action_taken_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_fin_rec_org', 'financial_recommendations', ['organization_id'])
        op.create_index('ix_fin_rec_ws', 'financial_recommendations', ['workspace_id'])

    # 10. financial_scenarios
    if 'financial_scenarios' not in existing_tables:
        op.create_table(
            'financial_scenarios',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
            sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True),
            sa.Column('name', sa.String(length=128), nullable=False),
            sa.Column('scenario_type', sa.String(length=32), server_default='BASE', nullable=False),
            sa.Column('revenue_growth_rate', sa.Float(), server_default='0.05', nullable=False),
            sa.Column('cost_factor', sa.Float(), server_default='1.0', nullable=False),
            sa.Column('projected_mrr_cents', sa.Integer(), server_default='0', nullable=False),
            sa.Column('projected_arr_cents', sa.Integer(), server_default='0', nullable=False),
            sa.Column('projected_margin_pct', sa.Float(), server_default='80.0', nullable=False),
            sa.Column('assumptions_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_fin_scen_org', 'financial_scenarios', ['organization_id'])
        op.create_index('ix_fin_scen_ws', 'financial_scenarios', ['workspace_id'])

def downgrade() -> None:
    op.drop_table('financial_scenarios')
    op.drop_table('financial_recommendations')
    op.drop_table('financial_insights')
    op.drop_table('financial_imports')
    op.drop_table('financial_data_sources')
