"""B50: Goals, OKRs, Key Results, Milestones, and Check-Ins Management

Revision ID: 037_b50_goals_okrs_and_milestones
Revises: 036_b48_time_tracking_and_timesheets
Create Date: 2026-11-24 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '037_b50_goals_okrs_and_milestones'
down_revision = '036_b48_time_tracking_and_timesheets'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. goals
    if 'goals' not in existing_tables:
        op.create_table(
            'goals',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('team_id', sa.Integer(), sa.ForeignKey('teams.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('parent_goal_id', sa.String(64), sa.ForeignKey('goals.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('title', sa.String(255), nullable=False, index=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('goal_level', sa.String(32), nullable=False, server_default='ORGANIZATIONAL', index=True),
            sa.Column('status', sa.String(32), nullable=False, server_default='DRAFT', index=True),
            sa.Column('health_status', sa.String(32), nullable=False, server_default='ON_TRACK', index=True),
            sa.Column('health_reason', sa.Text(), nullable=True),
            sa.Column('priority', sa.String(32), nullable=False, server_default='HIGH', index=True),
            sa.Column('progress_percent', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('start_date', sa.DateTime(), nullable=True),
            sa.Column('target_date', sa.DateTime(), nullable=True, index=True),
            sa.Column('completed_date', sa.DateTime(), nullable=True),
            sa.Column('category', sa.String(64), nullable=False, server_default='STRATEGY'),
            sa.Column('tags_json', sa.Text(), nullable=False, server_default='[]'),
            sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )

    # 2. key_results
    if 'key_results' not in existing_tables:
        op.create_table(
            'key_results',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('goal_id', sa.String(64), sa.ForeignKey('goals.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('title', sa.String(255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('measurement_type', sa.String(32), nullable=False, server_default='NUMERIC_INCREASE', index=True),
            sa.Column('starting_value', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('current_value', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('target_value', sa.Float(), nullable=False, server_default='100.0'),
            sa.Column('unit', sa.String(32), nullable=False, server_default='%'),
            sa.Column('progress_percent', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
            sa.Column('status', sa.String(32), nullable=False, server_default='ACTIVE', index=True),
            sa.Column('tracking_method', sa.String(32), nullable=False, server_default='MANUAL'),
            sa.Column('due_date', sa.DateTime(), nullable=True),
            sa.Column('last_updated_at', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )

    # 3. key_result_progress_history
    if 'key_result_progress_history' not in existing_tables:
        op.create_table(
            'key_result_progress_history',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('key_result_id', sa.String(64), sa.ForeignKey('key_results.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('previous_value', sa.Float(), nullable=False),
            sa.Column('new_value', sa.Float(), nullable=False),
            sa.Column('previous_progress', sa.Float(), nullable=False),
            sa.Column('new_progress', sa.Float(), nullable=False),
            sa.Column('update_source', sa.String(32), nullable=False, server_default='MANUAL'),
            sa.Column('comment', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
        )

    # 4. goal_milestones
    if 'goal_milestones' not in existing_tables:
        op.create_table(
            'goal_milestones',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('goal_id', sa.String(64), sa.ForeignKey('goals.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('key_result_id', sa.String(64), sa.ForeignKey('key_results.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('title', sa.String(255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('status', sa.String(32), nullable=False, server_default='NOT_STARTED', index=True),
            sa.Column('priority', sa.String(32), nullable=False, server_default='MEDIUM'),
            sa.Column('progress_percent', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('start_date', sa.DateTime(), nullable=True),
            sa.Column('due_date', sa.DateTime(), nullable=True, index=True),
            sa.Column('completed_date', sa.DateTime(), nullable=True),
            sa.Column('blocked_reason', sa.Text(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )

    # 5. milestone_dependencies
    if 'milestone_dependencies' not in existing_tables:
        op.create_table(
            'milestone_dependencies',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('milestone_id', sa.String(64), sa.ForeignKey('goal_milestones.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('depends_on_milestone_id', sa.String(64), sa.ForeignKey('goal_milestones.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.UniqueConstraint('milestone_id', 'depends_on_milestone_id', name='uq_milestone_dependency'),
        )

    # 6. goal_project_links
    if 'goal_project_links' not in existing_tables:
        op.create_table(
            'goal_project_links',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('goal_id', sa.String(64), sa.ForeignKey('goals.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.UniqueConstraint('goal_id', 'project_id', name='uq_goal_project_link'),
        )

    # 7. key_result_task_links
    if 'key_result_task_links' not in existing_tables:
        op.create_table(
            'key_result_task_links',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('key_result_id', sa.String(64), sa.ForeignKey('key_results.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('task_id', sa.String(64), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.UniqueConstraint('key_result_id', 'task_id', name='uq_key_result_task_link'),
        )

    # 8. goal_check_ins
    if 'goal_check_ins' not in existing_tables:
        op.create_table(
            'goal_check_ins',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('goal_id', sa.String(64), sa.ForeignKey('goals.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('progress_percent', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('confidence_score', sa.Integer(), nullable=False, server_default='4'),
            sa.Column('summary', sa.Text(), nullable=False),
            sa.Column('blockers', sa.Text(), nullable=True),
            sa.Column('next_steps', sa.Text(), nullable=True),
            sa.Column('support_needed', sa.Text(), nullable=True),
            sa.Column('status', sa.String(32), nullable=False, server_default='SUBMITTED', index=True),
            sa.Column('reviewer_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('reviewed_at', sa.DateTime(), nullable=True),
            sa.Column('reviewer_feedback', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
        )

    # 9. goal_comments
    if 'goal_comments' not in existing_tables:
        op.create_table(
            'goal_comments',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('goal_id', sa.String(64), sa.ForeignKey('goals.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )

    # 10. goal_settings
    if 'goal_settings' not in existing_tables:
        op.create_table(
            'goal_settings',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
            sa.Column('check_in_frequency', sa.String(32), nullable=False, server_default='WEEKLY'),
            sa.Column('auto_recalculate_progress', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('enable_ai_recommendations', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('rules_config_json', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )


def downgrade() -> None:
    op.drop_table('goal_settings')
    op.drop_table('goal_comments')
    op.drop_table('goal_check_ins')
    op.drop_table('key_result_task_links')
    op.drop_table('goal_project_links')
    op.drop_table('milestone_dependencies')
    op.drop_table('goal_milestones')
    op.drop_table('key_result_progress_history')
    op.drop_table('key_results')
    op.drop_table('goals')
