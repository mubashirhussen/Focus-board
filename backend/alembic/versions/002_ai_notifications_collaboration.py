"""Add notifications and collaboration tables

Revision ID: 002_ai_notifications_collaboration
Revises: 001_initial
Create Date: 2026-11-22 11:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '002_ai_notifications_collaboration'
down_revision = '001_initial'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Notifications & Preferences
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('task_id', sa.String(length=64), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='SENT', nullable=False),
        sa.Column('delivery_channel', sa.String(length=50), server_default='IN_APP', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_user_read', 'notifications', ['user_id', 'read_at'])

    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('enable_in_app', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('enable_email', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('enable_due_soon', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('enable_overdue', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('enable_daily_plan', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('daily_reminder_time', sa.String(length=10), server_default='09:00', nullable=False),
        sa.Column('timezone', sa.String(length=50), server_default='UTC', nullable=False),
    )

    # 2. Workspaces
    op.create_table(
        'workspaces',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_workspaces_owner_id', 'workspaces', ['owner_id'])

    # 3. Workspace Members
    op.create_table(
        'workspace_members',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(length=20), server_default='MEMBER', nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_workspace_member_unique', 'workspace_members', ['workspace_id', 'user_id'], unique=True)

    # 4. Workspace Invitations
    op.create_table(
        'workspace_invitations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('inviter_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('invitee_email', sa.String(length=255), nullable=False),
        sa.Column('token', sa.String(length=64), unique=True, nullable=False),
        sa.Column('role', sa.String(length=20), server_default='MEMBER', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='PENDING', nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_workspace_invitations_token', 'workspace_invitations', ['token'])

    # 5. Projects
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('deadline', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_projects_workspace_id', 'projects', ['workspace_id'])

    # 6. Task Comments & Activities
    op.create_table(
        'task_comments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('task_id', sa.String(length=64), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('author_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_task_comments_task_id', 'task_comments', ['task_id'])

    op.create_table(
        'activities',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True),
        sa.Column('task_id', sa.String(length=64), sa.ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True),
        sa.Column('actor_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_activities_workspace_id', 'activities', ['workspace_id'])

    # 7. Add collaboration columns to tasks table
    with op.batch_alter_table('tasks') as batch_op:
        batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('project_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('assignee_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_tasks_workspace_id', 'workspaces', ['workspace_id'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key('fk_tasks_project_id', 'projects', ['project_id'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key('fk_tasks_assignee_id', 'users', ['assignee_id'], ['id'], ondelete='SET NULL')

def downgrade() -> None:
    with op.batch_alter_table('tasks') as batch_op:
        batch_op.drop_column('assignee_id')
        batch_op.drop_column('project_id')
        batch_op.drop_column('workspace_id')

    op.drop_table('activities')
    op.drop_table('task_comments')
    op.drop_table('projects')
    op.drop_table('workspace_invitations')
    op.drop_table('workspace_members')
    op.drop_table('workspaces')
    op.drop_table('notification_preferences')
    op.drop_table('notifications')
