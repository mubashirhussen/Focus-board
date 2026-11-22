"""Add automation workflows, executions, approvals, integration providers, and marketplace tables

Revision ID: 011_automation_and_integration_platform
Revises: 010_strategic_innovation_and_knowledge_intelligence
Create Date: 2026-11-22 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '011_automation_and_integration_platform'
down_revision = '010_strategic_innovation_and_knowledge_intelligence'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # --- PHASE 39: SAAS AUTOMATION WORKFLOWS & EXECUTION ---
    # 1. Automation Workflows
    op.create_table(
        'automation_workflows',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('workflow_type', sa.String(length=64), server_default='EVENT_DRIVEN', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='DRAFT', nullable=False),
        sa.Column('trigger_type', sa.String(length=64), server_default='EVENT', nullable=False),
        sa.Column('trigger_config_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('nodes_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('edges_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('variables_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('execution_settings_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('version', sa.String(length=16), server_default='1.0', nullable=False),
        sa.Column('is_template', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('template_category', sa.String(length=64), nullable=True),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('last_executed_at', sa.DateTime(), nullable=True),
        sa.Column('execution_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('failure_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_automation_workflows_workspace', 'automation_workflows', ['workspace_id'])
    op.create_index('ix_automation_workflows_status', 'automation_workflows', ['status'])
    op.create_index('ix_automation_workflows_type', 'automation_workflows', ['workflow_type'])
    op.create_index('ix_automation_workflows_template', 'automation_workflows', ['is_template'])

    # 2. Automation Workflow Versions
    op.create_table(
        'automation_workflow_versions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('workflow_id', sa.String(length=64), sa.ForeignKey('automation_workflows.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.String(length=16), nullable=False),
        sa.Column('nodes_json', sa.Text(), nullable=False),
        sa.Column('edges_json', sa.Text(), nullable=False),
        sa.Column('change_summary', sa.String(length=255), server_default='Incremental update', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_automation_wf_versions_wfid', 'automation_workflow_versions', ['workflow_id'])

    # 3. Automation Executions
    op.create_table(
        'automation_executions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('workflow_id', sa.String(length=64), sa.ForeignKey('automation_workflows.id', ondelete='CASCADE'), nullable=False),
        sa.Column('workflow_version', sa.String(length=16), server_default='1.0', nullable=False),
        sa.Column('trigger_event', sa.String(length=64), server_default='MANUAL', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='QUEUED', nullable=False),
        sa.Column('context_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('current_node_id', sa.String(length=64), nullable=True),
        sa.Column('results_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('duration_ms', sa.Integer(), server_default='0', nullable=False),
        sa.Column('correlation_id', sa.String(length=128), nullable=False),
        sa.Column('actor_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_automation_executions_wfid', 'automation_executions', ['workflow_id'])
    op.create_index('ix_automation_executions_status', 'automation_executions', ['status'])
    op.create_index('ix_automation_executions_corr', 'automation_executions', ['correlation_id'])

    # 4. Automation Execution Logs
    op.create_table(
        'automation_execution_logs',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('execution_id', sa.String(length=64), sa.ForeignKey('automation_executions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('node_id', sa.String(length=64), nullable=False),
        sa.Column('node_name', sa.String(length=128), nullable=False),
        sa.Column('node_type', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='SUCCESS', nullable=False),
        sa.Column('input_data_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('output_data_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_automation_logs_execid', 'automation_execution_logs', ['execution_id'])

    # 5. Automation Approvals
    op.create_table(
        'automation_approvals',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('execution_id', sa.String(length=64), sa.ForeignKey('automation_executions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('node_id', sa.String(length=64), nullable=False),
        sa.Column('approval_type', sa.String(length=64), server_default='TASK_ACTION', nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('context_summary', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='PENDING', nullable=False),
        sa.Column('assigned_approver_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('decision_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('decision_comments', sa.Text(), nullable=True),
        sa.Column('decision_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_automation_approvals_execid', 'automation_approvals', ['execution_id'])
    op.create_index('ix_automation_approvals_status', 'automation_approvals', ['status'])

    # 6. Automation Schedules
    op.create_table(
        'automation_schedules',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('workflow_id', sa.String(length=64), sa.ForeignKey('automation_workflows.id', ondelete='CASCADE'), nullable=False),
        sa.Column('cron_expression', sa.String(length=64), nullable=False),
        sa.Column('timezone', sa.String(length=64), server_default='UTC', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('next_run_at', sa.DateTime(), nullable=True),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_automation_schedules_wfid', 'automation_schedules', ['workflow_id'])

    # --- PHASE 40: INTEGRATION ECOSYSTEM & MARKETPLACE ---
    # 7. Integration Providers
    op.create_table(
        'integration_providers',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=64), server_default='Productivity', nullable=False),
        sa.Column('icon', sa.String(length=64), server_default='Layers', nullable=False),
        sa.Column('auth_type', sa.String(length=32), server_default='OAUTH2', nullable=False),
        sa.Column('supported_features_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('required_scopes_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('documentation_url', sa.String(length=512), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_integration_providers_category', 'integration_providers', ['category'])

    # 8. Marketplace Listings
    op.create_table(
        'marketplace_listings',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('slug', sa.String(length=128), unique=True, nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=64), server_default='Productivity', nullable=False),
        sa.Column('developer_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('developer_name', sa.String(length=128), server_default='FocusBoard Official', nullable=False),
        sa.Column('version', sa.String(length=16), server_default='1.0.0', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='PUBLISHED', nullable=False),
        sa.Column('is_official', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('permissions_json', sa.Text(), server_default='["tasks:read"]', nullable=False),
        sa.Column('install_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('rating', sa.Float(), server_default='4.9', nullable=False),
        sa.Column('icon', sa.String(length=64), server_default='Layers', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_marketplace_listings_status', 'marketplace_listings', ['status'])
    op.create_index('ix_marketplace_listings_category', 'marketplace_listings', ['category'])

    # 9. Marketplace Installations
    op.create_table(
        'marketplace_installations',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('listing_id', sa.String(length=64), sa.ForeignKey('marketplace_listings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('installed_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('granted_scopes_json', sa.Text(), server_default='["tasks:read"]', nullable=False),
        sa.Column('installed_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_mkt_install_workspace_listing', 'marketplace_installations', ['workspace_id', 'listing_id'], unique=True)

    # 10. OAuth Connectors
    op.create_table(
        'oauth_connectors',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('provider_id', sa.String(length=64), sa.ForeignKey('integration_providers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('connection_status', sa.String(length=32), server_default='AVAILABLE', nullable=False),
        sa.Column('account_identifier', sa.String(length=255), nullable=True),
        sa.Column('granted_scopes_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('encrypted_token_data', sa.Text(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('last_error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_oauth_conn_provider_workspace', 'oauth_connectors', ['provider_id', 'workspace_id'], unique=True)


def downgrade() -> None:
    op.drop_table('oauth_connectors')
    op.drop_table('marketplace_installations')
    op.drop_table('marketplace_listings')
    op.drop_table('integration_providers')
    op.drop_table('automation_schedules')
    op.drop_table('automation_approvals')
    op.drop_table('automation_execution_logs')
    op.drop_table('automation_executions')
    op.drop_table('automation_workflow_versions')
    op.drop_table('automation_workflows')
