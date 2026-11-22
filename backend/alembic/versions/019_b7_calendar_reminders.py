"""B7: Complete Calendar, Scheduling, Deadlines, Reminders & Time-Based Task Management

Revision ID: 019_b7_calendar_reminders
Revises: 018_b6_boards_and_views
Create Date: 2026-11-22 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '019_b7_calendar_reminders'
down_revision = '018_b6_boards_and_views'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. Add scheduling columns to tasks table if missing
    if 'tasks' in existing_tables:
        existing_cols = [c['name'] for c in inspector.get_columns('tasks')]
        if 'is_all_day' not in existing_cols:
            op.add_column('tasks', sa.Column('is_all_day', sa.Boolean(), server_default='0', nullable=False))
        if 'start_date' not in existing_cols:
            op.add_column('tasks', sa.Column('start_date', sa.String(length=50), nullable=True))
        if 'timezone_name' not in existing_cols:
            op.add_column('tasks', sa.Column('timezone_name', sa.String(length=50), server_default='UTC', nullable=True))

    # 2. Create reminders table
    if 'reminders' not in existing_tables:
        op.create_table(
            'reminders',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
            sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True),
            sa.Column('task_id', sa.String(length=64), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('reminder_type', sa.String(length=50), server_default='DUE_DATE', nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('scheduled_at', sa.DateTime(), nullable=False),
            sa.Column('timezone', sa.String(length=50), server_default='UTC', nullable=False),
            sa.Column('status', sa.String(length=50), server_default='PENDING', nullable=False),
            sa.Column('delivery_channel', sa.String(length=50), server_default='IN_APP', nullable=False),
            sa.Column('delivery_attempts', sa.Integer(), server_default='0', nullable=False),
            sa.Column('max_attempts', sa.Integer(), server_default='3', nullable=False),
            sa.Column('snoozed_until', sa.DateTime(), nullable=True),
            sa.Column('delivered_at', sa.DateTime(), nullable=True),
            sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
            sa.Column('last_attempt_at', sa.DateTime(), nullable=True),
            sa.Column('error_metadata', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_reminders_id', 'reminders', ['id'])
        op.create_index('ix_reminders_user_status', 'reminders', ['user_id', 'status'])
        op.create_index('ix_reminders_scheduled_at', 'reminders', ['scheduled_at'])
        op.create_index('ix_reminders_task_id', 'reminders', ['task_id'])
        op.create_index('ix_reminders_due_processing', 'reminders', ['status', 'scheduled_at'])

    # 3. Create task_recurrence_rules table
    if 'task_recurrence_rules' not in existing_tables:
        op.create_table(
            'task_recurrence_rules',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('task_id', sa.String(length=64), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, unique=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
            sa.Column('frequency', sa.String(length=50), server_default='WEEKLY', nullable=False),
            sa.Column('interval', sa.Integer(), server_default='1', nullable=False),
            sa.Column('weekdays_json', sa.String(length=255), server_default='[]', nullable=False),
            sa.Column('month_day', sa.Integer(), nullable=True),
            sa.Column('end_date', sa.DateTime(), nullable=True),
            sa.Column('max_occurrences', sa.Integer(), nullable=True),
            sa.Column('occurrences_created', sa.Integer(), server_default='0', nullable=False),
            sa.Column('next_run_at', sa.DateTime(), nullable=True),
            sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_task_recurrence_rules_id', 'task_recurrence_rules', ['id'])
        op.create_index('ix_task_recurrence_rules_task_id', 'task_recurrence_rules', ['task_id'])
        op.create_index('ix_task_recurrence_rules_next_run', 'task_recurrence_rules', ['next_run_at'])

def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    if 'task_recurrence_rules' in existing_tables:
        op.drop_table('task_recurrence_rules')
    if 'reminders' in existing_tables:
        op.drop_table('reminders')
    if 'tasks' in existing_tables:
        existing_cols = [c['name'] for c in inspector.get_columns('tasks')]
        if 'timezone_name' in existing_cols:
            op.drop_column('tasks', 'timezone_name')
        if 'start_date' in existing_cols:
            op.drop_column('tasks', 'start_date')
        if 'is_all_day' in existing_cols:
            op.drop_column('tasks', 'is_all_day')
