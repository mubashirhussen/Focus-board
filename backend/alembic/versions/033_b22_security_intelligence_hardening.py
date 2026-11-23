"""B22: Security Intelligence, Zero Trust, Threat Detection & SecOps Hardening

Revision ID: 033_b22_security_intelligence_hardening
Revises: 032_b21_data_intelligence_hardening
Create Date: 2026-11-23 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '033_b22_security_intelligence_hardening'
down_revision = '032_b21_data_intelligence_hardening'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. Update security_events
    if 'security_events' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('security_events')}
        with op.batch_alter_table('security_events') as batch_op:
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))

    # 2. Update security_detection_rules
    if 'security_detection_rules' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('security_detection_rules')}
        with op.batch_alter_table('security_detection_rules') as batch_op:
            if 'organization_id' not in cols:
                batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))

    # 3. Update security_detection_results
    if 'security_detection_results' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('security_detection_results')}
        with op.batch_alter_table('security_detection_results') as batch_op:
            if 'organization_id' not in cols:
                batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))

    # 4. Update security_alerts
    if 'security_alerts' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('security_alerts')}
        with op.batch_alter_table('security_alerts') as batch_op:
            if 'organization_id' not in cols:
                batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))

    # 5. Update identity_risk_records
    if 'identity_risk_records' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('identity_risk_records')}
        with op.batch_alter_table('identity_risk_records') as batch_op:
            if 'organization_id' not in cols:
                batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))

    # 6. Update access_review_campaigns
    if 'access_review_campaigns' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('access_review_campaigns')}
        with op.batch_alter_table('access_review_campaigns') as batch_op:
            if 'organization_id' not in cols:
                batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))

    # 7. Update vulnerability_records
    if 'vulnerability_records' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('vulnerability_records')}
        with op.batch_alter_table('vulnerability_records') as batch_op:
            if 'organization_id' not in cols:
                batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))

    # 8. Update security_posture_assessments
    if 'security_posture_assessments' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('security_posture_assessments')}
        with op.batch_alter_table('security_posture_assessments') as batch_op:
            if 'organization_id' not in cols:
                batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))

    # 9. Update security_remediations
    if 'security_remediations' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('security_remediations')}
        with op.batch_alter_table('security_remediations') as batch_op:
            if 'organization_id' not in cols:
                batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            if 'workspace_id' not in cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))

    # 10. Create zero_trust_policies if not exists
    if 'zero_trust_policies' not in existing_tables:
        op.create_table(
            'zero_trust_policies',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('name', sa.String(length=128), nullable=False),
            sa.Column('policy_type', sa.String(length=64), nullable=False),
            sa.Column('target_resource', sa.String(length=128), server_default='*', nullable=False),
            sa.Column('conditions_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('action', sa.String(length=32), server_default='BLOCK', nullable=False),
            sa.Column('is_enabled', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('organization_id', sa.Integer(), nullable=True),
            sa.Column('workspace_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_zero_trust_policies_policy_type', 'zero_trust_policies', ['policy_type'])
        op.create_index('ix_zero_trust_policies_organization_id', 'zero_trust_policies', ['organization_id'])
        op.create_index('ix_zero_trust_policies_workspace_id', 'zero_trust_policies', ['workspace_id'])

    # 11. Create zero_trust_evaluations if not exists
    if 'zero_trust_evaluations' not in existing_tables:
        op.create_table(
            'zero_trust_evaluations',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('resource', sa.String(length=128), nullable=False),
            sa.Column('action_requested', sa.String(length=64), nullable=False),
            sa.Column('decision', sa.String(length=32), nullable=False),
            sa.Column('risk_score', sa.Integer(), server_default='0', nullable=False),
            sa.Column('reasons_json', sa.Text(), server_default='[]', nullable=False),
            sa.Column('context_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('organization_id', sa.Integer(), nullable=True),
            sa.Column('workspace_id', sa.Integer(), nullable=True),
            sa.Column('evaluated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_zero_trust_evaluations_organization_id', 'zero_trust_evaluations', ['organization_id'])
        op.create_index('ix_zero_trust_evaluations_workspace_id', 'zero_trust_evaluations', ['workspace_id'])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    if 'zero_trust_evaluations' in existing_tables:
        op.drop_table('zero_trust_evaluations')
    if 'zero_trust_policies' in existing_tables:
        op.drop_table('zero_trust_policies')
