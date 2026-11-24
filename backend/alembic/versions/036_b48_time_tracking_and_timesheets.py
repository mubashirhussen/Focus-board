"""B48: Time Tracking, Active Timers, Timesheets, Approvals, and Settings

Revision ID: 036_b48_time_tracking_and_timesheets
Revises: 035_b47_predictive_project_intelligence
Create Date: 2026-11-24 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '036_b48_time_tracking_and_timesheets'
down_revision = '035_b47_predictive_project_intelligence'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. timesheets
    if 'timesheets' not in existing_tables:
        op.create_table(
            'timesheets',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('period_start', sa.DateTime(), nullable=False, index=True),
            sa.Column('period_end', sa.DateTime(), nullable=False, index=True),
            sa.Column('total_seconds', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('billable_seconds', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('non_billable_seconds', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('status', sa.String(32), nullable=False, server_default='DRAFT', index=True),
            sa.Column('submitted_at', sa.DateTime(), nullable=True),
            sa.Column('reviewed_at', sa.DateTime(), nullable=True),
            sa.Column('reviewer_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('review_comments', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )

    # 2. time_entries
    if 'time_entries' not in existing_tables:
        op.create_table(
            'time_entries',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('task_id', sa.String(64), sa.ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('timesheet_id', sa.Integer(), sa.ForeignKey('timesheets.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('start_time', sa.DateTime(), nullable=False, index=True),
            sa.Column('end_time', sa.DateTime(), nullable=True, index=True),
            sa.Column('duration_seconds', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('billable', sa.Boolean(), nullable=False, server_default='1', index=True),
            sa.Column('hourly_rate', sa.Float(), nullable=True, server_default='0.0'),
            sa.Column('billable_amount', sa.Float(), nullable=True, server_default='0.0'),
            sa.Column('entry_source', sa.String(32), nullable=False, server_default='TIMER', index=True),
            sa.Column('approval_status', sa.String(32), nullable=False, server_default='DRAFT', index=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )

    # 3. active_timers
    if 'active_timers' not in existing_tables:
        op.create_table(
            'active_timers',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('task_id', sa.String(64), sa.ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('started_at', sa.DateTime(), nullable=False),
            sa.Column('last_resumed_at', sa.DateTime(), nullable=False),
            sa.Column('accumulated_seconds', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('status', sa.String(32), nullable=False, server_default='RUNNING', index=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('billable', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )

    # 4. timesheet_approvals
    if 'timesheet_approvals' not in existing_tables:
        op.create_table(
            'timesheet_approvals',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column('timesheet_id', sa.Integer(), sa.ForeignKey('timesheets.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('reviewer_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('decision', sa.String(32), nullable=False),
            sa.Column('review_comments', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
        )

    # 5. time_tracking_settings
    if 'time_tracking_settings' not in existing_tables:
        op.create_table(
            'time_tracking_settings',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, unique=True, index=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('default_daily_hours', sa.Float(), nullable=False, server_default='8.0'),
            sa.Column('default_weekly_hours', sa.Float(), nullable=False, server_default='40.0'),
            sa.Column('allow_manual_entry', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('allow_overlapping_entries', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('require_timesheet_approval', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('default_billable', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('default_hourly_rate', sa.Float(), nullable=False, server_default='75.0'),
            sa.Column('max_entry_duration_hours', sa.Float(), nullable=False, server_default='24.0'),
            sa.Column('submission_deadline_day', sa.String(32), nullable=False, server_default='MONDAY'),
            sa.Column('settings_json', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )

    # 6. time_entry_audit_logs
    if 'time_entry_audit_logs' not in existing_tables:
        op.create_table(
            'time_entry_audit_logs',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column('time_entry_id', sa.Integer(), nullable=True, index=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('action', sa.String(64), nullable=False),
            sa.Column('changes_json', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('timestamp', sa.DateTime(), nullable=False, index=True),
        )

def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    for table in [
        'time_entry_audit_logs',
        'time_tracking_settings',
        'timesheet_approvals',
        'active_timers',
        'time_entries',
        'timesheets',
    ]:
        if table in existing_tables:
            op.drop_table(table)
