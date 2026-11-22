"""Add intelligence events, preferences, enterprise policies, custom roles, and MFA

Revision ID: 005_intelligence_and_enterprise
Revises: 004_saas_billing_integrations_pwa
Create Date: 2026-11-22 11:55:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '005_intelligence_and_enterprise'
down_revision = '004_saas_billing_integrations_pwa'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Productivity Events
    op.create_table(
        'productivity_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', name='fk_pe_user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', sa.String(length=64), nullable=False),
        sa.Column('task_id', sa.String(length=64), sa.ForeignKey('tasks.id', name='fk_pe_task_id', ondelete='SET NULL'), nullable=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', name='fk_pe_project_id', ondelete='SET NULL'), nullable=True),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('event_metadata_json', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_prod_event_user_type', 'productivity_events', ['user_id', 'event_type', 'timestamp'])

    # 2. Intelligence Preferences
    op.create_table(
        'intelligence_preferences',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', name='fk_ip_user_id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('insights_enabled', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('coaching_enabled', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('work_start_hour', sa.Integer(), server_default='9', nullable=False),
        sa.Column('work_end_hour', sa.Integer(), server_default='18', nullable=False),
        sa.Column('working_days_json', sa.Text(), server_default='[1,2,3,4,5]', nullable=False),
        sa.Column('time_zone', sa.String(length=50), server_default='UTC', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # 3. Insight Feedback
    op.create_table(
        'insight_feedback',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', name='fk_if_user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('insight_id', sa.String(length=64), nullable=False),
        sa.Column('feedback_type', sa.String(length=32), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_insight_feedback_unique', 'insight_feedback', ['user_id', 'insight_id'], unique=True)

    # 4. Organization Policies
    op.create_table(
        'organization_policies',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False),
        sa.Column('policy_type', sa.String(length=64), nullable=False),
        sa.Column('policy_value_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('updated_by', sa.Integer(), sa.ForeignKey('users.id', name='fk_op_user_id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_org_policy_tenant_type', 'organization_policies', ['tenant_id', 'policy_type'], unique=True)

    # 5. Custom Roles
    op.create_table(
        'custom_roles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('permissions_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', name='fk_cr_user_id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_custom_role_tenant_name', 'custom_roles', ['tenant_id', 'name'], unique=True)

    # 6. Organization Domains
    op.create_table(
        'organization_domains',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('verification_token', sa.String(length=64), nullable=False),
        sa.Column('is_verified', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_org_domain_unique', 'organization_domains', ['tenant_id', 'domain'], unique=True)

    # 7. Enterprise Invitations
    op.create_table(
        'enterprise_invitations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=32), server_default='Member', nullable=False),
        sa.Column('token_hash', sa.String(length=64), unique=True, nullable=False),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_enterprise_invitations_tenant', 'enterprise_invitations', ['tenant_id'])

    # 8. User MFA
    op.create_table(
        'user_mfa',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', name='fk_mfa_user_id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('secret_hash', sa.String(length=255), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('recovery_codes_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('enrolled_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

def downgrade() -> None:
    op.drop_table('user_mfa')
    op.drop_table('enterprise_invitations')
    op.drop_table('organization_domains')
    op.drop_table('custom_roles')
    op.drop_table('organization_policies')
    op.drop_table('insight_feedback')
    op.drop_table('intelligence_preferences')
    op.drop_table('productivity_events')
