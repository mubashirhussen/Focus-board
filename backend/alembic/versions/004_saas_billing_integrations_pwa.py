"""Add SaaS billing, integrations, workflows, push subscriptions, and task scheduling

Revision ID: 004_saas_billing_integrations_pwa
Revises: 003_audit_trail
Create Date: 2026-11-22 11:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '004_saas_billing_integrations_pwa'
down_revision = '003_audit_trail'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Plans table
    op.create_table(
        'plans',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('slug', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price_cents', sa.Integer(), server_default='0', nullable=False),
        sa.Column('billing_interval', sa.String(length=20), server_default='month', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('features_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('limits_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_plans_slug', 'plans', ['slug'], unique=True)

    # 2. Subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False),
        sa.Column('plan_id', sa.Integer(), sa.ForeignKey('plans.id', name='fk_subscriptions_plan_id'), nullable=False),
        sa.Column('billing_provider', sa.String(length=50), server_default='mock', nullable=False),
        sa.Column('provider_subscription_id', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='active', nullable=False),
        sa.Column('billing_interval', sa.String(length=20), server_default='month', nullable=False),
        sa.Column('current_period_start', sa.DateTime(), nullable=False),
        sa.Column('current_period_end', sa.DateTime(), nullable=False),
        sa.Column('trial_start', sa.DateTime(), nullable=True),
        sa.Column('trial_end', sa.DateTime(), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('canceled_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_subscriptions_tenant_id', 'subscriptions', ['tenant_id'])
    op.create_index('ix_subscriptions_status', 'subscriptions', ['status'])
    op.create_index('ix_subscriptions_tenant_status', 'subscriptions', ['tenant_id', 'status'])

    # 3. Billing Customers table
    op.create_table(
        'billing_customers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False),
        sa.Column('provider', sa.String(length=50), server_default='mock', nullable=False),
        sa.Column('provider_customer_id', sa.String(length=100), nullable=False),
        sa.Column('billing_email', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_billing_customers_tenant_id', 'billing_customers', ['tenant_id'], unique=True)
    op.create_index('ix_billing_customers_provider_id', 'billing_customers', ['provider_customer_id'])

    # 4. Usage Records table
    op.create_table(
        'usage_records',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', name='fk_usage_user_id', ondelete='SET NULL'), nullable=True),
        sa.Column('metric_name', sa.String(length=64), nullable=False),
        sa.Column('usage_quantity', sa.Integer(), server_default='1', nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_usage_tenant_metric', 'usage_records', ['tenant_id', 'metric_name', 'created_at'])

    # 5. External Integrations table
    op.create_table(
        'external_integrations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', name='fk_integrations_user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', name='fk_integrations_ws_id', ondelete='CASCADE'), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='connected', nullable=False),
        sa.Column('external_account_email', sa.String(length=255), nullable=True),
        sa.Column('connection_metadata', sa.Text(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_integrations_user_provider', 'external_integrations', ['user_id', 'provider'], unique=True)

    # 6. Integration Credentials table
    op.create_table(
        'integration_credentials',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('integration_id', sa.Integer(), sa.ForeignKey('external_integrations.id', name='fk_cred_integration_id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('encrypted_access_token', sa.Text(), nullable=False),
        sa.Column('encrypted_refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expiry', sa.DateTime(), nullable=True),
        sa.Column('scopes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # 7. Calendar Sync Mappings table
    op.create_table(
        'calendar_sync_mappings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('integration_id', sa.Integer(), sa.ForeignKey('external_integrations.id', name='fk_map_integration_id', ondelete='CASCADE'), nullable=False),
        sa.Column('task_id', sa.String(length=64), sa.ForeignKey('tasks.id', name='fk_map_task_id', ondelete='CASCADE'), nullable=False),
        sa.Column('external_calendar_id', sa.String(length=255), server_default='primary', nullable=False),
        sa.Column('external_event_id', sa.String(length=255), nullable=False),
        sa.Column('sync_status', sa.String(length=50), server_default='SYNCED', nullable=False),
        sa.Column('last_synced_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_sync_map_unique', 'calendar_sync_mappings', ['integration_id', 'task_id'], unique=True)

    # 8. Sync Logs table
    op.create_table(
        'sync_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('integration_id', sa.Integer(), sa.ForeignKey('external_integrations.id', name='fk_log_integration_id', ondelete='CASCADE'), nullable=False),
        sa.Column('operation', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 9. Workflows table
    op.create_table(
        'workflows',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', name='fk_workflows_user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('trigger_type', sa.String(length=64), nullable=False),
        sa.Column('trigger_config_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('conditions_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('actions_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('execution_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_workflows_tenant_id', 'workflows', ['tenant_id'])

    # 10. Workflow Executions table
    op.create_table(
        'workflow_executions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('workflow_id', sa.Integer(), sa.ForeignKey('workflows.id', name='fk_wf_exec_workflow_id', ondelete='CASCADE'), nullable=False),
        sa.Column('trigger_event', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='success', nullable=False),
        sa.Column('result_details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 11. Push Subscriptions table
    op.create_table(
        'push_subscriptions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', name='fk_push_user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('endpoint', sa.Text(), nullable=False),
        sa.Column('p256dh_key', sa.Text(), nullable=False),
        sa.Column('auth_key', sa.Text(), nullable=False),
        sa.Column('device_info', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_push_user_active', 'push_subscriptions', ['user_id', 'is_active'])

    # 12. Add scheduling columns to tasks table
    with op.batch_alter_table('tasks') as batch_op:
        batch_op.add_column(sa.Column('scheduled_start', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('scheduled_end', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('estimated_duration_minutes', sa.Integer(), server_default='30', nullable=True))

def downgrade() -> None:
    with op.batch_alter_table('tasks') as batch_op:
        batch_op.drop_column('estimated_duration_minutes')
        batch_op.drop_column('scheduled_end')
        batch_op.drop_column('scheduled_start')

    op.drop_table('push_subscriptions')
    op.drop_table('workflow_executions')
    op.drop_table('workflows')
    op.drop_table('sync_logs')
    op.drop_table('calendar_sync_mappings')
    op.drop_table('integration_credentials')
    op.drop_table('external_integrations')
    op.drop_table('usage_records')
    op.drop_table('billing_customers')
    op.drop_table('subscriptions')
    op.drop_table('plans')
