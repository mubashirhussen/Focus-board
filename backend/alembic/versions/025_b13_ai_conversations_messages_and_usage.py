"""B13: AI Assistant, Conversations, Messages, Token Tracking & Contextual Intelligence

Revision ID: 025_b13_ai_conversations_messages_and_usage
Revises: 024_b12_analytics_and_reporting
Create Date: 2026-11-22 23:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '025_b13_ai_conversations_messages_and_usage'
down_revision = '024_b12_analytics_and_reporting'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. AI Conversations
    if 'ai_conversations' not in existing_tables:
        op.create_table(
            'ai_conversations',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
            sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='SET NULL'), nullable=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('context_type', sa.String(length=32), server_default='GENERAL', nullable=False),
            sa.Column('context_id', sa.String(length=64), nullable=True),
            sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
            sa.Column('is_archived', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_ai_conversations_user_id', 'ai_conversations', ['user_id'])
        op.create_index('ix_ai_conversations_ws_id', 'ai_conversations', ['workspace_id'])
        op.create_index('ix_ai_conversations_created', 'ai_conversations', ['created_at'])

    # 2. AI Messages
    if 'ai_messages' not in existing_tables:
        op.create_table(
            'ai_messages',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('conversation_id', sa.String(length=64), sa.ForeignKey('ai_conversations.id', ondelete='CASCADE'), nullable=False),
            sa.Column('role', sa.String(length=32), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('model', sa.String(length=64), nullable=True),
            sa.Column('provider', sa.String(length=32), nullable=True),
            sa.Column('tokens_input', sa.Integer(), server_default='0', nullable=False),
            sa.Column('tokens_output', sa.Integer(), server_default='0', nullable=False),
            sa.Column('total_tokens', sa.Integer(), server_default='0', nullable=False),
            sa.Column('task_references_json', sa.Text(), server_default='[]', nullable=False),
            sa.Column('proposed_actions_json', sa.Text(), server_default='[]', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_ai_messages_conv_id', 'ai_messages', ['conversation_id'])
        op.create_index('ix_ai_messages_created', 'ai_messages', ['created_at'])

    # 3. AI Usage Logs
    if 'ai_usage_logs' not in existing_tables:
        op.create_table(
            'ai_usage_logs',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True),
            sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='SET NULL'), nullable=True),
            sa.Column('conversation_id', sa.String(length=64), sa.ForeignKey('ai_conversations.id', ondelete='SET NULL'), nullable=True),
            sa.Column('feature', sa.String(length=64), nullable=False),
            sa.Column('provider', sa.String(length=32), nullable=False),
            sa.Column('model', sa.String(length=64), nullable=False),
            sa.Column('prompt_tokens', sa.Integer(), server_default='0', nullable=False),
            sa.Column('completion_tokens', sa.Integer(), server_default='0', nullable=False),
            sa.Column('total_tokens', sa.Integer(), server_default='0', nullable=False),
            sa.Column('estimated_cost_cents', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('latency_ms', sa.Integer(), server_default='0', nullable=False),
            sa.Column('status', sa.String(length=32), server_default='SUCCESS', nullable=False),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_ai_usage_logs_user', 'ai_usage_logs', ['user_id'])
        op.create_index('ix_ai_usage_logs_feature', 'ai_usage_logs', ['feature'])
        op.create_index('ix_ai_usage_logs_created', 'ai_usage_logs', ['created_at'])

def downgrade() -> None:
    pass
