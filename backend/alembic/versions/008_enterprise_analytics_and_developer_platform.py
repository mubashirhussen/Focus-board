"""Add enterprise analytics, project milestones, project risks, resource capacities, reports, and developer platform tables

Revision ID: 008_enterprise_analytics_and_developer_platform
Revises: 007_ai_agents_and_globalization
Create Date: 2026-11-22 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '008_enterprise_analytics_and_developer_platform'
down_revision = '007_ai_agents_and_globalization'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Project Milestones
    op.create_table(
        'project_milestones',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='PENDING', nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_project_milestones_proj', 'project_milestones', ['project_id'])
    op.create_index('ix_project_milestones_status', 'project_milestones', ['status'])

    # 2. Project Risks
    op.create_table(
        'project_risks',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category', sa.String(length=32), nullable=False),
        sa.Column('severity', sa.String(length=32), server_default='MEDIUM', nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('mitigation_plan', sa.Text(), nullable=True),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_project_risks_proj', 'project_risks', ['project_id'])
    op.create_index('ix_project_risks_status', 'project_risks', ['status'])

    # 3. Resource Capacities
    op.create_table(
        'resource_capacities',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('weekly_hours_capacity', sa.Float(), server_default='40.0', nullable=False),
        sa.Column('effective_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_resource_capacities_user', 'resource_capacities', ['user_id'])
    op.create_index('ix_resource_capacities_ws', 'resource_capacities', ['workspace_id'])

    # 4. Analytics Reports
    op.create_table(
        'analytics_reports',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('report_type', sa.String(length=64), nullable=False),
        sa.Column('parameters_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('summary_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('format', sa.String(length=16), server_default='JSON', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_analytics_reports_ws', 'analytics_reports', ['workspace_id'])
    op.create_index('ix_analytics_reports_type', 'analytics_reports', ['report_type'])

    # 5. Developer Applications
    op.create_table(
        'developer_applications',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('app_type', sa.String(length=32), server_default='INTERNAL', nullable=False),
        sa.Column('redirect_uri', sa.String(length=512), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_dev_apps_user', 'developer_applications', ['user_id'])
    op.create_index('ix_dev_apps_ws', 'developer_applications', ['workspace_id'])

    # 6. Developer Credentials
    op.create_table(
        'developer_credentials',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('application_id', sa.String(length=64), sa.ForeignKey('developer_applications.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('key_prefix', sa.String(length=16), nullable=False),
        sa.Column('hashed_key', sa.String(length=128), nullable=False, unique=True),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('scopes_json', sa.Text(), server_default='["tasks:read"]', nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_dev_creds_app', 'developer_credentials', ['application_id'])
    op.create_index('ix_dev_creds_prefix', 'developer_credentials', ['key_prefix'])

    # 7. Webhook Subscriptions
    op.create_table(
        'webhook_subscriptions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('application_id', sa.String(length=64), sa.ForeignKey('developer_applications.id', ondelete='CASCADE'), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_url', sa.String(length=512), nullable=False),
        sa.Column('secret_key', sa.String(length=128), nullable=False),
        sa.Column('events_json', sa.Text(), server_default='["task.created","task.updated","task.completed"]', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('failure_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_delivered_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_webhook_subs_ws', 'webhook_subscriptions', ['workspace_id'])

    # 8. Webhook Deliveries
    op.create_table(
        'webhook_deliveries',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('subscription_id', sa.String(length=64), sa.ForeignKey('webhook_subscriptions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('payload_json', sa.Text(), nullable=False),
        sa.Column('response_status_code', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('attempt_count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('delivered_at', sa.DateTime(), nullable=False),
        sa.Column('is_success', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
    )
    op.create_index('ix_webhook_deliveries_sub', 'webhook_deliveries', ['subscription_id'])
    op.create_index('ix_webhook_deliveries_status', 'webhook_deliveries', ['is_success'])

    # 9. API Usage Records
    op.create_table(
        'api_usage_records',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('credential_id', sa.String(length=64), sa.ForeignKey('developer_credentials.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('endpoint', sa.String(length=255), nullable=False),
        sa.Column('method', sa.String(length=16), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), server_default='0', nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_api_usage_user', 'api_usage_records', ['user_id'])
    op.create_index('ix_api_usage_ts', 'api_usage_records', ['timestamp'])

    # 10. Idempotency Records
    op.create_table(
        'idempotency_records',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('idempotency_key', sa.String(length=128), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('endpoint', sa.String(length=255), nullable=False),
        sa.Column('request_hash', sa.String(length=64), nullable=False),
        sa.Column('response_code', sa.Integer(), nullable=False),
        sa.Column('response_body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_idem_key_user', 'idempotency_records', ['idempotency_key', 'user_id'])
    op.create_index('ix_idem_expires', 'idempotency_records', ['expires_at'])

def downgrade() -> None:
    op.drop_table('idempotency_records')
    op.drop_table('api_usage_records')
    op.drop_table('webhook_deliveries')
    op.drop_table('webhook_subscriptions')
    op.drop_table('developer_credentials')
    op.drop_table('developer_applications')
    op.drop_table('analytics_reports')
    op.drop_table('resource_capacities')
    op.drop_table('project_risks')
    op.drop_table('project_milestones')
