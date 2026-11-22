"""Add AI agents, agent executions, approvals, memory, and regional settings tables

Revision ID: 007_ai_agents_and_globalization
Revises: 006_growth_and_customer_operations
Create Date: 2026-11-22 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '007_ai_agents_and_globalization'
down_revision = '006_growth_and_customer_operations'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. AI Agents
    op.create_table(
        'ai_agents',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('agent_type', sa.String(length=64), nullable=False),
        sa.Column('model_name', sa.String(length=64), server_default='focusboard-agent-v1', nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('tools_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('is_system', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_ai_agents_type', 'ai_agents', ['agent_type'])

    # 2. AI Agent Executions
    op.create_table(
        'ai_agent_executions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='SET NULL'), nullable=True),
        sa.Column('agent_id', sa.String(length=64), sa.ForeignKey('ai_agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='PLANNING', nullable=False),
        sa.Column('plan_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('current_step_index', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_steps', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), server_default='0', nullable=False),
        sa.Column('cost_estimate_cents', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_ai_agent_executions_user', 'ai_agent_executions', ['user_id'])
    op.create_index('ix_ai_agent_executions_agent', 'ai_agent_executions', ['agent_id'])
    op.create_index('ix_ai_agent_executions_status', 'ai_agent_executions', ['status'])

    # 3. AI Agent Execution Steps
    op.create_table(
        'ai_agent_execution_steps',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('execution_id', sa.String(length=64), sa.ForeignKey('ai_agent_executions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_index', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('tool_name', sa.String(length=64), nullable=False),
        sa.Column('arguments_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('requires_approval', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='PENDING', nullable=False),
        sa.Column('result_json', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_ai_agent_exec_steps_exec', 'ai_agent_execution_steps', ['execution_id'])

    # 4. AI Agent Approvals
    op.create_table(
        'ai_agent_approvals',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('execution_id', sa.String(length=64), sa.ForeignKey('ai_agent_executions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_id', sa.Integer(), sa.ForeignKey('ai_agent_execution_steps.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action_type', sa.String(length=64), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('target_resource', sa.String(length=255), nullable=False),
        sa.Column('proposed_payload_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='PENDING', nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_ai_agent_approvals_exec', 'ai_agent_approvals', ['execution_id'])
    op.create_index('ix_ai_agent_approvals_user', 'ai_agent_approvals', ['user_id'])
    op.create_index('ix_ai_agent_approvals_status', 'ai_agent_approvals', ['status'])

    # 5. AI Persistent Preferences (Memory)
    op.create_table(
        'ai_persistent_preferences',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('planning_style', sa.String(length=32), server_default='balanced', nullable=False),
        sa.Column('preferred_work_hours', sa.Integer(), server_default='6', nullable=False),
        sa.Column('summary_format', sa.String(length=32), server_default='bullet_points', nullable=False),
        sa.Column('prioritization_approach', sa.String(length=32), server_default='deadline_first', nullable=False),
        sa.Column('personalization_enabled', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_ai_persistent_pref_user', 'ai_persistent_preferences', ['user_id'])

    # 6. User Regional Settings (Phase 31)
    op.create_table(
        'user_regional_settings',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('language', sa.String(length=16), server_default='en', nullable=False),
        sa.Column('locale', sa.String(length=32), server_default='en-US', nullable=False),
        sa.Column('timezone', sa.String(length=64), server_default='Asia/Kolkata', nullable=False),
        sa.Column('date_format', sa.String(length=32), server_default='YYYY-MM-DD', nullable=False),
        sa.Column('time_format', sa.String(length=16), server_default='12h', nullable=False),
        sa.Column('week_start', sa.Integer(), server_default='1', nullable=False),
        sa.Column('currency', sa.String(length=8), server_default='USD', nullable=False),
        sa.Column('number_format', sa.String(length=32), server_default='standard', nullable=False),
        sa.Column('direction', sa.String(length=8), server_default='ltr', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_user_regional_settings_user', 'user_regional_settings', ['user_id'])

def downgrade() -> None:
    op.drop_table('user_regional_settings')
    op.drop_table('ai_persistent_preferences')
    op.drop_table('ai_agent_approvals')
    op.drop_table('ai_agent_execution_steps')
    op.drop_table('ai_agent_executions')
    op.drop_table('ai_agents')
