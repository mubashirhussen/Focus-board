"""Add growth engine, customer support, knowledge base, and roadmap tables

Revision ID: 006_growth_and_customer_operations
Revises: 005_intelligence_and_enterprise
Create Date: 2026-11-22 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '006_growth_and_customer_operations'
down_revision = '005_intelligence_and_enterprise'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Onboarding Progress
    op.create_table(
        'onboarding_progress',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('current_step', sa.Integer(), server_default='1', nullable=False),
        sa.Column('completed_steps_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('dismissed', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('primary_goal', sa.String(length=100), server_default='personal_productivity', nullable=False),
        sa.Column('is_completed', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_onboarding_progress_user_id', 'onboarding_progress', ['user_id'])

    # 2. Product Analytics Events
    op.create_table(
        'product_analytics_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_name', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='SET NULL'), nullable=True),
        sa.Column('properties_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('source', sa.String(length=50), server_default='web', nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_product_analytics_events_name', 'product_analytics_events', ['event_name'])
    op.create_index('ix_product_analytics_events_user', 'product_analytics_events', ['user_id'])
    op.create_index('ix_product_analytics_events_time', 'product_analytics_events', ['timestamp'])

    # 3. Customer Feedbacks
    op.create_table(
        'customer_feedbacks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='SET NULL'), nullable=True),
        sa.Column('category', sa.String(length=50), server_default='general_feedback', nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=30), server_default='NEW', nullable=False),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_customer_feedbacks_user', 'customer_feedbacks', ['user_id'])
    op.create_index('ix_customer_feedbacks_status', 'customer_feedbacks', ['status'])

    # 4. Support Tickets
    op.create_table(
        'support_tickets',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), server_default='technical_issue', nullable=False),
        sa.Column('priority', sa.String(length=20), server_default='NORMAL', nullable=False),
        sa.Column('status', sa.String(length=30), server_default='OPEN', nullable=False),
        sa.Column('assigned_agent_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('sla_deadline', sa.DateTime(), nullable=True),
        sa.Column('first_response_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_support_tickets_user', 'support_tickets', ['user_id'])
    op.create_index('ix_support_tickets_status', 'support_tickets', ['status'])
    op.create_index('ix_support_tickets_priority', 'support_tickets', ['priority'])

    # 5. Support Messages
    op.create_table(
        'support_messages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('ticket_id', sa.String(length=64), sa.ForeignKey('support_tickets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sender_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_internal_note', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_support_messages_ticket', 'support_messages', ['ticket_id'])

    # 6. Knowledge Base Categories
    op.create_table(
        'knowledge_base_categories',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), unique=True, nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
    )

    # 7. Knowledge Base Articles
    op.create_table(
        'knowledge_base_articles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('knowledge_base_categories.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), unique=True, nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='PUBLISHED', nullable=False),
        sa.Column('helpful_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('not_helpful_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_kb_articles_category', 'knowledge_base_articles', ['category_id'])
    op.create_index('ix_kb_articles_slug', 'knowledge_base_articles', ['slug'])

    # 8. Product Roadmap Items
    op.create_table(
        'product_roadmap_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=30), server_default='PLANNED', nullable=False),
        sa.Column('category', sa.String(length=50), server_default='Productivity', nullable=False),
        sa.Column('vote_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_roadmap_status', 'product_roadmap_items', ['status'])

def downgrade() -> None:
    op.drop_table('product_roadmap_items')
    op.drop_table('knowledge_base_articles')
    op.drop_table('knowledge_base_categories')
    op.drop_table('support_messages')
    op.drop_table('support_tickets')
    op.drop_table('customer_feedbacks')
    op.drop_table('product_analytics_events')
    op.drop_table('onboarding_progress')
