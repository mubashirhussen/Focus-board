"""B20: Strategic Intelligence Hardening, Multi-Tenant Scoping, Scenarios, Business KPIs & AI Strategy

Revision ID: 031_b20_strategic_intelligence_hardening
Revises: 030_b19_financial_intelligence_hardening
Create Date: 2026-11-23 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '031_b20_strategic_intelligence_hardening'
down_revision = '030_b19_financial_intelligence_hardening'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # Add organization_id and workspace_id to existing strategic intelligence tables
    target_tables = [
        'strategic_plans',
        'strategic_goals',
        'strategic_initiatives',
        'market_intelligences',
        'market_signals',
        'competitors',
        'swot_entries',
        'market_sizings',
        'strategic_opportunities',
        'strategic_scenarios',
        'strategic_decisions',
    ]

    for tbl in target_tables:
        if tbl in existing_tables:
            cols = {c['name'] for c in inspector.get_columns(tbl)}
            with op.batch_alter_table(tbl) as batch_op:
                if 'organization_id' not in cols:
                    batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
                if 'workspace_id' not in cols:
                    batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))

    # Create business_kpis table if not exists
    if 'business_kpis' not in existing_tables:
        op.create_table(
            'business_kpis',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('organization_id', sa.Integer(), nullable=True),
            sa.Column('workspace_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('category', sa.String(length=64), nullable=False, server_default='GROWTH'),
            sa.Column('measurement_unit', sa.String(length=32), nullable=False, server_default='units'),
            sa.Column('target_value', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('current_value', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('baseline_value', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('trend_direction', sa.String(length=32), nullable=False, server_default='UP'),
            sa.Column('status', sa.String(length=32), nullable=False, server_default='ON_TRACK'),
            sa.Column('owner_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        with op.batch_alter_table('business_kpis') as batch_op:
            batch_op.create_index('ix_business_kpis_category', ['category'], unique=False)
            batch_op.create_index('ix_business_kpis_status', ['status'], unique=False)
            batch_op.create_index('ix_business_kpis_org', ['organization_id'], unique=False)
            batch_op.create_index('ix_business_kpis_ws', ['workspace_id'], unique=False)

    # Create business_kpi_values table if not exists
    if 'business_kpi_values' not in existing_tables:
        op.create_table(
            'business_kpi_values',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('kpi_id', sa.String(length=64), nullable=False),
            sa.Column('value', sa.Float(), nullable=False),
            sa.Column('period_date', sa.String(length=32), nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('recorded_by_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        with op.batch_alter_table('business_kpi_values') as batch_op:
            batch_op.create_index('ix_business_kpi_values_kpi_id', ['kpi_id'], unique=False)
            batch_op.create_index('ix_business_kpi_values_period', ['period_date'], unique=False)

def downgrade() -> None:
    pass
