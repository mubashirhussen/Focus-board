"""B18: Product Lifecycle Intelligence Hardening, Workspace Isolation, Statistical Summary & Readiness

Revision ID: 029_b18_product_lifecycle_hardening
Revises: 028_b17_cx_intelligence
Create Date: 2026-11-23 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '029_b18_product_lifecycle_hardening'
down_revision = '028_b17_cx_intelligence'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. product_discoveries: workspace_id
    if 'product_discoveries' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('product_discoveries')}
        with op.batch_alter_table('product_discoveries') as batch_op:
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))

    # 2. product_ideas: workspace_id, linked_task_id, linked_feature_id
    if 'product_ideas' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('product_ideas')}
        with op.batch_alter_table('product_ideas') as batch_op:
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))
            if 'linked_task_id' not in cols:
                batch_op.add_column(sa.Column('linked_task_id', sa.String(length=64), nullable=True))
            if 'linked_feature_id' not in cols:
                batch_op.add_column(sa.Column('linked_feature_id', sa.String(length=64), nullable=True))

    # 3. product_feature_requests: workspace_id, feedback_id
    if 'product_feature_requests' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('product_feature_requests')}
        with op.batch_alter_table('product_feature_requests') as batch_op:
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))
            if 'feedback_id' not in cols:
                batch_op.add_column(sa.Column('feedback_id', sa.Integer(), nullable=True))

    # 4. product_opportunities: workspace_id
    if 'product_opportunities' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('product_opportunities')}
        with op.batch_alter_table('product_opportunities') as batch_op:
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))

    # 5. product_prioritization_items: workspace_id, formula_json
    if 'product_prioritization_items' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('product_prioritization_items')}
        with op.batch_alter_table('product_prioritization_items') as batch_op:
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))
            if 'formula_json' not in cols:
                batch_op.add_column(sa.Column('formula_json', sa.Text(), server_default='{}', nullable=False))

    # 6. product_initiatives: workspace_id
    if 'product_initiatives' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('product_initiatives')}
        with op.batch_alter_table('product_initiatives') as batch_op:
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))

    # 7. lifecycle_roadmap_items: workspace_id, sort_order, linked_feature_id, linked_task_id
    if 'lifecycle_roadmap_items' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('lifecycle_roadmap_items')}
        with op.batch_alter_table('lifecycle_roadmap_items') as batch_op:
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))
            if 'sort_order' not in cols:
                batch_op.add_column(sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False))
            if 'linked_feature_id' not in cols:
                batch_op.add_column(sa.Column('linked_feature_id', sa.String(length=64), nullable=True))
            if 'linked_task_id' not in cols:
                batch_op.add_column(sa.Column('linked_task_id', sa.String(length=64), nullable=True))

    # 8. product_experiments: workspace_id, statistical_summary_json
    if 'product_experiments' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('product_experiments')}
        with op.batch_alter_table('product_experiments') as batch_op:
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))
            if 'statistical_summary_json' not in cols:
                batch_op.add_column(sa.Column('statistical_summary_json', sa.Text(), server_default='{}', nullable=False))

    # 9. product_releases: workspace_id, readiness_score, readiness_status
    if 'product_releases' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('product_releases')}
        with op.batch_alter_table('product_releases') as batch_op:
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))
            if 'readiness_score' not in cols:
                batch_op.add_column(sa.Column('readiness_score', sa.Float(), server_default='100.0', nullable=False))
            if 'readiness_status' not in cols:
                batch_op.add_column(sa.Column('readiness_status', sa.String(length=32), server_default='READY', nullable=False))

    # 10. product_decisions: workspace_id
    if 'product_decisions' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('product_decisions')}
        with op.batch_alter_table('product_decisions') as batch_op:
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))

    # 11. product_risk_records: workspace_id, risk_score
    if 'product_risk_records' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('product_risk_records')}
        with op.batch_alter_table('product_risk_records') as batch_op:
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))
            if 'risk_score' not in cols:
                batch_op.add_column(sa.Column('risk_score', sa.Float(), server_default='25.0', nullable=False))

def downgrade() -> None:
    pass
